#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_roceswitchhandler.py /main/9 2026/01/22 08:11:12 araghave Exp $
#
# tests_roceswitchhandler.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
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
#    araghave    01/19/26 - Bug 38861325 - ECS_MAIN ->
#                           TESTS_ROCESWITCHHANDLER_PY.DIF AND
#                           TESTS_TARGETHANDLER_PY.DIF IS FAILING IN
#                           ECS_MAIN_LINUX.X64_260116.0518
#    araghave    01/14/26 - Inline crypto constants in tests
#    araghave    12/16/25 - Enh 38766076 - CONFIGURE UPDATE-CRYPTO-POLICIES
#                           BEFORE AND AFTER SWITCH PATCHING
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
import io
import sys
from pathlib import Path

def _ensure_exacloud_on_path():
    current = Path(__file__).resolve()
    for parent in current.parents:
        package_root = parent / "exacloud"
        if (package_root / "__init__.py").exists():
            parent_path = str(parent)
            if parent_path not in sys.path:
                sys.path.insert(0, parent_path)
            package_root_path = str(package_root)
            if package_root_path not in sys.path:
                sys.path.insert(0, package_root_path)
            return
    raise ModuleNotFoundError("Unable to locate exacloud package root for tests_roceswitchhandler")

_ensure_exacloud_on_path()

CRYPTO_POLICY_DEFAULT_EXADATA = "DEFAULT:EXADATA"
CRYPTO_POLICY_DEFAULT = "DEFAULT"
CRYPTO_POLICY_SHOW_CMD = "/usr/bin/update-crypto-policies --show"
CRYPTO_POLICY_SET_CMD = "/usr/bin/update-crypto-policies --set {}"
import unittest
from unittest.mock import patch

from types import MethodType

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.handlers.targetHandler.roceswitchhandler import RoceSwitchHandler
from exabox.core.MockCommand import exaMockCommand

_LOCAL_HOST_STATE = {}


def _set_local_host(self, value):
    _LOCAL_HOST_STATE[id(self)] = value


def _get_local_host(self):
    return _LOCAL_HOST_STATE.get(id(self))


def _ensure_local_host_helpers(ctx):
    if not hasattr(ctx, "mSetLocalHost"):
        ctx.mSetLocalHost = MethodType(_set_local_host, ctx)
    if not hasattr(ctx, "mGetLocalHost"):
        ctx.mGetLocalHost = MethodType(_get_local_host, ctx)

class mockFileHandler():

    def __init__(self, fileoutput=None):
        self.terminal_op = fileoutput

    def read(self):
        if self.terminal_op is None:
            return ""
        if hasattr(self.terminal_op, "read"):
            return self.terminal_op.read()
        return str(self.terminal_op)

    def readlines(self):
        if self.terminal_op is None:
            return []
        if hasattr(self.terminal_op, "readlines"):
            return self.terminal_op.readlines()
        return []

class ebTestRoceSwitchHandler(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"

    @classmethod
    def setUpClass(self):
        ebLogInfo("Starting classSetUp RoceSwitchHandler")
        super(ebTestRoceSwitchHandler, self).setUpClass(aGenerateDatabase=False)
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

    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mIsCryptoPolicyResetEnabled", return_value=True)
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mIsExaCC", return_value=True)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect")
    @patch("exabox.core.Node.exaBoxNode.mIsConnected", return_value=False)
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mUpdateCryptoPolicyIfRequired", return_value=True)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetConnectionUser")
    @patch("exabox.core.Node.exaBoxNode.__init__", return_value=None)
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mRegularPatchRun", return_value=(SUCCESS_ERROR_CODE, 0))
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mPatchRequestRetried", return_value=False)
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mIsSwitchPatchingSkipped", return_value=False)
    @patch("exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler.mSetEnvironment")
    def test_mPatch_resets_crypto_policy(self, _mock_set_environment, _mock_is_skipped, _mock_patch_request_retried, _mock_regular_patch_run,
                                         _mock_node_init, _mock_set_connection_user, _mock_connect, _mock_execute_cmd, _mock_update_crypto, _mock_get_exit_status,
                                         _mock_is_connected, _mock_disconnect, _mock_is_exacc, _mock_is_enabled):
        ebLogInfo("")
        ebLogInfo("Running unit test on RoceSwitchHandler.mPatch crypto policy reset")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="slcs27adm03.us.oracle.com"),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        def _execute_side_effect(aCmd, *args, **kwargs):
            if aCmd == CRYPTO_POLICY_SHOW_CMD:
                return (None, mockFileHandler(io.StringIO(f"{CRYPTO_POLICY_DEFAULT_EXADATA}\n")), None)
            if aCmd in [CRYPTO_POLICY_SET_CMD.format(CRYPTO_POLICY_DEFAULT), CRYPTO_POLICY_SET_CMD.format(CRYPTO_POLICY_DEFAULT_EXADATA)]:
                return (None, mockFileHandler(), None)
            return (None, mockFileHandler(), None)

        _mock_execute_cmd.side_effect = _execute_side_effect

        _roceSwitchHandler = RoceSwitchHandler(self.__patch_args_dict)
        _context = _roceSwitchHandler.mGetCluControl().mGetCtx()
        _ensure_local_host_helpers(_context)
        _context.mSetLocalHost("slcs27adm03.us.oracle.com")

        _ret, _no_action = _roceSwitchHandler.mPatch()

        self.assertEqual((_ret, _no_action), (self.SUCCESS_ERROR_CODE, 0))
        _mock_execute_cmd.assert_called()

        ebLogInfo("Unit test on RoceSwitchHandler.mPatch crypto policy reset executed successfully")

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
