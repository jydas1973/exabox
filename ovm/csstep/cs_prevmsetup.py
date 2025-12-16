"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_prevmsetup.py - Create Service PRE VM Setup

FUNCTION:
   Implements the Pre VM Setup for create service execution

NOTES:
    Invoked from cs_driver.py

EXTERNAL INTERFACES: 
    csPreVMSetup: ESTP_PREVM_SETUP

INTERNAL CLASSES:

History:

    MODIFIED (MM/DD/YY)
    prsshukl  11/19/25 - Bug 38037088 - BASE DB -> MOVE THE DO/UNDO STEPS FOR
                         BASEDB TO A NEW FILE IN CSSTEP
    jfsaldan  08/20/25 - Bug 38210429 - OCI: EXADB-D | EXACLOUD IS NOT CLEANING
                         UP PKEY FOR XEN BASED CLUSTERS IN PREVM_SETUP | CAUSES
                         CREATEVM PROBLEMS AS PKEY/PARTITION IS DUPLICATED
    pbellary  08/15/25 - Enh 38318848 - CREATE ASM CLUSTERS TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT
    rajsag    03/11/25 - Enh 37526315 - support additional response fields in
                         exacloud status response for create service steps
    pbellary  02/21/25 - Bug 37614526 - EXACC 24.3.2 :EXASCALE: TERMINATE EXASCALE CLUSTER NOT DELETING THE VAULT ACL ASSOCIATION 
    jfsaldan  02/10/25 - Bug 37570873 - EXADB-D|XS -- EXACLOUD | PROVISIONING |
                         REVIEW AND ORGANIZE PREVM_CHECKS AND PREVM_SETUP STEPS
    jfsaldan  11/27/24 - Enh 37327500 - EXADB-XS: EXACLOUD - OPEN HOST ACCESS
                         CONTROL FOR ROCE NETWORK IN TARGET HOST DURING CREATE
                         SERVICE AND ADD COMPUTE FLOWS
    pbellary  06/02/24 - Bug 37517052 - EDV detach is failing with 'operation in progress'
    naps      10/24/24 - Bug 37192649 - Handle eth0 removal per node instead of
                         cluster wide.
    prsshukl  07/19/24 - Bug 36860623 - mWhitelistCidr() method needs to be
                         called for Fedramp enabled Exacc env
    pbellary  07/02/24 - ENH 36690772 - EXACLOUD: IMPLEMENT PRE-VM STEPS FOR EXASCALE SERVICE
    jfsaldan  03/19/24 - Bug 36409419 - EXACS:23.4.1.2.1: VMBACKUP GOLD IMAGE :
                         DID NOT REMOVE PREVIOUS TERMINATED PROVISION GOLD
                         BACKUP IMAGE (ONLY IN CACHEFILE)
    jfsaldan  02/26/24 - Enh 35951447 - EXACC - SUPPORT FS ENCRYPTION AT REST -
                         EXACLOUD MUST INJECT KEYS VIA SOCATIO FOR ANY
                         OPERATION THAT REQUIRES REBOOT
    jfsaldan  02/20/24 - Bug 36277822 - CELLINIT.ORA HAS STIB0/STIB1 SET AFTER
                         TERMINATION CAUSING CELLRSRV PROBLEMS IN XEN/IB SVM
    scoral    01/18/24 - Bug 36201904 - Enable mCopyVifFiles to copy vif-bridge
                         for all ExaCS XEN envs even if EBTables are disabled.
    jfsaldan  11/09/23 - Bug 35966373 - PIA1 PROVISIONING ISSUE RUNNING
                         ORACLE.ONECOMMAND.DEPLOY.MACHINES.VMUTILS METHOD
                         CREATEVMS FAILEDL:EBTABLES BLOCKING DOMU ADMIN TRAFFIC
    jesandov  10/16/23 - 35729701: Support of OL7 + OL8
    scoral    10/10/23 - Enh 35779476 - Do not update the bonding configuration
                         if eth0 is removed.
    ririgoye  08/22/23 - Bug 35631856 - EXACS:EXACLOUD:CREATE SERVICE:ADD BASH
                         HISTORY TIME DURING EXACLOUD CREATE SERVICE
    jfsaldan  08/18/23 - Bug 35719818 - PLEASE PROVIDE A WAY TO IDENTIFY FROM A
                         XEN DOM0 IF THE GUESTVM HAS LUKS ENABLED OR NOT
    jfsaldan  08/17/23 - Enh 35692408 - EXACLOUD - VMBOSS - CREATE A FLAG IN
                         EXABOX.CONF THAT TOGGLES BETWEEN INSTANCE PRINCIPALS
                         AND USERS PRINCIPALS FOR VMBACKUP TO OSS MODULE
    ririgoye  07/25/23 - Enh 35631856 - ADD BASH HISTORY TIME DURING EXACLOUD CREATE SERVICE
    aararora  07/03/23 - Bug 35156368: Move out mCellSecureShredding method
                         call out from undo method of prevmsetup.
    jfsaldan  05/24/23 - Bug 35410783 - EXACLOUD FAILED TO CALCULATE THE NON
                         ENCRYPTED FIRST BOOT IMAGE
    scoral    05/24/23 - Bug 35285863: Update bonding interface during create
                         service for bonding environments to increase
                         arp_interval from 100 to 1000 if needed.
    scoral    05/04/23 - Bug 35298579 - Move the temporary iptables rules setup
                         to CreateVM.
    scoral    04/14/23 - Bug 35177571 - Use bridge family instead of ip
                         family for VM NFTables rules in OL8 envs.
    jesandov  03/16/23 - Backport 35192222 of jesandov_bug-35174357 from
                         st_ecs_22.3.1.0.0
    prsshukl  01/18/23 - Bug 34989467 - Copy the dom0 iptables setup script
                         everytime in PDIT clusters
    naps      01/06/23 - Bug 34884577 - Move HT for zdlra to prevmsetup step.
    aypaul    12/12/22 - Bug#34881713 Delete vmbackups on vm cluster
                         termination.
    prsshukl  11/25/22 - Bug 34836538 - Replaced mGetStorage with mGetStorage()
    prsshukl  11/23/22 - Bug 34809190 - Removing Double Call of
                         mCheckCellsServicesUp function
    jfsaldan  11/02/22 - Bug 33993510 - CELLDISKS RECREATED AFTER DBSYSTEM
                         TERMINATION
    jfsaldan  10/13/22 - Bug 34700762 - Exacloud should not enforce Deletion of
                         Griddisks on Exascale
    jfsaldan  09/29/22 - Bug 34655112 - Delete Service doesn't delete Grid
                         Disks on cells
    aararora  09/11/22 - Change FORWARD REJECT to FORWARD DROP
    scoral    06/22/22 - Bug 34300556 - Moved bonding setup from undo of PreVM
                         Checks to undo of PreVM Setup.
    jfsaldan  06/08/22 - Bug 34242884 - Run vlanId change during prevm_setup only
                         in singleVM, and run it on MVM during Delete Infra
    aararora  06/03/22 - Add condition for pdit clusters for iptables issue
    jfsaldan  05/27/22 - Bug 34219873 - DELETE KEYAPI SHELL WRAPPER FROM DOM0
                         DURING DELETE SERVICE
    jfsaldan  05/18/22 - Enh 34185907 - Add support to use local passphrase in
                         DEV/QA environments only
    jfsaldan  03/17/22 - Bug 33131402 - Adding OEDA based encryption support
    jfsaldan  01/28/22 - Bug 33797430 - Reset KVM Vlan Using Diskgroup as
                         condition instead of cluster count
    alsepulv  08/30/21 - Enh 33260899: MVM - Reset vlan id when last VM is
                         deleted
    dekuckre  07/16/21 - 33079527: Call mSecureDom0SSH in prevm step
    jvaldovi  05/07/21 - Bug 32862631 - EXACS:20.4.1.2:VNUMA MARKER NOT
                         DELETING VNUMA MARKER IN STEP BASE FLOW
    gsundara  07/24/20 - 31664433 - Save keys in prevm setup step.
    oerincon  04/03/20 - 31124650: Validate QinQ proper setup for RoCE enabled
                         environments during Create Service
    oerincon  03/11/20 - 31030637: SETUP ROCE INTERFACES ON CPS DURING
                         PROVISION (NO QINQ)
    ndesanto  08/06/19 - EXACLOUD STEPBASED CS FIX INVALID IORM OBJECT CREATION
    srtata    04/19/19 - bug 29556301: added missing ATP steps
    pbellary  04/17/19 - bug 29472359: undo stepwise createservice
    srtata    03/05/19 - Creation
"""

import os
import time
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogCritical
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.atp import AtpAddiptables2Dom0
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.ovm.cluresmgr import ebCluResManager
from exabox.ovm.cluexaccib import ExaCCIB_CPS
from exabox.ovm.cluexaccatp_filtering import ebExaCCAtpFiltering
from exabox.ovm.cluexaccroce import ExaCCRoCE_CPS
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.ovm.clumisc import mChangeOpCtlAudit
import exabox.ovm.clubonding as clubonding
from exabox.ovm.cluencryption import (isEncryptionRequested, createAndPushRemotePassphraseSetup,
        deleteRemotePassphraseSetup, ensureSystemFirstBootEncryptedExistsParallelSetup,
        useLocalPassphrase, deleteOEDAKeyApiFromDom0, createEncryptionMarkerFileForVM,
        deleteEncryptionMarkerFileForVM, exacc_fsencryption_requested, exacc_save_fsencryption_passphrase,
        exacc_del_fsencryption_passphrase)
from exabox.utils.node import connect_to_host, node_update_key_val_file
from exabox.ovm.csstep.exascale.exascaleutils import ebExascaleUtils
from exabox.ovm.vmbackup import ebCluManageVMBackup
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.ovm.clustorage import ebCluManageStorage
from exabox.ovm.cluhostaccesscontrol import addRoceNetworkHostAccessControl
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.utils.clu_utils import ebCluUtils

# This class implements doExecute and undoExecute functions
# for the ESTP_PREVM_SETUP step of create service
class csPreVMSetup(CSBase):
    def __init__(self):
        self.step = 'ESTP_PREVM_SETUP'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPreVMSetup: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        steplist = aStepList
        _csu = csUtil()
        imageBom = ImageBOM(ebox)

        ebox.mUpdateStatus('createservice step ESTP_PREVM_SETUP')
        _clu_utils = ebCluUtils(ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "Pre VM setup in progress", 'ESTP_PREVM_SETUP')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Pre VM setup", "In Progress", _stepSpecificDetails)

        #
        # Disable RDS IB module if option set
        #
        if not imageBom.mIsSubStepExecuted(self.step, "INFINIBAND_RDS_MODULE"):
            if not ebox.mIsKVM() and ebox.mCheckConfigOption ('disable_ib_rds', 'True'):
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Disabing Infiniband RDS Module')
                ebox.mAcquireRemoteLock()
                ebox.mDisableDom0IBRdsModule()
                ebox.mReleaseRemoteLock()
                ebox.mLogStepElapsedTime(_step_time, 'Disabling Infiniband RDS Module')

        #
        # Add missing NTP/DNS if no vms present
        #
        if not imageBom.mIsSubStepExecuted(self.step, "ADD_MISSING_NTP"):

            # Run ntp and dns updation if there are no domU in the dom0
            if ebox.mIsKVM() and (_csu.mReturnCountofVm(ebox) == 0):
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Add DNS/NTP to infra nodes')
                _dom0s, _, _cells, _ = ebox.mReturnAllClusterHosts()
                _hostList = _dom0s + _cells
                _pchecks = ebCluPreChecks(ebox)
                if ebox.mIsExaScale():
                    _pchecks.mAddMissingNtpDnsIps(_dom0s)
                else:
                    _pchecks.mAddMissingNtpDnsIps(_hostList)
                ebox.mLogStepElapsedTime(_step_time, 'Add DNS/NTP to infra nodes')

        # Grab lock
        with ebox.remote_lock():

            #
            # PRE-VM iprules setup
            #
            if not imageBom.mIsSubStepExecuted(self.step, "SET_IPRULES"):

                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist,
                    aComment='Setup IPRules (iptables/nftables) on Dom0')

                if not ebox.mIsKVM():

                    ebox.mCleanupEbtablesOnDom0()
                    # Bug 35966373: Ebtables are currently set during PREVM_SETUP, and
                    # removed during POSTVM_INSTALL. We're disabling this through an
                    # 'exabox.conf' property and we will remove this code in the coming
                    # future
                    ebox.mSetupEbtablesOnDom0()

                # Set default IPrules in the Dom0s
                ebox.mHandlerSetupNATIptablesOnDom0()

                # Logic for X5/X6 and IB based systems
                if not ebox.mEnvTarget() and ebox.mGetExadataDom0Model() in ['X5', 'X6']:
                    self.mChangeForwardAccept(ebox)
                if not ebox.mIsKVM() and not ebox.mIsOciEXACC():
                    self.mCopyVifFiles(ebox)

                ## BUG 28598302
                if ebox.isATP() and ebox.mIsExabm() and ebox.mCheckClusterNetworkType():
                   AtpAddiptables2Dom0(None, ebox.mGetATP(), ebox.mReturnDom0DomUPair(), ebox.mGetMachines(), ebox.mGetNetworks()).mExecute()
                # Set IPrules in the Dom0s sepcific to the VMs we'll create
                if ebox.mIsExabm():
                    _nftDom0s = ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL8"])
                    if _nftDom0s:
                        ebIpTablesRoCE.mSetupSecurityRulesExaBM(
                            ebox, aOptions.jsonconf, aDom0s=_nftDom0s)

                ebox.mLogStepElapsedTime(_step_time,
                    'Setup IPRules (iptables/nftables) on Dom0')

            #
            # PRE-VM Update/Copy images/bits (TODO: Step currently very slow in need or improvement)
            #
            if not imageBom.mIsSubStepExecuted(self.step, "COPY_IMAGES"):
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Copy/Update images on Dom0')
                ebox.mUpdateDepFiles()
                ebox.mLogStepElapsedTime(_step_time, 'Copy/Update images on Dom0')


            #
            # Setup Access.conf in nodes when needed
            #
            if not imageBom.mIsSubStepExecuted(self.step, "SET_ACCESS_CONF"):

                if not ebox.mCheckConfigOption('secure_ssh_all', 'False'):
                    _step_time = time.time()
                    ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Secure DOM SSH')
                    ebox.mSecureDom0SSH()
                    if ebox.mIsExaScale() and not ebox.mIsOciEXACC():
                        addRoceNetworkHostAccessControl(aOptions)
                    ebox.mLogStepElapsedTime(_step_time, 'Secure DOM SSH')

                    if (ebox.mIsFedramp() and
                        ebox.mCheckConfigOption ('whitelist_admin_network_cidr', 'True')):
                        _step_time = time.time()
                        ebox.mUpdateStatusCS(True, self.step, steplist,
                            aComment='Fedramp Whitelist Admin Network Cidr on Dom0s and Cells')
                        _dom0s, _, _cells, _ = ebox.mReturnAllClusterHosts()
                        _hosts = _dom0s + _cells
                        for _host in _hosts:
                            with connect_to_host(_host, get_gcontext()) as _node:
                                _csu.mWhitelistCidr(ebox, _node)
                        ebox.mLogStepElapsedTime(_step_time,
                            'Fedramp Whitelist Admin Network Cidr on Dom0s and Cells')

            #
            # XEN/IB CHECK PKEYS
            #
            if not imageBom.mIsSubStepExecuted(self.step, "CHECK_PKEYS"):
                if not ebox.mIsKVM() and not ebox.mIsExaScale():
                    _step_time = time.time()
                    ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Check/Delete PKEYS on IB-Switches')
                    ebox.mCheckCellsPkeyConfig()
                    _allGuids = ebox.mGetAllGUID()
                    _pkeys = ebox.mCheckPkeysConfig(_allGuids, True)
                    ebox.mLogStepElapsedTime(_step_time, 'Check/Delete PKEYS checks completed')

            #
            # ExaCC Specific Steps
            #
            if not imageBom.mIsSubStepExecuted(self.step, "EXACC_SETUP") and ebox.mIsOciEXACC():
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='ExaCC Specific Setup')

                # Roce steps
                if ebox.mIsKVM():
                    if ebox.mIsRoCEQinQ():
                        ebLogInfo('RoCE must have been configured during CPS reimage. Verifying setup is correct.')
                        ebox.mCheckCPSQinQSetup()
                    else:
                        _exacc_roce_cps = ExaCCRoCE_CPS(ebox.mIsDebug(), True)
                        _exacc_roce_cps.mSetupCPSRoCE()

                # IB Based steps
                else:
                    _allGuids = ebox.mGetAllGUID()
                    _pkeys = ebox.mCheckPkeysConfig(_allGuids, True)
                    if _pkeys is not None:
                        _exacc_ib_cps = ExaCCIB_CPS(_allGuids, _pkeys, ebox.mIsDebug(), True)
                        _dom0s, _, _cells, _ = ebox.mReturnAllClusterHosts()
                        _exacc_ib_cps.mSetupIBSwitches(_dom0s, _cells)
                        _exacc_ib_cps.mSetupCPSIB()

                # opctl is supported only for exacc
                mChangeOpCtlAudit(ebox, True)

                # Removal of ExaCC Macros file
                ebox.mRemoveExaCCMacrosVerify("Dom0")
                ebox.mLogStepElapsedTime(_step_time, 'ExaCC Specific Setup')

        #
        # Check if time format property is included in dom0s and cells' .bashrc file
        #
        if not imageBom.mIsSubStepExecuted(self.step, "HISTTIMEFORMAT"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist,
                aComment='Enable HISTTIMEFORMAT in Infra nodes')

            _dom0s, _, _cells, _ = ebox.mReturnAllClusterHosts()
            if ebox.mIsXS():
                _cells = []
            _hostnames = _dom0s + _cells

            _filepath = os.path.expanduser("/root/.bashrc")
            _keyValue, _sep = {"HISTTIMEFORMAT": '"%d/%m/%y %T"'}, "="

            ebLogInfo(f'Looking for property HISTTIMEFORMAT in all nodes')
            for _hostname in _hostnames:
                with connect_to_host(_hostname, get_gcontext()) as _host:
                    try:
                        node_update_key_val_file(_host, _filepath, _keyValue, sep=_sep, ignore=True)
                    except Exception as exp:
                        ebLogError(f"Failed to look for HISTTIMEFORMAT property due to the following exception: ")
                        ebLogError(str(exp))
            ebox.mLogStepElapsedTime(_step_time,
                'Enable HISTTIMEFORMAT in Infra nodes')

        #
        # Update bonding configuration only if static bridges are supported.
        #
        if not imageBom.mIsSubStepExecuted(self.step, "UPDATE_BONDING"):
            # No need to run this in exadb-xs as exacompute will
            # run bonding setup which will set the configs
            if not ebox.mIsExaScale():
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist,
                    aComment='Update bonding configuration')
                if clubonding.is_static_monitoring_bridge_supported(
                        ebox, payload=aOptions.jsonconf):
                    clubonding.update_bonded_bridges(ebox, payload=aOptions.jsonconf)
                ebox.mLogStepElapsedTime(_step_time,
                    'Update bonding configuration')

        #
        # PRE-VM network config setup
        #
        if not imageBom.mIsSubStepExecuted(self.step, "NETWORK_DISCOVERY"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Check Network Discovery')
            if ebox.mCheckDom0NetworkType():
                if ebox.mCheckConfigOption('reset_net_mapping','True'):
                    ebox.mResetDom0NetworkMapping()
            ebox.mLogStepElapsedTime(_step_time, 'Network Discovery checks completed')

        #
        # PRE-VM reclaim dom0 local disk space from unused LVs
        #
        if not imageBom.mIsSubStepExecuted(self.step, "DOM0_SETUP"):

            # PRE_VM logrotation setup for log files under
            # '/opt/exacloud/clusters/operations'
            ebox.mEnableLogRotationOnDom0()
            ebox.mRestoreMissingMountPoints()
            ebox.mConfigureArp()
            self.mRpmCheck(ebox)

            if not ebox.mIsKVM():
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist,
                    aComment='Running reclaimdisks.sh -extend-vgexadb')
                ebox.mRunReclaimdisks('extend-vgexadb')
                ebox.mLogStepElapsedTime(_step_time,
                    'PREVM SETUP : reclaim disks space from unused LVs on Dom0')

            else:
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Resize logical volume EXAVMIMAGES')
                ebox.mResizeExaVMImages()
                ebox.mLogStepElapsedTime(_step_time, 'PREVM INSTALL : resize EXAVMIMAGES from unused LVs on Dom0')

        #
        # PRE-VM Update/Copy vmetrics and xend-config.sxp
        #
        if not imageBom.mIsSubStepExecuted(self.step, "COPY_VM_METRICS"):
            if not ebox.mIsKVM():
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Update vmetrics and xend-config.sxp on Dom0')
                ebox.mUpdateVmetrics('vmexacs')
                ebox.mStopVmetrics()
                ebox.mXendConfig()
                ebox.mLogStepElapsedTime(_step_time, 'PREVM SETUP : Update vmetrics and xend-config.sxp on Dom0')
            else:
                ebLogInfo("Skip updating xend-config.sxp for KVM")

        #
        # PRE-VM Create PreVm Keys Oeda WorkDir
        #
        if not imageBom.mIsSubStepExecuted(self.step, "PRECREATE_SSH_KEY"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Create PreVm Keys Oeda WorkDir')
            ebox.mCreatePreVmKeysOedaWorkDir()

            #keys in config directory are injected into dom0s, switches, cells, iloms etc
            ebox.mInjectSSHMasterKey()
            ebox.mLogStepElapsedTime(_step_time, 'Create PreVm Keys Oeda WorkDir')

            if ebox.IsZdlraHThread() is False:
                ebox.mGetZDLRA().mEnableDisableHT("Disabled", aOptions)
            #
            # PRE-VM Create and push luks devices passphrase to SiV for ExaCS
            #
            if not ebox.mIsExaScale() and isEncryptionRequested(aOptions, 'domU') and not ebox.mIsOciEXACC():

                # Don't create and push luks passphrase if property is we're using local passphrase
                if not useLocalPassphrase():
                    _step_time = time.time()
                    ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Create and push luks devices passphrase')
                    _domu_list = [ _domu for _ , _domu in ebox.mReturnDom0DomUPair()]
                    createAndPushRemotePassphraseSetup(aOptions, _domu_list)
                    ebox.mLogStepElapsedTime(_step_time, 'Create and push luks devices passphrase')

                # Create Marker file for Encryption
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Create crypto luks marker file')
                for _dom0, _domU in ebox.mReturnDom0DomUPair():
                    createEncryptionMarkerFileForVM(_dom0, _domU)
                ebox.mLogStepElapsedTime(_step_time, 'Create crypto luks marker file')

            #
            # PRE-VM Store luks passphrase in ExaKMSDB for ExaCC
            #
            if ebox.mIsOciEXACC() and exacc_fsencryption_requested(aOptions):
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Store luks passphrase in ExaKMSDB for ExaCC')
                _domu_list = [ _domu for _ , _domu in ebox.mReturnDom0DomUPair()]
                exacc_save_fsencryption_passphrase(aOptions, _domu_list)
                ebox.mLogStepElapsedTime(_step_time, 'Store luks passphrase in ExaKMSDB for ExaCC')

                # Create Marker file for Encryption
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Create crypto luks marker file')
                for _dom0, _domU in ebox.mReturnDom0DomUPair():
                    createEncryptionMarkerFileForVM(_dom0, _domU)
                ebox.mLogStepElapsedTime(_step_time, 'Create crypto luks marker file')

        ebLogInfo('csPreVMSetup: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "Pre VM setup completed", 'ESTP_PREVM_SETUP')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Pre VM Setup", "Done", _stepSpecificDetails)

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPreVMSetup: Entering undoExecute')
        _ebox = aExaBoxCluCtrlObj
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'ONGOING', "Undo Pre VM setup in progress", 'ESTP_PREVM_SETUP')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Undo Pre VM setup", "In Progress", _stepSpecificDetails)

        self.mPostVMDeleteSteps(aExaBoxCluCtrlObj, aOptions, aStepList)

        if _ebox.mIsXS():
            try:
                _utils = ebExascaleUtils(_ebox)
                _utils.mDetachAcfsVolume(aOptions, aForce=True)
                _utils.mDeleteFilesInDbVault(aOptions)
                _utils.mUpdateACL(aOptions, aAclPriv="none")
            except Exception as e:
                ebLogWarn(f"*** mDeleteFilesInDbVault failed with Exception: {str(e)}")

        ebLogInfo('csPreVMSetup: Completed undoExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'DONE', "Undo Pre VM setup completed", 'ESTP_PREVM_SETUP')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Undo Pre VM Setup", "Done", _stepSpecificDetails)




