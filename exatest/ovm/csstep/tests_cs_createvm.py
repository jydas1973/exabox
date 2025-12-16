#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_createvm.py /main/11 2025/12/01 22:37:00 avimonda Exp $
#
# tests_cs_createvm.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_createvm.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    11/06/25 - Bug 38427813 - OCI: EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 1877 EXACLOUD : ERROR IN
#                           MULTIPROCESSING(NON-ZERO EXITCODE(-9) RETURNED
#                           <PROCESSSTRUCTURE(<DOM0 NODE>, STOPPED[SIGKILL])>,
#                           ID: <DOM0 NODE>, START_TIME: <T1>, END_TIME: <T2>,
#                           MAX_TIME
#    avimonda    10/24/25 - Bug 38442915 - OCI: ADD MAXDISTANCE 16 PARAMETER IN
#                           DOMU CHRONY CONFIG BEFORE CLUSTER CREATION SANITY
#                           CHECK.
#    aararora    10/17/23 - Bug 35893125: Unit test for checking if system img
#                           file is present on DOM0
#    jesandov    06/15/23 - Creation
#

import unittest

from unittest.mock import patch

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.csstep.cs_createvm import csCreateVM
from unittest.mock import patch, MagicMock, PropertyMock, mock_open

class testOptions(object): pass

class ebTestCSCreateVm(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCSCreateVm, self).setUpClass(aUseOeda=True)

    def test_mCreateVM(self):
        ebLogInfo("Running unit test on csCreateVM.py:mCreateVM")

        with patch('exabox.ovm.csstep.cs_base.ImageBOM.mIsSubStepExecuted', side_effect=iter([True,True,True,True,True,True,True,True,True,False,True,True])),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsOciEXACC', return_value=True),\
             patch('exabox.ovm.csstep.cs_base.serialConsole.mRunContainer'),\
             patch('exabox.ovm.csstep.cs_base.serialConsole.mRestartContainer'):
                _createvm_instance = csCreateVM()
                _createvm_instance.mCreateVM(self.mGetClubox(),self.mGetClubox().mGetArgsOptions(), [])



    def test_mCheckSystemImage(self):

        mockCommands = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("sed.*es.properties", aPersist=True),
                    exaMockCommand("/bin/mkdir -p *", aRc=0, aPersist=True), # Create exabox.conf
                    exaMockCommand("/bin/scp *", aRc=0, aPersist=True)    # Copy xml
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo -version", aStdout="22.1.10.0.0.230422", aPersist=True),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/*", aStdout="System.first.boot.22.1.10.0.0.230422.img", aPersist=True)
                ],
                [
                    exaMockCommand("imageinfo -version", aStdout="22.1.10.0.0.230422", aPersist=True),
                    exaMockCommand("ls /EXAVMIMAGES/*", aStdout="System.first.boot.22.1.10.0.0.230422.img", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/*", aRc=0, aPersist=True),
                    exaMockCommand("test.*touch", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.22.1.10.0.0.230422.img", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("ls /EXAVMIMAGES/*", aStdout="System.first.boot.22.1.10.0.0.230422.img", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/*", aRc=0, aPersist=True),
                    exaMockCommand("test.*find", aRc=0, aPersist=True),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7', aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/*", aRc=0, aPersist=True),
                    exaMockCommand("ls /EXAVMIMAGES/*", aStdout="System.first.boot.22.1.10.0.0.230422.img", aPersist=True),
                    exaMockCommand("test.*find", aRc=0, aPersist=True),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7', aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand('/bin/test -e /EXAVMIMAGES/System.first.boot.22.1.10.0.0.230422.img', aRc=0, aPersist=True),
                    exaMockCommand("test.*touch", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.22.1.10.0.0.230422.img", aRc=0, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(mockCommands)
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetVersionGi', return_value="191") ,\
            patch('exabox.ovm.sysimghandler.mGetLocalFileHash', return_value={'System.first.boot.22.1.10.0.0.230422.img':'d2fd86...'}):
            self.mGetClubox().mCheckSystemImage()

    def test_mCheckDomUImageFor23ai_invalid_image(self):
        mockCommands = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("sed.*es.properties", aPersist=True),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo -version", aStdout="22.1.10.0.0.230422", aPersist=True),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/*", aStdout="System.first.boot.22.1.10.0.0.230422.img", aPersist=True)
                ],
                [
                    exaMockCommand("imageinfo -version", aStdout="22.1.10.0.0.230422", aPersist=True),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/*", aStdout="System.first.boot.22.1.10.0.0.230422.img", aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetVersionGi', return_value="230"):
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                self.mGetClubox().mCheckSystemImage()
                self.assertEqual(ctx.exception.mGetErrorCode(), 0x0826)
                       
    def test_mCheckDomUImageFor23ai_19gi(self):
        mockCommands = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("sed.*es.properties", aPersist=True),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo -version", aStdout="22.1.10.0.0.230422", aPersist=True),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/*", aStdout="System.first.boot.22.1.10.0.0.230422.img", aPersist=True)
                ],
                [
                    exaMockCommand("imageinfo -version", aStdout="22.1.10.0.0.230422", aPersist=True),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/*", aStdout="System.first.boot.22.1.10.0.0.230422.img", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(mockCommands)
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetVersionGi', return_value="230"):
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                self.mGetClubox().mCheckSystemImage()        
                self.assertEqual(ctx.exception.mGetErrorCode(), 0x0826)
    
    def test_mCheckDomUImageFor23ai_valid_image(self):
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetVersionGi', return_value="230"):
            self.mGetClubox().mCheckDomUImageFor23ai("24.1.0.0.0.240517.1")

    def test_mDeleteVM(self):
        # Arrange
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mKillOngoingStartDomains', return_value=True ),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption',return_value=False ),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsOciEXACC', return_value=False),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCleanUpStaleVm', return_value=True),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckVMCyclesAndReboot'),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDeleteClusterDomUList'),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCleanUpReconfig'):
                _createvm_instance = csCreateVM()
                _createvm_instance.mDeleteVM(self.mGetClubox(),self.mGetClubox().mGetArgsOptions(), [])

    def test_doExecute(self):
        ebLogInfo("Running unit test on csCreateVM.py:doExecute")

        with patch('exabox.ovm.csstep.cs_createvm.csCreateVM.mCreateVM'), \
             patch('exabox.ovm.csstep.cs_base.ImageBOM.mIsSubStepExecuted', side_effect=[False, False, False, False]), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.IsZdlraProv', return_value=True), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateOedaUserPswd'), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetZDLRA', return_value=MagicMock()), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale', return_value=True), \
             patch('exabox.ovm.csstep.cs_util.csUtil.mSetEnvVariableInDomU'), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True), \
             patch('exabox.ovm.csstep.cs_util.csUtil.mReturnCountofVm', return_value=1), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnAllClusterHosts', return_value=([], [], [], [])), \
             patch('exabox.ovm.clumisc.ebCluPreChecks.mAddMissingNtpDnsIps'), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.isBaseDB', return_value=False), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.isDBonVolumes', return_value=False), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', return_value=False), \
             patch('exabox.ovm.cluexascale.ebCluExaScale.mAttachDBVolumetoGuestVMs'), \
             patch('exabox.ovm.csstep.cs_createvm.csCreateVM.maxDistanceUpdate'), \
             patch('exabox.ovm.utils.clu_utils.ebCluUtils.mStepSpecificDetails', return_value={}), \
             patch('exabox.ovm.utils.clu_utils.ebCluUtils.mUpdateTaskProgressStatus'):
            _createvm_instance = csCreateVM()
            _createvm_instance.doExecute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions(), [])

        # Test edge case: Non-ZDLRA, non-ExaScale, no KVM
        with patch('exabox.ovm.csstep.cs_createvm.csCreateVM.mCreateVM'), \
             patch('exabox.ovm.csstep.cs_base.ImageBOM.mIsSubStepExecuted', side_effect=[True, True, True, True]), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.IsZdlraProv', return_value=False), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale', return_value=False), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.isBaseDB', return_value=False), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.isDBonVolumes', return_value=False), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', return_value=False), \
             patch('exabox.ovm.csstep.cs_createvm.csCreateVM.maxDistanceUpdate'), \
             patch('exabox.ovm.utils.clu_utils.ebCluUtils.mStepSpecificDetails', return_value={}), \
             patch('exabox.ovm.utils.clu_utils.ebCluUtils.mUpdateTaskProgressStatus'):
            _createvm_instance = csCreateVM()
            _createvm_instance.doExecute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions(), [])


if __name__ == '__main__':
    unittest.main()
