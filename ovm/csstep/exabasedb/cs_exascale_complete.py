#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exabasedb/cs_exascale_complete.py /main/2 2025/11/26 16:56:00 prsshukl Exp $
#
# cs_exascale_complete.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_exascale_complete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/26/25 - Bug 38694263 - EXACOMPUTE:EXACLOUD:
#                           EXASCALE_COMPLETE FAILED IN R1 COPYING WEBLOGIC
#                           CERT
#    prsshukl    11/19/25 - Creation
#

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

        if not imageBom.mIsSubStepExecuted(self.step, "PATCH_VM_CFG"):
            _exascale = ebCluExaScale(ebox)

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
                
                if ebox.mCheckConfigOption('enable_vmexacs_kvm') == 'True':
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
            # in dev2 stack i have skipped for the 1st provisioning testing, cause of the base template xml issue
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

        if not imageBom.mIsSubStepExecuted(self.step, "RPM_UPDATE"):
            # install nosql
            if ebox.mCheckConfigOption('install_nosql', 'True'):
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='nosql install')
                _domUs = list(map(operator.itemgetter(1),ebox.mReturnDom0DomUPair()))
                _rackSize = ebox.mGetRackSize()
                _nosql = ebNoSqlInstaller(_domUs,_rackSize)
                _nosql.mRunInstall()
                ebox.mLogStepElapsedTime(_step_time, 'nosql install')

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

            # Add customer SSH Key in DOMUs
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Patch VM SSH Keys')
            ebox.mPatchVMSSHKey(aOptions)
            ebox.mLogStepElapsedTime(_step_time, 'Patch VM SSH Keys')

        if not imageBom.mIsSubStepExecuted(self.step, "ATP_BACKUP_LISTENER"):
            # Workaround for incorrect permissions of cellkey.ora 
            # when asm scoped security is enabled (should be removed if fixed in OEDA)
            for _, _domu in ebox.mReturnDom0DomUPair():
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domu)
                if _node.mFileExists('/etc/oracle/cell/network-config/cellkey.ora'):
                    _node.mExecuteCmd("chmod 640 /etc/oracle/cell/network-config/cellkey.ora")
                _node.mDisconnect()

        _exascale = ebCluExaScale(ebox)
        if not imageBom.mIsSubStepExecuted(self.step, "UDEV_RULES_CREATION_AND_REMOVE_CELLINIT_ORA"):
            _exascale.mWriteUdevDbVolumesRules()
            _exascale.mRemoveCellinitOra()
        
        if ebox.mCheckConfigOption('enable_validate_volumes', 'True'):
            for _dom0, _domU in ebox.mReturnDom0DomUPair():
                _exascale.mPerformValidateVolumesCheck(_dom0, _domU)
        else:
            ebLogInfo(f"enable_validate_volumes config is disabled in exabox.conf. Hence Skipping")

        _isclone = aOptions.jsonconf.get("isClone", None)
        if ebox.isBaseDB():
            if not _isclone or str(_isclone).lower() == "false":
                # Install Base DB rpm 
                ebox.mUpdateRpm('dcs-agent.x86_64.rpm', False, None, False, 'packages/', '/')
                ebox.mUpdateRpm('dcs-admin.x86_64.rpm', False, None, False, 'packages/', '/')
                ebox.mUpdateRpm('dcs-cli.x86_64.rpm', False, None, False, 'packages/', '/')
                ebox.mUpdateRpm('mysql.x86_64.rpm', False, None, False, 'packages/', '~/Extras/')

            if is_r1_region():
                _exascale = ebCluExaScale(ebox)
                _exascale.mCopyWeblogicCert()

            # vmdb_setupenv.sh gets generated as part of installation of above rpms. 
            for _dom0, _domU in ebox.mReturnDom0DomUPair():
                with connect_to_host(_domU, get_gcontext()) as _node:
                    _node.mCopyFile('packages/basedb_exaxs_vmdb_setupenv.sh', '/basedb_exaxs_vmdb_setupenv.sh')
                    _node.mExecuteCmdLog('chmod +x /basedb_exaxs_vmdb_setupenv.sh')
                    _node.mExecuteCmdLog('/basedb_exaxs_vmdb_setupenv.sh > /tmp/basedb_exaxs_vmdb_setupenv.log')

        elif ebox.isExacomputeVM():
            # need to use latest rpm (not versioned rpm here)
            ebox.mUpdateRpm('exacompute-vm-agent.rpm', False, None, False, 'images/', '/')

            # cloud-init rpm installation disabled for now.
            """
            _dep_list = ['gdisk-1.0.3-11.el8.x86_64.rpm', 'python3-pytz-2017.2-11.0.1.el8.noarch.rpm', \
            'python3-jwt-1.6.1-2.el8.noarch.rpm', 'python3-jsonpointer-1.10-11.el8.noarch.rpm', 'python3-babel-2.5.1-7.el8.noarch.rpm', \
            'python3-markupsafe-0.23-19.el8.x86_64.rpm', 'python3-prettytable-0.7.2-14.el8.noarch.rpm', \
            'python3-jsonpatch-1.21-2.el8.noarch.rpm', 'python3-oauthlib-2.1.0-1.el8.noarch.rpm', \
            'python3-jsonschema-2.6.0-4.el8.noarch.rpm', 'python3-netifaces-0.10.6-4.el8.x86_64.rpm', \
            'python3-configobj-5.0.6-11.el8.noarch.rpm', 'python3-pyserial-3.1.1-9.el8.noarch.rpm', \
            'python3-jinja2-2.10-9.el8.noarch.rpm']

            for _dep in _dep_list:
                ebox.mUpdateRpm(_dep, False, None, False, 'images/', '/')

            ebox.mUpdateRpm('cloud-init.rpm', False, None, False, 'images/', '/')

            for _dom0, _domU in ebox.mReturnDom0DomUPair():
                with connect_to_host(_domU, get_gcontext()) as _node:
                    _node.mExecuteCmdLog('echo -e "network:\n config: disabled" > /etc/cloud/cloud.cfg.d/04_exadata_net.cfg')
                    _node.mExecuteCmdLog('systemctl daemon-reexec')
                    _node.mExecuteCmdLog('systemctl daemon-reload')
                    _node.mExecuteCmdLog('systemctl enable cloud-init-local.service')
                    _node.mExecuteCmdLog('ystemctl enable cloud-init.service')
                    _node.mExecuteCmdLog('systemctl enable cloud-config.service')
                    _node.mExecuteCmdLog('systemctl enable cloud-final.service')
                    _node.mExecuteCmd('grep "datasource_list: [ Oracle ]" /etc/cloud/cloud.cfg')
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mExecuteCmdLog("sed -i '/^cloud_init_modules/a \  datasource_list: [ Oracle ]'  /etc/cloud/cloud.cfg")

                    _node.mExecuteCmdLog('cloud-init clean --logs')
                    _node.mExecuteCmdLog('rm -rf /var/lib/cloud/')

                ebox.mSingleDomURestart(_dom0,_domU,aOptions) 
            """

        ebLogInfo('*** Exacloud Operation Successful : POST GI Install')
        ebLogInfo('csExaScaleComplete: Completed doExecute Successfully')

  
    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, _steplist):
        ebLogInfo('csExaScaleComplete: Entering undoExecute')
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

        if _ebox.mIsExabm() and _ebox.mGetCmd() in ['vmgi_delete', 'gi_delete', 'deleteservice']:
            _csu.mDeleteVM(aExaBoxCluCtrlObj, self.step, _steplist)
            ebLogInfo('*** csExaScaleComplete: Completed undoExecute Successfully')
            return