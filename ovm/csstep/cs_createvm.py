"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_createvm.py - Create Service CREATE VM

FUNCTION:
    Implements the Create VM step for create service execution 

NOTES:
    Invoked from cs_driver.py 

EXTERNAL INTERFACES: 
    csCreateVM     ESTP_CREATE_VM

INTERNAL CLASSES:

History:
    MODIFIED (MM/DD/YY)
    prsshukl  11/19/25 - Bug 38037088 - BASE DB -> MOVE THE DO/UNDO STEPS FOR
                         BASEDB TO A NEW FILE IN CSSTEP , REMOVE CODE THAT IS
                         UNNECESSARY FOR BASEDB
    avimonda  10/21/25 - Bug 38442915 - OCI: ADD MAXDISTANCE 16 PARAMETER IN
                         DOMU CHRONY CONFIG BEFORE CLUSTER CREATION SANITY
                         CHECK.
    prsshukl  04/11/25 - Enh 37807155 - EXADB-XS 19C :CS AND ADD COMPUTE ENDPOINT UPDATE -> 
                         USE OEDACLI CMD TO ATTACH DBVOLUME VOLUMES TO GUEST VMS
    prsshukl  04/03/25 - Enh 37740750 - EXADB-XS 19C :CS AND ADD COMPUTE
                         ENDPOINT UPDATE-> ATTACH DBVOLUME VOLUMES TO GUEST VMS
    rajsag    03/11/25 - Enh 37526315 - support additional response fields in
                         exacloud status response for create service steps
    prsshukl  11/28/24 - Bug 37240032 - Add ntp and dns value pre and post OEDA
                         create vm
    naps      07/24/24 - Bug 36864558 - Update chasis info after create_vm
                         step.
    pbellary  06/21/24 - ENH 36690743 - EXACLOUD: IMPLEMENT OEDA STEPS FOR EXASCALE CREATE SERVICE
    gsundara  04/12/24 - Bug 36491981 - deploy vmconsole bits during create
                         service if already not present (not for ExaCC)
    dekuckre  04/03/24 - 36503657: Remove gcv volume for deleted vms.
    prsshukl  02/14/24 - Bug 36260050 - SUPPORT CREATING TEST OVERRIDE URL FOR
                         EXASCALE CLUSTERS
    jfsaldan  01/26/24 - Bug 35471024 - EXACS:22.2.1:DROP4:FS ENCRYPTION
                         VALIDATION FOR OL8
    jesandov  10/27/23 - 35922798: Add remote lock to mCheckSystemImages
    jfsaldan  10/24/23 - Bug 35909734 - EXACS:23.4.1:FILE SYSTEM ENCRYPTION:KVM
                         ENCRYPTION TAG GETS DELETED BEFORE CALLING OEDA
    jesandov  10/16/23 - 35729701: Support of OL7 + OL8
    pbellary  08/25/23 - Bug 35737837 - EXACS:23.4.1:X9M:MULTI-VM:ADBD PROVISIONING FAILING AT CREATE VM
                           STEP:ERROR - 6153 - UNABLE TO REMOVE STALE DUMMY BRIDGE VMETH200
    pbellary  08/22/23 - Enh 35728221 - ADD SUPPORT FOR 2TB MEMORY IN X10M
    gparada   07/10/23 - 35529689 Refactored cluctl.mCheckSystemImage 
    pbellary  06/28/23 - 35543679 - ADD VM (ON NON 2TB SYSTEM) FAILING AT PRECHECK:"ERROR-MESSAGE": "2TB MEMORY NOT SUPPORTED ON DOM0 
    gparada   06/08/23 - 35402940 ECRA can define OS version to setup in VM
    pbellary  06/06/23 - ENH 35445802 - EXACS X9M - ADD SUPPORT FOR 2TB MEMORY IN X9M
    jfsaldan  05/24/23 - Bug 35410783 - EXACLOUD FAILED TO CALCULATE THE NON
                         ENCRYPTED FIRST BOOT IMAGE
    scoral    05/04/23 - Bug 35298579 - Move the temporary iptables rules setup
                         to CreateVM.
    scoral    04/14/23 - Bug 35177571 - Use bridge family instead of ip
                         family for VM NFTables rules in OL8 envs.
    rajsag    03/27/23 - 35221187 - create_vm task failing with error while
                         performing postchecks for ip route/dns validation
                         after vm creation
    rajsag    03/14/23 - Enh 34837590 - implement postchecks for ip route and
                         dns validation after vm creation
    aararora  01/02/23 - Add DR network configuration during cluster
                         provisioning.
    pbellary  10/17/22 - Bug 34686909 - FOR HETERO ENV, PATCH THE XML WITH CORRECT INTERFACES
    naps      09/13/22 - Bug 34538968 - Generate correct random password for
                         zdlra to include both uppercase and lowercase chars.
    jlombera  03/28/22 - Bug 34000208: pass JSON payload to
                         clubonding.is_static_monitoring_bridge_supported()
    jlombera  03/18/22 - Bug 33244220: add support for bonding static
                         monitoring bridge
    jlombera  03/08/22 - Bug 33891346: configure bondmonitor at CreateVM
    ajayasin  02/16/22 - stale bridge removal
    jlombera  01/12/22 - Bug 33749491: configure bonding in shared envs
    jlombera  12/01/21 - ENH 33304767: honor _skip_jumbo_frames_config
                         exabox.conf param
    naps      07/27/21 - enable back HT during prevmsetup undo stage.
    naps      07/07/21 - Disable HT for elastic nodes.
    dekuckre  15/06/21 - 32982101: Update nonroot password and store in wallet
                         in ZDLRA env
    ajayasin  05/19/21 - 32860518 - Add volume u01 xml patching
    rajsag    05/10/21 - 32847732 - exacc:ds: delete cluster doesnot remove
                         files under clusterjson
    jlombera  03/23/21 - Bug 32620666: use new clujumboframes API
    jlombera  02/18/21 - Bug 32422373: undo bonding config during
                         create-service at PreVMChecks instead of CreateVM
    naps      02/18/21 - Remove correct vms while cleaning up.
    naps      02/10/21 - Patch xml with zdlra attrs and enable hyperthreading
                         during deleteservice.
    naps      02/04/21 - Cleanup Bridge during DeleteService.
    jlombera  01/12/21 - Bug 32295581: use new clubonding API
    jlombera  12/07/20 - Bug 32166715: cleanup bonding before OEDA CREATE_VM
                         step
    dekuckre  11/20/20 - 32177169: Correct logging.
    jlombera  11/02/20 - Bug 31862187: cleanup bonding configuration when
                         undoing VM creation
    diyanez   09/11/20 - 31861044 - OCIEXACC: ADBD: exacloud needs to create
                         secscan user with UID < 3000
    dekuckre  08/14/20 - 31747137: Verify VM deletion.
    dekuckre  03/18/20 - 31046996: use mExecuteOedaStep for OSTP_CREATE_VM
    pbellary  04/17/19 - bug 29472359: undo stepwise createservice
    srtata    03/05/19 - Creation

"""
import exabox.ovm.clubonding as clubonding
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.log.LogMgr import ebLogInfo, ebLogTrace, ebLogError
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext                                                                                                                                                                                                  

# This class implements doExecute and undoExecute functions
# for the ESTP_CREATE_VM step of create service
# This class primarily invokes OEDA do/undo create VM step
class csCreateVM(CSBase):
    def __init__(self):
        self.step = 'ESTP_CREATE_VM'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csCreateVM: Entering doExecute')
        _ebox = aExaBoxCluCtrlObj
        _csu = csUtil()
        imageBom = ImageBOM(_ebox)
        _pchecks = ebCluPreChecks(_ebox)
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "Create VM in progress", 'ESTP_CREATE_VM')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Create VM ", "In Progress", _stepSpecificDetails)
        _exascale = ebCluExaScale(_ebox)

        if not imageBom.mIsSubStepExecuted(self.step, "CONFIGURE_DOMU_PASSWORD_OEDA"):
            if _ebox.IsZdlraProv():
                # Update non root password (es.properties) in ZDLRA env from wallet  
                _password = _ebox.mGetZDLRA().mGenerate_random_password()
                _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _password) 

        self.mCreateVM(_ebox, aOptions, aStepList)

        if not imageBom.mIsSubStepExecuted(self.step, "CONFIGURE_DOMU_PASSWORD_EXACLOUD"):
            if _ebox.IsZdlraProv():
                # Update the password (generated above) in ZDLRA wallet
                _ebox.mGetZDLRA().mCreateWallet()
                if _ebox.mGetZDLRA().mGetWalletViewEntry("passwd"):
                    _ebox.mGetZDLRA().mDelWalletEntry("passwd")
                _ebox.mGetZDLRA().mAddWalletEntry("passwd", _password)

            #
            # Setting CSWLIB_OSS_URL environment variable in domU for Exascale clusters
            #
            if _ebox.mIsExaScale():
                _csu.mSetEnvVariableInDomU(_ebox)

        #
        # Attach virtio serial device to KVM Guest.
        # Update the chasis information to GuestVM. 
        #
        if not imageBom.mIsSubStepExecuted(self.step, "START_VM_EXACS_SERVICE"):
            if not _ebox.mIsExaScale():
                if _ebox.mIsKVM():
                    _ebox.mUpdateVmetrics('vmexacs_kvm')
                    _ebox.mStartVMExacsService(aOptions, aCheckCrsAsm=False)     

        # Run ntp and dns updation as oeda create vm will remove these entries
        if not imageBom.mIsSubStepExecuted(self.step, "ADD_MISSING_DNS_NTP"):
            ebLogInfo('csCreateVM: Entering mAddMissingNtpDnsIps')
            if _ebox.mIsKVM() and (_csu.mReturnCountofVm(_ebox) == 1):
                _dom0s, _, _cells, _ = _ebox.mReturnAllClusterHosts()
                _hostList = _dom0s + _cells
                if _ebox.mIsExaScale():
                    _pchecks.mAddMissingNtpDnsIps(_dom0s)
                else:
                    _pchecks.mAddMissingNtpDnsIps(_hostList)

        if _ebox.isDBonVolumes() and _ebox.mCheckConfigOption("exadbxs_19c_invoke_oedacli", "False"):
            _exascale.mAttachDBVolumetoGuestVMs(aWhen="CS")

        try:
            self.maxDistanceUpdate(_ebox)
        except Exception as e: 
            ebLogError(f"*** maxDistanceUpdate failed with Exception: {str(e)}")

        ebLogTrace('csCreateVM: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "Create VM in completed", 'ESTP_CREATE_VM')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Create VM ", "Done", _stepSpecificDetails)

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csCreateVM: Entering undoExecute')
        _ebox = aExaBoxCluCtrlObj
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'ONGOING', "Undo Create VM in progress", 'ESTP_CREATE_VM')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Undo Create VM ", "In Progress", _stepSpecificDetails)

        if _ebox.IsZdlraProv():                                                                                                                 
            # Update non root password (es.properties) in ZDLRA env from wallet                                                                
            _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd')                                                                             
            _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd) 

        if _ebox.mGetCmd() == 'deleteservice': 
            _exascale = ebCluExaScale(_ebox)                                                                                                                                                                         
            _json = {}
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():        
                for _dev in ['u01', 'u02']:
                    ebLogInfo(f"Checking if any snapshots need to be unmounted as part of delete service")
                    _lvm, _snap_dev = _exascale.mGetLVDev(_dom0, _domU, _dev)
                    if not _snap_dev or not _lvm:
                        ebLogInfo(f"No {_dev} snapshot mounted for the VM {_domU}. Nothing to unmount")
                        continue
                    _json['snapshot_device_name'] = _snap_dev 
                    _json['lvm'] = _lvm
                    _json['dom0'] = _dom0
                    _json['vm'] = _domU
                    ebLogInfo(f"Performing unmount of snapshot for {_json}")
                    _exascale.mUnmountVolume(aOptions, _json)

        self.mDeleteVM(_ebox, aOptions, aStepList)

        # Deconfigure bondmonitor.
        clubonding.cleanup_bonding_if_enabled(
            _ebox, payload=aOptions.jsonconf, cleanup_bridge=False,
            cleanup_monitor=True)

        ebLogInfo('csCreateVM: Completed undoExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'DONE', "Undo Create VM completed", 'ESTP_CREATE_VM')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Undo Create VM ", "Done", _stepSpecificDetails)
