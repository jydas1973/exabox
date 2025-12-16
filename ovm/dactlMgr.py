#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/dactlMgr.py /main/2 2025/08/05 07:01:28 kkviswan Exp $
#
# dactlMgr.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      dactlMgr.py - Delegation Access Control Management Operations
#
#    DESCRIPTION
#      This Module provides Operations related to Delegation Access Control Management capabilities
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    kkviswan    07/23/25 - 38225214 - DELEGATION MANAGEMENT BACKEND
#                           INTEGRATION ISSUES ON EXADB-XS ENVIRONMENT
#    nisrikan    06/05/25 - ENH 38035583 - BACKPORT DELEGATION ACCESS CONTROL
#                           SUPPORT TO EXADB-XS
#    kkviswan    05/21/25 - 37928955 Delegation Management New ER
#    kkviswan    05/21/25 - Creation
#


import base64
import json
import os
from time import time, sleep
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo

ALL_SUCCESS = "ALL_SUCCESS"
ANY_SUCCESS = "ANY_SUCCESS"

RUN_MODE_SYNC = "SYNC"
RUN_MODE_ASYNC = "ASYNC"

OPERATION_SUCCESS = "200"
OPERATION_PARTIAL_SUCCESS = "201"
OPERATION_IN_PROGRESS = "202"
OPERATION_INVALID_INPUT = "301"
OPERATION_INTERNAL_ERROR = "500"
OPERATION_INVALID_PARAMS = "400"
OPERATION_SERVICE_UNAVAILABLE = "503"


class ebDactlMgr(object):
    def __init__(self):
        self.options = None
        self.response = {"status": 301, "error": "initialized"}
        self.__resourceType = None

    @classmethod
    def mValidateCommonParams(cls, aCommonParams):
        # resourceType Already validated.
        if "idemtoken" not in aCommonParams:
            return False, "Invalid commonParameters, Missing idemtoken"
        dom0_domu_pairs = aCommonParams.get("dom0domUPairs")
        if not isinstance(dom0_domu_pairs, dict):
            return False, "Invalid commonParameters, Missing/Invalid dom0domUPairs"
        domu_list = dom0_domu_pairs.get("DOMU")
        if not isinstance(domu_list, list) or len(domu_list) == 0:
            return False, "Invalid commonParameters, Missing/Invalid DOMU parameters in dom0domUPairs"
        if  not aCommonParams.get("secretId"):
            return False, "Invalid commonParameters, Missing secretId"
        if  not aCommonParams.get("rpmVersion"):
            return False, "Invalid commonParameters, Missing rpmVersion"
        if  not aCommonParams.get("rpmParUrl"):
            return False, "Invalid commonParameters, Missing rpmParUrl"
        return True, None

    def mExecuteCmd(self, aOptions):
        """
        receive the command from the jsondispatch and process it accordingly
        the 'usercmd' holds which command need to be executed
        Args:
            aOptions: Json payload received from DACTL MIDTIER
        Returns: success/failure
        """
        self.options = aOptions

        _ret, _err = self.mValidateCommonParams(self.options.get("commonParameters"))
        if _ret is False:
            self.response = {"errorMessage": _err, "status": 301}
            return 0
        # Mandatory json payload is validated as part of jsondispatch in handler_dactl.py
        # For future implementations involving cloudvmcluster and vmcluster resource types,
        # new classes should be added that inherit from DaCtlOperationWrapper and implement the necessary functionality.
        self.__resourceType = self.options.get('commonParameters', {}).get('resourceType')
        if self.__resourceType == "exadbvmcluster":
            executor = DaCtlOperationWrapper(self.options)
        elif self.__resourceType == "cloudvmcluster":
            executor = DaCtlOperationWrapper(self.options)
        elif self.__resourceType == "vmcluster":
            executor = DaCtlOperationWrapper(self.options)
        else:
            _err = f"Invalid resource type - {self.__resourceType}"
            self.response = {"errorMessage": _err, "status": 301}
            return 0
        self.response = executor.mProcessCommand()
        status = self.response["status"] = int(self.response.get("status", 500))
        if  status == 202:
            self.response["status"] = 500
        # ebLogInfo("Operation Complete; updating the final result to exacloud")
        # self.mUpdateRequestData(response, "success")
        return 0

    def mGetResponseData(self):
        """
        Returns: DICT -- response of the current operation
        """
        return self.response


class DaCtlResponseFormat(object):
    def __init__(self):
        self.success_nodes = list()
        self.failure_nodes = list()
        self.in_progress_nodes = list()
        self.status = OPERATION_IN_PROGRESS
        self.statuses = dict()
        self.output = ""
        self.output_msgs = dict()
        self.errorMessage = dict()
        self.warningMessage = dict()
        self.dactlRpmVersion = dict()
        self.parUrl = ""
        self.logFileNames = []

    def mMergeDomuResponseJson(self, aDomuName, aReturnJson, aOutputFormat):
        """
        This function merges results from multiple DOMU's one by one
        Args:
            aDomuName: domu host name
            aReturnJson:  Backend Operation Result in JSON (dict) format.
            aOutputFormat: for most operation it is string or null. for special operations like command execute
                           output message holds json string required to be converted back to list/dict.

        Returns: None
        """
        operation_status = aReturnJson.get("status", OPERATION_IN_PROGRESS)
        node_output = aReturnJson.get("output", "")
        self.statuses[aDomuName] = operation_status
        self.output_msgs[aDomuName] = node_output
        self.errorMessage[aDomuName] = aReturnJson.get("errorMessage", "")
        self.warningMessage[aDomuName] = aReturnJson.get("warningMessage", "")
        self.dactlRpmVersion[aDomuName] = aReturnJson.get("dlgtMgmtRpmVersion", "")
        self.parUrl = aReturnJson.get("parUrl", "")
        self.logFileNames.extend(aReturnJson.get("logfileName", []))
        if operation_status == OPERATION_SUCCESS:
            if aOutputFormat == "file_list":
                try:
                    node_output = json.loads(aReturnJson.get("output", "[]"))
                    if type(self.output) is not list:
                        self.output = node_output
                    else:
                        self.output.extend(node_output)
                except Exception as e:
                    ebLogError(f"Failed to decode output format from {aDomuName}, skipped to add results to output: {e}")
            if aOutputFormat == "string":
                self.output = node_output if node_output else "Received success message from DOM-U"
            if aOutputFormat == "dict_map":
                try:
                    node_output = json.loads(aReturnJson.get("output", "{}"))
                    if type(self.output) is not dict:
                        self.output = node_output
                    else:
                        self.output.update(node_output)
                except Exception as e:
                    ebLogError(f"Failed to decode output format from {aDomuName}, skipped to add results to output: {e}")

    @property
    def response_json(self):
        """
        Returns: dict returns merged result from all DOM-U nodes
        """
        dactl_rpm_version = ','.join(set(v.strip() for v in self.dactlRpmVersion.values() if v != "-NA-"))
        if dactl_rpm_version == "":
            dactl_rpm_version = "-NA-"
        return_json = {
            "status": self.status,
            "output": self.output if isinstance(self.output, str) else json.dumps(self.output),
            "dlgtMgmtRpmVersion": dactl_rpm_version
        }
        error_message = "\n".join(f"{node}:{msg}" for node, msg in self.errorMessage.items() if msg)
        if error_message:
            return_json["errorMessage"] = error_message
        warning_message = "\n".join(f"{node}:{msg}" for node, msg in self.warningMessage.items() if msg)
        if warning_message:
            return_json["warningMessage"] = warning_message
        success_nodes = []
        failure_nodes = []
        in_progress_nodes = []
        for node_name, status in self.statuses.items():
            if status == OPERATION_SUCCESS:
                success_nodes.append(node_name)
            elif status == OPERATION_IN_PROGRESS:
                in_progress_nodes.append(node_name)
            else:
                failure_nodes.append(node_name)
        if success_nodes:
            return_json["success_domus"] = success_nodes
        if failure_nodes:
            return_json["failure_domus"] = failure_nodes
        if in_progress_nodes:
            return_json["in_progress_domus"] = in_progress_nodes
        if self.parUrl != "":
            return_json["parUrl"] = self.parUrl
        if self.logFileNames:
            return_json["logfileName"] = self.logFileNames
        return return_json

    def mSetResponseStatus(self, aStatus):
        self.status = aStatus


class dactlOperationConfig(object):
    def __init__(self,
                 json_tag="EMPTY",
                 node_policy=ALL_SUCCESS,
                 run_mode=RUN_MODE_SYNC,
                 pre_assign_check=True,
                 backend_op=None,
                 skip_install_failure=False,
                 output_format="string"):
        self.json_tag = json_tag
        self.node_policy = node_policy
        self.run_mode = run_mode
        self.pre_assign_check = pre_assign_check
        self.backend_op = backend_op or []
        self.output_format = output_format
        self.skip_install_failure = skip_install_failure


class DaCtlOperationWrapper(object):
    REMOTE_PYTHON3_EXE = '/usr/bin/python3'
    WRAPPER_SCRIPT = '/usr/local/supportctl/supportctlwrapper/supctlWrapper.py'
    OPERATION_POLL_WAIT_INTERVAL = 10  # sec
    CURL_RPM_DOWNLOAD_CMD_TEMPLATE = "/usr/bin/curl -X GET --silent --show-error {URL}{RPM} {EXTRA_OPTIONS} >/tmp/{RPM}"
    INSTALL_UPGRADE_RPM_CMD_TEMPLATE = "/usr/bin/sudo /usr/bin/rpm -U --force /tmp/{RPM}"
    QUERY_SUPPORTCTL_RPM = '/usr/bin/rpm -qa supportctl* | grep "supportctl-"'
    OPERATION_MAP = {
        "deploy": dactlOperationConfig(json_tag="deployInfo", pre_assign_check=False, backend_op=["install", "deploy"]),
        "create_user": dactlOperationConfig(json_tag="createUserInfo", node_policy=ANY_SUCCESS, backend_op=["adduser"]),
        "delete_user": dactlOperationConfig(json_tag="deleteUserInfo", backend_op=["deleteuser"], skip_install_failure=True),
        "update_debug_parurl": dactlOperationConfig(json_tag="parUrlInfo", backend_op=["updateparurl"], skip_install_failure=True),
        "get_debug_parurl": dactlOperationConfig(node_policy=ANY_SUCCESS, backend_op=["getparurl"], output_format="file_list"),
        "collect_debug_log": dactlOperationConfig(json_tag="parUrlInfo", node_policy=ANY_SUCCESS, output_format="file_list",
                                                backend_op=["collectdebuglog"]),
        "health_check": dactlOperationConfig(json_tag="parUrlInfo", node_policy=ANY_SUCCESS, backend_op=["healthcheck"]),
        "upgrade": dactlOperationConfig(json_tag="upgradeInfo", backend_op=["upgrade_download_rpm", "upgrade_rpm"]),
        "execute_commands": dactlOperationConfig(json_tag="commandExecutionInfo", run_mode=RUN_MODE_ASYNC, pre_assign_check=False,
                                                 backend_op=["multi_execute_commands"], output_format="dict_map"),
        "undeploy": dactlOperationConfig(pre_assign_check=False, backend_op=["undeploy"])
    }

    def __init__(self, aJsonPayloadOptions):
        self.json_config = aJsonPayloadOptions
        self.user_cmd = aJsonPayloadOptions.get("usercmd")
        self.common_parameters = aJsonPayloadOptions.get("commonParameters", {})
        self.idemtoken = self.common_parameters.get('idemtoken')
        self.domu_list = self.common_parameters.get("dom0domUPairs", {}).get("DOMU", [])
        self.rpm_version = self.common_parameters.get('rpmVersion')
        self.rpm_par_url = self.common_parameters.get('rpmParUrl')
        if not self.rpm_version.endswith(".rpm"):
            self.rpm_version += ".rpm"
        if self.rpm_par_url.endswith(".rpm"):
            self.rpm_par_url = os.path.dirname(self.rpm_par_url) + '/'
        self.par_url = self.common_parameters.get('parUrl')
        self.secret_id = self.common_parameters.get('secretId')

        self.target_nodes = list()
        self.executor_context = {}
        self.executor_result = {}
        self.success_nodes = list()
        self.failure_nodes = list()
        self.overall_result = DaCtlResponseFormat()
        self.sudo = True
        self.__sudoPath = "/usr/bin/sudo"

    def mConnectToDomuNode(self, aHost, aUser, aPrivateKey):
        """
        This function connect to DOM-U using kms object with ssh private key retrieved from secrets
        Args:
            aHost: DOM-U NAT Hostname
            aUser: Username - for all operation opc user; for validate assignment and command execution
                   Uses temp username.
            aPrivateKey: Corresponding user's private key always retrieved from secret.
        Returns: None
        """
        # Connect to DOM-U Host name, with
        try:
            _exakms = get_gcontext().mGetExaKms()
            _entry = _exakms.mBuildExaKmsEntry(aHost, aUser, aPrivateKey, ExaKmsHostType.DOMU)
        except Exception as e:
            _err_msg = f"Unable to build the Host ExaKmsEntry {str(e)}"
            ebLogError(f"{aHost} - {_err_msg}")
            return None, _err_msg
        try:
            _node = exaBoxNode(get_gcontext())
            _node.mSetUser(aUser)
            _node.mSetSudo(False)
            _node.mSetExaKmsEntry(_entry)
            if not _node.mIsConnectable(aHost=aHost):
                _err_msg = f"Can't establish connection to remote host"
                ebLogError(f"{aHost} - {_err_msg}")
                return None, _err_msg
            _node.mConnect(aHost=aHost, aTimeout=20)
        except Exception as e:
            _err_msg = f"Unable to connect to the Host {str(e)}"
            ebLogError(f"{aHost} - {_err_msg}")
            return None, _err_msg
        ebLogInfo(f"Successfully connected to {aHost}.")
        return _node, ""

    def mExecuteOnDomU(self, aDomuName, aCmd):
        """
        Execute command on DOM-U.
        Args:
            aDomuName: DomU hostname
            aCmd: command to be executed
        Returns: success/failure, _out, _err
        """

        _node = self.executor_context.get(aDomuName)
        if _node is None:
            ebLogInfo(f"Unable to execute command on DOM-U {aDomuName}; No valid connection")
            return -1, "", "Invalid connection"
        try:
            ebLogInfo(f"Executing command on DOM-U {aDomuName} cmd: {aCmd}")
            _, _o, _e = _node.mExecuteCmd(aCmd, aDecodeUtf8=True, aTimeout=30)
            _out = _o.read()
            _err = _e.read()
            if isinstance(_out, bytes):
                _out = _out.decode('utf8', errors='ignore')
            if isinstance(_err, bytes):
                _err = _err.decode('utf8', errors='ignore')
            _rc = _node.mGetCmdExitStatus()
            ebLogInfo(f"Executed on DOM-U {aDomuName} rc: {_rc} out: {_out} err: {_err}")
        except Exception as e:
            _err = f"Unable to execute command error: {str(e)}"
            _rc = -1
            _out = ""
            ebLogError(_err)
        return _rc, _out, _err

    def mInitializeClusterOperations(self, aUser, aSshPvtKey):
        """
        for all target nodes makes connection cache for executing dactl operations
        Args:
            aUser: Username - for all operation opc user; for validate assignment and command execution
                   temp username is used
            aSshPvtKey: Corresponding user's private key always retrieved from secret.
        Returns:
            None
        Note: If any node connection fails depending on operation need to take judgement later
        """
        for domu in self.target_nodes:
            _node, _err_msg = self.mConnectToDomuNode(domu, aUser, aSshPvtKey)
            if _node is None:
                self.executor_result[domu] = self.mReportError(OPERATION_INTERNAL_ERROR,
                                                               "Failed to connect to remote host",
                                                               error_message=_err_msg)
            self.executor_context[domu] = _node

    def mReleaseClusterOperations(self):
        """
        Release all cluster connection to DOM-U
        Returns: None
        """
        for _dom_u in self.executor_context:
            if self.executor_context.get(_dom_u):
                self.executor_context[_dom_u].mDisconnect()
                self.executor_context[_dom_u] = None

    def mGetRpmVersionFromDomu(self, aDomuName):
        """
        Get the RPM version number from DOM-U
        Args:
            aDomuName: domu host name
        Returns:
            string rpm version number or "-NA-"
        """
        cmd = '/usr/bin/rpm -qa supportctl* | grep "supportctl-"'
        ret, output, error = self.mExecuteOnDomU(aDomuName, cmd) ## self.executor_context[aDomuName].mExecuteCmd(cmd)
        if ret != 0 or 'supportctl-' not in output:
            return "-NA-"
        else:
            return output.splitlines()[0]

    def mDownloadAndInstallRpmOnDomu(self, aDomuName):
        extra_options = "-k" if "r1.oracleiaas" in self.rpm_par_url else ""
        download_rpm_cmd = self.CURL_RPM_DOWNLOAD_CMD_TEMPLATE.format(URL=self.rpm_par_url, RPM=self.rpm_version,
                                                                      EXTRA_OPTIONS=extra_options)
        ret, output, error = self.mExecuteOnDomU(aDomuName, download_rpm_cmd)
            # self.executor_context[aDomuName].mExecuteCmd(download_rpm_cmd))
        if ret != 0:
            error = f"Failed to download {self.rpm_version} RPM on node {aDomuName} stdout: {output} error: {error}"
            ebLogError(error)
            return -1

        rpm_install_or_upgrade_cmd = self.INSTALL_UPGRADE_RPM_CMD_TEMPLATE.format(RPM=self.rpm_version)
        ret, output, error =  self.mExecuteOnDomU(aDomuName, rpm_install_or_upgrade_cmd)
        if ret != 0:
            error = f"Failed to install {self.rpm_version} on node {aDomuName} stdout: {output} error: {error}"
            ebLogError(error)
            return -1

        ebLogInfo("Successfully installed {0} on node {1}".format(self.rpm_version, aDomuName))
        return 0

    def mGetSSHPrivateKeyFromSecrets(self, aSecretId):
        """
        Args:
            aSecretId: sectect ocid, using which need to retrieve private key from secrets
        Returns:
            string - decoded private key
        """
        try:
            # Initialize Instance Principals and SecretsClient
            _factory = ExaOCIFactory()
            _secrets_client = _factory.get_secrets_client()
            _response = _secrets_client.get_secret_bundle(secret_id=aSecretId)
            secret_data_json_str = base64.b64decode(_response.data.secret_bundle_content.content).decode('utf-8')
        except Exception as e:
            _err_msg = f"Failed to retrieve secret bundle content from secret service: {e}"
            ebLogError(_err_msg)
            return -1, "", _err_msg
        try:
            secret_data_json = json.loads(secret_data_json_str)
            secret_data = secret_data_json['privateKey']
        except Exception as e:
            _err_msg = f"Failed to decode private key from secret data: {e}"
            ebLogError(_err_msg)
            return -1, "", _err_msg

        return 0, secret_data, ""

    def mExecuteBackendOperationOnDomu(self, aDomuName, aBackendWrapperCmd):
        """
        execute backend operation on DOM-U
        Args:
            aDomuName: Domu Hostname
            aBackendWrapperCmd: dactl backend operation full command
        Returns: None
        Note: The result of execution is exists in executor_result for each node
        """
        if self.executor_context.get(aDomuName) is None:

            if self.executor_result.get(aDomuName, {}).get("status", OPERATION_IN_PROGRESS) != OPERATION_INTERNAL_ERROR:
                self.executor_result[aDomuName] = self.mReportError(OPERATION_INTERNAL_ERROR,
                                                                    "No valid connection found",
                                                                    error_message="No valid connection found")
            return
        ret, stdout, stderr =  self.mExecuteOnDomU(aDomuName, aBackendWrapperCmd)
        try:
            # {"idemtoken": "12345676", "status": "202", "output": "in progress", "errorMessage": null,
            # "warningMessage": null, "remoteHostName": "mcdb4vm-bn0ni1", "dlgtMgmtRpmVersion":
            # "supportctl-24.1.0.0.0-240221.0256.x86_64\n", "returnCode": "0"}
            self.executor_result[aDomuName] = json.loads(stdout.splitlines()[-1])
        except Exception:
            self.executor_result[aDomuName] = self.mReportError(OPERATION_INTERNAL_ERROR, stdout, stderr)
        return

    def mReportError(self, status, output, error_message="", warning_message="", backend_version='-NA-',
                     failure_domus=None):
        return_json = {"status": status, "output": output, "errorMessage": error_message,
                       "warningMessage": warning_message, "dlgtMgmtRpmVersion": backend_version}
        if failure_domus:
            return_json["failure_domus"] = failure_domus
        return return_json

    def mFormDactlBackendWrapperCommand(self, idemtoken, operation, json_input, comment=None, sudo=False):
        sudo_cmd = [self.__sudoPath, "--"] if (self.sudo is True or sudo is True) else []
        cmd = sudo_cmd + [self.REMOTE_PYTHON3_EXE, self.WRAPPER_SCRIPT, 'supportctl',
                          '-i', idemtoken,
                          '-o', operation,
                          '-j', json.dumps(json_input)]
        if comment:
            cmd.append('-c')
            cmd.append(comment)
        cmd_str = cmd[0]
        for arg in cmd[1:]:
            cmd_str += " '" + str(arg) + "'"
        return cmd_str

    def mExecuteBackendOperationWaitForResult(self, aOperation, aIdemtoken, aJsonInput, aComment, timeout=1800,
                                              aTargetDomuNodes=None):
        """
        Executes backend DACTL operations on each DOMU within the target nodes and waits for all operations to complete.
               Each DOMU responds with a JSON status code (e.g., 202, 200, 500).
               The process waits until all DOMU operations have logically concluded — i.e., no response with status 202
        Args:
            aOperation: dactl operation name
            aIdemtoken: idemtoken to operation dactl operation.
            aJsonInput: operation json payload
            aComment: comment for debugging
            timeout: timeout in seconds
            aTargetDomuNodes: - list of target nodes.

        Returns: None
        """
        _target_domu_nodes = aTargetDomuNodes
        if _target_domu_nodes is None:
            _target_domu_nodes = self.target_nodes

        backend_wrapper_cmd = self.mFormDactlBackendWrapperCommand(aIdemtoken, aOperation, aJsonInput, aComment)
        # clear execution results; start fresh context
        self.mResetIntermediateExecutorResult()
        operation_in_progress = True
        operation_start_time = time()
        while operation_in_progress:
            operation_in_progress = False
            iter_start = time()
            for host in _target_domu_nodes:
                status = self.executor_result.get(host, {}).get('status', OPERATION_IN_PROGRESS)
                # ebLogInfo("Check Operation status for {0} on {1} is {2}".format(operation, host, status))
                if status != OPERATION_IN_PROGRESS:
                    continue
                self.mExecuteBackendOperationOnDomu(host, backend_wrapper_cmd)
                status = self.executor_result.get(host, {}).get('status', OPERATION_IN_PROGRESS)
                if status != OPERATION_IN_PROGRESS:
                    continue
                operation_in_progress = True
            if operation_in_progress:
                time_lapsed = time() - iter_start
                if time_lapsed < self.OPERATION_POLL_WAIT_INTERVAL:
                    sleep(self.OPERATION_POLL_WAIT_INTERVAL - time_lapsed)
                if 0 < timeout < time() - operation_start_time:
                    break

    def mExecuteBackendOperationAsyncResult(self, aOperation, aIdemtoken, aJsonInput, aComment, aTargetDomuNodes=None):
        """
        Do not wait for all backend operation results. Simply execute command once and send the result
        merge the result and send it. Merging of results / handling of result are
        determined by caller using determine_backend_result
        Args:
            aOperation: dactl operation name
            aIdemtoken: idemtoken to operation dactl operation.
            aJsonInput: operation json payload
            aComment: comment for debugging
            aTargetDomuNodes: - list of target nodes.

        Returns: None
        """
        target_nodes = aTargetDomuNodes
        if target_nodes is None:
            target_nodes = self.target_nodes
        backend_wrapper_cmd = self.mFormDactlBackendWrapperCommand(aIdemtoken, aOperation, aJsonInput, aComment)
        self.mResetIntermediateExecutorResult()
        for host in target_nodes:
            self.mExecuteBackendOperationOnDomu(host, backend_wrapper_cmd)

    def mDetermineBackendOperationResult(self, operation_cfg):
        # 1. Merge the results and set the overall operation status
        #    1.1. set result to IN_PROGRESS if any node's operation is IN_PROGRESS.
        #    1.2. determine the final result based on node_policy
        #          ALL_SUCCESS – Mark as SUCCESS only if all nodes succeed; otherwise, mark as FAILURE.
        #          ANY_SUCCESS – Mark as SUCCESS if at least one node succeeds; otherwise, mark as FAILURE.
        # 2. Populate the success nodes and failure nodes.
        ret = OPERATION_INTERNAL_ERROR
        self.success_nodes = list()
        self.failure_nodes = list()
        in_progress = False
        for domu in self.domu_list:
            if domu not in self.executor_result:
                continue
            status = self.executor_result[domu].get('status', OPERATION_IN_PROGRESS)
            # ebLogInfo("Check Operation status for {0} on {1} is {2}".format(operation, host, status))
            if status == OPERATION_SUCCESS:
                self.success_nodes.append(domu)
            elif status != OPERATION_IN_PROGRESS:
                self.failure_nodes.append(domu)
            else:
                in_progress = True
            self.overall_result.mMergeDomuResponseJson(domu, self.executor_result[domu],
                                                       operation_cfg.output_format)
        if in_progress is True:
            self.overall_result.mSetResponseStatus(OPERATION_IN_PROGRESS)
            ret = OPERATION_IN_PROGRESS
        elif operation_cfg.node_policy == ALL_SUCCESS:
            if len(self.failure_nodes) == 0:
                self.overall_result.mSetResponseStatus(OPERATION_SUCCESS)
                ret = OPERATION_SUCCESS
            else:
                self.overall_result.mSetResponseStatus(OPERATION_INTERNAL_ERROR)
                # Partial Success which means need rollback and return OPERATION_INTERNAL_ERROR
                ret = OPERATION_PARTIAL_SUCCESS
        elif operation_cfg.node_policy == ANY_SUCCESS:
            if len(self.success_nodes) > 0:
                self.overall_result.mSetResponseStatus(OPERATION_SUCCESS)
                ret = OPERATION_SUCCESS
            else:
                self.overall_result.mSetResponseStatus(OPERATION_INTERNAL_ERROR)
                ret = OPERATION_INTERNAL_ERROR
        return ret

    def mRollbackBackendOperation(self):
        # [optional] Rollback - nodes operation in case of FAILURE and node_policy is ALL_NODES_MUST_SUCCEED
        #       for each of SUCCESS nodes execute rollback function.
        #
        # This is needed for future commands.
        pass

    def mExecuteBackendOperationOnAllDomus(self, aOperation, aOperationJson, aOperationCfg):
        idemtoken = self.idemtoken + "-" + aOperation
        if aOperationCfg.run_mode == RUN_MODE_SYNC:
            self.mExecuteBackendOperationWaitForResult(aOperation, idemtoken, aOperationJson, "")
        elif aOperationCfg.run_mode == RUN_MODE_ASYNC:
            self.mExecuteBackendOperationAsyncResult(aOperation, idemtoken, aOperationJson, "")
        ret = self.mDetermineBackendOperationResult(aOperationCfg)
        if ret == OPERATION_PARTIAL_SUCCESS:
            self.mRollbackBackendOperation()
            ret = OPERATION_INTERNAL_ERROR
        return ret

    def mResetIntermediateExecutorResult(self):
        for _dom_u in self.domu_list:
            if self.executor_context.get(_dom_u) is None:
                continue
            self.executor_result[_dom_u] = {"status": OPERATION_IN_PROGRESS}

    def mVerifyRpmOnAllRequiredDomus(self, aPreAssignCheck, aIsAssignOperation):
        """
        Verify DACTL rpm is installed on all DOM-Us; if not install the rpm.
        Args:
            aPreAssignCheck: Install of RPM is mandatory for some operations; some operation
                    Install is not possible as login with temp user etc..
            aIsAssignOperation: For assignment operation its handled outside
        Returns: succes/failure
        """
        install_rpm = aPreAssignCheck or aIsAssignOperation
        if install_rpm is False:
            return 0
        error_during_install = 0
        assignment_nodes = list()
        self.failure_nodes.clear()
        for _dom_u in self.target_nodes:
            if self.executor_context.get(_dom_u) is None:
                ebLogError(f"Connection to {_dom_u} is unsuccessful, marking installation on this node as failed.")
                self.failure_nodes.append(_dom_u)
                error_during_install = -1
                continue
            rpm_version = self.mGetRpmVersionFromDomu(_dom_u)
            if rpm_version != '-NA-' and (aIsAssignOperation is False or rpm_version == self.rpm_version[:-4]):
                continue
            _ret = self.mDownloadAndInstallRpmOnDomu(_dom_u)
            if _ret != 0:
                self.failure_nodes.append(_dom_u)
                error_during_install = -1
                continue
            if aPreAssignCheck is True:
                assignment_nodes.append(_dom_u)

        if len(assignment_nodes) == 0:
            return error_during_install

        _deployInfo = {"parUrl": self.par_url, "rpmVersion": self.rpm_version, "rpmParUrl": self.rpm_par_url}
        idemtoken = self.idemtoken + "-" + "install"
        self.mExecuteBackendOperationWaitForResult("install", idemtoken, _deployInfo,
                                                   f"Assignment during operation {self.user_cmd} ",
                                                   aTargetDomuNodes=assignment_nodes)
        idemtoken = self.idemtoken + "-" + "deploy"
        self.mExecuteBackendOperationWaitForResult("deploy", idemtoken, _deployInfo,
                                                   f"Assignment during operation {self.user_cmd} ",
                                                   aTargetDomuNodes=assignment_nodes)
        return error_during_install

    def mValidateInputJson(self):
        """
        validates minimum validation (which are directly used in exacloud code)
            - other key,value pair are validated in RPM.
            - this is done to compatibility between RPM and DACTL midtier.
        Returns: success/failure , error message
        """
        if self.user_cmd not in self.OPERATION_MAP:
            _err_msg = f"{self.user_cmd} is not supported - supported operations {','.join(self.OPERATION_MAP.keys())}"
            return -1, _err_msg

        operation_cfg = self.OPERATION_MAP[self.user_cmd]
        if operation_cfg.json_tag != "EMPTY" and operation_cfg.json_tag not in self.json_config:
            _err_msg = f"Missing {operation_cfg.json_tag} key for {self.user_cmd} command"
            return -1, _err_msg

        operation_json = self.json_config.get(operation_cfg.json_tag, {})
        if not isinstance(operation_json, dict):
            _err_msg = f"Invalid value for {operation_cfg.json_tag} key for {self.user_cmd} command"
            return -1, _err_msg

        # Validate execute_commands minimal needed as using which need to connect to DOM-U nodes
        if self.user_cmd == 'execute_commands':
            username = operation_json.get('commandExecutionUser')
            list_of_commands = operation_json.get('listOfCommands')
            secret_id = operation_json.get('commandExecutionUserSecretId')
            if username is None:
                return -1, "Missing commandExecutionUser for execute_commands operation"
            if secret_id is None:
                return -1, "Missing commandExecutionUserSecretId for execute_commands operation"
            if not isinstance(list_of_commands, dict):
                return -1, "Missing/Invalid listOfCommands for execute_commands operation"

        return 0, ""

    def mProcessCommand(self):
        """
        Process dactl command
        Returns:
            dict - overall result of operation which is sent back to API response.
        """
        # Validate all static checks before starting operation
        _rc, _err_msg = self.mValidateInputJson()
        if _rc != 0:
            ebLogError(_err_msg)
            return self.mReportError(OPERATION_INVALID_INPUT, output="Invalid operation", error_message=_err_msg)

        operation_cfg = self.OPERATION_MAP[self.user_cmd]
        operation_json = self.json_config.get(operation_cfg.json_tag, {})

        # deploy info must contain following values so update params
        if operation_cfg.json_tag in ["deployInfo", "upgradeInfo"]:
            operation_json["parUrl"] =  self.par_url
            operation_json["rpmVersion"] = self.rpm_version
            operation_json["rpmParUrl"] = self.rpm_par_url

        if self.user_cmd == 'execute_commands':
            self.sudo = False
            username = operation_json.get('commandExecutionUser')
            # hostnames are optional parameter if not specified execute on all DOM-Us.
            self.target_nodes = operation_json.get('listOfCommands').get('hostnames', self.domu_list)
            secret_id = operation_json.get('commandExecutionUserSecretId')
        else:
            username = 'opc'
            secret_id = self.secret_id
            self.target_nodes = self.domu_list

        _rc, ssh_pkey, _err_msg = self.mGetSSHPrivateKeyFromSecrets(secret_id)
        if _rc != 0:
            ebLogError(_err_msg)
            return self.mReportError(OPERATION_INTERNAL_ERROR, output="SSH key is missing", error_message=_err_msg)
        try:
            self.mInitializeClusterOperations(username, ssh_pkey)
            ret = self.mVerifyRpmOnAllRequiredDomus(operation_cfg.pre_assign_check, self.user_cmd == "deploy")
            if ret != 0:
                if operation_cfg.node_policy == ALL_SUCCESS and operation_cfg.skip_install_failure is False:
                    return self.mReportError(OPERATION_INTERNAL_ERROR, output="Failed to install RPM in some of DOM-U",
                                             failure_domus=self.failure_nodes)
            for operation in operation_cfg.backend_op:
                ret = self.mExecuteBackendOperationOnAllDomus(operation, operation_json, operation_cfg)
                if ret != OPERATION_SUCCESS:
                    break
            operation_response = self.overall_result.response_json
            if operation_cfg.run_mode == RUN_MODE_ASYNC:
                operation_response["async_operation_status"] = operation_response["status"]
                operation_response["status"] = OPERATION_SUCCESS
            return operation_response
        # Here do not catch any exception (only Unknown runtime exceptions are possible and
        # call will handle same, and send the information to dactl midtier
        finally:
            # it is mandatory to release all ssh connection.
            self.mReleaseClusterOperations()

