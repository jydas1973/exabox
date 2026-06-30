#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_manage_service.py /main/1 2025/11/27 18:10:45 jepalomi Exp $
#
# handler_manage_service.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      handler_manage_service.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jepalomi    04/28/26 - Bug 39263021 - Fix security findings
#    jepalomi    11/12/25 - Bug 38529119 - EXACLOUD API TO SUPPORT START/STOP
#                           SYSLENS ON DOM0S
#    jepalomi    11/12/25 - Creation
#

import os
import time

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo
from exabox.utils.node import (connect_to_host, node_exec_cmd_check, node_exec_cmd)

from exabox.jsondispatch.jsonhandler import JDHandler

class ManageServiceHandler(JDHandler):
    TRUSTED_SERVICES = {
        "syslens": {
            "unit": "syslens",
            "package": "syslens",
        },
    }

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/manage_service.json"))

    @classmethod
    def mGetTrustedServiceMeta(cls, aRequestedService: str) -> dict:
        """
        Resolve the request-facing service name to trusted internal metadata.

        Only explicitly supported services are allowed to flow into command
        construction.
        """
        _service_meta = cls.TRUSTED_SERVICES.get(aRequestedService)
        if _service_meta is None:
            raise ExacloudRuntimeError(
                0x00, 0x0,
                f"Unsupported service '{aRequestedService}' for manage_service endpoint"
            )

        return _service_meta

    @staticmethod
    def mBuildTaskCmds(aServiceMeta: dict) -> dict:
        """
        Build command strings from trusted service metadata only.
        """
        _systemctl = "/usr/bin/systemctl"
        _rpm = "/usr/bin/rpm"
        _service_unit = aServiceMeta["unit"]
        _service_pkg = aServiceMeta["package"]

        return {
            "exists": f"{_systemctl} cat {_service_unit}",
            "start": f"{_systemctl} start {_service_unit}",
            "stop": f"{_systemctl} stop {_service_unit}",
            "status": f"{_systemctl} is-active {_service_unit}",
            "full_status": f"{_systemctl} status {_service_unit}",
            "version": f"{_rpm} -q {_service_pkg}",
            "recent_logs": (
                f'''/usr/bin/journalctl -u {_service_unit} --since "5 min ago" '''
                f'''--no-pager -l --full -n 20'''
            ),
        }
        
    def mExecute(self) -> tuple:
        """
        Driver func for running a service command on the specified hosts

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """
        _rc = 0
        _response = {}

        _jconf = self.mGetOptions().jsonconf
        # "operation" is part of the public request contract and is kept for
        # API compatibility. It is currently unused by the handler logic but
        # reserved for future behavior.
        _operation = _jconf["operation"]
        task = _jconf["task"]
        requested_service = _jconf["service"]
        service_meta = self.mGetTrustedServiceMeta(requested_service)
        task_cmds = self.mBuildTaskCmds(service_meta)
        node_results = []

        ebLogInfo(
            f"Executing {task} task on service {requested_service} for hosts: "
            f"{_jconf['host_nodes']}"
        )

        for host in _jconf["host_nodes"]:
            node_result = self.mExecServiceCmd(host, requested_service, task, task_cmds)
            node_results.append(node_result)

        _response = {
            "service": requested_service,
            "task": task,
            "node_task_status": node_results
        }

        return (_rc, _response)

    @staticmethod
    def mExecServiceCmd(aHostname: str, aServiceLabel: str, aTask: str, aTaskCmds: dict) -> dict:
        """
        Execute a service management task on a remote host.

        Args:
            aHostname (str): Target host.
            aServiceLabel (str): Request-facing service name.
            aTask      (str): Task to perform ("start", "stop", "status").
            aTaskCmds  (dict): Mapping of task names to command templates.

        Returns:
            dict: Result containing task status, message, error, and task output.
        """

        # Default result
        res = {
            "task_status": "failure",
            "hostname": aHostname,
            "error": "",
            "message": "",
        }

        try:
            with connect_to_host(aHostname, get_gcontext()) as _node:

                # Validate service exists
                node_exec_cmd_check(_node, aTaskCmds["exists"])

                # Call handler for task
                if aTask in ("start", "stop"):
                    res = ManageServiceHandler._handle_start_stop_task(
                        _node, aHostname, aServiceLabel, aTask, aTaskCmds
                    )
                elif aTask == "status":
                    res = ManageServiceHandler._handle_status_task(
                        _node, aHostname, aServiceLabel, aTaskCmds
                    )
                else:
                    raise ValueError(
                        f"Invalid task '{aTask}' for service {aServiceLabel} on host {aHostname}"
                    )

        except Exception as e:
            # Use default res since handler result was never assigned
            res["error"] = str(e)
            res["message"] = (
                f"Exception while executing {aTask} task on service {aServiceLabel} "
                f"for host {aHostname}"
            )

            ebLogError(res["message"])
            ebLogError(res["error"])

            # Status task requires these fields
            if aTask == "status":
                res.setdefault("status", "")
                res.setdefault("version", "")

        return res


    @staticmethod
    def _handle_start_stop_task(aNode, aHostname: str, aServiceLabel: str, aTask: str, aTaskCmds: dict) -> dict:
        """
        Handle a start or stop operation for a systemd service.

        Args:
            aNode: Remote execution context.
            aHostname (str): Target host.
            aServiceLabel (str): Request-facing service name.
            aTask (str): Operation ("start" or "stop").
            aTaskCmds (dict): Command templates for each operation.

        Returns:
            dict: Result describing success/failure, message, and error info.
        """

        res = {
            "task_status": "failure",
            "hostname": aHostname,
            "error": "",
            "message": "",
        }

        # Execute the start/stop command
        node_exec_cmd(aNode, aTaskCmds[aTask])

        # Wait for service to reach expected state
        max_timeout = 300      # 5 minutes
        interval = 5
        elapsed_time = 0

        time.sleep(interval)   # let service settle

        while elapsed_time < max_timeout:
            _, status_val, _ = node_exec_cmd(aNode, aTaskCmds["status"])
            status_val = status_val.strip()

            # Immediate failure states
            if status_val in ("failed", "unknown"):
                break

            # success conditions
            if (aTask == "start" and status_val == "active") or \
               (aTask == "stop" and status_val != "active"):

                res["task_status"] = "success"
                res["message"] = f"{aServiceLabel} {aTask} successful for host {aHostname}"
                return res

            time.sleep(interval)
            elapsed_time += interval

        _, full_status, _ = node_exec_cmd(aNode, aTaskCmds["full_status"])
        _, journal_out, _ = node_exec_cmd(aNode, aTaskCmds["recent_logs"])

        combined_error = (
            full_status +
            "\n----Recent Log Entries----\n" +
            journal_out
        )

        res["message"] = f"{aServiceLabel} {aTask} failed for host {aHostname}"
        res["error"] = (
            combined_error.strip()
            if combined_error.strip()
            else f"Task failed with no error message. Service status: {status_val}."
        )

        ebLogError(res["message"])
        ebLogError(res["error"])

        return res


    @staticmethod
    def _handle_status_task(aNode, aHostname: str, aServiceLabel: str, aTaskCmds: dict) -> dict:
        """
        Retrieve the current status and version of a systemd service.

        Args:
            aNode: Remote execution context.
            aHostname (str): Target host.
            aServiceLabel (str): Request-facing service name.
            aTaskCmds (dict): Command templates for "status" and "version".

        Returns:
            dict: Result containing task status, message, error, service status, and version.
        """

        res = {
            "task_status": "failure",
            "hostname": aHostname,
            "error": "",
            "message": "",
            "status": "",
            "version": "",
        }

        # Get service status
        _, status_val, status_err = node_exec_cmd(aNode, aTaskCmds["status"])
        # Get version
        _, ver_val, ver_err = node_exec_cmd(aNode, aTaskCmds["version"])

        res["status"] = status_val.strip()
        res["version"] = ver_val.strip()

        if not status_val or not ver_val:
            res["error"] = status_err or ver_err
            res["message"] = (
                f"Failed to obtain status and version for service {aServiceLabel} "
                f"on host {aHostname}"
            )
            ebLogError(res["message"])
            ebLogError(res["error"])
            return res

        # SUCCESS
        res["task_status"] = "success"
        res["message"] = (
            f"Status and version retrieved successfully for service {aServiceLabel} "
            f"on host {aHostname}"
        )

        ebLogInfo(res["message"])
        return res
