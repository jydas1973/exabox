#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_manage_service.py /main/1 2025/11/27 18:10:45 jepalomi Exp $
#
# handler_manage_service.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
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
#    jepalomi    11/12/25 - Bug 38529119 - EXACLOUD API TO SUPPORT START/STOP
#                           SYSLENS ON DOM0S
#    jepalomi    11/12/25 - Creation
#

import os
import time

from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo
from exabox.utils.node import (connect_to_host, node_exec_cmd_check, node_exec_cmd)

from exabox.jsondispatch.jsonhandler import JDHandler

class ManageServiceHandler(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/manage_service.json"))
        
    def mExecute(self) -> tuple:
        """
        Driver func for running a service command on the specified hosts

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """
        _rc = 0
        _response = {}

        systemctl = "/usr/bin/systemctl"
        rpm = "/usr/bin/rpm"

        task_cmds = {
            'start': f'{systemctl} start {{service}}',
            'stop': f'{systemctl} stop {{service}}',
            'status': f'{systemctl} is-active {{service}}',
            'version': f'{rpm} -q {{service}}',
        }
        
        _jconf = self.mGetOptions().jsonconf
        task = _jconf["task"]
        service = _jconf["service"]
        node_results = []

        ebLogInfo(f"Executing {task} task on service {service} for hosts: {_jconf['host_nodes']}")

        for host in _jconf["host_nodes"]:
            node_result = self.mExecServiceCmd(host, service, task, task_cmds)
            node_results.append(node_result)

        _response = {
            "service": service,
            "task": task,
            "node_task_status": node_results
        }

        return (_rc, _response)

    @staticmethod
    def mExecServiceCmd(aHostname: str, aService: str, aTask: str, aTaskCmds: dict) -> dict:
        """
        Execute a service management task on a remote host.

        Args:
            aHostname (str): Target host.
            aService   (str): Systemd service name.
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
                node_exec_cmd_check(_node, f"/usr/bin/systemctl cat {aService}")

                # Call handler for task
                if aTask in ("start", "stop"):
                    res = ManageServiceHandler._handle_start_stop_task(
                        _node, aHostname, aService, aTask, aTaskCmds
                    )
                elif aTask == "status":
                    res = ManageServiceHandler._handle_status_task(
                        _node, aHostname, aService, aTaskCmds
                    )
                else:
                    raise ValueError(
                        f"Invalid task '{aTask}' for service {aService} on host {aHostname}"
                    )

        except Exception as e:
            # Use default res since handler result was never assigned
            res["error"] = str(e)
            res["message"] = (
                f"Exception while executing {aTask} task on service {aService} "
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
    def _handle_start_stop_task(aNode, aHostname: str, aService: str, aTask: str, aTaskCmds: dict) -> dict:
        """
        Handle a start or stop operation for a systemd service.

        Args:
            aNode: Remote execution context.
            aHostname (str): Target host.
            aService (str): Systemd service name.
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
        base_cmd = aTaskCmds[aTask].format(service=aService)
        node_exec_cmd(aNode, base_cmd)

        # Wait for service to reach expected state
        max_timeout = 300      # 5 minutes
        interval = 5
        elapsed_time = 0

        time.sleep(interval)   # let service settle

        while elapsed_time < max_timeout:
            _, status_val, _ = node_exec_cmd(
                aNode, aTaskCmds["status"].format(service=aService)
            )
            status_val = status_val.strip()

            # success conditions
            if (aTask == "start" and status_val == "active") or \
               (aTask == "stop" and status_val != "active"):

                res["task_status"] = "success"
                res["message"] = f"{aService} {aTask} successful for host {aHostname}"
                return res

            # Immediate failure states
            if status_val in ("failed", "unknown"):
                break

            time.sleep(interval)
            elapsed_time += interval

        _, full_status, _ = node_exec_cmd(aNode, f"/usr/bin/systemctl status {aService}")
        _, journal_out, _ = node_exec_cmd(
            aNode,
            f'''/usr/bin/journalctl -u {aService} --since "5 min ago" --no-pager -l --full | tail -20'''
        )

        combined_error = (
            full_status +
            "\n----Recent Log Entries----\n" +
            journal_out
        )

        res["message"] = f"{aService} {aTask} failed for host {aHostname}"
        res["error"] = (
            combined_error.strip()
            if combined_error.strip()
            else f"Task failed with no error message. Service status: {status_val}."
        )

        ebLogError(res["message"])
        ebLogError(res["error"])

        return res


    @staticmethod
    def _handle_status_task(aNode, aHostname: str, aService: str, aTaskCmds: dict) -> dict:
        """
        Retrieve the current status and version of a systemd service.

        Args:
            aNode: Remote execution context.
            aHostname (str): Target host.
            aService (str): Systemd service name.
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
        _, status_val, status_err = node_exec_cmd(
            aNode, aTaskCmds["status"].format(service=aService)
        )
        # Get version
        _, ver_val, ver_err = node_exec_cmd(
            aNode, aTaskCmds["version"].format(service=aService)
        )

        res["status"] = status_val.strip()
        res["version"] = ver_val.strip()

        if not status_val or not ver_val:
            res["error"] = status_err or ver_err
            res["message"] = (
                f"Failed to obtain status and version for service {aService} "
                f"on host {aHostname}"
            )
            ebLogError(res["message"])
            ebLogError(res["error"])
            return res

        # SUCCESS
        res["task_status"] = "success"
        res["message"] = (
            f"Status and version retrieved successfully for service {aService} "
            f"on host {aHostname}"
        )

        ebLogInfo(res["message"])
        return res