
"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_postvminstall.py - Create Service POST VM INSTALL

FUNCTION:
   Implements the post VM install for create service execution

NOTES:
    Invoked from cs_driver.py

EXTERNAL INTERFACES: 
    csPostVMInstall         ESTP_POSTVM_INSTALL

INTERNAL CLASSES:

History:
    prsshukl  11/19/2025 - Bug 38037088 - BASE DB -> MOVE THE DO/UNDO STEPS FOR
                           BASEDB TO A NEW FILE IN CSSTEP , REMOVE CODE THAT IS
                           UNNECESSARY FOR BASEDB
    abflores  06/20/2025 - Bug 38003663 - Remove large FQDN before applying fs encryption
    gparada   08/29/2024 - 36628459 Moved mAddSecscanSshd to ebUserUtils
    ririgoye  27/03/2024 - Bug 35810419 - Added remote execute of vmrules_reconfig.py 
                           script when ExaCC shared rack is present
    akkar     15/12/2023 - Bug 36040644 - Add patchserver ip in /etc/hosts
    ririgoye  02/11/2023 - 35419881: FS encryption to be ran in parallel
    dekuckre  15/06/2021 - 32982101: Update nonroot password in ZDLRA env
    dekuckre  06/19/2019 - 29928603: Sync-up legacy and stepwise create service    
    srtata    04/19/2019 - bug 29556301: added missing pre GI step
    srtata    03/05/2019 - Creation

"""

import time
import operator
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import (ebLogError, ebLogInfo, ebLogWarn, ebLogDebug,
    ebLogVerbose, ebLogCritical)
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.cluexaccib import ExaCCIB_DomU
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.cluencryption import (isEncryptionRequested,
    batchEncryptionSetupDomU, exacc_fsencryption_requested,
    mSetLuksChannelOnDom0Exacc, validateMinImgEncryptionSupport,
    setupU01EncryptedDiskParallel)
from exabox.ovm.clunetworkvalidations import ebNetworkValidations
from exabox.ovm.userutils import ebUserUtils
from exabox.utils.node import connect_to_host
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.utils.clu_utils import ebCluUtils


# This class implements doExecute and undoExecute functions
# for the ESTP_POSTVM_INSTALL step of create service
class csPostVMInstall(CSBase):
    def __init__(self):
        self.step = 'ESTP_POSTVM_INSTALL'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPostVMInstall: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        steplist = aStepList
        ebox.mUpdateStatus('createservice step '+self.step)
        _clu_utils = ebCluUtils(ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "Post VM Install in progress", 'ESTP_POSTVM_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Post VM Install", "In Progress", _stepSpecificDetails)
        imageBom = ImageBOM(ebox)

        # 34527636: Historically ebtables where disabled during starterDB,
        # then this was moved to postginid as part of
        # Bug32439802/32459363:
        # We need to make sure now that ebtables are disabled before trying
        # to retrieve the remote passphrase for fsencryption stored in OCI SiV
        ebox.mSetupEbtablesOnDom0(aMode=False)

        #
        # Reference: bug 35834771
        # Make sure bondeth0/1 both have an IP assigned, else try to
        # force it in case ip is in standby vnic (useful to fix
        # ip in wrong vnic issues during cluster replacement)
        if ebox.mIsExabm() and not ebox.isATP():
            _net_val_mgr = ebNetworkValidations(ebox, ebox.mReturnDom0DomUPair())
            _net_val_mgr.mCheckClientBackupIPSet()

        # Ref 38003663 - Remove large FQDN before applying fs encryption
        # Remove FQDN of vms
        #
        if not imageBom.mIsSubStepExecuted(self.step, "REMOVE_FQDN_DOMU"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Remove FQDN on DomU')
            ebox.mRemoveFqdnOnDomU()
            ebox.mLogStepElapsedTime(_step_time, 'Remove FQDN on DomU')
        #
        # Filesystem Encryption in volume mounted on /u01 on non-KVM environments
        # as encryption on KVM is done through OEDA
        #
        if not imageBom.mIsSubStepExecuted(self.step, "U01_FS_ENCRYPT"):
            if isEncryptionRequested(aOptions, 'domU') and not ebox.mIsOciEXACC() and not ebox.mIsKVM():
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Filesystem Encryption on /u01')
                batchEncryptionSetupDomU(ebox, ebox.mReturnDom0DomUPair(), '/u01')
                ebox.mLogStepElapsedTime(_step_time, 'Filesystem Encryption on /u01')


            # If encryption is requested on KVM OL8, we encrypt the /u01 disk
            # This applies for both ExaCS and ExaCC
            if ebox.mIsKVM() and (isEncryptionRequested(aOptions, 'domU') or
                    exacc_fsencryption_requested(aOptions)):
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Filesystem Encryption on /u01')

                if not validateMinImgEncryptionSupport(
                        ebox,  ebox.mReturnDom0DomUPair()):

                    _err_msg = (f"Some nodes failed the "
                        f"minimum image version requirements for Encryption. ")
                    _action_msg = ("Disable encryption on the input payload or upgrade "
                        "the nodes and undo/retry")
                    ebLogCritical(_err_msg, _action_msg)
                    raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

                # If we're in ExaCC, we must create a socket to use
                # for the fs encryption passphrase communication
                if ebox.mIsOciEXACC():
                    for _dom0, _domU in ebox.mReturnDom0DomUPair():
                        mSetLuksChannelOnDom0Exacc(ebox, _dom0, _domU)

                    # Set clustersjson file for this cluster!
                    ebox.mSaveClusterDomUList()


                # Run the u01 encryption entry point
                setupU01EncryptedDiskParallel(
                        ebox, aOptions, ebox.mReturnDom0DomUPair())
                ebox.mLogStepElapsedTime(_step_time, 'Filesystem Encryption on /u01')

        if ebox.IsZdlraProv():                                                                                                                 
            # Update non root password (es.properties) in ZDLRA env from wallet
            _pswd = ebox.mGetZDLRA().mGetWalletViewEntry('passwd')
            ebox.mUpdateOedaUserPswd(ebox.mGetOedaPath(), "non-root", _pswd) 

        #
        # POST-VM Reset SSH Host Key
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Reset Cluster SSH Keys')
        #flush the cluster hosts from known_hosts file
        ebox.mResetClusterSSHKeys(aOptions)
        ebox.mLogStepElapsedTime(_step_time, 'POSTVM INSTALL : Reset Cluster SSH Keys')

        # POST-VM Add ECRA NAT IP in domU /etc/hosts
        if ebox.isBM() or  ebox.mIsOciEXACC():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Add ECRA NAT-Ip')
            ebox.mAddEcraNatOnDomU()
            ebox.mLogStepElapsedTime(_step_time, 'POSTVM INSTALL : Add ECRA NAT-Ip')

        # Patching post VM Create for all domUs
        if not imageBom.mIsSubStepExecuted(self.step, "POST_VM_PATCHING"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Post VM Patching')
            ebox.mPostVMCreatePatching(aOptions)
            ebox.mLogStepElapsedTime(_step_time, 'POST VM Patching')

        #
        # POST-VM Check Cell for write-back cache option - if not set then enable the option
        #
        if not imageBom.mIsSubStepExecuted(self.step, "POST_VM_CELL_PATCH") and not ebox.mIsExaScale():
            ebox.remote_lock.set_lock_type("cell")
            with ebox.remote_lock():
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Cell Patching (Write-Back Cache)')
                ebox.mPostVMCellPatching(aOptions)
                ebox.mLogStepElapsedTime(_step_time, 'Cell Patching (Write-Back Cache)')

                if not ebox.mCheckConfigOption('secure_ssh_all', 'False'):
                    _step_time = time.time()
                    ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Secure Cell SSH config')
                    ebox.mSecureCellsSSH()
                    ebox.mLogStepElapsedTime(_step_time, 'Secure Cell SSH config')

        #
        # POST-VM Check sshd config in VMs for client interface - if not present add it to the list of interface to Listen
        #
        if not imageBom.mIsSubStepExecuted(self.step, "POST_SSHD_CONFIG"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Patching SSHD Config')
            ebox.mPatchSSHDConfig()
            ebox.mLogStepElapsedTime(_step_time, 'Patching SSHD Config')

        #
        # POST-VM Save Cluster Configuration
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Save Cluster Configuration')
        ebox.mSaveClusterConfiguration()
        ebox.mLogStepElapsedTime(_step_time, 'Save Cluster Configuration')

        #
        # POST-VM Change Min Free Kb
        #
        if not imageBom.mIsSubStepExecuted(self.step, "CHANGE_MIN_KB"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Change Min Free Kb')
            ebox.mChangeMinFreeKb()
            ebox.mLogStepElapsedTime(_step_time, 'Change Min Free Kb')

        # Removal of ExaCC Macros file
        ebox.mRemoveExaCCMacrosVerify("DomU")

        #
        # POST-VM Secure DomU Pwd - NOTE: At this stage Oracle/Grid are not yet created so expect and disregard errors
        #
        if not imageBom.mIsSubStepExecuted(self.step, "SECURE_SSH_PASSWORD"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Secure DomU Passwords')
            ebox.mSecureDOMUPwd()
            ebox.mSecureDOMUSsh()
            if ebox.mIsOciEXACC() and ebox.isATP():
                ebUserUtils.mPushSecscanKey(ebox)
            ebUserUtils.mAddSecscanSshd(ebox)
            ebox.mLogStepElapsedTime(_step_time, 'Secure DomU Passwords')

        # OCI EXACC Secure Listeners
        if ebox.mIsOciEXACC() and not ebox.mIsKVM():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='OCIEXACC: Secure Infiniband')
            _domUs = list(map(operator.itemgetter(1),ebox.mReturnDom0DomUPair()))
            ExaCCIB_DomU(_domUs).mSecureDomUIB()
            ebox.mLogStepElapsedTime(_step_time, 'OCIEXACC: Secure Infiniband')
        elif ebox.mIsOciEXACC() and ebox.mIsKVM():
            ebLogWarn('*** mIsOciEXACC (CC) not yet supported with ROCE/KVM -- FIXME')

        #
        # POST-VM ATP Secure SCAN listener
        #
        if not imageBom.mIsSubStepExecuted(self.step, "ATP_SECURE_LISTENERS"):
            if ebox.isATP():
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='ATP: Secure Listeners')
                ebox.mATPSecureListeners()
                ebox.mLogStepElapsedTime(_step_time, 'ATP: Secure Listeners')

        #
        # POST-VM add GI and DB BPL
        #
        if not imageBom.mIsSubStepExecuted(self.step, "UPDATE_GI_DB_BLP"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Update GI and DB BPL')
            ebox.mUpdateDBGIBPL()
            ebox.mLogStepElapsedTime(_step_time, 'Update GI and DB BPL')

        #
        # POST-VM Update final status
        #
        ebLogInfo('*** Exacloud Operation Successful : POST CREATE VM')

        #
        # PRE GI Install steps
        #
        if not imageBom.mIsSubStepExecuted(self.step, "UPDATE_XML_CLUSTER_CONFIG"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Update XML Cluster Config')
            ebox.mCopyFileToClusterConfiguration(ebox.mGetConfigPath(), 'gi_install_cluster.xml')
            ebox.mLogStepElapsedTime(_step_time, 'Update XML Cluster Config')

            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Running External PREGI Scripts')
            ebox.mRunScript(aType='*',aWhen='pre.gi_install')
            ebox.mLogStepElapsedTime(_step_time, 'Running External PREGI Scripts')

        ebLogInfo("Running cavium instance metadata check.")
        if ebox.mIsExabm():
            ebox.mCheckCaviumInstanceDomUs()

        #
        # POST-VM Create/Update nat-rules file to support NAT RULES recreation via dom0_iptables_setup.sh script
        #
        ebox.mCreateNatIptablesRulesFile()

        # In case we're dealing with an ExaCC non-prod environment, set the IP table rules correctly
        if ebox.mCheckConfigOption("exacc_nonprod_shared_rack", "True"):
            # Get IPs and ports
            _admin_services = ebox.mGetOciExaCCServicesSetup()
            _fwd_ip = _admin_services.get("forwardproxy", {}).get("ip")
            _fwd_port = _admin_services.get("forwardproxy", {}).get("port")
            _patch_ip = _admin_services.get("fileserver", {}).get("ip")
            _patch_port = _admin_services.get("fileserver", {}).get("port")
            # Run script on each Dom0
            ebLogInfo("Reconfiguring IP rules since this is an ExaCC shared rack.")
            _script_loc = "/opt/oci/exacc/exacloud/scripts/network/vmrules_reconfig.py"
            _target_loc = "/tmp/vmrules_reconfig.py"
            for _dom0, _domU in ebox.mReturnDom0DomUPair():
                with connect_to_host(_dom0, get_gcontext()) as _node:
                    ebLogInfo(f"Reconfiguring IP rules for dom0: {_dom0}")
                    # Check if Python3 exists
                    _cmd = "/bin/python3 -V"
                    _node.mExecuteCmd(_cmd)
                    _rc = _node.mGetCmdExitStatus() 
                    if _rc != 0:
                        ebLogInfo(f"Python3 not found in dom0: {_dom0}. Skipping reconfiguration.")
                        break
                    # Copy file and set permissions
                    _node.mCopyFile(_script_loc, _target_loc)
                    _cmd = f"/bin/chmod +x {_target_loc}"
                    _node.mExecuteCmd(_cmd)
                    ebLogInfo("Copied script to dom0.")
                    # Run script with correct params
                    _cmd = f"/bin/python3 {_target_loc} -n {_domU}"
                    _cmd += f" -fip {_fwd_ip} -pip {_patch_ip} -fp {_fwd_port} -pp {_patch_port}"
                    ebLogInfo(f"Running command: {_cmd}")
                    _, _, _e = _node.mExecuteCmd(_cmd)
                    _rc = _node.mGetCmdExitStatus() 
                    # If script fails to run, attempt to rollback changes first, then raise Error
                    if _rc != 0:
                        _err_msg = f"Script ended with exit code: {_rc}. Rolling back changes. (Error: {_e})"
                        ebLogError(_err_msg)
                        _cmd = f"/bin/python3 {_script_loc} -r"
                        _, _, _e = _node.mExecuteCmd(_cmd)
                        _rc = _node.mGetCmdExitStatus()
                        if _rc != 0:
                            ebLogError(f"Could not rollback changes due to error: {_e}")
                        raise ExacloudRuntimeError(0x407, 0xA, _err_msg)
                ebLogInfo(f"Reconfiguration successful on dom0: {_dom0}")

        ebLogInfo('csPostVMInstall: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "Post VM Install Completed", 'ESTP_POSTVM_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Post VM Install", "Done", _stepSpecificDetails)

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPostVMInstall: Entering undoExecute')

        _ebox = aExaBoxCluCtrlObj
        _step_list = aStepList
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'ONGOING', "Undo Post VM Install in progress", 'ESTP_POSTVM_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Undo Post VM Install", "In Progress", _stepSpecificDetails)
        #
        # PREVM - Run External Scripts
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _step_list, aComment='Running External PREVM Scripts')
        _ebox.mRunScript(aType='*',aWhen='pre.vm_delete')
        _ebox.mLogStepElapsedTime(_step_time, 'Running External PREVM Scripts')
 
        #
        # PREVM - Shred VM Images (Sytem, User, DB/GI bits)
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _step_list,
                                 aComment='VM Image shredding in progress (this operation can take a long time')
        _ebox.mVMImagesShredding(aOptions)
        _ebox.mLogStepElapsedTime(_step_time, 'VM Image shredding')

        _csu = csUtil()
        if _ebox.mGetCmd() not in ['vmgi_delete', 'vm_delete', 'gi_delete', 'deleteservice']:
            _csu.mPreVMDeleteCreatePatching(_ebox, aOptions)

        #TO-DO Need to validate whether this step is required or  not
        #_csu.mPreVMDeleteCellPatching(_ebox, aOptions)
        #_csu.mUndoSecureDOMUPwd(_ebox, aOptions)
        #_csu.mUndoSecureDOMUSsh(_ebox, aOptions)
        _csu.mUndoCopyFileToClusterConfiguration(_ebox, 'gi_install_cluster.xml')
        ebLogInfo('csPostVMInstall: Completed undoExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'DONE', "Undo Post VM Install Completed", 'ESTP_POSTVM_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Undo Post VM Install", "Done", _stepSpecificDetails)


        
        
