#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/cs_postvminstall.py /main/6 2024/10/29 15:18:54 ririgoye Exp $
#
# cs_exascale_complete.py
#
# Copyright (c) 2021, 2024, Oracle and/or its affiliates.
#
#    NAME
#      cs_postgiinstall.py - XS Create Service POST GI INSTALL
# 
#   FUNCTION:
#      Implements the post GI install for XS create service execution 
#
#    NOTES
#      Invoked from cs_driver.py
#
#    EXTERNAL INTERFACES:
#      csPostVMInstall     ESTP_POSTVM_INSTALL
#
#    INTERNAL CLASSES:
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    10/24/24 - Bug 37163074 - REQUEST TO TEMPORARILY REMOVE
#                           VMRULE_RECONFIG SCRIPT EXECUTION
#    jfsaldan    07/19/24 - Enh 36711025 - EXACLOUD OL8 FS ENCRYPTION -EXACLOUD
#                           TO SUPPORT CREATING U01 ENCRYPTED ON THE DOMU
#    pbellary    06/21/24 - ENH 36690846 - IMPLEMENT POST-VM STEPS FOR EXASCALE SERVICE 
#    pbellary    06/06/24 - Creation
#
import time
import operator
from exabox.core.Context import get_gcontext
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.utils.node import connect_to_host
from exabox.ovm.cluexaccib import ExaCCIB_DomU
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogCritical, ebLogTrace
from exabox.ovm.clunetworkvalidations import ebNetworkValidations
from exabox.ovm.cluencryption import (isEncryptionRequested,
    batchEncryptionSetupDomU, exacc_fsencryption_requested,
    mSetLuksChannelOnDom0Exacc, validateMinImgEncryptionSupport,
    setupU01EncryptedDiskParallel)
from exabox.ovm.userutils import ebUserUtils


# This class implements doExecute and undoExecute functions
# for the ESTP_POSTVM_INSTALL step of create service
class csPostVMInstall(CSBase):
    def __init__(self):
        self.step = 'ESTP_POSTVM_INSTALL'

    def doExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPostVMInstall: Entering doExecute')
        _ebox = aCluCtrlObj
        _steplist = aStepList
        _ebox.mUpdateStatus('createservice step '+self.step)

        # 34527636: Historically ebtables where disabled during starterDB,
        # then this was moved to postginid as part of
        # Bug32439802/32459363:
        # We need to make sure now that ebtables are disabled before trying
        # to retrieve the remote passphrase for fsencryption stored in OCI SiV
        _ebox.mSetupEbtablesOnDom0(aMode=False)

        #
        # Reference: bug 35834771
        # Make sure bondeth0/1 both have an IP assigned, else try to
        # force it in case ip is in standby vnic (useful to fix
        # ip in wrong vnic issues during cluster replacement)
        if _ebox.mIsExabm() and not _ebox.isATP():
            _net_val_mgr = ebNetworkValidations(_ebox, _ebox.mReturnDom0DomUPair())
            _net_val_mgr.mCheckClientBackupIPSet()

        #
        # Filesystem Encryption in volume mounted on /u01 on non-KVM environments
        # as encryption on KVM is done through OEDA
        #
        if isEncryptionRequested(aOptions, 'domU') and not _ebox.mIsOciEXACC() and not _ebox.mIsKVM():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Filesystem Encryption on /u01')
            batchEncryptionSetupDomU(_ebox, _ebox.mReturnDom0DomUPair(), '/u01')
            _ebox.mLogStepElapsedTime(_step_time, 'Filesystem Encryption on /u01')

        # If encryption is requested on KVM OL8, we encrypt the /u01 disk
        # This applies for both ExaCS and ExaCC
        _exascale_encryption = False
        if str(get_gcontext().mGetConfigOptions().get(
            "fs_encryption_exascale", "False")).upper() == "TRUE":
            _exascale_encryption = True
            ebLogTrace(f"Detected fs encryption for exascale enabled")

        if (_ebox.mIsKVM() and (isEncryptionRequested(aOptions, 'domU') or
                exacc_fsencryption_requested(aOptions)) and _exascale_encryption):
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='KVM Filesystem Encryption on /u01')

            if not validateMinImgEncryptionSupport(
                    _ebox,  _ebox.mReturnDom0DomUPair()):

                _err_msg = (f"Some nodes failed the "
                    f"minimum image version requirements for Encryption. ")
                _action_msg = ("Disable encryption on the input payload or upgrade "
                    "the nodes and undo/retry")
                ebLogCritical(_err_msg, _action_msg)
                raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

            # If we're in ExaCC, we must create a socket to use
            # for the fs encryption passphrase communication
            if _ebox.mIsOciEXACC():
                for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                    mSetLuksChannelOnDom0Exacc(_ebox, _dom0, _domU)

            # Run the u01 encryption entry point
            setupU01EncryptedDiskParallel(
                    _ebox, aOptions, _ebox.mReturnDom0DomUPair())
            _ebox.mLogStepElapsedTime(_step_time, 'KVM Filesystem Encryption on /u01')

        #
        # POST-VM Reset SSH Host Key
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Reset Cluster SSH Keys')
        #flush the cluster hosts from known_hosts file
        _ebox.mResetClusterSSHKeys(aOptions)
        _ebox.mLogStepElapsedTime(_step_time, 'POSTVM INSTALL : Reset Cluster SSH Keys')

        # POST-VM Add ECRA NAT IP in domU /etc/hosts
        if _ebox.isBM() or  _ebox.mIsOciEXACC():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Add ECRA NAT-Ip')
            _ebox.mAddEcraNatOnDomU()
            _ebox.mLogStepElapsedTime(_step_time, 'POSTVM INSTALL : Add ECRA NAT-Ip')

        # Patching post VM Create for all domUs
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Post VM Patching')
        _ebox.mPostVMCreatePatching(aOptions)
        _ebox.mLogStepElapsedTime(_step_time, 'POST VM Patching')

        #
        # POST-VM Dom0 additional updates to network configuration when needed
        #
        _ebox.remote_lock.set_lock_type("dom0")
        with _ebox.remote_lock():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Update Dom0 Network Config')
            _ebox.mDom0PostVMCreateNetConfig(aMode=False)       # POST CSVC
            _ebox.mLogStepElapsedTime(_step_time, 'Update Dom0 Network Config')

        #
        # POST-VM Check sshd config in VMs for client interface - if not present add it to the list of interface to Listen
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Patching SSHD Config')
        _ebox.mPatchSSHDConfig()
        _ebox.mLogStepElapsedTime(_step_time, 'Patching SSHD Config')

        #
        # POST-VM Save Cluster Configuration
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Save Cluster Configuration')
        _ebox.mSaveClusterConfiguration()
        _ebox.mLogStepElapsedTime(_step_time, 'Save Cluster Configuration')

        #
        # POST-VM Change Min Free Kb
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Change Min Free Kb')
        _ebox.mChangeMinFreeKb()
        _ebox.mLogStepElapsedTime(_step_time, 'Change Min Free Kb')

        # Removal of ExaCC Macros file
        _ebox.mRemoveExaCCMacrosVerify("DomU")

        #
        # POST-VM Secure DomU Pwd - NOTE: At this stage Oracle/Grid are not yet created so expect and disregard errors
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Secure DomU Passwords')
        _ebox.mSecureDOMUPwd()
        _ebox.mSecureDOMUSsh()
        if _ebox.mIsOciEXACC() and _ebox.isATP():
            ebUserUtils.mPushSecscanKey(_ebox)
        ebUserUtils.mAddSecscanSshd(_ebox)
        _ebox.mLogStepElapsedTime(_step_time, 'Secure DomU Passwords')

        # OCI EXACC Secure Listeners
        if _ebox.mIsOciEXACC() and not _ebox.mIsKVM():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='OCIEXACC: Secure Infiniband')
            _domUs = list(map(operator.itemgetter(1),_ebox.mReturnDom0DomUPair()))
            ExaCCIB_DomU(_domUs).mSecureDomUIB()
            _ebox.mLogStepElapsedTime(_step_time, 'OCIEXACC: Secure Infiniband')
        elif _ebox.mIsOciEXACC() and _ebox.mIsKVM():
            ebLogWarn('*** mIsOciEXACC (CC) not yet supported with ROCE/KVM -- FIXME')

        #
        # POST-VM ATP Secure SCAN listener
        #
        if _ebox.isATP():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='ATP: Secure Listeners')
            _ebox.mATPSecureListeners()
            _ebox.mLogStepElapsedTime(_step_time, 'ATP: Secure Listeners')

        #
        # POST-VM add GI and DB BPL
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Update GI and DB BPL')
        _ebox.mUpdateDBGIBPL()
        _ebox.mLogStepElapsedTime(_step_time, 'Update GI and DB BPL')

        #
        # POST-VM Update final status
        #
        ebLogInfo('*** Exacloud Operation Successful : POST CREATE VM')

        #
        # PRE GI Install steps
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Update XML Cluster Config')
        _ebox.mCopyFileToClusterConfiguration(_ebox.mGetConfigPath(), 'gi_install_cluster.xml')
        _ebox.mLogStepElapsedTime(_step_time, 'Update XML Cluster Config')

        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Running External PREGI Scripts')
        _ebox.mRunScript(aType='*',aWhen='pre.gi_install')
        _ebox.mLogStepElapsedTime(_step_time, 'Running External PREGI Scripts')

        ebLogInfo("Running cavium instance metadata check.")
        if _ebox.mIsExabm():
            _ebox.mCheckCaviumInstanceDomUs()

        #
        # POST-VM Create/Update nat-rules file to support NAT RULES recreation via dom0_iptables_setup.sh script
        #
        _ebox.mCreateNatIptablesRulesFile()

        # In case we're dealing with an ExaCC non-prod environment, set the IP table rules correctly
        if _ebox.mCheckConfigOption("exacc_nonprod_shared_rack", "True"):
            # Get IPs and ports
            _admin_services = _ebox.mGetOciExaCCServicesSetup()
            _fwd_ip = _admin_services.get("forwardproxy", {}).get("ip")
            _fwd_port = _admin_services.get("forwardproxy", {}).get("port")
            _patch_ip = _admin_services.get("fileserver", {}).get("ip")
            _patch_port = _admin_services.get("fileserver", {}).get("port")
            # Run script on each Dom0
            ebLogInfo("Reconfiguring IP rules since this is an ExaCC shared rack.")
            _script_loc = "/opt/oci/exacc/exacloud/scripts/network/vmrules_reconfig.py"
            _target_loc = "/tmp/vmrules_reconfig.py"
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                with connect_to_host(_dom0, get_gcontext()) as _node:
                    ebLogInfo(f"Reconfiguring IP rules for dom0: {_dom0}")
                    # Copy file and set permissions
                    _node.mCopyFile(_script_loc, _target_loc)
                    _cmd = f"/bin/chmod +x {_target_loc}"
                    _node.mExecuteCmd(_cmd)
                    ebLogInfo("Copied script to dom0.")
                    # Run script with correct params
                    _cmd = f"/bin/python {_target_loc} -n {_domU}"
                    _cmd += f" -fip {_fwd_ip} -pip {_patch_ip} -fp {_fwd_port} -pp {_patch_port}"
                    ebLogInfo(f"Running command: {_cmd}")
                    _, _, _e = _node.mExecuteCmd(_cmd)
                    _rc = _node.mGetCmdExitStatus() 
                    # If script fails to run, attempt to rollback changes first, then raise Error
                    if _rc != 0:
                        _err_msg = f"Script ended with exit code: {_rc}. Rolling back changes. (Error: {_e})"
                        ebLogError(_err_msg)
                        _cmd = f"/bin/python {_script_loc} -r"
                        _, _, _e = _node.mExecuteCmd(_cmd)
                        _rc = _node.mGetCmdExitStatus()
                        if _rc != 0:
                            ebLogError(f"Could not rollback changes due to error: {_e}")
                        raise ExacloudRuntimeError(0x407, 0xA, _err_msg)
            ebLogInfo(f"Reconfiguration successful on dom0: {_dom0}")

        ebLogInfo('csPostVMInstall: Completed doExecute Successfully')

    def undoExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPostVMInstall: Entering undoExecute')

        _ebox = aCluCtrlObj
        _step_list = aStepList
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

        _csu.mUndoCopyFileToClusterConfiguration(_ebox, 'gi_install_cluster.xml')
        ebLogInfo('csPostVMInstall: Completed undoExecute Successfully')
