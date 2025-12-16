#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/userutils.py /main/7 2025/04/21 23:52:05 gparada Exp $
#
# userutils.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      userutils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED (MM/DD/YY)
#    gparada   04/15/25 - 37828983 ssh CPS' as ecra usr, exec cmds with sudo
#    gparada   02/28/25 - 37746597 force userdel for secscan with diff owner
#    gparada   02/28/25 - 37652127 remove secscan home folder
#    gparada   06/25/24 - Bug 36628459 Refactor secscan methods out of cluctrl
#    gparada   06/25/24 - Creation
#

# Python libs
import operator
from subprocess import PIPE
from typing import Optional, Dict, List, Tuple, TYPE_CHECKING 

# Exacloud libs
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.node import (
    node_cmd_abs_path_check,
    node_exec_cmd_check,    
)

# We need to import exaBoxCluCtrl for type annotations, but it will cause a
# cyclic-import at runtime.  Thus we import it only when type-checking.  We
# still need to define type exaBoxCluCtrl or pylint will complain, though, so
# we just make it an alias to 'object' when not type-checking.
if TYPE_CHECKING:
    from exabox.ovm.clucontrol import exaBoxCluCtrl
else:
    exaBoxCluCtrl = object  # pylint: disable=invalid-name

class ebUserUtils:

    @staticmethod
    def mAddSecscanSshd(aEbox: exaBoxCluCtrl) -> None:

        _dom0s, _, _cells, _switches = aEbox.mReturnAllClusterHosts()
        _hosts = _dom0s + _cells + _switches

        for _host in _hosts:
            ebUserUtils.mAddSecscanSshdSingle(aEbox, _host)
    
    @staticmethod
    def mAddSecscanSshdSingle(aEbox: exaBoxCluCtrl, aHostname:str) -> None:
        """
        A first refactor was done. 
        Notes for a 2nd iteration to Refactor:
            mAddSecscanSshdSingle is called from 2 places 
            a) Exacloud clucontrol.py
            b) Infrapatching targethandler.py
            We can remove dependency on ebox argument if we ensure 
            the aHostname is always present and valid
        """

        _dom0s, _, _cells, _switches = aEbox.mReturnAllClusterHosts()
        _hosts = _dom0s + _cells + _switches

        # Patching validation
        if aHostname not in _hosts:
            return

        _node = exaBoxNode(get_gcontext())

        try:
            _node.mConnect(aHost=aHostname)
            _svc_cmd = node_cmd_abs_path_check(_node, "service", sbin=True)

            _cmd = "/bin/cat /etc/ssh/sshd_config | /bin/grep 'TrustedUserCAKey.*ca.pub'"
            _node.mExecuteCmd(_cmd)

            if _node.mGetCmdExitStatus() != 0:

                _cmd = "/bin/echo 'TrustedUserCAKeys /etc/ssh/ca.pub' >> /etc/ssh/sshd_config"
                node_exec_cmd_check(_node, _cmd)

                _cmd = f"{_svc_cmd} sshd restart"
                node_exec_cmd_check(_node, _cmd)

        finally:
            _node.mDisconnect()

    @staticmethod
    def mPushSecscanKey(aEbox:exaBoxCluCtrl, aDomuList:list=None) -> None:
        _path = 'misc/secscan/id_rsa.secscan.pub'
        try:
            _file = open(_path)
            _secscankey = _file.read()
            _file.close()
        except:
            ebLogError(f'*** Cannot access/read {_path} key file')
            return

        cmd = "/usr/bin/chage -E -1 -M -1 secscan;"
        cmd += "/bin/mkdir -p /etc/ssh-keys/;"
        cmd += "/bin/touch /etc/ssh-keys/secscan;"
        cmd += "/bin/chmod 644 /etc/ssh-keys/secscan;"
        cmd += "/bin/chown -R secscan:secscan /etc/ssh-keys/secscan;"
        cmd += "/bin/echo '" + _secscankey + "' > /etc/ssh-keys/secscan"

        if aDomuList:
            _domu_list = aDomuList
        else:
            _domu_list = list(map(operator.itemgetter(1),aEbox.mReturnDom0DomUPair()))

        for _domU in _domu_list:
            _nodeU = exaBoxNode(get_gcontext())
            _nodeU.mConnect(aHost=_domU)

            # Search for secscan user id between 2009 and 3000. 
            # Errors out if not found.
            _domu_secscan_uid = ebUserUtils.mSearchSecScanUser(_nodeU)

            ebUserUtils.mCreateUser(_nodeU, _domu_secscan_uid, 'secscan', cmd)

            _nodeU.mDisconnect()

    @staticmethod
    def mSearchSecScanUser(aNode:exaBoxNode) -> int:
        _node = aNode
        _default_uid = 2009
        _max_uid = 3000
        _uid_available = False
        _uid = -1
        _uid_available, _uid = ebUserUtils.mGetUidAvailable(
            _node, _default_uid, _max_uid)
        if not _uid_available:
            ebLogError('*** Could not find a suitable uid for secscan user')
            return -1
        return _uid   

    @staticmethod
    def mGetUidAvailable(aNode:exaBoxNode, aDefaultUid:int, aMaxUid:int) -> Tuple[bool, int]:
        """
        Generic function to search if a default_uid is available in a host.
        If default_uid is not available (other user exists with it), then
        it will iterate one by one to find the next uid available 
        (until max_id is reached)
        Refactored out of mPushSecscanKey.
        """
        _node = aNode
        _default_uid = aDefaultUid
        _max_uid = aMaxUid
        _uid_available = False

        _uid = _default_uid

        while not _uid_available and _uid < 3000:
            _uid_cmd = "/bin/id {0}".format(str(_uid))

            _node.mExecuteCmdLog(_uid_cmd)
            _rc = _node.mGetCmdExitStatus()

            if _rc:
                _uid_available = True
            else:
                _uid = _uid + 1
        
        return _uid_available, _uid

    @staticmethod
    def mCreateUser(aNode:exaBoxNode, aUid:int, aId:str, aExtraCmd:str=None) -> int:
        _node = aNode
        _uid = aUid
        _id = aId
        _extraCmd = aExtraCmd

        ebLogInfo(f'Creating user: {_id} with uid: {_uid} in {_node.mGetHostname()}')
        # Create user account with given uid and id (username and numberId)
        _user_add_cmd = f"sudo /usr/sbin/useradd --uid {_uid} {_id};"
        _full_cmd = _user_add_cmd
        if _extraCmd:
            _full_cmd = _full_cmd + _extraCmd

        _std_out = PIPE
        _std_err = PIPE

        _node.mExecuteCmdLog(_full_cmd,aStdOut=_std_out, aStdErr=_std_err)
        _rc = _node.mGetCmdExitStatus()
        return _rc, _std_out, _std_err

    @staticmethod
    def mDeleteUser(aNode:exaBoxNode, aId:str) -> int:
        _node = aNode
        _id = aId
        ebLogInfo(f'Deleting user: {_id} in {_node.mGetHostname()}')
        # Delete user account, user's home directory and mail spool
        _user_del_cmd = f"sudo /usr/sbin/userdel -f -r {_id};"

        _std_out = PIPE
        _std_err = PIPE

        _node.mExecuteCmdLog(_user_del_cmd,aStdOut=_std_out, aStdErr=_std_err)
        _rc = _node.mGetCmdExitStatus()
        return _rc, _std_out, _std_err

    @staticmethod
    def mCreateSshKeys(aUserName) -> dict:
        """
        Returns a dictionary containing keys: 'private_key' and 'public_key'
        """
        _exakms = get_gcontext().mGetExaKms()
        _dummyEntry = _exakms.mBuildExaKmsEntry("dummy", 
            aUserName, _exakms.mGetEntryClass().mGeneratePrivateKey())
        return _dummyEntry

