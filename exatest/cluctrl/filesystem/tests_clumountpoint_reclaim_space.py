#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/filesystem/tests_clumountpoint_reclaim_space.py /main/4 2025/11/04 06:25:42 aararora Exp $
#
# tests_clumountpoint_reclaim_space.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clumountpoint_reclaim_space.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    10/29/25 - Bug 38591105: Read grid version using gridVersion
#                           from payload
#    aararora    08/28/25 - ER 38335598: Address additional requirement for
#                           reclaiming mountpoint space
#    aararora    11/08/23 - Bug 35824846: Unit test for file clumountpoint_reclaim_space.py
#    aararora    11/08/23 - Creation
#
import unittest

from unittest.mock import patch

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.ovm.hypervisorutils import HVIT_XEN, HVIT_KVM
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.filesystem.clumountpoint_reclaim_space import ebCluMountpointReclaimSpace

PAYLOAD = {
        "mountpoint": "/u01/app/19.0.0.0/grid",
        "gridVersion": "19.25.0.0.241015"
}

PAYLOAD_ERROR_MISSING_PARAM = {
    "mountpoint": "/u01/app/19.0.0.0/grid"
}

PAYLOAD_ERROR_PARAM_EMPTY = {
        "mountpoint": "/u01/app/19.0.0.0/grid",
        "gridVersion": ""
}

DISK = """
['file:/OVS/Repositories/f4d9b4cce8cc47ce8d2e551490dbc7cd/VirtualDisks/fc12d5a09af849d49fda801f640fad00.img,xvda,w',
'file:/OVS/Repositories/f4d9b4cce8cc47ce8d2e551490dbc7cd/VirtualDisks/92d9f4feee1740a3bec29e369156dda9.img,xvdb,w',
'file:/OVS/Repositories/f4d9b4cce8cc47ce8d2e551490dbc7cd/VirtualDisks/b7ab0e20947c4af9893d79e68d25b9c8.img,xvdc,w',
'file:///EXAVMIMAGES/GuestImages/scaqab10adm08vm07.us.oracle.com/u02_extra.img,xvdd,w',
'file:///EXAVMIMAGES/GuestImages/scaqab10adm08vm07.us.oracle.com/fs_resize_2023-10-31_15-24-18.img,xvde,w',
'file:///EXAVMIMAGES/GuestImages/scaqab10adm08vm07.us.oracle.com/fs_resize_2023-10-31_15-24-30.img,xvdf,w',
'file:///EXAVMIMAGES/GuestImages/scaqab10adm08vm07.us.oracle.com/fs_resize_2023-10-31_15-33-06.img,xvdg,w']
"""

class IOObject(object):
    def __init__(self, value):
        self.io = value

    def read(self):
        return self.io

    def readlines(self):
        return self.io

class cfgMock(object):
    def __init__(self):
        self.cfg = {"disk": DISK}

    def mGetValue(self, aParam):
        return self.cfg[aParam]

    def mSetValue(self, aParam, aValue):
        self.cfg[aParam] = aValue

    def mRawConfig(self):
        return str(self.cfg)

class exaBoxOVMCtrlMock(object):
    def __init__(self, aCtx=None, aNode=None):
        self.aCtx=aCtx
        self.aNode=aNode

    def mReadRemoteCfg(aDOMU):
        pass

    def mGetOVSVMConfig(aDOMU):
        _cfg = cfgMock()
        return _cfg

class testOptions(object): pass

class ebTestCluMountpointReclaimSpace(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluMountpointReclaimSpace, self).setUpClass(False,False)
        self._cluctrl = self.mGetClubox(self)
    
    def test_mPerformPayloadValidations(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluMountpointReclaimSpace.mPerformPayloadValidations.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _mountpoint_reclaim_space.mPerformPayloadValidations(PAYLOAD)

    def test_mPerformPayloadValidationsError(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario unit test on ebCluMountpointReclaimSpace.mPerformPayloadValidations. Payload not valid.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        with self.assertRaises(ExacloudRuntimeError):
            _mountpoint_reclaim_space.mPerformPayloadValidations({})

    def test_mPerformPayloadValidationsErrorMissingParam(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario unit test on ebCluMountpointReclaimSpace.mPerformPayloadValidations. Payload missing one of the parameter.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        with self.assertRaises(ExacloudRuntimeError):
            _mountpoint_reclaim_space.mPerformPayloadValidations(PAYLOAD_ERROR_MISSING_PARAM)

    def test_mPerformPayloadValidationsErrorParamEmpty(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario unit test on ebCluMountpointReclaimSpace.mPerformPayloadValidations. One of the parameter in payload is empty.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        with self.assertRaises(ExacloudRuntimeError):
            _mountpoint_reclaim_space.mPerformPayloadValidations(PAYLOAD_ERROR_PARAM_EMPTY)

    def test_mCheckPathUsed(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluMountpointReclaimSpace.mCheckPathUsed.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _node = exaBoxNode(get_gcontext())
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        with patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(IOObject("stdin"), IOObject("0"), IOObject("stderr"))):
             _mountpoint_reclaim_space.mCheckPathUsed(_node, PAYLOAD["mountpoint"], _domu)

    def test_mCheckPathUsedError(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario unit test on ebCluMountpointReclaimSpace.mCheckPathUsed.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _node = exaBoxNode(get_gcontext())
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        with patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(IOObject("stdin"), IOObject("2"), IOObject("stderr"))),\
             self.assertRaises(ExacloudRuntimeError):
             _mountpoint_reclaim_space.mCheckPathUsed(_node, PAYLOAD["mountpoint"], _domu)

    def test_mGetDiskUsageOutput(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluMountpointReclaimSpace.mGetDiskUsageOutput.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _node = exaBoxNode(get_gcontext())
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        with patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(IOObject("stdin"), IOObject("0"), IOObject("stderr"))):
             _mountpoint_reclaim_space.mGetDiskUsageOutput(_node, PAYLOAD["mountpoint"], _domu)

    def test_mGetDiskUsageOutputError(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario unit test on ebCluMountpointReclaimSpace.mGetDiskUsageOutput.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _node = exaBoxNode(get_gcontext())
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        with patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(IOObject("stdin"), IOObject(""), IOObject("stderr"))):
             _mountpoint_reclaim_space.mGetDiskUsageOutput(_node, PAYLOAD["mountpoint"], _domu)

    def test_mRemoveFstabEntry(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluMountpointReclaimSpace.mRemoveFstabEntry.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _node = exaBoxNode(get_gcontext())
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        with patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmdLog"),\
             patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0):
             _mountpoint_reclaim_space.mRemoveFstabEntry(_node, PAYLOAD["mountpoint"], _domu)

    def test_mRemoveFstabEntryError(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario unit test on ebCluMountpointReclaimSpace.mRemoveFstabEntry.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _node = exaBoxNode(get_gcontext())
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        with patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmdLog"),\
             patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=1):
             _mountpoint_reclaim_space.mRemoveFstabEntry(_node, PAYLOAD["mountpoint"], _domu)

    def test_mRemoveGridImgFile(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluMountpointReclaimSpace.mRemoveGridImgFile.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _node = exaBoxNode(get_gcontext())
        _dom0 = self._cluctrl.mReturnDom0DomUPair()[0][0]
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        with patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmdLog"),\
             patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0):
             _mountpoint_reclaim_space.mRemoveGridImgFile(_node, _domu, _dom0, "19.0.0.0")

    def test_mRemoveGridImgFileError(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario unit test on ebCluMountpointReclaimSpace.mRemoveGridImgFile.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _node = exaBoxNode(get_gcontext())
        _dom0 = self._cluctrl.mReturnDom0DomUPair()[0][0]
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        with patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmdLog"),\
             patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=1):
             _mountpoint_reclaim_space.mRemoveGridImgFile(_node, _domu, _dom0, "19.0.0.0")

    def test_mRemoveDeviceEntryVMCfg(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluMountpointReclaimSpace.mRemoveDeviceEntryVMCfg.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _node = exaBoxNode(get_gcontext())
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        with patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.exaBoxOVMCtrl", return_value=exaBoxOVMCtrlMock),\
             patch("exabox.core.Node.exaBoxNode.mCopyFile"):
            _mountpoint_reclaim_space.mRemoveDeviceEntryVMCfg(_node, _domu, "xvdb")

    def test_mExecuteXenSteps(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluMountpointReclaimSpace.mExecuteXenSteps.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _dom0 = self._cluctrl.mReturnDom0DomUPair()[0][0]
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        _rc_status = {}
        with patch("exabox.core.Node.exaBoxNode.mConnect"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mCheckPathUsed"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(IOObject("stdin"), IOObject("xvdb"), IOObject("stderr"))),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mRemoveFstabEntry"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mGetDiskUsageOutput", return_value="12G  /u01/app/19.0.0.0/grid"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmdLog"),\
             patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mRemoveDeviceEntryVMCfg"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mRemoveGridImgFile"):
             _mountpoint_reclaim_space.mExecuteXenSteps(_dom0, _domu, PAYLOAD["mountpoint"], "19.0.0.0", _rc_status)

    def test_mExecuteKVMSteps(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluMountpointReclaimSpace.mExecuteKVMSteps.")
        _options = self.mGetPayload()
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        _dom0 = self._cluctrl.mReturnDom0DomUPair()[0][0]
        _domu = self._cluctrl.mReturnDom0DomUPair()[0][1]
        _rc_status = {}
        with patch("exabox.core.Node.exaBoxNode.mConnect"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mCheckPathUsed"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(IOObject("stdin"), IOObject("xvdb  /u01/app/19.0.0.0/grid"), IOObject("stderr"))),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mRemoveFstabEntry"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mGetDiskUsageOutput", return_value="12G  /u01/app/19.0.0.0/grid"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmdLog"),\
             patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mRemoveDeviceEntryVMCfg"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mRemoveGridImgFile"):
             _mountpoint_reclaim_space.mExecuteKVMSteps(_dom0, _domu, PAYLOAD["mountpoint"], "19.0.0.0", _rc_status)

    def test_mReclaimMountpointSpace(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluMountpointReclaimSpace.mReclaimMountpointSpace.")
        _options = self.mGetPayload()
        _options.jsonconf = PAYLOAD
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        with patch("exabox.core.Node.exaBoxNode.mConnect"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mPerformPayloadValidations"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.getTargetHVIType"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mExecuteKVMSteps"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mExecuteXenSteps"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(IOObject("stdin"), IOObject("0"), IOObject("stderr"))):
             _mountpoint_reclaim_space.mReclaimMountpointSpace()

    def test_mReclaimMountpointSpaceError1(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario 1 unit test on ebCluMountpointReclaimSpace.mReclaimMountpointSpace.")
        _options = self.mGetPayload()
        _options.jsonconf = PAYLOAD
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        with patch("exabox.core.Node.exaBoxNode.mConnect"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mPerformPayloadValidations"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.getTargetHVIType", return_value=HVIT_KVM),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(IOObject("stdin"), IOObject("0"), IOObject("stderr"))),\
             self.assertRaises(ExacloudRuntimeError):
             _mountpoint_reclaim_space.mReclaimMountpointSpace()

    def test_mReclaimMountpointSpaceError2(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario 2 unit test on ebCluMountpointReclaimSpace.mReclaimMountpointSpace.")
        _options = self.mGetPayload()
        _options.jsonconf = PAYLOAD
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        with patch("exabox.core.Node.exaBoxNode.mConnect"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mPerformPayloadValidations"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.getTargetHVIType"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mExecuteKVMSteps"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mExecuteXenSteps"),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(IOObject("stdin"), IOObject("1"), IOObject("stderr"))),\
             self.assertRaises(ExacloudRuntimeError):
             _mountpoint_reclaim_space.mReclaimMountpointSpace()

    def test_mReclaimMountpointSpaceSuccess2(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario 2 unit test on ebCluMountpointReclaimSpace.mReclaimMountpointSpace.")
        _options = self.mGetPayload()
        _options.jsonconf = PAYLOAD
        _mountpoint_reclaim_space = ebCluMountpointReclaimSpace(self._cluctrl, _options)
        with patch("exabox.core.Node.exaBoxNode.mConnect"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.node_cmd_abs_path_check"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.ebCluMountpointReclaimSpace.mPerformPayloadValidations"),\
             patch("exabox.ovm.filesystem.clumountpoint_reclaim_space.getTargetHVIType", return_value=HVIT_KVM),\
             patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", side_effect=[0, 0, 0, 0]),\
             patch("exabox.core.Node.exaBoxNode.mExecuteCmd", side_effect=[(IOObject("stdin"), IOObject("0"), IOObject("stderr")),
                   (IOObject("stdin"), IOObject("0"), IOObject("stderr")), (IOObject("stdin"), IOObject("0 1"), IOObject("stderr"))]):
             _mountpoint_reclaim_space.mReclaimMountpointSpace()

if __name__ == '__main__':
    unittest.main()