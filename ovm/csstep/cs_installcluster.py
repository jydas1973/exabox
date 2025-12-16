"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_installcluster.py - Create Service INSTALL CLUSTER

FUNCTION:
    Implements the Install and Init Cluster steps for create service execution 

NOTES:
    Invoked from cs_driver.py 

EXTERNAL INTERFACES: 
    csInstallCluster ESTP_INSTALL_CLUSTER

INTERNAL CLASSES:

History:
    avimonda  10/21/2025 - Bug 38442915: Remove maxDistanceUpdate function call to place it in CreateVM step
    pbellary  06/06/2025 - Enh 38035467 - EXASCALE: EXACLOUD TO PROVIDE ACFS FILE SYSTEM SIZES IN SYNCH CALL
    anudatta  11/22/2024 - Enh 36553996 - clufy report before add node root.script
    gparada   11/05/2024 - 37009693: Validate rsp exists and copy afterwards.
    joysjose  09/01/2024 - 36988806: Invoke maxDistanceUpdate function before install cluster step.
    dekuckre  05/02/2024 - 36572947: Remove fqdn in create user step and not in install-cluster step.
    ndesanto  10/24/2023 - 35942375: Copy rsp file for vmgi_reconfig
    ririgoye  02/11/2023 - 35419881: FS encryption to be ran in parallel
    dekuckre  10/09/2023 - 3588162: Store rsp file in /tmp and not in scripts dir
    dekuckre  07/21/2023 - 35629339: Fix copying of rsp file.
    dekuckre  20/02/2023 - 34851263: Store rsp file in exacloud/scripts
    joysjose  04/10/2023 - 35264867: Correction on RDS ping cellinit IP retrieval.
    dekuckre  15/06/2021 - 32982101: Update nonroot password in es.properties in ZDLRA env 
    seha      07/20/2019 - 30059351: Change IB syslog format
    dekuckre  06/04/2019 - 29782829: Undo step7 as part of undo step8,9
    srtata    04/23/2019 - 29556301: implement doExecute
    srtata    03/05/2019 - Creation

"""
import ast
import time
import operator
import os

from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.ovm.vmcontrol import exaBoxOVMCtrl
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.cluencryption import (isEncryptionRequested,
    batchEncryptionSetupDomU, exacc_fsencryption_requested,
    cleanupU02EncryptedDisk)
from exabox.utils.node import connect_to_host, node_exec_cmd, node_cmd_abs_path_check
from exabox.ovm.utils.clu_utils import ebCluUtils

# This class implements doExecute and undoExecute functions
# for the ESTP_INSTALL_CLUSTER step of create service
# This class primarily invokes OEDA do/undo Install and Init Cluster steps
class csInstallCluster(CSBase):
    def __init__(self):
        self.step = 'ESTP_INSTALL_CLUSTER'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        ebLogInfo('csInstallCluster: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        csu = csUtil()
        _csConstants = csu.mGetConstants(ebox, aOptions)
        ebox.mUpdateStatus('createservice step '+self.step)
        _clu_utils = ebCluUtils(ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "Install Cluster in progress", 'ESTP_INSTALL_CLUSTER')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Install Cluster", "In Progress", _stepSpecificDetails)

        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Copy/Update images on Dom0')
        ebox.mUpdateDepFiles()
        ebox.mLogStepElapsedTime(_step_time, 'INSTALL CLUSTER : Copy/Update images on Dom0')

        #bug-34522121 (precheck for network reachability between domu and cells)
        #rds-ping from domUs to cells, cells to domUs and among cells on storage interface on stre0/stre1 or re0/re1 interface for KVM and stib0/stib1 interface from XEN systems.
        #rds-ping between domUs to check the cluster interface clre0/clre1 for KVM and clib0/clib1 for XEN systems.
        # A new parameter 'exacloud_precheck_install_cluster' is added in exabox.conf, which is by default set to "True". In future, if there are issues, this parameter is configurable.
        # Note: rdsPingDriver() also covers the fix for the bug 34591032 - INCLUDE A CHECK FOR CLRE0 AND CLRE1 AS PART OF HEALTHCHECK TO BE RUN BEFORE CRS INSTALL.
        # So if disabling this function call, please consider the fix for 34591032 seperately.
        _val = ebox.mCheckConfigOption("exacloud_precheck_install_cluster", "True")
        if (_val):
            self.rdsPingDriver(aExaBoxCluCtrlObj)

        if ebox.IsZdlraProv():                                                                                                                 
            # Update non root password (es.properties) in ZDLRA env from wallet                                                                
            _pswd = ebox.mGetZDLRA().mGetWalletViewEntry('passwd')                                                                             
            ebox.mUpdateOedaUserPswd(ebox.mGetOedaPath(), "non-root", _pswd) 
            
        # Create grid disks, If they are not already created for the cluster.
        if not ebox.mGetStorage().mCheckGridDisks():
            csu.mExecuteOEDAStep(ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_CREATE_GDISK)            

        #
        # INSTALL CLUSTER Configure Syslog Ilom Host
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Configure Syslog Ilom Host')
        ebox.mConfigureSyslogIlomHost()
        ebox.mLogStepElapsedTime(_step_time, 'Configure Syslog Ilom Host')

        #
        # INSTALL CLUSTER Configure Syslog IB Switches
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Configure Syslog IB Switches')
        ebox.mConfigureSyslogIBSwitches()
        ebox.mLogStepElapsedTime(_step_time, 'Configure Syslog IB Switches')

        #
        # Customize VM.CFG (e.g. additional images, partitions,...)
        #
        ebox.mAcquireRemoteLock()
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Patching VM Configuration')
        ebox.mPatchVMCfg(aOptions)          
        ebox.mConfigureShmAll()


        # Perform Encryption on Fs Mounted on /u02 if requested in payload, on non-KVM environments
        # as encryption on KVM is done through OEDA
        if isEncryptionRequested(aOptions, 'domU') and not ebox.mIsOciEXACC() and not ebox.mIsKVM():
            batchEncryptionSetupDomU(ebox, ebox.mReturnDom0DomUPair(), "/u02")

        ebox.mLogStepElapsedTime(_step_time, 'Patching VM Configuration')
        ebox.mReleaseRemoteLock()

        #
        # Execute OEDA Install Cluster
        #
        csu.mExecuteOEDAStep(ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_INSTALL_CLUSTER,dom0Lock=False)
        
        _val = ebox.mCheckConfigOption("exacloud_health_install_cluster", "True")
        if (_val):
            csu.mHealthCheckClufy(ebox)
        #
        # Execute OEDA Init Cluster
        #
        csu.mExecuteOEDAStep(ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_INIT_CLUSTER,dom0Lock=False)

        #
        # Set CACHINGPOLICY to DEFAULT on ADB-S RECO GridDisk
        #
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Set CACHEPOLICY to DEFAULT on ADB-S RECO GridDisk')
        ebox.mSetCachingPolicyRecoGD(ebox.mReturnCellNodes(), aOptions)
        ebox.mLogStepElapsedTime(_step_time, 'Set CACHEPOLICY to DEFAULT on ADB-S RECO GridDisk')

        # RSP File Logic (for vmgi_reconfig)
        if ebox.mCheckConfigOption("reconfig_enabled", "True"):
            # There is a separate fn mSetSrcDom0DomU but includes OLS and GI
            # logic, which is executed in posterior steps. 
            # Technically, RSP file exists only for one domU.
            for _, _domU in ebox.mReturnDom0DomUPair():
                _rspfile = ebox.mGetOedaPath()+f"/WorkDir/Grid-{_domU}.rsp"
                if os.path.exists(_rspfile):
                    ebLogTrace(f'rsp file found {_rspfile}')
                    with connect_to_host(_domU, get_gcontext()) as _node:                        
                        _node.mCopyFile(_rspfile, f"/u01/Grid-{_domU}.rsp")

        ebLogInfo('csInstallCluster: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "Install Cluster completed", 'ESTP_INSTALL_CLUSTER')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Install Cluster", "Done", _stepSpecificDetails)


    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        _ebox = aExaBoxCluCtrlObj
        ebLogVerbose('csInstallCluster: Entering undoExecute')
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, aOptions)
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'ONGOING', "Undo Install Cluster in progress", 'ESTP_INSTALL_CLUSTER')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Undo Install Cluster", "In Progress", _stepSpecificDetails)

        if _ebox.mIsExabm() and _ebox.mGetCmd() in ['vmgi_delete', 'gi_delete']:
            ebLogInfo('*** csInstallCluster: Completed undoExecute Successfully')
            return

        if _ebox.IsZdlraProv():   
            # Update non root password (es.properties) in ZDLRA env from wallet
            _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd')      
            _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd) 

        # All Guest images are removed during undo step2
        # Remove u02_extra.img file (which gets created as part of mPatchVMCfg() in doExecute())

        # mPatchKVMImageCfg handles /u02 being still there, do nothing on KVM
        if not _ebox.mIsKVM():
            _ddp = _ebox.mReturnDom0DomUPair()
            for _dom0, _domU in _ddp:
                with connect_to_host(_dom0, get_gcontext()) as _node:
                    _extra_disk = '/EXAVMIMAGES/GuestImages/' + _domU + '/u02_extra.img'
                    if _node.mFileExists(_extra_disk):
                        _node.mExecuteCmdLog("rm -f " + _extra_disk)
        
                    # Remove the u02_extra.img entry from vm.cfg in dom0
                    _vmhandle = exaBoxOVMCtrl(aCtx=get_gcontext(), aNode=_node)
                    _vmhandle.mReadRemoteCfg(_domU)
                    _cfg = _vmhandle.mGetOVSVMConfig(_domU)
                    if _cfg is None:
                        continue
                    _ddata = ast.literal_eval(_cfg.mGetValue('disk'))
                    _ddata = [_disk for _disk in _ddata if 'u02_extra.img' not in _disk]
                    _cfg.mSetValue('disk', str(_ddata))
                    _ebox.mSaveVMCfg(_node, _domU, _cfg.mRawConfig())

                # Remove the u02 entry from fstab in the domU
                if not _ebox.mPingHost(_domU):
                    ebLogWarn(f'*** Host ({_domU}) is not pingable aborting .')
                    continue

                with connect_to_host(_domU, get_gcontext()) as _node:
                    _node.mExecuteCmdLog('umount /u02')
                    _node.mExecuteCmdLog('cat /etc/fstab | grep -v /u02 > /etc/fstab.orig; cp /etc/fstab.orig /etc/fstab')

        # If FS Encryption is requested, we remove u02 to allow recreation on retry
        # mPatchKVMImageCfg handles /u02 being still there, do nothing on KVM

        if _ebox.mIsKVM() and ( isEncryptionRequested(aOptions, 'domU') or exacc_fsencryption_requested(aOptions)):

            cleanupU02EncryptedDisk(_ebox.mReturnDom0DomUPair())

        # If EDV Volume is detected, umount u02 volume from the cells
        _utils = _ebox.mGetExascaleUtils()
        if _ebox.mIsKVM() and _utils.mIsEDVImageSupported(aOptions):
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                _dom0_short_name = _dom0.split('.')[0]
                _domU_short_name = _domU.split('.')[0]
                _u02_vol_name = _domU_short_name + "_u02"
                _u02_name = _ebox.mCheckConfigOption('u02_name') if _ebox.mCheckConfigOption('u02_name') else 'u02_extra'
                _utils.mDetachU02(_dom0, _domU, _u02_name, _u02_vol_name, aOptions)

        # Undo OEDA Init Cluster step
        _csu.mExecuteOEDAStep(_ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_INIT_CLUSTER, undo=True,dom0Lock=False, aSkipFail=True)

        #
        # Undo OEDA Install Cluster step
        #
        _csu.mExecuteOEDAStep(_ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_INSTALL_CLUSTER, undo=True, dom0Lock=False, aSkipFail=True)

        #
        # POSTGI - Run External Scripts
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Running External POSTGI Scripts')
        _ebox.mRunScript(aType='*',aWhen='post.gi_delete')
        _ebox.mLogStepElapsedTime(_step_time, 'Running External POSTGI Scripts')

        # Delete grid disks.
        _csu.mExecuteOEDAStep(_ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_CREATE_GDISK, undo=True, dom0Lock=False)

        #
        # Grid Disk Force Delete (this is required as most of the time GridDisks delete step will fail
        # (e.g. ASM/DB not shutdown properly due to inability to access the DomUs/VMs)
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Running Delete Force Grid Disks POSTVM')
        if _ebox.mCheckCellsServicesUp():
            _ebox.mGetStorage().mDeleteForceGridDisks()
        else:
            ebLogWarn('*** Cell Services are not running, unable to delete Grid disks')
        _ebox.mLogStepElapsedTime(_step_time, 'Running Delete Force Grid Disks')
        
        ebLogVerbose('csInstallCluster: Completed undoExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'DONE', "Undo Install Cluster completed", 'ESTP_INSTALL_CLUSTER')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Undo Install Cluster", "Done", _stepSpecificDetails)
