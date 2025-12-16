#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/core/tests_cludispatcher.py /main/4 2024/10/04 21:19:51 avimonda Exp $
#
# tests_cludispatcher.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_cludispatcher.py - Unit test implemented for cludispatcher.py
#
#    DESCRIPTION
#      Implemented unit test for the file named cludispatcher.py
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    09/16/24 - Enhancement Request 36775120 - EXACLOUD TIMEOUT
#                           MUST BE CALCULATED BASED ON THE PATCH OPERATION
#                           AND TARGET TYPE
#    sdevasek    07/10/24 - ENH 36752768 - PROVIDE SPECIFIC ERROR CODE WHEN
#                           BUNDLE IS MISSING ON THE CPS NODE INSTEAD OF
#                           GENERIC DISPATCHER EXCEPTION ERROR CODE
#    avimonda    05/16/24 - Enhancement Request 36569957 - AGENT UNAVAILABLE
#                           RESOURCES ERROR IS MISLEADING AS FILENOTFOUNDERROR
#    avimonda    01/03/24 - Bug 36148893: Create unit test for the
#                           respective fix.
#    avimonda    01/03/24 - Creation
#
import unittest
from unittest.mock import patch
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.infrapatching.utils.utility import mGetInfraPatchingConfigParam
from exabox.infrapatching.core.cludispatcher import ebCluPatchDispatcher
from exabox.core.MockCommand import exaMockCommand

class ebTestCluPatchDispatcher(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"
    EXACLOUD_CHILD_REQUEST_CREATION_FAILED = "0x03010061"
    class DummyManager:
        def __init__(self):
            self.dummy_list = []

        def list(self):
            return self.dummy_list

    class DummyProcess:
        def __init__(self):
            pass

        def start(self):
            pass

    @classmethod
    def setUpClass(self):
        ebLogInfo("Starting classSetUp CellHandler")
        super(ebTestCluPatchDispatcher, self).setUpClass(aGenerateDatabase=True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption("repository_root", self.mGetPath(self))
        _cluCtrl = self.mGetClubox(self)
        _cluCtrl._exaBoxCluCtrl__kvm_enabled = True
        ebLogInfo("Ending classSetUp CellHandler")

    @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mLockPatchCmd', return_value = True)
    @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mUpdateStatusFromList')
    @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mParsePatchJson', return_value=(SUCCESS_ERROR_CODE, ""))
    @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mCheckExacloudMnt', return_value = True)
    @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mAddDispatcherError')
    @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mReleasePatchCmd')
    def test_mStartPatchRequestExecution_DispatchToExacloudForCreatingChildFailed(self, mock_mLockPatchCmd, mock_mUpdateStatusFromList, mock_mParsePatchJson, mock_mCheckExacloudMnt, mock_mAddDispatcherError, mock_mReleasePatchCmd):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluPatchDispatcher.mStartPatchRequestExecution")
        _job = ebJobRequest("version", {})
        _options = self.mGetPayload()
        _patch_dispatcher = ebCluPatchDispatcher(aJob=_job)
        _rc=_patch_dispatcher.mStartPatchRequestExecution(_options)
        self.assertEqual(_rc, self.EXACLOUD_CHILD_REQUEST_CREATION_FAILED)
        ebLogInfo("Unit test on ebCluPatchDispatcher.mStartPatchRequestExecution executed successfully")

    def test_mDumpCallInformation(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluPatchDispatcher.mDumpCallInformation")
        _job = ebJobRequest("version", {})
        _patch_dispatcher = ebCluPatchDispatcher(aJob=_job)
        _patch_dispatcher._ebCluPatchDispatcher__done_requests = [{'status': 'Done', 'uuid': '00000000-0000-0000-0000-000000000000', 'error': '503', 'error_str': 'Exacloud is unable to process the request due to system resources overload. Please retry after sometime.', 'non_ibswitch': True, 'cluster_id': '1', 'fabric_ptr': '<exabox.infrapatching.core.ibfabricpatch.IBFabricPatch object at 0x7f3ab03bcac8>'}]
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_target = ['domu']
        _patch_dispatcher._ebCluPatchDispatcher__cluster_key = 'scaqan10adm07scaqan10dv0701scaqan10adm08scaqan10dv0801'
        _patch_dispatcher.mDumpCallInformation()
        self.assertEqual(_patch_dispatcher._ebCluPatchDispatcher__done_requests, [{'status': 'Done', 'uuid': '00000000-0000-0000-0000-000000000000', 'error': '503', 'error_str': 'Exacloud is unable to process the request due to system resources overload. Please retry after sometime.', 'non_ibswitch': True, 'cluster_id': '1', 'fabric_ptr': '<exabox.infrapatching.core.ibfabricpatch.IBFabricPatch object at 0x7f3ab03bcac8>'}])
        ebLogInfo("Unit test on ebCluPatchDispatcher.mDumpCallInformation executed successfully")

    def test_mCalculatePatchOperationTimeout_NonRolling_Patch(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluPatchDispatcher.mCalculatePatchOperationTimeout_NonRolling_Patch")
        _job = ebJobRequest("version", {})
        _options = self.mGetPayload()
        _options.jsonconf['StorageNodeList'] = ["1cell", "2cell", "3cell", "4cell", "5cell", "6cell", "7cell"] 
        _patch_dispatcher = ebCluPatchDispatcher(aJob=_job)
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_target = ['cell']
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_style = 'non-rolling'
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_operation = 'patch'
        _rc=_patch_dispatcher.mCalculatePatchOperationTimeout(_options)
        self.assertEqual(_rc, 86400)
        ebLogInfo("Unit test on ebCluPatchDispatcher.mCalculatePatchOperationTimeout_NnonRolling_Patch executed successfully")

    def test_mCalculatePatchOperationTimeout_Rolling_Precheck(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluPatchDispatcher.mCalculatePatchOperationTimeout_Rolling_Precheck")
        _job = ebJobRequest("version", {})
        _options = self.mGetPayload()
        _options.jsonconf['StorageNodeList'] = ["1cell", "2cell", "3cell", "4cell", "5cell", "6cell", "7cell"] 
        _patch_dispatcher = ebCluPatchDispatcher(aJob=_job)
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_target = ['cell']
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_style = 'rolling'
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_operation = 'patch_prereq_check'
        _rc=_patch_dispatcher.mCalculatePatchOperationTimeout(_options)
        self.assertEqual(_rc, 86400)
        ebLogInfo("Unit test on ebCluPatchDispatcher.mCalculatePatchOperationTimeout_Rolling_Precheck executed successfully")

    def test_mCalculatePatchOperationTimeout_Rolling_Patch(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluPatchDispatcher.mCalculatePatchOperationTimeout_Rolling_Patch")
        _job = ebJobRequest("version", {})
        _options = self.mGetPayload()
        _options.jsonconf['StorageNodeList'] = ["1cell", "2cell", "3cell", "4cell", "5cell", "6cell", "7cell"] 
        _patch_dispatcher = ebCluPatchDispatcher(aJob=_job)
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_target = ['cell']
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_style = 'rolling'
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_operation = 'patch'
        _rc=_patch_dispatcher.mCalculatePatchOperationTimeout(_options)
        self.assertEqual(_rc, 169200)
        ebLogInfo("Unit test on ebCluPatchDispatcher.mCalculatePatchOperationTimeout_Rolling_Patch executed successfully")

    def test_mCalculatePatchOperationTimeout_Rolling_Rollback(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluPatchDispatcher.mCalculatePatchOperationTimeout_Rolling_Rollback")
        _job = ebJobRequest("version", {})
        _options = self.mGetPayload()
        _options.jsonconf['StorageNodeList'] = ["1cell", "2cell", "3cell", "4cell", "5cell", "6cell", "7cell"] 
        _patch_dispatcher = ebCluPatchDispatcher(aJob=_job)
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_target = ['cell']
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_style = 'rolling'
        _patch_dispatcher._ebCluPatchDispatcher__dispatcher_operation = 'rollback'
        _rc=_patch_dispatcher.mCalculatePatchOperationTimeout(_options)
        self.assertEqual(_rc, 169200)
        ebLogInfo("Unit test on ebCluPatchDispatcher.mCalculatePatchOperationTimeout_Rolling_Rollback executed successfully")

if __name__ == "__main__":
    unittest.main()

