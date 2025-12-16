#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/cs_exascale_complete.py /main/25 2025/12/01 14:45:28 remamid Exp $
#
# cs_exascale_complete.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_exascale_complete.py - Complete step on XS Provisioning
# 
#   FUNCTION:
#      Implements the Exascale Complete step for XS create service execution 
#
#    NOTES
#      Invoked from cs_driver.py
#
#    EXTERNAL INTERFACES:
#      csExaScaleComplete     ESTP_EXASCALE_COMPLETE
#
#    INTERNAL CLASSES:
#
#    MODIFIED   (MM/DD/YY)
#.   remamid     11/10/25 - exacc natfilesystem ip different for vms in the
#.                          cluster bug 38581933
#.   siyarlag    10/30/25 - 38500170: create eswallet for oracle/db user
#.   bhpati      10/20/25 - Bug 38490905 - OCI: ExaDB-D on exascale
#.                          provisioning fails if ICMP ingress is not open on
#.                          client network
#.   akkar       30/06/25 - Bug 38025087: dbaastool rpm for multi cloud
#    scoral      08/20/25 - Bug 38338038 - EXASCALE: EXACLOUD PROVISIONING
#                           FAILURE OCDE STEP: NID CONFIGURATION ERROR DUE
#                           TO INSUFFICIENT /VAR SPACE
#    aliarias    08/20/25 - Enh 38332780 - EXACC/EXACS DELINKING SYSLENS FROM
#                           DBAASTOOLS (EXACLOUD MOVE EXECUTION OF
#                           REMOVECLOUDPROPERTIESPAYLOAD AT THE END POSTGINID
#                           STEP)
#    pbellary    08/15/25 - Enh 38318848 - CREATE ASM CLUSTERS TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT
#    abflores    06/11/25 - Bug 37508725 - IMPROVE PORT SCAN
#    pbellary    06/06/25 - Enh 38035467 - EXASCALE: EXACLOUD TO PROVIDE ACFS FILE SYSTEM SIZES IN SYNCH CALL
#    vikasras    03/18/25 - Bug 37712234 - EXACS: EXACLOUD PROVISIONING FAILURE OCDE STEP: NID CONFIGURATION ERROR 
#                                          DUE TO INSUFFICIENT /VAR SPACE
#    pbellary    26/19/24 - Bug 37220441 - EXASCALE: SKIP UPDATING CLOUD USER DURING ADD NODE
#    pbelalry    08/28/24 - Bug 37000491 - EXASCALE: CREATE EXASCALE CLUSTER FAILS AFTER REBOOTING DOMU
#    pbellary    08/21/24 - Bug 36974106 - ENHANCE CS FLOW FOR EXASCALE CLUSTER TO ADD REQUIRED FIELDS THE GRID.INI FILE. 
#    pbellary    08/12/24 - ENH 36945014 - CREATE AND BRING UP ACFS / MOUNT THE VOLUMES TOO ON THE DB VAULTS
#    pbellary    09/04/24 - Enh 36976333 - EXASCALE:ADD NODE CHANGES FOR EXASCALE CLUSTERS 
#    pbellary    06/21/24 - ENH 36690846 - IMPLEMENT POST-VM STEPS FOR EXASCALE SERVICE 
#    pbellary    06/14/24 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
#    pbellary    06/06/24 - Creation
#

import time
import operator
from exabox.core.Node import exaBoxNode
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.core.Context import get_gcontext
from exabox.ovm.cludbaas import (updateGridINI, mUpdateListenerPort)
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.ovm.cluexaccatp import ebExaCCAtpListener
from exabox.ovm.csstep.cs_constants import csXSConstants, csXSEighthConstants
from exabox.core.Error import ebError, ExacloudRuntimeError, gExascaleError
from exabox.tools.ebNoSql.ebNoSqlInstaller import ebNoSqlInstaller
from exabox.ovm.csstep.exascale.exascaleutils import ebExascaleUtils
from exabox.ovm.clumisc import ebCluPreChecks, ebCopyDBCSAgentpfxFile
from exabox.ovm.cludomufilesystems import expand_domu_filesystem, expand_domu_vg
from exabox.ovm.cluencryption import resizeEncryptedVolume, isEncryptionRequested
from exabox.ovm.atp import (AtpAddRoutes2DomU, ebCluATPConfig,
        AtpSetupSecondListener, AtpAddiptables2Dom0, ebATPTest, AtpCreateAtpIni,
        AtpAddScanname2EtcHosts, AtpSetupNamespace, AtpSetupASMListener)
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.ovm.cluencryption import exacc_fsencryption_requested, mSetLuksPassphraseOnDom0Exacc

# This class implements doExecute and undoExecute functions
# for the ESTP_EXASCALE_COMPLETE step of create service
# This class primarily invokes OEDA do/undo exascale complete step
class csExaScaleComplete(CSBase):
    def __init__(self):
        self.step = 'ESTP_EXASCALE_COMPLETE'

    def doExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csExaScaleComplete: Entering doExecute')
        _ebox = aCluCtrlObj
        _steplist = aStepList
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, False)
        # Obtain DOM0-DOMU pairs, and all the DOMMU list
        _dpairs = _ebox.mReturnDom0DomUPair()
        _domu_list = [ _domu for _ , _domu in _dpairs]

        # For ExaCC with FS Encryption enabled, we must inject the
        # u02 passphrase to allow the VMs to reboot during OEDA
        # APPLY_SECURITY_FIXES STEP
        if _ebox.mIsKVM() and exacc_fsencryption_requested(aOptions):

            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                ebLogInfo(f"{_domU} -- Setting up u02 socket data "
                    f"before OEDA APPLY_SEC_FIXES")
                mSetLuksPassphraseOnDom0Exacc(_ebox, _dom0, _domU, aWait=False)

        # 38500170: create eswallet for oracle/db user
        try:
            _utils = ebExascaleUtils(_ebox)
            _utils.mCreateOracleWallet(aOptions)
        except Exception as ex:
            ebLogError(f"*** Could not create oracle eswallet. Error: {ex}")

        # Resize Domu filesystems
        _step_time = time.time()
        _utils = _ebox.mGetExascaleUtils()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Resize FS')
        expand_domu_filesystem(_ebox, run_in_parallel=True, perform_dom0_resize=not _utils.mIsEDVImageSupported(aOptions))

        # Depending on which volumes are encrypted during Create Service, Exacloud may need
        # to perform resizing for LUKS Devices in here. Since /u02 is created from the beginning
        # with its final size we don't need to check if it is encrypted to resize/enlarge it in here.
        # Expand Luks Volume and filesystem in case /u01 is encrypted
        if isEncryptionRequested(aOptions, 'domU') and not _ebox.mIsOciEXACC() and not _ebox.mIsKVM():
            for _, _domU in _ebox.mReturnDom0DomUPair():
                resizeEncryptedVolume(_domU, "/u01")

        _ebox.mLogStepElapsedTime(_step_time, 'Resize FS')

        if _ebox.mGetCmd() == "createservice":
            _csu.mExecuteOEDAStep(_ebox, self.step, _steplist, aOedaStep=_csConstants.OSTP_APPLY_FIX)

            #create default acfs volume
            _utils.mCreateDefaultAcfs(aOptions)

        # Print the permissions of the dbnid directory
        try:
            for _, _domu in _ebox.mReturnDom0DomUPair():
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domu)
                if _node.mFileExists('/var/opt/oracle/dbaas_acfs'):
                    _node.mExecuteCmdLog("/bin/chown -fR oracle:oinstall /var/opt/oracle/dbaas_acfs")
                    _i, _o, _e = _node.mExecuteCmd("ls -ltr /var/opt/oracle/dbaas_acfs")
                    ebLogInfo(f"The output for ls -ltr /var/opt/oracle/dbaas_acfs is {_o.read()}")
                    break
                else:
                    ebLogInfo(f"The output for ls -ltr /var/opt/oracle/dbaas_acfs could not be obtained - the directory does not exist.")
                _node.mDisconnect()
        except Exception as ex:
            ebLogError(f"*** Could not get output for ls -ltr /var/opt/oracle/dbaas_acfs. Error: {ex}")

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
        if _ebox.mGetDbaasApiPayload():
            _ebox.mPrepareCloudPropertiesPayload()
            _ebox.mPushCloudPropertiesPayload()
            #It is possible to have a different NAT IP for fileserver in Each ExaCC VM.
            #Need to set correct cloud_properties params if fileserver IP is different.
            _ebox.mModifyAndUploadCloudPropertiesExaCC()

        # Bug32439802/32459363:
        # atp_namespace rpm its required before installing dbaastools rpms
        #
        # Will install ATP Namespace rpm,
        # if enable_namespace is True in exabox.conf
        if _ebox.mIsExabm() and _ebox.isATP():
            _majorityVersion = _ebox.mGetMajorityHostVersion(ExaKmsHostType.DOMU)
            if _majorityVersion in ["OL7", "OL8"]:
                _atp_config = _ebox.mCheckConfigOption('atp')
                if _atp_config:
                    if 'enable_namespace' in _atp_config and _atp_config['enable_namespace'] == 'True':
                        _step_time = time.time()
                        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Installing ATP Namespace rpm')
                        _ebox.mSetupNamespace()
                        _step_time = time.time()
                        _ebox.mUpdateRpm('atp-namespace.x86_64.rpm')
                        _ebox.mLogStepElapsedTime(_step_time, 'Install ATP Namespace rpm')

        # run the installation of dbaastools_exa_main.rpm and rpm updates
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='RPM install script')
        _rc, _cmd = _ebox.mRunScript(aType='*', aWhen='post.gi_rpm', aStatusAbort=True)
        if _rc:
            ebLogError('*** Error ('+str(_rc)+') catched during scripts execution for cmd: '+_cmd)
            raise ExacloudRuntimeError(0x0116, 0xA, 'Step: RPM configuration error')

        _ebox.mLogStepElapsedTime(_step_time, 'RPM install script')

        # Set the DR Scan and VIP configuration if present in payload
        if _ebox.mGetCmd() == "createservice" and _ebox.mIsDRNetPresent() and _ebox.mIsOciEXACC():
            self.mSetDRScanVip(_ebox)

        # Install VmexacsRpm
        _ebox.mCopyVmexacsRpm()

        #Bug 33553474: Listener port need to be reconfigured to the GRID.INI
        if not _ebox.isATP() and _ebox.mGetCmd() == "createservice":
            mUpdateListenerPort(_ebox, _domu_list)

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
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='DBAASAPI Cloud Properties script')
        _ebox.mExecuteDbaaSApi()
        _ebox.mLogStepElapsedTime(_step_time, 'DBAASAPI Cloud Properties script')

        # Bug32312482: ADB configuration.
        # Install ADB init RPM and run adb_init script 
        if _ebox.isATP():
            ebLogInfo("*** Installing ADB Init rpm ***")
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='ADB_INIT RPM install')
            _ebox.mUpdateRpm('adb_init.x86_64.rpm', aForce=True)
            _ebox.mLogStepElapsedTime(_step_time, 'ADB_INIT RPM install')

            ebLogInfo("*** Running adb_init configuration script ***")
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='ADB_INIT configuration script')
            _rc, _cmd = _ebox.mRunScript(aType='*', aWhen='post.gi_adb_init', aStatusAbort=True, aParallel=False)
            if _rc:
                ebLogError('*** Error ('+str(_rc)+') catched during scripts execution for cmd: '+_cmd)
                raise ExacloudRuntimeError(0x0116, 0xA, 'ADB Init Step: ADB Init script configuration error',
                                           aStackTrace=True, aStep=self.step, aDo=True)
            _ebox.mLogStepElapsedTime(_step_time, 'ADB_INIT configuration script')
            _step_time = time.time()

        # install nosql
        if _ebox.mCheckConfigOption('install_nosql', 'True'):
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='nosql install')
            _domUs = list(map(operator.itemgetter(1),_ebox.mReturnDom0DomUPair()))
            _rackSize = _ebox.mGetRackSize()
            _nosql = ebNoSqlInstaller(_domUs,_rackSize)
            _nosql.mRunInstall()
            _ebox.mLogStepElapsedTime(_step_time, 'nosql install')

        # At self point opc user is available & hence create the priv/pub keys for opc user & inject the pub key
        # into the /home/opc/.ssh/authorized_keys and save the keys in the exacloud keys dir.
        ebLogInfo("*** Manage OPC user keys ****")
        _ebox.mAddUserPubKey('opc')
        _ebox.mCopySAPfile()

        #
        # POSTGI - Disable TFA if grid_tfa_enabled is not True( Dev Env )
        if not _ebox.mCheckConfigOption('grid_tfa_enabled','True') and _ebox.isATP() == False:
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Disabing TFA')
            _ebox.mDisableTFA()
            _ebox.mLogStepElapsedTime(_step_time, 'Disabling TFA')

        #Run the mAtpConfig after create the OPC user
        if _ebox.isATP():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='ATPConfig')
            _ebox.mAtpConfig()
            _ebox.mLogStepElapsedTime(_step_time, 'ATPConfig')

        # 
        # ER 31923304: Configure temporary directories exclusions
        # 
        _ebox.mAddOracleFolderTmpConf()

        #
        # ER 30138555: MTLS Authentication For ExaCC DBCS Agent
        # Prepare domUs for MTLS communication
        #
        if _ebox.mIsOciEXACC():
            # Enh 35823972: COPY DOM-U CERTIFICATE INTO DOM-U DURING CS
            if _ebox.mIsFedramp():
                _ebox.mSetupDomUsForSecurePatchServerCommunication()
            else:
                _ebox.mSetupDomUsForSecureDBCSCommunication()
            _obj = ebCopyDBCSAgentpfxFile(_ebox)
            _obj.mCopyDbcsAgentpfxFiletoDomUsForFedramp()
            # ER 32161016: Copy DBCS/CPS agent wallets
            _ebox.mAddAgentWallet()

        #
        # ER 27371691: Install DBCS agent rpm
        #
        _step_time = time.time()
        # skip the dbcs-agent installation for ADB
        if not _ebox.isATP():
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Installing DBCS Agent rpm')
            _majorityVersion = _ebox.mGetMajorityHostVersion(ExaKmsHostType.DOMU)
            if _majorityVersion in ["OL7", "OL8"]:
                if _ebox.mIsExabm() or _ebox.mCheckConfigOption("force_install_dbcs_agent", "exacs"):
                    _ebox.mUpdateRpm('dbcs-agent.OL7.x86_64.rpm')
                else:
                    if _ebox.mIsOciEXACC() or _ebox.mCheckConfigOption("force_install_dbcs_agent", "exacc"):
                        _ebox.mUpdateRpm('dbcs-agent-exacc.OL7.x86_64.rpm')
                    else:
                        ebLogInfo('Skipping OL7 dbcs agent install')
            else:
                if _ebox.mIsExabm() or _ebox.mCheckConfigOption("force_install_dbcs_agent", "exacs"):
                    _ebox.mUpdateRpm('dbcs-agent.OL6.x86_64.rpm')
                else:
                    if _ebox.mIsOciEXACC() or _ebox.mCheckConfigOption("force_install_dbcs_agent", "exacc"):
                        _ebox.mUpdateRpm('dbcs-agent-exacc.OL6.x86_64.rpm')
                    else:
                        ebLogInfo('Skipping OL6 dbcs agent install')
            _ebox.mLogStepElapsedTime(_step_time, 'Install DBCS Agent rpm')
        else:
            ebLogInfo('Skipping dbcs-agent installation for ADB')

        # DBCS No-Auth mode only in DEV/QA
        if not _ebox.mEnvTarget() and _ebox.mCheckConfigOption('force_dbcsagent_auth', 'True'):
            _ebox.mEnableNoAuthDBCS()

        if _ebox.mIsExacm() is True:
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='EXACM copy ssh key patch script')
            _ebox.mCopyExacmPatchKeyScript()
            _ebox.mLogStepElapsedTime(_step_time, 'EXACM copy ssh key script')

        if _ebox.isATP():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Set CSS Misscount in ATP')
            _miscnt = get_gcontext().mGetConfigOptions().get("css_misscount", "")
            if _miscnt:
                _ebox.mDomUCSSMisscountHandler(aMode = False, aMisscount = _miscnt)
            else:
                ebLogInfo("*** Setting CSS Misscount as value set in exabox.conf")
            _ebox.mLogStepElapsedTime(_step_time, 'Set CSS Misscount in ATP')

        #Set OraInventory Permissions to drwxrwx---
        _ebox.mSetOraInventoryPermissions()


        #Install AHF setup on domU for non-ATP services
        if not _ebox.isATP() and _ebox.mGetCmd() == "createservice":
            _csu.mInstallAhfonDomU(_ebox, self.step, _steplist)

        #
        # run Exachk
        # 
        _enable_exachk = _ebox.mCheckConfigOption('enable_exachk')
        if _enable_exachk:
            if 'post_create_vm' in _enable_exachk and _enable_exachk['post_create_vm'] == 'True':
                _ebox.mExecuteExachk()

        # Stores the interconnect IP's of the VM's in cluster_interconnect.dat
        _ebox.mStoreDomUInterconnectIps()

        if not _ebox.isATP():
            _ebox.mRemoveDatabaseMachineXmlDomU()

        _ebox.mCopyExaDataScript() # copy the exadata_updates script to DomUs
        #Create a list of DomUs for the given cluster and store it in a json file
        #
        _ebox.mSaveClusterDomUList()
        
        # Sanitize DomU /etc/stsctl.conf for XEN envs.
        self.mSanitizeDomUSysctlConf(_ebox)

        # Configure Hugepages
        if not _ebox.isATP():
            _percentage = _ebox.mCheckConfigOption('hugepages_percentage')
            if _percentage is None:
                _percentage = '50' # set hugepages to 50% of the total VM memory 
            _ebox.mUpdateHugepagesForCluster(_percentage) 

        _reboot_vms = False
        if _ebox.mIsKVM():
            for _, _domU in _ebox.mReturnDom0DomUPair():
                _rc, _str = _ebox.mMakeFipsCompliant(aOptions, aHost=_domU)
                if _str == "reboot_host":
                    _reboot_vms = True
                    #reboot will happen at the end of this step!

        if _ebox.IsZdlraProv():
            _ebox.mGetZDLRA().mUpdateHugePages(aOptions)

        try:
            self.mSeedOCIDonDomU(_ebox,aOptions)
        except Exception as e: 
            ebLogError(f"*** mSeedOCIDonDomU failed with Exception: {str(e)}")

        try:
            self.maxDistanceUpdate(_ebox)
        except Exception as e: 
            ebLogError(f"*** maxDistanceUpdate failed with Exception: {str(e)}")

        if _ebox.mCheckConfigOption('ociexacc', 'True') and _ebox.isATP():
            try:
                _ebox.mInstallSuricataRPM()
            except Exception as e: 
                ebLogWarn(f"*** mInstallSuricataRPM failed with Exception: {str(e)}")

        # Reset SSH Cluster Keys
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Reset SSH Cluster knowhost entries')
        _ebox.mResetClusterSSHKeys(aOptions)
        _ebox.mLogStepElapsedTime(_step_time, 'Reset SSH Cluster knowhost entries')

        # Generate switch keys
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Generate Switch Keys')
        _ebox.mHandlerGenerateSwitchesKeys()
        _ebox.mLogStepElapsedTime(_step_time, 'Generate Switch Keys')

        # Copy additional files
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Copy additional files')

        # Bug32540420: For ADBD, we use rpmupd logic to update dbaastools_exa rpm
        # during create service.
        # We shouldnt update any rpm after CreateService has finished (for ADB-D)
        if not _ebox.isATP():
            # ER 27503421
            if _ebox.mIsOciEXACC():
                _ebox.mCopyVmexacsRpm()
            # Bug 27216120
            _csu = csUtil()
            _dbaastools_rpm = _csu.mGetDbaastoolRpmName(aOptions)                   
            _ebox.mUpdateRpm(_dbaastools_rpm)

        # ER 25900538 and 27555477
        if _ebox.mIsExabm() or _ebox.mIsOciEXACC():
            _ebox.mCopyCreateVIP()
            _ebox.mCopyOneoffZipToDomus()
        _ebox.mLogStepElapsedTime(_step_time, 'Copy additional files')

        # Add customer SSH Key in DOMUs
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Patch VM SSH Keys')
        _ebox.mPatchVMSSHKey(aOptions)
        _ebox.mLogStepElapsedTime(_step_time, 'Patch VM SSH Keys')

        # SSH Key patching (default root/opc/oracle)
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Create SSH Key patching')
        _ebox.mPostDBSSHKeyPatching(aOptions, 'addkey', ['root','oracle','opc'])
        _ebox.mLogStepElapsedTime(_step_time, 'Create SSH Key patching')

        #
        # Alter cloud_user's password in the cells.
        #
        if _ebox.mGetCmd() == "createservice" and _ebox.mCheckConfigOption('exacli_use_db_pwd', 'True'):

            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Alter user-password')
            try:
                if not _ebox.mIsOciEXACC():
                    _ebox.mSetWalletEntry(aOptions)
                _ebox.mUpdateCloudUser(aOptions)
            except Exception as e:
                ebLogError("Error while updating cloud user password")
                ebLogError(e)
                # We will not raise any errors regarding the ExaCLI password if we're in an ExaCC environment
                if _ebox.mIsOciEXACC():
                    ebLogInfo("Not stopping step flow since we're in an ExaCC environment.")
                # Else, if the corresponding flag is enabled, we will raise runtime error when invalid ExaCLI pwd is passed
                elif get_gcontext().mGetConfigOptions().get("enforce_exacli_password_update"):
                    raise ExacloudRuntimeError(0x0116, 0xA, 'Failed to update cloud user password', aStackTrace=True, aStep=self.step) from e
            _ebox.mLogStepElapsedTime(_step_time, 'Alter user-password')

        #
        # Create ADBS cloud_user
        #
        _ebox.mCreateAdbsUser(aOptions)

        # Enable Storage Cell remote password change for exacli users
        _ebox.mEnableRemotePwdChange(aOptions)

        # ATP backup Listener
        if _ebox.isATP():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Setup ATP Backup Listener')

            # Setup ATP Backup Listener
            # Below is the flow needed for EXABM - ATP
            if _ebox.mIsExabm() and _ebox.mCheckClusterNetworkType():

                for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                    ebLogInfo("*** ATP etc/hosts on %s ***" % _domU)
                    AtpAddScanname2EtcHosts(None, _ebox.mGetATP(), _domU).mExecute()

                # Only need to be run on one domU
                ebLogInfo("*** ATP Listener on %s ***" % _domU)
                AtpSetupSecondListener(None, _ebox.mGetATP(), _ebox.mReturnDom0DomUPair(),
                        _ebox.mGetMachines(), _ebox.mGetNetworks(), None, _ebox.mGetClusters,
                        aOptions).mExecute()
                AtpSetupASMListener(None, _ebox, None).mExecute()

            # All the Above is for EXABM, below is EXACC-ATP hook (VGE:NEED TO BE EXTERNALIZED)
            if _ebox.mIsOciEXACC():

                _node = exaBoxNode(get_gcontext())

                # First domU
                _all_domU = list(map(operator.itemgetter(1), _ebox.mReturnDom0DomUPair()))
                _first_domU = _all_domU[0]
                _node.mConnect(aHost=_first_domU)
                _listener_info = ebExaCCAtpListener.sExtractInfoFromDomU(_node)

                if _ebox.mIsDebug():
                    ebLogDebug("ExaCCAtp Listener Info: {}".format(_listener_info))

                if not _listener_info:
                    ebLogWarn("Error on obtaining ATP Listener info, skip setup")
                    _node.mDisconnect()

                else:
                    # VGE: Need to be refactored
                    _root_commands, _grid_commands, _final_grid_commands, _final_root_commands = ebExaCCAtpListener.sGenerateListenerCommands(**_listener_info)
                    if _ebox.mIsDebug():
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

            _ebox.mLogStepElapsedTime(_step_time, 'Setup ATP Backup Listener')

        #ATP will be detected from inside the function
        _ebox.mATPUnlockListeners()

        # Disable TFA blackout after starter db deletion (end of pre-provisioning),
        # blackout is enabled right after TFA is installed
        _ebox.mEnableTFABlackout(False, "Pre-Provision blackout", aOptions)

        if _ebox.isATP():
            try:
                _dpairs = _ebox.mReturnDom0DomUPair()
                ebAtpUtils.setScanFqdn(_dpairs)
            except Exception as ex:
                ebLogError(f"*** Could not modify scan name to fqdn. Error: {ex}")

        #ocde init
        #Updates grid.ini with parameters - oracle_home, acfs_vol_dir
        for _, _domU in _ebox.mReturnDom0DomUPair():
            _rc = updateGridINI(_domU)
            if _rc:
                _err_str = f"{_domU}: Error while running the command: /usr/bin/dbaascli admin initializeCluster"
                ebLogError(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["OCDE_INIT_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)        

        if _reboot_vms is True:
            ebLogTrace(f'Rebooting cluster Vms')
            _ebox.mParallelDomUShutdown()
            _ebox.mParallelDomUStart()

        # Check if Clusterware (CRS) is up post vm reboot
        _dpairs = _ebox.mReturnDom0DomUPair()
        _domu_list = [ _domu for _ , _domu in _dpairs]
        _ebox.mCheckCrsIsUp(_domu_list[0], _domu_list)
        

        # Bug34266093: StarterDB removal changes for ADBD
        # This script will be executed inside the domU 
        # to perform tasks that were previously executed in starterDB flow.
        #
        # Important notes: 
        # This block of code should be always the last to be executed
        # in POSTGINID step of create service.
        if _ebox.isATP() and not _ebox.mCheckConfigOption("force_starter_db_install") == 'True':
            ebLogInfo("*** Running adb_endcreateservice script ***")
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='ADB End Create Service script')

            ebLogInfo("*** CRS/ACFS is up ***")
            _rc, _cmd = _ebox.mRunScript(aType='*', aWhen='post.gi_adbd_endcs', aStatusAbort=True, aParallel=False)
            if _rc:
                ebLogError('*** Error ('+str(_rc)+') catched during scripts execution for cmd: '+_cmd)
                raise ExacloudRuntimeError(0x0116, 0xA, 'ADB End Create Service Step script error',
                                           aStackTrace=True, aStep=self.step, aDo=True)
            _ebox.mLogStepElapsedTime(_step_time, 'ADB End Create Service script')
            _step_time = time.time()
        # End of ADBD CreateService End script block

        # Bug 32533418: Remove cloud_properties json from the domUs
        # Bug 38332780: Remove the file after DBCS Agent is installed and ADBD processes are finsihed.
        _ebox.mRemoveCloudPropertiesPayload() 

        # Print the permissions of the dbnid directory
        try:
            for _, _domU in _ebox.mReturnDom0DomUPair():
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domU)
                if _node.mFileExists('/var/opt/oracle/dbaas_acfs'):
                    _node.mExecuteCmdLog("/bin/chown -fR oracle:oinstall /var/opt/oracle/dbaas_acfs")
                    _i, _o, _e = _node.mExecuteCmd("ls -ltrd /var/opt/oracle/dbaas_acfs")
                    ebLogInfo(f"The output for ls -ltrd /var/opt/oracle/dbaas_acfs is {_o.read()}")
                    _i, _o, _e = _node.mExecuteCmd("ls -ltr /var/opt/oracle/dbaas_acfs")
                    ebLogInfo(f"The output for ls -ltr /var/opt/oracle/dbaas_acfs is {_o.read()}")
                    break
                else:
                    ebLogInfo(f"The output for ls -ltr /var/opt/oracle/dbaas_acfs could not be obtained - the directory does not exist.")
                _node.mDisconnect()
        except Exception as ex:
            ebLogError(f"*** Could not get output for ls -ltr /var/opt/oracle/dbaas_acfs. Error: {ex}")

        #Update System Vault Access to the new compute
        if _ebox.mGetCmd() == "createservice" and not _ebox.isBaseDB() and not _ebox.mIsExaScale():
            _utils.mUpdateSystemVaultAccess(aOptions)

        # Remove DomU Access
        if _ebox.mGetCmd() == "createservice" and aOptions and aOptions.jsonconf and \
           "delete_domu_keys" in aOptions.jsonconf and \
           aOptions.jsonconf['delete_domu_keys'].lower() == "true":
            _ebox.mHandlerRemoveDomUsKeys()

        ebLogTrace('csExaScaleComplete: Completed doExecute Successfully')

    def undoExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csExaScaleComplete: Entering undoExecute')
        _ebox = aCluCtrlObj
        _steplist = aStepList

        #Remove default & additional acfs volumes
        _utils = ebExascaleUtils(_ebox)
        _utils.mRemoveDefaultAcfsVolume(aOptions)
        _utils.mRemoveACFS(aOptions)

        # Uninstall dbcs agent rpm.
        _majorityVersion = _ebox.mGetMajorityHostVersion(ExaKmsHostType.DOMU)

        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Uninstalling DBCS Agent rpm')
        _domUsPingable = True
        _domU_list = [ _domU for _dom0, _domU in _ebox.mReturnDom0DomUPair()]
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

        _ebox.mLogStepElapsedTime(_step_time, 'Uninstall DBCS Agent rpm')

        ebLogTrace('csExaScaleComplete: Completed undoExecute Successfully')
