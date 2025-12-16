#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/tools/profiling/stepwise.py /main/5 2025/04/23 14:38:26 abflores Exp $
#
# stepwise.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      stepwise.py - Profiler implementation for ExaCloud CS and DS.
#
#    DESCRIPTION
#      This module contains a set of functions to log useful profiling
#      information recolected during CS and DS.
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    abflores    04/07/25 - Bug 37473868: Fix marker files logging
#    jesandov    09/28/23 - 35141262: Profiler enhancement to use DB tables,
#    scoral      07/05/21 - Creation
#

from typing import Any, Union, Optional, Callable, Dict, List, TYPE_CHECKING
import time, os
import re
import json
import datetime
from threading import Thread
from itertools import takewhile
from exabox.utils.common import tails
from exabox.tools.profiling.profiler import consume_profiling_data
from exabox.tools.profiling.profiler_info import ProfilerInfo
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.core.Context import get_gcontext
from exabox.agent.ebJobRequest import ebJobRequest, nsOpt

if TYPE_CHECKING:
    from exabox.core.Node import exaBoxNode
    from exabox.ovm.csstep.cs_driver import csDriver
    from exabox.ovm.clucontrol import exaBoxCluCtrl
else:
    exaBoxNode = object # pylint: disable=invalid-name
    csDriver = object # pylint: disable=invalid-name
    exaBoxCluCtrl = object # pylint: disable=invalid-name



###############################################################################
### Constants
###############################################################################

DATETIME_FMT: str = '%Y-%m-%d %H:%M:%S'



###############################################################################
### Common argument stealers
###############################################################################

def steal_hostname(node: exaBoxNode, *args, **kwargs) -> Dict[str, str]:
    """
    Preferred argument stealer for mConnect and mDisconnect.

    This function steals the hostname of a node and stores it into a singleton
    dictionary which key is 'hostname'.

    :param node: exaBoxNode from which to get the hostname.
    :returns: Dict with the node hostname.
    """
    return { 'hostname': node.mGetHostname() }


def steal_hostname_cmd(
    node: exaBoxNode,
    cmd: str,
    *args,
    **kwargs
) -> Dict[str, str]:
    """
    Preferred argument stealer for mExecuteCmd-like functions.

    This function steals the hostname of the node and the command that is
    intended to be run and stores them into a dictionary with keys 'hostname'
    and 'cmd' respectively.

    :param node: exaBoxNode from which to get the hostname.
    :param cmd: str to e copied into the returned dictionary.
    :returns: Dict with the node hostname and the given string.
    """
    return {
        'hostname': node.mGetHostname(),
        'cmd': "*****" if "pass" in cmd else cmd
    }

def steal_hostname_file_copied(
    node: exaBoxNode,
    local_file: str,
    remote_file: str,
    retries: int = 0
) -> Dict[str, Union[str, int]]:
    """
    Preferred argument stealer for mCopyFile.

    This function steals the hostname of the node in which the file is
    intended to be copied, the remote file path where it is going to be copied
    and the size in bytes of the file and stores them into a dictionary with
    keys 'hostname', 'remote_file' and 'size_bytes' respectively.

    :param node: exaBoxNode from which to get the hostname.
    :param local_file: str indicating the local file to be copied.
    :param remote_file: str indicating the remote file path.
    :returns: Dict with the hostname, remote path and size in bytes of the
              file to be copied.
    """
    size_bytes: int = 0
    try:
        size_bytes = os.path.getsize(local_file)
    except FileNotFoundError:
        pass
    return {
        'hostname': node.mGetHostname(),
        'remote_file': remote_file,
        'size_bytes': size_bytes
    }


def steal_steplist(
    cs_driver: csDriver,
    step_list: List[str],
    *args,
    **kwargs
) -> Dict[str, str]:
    """
    Preferred argument stealer for mHandleStep.

    This function takes the step name and stores it into a singleton
    dictionary which key is 'step_name'.

    :param cs_driver: csDriver object, ignored.
    :param step_list: List from which to return the first element.
    :returns: Dict with the first element of the given list.
    """
    return { 'step_name': step_list[0] }


def steal_step_substep(
    clu_ctrl: exaBoxCluCtrl,
    status: Union[bool, int],
    step: str,
    *args,
    **kwargs
) -> Dict[str, Union[str, int, bool]]:
    """
    Preferred argument stealer for mUpdateStatus-like functions.

    This function steals the step name and either the substep commentary or
    the oeda substep if the substep commentary does not exist in the kwargs.
    
    :param clu_ctrl: exaBoxCluCtrl object, ignored.
    :param status: A string ignored.
    :param step: A string with the current CS or DS step.
    :returns: Dict with the current step and substep information.
    """
    return {
        'step': step,
        'substep_name': kwargs.get('aComment', kwargs.get('oedaStep', '')),
        'is_oeda': 'oedaStep' in kwargs
    }



###############################################################################
### Common profiling data logging functions
###############################################################################

def log_exec_time(step: str, t0: float, tf: float, padding: str=''):
    """
    Logs a formatted start and finish time of a given process.

    :param step: Step name.
    :param t0: Unix time of the starting time of the step.
    :param ft: Unix time of the finish time of the step.
    :param padding: String printed at the beginning of every logged line.
    """
    start_time_str = time.strftime(DATETIME_FMT, time.localtime(t0))
    finish_time_str = time.strftime(DATETIME_FMT, time.localtime(tf))
    step_exec_time = tf - t0

    ebLogInfo('')
    ebLogInfo(f"{padding}//////// {step} ////////")
    ebLogInfo(f"{padding}Start time: {start_time_str}")
    ebLogInfo(f"{padding}Finish time: {finish_time_str}")
    ebLogInfo(
        f"{padding}Total execution time: "
        f"{int(step_exec_time / 3600)} hours, "
        f"{int(step_exec_time / 60 % 60)} minutes, "
        f"{step_exec_time % 60} seconds."
    )


def create_profile_info(
        aStepName,
        aSection,
        aStart,
        aEnd,
        aOperationId,
        aWorkflowId,
        aExaunitId,
        aCmdType,
        aDetails,
        aUndo,
        aRawDate=True
    ):

    _pi = ProfilerInfo()

    _pi.mSetStep(aStepName)
    _pi.mSetProfilerType(aSection)

    _start = aStart
    _end = aEnd

    if aRawDate:
        _start = time.strftime(DATETIME_FMT, time.localtime(aStart))
        _end = time.strftime(DATETIME_FMT, time.localtime(aEnd))

    _pi.mSetStartTime(_start)
    _pi.mSetEndTime(_end)

    _pi.mSetOperationId(aOperationId)
    _pi.mSetWorkflowId(aWorkflowId)
    _pi.mSetExaunitId(aExaunitId)
    _pi.mSetCmdType(aCmdType)

    # Create details
    _pi.mSetDetails(str(json.dumps(aDetails)).strip())

    # Calculate elapsed

    if aUndo:
        _pi.mSetExecType("UNDO")
    else:
        _pi.mSetExecType("DO")

    if "oeda" in str(json.dumps(aDetails)).lower():
        _pi.mSetComponent("OEDA")
    else:
        _pi.mSetComponent("EXACLOUD")

    _start = datetime.datetime.strptime(_start, DATETIME_FMT)
    _end = datetime.datetime.strptime(_end, DATETIME_FMT)
    _spend = _end - _start
    _pi.mSetElapsed(str(_spend))

    return _pi

def log_profiled_data(steps: List[str], get_oeda_step: Callable[[int], str]):
    """
    Logs a formatted summary of the profiled data from a Create Service or a
    Delete Service.

    This includes the start and finish timestamps and execution time of every
    step and substep (including OEDA substeps) of the operation and from the
    longest command run for each step.

    Also the number of connections opened and closed and executed remote
    commands.

    :param steps: A list of strings naming the CS or DS steps run.
    :param get_oeda_step: A function that returns a string of the given OEDA
                          substep.
    """

    def log_banner(message: str):
        ebLogInfo('')
        ebLogInfo('')
        ebLogInfo('')
        ebLogInfo(80 * '*')
        ebLogInfo(f"*** {message.upper()}")
        ebLogInfo(80 * '*')
        ebLogInfo('')

    def hr_size(b: int) -> str:
        preferred_suffix = "T"
        for suffix in ["", "K", "M", "G"]:
            if b / 1024 > 1:
                b /= 1024
                continue
            preferred_suffix = suffix
            break
        return f"{b}{preferred_suffix}B"


    # Prepare the data we're going to log.
    TStepData = Dict[
        str, # start | finish | connections | substeps | cmds | files
        Union[
            float,      # start | finish
            List[int],  # connections
            List[       # substeps | cmds | files
                Dict[
                    # substeps: substep? | start? | finish?
                    # cmds: cmd | hostname | start | finish
                    # files: remote_file | size_bytes | hostname | start |
                    #        finish
                    str,
                    Union[
                        str,    # substep | cmd | hostname | remote_file
                        float,  # start | finish
                        int     # size_bytes
                    ]
                ]
            ]
        ]
    ]
    steps_data: Dict[str, TStepData] = {
        step: {
            'connections': [0, 0],
            'cmds': [],
            'substeps': [],
            'files': []
        } for step in steps
    }


    def get_steps_exec_time(
        thread: Thread,
        func: Callable[..., Any],
        exec_start_time: float,
        exec_data: Dict[str, Union[float, Exception, Any]]
    ):
        for step in steps:
            if 'args' not in exec_data or \
                'step_name' not in exec_data['args'] or \
                exec_data['args']['step_name'] != step:
                continue

            steps_data[step]['start'] = exec_start_time
            steps_data[step]['finish'] = exec_data['finished']
            break


    def get_step_executed(timestamp: float) -> Optional[str]:
        result: Optional[str] = None
        for step in steps:
            if timestamp < steps_data[step]['finish']:
                result = step
                break
        if result and timestamp < steps_data[steps[0]]['start']:
            return None
        return result


    def get_connections_count(
        thread: Thread,
        func: Callable[..., Any],
        exec_start_time: float,
        exec_data: Dict[str, Union[float, Exception, Any]]
    ):
        step: Optional[str] = get_step_executed(exec_start_time)
        if not step:
            return

        if 'mConnect' in func.__name__:
            steps_data[step]['connections'][0] += 1
        elif 'mDisconnect' in func.__name__:
            steps_data[step]['connections'][1] += 1



    def store_data_db():

        # Avoid cyclical dependency
        from exabox.core.DBStore import ebGetDefaultDB

        _db = ebGetDefaultDB()

        _sections = {
            "cmds" : [
                "cmd",
                "hostname"
            ],
            "substeps": [
                "substep"
            ],
            "files": [
                "remote_file",
                "hostname",
                "size_bytes"
            ]
        }


        _operationId = ""
        if get_gcontext().mCheckRegEntry("operation_id"):
            _operationId = get_gcontext().mGetRegEntry("operation_id")

        _workflowId = ""
        if get_gcontext().mCheckRegEntry("workflow_id"):
            _workflowId = get_gcontext().mGetRegEntry("workflow_id")

        _exaunitId = ""
        if get_gcontext().mCheckRegEntry("exaunit_id"):
            _exaunitId = get_gcontext().mGetRegEntry("exaunit_id")

        _undo = ""
        if get_gcontext().mCheckRegEntry("undo"):
            _undo = get_gcontext().mGetRegEntry("undo")

        _cmdType = ""
        if _operationId:
            _job = ebJobRequest(None,{}, aDB=_db)
            _job.mLoadRequestFromDB(_operationId)
            _cmdType = _job.mGetCmdType()

        for stepname, step_data in steps_data.items():

            # Register main step
            _pi = create_profile_info(
                stepname,
                "step",
                step_data["start"],
                step_data["finish"],
                _operationId,
                _workflowId,
                _exaunitId,
                _cmdType,
                {},
                _undo,
            )
            _db.mInsertProfiler(_pi)

            for _section, _details in _sections.items():
                for _instance in step_data[_section]:

                    if not "start" in _instance or \
                       not "finish" in _instance:
                        continue

                    _details_parsed = {}
                    for _detail in _details:
                        _details_parsed[_detail] = _instance[_detail]

                    # Register individual steps
                    _pi = create_profile_info(
                        stepname,
                        _section,
                        _instance["start"],
                        _instance["finish"],
                        _operationId,
                        _workflowId,
                        _exaunitId,
                        _cmdType,
                        _details_parsed,
                        _undo,
                    )

                    if _section == "cmds":

                        # Commands that takes more than 1s to complete
                        _delta = datetime.datetime.strptime(_pi.mGetElapsed(),"%H:%M:%S")
                        _delta = datetime.timedelta(
                            hours=_delta.hour,
                            minutes=_delta.minute,
                            seconds=_delta.second
                        )

                        if _delta > datetime.timedelta(seconds=1):
                            _db.mInsertProfiler(_pi)

                    else:

                        # Add extra record for Exacloud step
                        if _pi.mGetComponent() == "OEDA":
                            _db.mInsertProfiler(_pi)
                            _pi.mSetComponent("EXACLOUD")

                        _db.mInsertProfiler(_pi)

    def get_substeps_exec_time(
        thread: Thread,
        func: Callable[..., Any],
        exec_start_time: float,
        exec_data: Dict[str, Union[float, Exception, Any]]
    ):
        step: Optional[str] = get_step_executed(exec_start_time)
        if not step:
            return
        
        if 'args' in exec_data and 'substep_name' in exec_data['args']:
            if exec_data['args']['is_oeda']:
                exec_data['args']['substep_name'] = \
                    f"OEDA step {exec_data['args']['substep_name']}: " + \
                    get_oeda_step(exec_data['args']['substep_name'])

            steps_data[step]['substeps'].append({
                'substep': exec_data['args']['substep_name'],
                'start': exec_start_time
            })

        if 'mLogStepElapsedTime' in func.__name__:
            for substep in steps_data[step]['substeps']:
                if re.search(substep["substep"].lower(), exec_data["args"]["step"].lower()): 
                    substep['finish'] = exec_data['finished']
              
    def get_remote_cmds_executed(
        thread: Thread,
        func: Callable[..., Any],
        exec_start_time: float,
        exec_data: Dict[str, Union[float, Exception, Any]]
    ):
        if 'mExecuteCmd' not in func.__name__:
            return

        step: Optional[str] = get_step_executed(exec_start_time)
        if not step:
            return

        steps_data[step]['cmds'].append({
            'cmd': exec_data['args']['cmd'],
            'hostname': exec_data['args']['hostname'],
            'start': exec_start_time,
            'finish': exec_data['finished']
        })


    def get_files_copied(
        thread: Thread,
        func: Callable[..., Any],
        exec_start_time: float,
        exec_data: Dict[str, Union[float, Exception, Any]]
    ):
        if 'mCopyFile' not in func.__name__:
            return

        step: Optional[str] = get_step_executed(exec_start_time)
        if not step:
            return

        steps_data[step]['files'].append({
            'remote_file': exec_data['args']['remote_file'],
            'hostname': exec_data['args']['hostname'],
            'size_bytes': exec_data['args']['size_bytes'],
            'start': exec_start_time,
            'finish': exec_data['finished']
        })


    # Compute everything and log the summary
    consume_profiling_data(get_steps_exec_time)
    consume_profiling_data(get_connections_count)
    consume_profiling_data(get_substeps_exec_time)
    consume_profiling_data(get_remote_cmds_executed)
    consume_profiling_data(get_files_copied)

    if len(steps) > 1:
        log_banner('global summary')
        log_exec_time(
            f"{'Create' if 'PRE' in steps[0] else 'Delete'} service",
            steps_data[steps[0]]['start'],
            steps_data[steps[-1]]['finish']
        )

        cmds: int = 0
        connections: List[int] = [0, 0]
        files_copied: int = 0
        bytes_copied: int = 0
        copy_time_secs: int = 0
        for step_data in steps_data.values():
            cmds += len(step_data['cmds'])
            connections[0] += step_data['connections'][0]
            connections[1] += step_data['connections'][1]
            files_copied += len(step_data['files'])
            for file_data in step_data['files']:
                bytes_copied += file_data['size_bytes']
                copy_time_secs += file_data['finish'] - file_data['start']

        ebLogInfo(f"Connections opened and closed: {connections}")
        ebLogInfo(f"Remote commands run: {cmds}")
        ebLogInfo(
            f"Copied {hr_size(bytes_copied)} from {files_copied} files in "
            f"{int(copy_time_secs / 3600)} hours, "
            f"{int(copy_time_secs / 60 % 60)} minutes, "
            f"{copy_time_secs % 60} seconds."
        )


    log_banner('stepwise time execution summary')
    for step in steps:
        step_data: TStepData = steps_data[step]
        step_data['cmds'].sort(key=lambda cmd: cmd['finish'] - cmd['start'])
        files_copied: int = len(step_data['files'])
        bytes_copied: int = 0
        copy_time_secs: int = 0
        for file_data in step_data['files']:
            bytes_copied += file_data['size_bytes']
            copy_time_secs += file_data['finish'] - file_data['start']

        log_exec_time(step, step_data['start'], step_data['finish'])
        ebLogInfo(f"Connections opened and closed: {step_data['connections']}")
        ebLogInfo(f"Remote commands run: {len(step_data['cmds'])}")
        ebLogInfo(
            f"Copied {hr_size(bytes_copied)} from {files_copied} files in "
            f"{int(copy_time_secs / 3600)} hours, "
            f"{int(copy_time_secs / 60 % 60)} minutes, "
            f"{copy_time_secs % 60} seconds."
        )

        if not step_data['cmds']:
            continue

        ebLogInfo(f"Longest remote command:")
        longest_cmd = step_data['cmds'][-1]
        log_exec_time(
            longest_cmd['cmd'],
            longest_cmd['start'],
            longest_cmd['finish'],
            '    '
        )
        ebLogInfo(f"    Hostname: {longest_cmd['hostname']}")


    log_banner('substeps time execution summary')
    for step in steps:

        ebLogInfo('')
        ebLogInfo(f"//////// {step} ////////")

        step_data: TStepData = steps_data[step]
        step_data['substeps'].sort(key=lambda substep:
            substep.get('start', 0) + substep.get('finish', 0)
        )

        for substeps in tails(step_data['substeps']):
            substep: Dict[str, Union[str, float]] = next(substeps)
            if not substep.get("substep"):
                continue

            finish_mark = None
            if "finish" in substep:
                finish_mark =  substep["finish"]
            
            if not finish_mark:
                ebLogInfo('')
                ebLogWarn(
                    f"    Substep `{substep['substep']}` never finished!, "
                    "Please check."
                )
                continue

            log_exec_time(
                substep['substep'],
                substep['start'],
                substep["finish"],
                '    '
            )

        ebLogInfo('')
        ebLogInfo(160 * '-')

    store_data_db()

# end of file
