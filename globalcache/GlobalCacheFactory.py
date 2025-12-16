#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/globalcache/GlobalCacheFactory.py /main/13 2024/05/10 10:16:57 pbellary Exp $
#
# GlobalCacheFactory.py
#
# Copyright (c) 2021, 2024, Oracle and/or its affiliates.
#
#    NAME
#      GlobalCacheFactory.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    05/09/24 - Bug 36553223 - EXADBXS:23.4.1.2.2:ZURICH: DOM0 TO DOM0 
#                           IMAGE COPY FAILING DUE TO IMPROPER PASSWORDLESS SETUP
#    ririgoye    02/20/24 - Bug 36315154 - Switched from checking skippable
#                           grid images as strings to checking them as
#                           dictionaries.
#    ririgoye    01/09/24 - SKIP GRID IMAGES VALIDATION DURING PREVM_SETUP FOR
#                           EXADB-XS
#    aararora    09/27/23 - Use ProcessManager instead of multiprocessing Pool
#                           directly and add timeout.
#    ririgoye    08/23/23 - Bug 35616435 - Fix redundant/multiple instances of
#                           mConnect
#    jesandov    10/07/21 - Creation
#

import os
import copy

from exabox.globalcache.GlobalCacheWorker import GlobalCacheWorker
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
                               node_exec_cmd, node_write_text_file)

from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure

def mStartWorker(aImagePath, aImageHash, aDom0s):

    _worker = GlobalCacheWorker(aImagePath, aImageHash, aDom0s)
    _rc = _worker.mDoImageCopy()

    return _rc

def mStartWorkerValidateImage(aImagePath, aImageHash):

    ebLogInfo(f"Validating {aImagePath}")

    _worker = GlobalCacheWorker("dummy", None, [])
    _worker.mCreateConnections()

    _inventoryHash = aImageHash
    _realHash = _worker.mCalculateHash("local", aImagePath)

    if _inventoryHash != _realHash:
        _msg = "Corrupted entry on inventory.json"
        _msg = f"{_msg} image on {aImagePath} has different sha256hash"
        _msg = f"{_msg} local hash:'{_realHash}'"
        _msg = f"{_msg} inventory hash:'{_inventoryHash}'"
        ebLogError(_msg)
        raise ExacloudRuntimeError(0x0754, 0x0A, _msg)


class GlobalCacheFactory:

    def __init__(self, aClubox):
        self.__clubox = aClubox

    def mGetClubox(self):
        return self.__clubox

    def mSetClubox(self, aValue):
        self.__clubox = aValue

    def mValidateImageInventory(self):

        ebLogInfo("Validating image repository and inventory.json information")

        _, _fileList = self.mGetClubox().mDyndepFilesList()
        if _fileList is None or _fileList == {}:
            ebLogWarn('*** Image configuration not found - skipping images/bits update and copy')
            return

        _plist = ProcessManager()
        for _image in _fileList:
            _poolArgs = []
            if ("grid-klone" in _image["local"] or "db-klone" in _image["local"]) and self.mGetClubox().mIsExaScale():
                ebLogWarn('*** Skipped grid-klone/db-klone image since this is an ExaScale service')
                continue
            if "sha256sum" in _image:
                _poolArgs = [_image['local'], _image["sha256sum"]]
            else:
                ebLogTrace(f"sha256sum not defined for image: {_image}")
                continue
            _p = ProcessStructure(mStartWorkerValidateImage, _poolArgs)
            _p.mSetMaxExecutionTime(60*60) # 60 minutes timeout should be enough for local validation of hash
            _p.mSetJoinTimeout(60)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

    def mFetchDom0IpAddress(self, aDom0s):
        _dom0s = aDom0s
        _dom0_addr = {}

        for _dom0 in _dom0s:
            _dom0_mac = self.mGetClubox().mGetMachines().mGetMachineConfig(_dom0)
            _net_list = _dom0_mac.mGetMacNetworks()
            for _net in _net_list:
                _priv = self.mGetClubox().mGetNetworks().mGetNetworkConfig(_net)
                if _priv.mGetNetType() == "admin":
                    _dom0_addr[_dom0] = _priv.mGetNetIpAddr()
                    break
        return _dom0_addr

    def mAddHostsOnDom0(self, aNode, aCurrentDom0, aDom0s):
        _node = aNode
        _currentDom0 = aCurrentDom0
        _dom0s = aDom0s
        _etc_hosts = "/etc/hosts"

        _dom0_addr = self.mFetchDom0IpAddress(_dom0s)
        try:
            _grep_bin = node_cmd_abs_path_check(node=_node, cmd="grep")
            for _dom0 in _dom0s:
                _ipaddr = _dom0_addr[_dom0]
                _hostname = _dom0.split('.')[0]
                # Check if /etc/hosts contains dom0 ip address already
                # If is not present, add it
                _addr_in_etchosts = node_exec_cmd(node=_node,
                    cmd = f"{_grep_bin} -q '{_ipaddr}' {_etc_hosts}")

                if _addr_in_etchosts.exit_code == 0:
                    ebLogInfo(f"This is nop, as '{_ipaddr}' is already present in: {_currentDom0} on {_etc_hosts}")
                elif _addr_in_etchosts.exit_code == 1:
                    ebLogInfo(f"Adding '{_ipaddr}' to '{_etc_hosts}' in {_currentDom0}")
                    _data = f"{_ipaddr}  {_dom0}  {_hostname}\n"
                    node_write_text_file(_node, _etc_hosts, _data, append=True)
                else:
                    ebLogWarn(f"Unable to fetch '{_etc_hosts}' state, in {_currentDom0}. ")
        except Exception as e:
            ebLogError(f"Error during connection to host {_dom0}.")
            ebLogError(f"{e}")

    def mCreatePasswordless(self):

        _dom0s, _, _, _ = self.mGetClubox().mReturnAllClusterHosts()
        _exakms = get_gcontext().mGetExaKms()
        _dummyEntry = _exakms.mBuildExaKmsEntry("dummy", "dummy",
                         _exakms.mGetEntryClass().mGeneratePrivateKey())
        _privkey = _dummyEntry.mGetPrivateKey()
        _pubkey = _dummyEntry.mGetPublicKey("GlobalCache")

        # Create private key
        for _dom0 in _dom0s:

            try:
                with connect_to_host(_dom0, get_gcontext()) as _node:

                    #Add Dom0s ipaddress to /etc/hosts
                    self.mAddHostsOnDom0(_node, _dom0, _dom0s)

                    if not _node.mFileExists("/root/.ssh/global_cache_key"):

                        _node.mExecuteCmd(f"/bin/echo '{_privkey}' > /root/.ssh/global_cache_key")
                        _node.mExecuteCmd(f"/bin/chmod 0700 /root/.ssh/global_cache_key")
                        _node.mExecuteCmd(f"/bin/echo '{_pubkey}' >> /root/.ssh/authorized_keys")

                        for _dom0ToRemove in _dom0s:
                            _node.mExecuteCmdLog(f"/usr/bin/ssh-keygen -R {_dom0ToRemove}")

                            if _dom0ToRemove == _dom0:
                                continue

                            try:
                                with connect_to_host(_dom0ToRemove, get_gcontext()) as _restnode:
                                    _i, _o, _e = _restnode.mExecuteCmd(f"/bin/grep -i '{_pubkey}' /root/.ssh/authorized_keys")
                                    _key_exists = _o.readlines()
                                    if _key_exists:
                                        ebLogInfo(f"*** SSH equivalence is already exists")
                                    else:
                                        _restnode.mExecuteCmd(f"/bin/echo '{_pubkey}' >> /root/.ssh/authorized_keys")

                            except Exception as e:
                                ebLogError(f"Error during connection to host {_dom0ToRemove}.")
                                ebLogError(f"{e}")
            except Exception as e:
                ebLogError(f"Error during connection to host {_dom0}.")
                ebLogError(f"{e}")

    def mCleanPassordless(self):

        _dom0s, _, _, _ = self.mGetClubox().mReturnAllClusterHosts()

        for _dom0 in _dom0s:

            try:
                with connect_to_host(_dom0, get_gcontext()) as _node:
                    _node.mExecuteCmd(f"/bin/rm /root/.ssh/global_cache_key")
                    _node.mExecuteCmd(f"/bin/sed -i /GlobalCache/d /root/.ssh/authorized_keys")

            except Exception as e:
                ebLogError(f"Error during connection to host {_dom0}.")
                ebLogError(f"{e}")

    def mDoParallelCopy(self):

        _dom0s, _, _, _ = self.mGetClubox().mReturnAllClusterHosts()
        _, _fileList = self.mGetClubox().mDyndepFilesList()
        if _fileList is None or _fileList == {}:
            ebLogWarn('*** Image configuration not found - skipping images/bits update and copy')
            return

        _plist = ProcessManager()
        for _image in _fileList:
            _poolArgs = []
            _hash = None
            if "sha256sum" in _image:
                _hash = _image['sha256sum']
            _poolArgs = [_image['local'], _hash, _dom0s]
            _p = ProcessStructure(mStartWorker, _poolArgs)
            _p.mSetMaxExecutionTime(120*60) # 120 minutes timeout should be enough to copy for each file.
            _p.mSetJoinTimeout(60)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()


# end of file
