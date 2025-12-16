#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_createstorage.py /main/2 2025/08/25 06:17:10 pbellary Exp $
#
# tests_cs_createstorage.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_createstorage.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    03/19/25 - Bug 37508799: Optimize call to mValidateGridDisks -
#                           parallel execution on cells
#    aararora    03/19/25 - Creation
#
import unittest
import copy
from unittest.mock import patch, MagicMock

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.cs_createstorage import csCreateStorage
from exabox.ovm.csstep.cs_util import csUtil

class testOptions(object): pass

class ebTestCSCreateStorage(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCSCreateStorage, self).setUpClass(aGenerateDatabase=True)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mValidateGridDisks", return_value=0)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mFetchOedaStep')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCellConfig')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCellAssertNormalStatus')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateStatusCS')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReleaseRemoteLock')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAcquireRemoteLock')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCellsServicesUp', return_value=False)
    @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDeleteCloudUser')
    def test_doExecute(self, mock_mDeleteCloudUser, mock_mExecuteOEDAStep, mock_mCheckCellsServicesUp, mock_mAcquireRemoteLock,
                         mock_mReleaseRemoteLock, mock_mUpdateStatusCS, mock_mCellAssertNormalStatus, mock_mCheckCellConfig,
                         mock_mFetchOedaStep, mock_mValidateGridDisks):
      _ebox = self.mGetClubox()
      _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
      _step_list = ["ESTP_CREATE_STORAGE"]

      _handler = csCreateStorage()
      _handler.doExecute(_ebox, _options, _step_list)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mValidateGridDisks", return_value=0)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCellAssertNormalStatus')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateStatusCS')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReleaseRemoteLock')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAcquireRemoteLock')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCellsServicesUp', return_value=False)
    @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDeleteCloudUser')
    def test_undoExecute(self, mock_mDeleteCloudUser, mock_mExecuteOEDAStep, mock_mCheckCellsServicesUp, mock_mAcquireRemoteLock,
                         mock_mReleaseRemoteLock, mock_mUpdateStatusCS, mock_allCellDisksAreNormal, mock_mValidateGridDisks):
      _ebox = self.mGetClubox()
      _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
      _step_list = ["ESTP_CREATE_STORAGE"]

      _handler = csCreateStorage()
      _handler.undoExecute(_ebox, _options, _step_list)

    def test_mParallelValidateGriddisks(self):
        ebLogInfo("")
        ebLogInfo("Running success/failure scenario unit test on csCreateStorage.mParallelValidateGriddisks.")

        csCreateStorageInstance = csCreateStorage()
        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mValidateGridDisks", return_value=0):
            csCreateStorageInstance.mParallelValidateGriddisks(self.mGetClubox())
        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mValidateGridDisks", return_value=1):
            with self.assertRaises(ExacloudRuntimeError) as ex:
                csCreateStorageInstance.mParallelValidateGriddisks(self.mGetClubox())


if __name__ == '__main__':
    unittest.main() 