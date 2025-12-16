#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exabasedb/tests_cs_prevmchecks.py /main/1 2025/11/25 05:03:58 prsshukl Exp $
#
# tests_cs_prevmchecks.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_prevmchecks.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/24/25 - Creation
#

import json
import unittest
from unittest import mock
import warnings
import os, re, io
import sys
from io import StringIO
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, Mock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogWarn, ebLogDebug, ebLogTrace
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.network.Connection import exaBoxConnection
from exabox.ovm.csstep.exabasedb.cs_prevmchecks import csPreVMChecks
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.cluexascale import ebCluExaScale


class test_csPreVMChecks(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(test_csPreVMChecks, cls).setUpClass(aGenerateDatabase=True, aEnableUTFlag=False)
        warnings.filterwarnings("ignore")

    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ebCluPreChecks')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ImageBOM')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.csUtil')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ebCluExaScale')
    def test_doExecute_success(self, mock_ebCluExaScale, mock_csUtil, mock_ImageBOM, mock_ebCluPreChecks):
        ebLogInfo("Running unit test on csPreVMChecks.doExecute success")
        _cs_prevm_checks = csPreVMChecks()
        _mock_ebox = MagicMock()
        _mock_options = MagicMock()
        _mock_options.jsonconf = {"isClone": "false"}
        _mock_steplist = MagicMock()

        # Mock the dependencies
        mock_pchecks = mock_ebCluPreChecks.return_value
        mock_pchecks.mVMPreChecks.return_value = False
        mock_pchecks.mFetchHardwareAlerts.return_value = True

        mock_image_bom = mock_ImageBOM.return_value
        mock_image_bom.mIsSubStepExecuted.return_value = False

        mock_csu = mock_csUtil.return_value

        # Mock ebox methods
        _mock_ebox.mUpdateStatus = MagicMock()
        _mock_ebox.mLogStepElapsedTime = MagicMock()

        # Execute
        _cs_prevm_checks.doExecute(_mock_ebox, _mock_options, _mock_steplist)

        # Assertions
        mock_pchecks.mVMPreChecks.assert_called_once()
        mock_pchecks.mFetchHardwareAlerts.assert_called_once()
        _mock_ebox.mUpdateStatus.assert_called_with('createservice step ESTP_PREVM_CHECKS')
        _mock_ebox.mLogStepElapsedTime.assert_called_once()

    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ebCluPreChecks')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ImageBOM')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.csUtil')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ebCluExaScale')
    def test_doExecute_vm_already_exists(self, mock_ebCluExaScale, mock_csUtil, mock_ImageBOM, mock_ebCluPreChecks):
        ebLogInfo("Running unit test on csPreVMChecks.doExecute VM already exists")
        _cs_prevm_checks = csPreVMChecks()
        _mock_ebox = MagicMock()
        _mock_options = MagicMock()
        _mock_options.jsonconf = {"isClone": "false"}
        _mock_steplist = MagicMock()

        # Mock the dependencies
        mock_pchecks = mock_ebCluPreChecks.return_value
        mock_pchecks.mVMPreChecks.return_value = True  # VMs already exist

        mock_image_bom = mock_ImageBOM.return_value
        mock_csu = mock_csUtil.return_value

        # Mock ebox methods
        _mock_ebox.mUpdateStatus = MagicMock()

        # Execute and expect exception
        with self.assertRaises(ExacloudRuntimeError) as cm:
            _cs_prevm_checks.doExecute(_mock_ebox, _mock_options, _mock_steplist)

        self.assertEqual(cm.exception.args[0], 0x0410)

    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ebCluPreChecks')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ImageBOM')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.csUtil')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ebCluExaScale')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.time')
    def test_doExecute_hw_alerts_fail_all_retries(self, mock_time, mock_ebCluExaScale, mock_csUtil, mock_ImageBOM, mock_ebCluPreChecks):
        ebLogInfo("Running unit test on csPreVMChecks.doExecute HW alerts fail all retries")
        _cs_prevm_checks = csPreVMChecks()
        _mock_ebox = MagicMock()
        _mock_options = MagicMock()
        _mock_options.jsonconf = {"isClone": "false"}
        _mock_steplist = MagicMock()

        # Mock the dependencies
        mock_pchecks = mock_ebCluPreChecks.return_value
        mock_pchecks.mVMPreChecks.return_value = False
        mock_pchecks.mFetchHardwareAlerts.return_value = False  # Always fail

        mock_image_bom = mock_ImageBOM.return_value
        mock_image_bom.mIsSubStepExecuted.return_value = False

        mock_csu = mock_csUtil.return_value

        # Mock ebox methods
        _mock_ebox.mUpdateStatus = MagicMock()
        _mock_ebox.mLogStepElapsedTime = MagicMock()

        # Execute and expect exception
        with self.assertRaises(ExacloudRuntimeError) as cm:
            _cs_prevm_checks.doExecute(_mock_ebox, _mock_options, _mock_steplist)

        self.assertEqual(cm.exception.args[0], 0x0390)

    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ebCluPreChecks')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ImageBOM')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.csUtil')
    @patch('exabox.ovm.csstep.exabasedb.cs_prevmchecks.ebCluExaScale')
    def test_doExecute_hw_alerts_retry_success(self, mock_ebCluExaScale, mock_csUtil, mock_ImageBOM, mock_ebCluPreChecks):
        ebLogInfo("Running unit test on csPreVMChecks.doExecute HW alerts retry success")
        _cs_prevm_checks = csPreVMChecks()
        _mock_ebox = MagicMock()
        _mock_options = MagicMock()
        _mock_options.jsonconf = {"isClone": "false"}
        _mock_steplist = MagicMock()

        # Mock the dependencies
        mock_pchecks = mock_ebCluPreChecks.return_value
        mock_pchecks.mVMPreChecks.return_value = False
        # First two calls fail, third succeeds
        mock_pchecks.mFetchHardwareAlerts.side_effect = [False, False, True]

        mock_image_bom = mock_ImageBOM.return_value
        mock_image_bom.mIsSubStepExecuted.return_value = False

        mock_csu = mock_csUtil.return_value

        # Mock ebox methods
        _mock_ebox.mUpdateStatus = MagicMock()
        _mock_ebox.mLogStepElapsedTime = MagicMock()

        # Execute
        _cs_prevm_checks.doExecute(_mock_ebox, _mock_options, _mock_steplist)

        # Assertions
        self.assertEqual(mock_pchecks.mFetchHardwareAlerts.call_count, 3)

    def test_undoExecute(self):
        ebLogInfo("Running unit test on csPreVMChecks.undoExecute")
        _cs_prevm_checks = csPreVMChecks()
        _mock_ebox = MagicMock()
        _mock_options = MagicMock()
        _mock_steplist = MagicMock()

        # Execute
        _cs_prevm_checks.undoExecute(_mock_ebox, _mock_options, _mock_steplist)


if __name__ == '__main__':
    unittest.main()
