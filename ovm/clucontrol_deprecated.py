# pylint: disable=invalid-name, line-too-long, C0103, C0301
"""
$Header: 

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Dead code removal

FUNCTION:
    Moving all the dead code from clucontrol.py to this file, later once tested this file will be deleted

History:

       MODIFIED (MM/DD/YY)
       ajayasin  08/19/25 - 38288530 : dead code removal

"""
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogJson, ebLogCritical, ebLogTrace, gLogMgrDirectory
from exabox.core.Error import ebError, ExacloudRuntimeError, gReshapeError, gPartialError, gProvError, gNodeElasticError
from time import strftime
import time
import datetime
from exabox.ovm.coredump import ebCoredumpUtil, setKvmOnCrash
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.ovm.clumisc import ebSubnetSet, ebCluPostComputeValidate, ebMiscFx, ebCluFaultInjection, ebMigrateUsersUtil
from exabox.ovm.clubackup import backupCreateVMLogs
import exabox.ovm.clubonding as clubonding
from exabox.ovm.hypervisorutils import getHVInstance, ebVgCompRegistry
from exabox.core.Context import get_gcontext
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.cluresmgr import ebCluResManager
from exabox.core.Node import exaBoxNode, exaBoxNodePool
from exabox.ovm.cluexaccatp_filtering import ebExaCCAtpFiltering
import exabox.ovm.clujumboframes as clujumboframes
from exabox.ovm.clumisc import (ebCluPreChecks, ebCluFetchSshKeys, 
                                ebCluScheduleManager, ebCluCellValidate, 
                                ebCluServerSshConnectionCheck, 
                                ebCluReshapePrecheck, ebCluNodeSubsetPrecheck,
                                mGetDom0sImagesListSorted,
                                ebCopyDBCSAgentpfxFile, ebCluEthernetConfig, mPatchPrivNetworks,ebCluStartStopHostFromIlom, ebCluSshSetup, mGetGridListSupportedByOeda)

OSTP_VALIDATE_CNF = 1
OSTP_CREATE_VM    = 2
OSTP_CREATE_USER  = 3
OSTP_SETUP_CELL   = 4
OSTP_CREATE_CELL  = 5
OSTP_CREATE_GDISK = 6
OSTP_INSTALL_CLUSTER = 7
OSTP_INIT_CLUSTER = 8
OSTP_INSTALL_DB   = 9
OSTP_RELINK_DB    = 10
OSTP_CREATE_ASM   = 11
OSTP_CREATE_DB    = 12
OSTP_CREATE_PDB   = 13
OSTP_APPLY_FIX    = 14
OSTP_INSTALL_EXCHK = 15
OSTP_CREATE_SUMMARY = 16
OSTP_RESECURE_MAC = 17

OSTP_PRE_INSTALL    = 127
OSTP_PREVM_INSTALL  = 128
OSTP_PREGI_INSTALL  = 129
OSTP_POSTVM_INSTALL = 130
OSTP_POSTGI_INSTALL = 131
OSTP_POST_INSTALL   = 132
OSTP_PREDB_INSTALL  = 133
OSTP_POSTDB_INSTALL = 134

OSTP_PREGI_DELETE   = 135
OSTP_POSTGI_DELETE  = 136
OSTP_PREVM_DELETE   = 137
OSTP_POSTVM_DELETE  = 138
OSTP_PREDB_DELETE   = 139
OSTP_POSTDB_DELETE  = 140

OSTP_POSTGI_NID     = 141
OSTP_DBNID_INSTALL  = 142
OSTP_APPLY_FIX_NID  = 143
OSTP_DG_CONFIG      = 144

OSTP_END_INSTALL    = 255


OSTP_SKIP_LIST = [OSTP_PRE_INSTALL, OSTP_PREVM_INSTALL, OSTP_PREGI_INSTALL, OSTP_POSTVM_INSTALL,
                  OSTP_POSTGI_INSTALL, OSTP_POST_INSTALL, OSTP_PREDB_INSTALL, OSTP_POSTDB_INSTALL,
                  OSTP_END_INSTALL, OSTP_PREGI_DELETE, OSTP_POSTGI_DELETE, OSTP_PREVM_DELETE, OSTP_POSTVM_DELETE]
VM_MODE   = 1
GI_MODE   = 2
VMGI_MODE = 3



class ebCluControlDeprecated(object):
    # Handler for exacloud endpoints which contain the exaBoxCluCtrl object

    def __init__(self, aCluCtrl):
        self.__cluctrlobj = aCluCtrl

    def mGetCluCtrlObj(self):
        return self.__cluctrlobj

    def mMgmtVMGI(self, aAction=True, aOptions=None, aMode=VMGI_MODE):
        """
        Automata driving Create and Delete Service, GI or VM
        :param aAction: True for Create and False for Delete
        :param aOptions: Options context
        :param aMode: If VMGI_MODE then Create/Delete Service if set to GI_MODE or VM_MODE Create/Delete VM or GI accordingly
        :return:
        """
        aCluCtrlObj = self.mGetCluCtrlObj()

        if aCluCtrlObj.mCheckConfigOption('use_step_wise', "True"):
            return aCluCtrlObj.mStepwiseMgmtVMGI(aAction, aOptions, aMode)

        _oeda_path = aCluCtrlObj.mGetOedaPath()
        #
        # CREATE SERVICE/GI/VM
        #
        if aAction:
            aCluCtrlObj.mUpdateStatus('Create Service install')

            if aOptions.undostep != None:
                ebLogError('*** Enter valid input. -us not valid for vmgi_install ***')
                return

            if aMode == VMGI_MODE:

                step_list = [OSTP_PREVM_INSTALL, OSTP_CREATE_VM, OSTP_POSTVM_INSTALL, OSTP_PREGI_INSTALL, OSTP_CREATE_USER,
                         OSTP_SETUP_CELL, OSTP_CREATE_CELL, OSTP_CREATE_GDISK, OSTP_INSTALL_CLUSTER, OSTP_INIT_CLUSTER,
                         OSTP_POSTGI_INSTALL, OSTP_END_INSTALL]
                gi_step_list = [OSTP_CREATE_USER, OSTP_SETUP_CELL, OSTP_CREATE_CELL, OSTP_CREATE_GDISK,
                            OSTP_INSTALL_CLUSTER, OSTP_INIT_CLUSTER]


                if aOptions.runstep != None:
                    step_list, gi_step_list  = aCluCtrlObj.formStepList(True, aOptions)
                    if step_list[0] == -1:
                        ebLogError('*** Enter valid input. Input must be integer and 1<=range<=12 ***')
                        return

            elif aMode == GI_MODE:
                step_list = [OSTP_PREGI_INSTALL, OSTP_CREATE_USER, OSTP_SETUP_CELL, OSTP_CREATE_CELL, OSTP_CREATE_GDISK,
                             OSTP_INSTALL_CLUSTER, OSTP_INIT_CLUSTER, OSTP_POSTGI_INSTALL, OSTP_END_INSTALL]
                gi_step_list = [OSTP_CREATE_USER, OSTP_SETUP_CELL, OSTP_CREATE_CELL, OSTP_CREATE_GDISK,
                                OSTP_INSTALL_CLUSTER, OSTP_INIT_CLUSTER]
            elif aMode == VM_MODE:
                step_list = [OSTP_PREVM_INSTALL, OSTP_CREATE_VM, OSTP_POSTVM_INSTALL, OSTP_END_INSTALL]
                gi_step_list = []
            #
            # Run PRECHECKS for VM and VMGI mode
            #
            if aMode in [VM_MODE, VMGI_MODE]:
                _pchecks = ebCluPreChecks(aCluCtrlObj)

                if step_list[0] in [OSTP_PREVM_INSTALL, OSTP_CREATE_VM]:

                    if _pchecks.mVMPreChecks():
                        _error_str = '*** Fatal ERROR - VMs already existing can not continue VM install'
                        ebLogError(_error_str)
                        raise ExacloudRuntimeError(0x0410, 0xA, _error_str,aStackTrace=False)

                _ib_target = not aCluCtrlObj.mIsKVM()
                if _pchecks.mRunAllPreChecks(aVerboseMode=False,aMode=aMode,aIbTarget=_ib_target) == False:
                    _error_str = '*** Fatal ERROR - Prechecks failed, can not continue VM install'
                    ebLogError(_error_str)
                    raise ExacloudRuntimeError(0x0390, 0xA, _error_str,aStackTrace=False)
            #
            # Run PRECHECKS for VMGI and GI mode
            #
            if aMode in [GI_MODE, VMGI_MODE]:
                if aCluCtrlObj.mCheckNIDStarterDB():
                    # adding dbnid configuration steps for specific to the service
                    step_list.append(OSTP_POSTGI_NID)
                    step_list[-1], step_list[-2] = step_list[-2], step_list[-1]

                if step_list[0] not in [OSTP_INSTALL_CLUSTER, OSTP_INIT_CLUSTER, OSTP_POSTGI_INSTALL, OSTP_END_INSTALL]:
                    #Only Delete preexisting griddisks on DEV/QA
                    if aCluCtrlObj.mCheckCellsServicesUp():
                        if not aCluCtrlObj.mEnvTarget() and aCluCtrlObj.mGetStorage().mDeleteForceGridDisks() is False:
                            _error_str = '*** Fatal ERROR - Grid Disks for current cluster already present can not continue GI install'
                            ebLogError(_error_str)
                            raise ExacloudRuntimeError(0x0410, 0xA, _error_str, aStackTrace=False)

                    _exadata_model = aCluCtrlObj.mGetExadataDom0Model()

                    if not aCluCtrlObj.mGetSharedEnv() and _exadata_model=='X8':
                        aCluCtrlObj.mCheckCellLimits()

            #
            # Check status of services in cells:
            #
            _exacloud_prevm_checks = aCluCtrlObj.mCheckConfigOption('exacloud_prevm_checks')
            if _exacloud_prevm_checks and _exacloud_prevm_checks.get("cell_services_check") == 'True'\
                and aCluCtrlObj.mCheckIsCellConfigured():
                if not aCluCtrlObj.mCheckCellsServicesUp():
                    msg = "Cell services are still down after one restart attempt"
                    raise ExacloudRuntimeError(0x0310, 0xA, msg)
                
                # Run check to check physical disk status is normal
                if not aCluCtrlObj.mCheckCellDisks(aCheckType="physicaldisk"):
                        ebLogError('*** Fatal Error *** : Aborting create service - please check cells and try again.')
                        _error_str = '*** Exacloud Operation Failed : Physical disks do not have normal status.'
                        ebLogError(_error_str)
                        raise ExacloudRuntimeError(0x1009, 0xA, _error_str, aStackTrace=False)
                
                  # Run check to check celldisk disk status is normal                
                if not aCluCtrlObj.mCheckCellDisks(aCheckType="celldisk"):
                        ebLogError('*** Fatal Error *** : Aborting create service - please check cells and try again.')
                        _error_str = '*** Exacloud Operation Failed : Cell disks do not have normal status.'
                        ebLogError(_error_str)
                        raise ExacloudRuntimeError(0x1009, 0xA, _error_str, aStackTrace=False)

            # Run exachk before and after create_vm
            #
            if aMode in [VM_MODE, VMGI_MODE]:
                _enable_exachk = aCluCtrlObj.mCheckConfigOption('enable_exachk')
                if _enable_exachk:
                    if 'pre_create_vm' in _enable_exachk and _enable_exachk['pre_create_vm'] == 'True':
                        step_list.insert(0, OSTP_INSTALL_EXCHK)

                    if 'post_create_vm' in _enable_exachk and _enable_exachk['post_create_vm'] == 'True':
                        step_list.insert(step_list.index(OSTP_END_INSTALL), OSTP_INSTALL_EXCHK)

            #
            # Update OEDA properties
            #
            _step_time = time.time()
            aCluCtrlObj.mUpdateOEDAProperties(aOptions)
            aCluCtrlObj.mLogStepElapsedTime(_step_time, 'PREVM VM/GI INSTALL : Updating OEDA environment')
            #
            # PRE-VM Firewall agent check
            #
            if step_list[0] in [OSTP_PREVM_INSTALL, OSTP_CREATE_VM]:
                _fw_enable = aCluCtrlObj.mCheckConfigOption('firewall')
                if _fw_enable and _fw_enable == 'True':
                    aCluCtrlObj.mAcquireRemoteLock()
                    aCluCtrlObj.mFirewallAgentRunning()
                    aCluCtrlObj.mReleaseRemoteLock()

            for step in step_list:

                if step == OSTP_INSTALL_EXCHK:
                    #
                    # run exachk
                    #
                    aCluCtrlObj.mExecuteExachk()

                if step == OSTP_PREVM_INSTALL:

                    # Execute Pre VM Install steps.
                    aCluCtrlObj.mAddPreVMInstallSteps(step_list, aOptions)

                    # Pre VM iptables setup required in KVM
                    if aCluCtrlObj.mIsExabm() and aCluCtrlObj.mIsKVM():

                        _nftDom0s = aCluCtrlObj.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL8"])
                        _iptDom0s = aCluCtrlObj.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])

                        if _nftDom0s:
                            ebIpTablesRoCE.mSetupSecurityRulesExaBM(aCluCtrlObj, aOptions.jsonconf, aDom0s=_nftDom0s)

                        if _iptDom0s:
                            ebIpTablesRoCE.mPrevmSetupIptables(aCluCtrlObj, aDom0s=_iptDom0s)

                if step == OSTP_CREATE_VM:

                    # Cleanup in this step as NAT Bridge are created during CreateVM
                    aCluCtrlObj.mCleanUpBackupsQemu()
                    aCluCtrlObj.mCleanupSingleVMNatBridge()
                    #
                    # OEDA CREATE VM
                    #

                    # Acquire Remote Lock in shared mode-environment
                    aCluCtrlObj.mAcquireRemoteLock()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_CREATE_VM, step_list)
                    # xxx/MR: -v required for TESTING/DEBUGGING ONLY
                    lCmd = "/bin/bash install.sh -cf {0} -s {1} {2}".format(aCluCtrlObj.mGetRemoteConfig(), \
                                                                            aCluCtrlObj.mFetchOedaStep(OSTP_CREATE_VM), \
                                                                            aCluCtrlObj.mGetOEDAExtraArgs())
                    ebLogInfo('Running: ' + lCmd)
                    _out = aCluCtrlObj.mExecuteCmdLog2(lCmd, aCurrDir=_oeda_path)
                    _rc = aCluCtrlObj.mParseOEDALog(_out)
                    aCluCtrlObj.mUpdateStatusOEDA(_rc, OSTP_CREATE_VM, step_list)
                    aCluCtrlObj.mReleaseRemoteLock()
                    if not _rc:
                        ebLogError('*** Fatal Error *** : Aborting current job - please review errors log and try again.')
                        _error_str = '*** Exacloud Operation Failed : OEDA Create VM failed during Create Service'
                        ebLogError(_error_str)
                        _oedaReqPath = aCluCtrlObj.mGetOEDARequestsPath()
                        backupCreateVMLogs(get_gcontext(), aCluCtrlObj.mReturnDom0DomUPair(), f"{_oedaReqPath}/log", aCluCtrlObj.mGetUUID())
                        raise ExacloudRuntimeError(0x0411, 0xA, _error_str, aStackTrace=False)

                    # Configure bonding
                    clubonding.configure_bonding_if_enabled(
                        aCluCtrlObj, payload=aOptions.jsonconf,
                        configure_bridge=True, configure_monitor=True)

                    if not aCluCtrlObj.mCheckConfigOption("_skip_jumbo_frames_config", "True"):
                        clujumboframes.configureJumboFrames(
                            aCluCtrlObj, aOptions.jsonconf)

                    if aCluCtrlObj.mIsExabm() and aCluCtrlObj.mIsKVM():
                        _iptDom0s = aCluCtrlObj.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])
                        if _iptDom0s:
                            ebIpTablesRoCE.mSetupSecurityRulesExaBM(aCluCtrlObj, aOptions.jsonconf, aDom0s=_iptDom0s)

                    if aCluCtrlObj.mIsKVM():
                        ### Change on_crash to restart
                        ebLogInfo("Set on_crash value to restart")
                        setKvmOnCrash(doms=aCluCtrlObj.mReturnDom0DomUPair(), value="restart")

                if step == OSTP_POSTVM_INSTALL:
                    #
                    # Execute post VM install steps.
                    #
                    aCluCtrlObj.mAddPostVMInstallSteps(step_list, aOptions)

                if step == OSTP_PREGI_INSTALL:
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_PREGI_INSTALL, step_list, 'Update XML Cluster Config')
                    aCluCtrlObj.mCopyFileToClusterConfiguration(aCluCtrlObj.mGetConfigPath(), 'gi_install_cluster.xml')
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Update XML Cluster Config')

                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_PREGI_INSTALL, step_list, 'Running External PREGI Scripts')
                    aCluCtrlObj.mRunScript(aType='*',aWhen='pre.gi_install')
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Running External PREGI Scripts')

                if step == OSTP_INSTALL_CLUSTER:
                    #
                    # INSTALL CLUSTER Remove FQDN of vms
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_INSTALL_CLUSTER, step_list, 'Remove FQDN on DomU')
                    aCluCtrlObj.mRemoveFqdnOnDomU()
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Remove FQDN on DomU')

                    #
                    # Configure Syslog Ilom Host
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_INSTALL_CLUSTER, step_list, 'Configure Syslog Ilom Host')
                    aCluCtrlObj.mConfigureSyslogIlomHost()
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Configure Syslog Ilom Host')

                    #
                    # Configure Syslog IB Switches
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_INSTALL_CLUSTER, step_list, 'Configure Syslog IB Switches')
                    aCluCtrlObj.mConfigureSyslogIBSwitches()
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Configure Syslog IB Switches')


                if step in gi_step_list:
                    #
                    # Update Current OEDA Step
                    #
                    aCluCtrlObj.mUpdateStatusOEDA(True,step,step_list)
                    #
                    # Some operation in PatchVMCfg requires users / cell to be setup
                    #
                    if step == OSTP_INSTALL_CLUSTER:
                        aCluCtrlObj.mAcquireRemoteLock()
                        _step_time = time.time()

                        if aCluCtrlObj.mIsKVM():
                            aCluCtrlObj.patchKVMGuestCfg(aOptions)
                        else:
                            aCluCtrlObj.mPatchVMCfg(aOptions)              # Customize VM.CFG (e.g. additional images, partitions,...
                        aCluCtrlObj.mConfigureShmAll()
                        aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Patching VM Configuration')
                        aCluCtrlObj.mReleaseRemoteLock()
                    #
                    # In shared environments Cell can be already created at this stage (skip if it is the case)
                    #
                    if step in [ OSTP_CREATE_CELL, OSTP_CREATE_GDISK ]:
                        aCluCtrlObj.mAcquireRemoteLock()

                    if step == OSTP_CREATE_CELL and aCluCtrlObj.mCheckConfigOption('skip_cell_create', 'True'):
                        aCluCtrlObj.mEnforceFlashCache(aOptions)
                        aCluCtrlObj.mReleaseRemoteLock()
                        continue
                    if step == OSTP_CREATE_CELL and aCluCtrlObj.mCheckCellConfig(aOptions, aStartup=True) and not aCluCtrlObj.mCheckConfigOption('force_cell_config'):
                        # CheckCellConfig return True therefore Cells are already configured
                        ebLogInfo('*** CheckCellConfig found Cell to be already setup skipping step : '+aCluCtrlObj.mFetchOedaStep(str(step)))
                        aCluCtrlObj.mEnforceFlashCache(aOptions)
                        aCluCtrlObj.mReleaseRemoteLock()
                        continue

                    if step in [ OSTP_SETUP_CELL, OSTP_CREATE_CELL, OSTP_CREATE_GDISK ]:
                        aCluCtrlObj.mAcquireRemoteLock()

                    if step == OSTP_SETUP_CELL and aCluCtrlObj.mCheckConfigOption('delete_cloud_user', 'True'):
                        aCluCtrlObj.mDeleteCloudUser(aOptions, True)

                    lCmd = "/bin/bash install.sh -cf {0} -s {1} {2}".format(aCluCtrlObj.mGetRemoteConfig(), \
                                                                            aCluCtrlObj.mFetchOedaStep(str(step)), \
                                                                            aCluCtrlObj.mGetOEDAExtraArgs())
                    ebLogInfo('Running: ' + lCmd)
                    _out = aCluCtrlObj.mExecuteCmdLog2(lCmd, aCurrDir=_oeda_path)
                    _rc = aCluCtrlObj.mParseOEDALog(_out)
                    aCluCtrlObj.mUpdateStatusOEDA(_rc,step,step_list)

                    if step in [ OSTP_SETUP_CELL, OSTP_CREATE_CELL, OSTP_CREATE_GDISK ]:
                        aCluCtrlObj.mReleaseRemoteLock()

                    if not _rc:
                        ebLogError('*** Fatal Error *** : Aborting current job - please review errors log and try again.')
                        _error_str = '*** Exacloud Operation Failed : OEDA Install GI failed during Create Service'
                        ebLogError(_error_str)
                        raise ExacloudRuntimeError(0x0410, 0xA, _error_str, aStackTrace=False)

                if step == OSTP_CREATE_CELL:
                    aCluCtrlObj.mEnforceFlashCache(aOptions)

                if step == OSTP_CREATE_USER and not aCluCtrlObj.mCheckConfigOption('secure_ssh_all', 'False'):
                    _step_time = time.time()
                    aCluCtrlObj.mSecureDom0SSH()
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Secure DOM SSH')

                if step == OSTP_CREATE_USER:
                    _step_time = time.time()

                    _opcid = "2000"
                    _opcgid = None

                    _remapUtil = ebMigrateUsersUtil(aCluCtrlObj)
                    _usrConfig = _remapUtil.mMergeUsersGroupsConfigPayload()

                    if "opc" in _usrConfig:
                        _opccfg = _usrConfig["opc"]
                        if _opccfg:
                            if "uid" in _opccfg:
                                _opcid = str(_opccfg["uid"])
                            if "gid" in _opccfg:
                                _opcgid = str(_opccfg["gid"])

                    aCluCtrlObj.mAddUserDomU("opc", _opcid, aSudoAccess=True, aPasswordLess=True, aGID=_opcgid)
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Create opc user')

                if step == OSTP_CREATE_USER:
                    _step_time = time.time()
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Saving OEDA SSH Keys')

                if step == OSTP_CREATE_USER:
                    _step_time = time.time()
                    _remapUtil = ebMigrateUsersUtil(aCluCtrlObj)
                    _remapUtil.mExecuteRemap()
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Remapping Users and Groups IDs')

                if step == OSTP_CREATE_USER and aCluCtrlObj.mIsOciEXACC():
                    _step_time = time.time()
                    aCluCtrlObj.mLockDBMUsers()
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Lockdown dbmadmin/dbmmonitor users')

                if step == OSTP_POSTGI_INSTALL:
                    aCluCtrlObj.mAddPostGIInstallSteps(step_list, aOptions)

                if step == OSTP_POSTGI_NID:
                    aCluCtrlObj.mAddPostGINIDSteps(step_list, aOptions)

                if step == OSTP_END_INSTALL:
                    aCluCtrlObj.mSaveClusterDomUList() # save the cluster xml and the domu list in the json file
                    aCluCtrlObj.mCopyExaDataScript() # copy the exadata_updates script to DomUs
                    aCluCtrlObj.mSetupDomUsForSecurePatchServerCommunication() # Copy ca cert(pem format) on domUs
                    if aMode == VMGI_MODE:
                        ebLogInfo('*** Exacloud Operation Successful : Create Service completed')
                        aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_END_INSTALL, step_list, 'Create Service Completed')
                    elif aMode == GI_MODE:
                        ebLogInfo('*** Exacloud Operation Successful : Create GI completed')
                        aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_END_INSTALL, step_list, 'Create GI Completed')
                    elif aMode == VM_MODE:
                        ebLogInfo('*** Exacloud Operation Successful : Create VM completed')
                        aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_END_INSTALL, step_list, 'Create VM Completed')
                    #
                    # POST Provisioning remove databasemachine.xml from domU and place it in dom0
                    #
                    if aMode in [VMGI_MODE, GI_MODE, VM_MODE] and not aCluCtrlObj.isATP():
                        aCluCtrlObj.mRemoveDatabaseMachineXmlDomU()

        else:
            #
            # DELETE SERVICE/GI/VM
            #
            aCluCtrlObj.mUpdateStatus('Delete Service')

            if aOptions.runstep != None:
                ebLogError('*** Enter valid input. -rs not valid for vmgi_delete ***')
                return

            if aMode == VMGI_MODE:

                step_list = [OSTP_PREGI_DELETE, OSTP_INIT_CLUSTER, OSTP_INSTALL_CLUSTER, OSTP_CREATE_GDISK, OSTP_CREATE_CELL,
                                 OSTP_SETUP_CELL, OSTP_CREATE_USER, OSTP_POSTGI_DELETE, OSTP_PREVM_DELETE, OSTP_CREATE_VM,
                                 OSTP_POSTVM_DELETE, OSTP_END_INSTALL]
                gi_step_list = [OSTP_INIT_CLUSTER, OSTP_INSTALL_CLUSTER, OSTP_CREATE_GDISK, OSTP_CREATE_CELL,
                                 OSTP_SETUP_CELL, OSTP_CREATE_USER]

                if aOptions.undostep != None:

                    step_list, gi_step_list  = aCluCtrlObj.formStepList(False, aOptions)
                    if step_list[0] == -1:
                        ebLogError('*** Enter valid input. Input must be integer and 1<=range<=12 ***')
                        return

            elif aMode == GI_MODE:
                step_list = [OSTP_PREGI_DELETE, OSTP_INIT_CLUSTER, OSTP_INSTALL_CLUSTER, OSTP_CREATE_GDISK, OSTP_CREATE_CELL,
                             OSTP_SETUP_CELL, OSTP_CREATE_USER, OSTP_POSTGI_DELETE, OSTP_END_INSTALL]
                gi_step_list = [OSTP_INIT_CLUSTER, OSTP_INSTALL_CLUSTER, OSTP_CREATE_GDISK, OSTP_CREATE_CELL,
                                OSTP_SETUP_CELL, OSTP_CREATE_USER]
            elif aMode == VM_MODE:
                step_list = [OSTP_PREVM_DELETE, OSTP_CREATE_VM, OSTP_POSTVM_DELETE, OSTP_END_INSTALL]
                gi_step_list = []

            # Remove non-needed OEDA steps on delete (By default as param is False)
            if not aCluCtrlObj.mGetRunAllUndoSteps():
                if gi_step_list: #if GI step list, just remove step 8 and 9
                    gi_step_list.remove(OSTP_INIT_CLUSTER)
                    gi_step_list.remove(OSTP_INSTALL_CLUSTER)
                    step_list.remove(OSTP_INIT_CLUSTER)    # 9 (mapped)
                    step_list.remove(OSTP_INSTALL_CLUSTER) # 8

            #
            # Update OEDA properties
            #
            _step_time = time.time()
            aCluCtrlObj.mUpdateOEDAProperties(aOptions)
            aCluCtrlObj.mLogStepElapsedTime(_step_time, 'PREVM VM/GI INSTALL : Updating OEDA environment')
            #
            # GI_DELETE
            #

            # BUG 28641550 - only for exabm
            # As VNIC are deleted, having DNS affects SSH connection during DS
            if aCluCtrlObj.mIsExabm():
                aCluCtrlObj.mRemoveDNS()

            for step in step_list:

                if step == OSTP_PREGI_DELETE:
                    #
                    # PRE-GI - Run External Scripts
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_PREGI_DELETE, step_list, 'Running External PREGI Scripts')
                    aCluCtrlObj.mRunScript(aType='*',aWhen='pre.gi_delete')
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Running External PREGI Scripts')

                if step in gi_step_list:
                    #
                    # Update Current OEDA Step
                    #
                    aCluCtrlObj.mUpdateStatusOEDA(True,step,step_list)

                    if step == OSTP_CREATE_GDISK:
                        #
                        # POSTGI - Delete ACFS Grid Disks
                        #
                        try:
                            _step_time = time.time()
                            aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTGI_DELETE, step_list, 'Delete ACFS Grid Disks')
                            aCluCtrlObj.mGetStorage().mCreateACFSGridDisks(aCreate=False)
                            aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Delete ACFS Grid Disks')
                        except:
                            ebLogWarn('*** Delete ACFS Grid Disk did not completed successully')

                        if not aCluCtrlObj.mGetRunAllUndoSteps():
                            aCluCtrlObj.mAcquireRemoteLock()
                            step_time = time.time()
                            aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTGI_DELETE, step_list, 'Destroy VM before undoing Cells Setup')
                            for _dom0, _domu in aCluCtrlObj.mReturnDom0DomUPair():
                                _vm = getHVInstance(_dom0)
                                _vm.mDestroyVM(_domu)
                            aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Destroy VM before undoing Cells Setup')
                            aCluCtrlObj.mReleaseRemoteLock()  

                    if step == OSTP_CREATE_CELL:
                        #
                        # Grid Disk Force Delete (this is required as most of the time GridDisks delete step will fail
                        # (e.g. ASM/DB not shutdown properly due to inability to access the DomUs/VMs)
                        #
                        _step_time = time.time()
                        aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTGI_DELETE, step_list, 'Running Delete Force Grid Disks')
                        if aCluCtrlObj.mCheckCellsServicesUp():
                            aCluCtrlObj.mGetStorage().mDeleteForceGridDisks()
                        else:
                            ebLogWarn('*** Cell Services are not running, unable to delete Grid disks')
                        aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Running Delete Force Grid Disks')

                    if step == OSTP_CREATE_CELL and aCluCtrlObj.mCheckConfigOption('skip_cell_delete', 'True'):
                        ebLogWarn('*** Delete Cell Disk has been disabled - skipping OEDA step -')
                        continue

                    if step == OSTP_CREATE_CELL and aCluCtrlObj.mGetSharedEnv():
                        aCluCtrlObj.mAcquireRemoteLock()
                        #do not execute undostep 6 override if any other VM exists
                        _numVMs = aCluCtrlObj.mCheckNumVM(aExcludeOwn=True)
                        if (_numVMs == -1) or (_numVMs > 0):
                            ebLogWarn('*** Another cluster\'s VM exists. skipping OEDA undostep 6 - Delete Cell Disk')
                            aCluCtrlObj.mReleaseRemoteLock()
                            continue

                    if step == OSTP_CREATE_CELL:

                        aCluCtrlObj.mUpdateStatusOEDA(True, step, step_list, 'Checking if cell disks state is normal (this operation can take a long time)')
                        _step_time = time.time()
                        aCluCtrlObj.mCellAssertNormalStatus(aOptions)
                        aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Checking cell disks status')
                        # Refresh the UI to reflect the correct step by
                        aCluCtrlObj.mUpdateStatusOEDA(True,step,step_list)

                    if step in [OSTP_CREATE_CELL, OSTP_CREATE_GDISK]:
                        lCmd = "/bin/bash install.sh -cf {0} -u {1} -override {2}".format(aCluCtrlObj.mGetRemoteConfig(), \
                                                                            aCluCtrlObj.mFetchOedaStep(str(step)), \
                                                                            aCluCtrlObj.mGetOEDAExtraArgs())
                        if step == OSTP_CREATE_CELL:
                            aCluCtrlObj.mReleaseRemoteLock()
                    else:
                        lCmd = "/bin/bash install.sh -cf {0} -u {1} {2}".format(aCluCtrlObj.mGetRemoteConfig(), \
                                                                            aCluCtrlObj.mFetchOedaStep(str(step)), \
                                                                            aCluCtrlObj.mGetOEDAExtraArgs())

                    ebLogInfo('Running: ' + lCmd)
                    # Update Status (before)
                    _out = aCluCtrlObj.mExecuteCmdLog2(lCmd, aCurrDir=_oeda_path)
                    _rc = aCluCtrlObj.mParseOEDALog(_out)
                    aCluCtrlObj.mUpdateStatusOEDA(_rc,step,step_list)
                    if not _rc:
                        ebLogError('*** Non Fatal Error *** : Delete Service - GI delete step failed.')

                    # bug 28215108: Delete cloud users
                    if step == OSTP_CREATE_GDISK:
                        ebLogInfo('Delete Service: Calling mDeleteCloudUser only for this cluster')
                        aCluCtrlObj.mDeleteCloudUser(aOptions, False)

                if step == OSTP_POSTGI_DELETE:
                    #
                    # POSTGI - Run External Scripts
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTGI_DELETE, step_list, 'Running External POSTGI Scripts')
                    aCluCtrlObj.mRunScript(aType='*',aWhen='post.gi_delete')
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Running External POSTGI Scripts')
                #
                # VM DELETE
                #
                if step == OSTP_PREVM_DELETE:
                    #
                    # PREVM - Run External Scripts
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_PREVM_DELETE, step_list, 'Running External PREVM Scripts')
                    aCluCtrlObj.mRunScript(aType='*',aWhen='pre.vm_delete')
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Running External PREVM Scripts')
                    #
                    # PREVM - Shred VM Images (Sytem, User, DB/GI bits)
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_PREVM_DELETE, step_list,
                                                 'VM Image shredding in progress (this operation can take a long time')
                    aCluCtrlObj.mVMImagesShredding(aOptions)
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'VM Image shredding')

                if step == OSTP_CREATE_VM:
                    #
                    # VGE: 09 2018 : Reenable OEDA DeleteVM
                    #
                    _csu = csUtil()
                    _bridges = _csu.mFetchBridges(aCluCtrlObj)

                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_CREATE_VM, step_list, 'Delete Virtual Machine')
                    #
                    # Populate final config (new OEDA requirement)
                    #
                    if not aCluCtrlObj.mIsKVM():
                        aCluCtrlObj.mCopyFinalVMConfig(_oeda_path)
                    else:
                        ebLogWarn('*** mCopyFinalVMConfig() not supported on KVM - FIXME')

                    # Kill any ongoing start-domain of same domU (bug 31349800)
                    aCluCtrlObj.mKillOngoingStartDomains()

                    #
                    # Try to clean up via OEDA first
                    #
                    # Option is not in template, setting it to False will revert to old behavior
                    _oeda_cleanup_success = False
                    if not aCluCtrlObj.mCheckConfigOption('oeda_vm_delete_step', 'False'):
                        # Execute the OEDA Step
                        lCmd = "/bin/bash install.sh -cf {0} -u {1} {2}".format(aCluCtrlObj.mGetRemoteConfig(), \
                                                                            aCluCtrlObj.mFetchOedaStep(OSTP_CREATE_VM), \
                                                                            aCluCtrlObj.mGetOEDAExtraArgs())
                        ebLogInfo('Executing: ' + lCmd)
                        _out = aCluCtrlObj.mExecuteCmdLog2(lCmd, aCurrDir=_oeda_path)
                        _rc = aCluCtrlObj.mParseOEDALog(_out)
                        if not _rc:
                            ebLogError('*** Delete Virtual Machine (OEDA) returned with errors')
                        else:
                            _oeda_cleanup_success = True

                    # Force delete unnamed
                    aCluCtrlObj.mForceDeleteDomainUnnamed(aOptions)
                    aCluCtrlObj.mCleanUpReconfig()

                    # Stale cleanup
                    aCluCtrlObj.mCleanUpStaleVm(_oeda_cleanup_success)

                    if aCluCtrlObj.mCheckConfigOption('min_vm_cycles_reboot') is not None:
                        aCluCtrlObj.mCheckVMCyclesAndReboot()

                    _csu.mDeleteBridges(aCluCtrlObj, _bridges)
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Delete Virtual Machine')

                if step == OSTP_POSTVM_DELETE:
                    #
                    # Removing libvirt network filters or NFTables in kvm
                    #
                    if aCluCtrlObj.mIsExabm() and aCluCtrlObj.mIsKVM():
                        ebIpTablesRoCE.mRemoveSecurityRulesExaBM(aCluCtrlObj)
                    # Check if Cell services are running
                    #
                    _cells_services_up = True
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTVM_DELETE, step_list, 'Running cell services checks')
                    if not aCluCtrlObj.mCheckCellsServicesUp():
                        ebLogWarn('*** Cell services are still down after one restart attempt ***')
                        _cells_services_up = False

                    # Cleanup bonding
                    clubonding.cleanup_bonding_if_enabled(
                        aCluCtrlObj, payload=aOptions.jsonconf,
                        cleanup_bridge=False, cleanup_monitor=True)

                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Running cell services check')

                    #
                    # Grid Disk Force Delete (TODO: Add support for celldisk force delete with support for Multi-VMs)
                    #
                    if _cells_services_up:
                        _step_time = time.time()
                        aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTVM_DELETE, step_list, 'Running Delete Force Grid Disks POSTVM')
                        if aCluCtrlObj.mGetStorage().mCheckGridDisks() and aCluCtrlObj.mIsLastCluster(aCluCtrlObj.mReturnCellNodes()):
                            if aCluCtrlObj.mGetStorage().mDeleteForceGridDisks():
                                ebLogInfo("Griddisks of the cells in this cluster are deleted. Secure cell shredding will be performed during infra delete.")
                        aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Running Delete Force Grid Disks POSTVM')

                    #
                    # Reset storage vlan for Cells
                    #
                    if aCluCtrlObj.mIsKVM() and aCluCtrlObj.mIsExabm() and not aCluCtrlObj.mGetSharedEnv():
                        _step_time = time.time()
                        aCluCtrlObj.mUpdateStatusCS(True, OSTP_POSTVM_DELETE, step_list, aComment='Reset storage vlan for Cells')
                        aCluCtrlObj.mRestoreStorageVlan(aCluCtrlObj.mReturnCellNodes())
                        aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Reset storage vlan for Cells')

                    #
                    # Remove ClusterConfiguration from Dom0s
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTVM_DELETE, step_list, 'Remove Cluster Configuration')
                    aCluCtrlObj.mRemoveClusterConfiguration()
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Remove Cluster Configuration')
                    #
                    # Update request status
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTVM_DELETE, step_list, 'Running External POSTVM Scripts')
                    aCluCtrlObj.mRunScript(aType='*',aWhen='post.vm_delete')
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Running External POSTVM Scripts')
                    #
                    # Remove ebtables whitelist if present
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_PREVM_DELETE, step_list, 'Remove and flush ebtables from Dom0')
                    aCluCtrlObj.mSetupEbtablesOnDom0(aMode=False)
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Remove and flush ebtables from Dom0')

                    for _dom0, _domU in aCluCtrlObj.mReturnDom0DomUPair():
                        _myfilename = '/opt/exacloud/network/vif-all-client-ips' + "." + _domU
                        _node = exaBoxNode(get_gcontext())
                        _node.mConnect(aHost=_dom0)
                        _node.mExecuteCmd('rm -f %s 2>/dev/null' % _myfilename)
                        if aCluCtrlObj.mIsOciEXACC():
                            ebExaCCAtpFiltering.sCleanupDom0EBtables(_node, _domU)
                        _node.mDisconnect()
                    #
                    # Reset IORM DB Plan
                    #
                    if not aCluCtrlObj.mGetSharedEnv():
                        _step_time = time.time()
                        aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTVM_DELETE, step_list, 'Resetting IORM DB Plan')
                        _ioptions = aOptions
                        _ioptions.resmanage = "resetdbplan"
                        _iormobj = ebCluResManager(aCluCtrlObj, _ioptions)
                        _iormobj.mClusterIorm(_ioptions)
                        aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Resetting IORM DB Plan')
                    #
                    # Delete Pkey Cell
                    #
                    _step_time = time.time()
                    aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_POSTVM_DELETE, step_list, 'Delete PKey Cell')
                    aCluCtrlObj.mDeletePKeyCell()
                    aCluCtrlObj.mLogStepElapsedTime(_step_time, 'Delete PKey Cell')

                    #
                    # Return error during delete service in case Physical disks do not have normal status.
                    #
                    if not aCluCtrlObj.mCheckCellDisks(aCheckType="physicaldisk"):
                        ebLogError('*** Fatal Error *** : Aborting delete service - please check cells and try again.')
                        _error_str = '*** Exacloud Operation Failed : Physical disks do not have normal status.'
                        ebLogError(_error_str)
                        raise ExacloudRuntimeError(0x1009, 0xA, _error_str, aStackTrace=False)

                    #
                    # Return error during delete service in case Cell disks do not have normal status.
                    #
                    if not aCluCtrlObj.mCheckCellDisks(aCheckType="celldisk"):
                        ebLogError('*** Fatal Error *** : Aborting delete service - please check cells and try again.')
                        _error_str = '*** Exacloud Operation Failed : Cell disks do not have normal status.'
                        ebLogError(_error_str)
                        raise ExacloudRuntimeError(0x1009, 0xA, _error_str, aStackTrace=False)
                        
                    if aCluCtrlObj.IsZdlraHThread() is False:
                        aCluCtrlObj.mGetZDLRA().mEnableDisableHT("Enabled", aOptions)
                    #
                    # Delete nat-rules file to support NAT RULES recreation via dom0_iptables_setup.sh script
                    #
                    aCluCtrlObj.mDeleteNatIptablesRulesFile()

                #
                # Update Final status
                #
                if step == OSTP_END_INSTALL:
                    # remove the clustersjson file created for the given cluster
                    aCluCtrlObj.mDeleteClusterDomUList()
                    if aMode == VMGI_MODE:
                        ebLogInfo('*** Exacloud Operation Successful : Delete Service completed')
                        aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_END_INSTALL, step_list, 'Delete Service Completed')
                    elif aMode == GI_MODE:
                        ebLogInfo('*** Exacloud Operation Successful : Delete GI completed')
                        aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_END_INSTALL, step_list, 'Delete GI Completed')
                    elif aMode == VM_MODE:
                        ebLogInfo('*** Exacloud Operation Successful : Delete VM completed')
                        aCluCtrlObj.mUpdateStatusOEDA(True, OSTP_END_INSTALL, step_list, 'Delete VM Completed')


