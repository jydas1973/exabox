#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_hostaccesscontrol.py /main/1 2024/07/01 09:17:04 aypaul Exp $
#
# handler_hostaccesscontrol.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      handler_hostaccesscontrol.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/19/24 - Creation
#
import os
import time
import ipaddress
import re
from typing import Tuple
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.utils.node import connect_to_host

def validateIPV4CIDR(inputString):
    try:
        ipaddress.IPv4Network(inputString)
        return True
    except:
        return False


class ECHostAccessControlHandler(JDHandler):

    # Class attributes
    SUCCESS = 0
    FAILURE = 1

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/hostaccesscontrol.json"))
        _input_payload = self.mGetPayload()
        self.__input_hostnames = _input_payload.get("hostnames")
        self.__input_cidrs     = _input_payload.get("cidrs")
        self.__input_operation = _input_payload.get("operation")
        self.__input_hosttype  = _input_payload.get("hosttype")

    def mExecute(self):

        _rc = self.mValidatePayload()
        if _rc == ECHostAccessControlHandler.FAILURE:
            ebLogError("Host access control payload verification failed.")
            return ECHostAccessControlHandler.FAILURE, {}

        _response_dict = self.mUpdateHostAccessControl()
        
        return ECHostAccessControlHandler.SUCCESS, _response_dict

    def mValidatePayload(self):
        
        ebLogTrace("Validating host access control operations payload for jsondipatch endpoint.")
        _valid_operation_types = ['add', 'delete']
        ebLogTrace(f"Endpoint: jsondispatch, command: hac,  payload values: (hostnames: {self.__input_hostnames}) ; (cidr: {self.__input_cidrs}) ; (operation: {self.__input_operation})")
        
        if self.__input_operation not in _valid_operation_types:
            ebLogError(f"Operation type {self.__input_operation} is not supported for host access control.")
            return ECHostAccessControlHandler.FAILURE

        if self.__input_hosttype not in ["dom0", "cell"]:
            ebLogError(f"Input host type {self.__input_hosttype} is not a supported host type for host access control.")
            return ECHostAccessControlHandler.FAILURE
        for _input_cidr in self.__input_cidrs:

            if not validateIPV4CIDR(_input_cidr):
                ebLogError(f"Input CIDR {_input_cidr} is not a valid CIDR block.")
                return ECHostAccessControlHandler.FAILURE

        ebLogInfo("Payload validation successful.")
        return ECHostAccessControlHandler.SUCCESS

    def mUpdateHostAccessControl(self):

        ebLogTrace("Updating host access control for input hostnames.")
        _host_access_control_update_results = dict()
        for _hostname in self.__input_hostnames:
            _result = dict()
            for _input_cidr in self.__input_cidrs:
                _cidr_result = dict()
                if self.__input_operation == "add":
                    _cidr_result = self.mAddHostAccessControlForNode(_hostname, _input_cidr)
                elif self.__input_operation == "delete":
                    _cidr_result = self.mDeleteHostAccessControlForNode(_hostname, _input_cidr)
                _result[_input_cidr] = _cidr_result
            _host_access_control_update_results[_hostname] = _result

        return _host_access_control_update_results

    def mAddHostAccessControlForNode(self, aHostname, aInputCidr):

        _hostname = aHostname
        _input_cidr = aInputCidr
        ebLogTrace(f"Updating host access control for dom0: {_hostname}")
        _combined_result = dict()
        with connect_to_host(_hostname, get_gcontext()) as _node:
            _timestamp = str(time.time()).replace(".", "")
            _export_file = f"/tmp/node_hacaccess_export{_timestamp}.txt"
            _cmd_export = f"/opt/oracle.cellos/host_access_control access-export --file='{_export_file}'"
            ebLogInfo(f"Running on {_node.mGetHostname()} the cmd {_cmd_export}")
            _node.mExecuteCmdLog(_cmd_export)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _error_msg = _combined_result["root"] = f"Host access control update failed for {_node.mGetHostname()}. Reason: Unable to fetch existing hac rules."
                _combined_result["root"] = _error_msg
                return _combined_result

            _users = ["root", "secscan"]
            if self.__input_hosttype == "cell":
                _users.append("cellmonitor")

            for _user in _users:
                _cmd_fetch = f"/bin/cat {_export_file} | /bin/grep {_user}"
                _node.mExecuteCmdLog(_cmd_fetch)

                _current_list = [_input_cidr]
                if _node.mGetCmdExitStatus() != 0:
                    ebLogTrace(f"HAC rules doesn't exist for user {_user} in {_node.mGetHostname()}")
                else:
                    _i, _o, _e = _node.mExecuteCmd(_cmd_fetch)
                    _current_rules_str = _o.readline()
                    ebLogTrace(f"Existing hac rule for {_user} in {_node.mGetHostname()}: {_current_rules_str}")
                    _current_rules_composite = _current_rules_str.split(":")
                    if len(_current_rules_composite) < 3:
                        _error_msg = f"Host access control update for user {_user} failed for {_node.mGetHostname()}. Reason: Invalid hac setting: {_current_rules_str}"
                        _combined_result[_user] = _error_msg
                        continue

                    _current_rules_unedited = _current_rules_composite[2]
                    _current_rules = _current_rules_unedited.strip()
                    _current_controls = _current_rules.split(" ")
                    for _current_control in _current_controls:
                        _current_control = _current_control.strip()
                        _has_matched = re.search('[a-zA-Z]', _current_control)
                        if _has_matched is None and _current_control != _input_cidr:
                            _current_list.append(_current_control)

                _ip_access_list = ",".join(_current_list)
                _cmd_update_hac = f"/opt/oracle.cellos/host_access_control access --add -u {_user} -o {_ip_access_list}"

                _node.mExecuteCmdLog(_cmd_update_hac)
                if _node.mGetCmdExitStatus() != 0:
                    _error_msg = f"Failed to add hac rules for {_user} in {_node.mGetHostname()}"
                    ebLogError(_error_msg)
                    _combined_result[_user] = _error_msg
                else:
                    _success_msg = f"Successfully added hac rules for {_user} in {_node.mGetHostname()}"
                    ebLogInfo(_success_msg)
                    _combined_result[_user] = _success_msg

        return _combined_result


    def mDeleteHostAccessControlForNode(self, aHostname, aInputCidr):

        _hostname = aHostname
        _input_cidr = aInputCidr
        ebLogTrace(f"Updating host access control for dom0: {_hostname}")
        _combined_result = dict()
        with connect_to_host(_hostname, get_gcontext()) as _node:
            _timestamp = str(time.time()).replace(".", "")
            _export_file = f"/tmp/node_hacaccess_export{_timestamp}.txt"
            _cmd_export = f"/opt/oracle.cellos/host_access_control access-export --file='{_export_file}'"
            ebLogInfo(f"Running on {_node.mGetHostname()} the cmd {_cmd_export}")
            _node.mExecuteCmdLog(_cmd_export)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _error_msg = f"Host access control update failed for {_node.mGetHostname()}. Reason: Unable to fetch existing hac rules."
                _combined_result["root"] = _error_msg
                return _combined_result

            _users = ["root", "secscan"]
            if self.__input_hosttype == "cell":
                _users.append("cellmonitor")

            for _user in _users:
                _cmd_fetch = f"/bin/cat {_export_file} | /bin/grep {_user} | /bin/grep {_input_cidr}"
                _node.mExecuteCmdLog(_cmd_fetch)

                _current_list = list()
                if _node.mGetCmdExitStatus() != 0:
                    _success_msg = f"HAC rules doesn't exist or current subnet is not configured for user {_user} in {_node.mGetHostname()}"
                    ebLogInfo(_success_msg)
                    _combined_result[_user] = _success_msg
                    continue
                else:
                    _i, _o, _e = _node.mExecuteCmd(_cmd_fetch)
                    _current_rules_str = _o.readline()
                    ebLogTrace(f"Existing hac rule for {_user} in {_node.mGetHostname()}: {_current_rules_str}")
                    _current_rules_composite = _current_rules_str.split(":")
                    if len(_current_rules_composite) < 3:
                        _error_msg = f"Host access control update for user {_user} failed for {_node.mGetHostname()}. Reason: Invalid hac setting: {_current_rules_str}"
                        _combined_result[_user] = _error_msg
                        continue

                    _current_rules_unedited = _current_rules_composite[2]
                    _current_rules = _current_rules_unedited.strip()
                    _current_controls = _current_rules.split(" ")
                    for _current_control in _current_controls:
                        _current_control = _current_control.strip()
                        _has_matched = re.search('[a-zA-Z]', _current_control)
                        if _has_matched is None and _current_control != _input_cidr:
                            _current_list.append(_current_control)

                _ip_access_list = ",".join(_current_list)
                _cmd_update_hac = f"/opt/oracle.cellos/host_access_control access --add -u {_user} -o {_ip_access_list}"

                _node.mExecuteCmdLog(_cmd_update_hac)
                if _node.mGetCmdExitStatus() != 0:
                    _error_msg = f"Failed to delete hac rules for {_user} in {_node.mGetHostname()}"
                    ebLogError(_error_msg)
                    _combined_result[_user] = _error_msg
                else:
                    _success_msg = f"Successfully deleted hac rules for {_user} in {_node.mGetHostname()}"
                    ebLogInfo(_success_msg)
                    _combined_result[_user] = _success_msg

        return _combined_result