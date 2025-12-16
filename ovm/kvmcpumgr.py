"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    kvmcpumgr - Cpu Functionality for KVM.

FUNCTION:
    CPU Operations for KVM.

NOTE:
    None
"""

import time
import json
import re

from exabox.utils.node import node_exec_cmd_check
from exabox.log.LogMgr import ebLogDiag, ebLogWarn, ebLogInfo, ebLogError, ebLogVerbose, ebLogJson, ebLogTrace
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError, gReshapeError, gPartialError
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.kvmdgrpvmkr import exaBoxKvmDgrpVmkr
from exabox.utils.node import connect_to_host
from exabox.ovm.vmcontrol import ebVgLifeCycle
import datetime
import difflib
import os
import glob
import copy
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, TimeoutBehavior, ExitCodeBehavior

HYPERVISOR_RSRVD_CORES = 2
CPULOG_DIR = "cpuresize_logs"

class exaBoxKvmCpuMgr(object):

    def __init__(self, aCluCtrlObject):
        self.__ecc = aCluCtrlObject
        if self.__ecc.IsZdlraProv():
            self.__ht_factor = 1
        else:
            self.__ht_factor = 2

    def mIsActiveGuest(self, aDom0Node, aDomU):

        _cmd = "/usr/sbin/vm_maker --list | /bin/grep running | /bin/grep {0}".format(aDomU)
        _vmid = aDom0Node.mSingleLineOutput(_cmd)

        if aDom0Node.mGetCmdExitStatus() != 0:
            return False
        else:
            return True

        
    def mModifyServiceKvm(self, aOptions=None, aSubfactor=None, aPoolsize=None, aDomain=None, aForcePinning=False):

        if self.__ecc.mCheckConfigOption('kvm_override_disable_pinning','True'):
            ebLogTrace('*** cpu pinning disabled for kvm!')
            return

        _jconf = None
        _cores = 0
        _subfactor = 2 #default (override in payload)
        _cos = True
        _num_computes = len(self.__ecc.mGetOrigDom0sDomUs())

        #VGE: aForcePinning arg was added as the disable_vcpus_pinning flag
        # is only reliable during create service (where ATP flag is passed and image verified)
        # Also ONLY in multiVM+disableCOS:    the create service flows
        #      will RELY ON THIS FUNCTION to set pinning so vm.cfg
        #      will NOT have pinning (no cpus= line) 
        #      but also NOT be expected to be vNuma
        #if not aForcePinning and not self.mCheckConfigOption('force_pinning_on_resize', 'True'):

        # ********************************************************************************************
        # ******* Below code is commented out for now. Need to see if this relevant for kvm ! ********
        # ********************************************************************************************

        #    for _hyp, _dom in self.mReturnDom0DomUPair():

        #        if (aDomain is not None) and (aDomain != _dom):
        #            ebLogVerbose('*** Skipping CPU Pinning for %s' %(_dom))
        #            continue

        #        _node = exaBoxNode(get_gcontext())
        #        _node.mConnect(aHost=_hyp)

        #        _node.mExecuteCmd("/bin/grep '^cpus' /EXAVMIMAGES/GuestImages/{0}/vm.cfg".format(_dom))
        #        _rc = _node.mGetCmdExitStatus() != 0
        #        _node.mDisconnect()

        #        if _rc != 0:
        #            ebLogInfo("*** vNuma Configuration as no Pinning set in vm.cfg, will not update Pinning")
        #            return # BAIL OUT

        if not aOptions:
            aOptions = self.__ecc.mGetArgsOptions()

        if aOptions is not None:
            _jconf = aOptions.jsonconf

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
            ebLogInfo('*** mModifyServiceKvm: _ratio is : %d' %(_ratio))

        if aPoolsize is not None:
            # Internal call. Ratio already accounted for since we
            # calculated it using VCPU column of 'xm list'
            _cores = str(aPoolsize)
        elif 'poolsize' in _jconf.keys():
            # Call from upper layer
            _cores = str(_jconf['poolsize'])
            ebLogVerbose('*** mModifyService: Poolsize : %s' %(_cores))
            _cores = str(int(_cores) * _ratio) # xen vcpus across all computes
            _cores = str((int(_cores))/_num_computes)      # xen vcpus per compute : use this for range calculation
        else:
            ebLogError('*** json payload for CPU oversubscription command: poolsize not provided.')
            return ebError(0x0433)

        if aSubfactor is not None:
            _subfactor = int(aSubfactor)
        elif 'subfactor' in _jconf.keys():
            _subfactor = int(_jconf['subfactor'])

        if _subfactor == 1:
            _cos = False

        _allocatable_cores = str(int(_subfactor) * int(_cores)) # Max allowed sum of all vcpus

        if _cos:
            ebLogVerbose('*** mModifyService: Subfactor : %d | vcores_per_compute : %s' %(_subfactor, _cores))
            ebLogVerbose('*** mModifyService: Sum of vcpus cannot be more than (allocatable_cores) : %s' %(_allocatable_cores))
        else:
            ebLogVerbose('*** mModifyService (non-cos): Subfactor : %d | vcores_per_compute : %s' %(_subfactor, _cores))

        # 5 minutes default timeout for vcpu-pin operation
        _vpt = self.__ecc.mCheckConfigOption('timeout_vcpu_pin')
        if _vpt is not None:
            ebLogInfo('Default value is: %s' %(_vpt))
            _timeout_vcpu_pin = int(_vpt)
        else:
            _timeout_vcpu_pin = 300

        for _hyp, _dom in self.__ecc.mReturnDom0DomUPair():
            if (aDomain is not None) and (aDomain != _dom):
                ebLogVerbose('*** Skipping CPU Pinning for %s' %(_dom))
                continue
            ebLogVerbose('*** Attempting CPU Pinning for %s' %(_dom))
            _range_dict={}
            _cluster_list=[]
            _clusters_to_update=[]
            _pin_range_start = None

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_hyp)

            ##########
            # STEP 1 #
            ##########
            # Get the cluster list from each hypervisor.
            # TO-DO : Once ECRA provides the cluster list, validate against it.
            #  i. if ECRA's list is subset of Exacloud's list we will use ECRA list
            #  ii. if ECRA's list is a superset of Exacloud's list we will error out
            #  iii. if they are same any list should be fine

            _cmd = "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'"
            _, _out, _ = _node.mExecuteCmd(_cmd)
            if _out:
                _out = _out.readlines()
                for _line in _out:
                    if not _line.isspace():
                        _cluster_list.append(_line.strip())

            ##########
            # STEP 2 #
            ##########
            # Get the expected range with the start value after num_of_hyp_vcpus and end value would be the start+_cores-1

            #_cmd = "xm li | /bin/grep Domain-0 | /bin/awk '{ print $4 }'"
            #_, _out, _ = _node.mExecuteCmd(_cmd)
            #if _out:
            #    _out = _out.readlines()
            #    _hypvcpus = int(_out[0])
            #    ebLogInfo('*** Hypervisor %s current VCPUS allocation: %d' % (_hyp, _hypvcpus))
            #else:
            #    _node.mDisconnect()
            #    _error_str = '*** Can not retrieve Hypervisor vCPUS allocation'
            #    ebLogError(_error_str)
            #    raise ExacloudRuntimeError(0x0800, 0xA, _error

            # ********************************************************************************************
            # ***************************************TODO*************************************************
            # ********************************************************************************************
            # We start with 4, so we should ensure that the cumulative count allocated for 
            # VMs is totalcount-4. For eg: if totalcount is 96, then ensure we allocate only 92 for VMs.
            _hypvcpus = 4

            # In the non-COS case, we will generate a separate pinning range for each VM
            if not _cos:
                _dom_start_range = _hypvcpus
                _pr_start_dict={}
                _pr_end_dict={}
                _pin_range_dict={}

            ##########
            # STEP 3 #
            ##########
            # Get the sum of vcpus of all VMs (excluding Hypervisor) and validate against the max allowed value


            _sum_vcpus = 0
            for _dom in _cluster_list:
                _cmd = "/usr/bin/virsh dominfo " + _dom + " | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'"
                _, _out, _ = _node.mExecuteCmd(_cmd)
                _out = _out.readlines()
                if _out:
                    _sum_vcpus += int(_out[0])
                    ebLogInfo('*** cpucount for %s is %s' %(_dom, _out[0]))
                    # In the non-COS case, each VM gets its own range
                    if not _cos:
                        _pr_start_dict[_dom] = _dom_start_range
                        _pr_end_dict[_dom] =  _pr_start_dict[_dom] + int(_out[0]) -1
                        _dom_start_range = _pr_end_dict[_dom] + 1
                        ebLogInfo('*** Domain: %s expected pinning range: %s - %s' %(_dom, _pr_start_dict[_dom], _pr_end_dict[_dom]))
                        _pin_range_dict[_dom]="%s-%s" %(str(_pr_start_dict[_dom]),str(_pr_end_dict[_dom]))
                else:
                    _error_str = '*** Can not retrieve VCPUS allocation for (%s)' % (_dom)
                    ebLogError(_error_str)
                    _node.mDisconnect()
                    raise ExacloudRuntimeError(0x0780, 0xA, _error_str)

            if (_subfactor > 1) and (_sum_vcpus > int(_allocatable_cores)):
                _error_str = '*** Sum of vcpus (%s) > max(allocatable cores) (%s) on dom0 (%s)' % (_sum_vcpus, _allocatable_cores, _hyp)
                ebLogError(_error_str)
                raise ExacloudRuntimeError(0x0780, 0xA, _error_str)
            ebLogInfo('*** Sum of vcpus (%s) : max(allocatable cores) (%s) on dom0 (%s)' % (_sum_vcpus, _allocatable_cores, _hyp))

            if _cos:
                _pin_range_start = _hypvcpus
                _pin_range_end = _pin_range_start + int(_cores) - 1

                _expected_range="%s-%s" %(str(_pin_range_start),str(_pin_range_end))
                ebLogInfo('*** expected range : <%s>' %(_expected_range))


            ##########
            # STEP 4 #
            ##########
            #validate the range & do a hot-update & on-disk update of the vm.cfgs as needed with the new pinning pool

            domsvcpus = dict()
            for _dom in _cluster_list:
                _cpuranges=[]
                vcpu = []
                _cmd = "/usr/bin/virsh vcpuinfo " + _dom + " --pretty | /bin/grep VCPU | /bin/awk '{print$2}'"
                _, _out, _ = _node.mExecuteCmd(_cmd)
                _out = _out.readlines()
                if _out:
                    for _line in _out:
                        vcpu.append(_line.lstrip().rstrip())
                        _cmd = "/usr/bin/virsh vcpupin --domain " + _dom + " --vcpu " + _line.lstrip().rstrip() + " | /bin/tail -n+3 | /bin/awk '{print $2}'"
                        _, _out2, _ = _node.mExecuteCmd(_cmd)
                        _out2 = _out2.readlines()
                        if _out2:
                            _cpuranges.append(_out2[0].lstrip().rstrip())
                    domsvcpus[_dom] = vcpu

                    if _cos:
                        if (len(set(_cpuranges)) > 1) or (_expected_range not in _cpuranges):
                            _clusters_to_update.append(_dom)
                            ebLogInfo('*** COS: Pin range of %s will be changed to %s' %(_dom, _expected_range))
                        else:
                            ebLogInfo('*** COS: domain %s does not need a pinning change' %(_dom))
                    else:
                        if ((len(set(_cpuranges)) > 1) or (_pin_range_dict[_dom] not in _cpuranges)) or (_dom == aDomain):
                            _clusters_to_update.append(_dom)
                            ebLogInfo('*** non-COS: Pin range of %s will be changed to %s' %(_dom, _pin_range_dict[_dom]))
                        else:
                            ebLogInfo('*** non-COS: domain %s does not need a pinning change' %(_dom))
                else:
                    _clusters_to_update.append(_dom)

            if len(_clusters_to_update) == 0:
                ebLogInfo('*** Pinning range does not need a change for all clusters !')
            else:
                ebLogInfo('*** Pinning range will be changed now')
                for _dom in _clusters_to_update:
                    ebLogVerbose('*** Updating pinning range for %s' %(_dom))
                    if self.mIsActiveGuest(_node, _dom):
                        ebLogInfo('*** Domain (%s) is pingable.' % (_dom))
                        if _cos:
                            for vcpu in domsvcpus[_dom]:
                                _cmd = "/usr/bin/virsh vcpupin --domain " + _dom + " --vcpu " + vcpu + " " + _expected_range + " --live --config"
                                ebLogInfo('***Executing %s' %(_cmd))
                                _node.mExecuteCmdLog(_cmd)
                        else:
                            for vcpu in domsvcpus[_dom]:
                                _cmd = "/usr/bin/virsh vcpupin --domain " + _dom + " --vcpu " + vcpu + " " + _pin_range_dict[_dom] + " --live --config"
                                ebLogInfo('***Executing %s' %(_cmd))
                                _node.mExecuteCmdLog(_cmd)
                    else:
                        ebLogInfo('*** Domain (%s) is NOT pingable.' % (_dom))
                        if _cos:
                            for vcpu in domsvcpus[_dom]:
                                _cmd = "/usr/bin/virsh vcpupin --domain " + _dom + " --vcpu " + vcpu + " " + _expected_range + " --config"
                                ebLogInfo('***Executing %s' %(_cmd))
                                _node.mExecuteCmdLog(_cmd)
                        else:
                            for vcpu in domsvcpus[_dom]:
                                _cmd = "/usr/bin/virsh vcpupin --domain " + _dom + " --vcpu " + vcpu + " " + _pin_range_dict[_dom] + " --config"
                                ebLogInfo('***Executing %s' %(_cmd))
                                _node.mExecuteCmdLog(_cmd)


            ##########
            # STEP 5 #
            ##########
            # Validate the pinning range for all live VMs only if there was an update.

            if len(_clusters_to_update) != 0:
                _total_time = 0
                _check_intv = 10
                _suc = 0

                if _cos:
                    ebLogInfo('*** Validating pinning range for %s' %(_hyp))
                    for _dom in _cluster_list:
                        if not self.mIsActiveGuest(_node, _dom):
                            ebLogInfo('*** vm %s is not pingable, hence skipping' %(_dom))
                            _suc += 1
                            continue
                        while _total_time < _timeout_vcpu_pin:
                            _cmd = "/usr/bin/virsh vcpuinfo " + _dom + " --pretty | /bin/grep Affinity | /bin/awk '{print$3}' | /bin/sort | /bin/uniq"
                            _, _out, _ = _node.mExecuteCmd(_cmd)
                            if _out:
                                _out = _out.readlines()
                                if (len(_out) ==1) and  (_out[0].strip() == _expected_range.strip('\'')):
                                    ebLogInfo('*** CPU pinning range updated successfully on %s' % (_dom))
                                    _suc += 1
                                    break
                                else:
                                    time.sleep(_check_intv)
                                    _total_time += _check_intv

                    if _suc != len(_cluster_list):
                        _node.mDisconnect()
                        _error_str = '*** The pinning range is not same across clusters or incorrect range on %s' %(_hyp)
                        ebLogError(_error_str)
                        raise ExacloudRuntimeError(0x0780, 0xA, _error_str)
                    else:
                        ebLogInfo('*** CPU pinning range updated successfully on all domains in %s' % (_hyp))
                else:
                    ebLogInfo('*** Validating pinning range for %s' %(_hyp))

                    _suc = 0
                    for _dom in _clusters_to_update:
                        if not self.mIsActiveGuest(_node, _dom):
                            ebLogInfo('*** Skipping validation of pinning range for %s as VM is not up' %(_dom))
                            _suc = 1    # This will take care of cases where all vms are down !
                            continue

                        _total_time = 0
                        _check_intv = 10
                        _cmd = "/usr/bin/virsh vcpuinfo " + _dom + " --pretty | /bin/grep Affinity | /bin/awk '{print$3}' | /bin/sort | /bin/uniq"
                        while _total_time < _timeout_vcpu_pin:
                            time.sleep(_check_intv)
                            _, _out, _ = _node.mExecuteCmd(_cmd)
                            if _out:
                                _out = _out.readlines()
                                if (len(_out) ==1) and  (_out[0].strip() == _pin_range_dict[_dom].strip('\'')):
                                    ebLogInfo('*** CPU pinning range updated successfully on %s' % (_dom))
                                    _suc = 1
                                    break
                                else:
                                    ebLogInfo('*** CPU pinning range NOT yet updated on %s' % (_dom))
                                    _suc = 0
                            else:
                                _node.mDisconnect()
                                _error_str = '*** Can not retrieve vCPUS allocation for %s' %(_dom)
                                ebLogError(_error_str)
                                raise ExacloudRuntimeError(0x0780, 0xA, _error_str)
                            _total_time += _check_intv
                        if _suc == 0:
                            break
                    if _suc == 0:
                        _node.mDisconnect()
                        _error_str = '*** Error: The pinning range is incorrect on %s' %(_hyp)
                        ebLogError(_error_str)
                        raise ExacloudRuntimeError(0x0780, 0xA, _error_str)

            _node.mDisconnect()

        return 0


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
        _partial_update = False
        _configvcpus = None
        _currvcpus = None
        _dict_list = []
        _half_way_mark = False


        ebLogVerbose("mManageVMCpusCount: aVMCmd = %s, aVMId = %s" % (aVMCmd, aVMId))

        def _mUpdateRequestData(aDataD):
            _data_d = aDataD
            _reqobj = self.__ecc.mGetRequestObj()
            if _reqobj is not None:
                _reqobj.mSetData(json.dumps(_data_d))
                _db = ebGetDefaultDB()
                _db.mUpdateRequest(_reqobj)

        _valid_modes = ['dg_vmmaker', 'dg_oedacli', 'vm_maker']
        _cpu_manage_mode = self.__ecc.mCheckConfigOption('cpu_manage_mode')
        if _cpu_manage_mode is not None:
            ebLogInfo('***Tooling used for cpu resize: ' + _cpu_manage_mode)

        if _cpu_manage_mode is not None and _cpu_manage_mode in _valid_modes:
            if _cpu_manage_mode == "dg_vmmaker":
                ebLogInfo('***Domain Group implementation with vm_maker ***')
                _exacpueobj = exaBoxKvmDgrpVmkr(self.__ecc)
                return _exacpueobj.mManageVMCpusCountKvm(aVMCmd, aVMId, aOptions)
            if _cpu_manage_mode == "dg_oedacli":
                #TODO
                ebLogError('***Domain Group implementation with oedacli is not yet supported !***')
                return

        ebLogInfo('*** KVM: resize of cpus using vm_maker***')

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
            _detail_error = ('json payload for VMCpusCount command: %s not provided.' % (_vmcmd))
            ebLogError('*** '+ _detail_error)
            _mUpdateRequestData(_data_d)
            self.__ecc.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
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
            ebLogInfo('*** mManageVMCpusCountKvm: core to cpu ratio is : %d' %(_ratio))

        _host_d = {}
        try:
            if 'vms' in _jconf.keys():
                for _h in _jconf['vms']:
                    _host_d[_h['hostname']] = {}
                    _host_d[_h['hostname']]['cpus'] = int(_h['cores']) * _ratio
                    # xxx/MR: Add support to deltacores if needed.
            elif "exaunitAllocations" in _jconf.keys():
                for _, _domU in self.__ecc.mReturnDom0DomUPair():
                    _host_d[_domU] = {}
                    _host_d[_domU]['cpus'] = int(_jconf['exaunitAllocations']['cores']) * _ratio
        except Exception as e:
            _detail_error = "mManageVMCpusCount Exception:: %s - %s" % (e.__class__, e)
            ebLogError(_detail_error)
            _mUpdateRequestData(_data_d)
            self.__ecc.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
            return ebError(0x0430)

        #
        # Check if payload is valid
        #
        if not len(_host_d.keys()) and not _review:
            _detail_error = 'vm cpu count/delta not found in payload'
            ebLogError('*** '+ _detail_error)
            ebLogWarn('*** Payload: %s' % (str(_jconf)))
            _mUpdateRequestData(_data_d)
            self.__ecc.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
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
                    _poolsize = str(int(_poolsize) * int(_ratio)) # xen vcpus across all computes
                    ## There seems to be a bug in below line.. need to see why it is required.
                    #_poolsize = str((int(_poolsize))/_num_computes[self.mGetRackSize()])                # xen vcpus per compute
                    _allocatable_cores = str(int(_subfactor) * int(_poolsize)) # Max allowed sum of all vcpus
                    ebLogInfo('*** COS: allocatable cores are : %s' %(_allocatable_cores))
                else:
                    ebLogError('*** json payload for cpu oversubscription does not have poolsize.')
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

        _dom0s_pingable, _dom0s_offline = self.__ecc.mCheckDom0sPingable()
        if len(_dom0s_pingable) == 0:
            _mUpdateRequestData(_data_d)
            _error_str = 'cpu resize failed as none of the Dom0s are pingable'
            ebLogError('*** ' + _error_str)
            self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_VM_CPU_RESIZE_PINGABLE'],_error_str)
            raise ExacloudRuntimeError(0x0430, 0xA, _error_str)

        _pingable_vm_count = 0
        #set #1 will be half of pingable vm count.
        _set1_count = 0
        _ddpair = []
        for _hyp, _dom in self.__ecc.mReturnDom0DomUPair():
           
            if _vmid != '_all_' and _vmid != _dom:
                continue

            if _dom not in _host_d.keys() and not _review:
                continue

            if _hyp not in _dom0s_pingable:
                _partial_update = True
                ebLogWarn('*** vm cpu count will be partially updated as dom0 %s is not pingable'%(_hyp))
                continue

            with connect_to_host(_hyp, get_gcontext()) as _node:
                if self.mIsActiveGuest(_node, _dom):
                    _pingable_vm_count += 1
                    _host_d[_dom]['active'] = True
                    if self.__ecc.mCheckConfigOption('cpuresize_check_reboots') == 'True':
                        _fname = f"serial-{self.__ecc.mGetUUID()}-{_dom}.log.1"
                        _l_log_file = self.mGetConsoleLog(_hyp, _dom, _fname)
                        if _l_log_file is not None:
                            _host_d[_dom]['consoleaccess'] = True
                            _host_d[_dom]['logbeforeresize'] = _l_log_file 
                else:
                    _host_d[_dom]['active'] = False
                    ebLogInfo(f"*** Domain {_dom} is not in running state!")

            _ddpair.append([_hyp, _dom])

        _total_vms = len(_ddpair)
        ebLogInfo(f'Total vms to resized: {_total_vms}')
        _index = 0
        for _hyp, _dom in _ddpair:
           
            #
            # Initialize _data_d
            #
            _data_d['vms'][_dom] = {}
            #
            # Fetch new cores number for the VM
            #
            if not _review:
                _vcpus = int(_host_d[_dom]['cpus'])
            else:
                _vcpus = 0

            ebLogInfo(f'*** cpu resize request: {_vcpus} cpus for vm {_dom}')
            _index += 1

            #TODO: We should be ideally checking output of "numactl -H" and look for available number of nodes to
            # deduce the minimum vcpu count. Its possible that minimum value for vcpu count could be more than 4 depending on configuration.
            #For now, setting it to 4.
            if not self.__ecc.isBaseDB() and not self.__ecc.isExacomputeVM() and _vcpus < _minvcpus:
                _vcpus = _minvcpus
                ebLogInfo('*** Changing cpu count to %d ' %(_minvcpus))

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_hyp)
            _in, _out, _err = _node.mExecuteCmd("/usr/bin/virsh nodeinfo | /bin/grep 'CPU(s)' | /bin/awk '{print$2}'")
            if _out:
                _out = _out.readlines()
                _dat = _out[0].strip()
                _reserved = HYPERVISOR_RSRVD_CORES * self.__ht_factor
                _in, _out, _err = _node.mExecuteCmd("/usr/sbin/vm_maker --list --vcpu | /bin/grep 'Host reserved' | /bin/awk '{print $5}'")
                _out = _out.readlines()
                if _out and len(_out):
                    _reserved = _out[0].strip()
                    ebLogInfo(f'*** cpus reserved for the dom0 {_hyp}: {_reserved}')
                _maxcores = int(_dat) - int(_reserved)
                ebLogInfo(f'*** In dom0 {_hyp}, the total cpus allocated for all the guests cannot exceed {_maxcores}')
                # If cos enabled, consider virtual max cores
                if _cos:
                    ebLogInfo('*** Maximum cos value on dom0 %s : %s' % (_hyp, _allocatable_cores))
                    _maxvcores = int(_allocatable_cores)

            _is_pingable = _host_d[_dom]['active']
            #
            # Fetch current vCPU for Domain
            #
            _in, _out, _err = _node.mExecuteCmd("/usr/sbin/vm_maker --list --vcpu --domain %s | /bin/awk -F: '{print $4}'" % (_dom))

            #virsh command runs successfully even if domain is shutdown.
            if _out:
                _out = _out.readlines()
                _currvcpus = int(_out[0].strip())
                ebLogTrace(f'*** Existing cpu count for {_dom} : {_currvcpus}')
                #
                # Fetch current MAXVCPUs (not the one set in vm.cfg)
                #
            _in, _out, _err = _node.mExecuteCmd("/usr/bin/virsh vcpucount %s | /bin/grep maximum | /bin/grep config | /bin/awk '{print $3}'" % (_dom))
            if _out:
                _out = _out.readlines()
                _currmaxvcpus = int(_out[0])
                ebLogTrace('*** Maximum allocatable cpus for domain %s : %d' % (_dom, _currmaxvcpus))

            _data_d['vms'][_dom]['currvcpus']    = _currvcpus
            _data_d['vms'][_dom]['currmaxvcpus'] = _currmaxvcpus
            #
            # Check if new VCPUs count is 2X more than current VCPUs
            #
            if _vcpus > _currvcpus * 2:
                ebLogWarn('*** Requested cpu count of %s for %s is 2 times higher than existing cpu count %s' % (str(_vcpus),_dom,str(_currvcpus)))
            #
            # Fetch current vCPUs used by all VMs (including hypervisor)
            #

            # We use vm_maker to get all VCPUs from all DomUs and log it

            _cmd = "/usr/sbin/vm_maker --list --vcpu"
            _out_vcpu_list = node_exec_cmd_check(_node, _cmd)
            ebLogTrace(f"VCPU list from Dom0 {_hyp}:\n{_out_vcpu_list}")

            # Then we parse the CPUs in use in Exacloud
            # String expected for below regex:
            # [root@sea201602exdd001 ~]# vm_maker --list --vcpu
            # gold-luks-real-k0obn1.client.exaclouddev.oraclevcn.com: Current: 32 Restart: 32
            #                                          ----------
            # Total VCPU required for reboot         : 32 (assumes restart situation)
            # Host reserved PCPU                     : 4
            # Available VCPU (now)                   : 168
            # Available VCPU (delayed)
            _match = re.search(
                "Total\s+vcpu\s+[a-zA-Z\s]+:\s+([0-9]+)",
                _out_vcpu_list.stdout, re.IGNORECASE)
            if not _match:
                _detail_error = (f"Could not parse the current VCPUs with vm_maker. "
                    f"Make sure the Dom0 responds to the command: {_cmd} "
                    " and then retry the CPU Reshape")
                ebLogError('*** '+ _detail_error)
                _mUpdateRequestData(_data_d)
                self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_VCPUS_ALLOC'], _detail_error)
                _node.mDisconnect()
                return ebError(0x0433)

            _vcpusinuse = _match.groups()[0]
            _vcpusleft  = 0

            try:
                _vcpusinuse = int(_vcpusinuse)
            except Exception as e:
                _detail_error = (f"Could not parse the current VCPUs value obtained. "
                    f"Make sure the Dom0 responds properly to the command: {_cmd} "
                    " and then retry the CPU Reshape")
                ebLogError('*** '+ _detail_error)
                _mUpdateRequestData(_data_d)
                self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_VCPUS_ALLOC'], _detail_error)
                _node.mDisconnect()
                return ebError(0x0433)

            if _maxvcores:
                _vcpusleft = _maxvcores - _vcpusinuse
            else:
                _vcpusleft = _maxcores - _vcpusinuse

            ebLogInfo('*** Current cpu allocation in dom0 %s : %d (%d left)' % (_hyp, _vcpusinuse, _vcpusleft))

            _left = _vcpusleft
            _requested = (_vcpus - _currvcpus)
            _vcpusleft = _vcpusleft - (_vcpus - _currvcpus)
            if _vcpusleft < 0:
                _detail_error = 'cpu over-provisioning detected !!! (%d left / %d requested)' % (_left,_requested)
                ebLogError('*** '+ _detail_error)
                _node.mDisconnect()
                _mUpdateRequestData(_data_d)
                self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_VCPU_OVERSUBSCRIBED'], _detail_error)
                return ebError(0x0431)

            if _cos:
                _maxvcoresdomu = (int(_maxvcores)/int(_ratio))
                if _maxvcoresdomu < _vcpus:
                    _detail_error = 'cpu over-provisioning detected !!! (max(allocatable cores) (%d) on domain (%s) /  %d requested)' % (_maxvcoresdomu,_dom,_requested)
                    ebLogError('*** '+ _detail_error)
                    _node.mDisconnect()
                    _mUpdateRequestData(_data_d)
                    self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_VCPU_OVERSUBSCRIBED'], _detail_error)
                    return ebError(0x0431)

            #
            # Check vm.cfg settings : maxvcpus and current vCPUs
            #
            _cmd = "/usr/bin/virsh vcpucount " + _dom + " | /bin/grep maximum | /bin/grep config | /bin/awk '{print $3}'"
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            if _out:
                _out = _out.readlines()
                _maxvcpus = int(_out[0].strip())
            #
            # _data_d udpate
            #
            _data_d['vms'][_dom]['cfgmaxvcpus'] = _maxvcpus
            #
            # Check for discrepancy between current and <vm>.xml maxvcpus values
            #
            if _currmaxvcpus != 0 and _currmaxvcpus != _maxvcpus:
                ebLogWarn('*** Max cpu count for domain in xml not applied to running VM (xml:%s/current:%s)' % (_maxvcpus,_currmaxvcpus))
                if not _review:
                    _data_d['vms'][_dom]['bursting_enabled'] = 'False'
                    _data_d['bursting_enabled'] = 'False'
                    _data_d['bursting_ready'] = 'False'
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
            if _vcpus > _maxvcpus and not _review:
                _detail_error = 'domain limit of max cpu count (%d) is lower than new number of cores requested: %d' %(_maxvcpus,_vcpus)
                ebLogError('*** '+ _detail_error)
                _node.mDisconnect()
                _mUpdateRequestData(_data_d)
                self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_MAX_CPU_LESS'], _detail_error)
                return ebError(0x0434)

            if _vcpus == _currvcpus and not _review:
                ebLogWarn(f'*** domain cores already matching cores numbers in resize request for {_dom}')
                _node.mDisconnect()
                if _is_pingable:
                    _set1_count += 1
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
            ebLogInfo(f'*** Guest {_dom}: existing cpu count: {_currvcpus}, requested cpu count: {_vcpus}')
            #
            # Adjust vcpu on Domain
            #
            _cpu_resize_success = False
            if not _review and _cos:
                #
                # modify cluster with CPU oversubscription factor; do update the vcpu count as needed
                #
                if _cos:
                    _sum_vcpus = 0

                    _cluster_list=[]
                    _cmd = "/usr/sbin/vm_maker --list-domains | /bin/awk '{print $1}'"
                    _, _out, _ = _node.mExecuteCmd(_cmd)
                    if _out:
                        _out = _out.readlines()
                        for _line in _out:
                            if not _line.isspace():
                                _cluster_list.append(_line.strip().split('(')[0])

                    for _vm in _cluster_list:
                        _in, _out, _err = _node.mExecuteCmd("/usr/sbin/vm_maker --list --vcpu --domain %s | /bin/awk -F: '{print $4}'" % (_vm))
                        _out = _out.readlines()
                        if _out:
                            # sum all vcpus except the domain whose _vcpus is getting updated.
                            if _vm not in _dom:
                                _sum_vcpus += int(_out[0].strip())
                        else:
                            _detail_error = 'Can not retrieve cpu allocation for (%s)' % (_dom)
                            ebLogError('*** ' + _detail_error)
                            _node.mDisconnect()
                            self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_VCPUS_ALLOC'],_detail_error)
                            raise ExacloudRuntimeError(0x0780, 0xA, _detail_error)

                    # We don't need the range check since modify_service should have
                    # taken care of range check for all clusters.
                    # Verification of the sum of vcpus <= allocatbale cores, should suffice
                    # _vcpus is the new cores value for the domain

                    if (int(_allocatable_cores) - _sum_vcpus) < _vcpus:
                        _detail_error = 'Number of cores is more than the maximum allowed value for %s' % (_dom)
                        ebLogError('*** ' + _detail_error)
                        _node.mDisconnect()
                        self.__ecc.mUpdateErrorObject(gReshapeError['INVALID_ALLOC_SIZE'], _detail_error)
                        raise ExacloudRuntimeError(0x0780, 0xA, _detail_error)
                    else:
                        ebLogInfo('****** COS: Executing cpu resize')
                        _result = {}
                        self.mSetVCPUandValidate(_dom, _vcpus, _hyp, _is_pingable, _result)


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
                    _poolsize = str(_vcpusinuse + _vcpus - _currvcpus - _hypvcpus)
                    ebLogVerbose('*** Poolsize calculated is %s' %(_poolsize))

                # Ensure subfactor is 1
                _subfactor = 1

                _vm_rebooted = False
                #
                # Dynamic vCPUs change
                #
                ebLogInfo('****** Non-COS: Executing cpu resize')
                if _is_pingable:
                    _set1_count += 1
                ebLogTrace(f"set #1 ite: {_set1_count}, 50% pingable-vm count: {_pingable_vm_count/2}")
                _restart = False
                _vmhandle = None
                if self.__ecc.isBaseDB() or self.__ecc.isExacomputeVM():
                    '''
                    For baseDB/ggs, we allow core updates from 1 core to higher core and from a higher core count to 1 core.
                    In both the cases, we can perform core update, only if VM is down.
                    For basedb customers, its ok to reboot VM during cpu resize operation.
                    '''
                    if(_is_pingable is True and (_currvcpus/_ratio == 1 or _vcpus/_ratio == 1)):
                        ebLogInfo(f"Shutting down VM {_dom} since we are trying to resize from/to 1 core !")
                        _vmhandle = ebVgLifeCycle()
                        _vmhandle.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_node)
                        _rc = _vmhandle.mDispatchEvent('shutdown', aOptions=None, aVMId=_dom)
                        if _rc == 0:
                            ebLogInfo('Shutdown of VM is successful!')
                            _restart = True
                            _is_pingable = False
                        else:
                            _detail_error = f"VM {_dom} failed to stop before cpu reshape"
                            ebLogError('*** '+ _detail_error)
                            self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_VM_NOT_RUNNING'], _detail_error)
                            return ebError(0x0451)

                _domu_dict = {}
                _domu_dict["domu"] = _dom
                _domu_dict["vcpus"] = _vcpus
                _domu_dict["dom0"] = _hyp
                _domu_dict["pingable"] = _is_pingable
                _dict_list.append(_domu_dict)

                if _set1_count == int(_pingable_vm_count/2):
                    _half_way_mark = True
                    _result = self.mResizeCpus(_dict_list)
                    _dict_list = []
                elif _index == _total_vms:
                    _result = self.mResizeCpus(_dict_list)
                else:
                    continue

                if _restart:
                    ebLogInfo(f"Starting VM {_dom} after cpu reshape !")
                    _rc = _vmhandle.mDispatchEvent('start', aOptions=None, aVMId=_dom)
                    if _rc == 0:
                        ebLogInfo('Start of VM is successful!')
                        _is_pingable = True
                    else:
                        _detail_error = f"VM {_dom} failed to start after cpu reshape"
                        ebLogError('*** '+ _detail_error)
                        self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_VM_NOT_RUNNING'], _detail_error)
                        return ebError(0x0452)
                '''
                During resize of cpus, sometimes a vm may reboot due to a kernel issue.
                We want to detect such a reboot. And abort the cpu resize for rest of the vms.
                This is a workaround in exacloud untill the issue is fixed in teh kernel side.
                We just split the number of nodes into 2 sets. We will first do resize of set #1.
                Then check if any reboots happened in the set #1.
                If any reboots happened, then abort the resize for set #2.
                '''
                if self.__ecc.mCheckConfigOption('cpuresize_check_reboots') == 'True' and _half_way_mark == True:
                    ebLogInfo(f"Sleeping for 2 minutes before checking for VM reboot")
                    time.sleep(120)
                    _vm_rebooted = self.mCheckForReboots(_ddpair, _set1_count, _host_d)

                    if _vm_rebooted:
                        _detail_error = f"VM got rebooted after cpu resize. Aborting the resize of other VMs."
                        ebLogError('*** '+ _detail_error)
                        self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_VCPU_RESIZE_FAILED'], _detail_error)
                        return ebError(0x0430)
                    else:
                        ebLogInfo(f"VM reboots did not occur. Continuing with resize for other VMs.")

                    _half_way_mark = False

                # Invoke mModifyService() to do pinning
                self.__ecc.mModifyService(aOptions, _subfactor, _poolsize, _dom)

            #
            # Check if vCPUs have been updated effectively.
            #
            if not _review:
                ebLogInfo(f'*** mManageVMCpusCountKvm result:{_result}')
                for _domu, _val in _result.items():
                    _cpu_resize_success = _val["cpu_resize_success"]
                    _currvcpus = _val["currvcpus"]
                    _configvcpus = _val["configvcpus"]
                    if not _cpu_resize_success:
                        _detail_error = 'domain cpu update not successful. current: %d - requested: %d - Configured: %d' % (_currvcpus,_vcpus, _configvcpus)
                        ebLogError('*** '+ _detail_error)
                        try:
                            self.fetchDiagLogs(_hyp, _node)
                        except Exception as e:
                            ebLogError(f"Error while fetching diagnostic logs: {str(e)}")
                        _node.mDisconnect()
                        _mUpdateRequestData(_data_d)
                        self.__ecc.mUpdateErrorObject(gReshapeError['ERROR_VCPU_RESIZE_FAILED'], _detail_error)
                        return ebError(0x0430)
                    else:
                        ebLogInfo(f'*** domain cpu update successfull for {_domu}.')
                
            _node.mDisconnect()

        if _partial_update:
            _mUpdateRequestData(_data_d)
            _dbNodeData = []
            for _nodeData in _dom0s_offline:
                _ndata = {}
                _ndata['hostname'] = _nodeData.strip()
                _dbNodeData.append(_ndata)
            _error_str = 'cpu resize failed to update all nodes as following Dom0s are not pingable %s'%(str(_dom0s_offline))
            ebLogError('*** ' + _error_str)
            self.__ecc.mUpdateErrorObject(gPartialError['ERROR_VM_CPU_RESIZE_PARTIAL'], _error_str, _dbNodeData)
            raise ExacloudRuntimeError(0x0436, 0xA, _error_str)

        #
        # update _data_d and flush request.data field to DB
        #
        if _cpu_bursting != None and _cpu_bursting == 'True':
            _data_d['bursting_ready'] = 'True'
        _mUpdateRequestData(_data_d)

        return 0

    def mResizeCpus(self, aDictList):

        _dict_list = aDictList
        _ret_dict_list = []
        run_in_parallel = False

        if self.__ecc.mCheckConfigOption('cpu_resize_run_parallel', 'True'):
            run_in_parallel = True

        if run_in_parallel:
            _plist = ProcessManager()
            _result = _plist.mGetManager().dict()

            for _domu_dict in _dict_list:
                _p = ProcessStructure(self.mSetVCPUandValidate, [_domu_dict["domu"], _domu_dict["vcpus"], _domu_dict["dom0"], _domu_dict["pingable"], _result])
                _p.mSetMaxExecutionTime(30*60) # 30 minutes
                _p.mSetJoinTimeout(5)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
            _plist.mJoinProcess()

            _ret = copy.deepcopy(dict(_result))
            return _ret

        _result = {}
        for _domu_dict in _dict_list:
            self.mSetVCPUandValidate(_domu_dict["domu"], _domu_dict["vcpus"], _domu_dict["dom0"], _domu_dict["pingable"], _result)

        return _result

    def mGetConsoleLog(self, aHyp, aDom, aFname):
        _hyp = aHyp
        _dom = aDom
        _fname = aFname
        if self.__ecc.mCheckConfigOption('history_console_timeout_in_seconds') is not None:
            _cmd_timeout = int(self.__ecc.mCheckConfigOption('history_console_timeout_in_seconds'))
        else:
            _cmd_timeout = 300

        with connect_to_host(_hyp, get_gcontext()) as _node:
            _fpath = f"/tmp/{_fname}"
            if not _node.mFileExists("/opt/exacloud/vmconsole/history_console.py"):                                                                                                                            
                ebLogTrace(f"serial console not available in dom0 {_hyp}")
                return None
            _cmd = f"/usr/bin/python3 /opt/exacloud/vmconsole/history_console.py --host {_dom} --path {_fpath}"                                                                                            
            _node.mExecuteCmd(_cmd, aTimeout=_cmd_timeout)
            if _node.mGetCmdExitStatus() != 0:
                ebLogError(f"mGetConsoleLog: Failed to retreive serial console log from dom0 {_hyp}")
                return None
            _l_log_file = f"{self.__ecc.mGetOedaPath()}/log/{_fname}"
            if _node.mFileExists(_fpath):
                _node.mCopy2Local(_fpath, _l_log_file)
                _cmd = f"/bin/rm -f {_fpath}"
                _node.mExecuteCmd(_cmd)
                if not os.path.exists(_l_log_file):
                    ebLogError(f"Unable to copy file {_fname} to local box!")
                    return None
        ebLogTrace(f"Retreived console log in path: {_fname}")
        return _l_log_file

    '''
    There are cases where a VM kernel may crash and reboot during cpuresize operation.
    The purpose of the function mCheckForReboots is to detect such reboots.
    Approach:
    a. Capture console log before reboot.
    b. perform resize operation.
    c. Capture the console log again.
    d. Perform a diff of the 2 log files and check for markers that suggest a reboot occurred.
    '''
    def mCheckForReboots(self, aDdpair, aSetcount, aHostd):
        _set1_count = aSetcount
        _ddpair = aDdpair
        _host_d = aHostd
        _ite = 0

        try:
            for _hyp, _dom in _ddpair:
                if _host_d[_dom]['consoleaccess'] != True:
                    continue

                _ite += 1
                if _ite > _set1_count:
                    ebLogTrace('*** Finished checking all nodes for reboots in set 1')
                    break

                _fname = f"serial-{self.__ecc.mGetUUID()}-{_dom}.log.2"
                _l_log_file = self.mGetConsoleLog(_hyp, _dom, _fname)
                if _l_log_file is None:
                    continue

                file1 = _host_d[_dom]['logbeforeresize']
                file2 = _l_log_file
                _reboot_string = self.__ecc.mCheckConfigOption('vm_reboot_consolelog_markers')
                with open(file1, "r") as f1, open(file2, "r") as f2:
                    diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=file1, tofile=file2)
                    for line in diff:
                        if line.startswith("+") and any(s in line for s in _reboot_string):
                            #In the diff log, look at only additions.. not removals
                            #Lines beginning with '+' are additions.
                            ebLogError(f"VM {_dom} was rebooted immediately after cpu resize. Suspecting a Kernel crash !")
                            return True

            #remove files after comparision!
            _file_list = glob.glob(f"{self.__ecc.mGetOedaPath()}/log/serial-{self.__ecc.mGetUUID()}-*")
            for _file in _file_list:
                os.remove(_file)

        except Exception as e:
            ebLogError(f"mCheckForReboots error: {str(e)}")

        return False

    def mSetVCPUandValidate(self, aDom, aVcpus, aNode, aPingable, aResult):
        ret = False
        currvcpus = None
        configvcpus = None
        retry_count = 6
        result = aResult
        result[aDom] = {}

        _pvl = self.__ecc.mCheckConfigOption('timeout_vmcpu_resize')
        if _pvl is not None:
            self.__timeout_vmcpu_resize = int(_pvl)
        else:
            self.__timeout_vmcpu_resize = 15
        _cmd = ''

        _pvl = self.__ecc.mCheckConfigOption('setvcpu_retry_count')
        if _pvl is not None:
            retry_count = int(_pvl)

        # Get max timeout from exabox.conf
        _timeout_sec = str(get_gcontext().mGetConfigOptions(
                ).get("cpuresize_timeout_setvcpu", 600))


        ebLogTrace(f"Setting timeout for set-vcpus command to: {_timeout_sec}")

        if aPingable:
            _cmd = (f"timeout {_timeout_sec} /usr/sbin/vm_maker --set --vcpu "
                f"{aVcpus} --domain {aDom} --force")
        else:
            _cmd = (f"timeout {_timeout_sec} /usr/sbin/vm_maker --set --vcpu "
                f"{aVcpus} --domain {aDom} --config --force")
        ebLogInfo('****** cpu resize for Domain %s: Executing: %s  ' %(aDom,_cmd))
        with connect_to_host(aNode, get_gcontext()) as _node:
            while retry_count !=0:
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                if _node.mGetCmdExitStatus():
                    _error_str = 'cpu resize command failed on: {0} for Domain: {1} err: {2}'.format(_node.mGetHostname(), aDom, _e.read())
                    ebLogWarn(_error_str)
                #
                # Check if vCPUs have been updated effectively.
                # Default timeout of 30 seconds (30 sec)
                time.sleep(self.__timeout_vmcpu_resize)
                ebLogInfo(f'****** cpu resize for Domain {aDom}: Finished')

                # If the below command is successful and the VM is UP, we expect its stdout to be like:
                # [root@sea201602exdd001 ~]# /usr/sbin/vm_maker --list --vcpu --domain c1602n1c1.client.mvmvcn.oraclevcn.com
                # c1602n1c1.client.mvmvcn.oraclevcn.com  : Current: 20 Restart: 20
                # [root@sea201602exdd001 ~]#
                #
                # If the below command is successful and the VM is DOWN, we expect its stdout to be like:
                # [root@sea201602exdd001 ~]# /usr/sbin/vm_maker --list --vcpu --domain c1602n1c1.client.mvmvcn.oraclevcn.com
                # c1602n1c1.client.mvmvcn.oraclevcn.com  : Current: 0 (domain is down) Restart: 20
                # [root@sea201602exdd001 ~]#
                ebLogInfo(f'*** Fetching guest cpu count from dom0, to validate if cpu resize was successful')
                _in, _out, _err = _node.mExecuteCmd("/usr/sbin/vm_maker   --list   --vcpu   --domain %s" % (aDom))
                if _node.mGetCmdExitStatus():
                    _error_str = 'VM maker list cpu command failed on: {0} for Domain: {1} err: {2}'.format(_node.mGetHostname(), aDom, _err.read())
                    ebLogWarn(_error_str)
                    # wait for 30 sec since command failed and retry
                    time.sleep(self.__timeout_vmcpu_resize)
                    retry_count -=1
                    continue
                if _out:
                    currvcpus = None
                    configvcpus = None
                    try:
                        _out = _out.readlines()[0]
                        _current_vcpus_index = _out.index("Current")
                        _config_vcpus_index = _out.index("Restart")
                        _out_current_vcpus = _out[_current_vcpus_index:_config_vcpus_index]
                        _out_current_vcpus_list = _out_current_vcpus.split(":")
                        _out_config_vcpus = _out[_config_vcpus_index:]
                        _out_config_vcpus_list = _out_config_vcpus.split(":")

                        # If the VM is down, don't check the currvcpus value as we only care for configvcpus
                        if not aPingable:
                            ebLogInfo(f"The VM {aDom} was detected to be down, Exacloud will not check for "
                                    f"current vcpus value: '{_out_current_vcpus}'")
                            currvcpus = aVcpus
                        else:
                            currvcpus = int(_out_current_vcpus_list[1].strip())
                        configvcpus = int(_out_config_vcpus_list[1].strip())
                        ebLogInfo(f'*** Guest {aDom}: live cpu count: {currvcpus}, config cpu count: {configvcpus}')
                    except Exception as ex:
                        _error_str = 'Unable to read live cpu and config cpu count on: {0} for Domain: {1} err: {2}'.format(_node.mGetHostname(), aDom, str(ex))
                        ebLogError(_error_str)

                    if currvcpus == aVcpus and configvcpus == aVcpus:
                        ret = True
                        break
                    elif currvcpus == aVcpus and configvcpus != aVcpus and aPingable:
                        _cmd =  "/usr/sbin/vm_maker --set --vcpu " + str(aVcpus) + " --domain " + aDom + " --config --force"
                retry_count -=1

            result_dict = {}
            result_dict["cpu_resize_success"] = ret
            result_dict["currvcpus"] = currvcpus
            result_dict["configvcpus"] = configvcpus
            result[aDom] = result_dict
            ebLogInfo(f'*** mSetVCPUandValidate : result: {result}')


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

        if not self.mIsActiveGuest(_node, aDom):
            ebLogWarn('*** Domain (%s) is not pingable for command mPatchVMCfgVcpuCountKvm' % (aDom))
            _is_pingable = False
        else:
            _is_pingable = True

        if _is_pingable:
            _cmd = "/usr/sbin/vm_maker --set --vcpu " + str(_cores) + " --domain " + aDom + " --force"
        else:
            _cmd = "/usr/sbin/vm_maker --set --vcpu " + str(_cores) + " --domain " + aDom + " --config --force"

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

        _valid_modes = ['dg_vmmaker', 'dg_oedacli', 'virsh']
        _cpu_manage_mode = self.__ecc.mCheckConfigOption('cpu_manage_mode')
        if _cpu_manage_mode is not None:
            ebLogInfo('***_cpu_manage_mode: ' + _cpu_manage_mode)

        if _cpu_manage_mode is not None and _cpu_manage_mode in _valid_modes:
            if _cpu_manage_mode == "dg_vmmaker":
                ebLogInfo('***Domain Group implementation with vm_maker ***')
                _exacpueobj = exaBoxKvmDgrpVmkr(self.__ecc)
                return _exacpueobj.mManageVMCpusBurstingKvm(aVMCmd, aVMId, aOptions)
            if _cpu_manage_mode == "dg_oedacli":
                #TODO
                ebLogError('***Domain Group implementation with oedacli is not yet supported !***')
                return

        ebLogInfo('***Domain Group implementation with virsh***')

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
            _in, _out, _err = _node.mExecuteCmd("/usr/bin/virsh nodeinfo | /bin/grep 'CPU(s)'")
            _out = _out.readlines()
            if _out and len(_out):
                try:
                    _dat = _out[0].split(':')[1].strip()
                except ValueError:
                    ebLogError('*** Failed to split the output String :%s'%(_out))
                    return ebError(0x0430)
                _reserved = HYPERVISOR_RSRVD_CORES * self.__ht_factor
                _in, _out, _err = _node.mExecuteCmd("/usr/sbin/vm_maker --list --vcpu | /bin/grep 'Host reserved' | /bin/awk '{print $5}'")
                _out = _out.readlines()
                if _out and len(_out):
                    _reserved = _out[0].strip()
                    ebLogInfo('*** Host reserved cpus from vm_maker: %s.' %_reserved)
                _maxcores = int(_dat) - int(_reserved) 
                ebLogInfo('*** MAX_VCPUS on hypervisor %s : %d' % (_hyp, _maxcores))

            #
            # Update vm vcpus for bursting mode
            #
            _cmd = "/usr/bin/virsh vcpucount " + _dom + " | /bin/grep maximum | /bin/grep config | /bin/awk '{print $3}'"
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            _out = _out.readlines()
            if _out and len(_out):
                _maxvcpus = int(_out[0].strip())
                ebLogInfo('*** MAX_VCPUS (CFG) for domain %s : %d' % (_dom, _maxvcpus))

            if _maxvcpus != _maxcores:
                #
                # Update maxvcpus
                #
                _cmd = "/usr/bin/virsh setvcpus " + _dom + " " + str(_maxcores) + " --maximum --config"
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

        _valid_modes = ['dg_vmmaker', 'dg_oedacli', 'virsh']
        _cpu_manage_mode = self.__ecc.mCheckConfigOption('cpu_manage_mode')
        if _cpu_manage_mode is not None:
            ebLogInfo('***_cpu_manage_mode: ' + _cpu_manage_mode)

        if _cpu_manage_mode is not None and _cpu_manage_mode in _valid_modes:
            if _cpu_manage_mode == "dg_vmmaker":
                ebLogInfo('***Domain Group implementation with vm_maker ***')
                _exacpueobj = exaBoxKvmDgrpVmkr(self.__ecc)
                return _exacpueobj.mClusterCPUInfoKvm(aOptions)
            if _cpu_manage_mode == "dg_oedacli":
                #TODO
                ebLogError('***Domain Group implementation with oedacli is not yet supported !***')
                return

        ebLogInfo('***Domain Group implementation with virsh***')

        for _hyp, _dom in self.__ecc.mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _result = []
            _node.mConnect(aHost=_hyp)
            _res={}
            if not self.mIsActiveGuest(_node, _dom):
                ebLogWarn('*** Domain (%s) is not pingable.' % (_dom))
                _is_pingable = False
            else:
                _is_pingable = True

            _in, _out, _err = _node.mExecuteCmd("/usr/sbin/vm_maker --list --vcpu --domain %s | /bin/awk -F: '{print $4}'" % (_dom))

            if _out:
                _out = _out.readlines()
                _res["vm_detail"] = _dom
                _res["vcpus"]= _out[0].strip()

            _, _out, _ = _node.mExecuteCmd("/usr/bin/virsh vcpuinfo " + _dom + " --pretty | /bin/grep Affinity | /bin/awk '{print$3}' | /bin/sort | /bin/uniq")
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

    def fetchDiagLogs(self, aHyp, aNode):
        if self.__ecc.mCheckConfigOption('collect_diags_for_cpuresize_failures') == 'False':
            return

        _node = aNode
        _hyp = aHyp
        ebLogInfo(f"*** Begin: Collect cpuresize diagnostics from dom0 {aHyp}")

        _cpuresize_log_path = os.path.join(get_gcontext().mGetBasePath(), "log", CPULOG_DIR, self.__ecc.mGetUUID())
        if not os.path.exists(_cpuresize_log_path):
            os.makedirs(_cpuresize_log_path)

        _sundiag_report = None

        _cmd_sundiag = f"/opt/oracle.SupportTools/sundiag.sh"
        _i, _o, _e = _node.mExecuteCmd(f"{_cmd_sundiag}", aTimeout=1800)
        _rc = _node.mGetCmdExitStatus()
        if _rc == 0:
            _out = _o.read()
            _lines = _out.split('\n')
            for _line in _lines:
                if "Done." in _line:
                    _sundiag_report = _line.strip().split()[-1]
                    ebLogInfo(f"Generated sundiag report in {_sundiag_report}")

        if _sundiag_report:
            _status = _node.mDownloadRemoteFile(_sundiag_report, _cpuresize_log_path)
            if _status is False:
                ebLogError(f"Remote Copy of sundiag report from dom0 to exacloud was not successful.")
            else:
                ebLogInfo(f"Sundiag report successfully copied from dom0 to {_cpuresize_log_path}")
            _node.mExecuteCmd(f"/usr/bin/rm -rf {_sundiag_report}")

        _ts = datetime.datetime.now().strftime("%Y_%m_%d_%H-%M")
        _varlog_path = f"/tmp/varlog-{_ts}.tar.gz"
        _cmd_varlog = f"/usr/bin/tar -czvf {_varlog_path} /var/log/cellos* /var/log/libvirt/ /var/log/messages*"
        _i, _o, _e = _node.mExecuteCmd(f"{_cmd_varlog}", aTimeout=1800)
        _rc = _node.mGetCmdExitStatus()
        if _rc == 0:
            ebLogInfo(f"Compressed the necessary logs from /var/log in {_varlog_path}")
            _status = _node.mDownloadRemoteFile(_varlog_path, _cpuresize_log_path)
            if _status is False:
                ebLogError(f"Remote Copy of {_varlog_path} from dom0 to exacloud was not successful.")
            else:
                ebLogInfo(f"Successfully copied {_varlog_path} from dom0 to {_cpuresize_log_path}")
            _node.mExecuteCmd(f"/usr/bin/rm -rf {_varlog_path}")

        ebLogInfo(f"*** End: Diagnostics location: {_cpuresize_log_path}")
 
