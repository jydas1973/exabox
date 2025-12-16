"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    kvmdgrpvmkr - Cpu Functionality for KVM using Domain Groups and vm_maker

FUNCTION:
    CPU Operations for KVM.

NOTE:
    None

History:
    ririgoye    20/11/35 - Fix SyntaxWarning caused by invalid comparators
    naps        23/04/20 - Create file

"""

import time
import json

from exabox.log.LogMgr import ebLogDiag, ebLogWarn, ebLogInfo, ebLogError, ebLogVerbose, ebLogJson
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.DBStore import ebGetDefaultDB
from exabox.tools.ebOedacli.ebOedacli import ebOedacli
from exabox.utils.node import connect_to_host

HYPERVISOR_RSRVD_CORES = 2

class exaBoxKvmDgrpVmkr(object):

    def __init__(self, aCluCtrlObject):
        self.__ecc = aCluCtrlObject
        if self.__ecc.IsZdlraProv():
            self.__ht_factor = 1
        else:
            self.__ht_factor = 2

    def mManageVMCpusCountKvm(self, aVMCmd, aVMId, aOptions=None):

        _vmcmd = aVMCmd
        _vmid  = aVMId
        _options = aOptions
        _jconf   = None
        _review  = False
        _cpu_bursting = None
        _bursting_enabled = None
        _subfactor = None
        _cos = False
        _allocatable_cores = 0
        _num_computes = len(self.__ecc.mGetOrigDom0sDomUs())
        _data_d  = {}
        _data_d['version'] = '1.0'
        _data_d['comment'] = 'vcpu data info and status'
        _data_d['bursting_ready'] = 'False'
        _data_d['bursting_enabled'] = 'False'
        _data_d['vms'] = {}

        ebLogVerbose("mManageVMCpusCount: aVMCmd = %s, aVMId = %s" % (aVMCmd, aVMId))

        def _mUpdateRequestData(aDataD):
            _data_d = aDataD
            _reqobj = self.__ecc.mGetRequestObj()
            if _reqobj is not None:
                _reqobj.mSetData(json.dumps(_data_d))
                _db = ebGetDefaultDB()
                _db.mUpdateRequest(_reqobj)

        if _options is not None:
            _jconf = aOptions.jsonconf
        #
        # Handle special case for cpustatus
        #
        if _vmcmd == 'cpustatus':
            if _jconf is None:
                _jconf = {}
            _review = True
        #
        # Payload (json) is mandatory
        #
        if _jconf is None:
            ebLogWarn('*** json payload for VMCpusCount command: %s not provided.' % (_vmcmd))
            _mUpdateRequestData(_data_d)
            return ebError(0x0433)
        #
        # Fetch values from payload for cores, memory and disk (only cpus used for now)
        #

        _ratio  = 2
        if self.__ecc.IsZdlraProv():
            if self.__ecc.mCheckConfigOption('zdlra_core_to_vcpu_ratio') is not None:
                _ratio = int(self.__ecc.mCheckConfigOption('zdlra_core_to_vcpu_ratio'))
            else:
                _ratio = 1
            ebLogInfo('*** mManageVMCpusCountKvm: _ratio is : %d' %(_ratio))

        _host_d = {}
        try:
            if 'vms' in _jconf.keys():
                for _h in _jconf['vms']:
                    _host_d[_h['hostname']] = int(_h['cores']) * _ratio
                    # xxx/MR: Add support to deltacores if needed.
        except Exception as e:
            ebLogError("CC:mManageVMCpusCount Exception:: %s - %s" % (e.__class__, e))
            _mUpdateRequestData(_data_d)
            return ebError(0x0430)

        #
        # Check if payload is valid
        #
        if not len(_host_d.keys()) and not _review:
            ebLogWarn('*** VMCpusCount core count/delta not found in payload')
            ebLogWarn('*** PL: %s' % (str(_jconf)))
            _mUpdateRequestData(_data_d)
            return ebError(0x0433)

        #
        # modify cluster with CPU oversubscription factor; check payload attributes
        #
        _subfactor = None
        if 'subfactor' in _jconf.keys():
            _subfactor = int(_jconf['subfactor'])

        if _subfactor is not None:
            if _subfactor > 1:
                _cos = True
                if 'poolsize' in _jconf.keys():
                    _poolsize = str(_jconf['poolsize'])
                    _poolsize = str(int(_poolsize) * int(_ratio))
                    _poolsize = str((int(_poolsize))/_num_computes)
                    _allocatable_cores = str(int(_subfactor) * int(_poolsize)) # Max allowed sum of all vcpus
                    ebLogInfo('*** COS: _allocatable_cores is : %s' %(_allocatable_cores))
                else:
                    ebLogError('*** json payload for CPU oversubscription command: poolsize not provided.')
                    return ebError(0x0433)


        #
        # Iterative/Sequential VCPU update (e.g. parallel support may be added in the future)
        #
        _maxcores = 0
        _maxvcores = 0
        _minvcpus = self.__ecc.mCheckConfigOption('kvm_minimum_vcpus')
        if _minvcpus is None:
            _minvcpus = 4
        else:
            _minvcpus = int(_minvcpus)

        for _hyp, _dom in self.__ecc.mReturnDom0DomUPair():

            if _vmid != '_all_' and _vmid != _dom:
                continue

            if _dom not in _host_d.keys() and not _review:
                continue

            #
            # Initialize _data_d
            #
            _data_d['vms'][_dom] = {}
            #
            # Fetch new cores number for the VM
            #
            if not _review:
                _cores = int(_host_d[_dom])
            else:
                _cores = 0

            #TODO: We should be ideally checking output of "numactl -H" and look for available number of nodes to
            # deduce the minimum vcpu count. Its possible that minimum value for vcpu count could be more than 4 depending on configuration.
            #For now, setting it to 4.
            if _cores < _minvcpus:
                _cores = _minvcpus
                ebLogInfo('*** Changing vcpu count to %d ' %(_minvcpus))

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_hyp)
            # TODO There is no vm_maker alternative for getting below info. hence contining to use virsh
            _in, _out, _err = _node.mExecuteCmd("virsh nodeinfo | grep 'CPU(s)' | awk '{print$2}'")
            if _out:
                _out = _out.readlines()
                _total = _out[0].strip()
                _reserved = HYPERVISOR_RSRVD_CORES * self.__ht_factor
                _in, _out, _err = _node.mExecuteCmd("/usr/sbin/vm_maker --list --vcpu | /bin/grep 'Host reserved' | /bin/awk '{print $5}'")
                if _out:
                    _out = _out.readlines()
                    _reserved = _out[0].strip()
                    ebLogInfo('*** Host reserved cpus from vm_maker: %s.' %_reserved)
                _maxcores = int(_total) - int(_reserved)
                ebLogInfo('*** MAX_VCPUS on hypervisor %s : %d' % (_hyp, _maxcores))
                # If cos enabled, consider virtual max cores
                if _cos:
                    ebLogInfo('*** MAX_COS_VCPUS on hypervisor %s : %s' % (_hyp, _allocatable_cores))
                    _maxvcores = int(_allocatable_cores)

            if not self.__ecc.mPingHost(_dom):
                ebLogWarn('*** Domain (%s) is not pingable for command: %s.' % (_dom, _vmcmd))
                _is_pingable = False
            else:
                _is_pingable = True

            #
            # Fetch current vCPU for Domain
            #
            if _is_pingable:
                _in, _out, _err = _node.mExecuteCmd("vm_maker --list --vcpu --domain %s | awk '{print $4}'" % (_dom))
            else:
                _in, _out, _err = _node.mExecuteCmd("vm_maker --list --vcpu --domain %s | awk -F: '{print $4}'" % (_dom))
            if _out:
                _out = _out.readlines()
                _currvcpus = int(_out[0].strip())
                ebLogInfo('*** CURRENT_VCPUS for domain %s : %d' % (_dom, _currvcpus))
                #
                # Fetch current MAXVCPUs (not the one set in vm.cfg)
                #
            # TODO There is no vm_maker alternative for getting below info. hence contining to use virsh
            _in, _out, _err = _node.mExecuteCmd("virsh vcpucount %s | grep maximum | grep config | awk '{print $3}'" % (_dom))
            if _out:
                _out = _out.readlines()
                _currmaxvcpus = int(_out[0])
                ebLogInfo('*** CURRENT_MAXVCPUS for domain %s : %d' % (_dom, _currmaxvcpus))

            _data_d['vms'][_dom]['currvcpus']    = _currvcpus
            _data_d['vms'][_dom]['currmaxvcpus'] = _currmaxvcpus
            #
            # Check if new VCPUs count is 2X more than current VCPUs
            #
            if _cores > _currvcpus * 2:
                ebLogWarn('*** NEW_VCPUS count %s for %s is 2 times higher than CURR_VCPUS %s' % (str(_cores),_dom,str(_currvcpus)))
            #
            # Fetch current vCPUs used by all VMs (including hypervisor)
            #



            _cluster_list=[]
            _cmd = "vm_maker --list-domains | awk '{print $1}'"
            _, _out, _ = _node.mExecuteCmd(_cmd)
            if _out:
                _out = _out.readlines()
                for _line in _out:
                    if not _line.isspace():
                        _cluster_list.append(_line.strip().split('(')[0])

            _vcpusinuse = 0
            _vcpusleft  = 0

            for _vm in _cluster_list:
                ebLogInfo("_vm: " + _vm)
                if self.__ecc.mPingHost(_vm):
                    _cmd = "vm_maker --list --vcpu --domain " +_vm + " | awk '{print $4}'"
                else:
                    _cmd = "vm_maker --list --vcpu --domain " +_vm + " | awk -F: '{print $4}'"
                _, _out, _ = _node.mExecuteCmd(_cmd)
                _out = _out.readlines()
                if _out:
                    _vcpusinuse += int(_out[0].strip())
                    ebLogInfo('current cpu: ' +_out[0])
                else:
                    _error_str = '*** Can not retrieve VCPUS allocation for (%s)' % (_vm)
                    ebLogError(_error_str)
                    _node.mDisconnect()
                    raise ExacloudRuntimeError(0x0800, 0xA, _error_str)

            if _maxvcores:
                _vcpusleft = _maxvcores - _vcpusinuse
            else:
                _vcpusleft = _maxcores - _vcpusinuse

            ebLogInfo('*** CURRENT_VCPUS in hypervisor %s : %d (%d left)' % (_hyp, _vcpusinuse, _vcpusleft))
            ebLogInfo('*** Input _cores: %d' %_cores)

            _left = _vcpusleft
            _requested = (_cores - _currvcpus)
            _vcpusleft = _vcpusleft - (_cores - _currvcpus)
            if _vcpusleft < 0:
                ebLogError('*** vCPUs over-provisioning detected !!! (%d left / %d requested)' % (_left,_requested))
                _node.mDisconnect()
                _mUpdateRequestData(_data_d)
                return ebError(0x0431)

            if _cos:
                _maxvcoresdomu = (int(_maxvcores)/int(_ratio))
                if _maxvcoresdomu < _cores:
                    ebLogError('*** vCPUs over-provisioning detected !!! (max(allocatable cores) (%d) on domain (%s) /  %d requested)' % (_maxvcoresdomu,_dom,_requested))
                    _node.mDisconnect()
                    _mUpdateRequestData(_data_d)
                    return ebError(0x0431)

            #
            # Check vm.cfg settings : maxvcpus and current vCPUs
            #
            # TODO There is no vm_maker alternative for getting below info. hence contining to use virsh
            _cmd = "virsh vcpucount " + _dom + " | grep maximum | grep config | awk '{print $3}'"
            _nodeU = exaBoxNode(get_gcontext())
            _nodeU.mConnect(aHost=_hyp)
            _in, _out, _err = _nodeU.mExecuteCmd(_cmd)
            if _out:
                _out = _out.readlines()
                _maxvcpus = int(_out[0].strip())
                ebLogInfo('*** MAX_VCPUS (CFG) for domain %s : %d' % (_dom, _maxvcpus))
            #
            # _data_d udpate
            #
            _data_d['vms'][_dom]['cfgmaxvcpus'] = _maxvcpus
            #
            # Check for discrepancy between current and <vm>.xml maxvcpus values
            #
            if _currmaxvcpus != 0 and _currmaxvcpus != _maxvcpus:
                ebLogWarn('*** MAX_VCPUS for domain in xml not applied to running VM (xml:%s/current:%s)' % (_maxvcpus,_currmaxvcpus))
                if not _review:
                    _data_d['vms'][_dom]['bursting_enabled'] = 'False'
                    _data_d['bursting_enabled'] = 'False'
                    _data_d['bursting_ready'] = 'False'
                    _nodeU.mDisconnect()
                    _node.mDisconnect()
                    _mUpdateRequestData(_data_d)
                    return ebError(0x0435)
                else:
                    _data_d['vms'][_dom]['bursting_enabled'] = 'False'
                    _bursting_enabled = 'False'
                    _data_d['bursting_enabled'] = 'False'
                    _data_d['bursting_ready'] = 'False'
            else:
                _data_d['vms'][_dom]['bursting_enabled'] = 'True'
                if _bursting_enabled is None:
                    _bursting_enabled = 'True'
                    _cpu_bursting = 'False'
                    _data_d['bursting_enabled'] = 'True'
            #
            # Check if VCPUS adjustment is correct
            #
            if _cores > _maxvcpus and not _review:
                ebLogError('*** domain MAX_VCPUS (%d) is lower than new number of cores requested: %d' %(_maxvcpus,_cores))
                _nodeU.mDisconnect()
                _node.mDisconnect()
                _mUpdateRequestData(_data_d)
                return ebError(0x0434)

            if _cores == _currvcpus and not _review:
                ebLogWarn('*** domain cores already matching cores numbers in resize request')
                _nodeU.mDisconnect()
                _node.mDisconnect()
                continue
            #
            # set cpu-bursting enabled or disabled
            #
            if _cpu_bursting is None or _cpu_bursting != 'False':
                if (_currmaxvcpus and _currmaxvcpus == _maxcores) or (_currmaxvcpus == 0 and _maxvcpus == _maxcores):
                    _cpu_bursting = 'True'
                else:
                    _cpu_bursting = 'False'
                ebLogInfo('*** setting cpu_bursting to : %s (_currmaxcvpus: %d/ _maxcores: %d/ _cfgmaxvcpus: %d)' % (_cpu_bursting, _currmaxvcpus, _maxcores, _maxvcpus))
            #
            # Display vCPUs change requested
            #
            ebLogInfo('*** domain (%s) current vCPUs: %s new vCPUS count: %s' % (_dom, _currvcpus, _cores))
            #
            # Adjust vcpu on Domain
            #

            if not _review and _cos:
                #
                # modify cluster with CPU oversubscription factor; do update the vcpu count as needed
                #
                if _cos:
                    _sum_vcpus = 0

                    for _vm in _cluster_list:
                        if _is_pingable:
                            _cmd = "vm_maker --list --vcpu --domain " +_vm + " | awk '{print $4}'" 
                        else:
                            _cmd = "vm_maker --list --vcpu --domain " +_vm + " | awk -F: '{print $4}'"
                        _, _out, _ = _node.mExecuteCmd(_cmd)
                        _out = _out.readlines()
                        if _out:
                            # sum all vcpus except the domain whose _cores is getting updated.
                            if _vm not in _dom:
                                _sum_vcpus += int(_out[0])
                        else:
                            _error_str = '*** Can not retrieve VCPUS allocation for (%s)' % (_dom)
                            ebLogError(_error_str)
                            _node.mDisconnect()
                            raise ExacloudRuntimeError(0x0800, 0xA, _error_str)

                    # We don't need the range check since modify_service should have
                    # taken care of range check for all clusters.
                    # Verification of the sum of vcpus <= allocatbale cores, should suffice
                    # _cores is the new cores value for the domain

                    if (int(_allocatable_cores) - _sum_vcpus) < _cores:
                        _error_str = '*** Number of cores is more than the maximum allowed value for %s' % (_dom)
                        ebLogError(_error_str)
                        _node.mDisconnect()
                        raise ExacloudRuntimeError(0x0800, 0xA, _error_str)
                    else:
                        if _is_pingable:
                            _cmd = "vm_maker --set --vcpu " +str(_cores) +" --domain " +_dom + " --force"
                        else:
                            _cmd = "vm_maker --set --vcpu " +str(_cores) +" --domain " +_dom + " --config"

                        ebLogInfo('****** COS: Executing: %s ' %(_cmd))
                        _node.mExecuteCmdLog(_cmd)

                    #COS ends here

            if not _review and not _cos:

                # 1. Read hypervisor CPU usage
                # 2. Determine poolsize using _vcpusinuse and hypervisor CPU usage
                # 3. Do vcpu-set operation for the current domain
                # 4. Call mModifyService with subfactor as 1 and poolsize to do
                # vcpu pinning in both single and multi-vm cases

                if 'poolsize' in _jconf.keys():
                    # Rack where COS is enabled
                    _poolsize = str(_jconf['poolsize'])
                    ebLogVerbose('*** Poolsize received is %s' %(_poolsize))
                else:
                    # Rack where COS is not enabled

                    # Total number of cpus used by hypervisor
                    _hypvcpus = 0

                    # Determine poolsize
                    _poolsize = str(_vcpusinuse + _cores - _currvcpus - _hypvcpus)
                    ebLogVerbose('*** Poolsize calculated is %s' %(_poolsize))

                # Ensure subfactor is 1
                _subfactor = 1

                #
                # Dynamic vCPUs change
                #
                if _is_pingable:
                    _cmd = "vm_maker --set --vcpu " +str(_cores) +" --domain " +_dom + " --force"
                else:
                    _cmd = "vm_maker --set --vcpu " +str(_cores) +" --domain " +_dom + " --config"

                ebLogInfo('****** Non-COS Executing: %s ' %(_cmd))
                _nodeU.mExecuteCmdLog(_cmd)


            _pvl = self.__ecc.mCheckConfigOption('timeout_vmcpu_resize')
            if _pvl is not None:
                self.__timeout_vmcpu_resize = int(_pvl)
            else:
                self.__timeout_vmcpu_resize = 60

            #
            # Check if vCPUs have been updated effectively.
            #
            if not _review:
                _total_time = 0
                _check_itv  = 5

                # Default timeout of 900 seconds (15min)
                while _total_time < self.__timeout_vmcpu_resize:
                    time.sleep(_check_itv)
                    if _is_pingable:
                        _in, _out, _err = _node.mExecuteCmd("vm_maker --list --vcpu --domain %s | awk '{print $4}'" % (_dom))
                    else:
                        _in, _out, _err = _node.mExecuteCmd("vm_maker --list --vcpu --domain %s | awk -F: '{print $4}'" % (_dom))
                    ebLogInfo('*** checking domain cores if updated correctly !')
                    if _out:
                        _out = _out.readlines()
                        _currvcpus = int(_out[0])
                    if _currvcpus == _cores:
                        break
                    _total_time += _check_itv

                if _currvcpus != _cores:
                    ebLogError('*** domain cores update not successful current: %d - requested: %d' % (_currvcpus,_cores))
                    _nodeU.mDisconnect()
                    _node.mDisconnect()
                    _mUpdateRequestData(_data_d)
                    return ebError(0x0430)
                else:
                    ebLogInfo('*** domain cores update successfull.')

            _nodeU.mDisconnect()

            _node.mDisconnect()
        #
        # update _data_d and flush request.data field to DB
        #
        if _cpu_bursting is not None and _cpu_bursting == 'True':
            _data_d['bursting_ready'] = 'True'
        _mUpdateRequestData(_data_d)

        return 0

    def mPatchVMCfgVcpuCountKvm(self, aHyp, aDom, aOptions):

        _ratio = self.__ecc.mCheckConfigOption('core_to_vcpu_ratio')
        if _ratio is None:
            _ratio = 2
        else:
            _ratio = int(_ratio)
        if self.__ecc.IsZdlraProv():
            if self.__ecc.mCheckConfigOption('zdlra_core_to_vcpu_ratio') is not None:
                _ratio = int(self.__ecc.mCheckConfigOption('zdlra_core_to_vcpu_ratio'))
            else:
                _ratio = 1
            ebLogInfo('*** mPatchVMCfgVcpuCountKvm: _ratio is : %d' %(_ratio))

        _cores = str(aOptions.jsonconf['vm']['cores'])
        _cores = str(int(_cores) * _ratio)

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aHyp)

        # Dynamic vcpu update
        ebLogInfo('mPatchVMCfgVcpuCountKvm: Dynamic vcpu update for VM ' + aDom + ' with '+str(_cores)+' vcpus')

        if not self.__ecc.mPingHost(aDom):
            ebLogWarn('*** Domain (%s) is not pingable for command mPatchVMCfgVcpuCountKvm' % (aDom))
            _is_pingable = False
        else:
            _is_pingable = True

        if _is_pingable:
            _cmd = "vm_maker --set --vcpu " +str(_cores) +" --domain " +aDom + " --force"
        else:
            _cmd = "vm_maker --set --vcpu " +str(_cores) +" --domain " +aDom + " --config"

        _node.mExecuteCmdLog(_cmd)
        _node.mDisconnect()

    def mManageVMCpusBurstingKvm(self, aVMCmd, aVMId, aOptions=None):

        _vmcmd = aVMCmd
        _vmid  = aVMId
        _options = aOptions
        _maxcores = 0
        _maxvcpus = 0
        _data_d  = {}
        _data_d['version'] = '1.0'
        _data_d['comment'] = 'vcpu bursting enabling'
        _data_d['vms'] = {}

        ebLogVerbose("mManageVMCpusBurstingKvm: aVMCmd = %s, aVMId = %s" % (aVMCmd, aVMId))

        def _mUpdateRequestData(aDataD):
            _data_d = aDataD
            _reqobj = self.__ecc.mGetRequestObj()
            if _reqobj is not None:
                _reqobj.mSetData(json.dumps(_data_d))
                _db = ebGetDefaultDB()
                _db.mUpdateRequest(_reqobj)

        if _options is not None:
            _jconf = aOptions.jsonconf

        if _vmcmd == 'enablebursting':
            if _jconf is None:
                _jconf = {}

        for _hyp, _dom in self.__ecc.mReturnDom0DomUPair():

            if _vmid != '_all_' and _vmid != _dom:
                continue
            #
            # Initiaize _data_d
            #
            _data_d['vms'][_dom] = {}
            #
            # Fetch maxcores from Hypervisor
            #
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_hyp)
            _in, _out, _err = _node.mExecuteCmd("virsh nodeinfo | grep 'CPU(s)'")
            if _out:
                _out = _out.readlines()
                _total = _out[0].split(':')[1].strip()
                _reserved = HYPERVISOR_RSRVD_CORES * self.__ht_factor
                _in, _out, _err = _node.mExecuteCmd("/usr/sbin/vm_maker --list --vcpu | /bin/grep 'Host reserved' | /bin/awk '{print $5}'")
                if _out:
                    _out = _out.readlines()
                    _reserved = _out[0].strip()
                    ebLogInfo('*** Host reserved cpus from vm_maker: %s.' %_reserved)
                _maxcores = int(_total) - int(_reserved)
                ebLogInfo('*** MAX_VCPUS on hypervisor %s : %d' % (_hyp, _maxcores))

            #
            # Update vm vcpus for bursting mode
            #
            _cmd = "virsh vcpucount " + _dom + " | grep maximum | grep config | awk '{print $3}'"
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            if _out:
                _out = _out.readlines()
                _maxvcpus = int(_out[0].strip())
                ebLogInfo('*** MAX_VCPUS (CFG) for domain %s : %d' % (_dom, _maxvcpus))

            if _maxvcpus != _maxcores:
                #
                # Update maxvcpus
                #
                _cmd = "virsh setvcpus " + _dom + " " + str(_maxcores) + " --maximum --config"
                _node.mExecuteCmd(_cmd)
                ebLogInfo('*** MAX_VCPUS (CFG) for domU %s reset to: %d' % (_dom, _maxcores))
            else:
                ebLogInfo('*** vm' + _dom + 'maxvcpus already updated to maxcores')

            _data_d['vms'][_dom]['bursting_enabled'] = 'True'

            _node.mDisconnect()

        _data_d['bursting_enabled'] = 'True'
        _mUpdateRequestData(_data_d)

        return 0

    def mClusterCPUInfoKvm(self, aOptions):

        _data_d = {}
        _err = None
        _rc = -1
        def _mUpdateRequestData(rc, aData, err):
            """
            Updates request object with the response payload
            """
            _reqobj = self.__ecc.mGetRequestObj()
            _response = {}
            _response["success"] = "True" if (rc == 0) else "False"
            _response["error"] = err
            _response["output"] = aData
            if _reqobj is not None:
                _db = ebGetDefaultDB()
                _reqobj.mSetData(json.dumps(_response, sort_keys = True))
                _db.mUpdateRequest(_reqobj)
            elif aOptions.jsonmode:
                ebLogJson(json.dumps(_response, indent=4, sort_keys = True))

        for _hyp, _dom in self.__ecc.mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _result = []
            _node.mConnect(aHost=_hyp)
            _res={}
            _, _out, _  = _node.mExecuteCmd("virsh dominfo " + _dom  + " | grep 'CPU(s):' | awk '{print $2}'")
            if _out:
                _out = _out.readlines()
                _res["vm_detail"] = _dom
                _res["vcpus"]= _out[0].strip()

            _, _out, _ = _node.mExecuteCmd("virsh vcpuinfo " + _dom + " --pretty | grep Affinity | awk '{print$3}' | sort | uniq")
            if _out:
                _out = _out.readlines()
                _aff = []
                for _line in _out:
                    _aff.append(_line.strip())
                _res["pinning_range"]=','.join(_aff)

            _result.append(_res)

            _data_d[_hyp]= _result
            _node.mDisconnect()
        _rc = 0
        _err = None
        ebLogInfo("mClusterCPUInfo is : %s" % (json.dumps(_data_d)))
        _mUpdateRequestData(_rc,_data_d,_err)

    def createDG(self, aExaBoxCluCtrlObj):
        ebLogInfo('csCreateVM: Entering createDG')

        for _dom0, _domU in aExaBoxCluCtrlObj.mReturnDom0DomUPair():
            _sname = _dom0.split('.')[0].strip()
            _dgname = "dg-" + _sname
            _oedacli_bin = get_gcontext().mGetOEDAPath() + '/oedacli'
            _oedacli = ebOedacli(_oedacli_bin, "log/oedacli", aLogFile="oedacli_dg.log")
            _oedacli.mSetAutoSaveActions(False)

            # There is a bug in vm_maker --list --domain-group-info <DG-name>
            # It does not return proper error value. Hence temp w/a below code searches among all DGs.
            # Once vm_maker bug is fixed, replace --all with DG-name
            _cmd = "vm_maker --list --domain-group-info --all | grep " + _dgname
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _maxcores = 0
                ebLogInfo('Executing: ' +_cmd)
                _node.mExecuteCmd(_cmd)
                _rc = _node.mGetCmdExitStatus()
                if not _rc:
                    ebLogInfo('DG exists!')
                    # We still need to add the domaingroup to the xml for the sake of the following step of VM assignment.
                    # But lets pick the same size which is already defined.
                    _cmd = "vm_maker --list --domain-group-info --all | grep " +_dgname + " | awk '{print $2}'"
                    _, _out, _ = _node.mExecuteCmd(_cmd)
                    if _out:
                        _out = _out.readlines()
                        _dgpcpus = int(_out[0])

                    _oedacli.mSetDeploy(False)
                    _oedacli.mAppendCommand("ADD DOMAINGROUP GROUPNAME=" + _dgname +" SIZE="+str(_dgpcpus) +" WHERE HOSTNAME=" + _sname)
                    _oedacli.mRun(aExaBoxCluCtrlObj.mGetRemoteConfig(), aExaBoxCluCtrlObj.mGetRemoteConfig())
                else:
                    ebLogInfo('DG does not exist!')
                    _cmd = "vm_maker --list --domain-group-info --all | awk '{if(NR>2 && NF)print$2}'"
                    _, _out, _ = _node.mExecuteCmd(_cmd)
                    if _out:
                        _out = _out.readlines()
                        _cnt = 0
                        for _line in _out:
                            _cnt = _cnt + int(_line)
                        ebLogInfo('*** Already allocated %d pcpus on dom0 ***' %(_cnt))

                    _in, _out, _err = _node.mExecuteCmd("virsh nodeinfo | grep 'CPU(s)' | awk '{print$2}'")
                    if _out:
                        _out = _out.readlines()
                        _dat = _out[0].strip()
                        ebLogInfo('*** MAX_VCPUS on hyp : %s' % (_dat))
                        _maxcores = int(_dat)

                    _reserved = HYPERVISOR_RSRVD_CORES * self.__ht_factor
                    _in, _out, _err = _node.mExecuteCmd("/usr/sbin/vm_maker --list --vcpu | /bin/grep 'Host reserved' | /bin/awk '{print $5}'")
                    if _out:
                        _out = _out.readlines()
                        _reserved = _out[0].strip()
                        ebLogInfo('*** Host reserved cpus from vm_maker: %s.' %_reserved)

                _dgcores = _maxcores - _cnt - int(_reserved)
                ebLogInfo('***Allocating %d pcpus for hyp ***' %_dgcores)
                _oedacli.mSetDeploy(True)
                _oedacli.mAppendCommand("ADD DOMAINGROUP GROUPNAME=" + _dgname +" SIZE="+str(_dgcores) +" WHERE HOSTNAME=" + _sname)
                _oedacli.mRun(aExaBoxCluCtrlObj.mGetRemoteConfig(), aExaBoxCluCtrlObj.mGetRemoteConfig())

            _oedacli.mSetDeploy(False)
            _oedacli.mAppendCommand("ALTER MACHINE GROUPNAME=" + _dgname +" WHERE HOSTNAME=" + _domU.split('.')[0].strip())
            _oedacli.mRun(aExaBoxCluCtrlObj.mGetRemoteConfig(), aExaBoxCluCtrlObj.mGetRemoteConfig())

