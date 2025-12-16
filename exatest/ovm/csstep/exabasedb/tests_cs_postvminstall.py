#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exabasedb/tests_cs_postvminstall.py /main/1 2025/11/25 05:03:58 prsshukl Exp $
#
# tests_cs_postvminstall.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_postvminstall.py - <one-line expansion of the name>
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

import unittest
from unittest.mock import patch, Mock
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.exabasedb.cs_postvminstall import csPostVMInstall
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.bom_manager import ImageBOM

class ebTestCsPostVMInstall(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCsPostVMInstall, cls).setUpClass()

    @patch('exabox.core.Context.get_gcontext')
    @patch('exabox.log.LogMgr.ebLogInfo')
    @patch('exabox.ovm.csstep.exabasedb.cs_postvminstall.time')
    @patch('exabox.ovm.bom_manager.ImageBOM')
    def test_doExecute_atp_secure_listeners(self, mock_ImageBOM, mock_time, mock_ebLogInfo, mock_get_gcontext):
        ebLogInfo("Running unit test for csPostVMInstall.doExecute ATP secure listeners")
        # Mock context
        mock_ctx = Mock()
        mock_get_gcontext.return_value = mock_ctx
        mock_ctx.mCheckConfigOption.side_effect = lambda key, default=None: {'kms_key_id': 'mock_id'}.get(key, default)

        # Mock ImageBOM
        mock_imageBom = Mock()
        mock_ImageBOM.return_value = mock_imageBom
        mock_imageBom.mIsSubStepExecuted.return_value = False

        # Mock ebox
        mock_ebox = self.mGetClubox()
        mock_ebox.mUpdateStatus = Mock()
        mock_ebox.mUpdateStatusCS = Mock()
        mock_ebox.mSetupEbtablesOnDom0 = Mock()
        mock_ebox.mResetClusterSSHKeys = Mock()
        mock_ebox.mPostVMCreatePatching = Mock()
        mock_ebox.mPatchSSHDConfig = Mock()
        mock_ebox.mChangeMinFreeKb = Mock()
        mock_ebox.mSecureDOMUPwd = Mock()
        mock_ebox.mSecureDOMUSsh = Mock()
        mock_ebox.mIsOciEXACC = Mock(return_value=True)
        mock_ebox.isATP = Mock(return_value=True)
        mock_ebox.mATPSecureListeners = Mock()
        mock_ebox.mLogStepElapsedTime = Mock()

        # Mock ebUserUtils
        with patch('exabox.ovm.userutils.ebUserUtils.mPushSecscanKey', Mock()), \
             patch('exabox.ovm.userutils.ebUserUtils.mAddSecscanSshd', Mock()):

            cs_instance = csPostVMInstall()
            options = Mock()
            steplist = Mock()

            # Call doExecute
            cs_instance.doExecute(mock_ebox, options, steplist)

            # Assertions
            mock_ebox.mATPSecureListeners.assert_called_once()

    @patch('exabox.core.Context.get_gcontext')
    @patch('exabox.log.LogMgr.ebLogInfo')
    @patch('exabox.ovm.csstep.exabasedb.cs_postvminstall.time')
    @patch('exabox.ovm.bom_manager.ImageBOM')
    def test_undoExecute_positive_path(self, mock_ImageBOM, mock_time, mock_ebLogInfo, mock_get_gcontext):
        ebLogInfo("Running unit test for csPostVMInstall.undoExecute positive path")
        # Mock context
        mock_ctx = Mock()
        mock_get_gcontext.return_value = mock_ctx
        mock_ctx.mCheckConfigOption.side_effect = lambda key, default=None: {'kms_key_id': 'mock_id'}.get(key, default)

        # Mock ImageBOM
        mock_imageBom = Mock()
        mock_ImageBOM.return_value = mock_imageBom

        # Mock ebox
        mock_ebox = self.mGetClubox()
        mock_ebox.mUpdateStatusCS = Mock()
        mock_ebox.mRunScript = Mock()
        mock_ebox.mLogStepElapsedTime = Mock()
        mock_ebox.mVMImagesShredding = Mock()
        mock_ebox.mGetCmd = Mock(return_value='test_cmd')  # Not in delete commands

        # Mock csUtil
        with patch('exabox.ovm.csstep.cs_util.csUtil.mPreVMDeleteCreatePatching', Mock()):

            cs_instance = csPostVMInstall()
            options = Mock()
            steplist = Mock()

            # Call undoExecute
            cs_instance.undoExecute(mock_ebox, options, steplist)

            # Assertions
            mock_ebox.mRunScript.assert_called_once_with(aType='*', aWhen='pre.vm_delete')
            mock_ebox.mVMImagesShredding.assert_called_once_with(options)

    @patch('exabox.core.Context.get_gcontext')
    @patch('exabox.log.LogMgr.ebLogInfo')
    @patch('exabox.ovm.csstep.exabasedb.cs_postvminstall.time')
    @patch('exabox.ovm.bom_manager.ImageBOM')
    def test_undoExecute_delete_command(self, mock_ImageBOM, mock_time, mock_ebLogInfo, mock_get_gcontext):
        ebLogInfo("Running unit test for csPostVMInstall.undoExecute delete command")
        # Mock context
        mock_ctx = Mock()
        mock_get_gcontext.return_value = mock_ctx
        mock_ctx.mCheckConfigOption.side_effect = lambda key, default=None: {'kms_key_id': 'mock_id'}.get(key, default)

        # Mock ImageBOM
        mock_imageBom = Mock()
        mock_ImageBOM.return_value = mock_imageBom

        # Mock ebox
        mock_ebox = self.mGetClubox()
        mock_ebox.mUpdateStatusCS = Mock()
        mock_ebox.mRunScript = Mock()
        mock_ebox.mLogStepElapsedTime = Mock()
        mock_ebox.mVMImagesShredding = Mock()
        mock_ebox.mGetCmd = Mock(return_value='deleteservice')  # In delete commands

        # Mock csUtil
        mock_csu = Mock()
        with patch('exabox.ovm.csstep.cs_util.csUtil', return_value=mock_csu):

            cs_instance = csPostVMInstall()
            options = Mock()
            steplist = Mock()

            # Call undoExecute
            cs_instance.undoExecute(mock_ebox, options, steplist)

            # Assertions: mPreVMDeleteCreatePatching should not be called
            mock_csu.mPreVMDeleteCreatePatching.assert_not_called()

if __name__ == '__main__':
    unittest.main()
