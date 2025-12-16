#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_roceswitchhandler.py /main/7 2024/08/16 10:00:25 araghave Exp $
#
# tests_roceswitchhandler.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_roceswitchhandler.py - Class for testing roceswitch precheck, patch and rollback
#
#    DESCRIPTION
#      File for testing the Roce Switch Handler operations regarding infrapatching.
#      (mPreCheck, mPatch, mRollBack)
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    emekala     07/30/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    emekala     06/28/24 - ENH 36748433 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE DOM0, CELL, IBSWITCH AND ROCESWITCH PATCHMGR
#                           CMDS
#    jyotdas     10/18/22 - BUG 34681939 - Infrapatching compute nodes should
#                           be sorted by dbserver name from ecra
#    araghave    09/19/22 - ENH 34480945 - EXACS:22.2.1:MVM IMPLEMENTATION ON
#                           INFRA PATCHING CORE FILES
#    abherrer    07/05/22 - Enh 34349300 - Creation
#    abherrer    08/15/22 - Bug 34461211 - Stage 2 implementation
#
import unittest
from unittest.mock import patch
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.handlers.targetHandler.roceswitchhandler import RoceSwitchHandler
from exabox.core.MockCommand import exaMockCommand

class ebTestRoceSwitchHandler(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"

    @classmethod
    def setUpClass(self):
        ebLogInfo("Starting classSetUp RoceSwitchHandler")
        super(ebTestRoceSwitchHandler, self).setUpClass(aGenerateDatabase=True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption("repository_root", self.mGetPath(self))
        _cluCtrl = self.mGetClubox(self)
        _cluCtrl._exaBoxCluCtrl__kvm_enabled = True
        self.__patch_args_dict = {'CluControl': _cluCtrl,
                                'LocalLogFile': 'exabox/exatest/infrapatching/resources/patchmgr_logs',
                                'TargetType': ['cell'], 'Operation': 'patch_prereq_check', 'OperationStyle': 'auto',
                                'PayloadType': 'exadata_release', 'TargetEnv': 'production', 'EnablePlugins': 'no',
                                'PluginTypes': 'none',
                                'CellIBSwitchesPatchZipFile': 'exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/CellPatchFile/21.2.11.0.0.220414.1.patch.zip',
                                'Dom0DomuPatchZipFile': 'exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/CellPatchFile/21.2.11.0.0.220414.1.patch.zip',
                                'TargetVersion': '21.2.11.0.0.220414.1', 'ClusterID': 1,
                                'BackupMode': 'yes', 'Fedramp': 'DISABLED', 'Retry': 'no',
                                'RequestId': 'e2f947dd-b902-4949-bc04-8b8c52ec170b', 'RackName': 'slcs27', 'isMVM':'no', 'Dom0domUDetails':{},'ComputeNodeList':[],'StorageNodeList':[],'ComputeNodeListByAlias':[],
                                'AdditionalOptions': [
                                    {'AllowActiveNfsMounts': 'yes', 'ClusterLess': 'no', 'EnvType': 'ecs',
                                     'ForceRemoveCustomRpms': 'no', 'IgnoreAlerts': 'no', 'IgnoreDateValidation': 'yes',
                                     'IncludeNodeList': 'none', 'LaunchNode': 'none',
                                     'OneoffCustomPluginFile': 'none', 'OneoffScriptArgs': 'none',
                                     'RackSwitchesOnly': 'no', 'SingleUpgradeNodeName': 'none', 'SkipDomuCheck': 'no',
                                     'exasplice': 'no', 'isSingleNodeUpgrade': 'no', 'serviceType': 'EXACC',
                                     'exaunitId': 0}]}
        ebLogInfo("Ending classSetUp RoceSwitchHandler")

    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mSetEnvironment", return_value="")
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mCustomCheck", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mPatchRequestRetried", return_value=False)
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mRegularPatchRun", return_value=(SUCCESS_ERROR_CODE, 0))
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))      
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    def test_mPreCheck(self, mock_mSetEnvironment, mock_mCustomCheck, mock_mPatchRequestRetried, mock_mRegularPatchRun, mock_mGetPatchMgrCmd, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode):
        ebLogInfo("")
        ebLogInfo("Running unit test on SwitchHandler.mPreCheck")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("mkdir -p *", aPersist=True),
                    exaMockCommand(
                        "df -mP /EXAVMIMAGES/21.2.11.0.0.220414.1.patch.zip/ | tail -n1 | awk '{print $(NF - 2); }",
                        aStdout="4096"),
                    exaMockCommand("/bin/test -e *", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="", aPersist=True)
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -status", aStdout="success")
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/sha1sum *", aRc=0, aStdout=""),
                    exaMockCommand("/bin/awk *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/du -sh *", aRc=0, aStdout="")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _roceSwitchHandler = RoceSwitchHandler(self.__patch_args_dict)
        self.assertEqual(_roceSwitchHandler.mPreCheck(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetMasterReqId", return_value="a7714e6f-c242-4ba9-9ae0-98351caecc5a")
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExadataPatchWorkingSpaceMB", return_value=500)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellSwitchesPatchBaseAfterUnzip", return_values="/EXAVMIMAGES/21.2.11.0.0.220414.1.switch.patch.zip/patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.mGetFirstDirInZip", return_value="patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellSwitchesPatchBase", return_values="/EXAVMIMAGES/21.2.11.0.0.220414.1.switch.patch.zip/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellIBPatchZipName", return_values="21.2.11.0.0.220414.1.switch.patch.zip")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellSwitchesLocalPatchZip", return_values="/scratch/abherrer/ecra_installs/jul22/mw_home/user_projects/domains/exacloud/PatchPayloads/21.2.11.0.0.220414.1/SwitchPatchFile/21.2.11.0.0.220414.1.switch.patch.zip")
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mCustomCheck", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mPatchRequestRetried", return_value=False)
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mRegularPatchRun", return_value=(SUCCESS_ERROR_CODE, 0))
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))      
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    def test_mPatch(self, mock_mGetMasterReqId, mock_mGetExadataPatchWorkingSpaceMB, mock_mGetCellSwitchesPatchBaseAfterUnzip, mockmGetFirstDirInZip, mock_mGetCellSwitchesPatchBase, mock_mGetCellIBPatchZipName, mock_mGetCellSwitchesLocalPatchZip, mock_mCustomCheck, mock_mPatchRequestRetried, mock_mRegularPatchRun, mock_mGetPatchMgrCmd, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode):
        ebLogInfo("")
        ebLogInfo("Running unit test on SwitchHandler.mPatch")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("mkdir -p *", aPersist=True),
                    exaMockCommand(
                        "df -mP /EXAVMIMAGES/21.2.11.0.0.220414.1.patch.zip/ | tail -n1 | awk '{print $(NF - 2); }",
                        aStdout="4096"),
                    exaMockCommand("/bin/test -e *", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="", aPersist=True)
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -status", aStdout="success")
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/sha1sum *", aRc=0, aStdout=""),
                    exaMockCommand("/bin/awk *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/du -sh *", aRc=0, aStdout="")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _roceSwitchHandler = RoceSwitchHandler(self.__patch_args_dict)
        self.assertEqual(_roceSwitchHandler.mPatch(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetMasterReqId", return_value="a7714e6f-c242-4ba9-9ae0-98351caecc5a")
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExadataPatchWorkingSpaceMB", return_value=500)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellSwitchesPatchBaseAfterUnzip", return_values="/EXAVMIMAGES/21.2.11.0.0.220414.1.switch.patch.zip/patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.mGetFirstDirInZip", return_value="patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellSwitchesPatchBase", return_values="/EXAVMIMAGES/21.2.11.0.0.220414.1.switch.patch.zip/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellIBPatchZipName", return_values="21.2.11.0.0.220414.1.switch.patch.zip")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellSwitchesLocalPatchZip", return_values="/scratch/abherrer/ecra_installs/jul22/mw_home/user_projects/domains/exacloud/PatchPayloads/21.2.11.0.0.220414.1/SwitchPatchFile/21.2.11.0.0.220414.1.switch.patch.zip")
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mCustomCheck", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mPatchRequestRetried", return_value=False)
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mRegularPatchRun", return_value=(SUCCESS_ERROR_CODE, 0))
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))      
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    def test_mRollBack(self, mock_mGetMasterReqId, mock_mGetExadataPatchWorkingSpaceMB, mock_mGetCellSwitchesPatchBaseAfterUnzip, mockmGetFirstDirInZip, mock_mGetCellSwitchesPatchBase, mock_mGetCellIBPatchZipName, mock_mGetCellSwitchesLocalPatchZip, mock_mCustomCheck, mock_mPatchRequestRetried, mock_mRegularPatchRun, mock_mGetPatchMgrCmd, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode):
        ebLogInfo("")
        ebLogInfo("Running unit test on SwitchHandler.mRollBack")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("mkdir -p *", aPersist=True),
                    exaMockCommand(
                        "df -mP /EXAVMIMAGES/21.2.11.0.0.220414.1.patch.zip/ | tail -n1 | awk '{print $(NF - 2); }",
                        aStdout="4096"),
                    exaMockCommand("/bin/test -e *", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="", aPersist=True)
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -status", aStdout="success")
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/sha1sum *", aRc=0, aStdout=""),
                    exaMockCommand("/bin/awk *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/du -sh *", aRc=0, aStdout="")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _roceSwitchHandler = RoceSwitchHandler(self.__patch_args_dict)
        self.assertEqual(_roceSwitchHandler.mRollBack(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetMasterReqId", return_value="a7714e6f-c242-4ba9-9ae0-98351caecc5a")
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExadataPatchWorkingSpaceMB", return_value=500)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellSwitchesPatchBaseAfterUnzip", return_values="/EXAVMIMAGES/21.2.11.0.0.220414.1.switch.patch.zip/patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.mGetFirstDirInZip", return_value="patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellSwitchesPatchBase", return_values="/EXAVMIMAGES/21.2.11.0.0.220414.1.switch.patch.zip/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellIBPatchZipName", return_values="21.2.11.0.0.220414.1.switch.patch.zip")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetCellSwitchesLocalPatchZip", return_values="/scratch/abherrer/ecra_installs/jul22/mw_home/user_projects/domains/exacloud/PatchPayloads/21.2.11.0.0.220414.1/SwitchPatchFile/21.2.11.0.0.220414.1.switch.patch.zip")
    def test_mSetEnvironment(self, mock_mGetMasterReqId, mock_mGetExadataPatchWorkingSpaceMB, mock_mGetCellSwitchesPatchBaseAfterUnzip, mockmGetFirstDirInZip, mock_mGetCellSwitchesPatchBase, mock_mGetCellIBPatchZipName, mock_mGetCellSwitchesLocalPatchZip):
        ebLogInfo("")
        ebLogInfo("Running unit test on SwitchHandler.mSetEnvironment")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("mkdir -p *", aPersist=True),
                    exaMockCommand(
                        "df -mP /EXAVMIMAGES/21.2.11.0.0.220414.1.patch.zip/ | tail -n1 | awk '{print $(NF - 2); }",
                        aStdout="4096"),
                    exaMockCommand("/bin/test -e *", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="", aPersist=True)
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -status", aStdout="success")
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/sha1sum *", aRc=0, aStdout=""),
                    exaMockCommand("/bin/awk *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/du -sh *", aRc=0, aStdout="")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _roceSwitchHandler = RoceSwitchHandler(self.__patch_args_dict)
        _roceSwitchHandler.mSetEnvironment()

if __name__ == "__main__":
    unittest.main()

