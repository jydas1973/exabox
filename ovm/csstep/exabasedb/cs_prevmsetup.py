#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exabasedb/cs_prevmsetup.py /main/2 2025/12/01 09:38:52 jesandov Exp $
#
# cs_prevmsetup.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_prevmsetup.py - <one-line expansion of the name>
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

import os
import time
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogCritical
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.atp import AtpAddiptables2Dom0
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.ovm.cluresmgr import ebCluResManager
from exabox.ovm.cluexaccib import ExaCCIB_CPS
from exabox.ovm.cluexaccatp_filtering import ebExaCCAtpFiltering
from exabox.ovm.cluexaccroce import ExaCCRoCE_CPS
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.ovm.clumisc import mChangeOpCtlAudit
import exabox.ovm.clubonding as clubonding
from exabox.ovm.cluencryption import (isEncryptionRequested, createAndPushRemotePassphraseSetup,
        deleteRemotePassphraseSetup, ensureSystemFirstBootEncryptedExistsParallelSetup,
        useLocalPassphrase, deleteOEDAKeyApiFromDom0, createEncryptionMarkerFileForVM,
        deleteEncryptionMarkerFileForVM, exacc_fsencryption_requested, exacc_save_fsencryption_passphrase,
        exacc_del_fsencryption_passphrase)
from exabox.utils.node import connect_to_host, node_update_key_val_file
from exabox.ovm.csstep.exascale.exascaleutils import ebExascaleUtils
from exabox.ovm.vmbackup import ebCluManageVMBackup
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.ovm.clustorage import ebCluManageStorage
from exabox.ovm.cluhostaccesscontrol import addRoceNetworkHostAccessControl
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.utils.clu_utils import ebCluUtils

# This class implements doExecute and undoExecute functions
# for the ESTP_PREVM_SETUP step of create service
class csPreVMSetup(CSBase):
    def __init__(self):
        self.step = 'ESTP_PREVM_SETUP'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPreVMSetup: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        steplist = aStepList
        _csu = csUtil()
        imageBom = ImageBOM(ebox)

        ebox.mUpdateStatus('createservice step ESTP_PREVM_SETUP')

        # Grab lock
        ebox.mAcquireRemoteLock()

        #
        # PRE-VM iprules setup
        #
        if not imageBom.mIsSubStepExecuted(self.step, "SET_IPRULES"):

            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist,
                aComment='Setup IPRules (iptables/nftables) on Dom0')

            if not ebox.mIsKVM():

                ebox.mCleanupEbtablesOnDom0()
                # Bug 35966373: Ebtables are currently set during PREVM_SETUP, and
                # removed during POSTVM_INSTALL. We're disabling this through an
                # 'exabox.conf' property and we will remove this code in the coming
                # future
                ebox.mSetupEbtablesOnDom0()

            # Set default IPrules in the Dom0s
            ebox.mHandlerSetupNATIptablesOnDom0()

            # Logic for X5/X6 and IB based systems
            if not ebox.mEnvTarget() and ebox.mGetExadataDom0Model() in ['X5', 'X6']:
                self.mChangeForwardAccept(ebox)
            if not ebox.mIsKVM() and not ebox.mIsOciEXACC():
                self.mCopyVifFiles(ebox)

            ## BUG 28598302
            if ebox.isATP() and ebox.mIsExabm() and ebox.mCheckClusterNetworkType():
               AtpAddiptables2Dom0(None, ebox.mGetATP(), ebox.mReturnDom0DomUPair(), ebox.mGetMachines(), ebox.mGetNetworks()).mExecute()
            # Set IPrules in the Dom0s sepcific to the VMs we'll create
            if ebox.mIsExabm():
                _nftDom0s = ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL8"])
                if _nftDom0s:
                    ebIpTablesRoCE.mSetupSecurityRulesExaBM(
                        ebox, aOptions.jsonconf, aDom0s=_nftDom0s)

            ebox.mLogStepElapsedTime(_step_time,
                'Setup IPRules (iptables/nftables) on Dom0')

        # Releasing remote lock
        ebox.mReleaseRemoteLock()

        #
        # Check if time format property is included in dom0s and cells' .bashrc file
        #
        if not imageBom.mIsSubStepExecuted(self.step, "HISTTIMEFORMAT"):
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist,
                aComment='Enable HISTTIMEFORMAT in Infra nodes')

            _dom0s, _, _cells, _ = ebox.mReturnAllClusterHosts()
            if ebox.mIsXS():
                _cells = []
            _hostnames = _dom0s + _cells

            _filepath = os.path.expanduser("/root/.bashrc")
            _keyValue, _sep = {"HISTTIMEFORMAT": '"%d/%m/%y %T"'}, "="

            ebLogInfo(f'Looking for property HISTTIMEFORMAT in all nodes')
            for _hostname in _hostnames:
                with connect_to_host(_hostname, get_gcontext()) as _host:
                    try:
                        node_update_key_val_file(_host, _filepath, _keyValue, sep=_sep, ignore=True)
                    except Exception as exp:
                        ebLogError(f"Failed to look for HISTTIMEFORMAT property due to the following exception: ")
                        ebLogError(str(exp))
            ebox.mLogStepElapsedTime(_step_time,
                'Enable HISTTIMEFORMAT in Infra nodes')

        #
        # PRE-VM reclaim dom0 local disk space from unused LVs
        #
        if not imageBom.mIsSubStepExecuted(self.step, "DOM0_SETUP"):

            # PRE_VM logrotation setup for log files under
            # '/opt/exacloud/clusters/operations'
            ebox.mEnableLogRotationOnDom0()
            ebox.mRestoreMissingMountPoints()
            ebox.mConfigureArp()
            self.mRpmCheck(ebox)

            if not ebox.mIsKVM():
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist,
                    aComment='Running reclaimdisks.sh -extend-vgexadb')
                ebox.mRunReclaimdisks('extend-vgexadb')
                ebox.mLogStepElapsedTime(_step_time,
                    'PREVM SETUP : reclaim disks space from unused LVs on Dom0')

            else:
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Resize logical volume EXAVMIMAGES')
                ebox.mResizeExaVMImages()
                ebox.mLogStepElapsedTime(_step_time, 'PREVM INSTALL : resize EXAVMIMAGES from unused LVs on Dom0')

        ebLogInfo('csPreVMSetup: Completed doExecute Successfully')

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPreVMSetup: Entering undoExecute')

        self.mPostVMDeleteSteps(aExaBoxCluCtrlObj, aOptions, aStepList)
        ebLogInfo('csPreVMSetup: Completed undoExecute Successfully')
