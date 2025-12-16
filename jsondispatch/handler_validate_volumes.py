#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_validate_volumes.py /main/1 2025/10/10 12:43:53 prsshukl Exp $
#
# handler_validate_volumes.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      handler_validate_volumes.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    08/20/25 - Enh 38180284 - EXADB-XS -> VALIDATE_VOLUME AT THE
#                           HOST/DOM0 LEVEL
#    prsshukl    08/20/25 - Creation
#

import os
from typing import Tuple

from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check
from exabox.core.Error import ebError, ExacloudRuntimeError

class ValidateVolumesHandler(JDHandler):

    # EXIT CODES
    SUCCESS = 0

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/validatevolumes.json"))

    def mExtractDevicePath(self, output):
        devices = []
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Device:"):
                # Split on comma, take first part, then remove "Device: "
                device = line.split(",")[0].replace("Device:", "").strip()
                devices.append(device)
        return devices

    def mCompareDevicePath(self, aDom0DeviceList, aPayloadDeviceList):

        _unattached_edv_device_path = []

        for _item in aPayloadDeviceList:
            if _item not in aDom0DeviceList:
                _unattached_edv_device_path.append(_item)

        return _unattached_edv_device_path

    def mBuildResponse(self, attached_vols=[], unattached_vols=[], stale_vols=[]):
            
        response = {"volumes": []}

        # Add attached
        for vol in attached_vols:
            response["volumes"].append({"volumename": vol, "status": "attached"})

        # Add unattached
        for vol in unattached_vols:
            response["volumes"].append({"volumename": vol, "status": "unattached"})

        # Add stale
        for vol in stale_vols:
            response["volumes"].append({"volumename": vol, "status": "stale"})

        ebLogTrace(f"response: {response}")

        return response

    def mReturnUnattachedStaleVolumelists(self, aNode, vol_list):

        _dom0_unattached_vol_list = []
        _dom0_stale_vol_list = []
        _node = aNode
        _edvutil_cmd = node_cmd_abs_path_check(node=_node, cmd="edvutil", sbin=True)
        for vol in vol_list:
            _cmd = f"{_edvutil_cmd} volinfo -l {vol}"
            _, _out, _err = _node.mExecuteCmd(_cmd, aTimeout=5)
            _val = "No such device"
            if _val in _out:
                _dom0_stale_vol_list.append(vol)
            else:
                _dom0_unattached_vol_list.append(vol)
        
        return _dom0_unattached_vol_list, _dom0_stale_vol_list
            

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver func to check if the volumes are attached to the dom0 and if there are any stale
        volumes in the dom0

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """

        _rc = ValidateVolumesHandler.SUCCESS
        response = {"volumes": []}

        _clucontrol = exaBoxCluCtrl(get_gcontext())
        aOptions = self.mGetOptions()

        if not aOptions or "hostname" not in aOptions.jsonconf or "edvvolume" not in aOptions.jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, f'Missing hostname and edvvolume list details in the payload')

        _dom0 = aOptions.jsonconf["hostname"]
        aEdvVolumeList = aOptions.jsonconf["edvvolume"]

        _edvVolume_list = aEdvVolumeList
        if _edvVolume_list:
            for i in range(len(_edvVolume_list)):
                _edvVolume_list[i] = "/dev/exc/" + _edvVolume_list[i]

        _volstr = "|".join(_edvVolume_list)

        with connect_to_host(_dom0, get_gcontext()) as _node:
            _edvutil_cmd = node_cmd_abs_path_check(node=_node, cmd="edvutil", sbin=True)
            _cmd = f"{_edvutil_cmd} volinfo -l | grep {_volstr}"
            _, _out, _err = _node.mExecuteCmd(_cmd, aTimeout=300)
            _rc = _node.mGetCmdExitStatus()
            if _rc == 0:
                ebLogInfo(f'Execution of validate_volumes operation was successful.')
                _dom0_attached_device_list = self.mExtractDevicePath(_out)
                _dom0_missing_device_list = self.mCompareDevicePath(_dom0_attached_device_list, _edvVolume_list)

                _dom0_unattached_device_list, _dom0_stale_device_list = self.mReturnUnattachedStaleVolumelists(_node, _dom0_missing_device_list)

                _response = self.mBuildResponse(_dom0_attached_device_list, unattached_vols= _dom0_unattached_device_list, stale_vols= _dom0_stale_device_list)
            else:
                _msg = f'Execution of validate_volumes operation Failed with _rc status {_rc} and Error: {_err}'
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

        return _rc, _response



