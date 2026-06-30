#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_imagebase_copy_volumes.py jesandov_bug-38875952/1 2026/02/20 15:45:46 jesandov Exp $
#
# handler_imagebase_copy_volumes.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
#    aypaul      05/11/26 - Bug#39276269 Fix security issue for base image
#                           attach
#    joysjose    04/10/26 - fix imagebase copy volume lock handling for unit
#                           tests
#    jesandov    03/30/26 - 39139207: Fix collision on parallel imagebase copy
#    jesandov    03/26/26 - 39060375: Add correct R1 certificate path
#    jesandov    03/13/26 - 38875952: Change approach to copy to domU
#    jesandov    06/02/26 - 38938299: Add lock mechanism
#    jesandov    02/17/26 - 38934422: Add ExaLock
#    gsundara    12/11/25 - PYTHON ENVIRONMENT CONFIGURATION ISSUES CAUSING OSS
#                           INSTANCE PRINCIPAL SCRIPT FAILURES ON DOM0
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
from exabox.utils.common import is_valid_fqdn
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check, node_exec_cmd_check,
                               node_exec_cmd, node_read_text_file, node_write_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, TimeoutBehavior, ExitCodeBehavior
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.ovm.remotelock import RemoteLock


class ImagebaseCopyVolume(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/imagebase_copy_volumes.json"))
        self.payload = aOptions

    def mGetUdevPath(self, aDomUNode, aUdevStr):

        _mountedHdd = None

        try:

            _cmd = f'dmesg | grep "Attached SCSI disk" | grep "{aUdevStr}"'
            _, _mountedHdd, _ = node_exec_cmd_check(aDomUNode, _cmd)
            _mountedHdd = _mountedHdd.strip().split("\n")[-1].strip()
            _mountedHdd = re.search("\[.*\].*\[(.*)\]", _mountedHdd).group(1)
            _mountedHdd = f"/dev/{_mountedHdd}"

        except:
            _mountedHdd = None

        ebLogInfo(f"Mounted Udev: {aUdevStr} to {_mountedHdd}")
        return _mountedHdd

    def mGetNextDeviceDom0(self, aDom0Node, aClientDomU):

        _next = None

        _cmd = f"virsh domblklist {aClientDomU}"
        _, _devices, _ = node_exec_cmd_check(aDom0Node, _cmd)
        _lastDevice = _devices.strip().split("\n")[-1].strip().split(" ")[0]

        if ord(_lastDevice[-1])+1 >= 123: # 'z'+1
            raise ValueError(f"Current last device is too long: {_lastDevice}")

        _next = _lastDevice[0:-1] + chr(ord(_lastDevice[-1])+1)

        return _next


    def mCreateNatDomUToClientDomUMapping(self, aDom0Node):

        _cmd = """
            for VM in `virsh list --all --name`;
                do
                    grep IPADDR /etc/sysconfig/network-scripts/ifcfg-vmeth0*:`
                        virsh domiflist $VM |
                        grep vmeth2 | awk '{ print $3 }' | cut -d h -f 2` |
                    cut -d = -f 2 | xargs nslookup | grep name | awk '{ print $4 }';
                done
            """

        _, _natVms, _ = node_exec_cmd(aDom0Node, _cmd)
        _natVms = _natVms.split("\n")
        _natVms = list(map(lambda x: x.strip()[0:-1], _natVms))
        _natVms = list(filter(lambda x: x, _natVms))

        _cmd = """virsh list --all --name | grep -v 'gold\..*\.internal'"""
        _, _clientVms, _ = node_exec_cmd(aDom0Node, _cmd)
        _clientVms = _clientVms.split("\n")
        _clientVms = list(filter(lambda x: x, _clientVms))

        if len(_natVms) != len(_clientVms):
            raise ValueError(f"Mismatch between nat vms: {_natVms} and client vms: {_clientVms}")

        return dict(zip(_natVms, _clientVms))


    def mCopyVolume(self, aBomSpec, aHostInfo, aKey):

        _uuid = str(uuid.uuid4())
        _workdir = f"/opt/exacloud/{_uuid}"
        _exacloudPath = re.search("(.*exacloud)", os.path.abspath(__file__)).group(1)
        _pythonPath = os.path.join(_exacloudPath, "bin/python")
        _exacloudTmpFolder = os.path.join(_exacloudPath, "tmp", _uuid)

        _bomFullSystem = aBomSpec["gold_image"]["system_image"]
        _bomFullU01 = aBomSpec["gold_image"]["u01_image"]
        _bomSystem = os.path.basename(aBomSpec["gold_image"]["system_image"])
        _bomU01 = os.path.basename(aBomSpec["gold_image"]["u01_image"])
        _attachDone = False

        try:

            # Download gold images in exacloud folder
            _cmd = f"/bin/mkdir -p {_exacloudTmpFolder}"
            self.mExecuteLocal(_cmd)

            # get information of the oss
            with open("exagip/config/oss.conf") as _f:
                _ossInfo = json.loads(_f.read())

            _namespace = _ossInfo.get("bom_namespace")
            _bucket = _ossInfo.get("bom_bucket")
            _goldPath = ""
            _clientDomU = ""

            _ossPrefix = f"{_pythonPath} {_exacloudPath}/exagip/src/oss_instance_principal_script.py"
            _ossPrefix = f"{_ossPrefix} download {_namespace} {_bucket} --r1-cert={_exacloudPath}/exabox/kms/combined_r1.crt"

            if aKey == "gold_system":
                _goldPath = f"{_exacloudTmpFolder}/{_bomSystem}"
                _cmd = f"{_ossPrefix} --from={_bomFullSystem} --to={_goldPath}"
                self.mExecuteLocal(_cmd)

            elif aKey == "gold_u01":
                _goldPath = f"{_exacloudTmpFolder}/{_bomU01}"
                _cmd = f"{_ossPrefix} --from={_bomFullU01} --to={_exacloudTmpFolder}/{_bomU01}"
                self.mExecuteLocal(_cmd)

            else:
                raise ValueError(f"Missing {aKey} in bom file")

            _lock = RemoteLock(None, force_host_list=[aHostInfo["domU"]])
            _lockAcquired = False

            try:
                _lock.acquire()
                _lockAcquired = True

                # Calculate udev device
                with connect_to_host(aHostInfo["domU"], get_gcontext()) as _node:

                    _startUdev = 30
                    _foundUdev = False

                    while not _foundUdev and _startUdev < 99:
                        _startUdev += 1

                        _udevStr = f":{_startUdev//10}:{_startUdev%10}: "
                        _mountedHdd = self.mGetUdevPath(_node, _udevStr)

                        if not _mountedHdd:
                            _foundUdev = True

                    _udev = [0, 0, _startUdev//10, _startUdev%10]
                    ebLogInfo(f"Found free udev: {_udev}")

                if not _foundUdev:
                    raise ValueError(f"No free SCSI udev address found")

                with connect_to_host(aHostInfo["dom0"], get_gcontext()) as _node:

                    _domUMap = self.mCreateNatDomUToClientDomUMapping(_node)
                    _clientDomU = _domUMap[aHostInfo["domU"]]

                    # Create workdir folder
                    _cmd = f"/bin/mkdir -p {_workdir}"
                    node_exec_cmd_check(_node, _cmd)

                    # Create attach XML
                    _devTarget = self.mGetNextDeviceDom0(_node, _clientDomU)

                    _deviceXml = f"""
                        <disk type='block' device='disk'>
                            <driver name='qemu' type='raw' cache='none' io='native'/>
                            <source dev='/dev/exc/{aHostInfo[aKey]}'/>
                            <backingStore/>
                            <target dev='{_devTarget}' bus='scsi'/>
                            <address type='drive' controller='{_udev[0]}' bus='{_udev[1]}' target='{_udev[2]}' unit='{_udev[3]}'/>
                        </disk>
                    """

                    _targetFile = f"{_uuid}.xml"

                    with open(f"{_exacloudTmpFolder}/{_targetFile}", "w") as _f:
                        _f.write(_deviceXml)

                    ebLogInfo(f"Print XML: {_deviceXml}")
                    _node.mCopyFile(f"{_exacloudTmpFolder}/{_targetFile}", f"{_workdir}/{_targetFile}")

                    # Attach the XML
                    _cmd = f"virsh attach-device {_clientDomU} /opt/exacloud/{_uuid}/{_targetFile} --live"
                    node_exec_cmd_check(_node, _cmd)
                    _attachDone = True

            finally:
                if _lockAcquired:
                    _lock.release()

            with connect_to_host(aHostInfo["domU"], get_gcontext()) as _node:

                # Create workdir folder
                _cmd = f"/bin/mkdir -p {_workdir}"
                node_exec_cmd_check(_node, _cmd)

                # Copy gold image
                _domUGoldPath = f"{_workdir}/{os.path.basename(_goldPath)}"
                _node.mCopyFile(_goldPath, _domUGoldPath)
                _mountedHdd = self.mGetUdevPath(_node, _udevStr)

                # Performing the dd
                _cmd = f"pbzip2 -t {_domUGoldPath}"
                node_exec_cmd_check(_node, _cmd)

                _cmd = f"pbzip2 -dc {_domUGoldPath} | dd of={_mountedHdd} bs=64K"
                node_exec_cmd_check(_node, _cmd)

                _cmd = f"/bin/echo -e 'Fix\nFix' | parted ---pretend-input-tty {_mountedHdd} print"
                _, _out, _ = node_exec_cmd_check(_node, _cmd)
                ebLogInfo(f"Parted: {_out.strip()}")

        finally:

            if _attachDone:
                with connect_to_host(aHostInfo["dom0"], get_gcontext()) as _node:
                    _cmd = f"virsh detach-disk {_clientDomU} /dev/exc/{aHostInfo[aKey]} --live"
                    node_exec_cmd_check(_node, _cmd)

            _cmd = f"/bin/rm -rf {_exacloudTmpFolder}"
            self.mExecuteLocal(_cmd)

            with connect_to_host(aHostInfo["dom0"], get_gcontext()) as _node:
                _cmd = f"/bin/rm -rf {_workdir}"
                node_exec_cmd_check(_node, _cmd)

            with connect_to_host(aHostInfo["domU"], get_gcontext()) as _node:
                _cmd = f"/bin/rm -rf {_workdir}"
                node_exec_cmd_check(_node, _cmd)


    def mExecute(self):

        _rc = 0
        _response = {}

        ebLogTrace("Entering mImageBaseRestore")
        _bomSpec = {}

        if "image_base_bom" in self.payload.jsonconf:
            _bomSpec = self.payload.jsonconf["image_base_bom"]

        if _bomSpec:

            # Fetch host info from payload
            _hostInfoList = []

            for _jNode in self.payload.jsonconf["customer_network"]["nodes"]:
                _hostNode = {}

                if "volumes" in _jNode:
                    for _volume in _jNode["volumes"]:

                        if "domU" not in _hostNode:
                            if "domU" in _volume and _volume["domU"]:
                                if not is_valid_fqdn(_volume["domU"]):
                                    raise ExacloudRuntimeError(0x0825, 0xA, f"FQDN {_volume['domU']} is an invalid hostname")
                                _hostNode["domU"] = _volume["domU"]

                        if "dom0" not in _hostNode:
                            if "attach_host" in _volume and "dom0" in _volume:
                                if _volume["dom0"] in _volume["attach_host"]:
                                    if not is_valid_fqdn(_volume["attach_host"]):
                                        raise ExacloudRuntimeError(0x0825, 0xA, f"FQDN {_volume['attach_host']} is an invalid hostname")
                                    _hostNode["dom0"] = _volume["attach_host"]
                                else:
                                    if not is_valid_fqdn(_volume["dom0"]):
                                        raise ExacloudRuntimeError(0x0825, 0xA, f"FQDN {_volume['dom0']} is an invalid hostname")
                                    _hostNode["dom0"] = _volume["dom0"]

                        if "gold_system" not in _hostNode:
                            if "volumetype" in _volume and _volume["volumetype"] == "system":
                                _hostNode["gold_system"] = os.path.basename(_volume["volumedevicepath"])

                        if "gold_u01" not in _hostNode:
                            if "volumetype" in _volume and _volume["volumetype"] == "u01":
                                _hostNode["gold_u01"] = os.path.basename(_volume["volumedevicepath"])

                _hostInfoList.append(_hostNode)

            for _hostInfo in _hostInfoList:

                self.mCopyVolume(_bomSpec, _hostInfo, "gold_system")
                self.mCopyVolume(_bomSpec, _hostInfo, "gold_u01")

        return (0, _response)

# end of the file
