#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_dom0handler.py /main/28 2026/02/03 08:57:52 nelango Exp $
#
# tests_dom0handler.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_dom0handler.py - Class for testing dom0 precheck, patch and rollback
#
#    DESCRIPTION
#      File for testing the Dom0 Handler operations regarding infrapatching.
#      (mPreCheck, mPatch, mRollBack)
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    03/17/26 - Unit tests for bug 38969712
#    rbhandar    03/27/26 - Bug 38453227 - AIM4ECS:0X03030012 - INDIVIDUAL
#                           PATCH REQUEST EXCEPTION DETECTED
#    bhpati      03/02/26 - Bug 38932171 - AIM4ECS:0X03030006 - DB SERVICES
#                           WERE NOT UP ON DOM0
#    nelango     01/30/26 - Bug 38901967: No ilom service state disabling
#    nelango     01/09/26 - Bug 38676078 - update ipmi tests
#    bhpati      10/23/25 - Display an Exadata Live Update (ELU) specific error
#                           message when nodes are registered with an invalid
#                           version.
#    remamid     03/27/25 - Unittest for vm startup post non-rolling patch
#                           failure bug 37635610
#    nelango     01/20/25 - Bug 37328906: ipmi servicestate checks during
#                           precheck
#    sdevasek    11/15/24 - Enh 37172948 - ISOLATE CRS/HEARTBEAT/DB HEALTH
#                           CHECKS TO A SEPARATE API BASED MODULE
#    bhpati      08/27/24 - A UNIT TEST CASE FOR BUG(S) 36802587
#    emekala     08/14/24 - ENH 36679949 - REMOVE OVERHEAD OF INDEPENDENT
#                           MONITORING PROCESS FROM INFRAPATCHING
#    avimonda    08/14/24 - Bug 36563684 - AIM4EXACLOUD:0X03040001 - VM PRECHECK
#                           EXCEPTION DETECTED. (23.4.1.2.1-DOMU)
#    emekala     07/30/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    emekala     06/28/24 - ENH 36748433 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE DOM0, CELL, IBSWITCH AND ROCESWITCH PATCHMGR
#                           CMDS
#    emekala     06/18/24 - ENH 36619025 - BUILD PATCHMGR AS AN OBJECT
#    araghave    05/29/24 - Bug 36640067 - EXACS | EXASPLICE PRECHECK IS
#                           FAILING WHERE EXASPLICE IS NOT APPLICABLE
#    araghave    05/08/24 - Bug 36543876 - ERROR OUT WHEN GRID HOME PATH BINARY
#                           DOES NOT EXISTS FOR CRS AUTOSTART ENABLED CHECK
#    araghave    02/23/24 - ER 36234905 - ENHANCEMENT REQUEST | EXACC GEN 2 |
#                           ENABLE SERVICESTATE OF INFRA ILOM DURING UPGRADE &
#                           DISABLE THEM AFTER UPGRADE
#    araghave    12/05/23 - Enh 35244586 - DISABLE PRE AND POST CHECKS NOT
#                           APPLICABLE DURING MONTHLY PATCHING
#    antamil     18/08/23 - ENH 35577433 - ADD VALIDATIONS ON EXTERNAL LAUNCH
#                           NODE PASSED
#    vikasras    08/03/23 - Bug 35671592 - AFTER REFRESHING TO THE RECENT LABEL
#                           TEST FILES ARE REPORTING COMPILATION ERROR
#    vikasras    06/27/23 - Bug 35456901 - MOVE RPM LIST TO INFRAPATCHING.CONF
#                           FOR SYSTEM CONSISTIENCY DUPLICATE RPM CHECK
#    araghave    12/06/22 - Bug 34592207 - INFRA PATCHING SHOULD FAIL WHEN ONE
#                           OF VM IS DOWN
#    araghave    10/27/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODE
#    jyotdas     10/18/22 - BUG 34681939 - Infrapatching compute nodes should
#                           be sorted by dbserver name from ecra
#    araghave    09/19/22 - ENH 34480945 - EXACS:22.2.1:MVM IMPLEMENTATION ON
#                           INFRA PATCHING CORE FILES
#    abherrer    07/05/22 - Enh 34349300 - Creation
#    abherrer    08/15/22 - Bug 34461211 - Stage 2 implementation
#
import copy
import unittest
from unittest.mock import patch, MagicMock, call
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.infrapatching.helpers.crshelper import CrsHelper
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.handlers.targetHandler.dom0handler import Dom0Handler
from exabox.core.MockCommand import exaMockCommand
from exabox.infrapatching.core.infrapatcherror import (
    INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR,
    SSH_AUTHENTICATION_FAILED,
    SSH_CONNECTION_TIMEOUT,
)

class ebTestDom0Handler(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"
    DBSERVER_DOWN_ERROR_CODE = "0x03010060"
    ELUVERSION_NOTFOUND_ERROR_CODE = "0x0301006F"
    UNABLE_TO_STARTUP_VM_ON_DOM0 = "0x03030021"
    PATCHMGR_COMMAND_FAILED = "0x03010045"
    OP_STYLE_NON_ROLLING = "non-rolling"
    crsHelper = CrsHelper(None)

    @classmethod
    def setUpClass(self):
        ebLogInfo("Starting classSetUp Dom0Handler")
        super(ebTestDom0Handler, self).setUpClass(aGenerateDatabase=True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption("repository_root", self.mGetPath(self))
        _cluCtrl = self.mGetClubox(self)
        _cluCtrl._exaBoxCluCtrl__kvm_enabled = True

        self.__patch_args_dict = {'CluControl': _cluCtrl,
                                'LocalLogFile': 'exabox/exatest/infrapatching/resources/patchmgr_logs',
                                'TargetType': ['cell'], 'Operation': 'patch_prereq_check', 'OperationStyle': 'auto',
                                'PayloadType': 'exadata_release', 'TargetEnv': 'production', 'EnablePlugins': 'no',
                                'PluginTypes': 'none',
                                'CellIBSwitchesPatchZipFile': 'exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/CellPatchFile/21.2.11.0.0.220414.1.patch.zip',
                                'Dom0DomuPatchZipFile': 'exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/CellPatchFile/21.2.11.0.0.220414.1.patch.zip', 'TargetVersion': '21.2.11.0.0.220414.1', 'ClusterID': 1,
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
        ebLogInfo("Ending classSetUp Dom0Handler")

    class DummyebCluSshSetup:
        def mSetSSHPasswordlessForInfraPatching(self, dummy_arg1, dummy_arg2):
            return None

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mSetEnvironment", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCRSHelper", return_value=crsHelper)
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mPerformDomuCrsCheckForAllClusters",return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGetGiHomePath", return_value=(SUCCESS_ERROR_CODE, '/u01/app/19.0.0.0/grid'))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsIsEnabled", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckDomuAvailability", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCustomizedDom0List", return_value=['slcs27adm03.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mValidateRootFsSpaceUsage", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27adm03.us.oracle.com'], []))
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetListOfDom0sWhereExasplicePatchCanBeApplied", return_value=(['slcs27adm03.us.oracle.com']))
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mCheckHwCriticalAlert", return_value=(False, [], []))
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mCheckKnownAlertHistory", return_value=False)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mCheckSystemConsitency", return_value=(True, None))
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mPingNode", return_value=True)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mCheckFileExistsOnRemoteNodes", return_value=(True,[]))
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mStartIptablesService", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mUpdateCurrentLaunchNodeDetailsInCorrespondingTaskHandlerInstance", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCreateNodesToBePatchedFile", return_value = '/tmp/node_list')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetDom0FileCode", return_value = '/tmp')
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetPatchMgrOutFiles", return_value = True)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetPatchMgrDiagFiles", return_value = True)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetPatchMgrMiscLogFiles", return_value = True)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mUpdateNodePatcherLogDir", return_value = True)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPreCheckFilesCleanup", return_value = True)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckIdemPotency", return_value = (SUCCESS_ERROR_CODE,0))
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCreateDirOnNodes", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.core.clupatchmetadata.mWritePatchInitialStatesToLaunchNodes", return_value = True)
    def test_mPreCheck(self, mock_mSetEnvironment, mock_mGetCRSHelper, mock_mPerformDomuCrsCheckForAllClusters, mock_mGetGiHomePath, mock_mCheckCrsIsEnabled, mock_mCheckDomuAvailability, mock_mGetCustomizedDom0List, mock_mValidateRootFsSpaceUsage, mock_mFilterNodesToPatch, mock_mGetListOfDom0sWhereExasplicePatchCanBeApplied, mock_mCheckHwCriticalAlert, mock_mCheckKnownAlertHistory, mock_mCheckSystemConsitency, mock_mPingNode, mock_mCheckTargetVersion, mock_mCheckFileExistsOnRemoteNodes, mock_mStartIptablesService, mock_mUpdateCurrentLaunchNodeDetailsInCorrespondingTaskHandlerInstance, mock_mGetPatchMgrCmd, mock_mCreateNodesToBePatchedFile, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode, mock_mGetDom0FileCode, mock_mGetPatchMgrOutFiles, mock_mGetPatchMgrDiagFiles, mock_mGetPatchMgrMiscLogFiles, mock_mUpdateNodePatcherLogDir, mock_mPreCheckFilesCleanup, mock_mCheckIdemPotency, mock_mCreateDirOnNodes, mock_mWritePatchInitialStatesToLaunchNodes):
        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mPreCheck")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                    exaMockCommand("/usr/local/bin/imageinfo -status", aStdout="success", aPersist=True),
                    exaMockCommand("cat /etc/oracle/olr.loc | grep 'crs_home' | cut -f 2 -d '='", aStdout="/u01/app/19.0.0.0/grid", aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /etc/libvirt/qemu/autostart/scaqan03dv0208.us.oracle.com.xml", aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /tmp/node_list", aStdout="", aPersist=True),
                    exaMockCommand("grep on_reboot /etc/libvirt/qemu/autostart/scaqan03dv0208.us.oracle.com.xml | grep -i 'restart'", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("awk '{print $2}'  /etc/mtab  | sort -u", aStdout="", aPersist=True),
                    exaMockCommand("rpm -qa --queryformat '%{ARCH} %{NAME}' | sort | uniq -c | sed -e 's/^ *//g' | egrep -v '^1|*'", aStdout="", aPersist=True),
                    exaMockCommand("find *", aStdout="", aPersist=True),
                    exaMockCommand("ps -ef | egrep -i 'patchmgr -' | egrep -vi 'grep|tail'", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("imageinfo -ver", aStdout="", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _dom0handler = Dom0Handler(self.__patch_args_dict)
        self.assertEqual(_dom0handler.mPreCheck(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.mGetFirstDirInZip", return_value="patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetSSHEnvSetUp")
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mSetSSHPasswordlessForInfraPatching", return_values="")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchImageBackupDom0Node", return_value=0)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetDom0ToPatchInitialDom0", return_values="slcs27adm03.us.oracle.com")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mSetLaunchNodeToPatchOtherDom0Nodes", return_value=(SUCCESS_ERROR_CODE, ['slcs27adm03.us.oracle.com']))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDom0DomUPatchZipFile", return_value=["exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/DBPatchFile/dbserver.patch.zip", "exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip,exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip"])
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGetGiHomePath", return_value=(SUCCESS_ERROR_CODE, '/u01/app/19.0.0.0/grid'))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsIsEnabled", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckDomuAvailability", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCustomizedDom0List", return_value=['slcs27adm03.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mValidateRootFsSpaceUsage", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27adm03.us.oracle.com'], []))
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetListOfDom0sWhereExasplicePatchCanBeApplied", return_value=(['slcs27adm03.us.oracle.com']))
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mPingNode", return_value=True)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchRollbackDom0sRolling", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchRollbackDom0sNonRolling", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCreateDirOnNodes", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckIdemPotency", return_value = (SUCCESS_ERROR_CODE,0))
    @patch("exabox.infrapatching.core.clupatchmetadata.mWritePatchInitialStatesToLaunchNodes", return_value = True)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCreateNodesToBePatchedFile", return_value = '/tmp/node_list')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))      
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mStartupVMsUponNonRollingPatchFailure", return_value = '')
    def test_mPatch(self, mock_mGetFirstDirInZip, mock_mSetSSHEnvSetUp, mock_mSetSSHPasswordlessForInfraPatching, mock_mPatchImageBackupDom0Node, mock_mGetDom0ToPatchInitialDom0, mock_mSetLaunchNodeToPatchOtherDom0Nodes, mock_mGetDom0DomUPatchZipFile, mock_mGetGiHomePath, mock_mCheckCrsIsEnabled, mock_mCheckDomuAvailability, mock_mGetCustomizedDom0List, mock_mValidateRootFsSpaceUsage, mock_mFilterNodesToPatch, mock_mGetListOfDom0sWhereExasplicePatchCanBeApplied, mock_mPingNode, mock_mCheckTargetVersion, mock_mPatchRollbackDom0sRolling, mock_mPatchRollbackDom0sNonRolling, mock_mCreateDirOnNodes, mock_mCheckIdemPotency, mock_mWritePatchInitialStatesToLaunchNodes, mock_mGetPatchMgrCmd, mock_mCreateNodesToBePatchedFile, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode, mock_mStartupVMsUponNonRollingPatchFailure):
        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mPatch")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                    exaMockCommand("awk '{print $2}'  /etc/mtab  | sort -u", aStdout="", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/dbserver_patch_22.220412/patch_states_data", aStdout="", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/patch_switch_21.2.11.0.0.220414.1/patch_states_data", aPersist=True),
                    exaMockCommand("cat /etc/oracle/olr.loc | grep 'crs_home' | cut -f 2 -d '='", aStdout="", aPersist=True),
                    exaMockCommand("ps -ef | egrep -i 'patchmgr -' | egrep -vi 'grep|tail'", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -status", aStdout="", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _dom0handler = Dom0Handler(self.__patch_args_dict)
        self.assertEqual(_dom0handler.mPatch(), (self.SUCCESS_ERROR_CODE, 0))
    

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.mGetFirstDirInZip", return_value="patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mIsElu", return_value = True)
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetEluTargetVersiontoNodeMappings", return_value = {"0.0.0.0.0.0":"slcs27adm03.us.oracle.com"})
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTargetVersion", return_value = "0.0.0.0.0.0")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetSSHEnvSetUp")
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mSetSSHPasswordlessForInfraPatching", return_values="")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchImageBackupDom0Node", return_value=0)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetDom0ToPatchInitialDom0", return_values="slcs27adm03.us.oracle.com")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mSetLaunchNodeToPatchOtherDom0Nodes", return_value=(SUCCESS_ERROR_CODE, ['slcs27adm03.us.oracle.com']))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDom0DomUPatchZipFile", return_value=["exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/DBPatchFile/dbserver.patch.zip", "exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip,exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip"])
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGetGiHomePath", return_value=(SUCCESS_ERROR_CODE, '/u01/app/19.0.0.0/grid'))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsIsEnabled", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckDomuAvailability", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCustomizedDom0List", return_value=['slcs27adm03.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mValidateRootFsSpaceUsage", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27adm03.us.oracle.com'], []))
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetListOfDom0sWhereExasplicePatchCanBeApplied", return_value=(['slcs27adm03.us.oracle.com']))
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mPingNode", return_value=True)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchRollbackDom0sRolling", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchRollbackDom0sNonRolling", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCreateDirOnNodes", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckIdemPotency", return_value = (SUCCESS_ERROR_CODE,0))
    @patch("exabox.infrapatching.core.clupatchmetadata.mWritePatchInitialStatesToLaunchNodes", return_value = True)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCreateNodesToBePatchedFile", return_value = '/tmp/node_list')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))      
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mStartupVMsUponNonRollingPatchFailure", return_value = '')
    def test_mPatch_mIsElu(self, mock_mIsElu, mock_mGetEluTargetVersiontoNodeMappings, mock_mGetTargetVersion, mock_mGetFirstDirInZip, mock_mSetSSHEnvSetUp, mock_mSetSSHPasswordlessForInfraPatching, mock_mPatchImageBackupDom0Node, mock_mGetDom0ToPatchInitialDom0, mock_mSetLaunchNodeToPatchOtherDom0Nodes, mock_mGetDom0DomUPatchZipFile, mock_mGetGiHomePath, mock_mCheckCrsIsEnabled, mock_mCheckDomuAvailability, mock_mGetCustomizedDom0List, mock_mValidateRootFsSpaceUsage, mock_mFilterNodesToPatch, mock_mGetListOfDom0sWhereExasplicePatchCanBeApplied, mock_mPingNode, mock_mCheckTargetVersion, mock_mPatchRollbackDom0sRolling, mock_mPatchRollbackDom0sNonRolling, mock_mCreateDirOnNodes, mock_mCheckIdemPotency, mock_mWritePatchInitialStatesToLaunchNodes, mock_mGetPatchMgrCmd, mock_mCreateNodesToBePatchedFile, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode, mock_mStartupVMsUponNonRollingPatchFailure):
        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mPatch")
        INVALID_REGISTERED_PATCH_VERSIONS = [ "0.0.0.0.0.0" ]

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                    exaMockCommand("awk '{print $2}'  /etc/mtab  | sort -u", aStdout="", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/dbserver_patch_22.220412/patch_states_data", aStdout="", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/patch_switch_21.2.11.0.0.220414.1/patch_states_data", aPersist=True),
                    exaMockCommand("cat /etc/oracle/olr.loc | grep 'crs_home' | cut -f 2 -d '='", aStdout="", aPersist=True),
                    exaMockCommand("ps -ef | egrep -i 'patchmgr -' | egrep -vi 'grep|tail'", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -status", aStdout="", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _dom0handler = Dom0Handler(self.__patch_args_dict)
        self.assertEqual(_dom0handler.mPatch(), (self.ELUVERSION_NOTFOUND_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.mGetFirstDirInZip", return_value="patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetSSHEnvSetUp")
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mSetSSHPasswordlessForInfraPatching", return_values="")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetDom0ToPatchInitialDom0", return_values="slcs27adm04.us.oracle.com")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mSetLaunchNodeToPatchOtherDom0Nodes", return_value=(SUCCESS_ERROR_CODE, ['slcs27adm03.us.oracle.com', 'slcs27adm04.us.oracle.com']))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDom0DomUPatchZipFile", return_value=["exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/DBPatchFile/dbserver.patch.zip", "exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip,exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip"])
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckDomuAvailability", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCustomizedDom0List", return_value=['slcs27adm03.us.oracle.com', 'slcs27adm04.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mValidateRootFsSpaceUsage", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27adm03.us.oracle.com', 'slcs27adm04.us.oracle.com'], []))
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mPingNode", return_value=True)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mRollbackIsAvailable", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchRollbackDom0sRolling", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCreateDirOnNodes", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.core.clupatchmetadata.mWritePatchInitialStatesToLaunchNodes", return_value = True)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckIdemPotency", return_value = (SUCCESS_ERROR_CODE,0))
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCreateNodesToBePatchedFile", return_value = '/tmp/node_list')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))      
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    def test_mRollBack(self, mock_mGetFirstDirInZip, mock_mSetSSHEnvSetUp, mock_mSetSSHPasswordlessForInfraPatching, mock_mGetDom0ToPatchInitialDom0, mock_mSetLaunchNodeToPatchOtherDom0Nodes, mock_mGetDom0DomUPatchZipFile, mock_mCheckDomuAvailability, mock_mGetCustomizedDom0List, mock_mFilterNodesToPatch, mock_mValidateRootFsSpaceUsage, mock_mPingNode, mock_mCheckTargetVersion, mock_mRollbackIsAvailable, mock_mSetPatchmgrLogPathOnLaunchNode, mock_mCreateDirOnNodes, mock_mWritePatchInitialStatesToLaunchNodesi, mock_mCheckIdemPotency, mock_mGetPatchMgrCmd, mock_mCreateNodesToBePatchedFile, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode):
        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mRollBack")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                    exaMockCommand("date *", aStdout="", aPersist=True),
                    exaMockCommand("stat -c '%Y' /EXAVMIMAGES/GuestImages/*/vm.cfg | sort -n | tail -n 1", aStdout="", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/dbserver_patch_22.220412/patch_states_data", aStdout="", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/patch_switch_21.2.11.0.0.220414.1/patch_states_data", aPersist=True)

                ],
                [
                    exaMockCommand("dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful and alertShortName=Hardware and severity=Critical' *", aStdout="", aPersist=True),
                    exaMockCommand("date *", aStdout="", aPersist=True),
                    exaMockCommand("stat -c '%Y' /EXAVMIMAGES/GuestImages/*/vm.cfg | sort -n | tail -n 1", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful' | egrep -i 'No link detected on required Ethernet|alert.chassis.fw.fpga-upgrade-blocked|Attribute Name : DiskFirmwareVersion *Required *: *ORAB'", aStdout="", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _dom0handler = Dom0Handler(self.__patch_args_dict)
        self.assertEqual(_dom0handler.mRollBack(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.mGetFirstDirInZip", return_value="patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetSSHEnvSetUp")
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mSetSSHPasswordlessForInfraPatching", return_values="")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetDom0ToPatchInitialDom0", return_values="slcs27adm04.us.oracle.com")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mSetLaunchNodeToPatchOtherDom0Nodes", return_value=(SUCCESS_ERROR_CODE, ['slcs27adm03.us.oracle.com', 'slcs27adm04.us.oracle.com']))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDom0DomUPatchZipFile", return_value=["exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/DBPatchFile/dbserver.patch.zip", "exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip,exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip"])
    def test_mSetEnvironment(self, mock_mGetFirstDirInZip, mock_mSetSSHEnvSetUp, mock_mSetSSHPasswordlessForInfraPatching, mock_mGetDom0ToPatchInitialDom0, mock_mSetLaunchNodeToPatchOtherDom0Nodes, mock_mGetDom0DomUPatchZipFile):
        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mSetEnvironment")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                    exaMockCommand("if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]*",aRc=0, aStdout="aaaasdasdafasfafa",aPersist=True),
                    exaMockCommand("ssh scaqab10adm02.us.oracle.com 'uptime'", aRc=0, aPersist=True),
                    exaMockCommand("ssh scaqab10adm01.us.oracle.com 'uptime'", aRc=0, aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/dabserver_patch_22.220412/patch_states_data", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/dbserver_patch_22.220412/patch_states_data", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/patch_switch_21.2.11.0.0.220414.1/patch_states_data", aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /etc/libvirt/qemu/autostart/scaqan03dv0208.us.oracle.com.xml", aStdout="", aPersist=True),
                    exaMockCommand("grep on_reboot /etc/libvirt/qemu/autostart/scaqan03dv0208.us.oracle.com.xml | grep -i 'restart'", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="", aPersist=True),
                    exaMockCommand("/bin/hostname -i", aStdout="", aPersist=True),
                    exaMockCommand("ssh-keygen -R *", aStdout="", aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i *", aStdout="", aPersist=True),
                    exaMockCommand("virsh list|tail -n+3|awk '{print $2}' | sed '/^$/d'", aPersist=True, aStdout="")
                ],
                [
                    exaMockCommand("awk '{print $2}'  /etc/mtab  | sort -u", aStdout="", aPersist=True),
                    exaMockCommand("rpm -qa --queryformat '%{ARCH} %{NAME}' | sort | uniq -c | sed -e 's/^ *//g' | egrep -v '*'", aStdout="", aPersist=True),
                    exaMockCommand("find *", aStdout="", aPersist=True),
                    exaMockCommand("ssh-keyscan -t rsa *", aStdout="", aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i *", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful and alertShortName=Hardware and severity=Critical' *", aStdout="", aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i *", aStdout="", aPersist=True),
                    exaMockCommand("sh -c 'echo aaaasdasdafasfafa >> ~/.ssh/authorized_keys'", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful' | egrep -i 'No link detected on required Ethernet|alert.chassis.fw.fpga-upgrade-blocked|Attribute Name : DiskFirmwareVersion *Required *: *ORAB'", aStdout="", aPersist=True),
                    exaMockCommand("sh -c 'echo aaaasdasdafasfafa >> ~/.ssh/authorized_keys'", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("imageinfo -ver", aStdout="", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _dom0handler = Dom0Handler(self.__patch_args_dict)
        _dom0handler.mSetEnvironment()

    def _mock_ipmi_commands(self, mock_execute_cmd, initial_state="enabled"):
        executed_cmds = []
        service_state = {"value": initial_state}

        def _execute_side_effect(command):
            executed_cmds.append(command)
            stdout = MagicMock()
            if "setval /SP/services/ipmi/servicestate enabled" in command:
                service_state["value"] = "enabled"
                stdout.readlines.return_value = ["Sun OEM setval command successful."]
            elif "setval /SP/services/ipmi/servicestate disabled" in command:
                service_state["value"] = "disabled"
                stdout.readlines.return_value = ["Sun OEM setval command successful."]
            elif "getval" in command:
                stdout.readlines.return_value = [f"Target Value: {service_state['value']}"]
            else:
                stdout.readlines.return_value = []
            return None, stdout, MagicMock()

        mock_execute_cmd.side_effect = _execute_side_effect
        return executed_cmds, service_state

    @patch("exabox.core.Node.exaBoxNode.mDisconnect")
    @patch("exabox.core.Node.exaBoxNode.mConnect")
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    def test_mCheckServiceStateOnDom0s_exacs_prepatch(self, mock_mCheckCondition, mock_mExecuteCmd, mock_mGetCmdExitStatus, mock_mConnect, mock_mDisconnect):

        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mUpdateServiceStateOnIlom for ExaCS prepatch")
        _dom0_list = ["slcs27adm04.us.oracle.com", "slcs27adm05.us.oracle.com"]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        executed_cmds, service_state = self._mock_ipmi_commands(mock_mExecuteCmd, initial_state="disabled")

        dom0handler = Dom0Handler(self.__patch_args_dict)
        with patch.object(dom0handler, "mIsExaCC", return_value=False):
            dom0handler.mUpdateServiceStateOnIlom(_dom0_list, "prepatch")

        enable_cmds = [cmd for cmd in executed_cmds if "setval /SP/services/ipmi/servicestate enabled" in cmd]
        disable_cmds = [cmd for cmd in executed_cmds if "setval /SP/services/ipmi/servicestate disabled" in cmd]

        self.assertGreater(len(enable_cmds), 0)
        self.assertEqual(len(disable_cmds), 0)
        self.assertEqual(service_state["value"], "enabled")

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mUpdateServiceStateOnIlom")
    def test_mUpdateServiceStateOnIlom_only_prepatch_called(self, mock_mUpdateServiceStateOnIlom):

        ebLogInfo("Running unit test to confirm Dom0 postpatch path is never invoked")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        dom0handler = Dom0Handler(self.__patch_args_dict)
        dom0handler.mPreCheck()

        phases = [call.args[1] for call in mock_mUpdateServiceStateOnIlom.call_args_list]
        self.assertNotIn("postpatch", phases)

    @patch("exabox.core.Node.exaBoxNode.mDisconnect")
    @patch("exabox.core.Node.exaBoxNode.mConnect")
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    def test_mCheckServiceStateOnDom0s_exacc_prepatch(self, mock_mCheckCondition, mock_mExecuteCmd, mock_mGetCmdExitStatus, mock_mConnect, mock_mDisconnect):

        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mUpdateServiceStateOnIlom for ExaCC prepatch")
        _dom0_list = ["slcs27adm04.us.oracle.com", "slcs27adm05.us.oracle.com"]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        executed_cmds, service_state = self._mock_ipmi_commands(mock_mExecuteCmd, initial_state="disabled")

        dom0handler = Dom0Handler(self.__patch_args_dict)
        with patch.object(dom0handler, "mIsExaCC", return_value=True):
            dom0handler.mUpdateServiceStateOnIlom(_dom0_list, "prepatch")

        enable_cmds = [cmd for cmd in executed_cmds if "setval /SP/services/ipmi/servicestate enabled" in cmd]
        disable_cmds = [cmd for cmd in executed_cmds if "setval /SP/services/ipmi/servicestate disabled" in cmd]

        self.assertGreater(len(enable_cmds), 0)
        self.assertEqual(len(disable_cmds), 0)
        self.assertEqual(service_state["value"], "enabled")

    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUListFromXml", return_value=[])
    @patch("exabox.core.Node.exaBoxNode.mDisconnect")
    @patch("exabox.core.Node.exaBoxNode.mIsConnected", return_value=True)
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect")
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    def test_mValidateServiceStateOnDom0s_exacs(self, mock_mCheckCondition, mock_mConnect, mock_mExecuteCmd, mock_mGetCmdExitStatus, mock_mIsConnected, mock_mDisconnect, mock_mGetDomUListFromXml):

        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mValidateServiceStateOnIlom for ExaCS")
        _dom0_list = ["slcs27adm04.us.oracle.com", "slcs27adm05.us.oracle.com"]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ipmitool sunoem getval /SP/services/ipmi/servicestate", aRc=0,
                                   aStdout="Target Value: enabled"),
                    exaMockCommand("ipmitool sunoem setval /SP/services/ipmi/service state enabled", aRc=0,
                                   aStdout="Sun OEM setval command successful."),
                    exaMockCommand("ipmitool sunoem getval /SP/services/ipmi/servicestate", aRc=0,
                                   aStdout="Target Value: enabled"),
                    exaMockCommand("virsh", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        dom0handler = Dom0Handler(self.__patch_args_dict)
        output_mock = MagicMock()
        output_mock.readlines.return_value = ["Target Value: enabled"]
        mock_mExecuteCmd.return_value = (None, output_mock, MagicMock())

        with patch.object(dom0handler, "mIsExaCC", return_value=False):
            _rc, _failed = dom0handler.mValidateServiceStateOnIlom(_dom0_list)

        self.assertEqual(_rc, self.SUCCESS_ERROR_CODE)
        self.assertEqual(_failed, [])
        target_connect = call(aHost=_dom0_list[0], aTimeout=30)
        self.assertIn(target_connect, mock_mConnect.mock_calls)
        mock_mExecuteCmd.assert_any_call("ipmitool sunoem getval /SP/services/ipmi/servicestate")
        self.assertGreater(len(mock_mDisconnect.mock_calls), 0)

    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUListFromXml", return_value=[])
    @patch("exabox.core.Node.exaBoxNode.mDisconnect")
    @patch("exabox.core.Node.exaBoxNode.mIsConnected", return_value=True)
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect")
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    def test_mValidateServiceStateOnDom0s_exacc(self, mock_mCheckCondition, mock_mConnect, mock_mExecuteCmd, mock_mGetCmdExitStatus, mock_mIsConnected, mock_mDisconnect, mock_mGetDomUListFromXml):

        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mValidateServiceStateOnIlom for ExaCC")
        _dom0_list = ["slcs27adm04.us.oracle.com", "slcs27adm05.us.oracle.com"]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ipmitool sunoem getval /SP/services/ipmi/servicestate", aRc=0,
                                   aStdout="Target Value: enabled"),
                    exaMockCommand("ipmitool sunoem setval /SP/services/ipmi/service state enabled", aRc=0,
                                   aStdout="Sun OEM setval command successful."),
                    exaMockCommand("ipmitool sunoem getval /SP/services/ipmi/servicestate", aRc=0,
                                   aStdout="Target Value: enabled"),
                    exaMockCommand("virsh", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        dom0handler = Dom0Handler(self.__patch_args_dict)
        output_mock = MagicMock()
        output_mock.readlines.return_value = ["Target Value: enabled"]
        mock_mExecuteCmd.return_value = (None, output_mock, MagicMock())

        with patch.object(dom0handler, "mIsExaCC", return_value=True):
            _rc, _failed = dom0handler.mValidateServiceStateOnIlom(_dom0_list)

        self.assertEqual(_rc, self.SUCCESS_ERROR_CODE)
        self.assertEqual(_failed, [])
        target_connect = call(aHost=_dom0_list[0], aTimeout=30)
        self.assertIn(target_connect, mock_mConnect.mock_calls)
        mock_mExecuteCmd.assert_any_call("ipmitool sunoem getval /SP/services/ipmi/servicestate")
        self.assertGreater(len(mock_mDisconnect.mock_calls), 0)

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.mGetFirstDirInZip", return_value="patch_switch_21.2.11.0.0.220414.1/")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetSSHEnvSetUp")
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mSetSSHPasswordlessForInfraPatching", return_values="")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchImageBackupDom0Node", return_value=0)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetDom0ToPatchInitialDom0", return_values="slcs27adm03.us.oracle.com")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mSetLaunchNodeToPatchOtherDom0Nodes", return_value=(SUCCESS_ERROR_CODE, ['slcs27adm03.us.oracle.com']))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDom0DomUPatchZipFile", return_value=["exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/DBPatchFile/dbserver.patch.zip", "exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip,exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip"])
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGetGiHomePath", return_value=(SUCCESS_ERROR_CODE, '/u01/app/19.0.0.0/grid'))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsIsEnabled", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckDomuAvailability", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCustomizedDom0List", return_value=['slcs27adm03.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mValidateRootFsSpaceUsage", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27adm03.us.oracle.com'], []))
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetListOfDom0sWhereExasplicePatchCanBeApplied", return_value=(['slcs27adm03.us.oracle.com']))
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mPingNode", return_value=True)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1)
    #@patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetOpStyle", return_value = OP_STYLE_NON_ROLLING)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchRollbackDom0sRolling", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mPatchRollbackDom0sNonRolling", return_value = DBSERVER_DOWN_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCreateDirOnNodes", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mCheckIdemPotency", return_value = (SUCCESS_ERROR_CODE,0))
    @patch("exabox.infrapatching.core.clupatchmetadata.mWritePatchInitialStatesToLaunchNodes", return_value = True)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCreateNodesToBePatchedFile", return_value = '/tmp/node_list')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))      
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    def test_mPatchNonRolling_testvmstartup(self, mock_mGetFirstDirInZip, mock_mSetSSHEnvSetUp, mock_mSetSSHPasswordlessForInfraPatching, mock_mPatchImageBackupDom0Node, mock_mGetDom0ToPatchInitialDom0, mock_mSetLaunchNodeToPatchOtherDom0Nodes, mock_mGetDom0DomUPatchZipFile, mock_mGetGiHomePath, mock_mCheckCrsIsEnabled, mock_mCheckDomuAvailability, mock_mGetCustomizedDom0List, mock_mValidateRootFsSpaceUsage, mock_mFilterNodesToPatch, mock_mGetListOfDom0sWhereExasplicePatchCanBeApplied, mock_mPingNode, mock_mCheckTargetVersion, mock_mPatchRollbackDom0sRolling, mock_mPatchRollbackDom0sNonRolling, mock_mCreateDirOnNodes, mock_mCheckIdemPotency, mock_mWritePatchInitialStatesToLaunchNodes, mock_mGetPatchMgrCmd, mock_mCreateNodesToBePatchedFile, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode):
        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mPatch for non-rolling")
        patch_args_dict = copy.deepcopy(self.__patch_args_dict)
        patch_args_dict['OperationStyle'] = 'non-rolling'
        patch_args_dict['Operation'] = 'patch'
        #print(f"test_mPatchNonRolling: \n {patch_args_dict}")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                    exaMockCommand("awk '{print $2}'  /etc/mtab  | sort -u", aStdout="", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/dbserver_patch_22.220412/patch_states_data", aStdout="", aPersist=True),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip/patch_switch_21.2.11.0.0.220414.1/patch_states_data", aPersist=True),
                    exaMockCommand("cat /etc/oracle/olr.loc | grep 'crs_home' | cut -f 2 -d '='", aStdout="", aPersist=True),
                    exaMockCommand("ps -ef | egrep -i 'patchmgr -' | egrep -vi 'grep|tail'", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -status", aStdout="success", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _dom0handler = Dom0Handler(patch_args_dict)
        self.assertEqual(_dom0handler.mPatch(), (self.DBSERVER_DOWN_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mValidateVIFBridgeInDom0", return_value="0x00000000")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mValidateDomUHeartBeatRdsAndCrsPostPatching", return_value="0x00000000")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mStartIptablesService", return_value="0x00000000")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetFedRamp", return_value="DISABLED")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetOpStyle", return_value="rolling")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetTimeoutForDom0DomuStartupInSeconds", return_value=5)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mIsExaSplice", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetInfrapatchExecutionValidator")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCluPatchCheck")
    def test_mPostDom0PatchCheck_skips_db_service_for_exasplice(self,
                                                                mock_get_clu_patch,
                                                                mock_get_validator,
                                                                mock_is_exasplice,
                                                                mock_timeout,
                                                                mock_get_op_style,
                                                                mock_get_fedramp,
                                                                mock_start_iptables,
                                                                mock_validate_hb,
                                                                mock_validate_vif):
        dom0handler = Dom0Handler(copy.deepcopy(self.__patch_args_dict))

        validator = MagicMock()
        validator.mCheckCondition.return_value = False
        mock_get_validator.return_value = validator

        clu_patch = MagicMock()
        clu_patch.mPingNode.return_value = True
        clu_patch.mCheckImageSuccess.return_value = True
        clu_patch.mCheckTargetVersion.return_value = 0
        clu_patch.mValidateAndEnableDomuAutoStartup.return_value = "0x00000000"
        clu_patch.mCheckVMsUp.return_value = True
        mock_get_clu_patch.return_value = clu_patch

        rc = dom0handler.mPostDom0PatchCheck(
            aDom0="test-dom0",
            aDomUList=["domu1"],
            aPrePatchVersion="25.1.10.0.0.251020",
            aPostPatchTargetVersion="25.1.13.0.0.260117",
            aRollback=False,
            aTaskType="patch"
        )

        self.assertEqual(rc, "0x00000000")
        clu_patch.mCheckDBServices.assert_not_called()

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.ProcessStructure")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.ProcessManager")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetVmExecutionTimeoutInSeconds", return_value=30)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCluPatchCheck")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mListOfDomusWithAutoStartEnabled")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mIsExaSplice", return_value=False)
    def test_mStartupVMsIfAutoStartEnabled_suppress_error(self, mock_mIsExaSplice, mock_mListOfDomusWithAutoStartEnabled, mock_mGetCluPatchCheck, mock_mGetVmExecutionTimeoutInSeconds, mock_ProcessManager, mock_ProcessStructure):

        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mStartupVMsIfAutoStartEnabled error handling")

        mock_mListOfDomusWithAutoStartEnabled.return_value = ['domu1']
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _clu_patch = MagicMock()
        _clu_patch.mCheckVMsUp.return_value = []
        mock_mGetCluPatchCheck.return_value = _clu_patch

        _rc_status = [{'status': 'failed', 'domu': 'domu1'}]
        _manager_mock = MagicMock()
        _manager_mock.list.return_value = _rc_status
        _process_manager = MagicMock()
        _process_manager.mGetManager.return_value = _manager_mock
        mock_ProcessManager.return_value = _process_manager
        mock_ProcessStructure.return_value = MagicMock()

        dom0handler = Dom0Handler(copy.deepcopy(self.__patch_args_dict))
        dom0handler.mAddError = MagicMock()

        _ret = dom0handler.mStartupVMsIfAutoStartEnabled("slcs27adm03.us.oracle.com", aSupressError=True)

        self.assertEqual(_ret, self.UNABLE_TO_STARTUP_VM_ON_DOM0)
        dom0handler.mAddError.assert_not_called()

        dom0handler.mAddError.reset_mock()
        _ret = dom0handler.mStartupVMsIfAutoStartEnabled("slcs27adm03.us.oracle.com")

        self.assertEqual(_ret, self.UNABLE_TO_STARTUP_VM_ON_DOM0)
        dom0handler.mAddError.assert_called_once_with(self.UNABLE_TO_STARTUP_VM_ON_DOM0, "Unable to startup VMs on Dom0 : slcs27adm03.us.oracle.com")

    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.ebPatchFormatBuildError", return_value=(PATCHMGR_COMMAND_FAILED, "patchmgr command failed with non-zero status.", None))
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mStartupVMsIfAutoStartEnabled", return_value=UNABLE_TO_STARTUP_VM_ON_DOM0)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCluPatchCheck")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetComputeNodeListSortedByAlias", return_value=["slcs27adm03.us.oracle.com"])
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetComputeNodeListFromPayload", return_value=["slcs27adm03.us.oracle.com"])
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetOpStyle", return_value="non-rolling")
    def test_mStartupVMsUponNonRollingPatchFailure_reports_original_status(self, mock_mGetOpStyle, mock_mGetComputeNodeListFromPayload, mock_mGetComputeNodeListSortedByAlias, mock_mGetCluPatchCheck, mock_mStartupVMsIfAutoStartEnabled, mock_ebPatchFormatBuildError):

        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mStartupVMsUponNonRollingPatchFailure for failure propagation")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _clu_patch = MagicMock()
        _clu_patch.mCheckImageSuccess.return_value = True
        mock_mGetCluPatchCheck.return_value = _clu_patch

        dom0handler = Dom0Handler(copy.deepcopy(self.__patch_args_dict))
        dom0handler.mAddError = MagicMock()
        dom0handler.mPatchLogWarn = MagicMock()

        dom0handler.mStartupVMsUponNonRollingPatchFailure(aStatus=self.PATCHMGR_COMMAND_FAILED)

        mock_mStartupVMsIfAutoStartEnabled.assert_called_once_with("slcs27adm03.us.oracle.com", aSupressError=True)
        dom0handler.mPatchLogWarn.assert_called_once()
        mock_ebPatchFormatBuildError.assert_called_once_with(self.PATCHMGR_COMMAND_FAILED)
        dom0handler.mAddError.assert_called_once_with(self.PATCHMGR_COMMAND_FAILED, "patchmgr command failed with non-zero status.")


    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.ebPatchFormatBuildError")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mStartupVMsIfAutoStartEnabled", return_value=UNABLE_TO_STARTUP_VM_ON_DOM0)
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetCluPatchCheck")
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetComputeNodeListSortedByAlias", return_value=["slcs27adm03.us.oracle.com"])
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetComputeNodeListFromPayload", return_value=["slcs27adm03.us.oracle.com"])
    @patch("exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler.mGetOpStyle", return_value="non-rolling")
    def test_mStartupVMsUponNonRollingPatchFailure_skips_error_for_success_status(self, mock_mGetOpStyle, mock_mGetComputeNodeListFromPayload, mock_mGetComputeNodeListSortedByAlias, mock_mGetCluPatchCheck, mock_mStartupVMsIfAutoStartEnabled, mock_ebPatchFormatBuildError):

        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mStartupVMsUponNonRollingPatchFailure for success status")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _clu_patch = MagicMock()
        _clu_patch.mCheckImageSuccess.return_value = True
        mock_mGetCluPatchCheck.return_value = _clu_patch

        dom0handler = Dom0Handler(copy.deepcopy(self.__patch_args_dict))
        dom0handler.mAddError = MagicMock()
        dom0handler.mPatchLogWarn = MagicMock()

        dom0handler.mStartupVMsUponNonRollingPatchFailure(aStatus=self.SUCCESS_ERROR_CODE)

        mock_mStartupVMsIfAutoStartEnabled.assert_called_once_with("slcs27adm03.us.oracle.com", aSupressError=True)
        dom0handler.mPatchLogWarn.assert_not_called()
        dom0handler.mAddError.assert_not_called()
        mock_ebPatchFormatBuildError.assert_not_called()



class Dom0HandlerSshMappingTests(unittest.TestCase):

    class _Dom0HandlerSshDummy(Dom0Handler):
        def __init__(self, error_msg):
            self._error_msg = error_msg
            self.mGetErrorCodeFromChildRequest = lambda: (None, False)
            self.mPatchLogError = MagicMock()
            self.mPatchLogTrace = MagicMock()
            self.mPatchLogInfo = ebLogInfo
            self.mAddError = MagicMock()

        def exercise(self):
            is_ssh_error, ssh_code = self.isSSHConnectivityError(self._error_msg)
            if is_ssh_error:
                code = ssh_code
                suggestion = self.mBuildSshSuggestion(code, self._error_msg)
            else:
                code = INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR
                suggestion = f"Exception in Running DOM0 Patch {self._error_msg}"
            self.mAddError(code, suggestion)
            return code, suggestion

    def test_non_ssh_message_uses_generic_fallback(self):
        message = "Unexpected failure reading metadata file"
        dummy = self._Dom0HandlerSshDummy(message)
        code, suggestion = dummy.exercise()
        dummy.mAddError.assert_called_once_with(code, suggestion)
        self.assertEqual(code, INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR)
        self.assertTrue(suggestion.startswith("Exception in Running DOM0 Patch"))
        self.assertIn(message.lower(), suggestion.lower())
        ebLogInfo(
            f"Dom0HandlerSshMappingTests.test_non_ssh_message_uses_generic_fallback mapped {code} "
            f"with suggestion: {suggestion}")

    def test_authentication_failure_message(self):
        message = (
            "Exception in Running DOM0 Patch Error: Bad authentication type; allowed types: ['publickey'] "
            "occurred while trying to read the patch states JSON file from the target node: "
            "vcp166901exdd001.oraclecloud.internal."
        )
        dummy = self._Dom0HandlerSshDummy(message)
        code, suggestion = dummy.exercise()
        dummy.mAddError.assert_called_once_with(code, suggestion)
        self.assertEqual(code, SSH_AUTHENTICATION_FAILED)
        self.assertIn("authentication", suggestion.lower())
        self.assertIn("vcp166901exdd001", suggestion)
        ebLogInfo(f"Dom0HandlerSshMappingTests.test_authentication_failure_message mapped {code} with suggestion: {suggestion}")

    def test_connection_timeout_message(self):
        message = (
            "Exception in Running DOM0 Patch [Errno 110] Connection timed out while contacting dom0. "
            "Check service logs from the target node: phx3dom0.example.internal"
        )
        dummy = self._Dom0HandlerSshDummy(message)
        code, suggestion = dummy.exercise()
        dummy.mAddError.assert_called_once_with(code, suggestion)
        self.assertEqual(code, SSH_CONNECTION_TIMEOUT)
        self.assertIn("timed out", suggestion.lower())
        self.assertIn("phx3dom0", suggestion)
        ebLogInfo(f"Dom0HandlerSshMappingTests.test_connection_timeout_message mapped {code} with suggestion: {suggestion}")
        
if __name__ == "__main__":
    unittest.main()
