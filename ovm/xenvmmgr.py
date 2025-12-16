"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    XenVmMgr - Implement HVMgr interface

FUNCTION:
    Implement HVMgr interface for Xen

NOTE:
    None

History:
    bhpati      09/09/24 - EXACS: PROVISIONING FAILED WITH EXACLOUD ERROR CODE:
                           16 HYPERVISOR STOPPED ON DOM0.
    ritikhan    11/03/23   - ENH 35405135 - VMCLUSTER PAYLOAD CREATION: HANDLE ALL VMS IN SHUT DOWN STATE SCENARIO
    nelson      05/14/2015 - File Creation
    mirivier    11/04/2019 - Add getDom0FreeMem support
    pbellary    02/06/2020 - ENH 30804242 DEVELOP ABSTRACT LAYER FOR HANDLING XEN AND KVM CODE PATHS
    pbellary    02/06/2020 - ENH 30804272 DEVELOP VM OPERATIONS SUPPORT FOR KVM USING VIRSH
    pbellary    10/04/21   - ENH 33056017 - EXACS EXACLOUD. ADD COMPUTE SUPPORT FOR MULTI VM
    bthampi     07/06/23   - ENH 35573065 - CREATE AN API TO GET CPU AND MEMORY DETAILS OF VMS IN A CLUSTER
    pbellary    17/08/2023 - 35714868 - VM CONSOLE - REBOOT VIA UI DOESNT ALLOW CUSTOMER TO GO TO GRUB
    avimonda    10/08/2023 - Bug 35939144 CPU scale introduces whitespaces in
                             vm.cfg file, causing subsequent cpu scale
                             requests to be stuck on reading vm.cfg file
"""

import six
import re
import time
from exabox.ovm.hvmgr import HVMgr
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.ovm.vmconfig import exaBoxVMConfig, exaBoxClusterConfig, ebVMCfg
from tempfile import NamedTemporaryFile
from multiprocessing import Process, Manager
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose

class ebXenVmMgr(HVMgr):

    def __init__(self, *initial_data, **kwargs):
        super(ebXenVmMgr, self).__init__(*initial_data, **kwargs)

        self.__ctx     = get_gcontext()
        self.DomUs    = []      # List of DomUs currently running
        self.DomUsCfg = []      # List of DomUs currently configured
        self.__remotecfg = {}

    def __del__(self):
        self.mShutdown()

    def _getDom0XenInfo(self, aXenInfoField, aRetryTime):
        # TODO: xxx/MR: Review why not using ebLogDebug
        #               Switch to kvm/libvirt driver when available
        _retvalue = 0
        _try_number = 1
        # Retry 3 times since Xend takes sometimes ~10min to be up
        while (_retvalue == 0 and _try_number <= 3):
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(self.hostname)
            _cmdstr = 'xm info |grep \'{}\''.format(aXenInfoField)
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            if _o:
                _out = _o.readlines()
                if not _out:
                    self.mLogDebug('*** Error can not retrieve {} from host: {}'.format(aXenInfoField, self.hostname))
                else:
                    try:
                        _retvalue = int(_out[0].strip().split(":")[1].lstrip())
                    except:
                        ebLogInfo('*** Failed to parse xm info output:({}) to get total memory'.format(_out[0]))
                        pass
            _node.mDisconnect()
            self.mLogDebug("Try number: {} Dom0: {}, {}: {}Mb".format(_try_number,
                                                     self.hostname, aXenInfoField,
                                                     _retvalue))
            if _retvalue == 0:
                _try_number += 1
                time.sleep(aRetryTime) # 3 Min Sleep by default
        return _retvalue

    # These two functions were factorized 
    # RetryTime argument is to speed up unit tests
    def getDom0FreeMem(self, aRetryTime=3*60):
        return self._getDom0XenInfo('free_memory', aRetryTime)

    def getDom0TotalMem(self, aRetryTime=3*60):
        return self._getDom0XenInfo('total_memory',aRetryTime)

    def getTotalVMs(self):
        _total_vms = 0
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(self.hostname)
        _cmdstr = 'xm list -l | grep guest_os_type | wc -l'
        _i, _o, _ = _node.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
            _total_vms = _out[0]
        return _total_vms

    def mListVmsCmd(self):
        return "xm list"

    def mGetDomUList(self):
        _out = []
        _cmdstr = self.mListVmsCmd()
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
        return _cmdstr, _out

    def mGetDom0Info(self):
        _out = []
        _cmdstr = "xm info"
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
        return _cmdstr, _out

    def mGetDom0Logs(self):
        _out = []
        _cmdstr = 'xm log'
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
        return _cmdstr, _out

    def mGetUptime(self):
        _out = []
        _cmdstr = 'xm uptime'
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
        return _cmdstr, _out

    def mGetVcpuList(self):
        _out = []
        _cmdstr = 'xm vcpu-list'
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
        return _cmdstr, _out

    def mVmConfigExist(self, aNode, aDomuName):
        _rc = aNode.mFileExists(_vm_image='/EXAVMIMAGES/GuestImages/%s/vm.cfg' % (aDomuName))
        return _rc

    def mGetDomains(self):
        _domains = []
        _cmdstr = "xm list | awk '!/^Name/ && !/^Domain-0/ {print $1}'"
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = []
            _out = _o.readlines()
            for _line in _out:
                _line = _line.strip()
                if _line:
                    _domains.append(_line)
        return _domains

    def mRetrieveVMID(self, aDomU):
        _vm_id = None
        _domU = aDomU
        _host_cmd = "xm li %s | grep %s | awk '{print $2}'" %(_domU, _domU)
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        if _o:
            _out = _o.readlines()
            if not _out:
                return None
            _vm_id = int(_out[0][:-1])
        return _vm_id

    def mGetVMMemory(self, aDomU, aType):
        _vm_mem = None
        _domU = aDomU
        _type = aType
        if _type == 'CUR_MEM':
            _host_cmd = "xm li %s | grep %s | awk '{ print $3 }'" % (_domU, _domU)
        elif _type == 'MAX_MEM':
            _host_cmd = "xm li %s -l | grep '(maxmem' | tr -d ')' | awk '{ print $2 }'" % (_domU)
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        if _o:
            _out = _o.readlines()
            if not _out:
                return None
            _vm_mem = int(_out[0][:-1])
        return _vm_mem

    def mGetVMMemoryFromConfig(self, aDomU):
        _vm_mem = 0
        _domU = aDomU
        _filename = "/EXAVMIMAGES/GuestImages/{0}/vm.cfg".format(_domU)
        _exists = self.mFileExists(_filename)
        if _exists:
            _host_cmd = """/bin/grep -i 'memory = ' %s | /bin/awk -F "'" '{print $2}' """ %(_filename)
            _, _o, _ = self.mExecuteCmd(_host_cmd)
            if _o:
                _out = _o.readlines()
                if not _out:
                    return None
                _vm_mem = int(_out[0][:-1])
        return _vm_mem
    
    def mGetVMCpu(self, aDomU, aType):
        _vm_cpu = 0
        _domU = aDomU
        _type = aType
        _host_cmd = ""
        if _type == 'CUR_CPU':
            _host_cmd = "/usr/sbin/xm li %s | /bin/grep %s | /bin/awk '{ print $4 }'" % (_domU, _domU)
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        if _o:
            _out = _o.readlines()
            if not _out:
                return None
            ebLogInfo('command _out : ' + str(_out))
            _vm_cpu = int(_out[0].strip())
        return _vm_cpu

    def mGetVMCPUFromConfig(self, aDomU):
        _vm_cpu = 0
        _domU = aDomU
        _filename = "/EXAVMIMAGES/GuestImages/{0}/vm.cfg".format(_domU)
        _exists = self.mFileExists(_filename)
        if _exists:
            _host_cmd = """/bin/grep -i ^'vcpus = ' %s | /bin/awk  '{print $3}' """ %(_filename)
            _, _o, _ = self.mExecuteCmd(_host_cmd)
            if _o:
                _out = _o.readlines()
                if not _out:
                    return None
                _vm_cpu = int(_out[0][:-1])
        return _vm_cpu

    def mNodeType(self):

        hostcmd = 'cat /sys/hypervisor/type /sys/hypervisor/uuid'
        fin, fout, ferr = self.mExecuteCmd(hostcmd)

        if fout:
            rl = fout.readlines()
            if len( rl ) != 2:
                ebLogWarn('Unexecpected output:' + str(rl) + ' VM Node not found (defaulting to BM node)')
                # VM Node more than likely
                self.hypervisor = None
                self.dom0 = False
                self.uuid = None
            else:
                self.hypervisor = rl[0][:-1]
                self.uuid = rl[1][:-1]

            if self.uuid == '00000000-0000-0000-0000-000000000000':
                self.dom0 = True
            else:
                self.dom0 = False
        return self.hypervisor, self.dom0, self.uuid

    def mRefreshDomUs(self):
        hostcmd = 'xm list'
        fin, fout, ferr = self.mExecuteCmd(hostcmd)
        out = fout.readlines()
        if out:
            # Skip header and Domain0
            self.DomUs = []
            for e in out[2:]:
                self.DomUs.append(e[:-1].split(' ')[0])
        return self.DomUs

    def mRefreshDomUsCfg(self):
        _hostcmd = 'ls /EXAVMIMAGES/GuestImages/'
        fin, fout, ferr = self.mExecuteCmd(_hostcmd)
        out = fout.readlines()
        if out:
            for _domu in out:
                _domu = _domu.strip()
                self.DomUsCfg.append(_domu)
        return self.DomUsCfg

    def mReadRemoteCfg(self, aRemoteVMName=None, aRemoteCfgPath=None):

        if aRemoteVMName and not aRemoteCfgPath:
            aRemoteCfgPath = '/EXAVMIMAGES/GuestImages/'+aRemoteVMName+'/vm.cfg'

        if aRemoteCfgPath:
            ebLogInfo('Reading remote cfg file: ' + aRemoteCfgPath)
            sedcmd = " | /usr/bin/sed -e 's/^[[:space:]]*//; s/[[:space:]]*$//'"
            hostcmd = '/usr/bin/cat ' + aRemoteCfgPath + sedcmd
            fin, fout, ferr = self.mExecuteCmd(hostcmd)
            out = fout.readlines()
            if out:
                data = ''
                for e in out:
                    e = e.strip()
                    data  = data + e + '\n'
                vmName = aRemoteCfgPath.split('/')[3]
                vmcfgobj = ebVMCfg(self.__ctx, aConfigData=data)
                vmConfig = { 'vmname': vmName, 'rpath': aRemoteCfgPath, 'cfgData': data, 'cfgObj':vmcfgobj }
                self.__remotecfg[ vmName ] = vmConfig
            else:
                ebLogWarn('Remote cfg file not found or unreadable')

    def mDumpOVSVMConfig(self, aVMName):

        self.mReadRemoteCfg(aRemoteVMName=aVMName)
        vmCfg = self.mGetOVSVMConfig(aVMName)
        vmCfg.mDumpConfig()

    def mPatchOVSVMConfig(self, aVMName, aList=None):

        self.mReadRemoteCfg(aRemoteVMName=aVMName)
        vmCfg = self.mGetOVSVMConfig(aVMName)

        xList = aList.split(';')
        for e in xList:
            k,v = e.split('=')
            if k not in [ "vcpus", "memory", "maxmem", ]:
                ebLogInfo("Unsuported key: " + k)
                continue
            ebLogInfo('Setting: ' + k + '=' + v)
            vmCfg.mSetValue(k,v)

        # TODO: Add verbose/debug mode for conditional output
        if 0:
            vmCfg.mDumpConfig()

        ntmp = NamedTemporaryFile()
        ntmp.file.write(six.ensure_binary(vmCfg.mRawConfig()))
        ntmp.file.close()
        vmPath='/EXAVMIMAGES/GuestImages/'+aVMName+'/vm.cfg'
        vmPathO='/EXAVMIMAGES/GuestImages/'+aVMName+'/vm.cfg.prev'
        self.mExecuteCmdLog('cp '+vmPath+' '+vmPathO)
        self.mCopyFile(ntmp.name,vmPath)

    def mGetOVSVMConfig(self, aVMName):
        """
        :param aVMName: VMName string corresponding to the vm.cfg to return
        :return: OVS VM Object already parsed
        """
        try:
            return self.__remotecfg[ aVMName ]['cfgObj']
        except:
            ebLogWarn('::mGetOVSVMConfig() not found for: '+aVMName)
            return None

    def mGetOVSVMList(self):

        return self.__remotecfg.keys()

    def mReadRemoteAllCfg(self, aOptions=None, aForce=False):

        if self.__remotecfg and not aForce:
            return

        hostcmd = 'ls /EXAVMIMAGES/GuestImages/*/vm.cfg'
        fin, fout, ferr = self.mExecuteCmd(hostcmd)
        out = fout.readlines()
        if out:
            for e in out:
                self.mReadRemoteCfg( aRemoteCfgPath=e[:-1] )

    def mPruneOVSRepo(self, aOptions):

        uuid_list = []
        hostcmd = 'ls /OVS/Repositories/'
        fin, fout, ferr = self.mExecuteCmd(hostcmd)
        out = fout.readlines()
        if out:
            for e in out:
                uuid = e[:-1]
                if len(uuid) == 32:
                    uuid_list.append( uuid )
                else:
                    ebLogInfo('Discarding non UUID directory: ' + uuid)

        for e in self.mGetOVSVMList():
            uuid = self.mGetOVSVMConfig(e).mGetValue('uuid')[1:-1]
            try:
                uuid_list.remove( uuid )
            except:
                ebLogError('*** UUID/LIST: '+str(uuid)+' - '+str(uuid_list))

        for e in uuid_list:
            lConfigPath = '/OVS/Repositories/'+e
            hostcmd = 'rm -rf '+lConfigPath
            if aOptions.force:
                self.mExecuteCmdLog(hostcmd)
                ebLogInfo('Removing : ' + lConfigPath)
            else:
                ebLogInfo('Use force option to remove: ' + lConfigPath)

    def mCreateVM(self, aVMId, aPubKey=None):
        _vmid = aVMId
        _public_key = aPubKey
        _cfgpath = '/EXAVMIMAGES/conf/final-' + _vmid + '-vm.xml'

        if _public_key:
            _cmd_str = f"""export EXADATA_SKIP_DOMU_NETWORK_CHECK=yes;/opt/exadata_ovm/exadata.img.domu_maker start-domain {_cfgpath} -locked -ssh-key {_public_key}"""
        else:
            _cmd_str = f"""export EXADATA_SKIP_DOMU_NETWORK_CHECK=yes;/opt/exadata_ovm/exadata.img.domu_maker start-domain {_cfgpath} -locked"""
        self.mExecuteCmdLog(_cmd_str)
        return 0

    def mDeleteVM(self, aVMId):
        _vmid = aVMId
        self.mExecuteCmdLog('/opt/exadata_ovm/exadata.img.domu_maker remove-domain '+_vmid)
        return 0

    """
    ::mLogListVms

    Logs the configured VMs and also the running VMs, by executing 2 commands on the node.

    return 0

    """
    def mLogListVms(self):
        ebLogDebug('VM Configured:')
        hostcmd = 'ls /EXAVMIMAGES/GuestImages/*/vm.cfg 2> /dev/null'       # Fix for 22229739
        self.mExecuteCmdLog(hostcmd)

        ebLogDebug('VM Running:')
        hostcmd = 'xm list'
        self.mExecuteCmdLog(hostcmd)

        return 0

    def mStatus(self):
        _host_cmd = 'xentop -b -r  -i 1'
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mInfo(self):
        _host_cmd = 'xm info'
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mVMInfo(self, aVMId):
        _vmid = aVMId
        _host_cmd = 'xm list -l ' + _vmid
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mDestroyVM(self, aVMId, aStaleDir=False):
        _vmid = aVMId
        _host_cmd = 'xm destroy ' + _vmid
        self.mExecuteCmdLog(_host_cmd)

        if aStaleDir:
            _cmd_str = f"/bin/rm -rf /EXAVMIMAGES/GuestImages/{_vmid}/"
            self.mExecuteCmdLog(_cmd_str)
        return 0

    def mRebootVM(self, aVMId):
        _vmid = aVMId
        _host_cmd = 'xm reboot ' + _vmid
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mStartVM(self, aVMId):
        _vmid = aVMId
        _host_cmd = 'xm create /EXAVMIMAGES/GuestImages/'+_vmid+'/vm.cfg'
        _i, _o, _e = self.mExecuteCmd(_host_cmd)
        _rc = self.mGetCmdExitStatus()
        if _rc:
            ebLogError('*** XM CREATE failed for : %s / %s' % (str(_rc), _vmid))

            for _line in _o.readlines():
                ebLogError('*** XM CREATE O_LOG: %s' % (_line))

            for _line in _e.readlines():
                ebLogError('*** XM CREATE E_LOG: %s' % (_line))

                # Calling destroy when the vm is already running
                if self.mGetDestroyOnStart():
                    _patt = re.search("already exists with ID '([0-9]{1,})'", _line)

                    if _patt is not None:
                        _tmpVmId = _patt.group(1)
                        ebLogInfo("Calling destroy on vmid: {0}".format(_tmpVmId))
                        hostcmd = 'xm destroy {0}'.format(_tmpVmId)
                        self.mDestroyVM(_tmpVmId)

        return _rc

    def mShutdownVM(self, aVMId):
        _vmid = aVMId
        _host_cmd = 'xm shutdown ' + _vmid
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mCheckAutoStart(self, aVMId):
        _vmid = aVMId
        _autoCheckEnabled = False
        _autoStartPath = "/etc/xen/auto/{0}.cfg".format(aVMId)
        if self.mFileExists(_autoStartPath):
            _autoCheckEnabled = True
        return _autoCheckEnabled

    def mAutoStartVM(self, aVMId, aEnabled):

        _autoStartPath = "/etc/xen/auto/{0}.cfg".format(aVMId)

        if aEnabled:

            if not self.mFileExists(_autoStartPath):

                self.mReadRemoteCfg(aRemoteVMName=aVMId)
                _vmCfg = self.mGetOVSVMConfig(aVMId)

                if _vmCfg:

                    _uuid = re.sub("[\'\"\s]", "", _vmCfg.mGetValue('uuid')[1:-1])
                    _ovsPath = "/OVS/Repositories/{0}/vm.cfg".format(_uuid)

                    if self.mFileExists(_ovsPath):

                        self.mExecuteCmdLog("/bin/ln -s {0} {1}".format(_ovsPath, _autoStartPath))
                        return self.node.mGetCmdExitStatus()

                    else:
                        ebLogWarn("OVS VM File not found for VM: {0} [{1}]".format(aVMId, _ovsPath))
                        return 1

                else:
                    ebLogWarn("Remote vm.cfg file not found for VM: {0}".format(aVMId))
                    return 1

        else:

            if self.mFileExists(_autoStartPath):
                self.mExecuteCmdLog("/bin/unlink {0}".format(_autoStartPath))
                return self.node.mGetCmdExitStatus()

        return 0


    def mUptime(self):
        _host_cmd = 'xm uptime'
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mSetVcpus(self, aVMId, aVcpuset):

        _domU = aVMId
        _cores = aVcpuset

        _maxRetries = 3
        _retries = 0
        _updateSuccess = False

        while _retries < _maxRetries:

            _cmd = f'/opt/exadata_ovm/exadata.img.domu_maker vcpu-set {_domU} {_cores}'

            if _retries != 0:
                _cmd = f"{_cmd} --force"

            self.mExecuteCmdLog(_cmd)

            if self.node.mGetCmdExitStatus() == 0:
                _updateSuccess = True
                break
            else:
                time.sleep(5)

            _retries += 1

        if not _updateSuccess:
            _msg = f"VCPU-SET not applied in {_domU} with {_cores}"
            raise ExacloudRuntimeError(0x0436, 0xA, _msg)

        return 0

    def mGetHVStatus(self):
        _host_cmd = "service xend status | grep running"
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        if self.mGetCmdExitStatus():
            _start_cmd = "service xend start"
            ebLogInfo('*** xend service stopped on DOM0:{0}. Starting xend service.'.format(self.hostname))
            _, _stdout, _stderr = self.mExecuteCmd(_start_cmd)
            if self.mGetCmdExitStatus():
                ebLogError(f"*** xend service failed to start on {self.hostname} with stderr: {_stderr.read().strip()} and stdout: {_stdout.read().strip()}")
            _, _o, _ = self.mExecuteCmd(_host_cmd)
            if self.mGetCmdExitStatus():
                ebLogError('*** xend service stopped on DOM0:{0}'.format(self.hostname))
                return "stopped"
            else:
                ebLogInfo('*** xend service running on DOM0:{0}'.format(self.hostname))
                return "running"
        ebLogInfo('*** xend service running on DOM0:{0}'.format(self.hostname))
        return "running"

    def mGetVmStatus(self, aDomu):
        _cmd = "/usr/sbin/xm li | /bin/grep %s | /bin/awk '{ print $5; }'" % aDomu
        _, _o, _ = self.mExecuteCmd(_cmd)
        _ret = self.mGetCmdExitStatus()
        _status = None
        if _ret == 0 and _o:
            _out = _o.readlines()
            _status = _out[0].strip()
            ebLogInfo('Status for the domu: {0} is {1}'.format(aDomu, _status))
        else:
            ebLogError('Unable to get status for the domu {0}'.format(aDomu))
        return _status
