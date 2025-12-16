#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_check_asm.py /main/2 2024/05/06 18:47:19 jfsaldan Exp $
#
# tests_check_asm.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_check_asm.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    04/26/24 - Bug 36558103 - EXACS : EXACLOUD SHOULD START THE
#                           LOCAL RESOURCE <DGPREFFIX>.ACFSVOL01.ACFS WHEN
#                           STARTING ACFS
#    jfsaldan    03/11/24 - Bug 36004327 - EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 276 EXACLOUD : TIMEOUT WHILE
#                           WAITING FOR ASM TO BE RUNNING
#    jfsaldan    03/11/24 - Creation
#

import unittest
from unittest.mock import patch
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError
from exabox.network.Connection import exaBoxConnection

class ebTestASMIsUp(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

    @patch('exabox.ovm.clucontrol.time.sleep')
    def test_mCheckAsmIsUp(self, aMagicSleep):
        """
        ASM is all up already
        """

        _gi_path = "/u01/app/19.0.0.0/grid"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(
                        "cat /etc/oratab | grep.*",
                        aStdout=f"{_gi_path}\n", aRc=0),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl status asm | grep 'ASM is running on'",
                        aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl  status asm",
                        aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl  status filesystem",
                        aStdout="ACFS file system /acfs01 is mounted on nodes scaqab10client01vm08,scaqab10client02vm08",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl  status filesystem | grep 'is mounted on nodes'",
                        aStdout="ACFS file system /acfs01 is mounted on nodes scaqab10client01vm08,scaqab10client02vm08",
                        aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _domu_list = [ _domu for _ , _domu in _ebox.mReturnElasticAllDom0DomUPair()]

        _ebox.mCheckAsmIsUp(_domu_list[0], _domu_list, aUser='oracle')

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mFetchCrsAsmLogs')
    def test_mCheckAsmIsUp_asm_restart_needed_and_failed(self, aMockASMFetchLogs):
        """
        """

        _gi_path = "/u01/app/19.0.0.0/grid"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(
                        "cat /etc/oratab | grep.*",
                        aStdout=f"{_gi_path}\n", aRc=0),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl status asm | grep 'ASM is running on'",
                        aStdout="ASM is running on scaqab10client01vm08",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl  status asm",
                        aStdout="ASM is running on scaqab10client01vm08",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl stop asm -n scaqab10client02vm08.us.oracle.com -force",
                        aStdout="",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl start asm -n scaqab10client02vm08.us.oracle.com",
                        aStdout="",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/crsctl stat rest -t | /bin/grep -i acfsvol01.acfs",
                        aStdout="ora.datac3.acfsvol01.acfs\n",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/crsctl start res ora.datac3.acfsvol01.acfs -n sca.* -unsupported",
                        aStdout="",
                        aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        self.mGetContext().mSetConfigOption('crs_timeout', '1')

        _domu_list = [ _domu for _ , _domu in _ebox.mReturnElasticAllDom0DomUPair()]

        with self.assertRaises(ExacloudRuntimeError):
            _ebox.mCheckAsmIsUp(_domu_list[0], _domu_list, aUser='oracle', aTimeOut=2)


    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mFetchCrsAsmLogs')
    def test_mCheckAsmIsUp_acfs_down_restart_needed_and_failed(self, aMockASMFetchLogs):
        """
        """

        _gi_path = "/u01/app/19.0.0.0/grid"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(
                        "cat /etc/oratab | grep.*",
                        aStdout=f"{_gi_path}\n", aRc=0),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl status asm | grep 'ASM is running on'",
                        aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl  status asm",
                        aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl  status filesystem",
                        aStdout="ACFS file system /acfs01 is mounted on nodes scaqab10client01vm08",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl  status filesystem | grep 'is mounted on nodes'",
                        aStdout="ACFS file system /acfs01 is mounted on nodes scaqab10client01vm08",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl stop asm -proxy -n scaqa.* -force",
                        aStdout="ora.datac3.acfsvol01.acfs\n",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/srvctl start asm -proxy -n scaqa.*",
                        aStdout="ora.datac3.acfsvol01.acfs\n",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/crsctl stat rest -t | /bin/grep -i acfsvol01.acfs",
                        aStdout="ora.datac3.acfsvol01.acfs\n",
                        aRc=0, aPersist=True),
                    exaMockCommand(
                        f"{_gi_path}/bin/crsctl start res ora.datac3.acfsvol01.acfs -n sca.* -unsupported",
                        aStdout="",
                        aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        self.mGetContext().mSetConfigOption('crs_timeout', '1')

        _domu_list = [ _domu for _ , _domu in _ebox.mReturnElasticAllDom0DomUPair()]

        with self.assertRaises(ExacloudRuntimeError):
            _ebox.mCheckAsmIsUp(_domu_list[0], _domu_list, aUser='oracle', aTimeOut=2)

if __name__ == "__main__":
    unittest.main(warnings='ignore')
