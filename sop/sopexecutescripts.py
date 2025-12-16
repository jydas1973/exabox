#!/bin/python
#
# $Header: ecs/exacloud/exabox/sop/sopexecutescripts.py /main/16 2025/06/19 09:03:46 aypaul Exp $
#
# sopexecutescripts.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      sopexecutescripts.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/17/25 - Bug#37990012 Improve error logging for non
#                           reachable iloms.
#    ririgoye    06/02/25 - Bug 38014410 - SOP: REMOTE EXECUTION FAILED DUE TO 
#                           EXACLOUDRUNTIMEERROR
#    ririgoye    04/28/25 - Bug 37588295 - EXACLOUD SOP LOCAL REMOTE EXECUTION
#    aypaul      03/17/25 - ER37624381 Support parameterisation for ilom
#                           commands.
#    aypaul      11/14/24 - Enh#37160657 local execution support for SOP
#                           framework.
#    aypaul      04/01/24 - ER#36391449 Save sop scripts in tmp directory for
#                           ibswitch.
#    aypaul      12/04/23 - Bug#36068400 allow false match to continue without
#                           raising exception.
#    aypaul      11/17/23 - Enh#35783067 multi host login support for
#                           interactive ilom ssh connection.
#    aypaul      07/13/23 - Bug#35598731 Harden ilom password fetch logic for
#                           QA R1 hosts.
#    aypaul      06/14/23 - Bug#35493129 Graceful handling of mandatory
#                           parameters.
#    aypaul      06/13/23 - Enh#35470717 Ilom connection support via
#                           username/password authentication.
#    aypaul      06/09/23 - Bug#35480382 script params needs to be updated with
#                           payload only once per script.
#    aypaul      06/07/23 - Issue#35470499 create complete oadt directory
#                           structure.
#    aypaul      03/07/23 - ENH#35128164 SOP support for ILOM CLI commands.
#    aypaul      02/20/23 - Enh#35091298 Connection verification for SOP script
#                           execution.
#    aypaul      01/12/23 - Creation
#

import os
import base64
import json
import uuid
import copy
import re
from exabox.utils.node import connect_to_host, node_exec_cmd, node_cmd_abs_path_check
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.sop.sopscripts import SOPScriptsRepo, SCRIPT_PATH, SCRIPT_RETURN_JSON_SUPPORT, SCRIPT_EXEC, SCRIPT_PARALLEL_EXEC, SCRIPT_VERSION, SCRIPT_COMMENTS
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogTrace, ebLogWarn
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, TimeoutBehavior, ExitCodeBehavior
from exabox.network.osds.sshgen import interactiveSSHconnection
from exabox.ovm.clumisc import ebMiscFx

OADT_BASE_DIR = "/opt/exacloud/oadt"
OADT_REQUESTS_DIR = "/opt/exacloud/oadt/requests"
COMPUTE_ILOM = "computeilom"
STORAGE_ILOM = "cellilom"
SUCCESSEXITCODE = 0


def fetch_ilom_password(aIlomType: str) -> str:

    _ilom_type = aIlomType
    _ilom_password = None
    _oci_secrets_helper = "/u01/oci/secrets.py"

    if _ilom_type is None or _ilom_type not in [COMPUTE_ILOM, STORAGE_ILOM]:
        ebLogError(f"Invalid or empty ilom type specified in payload: {_ilom_type}")
        return _ilom_password
    if not os.path.exists(_oci_secrets_helper):
        ebLogError(f"OCI secrets helper script not available at: {_oci_secrets_helper}")
        ebLogInfo("Attempting to fetch password from exabox.conf.")
    else:
        try:
            _ilom_secret_name = f"exadata-{_ilom_type}-root"
            _cmd = f"{_oci_secrets_helper} --action get --secret_name={_ilom_secret_name}"
            ebLogInfo(f"Fetching ilom info using command: {_cmd}")
            _rc, _, _o, _e = ebMiscFx.mExecuteLocal(_cmd)
            if _rc == 0:
                ebLogTrace("Successfully obtained password from OCI secrets.")
                _ilom_password = _o.strip()
        except Exception as e:
            ebLogError(f"Exception while fetching password from secrets vault: {e}")
            _ilom_password = None

    if not _ilom_password and _ilom_type == COMPUTE_ILOM and get_gcontext().mCheckConfigOption("ilom_compute_pwd_b64"):
        ebLogTrace("Updating compute-ilom password from exabox.conf.")
        _ilom_password = str(get_gcontext().mCheckConfigOption("ilom_compute_pwd_b64"))
        _ilom_password = base64.b64decode(_ilom_password).decode('utf8')
    if not _ilom_password and _ilom_type == STORAGE_ILOM and get_gcontext().mCheckConfigOption("ilom_cell_pwd_b64"):
        ebLogTrace("Updating cell-ilom password from exabox.conf.")
        _ilom_password = str(get_gcontext().mCheckConfigOption("ilom_cell_pwd_b64"))
        _ilom_password = base64.b64decode(_ilom_password).decode('utf8')

    if _ilom_password is not None and _ilom_password == "":
        _ilom_password = None

    return _ilom_password


class SOPExecution():

    def __init__(self, aUUID: str, aNodesList: list, aScriptName: str, aScriptParams: str, aScriptPayload: dict, aScriptVersion: str, aNodeType: str) -> None:
        self.__uuid = aUUID
        self.__nodes_list = aNodesList
        self.__script_name = aScriptName
        self.__script_params = aScriptParams
        self.__script_payload = aScriptPayload
        _scripts_repo = SOPScriptsRepo()
        self.__scripts_metadata = _scripts_repo.mGetScriptsMetadata()
        #{"node1" : {"return_code": 0, "stdout_msgs": None, "stderr_msgs": None, "return_json": {}}}
        self.__output = dict()
        self.__script_version_required = aScriptVersion
        self.__targetnode_type = aNodeType
        if self.__targetnode_type is not None and "switch" in self.__targetnode_type:
            self.__requests_dir = os.path.join("/tmp/oadt/requests", self.__uuid)
        else:
            self.__requests_dir = os.path.join(OADT_REQUESTS_DIR, self.__uuid)
        self.__local_requests_dir = os.path.join(get_gcontext().mGetBasePath(), "oadt/requests", self.__uuid)

    def mExecuteOperation(self) -> None:

        if self.__targetnode_type is not None and "ilom" in self.__targetnode_type:
            self.mProcessRequestILOM()
        else:
            self.mPrecheckProcessing()
            self.mProcessRequest()

        self.mPostProcessing()

    def mGetResult(self) -> dict:
        return self.__output

    """
    This function performs cleanup or post execution operations for a SOP execution at a node level.
    :returns None:
    """
    def mPostProcessing(self):
        if self.__targetnode_type is not None and "switch" in self.__targetnode_type:
            for _node in self.__nodes_list:
                with connect_to_host(_node, get_gcontext()) as _connected_node:
                    _test_exepath = node_cmd_abs_path_check(_connected_node, "test")
                    if _test_exepath is None:
                        ebLogWarn(f"test executable is not available for node: {_node}. Unable to delete {self.__requests_dir}")
                        continue
                    _cmd_to_execute = f"{_test_exepath} -d {self.__requests_dir}"
                    ebLogTrace(f"Executing command: {_cmd_to_execute} on host: {_node}")
                    _cmd_structure = node_exec_cmd(_connected_node, _cmd_to_execute)
                    if _cmd_structure.exit_code == SUCCESSEXITCODE:
                        _cmd_to_execute = f"/bin/rm -rf {self.__requests_dir}"
                        ebLogTrace(f"Executing command: {_cmd_to_execute} on host: {_node}")
                        _cmd_structure = node_exec_cmd(_connected_node, _cmd_to_execute)
                        if _cmd_structure.exit_code == SUCCESSEXITCODE:
                            ebLogInfo(f"Successfully deleted {self.__requests_dir} on {_node}")
                        else:
                            ebLogError(f"Failed to delete {self.__requests_dir} on {_node}")

    def mPrecheckProcessing(self) -> None:

        ebLogInfo("Prechecks for script execution.")
        if self.__nodes_list is None or len(self.__nodes_list) == 0:
            raise ExacloudRuntimeError(0x815, 0xA, "Node list cannot be empty.")
        if self.__script_name is None or self.__script_name == "":
            raise ExacloudRuntimeError(0x815, 0xA, "Script name cannot be empty.")
        if self.__scripts_metadata.get(self.__script_name, None) is None:
            raise ExacloudRuntimeError(0x815, 0xA, f"Script: {self.__script_name} is not present in the script repository.")
        if self.__script_version_required is None:
            ebLogWarn("Script version not mentioned in payload. Will attempt to execute the script present in the directory.")
        elif self.__script_version_required != self.__scripts_metadata.get(self.__script_name).get(SCRIPT_VERSION):
            raise ExacloudRuntimeError(0x815, 0xA, f"Script: {self.__script_name} Version: {self.__script_version_required} is not present in the script repository.")

        _dest_json_file = None
        for _node in self.__nodes_list:
            _request_directory = self.__requests_dir
            isLocal = False
            if _node == "localhost":
                isLocal = True
                _request_directory = self.__local_requests_dir
            _eb_node = exaBoxNode(get_gcontext(), aLocal=isLocal)
            if not _eb_node.mIsConnectable(_node):
                ebLogError(f"Node {_node} is not connectable, skipping SOP script {self.__script_name} execution.")
                _cmd_op = {"return_code": 500, "stdout_msgs": None, "stderr_msgs": f"Host {_node} unreachable", "return_json": {}}
                self.__output[_node] = _cmd_op
                continue
            try:
                #Check whether payload is required
                if _dest_json_file is None and self.__script_payload is not None and len(self.__script_payload.keys()) > 0:
                    _local_json_file = f"/tmp/sop_{self.__uuid}_payload.json"
                    with open(_local_json_file, 'w') as _fd:
                        json.dump(self.__script_payload, _fd)
                    _dest_json_file = os.path.join(_request_directory, f"sop_{self.__uuid}_payload.json")
                    self.__script_params = f"{self.__script_params} {_dest_json_file}"
                    ebLogTrace(f"Complete script parameters being used for this execution: {self.__script_params}")
                else:
                    ebLogTrace("Payload as a parameter is not configured for this request.")
                with connect_to_host(hostname = _node, ctx = get_gcontext(), local = isLocal) as _connected_node:
                    ebLogTrace("Creating/verifying OADT requests directory.")
                    _cmd_create_oadt_dir = f"/bin/mkdir -p {_request_directory}"
                    _cmd_structure = node_exec_cmd(_connected_node, _cmd_create_oadt_dir)
                    _create_oadt_dir_exitcode = _cmd_structure.exit_code
                    if _create_oadt_dir_exitcode != 0:
                        _error_message = f"Failed to create {_request_directory} directory."
                        ebLogError(_error_message)
                        raise Exception(_error_message)
                    _local_script_path = self.__scripts_metadata.get(self.__script_name).get(SCRIPT_PATH)
                    _dest_script_path = os.path.join(_request_directory, self.__script_name)
                    _connected_node.mCopyFile(_local_script_path, _dest_script_path)
                    ebLogTrace(f"SOP script {self.__script_name} copied to {_dest_script_path} on remote host: {_node}")

                    if _dest_json_file is not None:
                        _connected_node.mCopyFile(_local_json_file, _dest_json_file)
                        ebLogTrace(f"SOP script payload for {self.__script_name} copied to {_dest_json_file} on remote host: {_node}")

                    #Check if script executable has an absolute path or not
                    _script_executable = self.__scripts_metadata.get(self.__script_name).get(SCRIPT_EXEC)
                    if not _script_executable.startswith("/"):
                        ebLogTrace("Absolute path for executable not configured for this script, will attempt to check on remote node.")
                        _temp_exec = node_cmd_abs_path_check(_connected_node, _script_executable)
                        self.__scripts_metadata.get(self.__script_name)[SCRIPT_EXEC] = _temp_exec
                        ebLogTrace(f"Script: {self.__script_name} is configured to use the executable {_temp_exec}")
            except Exception as e:
                _error_msg = f"Error while running prechecks on {_node} for script {self.__script_name}. Detail error: {e}"
                ebLogError(_error_msg)
                _cmd_op = {"return_code": 500, "stdout_msgs": None, "stderr_msgs": _error_msg, "return_json": {}}
                self.__output[_node] = _cmd_op

        ebLogInfo("Prechecks successfully completed.")

    def mResolveIlomParametersIfApplicable(self, aCommands: list) -> None:

        _list_of_commands = aCommands
        if _list_of_commands is None or len(_list_of_commands) == 0:
            return

        _pattern = r'\{(.*?)\}'#Regex to extract one/multiple parameters from the command.
        for _idx, _commandmetadata in enumerate(_list_of_commands):
            _current_command = _commandmetadata.get("cmd", "")
            _current_matches = re.findall(_pattern, _current_command)
            _matched = False
            for _current_match in _current_matches:
                _matched = True
                if self.__script_payload.get(_current_match, None) is None:
                    raise ExacloudRuntimeError(0x815, 0xA, f"Parameter {_current_match} in command: {_current_command} is absent in payload.")

                _parameter_value = self.__script_payload.get(_current_match)
                _current_command = _current_command.replace(f"{{{_current_match}}}", _parameter_value)

            if _matched:
                ebLogTrace(f"Replacing ilom command: {_commandmetadata.get('cmd')} with {_current_command}")
                _list_of_commands[_idx]["cmd"] = _current_command


    def mProcessRequestILOM(self) -> None:

        ebLogInfo(f"Fetching ilom password for host(s): {self.__nodes_list}")
        _ilom_password = None
        _ilom_password = fetch_ilom_password(self.__targetnode_type)
        if _ilom_password is None:
            ebLogError("Failed to fetch ilom password.")
            raise ExacloudRuntimeError(0x815, 0xA, "Failed to fetch ilom password.")

        ebLogInfo(f"Executing script {self.__script_name}")
        _script_path = self.__scripts_metadata.get(self.__script_name).get(SCRIPT_PATH)
        _commands = list()
        with open(_script_path) as _file:
            _scipt_dict = json.load(_file)
            _commands = _scipt_dict.get("commands", [])
        _number_of_commands = len(_commands)
        self.mResolveIlomParametersIfApplicable(_commands)

        _is_asyncmode_supported = self.__scripts_metadata.get(self.__script_name).get(SCRIPT_PARALLEL_EXEC)
        if _is_asyncmode_supported:
            self.mProcessRequestILOMInAsyncMode(_commands, _ilom_password)
        else:
            for _node in self.__nodes_list:
                if _node in self.__output.keys():
                    ebLogWarn(f"Output metadata available before executing script {self.__script_name} on node {_node}. Skipping script execution.")
                    continue
                try:
                    _ssh_shell_object = None
                    with connect_to_host(_node, get_gcontext(), password = _ilom_password) as _connected_node:
                        _ssh_shell_object = interactiveSSHconnection(_connected_node.mGetSSHClient(), "->")
                        _cmd_op = {"return_code": 0, "stdout_msgs": "", "stderr_msgs": "", "return_json": {}}
                        _command_to_output_dict = dict()
                        for idx, _commandmetadata in enumerate(_commands):
                            _match_prompt = _commandmetadata.get("match", False)
                            _prompt = _commandmetadata.get("prompt", "->")
                            _command = _commandmetadata.get("cmd", "")
                            _current_timeout = _commandmetadata.get("timeout", 50)

                            if _ssh_shell_object.mGetCurrentPrompt() != _prompt:
                                if _match_prompt:
                                    if _ssh_shell_object is not None:
                                        _ssh_shell_object.mCloseInteractiveShell()
                                    raise ExacloudRuntimeError(0x0801, 0xA, f"Current prompt: {_ssh_shell_object.mGetCurrentPrompt()} doesn't match with required prompt {_prompt}")
                                else:
                                    ebLogWarn(f"Current prompt: {_ssh_shell_object.mGetCurrentPrompt()} doesn't match with required prompt {_prompt}. Continuing with execution of next command.")
                            _next_prompt = _prompt
                            if idx+1 < _number_of_commands:
                                _next_prompt = _commands[idx+1].get("prompt", "->")
                            ebLogTrace(f"Executing command: {_command} on host: {_node}, with prompt {_next_prompt}")
                            _output = _ssh_shell_object.mExecuteCommand(_command, _next_prompt, _current_timeout)
                            ebLogTrace(f"Output of {_command}: {_output}")
                            _command_to_output_dict[f"command_{idx+1}"] = {"command": _command, "output": _output}

                        if len(_command_to_output_dict.keys()) == 0:
                            ebLogWarn(f"There was no output for any commands executed before.")
                        else:
                            _cmd_op["return_json"] = copy.deepcopy(_command_to_output_dict)
                        self.__output[_node] = _cmd_op
                except Exception as e:
                    _error_msg = f"Error while executing script {self.__script_name} on node {_node}. Detail error: {e}"
                    ebLogError(_error_msg)
                    _cmd_op = {"return_code": 500, "stdout_msgs": None, "stderr_msgs": _error_msg, "return_json": {}}
                    self.__output[_node] = _cmd_op
                finally:
                    if _ssh_shell_object is not None:
                        _ssh_shell_object.mCloseInteractiveShell()

    def mProcessRequestILOMInAsyncMode(self, aListOfCommands: list, aPassword: str) -> None:

        _plist = ProcessManager()
        _commands = aListOfCommands
        _ilom_password = aPassword
        _number_of_commands = len(_commands)

        def exec_script(_node):
            _ssh_shell_object = None
            _cmd_op = {"return_code": 0, "stdout_msgs": "", "stderr_msgs": "", "return_json": {}}

            try:
                with connect_to_host(_node, get_gcontext(), password = _ilom_password) as _connected_node:
                    
                    _ssh_shell_object = interactiveSSHconnection(_connected_node.mGetSSHClient(), "->")
                    _command_to_output_dict = dict()

                    for idx, _commandmetadata in enumerate(_commands):
                        _match_prompt = _commandmetadata.get("match", False)
                        _prompt = _commandmetadata.get("prompt", "->")
                        _command = _commandmetadata.get("cmd", "")
                        _current_timeout = _commandmetadata.get("timeout", 50)

                        if _ssh_shell_object.mGetCurrentPrompt() != _prompt:
                            if _match_prompt:
                                if _ssh_shell_object is not None:
                                    _ssh_shell_object.mCloseInteractiveShell()
                                raise ExacloudRuntimeError(0x0801, 0xA, f"Current prompt: {_ssh_shell_object.mGetCurrentPrompt()} doesn't match with required prompt {_prompt}")
                            else:
                                ebLogWarn(f"Current prompt: {_ssh_shell_object.mGetCurrentPrompt()} doesn't match with required prompt {_prompt}. Continuing with execution of next command.")
                        _next_prompt = _prompt
                        if idx+1 < _number_of_commands:
                            _next_prompt = _commands[idx+1].get("prompt", "->")
                        ebLogTrace(f"Executing command: {_command} on host: {_node}, with prompt {_next_prompt}")
                        _output = _ssh_shell_object.mExecuteCommand(_command, _next_prompt, _current_timeout)
                        ebLogTrace(f"Output of {_command}: {_output}")

                        _command_to_output_dict[f"command_{idx+1}"] = {"command": _command, "output": _output}

                    if len(_command_to_output_dict.keys()) == 0:
                        ebLogWarn(f"There was no output for any commands executed before.")
                    else:
                        _cmd_op["return_json"] = copy.deepcopy(_command_to_output_dict)
                    
            except Exception as e:
                _error_msg = f"Error while executing script {self.__script_name} on node {_node}. Detail error: {e}"
                ebLogError(_error_msg)
                _cmd_op = {"return_code": 500, "stdout_msgs": None, "stderr_msgs": _error_msg, "return_json": {}}
            finally:
                if _ssh_shell_object is not None:
                    _ssh_shell_object.mCloseInteractiveShell()

            return _cmd_op


        for _node in self.__nodes_list:
            if _node in self.__output.keys():
                ebLogWarn(f"Output metadata available before executing script {self.__script_name} on node {_node}. Skipping script execution.")
                continue
            _p = ProcessStructure(exec_script, [_node,])
            _p.mSetMaxExecutionTime(30*60) #30 minutes timeout
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()
        _curent_process_list = _plist.mGetProcessList()
        for _current_process in _curent_process_list:
            _current_node = _current_process.mGetArgs()[0]
            _function_return = _current_process.mGetReturn()
            self.__output[_current_node] = _function_return

    def mProcessRequest(self) -> None:

        ebLogInfo(f"Executing script {self.__script_name}")
        _script_executable = self.__scripts_metadata.get(self.__script_name).get(SCRIPT_EXEC)
        _script_params = self.__script_params
        

        _is_asyncmode_supported = self.__scripts_metadata.get(self.__script_name).get(SCRIPT_PARALLEL_EXEC)
        if _is_asyncmode_supported:
            self.mProcessRequestInAynscMode()
        else:
            for _node in self.__nodes_list:
                if _node in self.__output.keys():
                    ebLogWarn(f"Output metadata available before executing script {self.__script_name} on node {_node}. Skipping script execution.")
                    continue
                try:
                    isLocal = False
                    _request_directory = self.__requests_dir
                    if _node == "localhost":
                        isLocal = True
                        _request_directory = self.__local_requests_dir
                    _script_path = os.path.join(_request_directory, self.__script_name)
                    _cmd_to_execute = f"{_script_executable} {_script_path} {_script_params}"
                    with connect_to_host(hostname = _node, ctx = get_gcontext(), local = isLocal) as _connected_node:
                        ebLogTrace(f"Executing command: {_cmd_to_execute} on host: {_node}")
                        _cmd_structure = node_exec_cmd(_connected_node, _cmd_to_execute)
                        _cmd_op = {"return_code": 0, "stdout_msgs": None, "stderr_msgs": None, "return_json": {}}
                        _cmd_op["return_code"] = _cmd_structure.exit_code
                        _cmd_op["stdout_msgs"] = _cmd_structure.stdout
                        _cmd_op["stderr_msgs"] = _cmd_structure.stderr
                        _return_json_support = self.__scripts_metadata.get(self.__script_name).get(SCRIPT_RETURN_JSON_SUPPORT)
                        if _return_json_support:
                            _return_json_path = os.path.join(_request_directory, "execution_output.json")
                            if _connected_node.mFileExists(_return_json_path):
                                ebLogTrace(f"Fetching execution_output.json from {_return_json_path} on remote host: {_node}")
                                if isLocal:
                                    _cmd_op["return_json"] = json.load(open(_return_json_path, 'r'))
                                else:
                                    _local_return_json_path = f"/tmp/{uuid.uuid1()}_execution_output.json"
                                    _connected_node.mCopy2Local(_return_json_path, _local_return_json_path)
                                    _cmd_op["return_json"] = json.load(open(_local_return_json_path, 'r'))
                            else:
                                ebLogWarn(f"Return json is configured but script did not produce any execution_output.json at {_return_json_path}")
                        self.__output[_node] = _cmd_op
                except Exception as e:
                    _error_msg = f"Error while executing script {self.__script_name} on node {_node}. Detail error: {e}"
                    ebLogError(_error_msg)
                    _cmd_op = {"return_code": 500, "stdout_msgs": None, "stderr_msgs": _error_msg, "return_json": {}}
                    self.__output[_node] = _cmd_op

    def mProcessRequestInAynscMode(self) -> None:

        _script_executable = self.__scripts_metadata.get(self.__script_name).get(SCRIPT_EXEC)
        _script_params = self.__script_params
        _plist = ProcessManager()

        def exec_script(_node):
            _cmd_op = {"return_code": 0, "stdout_msgs": None, "stderr_msgs": None, "return_json": {}}

            try:
                isLocal = False
                _request_directory = self.__requests_dir
                if _node == "localhost":
                    isLocal = True
                    _request_directory = self.__local_requests_dir
                _script_path = os.path.join(_request_directory, self.__script_name)
                _cmd_to_execute = f"{_script_executable} {_script_path} {_script_params}"
                with connect_to_host(hostname = _node, ctx = get_gcontext(), local = isLocal) as _connected_node:
                    _cmd_structure = node_exec_cmd(_connected_node, _cmd_to_execute)
                    ebLogTrace(f"Executing command: {_cmd_to_execute} on host: {_node}")
                    
                    _cmd_op["return_code"] = _cmd_structure.exit_code
                    _cmd_op["stdout_msgs"] = _cmd_structure.stdout
                    _cmd_op["stderr_msgs"] = _cmd_structure.stderr
                    _return_json_support = self.__scripts_metadata.get(self.__script_name).get(SCRIPT_RETURN_JSON_SUPPORT)
                    if _return_json_support:
                        _return_json_path = os.path.join(_request_directory, "execution_output.json")
                        if _connected_node.mFileExists(_return_json_path):
                            ebLogTrace(f"Fetching execution_output.json from {_return_json_path} on remote host: {_node}")
                            if isLocal:
                                _cmd_op["return_json"] = json.load(open(_return_json_path, 'r'))
                            else:
                                _local_return_json_path = f"/tmp/{uuid.uuid1()}_execution_output.json"
                                _connected_node.mCopy2Local(_return_json_path, _local_return_json_path)
                                _cmd_op["return_json"] = json.load(open(_local_return_json_path, 'r'))
                        else:
                            ebLogWarn(f"Return json is configured but script did not produce any execution_output.json at {_return_json_path}")
                    ebLogTrace(f"Command output: {_cmd_op}")
            except Exception as e:
                _error_msg = f"Error while executing script {self.__script_name} on node {_node}. Detail error: {e}"
                ebLogError(_error_msg)
                _cmd_op = {"return_code": 500, "stdout_msgs": None, "stderr_msgs": _error_msg, "return_json": {}}

            return _cmd_op

        for _node in self.__nodes_list:
            if _node in self.__output.keys():
                ebLogWarn(f"Output metadata available before executing script {self.__script_name} on node {_node}. Skipping script execution.")
                continue
            _p = ProcessStructure(exec_script, [_node,])
            _p.mSetMaxExecutionTime(30*60) #30 minutes timeout
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()
        _curent_process_list = _plist.mGetProcessList()
        for _current_process in _curent_process_list:
            _current_node = _current_process.mGetArgs()[0]
            _function_return = _current_process.mGetReturn()
            self.__output[_current_node] = _function_return
