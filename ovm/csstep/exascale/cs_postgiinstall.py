#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/cs_postgiinstall.py /main/3 2025/02/11 16:50:19 rajsag Exp $
#
# cs_exascale_complete.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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
#      csPostGIInstall     ESTP_POSTGI_INSTALL
#
#    INTERNAL CLASSES:
#
#    MODIFIED   (MM/DD/YY)
#    rajsag      02/06/25 - Enh 37487791 - exacloud postgiinstall is running an
#                           extra unnecesary global cache images sync | improve
#                           cluster provisioning time
#    pbellary    06/21/24 - ENH 36690846 - IMPLEMENT POST-VM STEPS FOR EXASCALE SERVICE 
#    pbellary    06/06/24 - Creation
#
import time
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.log.LogMgr import ebLogInfo, ebLogTrace, ebLogError

# This class implements doExecute and undoExecute functions
# for the ESTP_POSTGI_INSTALL step of XS create service
class csPostGIInstall(CSBase):
    def __init__(self):
        self.step = 'ESTP_POSTGI_INSTALL'

    def doExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csPostGIInstall: Entering doExecute')
        _ebox = aCluCtrlObj
        _steplist = aStepList

        _ebox.mUpdateStatus('createservice step ' +self.step)


        #
        # Install / Configure any extra RPMs
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Running Extra RPMS and Config')
        _ebox.mExtraRPMsConfig(aOptions)
        _ebox.mSetupBDCSTree()
        _ebox.mLogStepElapsedTime(_step_time, 'Running Extra RPMS and Config')

        #
        # POSTGI - Run External Scripts
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Running External POSTGI Scripts')
        _ebox.mRunScript(aType='*',aWhen='post.gi_install')
        _ebox.mLogStepElapsedTime(_step_time, 'Running External Scripts')

        #
        # POSTGI - Security Hardening for OCI
        #
        if _ebox.mIsExabm():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='OCI Security Hardening')
            _ebox.mHardenOCISecurity()
            _ebox.mLogStepElapsedTime(_step_time, 'OCI Security Hardening')

        #
        # POSTGI - Secure SSH Ciphers
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Secure SSH Ciphers')
        _ebox.mSecureSSHCiphers()
        _ebox.mLogStepElapsedTime(_step_time, 'Secure SSH Ciphers')

        #
        #
        # POSTGI - Run script of fedramp
        if _ebox.mIsFedramp():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='OCI Fedramp Hardening')
            _ebox.mFedrampConfig()
            _ebox.mLogStepElapsedTime(_step_time, 'OCI Fedramp Hardening')

        #
        # POSTGI - Disable QoSM in the ATP-Dedicated GI install
        #
        if _ebox.isATP():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Disable QoSM in the ATP')
            _ebox.mDisableQoSM()
            _ebox.mLogStepElapsedTime(_step_time, 'Disable QoSM in the ATP')

        #
        # POSTGI - Enable Not Expire Password
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Disable Password Expiration in ATP')
        _ebox.mDisablePasswordExpiration()
        _ebox.mLogStepElapsedTime(_step_time, 'Disable Password Expiration in ATP')

        #
        # POSTGI - Lockdown Dom0
        #
        if _ebox.mIsDisableDom0CellLockdown():
            ebLogInfo('*** Skipping Dom0 Lockdown')
        else :
            ebLogInfo('*** Starting Dom0 Lockdown')
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Lockdown Dom0')
            _ebox.mSetupLockdown()
            _ebox.mLogStepElapsedTime(_step_time, 'Lockdown Dom0')
            ebLogInfo('*** Completed Dom0 Lockdown')

        #
        # POSTGI - Remove rsp files form tmp
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Removing Grid rsp files')
        _ebox.mRemoveRspFiles()
        _ebox.mLogStepElapsedTime(_step_time, 'Removing Grid rsp files')

        #
        # POSTGI - OCIEXACC: Reload dnsmasq service
        #
        if _ebox.mIsOciEXACC():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Restarting dnsmasq service on CPS')
            _ebox.mRestartDnsmasq()
            _ebox.mLogStepElapsedTime(_step_time, 'Restarting dnsmasq service on CPS')


        ebLogInfo('*** Exacloud Operation Successful : POST GI Install')

        ebLogTrace('csPostGIInstall: Completed doExecute Successfully')

    def undoExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csPostGIInstall: Entering undoExecute')
        _ebox = aCluCtrlObj
        _steplist = aStepList

        _ebox.mUpdateStatus('csPostGIInstall step '+ self.step)

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

        _ebox.mReleaseRemoteLock()

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
        ebLogTrace('csPostGIInstall: Completed undoExecute Successfully')