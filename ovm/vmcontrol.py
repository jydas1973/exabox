"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Basic functionality

FUNCTION:
    Provide basic/core API for managing OVM (VM Lifecycle, dom0 metrics, ...)

NOTE:
    None

History:
    jesandov    10/30/2025 - 38554948: Add force shutdown and force bounce
    remamid     09/24/2025 - Add OS command as part of mRebootVMCheck as part of VM validation bug 38347575
    avimonda    09/06/2015 - Bug 38205634 - OCI: EXACC: SOFTRESETEXACCVMNODE FAILS ON EXACLOUD WITH "ERROR WHILE MULTIPROCESSING(PROCESS TIMEOUT)"
    joysjose    09/05/2024 - 36462445 - EXACS: EXACLOUD  STOP VM TAKES 30 MINUTES TO STOP VM
    talagusu    13/11/2023 - 35990847 - VM SHUTDOWN RETRY LOGIC NOT DISABLING AUTOSTART 
    pbellary    17/08/2023 - 35714868 - VM CONSOLE - REBOOT VIA UI DOESNT ALLOW CUSTOMER TO GO TO GRUB
    pbellary    05/04/2023 - 35343409 EXISTING SERIAL CONSOLE CONNECTION NOT WORKING AFTER MEMORY RESHAPE OPERATION
    gparada     21/02/2023 - 35029440 Remove mCollectKernelMsg no longer used (Xen is not used anymore)
    jesandov    03/31/2023 - 35141247 - Add SSH Connection Pool
    dekuckre    24/05/21   - 32899744: Acquire - Release locks around mDispatchEvent
    jesandov    15/04/2020 - Remove code duplication btween the abstraction layer and the vmctrl class
    ndesanto    10/02/2019 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
    pbellary    02/06/20   - ENH 30804242 DEVELOP ABSTRACT LAYER FOR HANDLING XEN AND KVM CODE PATHS
    pbellary    02/06/20   - ENH 30804272 DEVELOP VM OPERATIONS SUPPORT FOR KVM USING VIRSH        
    ndesanto    07/19/2019 - Return vm list, not only log it. bug 29925312 
    hnvenkat    02/17/2016 - Support for vcpu runtime change - bug 22452941
    mirivier    12/18/2014 - Create file
"""

from __future__ import print_function

from exabox.core.Error import ebError
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn
from exabox.ovm.vmconfig import exaBoxVMConfig, exaBoxClusterConfig, ebVMCfg
from tempfile import NamedTemporaryFile
from multiprocessing import Process, Manager
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, ExitCodeBehavior, TimeoutBehavior
from exabox.ovm.hypervisorutils import *
from exabox.network.osds.sshgen import validate_hostname, ping_host
from exabox.recordreplay.record_replay import ebRecordReplay
from exabox.ovm.cluserialconsole import serialConsole
from exabox.utils.node import connect_to_host

import threading
import socket
import time
import os
import re
import json
import signal
import difflib
import glob


def vmList(context, clusters, machines, aOptions, reqobj, db):
    if reqobj is None:
        ebLogError("No request object.")
        return ebError(0x0400)
    else:
        _vm_list = getVMsForCluster(context, clusters, machines, aOptions)
        reqobj.mSetData(json.dumps(_vm_list))
        db.mUpdateRequest(reqobj)

    return 0


def getVMsForCluster(context, clusters, machines, aOptions):
    _vm_list = []

    _mac_list = clusters.mGetClusterMachines()
    for _mac in _mac_list:
        _mac_config = machines.mGetMachineConfig(_mac)
        _host = _mac_config.mGetMacHostName()
        _id = _mac_config.mGetMacId()

        _ml = machines.mGetMachineConfigList()
        for _m in list(_ml.keys()):
            _vml = _ml[_m].mGetMacMachines()

            if _id in _vml:
                _dom0 = _ml[_m].mGetMacHostName()
                _node = exaBoxNode(context)
                _node.mConnect(aHost=_dom0)
                _vmhandle = exaBoxOVMCtrl(aCtx=context, aNode=_node)
                _vmhandle.mRefreshDomUs()
                _vm_list.extend(_vmhandle.mGetDomUs())
                _node.mDisconnect()

    return _vm_list


class exaBoxOVMCtrl(object):

    def __init__(self, aCtx, aNode = None):

        self.__ctx     = aCtx
        self.__node    = aNode
        self.__remotecfg = {}
        self.__vmhandle = None
        self.__time_sleep_reboot = 10
        if "vm_time_sleep_reboot" in aCtx.mGetConfigOptions():
            self.__time_sleep_reboot = aCtx.mGetConfigOptions()['vm_time_sleep_reboot']

        if not self.__node:
            ebLogWarn('Node object not provided.')
            return

        self.__vmhandle = getHVInstance(self.__node.mGetHostname())

        # Retrieve VM type, UUID and Dom0
        self.hypervisor, self.dom0, self.uuid = self.__vmhandle.mNodeType()

        self.__domUs = []    # List of DomUs currently running
        self.__domUsCfg = [] # List of DomUs currently configured
        self.__debug  = False

        if self.dom0:
            self.mRefreshDomUs()
            self.mRefreshDomUsCfg()

    def mGetHVInstance(self):
        return self.__vmhandle

    def mSetDestroyOnStart(self, aValue):
        self.__vmhandle.mSetDestroyOnStart(aValue)

    def mGetDom0(self):
        return self.__node.mGetHostname()

    def mGetDomUs(self):
        return self.__domUs

    def mGetDomUsCfg(self):
        return self.__domUsCfg

    def mRefreshDomUs(self):
        self.__domUs = self.__vmhandle.mRefreshDomUs()

    def mRefreshDomUsCfg(self):
        self.__domUsCfg = self.__vmhandle.mRefreshDomUsCfg()

    def mReadRemoteCfg(self, aRemoteVMName=None, aRemoteCfgPath=None):
        self.__vmhandle.mReadRemoteCfg(aRemoteVMName, aRemoteCfgPath)

    def mDumpOVSVMConfig(self, aVMName):
        self.__vmhandle.mDumpOVSVMConfig(aVMName)

    def mPatchOVSVMConfig(self, aVMName, aList=None):
        self.__vmhandle.mPatchOVSVMConfig(aVMName, aList)

    def mGetOVSVMConfig(self, aVMName):
        return self.__vmhandle.mGetOVSVMConfig(aVMName)

    def mGetOVSVMList(self):
        return self.__vmhandle.mGetOVSVMList()

    def mReadRemoteAllCfg(self, aOptions=None, aForce=False):
        self.__vmhandle.mReadRemoteAllCfg(aOptions, aForce)

    def mPruneOVSRepo(self, aOptions):
        self.__vmhandle.mPruneOVSRepo(aOptions)

    def mPingHost(self,aHostname,aCount=4):

        # Already validated the xm li on the ping endpoint
        _ctx = get_gcontext()
        if _ctx.mCheckRegEntry("ssh_post_fix") and \
           _ctx.mGetRegEntry("ssh_post_fix") == "True":

            ebLogInfo("ssh_post_fix, Skipping Ping")
            return True

        _host = aHostname
        if _ctx.mCheckRegEntry('_natHN_' + _host):
            _host = _ctx.mGetRegEntry('_natHN_' + _host)
            if self.__debug:
                ebLogDebug('*** CONN_PING_USING_NATHN: %s/%s' % (aHostname, _host))

        _count = aCount
        _valid_hostname = validate_hostname(_host)
        if _valid_hostname and ping_host(_host, _count):
            return True
        elif not _valid_hostname:
            ebLogError("Hostname: " + str(_host) + " is not valid.")
        return False

    def mCreateVM(self, aVMId):
        self.__vmhandle.mCreateVM(aVMId)

    def mDeleteVM(self, aVMId):
        self.__vmhandle.mDeleteVM(aVMId)

    def mCheckAutoStart(self, aVMId):
       _rc = self.__vmhandle.mCheckAutoStart(aVMId)
       return _rc

    def mAutoStartVM(self, aVMId, aEnabled):
        _rc = self.__vmhandle.mAutoStartVM(aVMId, aEnabled)
        return _rc

    def mLogListVms(self):
        ebLogInfo("".join(self.__vmhandle.mGetDomUList()[1]))
        return 0

    def mStatus(self):
        self.__vmhandle.mStatus()

    def mInfo(self):
        self.__vmhandle.mInfo()

    def mVMInfo(self, aVMId):
        self.__vmhandle.mVMInfo(aVMId)

    def mDestroyVM(self, aVMId):
        self.__vmhandle.mDestroyVM(aVMId)

    def mShutdownVM(self, aVMId, aOptions=None):
        _vmid = aVMId
        _vm_list_cmd = self.__vmhandle.mListVmsCmd()
        _timeout_vm_shutdown = 900 # 15mins
        if aOptions is not None and aOptions.jsonconf is not None and aOptions.jsonconf.get('non_rolling_patching'):
            _timeout_vm_shutdown = 300

        # Close active ssh connections
        _connkey = f"{threading.get_ident()}-{os.getpid()}"
        _sshPoolName = f'SSH-POOL-{_connkey}'

        if get_gcontext().mCheckRegEntry(_sshPoolName):
            _connectionPool = get_gcontext().mGetRegEntry(f'SSH-POOL-{_connkey}')
            _connectionPool.mCloseConnections(aHost=_vmid)

        _starttime = time.time()
        #Execute the shutdown
        self.__vmhandle.mShutdownVM(aVMId)
        #
        # Wait for WM to Shutdown 
        #
        _elapsed  = 0
        _iterations = 0
        while _elapsed < _timeout_vm_shutdown:
            time.sleep(self.__time_sleep_reboot)
            self.mRefreshDomUs()
            if not _vmid in self.mGetDomUs():
                break
            else:
                if _iterations % 10 == 0:
                    ebLogDebug('*** Waiting for complete of Shutdown of VM: {0}, time: {1}'.format(_vmid, _elapsed))
            _elapsed = time.time() - _starttime

            #Join the collect process is still alive
            _iterations += 1

        _elapsed = time.time() - _starttime
    
        #Verified the output
        if _elapsed >= _timeout_vm_shutdown:
            _, _o, _ = self.__vmhandle.mExecuteCmd(_vm_list_cmd)
            ebLogError('Failing to Shutdown VM: {0}, time: {1}'.format(_vmid, _elapsed))

            ebLogError("CMD DOM0 ({0}) : {1}\n".format(self.__node.mGetHostname(), _vm_list_cmd))
            ebLogError(_o.read().strip())
            ebLogInfo("Process with destroy")

            return self.__vmhandle.mDestroyVM(_vmid)
        else:

            time.sleep(self.__time_sleep_reboot)
            ebLogInfo('*** Successfully Shutdown VM: {0}, time: {1}'.format(_vmid, _elapsed))

            self.mRefreshDomUs()
            if _vmid in self.mGetDomUs():
                ebLogWarn("The vm {0} is still present, calling destroy".format(_vmid))
                return self.__vmhandle.mDestroyVM(_vmid)

            else:
                return 0

    def mRebootVM(self, aVMId, atimeout, reachability_chk=None):

        _node = exaBoxNode(get_gcontext())
        _is_ssh_port_accessible = _node.mCheckPortSSH(aVMId) 
        if _is_ssh_port_accessible:
            ebLogInfo('***The SSH port was accessible before rebooting VM')
        else:
            ebLogWarn('***The SSH port was NOT reachable before rebooting VM')
            
        if reachability_chk == "True" or reachability_chk == "true":
            _rc = self.mShutdownVM(aVMId)
            if _rc == 0:
                _starttime = time.time()
                _timeout = atimeout
                _rc = self.__vmhandle.mStartVM(aVMId)
                if _rc == 0:
                    _rc = self.mRebootVMCheck(aVMId, _starttime, _timeout)
        else:
            return self.__vmhandle.mRebootVM(aVMId)
        return _rc

    def mStartVM(self, aVMId):
        _vmid = aVMId
        _count = 5
        _rc = 0
        _time_sleep = 15
        while _count:
            _rc = self.__vmhandle.mStartVM(aVMId)
            if not _rc:
                break
            _count = _count -1
            _time_sleep = _time_sleep * 2
            time.sleep(_time_sleep)
        if _count == 0 and _rc:
            return _rc
        #
        # Wait for VM pre-start (e.v. qemu / vif attach...)
        #
        _starttime = time.time()
        _elapsed  = 0
        _timeout = 3600 # 60 minutes
        while _elapsed < _timeout:
            time.sleep(self.__time_sleep_reboot)
            self.mRefreshDomUs()
            if _vmid in self.mGetDomUs():
                break
            else:
                ebLogDebug('*** Waiting for initial Start of VM: {0}, time: {1}'.format(_vmid, _elapsed))
            _elapsed = time.time() - _starttime
        _elapsed = time.time() - _starttime
        if _elapsed >= _timeout:
            ebLogError('Failing to Start VM: {0}'.format(_vmid))
            return _rc
        else:
            ebLogInfo('*** Successfully Started VM: {0}, time: {1}'.format(_vmid, _elapsed))
            return 0

    def mUptime(self):
        self.__vmhandle.mUptime()

    def mSetVcpus(self, aVMId, aVcpuset):
        self.__vmhandle.mSetVcpus(aVMId, aVcpuset)

    """
    ::mCheckVMId

    Check if VMId is available/valid and if the corresponding VM is running or not

    return: (VMid, Exist)

    :VMid if it is found and there is a corresponding VM configuration in /EXAVMIMAGES/GuestImages
    :Exist set to True is VMid/VM is currently running else set to False
    """
    def mCheckVMId(self, aVMId, aOptions, aErrorStr, aCheckVMExist=False):
        #
        # Update/Refresh running DomUs list
        #
        self.mRefreshDomUs()
        if aVMId:
            _vmid = aVMId
        else:
            _vmid = aOptions.vmid

        if not _vmid:
            ebLogError(aErrorStr)
            return None, False
        _exist = False

        #
        # Check name resolution
        #
        try:
            socket.gethostbyname(_vmid)
        except socket.gaierror:
            #
            # This needs to be fixed eventually on BM. E.g. Check NAT cache
            #
            ebLogWarn('*** BM_TRAP TBD *** Hostname (%s) could not be resolved please check hostname and domain name' % _vmid)
        #
        # Check if VM is running
        #
        if aCheckVMExist:
            if not _vmid in self.mGetDomUs():
                ebLogError('Currrent operation expecting VM: ' + _vmid+' to be running ('+aErrorStr+')')
                ebLogDebug('VM currently Running:')
                for vm in self.mGetDomUs():
                    ebLogInfo(vm)
            else:
                _exist = True
        #
        # Check if VM is _not_ running
        #
        if not aCheckVMExist:
            if _vmid in self.mGetDomUs():
                ebLogError('Currrent operation does not expect VM: ' + _vmid+' to be running ('+aErrorStr+')')
                ebLogDebug('VM currently Running:')
                for vm in self.mGetDomUs():
                    ebLogInfo(vm)
                _exist = True
        #
        # Refresh DomUsCfg
        #
        self.mRefreshDomUsCfg()
        if not _vmid in self.mGetDomUsCfg():
            _vmid = None

        return _vmid, _exist

    def mDumpInfo(self):
        ebLogInfo ('VM Info: hypervisor: %s , dom0: %s , uuid: %s' %(self.hypervisor, self.dom0, self.uuid))

    def mExecuteCmd(self, aCmd, aOptions=None):

        fin, fout, ferr = self.__node.mExecuteCmd(aCmd)
        return fin, fout, ferr

    def mGetCmdExitStatus(self):

        return self.__node.mGetCmdExitStatus()

    def mExecuteCmdLog(self, aCmd, aOptions=None):

        fin, fout, ferr = self.mExecuteCmd(aCmd)
        out = fout.readlines()
        if out:
            for e in out:
                ebLogInfo(e[:-1])
        err = ferr.readlines()
        if err:
            for e in err:
                ebLogError(e[:-1])

    def mRebootVMCheck(self, _vmid, astarttime, aTimeout): 
        _starttime = astarttime
        _timeout_vm_stopstart = aTimeout
        _elapsed  = 0
        _iterations = 0
        _node = exaBoxNode(get_gcontext())
        if self.__ctx.mCheckRegEntry('_natHN_' + _vmid):
            _natvmid = self.__ctx.mGetRegEntry('_natHN_' + _vmid)
        else:
            _natvmid = _vmid
        while _elapsed < _timeout_vm_stopstart:
            time.sleep(self.__time_sleep_reboot)
            _ret = _node.mCheckPortSSH(_vmid)
            if _ret is True:
                ebLogInfo(f'VM {_vmid} startup complete.')
                return 0  
            if _iterations % 10 == 0:
                ebLogInfo(f'*** Waiting for VM: {_vmid} to be accessible, time: {_elapsed}')
            _iterations += 1
            _elapsed = time.time() - _starttime  
        if _elapsed >= _timeout_vm_stopstart: 
            _vm_conn_cmd = f"curl -v --max-time 5 telnet://{_natvmid}:22"
            ebLogInfo(f'*** Executing {_vm_conn_cmd}')
            _, _, _, _e = _node.mExecuteLocal(_vm_conn_cmd)
            ebLogError(f'Timeout waiting for VM: {_vmid} to be accessible post start, ERROR: {str(_e)}')
            return 1
        else:
            return 0

class ebVgLifeCycle(ebVgBase):

    def __init__(self):
        self.__vmctrl = None

    def mSetOVMCtrl(self, aCtx, aNode = None):
        _ctx = aCtx
        _node = aNode
        self.__vmctrl = exaBoxOVMCtrl(aCtx=_ctx, aNode=_node)

    def mGetVmCtrl(self):
        return self.__vmctrl

    def mSetDestroyOnStart(self, aValue):
        self.__vmctrl.mSetDestroyOnStart(aValue)

    def mCheckCMDAndReboot(self, aCluCtrlObj=None, aOptions=None):
        if aCluCtrlObj:
            if ( aCluCtrlObj.mGetCmd() == 'vm_cmd' and aOptions and 'vmcmd' in aOptions and aOptions.vmcmd in ['memset', 'resizecpus'] ) \
               or (aCluCtrlObj.mGetCmd() == 'partition') \
               or (aCluCtrlObj.mGetCmd() == 'createservice' and aOptions and 'steplist' in aOptions and aOptions.steplist in ["ESTP_INSTALL_CLUSTER", "ESTP_POSTGI_NID"]):
                   ebLogInfo("Skipping shutdown/restarting containers 'exa-hippo-serialmux|exa-hippo-sshd'")
                   return False
            else:
                 return True
        else:
            return False

    def mDispatchEvent(self, aCmd, aOptions=None, aVMId=None, aCluCtrlObj=None):

        _rc = (-1 << 16 ) | 0x0000

        if aCmd in ['list', 'status', 'start', 'shutdown', 'bounce', 'create', 'destroy', 'vcpuset']:
            if self.__vmctrl.dom0 == False:
                ebLogWarn('Node type Dom0 expected to run command: ' + aCmd)
                self.__vmctrl.mDumpInfo()
                return _rc

        if aCmd == 'ping':
            _vmid, _exist = self.__vmctrl.mCheckVMId(aVMId, aOptions, 'vmctrl: ping', True)
            if not _exist and _vmid:
                return 0x0411       # ERROR_411 : VM IS NOT RUNNING
            if not _exist and not _vmid:
                return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED
            if not _vmid:
                return _rc
            _rc = self.__vmctrl.mPingHost(_vmid)

            if _rc is True:
                return 0
            else:
                return 0x0411

        if aCmd == 'dumpovsvmcfg':
            if not aOptions.vmid:
                ebLogError('VMName required for dumpovsvmcfg')
                return _rc
            self.__vmctrl.mDumpOVSVMConfig(aVMName=aOptions.vmid)

        if aCmd == 'patchovsvmcfg':
            if not aOptions.vmid or not aOptions.kvlist:
                ebLogError('VMName and KVList required for dumpovsvmcfg')
                return _rc
            self.__vmctrl.mPatchOVSVMConfig(aVMName=aOptions.vmid,aList=aOptions.kvlist)

        if aCmd == 'create':
            _vmid,_exist = self.__vmctrl.mCheckVMId(aVMId, aOptions,'vmctrl: create', False)
            if _exist:
                return 0x0410       # ERROR_410 : VM ALREADY RUNNING
            if not _vmid:
                return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED

            if aCluCtrlObj:   
                aCluCtrlObj.mAcquireRemoteLock()   

            try:
                self.__vmctrl.mCreateVM(_vmid)
            finally:
                if aCluCtrlObj:
                    aCluCtrlObj.mReleaseRemoteLock()

        if aCmd == 'delete':
            _vmid,_exist = self.__vmctrl.mCheckVMId(aVMId, aOptions,'vmctrl: create', False)
            if not _vmid:
                return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED

            if aCluCtrlObj:   
                aCluCtrlObj.mAcquireRemoteLock()   

            try:
                self.__vmctrl.mDeleteVM(_vmid)
            finally:
                if aCluCtrlObj:
                    aCluCtrlObj.mReleaseRemoteLock()

            return 0

        if aCmd == 'list':
            return self.__vmctrl.mLogListVms()

        #
        # Remove Orphan VMs in /OVS/Repositories
        #
        if aCmd == 'cleanup':
            self.__vmctrl.mReadRemoteAllCfg()
            self.__vmctrl.mPruneOVSRepo(aOptions)

        if aCmd == 'status':
            self.__vmctrl.mStatus()
            return 0

        if aCmd == 'info':
            self.__vmctrl.mInfo()
            return 0

        if aCmd == 'vminfo':
            _vmid,_exist = self.__vmctrl.mCheckVMId(aVMId, aOptions,'vmctrl: vminfo', True)
            if not _vmid:
                return -1
            self.__vmctrl.mVMInfo(_vmid)
            return 0

        if aCmd == 'destroy':
            _vmid, _exist = self.__vmctrl.mCheckVMId(aVMId, aOptions,'vmctrl: destroy', True)
            if not _exist and _vmid:
                return 0x0411       # ERROR_411 : VM IS NOT RUNNING
            if not _exist and not _vmid:
                return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED
            if not _vmid:
                return -1

            if aCluCtrlObj:   
                aCluCtrlObj.mAcquireRemoteLock()  
 
            try:
                self.__vmctrl.mDestroyVM(_vmid)
            finally:
                if aCluCtrlObj:
                    aCluCtrlObj.mReleaseRemoteLock()  

            return 0

        if aCmd == 'shutdown':
            _vmid, _exist = self.__vmctrl.mCheckVMId(aVMId,aOptions, 'vmctrl: shutdown', True)
            if not _exist and _vmid:
                # Bug 35990847 - check the autoStart
                _autoStart = self.__vmctrl.mCheckAutoStart(_vmid)
                if _autoStart:
                   ebLogInfo(f"*** node is already shutdown and autostart is not disabled, disabling it")
                   _rc = self.__vmctrl.mAutoStartVM(_vmid, False)
                   if _rc:
                       _detail_error = "Failed to disable AutoStart on %s" %(_vmid) 
                       ebLogError('*** ' + _detail_error)
                       _mAutostartSettingErr = 0x0454  # ERROR_454 : Failed to change the autostart parameter status
                       return _mAutostartSettingErr
                   return 0x0411
                else:
                   ebLogInfo(f"*** node is already shutdown and autostart is disabled")
                   return 0x0411       # ERROR_411 : VM IS NOT RUNNING
            if not _exist and not _vmid:
                return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED
            if not _vmid:
                return _rc
            _mAutostartSettingErr = None 
            if aCluCtrlObj:   
                aCluCtrlObj.mAcquireRemoteLock()

            try:
                _remote_dir = f"/EXAVMIMAGES/GuestImages/{_vmid}/console/write-qemu/"
                _file = _remote_dir + f"lcm_exacloud"
                with connect_to_host(self.__vmctrl.mGetDom0(), get_gcontext()) as _node:
                    if _node.mFileExists(_remote_dir):
                        _cmd_str = f"/bin/touch {_file}"
                        _node.mExecuteCmdLog(_cmd_str)
                    else:
                        ebLogInfo(f"*** write-qemu directory {_remote_dir} not exists on dom0:{self.__vmctrl.mGetDom0()}. Skipping creation of file {_file}")
 
                _rc = self.__vmctrl.mAutoStartVM(_vmid, False)
                if _rc:
                    _detail_error = "Failed to disable AutoStart on %s" %(_vmid) 
                    ebLogError('*** ' + _detail_error)
                    _mAutostartSettingErr = 0x0454  # ERROR_454 : Failed to change the autostart parameter status

                _rc = self.__vmctrl.mShutdownVM(_vmid, aOptions=aOptions)

                if aCluCtrlObj:
                    if self.mCheckCMDAndReboot(aCluCtrlObj, aOptions):
                        _consoleobj = serialConsole(aCluCtrlObj, aOptions)
                        _consoleobj.mStopContainer(self.__vmctrl.mGetDom0(), _vmid)

            finally:
                if aCluCtrlObj:
                    aCluCtrlObj.mReleaseRemoteLock() 

            if _rc == 0 and _mAutostartSettingErr == 0x0454:
                return _mAutostartSettingErr 
            return _rc

        # xxx/MR: Make sure that ctrl-del is configured properly in the VM
        if aCmd == 'bounce':
            _vmid, _exist = self.__vmctrl.mCheckVMId(aVMId, aOptions, 'vmctrl: reboot', True)
            if not _exist and _vmid:
                return 0x0411       # ERROR_411 : VM IS NOT RUNNING
            if not _exist and not _vmid:
                return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED
            if not _vmid:
                return _rc

            _mAutostartSettingErr = None
            _reachability_chk = None
            _timeout = 1800  #default
            if aCluCtrlObj:   
                aCluCtrlObj.mAcquireRemoteLock()
                #_reachability_chk = aCluCtrlObj.mCheckConfigOption('check_vm_reachability_post_bounce')
                #_vm_bounce_options = aCluCtrlObj.mCheckConfigOption('vm_bounce_options')
                _reachability_chk = aCluCtrlObj.mCheckSubConfigOption('vm_bounce_options', 'check_vm_reachability_post_bounce')
                _timeout = int(aCluCtrlObj.mCheckSubConfigOption('vm_bounce_options', 'vm_restart_timeout'))
 
            try:
                _remote_dir = f"/EXAVMIMAGES/GuestImages/{_vmid}/console/write-qemu/"
                _file = _remote_dir + f"lcm_exacloud"
                with connect_to_host(self.__vmctrl.mGetDom0(), get_gcontext()) as _node:
                    if _node.mFileExists(_remote_dir):
                        _cmd_str = f"/bin/touch {_file}"
                        _node.mExecuteCmdLog(_cmd_str)
                    else:
                        ebLogInfo(f"*** write-qemu directory {_remote_dir} not exists on dom0:{self.__vmctrl.mGetDom0()}. Skipping creation of file {_file}")

                _rc = self.__vmctrl.mRebootVM(_vmid, _timeout, _reachability_chk)
                #_rc = self.__vmctrl.mRebootVM(_vmid, _vm_bounce_options)

                _file = f"/EXAVMIMAGES/GuestImages/{_vmid}/console/write-qemu/lcm_exacloud"
                with connect_to_host(self.__vmctrl.mGetDom0(), get_gcontext()) as _node:
                    if _node.mFileExists(_file):
                        _cmd_str = f"/bin/rm -rf {_file}"
                        _node.mExecuteCmdLog(_cmd_str)
                    else:
                        ebLogInfo(f"*** File {_file} not exists on dom0:{self.__vmctrl.mGetDom0()}. Skipping deletion of file {_file}")

            finally:
                if aCluCtrlObj:
                    aCluCtrlObj.mReleaseRemoteLock() 

            if _rc == 0 and _mAutostartSettingErr == 0x0454:
                return _mAutostartSettingErr 
            return _rc

        if aCmd == 'start':
            _vmid, _exist = self.__vmctrl.mCheckVMId(aVMId, aOptions, 'vmctrl: start', False)
            if _exist:
                return 0x0410       # ERROR_410 : VM ALREADY RUNNING
            if not _vmid:
                return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED

            _mAutostartSettingErr = None
            if aCluCtrlObj:   
                aCluCtrlObj.mAcquireRemoteLock()

            try:
 
                _rc = self.__vmctrl.mStartVM(_vmid)
                _autostart_rc = self.__vmctrl.mAutoStartVM(_vmid, True)
                if _autostart_rc:
                    _detail_error = "Failed to enable AutoStart on %s" %(_vmid)
                    ebLogError('*** ' + _detail_error)
                    _mAutostartSettingErr = 0x0454  # ERROR_454 : Failed to change the autostart parameter status

                _file = f"/EXAVMIMAGES/GuestImages/{_vmid}/console/write-qemu/lcm_exacloud"
                with connect_to_host(self.__vmctrl.mGetDom0(), get_gcontext()) as _node:
                    if _node.mFileExists(_file):
                        _cmd_str = f"/bin/rm -rf {_file}"
                        _node.mExecuteCmdLog(_cmd_str)
                    else:
                        ebLogInfo(f"*** File {_file} not exists on dom0:{self.__vmctrl.mGetDom0()}. Skipping deletion of file {_file}")

                if aCluCtrlObj:
                    if self.mCheckCMDAndReboot(aCluCtrlObj, aOptions):
                        _consoleobj = serialConsole(aCluCtrlObj, aOptions)
                        _consoleobj.mRestartContainer(self.__vmctrl.mGetDom0(), _vmid)

            finally:
                if aCluCtrlObj:
                    aCluCtrlObj.mReleaseRemoteLock() 

            if _rc == 0 and _mAutostartSettingErr == 0x0454:
                return _mAutostartSettingErr 
            return _rc

        if aCmd == 'uptime':
            self.__vmctrl.mUptime()
            return 0

        if aCmd == 'vcpuset':
            if not aOptions.vcpuset:
                ebLogError('New value for vcpus required for vcpuset')
                return _rc
            else:
                _vcpu = aOptions.vcpuset

            _vmid, _exist = self.__vmctrl.mCheckVMId(aVMId, aOptions,'vmctrl: vcpuset', True)
            if not _exist and _vmid:
                return 0x0411       # ERROR_411 : VM IS NOT RUNNING
            if not _exist and not _vmid:
                return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED
            if not _vmid:
                return -1

            self.__vmctrl.mSetVcpus(_vmid, _vcpu)

            return 0

        return _rc

# end of file
