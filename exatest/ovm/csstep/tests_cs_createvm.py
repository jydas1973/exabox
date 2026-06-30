#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_createvm.py /main/13 2026/01/28 17:38:21 avimonda Exp $
#
# tests_cs_createvm.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
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
#    remamid     04/01/26 - Bug 39088724 update unit test for cell lock
#    remamid     03/30/26 - Bug39088724 Add cell lock unit test
#    avimonda    12/06/25 - Bug 38610132 - OCI: DBAAS.CREATEEXACCVMCLUSTER
#                           HANGS /DOES NOT PROGRESS
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
from contextlib import contextmanager

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

        def fake_is_substep_executed(step, substep):
            return substep != "SAVE_OEDA_KEYS"

        with patch('exabox.ovm.csstep.cs_base.ImageBOM.mIsSubStepExecuted', side_effect=fake_is_substep_executed),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsOciEXACC', return_value=True),\
             patch('exabox.ovm.csstep.cs_base.serialConsole.mRunContainer'),\
             patch('exabox.ovm.csstep.cs_base.serialConsole.mRestartContainer'):
                _createvm_instance = csCreateVM()
                _createvm_instance.mCreateVM(self.mGetClubox(),self.mGetClubox().mGetArgsOptions(), [])

    def test_mCreateVM_acquires_cell_lock_in_shared_env(self):
        cluster = self.mGetClubox()
        lock_contexts = []

        def fake_check_config(option, value=None):
            if option == "skip_dom0_lock_oeda_createvm" and value == "False":
                return True
            if option in {"skip_completely_stale_bridge_removal", "_skip_jumbo_frames_config"}:
                return True
            return False

        with patch('exabox.ovm.csstep.cs_base.ImageBOM') as mock_imagebom_cls, \
             patch('exabox.ovm.csstep.cs_base.csUtil') as mock_csutil_cls, \
             patch('exabox.ovm.csstep.cs_base.RemoteLock') as mock_remote_lock_cls, \
             patch.object(cluster, 'SharedEnv', return_value=True), \
             patch.object(cluster, 'mReturnAllClusterHosts', return_value=(['dom0a'], ['domUa'], ['cell1'], [])), \
             patch.object(cluster, 'mCheckConfigOption', side_effect=fake_check_config), \
             patch.object(cluster, 'mIsExaScale', return_value=True), \
             patch.object(cluster, 'mIsKVM', return_value=False), \
             patch.object(cluster, 'isBaseDB', return_value=False), \
             patch.object(cluster, 'isExacomputeVM', return_value=False), \
             patch.object(cluster, 'mIsOciEXACC', return_value=False), \
             patch.object(cluster, 'isDBonVolumes', return_value=False):

            mock_imagebom = mock_imagebom_cls.return_value
            mock_imagebom.mIsSubStepExecuted.side_effect = lambda step, substep: substep != "OEDA_STEP"
            mock_imagebom.mIsGoldImageProvisioning.return_value = False

            mock_csutil = mock_csutil_cls.return_value
            mock_csutil.mExecuteOEDAStep = MagicMock()

            fake_lock = MagicMock()

            def lock_call(*args, **kwargs):
                lock_name = args[0] if args else 'Default'

                @contextmanager
                def _ctx():
                    lock_contexts.append((lock_name, kwargs))
                    yield

                return _ctx()

            fake_lock.side_effect = lock_call
            mock_remote_lock_cls.return_value = fake_lock

            csCreateVM().mCreateVM(cluster, cluster.mGetArgsOptions(), [])

        mock_remote_lock_cls.assert_called_once_with(cluster, force_host_list=['cell1'])
        self.assertIn(('cell', {'step': 'Create VM OEDA'}), lock_contexts)
        mock_csutil.mExecuteOEDAStep.assert_called_once()
        self.assertTrue(mock_csutil.mExecuteOEDAStep.call_args.kwargs.get('dom0Lock'))


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
            patch('exabox.ovm.sysimghandler.mGetLocalFileHash', return_value={'System.first.boot.22.1.10.0.0.230422.img':'d2fd86...'}), \
            patch.object(self.mGetClubox(), 'mGetExadataDom0Model', return_value='X8-2'), \
            patch.object(self.mGetClubox(), 'mIsXS', return_value=False):
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
