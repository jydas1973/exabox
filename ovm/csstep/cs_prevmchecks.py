"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_prevmchecks.py - Create Service PRE VM CHECKS

FUNCTION:
    Implements the Pre VM checks for create service execution 

NOTES:
    Invoked from cs_driver.py 

EXTERNAL INTERFACES: 
    csPreVMChecks        ESTP_PREVM_CHECKS

INTERNAL CLASSES:

History:
    MODIFIED (MM/DD/YY)
    prsshukl  11/19/25 - Bug 38037088 - BASE DB -> MOVE THE DO/UNDO STEPS FOR
                         BASEDB TO A NEW FILE IN CSSTEP
    naps      06/26/25 - Bug 38042220 - precheck for basedb clone operation.
    avimonda  04/03/25 - Bug 37742228 - EXACS: PROVISIONING FAILED WITH
                         ERROR:OEDA-1602: INVALID BOND FOR BRIDGE BONDETH1
                         ON HOST <DOM0>
    jfsaldan  03/24/25 - Bug 37406059 - ETF: IN CREATE SERVICE FAILING IN
                         PRECHECKS WITH ERRORS IDENTIFIED FROM HARDWARE HEALTH
                         CHECK: {'SCAQAB10CELADM12': {'GRIDDISK': 'ABNORMAL'},
                         'SCAQAB10CELADM11': {'GRIDDISK': 'ABNORMAL'}}
    rajsag    03/11/25 - Enh 37526315 - support additional response fields in
                         exacloud status response for create service steps
    jfsaldan  03/03/25 - Bug 37609603 - EXADB-XS-PP: VMC PROVISION FAILED AT
                         THE STEP5 _CREATE_VIRTUAL_MACHINE WITH ERROR "MOUNT
                         POINT DOES NOT EXIST" | PARALLEL OP INCORRECTLY
                         REMOVES A NON STALE GUEST DIRECTORY
    jfsaldan  02/10/25 - Bug 37570873 - EXADB-D|XS -- EXACLOUD | PROVISIONING |
                         REVIEW AND ORGANIZE PREVM_CHECKS AND PREVM_SETUP STEPS
    prsshukl  11/28/24 - Bug 37240032 - Add ntp and dns value pre and post OEDA
                         create vm
    akkar     08/12/24 - Bug 36890137: Skip ahf install on dom0 till ahf fix
    pbellary  07/02/24 - ENH 36690772 - EXACLOUD: IMPLEMENT PRE-VM STEPS FOR EXASCALE SERVICE
    prsshukl  05/08/24 - Enh 36442918 - ADD A PRECHECK TO STOP PROVISIONING IF
                         VM NAME STARTS WITH "VM" AND AT LEAST ONE KVM DOM0 HAS
                         (< 23.1.90.0.0.231219) EXADATA IMAGE
    egalaviz  11/28/23 - XbranchMerge egalaviz_bug-35895844 from
                         st_ecs_22.3.1.4.0
    jesandov  10/16/23 - 35729701: Support of OL7 + OL8
    avimonda  10/14/23 - Bug 35863659 - Added automatic detection and removal
                         abilities for the stale VM directories in
                         /EXAVMIMAGES/GuestImages
    jesandov  07/27/22 - Bug 35646600 - ExaCC will have different version in cells
    prsshukl  10/18/22 - Bug 34614475 - Added RPM precheck and autorectified it
                         if RPM database is corrupt.
    scoral    08/02/22 - Bug 34482855 - Migrate to bonding static bridges.
    scoral    06/22/22 - Bug 34300556 - Moved bonding setup from undo of PreVM
                         Checks to undo of PreVM Setup.
    jlombera  03/28/22 - Bug 34000208: pass JSON payload to
                         clubonding.is_static_monitoring_bridge_supported()
    jlombera  03/18/22 - Bug 33244220: add support for bonding static
                         monitoring bridge
    jlombera  03/08/22 - Bug 33891346: update comment regarding bondmonitor
                         configuration
    jlombera  01/12/22 - Bug 33749491: configure bonding in shared envs
    scoral    10/07/21 - Bug 33445835: Added extra logging for the cells
                         PMEMLOG & PMEMCACHE.
    jlombera  06/01/21 - Bug 32920094: check System Image version consistency
    jvaldovi  05/07/21 - Bug 32862631 - EXACS:20.4.1.2:VNUMA MARKER NOT
                         DELETING VNUMA MARKER IN STEP BASE FLOW
    jvaldovi  03/18/21 - Enh 32621312 - Marker Script To Disable Vnuma
    jlombera  02/17/21 - Bug 32422373: undo bonding config during
                         create-service at PreVMChecks (required for X8M)
    dekuckre  06/19/19 - 29928603: Sync-up legacy and stepwise create service    
    srtata    04/19/19 - bug 29556301: run exachk based on config parameter
    pbellary  04/17/19 - bug 29472359: undo stepwise createservice
    srtata    03/05/19 - Creation

"""
import time

from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogTrace
import exabox.ovm.clubonding as clubonding
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.ovm.clustorage import ebCluStorageConfig
from exabox.healthcheck.cluexachk import ebCluExachk
from exabox.utils.node import connect_to_host, node_exec_cmd_check
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.clunetworkvalidations import ebNetworkValidations
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.ovm.cluexascale import ebCluExaScale

# This class implements doExecute and undoExecute functions
# for the ESTP_PREVM_CHECKS step of create service
class csPreVMChecks(CSBase):
    def __init__(self):
        self.step = 'ESTP_PREVM_CHECKS'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPreVMChecks: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        steplist = aStepList
        imageBom = ImageBOM(ebox)

        _csu = csUtil()
        _pchecks = ebCluPreChecks(ebox)
        ebox.mUpdateStatus('createservice step ESTP_PREVM_CHECKS')
        _clu_utils = ebCluUtils(ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "Pre VM check in progress", 'ESTP_PREVM_CHECKS')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Pre VM Checks", "In Progress", _stepSpecificDetails)

        # Check if infra node have the same System Image version
        if not imageBom.mIsSubStepExecuted(self.step, "IMG_CONSISTENCY_CHECKS"):
            _dom0s, _, _cells, _ = ebox.mReturnAllClusterHosts()

            _skipDom0Check = False
            if aOptions and aOptions.jsonconf and \
               "skip_sysimage_version_check" in aOptions.jsonconf and \
               str(aOptions.jsonconf['skip_sysimage_version_check']).lower() == "true":
                _skipDom0Check = True

            if not _skipDom0Check:
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Dom0 Image Consistency Checks')
                self.check_sys_img_version_consistency(_dom0s, ebox.mGetCtx())
                ebox.mLogStepElapsedTime(_step_time, 'Dom0 Image Consistency Checks')

            # Bug: 35646600  ExaCC will have different version in cells
            # Adding exabox parameter 'skip_sysimage_version_check_cell'= "true" for allowing 
            # different cell versions
            if ebox.mIsXS() or ebox.mIsExaScale():
                _skipCellImageCheck = True
            else:
                _skipCellImageCheck = False

            if ebox.mCheckConfigOption('skip_sysimage_version_check_cell') and \
               ebox.mCheckConfigOption('skip_sysimage_version_check_cell').lower() ==  "true":
                _skipCellImageCheck = True
                ebLogInfo("Skipping cell images check by exabox skip_sysimage_version_check_cell")

            if not ebox.mGetSharedEnv() and not _skipCellImageCheck:
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Cell Image Consistency Checks')
                self.check_sys_img_version_consistency(_cells, ebox.mGetCtx())
                ebox.mLogStepElapsedTime(_step_time, 'Cell Image Consistency Checks')


        #
        # Fix the PMEMLOG from the cells first
        #
        if not imageBom.mIsSubStepExecuted(self.step, "PMEMLOG_PMEMCACHE"):
            if not ebox.mIsExaScale() and not ebox.mIsXS() and ebox.mIsKVM():

                ebLogTrace("Checking cells dgs before Checking Cell's PMEMLOG and PMEMCACHE status")

                _dgList = []
                _ebCluStorageConfigObj = ebCluStorageConfig(ebox, ebox.mGetConfig())
                _, _, _cells, _ = ebox.mReturnAllClusterHosts()
                for _cell in _cells:
                    with connect_to_host(_cell, get_gcontext()) as _node:
                        _dgList += _ebCluStorageConfigObj.mListCellDG(_node, aSuffix=None)

                if not _dgList: # Execute only in first provisioning
                    # Grab lock
                    ebox.mAcquireRemoteLock()
                    ebLogInfo("*** Checking Cell's PMEMLOG and PMEMCACHE status... ")
                    _cells = ebox.mReturnCellNodes().keys()
                    ebCluStorageConfig.mFixPMEMComponent(_cells, "log")
                    ebCluStorageConfig.mFixPMEMComponent(_cells, "cache")
                    #Releasing remote lock
                    ebox.mReleaseRemoteLock()

        # Note: Ref Bug 37406059: run vm exists check before
        # mFetchHardwareAlerts()
        # Check if VM already exists -- skip precheck / semantic
        ebLogTrace('csPreVMChecks: Entering mVMPreChecks')
        if _pchecks.mVMPreChecks():
            _error_str = '*** Fatal ERROR - VMs already existing can not continue VM install'
            ebLogError(_error_str)
            raise ExacloudRuntimeError(0x0410, 0xA, _error_str,aStackTrace=False,
                   aStep=self.step, aDo=True)

        #
        # PRE-VM Hardware Alert check
        #
        if not imageBom.mIsSubStepExecuted(self.step, "HW_PRECHECKS"):
            _max_retries = 3
            _retry_count = 0
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='HW Prechecks')
            while _retry_count < _max_retries:
                if _pchecks.mFetchHardwareAlerts(aOptions, aStep=self.step):
                    break
                else:
                    _retry_count += 1
                    if _retry_count < _max_retries:
                        time.sleep(5)  # wait 5 seconds before retrying
            if _retry_count == _max_retries:
                _error_str = '*** Fatal ERROR - Hardware alerts fetching failed after {} retries'.format(_max_retries)
                ebLogError(_error_str)
                raise ExacloudRuntimeError(0x0390, 0xA, _error_str, aStackTrace=False,
                   aStep=self.step, aDo=True)
            ebox.mLogStepElapsedTime(_step_time, 'HW Prechecks')

        #
        # Exacheck
        #
        if not imageBom.mIsSubStepExecuted(self.step, "EXECUTE_EXACHK"):
            _enable_exachk = ebox.mCheckConfigOption('enable_exachk')
            if _enable_exachk:
                if 'pre_create_vm' in _enable_exachk and _enable_exachk['pre_create_vm'] == 'True':
                    _step_time = time.time()
                    ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Entering mExecuteExachk')
                    ebox.mExecuteExachk()
                    ebox.mLogStepElapsedTime(_step_time, 'Completed mExecuteExachk')

        #
        # Dom0 specific checks
        #
        if not imageBom.mIsSubStepExecuted(self.step, "CLEANUP_BONDING"):
            # Bonded-bridge configuration might cause net VM pre-checks to fail,
            # thus cleanup bonding first.  Bonding will be configured later at
            # CreateVM step.
            #
            # This operation is only required if static bonded-bridge creation is
            # not supported in the cluster.
            # In case static bonded-bridges are supported for this cluster, we'll
            # try to make sure the bridges are configured as dynamic to avoid
            # cleanup during provisioning.
            #
            # NOTE: We must make sure to configure the bonded-bridge again during
            #       cleanup (see undoExecute()) in case the flow never reaches
            #       bonding setup at CreateVM (e.g. if some step in between fails
            #       and the flow is aborted).

            if not ebox.mIsExaScale():
                clubonding.migrate_static_bridges(ebox, aOptions.jsonconf)
                if not clubonding.is_static_monitoring_bridge_supported(
                        ebox, payload=aOptions.jsonconf):
                    _step_time = time.time()
                    ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Cleanup bonding')
                    clubonding.cleanup_bonding_if_enabled(
                        ebox, payload=aOptions.jsonconf, cleanup_bridge=True,
                        cleanup_monitor=False)
                    ebox.mLogStepElapsedTime(_step_time, 'Cleanup bonding')

            if not ebox.mIsOciEXACC() and ebox.mIsKVM() and ebox.mCheckConfigOption('detect_and_remove_stale_bondeth_interface'):
                self.mDetectAndRemoveStaleBondethInterface(ebox)



        # Run Dom0 PRECHECKS
        # Internally this includes some checks on the XML combined with dom0
        # checks
        if not imageBom.mIsSubStepExecuted(self.step, "DOM0_PRECHECKS"):

            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Dom0 specific checks')

            # Ethernet speed checks
            _net_val_mgr = ebNetworkValidations(ebox, ebox.mReturnDom0DomUPair())
            _ifaces_to_update = _net_val_mgr.mCheckDom0EthernetSpeed()
            if _ifaces_to_update:

                # Grab lock if change is needed, but check once again before applying
                # change
                _remote_lock = ebox.mGetRemoteLock()
                with _remote_lock():
                    _ifaces_to_update = _net_val_mgr.mCheckDom0EthernetSpeed()
                    if _ifaces_to_update:
                        _net_val_mgr.mUpdateDom0EthernetSpeeds(_ifaces_to_update)


            # Node specific checks (XML duplicate ips, consistency checks,
            # space availability)
            if _pchecks.mRunAllPreChecks(aVerboseMode=False,aMode=csConstants.VMGI_MODE) == False:
                _error_str = '*** Fatal ERROR - Dom0 checks failed, can not continue VM install'
                ebLogError(_error_str)
                raise ExacloudRuntimeError(0x0390, 0xA, _error_str,aStackTrace=False,
                   aStep=self.step, aDo=True)

            # Enable firewall service
            for _dom0, _ in ebox.mReturnDom0DomUPair():
                with connect_to_host(_dom0, get_gcontext()) as _node:
                    if ebox.mIsHostOL8(_dom0):
                        ebox.mEnableDom0Service('nftables', _node, _dom0)
                    else:
                        ebox.mEnableDom0Service('iptables', _node, _dom0)

            # Misc checks
            ebox.mCheckDom0Resources(aOptions)
            # Below check is for kvm only, and NOT to be run for exacompute
            if not ebox.mIsExaScale() and ebox.mIsKVM() and ebox.mCheckConfigOption('detect_and_remove_stale_vm_dirs'):
                self.mDetectAndRemoveStaleVMdirs(ebox)
            ebox.mRemoveXleaveFromNtpConf()

            # Check VM Name
            if ebox.mIsKVM() and not ebox.mIsExaScale():
                ebLogInfo('csPreVMChecks: Entering mCheckVmNamePrefix')
                if _pchecks.mCheckVmNamePrefix():
                    _error_str = '*** Fatal ERROR - Prechecks failed, can not continue VM install'
                    ebLogError(_error_str)
                    raise ExacloudRuntimeError(0x0390, 0xA, _error_str,aStackTrace=False,
                                            aStep=self.step, aDo=True)

            ebox.mLogStepElapsedTime(_step_time, 'Dom0 specific checks')

        #
        # Cell checks
        #
        if not ebox.mIsExaScale():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Cell specifc checks')
            ebox.mCheckCellCompliance()
            ebox.mCheckDiskResources()
            ebox.mCheckCellsStatus()
            self.log_cells_pmem_components(ebox)
            ebox.mLogStepElapsedTime(_step_time, 'Cell specific checks')

        #
        # Switch checks
        #
        if not ebox.mIsKVM():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Switch specific checks')
            ebox.mCheckSwitchFreeSpace()
            ebox.mLogStepElapsedTime(_step_time, 'Switch specific checks')

        ebLogInfo('csPreVMChecks: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "Pre VM check completed", 'ESTP_PREVM_CHECKS')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Pre VM Checks", "Done", _stepSpecificDetails)

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPreVMChecks: Entering undoExecute')


