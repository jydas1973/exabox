#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_domuhandler.py /main/21 2025/11/08 08:54:10 araghave Exp $
#
# tests_domuhandler.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_domuhandler.py - Class for testing domu precheck, patch and rollback
#
#    DESCRIPTION
#      File for testing the DomU Handler operations regarding infrapatching.
#      (mPreCheck, mPatch, mRollBack)
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    09/11/25  - Enh 38173247 - EXACLOUD CHANGES TO SUPPORT DOMU
#                            ELU INFRA PATCH OPERATIONS
#    sdevasek    11/15/24 - Enh 37172948 - ISOLATE CRS/HEARTBEAT/DB HEALTH
#                           CHECKS TO A SEPARATE API BASED MODULE
#    avimonda    08/14/24 - Bug 36563684 - AIM4EXACLOUD:0X03040001 - VM PRECHECK
#                           EXCEPTION DETECTED. (23.4.1.2.1-DOMU)
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    diguma      07/01/24 - Bug 36727709 - add blackout api mock
#    antamil     06/13/24 - Bug 36666801 - Replace the calls of
#                           mGetCustomizedDomUList with filtered node list
#    araghave    05/29/24 - Bug 36640067 - EXACS | EXASPLICE PRECHECK IS
#                           FAILING WHERE EXASPLICE IS NOT APPLICABLE
#    avimonda    05/13/24 - BUG 36555012 - HW ALERTHISTORY CHECKS PERFORMED BY
#                           THE INFRAPATCHING TOOL ON DOMU MAY NOT BE NECESSARY
#    araghave    05/08/24 - Bug 36543876 - ERROR OUT WHEN GRID HOME PATH BINARY
#                           DOES NOT EXISTS FOR CRS AUTOSTART ENABLED CHECK
#    araghave    12/05/23 - Enh 35244586 - DISABLE PRE AND POST CHECKS NOT
#                           APPLICABLE DURING MONTHLY PATCHING
#    vikasras    08/03/23 - Bug 35671592 - AFTER REFRESHING TO THE RECENT LABEL
#                           TEST FILES ARE REPORTING COMPILATION ERROR
#    vikasras    06/27/23 - Bug 35456901 - MOVE RPM LIST TO INFRAPATCHING.CONF
#                           FOR SYSTEM CONSISTIENCY DUPLICATE RPM CHECK
#    diguma      02/21/22 - bug35080646: adding mock for mIsFSEncrpted*
#    diguma      11/13/22 - ER 34444560 - adding parameter
#                           --skip_gi_db_validation for patchmgr
#    araghave    10/27/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODE
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
from exabox.infrapatching.handlers.targetHandler.domuhandler import DomUHandler
from exabox.core.MockCommand import exaMockCommand

class ebTestDomUHandler(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"
    NO_ACTION_REQUIRED_CODE = "0x0301003D"

    @classmethod
    def setUpClass(self):
        ebLogInfo("Starting classSetUp DomUHandler")
        super(ebTestDomUHandler, self).setUpClass(aGenerateDatabase=True)
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
                                'RequestId': 'e2f947dd-b902-4949-bc04-8b8c52ec170b', 'RackName': 'slcs27', 'isMVM':'no','Dom0domUDetails':{},'ComputeNodeList':[],'StorageNodeList':[],'ComputeNodeListByAlias':[],
                                'AdditionalOptions': [
                                    {'AllowActiveNfsMounts': 'yes', 'ClusterLess': 'no', 'EnvType': 'ecs',
                                     'ForceRemoveCustomRpms': 'no', 'IgnoreAlerts': 'no', 'IgnoreDateValidation': 'yes',
                                     'IncludeNodeList': 'none', 'LaunchNode': 'none',
                                     'OneoffCustomPluginFile': 'none', 'OneoffScriptArgs': 'none',
                                     'RackSwitchesOnly': 'no', 'SingleUpgradeNodeName': 'none', 'SkipDomuCheck': 'no',
                                     'SkipGiDbValidation': 'yes', 'exasplice': 'no', 'isSingleNodeUpgrade': 'no', 'serviceType': 'EXACC',
                                     'exaunitId': 0}]}
        ebLogInfo("Ending classSetUp DomUHandler")

    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mGetDom0DomUPatchZipFile", return_value=["", "exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip,exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip"])
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mIsKvmEnv", return_value=False)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetSSHEnvSetUp")
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mSetSSHPasswordlessForInfraPatching", return_values="")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetDom0ToPatchInitialDom0", return_values="slcs27adm04.us.oracle.com")
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mSetLaunchNodeToPatchOtherDomuNodes", return_value=(SUCCESS_ERROR_CODE, ['slcs27dv0308m.us.oracle.com', 'slcs27dv0408m.us.oracle.com']))
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mGetDomULocalPatchZip2", return_value="exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/DomuYumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip")
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mCheckDomuAvailability", return_value=(True, []))
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mGetCustomizedDomUList", return_value=['slcs27adm04.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mValidateRootFsSpaceUsage", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27adm04.us.oracle.com'], []))
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mPingNode", return_value=True)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1)
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsIsEnabled", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.utils.utility.mIsFSEncryptedNode", return_value=False)
    @patch("exabox.infrapatching.utils.utility.mIsFSEncryptedList", return_value=False)
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGetGiHomePath", return_value=(SUCCESS_ERROR_CODE, '/u01/app/19.0.0.0/grid'))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mRunCrsctlCheckCrsCommand", return_value=(True, 'CRS is up and running'))
    def test_mPreCheck(self, mGetDom0DomUPatchZipFile, mock_mIsKvmEnv, mock_mSetSSHEnvSetUp, mock_mSetSSHPasswordlessForInfraPatching, mock_mGetDom0ToPatchInitialDom0, mock_mSetLaunchNodeToPatchOtherDomuNodes, mock_mGetDomULocalPatchZip2, mock_mCheckDomuAvailability, mock_mGetCustomizedDomUList, mock_mFilterNodesToPatch, mock_mValidateRootFsSpaceUsage, mock_mPingNode, mock_mCheckTargetVersion, mock_mCheckCrsIsEnabled, mock_mIsFSEncryptedNode, mock_mIsFSEncryptedList, mock_mGetGiHomePath, mock_mRunCrsctlCheckCrsCommand):
        ebLogInfo("")
        ebLogInfo("Running unit test on DomUHandler.mPreCheck")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                    exaMockCommand("crs=`cat /etc/oratab|egrep -i 'grid|ASM' |grep -v '^#'|cut -d ':' -f2` ; $crs/bin/crsctl config crs", aStdout="", aPersist=True),
                    exaMockCommand("awk '{print $2}'  /etc/mtab  | sort -u", aStdout="", aPersist=True),
                    exaMockCommand("rpm -qa --queryformat '%{ARCH} %{NAME}' | sort | uniq -c | sed -e 's/^ *//g'| egrep -v '*'", aStdout="", aPersist=True),
                    exaMockCommand("find *", aStdout="", aPersist=True),
                    exaMockCommand("xm list|tail -n+3|awk '{print $1}'", aStdout="", aPersist=True),
                    exaMockCommand("cat /etc/oracle/olr.loc | grep 'crs_home' | cut -f 2 -d '='", aStdout="/u01/app/19.0.0.0/grid", aPersist=True),
                    exaMockCommand("/bin/test -e /u01/app/19.0.0.0/grid/bin/crsctl", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /etc/libvirt/qemu/autostart/scaqan03dv0208.us.oracle.com.xml",
                                   aStdout="", aPersist=True),
                    exaMockCommand(
                        "grep on_reboot /etc/libvirt/qemu/autostart/scaqan03dv0208.us.oracle.com.xml | grep -i 'restart'",
                        aStdout="", aPersist=True),
                    exaMockCommand("dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful' | egrep -i 'Exadata cloud services test message.'", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("awk '{print $2}'  /etc/mtab  | sort -u", aStdout="", aPersist=True),
                    exaMockCommand(
                        "rpm -qa --queryformat '%{ARCH} %{NAME}' | sort | uniq -c | sed -e 's/^ *//g' | egrep -v '*'",
                        aStdout="", aPersist=True),
                    exaMockCommand("find *", aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e /opt/exacloud/network/dom0_iptables_setup.sh", aStdout="",
                                   aPersist=True),
                ],
                [
                    exaMockCommand(
                        "dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful' | egrep -i 'No link detected on required Ethernet|alert.chassis.fw.fpga-upgrade-blocked|Attribute Name : DiskFirmwareVersion *Required *: *ORAB'",
                        aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("imageinfo -ver", aStdout="", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _domuhandler = DomUHandler(self.__patch_args_dict)
        self.assertEqual(_domuhandler.mPreCheck(), (self.SUCCESS_ERROR_CODE, 1))

    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mGetDom0DomUPatchZipFile", return_value=["", "exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip,exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip"])
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mIsKvmEnv", return_value=False)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetSSHEnvSetUp")
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mSetSSHPasswordlessForInfraPatching", return_values="")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetDom0ToPatchInitialDom0", return_values="slcs27adm04.us.oracle.com")
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mSetLaunchNodeToPatchOtherDomuNodes", return_value=(SUCCESS_ERROR_CODE, ['slcs27dv0308m.us.oracle.com', 'slcs27dv0408m.us.oracle.com']))
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mGetDomULocalPatchZip2", return_value="exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/DomuYumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip")
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mCheckDomuAvailability", return_value=(True, []))
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mGetCustomizedDomUList", return_value=['slcs27adm04.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mValidateRootFsSpaceUsage", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27adm04.us.oracle.com'], []))
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mPingNode", return_value=True)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1)
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsIsEnabled", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.utils.utility.mIsFSEncryptedNode", return_value=False)
    @patch("exabox.infrapatching.utils.utility.mIsFSEncryptedList", return_value=False)
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGetGiHomePath", return_value=(SUCCESS_ERROR_CODE, '/u01/app/19.0.0.0/grid'))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mRunCrsctlCheckCrsCommand", return_value=(True, 'CRS is up and running'))
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mPatchRollbackDomUsNonRolling", return_value=NO_ACTION_REQUIRED_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetUnsetBlackout", return_value = SUCCESS_ERROR_CODE)
    def test_mPatch(self, mGetDom0DomUPatchZipFile, mock_mIsKvmEnv, mock_mSetSSHEnvSetUp, mock_mSetSSHPasswordlessForInfraPatching, mock_mGetDom0ToPatchInitialDom0, mock_mSetLaunchNodeToPatchOtherDomuNodes, mock_mGetDomULocalPatchZip2, mock_mCheckDomuAvailability, mock_mGetCustomizedDomUList, mock_mFilterNodesToPatch, mock_mValidateRootFsSpaceUsage, mock_mPingNode, mock_mCheckTargetVersion, mock_mCheckCrsIsEnabled, mock_mIsFSEncryptedNode, mock_mIsFSEncryptedList, mock_mGetGiHomePath, mock_mRunCrsctlCheckCrsCommand, mock_mPatchRollbackDomUsNonRolling, mock_mSetUnsetBlackout):
        ebLogInfo("")
        ebLogInfo("Running unit test on DomUHandler.mPatch")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                    exaMockCommand("crs=`cat /etc/oratab|grep grid|grep -v '^#'|grep -i asm|cut -d ':' -f2`; $crs/bin/crsctl config crs", aStdout="", aPersist=True),
                    exaMockCommand("awk '{print $2}'  /etc/mtab  | sort -u", aStdout="", aPersist=True),
                    exaMockCommand("rpm -qa --queryformat '%{ARCH} %{NAME}' | sort | uniq -c | sed -e 's/^ *//g'| egrep -v '*'", aStdout="", aPersist=True),
                    exaMockCommand("find *", aStdout="", aPersist=True),
                    exaMockCommand("xm list|tail -n+3|awk '{print $1}'", aStdout="", aPersist=True),
                    exaMockCommand("cat /etc/oracle/olr.loc | grep 'crs_home' | cut -f 2 -d '='", aStdout="/u01/app/19.0.0.0/grid", aPersist=True),
                    exaMockCommand("/bin/test -e /u01/app/19.0.0.0/grid/bin/crsctl", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful' | egrep -i 'Exadata cloud services test message.'", aStdout="", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _domuhandler = DomUHandler(self.__patch_args_dict)
        self.assertEqual(_domuhandler.mPatch(), (self.SUCCESS_ERROR_CODE, 0))

    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mGetDom0DomUPatchZipFile", return_value=["", "exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip,exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/Dom0YumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip"])
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mIsKvmEnv", return_value=False)
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetSSHEnvSetUp")
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mSetSSHPasswordlessForInfraPatching", return_values="")
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mGetDom0ToPatchInitialDom0", return_values="slcs27adm04.us.oracle.com")
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mSetLaunchNodeToPatchOtherDomuNodes", return_value=(SUCCESS_ERROR_CODE, ['slcs27dv0308m.us.oracle.com', 'slcs27dv0408m.us.oracle.com']))
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mGetDomULocalPatchZip2", return_value="exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/DomuYumRepository/exadata_ol7_21.2.11.0.0.220414.1_Linux-x86-64.zip")
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mCheckDomuAvailability", return_value=(True, []))
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mGetCustomizedDomUList", return_value=['slcs27adm03.us.oracle.com', 'slcs27adm04.us.oracle.com'])
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mValidateRootFsSpaceUsage", return_value = SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mFilterNodesToPatch", return_value=(SUCCESS_ERROR_CODE, "", ['slcs27adm03.us.oracle.com', 'slcs27adm04.us.oracle.com'], []))
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mPingNode", return_value=True)
    @patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1)
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mRollbackIsAvailable", return_value=True)
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mPatchRollbackDomUsRolling", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mSetPatchmgrLogPathOnLaunchNode", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler.mPatchRollbackDomUsNonRolling", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.utils.utility.mIsFSEncryptedNode", return_value=False)
    @patch("exabox.infrapatching.utils.utility.mIsFSEncryptedList", return_value=False)
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGetGiHomePath", return_value=(SUCCESS_ERROR_CODE, '/u01/app/19.0.0.0/grid'))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsIsEnabled", return_value=SUCCESS_ERROR_CODE)
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mRunCrsctlCheckCrsCommand", return_value=(True, 'CRS is up and running'))
    @patch("exabox.infrapatching.handlers.targetHandler.targethandler.TargetHandler.mSetUnsetBlackout", return_value = SUCCESS_ERROR_CODE)
    def test_mRollBack(self, mGetDom0DomUPatchZipFile, mock_mIsKvmEnv, mock_mSetSSHEnvSetUp, mock_mSetSSHPasswordlessForInfraPatching, mock_mGetDom0ToPatchInitialDom0, mock_mSetLaunchNodeToPatchOtherDomuNodes, mock_mGetDomULocalPatchZip2, mock_mCheckDomuAvailability, mock_mGetCustomizedDom0List, mock_mFilterNodesToPatch, mock_mValidateRootFsSpaceUsage, mock_mPingNode, mock_mCheckTargetVersion, mock_mRollbackIsAvailable, mock_mPatchRollbackDomUsRolling, mock_mock_mSetPatchmgrLogPathOnLaunchNode, mock_mPatchRollbackDomUsNonRolling, mock_mIsFSEncryptedNode, mock_mIsFSEncryptedListi, mock_mGetGiHomePath, mock_mCheckCrsIsEnabled, mock_mRunCrsctlCheckCrsCommand, mock_mSetUnsetBlackout):
        ebLogInfo("")
        ebLogInfo("Running unit test on DomUHandler.mRollBack")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                    exaMockCommand("date *", aStdout="", aPersist=True),
                    exaMockCommand("stat -c '%Y' /EXAVMIMAGES/GuestImages/*/vm.cfg | sort -n | tail -n 1", aStdout="", aPersist=True),
                    exaMockCommand("xm list|tail -n+3|awk '{print $1}'", aStdout="", aPersist=True),
                    exaMockCommand("cat /etc/oracle/olr.loc | grep 'crs_home' | cut -f 2 -d '='", aStdout="/u01/app/19.0.0.0/grid", aPersist=True),
                    exaMockCommand("/bin/test -e /u01/app/19.0.0.0/grid/bin/crsctl", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful' | egrep -i 'Exadata cloud services test message.'", aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand(
                        "dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful' | egrep -i 'No link detected on required Ethernet|alert.chassis.fw.fpga-upgrade-blocked|Attribute Name : DiskFirmwareVersion *Required *: *ORAB'",
                        aStdout="", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _domuhandler = DomUHandler(self.__patch_args_dict)
        self.assertEqual(_domuhandler.mRollBack(), (self.SUCCESS_ERROR_CODE, 0))

if __name__ == "__main__":
    unittest.main()
