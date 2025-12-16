#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_golden_backup/tests_goldenvm_backup.py /main/8 2025/10/09 18:24:01 jfsaldan Exp $
#
# tests_goldenvm_backup.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_goldenvm_backup.py
#
#    DESCRIPTION
#      Test file of the golden vmbackup step
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    10/03/25 - Bug 38485986 - EXACS: VMBOSS: USE 'VMBACKUP
#                           VERSION' FROM DOM0 TO COMPARE THE VERSION AGAINST
#                           $EC_HOME/IMAGES/<VMBACKUP TGZ>
#    jfsaldan    07/04/25 - Bug 38134918 - EXACS:25.2.1.1:RC5: X11 CROSS
#                           PLATFORM: ADD VM FAILS AT CREATEGOLDIMAGEBACKUP:
#                           TIMEOUT HAPPENED WHILE TAKING THE GOLDEN VM BACKUP
#                           | SPAWNED SUBPROCESS GOT STUCK
#    jfsaldan    04/24/25 - Enh 37817347 - EXACLOUD GOLDENVMBACKUP PROVISIONING
#                           STEP | FAILING TO TAKE GOLDEN VM REFLINK DURING
#                           CREATE SERVICE SHOULD NOT CAUSE FAILURE
#    jfsaldan    11/01/23 - Bug 35969085 - ECS:EXACLOUD:23.4.1.2:ADD KMS KEY
#                           OCID AND CRYPTO ENDPOINT IN ALREADY PROVISIONED
#                           CLUSTERS IF PARAMETER IS MISSING FROM VMBACKUP.CONF
#    jfsaldan    10/10/23 - Enh 35791811 - VMBACKUP TO OSS:EXACLOUD: REDUCE
#                           TIME WHILE TAKING GOLD IMAGE DURING PROVISIONING
#    jfsaldan    07/28/23 - Enh 35207551 - EXACLOUD - ADD SUPPORT TO TERMINATE
#                           CLUSTER LEVEL VMBACKUP OCI RESOURCES WHEN CLUSTER
#                           IS TERMINATED AND CREATE METADATA BUCKET
#    jfsaldan    06/06/23 - Enh 34965441 - EXACLOUD TO SUPPORT NEW TASK FOR
#                           GOLD IMAGE BACKUP
#    jfsaldan    01/10/23 - Creation
#

import unittest
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.csstep.cs_golden_backup import csGoldenBackup
from exabox.log.LogMgr import ebLogInfo
from unittest.mock import Mock, patch
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext

class ebTestCluControlGoldenVMBackup(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        # Call ebTestClucontrol, to specify noDB/noOEDA
        super().setUpClass(False,False)
        self.maxDiff = None

    def test_golden_backup_disabled(self):
        """
        Test if flag disables correctly the feature
        """
        ebLogInfo("Test - Golden Backup disabled")
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_goldvm_backup': "False"})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()

        _step = csGoldenBackup()
        _rc =_step.doExecute(_ebox, _json, ["ESTP_GOLDEN_BACKUP"])
        self.assertEqual(_rc, 0)

        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_goldvm_backup': "false"})
        _rc =_step.doExecute(_ebox, _json, ["ESTP_GOLDEN_BACKUP"])
        self.assertEqual(_rc, 0)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mInstallVMbackupOnDom0")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mEnableOssVMBackupConfig")
    @patch("exabox.ovm.csstep.cs_golden_backup.csGoldenBackup.mTakeGoldenVMBackup")
    def test_tool_not_present_already_no_issues_installing_it(self,
            aMockTakeGoldenBackup,
            aMockUpdateConfig,
            aMockInstallTool,
            aMockIsInstalled):

        ebLogInfo("Test - Golden Backup enabled, tool is not already installed")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock as if tool is not installed already
        aMockIsInstalled.return_value = False

        # Mock as if tool is installed with no issues
        aMockInstallTool.return_value = 0

        # Mock as if updating config is ok
        aMockUpdateConfig.return_value = 0

        # Mock taking golden backup
        aMockTakeGoldenBackup.return_value = 0

        # Enable feature flag
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_goldvm_backup': 'True'})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()

        # Run test
        _step = csGoldenBackup()
        _rc =_step.doExecute(_ebox, _json, ["ESTP_GOLDEN_BACKUP"])
        self.assertEqual(_rc, None)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mInstallVMbackupOnDom0")
    def test_tool_not_present_already_fail_install(self, aMockInstallTool,
            aMockIsInstalled):
        """
        """
        ebLogInfo("Test - Golden Backup enabled, tool fails to get installed")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock as if tool is not installed already
        aMockIsInstalled.return_value = False

        # Mock as if tool is installed with issues
        aMockInstallTool.return_value = 1

        # Enable feature flag
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_vmbackup_install': 'True'})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        # Run test
        _step = csGoldenBackup()

        with self.assertRaises(ExacloudRuntimeError):
            _step.mInstallCurrentVmbackupTool(_ebox, _json)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mInstallVMbackupOnDom0")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mGetVMBackupVersion")
    def test_tool_is_present_already_but_unable_get_version_install_ok(self, aMockGetVersion,
            aMockInstallTool,
            aMockIsInstalled):

        ebLogInfo("Test - Golden Backup enabled, tool is installed since version is not fetched")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep", aRc=1,
                        aStdout="")
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock as if tool is installed already
        aMockIsInstalled.return_value = True

        # Mock as if remote tool version is undetermined
        aMockGetVersion.return_value = ("", "")

        # Mock as if tool is installed with no issues
        aMockInstallTool.return_value = 0

        # Enable feature flag
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_vmbackup_install': 'True'})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        # Run test
        _step = csGoldenBackup()
        _rc =_step.mInstallCurrentVmbackupTool(_ebox, _json)
        self.assertEqual(_rc, 0)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mGetVMBackupVersion")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckRemoteProcessOngoing")
    def test_tool_is_present_already_but_unable_get_version_with_ongoing_process(self,
            aMockCheckProcess,
            aMockGetVersion,
            aMockIsInstalled):
        """
        """
        ebLogInfo("Test - Golden Backup enabled, version unable to be fetched but process ongoing")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock as if tool is installed already
        aMockIsInstalled.return_value = True

        # Mock as if remote tool version is undetermined
        aMockGetVersion.return_value = ("", "")

        # Mock as if remote process is ongoing
        aMockCheckProcess.return_value = "some PID and some process info"

        # Enable feature flag
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_vmbackup_install': 'True'})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        # Run test
        _step = csGoldenBackup()
        with self.assertRaises(ExacloudRuntimeError):
            _step.mInstallCurrentVmbackupTool(_ebox, _json)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mGetVMBackupVersion")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckRemoteProcessOngoing")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mInstallVMbackupOnDom0")
    def test_tool_is_present_already_but_unable_get_version_with_no_ongoing_process(self,
            aMockInstallTool,
            aMockCheckProcess,
            aMockGetVersion,
            aMockIsInstalled):
        """
        """
        ebLogInfo("Test - Golden Backup enabled, version not read and no ongoing process, install ok")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock as if tool is installed already
        aMockIsInstalled.return_value = True

        # Mock as if remote tool version is undetermined
        aMockGetVersion.return_value = ("", "")

        # Mock as if remote process is not ongoing
        aMockCheckProcess.return_value = ""

        # Mock as if installation of tool is ok
        aMockInstallTool.return_value = 0

        # Enable feature flag
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_vmbackup_install': 'True'})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        # Run test
        _step = csGoldenBackup()
        _rc =_step.mInstallCurrentVmbackupTool(_ebox, _json)
        self.assertEqual(_rc, 0)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mGetVMBackupVersion")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mGetLocalVMBackupVersion")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mInstallVMbackupOnDom0")
    def test_tool_is_present_already_version_is_current(self,
            aMockInstallTool,
            aMockGetLocalVersion,
            aMockGetRemoteVersion,
            aMockIsInstalled):
        """
        """
        ebLogInfo("Test - Golden Backup enabled, tool is installed and version is current")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock as if tool is installed already
        aMockIsInstalled.return_value = 0

        # Mock remote version
        aMockGetRemoteVersion.return_value = "230111"

        # Mock local version
        aMockGetLocalVersion.return_value = "230111"

        # Mock as if installation of tool is ok
        aMockInstallTool.return_value = 0

        # Enable feature flag
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_vmbackup_install': 'True'})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        # Run test
        _step = csGoldenBackup()
        _rc =_step.mInstallCurrentVmbackupTool(_ebox, _json)
        self.assertEqual(_rc, 0)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mGetVMBackupVersion")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mGetLocalVMBackupVersion")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mInstallVMbackupOnDom0")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckRemoteProcessOngoing")
    def test_tool_is_present_already_version_is_older(self,
            aMockCheckProcess,
            aMockInstallTool,
            aMockGetLocalVersion,
            aMockGetRemoteVersion,
            aMockIsInstalled):
        """
        """
        ebLogInfo("Test - Tool is already present but with an older version. "
                "Installation is sucessfull")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock as if tool is installed already
        aMockIsInstalled.return_value = 0

        # Mock remote version
        aMockGetRemoteVersion.return_value = "230105"

        # Mock local version
        aMockGetLocalVersion.return_value = "230111"

        # Mock as if installation of tool is ok
        aMockInstallTool.return_value = 0

        # Mock if remote ongoing process
        aMockCheckProcess.return_value = False

        # Enable feature flag
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_vmbackup_install': 'True'})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        # Run test
        _step = csGoldenBackup()
        _rc =_step.mInstallCurrentVmbackupTool(_ebox, _json)
        self.assertEqual(_rc, 0)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mGetVMBackupVersion")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mGetLocalVMBackupVersion")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mInstallVMbackupOnDom0")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckRemoteProcessOngoing")
    def test_tool_is_present_already_version_is_older_ongoing_process(self,
            aMockCheckProcess,
            aMockInstallTool,
            aMockGetLocalVersion,
            aMockGetRemoteVersion,
            aMockIsInstalled):
        """
        """
        ebLogInfo("Test - Tool is already present but with an older version. "
                "Installation is sucessfull")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock as if tool is installed already
        aMockIsInstalled.return_value = True

        # Mock remote version
        aMockGetRemoteVersion.return_value = ("MAIN", "230105")

        # Mock local version
        aMockGetLocalVersion.return_value = ("MAIN", "230111")

        # Mock as if installation of tool is ok
        aMockInstallTool.return_value = 0

        # Mock if remote ongoing process
        aMockCheckProcess.return_value = "Some pid and process info"

        # Enable feature flag
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_vmbackup_install': 'True'})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        # Run test
        _step = csGoldenBackup()
        with self.assertRaises(ExacloudRuntimeError):
                _step.mInstallCurrentVmbackupTool(_ebox, _json)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebVMBackupOCI")
    @patch("exabox.ovm.csstep.cs_golden_backup.csGoldenBackup.mStopVMAndTakeGoldenBackup")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    def test_mTakeGoldenVMBackup(self,
            aMockIsToolInstalled,
            aMockTriggerBackup,
            aMockVMBackupOCIMgr):

        ebLogInfo("Test - Take Golden VMBackup")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock if tool is installed
        aMockIsToolInstalled.return_value = True

        # Mock if golden backup trigger works
        aMockTriggerBackup.return_value = True

        # Mock if copying creds works
        #aMockVMBackupOCIMgr.return_value = 0

        _ebox = self.mGetClubox()
        aOptions = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        _step = csGoldenBackup()
        _step.mTakeGoldenVMBackup(_ebox, aOptions, _dom0_list)

    def test_mTakeGoldenBackupCallback_all_good(self):

        ebLogInfo("Test - Take Golden VMBackup")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("source .*; timeout 3600 vmbackup backup --vm .* --gold", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        aOptions = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]
        _domU_list = [_domU for _, _domU in _ebox.mReturnDom0DomUPair()]

        _step = csGoldenBackup()
        _rc_status = {}
        _step.mTakeGoldenReflinkCallback(_dom0_list[0], _domU_list[0], 3600, _rc_status)
        self.assertEqual(_rc_status[_dom0_list[0]], 0)

    def test_mTakeGoldenBackupCallback_error(self):

        ebLogInfo("Test - Take Golden VMBackup")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("source .*; timeout 3600 vmbackup backup --vm .* --gold", aRc=1),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        aOptions = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]
        _domU_list = [_domU for _, _domU in _ebox.mReturnDom0DomUPair()]

        _step = csGoldenBackup()
        _rc_status = {}
        #with self.assertRaises(ExacloudRuntimeError):
        _step.mTakeGoldenReflinkCallback(_dom0_list[0], _domU_list[0], 3600, _rc_status)
        self.assertNotEqual(_rc_status[_dom0_list[0]], 0)

    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mDisableOSSVMBackupConfig")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckAsmIsUp")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsIsUp")
    @patch("exabox.ovm.csstep.cs_golden_backup.csGoldenBackup.mTakeGoldenVMBackup")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebVMBackupOCI.mIsForceUsersPrincipalsSet")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebVMBackupOCI")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebCluManageVMBackup.mEnableOssVMBackupConfig")
    @patch("exabox.ovm.csstep.cs_golden_backup.ebVMBackupOCI.mIsVMBOSSEnabled")
    @patch("exabox.ovm.csstep.cs_golden_backup.csGoldenBackup.mInstallCurrentVmbackupTool")
    def test_csGoldenBackup_doExecute_happy_path(self,
            aMockInstallLatest,
            aMockIsOSSEnabled,
            aMockEnableOssVMBackupConfig,
            aMockVMBackupOCIClass,
            aMockIsForceUsersPrincipals,
            aMockTakeGoldenBackup,
            aMockCheckCRS,
            aMockCheckASM,
            aMockDisableOssVMBackupConfig):
        """
        """
        ebLogInfo("Test - csGolde doExecute")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("source .*; timeout 3600 vmbackup backup --vm .* --gold", aRc=1),
                ],
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping -c 1", aRc=0),
                    exaMockCommand("ping -c 1", aRc=0),
                ]
            ]
        }

        # Test Setup
        self.mGetContext().mSetConfigOption('exabm',"True")
        self.mGetContext().mSetConfigOption('vmbackup',
                {'raise_gold_backup_on_error': "True"})

        aMockIsOSSEnabled.return_value = True
        aMockIsForceUsersPrincipals.return_value = False

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        aOptions = self.mGetPayload()

        _step = csGoldenBackup()
        self.assertEqual(None, _step.doExecute(_ebox, aOptions, []))

    def test_csGoldenBackup_doExecute_error_not_reported(self):
        """
        """
        ebLogInfo("Test - csGolde doExecute")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("source .*; timeout 3600 vmbackup backup --vm .* --gold", aRc=1),
                ],
            ],
        }

        # Test Setup
        self.mGetContext().mSetConfigOption('exabm',"True")
        self.mGetContext().mSetConfigOption('vmbackup',
                {'raise_gold_backup_on_error': "False"})

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        aOptions = self.mGetPayload()

        _step = csGoldenBackup()
        self.assertEqual(None, _step.doExecute(_ebox, aOptions, []))

if __name__ == '__main__':
    unittest.main()
