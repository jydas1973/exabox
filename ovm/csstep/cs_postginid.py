"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_postginid.py - Create Service POST GI NID

FUNCTION:
   Implements the post GI nid for create service execution

NOTES:
    Invoked from cs_driver.py

EXTERNAL INTERFACES: 
    csPostGINID ESTP_POSTGI_NID

INTERNAL CLASSES:

History:
       MODIFIED (MM/DD/YY)
       remamid   11/26/25 - exacc natfilesystem ip different for vms in the
                            cluster bug 38581933
       joalcala  10/27/25 - Bug38397386: avoid 3rd nic setup in ADBD since
                            dbaascli not supported
       atgandhi  10/16/25 - Enh 38421350 - UPDATE PROVISIONING WORKFLOW WITH
                            FETCH VOTING DISKS
       aararora  09/05/25 - Bug 38391988: Disable tcps port config for atp
                            environment
       scoral    09/03/25 - Bug 38338038 - EXASCALE: EXACLOUD PROVISIONING
                            FAILURE OCDE STEP: NID CONFIGURATION ERROR DUE
                            TO INSUFFICIENT /VAR SPACE
       akkar     30/06/25 - Bug 38025087: dbaastool rpm for multi cloud
       aliarias  08/20/25 - Enh 38332780 - EXACC/EXACS DELINKING SYSLENS FROM
                            DBAASTOOLS (EXACLOUD MOVE EXECUTION OF
                            REMOVECLOUDPROPERTIESPAYLOAD AT THE END POSTGINID
                            STEP)
       aararora  08/07/25 - ER 37858683: Add tcps config if present in the
                            payload
       ririgoye  07/21/25 - Enh 38219932 - CPG: RAISE EXACLOUD ERROR IF THE
                            LOCATION ATTRIBUTE HAS INVALID OR EMPTY INFO IN
                            ECRA PAYLOAD
       sauchaud  07/15/25 - 38157758:ConfigCollector Implementation
       ajayasin  07/11/25 - bug 38169186 : suricata rpm is not getting
                            installed during provisioning
       ririgoye  06/30/25 - Enh 38086929 - CREATE /OPT/ORACLE/SG.JSON DURING
                            PROVISIONING OF ADBS CLUSTERS
       abflores  06/11/25 - Bug 37508725 - IMPROVE PORT SCAN
       aararora  05/12/25 - Bug 37909154: Catch exception during update of rpm
                            in undo step and proceed
       vikasras  03/18/25 - Bug 37712234 - EXACS: EXACLOUD PROVISIONING FAILURE
                            OCDE STEP: NID CONFIGURATION ERROR DUE TO
                            INSUFFICIENT /VAR SPACE
       rajsag    03/11/25 - Enh 37526315 - support additional response fields
                            in exacloud status response for create service
                            steps
       abflores  03/05/25 - Bug 37473868: Fix marker files logging
       rajsag    02/05/25 - 37508596 exacloud | postginid
                            expand_domu_filesystem runs customer fs resize
                            sequentially on each vm taking close to 4 minutes
                            more in large clusters | improve large cluster
                            provisioning time
       jfsaldan  01/29/25 - Bug 37459561 - REVIEW ECRA STEP OCDE NID
                            CONFIGURATION SCRIPT FOR PARALLEL PROCESSING
       jfsaldan  10/02/24 - Bug 37081598 - EXACC:BB:FEDRAMP: COMMON_FEDRAMP
                            SHOULD BE ENABLED ON
                            /VAR/OPT/ORACLE/CPROPS/CPROPS.INI
       gojoseph  09/24/24 - Bug 37086896 Force shutdown of domU after timeout
       joysjose  09/01/24 - Bug 36988806: Remove maxDistanceUpdate function
                            call to place it before install cluster step
       ririgoye  07/30/24 - Enh 35752204 - UPDATE CRS ORA_NET PARAMETERS DURING
                            PROVISIONING
       naps      07/24/24 - Bug 36864558 - Update chasis info after create_vm
                            step.
       ivang     07/19/24 - Bug36781578: fix regression in undo/retry
       jfsaldan  04/15/24 - Bug 36501551 - EXACLOUD - EXACC - BATCH OF PENDING
                            CREATE SERVICE ISSUES REPORTED DURING E2E TESTING
                            W/ FS ENCRYPTION ENABLED
       ivang     03/27/24 - Bug36427045: ADBD: remove dbcs-agent installation 
                            and uninstall for adbd
       scoral    03/26/24 - Bug 36446168: Add ADBD/ADBCC support for
                            mSanitizeDomUSysctlConf.
       ivang     03/20/24 - 36427045 make undo-retry work for adbd
       akkar     03/07/24 - Bug 36377723: Copy Agent pfx files for fedramp
       ririgoye  01/19/24 - Bug 36165727 - Added check to verify that failure
                            is silent when in a ExaCC environment and ExaCLI
                            password is invalid
       ririgoye  12/01/23 - Bug 35965709 - ECS : EXACLOUD SHOULD FAIL DURING
                            PROVISIONING OR ADD NODE IF IT FAILS TO SET UP THE
                            EXACLI CLOUD USER PASSWORD
       scoral    11/16/23 - Bug 36015572 - /SYS/DEVICES/VIRTUAL/DMI/ID/
                            CHASSIS_ASSET_TAG IS INCOMPLETE IN XS CLUSTER DB
                            NODES
       jfsaldan  11/10/23 - Bug 35216865 - ADB-D:PROVISIONING: EXACLOUD
                            CRSREBOOT 19.18 TAKES 1 MIN LONGER TO MOUNT ACFS
                            AND DOES NOT WAIT FOR ACFS TO BE MOUNTED AND RPMUPD
                            ENABLE FAILS IN THE DOMU
       prsshukl  11/03/23 - Bug 35823972: Copy domu certificates during
                            cs(fedramp enabled)
       jesandov  10/16/23 - 35729701: Support of OL7 + OL8
       scoral    10/06/23 - Bug 35884515 - Sanitize /etc/sysctl.conf in DomUs.
       rajsag    09/29/23 - 35853827 - atp x10m: postginid exacloud create
                            service step failure. hugepages should not be done
                            for adbd.
       rajsag    06/22/23 - 35511111 - exacs:set hugepages in exacloud instead
       scoral    04/17/23 - Bug 35300995: Remove ADBD iptables deprecated code.
       aararora  03/13/23 - Call dbaascli command with dr vip and dr scan
                            values
       ndesanto  01/24/23 - Bug 35001886 - Fixed system model compare code to 
                            work correctly with X10M systems
       rajsag    01/15/23 - ol8 support
       joysjose  10/13/22 - Moving mInstallSuricataRPM definition from
                            cs_postginid.py to clucontrol.py to include
                            Suricata installation as part of elastic add node
                            operation in ADBD DomUs.
       naps      09/30/22 - Bug 34607608 - Collect ocde logs during failure.
       jfsaldan  09/30/22 - Bug 34527636 - Ebtables causes connectivity issues
                            to fetch remote fsencryption passphrase from domU
       naps      09/05/22 - Bug 34564820 - Populate grid.ini for zdlra before
                            crsreboot.
       aararora  07/01/22 - Modify scan name to fqdn.
       joalcala  06/23/22 - Bug34266093: ADBD StarterDB removal support changes.
       jfsaldan  06/07/22 - Enh 34105573 - Move ssh key and exacli password
                            from starterDB to PostgiNid in CS
       dekuckre  06/14/22 - 34267393: Update grid.ini in ZDLRA env.
       jfsaldan  04/06/22 - Bug 33131402 - Adding OEDA support for encryption
                            in KVM
       joysjose  21/03/22 - Bug 33443806: Create service support for 
                            Suricata RPM in ADBD domUs.
       jlombera  03/08/22 - Bug 33891346: configure bondmonitor at CreateVM
                            instead of PostGINID
       dekuckre  02/02/22 - 33294041: Enforce permissions for cellkey.ora
       ajayasin  01/05/22 - ahf installation on domU during postginid step
       naps      10/29/21 - remove dependency with non-root user keys post
                            provisioning.
       joysjose  10/18/21 - Include maxDistanceUpdate function.
       scoral    10/11/21 - Bug 33265977: DomU filesystems API refactoring.
       ajayasin  08/30/21 - 33293192_payload_vmClusterOcid
       ajayasin  08/02/21 - ocid seeding in domu
       naps      07/24/21 - move diagnostic messages to trace file.
       dekuckre  07/08/21 - 33044799: Call mAtpConfig in ATP env
       dekuckre  06/15/21 - 32982101: Update nonroot password in ZDLRA env
       joalcala  04/20/21 - Bug32794273: Remove atp rpm from ECS/exacloud
       joalcala  03/05/21 - Bug32533418: Fix the Header
       joalcala  03/05/21 - Bug32533418: inject cprops json paylod before ocde-init
       naps      02/28/21 - Apply security fixes before dbaas rpm installation.
       naps      02/08/21 - Apply security fixes during createservice.
       jlombera  02/17/21 - Bug 32422373: adjust to new clubonding API
       joalcala  02/03/21 - Bug32459363: Remove ebtables and install
                            atp_namespace rpm before dbaastools install
       joalcala  02/03/21 - Bug32439802: install atp rpm if exacc
       jlombera  01/12/21 - Bug 32295581: use new clubonding API
       joalcala  01/05/21 - Bug32312482: adb_init rpm and script support
                            And removal of dbaastools_exa_atp rpm
       dekuckre  09/16/20 - Fix 31881449
       saromer   09/10/19 - 30288233: port nosql provisioning from clucontrol
       dekuckre  06/19/19 - 29928603: Sync-up legacy and stepwise create service
       dekuckre  06/17/19 - 29859854: Call mStoreDomUInterconnectIps as part of
                            create service
       srtata    05/05/19 - bug 29739666: fix import from clucontrol
       gshiva    04/23/19 - Integrated undo step.
       srtata    03/05/19 - Creation
"""

from datetime import datetime
import time
import os
import operator
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogTrace, gLogMgrDirectory
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.cludbaas import executeOCDEInitOnDomUs
from exabox.tools.ebNoSql.ebNoSqlInstaller import ebNoSqlInstaller
from exabox.ovm.kvmdiskmgr import exaBoxKvmDiskMgr
import exabox.ovm.clubonding as clubonding
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.healthcheck.cluexachk import ebCluExachk
from exabox.ovm.atp import (AtpAddRoutes2DomU, ebCluATPConfig,
        AtpSetupSecondListener, AtpAddiptables2Dom0, ebATPTest, AtpCreateAtpIni,
        AtpAddScanname2EtcHosts, AtpSetupNamespace, AtpSetupASMListener)
from exabox.ovm.cluexaccatp import ebExaCCAtpListener
from exabox.ovm.clumisc import ebCluPreChecks, ebCopyDBCSAgentpfxFile
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.utils.common import mCompareModel
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check, node_exec_cmd_check, node_read_text_file, node_write_text_file
from exabox.ovm.cludomufilesystems import expand_domu_filesystem, expand_domu_vg
from exabox.ovm.cluencryption import resizeEncryptedVolume, isEncryptionRequested
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.ovm.cluencryption import exacc_fsencryption_requested, mSetLuksPassphraseOnDom0Exacc
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.ovm.adbs_elastic_service import mCreateADBSSiteGroupConfig

from exabox.ovm.cludbaas import mUpdateListenerPort
from exabox.ovm.configmgmt import ebConfigCollector

# This class implements doExecute and undoExecute functions
# for the ESTP_POSTGI_NID step of create service
class csPostGINID(CSBase):
    def __init__(self):
        self.step = 'ESTP_POSTGI_NID'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        ebLogInfo('csPostGINID: Entering doExecute')
        _reboot_vms = False
        ebox = aExaBoxCluCtrlObj
        ebox.mUpdateStatus('createservice step '+self.step)
        _clu_utils = ebCluUtils(ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "Post GI NID in progress", 'ESTP_POSTGI_NID')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Post GI NID", "In Progress", _stepSpecificDetails)

        # We now expand the filesystem to 5G before moving ahead with POSTGNID_STEP to address Bug 37712234
        # Resize Domu filesystems
        _step_time = time.time()
        _utils = ebox.mGetExascaleUtils()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Resize FS')
        expand_domu_filesystem(ebox, run_in_parallel=True, perform_dom0_resize=not _utils.mIsEDVImageSupported(aOptions))

        # Depending on which volumes are encrypted during Create Service, Exacloud may need
        # to perform resizing for LUKS Devices in here. Since /u02 is created from the beginning
        # with its final size we don't need to check if it is encrypted to resize/enlarge it in here.
        # Expand Luks Volume and filesystem in case /u01 is encrypted
        if isEncryptionRequested(aOptions, 'domU') and not ebox.mIsOciEXACC() and not ebox.mIsKVM():
            for _, _domU in ebox.mReturnDom0DomUPair():
                resizeEncryptedVolume(_domU, "/u01")

        ebox.mLogStepElapsedTime(_step_time, 'Resize FS')

        if ebox.mCheckConfigOption("force_reboot_vms_during_postginid") == 'True':
            ebLogTrace(f'Force reboot of VMs during postginid step')
            _reboot_vms = True

        if ebox.IsZdlraProv():
            # Update non root password (es.properties) in ZDLRA env from wallet
            _pswd = ebox.mGetZDLRA().mGetWalletViewEntry('passwd')
            ebox.mUpdateOedaUserPswd(ebox.mGetOedaPath(), "non-root", _pswd)

        if not ebox.mIsExaScale():

            #Create a list of DomUs for the given cluster and store it in a json file
            #
            ebox.mSaveClusterDomUList()

            #
            # REQ 1 FOR NID (Create ASM Diskgroups)
            #
            ebox.mAcquireRemoteLock()

            # Do OEDA update, ASM is missing in oratab. Here we are adding the entry
            ebox.mAddOratabEntry()
            
            ebox.mReleaseRemoteLock()

            # Create ASM diskgroups.
            csu = csUtil()
            _csConstants = csu.mGetConstants(ebox, aOptions)
            csu.mExecuteOEDAStep(ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_CREATE_ASM)

            ebLogInfo("*** DBCS nid requirements ")
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='CRS/ASM OCDE INIT Prechecks')

            # BUG 27941250 Needed for creating acfs diskgroup as a part of ocde init
            ebox.mSaveCellInformation()

            _checkACFS = False
            if mCompareModel(ebox.mGetExadataDom0Model(), 'X7') >= 0:
                _checkACFS = True

            if _checkACFS:
                ebox.mCreateAcfsDirs()

            # Obtain DOM0-DOMU pairs, and all the DOMMU list
            _dpairs = ebox.mReturnDom0DomUPair()
            _domu_list = [ _domu for _ , _domu in _dpairs]

            # Verify Clusterware (CRS) and ASM DB instance is up,
            # as well if ACFS is up too
            ebox.mCheckCrsIsUp(_domu_list[0], _domu_list)
            ebox.mCheckAsmIsUp(_domu_list[0], _domu_list, aCheckACFS=_checkACFS)

            ebox.mLogStepElapsedTime(_step_time, 'CRS/ASM OCDE INIT Prechecks')

            # For ExaCC with FS Encryption enabled, we must inject the
            # u02 passphrase to allow the VMs to reboot during OEDA
            # APPLY_SECURITY_FIXES STEP
            if ebox.mIsKVM() and exacc_fsencryption_requested(aOptions):

                for _dom0, _domU in ebox.mReturnDom0DomUPair():
                    ebLogInfo(f"{_domU} -- Setting up u02 socket data "
                        f"before OEDA APPLY_SEC_FIXES")
                    mSetLuksPassphraseOnDom0Exacc(ebox, _dom0, _domU, aWait=False)

            csu.mExecuteOEDAStep(ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_APPLY_FIX)

            # ===============================================================
            # Bug32533418: Push cloud_properties json into the domU
            # ===============================================================
            # ocde -init will consume this file to create cprops.ini
            # ===============================================================
            # cprops.ini will contain entries for each 
            # platform or module: 
            # 
            # For example:
            # -Platforms:
            #   for ADBD = atp_enabled=True
            #   for ADBS = adb_s_enabled=True
            # - Modules:
            #   CNS = cns_db_system_shape=X6-2-quarter
            #   DIAG = diag_srvrs=em,logstash,oss,tfaweb,em_agent
            # ===============================================================
            # All consumers of cprops.ini should:
            # =========================================<F11>======================
            # 1. create your module/platform/service inside cprops folder
            #    inside cprops folder:
            #  Example module:
            #  /var/opt/oracle/perl_lib/DBAAS/cprops/atp.pm
            # ===============================================================
            # 2. Usage example inside perl modules/scripts:
            # ===============================================================
            # use DBAAS::cprops::atp;
            # my $atp = atp->new({log => $log});
            # my $is_atp = $atp->get_atp_enabled();
            # if($is_atp) { run_my_atp_code(); }
            # ===============================================================
            ebox.mPrepareCloudPropertiesPayload()
            ebox.mPushCloudPropertiesPayload()
            #It is possible to have a different NAT IP for fileserver in Each ExaCC VM.
            #Need to set correct cloud_properties params if fileserver IP is different.
            ebox.mModifyAndUploadCloudPropertiesExaCC()

        # Bug32439802/32459363:
        # atp_namespace rpm its required before installing dbaastools rpms
        #
        # Will install ATP Namespace rpm,
        # if enable_namespace is True in exabox.conf
        if ebox.mIsExabm() and ebox.isATP():
            _majorityVersion = ebox.mGetMajorityHostVersion(ExaKmsHostType.DOMU)
            if _majorityVersion in ["OL7", "OL8"]:
                _atp_config = ebox.mCheckConfigOption('atp')
                if _atp_config:
                    if 'enable_namespace' in _atp_config and _atp_config['enable_namespace'] == 'True':
                        _step_time = time.time()
                        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Installing ATP Namespace rpm')
                        ebox.mSetupNamespace()
                        _step_time = time.time()
                        ebox.mUpdateRpm('atp-namespace.x86_64.rpm')
                        ebox.mLogStepElapsedTime(_step_time, 'Installing ATP Namespace rpm')

        # run the installation of dbaastools_exa_main.rpm and rpm updates
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='RPM install script')
        _rc, _cmd = ebox.mRunScript(aType='*', aWhen='post.gi_rpm', aStatusAbort=True)
        if _rc:
            ebLogError('*** Error ('+str(_rc)+') catched during scripts execution for cmd: '+_cmd)
            raise ExacloudRuntimeError(0x0116, 0xA, 'Step: RPM configuration error')

        ebox.mLogStepElapsedTime(_step_time, 'RPM install script')

        # Set the DR Scan and VIP configuration if present in payload
        if not ebox.isATP() and ebox.mIsDRNetPresent() and ebox.mIsOciEXACC():
            self.mSetDRScanVip(ebox)

        # Install VmexacsRpm
        ebox.mCopyVmexacsRpm()

        if not ebox.mIsExaScale():

           # Verify Clusterware (CRS) and ASM DB instance is up,
            # as well if ACFS is up too
            ebox.mCheckCrsIsUp(_domu_list[0], _domu_list)
            ebox.mCheckAsmIsUp(_domu_list[0], _domu_list, aCheckACFS=_checkACFS)

            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='OCDE NID configuration script')
            if not ebox.IsZdlraProv():
                _tcp_ssl_port = None
                if aOptions and aOptions.jsonconf and 'customer_network' in aOptions.jsonconf and\
                    'scan' in aOptions.jsonconf['customer_network'] and\
                        'tcp_ssl_port' in aOptions.jsonconf['customer_network']['scan']:
                            _tcp_ssl_port = aOptions.jsonconf['customer_network']['scan']['tcp_ssl_port']
                            if _tcp_ssl_port:
                                _tcp_ssl_port = str(_tcp_ssl_port)
                                _tcp_ssl_port = _tcp_ssl_port.strip()

                # First, run OCDE on 1st node, then in parallel on the rest of
                # nodes
                _domU_list = [_domU for _, _domU in ebox.mReturnDom0DomUPair()]
                ebLogInfo(f"Running OCDE Init on first node: {_domU_list[0]}")
                _is_atp = ebox.isATP()
                _rc = executeOCDEInitOnDomUs([_domU_list[0]], aParallel=False, aTcpSslPort=_tcp_ssl_port, aIsAtp=_is_atp)

                if _rc:
                    ebLogError(f'*** Error ({_rc}) caught during OCDE init '
                        f'execution in {_domU_list[0]}')
                    ebox.mCopyOCDELogFile()
                    raise ExacloudRuntimeError(0x0116, 0xA,
                        'OCDE Step: NID configuration error',
                        aStackTrace=True, aStep=self.step, aDo=True)

                if len(_domU_list) > 1:
                    ebLogInfo(f"Running OCDE Init on the rest of nodes: "
                        f"{_domU_list[1:]}")
                    _rc = executeOCDEInitOnDomUs(_domU_list[1:], aParallel=True, aTcpSslPort=_tcp_ssl_port, aIsAtp=_is_atp)
                    if _rc:
                        ebLogError(f'*** Error ({_rc}) caught during OCDE init '
                                f'execution in {_domU_list[1:]}')
                        ebox.mCopyOCDELogFile()
                        raise ExacloudRuntimeError(0x0116, 0xA,
                            'OCDE Step: NID configuration error',
                            aStackTrace=True, aStep=self.step, aDo=True)

            ebox.mLogStepElapsedTime(_step_time, 'OCDE NID configuration script')

            #Bug 33553474: Listener port need to be reconfigured to the GRID.INI
            if not ebox.isATP():
                mUpdateListenerPort(ebox, _domu_list)

            _step_time = time.time()

            # =============================================================================== 
            # Execute dbaasapi to create cloud properties file (cprops.ini)
            # =============================================================================== 
            # NOTE: cprops.ini (cloud properties file) can't be created before OCDE INIT 
            #       for the simple reason that dbaasapi
            #       perl modules are part of dbaastools_exa rpm
            # =============================================================================== 
            # IMPORTANT NOTE FOR ADB EXACC:
            # =============================================================================== 
            # For ADB, this step injects the image server IP and forward proxy info
            # So after this point they should be accessible from DOMU
            # =============================================================================== 
            ebLogInfo("***  DBAAS API Params setup ****")
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='DBAASAPI Cloud Properties script')
            ebox.mExecuteDbaaSApi()
            if ebox.mIsOciEXACC() and ebox.mIsFedramp():
                ebox.mEnsureFedRampCpropsIni(
                        ebox.mReturnDom0DomUPair(), aOptions)
            ebox.mLogStepElapsedTime(_step_time, 'DBAASAPI Cloud Properties script')

        # Bug32312482: ADB configuration.
        # Install ADB init RPM and run adb_init script 
        if ebox.isATP():
            ebLogInfo("*** Installing ADB Init rpm ***")
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='ADB_INIT RPM install')
            ebox.mUpdateRpm('adb_init.x86_64.rpm', aForce=True)
            ebox.mLogStepElapsedTime(_step_time, 'ADB_INIT RPM install')

            ebLogInfo("*** Running adb_init configuration script ***")
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='ADB_INIT configuration script')
            _rc, _cmd = ebox.mRunScript(aType='*', aWhen='post.gi_adb_init', aStatusAbort=True, aParallel=False)
            if _rc:
                ebLogError('*** Error ('+str(_rc)+') catched during scripts execution for cmd: '+_cmd)
                raise ExacloudRuntimeError(0x0116, 0xA, 'ADB Init Step: ADB Init script configuration error',
                                           aStackTrace=True, aStep=self.step, aDo=True)
            ebox.mLogStepElapsedTime(_step_time, 'ADB_INIT configuration script')
            _step_time = time.time()

        # install nosql
        if ebox.mCheckConfigOption('install_nosql', 'True'):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='nosql install')
            _domUs = list(map(operator.itemgetter(1),ebox.mReturnDom0DomUPair()))
            _rackSize = ebox.mGetRackSize()
            _nosql = ebNoSqlInstaller(_domUs,_rackSize)
            _nosql.mRunInstall()
            ebox.mLogStepElapsedTime(_step_time, 'nosql install')

        # Adding Site Group configuration file to the domU (only if working with ABDS)
        # This can only be done if this is an ADBS flow AND if this is a multicloud instance, 
        # which is already checked by ECRA before sending the payload. If any of these conditions
        # is not met, the payload will NOT contain the 'location' block, therefore we can assume 
        # that, if we can find said attribute in the payload, this is a multicloud instance:
        if ebox.mIsAdbs():
            mCreateADBSSiteGroupConfig(ebox)

        # At self point opc user is available & hence create the priv/pub keys for opc user & inject the pub key
        # into the /home/opc/.ssh/authorized_keys and save the keys in the exacloud keys dir.
        ebLogInfo("*** Manage OPC user keys ****")
        ebox.mAddUserPubKey('opc')
        ebox.mCopySAPfile()

        #
        # POSTGI - Disable TFA if grid_tfa_enabled is not True( Dev Env )
        if not ebox.mCheckConfigOption('grid_tfa_enabled','True') and ebox.isATP() == False:
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Disabing TFA')
            ebox.mDisableTFA()
            ebox.mLogStepElapsedTime(_step_time, 'Disabling TFA')

        #Run the mAtpConfig after create the OPC user
        if ebox.isATP():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='ATPConfig')
            ebox.mAtpConfig()
            ebox.mLogStepElapsedTime(_step_time, 'ATPConfig')

        # 
        # ER 31923304: Configure temporary directories exclusions
        # 
        ebox.mAddOracleFolderTmpConf()

        if not ebox.mIsExaScale():
            #
            # Apply Extra Srvcrl Config
            #
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Apply Extra Srvcrl Config')
            ebox.mApplyExtraSrvctlConfig()
            ebox.mLogStepElapsedTime(_step_time, 'Apply Extra Srvcrl Config')

        #
        # ER 30138555: MTLS Authentication For ExaCC DBCS Agent
        # Prepare domUs for MTLS communication
        #
        if ebox.mIsOciEXACC():
            # Enh 35823972: COPY DOM-U CERTIFICATE INTO DOM-U DURING CS
            if ebox.mIsFedramp():
                ebox.mSetupDomUsForSecurePatchServerCommunication()
            else:
                ebox.mSetupDomUsForSecureDBCSCommunication()
            _obj = ebCopyDBCSAgentpfxFile(ebox)
            _obj.mCopyDbcsAgentpfxFiletoDomUsForFedramp()
            # ER 32161016: Copy DBCS/CPS agent wallets
            ebox.mAddAgentWallet()

        #
        # ER 27371691: Install DBCS agent rpm
        #
        _step_time = time.time()
        # skip the dbcs-agent installation for ADB
        if not ebox.isATP():
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Installing DBCS Agent rpm')
            _majorityVersion = ebox.mGetMajorityHostVersion(ExaKmsHostType.DOMU)
            if _majorityVersion in ["OL7", "OL8"]:
                if ebox.mIsExabm() or ebox.mCheckConfigOption("force_install_dbcs_agent", "exacs"):
                    ebox.mUpdateRpm('dbcs-agent.OL7.x86_64.rpm')
                else:
                    if ebox.mIsOciEXACC() or ebox.mCheckConfigOption("force_install_dbcs_agent", "exacc"):
                        ebox.mUpdateRpm('dbcs-agent-exacc.OL7.x86_64.rpm')
                    else:
                        ebLogInfo('Skipping OL7 dbcs agent install')
            else:
                if ebox.mIsExabm() or ebox.mCheckConfigOption("force_install_dbcs_agent", "exacs"):
                    ebox.mUpdateRpm('dbcs-agent.OL6.x86_64.rpm')
                else:
                    if ebox.mIsOciEXACC() or ebox.mCheckConfigOption("force_install_dbcs_agent", "exacc"):
                        ebox.mUpdateRpm('dbcs-agent-exacc.OL6.x86_64.rpm')
                    else:
                        ebLogInfo('Skipping OL6 dbcs agent install')
            ebox.mLogStepElapsedTime(_step_time, 'Installing DBCS Agent rpm')
        else:
            ebLogInfo('Skipping dbcs-agent installation for ADB')

        # DBCS No-Auth mode only in DEV/QA
        if not ebox.mEnvTarget() and ebox.mCheckConfigOption('force_dbcsagent_auth', 'True'):
            ebox.mEnableNoAuthDBCS()

        # OraNet parameters update
        _localPath = 'scripts/network/change_ora_net_params.sh'
        _remoteDir = '/opt/exacloud/bin/'
        _dpairs = ebox.mReturnDom0DomUPair()

        for _dom0, _domU in _dpairs:
            ebLogInfo(f"Updating OraNet parameters from host: {_domU}")
            _node = exaBoxNode(get_gcontext())
            # Ensure host is connectable first
            if not _node.mIsConnectable(aHost=_domU):
                ebLogError(f"Node {_domU} is not connectable.")
                continue
            with connect_to_host(_domU, get_gcontext()) as _node:
                # Ensure that remote directory exists
                if not _node.mFileExists(_remoteDir):
                    _cmd = f'mkdir -p {_remoteDir}'
                    _stdin, _stdout, _stderr = _node.mExecuteCmd(_cmd)
                    ebLogInfo(f"Created directory {_remoteDir} since it didn't exist")
                # Copy local file to remote path
                _remotePath = '/opt/exacloud/bin/change_ora_net_params.sh'
                ebLogInfo(f"Copying {_localPath} to remote location: {_remotePath}")
                _node.mCopyFile(_localPath, _remotePath)

                # Execute script
                ebLogInfo(f"Executing remote OraNet script at {_remotePath}")
                _cmd = f"/bin/sh {_remotePath}"
                _stdin, _stdout, _stderr = _node.mExecuteCmd(_cmd)
                _rc = _node.mGetCmdExitStatus()
                # If no errors are found, don't keep iterating
                if _rc != 0:
                    _msg = f"Executing {_remotePath} ended with return code: {_rc}. Error: {_stderr}"
                    ebLogError(_msg)
                    raise ExacloudRuntimeError(0x0116, 0xA, _msg, aStackTrace=True, aStep=self.step)
                ebLogInfo("Successfully updated OraNet params.")
                break

        if ebox.mIsExacm() is True:
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='EXACM copy ssh key patch script')
            ebox.mCopyExacmPatchKeyScript()
            ebox.mLogStepElapsedTime(_step_time, 'EXACM copy ssh key patch script')

        if ebox.isATP():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Set CSS Misscount in ATP')
            _miscnt = get_gcontext().mGetConfigOptions().get("css_misscount", "")
            if _miscnt:
                ebox.mDomUCSSMisscountHandler(aMode = False, aMisscount = _miscnt)
            else:
                ebLogInfo("*** Setting CSS Misscount as value set in exabox.conf")
            ebox.mLogStepElapsedTime(_step_time, 'Set CSS Misscount in ATP')


        #Set OraInventory Permissions to drwxrwx---
        ebox.mSetOraInventoryPermissions()

        # Since RPMs are installed, skip everythin
        if not ebox.mIsExaScale():

            #Install AHF setup on domU for non-ATP services
            if not ebox.isATP():
               csu.mInstallAhfonDomU(ebox, self.step, steplist)

            #
            # run Exachk
            # 
            _enable_exachk = ebox.mCheckConfigOption('enable_exachk')
            if _enable_exachk:
                if 'post_create_vm' in _enable_exachk and _enable_exachk['post_create_vm'] == 'True':
                    ebox.mExecuteExachk()

        # Stores the interconnect IP's of the VM's in cluster_interconnect.dat
        ebox.mStoreDomUInterconnectIps()

        if not ebox.isATP():
            ebox.mRemoveDatabaseMachineXmlDomU()

        ebox.mCopyExaDataScript() # copy the exadata_updates script to DomUs

        # Sanitize DomU /etc/stsctl.conf for XEN envs.
        self.mSanitizeDomUSysctlConf(ebox)

        # Configure Hugepages
        if not ebox.isATP():
            _percentage = ebox.mCheckConfigOption('hugepages_percentage')
            if _percentage is None:
                _percentage = '50' # set hugepages to 50% of the total VM memory 
            ebox.mUpdateHugepagesForCluster(_percentage) 

        for _, _domU in ebox.mReturnDom0DomUPair():
            _rc, _str = ebox.mMakeFipsCompliant(aOptions, aHost=_domU)
            if _str == "reboot_host":
                _reboot_vms = True
                #reboot will happen at the end of this step!

        if ebox.IsZdlraProv():
            ebox.mGetZDLRA().mUpdateHugePages(aOptions)

        try:
            self.mSeedOCIDonDomU(ebox,aOptions)
        except Exception as e: 
            ebLogError(f"*** mSeedOCIDonDomU failed with Exception: {str(e)}")

        if ebox.mCheckConfigOption('ociexacc', 'True') and ebox.isATP():
            try:
                _dbpair = ebox.mReturnDom0DomUPair()
                _domUs_list = list(map(operator.itemgetter(1), _dbpair))
                ebox.mInstallSuricataRPM(_domUs_list,"domu")
            except Exception as e: 
                ebLogWarn(f"*** mInstallSuricataRPM failed with Exception: {str(e)}")

        # Reset SSH Cluster Keys
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Reset SSH Cluster knowhost entries')
        ebox.mResetClusterSSHKeys(aOptions)
        ebox.mLogStepElapsedTime(_step_time, 'Reset SSH Cluster knowhost entries')

        # Generate switch keys
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Generate Switch Keys')
        ebox.mHandlerGenerateSwitchesKeys()
        ebox.mLogStepElapsedTime(_step_time, 'Generate Switch Keys')

        # Copy additional files
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Copy additional files')

        # Bug32540420: For ADBD, we use rpmupd logic to update dbaastools_exa rpm
        # during create service.
        # We shouldnt update any rpm after CreateService has finished (for ADB-D)
        if not ebox.isATP():
            # ER 27503421
            if ebox.mIsOciEXACC():
                ebox.mCopyVmexacsRpm()
            # Bug 27216120
            # Enh 38025087 
            _csu = csUtil()
            _dbaastools_rpm = _csu.mGetDbaastoolRpmName(aOptions)                   
            ebox.mUpdateRpm(_dbaastools_rpm)

        # ER 25900538 and 27555477
        if ebox.mIsExabm() or ebox.mIsOciEXACC():
            ebox.mCopyCreateVIP()
            ebox.mCopyOneoffZipToDomus()
        ebox.mLogStepElapsedTime(_step_time, 'Copy additional files')

        # Add customer SSH Key in DOMUs
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Patch VM SSH Keys')
        ebox.mPatchVMSSHKey(aOptions)
        ebox.mLogStepElapsedTime(_step_time, 'Patch VM SSH Keys')

        # SSH Key patching (default root/opc/oracle)
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Create SSH Key patching')
        ebox.mPostDBSSHKeyPatching(aOptions, 'addkey', ['root','oracle','opc'])
        ebox.mLogStepElapsedTime(_step_time, 'Create SSH Key patching')

        #
        # Alter cloud_user's password in the cells.
        #
        if ebox.mCheckConfigOption('exacli_use_db_pwd', 'True'):

            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Alter user-password')
            try:
                ebox.mUpdateCloudUser(aOptions)
            except Exception as e:
                ebLogError("Error while updating cloud user password")
                ebLogError(e)
                # We will not raise any errors regarding the ExaCLI password if we're in an ExaCC environment
                if ebox.mIsOciEXACC():
                    ebLogInfo("Not stopping step flow since we're in an ExaCC environment.")
                # Else, if the corresponding flag is enabled, we will raise runtime error when invalid ExaCLI pwd is passed
                elif get_gcontext().mGetConfigOptions().get("enforce_exacli_password_update"):
                    raise ExacloudRuntimeError(0x0116, 0xA, 'Failed to update cloud user password', aStackTrace=True, aStep=self.step) from e
            ebox.mLogStepElapsedTime(_step_time, 'Alter user-password')

        #
        # Create ADBS cloud_user
        #
        ebox.mCreateAdbsUser(aOptions)

        # Enable Storage Cell remote password change for exacli users
        ebox.mEnableRemotePwdChange(aOptions)

        if ebox.IsZdlraProv():
            ebox.mUpdateGridINI(_domu_list)

        if not ebox.mIsExaScale():
            #
            # perform CRS reboot
            #
            ebox.mExecuteCRSReboot()

        # ATP backup Listener
        if ebox.isATP():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Setup ATP Backup Listener')

            # Setup ATP Backup Listener
            # Below is the flow needed for EXABM - ATP
            if ebox.mIsExabm() and ebox.mCheckClusterNetworkType():

                for _dom0, _domU in ebox.mReturnDom0DomUPair():
                    ebLogInfo("*** ATP etc/hosts on %s ***" % _domU)
                    AtpAddScanname2EtcHosts(None, ebox.mGetATP(), _domU).mExecute()

                # Only need to be run on one domU
                ebLogInfo("*** ATP Listener on %s ***" % _domU)
                AtpSetupSecondListener(None, ebox.mGetATP(), ebox.mReturnDom0DomUPair(),
                        ebox.mGetMachines(), ebox.mGetNetworks(), None, ebox.mGetClusters,
                        aOptions).mExecute()
                AtpSetupASMListener(None, ebox, None).mExecute()

            # All the Above is for EXABM, below is EXACC-ATP hook (VGE:NEED TO BE EXTERNALIZED)
            if ebox.mIsOciEXACC():

                _node = exaBoxNode(get_gcontext())

                # First domU
                _all_domU = list(map(operator.itemgetter(1),ebox.mReturnDom0DomUPair()))
                _first_domU = _all_domU[0]
                _node.mConnect(aHost=_first_domU)
                _listener_info = ebExaCCAtpListener.sExtractInfoFromDomU(_node)

                if ebox.mIsDebug():
                    ebLogDebug("ExaCCAtp Listener Info: {}".format(_listener_info))

                if not _listener_info:
                    ebLogWarn("Error on obtaining ATP Listener info, skip setup")
                    _node.mDisconnect()

                else:
                    # VGE: Need to be refactored
                    _root_commands, _grid_commands, _final_grid_commands, _final_root_commands = ebExaCCAtpListener.sGenerateListenerCommands(**_listener_info)
                    if ebox.mIsDebug():
                        ebLogDebug("ExaCCAtp Commands: root({}), grid({}), final_grid({}), "
                                "final_root_commands({})".format(_root_commands,
                                    _grid_commands, _final_grid_commands,
                                    _final_root_commands))

                    for _cmd in _root_commands:
                        _node.mExecuteCmdLog(_cmd)

                    # Reconnect as Grid
                    _node.mDisconnect()
                    _node = exaBoxNode(get_gcontext())
                    _node.mSetUser('grid')
                    _node.mConnect(aHost=_first_domU)
                    for _cmd in _grid_commands:
                        _node.mExecuteCmdLog(_cmd)

                    # Register ASM Backup listener on all DomU,
                    # reuse connected first domU then for loop on other
                    ebExaCCAtpListener.sRegisterListenerOnBKUPOnly(_node,
                                        _listener_info['aListenerPort'])
                    _node.mDisconnect()

                    for _other_domU in _all_domU[1:]:
                        _node = exaBoxNode(get_gcontext())
                        _node.mSetUser('grid')
                        _node.mConnect(aHost=_other_domU)
                        ebExaCCAtpListener.sRegisterListenerOnBKUPOnly(_node,
                                        _listener_info['aListenerPort'])
                        _node.mDisconnect()

                    # Now execute final grid commands on first domU
                    _node = exaBoxNode(get_gcontext())
                    _node.mSetUser('grid')
                    _node.mConnect(aHost=_first_domU)
                    for _cmd in _final_grid_commands:
                        _node.mExecuteCmdLog(_cmd)

                    # Then connect as root to bounce cluster
                    _node.mDisconnect()
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_first_domU)
                    for _cmd in _final_root_commands:
                        _node.mExecuteCmdLog(_cmd)
                    _node.mDisconnect()

                    # Wait for ACFS to be up
                    ebox.mCheckAsmIsUp(_first_domU, _all_domU, aCheckACFS=_checkACFS)

            ebox.mLogStepElapsedTime(_step_time, 'Setup ATP Backup Listener')

        #ATP will be detected from inside the function
        ebox.mATPUnlockListeners()

        # Disable TFA blackout after starter db deletion (end of pre-provisioning),
        # blackout is enabled right after TFA is installed
        ebox.mEnableTFABlackout(False, "Pre-Provision blackout", aOptions)

        # Workaround for incorrect permissions of cellkey.ora 
        # when asm scoped security is enabled (should be removed if fixed in OEDA)
        for _, _domu in ebox.mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domu)
            if _node.mFileExists('/etc/oracle/cell/network-config/cellkey.ora'):
                _node.mExecuteCmd("chmod 640 /etc/oracle/cell/network-config/cellkey.ora")
            _node.mDisconnect()

        #Drop pmemlogs for adbs env
        ebox.mDropPmemlogs(aOptions)

        if ebox.isATP():
            try:
                _dpairs = ebox.mReturnDom0DomUPair()
                ebAtpUtils.setScanFqdn(_dpairs)
            except Exception as ex:
                ebLogError(f"*** Could not modify scan name to fqdn. Error: {ex}")

        # Print the permissions of the dbnid directory
        try:
            for _, _domu in ebox.mReturnDom0DomUPair():
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domu)
                if _node.mFileExists('/var/opt/oracle/dbaas_acfs'):
                    _i, _o, _e = _node.mExecuteCmd("ls -ltr /var/opt/oracle/dbaas_acfs")
                    ebLogInfo(f"The output for ls -ltr /var/opt/oracle/dbaas_acfs is {_o.read()}")
                    break
                else:
                    ebLogInfo(f"The output for ls -ltr /var/opt/oracle/dbaas_acfs could not be obtained - the directory does not exist.")
                _node.mDisconnect()
        except Exception as ex:
            ebLogError(f"*** Could not get output for ls -ltr /var/opt/oracle/dbaas_acfs. Error: {ex}")

        if _reboot_vms is True:
            ebLogTrace(f'Rebooting cluster Vms')
            ebox.mParallelDomUShutdown(force_on_timeout=True)
            ebox.mParallelDomUStart()

        if ebox.mIsKVM() and ebox.mCheckConfigOption("domu_cluster_configuration_mgr") == 'True':
            ebLogInfo(f'Inside config collector ....')
            dom0_domu_pairs = ebox.mReturnDom0DomUPair()
            _cell_list = ebox.mReturnCellNodes()
            configmgmt = ebConfigCollector(dom0_domu_pairs, _cell_list, ebox)
            configmgmt.mCollectAllConfigs()

        # Remove DomU Access
        if aOptions and aOptions.jsonconf and \
           "delete_domu_keys" in aOptions.jsonconf and \
           aOptions.jsonconf['delete_domu_keys'].lower() == "true":
            ebox.mHandlerRemoveDomUsKeys()

        # Bug34266093: StarterDB removal changes for ADBD
        # This script will be executed inside the domU 
        # to perform tasks that were previously executed in starterDB flow.
        #
        # Important notes: 
        # This block of code should be always the last to be executed
        # in POSTGINID step of create service.
        if ebox.isATP() and not ebox.mCheckConfigOption("force_starter_db_install") == 'True':
            ebLogInfo("*** Running adb_endcreateservice script ***")
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='ADB End Create Service script')

            # Verify Clusterware (CRS) and ASM DB instance is up,
            # as well if ACFS is up too
            ebLogInfo("*** Check CRS/ACFS is up ***")
            ebox.mCheckCrsIsUp(_domu_list[0], _domu_list)
            ebox.mCheckAsmIsUp(_domu_list[0], _domu_list, aCheckACFS=_checkACFS)
            ebLogInfo("*** CRS/ACFS is up ***")
            _rc, _cmd = ebox.mRunScript(aType='*', aWhen='post.gi_adbd_endcs', aStatusAbort=True, aParallel=False)
            if _rc:
                ebLogError('*** Error ('+str(_rc)+') catched during scripts execution for cmd: '+_cmd)
                raise ExacloudRuntimeError(0x0116, 0xA, 'ADB End Create Service Step script error',
                                           aStackTrace=True, aStep=self.step, aDo=True)
            ebox.mLogStepElapsedTime(_step_time, 'ADB End Create Service script')
        # End of ADBD CreateService End script block

        # Bug 32533418: Remove cloud_properties json from the domUs
        # Bug 38332780: Remove the file after DBCS Agent is installed and ADBD processes are finsihed.  
        ebox.mRemoveCloudPropertiesPayload()

        #Update System Vault Access to the new compute
        if ebox.mGetCmd() == "createservice" and not ebox.isBaseDB() and not ebox.mIsExaScale():
            _utils = ebox.mGetExascaleUtils()
            _utils.mUpdateSystemVaultAccess(aOptions)

        #Add voting file locations in the response
        _data = {}
        try:
            """
            The voting disk information is shared and consistent across all healthy 
            nodes in the cluster. Running the command on any single node should 
            give complete, accurate list of all voting disks for the whole cluster.
            """
            _first_domU = _domu_list[0]
            _data["voting_files"] = ""

            with connect_to_host(_first_domU, get_gcontext(), username="root") as _node:
                _cell_list = ebox.mReturnCellNodes()
                configmgmt = ebConfigCollector(_dpairs, _cell_list, ebox)
                _data["voting_files"] = configmgmt.mGetVotingDiskConfig(_node, _first_domU)    
        except Exception as e:
            ebLogInfo(f"There was an error in adding voting files during postginid step: {e}")
            
        ebLogInfo('*** Exacloud Operation Successful : POST GI Install')
        ebLogInfo('csPostGINID: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "Post GI NID Completed", 'ESTP_POSTGI_NID')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Post GI NID", "Done", _stepSpecificDetails, _data)

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, _steplist):
        ebLogInfo('*** csPostGINid: Entering undoExecute')
        _ebox = aExaBoxCluCtrlObj
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, aOptions)
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'ONGOING', "Undo Post GI NID in progress", 'ESTP_POSTGI_NID')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Undo Post GI NID", "In Progress", _stepSpecificDetails)

        if _ebox.IsZdlraProv():   
            # Update non root password (es.properties) in ZDLRA env from wallet  
            _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd')   
            _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd) 

        if _ebox.mIsExabm() and _ebox.mGetCmd() in ['vmgi_delete', 'gi_delete', 'deleteservice']:
            _csu.mDeleteVM(aExaBoxCluCtrlObj, self.step, _steplist)
            ebLogInfo('*** csPostGINid: Completed undoExecute Successfully')
            return

        #
        # OSTP_POSTGI_NID step
        #

        # Acquire Remote Lock in shared mode-environment
        _ebox.mAcquireRemoteLock()

        # Remove ASM diskgroups, lock is already taken, so dom0Lock  is sent as False
        _csu.mExecuteOEDAStep(_ebox, self.step, _steplist, aOedaStep=_csConstants.OSTP_CREATE_ASM, undo=True, dom0Lock=False)

        _domU_list = [ _domU for _dom0, _domU in _ebox.mReturnDom0DomUPair()]

        # Uninstall dbcs agent rpm.
        # skip the dbcs-agent uninstall for ADB
        if not _ebox.isATP():
            try:
                _step_time = time.time()
                _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Uninstalling DBCS Agent rpm')
                _domUsPingable = True
                _majorityVersion = _ebox.mGetMajorityHostVersion(ExaKmsHostType.DOMU)
                for _domU in _domU_list:
                    _domUsPingable = _domUsPingable and _ebox.mPingHost(_domU)
                if (_majorityVersion in ["OL7", "OL8"]) and _domUsPingable:
                    if _ebox.mIsExabm():
                        _ebox.mUpdateRpm('dbcs-agent.OL7.x86_64.rpm', aUndo = True)
                    else:
                        if _ebox.mIsOciEXACC():
                            _ebox.mUpdateRpm('dbcs-agent-exacc.OL7.x86_64.rpm', aUndo = True)
                elif _domUsPingable:
                    if _ebox.mIsExabm():
                        _ebox.mUpdateRpm('dbcs-agent.OL6.x86_64.rpm', aUndo = True)
                    else:
                        if _ebox.mIsOciEXACC():
                            _ebox.mUpdateRpm('dbcs-agent-exacc.OL6.x86_64.rpm', aUndo = True)

                if not _domUsPingable:
                    ebLogWarn("Skipping Uninstalling DBCS Agent rpm as VMs are not running")

                _ebox.mLogStepElapsedTime(_step_time, 'Uninstalling DBCS Agent rpm')
            except Exception as ex:
                ebLogWarn(f'There was an exception during dbcs-agent uninstall. Exception: {ex}.')
        else:
            ebLogInfo('Skipping dbcs-agent uninstall for ADB')

        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='OCDE NID configuration script')
        try:
            _domU = _domU_list[0]
            _node = exaBoxNode(get_gcontext())
            if _node.mIsConnectable(aHost=_domU):
                _path, _sid = _ebox.mGetGridHome(_domU)
                _user = 'grid'
                _node.mConnect(aHost=_domU)
                _cmd_pfx = 'ORACLE_HOME=%s;export ORACLE_HOME;ORACLE_SID=%s; export ORACLE_SID;PATH=$PATH:$ORACLE_HOME/bin;export PATH;' % (_path,_sid)
                _cmd_str = _cmd_pfx + '$ORACLE_HOME/bin/srvctl status asm -proxy | grep running | wc -l'
                _, _o, _e = _node.mExecuteCmd("/bin/su - " + _user + " -c \'" + _cmd_str + "\'")
                if _o is not None:
                    _out = _o.readlines()
                    if _out:
                        _ret = _out[0].strip()
                        if _ret == '1':
                            _cmd_str = _cmd_pfx + '$ORACLE_HOME/bin/srvctl stop asm -proxy -force'
                            _node.mExecuteCmd("/bin/su - " + _user + " -c \'" + _cmd_str + "\'")

                            _cmd_str = _cmd_pfx + '$ORACLE_HOME/bin/srvctl disable asm -proxy'
                            _node.mExecuteCmd("/bin/su - " + _user + " -c \'" + _cmd_str + "\'")
 
                _node.mDisconnect()
        except Exception as e:
            ebLogTrace("Connection to domU %s failed. Exception reason: %s"%(_domU, str(e)))

        _ebox.mReleaseRemoteLock()

        _ebox.mLogStepElapsedTime(_step_time, 'OCDE NID configuration script')
        ebLogInfo('*** csPostGINid: Completed undoExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'DONE', "Undo Post GI NID Completed", 'ESTP_POSTGI_NID')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Undo Post GI NID", "Done", _stepSpecificDetails)

