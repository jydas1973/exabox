#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_mCheckCellConfig.py /main/1 2024/03/12 21:20:02 jfsaldan Exp $
#
# tests_mCheckCellConfig.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_mCheckCellConfig.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    03/07/24 - Bug 36350280 - EXACC: CREATE CLUSTER DROPS FLASHLOG
#                           AND FLASHCACHE BEFORE CALLING OEDA CREATE CELLDISKS
#    jfsaldan    03/07/24 - Creation
#

import unittest
from unittest.mock import Mock, patch
from unittest.mock import MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogTrace
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext


class ebTestCheckCellConfig(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None


    def test_mCheckCellConfig_mvm(self):
        """
        In MVM we don't even need to declare examock commands
        because we expect the method to return False
        in MVM
        """
        _ebox = self.mGetClubox()
        _ebox.mSetSharedEnv(True)

        self.assertEqual(False, _ebox.mCheckCellConfig(_ebox.mGetArgsOptions()))


if __name__ == '__main__':
    unittest.main()
