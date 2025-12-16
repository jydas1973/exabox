#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/core/tests_Config.py /main/1 2024/03/11 15:24:49 jfsaldan Exp $
#
# tests_Config.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_Config.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    03/08/24 - Bug 36350252 - EXACC GEN2 | INFRA PATCHING | DOMU
#                           OS PRECHECK/PATCHING FAILING ON ADBD VMS DUE TO
#                           MISSING KEYS
#    jfsaldan    03/08/24 - Creation
#

import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.config.Config import ebLoadProgramArguments

class ebTestConfig(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None


    def test_diffkeys_patching_program_args(self):
        """
        Make sure infrapatching has diffkeys argument
        """
        PROGRAM_ARGUMENTS, CLU_CMDS_OPTIONS, VM_CMDS_OPTIONS, CS_SUBSTEPS_CMDS_OPTIONS = ebLoadProgramArguments()
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('patch'))
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('patch_prereq_check'))
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('postcheck'))
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('rollback'))
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('rollback_prereq_check'))


if __name__ == '__main__':
    unittest.main()
