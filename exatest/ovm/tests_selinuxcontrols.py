#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_selinuxcontrols.py /main/1 2026/02/02 09:28:33 aypaul Exp $
#
# tests_selinuxcontrols.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_selinuxcontrols.py - Unit tests for ebSelinuxControls
#
#    DESCRIPTION
#      Exercises SELinux update helpers using ExaTest harness constructs.
#
#    NOTES
#      Tests rely on ebTestClucontrol base for request + node scaffolding.
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      03/30/26 - Adding unit tests for aypaul_bug-38277507
#    aypaul      01/29/26 - Adding unit tests for selinux implementation

import io
import warnings
import copy
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, Mock

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.selinuxcontrols import SELINUX_UPDATE_SUCCESS, ebSelinuxControls
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo

SELINUX_PAYLOAD = {
    "se_linux" :  
    {
        "infraComponent" :
            [
                {
                    "mode": "permissive",
                    "component": "dom0",
                    "targetComponentName": "all",
                    "policy": ""
                }
            ]
        }
    }

SELINUX_FULL_PAYLOAD = {
    "se_linux" :  
    {
        "infraComponent" :
            [
                {
                    "mode": "permissive",
                    "component": "dom0",
                    "targetComponentName": "all",
                    "policy": []
                },
                {
                    "mode": "enforcing",
                    "component": "cell",
                    "targetComponentName": "all",
                    "policy": []
                },
                {
                    "mode": "disabled",
                    "component": "domu",
                    "targetComponentName": "all",
                    "policy": []
                }
            ]
        }
    }


class ebTestSelinuxControls(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestSelinuxControls, self).setUpClass(aGenerateDatabase=True, aEnableUTFlag=True, aUseOeda = False)
        warnings.filterwarnings("ignore")
        self._db = ebGetDefaultDB()

    def mCreateSelinuxControllerInstance(self):
        
        _selinux_controller = ebSelinuxControls(self.mGetClubox())
        return _selinux_controller

    def test_mGetSELinuxMode(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebSelinuxControls.mGetSELinuxMode")
        selinuxinstance = self.mCreateSelinuxControllerInstance()
        self.assertEqual(selinuxinstance.mGetSELinuxMode("dom0"), None)

        fullOptions = self.mGetClubox().mGetArgsOptions()
        fullOptions.jsonconf = {"se_linux" : "permissive"}
        self.assertEqual(selinuxinstance.mGetSELinuxMode("dom0"), None)

        fullOptions.jsonconf = copy.deepcopy(SELINUX_PAYLOAD)
        self.assertEqual(selinuxinstance.mGetSELinuxMode("dom0"), "permissive")
        ebLogInfo("Running unit test on ebSelinuxControls.mGetSELinuxMode succeeded.")

    def test_mProcessSELinuxUpdate(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebSelinuxControls.mProcessSELinuxUpdate")
        selinuxinstance = self.mCreateSelinuxControllerInstance()

        self.assertRaises(ExacloudRuntimeError, selinuxinstance.mProcessSELinuxUpdate, None)

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.jsonconf = {"se_linux" : "permissive"}
        self.assertRaises(ExacloudRuntimeError, selinuxinstance.mProcessSELinuxUpdate, fullOptions)

        with patch('exabox.ovm.selinuxcontrols.ebSelinuxControls.mUpdateListWithDomainNameIfRequired', return_value=True),\
             patch('exabox.ovm.selinuxcontrols.ebSelinuxControls.mSetSeLinux', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRequestObj', return_value=ebJobRequest('cluctrl.selinuxpolicy_update', {})),\
             patch('exabox.ovm.selinuxcontrols.connect_to_host'):
            fullOptions.jsonconf = copy.deepcopy(SELINUX_FULL_PAYLOAD)
            self.assertEqual(selinuxinstance.mProcessSELinuxUpdate(fullOptions, True), SELINUX_UPDATE_SUCCESS)

        with patch('exabox.ovm.selinuxcontrols.ebSelinuxControls.mUpdateListWithDomainNameIfRequired', return_value=True),\
             patch('exabox.ovm.selinuxcontrols.ebSelinuxControls.mSetSeLinux', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRequestObj', return_value=ebJobRequest('cluctrl.selinuxpolicy_update', {})),\
             patch('exabox.ovm.selinuxcontrols.connect_to_host'):
            fullOptions.jsonconf = copy.deepcopy(SELINUX_PAYLOAD)
            fullOptions.jsonconf["se_linux"]["infraComponent"][0]["targetComponentName"] = {}
            self.assertRaises(ExacloudRuntimeError, selinuxinstance.mProcessSELinuxUpdate, fullOptions, True)

        with patch('exabox.ovm.selinuxcontrols.ebSelinuxControls.mUpdateListWithDomainNameIfRequired', return_value=True),\
             patch('exabox.ovm.selinuxcontrols.ebSelinuxControls.mSetSeLinux', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRequestObj', return_value=ebJobRequest('cluctrl.selinuxpolicy_update', {})),\
             patch('exabox.ovm.selinuxcontrols.connect_to_host'):
            fullOptions.jsonconf = copy.deepcopy(SELINUX_PAYLOAD)
            fullOptions.jsonconf["se_linux"]["infraComponent"][0]["targetComponentName"] = ['scaqab10adm01.us.oracle.com', 'scaqab10adm02.us.oracle.com']
            self.assertEqual(selinuxinstance.mProcessSELinuxUpdate(fullOptions, True), SELINUX_UPDATE_SUCCESS)

        with patch('exabox.ovm.selinuxcontrols.ebSelinuxControls.mUpdateListWithDomainNameIfRequired', return_value=False),\
             patch('exabox.ovm.selinuxcontrols.ebSelinuxControls.mSetSeLinux', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRequestObj', return_value=ebJobRequest('cluctrl.selinuxpolicy_update', {})),\
             patch('exabox.ovm.selinuxcontrols.connect_to_host'):
            fullOptions.jsonconf = copy.deepcopy(SELINUX_PAYLOAD)
            fullOptions.jsonconf["se_linux"]["infraComponent"][0]["targetComponentName"] = ['scaqab10adm01.us.oracle.com', 'scaqab10adm02.us.oracle.com']
            self.assertRaises(ExacloudRuntimeError, selinuxinstance.mProcessSELinuxUpdate, fullOptions, True)

        ebLogInfo("Running unit test on ebSelinuxControls.mProcessSELinuxUpdate succeeded.")


    def test_mUpdateListWithDomainNameIfRequired(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebSelinuxControls.mUpdateListWithDomainNameIfRequired")
        selinuxinstance = self.mCreateSelinuxControllerInstance()
        self.assertEqual(selinuxinstance.mUpdateListWithDomainNameIfRequired(["node1"], ["node1.domain.com"]), True)
        self.assertEqual(selinuxinstance.mUpdateListWithDomainNameIfRequired(["node1"], ["node2.domain.com"]), False)
        ebLogInfo("Running unit test on ebSelinuxControls.mUpdateListWithDomainNameIfRequired succeeded.")

    def test_mSetSeLinux(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebSelinuxControls.mSetSeLinux")
        selinuxinstance = self.mCreateSelinuxControllerInstance()

        rcstatus = selinuxinstance.mSetSeLinux(None, "notavalidselinuxmode")
        self.assertEqual(rcstatus, False)

        mocknode = MagicMock()
        mocknode.mExecuteCmd.return_value = [0,io.StringIO("SELINUX=disabled"),None]
        mocknode.mGetCmdExitStatus.return_value = 0
        rcstatus = selinuxinstance.mSetSeLinux(mocknode, "disabled", "dom0")
        self.assertEqual(rcstatus, False)

        statusinfodict = {}
        mocknode.mExecuteCmdLog.return_value = 0
        mocknode.mExecuteCmd.return_value = [0,io.StringIO("SELINUX=disabled"),None]
        rcstatus = selinuxinstance.mSetSeLinux(mocknode, "enforcing", None, statusinfodict)
        self.assertEqual(rcstatus, True)

        fullOptions = self.mGetClubox().mGetArgsOptions()
        fullOptions.jsonconf = copy.deepcopy(SELINUX_PAYLOAD)
        fullOptions.jsonconf["se_linux"]["dom0_policy"] = ["/folder1/folder2/policyfile1.pp","/folder1/folder2/policyfile2.pp"]
        mocknode.mCopyFile.return_value = 0
        mocknode.mExecuteCmd.return_value = [0,io.StringIO("SELINUX=disabled"),None]
        with patch('os.path.exists', return_value=True):
            rcstatus = selinuxinstance.mSetSeLinux(mocknode, "enforcing", "dom0", statusinfodict)
            self.assertEqual(rcstatus, True)

        ebLogInfo("Running unit test on ebSelinuxControls.mSetSeLinux succeeded.")

    @patch('exabox.ovm.selinuxcontrols.get_gcontext')
    def test_mSetSeLinux_records_operation_status(self, mock_ctx):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebSelinuxControls.mSetSeLinux operation status tracking")

        selinuxinstance = self.mCreateSelinuxControllerInstance()
        _ctx = MagicMock()
        _ctx.mCheckRegEntry.return_value = False
        mock_ctx.return_value = _ctx

        options = selinuxinstance._ebSelinuxControls__ebCluObj.mGetOptions()
        options.jsonconf = {"se_linux": {"dom0_policy": [], "infraComponent": []}}

        mocknode = MagicMock()
        mocknode.mGetHostname.return_value = "host-dom0"
        mocknode.mExecuteCmd.return_value = [0, io.StringIO("SELINUX=disabled"), None]
        mocknode.mExecuteCmdLog.return_value = 0
        mocknode.mCopyFile.return_value = 0
        mocknode.mGetCmdExitStatus.side_effect = [0, 0, 0]

        statusinfo = {}
        with patch('os.path.exists', return_value=False):
            selinuxinstance.mSetSeLinux(mocknode, "permissive", "dom0", statusinfo)

        _status_list = selinuxinstance.mGetSELinuxStatusForClusterOperations()
        self.assertGreaterEqual(len(_status_list), 1)
        _last_status = _status_list[-1]
        self.assertEqual(_last_status["componentType"], "dom0")
        self.assertEqual(_last_status["hostname"], "host-dom0")
        self.assertEqual(_last_status["modeUpdate"], "Success")
        self.assertEqual(_last_status["selinuxStatus"], "permissive")

        ebLogInfo("Running unit test on ebSelinuxControls.mSetSeLinux operation status tracking succeeded.")

    @patch('exabox.ovm.selinuxcontrols.get_gcontext')
    def test_mSetSeLinux_invalid_mode_records_failure(self, mock_ctx):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebSelinuxControls.mSetSeLinux invalid mode tracking")

        selinuxinstance = self.mCreateSelinuxControllerInstance()
        _ctx = MagicMock()
        _ctx.mCheckRegEntry.return_value = False
        mock_ctx.return_value = _ctx

        mocknode = MagicMock()
        mocknode.mGetHostname.return_value = "host-dom0"

        selinuxinstance.mSetSeLinux(mocknode, "invalid", "dom0")

        _status_list = selinuxinstance.mGetSELinuxStatusForClusterOperations()
        self.assertGreaterEqual(len(_status_list), 1)
        _last_status = _status_list[-1]
        self.assertEqual(_last_status["componentType"], "dom0")
        self.assertEqual(_last_status["hostname"], "host-dom0")
        self.assertEqual(_last_status["modeUpdate"], "Failure")
        self.assertEqual(_last_status["selinuxStatus"], "invalid")

        ebLogInfo("Running unit test on ebSelinuxControls.mSetSeLinux invalid mode tracking succeeded.")

    def test_mGetGeneratedSELinuxPolicies(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebSelinuxControls.mGetGeneratedSELinuxPolicies")
        selinuxinstance = self.mCreateSelinuxControllerInstance()
        self.assertRaises(ExacloudRuntimeError, selinuxinstance.mGetGeneratedSELinuxPolicies, None)

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.jsonconf = {"se_linux" : "permissive"}
        self.assertRaises(ExacloudRuntimeError, selinuxinstance.mGetGeneratedSELinuxPolicies, fullOptions)

        fullOptions.jsonconf = copy.deepcopy(SELINUX_PAYLOAD)
        fullOptions.jsonconf["sendall"] = True
        fullOptions.jsonconf["se_linux"]["infraComponent"][0]["targetComponentName"] = ['scaqab10adm01.us.oracle.com', 'scaqab10adm02.us.oracle.com']
        with patch('exabox.ovm.selinuxcontrols.ebGetDefaultDB') as mock_ebGetDefaultDB,\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRequestObj', return_value=ebJobRequest('cluctrl.selinuxpolicy_update', {})):
            mockdb = MagicMock()
            mock_ebGetDefaultDB.return_value = mockdb
            mockdb.mGetAllSELinuxPolicy.return_value=["policy1encodeddata", "policy2encodeddata"]
            self.assertEqual(selinuxinstance.mGetGeneratedSELinuxPolicies(fullOptions), SELINUX_UPDATE_SUCCESS)

        ebLogInfo("Running unit test on ebSelinuxControls.mGetGeneratedSELinuxPolicies succeeded.")

    def test_mGenerateCustomPolicyFileForThisRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebSelinuxControls.mGenerateCustomPolicyFileForThisRequest")
        selinuxinstance = self.mCreateSelinuxControllerInstance()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRequestObj', return_value=ebJobRequest('cluctrl.selinuxpolicy_update', {})),\
             patch('exabox.ovm.selinuxcontrols.exaBoxNode.mSetUser'),\
             patch('exabox.ovm.selinuxcontrols.exaBoxNode.mIsConnectable', return_value = True),\
             patch('exabox.ovm.selinuxcontrols.connect_to_host') as mock_connecthost,\
             patch('exabox.ovm.selinuxcontrols.ebGetDefaultDB') as mock_ebGetDefaultDB:
            mocknode = MagicMock()
            connect_cm = mock.MagicMock()
            connect_cm.__enter__.return_value = mocknode
            connect_cm.__exit__.return_value = False
            mock_connecthost.return_value = connect_cm
            mocknode.mFileExists.return_value = False
            mocknode.mFileExists.return_value = False
            selinuxinstance.mGenerateCustomPolicyFileForThisRequest()

            mocknode.mFileExists.return_value = True
            mocknode.mCopyFile.return_value = True
            mocknode.mExecuteCmd.return_value = [0,io.StringIO(""),io.StringIO("a mock error message")]
            mocknode.mGetCmdExitStatus.return_value = 1
            selinuxinstance.mGenerateCustomPolicyFileForThisRequest()

            mocknode.mFileExists.return_value = True
            mocknode.mCopyFile.return_value = True
            mocknode.mExecuteCmd.return_value = [0,io.StringIO("Custom policy file created: /tmp/mockpolicy.pp"),io.StringIO("a mock error message")]
            mocknode.mGetCmdExitStatus.return_value = 0
            mocknode.mReadFile.return_value = b'mock policy contents'
 
            mockdb = MagicMock()
            mock_ebGetDefaultDB.return_value = mockdb
            mockdb.mInsertGeneratedSELinuxPolicy.return_value = True
            selinuxinstance.mGenerateCustomPolicyFileForThisRequest()

        ebLogInfo("Running unit test on ebSelinuxControls.mGenerateCustomPolicyFileForThisRequest succeeded.")

def suite():
    loader = unittest.TestLoader()
    suite_obj = unittest.TestSuite()
    for name in loader.getTestCaseNames(ebTestSelinuxControls):
        suite_obj.addTest(ebTestSelinuxControls(name))
    return suite_obj


if __name__ == "__main__":
    unittest.TextTestRunner(failfast=True).run(suite())
