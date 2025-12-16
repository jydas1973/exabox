#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/cs_installcluster.py /main/7 2025/08/25 06:17:10 pbellary Exp $
#
# cs_installcluster.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_installcluster.py - Create Service INSTALL CLUSTER
# 
#   FUNCTION:
#      Implements the Install and Init Cluster steps for exascale create service execution  
#
#    NOTES
#      Invoked from cs_driver.py
#
#    EXTERNAL INTERFACES:
#      csInstallCluster ESTP_INSTALL_CLUSTER
#
#    INTERNAL CLASSES:
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    06/06/25 - Enh 38035467 - EXASCALE: EXACLOUD TO PROVIDE ACFS FILE SYSTEM SIZES IN SYNCH CALL
#    pbellary    06/21/24 - ENH 36690743 - EXACLOUD: IMPLEMENT OEDA STEPS FOR EXASCALE CREATE SERVICE
#    pbellary    06/14/24 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
#    pbellary    06/06/24 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
#    pbellary    06/06/24 - Creation
#
import time
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogTrace
from exabox.ovm.csstep.cs_constants import csXSConstants, csXSEighthConstants
from exabox.utils.node import connect_to_host, node_exec_cmd, node_cmd_abs_path_check
from exabox.ovm.cluencryption import isEncryptionRequested, batchEncryptionSetupDomU, exacc_fsencryption_requested

# This class implements doExecute and undoExecute functions
# for the ESTP_INSTALL_CLUSTER step of create service
# This class primarily invokes OEDA do/undo Install and Init Cluster steps
class csInstallCluster(CSBase):
    def __init__(self):
        self.step = 'ESTP_INSTALL_CLUSTER'

    def doExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csInstallCluster: Entering doExecute')
        _ebox = aCluCtrlObj
        _step_list = aStepList
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, False)
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _step_list, aComment='Copy/Update images on Dom0')
        _ebox.mUpdateDepFiles()
        _ebox.mLogStepElapsedTime(_step_time, 'INSTALL CLUSTER : Copy/Update images on Dom0')

        #
        # INSTALL CLUSTER Configure Syslog Ilom Host
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _step_list, aComment='Configure Syslog Ilom Host')
        _ebox.mConfigureSyslogIlomHost()
        _ebox.mLogStepElapsedTime(_step_time, 'Configure Syslog Ilom Host')

        #
        # Customize VM.CFG (e.g. additional images, partitions,...)
        #
        _ebox.mAcquireRemoteLock()
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _step_list, aComment='Patching VM Configuration')
        _ebox.mPatchVMCfg(aOptions)
        _ebox.mConfigureShmAll()

        # Perform Encryption on Fs Mounted on /u02 if requested in payload, on non-KVM environments
        # as encryption on KVM is done through OEDA
        if isEncryptionRequested(aOptions, 'domU') and not _ebox.mIsOciEXACC() and not _ebox.mIsKVM():
            batchEncryptionSetupDomU(_ebox, _ebox.mReturnDom0DomUPair(), "/u02")

        _ebox.mLogStepElapsedTime(_step_time, 'Patching VM Configuration')
        _ebox.mReleaseRemoteLock()

        #
        # Execute OEDA Install Cluster
        #
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_INSTALL_CLUSTER, dom0Lock=False)

        #
        # Execute OEDA Init Cluster
        #
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_INIT_CLUSTER,dom0Lock=False)

        ebLogTrace('csInstallCluster: Completed doExecute Successfully')

    def undoExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csInstallCluster: Entering undoExecute')
        _ebox = aCluCtrlObj
        _step_list = aStepList
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, False)
        # If FS Encryption is requested, we remove u02 to allow recreation on retry
        # mPatchKVMImageCfg handles /u02 being still there, do nothing on KVM

        if _ebox.mIsKVM() and ( isEncryptionRequested(aOptions, 'domU') or exacc_fsencryption_requested(aOptions)):

            for _dom0, _domU in _ebox.mReturnDom0DomUPair():

                # Try to unmounte /u02 on the domUs (if at all present)
                with connect_to_host(_domU, get_gcontext()) as _node:

                    ebLogInfo(f"{_domU} -- Attempting to unmount /u02 (no-op if not mounted)")
                    _out_unmount = node_exec_cmd(_node, f"/bin/unmount /u02")
                    ebLogTrace(_out_unmount)

                    # Remove u02 from fstab (if at all present)
                    ebLogInfo(f"{_domU} -- Attempting to remove fstab /u02 entry (no-op if not present)")
                    _out_fstab = node_exec_cmd(_node, 'cat /etc/fstab | grep -v /u02 > /etc/fstab.orig; cp /etc/fstab.orig /etc/fstab')
                    ebLogTrace(_out_fstab)

                # Now try to remove the disk u02 using vm_maker from the dom0 (if at all present)
                with connect_to_host(_dom0, get_gcontext()) as _node:

                    _extra_disk = f"/EXAVMIMAGES/GuestImages/{_domU}/u02_extra_encrypted.img"

                    # Remove u02 disk
                    if _node.mFileExists(_extra_disk):
                        ebLogInfo(f"{_dom0} -- Attempting to detach {_extra_disk} disk image (no-op if not present)")
                        _out_detach = node_exec_cmd(_node, f"vm_maker --detach --disk-image {_extra_disk} --domain {_domU}")
                        ebLogTrace(_out_detach)

                        ebLogInfo(f"{_dom0} -- Attempting to remove {_extra_disk} disk image (no-op if not present)")
                        _out_rm = node_exec_cmd(_node, f"/bin/rm -f {_extra_disk}")
                        ebLogTrace(_out_rm)

        # If EDV Volume is detected, umount u02 volume from the cells
        _utils = _ebox.mGetExascaleUtils()
        if _ebox.mIsKVM() and _utils.mIsEDVImageSupported(aOptions):
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                _dom0_short_name = _dom0.split('.')[0]
                _domU_short_name = _domU.split('.')[0]
                _u02_vol_name = _domU_short_name + "_u02"
                _u02_name = _ebox.mCheckConfigOption('u02_name') if _ebox.mCheckConfigOption('u02_name') else 'u02_extra'
                _utils.mDetachU02(_dom0, _domU, _u02_name, _u02_vol_name, aOptions)

        #
        # Undo OEDA Init Cluster step
        #
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_INIT_CLUSTER, undo=True,dom0Lock=False, aSkipFail=True)

        #
        # Undo OEDA Install Cluster step
        #
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_INSTALL_CLUSTER, undo=True, dom0Lock=False, aSkipFail=True)

        ebLogTrace('csInstallCluster: Completed undoExecute Successfully')
