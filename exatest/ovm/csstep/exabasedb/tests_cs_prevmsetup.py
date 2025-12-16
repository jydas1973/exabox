#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exabasedb/tests_cs_prevmsetup.py /main/1 2025/11/25 05:03:58 prsshukl Exp $
#
# tests_cs_prevmsetup.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_prevmsetup.py - <one-line expansion of the name>
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
from unittest import mock
import warnings
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.csstep.exabasedb.cs_prevmsetup import csPreVMSetup
from exabox.log.LogMgr import ebLogInfo


class test_csPreVMSetup(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(test_csPreVMSetup, cls).setUpClass(aGenerateDatabase=True, aUseOeda=True, aEnableUTFlag=False)
        warnings.filterwarnings("ignore")

    @mock.patch('exabox.ovm.csstep.cs_base.CSBase.mPostVMDeleteSteps')
    def test_undoExecute(self, mock_mPostVMDeleteSteps):
        """
        Test the undoExecute method of csPreVMSetup.
        Verifies that mPostVMDeleteSteps is called with correct arguments.
        """
        ebLogInfo("Running unit test on csPreVMSetup:undoExecute")

        # Create instance of csPreVMSetup
        cs_instance = csPreVMSetup()

        # Get test objects
        ebox = self.mGetClubox()
        options = ebox.mGetArgsOptions()
        steplist = ["ESTP_PREVM_SETUP"]

        # Execute undoExecute
        cs_instance.undoExecute(ebox, options, steplist)

        # Verify that mPostVMDeleteSteps was called once with correct arguments
        mock_mPostVMDeleteSteps.assert_called_once_with(ebox, options, steplist)

        ebLogInfo("Unit test on csPreVMSetup:undoExecute successful")

    @mock.patch('exabox.ovm.csstep.cs_base.CSBase.mPostVMDeleteSteps')
    def test_undoExecute_exception_handling(self, mock_mPostVMDeleteSteps):
        """
        Test the undoExecute method of csPreVMSetup with exception in mPostVMDeleteSteps.
        Verifies that exceptions from mPostVMDeleteSteps are propagated.
        """
        ebLogInfo("Running unit test on csPreVMSetup:undoExecute with exception")

        # Create instance of csPreVMSetup
        cs_instance = csPreVMSetup()

        # Get test objects
        ebox = self.mGetClubox()
        options = ebox.mGetArgsOptions()
        steplist = ["ESTP_PREVM_SETUP"]

        # Make mPostVMDeleteSteps raise an exception
        mock_mPostVMDeleteSteps.side_effect = Exception("Test exception")

        # Execute undoExecute and expect exception
        with self.assertRaises(Exception) as context:
            cs_instance.undoExecute(ebox, options, steplist)

        self.assertEqual(str(context.exception), "Test exception")

        # Verify that mPostVMDeleteSteps was called once with correct arguments
        mock_mPostVMDeleteSteps.assert_called_once_with(ebox, options, steplist)

        ebLogInfo("Unit test on csPreVMSetup:undoExecute exception handling successful")


if __name__ == '__main__':
    unittest.main()
