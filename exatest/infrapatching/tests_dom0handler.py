#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_dom0handler.py /main/26 2025/10/28 14:13:31 bhpati Exp $
#
# tests_dom0handler.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
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
from unittest.mock import patch
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.infrapatching.helpers.crshelper import CrsHelper
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.handlers.targetHandler.dom0handler import Dom0Handler
from exabox.core.MockCommand import exaMockCommand

class ebTestDom0Handler(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"
    DBSERVER_DOWN_ERROR_CODE = "0x03010060"
    ELUVERSION_NOTFOUND_ERROR_CODE = "0x0301006F"
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

    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mUpdateServiceStateOnIlom", return_value=('0x0301006A', ["slcs27adm04.us.oracle.com", "slcs27adm05.us.oracle.com"]))
    def test_mCheckServiceStateOnDom0s(self, mock_mCheckCondition,mock_mUpdateServiceStateOnIlom):

        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mUpdateServiceStateOnIlom")
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
        dom0handler.mUpdateServiceStateOnIlom(_dom0_list, "prepatch")
        dom0handler.mUpdateServiceStateOnIlom(_dom0_list, "postcheck")
        ebLogInfo("")
        
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mValidateServiceStateOnIlom", return_value=('0x03010069', ["slcs27adm04.us.oracle.com", "slcs27adm05.us.oracle.com"]))
    def test_mValidateServiceStateOnDom0s(self, mock_mCheckCondition,mock_mValidateServiceStateOnIlom):
        
        ebLogInfo("")
        ebLogInfo("Running unit test on Dom0Handler.mValidateServiceStateOnIlom")
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
        dom0handler.mValidateServiceStateOnIlom(_dom0_list)

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
        
if __name__ == "__main__":
    unittest.main()
