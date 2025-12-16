#
# $Header: ecs/exacloud/exabox/utils/node.py /main/25 2025/10/02 14:47:45 jesandov Exp $
#
# node.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      node.py - Auxiliary functions related to remote nodes.
#
#    DESCRIPTION
#      Auxiliary functions for remote node operations.
#
#    NOTES
#      - If you change this file, please make sure lines are no longer than 80
#        characters (including newline) and it passes pylint, mypy and flake8
#        with all the default checks enabled.
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    09/30/25 - 36206155: Add log of strerr and stdout on error
#    aypaul      09/17/25 - Bug#38440580 Revert changes for add defunct childs
#                           to be added for corrupt workers.
#    aypaul      07/25/25 - Bug#38202055 Catch AccessDenied exception while
#                           trying to kill defunct child processes from worker.
#    ririgoye    06/02/25 - Bug 38014410 - Removing changes from 37588295
#    aypaul      05/21/25 - Bug#37948804 Enable killing of worker processes
#                           with defunct pids in case agent delegation is
#                           enabled.
#    ririgoye    04/28/25 - Bug 37588295 - EXACLOUD SOP LOCAL REMOTE EXECUTION
#                           WILL HANG ON LARGE OUTPUT
#    jfsaldan    10/30/24 - Bug 37207274 -
#                           EXACS:24.4.1:241021.0914:MULTI-VM:PARALLEL VM
#                           CLUSTER PROVISIONING FAILING AT PREVM SETUP
#                           STEP:EXACLOUD : COULD NOT UPDATE CELL DISK SIZE
#    ririgoye    06/27/24 - Bug 36742070 - Additionaly including logs for
#                           updating key-val files
#    naps        03/08/24 - Bug 36367235 - defunct process handling during
#                           worker termination.
#    aypaul      01/08/24 - Bug#36150269 Add support to kill current process
#                           tree.
#    ririgoye    09/06/23 - Bug 35616435 - Add aLocal parameter to
#                           connect_to_host method for localhost nodes
#    ririgoye    09/01/23 - Bug 35769896 - PROTECT YIELD KEYWORDS WITH
#                           TRY-EXCEPT BLOCKS
#    ririgoye    06/13/23 - EXACS:EXACLOUD:CREATE SERVICE:ADD BASH HISTORY TIME DURING EXACLOUD CREATE SERVICE
#    aypaul      06/13/23 - Enh#35470717 Ilom connection support via
#                           username/password authentication.
#    aypaul      09/01/22 - Enh# 34528992 Replace incorrect DB images on VM.
#    alsepulv    03/08/22 - Bug 33691491: Add timeout parameter to
#                           connect_to_host and node_exec_cmd* functions
#    jlombera    02/22/22 - Bug 33882570: node_update_key_val_file() - add EOL
#    jlombera    04/22/21 - Bug 32753598: add param "log_warning" to
#                           node_exec_cmd()
#    jlombera    03/23/21 - Bug 32620666: add functions to connect and cmd
#                           execution
#    jlombera    03/22/21 - Bug 32652512: add node_cmd_abs_path()
#    jlombera    03/22/21 - Creation
#
"""
Auxiliary functions for remote node operations.
"""

import itertools
import os
import psutil
import signal
import time
from contextlib import contextmanager
from typing import Generator, Mapping, NamedTuple, Optional, Sequence

from exabox.core.Context import exaBoxContext, get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogWarn, ebLogInfo, ebLogTrace

UNIX_SUCCESS_CODE = 0
PROCESS_KILLED_WAITTIME = 5

# Public API
__all__ = [
    'kill_proc_tree',
    'connect_to_host',
    'node_cmd_abs_path',
    'node_cmd_abs_path_check',
    'node_connect_to_host',
    'node_exec_cmd',
    'node_exec_cmd_check',
    'node_list_process',
    'node_read_text_file',
    'node_update_key_val_file',
    'node_write_text_file',
    'node_replace_file'
]

"""Kill a process tree (including grandchildren) with signal specified by 'sig'
By default this routine is enabled, if required to disable, the config parameter 'kill_proc_tree' can be used."""
def kill_proc_tree(
        pid: int,
        sig = signal.SIGKILL) -> list:

    _config_opts = get_gcontext().mGetConfigOptions()
    if "kill_proc_tree" in _config_opts.keys():
        _config_val = _config_opts["kill_proc_tree"]
        if _config_val == "False":
            return []
    _add_defunct_child = False
    if "terminate_workers_having_defunct_child" in _config_opts.keys():
        _config_val = _config_opts["terminate_workers_having_defunct_child"]
        if _config_val == "True":
            _add_defunct_child = True
    _parent_proc = psutil.Process(int(pid))
    _children_procs = _parent_proc.children(recursive=True)

    _defunct_child_processes = list()
    if len(_children_procs) > 0:
        ebLogTrace(f"Number of child processes for PID: {pid}: {len(_children_procs)}")
    for _child_proc in _children_procs:
        ebLogTrace(f"Terminating process with PID: {_child_proc.pid}")
        try:
            _child_proc.send_signal(sig)
            time.sleep(PROCESS_KILLED_WAITTIME)
            if psutil.pid_exists(_child_proc.pid):
                _chproc = psutil.Process(_child_proc.pid)
                _proc_status = _chproc.status()
                ebLogWarn(f'*** kill_proc_tree: Unable to kill child process with pid:{_child_proc.pid}, status: {_proc_status}')
                if _proc_status == psutil.STATUS_ZOMBIE and _add_defunct_child is False:
                    #multiprocess functions with process list/dict and oeda install.sh can sometimes result in defunct functions.
                    #until we fix them all, lets ignore such defunct processes.. to avoid too many workers getting marked as corrupt.   
                    ebLogWarn(f'*** kill_proc_tree: skipping {_child_proc.pid} for defunct child process list !')
                else:
                    _defunct_child_processes.append(_child_proc.pid)
        except psutil.NoSuchProcess:
            ebLogWarn(f"No such process exists with pid: {_child_proc.pid}")
            pass
        except psutil.AccessDenied:
            ebLogWarn(f"Could not terminate process with pid: {_child_proc.pid} due to access denied.")
            pass
        except Exception as ex:
            ebLogWarn(f"Could not terminate process with pid: {_child_proc.pid} due to generic exception. Exception details: {ex}")
            pass

    return _defunct_child_processes

def node_list_process(
        node: exaBoxNode,
        process_pattern: str,
        log_when_found:bool = True) -> list:
    """
    List if any process with pattern "process_pattern" are running in the node

    :param node: already connected exaBoxNode
    :param process_pattern: pattern to look for

    :returns: a list of processes (if any)
    """

    if not process_pattern:
        msg = (f"Can't search for process without name in host "
            f"{node.mGetHostname()}")
        ebLogError(msg)
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    _bin_pgrep = node_cmd_abs_path_check(node, "pgrep", sbin=True)
    _bin_grep = node_cmd_abs_path_check(node, "grep", sbin=True)

    # Unfortunately the Exacloug layer to trigger commands somehow uses
    # subprocesses in the nodes through 'bash' so we need to manually filter
    # out the own process
    _process_list = []
    _out_process = node_exec_cmd(node,
        f"{_bin_pgrep} -af '{process_pattern}' | {_bin_grep} -v $$")

    if _out_process.exit_code == 0:
        _process_list = _out_process.stdout.strip().splitlines()
        if log_when_found:
            ebLogInfo(f"Found the process list:\n{_process_list}")
    else:
        ebLogInfo(f"No process '{process_pattern}' found to be running in "
            f"{node.mGetHostname()}")

    return _process_list

@contextmanager
def connect_to_host(
        hostname: str,
        ctx: exaBoxContext,
        username: Optional[str] = None,
        timeout: Optional[int] = None,
        password: Optional[int] = None,
        local: Optional[bool] = False) -> Generator[exaBoxNode, None, None]:
    """Connect to remote host.

    Connects to remote host.  Return an exaBoxNode connected to give remote
    host.  The recommended use is as contextmanager, which will automatically
    disconnect the node, even in the presence of an exception.

    This function is just a simple but convenient wrapper around exaBoxNode
    with more declarative semantics.  As an example, with this function the
    following safe (and correct) use of exaBoxNode:

        node = exaBoxNode(ctx)

        try:
            node.mConnect(hostname)
            # use connected node
        finally:
            node.mDisconnect(ctx)

    can be achieved simply as:

        with connect_to_host(hostname, ctx) as node:
            # use connected node

    If username is not specified, it'll be determined from the context.

    :param hostname: FQDN of the host to connect.
    :param ctx: exaBoxContext for the connection.
    :param username: username to connect as
    :param timeout: amount of seconds for connection timeout
    :returns: Contextmanager with the connected exaBoxNode
    :raises Exception: if an error occurred while connecting to the host.
    """
    node = exaBoxNode(ctx, aLocal=local)

    if username:
        node.mSetUser(username)

    if password:
        node.mSetPassword(password)

    with node_connect_to_host(node, hostname, timeout) as node:
        try:
            yield node
        except StopIteration as e:
            ebLogError(f"Error during node connection yielding: {e}")
            raise


@contextmanager
def node_connect_to_host(
        node: exaBoxNode,
        hostname: str,
        timeout: Optional[int] = None) -> Generator[exaBoxNode, None, None]:
    """Connect the given node to a remote host.

    Returns a contextmanager with the connected node.  The node will be
    automatically disconnected after leaving the context.

    :param node: exaBoxNode to connect.
    :param hostname: FQDN of the host to connect.
    :param timeout: amount of seconds for connection timeout.
    :returns: Contextmanager with the connected exaBoxNode.
    :raises Exception: if an error occurred while connecting.
    """
    try:
        node.mConnect(hostname, aTimeout=timeout)
        yield node
    except StopIteration as e:
        ebLogError(f"Error during node connection yielding: {e}")
    finally:
        node.mDisconnect()


def node_cmd_abs_path(
        node: exaBoxNode,
        cmd: str,
        sbin: bool = False) -> Optional[str]:
    """Get the absolute path to a command in a remote node.

    It will look for the given command in a set of predefined bin directories
    in a predefined order.  If 'sbin' is True, sbin directories will be
    considered as well and will take precedence over bin directories.

    :param node: already connected exaBoxNode
    :param cmd: name of the command to look for
    :param sbin: whether to look in sbin dirs too
    :returns: the absolute path to the command or None if not found
    """
    if sbin:
        dirs: Sequence[str] = ('/sbin/', '/usr/sbin/', '/bin/', '/usr/bin/')
    else:
        dirs = ('/bin/', '/usr/bin/')

    for bin_dir in dirs:
        path = os.path.join(bin_dir, cmd)

        if node.mFileExists(path):
            return path

    return None  # no command found


def node_cmd_abs_path_check(
        node: exaBoxNode,
        cmd: str,
        sbin: bool = False) -> str:
    """Get the absolute path to command in a remote node (raises on error).

    This is the same as node_cmd_abs_path() but raises an ExacloudRuntimeError
    exception if the command is not found.
    """
    path = node_cmd_abs_path(node, cmd, sbin)

    if path is None:
        msg = (f'Command "{cmd}" not found in host {node.mGetHostname()}')
        ebLogError(msg)
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    return path


class CmdRet(NamedTuple):
    """Result of remote command execution."""
    exit_code: int
    stdout: str
    stderr: str


def node_exec_cmd(  # pylint: disable=too-many-arguments
        node: exaBoxNode,
        cmd: str,
        log_warning: bool = False,
        log_error: bool = False,
        log_stdout_on_error: bool = False,
        check_error: bool = False,
        timeout: Optional[int] = None) -> CmdRet:
    """Execute a command in a node.

    Just a convenient wrapper around node.mExecuteCmd() that returns the
    command's exit code and stdout/stderr as strings.  If check_error=True, an
    ExacloudRuntimeError exception is raised in the command failed (it's exit
    code is != 0).  The exception will contain information about the command.
    On error, if log_error or log_warning is True, an error/warning will be
    logged (if log_error=True, log_warning is ignored).

    :param node: node where to execute the command.
    :param cmd: command to execute.
    :param log_warning: whether log a warning if the command failed.
    :param log_error: whether to log an error if the command failed.
    :param log_stdout_on_error: whether to add stdout to the logged error.
    :param check_error: whether raise an exception if command failed.
    :param timeout: seconds for command execution timeout.
    :returns: tuple with command's (exit_code, stdout, stderr)
    :raises ExacloudRuntimeError: if an error occurred.
    """
    _stdin = None
    stdout = None
    stderr = None
    out = None
    err = None

    try:
        _stdin, stdout, stderr = node.mExecuteCmd(cmd, aTimeout=timeout)
        ret = node.mGetCmdExitStatus()
        if stdout:
            out = stdout.read()
        if stderr:   
            err = stderr.read()

        if ret != 0:
            stdout_msg = f'stdout="{out}"' if log_stdout_on_error else ''
            msg = (f'Remote command execution failed: '
                   f'host={node.mGetHostname()}; cmd="{cmd}"; rc={ret}; '
                   f'{stdout_msg}; stderr="{err}"')

            if log_error:
                ebLogError(msg)
            elif log_warning:
                ebLogWarn(msg)

            if check_error:
                raise ExacloudRuntimeError(0x10, 0xA, msg)

        return CmdRet(ret, out, err)
    finally:
        if _stdin:
            _stdin.close()

        if stdout:
            stdout.close()

        if stderr:
            stderr.close()


def node_exec_cmd_check(
        node: exaBoxNode,
        cmd: str,
        log_error: bool = True,
        log_stdout_on_error: bool = True,
        timeout: Optional[int] = None) -> CmdRet:
    """Execute a command in a node and it succeeded.

    Simple wrapper around node_exec_cmd() that raises an ExacloudRuntimeError
    exception if the command failed (passes 'check_error=True').  On failure,
    logs error by default.

    See node_exec_cmd() for a complete description.
    """
    return node_exec_cmd(
        node, cmd, False, log_error, log_stdout_on_error, check_error=True,
        timeout=timeout)


def node_read_text_file(node: exaBoxNode, file_path: str) -> str:
    """Read content of a text file in a node.

    :param node: node to read file from.
    :param file_path: path file in to read in the node.
    :returns: the content of the file.
    :raises ExacloudRuntimeError: if an error occurred reading the file.
    """
    try:
        return node.mReadFile(file_path).decode('utf-8')
    except Exception as ex:
        msg = (f'Error reading file {file_path} in host '
               f'{node.mGetHostname()}: {ex}')
        raise ExacloudRuntimeError(0x10, 0xA, msg) from ex


def node_write_text_file(
        node: exaBoxNode,
        file_path: str,
        data: str,
        append: bool = False) -> None:
    """Write to a text file in a node.

    :param node: node where is the file to write.
    :param file_path: file to write in the node.
    :param data: data to write.
    :param append: whether append to the file instead of overwriting.
    :returns: nothing.
    :raises ExacloudRuntimeError: if an error occurred writing the file.
    """
    try:
        node.mWriteFile(file_path, data.encode('utf-8'), append)
    except Exception as ex:
        msg = (f'Error writing file {file_path} in host '
               f'{node.mGetHostname()}: {ex}')
        raise ExacloudRuntimeError(0x10, 0xA, msg) from ex


def node_update_key_val_file(
        node: exaBoxNode,
        file_path: str,
        key_vals: Mapping[str, Optional[str]],
        sep: str = '=',
        ignore: bool = False) -> None:
    """Update key-value pairs in remote text file.

    Updates key-value pairs in the given file with the new values as specified
    in 'key_vals'.  Any key whose value is None in 'key_vals' is removed from
    the file.

    :param node: already connected exaBoxNode where to operate.
    :param file_path: path of the file in remote node.
    :param key_vals: key-value pairs to update.
    :param sep: separator in key-value pair.
    :returns: Nothing
    :raises Exception: if an error occurred.
    """

    ebLogTrace(f"Updating {file_path} to include new key-value pairs.")
    content = node_read_text_file(node, file_path)
    new_content = _update_key_val_str(content, key_vals, sep, ignore=ignore)
    node_write_text_file(node, file_path, new_content)


def _update_key_val_str(
        content: str,
        key_vals: Mapping[str, Optional[str]],
        sep: str = '=',
        ignore: bool = False) -> str:
    """Update key-value pairs in a string.

    This is just the actual logic implementation of node_update_key_val_file(),
    that receives a string with key-value pairs and returns the updated string.

    See node_update_key_val_file() for details.
    """

    def __line_doesnt_match_key(line: str) -> bool:
        key, _, _ = line.partition(sep)
        return key.strip() not in key_vals

    # remove all lines matching the keys and then add them with the new values
    split_lines = content.splitlines()
    filtered_lines = filter(__line_doesnt_match_key, split_lines)
    # in case we do not want to update the content if the key-value pair is 
    # already present
    if ignore and split_lines != filtered_lines:
        ebLogInfo("Found property but will not make any changes to file.")
        return content
    # if ignore is set to false or the key-value pair wasn't found, proceed
    # as usual
    new_lines = (
        f'{key}{sep}{val}' for key, val in key_vals.items() if val is not None
    )
    new_content = '\n'.join(itertools.chain(filtered_lines, new_lines))

    ebLogTrace(f"Updated file to include these new key-value pairs: {list(new_lines)}")

    # ensure we add OEL at the end
    return f"{new_content}\n"

def node_replace_file(
    _node: exaBoxNode,
    _abs_local_file_path: str,
    _abs_remote_file_path: str) -> bool:

    if not os.path.isabs(_abs_local_file_path) or not os.path.isabs(_abs_remote_file_path):
        return False

    if not _node.mIsConnected():
        return False

    if not os.path.exists(_abs_local_file_path) or not _node.mFileExists(_abs_remote_file_path):
        return False

    _mv_cmd = node_cmd_abs_path_check(_node, "mv")
    _cmd = f"{_mv_cmd} {_abs_remote_file_path} {_abs_remote_file_path}.tmpbkup"
    _node.mExecuteCmd(_cmd)
    if _node.mGetCmdExitStatus() != UNIX_SUCCESS_CODE:
        return False

    _node.mCopyFile(_abs_local_file_path, _abs_remote_file_path)
    if not _node.mFileExists(_abs_remote_file_path):
        _cmd = f"{_mv_cmd} {_abs_remote_file_path}.tmpbkup {_abs_remote_file_path}"
        _node.mExecuteCmd(_cmd)
        return False

    _rm_cmd = node_cmd_abs_path_check(_node, "rm")
    _cmd = f"{_rm_cmd} -f {_abs_remote_file_path}.tmpbkup"
    _node.mExecuteCmd(_cmd)
    return True
