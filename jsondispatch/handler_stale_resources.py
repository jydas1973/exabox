#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_stale_resources.py /main/1 2024/07/16 16:00:25 aararora Exp $
#
# handler_stale_resources.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      handler_stale_resources.py
#
#
#    DESCRIPTION
#      This file is to obtain stale resources from the DOM0s if any
#      and send back to ecra. ECRA then needs to raise an alarm if any stale resources
#      are detected.
#      Assumptions:
#      The provided DOM0 for which stale resources need to be checked are:
#      KVM and ol8 DOM0s.
#      This handler expects a payload of the form:
#      {
#          "free_dom0s": ["DOM01.oracle.com", "DOM02.oracle.com"]
#      }
#      OR:
#      {
#          "hostnames":
#          [{
#               "dom0_fqdn": "DOM01.oracle.com",
#               "vm_list": [["NAT-VM1.us.oracle.com", "VM1.clientfqdn.com"], ["NAT-VM2.us.oracle.com", "VM2.clientfqdn.com"]]
#           },
#           {
#               "dom0_fqdn": "DOM02.oracle.com",
#               "vm_list": [["NAT-VM1.us.oracle.com", "VM1.clientfqdn.com"], ["NAT-VM2.us.oracle.com", "VM2.clientfqdn.com"]]
#           }]
#      }
#      OR:
#      Both the above payloads combined (No DOM0 FQDN should repeat).
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    07/09/24 - ER 36759599: Detect stale resources.
#    aararora    07/09/24 - Creation
#
import copy
import os
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check)
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace

class StaleResourcesHandler(JDHandler):
    # EXIT CODES
    SUCCESS = 0

    def __init__(self, aOptions, aRequestObj=None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.exception_bridges = get_gcontext().mCheckConfigOption("exception_bridges")
        self.rules = {
            "bridges": {
                "cmd": "brctl show",
                "custom_err_msg": "Error in getting stale bridges on DOM0s.",
                "method": self.mGetStaleBridges
            },
            "vms": {
                "cmd": "virsh list --all --name",
                "custom_err_msg": "Error in getting stale VMs using virsh.",
                "method": self.mGetAllVMs
            },
            "guestimages": {
                "cmd": "ls /EXAVMIMAGES/GuestImages",
                "custom_err_msg": "Error in getting stale VMs from /EXAVMIMAGES/GuestImages folder.",
                "method": self.mListVMFolder
            },
            "fstab": {
                "cmd": "cat /etc/fstab",
                "custom_err_msg": "Error in getting stale entries in /etc/fstab.",
                "method": self.mCheckFstab
            },
            "edv_volumes": {
                "cmd": "ls /dev/exc",
                "custom_err_msg": "Error in getting stale edv volumes.",
                "method": self.mListExcFolder
            },
            "docker": {
                "cmd": "docker ps",
                "custom_err_msg": "Error in getting stale docker containers.",
                "method": self.mCheckDockerContainers
            },
            "nat_rules": {
                "cmd": "nft list chain ip nat PREROUTING",
                "custom_err_msg": "Error in getting stale PREROUTING nat rules.",
                "type": "nft_rules",
                "method": self.mCheckNatRules
            },
            "bridge_filter_rules": {
                "cmd": "nft list table bridge filter",
                "custom_err_msg": "Error in getting stale bridge filter rules",
                "type": "nft_rules",
                "method": self.mCheckBridgeFilterRules
            },
        }
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/stale_resources.json"))

    def mRunCmd(self, aCmd, aDOM0):
        """
        Runs a command aCmd on dom0 aDOM0 and gets you either an error message
        and return code or the stdout object for you to either read or readlines.
        """
        with connect_to_host(aDOM0, get_gcontext()) as _node:
            _cmd_list = aCmd.split()
            # If the command passed is already having absolute path, then do
            # not get absolute path again
            if not _cmd_list[0].startswith('/'):
                try:
                    _bin_cmd = node_cmd_abs_path_check(_node, _cmd_list[0], sbin=True)
                except Exception as ex:
                    # Return the exception which will be added to the dictionary for the given key
                    return 1, str(ex)
                _cmd_list[0] = _bin_cmd
            _cmd =  " ".join(_cmd_list)
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            _rc = int(_node.mGetCmdExitStatus())
            if _rc !=0:
                _error = _err.read()
                _msg = f"*** Error while running {_cmd} on {aDOM0}. Error is {_error}."
                ebLogError(_msg)
                return _rc, _msg
            else:
                return _rc, _out

    def mGetStaleBridges(self, aDOM0, aOutput, aVMList=None):
        """
        Method to implement rule for getting stale bridges. If a vm list is passed,
        it will look for bridges not belonging to those VMs in the list.
        """
        _bridges = []
        _expected_bridges = []
        _output = []
        if aOutput:
            _output = aOutput.readlines()
        ebLogTrace(f"*** Output on {aDOM0} is {_output}")
        if aVMList:
            # From the VM list in the payload (if passed), get bridges associated with each VM
            # on the DOM0 and add it to an expected list of bridges
            for _vm in aVMList:
                _cmd = f"virsh domiflist {_vm[1]} | /bin/tail -n+3 | /bin/awk '{{print $3}}'"
                _rc, _out = self.mRunCmd(_cmd, aDOM0)
                if _rc != 0:
                    # Return the error message and store it in the response dict
                    return _out
                for _bridge in _out.readlines():
                    _bridge = _bridge.strip()
                    if _bridge.startswith(("vmbondeth", "vmeth")):
                        _expected_bridges.append(_bridge)
        for _line in _output:
            _line = _line.strip().split()
            # From the brctl show output, add the bridges to a list excluding exception bridges,
            # expected bridges, vnets, vifs and bridge column name
            if _line and _line[0].strip() not in self.exception_bridges\
                and not _line[0].strip().startswith(("vnet", "bridge", "vif"))\
                and _line[0].strip() not in _expected_bridges:
                _bridges.append(_line[0].strip())
        ebLogTrace(f"Obtained stale bridges are {_bridges}")
        return _bridges

    def mGetAllVMs(self, aDOM0, aOutput, aVMList=None):
        """
        Parses the output of virsh list --all --name and finds the stale VMs.
        If a VM list is passed, those VMs will not be added to the stale VM list.
        """
        _vms = []
        _output = []
        _stale_vms = []
        if aOutput:
            _output = aOutput.readlines()
        ebLogTrace(f"*** Output on {aDOM0} is {_output}")
        for _line in _output:
            _line = _line.strip()
            if _line:
                _vms.append(_line)
        if aVMList:
            # For a given VM list in payload, remove the VMs from the obtained vm list
            # from the DOM0. Here, we are taking a copy of the original list to avoid 
            # RuntimeError: list changed size during iteration
            _stale_vms = copy.copy(_vms)
            for _vm in aVMList:
                if _vm[1] in _vms:
                    _stale_vms.remove(_vm[1])
            _vms = _stale_vms
        ebLogTrace(f"Obtained stale vms are {_vms}")
        return _vms

    def mListVMFolder(self, aDOM0, aOutput, aVMList=None):
        """
        Parses the output of ls /EXAVMIMAGES/GuestImages and finds the stale VMs.
        If a VM list is passed, those VMs will not be added to the stale VM list.
        """
        _vms = []
        _output = []
        _stale_vms = []
        if aOutput:
            _output = aOutput.read()
            ebLogTrace(f"*** Output on {aDOM0} is {_output}")
            if _output:
                _output = _output.strip().split()
        for _vm in _output:
            _vm = _vm.strip()
            if _vm:
                _vms.append(_vm)
        if aVMList:
            # For a given VM list in payload, remove the VMs from the obtained vm list
            # from the DOM0. Here, we are taking a copy of the original list to avoid 
            # RuntimeError: list changed size during iteration
            _stale_vms = copy.copy(_vms)
            for _vm in aVMList:
                if _vm[1] in _vms:
                    _stale_vms.remove(_vm[1])
            _vms = _stale_vms
        ebLogTrace(f"Obtained stale vms are {_vms}")
        return _vms

    def mCheckFstab(self, aDOM0, aOutput, aVMList=None):
        """
        Check /etc/fstab for stale entries of VMs. If a VM list is passed,
        this method will compare the vm entry in /etc/fstab with the VMs in the
        VM list and will not add those vm entries belonging to the passed VMs
        to stale entries.
        """
        _vm_entries = []
        _stale_vm_entries = []
        _output = []
        if aOutput:
            _output = aOutput.readlines()
        ebLogTrace(f"*** Output on {aDOM0} is {_output}")
        for _line in _output:
            _line = _line.strip()
            if "/EXAVMIMAGES/GuestImages/" in _line:
                _vm_entries.append(_line)
        if aVMList:
            # For each vm entry obtained from /etc/fstab from the DOM0, check if the vm entry exists for the VM
            # client fqdn. If the vm entry exists for the VM, remove that from the copy of the vm entries.
            # Final copy of vm entries will contain the stale vm entries in /etc/fstab
            _stale_vm_entries = copy.copy(_vm_entries)
            for _vm_entry in _vm_entries:
                for (_nat_vm, _vm) in aVMList:
                    if _vm in _vm_entry:
                        _stale_vm_entries.remove(_vm_entry)
                        break
            _vm_entries = _stale_vm_entries
        ebLogTrace(f"Obtained stale vm entries are {_vm_entries}")
        return _vm_entries

    def mListExcFolder(self, aDOM0, aOutput, aVMList=None):
        """
        This will list /dev/exc directory to check for stale edv volumes.
        If a VM list is passed, this will check for volinfo with edvutil command
        to check if the volume is still available. edvutil will return non zero
        return code if an invalid volume exists. If an invalid return code is
        obtained for a volume, that will be added to stale edv volumes list.
        """
        _edv_volumes = []
        _stale_volumes = []
        _output = []
        if aOutput:
            _output = aOutput.read()
            ebLogTrace(f"*** Output on {aDOM0} is {_output}")
            if _output:
                _output = _output.strip().split()
        for _volume in _output:
            _volume = _volume.strip()
            if _volume.startswith(("gcv_", "gi_", "u01_", "u02_", "system_")):
                _edv_volumes.append(os.path.join("/dev/exc", _volume))
        if aVMList:
            try:
                with connect_to_host(aDOM0, get_gcontext()) as _node:
                    _bin_edvutil = node_cmd_abs_path_check(_node, "edvutil", sbin=True)
            except Exception as ex:
                # Return the exception which will be added to the dictionary for edv_volumes check
                return str(ex)
            for _vol in _edv_volumes:
                _cmd = f"{_bin_edvutil} volinfo {_vol} -l"
                _rc, _out = self.mRunCmd(_cmd, aDOM0)
                if _rc != 0:
                    _stale_volumes.append(os.path.join("/dev/exc", _vol))
            _edv_volumes = _stale_volumes
        ebLogTrace(f"Obtained stale edv volumes are {_edv_volumes}")
        return _edv_volumes

    def mCheckDockerContainers(self, aDOM0, aOutput, aVMList=None):
        """
        This method checks for stale docker containers on the given DOM0.
        If a VM list is passed, those VMs will be checked for having the
        containers belonging to them. If a container does not belong to any
        VM, that will be added to stale containers list.
        """
        _docker_containers = []
        _stale_docker_containers = []
        _output = []
        if aOutput:
            _output = aOutput.readlines()
        ebLogTrace(f"*** Output on {aDOM0} is {_output}")
        for _line in _output:
            _line = _line.strip()
            if not _line.startswith(("Emulate", "CONTAINER")):
                _line = _line.split()
                if _line:
                    # The container name will be the last column
                    _docker_containers.append(_line[-1].strip())
        if aVMList:
            # For each docker container obtained from the DOM0, check if the container exists for the VM
            # shortname. If the container exists for the VM, remove that from the copy of the containers.
            # Final copy of containers will contain the stale containers list.
            _stale_docker_containers = copy.copy(_docker_containers)
            for _docker_container in _docker_containers:
                _found = False
                for (_nat_vm, _vm) in aVMList:
                    _shortname_nat = _nat_vm.split('.')[0]
                    _shortname_client = _vm.split('.')[0]
                    if _shortname_nat in _docker_container or _shortname_client in _docker_container:
                        _stale_docker_containers.remove(_docker_container)
                        break
            _docker_containers = _stale_docker_containers
        ebLogTrace(f"Obtained stale docker containers are {_docker_containers}")
        return _docker_containers

    def mCheckNatRules(self, aDOM0, aOutput, aVMList=None):
        """
        This will check for any stale nat rules on the DOM0. If a VM list is passed,
        this method will check for the 'vmeth' bridge associated with those VMs
        and will exclude those bridges from the stale nat rule list.
        """
        _nat_rules = []
        _stale_nat_rules = []
        _expected_bridges = []
        _vm_ip_addresses = []
        _output = []
        if aOutput:
            _output = aOutput.readlines()
        ebLogTrace(f"*** Output on {aDOM0} is {_output}")
        for _line in _output:
            _line = _line.strip()
            # If the line starts with iif or oif - those are the rules added for vmeth interfaces
            if _line.startswith(("iif", "oif")):
                _nat_rules.append(_line)
        if aVMList:
            # From the VM list in the payload (if passed), get vmeth bridges associated with each VM
            # on the DOM0 and add it to an expected list of bridges
            for _vm in aVMList:
                _cmd = f"virsh domiflist {_vm[1]} | /bin/tail -n+3 | /bin/awk '{{print $3}}'"
                _rc, _out = self.mRunCmd(_cmd, aDOM0)
                if _rc != 0:
                    # Return the error message and store it in the returned dict
                    return _out
                for _bridge in _out.readlines():
                    _bridge = _bridge.strip()
                    if _bridge.startswith("vmeth"):
                        _expected_bridges.append(_bridge)
            for _expected_bridge in _expected_bridges:
                _cmd = f"ip addr show {_expected_bridge} | grep -w inet | awk '{{print $2}}'"
                _rc, _out = self.mRunCmd(_cmd, aDOM0)
                if _rc != 0:
                    # Return the error message and store it in the returned dict
                    return _out
                _bridge_ip_address = _out.read().strip().split('/')[0]
                _bridge_ip_address_segment_list = _bridge_ip_address.split('.')
                # The IP address for the eth0 interface of the VM is 1 greater than the
                # last segment of vmeth bridge on DOM0
                _last_segment_ip_address = int(_bridge_ip_address_segment_list[3])+1
                _bridge_ip_address_segment_list[3] = str(_last_segment_ip_address)
                _vm_ip_address = ".".join(_bridge_ip_address_segment_list)
                _vm_ip_addresses.append(_vm_ip_address)
            _stale_nat_rules = copy.copy(_nat_rules)
            ebLogInfo(f"VM IP addresses obtained are {_vm_ip_addresses}.")
            # For each nat rule obtained from the DOM0, check if the nat rule exists for an expected bridge
            # If the nat rule exists for the expected bridge, remove that from the copy of the nat rules.
            # Final copy of nat rules will contain the stale nat rules.
            for _nat_rule in _nat_rules:
                for _ip_address in _vm_ip_addresses:
                    if _ip_address in _nat_rule:
                        _stale_nat_rules.remove(_nat_rule)
                        break
            _nat_rules = _stale_nat_rules
        ebLogTrace(f"Obtained stale nat rules are {_nat_rules}")
        return _nat_rules

    def mCheckBridgeFilterRules(self, aDOM0, aOutput, aVMList=None):
        """
        This will check for any stale bridge filter rules on the DOM0. If a VM list is passed,
        this method will check for the vm shortname to be present in the filter list. If
        a vm shortname matches with any of the VM in the passed list, that filter rule
        will be excluded from the stale bridge filter rule list.
        """
        _bridge_filter_rules = []
        _stale_bridge_filter_rules = []
        _output = []
        if aOutput:
            _output = aOutput.readlines()
        ebLogTrace(f"*** Output on {aDOM0} is {_output}")
        for _line in _output:
            _line = _line.strip()
            # If the line contains a jump rule for a vm - bridge filter rule exists for that vm
            if "jump vm_" in _line:
                _line_values = _line.split()
                for _value in _line_values:
                    if "vm_" in _value.strip():
                        # _bridge_filter_rules will have chain names. Example: ["vm_sjc100705exddu0601"]
                        _bridge_filter_rules.append(_value.strip())
        if aVMList:
            # For each bridge filter rule obtained from the DOM0, check if the filter rule exists for the
            # VM in payload. If the filter rule exists for the VM, remove that from the copy of the filter rules.
            # Final copy of filter rules will contain the stale filter rules.
            _stale_bridge_filter_rules = copy.copy(_bridge_filter_rules)
            for _bridge_filter_rule in _bridge_filter_rules:
                for (_nat_vm, _vm) in aVMList:
                    _shortname = _nat_vm.split('.')[0]
                    if _shortname in _bridge_filter_rule:
                        _stale_bridge_filter_rules.remove(_bridge_filter_rule)
                        break
            _bridge_filter_rules = _stale_bridge_filter_rules
        ebLogTrace(f"Obtained stale chains for bridge filter rules are {_bridge_filter_rules}")
        return _bridge_filter_rules

    def mSetErrorMsg(self, aCmd, aDOM0, aErr, aResponseJson, aKey, aCustomMsg=""):
        """
        This method is to set error message in response json.
        """
        _error = aErr.read()
        _msg = f"*** Error while running {aCmd} on {aDOM0}. Error is {_error}. {aCustomMsg}"
        ebLogError(_msg)
        aResponseJson[aKey] = _msg

    def mExecuteRule(self, aDOM0, aCmd, aKey, aMethod, aCustomMsg, aResponseJson, aVMList=None):
        """
        This method executes the command passed to this and either sets an error message
        or will execute the specific method associated with a rule. If a not empty json
        is returned, that will be set in the response json.
        """
        with connect_to_host(aDOM0, get_gcontext()) as _node:
            _cmd_list = aCmd.split()
            if aKey == "edv_volumes":
                # If /dev/exc does not exist, we don't need to check volumes under this directory
                if not _node.mFileExists(_cmd_list[1]):
                    return
            try:
                _bin_cmd = node_cmd_abs_path_check(_node, _cmd_list[0], sbin=True)
            except Exception as ex:
                # Return the exception which will be added to the dictionary for the aKey passed
                aResponseJson[aKey] = str(ex)
                return
            _cmd_list[0] = _bin_cmd
            _cmd =  " ".join(_cmd_list)
            ebLogInfo(f"*** Executing the command - {_cmd}")
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            _rc = int(_node.mGetCmdExitStatus())
            if _rc !=0:
                self.mSetErrorMsg(_cmd, aDOM0, _err, aResponseJson, aKey, aCustomMsg=aCustomMsg)
            else:
                _response = aMethod(aDOM0, _out, aVMList)
                if _response:
                    # Add the key and response to the final dictionary only if response is not empty
                    aResponseJson[aKey] = _response

    def mCheckDOM0(self, aDOM0, aVMList=None):
        """
        Check the DOM0 for different rules and return the json
        containing map of bridges, VMs, etc found on it.
        Returned json will be like:
        {
            "bridges": ["bridge1", "bridge2"],
            "vms": ["vm1", "vm2"],
            ..
        }
        """
        _response_json = {}
        for _rule, _value in self.rules.items():
            self.mExecuteRule(aDOM0, _value["cmd"], _rule, _value["method"], _value["custom_err_msg"], _response_json, aVMList)
        return _response_json

    def mCombineResults(self, aResponseDOM0s, aResponse):
        """
        aResponseDOM0s will be like below (Note that the free DOM0s
        will not be same as allocated DOM0s). Also, there can be an error string assigned to a key
        if there was an error during any of the rule execution:
        {
            "DOM01.us.oracle.com": {
                "bridges": ["bridge1", "bridge2"],
                "vms": ["vm1", "vm2"],
                "guestimages": "Unable to list the VMs.",
                ..
            },
            ..
        }
        aResponse should be like below:
        {
            "bridges": {
                "DOM01.oracle.com": ["bridge1, bridge2"],
                ..
            },
            "vms": {
                "DOM01.oracle.com": ["vm1", "vm2"],
                ..
            },
            "guestimages": {
                "DOM01.oracle.com": "Unable to list the VMs.",
                ..
            },
            ..
        }
        """
        for _dom0, _values in aResponseDOM0s.items():
            for _key in self.rules:
                if _key in _values:
                    _response_dict = {_dom0: _values[_key]}
                    if _key not in aResponse:
                        aResponse[_key] = _response_dict
                    else:
                        aResponse[_key].update(_response_dict)

    def mExecute(self) -> tuple:
        """
        Driver func for checking stale resources on the DOM0s, and will 
        NOT require an XML as input (only a payload in JSON format 
        with a predefined JSON Schema)

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """
        _rc = StaleResourcesHandler.SUCCESS
        _response = {}
        _response_free_dom0s = {}
        _response_allocated_dom0s = {}
        _free_dom0s = self.mGetOptions().jsonconf.get("free_dom0s")
        if _free_dom0s:
            ebLogInfo(f"Started checking stale resources for free DOM0s: '{_free_dom0s}'")
            for _dom0 in _free_dom0s:
                _response_free_dom0s[_dom0] = self.mCheckDOM0(_dom0)
            ebLogInfo(f"Stale resources check completed for free DOM0s")
        _hostnames = self.mGetOptions().jsonconf.get("hostnames")
        if _hostnames:
            ebLogInfo(f"Started checking stale resources for allocated hosts: '{_hostnames}'")
            for _hostname in _hostnames:
                _dom0 = _hostname["dom0_fqdn"]
                _vm_list = _hostname["vm_list"]
                _response_allocated_dom0s[_dom0] = self.mCheckDOM0(_dom0, aVMList=_vm_list)
            ebLogInfo(f"Stale resources check completed for allocated hosts")
        if _response_free_dom0s:
            self.mCombineResults(_response_free_dom0s, _response)
            ebLogInfo(f"Combined result for free DOM0s.")
        if _response_allocated_dom0s:
            self.mCombineResults(_response_allocated_dom0s, _response)
            ebLogInfo(f"Combined result for allocated DOM0s.")
        return (_rc, _response)