
"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_postgiinstall.py - Create Service POST GI INSTALL

FUNCTION:
   Implements the post GI install for create service execution

NOTES:
    Invoked from cs_driver.py

EXTERNAL INTERFACES: 
    csPostGIInstall         ESTP_POSTGI_INSTALL

INTERNAL CLASSES:

History:
    dekuckre  15/06/2021 - 32982101: Update nonroot password in ZDLRA env
    srtata    03/05/2019 - Creation
    gshiva    04/23/2019 - Integrated undo step.
    araghave  08/19/2019 - Bug - 30190704 create service 
              fails with object has no attribute 
              mcreatepluginsdir error
    alsepulv  03/16/21   - Enh 32619413: remove any code related to Higgs
"""

import time
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.cluresmgr import ebCluResManager
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.utils.clu_utils import ebCluUtils

# This class implements doExecute and undoExecute functions
# for the ESTP_POSTGI_INSTALL step of create service
class csPostGIInstall(CSBase):
    def __init__(self):
        self.step = 'ESTP_POSTGI_INSTALL'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        ebLogInfo('csPostGIInstall: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        ebox.mUpdateStatus('createservice step '+self.step)
        _clu_utils = ebCluUtils(ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "Post GI Install in progress", 'ESTP_POSTGI_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Post GI Install", "In Progress", _stepSpecificDetails)


        if ebox.IsZdlraProv():
            # Update non root password (es.properties) in ZDLRA env from wallet
            _pswd = ebox.mGetZDLRA().mGetWalletViewEntry('passwd')
            ebox.mUpdateOedaUserPswd(ebox.mGetOedaPath(), "non-root", _pswd)

        if not ebox.mIsExaScale():
            #
            # Add ACFS GridDisks only if they have not been created before (e.g. no delete/overwrite)
            #
            ebox.mAcquireRemoteLock()
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Create ACFS Grid Disks')
            ebox.mGetStorage().mCreateACFSGridDisks()
            ebox.mLogStepElapsedTime(_step_time, 'Create ACFS Grid Disks')
            ebox.mReleaseRemoteLock()

        #
        # Install / Configure any extra RPMs
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Running Extra RPMS and Config')
        ebox.mExtraRPMsConfig(aOptions)
        ebox.mSetupBDCSTree()
        ebox.mLogStepElapsedTime(_step_time, 'Running Extra RPMS and Config')

        #
        # POSTGI - Run External Scripts
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Running External POSTGI Scripts')
        ebox.mRunScript(aType='*',aWhen='post.gi_install')
        ebox.mLogStepElapsedTime(_step_time, 'Running External Scripts')

        #
        # POSTGI - Set IORM Objective to auto
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Setting IORM Objective to auto')
        _ioptions = aOptions
        _ioptions.jsonconf['objective'] = "auto"
        _ioptions.resmanage = "setobj"
        _iormobj = ebCluResManager(ebox, _ioptions)
        _iormobj.mClusterIorm(_ioptions)
        ebox.mLogStepElapsedTime(_step_time, 'Setting IORM Objective to auto')

        #
        # POSTGI - Security Hardening for OCI
        #
        if ebox.mIsExabm():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='OCI Security Hardening')
            ebox.mHardenOCISecurity()
            ebox.mLogStepElapsedTime(_step_time, 'OCI Security Hardening')

        #
        # POSTGI - Secure SSH Ciphers
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Secure SSH Ciphers')
        ebox.mSecureSSHCiphers()
        ebox.mLogStepElapsedTime(_step_time, 'Secure SSH Ciphers')

        #
        #
        # POSTGI - Run script of fedramp
        if ebox.mIsFedramp():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='OCI Fedramp Hardening')
            ebox.mFedrampConfig()
            ebox.mLogStepElapsedTime(_step_time, 'OCI Fedramp Hardening')

        #
        # POSTGI - Disable QoSM in the ATP-Dedicated GI install
        #
        if ebox.isATP():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Disable QoSM in the ATP')
            ebox.mDisableQoSM()
            ebox.mLogStepElapsedTime(_step_time, 'Disable QoSM in the ATP')

        #
        # POSTGI - Enable Not Expire Password
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Disable Password Expiration in ATP')
        ebox.mDisablePasswordExpiration()
        ebox.mLogStepElapsedTime(_step_time, 'Disable Password Expiration in ATP')

        #
        # POSTGI - Lockdown Dom0/Cells
        #
        if ebox.mIsDisableDom0CellLockdown():
            ebLogInfo('*** Skipping Dom0/Cells Lockdown')
        else :
            ebLogInfo('*** Starting Dom0/Cells Lockdown')
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Lockdown Dom0/Cells')
            ebox.mSetupLockdown()
            ebox.mLogStepElapsedTime(_step_time, 'Lockdown Dom0/Cells')
            ebLogInfo('*** Completed Dom0/Cells Lockdown')

        #
        # POSTGI - Remove rsp files form tmp
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Removing Grid rsp files')
        ebox.mRemoveRspFiles()
        ebox.mLogStepElapsedTime(_step_time, 'Removing Grid rsp files')

        #
        # POSTGI - OCIEXACC: Reload dnsmasq service
        #
        if ebox.mIsOciEXACC():
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Restarting dnsmasq service on CPS')
            ebox.mRestartDnsmasq()
            ebox.mLogStepElapsedTime(_step_time, 'Restarting dnsmasq service on CPS')


        ebLogInfo('*** Exacloud Operation Successful : POST GI Install')
        ebLogInfo('csPostGIInstall: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "Post GI Install Completed", 'ESTP_POSTGI_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Post GI Install", "Done", _stepSpecificDetails)

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, _steplist):
        ebLogInfo('***  csPostGIInstall: Entering undoExecute')
        _ebox = aExaBoxCluCtrlObj
        _ebox.mUpdateStatus('csPostGIInstall step '+ self.step)
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'ONGOING', "Undo Post GI Install in progress", 'ESTP_POSTGI_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Undo Post GI Install", "In Progress", _stepSpecificDetails)

        #
        # PRE-GI - Run External Scripts
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Running External PREGI Scripts')
        _ebox.mRunScript(aType='*',aWhen='pre.gi_delete')
        _ebox.mLogStepElapsedTime(_step_time, 'Running External PREGI Scripts')

        # Acquire Remote Lock in shared mode-environment
        _ebox.mAcquireRemoteLock()

        #
        # POSTGI - Run External Scripts
        #
        ebLogInfo('csPostGIInstall: ' + 'Running External POSTGI Scripts')
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Running External POSTGI Scripts')
        _ebox.mRunScript(aType='*',aWhen='post.gi_delete')
        _ebox.mLogStepElapsedTime(_step_time, 'Running External Scripts')

        #
        # POSTGI - Delete ACFS Grid Disks
        #
        ebLogInfo('csPostGIInstall: ' + 'Running Delete ACFS Grid Disks')
        try:
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Delete ACFS Grid Disks')
            _ebox.mGetStorage().mCreateACFSGridDisks(aCreate=False)
            _ebox.mLogStepElapsedTime(_step_time, 'Delete ACFS Grid Disks')
        except:
            ebLogWarn('*** Delete ACFS Grid Disk did not completed successully')

        _ebox.mReleaseRemoteLock()

        if not _ebox.SharedEnv():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Resetting IORM DB Plan')
            _ioptions = aOptions
            _ioptions.resmanage = "resetdbplan"
            _iormobj = ebCluResManager(_ebox, _ioptions)
            _iormobj.mClusterIorm(_ioptions)
            _ebox.mLogStepElapsedTime(_step_time, 'Resetting IORM DB Plan')

        if _ebox.mIsExabm() and _ebox.mGetCmd() in ['vmgi_delete', 'gi_delete', 'deleteservice']:
            _csu = csUtil()
            _csu.mDeleteVM(aExaBoxCluCtrlObj, self.step, _steplist)
            ebLogInfo('*** csPostGIInstall: Completed undoExecute Successfully')
            return

        # BUG 28641550 - only for exabm
        if _ebox.mGetCmd() in ['vmgi_delete', 'gi_delete', 'deleteservice'] and _ebox.mIsExabm():
            _ebox.mRemoveDNS()

        # TODO In Sanity Testing  the below methods are getting blocked. 
        # To validate this during integration testing.
        try:
            ebLogInfo('*** csPostGIInstall:  ' + 'Remove Extra RPMs')
            _ebox.mExtraRPMsConfig(aOptions, aUndo=True)
        except:
            ebLogError("Error while uninstalling Extra RPMs")

        ebLogInfo('***  csPostGIInstall: Completed undoExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'DONE', "Undo Post GI Install Completed", 'ESTP_POSTGI_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Undo Post GI Install", "Done", _stepSpecificDetails)

