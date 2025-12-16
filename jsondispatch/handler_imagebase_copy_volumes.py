#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_imagebase_copy_volumes.py /main/1 2025/12/01 09:38:52 jesandov Exp $
#
# handler_imagebase_copy_volumes.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      handler_imagebase_copy_volumes.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    11/26/25 - Creation
#

import time
import os
import re
import uuid
import json
import copy

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.common import mCompareModel
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check, node_exec_cmd_check,
                               node_exec_cmd, node_read_text_file, node_write_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, TimeoutBehavior, ExitCodeBehavior
from exabox.core.Error import ebError, ExacloudRuntimeError


class ImagebaseCopyVolume(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/imagebase_copy_volumes.json"))
        self.payload = aOptions

    def mExecuteCmdParallel(self, aHostCmdDict, aUser="root"):
        """
            aHostCmdDict = {
                "host1": [cmd1]
            }
        """

        def mSingleExecuteCmd(aHost, aRc, aCmdList, aUser="root"):

            _localList = []
            with connect_to_host(aHost, get_gcontext(), username=aUser) as _node:

                for _cmd in aCmdList:
                    _, _o, _e = _node.mExecuteCmd(_cmd)

                    _status = {}
                    _status["cmd"] = _cmd
                    _status["stdout"] = _o.read() if _o else ""
                    _status["stderr"] = _e.read() if _e else ""
                    _status["rc"] = _node.mGetCmdExitStatus()

                    _localList.append(_status)

            aRc[aHost] = _localList

        _plist = ProcessManager()
        _rcs = _plist.mGetManager().dict()

        for _host, _cmdlist in aHostCmdDict.items():

            _p = ProcessStructure(mSingleExecuteCmd, [_host, _rcs, _cmdlist, aUser])
            _p.mSetMaxExecutionTime(30*60) # 30 minutes
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        _res = copy.deepcopy(dict(_rcs))
        _res = dict(sorted(_res.items(), key=lambda x: x[0]))

        return _res


    def mExecute(self):

        _rc = 0
        _response = {}

        def mPrepareExagipPython(aNode):

            _remoteLocation = "/opt/exacloud/exagip/"
            _exacloudFolder = re.search("(.*exacloud/)", os.path.abspath(__file__)).group(1)
            _cert = f"{_exacloudFolder}/exabox/kms/combined_r1.crt"

            node_exec_cmd_check(aNode, f"/bin/mkdir -p {_remoteLocation}")

            if not aNode.mFileExists(f"{_remoteLocation}/oss_instance_principal_script.py"):
                aNode.mCopyFile(
                    f"{_exacloudFolder}/exagip/src/oss_instance_principal_script.py",
                    f"{_remoteLocation}/oss_instance_principal_script.py"
                )

            if not aNode.mFileExists(f"{_remoteLocation}/mycert.crt"):
                aNode.mCopyFile(_cert, f"{_remoteLocation}/mycert.crt")

            if not aNode.mFileExists(f"/opt/exacloud/exagip/python"):

                node_exec_cmd_check(aNode, f"/bin/mkdir -p /opt/exacloud/exagip/python")

                aNode.mCopyFile(
                    f"{_exacloudFolder}/images/python-for-vmbackup.tgz",
                    f"/opt/exacloud/exagip/python/python-for-vmbackup.tgz"
                )

                node_exec_cmd_check(aNode, f"/bin/tar xf /opt/exacloud/exagip/python/python-for-vmbackup.tgz -C /opt/exacloud/exagip/python")
                node_exec_cmd_check(aNode, f"/bin/rm -rf /opt/exacloud/exagip/python/python-for-vmbackup.tgz")


        ebLogTrace("Entering mImageBaseRestore")
        _bomSpec = {}

        if "image_base_bom" in self.payload.jsonconf:
            _bomSpec = self.payload.jsonconf["image_base_bom"]

        if _bomSpec:

            # Test E2E Provisioning or Endpoint call

            _bomFullSystem = _bomSpec["gold_image"]["system_image"]
            _bomFullU01 = _bomSpec["gold_image"]["u01_image"]
            _bomSystem = os.path.basename(_bomSpec["gold_image"]["system_image"])
            _bomU01 = os.path.basename(_bomSpec["gold_image"]["u01_image"])
            _uuid = str(uuid.uuid1())
            _tmpFolder = f"/EXAVMIMAGES/{_uuid}"

            _toExecute = {}

            # Fetch host info from payload
            _hostInfo = {}
            for _jNode in self.payload.jsonconf["customer_network"]["nodes"]:
                if "volumes" in _jNode:

                    for _volume in _jNode["volumes"]:

                        if "attach_host" in _volume and _volume["attach_host"]:
                            if _volume["attach_host"] in _hostInfo:
                                _hostInfo[_volume["attach_host"]].append(_volume)
                            else:
                                _hostInfo[_volume["attach_host"]] = [_volume]

                        elif "dom0" in _volume and _volume["dom0"]:
                            if _volume[_volume["dom0"]] in _hostInfo:
                                _hostInfo[_volume["dom0"]].append(_volume)
                            else:
                                _hostInfo[_volume["dom0"]] = [_volume]

                        elif "fqdn" in _jNode and _jNode["fqdn"]:
                            if _jNode["fqdn"] in _hostInfo:
                                _hostInfo[_jNode["fqdn"]].append(_volume)
                            else:
                                _hostInfo[_jNode["fqdn"]] = [_volume]

            # get information of the oss
            with open("exagip/config/oss.conf") as _f:
                _ossInfo = json.loads(_f.read())

            # Replicate gold images
            for _hostName in _hostInfo.keys():

                with connect_to_host(_hostName, get_gcontext()) as _node:
                    mPrepareExagipPython(_node)

                _toExecute[_hostName] = []
                _toExecute[_hostName].append(f"/bin/mkdir -p {_tmpFolder}")

                _namespace = _ossInfo.get("bom_namespace")
                _bucket = _ossInfo.get("bom_bucket")

                # Activate python commands
                _cmd = "/opt/exacloud/exagip/python/opt/python-vmbackup/bin/python3.6"
                _cmd = f"{_cmd} /opt/exacloud/exagip/oss_instance_principal_script.py"
                _cmd = f"{_cmd} download {_namespace} {_bucket} --r1-cert=/opt/exacloud/exagip/mycert.crt"

                # Download file
                _toExecute[_hostName].append(f"{_cmd} --to={_tmpFolder}/{_bomSystem} --from={_bomFullSystem}")
                _toExecute[_hostName].append(f"{_cmd} --to={_tmpFolder}/{_bomU01} --from={_bomFullU01}")

            _result = self.mExecuteCmdParallel(_toExecute)
            ebLogInfo(json.dumps(_result, indent=4))

            # Review that the files downloaded from the OSS are correct
            for _hostName in _hostInfo.keys():
                with connect_to_host(_hostName, get_gcontext()) as _node:
                    _toReviewList = [f"{_tmpFolder}/{_bomSystem}", f"{_tmpFolder}/{_bomU01}"]
                    for _toReview in _toReviewList:
                        _errorOss = False
                        if _node.mFileExists(_toReview):
                            _node.mExecuteCmd(f"/bin/cat {_toReview} | grep 'was not found in the bucket'")
                            _errorOss = _node.mGetCmdExitStatus() == 0
                        else:
                            _errorOss = True
                        if _errorOss:
                            _msg = f"Error while download file {_toReview} from OSS, please review folder: {_tmpFolder}"
                            ebLogError(_msg)
                            raise ExacloudRuntimeError(0x0825, 0xA, _msg)

            # Continue with the parallel commands
            _toExecute = {}
            for _hostName in _hostInfo.keys():
                _toExecute[_hostName] = []
                _toExecute[_hostName].append(f"/usr/bin/pbzip2 -d {_tmpFolder}/{_bomSystem}")
                _toExecute[_hostName].append(f"/usr/bin/pbzip2 -d {_tmpFolder}/{_bomU01}")

            # Copy Gold Images into EDV Volumes
            _systemVolume = ""
            _u01Volume = ""
            _volInfo = {}

            for _hostName, _volHost in _hostInfo.items():

                for _volumen in _volHost:

                    if _volumen["volumetype"].lower() == "system":
                        _systemVolume = _volumen["volumedevicepath"]

                    if _volumen["volumetype"].lower() == "u01":
                        _u01Volume = _volumen["volumedevicepath"]

                    if not _systemVolume or not _u01Volume:
                        continue

                _ddSystem = f"{_tmpFolder}/{_bomSystem}".replace(".bz2", "")
                _ddU01 = f"{_tmpFolder}/{_bomU01}".replace(".bz2", "")

                _toExecute[_hostName].append(f"/usr/bin/dd if={_ddSystem} of=/dev/exc/{_systemVolume} bs=100M conv=sparse status=progress")
                _toExecute[_hostName].append(f"/usr/bin/dd if={_ddU01} of=/dev/exc/{_u01Volume} bs=100M conv=sparse status=progress")
                _volInfo[_hostName] = {"sys": _systemVolume, "u01": _u01Volume}

            for _hostName in _hostInfo.keys():
                _toExecute[_hostName].append(f"/bin/rm -rf {_tmpFolder}")

            _result = self.mExecuteCmdParallel(_toExecute)
            ebLogInfo(json.dumps(_result, indent=4))

            # Add XFS_Repair in case of faulty copy
            for _hostName in _hostInfo.keys():

                with connect_to_host(_hostName, get_gcontext()) as _node:

                    _systemVolume = _volInfo[_hostName]["sys"]
                    _loop = ""

                    node_exec_cmd(_node, f"/usr/sbin/vgrename VGExaDb VGExaDbDom0")

                    try:
                        node_exec_cmd_check(_node, f"/usr/sbin/losetup -fP /dev/exc/{_systemVolume}")

                        _, _o, _ = _node.mExecuteCmd("/usr/sbin/losetup -l | /bin/tail -n 1 | /bin/awk '{print $1}'")
                        _loop = _o.read().strip()

                        node_exec_cmd_check(_node, f"/usr/sbin/kpartx -av {_loop}p3")
                        node_exec_cmd(_node, f"/usr/sbin/vgchange -a y VGExaDbDomU")

                        node_exec_cmd(_node, f"for sys in /dev/VGExaDbDomU/LVDb*; do /usr/sbin/xfs_repair -L $sys; done")

                    finally:
                        node_exec_cmd(_node, f"/usr/sbin/vgchange -a n VGExaDbDomU")

                        if _loop:
                            node_exec_cmd(_node, f"/usr/sbin/kpartx -dv {_loop}p3")
                            node_exec_cmd(_node, f"/usr/sbin/losetup -d {_loop}")

                        node_exec_cmd(_node, f"/usr/sbin/vgrename  VGExaDbDom0 VGExaDb")


        return (0, _result)

# end of the file
