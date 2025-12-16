#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_cs_configcompute.py /main/1 2025/08/05 11:43:04 rajsag Exp $
#
# tests_cs_configcompute.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_configcompute.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rajsag      07/21/25 - Creation
#
import unittest
from unittest.mock import Mock, patch
from exabox.ovm.csstep.exascale.cs_configcompute import csConfigCompute
from exabox.ovm.csstep.cs_util import csUtil

class TestCsConfigCompute(unittest.TestCase):

    @patch.object(csUtil, 'mGetConstants')
    @patch.object(csUtil, 'mExecuteOEDAStep')
    def test_doExecute(self, mock_mExecuteOEDAStep, mock_mGetConstants):
        # Arrange
        mock_clu_ctrl_obj = Mock()
        mock_aOptions = Mock()
        mock_aStepList = Mock()
        mock_csConstants = Mock()
        mock_csConstants.OSTP_CONFIG_COMPUTE = 'OSTP_CONFIG_COMPUTE'
        mock_mGetConstants.return_value = mock_csConstants
        cs_config_compute = csConfigCompute()

        # Act
        cs_config_compute.doExecute(mock_clu_ctrl_obj, mock_aOptions, mock_aStepList)

        # Assert
        mock_mGetConstants.assert_called_once_with(mock_clu_ctrl_obj, False)
        mock_mExecuteOEDAStep.assert_called_once_with(mock_clu_ctrl_obj, cs_config_compute.step, mock_aStepList, 
                                                      aOedaStep=mock_csConstants.OSTP_CONFIG_COMPUTE, dom0Lock=False)

    @patch.object(csUtil, 'mGetConstants')
    @patch.object(csUtil, 'mExecuteOEDAStep')
    def test_undoExecute(self, mock_mExecuteOEDAStep, mock_mGetConstants):
        # Arrange
        mock_clu_ctrl_obj = Mock()
        mock_aOptions = Mock()
        mock_aStepList = Mock()
        mock_csConstants = Mock()
        mock_csConstants.OSTP_CONFIG_COMPUTE = 'OSTP_CONFIG_COMPUTE'
        mock_mGetConstants.return_value = mock_csConstants
        cs_config_compute = csConfigCompute()

        # Act
        cs_config_compute.undoExecute(mock_clu_ctrl_obj, mock_aOptions, mock_aStepList)

        # Assert
        mock_mGetConstants.assert_called_once_with(mock_clu_ctrl_obj, False)
        mock_mExecuteOEDAStep.assert_called_once_with(mock_clu_ctrl_obj, cs_config_compute.step, mock_aStepList, 
                                                      aOedaStep=mock_csConstants.OSTP_CONFIG_COMPUTE, undo=True, dom0Lock=False)

    def test_init(self):
        # Act
        cs_config_compute = csConfigCompute()

        # Assert
        self.assertEqual(cs_config_compute.step, 'ESTP_CONFIG_COMPUTE')

if __name__ == '__main__':
    unittest.main()