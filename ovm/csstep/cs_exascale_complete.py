"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_exascale_complete.py - Complete step on ExaScale Provisioning

FUNCTION:
    Complete step on ExaScale Provisioning

NOTES:
    Invoked from cs_driver.py

EXTERNAL INTERFACES: 
    csExaScaleComplete ESTP_EXASCALE_COMPLETE

INTERNAL CLASSES:

History:
       MODIFIED (MM/DD/YY)
       prsshukl  11/19/25 - Bug 38037088 - BASE DB -> MOVE THE DO/UNDO STEPS
                            FOR BASEDB TO A NEW FILE IN CSSTEP
       scoral    07/29/25 - 38209895 - Skip Remove ASM diskgroups during undo
                            since it's not applicable for ExaDB-XS because CRS
                            is not even installed by ECS on ExaDB-XS envs.
       dekuckre  07/03/25 - 38101160 - Install ggs rpm
       naps      07/03/25 - Bug 38116390 - copy weblogic cert for R1 env.
       prsshukl  06/26/25 - Bug 37747083 - Post check to validate that the volumes 
                            are attached to the domU
       prsshukl  04/23/25 - Bug 37857887 - REMOVE CELLINIT.ORA FILE FOR EXADBXS
                            (BLOCK STORAGE)
       prsshukl  04/04/25 - Enh 37740750 - EXADB-XS 19C :CS AND ADD COMPUTE
                            ENDPOINT UPDATE-> ATTACH DBVOLUME VOLUMES TO GUEST
                            VMS
       abflores  03/05/25 - Bug 37473868: Fix marker files logging
       jesandov  08/14/24 - 36948132: Add function that check cavium
                            connectivity after reboot
       ririgoye  06/27/24 - Bug 36742070 - EXADB-XS: PING_TARGETS SHOULD BE SET
                            IN CPROPS.INI
       prsshukl  06/12/24 - Bug 36260053 - 23C GRID IMAGES TO BE MADE AVAILABLE
                            FOR EXASCLE ENVIRONMENT
       ririgoye  03/11/24 - Bug 36390545 - Removed domU keys deletion block
                            since it's already performed in secure_vms endpoint
       dekuckre  02/27/24 - 36082776: Install dbaastools exadbcs rpm
       jesandov  01/30/24 - 36237806: Reorder exascale complete step to
                            optimice provisioning timing
       akkar     01/25/24 - Bug:36085104 - Add support for AHF installation on
                            EXASCALE
       scoral    11/16/23 - Bug 36015572 - /SYS/DEVICES/VIRTUAL/DMI/ID/
                            CHASSIS_ASSET_TAG IS INCOMPLETE IN XS CLUSTER DB
                            NODES
       jesandov  10/16/23 - 35729701: Support of OL7 + OL8
       gparada   28/08/23 - 35738616 Added updDomUsToJdk11
       scoral    09/01/23 - Bug 35761699: Re-enable filesystem resize.
       scoral    08/30/23 - Bug 35757281: Re-disable filesystem resize.
       scoral    08/25/23 - Bug 35689130: Re-enable filesystem resize.
       scoral    06/23/23 - Bug 35502608: Disable filesystem resize.
       scoral    04/17/23 - Bug 35300995: Remove ADBD iptables deprecated code.
       jesandov  21/10/22 - Bug 34410998 - File Creation
"""

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
from exabox.tools.ebNoSql.ebNoSqlInstaller import ebNoSqlInstaller
from exabox.ovm.hypervisorutils import ebVgCompRegistry
from exabox.ovm.atp import (AtpAddRoutes2DomU, ebCluATPConfig,
        AtpSetupSecondListener, AtpAddiptables2Dom0, ebATPTest, AtpCreateAtpIni,
        AtpAddScanname2EtcHosts, AtpSetupNamespace, AtpSetupASMListener)
from exabox.ovm.cluexaccatp import ebExaCCAtpListener
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.utils.node import node_cmd_abs_path_check
from exabox.ovm.cludomufilesystems import expand_domu_filesystem
from exabox.ovm.cluencryption import resizeEncryptedVolume, isEncryptionRequested, encryptionSetupDomU
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.utils.node import connect_to_host
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.ovm.bom_manager import ImageBOM
from exabox.utils.ExaRegion import is_r1_region

# This class implements doExecute and undoExecute functions
# for the ESTP_EXASCALE_COMPLETE step of create service
class csExaScaleComplete(CSBase):
    def __init__(self):
        self.step = 'ESTP_EXASCALE_COMPLETE'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        ebLogInfo('csExaScaleComplete: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        ebox.mUpdateStatus('createservice step '+self.step)
        imageBom = ImageBOM(ebox)
        _csu = csUtil()

        ################################
        ### STEPS BEFORE BOOT THE VM ###
        ################################

        # FIPs Compliance
        if not imageBom.mIsSubStepExecuted(self.step, "MAKE_FIPS_COMPLIANCE"):
            for _dom0, _domU in ebox.mReturnDom0DomUPair():
                ebox.mMakeFipsCompliant(aOptions, aHost=_domU)

        # At self point opc user is available & hence create the priv/pub keys for opc user & inject the pub key
        # into the /home/opc/.ssh/authorized_keys and save the keys in the exacloud keys dir.
        if not imageBom.mIsSubStepExecuted(self.step, "MANAGE_OPC_KEY"):
            ebLogInfo("*** Manage OPC user keys ****")
            ebox.mAddUserPubKey('opc')

        #
        # Customize VM.CFG (e.g. additional images, partitions,...)
        #

        if not imageBom.mIsSubStepExecuted(self.step, "PATCH_VM_BEFORE_BOOT"):
            with ebox.remote_lock():
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Patching VM Configuration before boot')
                ebox.mPatchVMCfgBeforeBoot(aOptions)
                ebox.mLogStepElapsedTime(_step_time, 'Patching VM Configuration before boot')

        if not imageBom.mIsSubStepExecuted(self.step, "PATCH_VM_CFG"):
            # Install VmexacsRpm
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='mCopyVmexacsRpm')
            ebox.mCopyVmexacsRpm()
            ebox.mLogStepElapsedTime(_step_time, 'mCopyVmexacsRpm')

            # Configure Huge Page for ExaScale
            if ebox.IsZdlraProv():
                ebox.mGetZDLRA().mUpdateHugePages(aOptions)

            _exascale = ebCluExaScale(ebox)

            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='mConfigureHugePage')
            _exascale.mConfigureHugePage(aOptions)
            ebox.mLogStepElapsedTime(_step_time, 'mConfigureHugePage')
            

            # Configure SHMALL
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='mConfigureShmAll')
            ebox.mConfigureShmAll()
            ebox.mLogStepElapsedTime(_step_time, 'mConfigureShmAll')
            

            with ebox.remote_lock():
                _step_time_lock = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Dom0 Lock Acquire')

                # VM Stop
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Parallel DomU Shutdown')
                ebox.mParallelDomUShutdown()
                ebox.mLogStepElapsedTime(_step_time, 'Parallel DomU Shutdown')
                
                #####################################
                ### STEPS WITH THE VM IN SHUTDOWN ###
                #####################################

                # Configure mPatchVMCfg
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='mPatchVMCfgOnShutdown')
                ebox.mPatchVMCfgOnShutdown(aOptions)
                ebox.mLogStepElapsedTime(_step_time, 'mPatchVMCfgOnShutdown')
                

                # Configure VMExacsService
                ebox.mUpdateVmetrics('vmexacs_kvm')
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='mStartVMExacsServiceOnShutdown')
                ebox.mStartVMExacsServiceOnShutdown(aOptions)
                ebox.mLogStepElapsedTime(_step_time, 'mStartVMExacsServiceOnShutdown')

                # VM Start
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='mParallelDomUStart')
                ebox.mParallelDomUStart()
                ebox.mLogStepElapsedTime(_step_time, 'mParallelDomUStart')

                ebox.mLogStepElapsedTime(_step_time_lock, 'Dom0 Lock Acquire')
                

            ###############################
            ### STEPS AFTER VM START UP ###
            ###############################

            # Configure mPatchVMCfg
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='mPatchVMCfgAfterBoot')
            ebox.mPatchVMCfgAfterBoot(aOptions)
            ebox.mLogStepElapsedTime(_step_time, 'mPatchVMCfgAfterBoot')

            # Resize Domu filesystems
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Resize FS')
            expand_domu_filesystem(
                ebox,
                perform_dom0_resize=not ebox.mCheckConfigOption("exascale_edv_enable", "True"),
                domu_reboot=False
            )
            ebox.mLogStepElapsedTime(_step_time, 'Resize FS')

            # Check Cavium Connectivity
            try:
                ebox.mCheckCaviumInstanceDomUs()
            except:
                ebLogWarn("Cavium connectivity down")

            # Configure VMExacsService
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='mStartVMExacsServiceAfterBoot')
            ebox.mStartVMExacsServiceAfterBoot(aOptions)
            ebox.mLogStepElapsedTime(_step_time, 'mStartVMExacsServiceAfterBoot')
            
        # Bug32439802/32459363:
        # atp_namespace rpm its required before installing dbaastools rpms
        #
        # Will install ATP Namespace rpm,
        # if enable_namespace is True in exabox.conf
        if not imageBom.mIsSubStepExecuted(self.step, "RPM_UPDATE"):
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

        if not imageBom.mIsSubStepExecuted(self.step, "UPDATE_DBAAS_EXA"):
            ebox.mUpdateRpm('dbaastools_exadbxs_main.rpm')

        if not imageBom.mIsSubStepExecuted(self.step, "RPM_UPDATE"):
            ebox.mLogStepElapsedTime(_step_time, 'RPM install script')

            # Bug32312482: ADB configuration.
            # Install ADB init RPM and run adb_init script 
            if ebox.isATP():
                ebLogInfo("*** Installing ADB Init rpm ***")
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='ADB_INIT RPM install')
                ebox.mUpdateRpm('adb_init.x86_64.rpm')
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

            # install nosql
            if ebox.mCheckConfigOption('install_nosql', 'True'):
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='nosql install')
                _domUs = list(map(operator.itemgetter(1),ebox.mReturnDom0DomUPair()))
                _rackSize = ebox.mGetRackSize()
                _nosql = ebNoSqlInstaller(_domUs,_rackSize)
                _nosql.mRunInstall()
                ebox.mLogStepElapsedTime(_step_time, 'nosql install')

            ebox.mCopySAPfile()

        #
        # POSTGI - Disable TFA if grid_tfa_enabled is not True( Dev Env )
        if not imageBom.mIsSubStepExecuted(self.step, "TFA_ATP_CONFIG"):
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

        #
        # ER 30138555: MTLS Authentication For ExaCC DBCS Agent
        # Prepare domUs for MTLS communication
        #
        if not imageBom.mIsSubStepExecuted(self.step, "SECURE_DBCSAGENT"):
            if ebox.mIsOciEXACC():
                ebox.mSetupDomUsForSecureDBCSCommunication()
                #
                # ER 32161016: Copy DBCS/CPS agent wallets
                ebox.mAddAgentWallet()

        #
        # ER 27371691: Install DBCS agent rpm
        #
        if not imageBom.mIsSubStepExecuted(self.step, "DBCS_AGENT_UPDATE"):
            _step_time = time.time()
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

            # DBCS No-Auth mode only in DEV/QA
            if not ebox.mEnvTarget() and ebox.mCheckConfigOption('force_dbcsagent_auth', 'True'):
                ebox.mEnableNoAuthDBCS()

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
        if not imageBom.mIsSubStepExecuted(self.step, "EXTRA_UPDATES"):
            ebox.mSetOraInventoryPermissions()

        if not imageBom.mIsSubStepExecuted(self.step, "AHF_UPDATE"):
            if not ebox.isATP():
                _step_time = time.time()
                _csu.mInstallAhfonDomU(ebox, self.step, steplist, aInit=True, aWait=False)
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Install AHF on Exascale')
                ebox.mLogStepElapsedTime(_step_time, 'Install AHF on Exascale')

        if not imageBom.mIsSubStepExecuted(self.step, "ADDITIONAL_DOMU_CHECKS"):
            # Bug 36742070: Adding domUs' gateway IPs to their cprops.ini file
            ebox.mAddXsPingTargets()

            # Stores the interconnect IP's of the VM's in cluster_interconnect.dat
            try:
                ebox.mStoreDomUInterconnectIps()
            except Exception as e:
                ebLogWarn("Could not execute mStoreDomUInterconnectIps: {str(e)}")
        
            if not ebox.isATP():
                ebox.mRemoveDatabaseMachineXmlDomU()

            ebox.mCopyExaDataScript() # copy the exadata_updates script to DomUs
            #Create a list of DomUs for the given cluster and store it in a json file
            #
            ebox.mSaveClusterDomUList()

            try:
                self.mSeedOCIDonDomU(ebox,aOptions)
            except Exception as e: 
                ebLogError(f"*** mSeedOCIDonDomU failed with Exception: {str(e)}")

            try:
                self.maxDistanceUpdate(ebox)
            except Exception as e: 
                ebLogError(f"*** maxDistanceUpdate failed with Exception: {str(e)}")

            if ebox.mCheckConfigOption('allow_23c_grid_image_download','True'):
                try:
                    csu = csUtil()
                    aDomUGridPath = ebox.mCheckConfigOption('domu_grid_image_path')
                    csu.mInstall23cGridImageInDomU(ebox, aDomUGridPath, aOptions)
                except Exception as e:
                    ebLogWarn(f"*** the copy of grid image failed with Exception: {str(e)} . Moving ahead")


            if ebox.mCheckConfigOption('ociexacc', 'True') and ebox.isATP():
                try:
                    self.mInstallSuricataRPM(ebox)
                except Exception as e: 
                    ebLogWarn(f"*** mInstallSuricataRPM failed with Exception: {str(e)}")

        # Reset SSH Cluster Keys
        if not imageBom.mIsSubStepExecuted(self.step, "SSH_KEY_MANAGEMENT"):
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

        if not imageBom.mIsSubStepExecuted(self.step, "ATP_BACKUP_LISTENER"):
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

                        # Sleep 2 min as I saw that clusterware take a bit of time here to mount ACFS
                        time.sleep(120)

            ebox.mLogStepElapsedTime(_step_time, 'Setup ATP Backup Listener')

            #ATP will be detected from inside the function
            ebox.mATPUnlockListeners()

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

        # UPDATE DBCS
        if ebox.mCheckConfigOption("exadbxs_image_base_provisioning_enable",  "True"):
            for _, _domU in ebox.mReturnDom0DomUPair():
                with connect_to_host(_domU, get_gcontext()) as _node:
                    ebLogInfo(f"Setup Auth DCS in {_domU}")
                    _node.mExecuteCmdLog("/opt/oracle/dcs/bin/setupAuthDcs.py")
                    _node.mExecuteCmdLog("service dbcsagent stop")
                    _node.mExecuteCmdLog("service dbcsagent start")
                    _node.mExecuteCmdLog("service dbcsadmin stop")
                    _node.mExecuteCmdLog("service dbcsadmin start")

        # Print the permissions of the dbnid directory
        if not imageBom.mIsSubStepExecuted(self.step, "UPDATE_DBFILES"):
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
                _rc, _cmd = ebox.mRunScript(aType='*', aWhen='post.gi_adbd_endcs', aStatusAbort=True, aParallel=False)
                if _rc:
                    ebLogError('*** Error ('+str(_rc)+') catched during scripts execution for cmd: '+_cmd)
                    raise ExacloudRuntimeError(0x0116, 0xA, 'ADB End Create Service Step script error',
                                               aStackTrace=True, aStep=self.step, aDo=True)
                ebox.mLogStepElapsedTime(_step_time, 'ADB End Create Service script')
            # End of ADBD CreateService End script block 

            self.updDomUsToJdk11(ebox)

        _exascale = ebCluExaScale(ebox)
        if not imageBom.mIsSubStepExecuted(self.step, "UDEV_RULES_CREATION_AND_REMOVE_CELLINIT_ORA"):
            if ebox.isDBonVolumes():
                _exascale.mWriteUdevDbVolumesRules()
                _exascale.mRemoveCellinitOra()

        if ebox.mCheckConfigOption('enable_validate_volumes', 'True'):
            for _dom0, _domU in ebox.mReturnDom0DomUPair():
                _exascale.mPerformValidateVolumesCheck(_dom0, _domU)
        else:
            ebLogInfo(f"enable_validate_volumes config is disabled in exabox.conf. Hence Skipping")      

        # Wait for AHF install
        if not imageBom.mIsSubStepExecuted(self.step, "AHF_UPDATE"):
            if not ebox.isATP():
                _step_time = time.time()
                _csu.mInstallAhfonDomU(ebox, self.step, steplist, aInit=False, aWait=True)
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Install AHF on Exascale')
                ebox.mLogStepElapsedTime(_step_time, 'Install AHF on Exascale')

        ebLogInfo('*** Exacloud Operation Successful : POST GI Install')
        ebLogInfo('csExaScaleComplete: Completed doExecute Successfully')


    def mInstallSuricataRPM(self,ebox):
        _domUs = [domU for _, domU in ebox.mReturnDom0DomUPair()]
        ebLogInfo(f"DomUs: {_domUs}")
        def _mInstallSuricataRPM(_host):
            try:
                _suricata_rpm_tar_path=os.path.join(get_gcontext().mGetBasePath(),"../suricata/suricata_installer.tgz")
                ebLogInfo(f"Suricata Installer Tar path: {_suricata_rpm_tar_path}")

                if not os.path.exists(_suricata_rpm_tar_path):
                    raise Exception(f"Suricata Installer File not found at {_suricata_rpm_tar_path}!")

                with connect_to_host(_host, get_gcontext(), "root") as _node:
                    ebLogTrace(f"connected node detail : {_host}")
                    _remote_rpm_tar_path = "/tmp/rpm"
                    _rm_cmd = node_cmd_abs_path_check(_node, "rm")

                    #delete the installation directory if already existing
                    if _node.mFileExists(_remote_rpm_tar_path):
                        ebLogInfo("RPM Directory exists! Deleting the Directory..")
                        _cmd = f"{_rm_cmd} -rf {_remote_rpm_tar_path}" 
                        _node.mExecuteCmdLog(_cmd)
                        #unsuccessful removal of existing Directory
                        if _node.mGetCmdExitStatus() != 0:
                            raise Exception("Unsuccessful removal of existing Directory")
                    #create directory for installation files
                    _node.mMakeDir(_remote_rpm_tar_path)

                    if _node.mFileExists(_remote_rpm_tar_path):
                        ebLogInfo(f"Directory created successfully at {_remote_rpm_tar_path}")
                    else:
                        raise Exception("Unsuccessful Directory creation at remote path")

                    _remote_rpm_tar_location = os.path.join(_remote_rpm_tar_path, os.path.basename(_suricata_rpm_tar_path))
                    #copy suricata tar file to remote location
                    _node.mCopyFile(_suricata_rpm_tar_path, _remote_rpm_tar_path)

                    if _node.mFileExists(_remote_rpm_tar_location):
                        ebLogInfo(f"Installer tar copied successfully at {_remote_rpm_tar_location}")
                    else:
                        raise Exception("Unsuccessful copy of installer tar file at remote path")

                    #untar 
                    _tar_cmd = node_cmd_abs_path_check(_node, "tar")
                    _cmd = f"{_tar_cmd} -xzf {_remote_rpm_tar_location} -C {_remote_rpm_tar_path}/." 
                    _node.mExecuteCmdLog(_cmd)
                    #unsuccessful untar of the rpm folder
                    if _node.mGetCmdExitStatus() != 0:
                        raise Exception("Unsuccessful untar of the RPM at remote path")

                    #find if install.py is present
                    _installer_file_name=f"{_remote_rpm_tar_path}/install.py"
                    if _node.mFileExists(_installer_file_name):
                        ebLogInfo(f"Installer file found at {_installer_file_name}")
                    else:
                        raise Exception("Installer file not present at {_installer_file_name}")

                    #run install.py
                    _python_cmd=node_cmd_abs_path_check(_node, "python3")
                    _install_type = "domu"
                    _install_action = "Install"
                    _cmd = f"{_python_cmd} {_installer_file_name} --type {_install_type} --action {_install_action}"
                    _node.mExecuteCmdLog(_cmd)
                    #unsuccessful installation
                    if _node.mGetCmdExitStatus() != 0:
                        _remote_log_file_name = f"{_remote_rpm_tar_path}/suricata-installer.log"
                        _suricata_log_name = "suricata-installer.log"
                        _suricata_log_timestamp = str(time.time()).replace(".", "")
                        _suricata_log_location = _remote_rpm_tar_path
                        _node_name = str(_host).split(".")[0]
                        _remote_log_file = f"{_suricata_log_timestamp}_{_node_name}_{_suricata_log_name}"
                        _remote_log_file_path = f"{_suricata_log_location}/{_remote_log_file}"
                        _mv_cmd=node_cmd_abs_path_check(_node, "mv")
                        _cmd = f"{_mv_cmd} {_remote_log_file_name} {_remote_log_file_path}"
                        _node.mExecuteCmdLog(_cmd)
                        _local_log_file_path=os.path.join(gLogMgrDirectory, _remote_log_file)
                        if _node.mFileExists(_remote_log_file_path):
                            ebLogInfo("suricata-installer.log present at remote location. Initiating copy to local.")
                            _node.mCopy2Local(_remote_log_file_path,_local_log_file_path)
                            ebLogInfo(f"local log file path: {os.path.abspath(_local_log_file_path)}")
                        else:
                            raise Exception("Suricata Installer log not found at remote location!")
                        raise Exception("Unsuccessful RPM installation.")

                    #delete tar file once installation is done
                    _cmd = f"{_rm_cmd} -rf {_remote_rpm_tar_path}"
                    _node.mExecuteCmdLog(_cmd)
                    #unsuccessful delete
                    if _node.mGetCmdExitStatus() != 0:
                        raise Exception("Could not delete the RPM tar directory after installation! ")
   

            except Exception as exep:
                ebLogTrace(f"*** Exception Message Detail on host {_host} {exep}")
                return

        _plist = ProcessManager()
        

        for _host in _domUs:
            _p = ProcessStructure(_mInstallSuricataRPM, [_host,])
            _p.mSetMaxExecutionTime(30*60) #30 minutes timeout
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()


    def maxDistanceUpdate(self, ebox):
        _dom0s, _domUs, _ , _ = ebox.mReturnAllClusterHosts()
        _hosts = _dom0s + _domUs
        def _maxDistanceUpdate(_host):
            try:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_host)                 

            
                if _node.mFileExists("/etc/chrony.conf"):
                    _sed_cmd = node_cmd_abs_path_check(_node, "sed")                        
                    #to delete the value in file if it already exist.                        
                    _cmd = f"{_sed_cmd} -i '/maxdistance/d' /etc/chrony.conf"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return

                    
                    _cmd = f"{_sed_cmd} -i '$ a # maxdistance directive sets the maximum allowed root distance of the sources to not be rejected by the source selection' /etc/chrony.conf"
                    _node.mExecuteCmdLog(_cmd)
                    _cmd = f"{_sed_cmd} -i '$ a maxdistance 16.0' /etc/chrony.conf"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return
                    else:
                        ebLogInfo(f"Chrony conf file update successful on {_host}")

                    _systemctl_cmd = node_cmd_abs_path_check(_node, "systemctl")                        
                    _cmd = f"{_systemctl_cmd} restart chronyd"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return
                    

                if _node.mFileExists("/etc/ntp.conf"):
                    _sed_cmd = node_cmd_abs_path_check(_node, "sed")
                    #to delete the value in file if it already exist.
                    _cmd = f"{_sed_cmd} -i '/maxdist/d' /etc/ntp.conf"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return

                    _cmd = f"{_sed_cmd} -i '$ a # maxdistance directive sets the maximum allowed root distance of the sources to not be rejected by the source selection' /etc/ntp.conf"
                    _node.mExecuteCmdLog(_cmd)
                    _cmd = f"{_sed_cmd} -i '$ a tos maxdist 16' /etc/ntp.conf"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return
                    else:
                        ebLogInfo(f"ntp.conf file update successful on {_host}")

                    _service_cmd = node_cmd_abs_path_check(_node, "service")                        
                    _cmd = f"{_service_cmd} ntpd restart"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return
                  

                _node.mDisconnect()

            except Exception as ere:
                ebLogWarn('*** Exception Message Detail on host {0} {1}'.format(_host,ere))
                return


        _plist = ProcessManager()

        for _host in _hosts:
            _p = ProcessStructure(_maxDistanceUpdate, [_host,])
            _p.mSetMaxExecutionTime(30*60) #30 minutes timeout
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

    def mSeedOCIDonDomU(self,eBox,aOptions):
        if (aOptions.jsonconf is not None and 'vmClusterOcid' in aOptions.jsonconf.keys()):
            _exa_ocid = aOptions.jsonconf['vmClusterOcid']
            _seed_file_name = "/var/opt/oracle/exacc.props" 
            for _, _domu in eBox.mReturnDom0DomUPair():
                _cmd =""
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domu)
                _echo_cmd = node_cmd_abs_path_check(_node, "echo")
                if _node.mFileExists("/var/opt/oracle/exacc.props"):
                    # sed and echo can live either in /bin or /usr/bin depending on
                    # Exadata's version so just get the right path
                    _sed_cmd = node_cmd_abs_path_check(_node, "sed")
                    _cmd += f"{_sed_cmd} -i '/d' {_seed_file_name} && "
                else:
                    _cmd += f"/bin/touch {_seed_file_name} && "
                _cmd += f"{_echo_cmd} 'vmcluster_ocid={_exa_ocid}' >> {_seed_file_name}; "
                ebLogDebug(f"mSeedOCIDonDomU : command: {_cmd}")
                _, _, _err = _node.mExecuteCmd(_cmd)
                _exit_code = _node.mGetCmdExitStatus()
                if _exit_code:
                    ebLogError(f"OCID seed failed on {_domu}: {_cmd} exit code: {_exit_code} stderr: {_err}")
                else:
                    ebLogInfo(f"OCID seeded on {_domu}: file path:{_seed_file_name}")



    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, _steplist):
        ebLogInfo('*** csExaScaleComplete: Entering undoExecute')
        _ebox = aExaBoxCluCtrlObj
        _csu = csUtil()

        _exascale = ebCluExaScale(_ebox)                                                                                                                                                                         
        _json = {}
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():        
            for _dev in ['u01', 'u02']:
                ebLogInfo(f"Checking if any snapshots need to be unmounted as part of delete service or undo")
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

        if _ebox.IsZdlraProv():   
            # Update non root password (es.properties) in ZDLRA env from wallet  
            _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd')   
            _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd) 

        if _ebox.mIsExabm() and _ebox.mGetCmd() in ['vmgi_delete', 'gi_delete', 'deleteservice']:
            _csu.mDeleteVM(aExaBoxCluCtrlObj, self.step, _steplist)
            ebLogInfo('*** csExaScaleComplete: Completed undoExecute Successfully')
            return

        #
        # OSTP_POSTGI_NID step
        #

        # Acquire Remote Lock in shared mode-environment
        _ebox.mAcquireRemoteLock()

        # Remove ASM diskgroups, lock is already taken, so dom0Lock  is sent as False
        #_csu.mExecuteOEDAStep(_ebox, self.step, _steplist, aOedaStep=csConstants.OSTP_CREATE_ASM, undo=True, dom0Lock=False)

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

        _ebox.mLogStepElapsedTime(_step_time, 'Uninstalling DBCS Agent rpm')

        """
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

        _ebox.mLogStepElapsedTime(_step_time, 'OCDE NID configuration script')
        """

        _ebox.mReleaseRemoteLock()

        ebLogInfo('*** csExaScaleComplete: Completed undoExecute Successfully')

    def updDomUsToJdk11(self, aExaBoxCluCtrlObj) -> None:
        """
        Java is set as symlink with "/etc/alternatives/java"
        Such link is poiting by default to JDK8, ExaDB-xs should use JDK11
        First JDK11 java location is validated.
        Then java location for JDK is changed with update-alternatives command.
        Then javac location for JDK11 is also changed with same command.
        """
        ebox = aExaBoxCluCtrlObj
        _domUs = [domU for _, domU in ebox.mReturnDom0DomUPair()]
        for _host in _domUs:
            with connect_to_host(_host, get_gcontext(), "root") as _node:
                ebLogTrace(f"connected node detail : {_host}")                
                _java_11 = "/usr/lib/jvm/jdk-11-oracle-x64/bin/java"
                _javac_11 = "/usr/lib/jvm/jdk-11-oracle-x64/bin/javac"
                _upd_cmd = node_cmd_abs_path_check(_node, "update-alternatives", sbin=True)
                _java_cmd = "java"
                _javac_cmd = "javac"
                
                # Update syntax: update-alternatives --set {CMD} {PATH}
                if _node.mFileExists(_java_11):
                    ebLogInfo(f"JDK 11 found {_java_11}")

                    # First, change java
                    _cmd = f"{_upd_cmd} --set {_java_cmd} {_java_11}" 
                    _node.mExecuteCmdLog(_cmd)                    
                    if _node.mGetCmdExitStatus() != 0:
                        raise Exception("Java change to JDK11 failed")

                    # Second, change javac 
                    _cmd = f"{_upd_cmd} --set {_javac_cmd} {_javac_11}" 
                    _node.mExecuteCmdLog(_cmd)                    
                    if _node.mGetCmdExitStatus() != 0:
                        raise Exception("Javac change to JDK11 failed")
                else:
                    ebLogWarn(f"JDK 11 was not found. Expected: {_java_11}")


# end of file
