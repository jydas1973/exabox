#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_cellhandler.py /main/24 2026/02/21 03:43:32 nelango Exp $
#
# tests_cellhandler.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cellhandler.py - Class for testing cell precheck, patch and rollback
#
#    DESCRIPTION
#      File for testing the Cell Handler operations regarding infrapatching.
#      (mPreCheck, mPatch, mRollBack)
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    nelango     02/19/26 - Bug 38930043 : unittest for ssh key removal in
#                           cells during ecra switchover
#    nelango     01/30/26 - Bug 38901967: No ilom service state disabling
#    nelango     01/09/26 - Bug 38676078 - update ipmi tests
#    avimonda    09/12/25 - Bug 38293914 - OCI: MISLEADING ERROR IN THE ECACLI
#                           STATUS FOR EXACLOUD
#    nelango     01/20/25 - Bug 37328906: ipmi servicestate checks during
#                           precheck
#    avimonda    01/11/25 - Bug 37232903 - AIM4ECS:0X03010010 - TASK HANDLER
#                           PATCH REQUEST EXCEPTION DETECTED.
#    avimonda    09/16/24 - Enhancement Request 36775120 - EXACLOUD TIMEOUT
#                           MUST BE CALCULATED BASED ON THE PATCH OPERATION
#                           AND TARGET TYPE
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
#    araghave    05/15/24 - Bug 36599891 - EXACC|GEN2|INFRA PATCHING|CELL
#                           PRECEHCK MARKED SUCCESS THOUGH THERE WAS FAILURE
#    araghave    02/23/24 - ER 36234905 - ENHANCEMENT REQUEST | EXACC GEN 2 |
#                           ENABLE SERVICESTATE OF INFRA ILOM DURING UPGRADE &
#                           DISABLE THEM AFTER UPGRADE
#    avimonda    11/30/23 - Bug 35972504 - Bug 35972504 - EXACS | EXACLOUD
#                           TAKES 10HOURS FOR CELL PATCH CLEANUP
#    antamil     18/08/23 - ENH 35577433 - ADD VALIDATIONS ON EXTERNAL LAUNCH
#                           NODE PASSED
#    araghave    06/27/23 - Enh 35479785 - PARAMETERISE TO ENABLE PERFORMING
#                           SPACE VALIDATIONS ON INDIVIDUAL TARGETS
#    sdevasek    12/06/22 - ENH 34743194 - UPDATE INFRAPATCHING TEST CODE
#                           TO MAKE AUTOMATION TO WORK IN X9M R1 ENV
#    jyotdas     10/18/22 - BUG 34681939 - Infrapatching compute nodes should
#                           be sorted by dbserver name from ecra
#    araghave    09/19/22 - ENH 34480945 - EXACS:22.2.1:MVM IMPLEMENTATION ON
#                           INFRA PATCHING CORE FILES
#    abherrer    06/22/22 - Bug 34304034 - Creation
#    abherrer    06/22/22 - Bug 34390250 - Stage 2 implementation
#

import unittest
from unittest.mock import patch, MagicMock, call
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.handlers.targetHandler.cellhandler import CellHandler
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.infrapatching.utils.constants import EXAPATCHING_KEY_TAG
from exabox.ovm.clumisc import ebCluSshSetup

cmdHypervisorOutput="""xen
b25bc434-c151-4b83-abf4-a6cfdca28ee8
"""

class ebTestCellHandler(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"
    FAIL_ERROR_CODE = "0x00000001"

    class DummyManager:
        def __init__(self):
            self.dummy_list = []

        def list(self):
            return self.dummy_list

    class DummyProcess:
        def __init__(self):
            pass

        def start(self):
            pass

    @classmethod
    def setUpClass(self):
        ebLogInfo("Starting classSetUp CellHandler")
        super(ebTestCellHandler, self).setUpClass(aGenerateDatabase=True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption("repository_root", self.mGetPath(self))
        _cluCtrl = self.mGetClubox(self)
        _cluCtrl._exaBoxCluCtrl__kvm_enabled = True
        self.__patch_args_dict = {'CluControl': _cluCtrl, 'LocalLogFile': 'exabox/exatest/infrapatching/resources/patchmgr_logs', 'TargetType': ['cell'], 'Operation': 'patch_prereq_check', 'OperationStyle': 'auto', 'PayloadType': 'exadata_release', 'TargetEnv': 'production', 'EnablePlugins': 'no', 'PluginTypes': 'none', 'CellIBSwitchesPatchZipFile': 'exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/CellPatchFile/21.2.11.0.0.220414.1.patch.zip', 'Dom0DomuPatchZipFile': '', 'TargetVersion': '21.2.11.0.0.220414.1', 'ClusterID': 1, 'BackupMode': 'yes', 'Fedramp': 'DISABLED', 'Retry': 'no', 'RequestId': 'e2f947dd-b902-4949-bc04-8b8c52ec170b', 'RackName': 'slcs27', 'isMVM':'no','Dom0domUDetails':{}, 'ComputeNodeList':[], 'StorageNodeList':[], 'ComputeNodeListByAlias':[], 'AdditionalOptions': [{'AllowActiveNfsMounts': 'yes', 'ClusterLess': 'no', 'EnvType': 'ecs', 'ForceRemoveCustomRpms': 'no', 'IgnoreAlerts': 'no', 'IgnoreDateValidation': 'yes', 'IncludeNodeList': 'none', 'LaunchNode': 'none', 'OneoffCustomPluginFile': 'none', 'OneoffScriptArgs': 'none', 'RackSwitchesOnly': 'no', 'SingleUpgradeNodeName': 'none', 'SkipDomuCheck': 'no', 'exasplice': 'no', 'isSingleNodeUpgrade': 'no', 'serviceType': 'EXACC', 'exaunitId': 0}]}
        ebLogInfo("Ending classSetUp CellHandler")

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mRegularPatchRun", return_value=(SUCCESS_ERROR_CODE, 0)) # todo separate method
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetCustomizedCellList", return_value=['slcs27celadm04.us.oracle.com', 'slcs27celadm05.us.oracle.com', 'slcs27celadm06.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mPrePostCellCheck", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetcellSwitchesBaseEnvironment", return_value=None) # candidate for separate test method
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetDom0ToPatchcellSwitches", return_value=(SUCCESS_ERROR_CODE, [])) # candidate for separate test method
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExecutedTargets", return_value=[])
    def test_mPreCheck(self, mock_mRegularPatchRun, mock_mGetCustomizedCellList, mock_mPrePostCellCheck, mock_mSetcellSwitchesBaseEnvironment, mock_mSetDom0ToPatchcellSwitches, mock_mGetExecutedTargets):
        ebLogInfo("")
        ebLogInfo("Running unit test on CellHandler.mPreCheck")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cellHandler = CellHandler(self.__patch_args_dict)
        self.assertEqual(cellHandler.mPreCheck(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetTask", return_value="")
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mRegularPatchRun", return_value=(SUCCESS_ERROR_CODE,0))
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetcellSwitchesBaseEnvironment", return_value=None) # candidate for separate test method
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetDom0ToPatchcellSwitches", return_value=(SUCCESS_ERROR_CODE, [])) # candidate for separate test method
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExecutedTargets", return_value=[])
    def test_mPatch(self, mock_mGetTask, mock_mRegularPatchRun, mock_mSetcellSwitchesBaseEnvironment, mock_mSetDom0ToPatchcellSwitches, mock_mGetExecutedTargets):
        ebLogInfo("")
        ebLogInfo("Running unit test on CellHandler.mPatch")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cellHandler = CellHandler(self.__patch_args_dict)
        self.assertEqual(cellHandler.mPatch(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetTask", return_value="rollback")
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mRegularPatchRun", return_value=(SUCCESS_ERROR_CODE,0))
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetcellSwitchesBaseEnvironment", return_value=None) # candidate for separate test method
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetDom0ToPatchcellSwitches", return_value=(SUCCESS_ERROR_CODE,[])) # candidate for separate test method
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExecutedTargets", return_value=[])
    def test_mRollBack(self, mock_mGetTask, mock_mRegularPatchRun, mock_mSetcellSwitchesBaseEnvironment, mock_mSetDom0ToPatchcellSwitches, mock_mGetExecutedTargets):
        ebLogInfo("")
        ebLogInfo("Running unit test on CellHandler.mRollBack")
        # exaMockCommand("/usr/local/bin/imageinfo -status", aStdout="success")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cellHandler = CellHandler(self.__patch_args_dict)
        self.assertEqual(cellHandler.mRollBack(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetTask", return_value="rollback_prereq_check")
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27celadm04.us.oracle.com', 'slcs27celadm05.us.oracle.com', 'slcs27celadm06.us.oracle.com'], []))
    @patch("exabox.BaseServer.AsyncProcessing.ProcessManager.mGetManager", return_value=DummyManager())
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetFabric", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mValidateRootFsSpaceUsage", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mPrepareEnvironment", return_value=('ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAyrLIeOTaFwEMybxhKpgPCe8GuDm6+Z0c9aFkMsLI+A87vBhiBvBqOlcW6n/iGMHz4fMQAulgoPm1aGj2wLvGjKt7kVpEswgIitUOFO5gOw5Owp5LlcS4dNRvacN+QugHqqWIYjcvEoDnjyYQ/hz/Hhhj5YSymeMRbvmHGXAK5zCyivyWoyUOsAYMF0VgmDZ8C64F3ULS/Edk8REt/LdszX9Q4QTd9HvZTlCHpHX4Uq41Jc5ujvwti1iwmfX9dPbaEHhnQm7hemXKD78uTrV2+OVrg54jFgnK56IjUUwYwJnBBCVaWfAHN/slrZiyYn76+qckz1+s68gZ6ly1MD5Pvw== EXACMISC KEY', '/EXAVMIMAGES/21.2.11.0.0.220414.1.patch.zip/patch_21.2.11.0.0.220414.1/node_list'))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetShutDownServices", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mVMOperation", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mPatchCellsRollingNonRolling", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckCellServices", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mCellsCleanUp", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mCleanEnvironment")
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCreateNodesToBePatchedFile", return_value = '/tmp/a')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))      
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    def test_mRegularPatchRun(self, mock_mGetTask, mock_mFilterNodesToPatch, mock_mGetManager, mock_mGetFabric, mValidateRootFsSpaceUsage, mock_mPrepareEnvironment, mock_mGetShutDownServices, mock_mVMOperation, mPatchCellsRollingNonRolling, mock_mCheckCellServices, mock_mCellsCleanUp, mock_mCleanEnvironment, mock_mGetPatchMgrCmd, mock_mCreateNodesToBePatchedFile, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode):
        ebLogInfo("")
        ebLogInfo("Running unit test on CellHandler.mRegularPatchRun")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0"),
                    exaMockCommand("cat /sys/hypervisor/type", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: GUEST"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdHypervisorOutput,
                                   aPersist=True),
                    exaMockCommand("xm shutdown scaqan03dv0208.us.oracle.com", aPersist=True),
                    exaMockCommand("xm list", aPersist=True)
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("imageinfo -ver", aStdout="", aPersist=True),
                    exaMockCommand("imageinfo -status", aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e \"list cell detail\" | grep running", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo | grep 'Rollback to the inactive partitions: Impossible'", aRc="1", aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name,asmmodestatus,asmdeactivationoutcome where asmmodestatus='ONLINE' and asmdeactivationoutcome !='Yes'", aPersist=True)

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cellHandler = CellHandler(self.__patch_args_dict)
        self.assertEqual(cellHandler.mRegularPatchRun(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetTask", return_value="patch")
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27celadm04.us.oracle.com', 'slcs27celadm05.us.oracle.com', 'slcs27celadm06.us.oracle.com'], []))
    @patch("exabox.BaseServer.AsyncProcessing.ProcessManager.mGetManager", return_value=DummyManager())
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetFabric", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mValidateRootFsSpaceUsage", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mPrepareEnvironment", return_value=('ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAyrLIeOTaFwEMybxhKpgPCe8GuDm6+Z0c9aFkMsLI+A87vBhiBvBqOlcW6n/iGMHz4fMQAulgoPm1aGj2wLvGjKt7kVpEswgIitUOFO5gOw5Owp5LlcS4dNRvacN+QugHqqWIYjcvEoDnjyYQ/hz/Hhhj5YSymeMRbvmHGXAK5zCyivyWoyUOsAYMF0VgmDZ8C64F3ULS/Edk8REt/LdszX9Q4QTd9HvZTlCHpHX4Uq41Jc5ujvwti1iwmfX9dPbaEHhnQm7hemXKD78uTrV2+OVrg54jFgnK56IjUUwYwJnBBCVaWfAHN/slrZiyYn76+qckz1+s68gZ6ly1MD5Pvw== EXACMISC KEY', '/EXAVMIMAGES/21.2.11.0.0.220414.1.patch.zip/patch_21.2.11.0.0.220414.1/node_list'))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetShutDownServices", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mVMOperation", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mPatchCellsRollingNonRolling", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckCellServices", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mCellsCleanUp", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mCleanEnvironment")
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCreateNodesToBePatchedFile", return_value = '/tmp/a')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value = (SUCCESS_ERROR_CODE, 'slcs27adm03.us.oracle.com'))      
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mExecutePatchMgrCmd", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mWaitForPatchMgrCmdExecutionToComplete", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetStatusCode", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGatherCellPreCheckData", return_value={})
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mUpdateServiceStateOnIlom", return_value=(SUCCESS_ERROR_CODE, []))
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetPluginMetadata", return_value=[])
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mDoCellPostCheck", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetCellCount", return_value=0)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetCellList", return_value=['slcs27celadm04.us.oracle.com', 'slcs27celadm05.us.oracle.com', 'slcs27celadm06.us.oracle.com'])
    @patch("exabox.exakms.ExaKmsEndpoint.ExaKmsEndpoint")
    @patch("multiprocessing.Process", return_value=DummyProcess())
    def test_mRegularPatchRun_for_patch(self, mock_mGetTask, mock_mFilterNodesToPatch, mock_mGetManager, mock_mGetFabric, mValidateRootFsSpaceUsage, mock_mPrepareEnvironment, mock_mGetShutDownServices, mock_mVMOperation, mPatchCellsRollingNonRolling, mock_mCheckCellServices, mock_mCellsCleanUp, mock_mCleanEnvironment, mock_mGetPatchMgrCmd, mock_mCreateNodesToBePatchedFile, mock_mCheckForPatchMgrSessionExistence, mock_mExecutePatchMgrCmd, mock_mWaitForPatchMgrCmdExecutionToComplete, mock_mGetStatusCode, mock_mGatherCellPreCheckData, mock_mUpdateServiceStateOnIlom, mock_mGetPluginMetadata, mock_mDoCellPostCheck, mock_mGetCellCount, mock_mGetCellList, mock_ExaKmsEndpoint, mock_Process):
        ebLogInfo("")
        ebLogInfo("Running unit test on CellHandler.mRegularPatchRun for patch")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0"),
                    exaMockCommand("cat /sys/hypervisor/type", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: GUEST"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdHypervisorOutput,
                                   aPersist=True),
                    exaMockCommand("xm shutdown scaqan03dv0208.us.oracle.com", aPersist=True),
                    exaMockCommand("xm list", aPersist=True)
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("imageinfo -ver", aStdout="", aPersist=True),
                    exaMockCommand("imageinfo -status", aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e \"list cell detail\" | grep running", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo | grep 'Rollback to the inactive partitions: Impossible'", aRc="1", aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name,asmmodestatus,asmdeactivationoutcome where asmmodestatus='ONLINE' and asmdeactivationoutcome !='Yes'", aPersist=True)

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cellHandler = CellHandler(self.__patch_args_dict)
        self.assertEqual(cellHandler.mRegularPatchRun(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetTask", return_value="patch")
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27celadm04.us.oracle.com', 'slcs27celadm05.us.oracle.com', 'slcs27celadm06.us.oracle.com'], []))
    @patch("exabox.BaseServer.AsyncProcessing.ProcessManager.mGetManager", return_value=DummyManager())
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetFabric", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mValidateRootFsSpaceUsage", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mPrepareEnvironment", return_value=('ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAyrLIeOTaFwEMybxhKpgPCe8GuDm6+Z0c9aFkMsLI+A87vBhiBvBqOlcW6n/iGMHz4fMQAulgoPm1aGj2wLvGjKt7kVpEswgIitUOFO5gOw5Owp5LlcS4dNRvacN+QugHqqWIYjcvEoDnjyYQ/hz/Hhhj5YSymeMRbvmHGXAK5zCyivyWoyUOsAYMF0VgmDZ8C64F3ULS/Edk8REt/LdszX9Q4QTd9HvZTlCHpHX4Uq41Jc5ujvwti1iwmfX9dPbaEHhnQm7hemXKD78uTrV2+OVrg54jFgnK56IjUUwYwJnBBCVaWfAHN/slrZiyYn76+qckz1+s68gZ6ly1MD5Pvw== EXACMISC KEY', '/EXAVMIMAGES/21.2.11.0.0.220414.1.patch.zip/patch_21.2.11.0.0.220414.1/node_list'))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetShutDownServices", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mVMOperation", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGatherCellPreCheckData", return_value={})
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckCellServices", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mUpdateServiceStateOnIlom", return_value=(SUCCESS_ERROR_CODE, []))
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetPluginMetadata", return_value=[])
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mPatchCellsRollingNonRolling", return_value=FAIL_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mCheckAndUpdateNodeList", return_value=['slcs27celadm04.us.oracle.com', 'slcs27celadm05.us.oracle.com', 'slcs27celadm06.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCreateNodesToBePatchedFile", return_value = '/tmp/a')
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mCellsCleanUp")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mCleanEnvironment")
    def test_mRegularPatchRun_for_patch_failure(self, mock_mCleanEnvironment, mock_mCellsCleanUp, mock_mCreateNodesToBePatchedFile, mock_mCheckAndUpdateNodeList, mock_mPatchCellsRollingNonRolling, mock_mGetPluginMetadata, mock_mUpdateServiceStateOnIlom, mock_mCheckCellServices, mock_mGatherCellPreCheckData, mock_mVMOperation, mock_mGetShutDownServices, mock_mPrepareEnvironment, mock_mValidateRootFsSpaceUsage, mock_mGetFabric, mock_mGetManager, mock_mFilterNodesToPatch, mock_mGetTask):
        ebLogInfo("")
        ebLogInfo("Running unit test on CellHandler.mRegularPatchRun for patch failure")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0"),
                    exaMockCommand("cat /sys/hypervisor/type", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: GUEST"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdHypervisorOutput,
                                   aPersist=True),
                    exaMockCommand("xm shutdown scaqan03dv0208.us.oracle.com", aPersist=True),
                    exaMockCommand("xm list", aPersist=True)
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("imageinfo -ver", aStdout="", aPersist=True),
                    exaMockCommand("imageinfo -status", aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e \"list cell detail\" | grep running", aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo | grep 'Rollback to the inactive partitions: Impossible'", aRc="1", aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name,asmmodestatus,asmdeactivationoutcome where asmmodestatus='ONLINE' and asmdeactivationoutcome !='Yes'", aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cellHandler = CellHandler(self.__patch_args_dict)
        result = cellHandler.mRegularPatchRun()
        self.assertEqual(result, (self.FAIL_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetCellSwitchesPatchBaseAfterUnzip", return_value="/EXAVMIMAGES/22.1.15.0.0.231006.patch.zip/patch_22.1.15.0.0.231006/")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmdAsync")
    @patch("exabox.utils.node.exaBoxNode.mGetCmdExitStatus", return_value="0")
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetPatchMgrCmd", return_value = '')
    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCreateNodesToBePatchedFile", return_value = '/tmp/a')
    def test_mCellsCleanUp(self, mock_mGetCellSwitchesPatchBaseAfterUnzip, mock_mExecuteCmdAsync, mock_mGetCmdExitStatus, mock_mGetPatchMgrCmd, mock_mCreateNodesToBePatchedFile):
        ebLogInfo("")
        ebLogInfo("Running unit test on CellHandler.mCellsCleanUp")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ]
            ],
        }
        self.mPrepareMockCommands(_cmds)
        cellHandler = CellHandler(self.__patch_args_dict)
        input_file="/EXAVMIMAGES/22.1.15.0.0.231006.patch.zip/patch_22.1.15.0.0.231006/node_list"
        self.assertEqual(cellHandler.mCellsCleanUp(input_file, cellHandler.mGetCallBacks()), '0x00000000')

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
    @patch("exabox.core.Node.exaBoxNode.mIsConnected", return_value=True)
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect")
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    def test_mValidateServiceStateOnCells_exacs(self, mock_mCheckCondition, mock_mConnect, mock_mExecuteCmd, mock_mGetCmdExitStatus, mock_mIsConnected, mock_mDisconnect):

        ebLogInfo("")
        ebLogInfo("Running unit test on Cellhandler.mValidateServiceStateOnIlom for ExaCS")
        _cell_list = ["slcs27celadm04.us.oracle.com"]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("ipmitool sunoem getval /SP/services/ipmi/servicestate", aRc=0,
                                   aStdout="Target Value: enabled"),
                    exaMockCommand("ipmitool sunoem setval /SP/services/ipmi/service state enabled", aRc=0,
                                   aStdout="Sun OEM setval command successful."),
                    exaMockCommand("ipmitool sunoem getval /SP/services/ipmi/servicestate", aRc=0,
                                   aStdout="Target Value: enabled")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        output_mock = MagicMock()
        output_mock.readlines.return_value = ["Target Value: enabled"]
        mock_mExecuteCmd.return_value = (None, output_mock, MagicMock())

        cellHandler = CellHandler(self.__patch_args_dict)
        with patch.object(cellHandler, "mIsExaCC", return_value=False):
            _rc, _failed = cellHandler.mValidateServiceStateOnIlom(_cell_list)

        self.assertEqual(_rc, self.SUCCESS_ERROR_CODE)
        self.assertEqual(_failed, [])
        target_connect = call(aHost=_cell_list[0], aTimeout=30)
        self.assertIn(target_connect, mock_mConnect.mock_calls)
        mock_mExecuteCmd.assert_any_call("ipmitool sunoem getval /SP/services/ipmi/servicestate")
        mock_mDisconnect.assert_called()
        ebLogInfo("")

    @patch("exabox.core.Node.exaBoxNode.mDisconnect")
    @patch("exabox.core.Node.exaBoxNode.mIsConnected", return_value=True)
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect")
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    def test_mValidateServiceStateOnCells_exacc(self, mock_mCheckCondition, mock_mConnect, mock_mExecuteCmd, mock_mGetCmdExitStatus, mock_mIsConnected, mock_mDisconnect):

        ebLogInfo("")
        ebLogInfo("Running unit test on Cellhandler.mValidateServiceStateOnIlom for ExaCC")
        _cell_list = ["slcs27celadm04.us.oracle.com"]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("ipmitool sunoem getval /SP/services/ipmi/servicestate", aRc=0,
                                   aStdout="Target Value: enabled"),
                    exaMockCommand("ipmitool sunoem setval /SP/services/ipmi/service state enabled", aRc=0,
                                   aStdout="Sun OEM setval command successful."),
                    exaMockCommand("ipmitool sunoem getval /SP/services/ipmi/servicestate", aRc=0,
                                   aStdout="Target Value: enabled")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        output_mock = MagicMock()
        output_mock.readlines.return_value = ["Target Value: enabled"]
        mock_mExecuteCmd.return_value = (None, output_mock, MagicMock())

        cellHandler = CellHandler(self.__patch_args_dict)
        with patch.object(cellHandler, "mIsExaCC", return_value=True):
            _rc, _failed = cellHandler.mValidateServiceStateOnIlom(_cell_list)

        self.assertEqual(_rc, self.SUCCESS_ERROR_CODE)
        self.assertEqual(_failed, [])
        target_connect = call(aHost=_cell_list[0], aTimeout=30)
        self.assertIn(target_connect, mock_mConnect.mock_calls)
        mock_mExecuteCmd.assert_any_call("ipmitool sunoem getval /SP/services/ipmi/servicestate")
        mock_mDisconnect.assert_called()
        ebLogInfo("")
        
    @patch("exabox.core.Node.exaBoxNode.mDisconnect")
    @patch("exabox.core.Node.exaBoxNode.mConnect")
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    def test_mCheckServiceStateOnCells_exacs_prepatch(self, mock_mCheckCondition, mock_mExecuteCmd, mock_mGetCmdExitStatus, mock_mConnect, mock_mDisconnect):

        ebLogInfo("")
        ebLogInfo("Running unit test on Cellhandler.mUpdateServiceStateOnIlom for ExaCS prepatch")
        _cell_list = ["slcs27celadm04.us.oracle.com"]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        executed_cmds, service_state = self._mock_ipmi_commands(mock_mExecuteCmd, initial_state="disabled")

        cellHandler = CellHandler(self.__patch_args_dict)
        with patch.object(cellHandler, "mIsExaCC", return_value=False):
            cellHandler.mUpdateServiceStateOnIlom(_cell_list, "prepatch")

        enable_cmds = [cmd for cmd in executed_cmds if "setval /SP/services/ipmi/servicestate enabled" in cmd]
        disable_cmds = [cmd for cmd in executed_cmds if "setval /SP/services/ipmi/servicestate disabled" in cmd]

        self.assertGreater(len(enable_cmds), 0)
        self.assertEqual(len(disable_cmds), 0)
        self.assertEqual(service_state["value"], "enabled")
        ebLogInfo("")

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mUpdateServiceStateOnIlom")
    def test_mUpdateServiceStateOnIlom_only_prepatch_called(self, mock_mUpdateServiceStateOnIlom):

        ebLogInfo("Running unit test to confirm Cell postpatch path is never invoked")

        with patch.object(CellHandler, "mGetDomUListFromXml", return_value=[]):
            cellHandler = CellHandler(self.__patch_args_dict)
            cellHandler.mPreCheck()

        args = [call.args[1] for call in mock_mUpdateServiceStateOnIlom.call_args_list]
        self.assertNotIn("postpatch", args)

    @patch("exabox.core.Node.exaBoxNode.mDisconnect")
    @patch("exabox.core.Node.exaBoxNode.mConnect")
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    def test_mCheckServiceStateOnCells_exacc_prepatch(self, mock_mCheckCondition, mock_mExecuteCmd, mock_mGetCmdExitStatus, mock_mConnect, mock_mDisconnect):

        ebLogInfo("")
        ebLogInfo("Running unit test on Cellhandler.mUpdateServiceStateOnIlom for ExaCC prepatch")
        _cell_list = ["slcs27celadm04.us.oracle.com"]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        executed_cmds, service_state = self._mock_ipmi_commands(mock_mExecuteCmd, initial_state="disabled")

        cellHandler = CellHandler(self.__patch_args_dict)
        with patch.object(cellHandler, "mIsExaCC", return_value=True):
            cellHandler.mUpdateServiceStateOnIlom(_cell_list, "prepatch")

        enable_cmds = [cmd for cmd in executed_cmds if "setval /SP/services/ipmi/servicestate enabled" in cmd]
        disable_cmds = [cmd for cmd in executed_cmds if "setval /SP/services/ipmi/servicestate disabled" in cmd]

        self.assertGreater(len(enable_cmds), 0)
        self.assertEqual(len(disable_cmds), 0)
        self.assertEqual(service_state["value"], "enabled")
        ebLogInfo("")

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetOpStyle", return_value = 'rolling')
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetTask", return_value = 'patch')
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetCustomizedCellList", return_value = ["1cell", "2cell", "3cell", "4cell", "5cell", "6cell", "7cell"])
    def test_mGetCellPatchingTimoutInSec_with7Cells(self, mock_mGetOpStyle, mock_mGetTask, mock_mGetCustomizedCellList):

        ebLogInfo("")
        ebLogInfo("Running unit test on Cellhandler.mGetCellPatchingTimoutInSec_with7Cells")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.__patch_args_dict['StorageNodeList'] = ["1cell", "2cell", "3cell", "4cell", "5cell", "6cell", "7cell"]
        _cell_handler = CellHandler(self.__patch_args_dict)
        _res = _cell_handler.mGetCellPatchingTimoutInSec()
        self.assertEqual(_res, 165600)
        ebLogInfo("Unit test on Cellhandler.mGetCellPatchingTimoutInSec_with7Cells executed successfully")

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetOpStyle", return_value = 'rolling')
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetTask", return_value = 'rollback')
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetCustomizedCellList", return_value = ["1cell", "2cell", "3cell"])
    def test_mGetCellPatchingTimoutInSec_with3Cells(self, mock_mGetOpStyle, mock_mGetTask, mock_mGetCustomizedCellList):

        ebLogInfo("")
        ebLogInfo("Running unit test on Cellhandler.mGetCellPatchingTimoutInSec_with3Cells")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.__patch_args_dict['StorageNodeList'] = ["1cell", "2cell", "3cell", "4cell", "5cell", "6cell", "7cell"]
        _cell_handler = CellHandler(self.__patch_args_dict)
        _res = _cell_handler.mGetCellPatchingTimoutInSec()
        self.assertEqual(_res, 82800)
        ebLogInfo("Unit test on Cellhandler.mGetCellPatchingTimoutInSec_with3Cells executed successfully")

    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetOpStyle", return_value = 'rolling')
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetTask", return_value = 'patch')
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mGetCustomizedCellList", return_value = ["1cell", "2cell", "3cell", "4cell", "5cell", "6cell", "7cell", "8cell", "9cell", "10cell", "11cell", "12cell"])
    def test_mGetCellPatchingTimoutInSec_with12Cells(self, mock_mGetOpStyle, mock_mGetTask, mock_mGetCustomizedCellList):

        ebLogInfo("")
        ebLogInfo("Running unit test on Cellhandler.mGetCellPatchingTimoutInSec_with12Cells")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.__patch_args_dict['StorageNodeList'] = ["1cell", "2cell", "3cell", "4cell", "5cell", "6cell", "7cell"]
        _cell_handler = CellHandler(self.__patch_args_dict)
        _res = _cell_handler.mGetCellPatchingTimoutInSec()
        self.assertEqual(_res, 248400)
        ebLogInfo("Unit test on Cellhandler.mGetCellPatchingTimoutInSec_with12Cells executed successfully")

    #@patch("exabox.core.node.Node.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mPatchRequestRetried", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mCleanEnvironment")
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mCellsCleanUp", return_value=0)
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUListFromXml", return_value=[])
    @patch("exabox.infrapatching.handlers.targetHandler.cellhandler.InfraPatchManager")
    def test_retry_cleanup_sets_hostkey(
            self,
            mock_patchmgr_cls,
            mock_get_domu,
            mock_cells_cleanup,
            mock_clean_env,
            mock_retry,
            mock_connect):
        mock_patchmgr = mock_patchmgr_cls.return_value
        mock_patchmgr.mIsPatchMgrConsoleOutputFileExists.return_value = True
        mock_patchmgr.mGetStatusCode.return_value = 0
        mock_patchmgr.mCreateNodesToBePatchedFile.return_value = "nodes_file"
        mock_patchmgr.mGetNodeListFromNodesToBePatchedFile.return_value = []
        handler = CellHandler(self.__patch_args_dict)
        ssh_env_mock = MagicMock()
        handler.mSetSshEnvSetupSwitchesCell(ssh_env_mock)
        handler.mGetCustomizedDom0List = MagicMock(return_value=['dom0'])
        handler.mGetDom0ToPatchcellSwitches = MagicMock(return_value='dom0')
        handler.mCheckIsCellsRolling = MagicMock(return_value=True)
        handler.mCheckIdemPotency()
        ssh_env_mock.mSetHostKeyComment.assert_called_with(EXAPATCHING_KEY_TAG)
        args = ssh_env_mock.mSetHostKeyComment.call_args[0]
        assert list(args)[0] == EXAPATCHING_KEY_TAG

    def test_get_hostkey_comment_returns_cached_value(self):
        mock_cluctrl = MagicMock()
        ssh_setup = ebCluSshSetup(mock_cluctrl)
        ssh_setup.mSetHostKeyComment(EXAPATCHING_KEY_TAG)
        assert ssh_setup.mGetHostKeyComment() == EXAPATCHING_KEY_TAG

if __name__ == "__main__":
    unittest.main()
