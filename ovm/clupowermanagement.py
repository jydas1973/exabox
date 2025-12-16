#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/clupowermanagement.py /main/1 2025/11/21 16:11:42 abysebas Exp $
#
# clupowermanagement.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      clupowermanagement.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    abysebas    11/13/25 - Enh 38299823 - PHASE 1: CPU CORE POWER SAVING -
#                           EXACLOUD CHANGES
#    abysebas    11/13/25 - Creation
#
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogWarn, ebLogTrace
from exabox.core.Error import ExacloudRuntimeError
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.utils.node import connect_to_host
import getpass
import time

STOP_SLEEP_TIME_FROM_ILOM = 330
START_SLEEP_TIME_FROM_ILOM = 330

class ebCluStartStopHostFromIlom(object):
    def __init__(self, aExaBoxCluCtrl):
        self.__ebox = aExaBoxCluCtrl
        
    def mExecuteIlomCmd(self, _cmds, IlomName):
        """
        This function executes the commands formulated on the iloms 
        and prints the console raw output.
        """
        _lastpwd = self.__ebox.mGetIlomPass()
        _ilomName = IlomName
        _maxTries = 3
        _tries    = 0
 
        while _tries < _maxTries:
    
            if _tries != 0:
                _lastpwd = getpass.getpass("Password for {0}: ".format(_ilomName))
    
            try:
                _node = exaBoxNode(get_gcontext())
                _node.mSetUser("root")
                _node.mSetPassword(_lastpwd)
    
                ebLogInfo("Try authentication: {0}".format(_ilomName))
                _node.mConnectAuthInteractive(aHost=_ilomName)
    
                _node.mExecuteCmdsAuthInteractive(_cmds)
                ebLogInfo("Read from socket: [{0}]".format(_node.mGetConsoleRawOutput()))
    
                _node.mDisconnect()
                break
    
            except Exception as e:
                ebLogInfo(f"Execution of Ilom command failed with exception: {str(e)}")
                _tries += 1
                    
    def mStopHostfromIlom(self, IlomName, aGracefulShutdown=True):
        _cmds = []
        if aGracefulShutdown:
            _cmds.append(['->', 'stop /System'])
        else:
            _cmds.append(['->', 'stop -f /System'])
        _cmds.append(['->', 'show /System'])
        self.mExecuteIlomCmd(_cmds, IlomName)
    
    def mStartHostfromIlom(self, IlomName):
        _cmds = []
        _cmds.append(['->', 'start /System'])
        _cmds.append(['->', 'show /System'])
        self.mExecuteIlomCmd(_cmds, IlomName)
        
    def mProcessHostLifecycle(self, ctx: dict):
        """
        Handles host lifecycle via ILOM for both 'start' and 'stop'.
        Accepts a dictionary with keys: host, ilom, operation, sleep_time, results_dict.
        """
        _host = ctx.get("host")
        _ilom = ctx.get("ilom")
        _operation = ctx.get("operation")
        _timeout = ctx.get("sleep_time")
        _results_dict = ctx.get("results_dict")

        if not all([_host, _ilom, _operation, _timeout is not None, _results_dict is not None]):
            msg = (f"Invalid lifecycle context: missing required keys or values. "
                   f"Context = {{'host': {_host}, 'ilom': {_ilom}, "
                   f"'operation': {_operation}, 'sleep_time': {_timeout}, 'results_dict': {_results_dict}}}")
            ebLogError(msg)
            raise ExacloudRuntimeError(0x0208, 0xA, msg)

        if _operation not in ("start", "stop"):
            msg = f"Failed: Invalid operation '{_operation}' for host {_host}"
            _results_dict[_host] = msg
            ebLogError(msg)
            raise ExacloudRuntimeError(0x0208, 0xA, msg)

        ebLogInfo(f"Operation {_operation} to be performed on host {_host} via ilom {_ilom}")

        # Trigger the appropriate ILOM action
        if _operation == "stop":
            self.mStopHostfromIlom(_ilom)
        else:
            self.mStartHostfromIlom(_ilom)

        # For start, give the host a short grace period to POST/boot before ping checks
        if _operation == "start":
            ebLogInfo(f"Waiting for the host {_host} to start up..")
            ebLogTrace("Waiting for 30 seconds first for the host to start up.")
            time.sleep(10)
        else:
            ebLogInfo(f"Waiting for the host {_host} to be shutdown..")

        _start_ts = time.time()

        # Desired ping state:
        #   stop  -> expect ping to be False (down)
        #   start -> expect ping to be True  (up)
        def _is_desired_state() -> bool:
            ping = self.__ebox.mPingHost(_host)
            return (not ping) if _operation == "stop" else ping

        while True:
            _elapsed = time.time() - _start_ts

            if _is_desired_state():
                _results_dict[_host] = "Success"
                if _operation == "stop":
                    ebLogInfo(
                        f"Host {_host} not pingeable after {_operation} from ilom and {_elapsed} seconds wait time")
                else:
                    ebLogInfo(f"Host {_host} pingeable after {_operation} from ilom and {_elapsed} seconds wait time")
                break

            if _elapsed > _timeout:
                msg = (f"Failed: Timeout while waiting for host {_host} to be "
                       f"{'stopped' if _operation == 'stop' else 'started'}.")
                _results_dict[_host] = msg
                ebLogError(msg)
                break

            ebLogTrace(f"Waiting for host {_host} to be "
                       f"{'stopped' if _operation == 'stop' else 'started'} : {_elapsed}")
            time.sleep(10)

    def mStopStartHostViaIlom(self, aOptions):
        if not aOptions or not aOptions.jsonconf:
            _err_str = "Please provide valid json input."
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        _json = aOptions.jsonconf
        _operation = _json.get("operation")
        _parallelprocess = bool(_json.get("parallel_process", False))
        _host_ilom_pair = _json.get("host_ilom_pair")

        if _operation not in ("start", "stop"):
            _err_str = "Invalid operation provided in the payload."
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        if not _host_ilom_pair:
            _err_str = "Host and Ilom information not present in input payload."
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        _sleep_time = STOP_SLEEP_TIME_FROM_ILOM if _operation == "stop" else START_SLEEP_TIME_FROM_ILOM
        _rc_final_result = {}

        if _parallelprocess:
            _items = list(_host_ilom_pair.items())
            for i in range(0, len(_items), 5):
                _batch_pairs = dict(_items[i:i + 5])
                _plist = ProcessManager()
                _rc_result = _plist.mGetManager().dict()

                for _host, _ilom in _batch_pairs.items():
                    ctx = {
                        "host": _host,
                        "ilom": _ilom,
                        "operation": _operation,
                        "sleep_time": _sleep_time,
                        "results_dict": _rc_result
                    }
                    _p = ProcessStructure(self.mProcessHostLifecycle, [ctx], _host)
                    _p.mSetMaxExecutionTime(10 * 60)
                    _p.mSetJoinTimeout(5)
                    _p.mSetLogTimeoutFx(ebLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()
                _rc_result = dict(_rc_result)

                for _host, _rcs in _rc_result.items():
                    ebLogInfo(f"{_operation.capitalize()} status for {_host} : {_rcs}")
                _rc_final_result.update(_rc_result)

        else:
            _rc_result = {}
            for _host, _ilom in _host_ilom_pair.items():
                ctx = {
                    "host": _host,
                    "ilom": _ilom,
                    "operation": _operation,
                    "sleep_time": _sleep_time,
                    "results_dict": _rc_result
                }
                self.mProcessHostLifecycle(ctx)

            for _host, _rcs in _rc_result.items():
                ebLogInfo(f"{_operation.capitalize()} status for {_host} : {_rcs}")
            _rc_final_result.update(_rc_result)

        return _rc_final_result

    def mHandleLowPowerMode(self, aOptions):
        """
        Handles low power mode operations via ILOM for all hosts in the payload.
        Supports parallel and serial execution.

        Validates:
        - lowpoweroperation must be one of: schedule, schedule_add, schedule_remove, schedule_clear, get_all
        - lowPowerModeSchedule must be present and well-formed for schedule/schedule_add/schedule_remove
        - lowPowerModeUntil = "NEVER" must not be combined with schedule
        - frequency values must be valid
        """
        if not aOptions or not aOptions.jsonconf:
            _err_str = "Please provide valid json input."
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        _json = aOptions.jsonconf
        _host_ilom_pair = _json.get("host_ilom_pair")
        _parallelprocess = bool(_json.get("parallel_process", False))
        _lowpoweroperation = _json.get("lowpoweroperation")
        _schedule = _json.get("lowPowerModeSchedule")
        _until = _json.get("lowPowerModeUntil")

        if not _host_ilom_pair:
            _err_str = "Host and Ilom information not present in input payload."
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        _valid_ops = {"schedule", "schedule_add", "schedule_remove", "schedule_clear", "get_all"}
        if _lowpoweroperation and _lowpoweroperation not in _valid_ops:
            _err_str = f"Invalid lowpoweroperation: {_lowpoweroperation}"
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        if _lowpoweroperation in {"schedule", "schedule_add", "schedule_remove"}:
            if not _schedule or not isinstance(_schedule, list) or len(_schedule) == 0:
                _err_str = f"lowPowerModeSchedule must be a non-empty list for operation {_lowpoweroperation}"
                ebLogError(_err_str)
                raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

            _valid_freqs = {"daily", "weekly", "monthly"}
            for entry in _schedule:
                if not all(k in entry for k in ("startTimestamp", "durationMinutes", "frequency")):
                    _err_str = f"Invalid schedule entry: {entry}"
                    ebLogError(_err_str)
                    raise ExacloudRuntimeError(0x0207, 0xA, _err_str)
                if entry["frequency"] not in _valid_freqs:
                    _err_str = f"Unsupported frequency '{entry['frequency']}' in schedule entry"
                    ebLogError(_err_str)
                    raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        if _lowpoweroperation == "schedule_clear" and _schedule:
            ebLogWarn("Schedule entries provided will be ignored due to 'schedule_clear' operation")

        if _until == "NEVER" and _schedule:
            _err_str = "lowPowerModeUntil=NEVER disables scheduling â€” lowPowerModeSchedule must be omitted"
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        _rc_final_result = {}

        if _parallelprocess:
            _items = list(_host_ilom_pair.items())
            for i in range(0, len(_items), 5):
                _batch_pairs = dict(_items[i:i + 5])
                _plist = ProcessManager()
                _rc_result = _plist.mGetManager().dict()

                for _host, _ilom in _batch_pairs.items():
                    ctx = {
                        "host": _host,
                        "ilom": _ilom,
                        "lowpoweroperation": _lowpoweroperation,
                        "lowPowerModeSchedule": _schedule,
                        "lowPowerModeUntil": _until,
                        "results_dict": _rc_result
                    }
                    _p = ProcessStructure(self.mProcessLowPowerMode, [ctx], _host)
                    _p.mSetMaxExecutionTime(10 * 60)
                    _p.mSetJoinTimeout(5)
                    _p.mSetLogTimeoutFx(ebLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()
                _rc_result = dict(_rc_result)

                for _host, _rcs in _rc_result.items():
                    ebLogInfo(f"Low power mode status for {_host} : {_rcs}")
                _rc_final_result.update(_rc_result)

        else:
            _rc_result = {}
            for _host, _ilom in _host_ilom_pair.items():
                ctx = {
                    "host": _host,
                    "ilom": _ilom,
                    "lowpoweroperation": _lowpoweroperation,
                    "lowPowerModeSchedule": _schedule,
                    "lowPowerModeUntil": _until,
                    "results_dict": _rc_result
                }
                self.mProcessLowPowerMode(ctx)

            for _host, _rcs in _rc_result.items():
                ebLogInfo(f"Low power mode status for {_host} : {_rcs}")
            _rc_final_result.update(_rc_result)

        return _rc_final_result

    def mProcessLowPowerMode(self, ctx: dict):
        _host = ctx.get("host")
        _ilom = ctx.get("ilom")
        _lowpoweroperation = ctx.get("lowpoweroperation")
        _schedule = ctx.get("lowPowerModeSchedule")
        _until = ctx.get("lowPowerModeUntil")
        _results_dict = ctx.get("results_dict")

        if not all([_host, _ilom, _results_dict is not None]):
            msg = f"Invalid context for low power mode: {_host}, {_ilom}, results_dict={_results_dict}"
            ebLogError(msg)
            _results_dict[_host] = f"Failed: {msg}"
            return

        ebLogInfo(f'DBMCLI services for lowpowermode on host: {_host}.')

        _cmds = []

        # Format schedule entries
        def fmt_schedules(schedules):
            return ",".join([
                f'(startTimestamp="{entry["startTimestamp"]}",durationMinutes={entry["durationMinutes"]},frequency={entry["frequency"]})'
                for entry in schedules
            ])

        # Handle lowPowerModeUntil
        if _until is not None:
            if _until == "NEVER":
                _cmds.append('dbmcli -e "ALTER DBSERVER lowPowerModeUntil=NEVER"')
            elif _until == "NULL":
                _cmds.append('dbmcli -e "ALTER DBSERVER lowPowerModeUntil=NULL"')
            elif _until in ("", None):
                _cmds.append('dbmcli -e "ALTER DBSERVER lowPowerModeUntil=\'\'"')
            else:
                _cmds.append(f'dbmcli -e "ALTER DBSERVER lowPowerModeUntil={_until}"')

        # Handle lowpoweroperation
        if _lowpoweroperation:
            if _lowpoweroperation == "schedule":
                _cmds.append(f'dbmcli -e "ALTER DBSERVER lowPowerModeSchedule=({fmt_schedules(_schedule)})"')
            elif _lowpoweroperation == "schedule_add":
                _cmds.append(f'dbmcli -e "ALTER DBSERVER lowPowerModeSchedule+=({fmt_schedules(_schedule)})"')
            elif _lowpoweroperation == "schedule_remove":
                _cmds.append(f'dbmcli -e "ALTER DBSERVER lowPowerModeSchedule-=({fmt_schedules(_schedule)})"')
            elif _lowpoweroperation == "schedule_clear":
                _cmds.append('dbmcli -e "ALTER DBSERVER lowPowerModeSchedule=NULL"')
            elif _lowpoweroperation == "get_all":
                _cmds.append('dbmcli -e "LIST DBSERVER attributes lowPowerModeSchedule,lowPowerModeUntil"')

        try:
            with connect_to_host(_host, get_gcontext()) as _dbnode:
                for _cmd in _cmds:
                    ebLogInfo(f"Executing on {_host}: {_cmd}")
                    _in, _out, _err = _dbnode.mExecuteCmd(_cmd)
                    _exit_code = _dbnode.mGetCmdExitStatus()
                    _output = _out.readlines()

                    if _exit_code != 0:
                        msg = f"Failed: Command '{_cmd}' on {_host} exited with code {_exit_code}. Error: {' '.join(_err.readlines()).strip()}"
                        ebLogError(msg)
                        _results_dict[_host] = msg
                        break
                    else:
                        _clean_output = ' '.join(_output).strip()
                        ebLogInfo(f"Command succeeded on {_host}: {_cmd}")
                        _results_dict[_host] = f"Success: {_clean_output}"
        except Exception as e:
            msg = f"Failed: Exception while applying low power mode on {_host}: {str(e)}"
            ebLogError(msg)
            _results_dict[_host] = msg

