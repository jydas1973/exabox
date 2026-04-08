#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exabasedb/tests_cs_exascale_complete.py /main/3 2026/01/02 04:46:45 naps Exp $
#
# tests_cs_exascale_complete.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_exascale_complete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    naps        12/23/25 - Bug 38746264 - UT Updation
#    naps        12/19/25 - Bug 38769320 - UT updation.
#    prsshukl    11/24/25 - Creation
#

import unittest
import warnings
from unittest import mock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.csstep.exabasedb.cs_exascale_complete import csExaScaleComplete
from exabox.ovm.bom_manager import ImageBOM
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.core.MockCommand import exaMockCommand

class ebTestExaScaleComplete(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestExaScaleComplete, self).setUpClass(aGenerateDatabase=True, aUseOeda=True, aEnableUTFlag=False)
        warnings.filterwarnings("ignore")

    @mock.patch('exabox.ovm.csstep.exabasedb.cs_exascale_complete.ImageBOM')
    @mock.patch('exabox.ovm.csstep.exabasedb.cs_exascale_complete.ebCluExaScale')
    @mock.patch('exabox.ovm.csstep.exabasedb.cs_exascale_complete.expand_domu_filesystem')
    def test_doExecute_substeps_already_executed(self, mock_expand_domu_filesystem, mock_ebCluExaScale, mock_ImageBOM):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _step_list = ["ESTP_EXASCALE_COMPLETE"]
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /etc/passw.*", aStdout=None),
                    exaMockCommand("/opt/oracle.cellos/host_access_control.*", aStdout=None)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Mock ImageBOM - substeps already executed
        mock_imagebom_instance = mock.Mock()
        mock_ImageBOM.return_value = mock_imagebom_instance
        mock_imagebom_instance.mIsSubStepExecuted.return_value = True

        # Mock ebCluExaScale
        mock_exascale_instance = mock.Mock()
        mock_ebCluExaScale.return_value = mock_exascale_instance

        _handler = csExaScaleComplete()
        _options.jsonconf['delete_domu_keys'] = 'True'
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetCmd', return_value="createservice"):
            _handler.doExecute(_ebox, _options, _step_list)

        # Verify that skipped steps are not called
        mock_expand_domu_filesystem.assert_not_called()

    @mock.patch('exabox.ovm.csstep.exabasedb.cs_exascale_complete.ImageBOM')
    @mock.patch('exabox.ovm.csstep.exabasedb.cs_exascale_complete.ebCluExaScale')
    def test_undoExecute_no_snapshots(self, mock_ebCluExaScale, mock_ImageBOM):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _step_list = ["ESTP_EXASCALE_COMPLETE"]

        # Mock ebCluExaScale
        mock_exascale_instance = mock.Mock()
        mock_ebCluExaScale.return_value = mock_exascale_instance
        mock_exascale_instance.mGetLVDev.return_value = (None, None)  # No snapshots

        _handler = csExaScaleComplete()
        _handler.undoExecute(_ebox, _options, _step_list)

        # Verify unmount not called
        mock_exascale_instance.mUnmountVolume.assert_not_called()

if __name__ == '__main__':
    unittest.main()
