#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_cs_createstorage.py /main/1 2025/08/05 11:43:04 rajsag Exp $
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
#    rajsag      08/01/25 - Test case of exascale createstorage flow
#    rajsag      08/01/25 - Creation
#
import unittest
from unittest.mock import Mock, patch
from exabox.ovm.csstep.exascale.cs_createstorage import csCreateStorage, csUtil, CSBase 

class TestCsCreateStorage(unittest.TestCase):

    def setUp(self):
        self.cs_create_storage = csCreateStorage()
        self.mock_clu_ctrl_obj = Mock()
        self.mock_options = Mock()
        self.mock_step_list = Mock()

    @patch.object(csUtil, 'mGetConstants')
    @patch.object(csUtil, 'mExecuteOEDAStep')
    def test_do_execute(self, mock_m_execute_oeda_step, mock_m_get_constants):
        # Arrange
        mock_m_get_constants.return_value = Mock(OSTP_SETUP_CELL='OSTP_SETUP_CELL', 
                                                 OSTP_VERIFY_FABRIC='OSTP_VERIFY_FABRIC', 
                                                 OSTP_CALIBRATE_CELLS='OSTP_CALIBRATE_CELLS')
        self.mock_clu_ctrl_obj.mAcquireRemoteLock = Mock()
        self.mock_clu_ctrl_obj.mReleaseRemoteLock = Mock()

        # Act
        self.cs_create_storage.doExecute(self.mock_clu_ctrl_obj, self.mock_options, self.mock_step_list)

        # Assert
        self.mock_clu_ctrl_obj.mAcquireRemoteLock.assert_called_once()
        mock_m_execute_oeda_step.assert_any_call(self.mock_clu_ctrl_obj, self.cs_create_storage.step, self.mock_step_list, 
                                                 aOedaStep='OSTP_SETUP_CELL', dom0Lock=False)
        self.mock_clu_ctrl_obj.mReleaseRemoteLock.assert_called_once()
        mock_m_execute_oeda_step.assert_any_call(self.mock_clu_ctrl_obj, self.cs_create_storage.step, self.mock_step_list, 
                                                 aOedaStep='OSTP_VERIFY_FABRIC')
        mock_m_execute_oeda_step.assert_any_call(self.mock_clu_ctrl_obj, self.cs_create_storage.step, self.mock_step_list, 
                                                 aOedaStep='OSTP_CALIBRATE_CELLS')

    @patch.object(csUtil, 'mGetConstants')
    @patch.object(csUtil, 'mExecuteOEDAStep')
    def test_undo_execute(self, mock_m_execute_oeda_step, mock_m_get_constants):
        # Arrange
        mock_m_get_constants.return_value = Mock(OSTP_CALIBRATE_CELLS='OSTP_CALIBRATE_CELLS', 
                                                 OSTP_SETUP_CELL='OSTP_SETUP_CELL')

        # Act
        self.cs_create_storage.undoExecute(self.mock_clu_ctrl_obj, self.mock_options, self.mock_step_list)

        # Assert
        mock_m_execute_oeda_step.assert_any_call(self.mock_clu_ctrl_obj, self.cs_create_storage.step, self.mock_step_list, 
                                                 aOedaStep='OSTP_CALIBRATE_CELLS', undo=True, dom0Lock=False)
        mock_m_execute_oeda_step.assert_any_call(self.mock_clu_ctrl_obj, self.cs_create_storage.step, self.mock_step_list, 
                                                 aOedaStep='OSTP_SETUP_CELL', undo=True, dom0Lock=False)

if __name__ == '__main__':
    unittest.main()
