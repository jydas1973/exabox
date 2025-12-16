#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exabasedb/cs_postvminstall.py /main/1 2025/11/25 05:03:58 prsshukl Exp $
#
# cs_postvminstall.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_postvminstall.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/19/25 - Creation
#

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
        imageBom = ImageBOM(ebox)

        # 34527636: Historically ebtables where disabled during starterDB,
        # then this was moved to postginid as part of
        # Bug32439802/32459363:
        # We need to make sure now that ebtables are disabled before trying
        # to retrieve the remote passphrase for fsencryption stored in OCI SiV
        ebox.mSetupEbtablesOnDom0(aMode=False)

        #
        # POST-VM Reset SSH Host Key
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Reset Cluster SSH Keys')
        #flush the cluster hosts from known_hosts file
        ebox.mResetClusterSSHKeys(aOptions)
        ebox.mLogStepElapsedTime(_step_time, 'POSTVM INSTALL : Reset Cluster SSH Keys')

        if not imageBom.mIsSubStepExecuted(self.step, "POST_VM_PATCHING"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Post VM Patching')
            ebox.mPostVMCreatePatching(aOptions)
            ebox.mLogStepElapsedTime(_step_time, 'POST VM Patching')

        #
        # POST-VM Check sshd config in VMs for client interface - if not present add it to the list of interface to Listen
        #
        if not imageBom.mIsSubStepExecuted(self.step, "POST_SSHD_CONFIG"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Patching SSHD Config')
            ebox.mPatchSSHDConfig()
            ebox.mLogStepElapsedTime(_step_time, 'Patching SSHD Config')

        #
        # POST-VM Change Min Free Kb
        #
        if not imageBom.mIsSubStepExecuted(self.step, "CHANGE_MIN_KB"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Change Min Free Kb')
            ebox.mChangeMinFreeKb()
            ebox.mLogStepElapsedTime(_step_time, 'Change Min Free Kb')

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
        # POST-VM Update final status
        #
        ebLogInfo('*** Exacloud Operation Successful : POST CREATE VM')

        ebLogInfo("Running cavium instance metadata check.")
        if ebox.mIsExabm():
            ebox.mCheckCaviumInstanceDomUs()

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPostVMInstall: Entering undoExecute')

        _ebox = aExaBoxCluCtrlObj
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

        ebLogInfo('csPostVMInstall: Completed undoExecute Successfully')