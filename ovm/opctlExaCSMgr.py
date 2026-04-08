#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/opctlExaCSMgr.py /main/1 2026/01/28 03:29:47 nisrikan Exp $
#
# opctlExaCSMgr.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      opctlExaCSMgr.py - Operator Access Control Management Operations for ExaCS
#
#    DESCRIPTION
#      This Module provides Operations related to Operator Access Control Management for ExaCS
#
#    NOTES
#      Structured similarly to dactlMgr.py
#
#    MODIFIED   (MM/DD/YY)
#    nisrikan  01/20/26 - Bug 38702503 - NEED A MECHANISM TO ROUTE CALLS TO OPCTL IN CASE OF NODE CONNECTION FAILURES
#


import json
import logging
import logging.handlers
import os
import socket
import sys
import traceback
import getpass

from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.scheduleJobs.utils import mExecuteLocal
from exabox.ovm.clucontrol import exaBoxCluCtrl

class ExaCloudWrapper(object):
    def __init__(self, ebox, infra, requestObj, logger, options, base_path):
        self.requestObj = requestObj
        self.options = options
        self.infra_type = infra
        self.current_user = getpass.getuser()
        
        self.ebox = ebox
        self.rpm_exec_path = "/bin/rpm"
        self.find_exec_path = "/usr/bin/find"
        self.sudo_exec_path = ""
        self.rmdir_path = "/usr/bin/rmdir"
        self.chown_path = "/usr/bin/chown"
        self.mkdir_path = "/usr/bin/mkdir"
        self.rpm_storage_path = "/u01/downloads/opctl/"

        self.opctl_base_path = base_path
        self.opctl_resource_path = None
        self.opctl_log_path = None

        if options:
            self.json_input = self.options.jsonconf

        # create logger or use an already existing one
        self.opctl_resource_path = os.path.join(self.opctl_base_path, infra)
        self.opctl_log_path = os.path.join(self.opctl_resource_path, "log")
        if logger == "create_logger":
            if not getattr(self.options, 'unittest', False):
                self.init_logging_folders(infra)
            self.logger = logging.getLogger('exacloud-opctlMgr')
        else:
            self.logger = logging.getLogger('exacloud-opctlMgr')

    @classmethod
    def set_infra_type(cls, infra=None):
        if infra == "cloudexadatainfrastructure":
            return ExaCSExacloudWrapper(None, infra, None, None, None, None)
        return cls(None, infra, None, None, None, "/u01/.opctl/")  # Adjust parameters as necessary
        
    def execute_cmd(self):
        raise NotImplementedError

    def get_rpm_version(self):
        rpm_version_check = f"""{self.rpm_exec_path} -qa opctl-backend-core*"""
        return_code, _, output, error = self.execute_local(rpm_version_check)
        if return_code != 0:
            error = f"rpm check error {error}"
            return None, error
        version = output.strip()
        return version, None

    def get_json_value(self, key):
        if self.options.jsonconf:
            return self.options.jsonconf.get(key, None)
        return None

    def execute_local(self, cmd):
        _rc, _io, _out, _err = mExecuteLocal(cmd)
        ebLogInfo(f"execution results of cmd {cmd}: return code {_rc} output {_out} error {_err}")
        return _rc, _io, _out, _err

    def execute_backend_script(self, backend_json_input):
        raise NotImplementedError

    def update_exacloud_db(self, status, data, aParams):
        if status in [202, '202']:
            status_info = "inprogress"
        elif status in [200, '200']:
            status_info = "success"
        else:
            status_info = "failed"

        db = ebGetDefaultDB()
        if aParams:
            ebLogInfo(f"from agent updating status {status} data {data} uuid {aParams['uuid']}")
            req_obj = db.mGetRequest(aParams["uuid"])
            if not req_obj:
                self.logger.error(f"could not get request object for uuid {aParams['uuid']}")
                return req_obj

            opctlJobReq = ebJobRequest(None, aParams)
            opctlJobReq.mPopulate(req_obj)

            if data:
                opctlJobReq.mSetData(json.dumps(data))

            if status_info == "inprogress":
                opctlJobReq.mSetStatus("Pending")
            else:
                opctlJobReq.mSetStatus("Done")

            if status_info == "failed":
                opctlJobReq.mSetError(int(status))
                opctlJobReq.mSetErrorStr(json.dumps(data.get("error_message")))

            db.mUpdateRequest(opctlJobReq, aInternal=True)
            return opctlJobReq
        else:
            req_obj = self.requestObj
            if req_obj is None:
                self.logger.error("could not get request object")
                return req_obj

            self.logger.info(f"from jsondispatch updating status of {req_obj.mGetUUID()} to {status_info}")

            if status_info == "inprogress":
                req_obj.mSetStatus("Pending")
            else:
                req_obj.mSetStatus("Done")

            if data:
                req_obj.mSetData(json.dumps(data))

            if status_info == "failed":
                req_obj.mSetError(int(status))
                req_obj.mSetErrorStr(json.dumps(data.get("error_message")))

            db.mUpdateRequest(req_obj, aInternal=True)
            return req_obj

    def get_status_for_idemtoken(self, idemtoken):
        raise NotImplementedError

    def check_status_for_idemtoken(self, uuid, idemtoken):
        raise NotImplementedError

    def get_stack_trace(self):
        trace_back = sys.exc_info()[2]
        trace_back = traceback.format_tb(trace_back)
        return '\n'.join(trace_back)

    def create_dir(self, path, user=None, permissions="744"):
        if not user:
            user = self.current_user

        if os.path.exists(path) and os.path.isdir(path):
            ebLogInfo(f"path {path} exists")
            chown_cmd = f"{self.sudo_exec_path} {self.chown_path} -R {user} {path}"
            self.execute_local(chown_cmd)
            return

        needed_paths = []
        needed_paths.append(path)
        parent_dir = os.path.dirname(path)
        while parent_dir:
            if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
                break
            needed_paths.append(parent_dir)
            parent_dir = os.path.dirname(parent_dir)

        if needed_paths:
            path_to_create = needed_paths.pop(0)
            if not os.path.exists(path_to_create) or os.path.isfile(path_to_create):
                if os.path.isfile(path_to_create):
                    rmdir_cmd = f"{self.sudo_exec_path} {self.rmdir_path} -rf {path_to_create}"
                    self.execute_local(rmdir_cmd)
                    ebLogInfo(f"path_to_create path was a file")

                mkdir_cmd = f"{self.sudo_exec_path} {self.mkdir_path} -p -m 744 {path_to_create}"
                self.execute_local(mkdir_cmd)
                ebLogInfo(f"{path_to_create} is created")

                chown_cmd = f"{self.sudo_exec_path} {self.chown_path} -R {user} {path_to_create}"
                self.execute_local(chown_cmd)
                ebLogInfo(f"{path_to_create} is created")

    def init_logging_folders(self, resource_type, opctl_base_path=None):
        if hasattr(self.options, 'unittest') and self.options.unittest is True:
            _opctlBasePath = os.getcwd()

        if not opctl_base_path:
            opctl_base_path = self.opctl_base_path

        self.opctl_resource_path = os.path.join(opctl_base_path, resource_type)
        self.opctl_log_path = os.path.join(self.opctl_resource_path, "log")

        self.create_dir(self.opctl_log_path)

        dfltLogger = logging.getLogger('dfltlog')
        h = dfltLogger.__dict__
        oldHandlerList = h['handlers']
        oldHandlerfmt = None
        if oldHandlerList:
            oldHandler = oldHandlerList[0]
            oldHandlerfmt = getattr(oldHandler, 'formatter', None)

        exaCloudOpctlLog = logging.getLogger('exacloud-opctlMgr')
        exaCloudOpctlLog.propagate = False

        if not (hasattr(self.options, 'unittest') and self.options.unittest is True):
            logFileName = os.path.join(self.opctl_log_path, "opctl-exacloud-wrapper-%(host)s.log")
            log_filename = logFileName % {'host': socket.gethostname()}
            logRotationSize = 10000000
            logRotationNum = 20
            handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=logRotationSize, backupCount=logRotationNum)
            handler.setFormatter(oldHandlerfmt)
            exaCloudOpctlLog.setLevel(logging.INFO)
            exaCloudOpctlLog.addHandler(handler)
            exaCloudOpctlLog.disabled = False

            os.chmod(log_filename, 0o666)

    def init_status_folders(self, resource_type):
        status_path = os.path.join(self.opctl_resource_path, ".idemtoken")
        self.create_dir(status_path)


class ExaCSExacloudWrapper(ExaCloudWrapper):
    def __init__(self, ebox, infra, requestObj, logger, options, host_info):
        self.resource_type = infra
        self.opctl_exacs_base_path = "/u01/.opctl/"
        super().__init__(ebox, infra, requestObj, logger, options, self.opctl_exacs_base_path)

        self.python3_path = os.path.dirname(os.path.abspath(__file__))
        self.python3_path = f"{self.python3_path}/../../bin/python3"
        self.backend_script_path = f"{self.python3_path} /usr/local/opctl/opctlexacswrapper/opctlWrapper.py"
        self.backend_status_path = os.path.join(self.opctl_resource_path, ".idemtoken")
        self.transform_host_info(host_info)
        
    def transform_host_info(self, host_info):
        self.host_info = {}
        self.host_info["host_info"] = {}
        
        if not host_info or len(host_info) == 0:
            return
        
        for dom0 in host_info.get("dom0s"):
            self.host_info["host_info"][dom0] = {"type": "dom0"}

        for cell in host_info.get("cells"):
            self.host_info["host_info"][cell] = {"type": "cell"}
            
    def execute_backend_script(self, backend_json_input):
        self.idemtoken = self.json_input.get("idemtoken", None)
        cmd = f"""{self.backend_script_path} -i {self.idemtoken} -o {self.operation} -j '{json.dumps(backend_json_input)}' -c '{json.dumps(self.host_info)}' """
        return_code, _, out, error = self.execute_local(cmd)
        return return_code, out, error

    def execute_cmd(self):
        idemtoken = self.get_json_value("idemtoken")

        if not getattr(self.options, 'unittest', False):
            if not os.path.exists(self.opctl_exacs_base_path) or not os.path.isdir(self.opctl_exacs_base_path):
                error = f"{self.opctl_exacs_base_path} does not exist"
                self.logger.error(error)
                return_value = -1
                status = 500
                data = {"error": error}
                self.update_exacloud_db(status, data, aParams=None)
                return return_value

        user_cmd = self.get_json_value("usercmd")
        if user_cmd == "assign":
            return_value, output, error = self.handle_assign_operations()
        elif user_cmd == "create_user":
            return_value, output, error = self.handle_create_user()
        elif user_cmd == "delete_user":
            return_value, output, error = self.handle_delete_user()
        else:
            error = f"{user_cmd} is not supported"
            self.logger.error(error)
            return_value = -1

        status = 500
        data = self.get_status_for_idemtoken(idemtoken)
        if data and "status" in data:
            status = data["status"]

        self.update_exacloud_db(status, data, aParams=None)
        return return_value

    def handle_assign_operations(self):
        self.operation = self.json_input.get("operation")
        if self.operation in ["install", "upgrade"]:
            return_value, output, error = self.handle_install_rpm()
        elif self.operation in ["deploy", "undeploy"]:
            return_value, output, error = self.handle_deploy_undeploy()
        elif self.operation == "getVersion":
            return_value, output, error = self.get_rpm_version()
        elif self.operation in ["collectDebugLog"]:
            return_value, output, error = self.handle_other_assign_operations()
        else:
            return_value = -1
            output = "not implemented"
            error = "not implemented"
        return return_value, output, error

    def handle_install_rpm(self):
        return_value, output, error = self.execute_backend_script(self.json_input.get("assignInfo"))
        if return_value == 0:
            self.enable_disable_exassh(self.operation)
        return return_value, output, error

    def handle_deploy_undeploy(self):
        return_value, output, error = self.execute_backend_script(self.json_input.get("assignInfo"))
        if return_value == 0:
            self.enable_disable_exassh(self.operation)
        return return_value, output, error

    def handle_other_assign_operations(self):
        return self.execute_backend_script(self.json_input.get("assignInfo"))

    def handle_create_user(self):
        self.operation = "create_user"
        return self.execute_backend_script(self.json_input)

    def handle_delete_user(self):
        self.operation = "delete_user"
        return self.execute_backend_script(self.json_input)

    def get_status_for_idemtoken(self, idemtoken):
        data = None
        status_file_for_idemtoken = os.path.join(self.backend_status_path, idemtoken, "status")
        ebLogInfo(f"status file for idemtoken {idemtoken} is {status_file_for_idemtoken}")
        if os.path.exists(status_file_for_idemtoken):
            with open(status_file_for_idemtoken, 'r') as f:
                data = json.load(f)
        return data

    def check_status_for_idemtoken(self, aParams, idemtoken):
        data = self.get_status_for_idemtoken(idemtoken)

        if data:
            status = data["status"]
            return self.update_exacloud_db(int(status), data, aParams)
        return None

    def enable_disable_exassh(self, operation):
        if self.ebox.mCheckConfigOption("enable_block_opctl", "True"):
            if operation in ["deploy", "undeploy", "install"]:
                exakms = get_gcontext().mGetExaKms()
                dom0s, _, cells, switches = self.ebox.mReturnAllClusterHosts()
                hosts = dom0s + cells + switches
                for host in hosts:
                    entries = exakms.mSearchExaKmsEntries({"FQDN": host})
                    if entries:
                        for entry in entries:
                            if operation in ["deploy"]:
                                if "OPCTL_ENABLE" in entry.mGetKeyValueInfo():
                                    self.logger.info(f"ExaKms entry already with OPCTL_ENABLE: {entry}")
                                else:
                                    self.logger.info(f"Adding OPCTL_ENABLE to ExaKms entry: {entry}")
                                    entry.mGetKeyValueInfo()["OPCTL_ENABLE"] = "TRUE"
                                    exakms.mUpdateKeyValueInfo(entry)
                            if operation in ["undeploy"]:
                                if "OPCTL_ENABLE" in entry.mGetKeyValueInfo():
                                    self.logger.info(f"Deleting OPCTL_ENABLE to ExaKms entry: {entry}")
                                    entry.mGetKeyValueInfo().pop("OPCTL_ENABLE")
                                    exakms.mUpdateKeyValueInfo(entry)
                                else:
                                    self.logger.info(f"ExaKms entry already without OPCTL_ENABLE: {entry}")
