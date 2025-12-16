"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    KVM - Functionality implementation layer for the HVMMgr

FUNCTION:
    Implement HVMMgr methods for KVM

NOTE:
    None

History:
    bhpati      09/09/24 - EXACS: PROVISIONING FAILED WITH EXACLOUD ERROR CODE:
                           16 HYPERVISOR STOPPED ON DOM0.
    pbellary    02/02/24   - Bug 36253784 - NODE RECOVERY : /U02 ON VM RESTORED FROM VM BACKUP 
                             IS NOT MOUNTED PROPERLY RESULTING IN MISSING DATA
    dekuckre    11/23/23   - 36034424: Fix vm_maker stop domain cmd used.
    joysjose    11/22/23   - Bug 36008772 - EXACLOUD USES A WRONG COMMAND TO STOP VM
    ritikhan    11/03/23   - ENH 35405135 - VMCLUSTER PAYLOAD CREATION: HANDLE ALL VMS IN SHUT DOWN STATE SCENARIO 
    pbellary    10/18/23   - Bug SYSTEM FIRST BOOT IMAGE FILE GETS REMOVED DURING IN-PLACE REPLACEMENT 
    talagusu    13/11/2023 - 35990847 - VM SHUTDOWN RETRY LOGIC NOT DISABLING AUTOSTART
    pbellary    10/18/2023   - Bug SYSTEM FIRST BOOT IMAGE FILE GETS REMOVED DURING IN-PLACE REPLACEMENT 
                             PROCESS CAUSING FAILURE OF "EXAUNIT-ATTACH-COMPUTE" OPERATION
    bthampi     07/06/2023   - ENH 35573065 - CREATE AN API TO GET CPU AND MEMORY DETAILS OF VMS IN A CLUSTER
    pbellary    10/04/2021   - ENH 33056017 - EXACS EXACLOUD. ADD COMPUTE SUPPORT FOR MULTI VM
    pbellary    02/06/2020 - ENH 30804242 DEVELOP ABSTRACT LAYER FOR HANDLING XEN AND KVM CODE PATHS
    pbellary    02/06/2020 - ENH 30804272 DEVELOP VM OPERATIONS SUPPORT FOR KVM USING VIRSH
    siyarlag    01/22/2020 - support vm operations on x8m 
    mirivier    08/20/2019 - Revamped initial file
"""

from exabox.ovm.hvmgr import HVMgr
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.tools.oedacli import OedacliCmdMgr
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.utils.node import connect_to_host

import socket
import time
from ast import literal_eval

class ebKvmVmMgr(HVMgr):

    def __init__(self, *initial_data, **kwargs):
        super(ebKvmVmMgr, self).__init__(*initial_data, **kwargs)

        self.DomUs    = []      # List of DomUs currently running
        self.DomUsCfg = []      # List of DomUs currently configured
        self.__configPath = None
        self.__oedaPath   = None

    def __del__(self):
        self.mShutdown()

    def setExtraConfig(self, aConfigPath, aOedaPath):
        self.__configPath = aConfigPath
        self.__oedaPath = aOedaPath

    def getDom0FreeMem(self, aVirshMode=False):
        # TODO: xxx/MR: Review why not using ebLogDebug
        #               Switch to kvm/libvirt driver when available
        _freeMem = 0
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(self.hostname)

        if aVirshMode:
            _cmdstr = "/usr/bin/virsh nodememstats | /bin/grep -E 'free|cached'"
        else:
            _cmdstr = '''/usr/sbin/vm_maker --list --memory | /bin/grep "all 'autostart enabled domains' restart)" '''
        _i, _o, _ = _node.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
            if not _out:
                self.mLogDebug('*** Error can not retrieve free memory from host: %s' % (self.hostname))
                _node.mDisconnect()
                return 0
            _freeMem = 0
            _cached  = 0
            _total_freeMem = 0
            try:
                if aVirshMode:
                    _freeMem = int(_out[0].split()[2]) / 1024
                    _cached  = int(_out[1].split()[2]) / 1024
                    _total_freeMem = _freeMem + _cached
                else:
                    _total_freeMem = int(_out[0].split(':')[1].split()[0])
            except:
                pass
            _node.mDisconnect()
        self.mLogDebug("Dom0: %s, freemem: %sMb" % (self.hostname, _total_freeMem))
        return _total_freeMem

    def getDom0TotalMem(self, aVirshMode=False):
        _totalMem = 0
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(self.hostname)
        if aVirshMode:
            _cmdstr = '/usr/bin/virsh nodememstats | /bin/grep total'
        else:
            _cmdstr = '/usr/sbin/vm_maker --list --memory | /bin/grep "Total OS memory"'
        _i, _o, _ = _node.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
            if not _out:
                self.mLogDebug('*** Error can not retrieve total memory from host: %s' % (self.hostname))
                _node.mDisconnect()
                return 0
            _totalMem = 0
            try:
                if aVirshMode:
                    _totalMem = int(_out[0].split()[2]) / 1024
                else:
                    _totalMem = int(_out[0].split()[4])
            except:
                pass
            _node.mDisconnect()
        self.mLogInfo("Dom0: %s, totalmem: %sMb" % (self.hostname, _totalMem))
        return _totalMem

    def getTotalVMs(self, aVirshMode=False):
        _total_vms = 0
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(self.hostname)
        if aVirshMode:
            _cmdstr = '/usr/bin/virsh list | /bin/grep running | wc -l'
        else:
            _cmdstr = '/usr/sbin/vm_maker --list-domains | /bin/grep running | wc -l'
        _i, _o, _ = _node.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
            _total_vms = _out[0]
        return _total_vms

    # Local Execute Command api
    def mExecuteCmdOedaCli(self, _cmdstr, _hostId):
        _ctx = get_gcontext()
        self.mLogDebug(_ctx)
        if _ctx:
            _hostname = _hostId if _hostId else self.hostname
            with connect_to_host(_hostname, get_gcontext()) as _node:
                self.mLogDebug(_node)
                fin, fout, ferr = _node.mExecuteCmd(_cmdstr)
                return fin, fout, ferr
        else:
            self.mLogError("Empty Context")
            return -1

    # Refresh KVM DomUs and update the global DomUs variable
    def mRefreshDomUsOedacli(self):
        hostcmd = 'vm_maker --list|grep running'
        #TODO: Above command will not always work. When this command is used right after a vm operation, then 
        # vm_maker continues to give below error atleast for a few seconds :
        # "Another instance of /usr/sbin/vm_maker  is running. Exiting."
        # In such cases, though the vm shutdown operation actually succeeded, we are unable to get the correct vm status because
        # of the way we check for status.
        # I think its better to check for vm status via oedacli, instead of vm_maker, since the
        # actual shutdown/start operation is done via oedacli.
        

        fin, fout, ferr = self.mExecuteCmdOedaCli(hostcmd, None)
        out = fout.readlines()
        if out:
            self.DomUs = []
            for e in out:
                self.DomUs.append(e[:-1].split('(')[0])

    # Existence Check of VMId. Based on the caller request returns
    #  appropriate return code
    def mCheckVMIdOedaCli(self, aVMId, aErrorStr, aCheckVMExist=False):

        # Update/Refresh running DomUs list
        self.mRefreshDomUsOedacli()

        _vmid = aVMId
        if not _vmid:
            self.mLogError(aErrorStr)
            return None, False
        _exist = False

        # Check name resolution
        try:
            socket.gethostbyname(_vmid)
        except socket.gaierror:
            self.mLogWarn('Hostname (%s) could not be resolved please check hostname and domain name' % _vmid)

        # Check if VM is running
        if aCheckVMExist:
            if not _vmid in self.DomUs:
                self.mLogError('Currrent operation expecting VM: ' + _vmid+' to be running ('+aErrorStr+')')
                self.mLogDebug('VM currently Running:')
                for vm in self.DomUs:
                    self.mLogInfo(vm)
            else:
                _exist = True

        # Check if VM is _not_ running
        if not aCheckVMExist:
            if _vmid in self.DomUs:
                self.mLogError('Currrent operation does not expect VM: ' + _vmid+' to be running ('+aErrorStr+')')
                self.mLogDebug('VM currently Running:')
                for vm in self.DomUs:
                    self.mLogInfo(vm)
                _exist = True

        return _vmid, _exist

    # Reachability check of hostname using ping
    def mPingHostOedaCli(self,aHostname,aCount=4):

        _host = aHostname
        _ctx = get_gcontext()
        if _ctx.mCheckRegEntry('_natHN_' + _host):
            _host = _ctx.mGetRegEntry('_natHN_' + _host)
            self.mLogDebug('*** CONN_PING_USING_NATHN: %s/%s' % (aHostname, _host))

        _count = aCount
        while _count:
            cmd = f'/bin/ping -c 1 {_host}'
            eboxNodeObject = exaBoxNode(get_gcontext())
            _rc, _, _, _ = eboxNodeObject.mExecuteLocal(cmd)
            if _rc == 0:
                return True
            _count -= 1
            if _count:
                self.mLogWarn('*** Ping Failed retrying for host: %s' % (_host))

        return False

    # ping domU
    def pingVMOedaCli(self, domU):
        _rc = (-1 << 16 ) | 0x0000

        _vmid, _exist = self.mCheckVMIdOedaCli(domU, 'kvmctrl: ping', True)
        if not _exist and _vmid:
            return 0x0411       # ERROR_411 : VM IS NOT RUNNING
        if not _exist and not _vmid:
            return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED
        if not _vmid:
            return _rc
        _rc = self.mPingHostOedaCli(_vmid)
        if _rc is True:
            return 0
        else:
            return 0x0411
        return 0

    # start domU - run oedacli command
    def startDomU(self, domU):
        ebox = self.eboxObject
        _rc = (-1 << 16 ) | 0x0000

        self.mLogInfo("Starting VM: %s on %s" % (domU, self.hostname))
        # TODO: When vms have a low cpu count such as 2, oedacli/vm_maker fails. It needs a minimum of 4 vcpus.
        
        _vmid, _exist = self.mCheckVMIdOedaCli(domU, 'kvmctrl: start', False)
        if _exist:
            return 0x0410       # ERROR_410 : VM ALREADY RUNNING
        if not _vmid:
            return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED

        _configpath = self.__configPath
        _oeda_path  = self.__oedaPath
        _oedacli_bin = _oeda_path + '/oedacli'
        _savexmlpath = '/tmp/'
        _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath )
        _oedacli_mgr.mVMOperation(_vmid, _configpath, _savexmlpath+'startedvm.xml', 'start')

        _vmid, _exist = self.mCheckVMIdOedaCli(domU, 'kvmctrl: start', True)
        if _exist:
            self.mLogInfo('*** Successfully Started VM: {0}'.format(_vmid))
            return 0
        else:
            self.mLogError('Failed to Start VM: {0}'.format(_vmid))
            return -1

    # stop domU - run oedacli command
    def stopDomU(self, domU):
        ebox = self.eboxObject
        _rc = (-1 << 16 ) | 0x0000

        self.mLogInfo("Stopping VM: %s on %s" % (domU, self.hostname))
        _vmid, _exist = self.mCheckVMIdOedaCli(domU, 'kvmctrl: shutdown', True)
        if not _exist and _vmid:
            return 0x0411       # ERROR_411 : VM IS NOT RUNNING
        if not _exist and not _vmid:
            return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED
        if not _vmid:
            return _rc

        _configpath = self.__configPath
        _oeda_path  = self.__oedaPath
        _oedacli_bin = _oeda_path + '/oedacli'
        _savexmlpath = '/tmp/'
        _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath )
        _oedacli_mgr.mVMOperation(_vmid, _configpath, _savexmlpath+'stoppedvm.xml', 'stop')

        _vmid, _exist = self.mCheckVMIdOedaCli(domU, 'kvmctrl: shutdown', False)
        if not _exist:
            self.mLogInfo('*** Successfully Shutdown VM: {0}'.format(_vmid))
            return 0
        else:
            self.mLogError('Failed to Shutdown VM: {0}'.format(_vmid))
            return -1


    # restart or bounce domU - run oedacli command
    def restartDomU(self, domU):
        ebox = self.eboxObject
        _rc = (-1 << 16 ) | 0x0000

        self.mLogInfo("Restarting VM: %s on %s" % (domU, self.hostname))
        _vmid, _exist = self.mCheckVMIdOedaCli(domU, 'kvmctrl: restart', True)
        if not _exist and _vmid:
            return 0x0411       # ERROR_411 : VM IS NOT RUNNING
        if not _exist and not _vmid:
            return 0x0412       # ERROR_412 : VMID INVALID OR VM NOT CONFIGURED
        if not _vmid:
            return _rc

        _configpath = self.__configPath
        _oeda_path  = self.__oedaPath
        _oedacli_bin = _oeda_path + '/oedacli'
        _savexmlpath = '/tmp/'
        _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath )
        _oedacli_mgr.mVMOperation(_vmid, _configpath, _savexmlpath+'restartedvm.xml', 'restart')

        _vmid, _exist = self.mCheckVMIdOedaCli(domU, 'kvmctrl: restart', True)
        if _exist:
            self.mLogInfo('*** Successfully Restarted VM: {0}'.format(_vmid))
            return 0
        else:
            self.mLogError('Failed to Restart VM: {0}'.format(_vmid))
            return -1


    def mListVmsCmd(self, aVirshMode=False):
        if aVirshMode:
            return "/usr/bin/virsh list"
        else:
            return "/usr/sbin/vm_maker --list-domains | /bin/grep running"

    def mGetDomUList(self):
        _out = []
        _cmdstr = self.mListVmsCmd()
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
        return _cmdstr, _out

    def mGetDom0Info(self):
        _out = []
        _cmdstr = "virsh nodeinfo"
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
        return _cmdstr, _out

    def mGetDom0Logs(self):
        return [], 'NO_OPERATION'

    def mGetVcpuList(self):
        _cmdstr = self.mListVmsCmd()
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        _domu_list = self.mRefreshDomUs()

        _domu_vcpus = dict()
        for _domU in _domu_list:
            _cmdstr = "virsh vcpuinfo " + _domU + " --pretty | grep VCPU | awk '{print$2}'"
            _i, _o, _ = self.mExecuteCmd(_cmdstr)
            if _o:
                _out = _o.readlines()
                _vcpu = []
                for _line in _out:
                        _vcpu.append(_line.lstrip().rstrip())
            _domu_vcpus[_domU] = _vcpu

        return _cmdstr, _domu_vcpus

    def mGetUptime(self):
        return [], 'NO_OPERATION'

    def mVmConfigExist(self, aNode, aDomuName):
        return False

    def mGetDomains(self, aVirshMode=False):
        _domains = []
        if aVirshMode:
            _cmdstr = "/usr/bin/virsh list --name --state-running"
        else:
            _cmdstr = "/usr/sbin/vm_maker --list-domains | /bin/grep running"
        _i, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = []
            _out = _o.readlines()
            for _line in _out:
                _line = _line.strip()
                if _line:
                    if aVirshMode:
                        _domains.append(_line)
                    else:
                        _domains.append(_line.strip().split('(')[0])
        return _domains

    def mRetrieveVMID(self, aDomU, aVirshMode=False):
        _vm_id = None
        _domU = aDomU
        if aVirshMode:
            _host_cmd = "/usr/bin/virsh list | /bin/grep %s | /bin/awk '{print $1}'" %(_domU)
        else:
            _host_cmd = "/usr/sbin/vm_maker --list --domain %s --detail | /bin/grep 'Id:'" %(_domU)
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        if _o:
            _out = _o.readlines()
            if not _out:
                return None
            if aVirshMode:
                _vm_id = int(_out[0][:-1])
            else:
                _vm_id = int(_out[0].strip().split()[1])
        return _vm_id

    def mGetVMMemory(self, aDomU, aType, aVirshMode=False):
        _vm_mem = 0
        _domU = aDomU
        _type = aType
        if _type == 'CUR_MEM':
            if aVirshMode:
                _host_cmd = "/usr/bin/virsh dominfo %s | /bin/grep 'Used memory' | /bin/awk '{ print $3/1024 }'" %(_domU)
            else:
                _host_cmd = "/usr/sbin/vm_maker --list --memory --domain %s | /bin/grep ^%s" %(_domU, _domU)
        elif _type == 'MAX_MEM':
            _host_cmd = "/usr/bin/virsh dominfo %s | /bin/grep 'Max memory' | /bin/awk '{ print $3/1024 }'" %(_domU)
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        _rc = self.mGetCmdExitStatus()
        if _rc == 0 and _o:
            _out = _o.readlines()
            if not _out:
                return None
            if aVirshMode or _type == 'MAX_MEM':
                _vm_mem = int(_out[0][:-1])
            else:
                _vm_mem = int(_out[0].strip().split()[-1])
     
        return _vm_mem

    def mGetVMMemoryFromConfig(self, aDomU):
        _vm_mem = 0
        _domU = aDomU
        _filename = "/etc/libvirt/qemu/{0}.xml".format(_domU)
        _exists = self.mFileExists(_filename)
        if _exists:
            _host_cmd = """/bin/grep -i 'currentMemory' %s | /bin/awk -F "[><]" '{print $3/1024}' """%(_filename)
            _, _o, _ = self.mExecuteCmd(_host_cmd)
            if _o:
                _out = _o.readlines()
                if not _out:
                    return None
                _vm_mem = int(_out[0][:-1])
        return _vm_mem

    def mGetVMCpu(self, aDomU, aType, aVirshMode=False):
        _vm_cpu = 0
        _domU = aDomU
        _type = aType
        _host_cmd = ""
        if _type == 'CUR_CPU':
            if aVirshMode:
                _host_cmd = "/usr/bin/virsh dominfo %s | /bin/grep 'CPU(s)' | /bin/awk '{ print $2}' " %(_domU)
            else:
                _host_cmd = f"/usr/sbin/vm_maker --list --vcpu --domain {_domU} | /bin/grep {_domU}"
        else:
            return None
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        _rc = self.mGetCmdExitStatus()

        if _rc == 0 and _o:
            _out = _o.readlines()
            if not _out:
                return None
            else:
                _vm_cpu = int(_out[0].strip().split()[-1])
        return _vm_cpu

    def mGetVMCPUFromConfig(self, aDomU):
        _vm_cpu = 0
        _domU = aDomU
        _filename = "/etc/libvirt/qemu/{0}.xml".format(_domU)
        _exists = self.mFileExists(_filename)
        if _exists:
            _host_cmd = """/usr/bin/xmllint --xpath /domain/vcpu/@current %s | /bin/awk -F'=' '{print $2}' """%(_filename)
            _, _o, _ = self.mExecuteCmd(_host_cmd)
            if _o:
                _out = _o.readlines()
                if not _out:
                    return None
                _vm_cpu = int(_out[0][:-1])
        return _vm_cpu

    def mSetVMMemory(self, aDomU, aMemSizeMB, aRestart=False):
        _domU = aDomU
        _memsizeMB = aMemSizeMB

        if aRestart:
            _host_cmd = "/opt/exadata_ovm/vm_maker --set --memory "+_memsizeMB+" --domain "+ _domU + "  --restart-domain"
        else:
            _host_cmd = "/opt/exadata_ovm/vm_maker --set --memory "+_memsizeMB+" --domain "+ _domU

        _i, _o, _e = self.mExecuteCmd(_host_cmd)
        _rc = self.mGetCmdExitStatus()
        if _rc:
            ebLogError('*** KVM SET VM MEMORY failed for : %s / %s' % (str(_rc), _domU))
            for _line in _o.readlines():
                ebLogError('*** KVM SET VM MEMORY O_LOG: %s' % (_line))
            for _line in _e.readlines():
                ebLogError('*** KVM SET VM MEMORY E_LOG: %s' % (_line))


        if _rc and aRestart:
            _rc = self.mShutdownVM2(_domU)
            if _rc == 0:
                ebLogInfo('*** Successfully Shutdown VM: {0}'.format(_domU))
            else:
                return _rc
            _rc = self.mStartVM(_domU)
            if _rc:
                return _rc

        if _rc == 0 and aRestart:
            _domUs = self.mRefreshDomUs()
            if _domU in _domUs:
                ebLogInfo('*** Successfully Started VM: {0}'.format(_domU))
                _currvmem = self.mGetVMMemory(_domU, 'CUR_MEM')
                ebLogInfo('*** CUR_MEM for domU %s : %d' % (_domU, _currvmem))
                _memsize = literal_eval(_memsizeMB[:-1])
                if int(_memsize) == _currvmem:
                    ebLogInfo('*** Requested memory is updated successfully on host: {0}'.format(_domU))
                return _rc
            return -1

        return _rc

    def mNodeType(self):
        self.hypervisor = None
        self.uuid = None
        self.dom0 = False

        _cmdstr = "imageinfo | grep 'Node type:'"
        _, _o, _ = self.mExecuteCmd(_cmdstr)
        if _o:
            _out = _o.readlines()
            if not _out:
                ebLogError('*** Error can not retrieve HV Instance Type from host: %s' % (self.hostname))
                return self.hypervisor, self.dom0, self.uuid 
            try:
                _hviType = _out[0].split()[2]
                if _hviType == 'KVMHOST':
                    self.dom0 = True
                    self.uuid = "00000000-0000-0000-0000-000000000000"
                    self.hypervisor = "KVMHOST"
                if _hviType == 'GUEST':
                    self.dom0 = False
                    self.hypervisor = "GUEST"
                    self.uuid = None
            except:
                pass

        return self.hypervisor, self.dom0, self.uuid

    def mRefreshDomUs(self, aVirshMode=False):
        self.DomUs = []
        if aVirshMode:
            _host_cmd = '/usr/bin/virsh list | /bin/grep running'
        else:
            _host_cmd = "/usr/sbin/vm_maker --list-domains | /bin/grep 'running' | /bin/awk '{print $1}'"
        fin, fout, ferr = self.mExecuteCmd(_host_cmd)
        out = fout.readlines()
        if out:
            for e in out:
                e = e.strip()
                if e:
                    if aVirshMode:
                        self.DomUs.append(e[:-1].split()[1])
                    else:
                        self.DomUs.append(e.split('(')[0])

        return self.DomUs

    def mRefreshDomUsCfg(self):
        self.DomUsCfg = []
        _host_cmd = 'ls /EXAVMIMAGES/GuestImages/'
        fin, fout, ferr = self.mExecuteCmd(_host_cmd)
        out = fout.readlines()
        if out:
            for _domu in out:
                _domu = _domu.strip()
                self.DomUsCfg.append(_domu)
        return self.DomUsCfg

    def mReadRemoteCfg(self, aRemoteVMName=None, aRemoteCfgPath=None):
        raise NotImplementedError

    def mDumpOVSVMConfig(self, aVMName):
        raise NotImplementedError

    def mPatchOVSVMConfig(self, aVMName, aList=None):
        raise NotImplementedError

    def mGetOVSVMConfig(self, aVMName):
        raise NotImplementedError

    def mGetOVSVMList(self):
        raise NotImplementedError

    def mReadRemoteAllCfg(self, aOptions=None, aForce=False):
        raise NotImplementedError

    def mPruneOVSRepo(self, aOptions):
        raise NotImplementedError

    def mLogListVms(self, aVirshMode=False):
        ebLogDebug('VM Running:')
        if aVirshMode:
            _host_cmd = 'virsh list'
        else:
            _host_cmd = '/usr/sbin/vm_maker --list-domains'
        self.mExecuteCmdLog(_host_cmd)

    def mCreateVM(self, aVMId, aPubKey=None):
        _vmid = aVMId
        _public_key = aPubKey
        _cfgpath = '/EXAVMIMAGES/conf/' + _vmid + '-vm.xml'

        if _public_key:
            _cmd_str = f"""export EXADATA_SKIP_DOMU_NETWORK_CHECK=yes;/opt/exadata_ovm/vm_maker --start-domain {_cfgpath} --locked --ssh-key {_public_key}"""
        else:
            _cmd_str = f"""export EXADATA_SKIP_DOMU_NETWORK_CHECK=yes;/opt/exadata_ovm/vm_maker --start-domain {_cfgpath} --locked"""
        self.mExecuteCmdLog(_cmd_str)
        return 0

    def mDeleteVM(self, aVMId):
        _vmid = aVMId
        self.mExecuteCmdLog('/opt/exadata_ovm/vm_maker --remove-domain '+_vmid +' --force')
        return 0

    def mStatus(self):
        _host_cmd = 'virsh nodecpustats'
        self.mExecuteCmdLog(_host_cmd)

        _host_cmd = 'virsh nodememstats'
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mInfo(self):
        _host_cmd = 'virsh nodeinfo'
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mCheckAutoStart(self, aVMId, aVirshMode=False):
        _vmid = aVMId
        _autoStartEnabled = False
        if aVirshMode:
            _host_cmd = '/usr/bin/virsh dominfo '+_vmid +' |  grep Autostart | grep enable | wc -l'
            _i, _o, _e = self.mExecuteCmd(_host_cmd)
            if _o:
                _out = _o.readlines()
                _data = _out[0]
                if int(_data) > 0:
                    _autoStartEnabled = True
        else:
            _host_cmd = '/usr/sbin/vm_maker --list --domain '+_vmid +' --detail | grep Autostart | grep enable | wc -l'
            _i, _o, _e = self.mExecuteCmd(_host_cmd)
            if _o:
                _out = _o.readlines()
                _data = _out[0]
                if int(_data.strip('\n')) > 0:
                    _autoStartEnabled = True
        ebLogInfo(f'mCheckAutoStart - returns {_autoStartEnabled}')
        return _autoStartEnabled

    def mVMInfo(self, aVMId, aVirshMode=False):
        _vmid = aVMId
        if aVirshMode:
            _host_cmd = 'virsh list --all'
        else:
            _host_cmd = '/usr/sbin/vm_maker --list-domains'
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mDestroyVM(self, aVMId, aStaleDir=False):

        _vmid = aVMId

        if "force_virsh" in get_gcontext().mGetConfigOptions().keys() and \
           get_gcontext().mGetConfigOptions()['force_virsh'] == "True":
            _host_cmd = 'virsh destroy ' + _vmid
            self.mExecuteCmdLog(_host_cmd)
            return 0
        
        _host_cmd = f"/opt/exadata_ovm/vm_maker --stop-domain {_vmid} --force"
        ebLogInfo(f"Executing stop-domain command with --force option : {_host_cmd}")
        _rc = self.mRunCmd(_host_cmd)
        if _rc:
            ebLogError(f"*** Trying KVM VM shutdown with --destroy option")
            _rc = 0    
            _host_cmd = f"/opt/exadata_ovm/vm_maker --stop-domain  {_vmid} --destroy"
            ebLogInfo(f"Executing stop-domain command with --destroy option: {_host_cmd}")
            _rc = self.mRunCmd(_host_cmd)

        if aStaleDir:
            _cmd_str = f"/bin/rm -rf /EXAVMIMAGES/GuestImages/{_vmid}/"
            self.mExecuteCmdLog(_cmd_str)

        return 0

    def mRebootVM(self, aVMId):
        _vmid = aVMId
        _host_cmd = '/opt/exadata_ovm/vm_maker --reboot '+ _vmid

        if "force_virsh" in get_gcontext().mGetConfigOptions().keys() and \
           get_gcontext().mGetConfigOptions()['force_virsh'] == "True":
            _host_cmd = 'virsh reboot ' + _vmid

        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mStartVM(self, aVMId):

        _vmid = aVMId
        _host_cmd = '/opt/exadata_ovm/vm_maker --start-domain '+ _vmid

        if "force_virsh" in get_gcontext().mGetConfigOptions().keys() and \
           get_gcontext().mGetConfigOptions()['force_virsh'] == "True":
            _host_cmd = 'virsh start ' + _vmid

        _i, _o, _e = self.mExecuteCmd(_host_cmd)
        _rc = self.mGetCmdExitStatus()
        if _rc:
            ebLogError('*** KVM START failed for : %s / %s' % (str(_rc), _vmid))
            for _line in _o.readlines():
                ebLogError('*** KVM START O_LOG: %s' % (_line))
            for _line in _e.readlines():
                ebLogError('*** KVM START E_LOG: %s' % (_line))
        return _rc
    
    def mRunCmd(self, _cmd):
        _host_cmd = _cmd
        ebLogInfo(f"Executing command: {_host_cmd}")
        _i, _o, _e = self.mExecuteCmd(_host_cmd)
        _rc = self.mGetCmdExitStatus()
        if _rc:
            ebLogError(f"*** Command failed: {_host_cmd}")
            for _line in _o.readlines():
                ebLogError(f"*** O_LOG: {_line}")
            for _line in _e.readlines():
                ebLogError(f"*** E_LOG: {_line}")
        return _rc

    def mShutdownVM(self, aVMId):
        _vmid = aVMId
        _rc = 0
        _host_cmd = f"/opt/exadata_ovm/vm_maker --stop-domain {_vmid}"
        
        if "force_virsh" in get_gcontext().mGetConfigOptions().keys() and \
           get_gcontext().mGetConfigOptions()['force_virsh'] == "True":
            _host_cmd = f"virsh shutdown {_vmid}"
            
        ebLogInfo(f'Executing VM shutdown command : {_host_cmd}')
        _rc = self.mRunCmd(_host_cmd)
        return _rc
                
    def mShutdownVM2(self, aVMId):
        _vmid = aVMId
        _vm_list_cmd = self.mListVmsCmd()

        _host_cmd = '/opt/exadata_ovm/vm_maker --stop-domain '+ _vmid

        if "force_virsh" in get_gcontext().mGetConfigOptions().keys() and \
           get_gcontext().mGetConfigOptions()['force_virsh'] == "True":
            _host_cmd = 'virsh shutdown ' + _vmid

        #Execute the shutdown
        self.mExecuteCmdLog(_host_cmd)
        #
        # Wait for VM to Shutdown
        #
        _starttime = time.time()
        _elapsed  = 0
        _iterations = 0
        _timeout = 900 # 15 minutes
        while _elapsed < _timeout:
            time.sleep(10)
            domU_list = self.mRefreshDomUs()
            if _vmid in domU_list:
                break
            else:
                if _iterations % 10 == 0:
                    ebLogDebug('*** Waiting for complete of Shutdown of VM: {0}, time: {1}'.format(_vmid, _elapsed))
            _elapsed = time.time() - _starttime

            #Join the collect process is still alive
            _iterations += 1


        _elapsed = time.time() - _starttime

        #Verified the output
        if _elapsed >= _timeout:
            _, _o, _ = self.mExecuteCmd(_vm_list_cmd)
            ebLogError('Failing to Shutdown VM: {0}, time: {1}'.format(_vmid, _elapsed))


            ebLogError(_o.read().strip())
            ebLogInfo("Process with destroy")

            return self.mDestroyVM(_vmid)
        else:

            time.sleep(10)
            ebLogInfo('*** Successfully Shutdown VM: {0}, time: {1}'.format(_vmid, _elapsed))

            domU_list = self.mRefreshDomUs()
            if _vmid in domU_list:
                ebLogWarn("The vm {0} is still present, calling destroy".format(_vmid))
                return self.mDestroyVM(_vmid)

            else:
                return 0

    def mUptime(self):
        return 0

    def mSetVcpus(self, aVMId, aVcpuset, aVirshMode=False):
        _vmid = aVMId
        _vcpu = aVcpuset
        if aVirshMode:
            _host_cmd = '/usr/bin/virsh setvcpus ' + _vmid + ' ' +_vcpu + ' --live'
        else:
            _host_cmd = "/usr/sbin/vm_maker --set --vcpu " + _vcpu + " --domain " + _vmid

        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mAttachDevice(self, aVMId, aFile):
        _vmid = aVMId
        _file = aFile
        _host_cmd = 'virsh attach-device ' + _vmid + '  --file ' + _file + ' --config'
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mDetachDevice(self, aVMId, aFile):
        _vmid = aVMId
        _file = aFile
        _host_cmd = 'virsh detach-device ' + _vmid + '  --file ' + _file
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mGetSysInfo(self):
        _data = ''
        _host_cmd = "virsh sysinfo"
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        if _o:
            _out = _o.readlines()
            if _out and len(_out):
                for _item in _out:
                    _data = _data + _item
        return _data

    def mReadRemoteXML(self, aRemoteVMName, aVirshMode=False):

        if aVirshMode:
            _cmd = "/usr/bin/virsh dumpxml {0}".format(aRemoteVMName)
        else:
            _cmd = "/usr/sbin/vm_maker --dumpxml {0}".format(aRemoteVMName)

        _, _o, _ = self.mExecuteCmd(_cmd)

        _configXML = ''
        if _o:
            _configXML = _o.read().strip()

        return _configXML

    def mDefineXMLToGuest(self, aFile):
        _file = aFile
        _host_cmd = '/usr/bin/virsh define ' + _file
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mUnDefineXMLToGuest(self, aFile):
        _file = aFile
        _host_cmd = '/usr/bin/virsh undefine ' + _file
        self.mExecuteCmdLog(_host_cmd)
        return 0

    def mAutoStartVM(self, aVMId, aEnabled):

        if aEnabled:
            _enableFlag = "--enable"
        else:
            _enableFlag = "--disable"

        _host_cmd = '/opt/exadata_ovm/vm_maker --autostart {0} {1}'.format(aVMId, _enableFlag)
        ebLogInfo('*** Executing Command: %s'%(_host_cmd))
        self.mExecuteCmdLog(_host_cmd)
        return self.node.mGetCmdExitStatus()

    def mGetHVStatus(self):
        _hv_status = ''
        _host_cmd = "systemctl is-active libvirtd.service"
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        if _o:
            _out = _o.readlines()
            if not _out:
                ebLogError('*** libvirtd service stopped on DOM0:{0}'.format(self.hostname))
                return "stopped"
            _hv_status = _out[0].strip()
            if _hv_status == "active":
                ebLogInfo('*** libvirtd service running on DOM0:{0}'.format(self.hostname))
                _hv_status = "running"
            else:
                _start_cmd="systemctl start libvirtd"
                ebLogInfo('*** libvirtd service stopped on DOM0:{0}. Starting libvirtd service'.format(self.hostname))
                _, _stdout, _stderr = self.mExecuteCmd(_start_cmd)
                if self.mGetCmdExitStatus():
                    ebLogError(f"*** libvirtd service failed to start on {self.hostname} with stderr: {_stderr.read().strip()} and stdout: {_stdout.read().strip()}")
                _, _o, _ = self.mExecuteCmd(_host_cmd)
                _out = _o.readlines()
                _hv_status = _out[0].strip()
                if _hv_status == "active":
                    ebLogInfo('*** libvirtd service running on DOM0:{0}'.format(self.hostname))
                    _hv_status = "running"
                else:
                    ebLogError('*** libvirtd service stopped on DOM0:{0}'.format(self.hostname))
                    _hv_status = "stopped"
        return _hv_status

    def mGetPhysicalMemory(self):
        _, _o, _ = self.mExecuteCmd('/sbin/dmidecode --type 19')
        _ret = self.mGetCmdExitStatus()
        if _ret:
            return 0, ""
        for _line in _o.readlines():
            if 'Range Size' not in _line:
                continue
            _size, _unit = _line.split(':')[1].strip().split()
            ebLogInfo(f"Physical Memory on DOM0:{self.hostname}: {_size}{_unit}")
            return int(_size), _unit
        return 0, ""

    def mGetVmStatus(self, aDomu):
        _cmd = "/usr/sbin/vm_maker --list-domains | /bin/grep %s | /bin/awk '{ print $3; }'" % aDomu
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

    def mGetVMUUID(self, aDomU):
        _domU = aDomU
        _uuid = ""
        _host_cmd = "/usr/bin/virsh dominfo %s | /bin/grep 'UUID' | /bin/awk '{ print $2 }' " %(_domU)
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        _rc = self.mGetCmdExitStatus()
        if _rc == 0 and _o:
            _out = _o.readlines()
            if not _out:
                return ""
            _uuid = _out[0].strip()
            ebLogInfo('UUID for the domU: {0} is {1}'.format(_domU, _uuid))

        return _uuid
    
    def mGetVMAdminBridge(self, aDomU):
        _domU = aDomU
        _bridge = ""
        _mac = ""

        _host_cmd = "/usr/bin/virsh domiflist %s | grep vmeth | awk '{print $3,$5}'"  %(_domU)
        _, _o, _ = self.mExecuteCmd(_host_cmd)
        _rc = self.mGetCmdExitStatus()
        if _rc == 0 and _o:
            _out = _o.readlines()
            if not _out:
                return "", ""
            
            _bridge = _out[0].split(' ')[0].strip()
            _mac = _out[0].split(' ')[1].strip()
            ebLogInfo('Admin bridge {0}, mac address {1} for the domU: {2}'.format(_bridge, _mac, _domU))

        return _bridge, _mac
