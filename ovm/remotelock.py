#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/remotelock.py /main/20 2025/07/04 12:47:23 jesandov Exp $
#
# remotelock.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      remotelock.py - Remote (Host) Lock
#
#    DESCRIPTION
#      Handles the acquisition and release of locks on host's (AKA Remote locks)
#
#    NOTES
#      Documentation can be found at
#      https://confluence.oraclecorp.com/confluence/display/EDCS/Remote+Lock+Heartbeat
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    06/30/25 - Bug 38127875 - Add logic for multiprocess in lock
#    jfsaldan    01/31/25 - Bug 37468472 - EXACLOUD - LOCK ACQUISITION IS
#                           DELAYED BY UP TO 60 SECONDS AFTER ANOTHER
#                           CONCURRENT OPERATION RELEASES IT
#    aararora    06/25/24 - Bug 36743916: op_cleanup command correction.
#    aypaul      05/20/24 - Bug#36565380 Skip exception while releasing locks
#                           and continue.
#    jesandov    04/04/24 - 36482990 - Optimization of remote lock
#    ririgoye    02/19/24 - Bug 36305000 - Added process killing enforcement
#                           and process start/end logging
#    jesandov    05/12/23 - 35371006: Add validation to use process and not
#                           thread
#    aypaul      03/22/23 - Enh#EXACS-106759 active stale lock release
#                           implementation
#    ajayasin    06/21/22 - Bug 34301090: host lock : order of lock is diff
#                           causing dead lock
#    jfsaldan    03/10/22 - Bug 33946412 - Delete remote host{UID}.py lock
#                           script from host after being used
#    ajayasin    01/10/22 - 33728983:create /opt/exacloud folder before copy
#    naps        10/14/21 - copy host_lock.py only if required.
#    joserran    08/06/21 - Bug 32614102: Adding Remote Lock heartbeat mechanism
#    joserran    07/14/21 - Creation
#

import enum
import json
import os
import sys
import pwd
import socket
import time
import subprocess
import uuid as uuidx
import copy

from base64 import b64encode

from typing import (
     Dict, Optional, Mapping, TYPE_CHECKING)

from exabox.core.DBLockTableUtils import ebDBLockTypes
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogWarn, ebLogInfo, ebLogDebug, ebLogTrace
from exabox.utils.node import (connect_to_host,
                               node_exec_cmd,
                               node_exec_cmd_check)
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, ExitCodeBehavior

# We need to import exaBoxCluCtrl for type annotations, but it will cause a
# cyclic-import at runtime.  Thus we import it only when type-checking.  We
# still need to define type exaBoxCluCtrl or pylint will complain, though, so
# we just make it an alias to 'object' when not type-checking.
if TYPE_CHECKING:
    from exabox.ovm.clucontrol import exaBoxCluCtrl
else:
    exaBoxCluCtrl = object  # pylint: disable=invalid-name

# NOTE! Make sure you keep LockRetCode in scripts/host_lock.py in sync
class LockRetCode(enum.Enum):
    """ Enumeration for host_lock.py return/exit codes """
    NO_ERROR = 0
    ERROR = 1 # Generic error
    LOCK_NOT_ACQUIRED = 2
    LOCK_NOT_ACQUIRED_LEGACY_MODE = 3
    LOCK_EXPIRED_AND_ACQUIRED = 4
    LOCK_NOT_FOUND = 5
    FILE_OPEN_ERROR = 126

class LockState(enum.Enum):
    """ Enumeration for lock state values """
    RELEASED = 0
    ACQUIRED = 1
    ACQUIRING = 2


def dict2base64(dictionary: Mapping) -> str:
    """ Converts a dictionary into a base64 json string """
    _dict_str = json.dumps(dictionary)
    _dict_str = _dict_str.encode('utf-8')
    _dict_base64_str = b64encode(_dict_str).decode('utf-8')
    return _dict_base64_str


class RemoteLock:
    """
    Implements the remote lock mechanism for host's

    * Implements a thread-based heartbeat to keep locks on host's active/valid.
    * Supports nested locks.
    * Context manager (i.e. 'with' block) is supported and encouraged.

        RECOMMENDED lock example using context manager:

        1 remote_lock = RemoteLock(clu_control)
        2 ...
        3 with remote_lock():
        4     # Protected operations on host
        5     # ...
    """
    # Lock validity should always be greater than refresh time
    LOCK_REFRESH_TIME_SECONDS = (60 * 5)
    LOCK_PING_TIME_SECONDS = 60
    LOCK_VALIDITY_SECONDS = (LOCK_REFRESH_TIME_SECONDS * 2)
    INIT_RETRY_DELAY_SECONDS = 2
    MAX_RETRY_DELAY_SECONDS = 16

    def __init__(self, clu_ctrl: exaBoxCluCtrl, force_host_list=[]):
        self._counter = 0
        self._request_lock_state = LockState.RELEASED
        self._clu_ctrl = clu_ctrl
        self._lock_name = "Default"
        self._extra_lock_info = None
        self._active_processes = None
        self._worker_port = None
        self._force_host_list = force_host_list
        # _active_processes is ProcessManager with the active process

    def set_lock_type(self, aType):
        self._lock_name = aType

    def update_worker_port(self):
        from exabox.agent.Worker import ebWorker
        _current_worker = ebWorker()
        _current_worker.mLoadWorkerUsingPID(os.getpid())

        # Get parent pid in case of subprocess
        if _current_worker.mGetPort() is None or str(_current_worker.mGetPort()) == "0":
            _current_worker.mLoadWorkerUsingPID(os.getppid())

        self._worker_port = _current_worker.mGetPort()

    def get_request_state(self) -> LockState:
        """ Return the lock state for the current exacloud request """
        return self._request_lock_state

    def acquire(self,
                lock_name: str = "Default",
                **extra_lock_info) -> None:
        """ Acquire lock on all Hosts. Supports nested acquisition.
        :param lock_name: A string to uniquely identify the lock.
        :param extra_lock_info: Keyworded items that help to better describe
                                the intent of this lock. While not mandatory,
                                adding some fields can result in useful data
                                while waiting for a lock, testing or
                                troubleshooting.
        ExacloudRuntimeError is raised if acquire fails.

        Example:
        # Creating a lock with a couple of custom extra lock info fields...
        with remote_lock(step="Copying images to Host",
                         estimated_duration="~30min"):
            # Protected code

        # Will result on the basic lock information plus an
        # "extra_info" field containing all the key-worded arguments passed
        # at acquisition time.
        {
            "acquire_date": "2021-07-27 01:27:41.416511 UTC",
            "expire_date": "2021-07-27 01:27:51.416511 UTC",
            "owner_uuid": "107be67e-e83e-11eb-8c87-fa163e150850"

            "extra_info": {
                "step": "Copying images to Host",
                "estimated_duration": "~30min"
            }
        }
        """
        if self._worker_port is None:
            self.update_worker_port()
        if not self._clu_ctrl.SharedEnv():
            ebLogInfo(f'Single-VM environment detected, skipping remote locking')
            return

        uuid = f"{self._clu_ctrl.mGetUUID()}_{os.getpid()}"

        host_list = []

        if not self._force_host_list:
            _dom0s, _domUs, _cells, _switches = self._clu_ctrl.mReturnAllClusterHosts()

            if lock_name.lower() in ["dom0", "default"]:
                host_list = _dom0s

            if lock_name.lower() in ["domu", "vm"]:
                host_list = _domUs

            if lock_name.lower() in ["cell"]:
                host_list = _cells

            if lock_name.lower() in ["switch"]:
                host_list = _switches

        else:
            host_list = copy.deepcopy(self._force_host_list)

        host_list.sort()
        try:

            # Create Process Manager
            self._active_processes = ProcessManager(aExitCodeBehavior=ExitCodeBehavior.IGNORE)

            if self._counter > 0:
                ebLogInfo((f'Acquiring NESTED remote lock for {uuid} '
                           f'on {host_list}. No-op'))
                self._counter = self._counter + 1
                return

            ebLogInfo(f'Acquiring remote lock for {uuid} on {host_list}')

            if extra_lock_info:
                self._extra_lock_info = extra_lock_info

            self._update_request_state(2) # 2 for ACQUIRING status

            host_count = len(host_list)
            for acquired_count, host in enumerate(host_list, start=1):
                self._acquire_per_host(host, uuid, lock_name,
                                       acquired_count, host_count)

            self._counter = self._counter + 1
            ebLogInfo(f'Full remote lock ACQUIRED for {uuid}')
        except Exception as exp:
            msg = ('Remote lock acquisition failed: '
                   f'host_list:{host_list}; uuid:{uuid}; error:"{exp}"')
            ebLogError(msg)

            self._cleanup_processes(uuid)

            raise ExacloudRuntimeError(0x806, 0xA, msg) from exp

    def isRemoteLocalFileSame(self, aNode, aLocal, aRemote):
        _node = aNode
        _local_file = aLocal
        _remote_file = aRemote
        _local_hash = ''
        _remote_hash = ''

        _out = subprocess.check_output(['/usr/bin/sha256sum', _local_file]).decode('utf8')
        if _out:
            _local_hash = _out.strip().split(' ')[0]
        else:
            ebLogError('*** Failed to compute sha256sum for %s' % (_local_file))

        _, _o, _ = _node.mExecuteCmd('/usr/bin/sha256sum ' + _remote_file)
        _rc = _node.mGetCmdExitStatus()
        if not _rc:
            _remote_hash = _o.readlines()[0].strip().split(' ')[0]

        if _remote_hash != _local_hash:
            return False

        return True

    def evaluate_existing_lock_information(self, aExitCode, aRemoteScript, aLockName, aNode, aHost, aRecurringEvaluation=False) -> bool:

        exit_code = aExitCode
        remote_script = aRemoteScript
        lock_name = aLockName
        node = aNode
        host = aHost
        retry_acquire_now = False
        if exit_code == LockRetCode.LOCK_NOT_ACQUIRED.value:
            get_lock_info_cmd = (f"{remote_script} get-info "
                                    f"--lock-scope {lock_name}")
        # Not acquired due to legacy lock in place (check host_lock.py)
        else:
            get_lock_info_cmd = f"{remote_script} get-info --legacy"

        _, out, _ = node_exec_cmd_check(node, get_lock_info_cmd)
        lock_info = json.loads(out)
        lock_info_str = json.dumps(lock_info, sort_keys=True, indent=4)

        if self.release_stale_locks(lock_info, host):
            ebLogInfo(f"Stale lock {lock_name} on host {host} has been released. Retrying lock acquire now.")
            retry_acquire_now = True
        else:
            if not aRecurringEvaluation:
                ebLogInfo((f'Lock {lock_name} on {host} is already '
                        f'acquired by another operation. '
                        f'Waiting until it gets released. '
                        f'Blocking lock information: {lock_info_str}'))

        return retry_acquire_now

    """Sample lock metadata:
    {
        "exacloud_service_path": "", 
        "acquire_date": "", 
        "owner_hostname": "", 
        "exadata_cluster_name": "", 
        "owner_user_name": "", 
        "owner_uuid": "", 
        "exadata_host": "", 
        "expire_date": "", 
        "exadata_cluster_key": "", 
        "exacloud_command": "",
        "worker_port" : ""
    }
    """
    def release_stale_locks(self, aLockInfo: dict, aHost: str) -> bool:

        _lock_info = aLockInfo
        _acquired_lock_owner_process_hostname = _lock_info.get("owner_hostname", None)
        _acquire_lock_uuid = _lock_info.get("owner_uuid", "00000000-0000-0000-0000-000000000000").split("_")[0]
        _current_process_hostname = socket.getfqdn()
        _release_currenthost_lock = False
        if _acquired_lock_owner_process_hostname is not None and _acquired_lock_owner_process_hostname == _current_process_hostname:
            _acquired_worker_port = _lock_info.get("worker_port", None)
            if _acquired_worker_port is not None and str(_acquired_worker_port) != "0":
                from exabox.agent.WClient import ebWorkerCmd
                _worker_cmd = ebWorkerCmd(aCmd='status', aPort=_acquired_worker_port)
                _worker_cmd.mIssueRequest()
                _status_json = _worker_cmd.mWaitForCompletion()
                if not _status_json:
                    ebLogError(f"Worker is not accessible at port ({_acquired_worker_port})")
                    _release_currenthost_lock = True
                else:
                    ebLogTrace(f"Worker with port {_acquired_worker_port} is running and active.")
                    _worker_current_uuid = _status_json.get("uuid","00000000-0000-0000-0000-000000000000").split("_")[0]
                    if _worker_current_uuid != _acquire_lock_uuid:
                        ebLogError(f"Worker with port {_acquired_worker_port} is running job with uuid {_worker_current_uuid} which doesn't match acquired lock uuid {_acquire_lock_uuid}.")
                        _release_currenthost_lock = True
        elif _acquired_lock_owner_process_hostname is not None:
            _ping_check = self._clu_ctrl.mPingHost(_acquired_lock_owner_process_hostname)
            if not _ping_check:
                ebLogError(f"Ping check for host which acquired the current lock {_acquired_lock_owner_process_hostname} has failed.")
                _release_currenthost_lock = True
        else:
            ebLogWarn(f"Hostname information missing from lock metadata: {json.dumps(_lock_info)}")

        _released_host_lock = False
        if _release_currenthost_lock:
            _target_host = aHost
            if _target_host is None:
                ebLogWarn(f"Host information is missing from lock metadata, skipping lock release.")
            else:
                ebLogInfo(f"Releasing acquired lock from host {_acquired_lock_owner_process_hostname} for host {_target_host}.")
                self.remove_all_locks(_target_host)
                _released_host_lock = True

        return _released_host_lock

    def _acquire_per_host(self,
                          host: str,
                          uuid: str,
                          lock_name: str,
                          acquired_count: str,
                          host_count: int) -> None:
        """ Helper method to acquire a lock on a single host """

        with connect_to_host(host, self._clu_ctrl.mGetCtx()) as node:

            # Make sure Host has our host_lock.py version
            remote_script = f'/opt/exacloud/host_lock{uuid.replace("-", "")}.py'
            local_script = 'scripts/network/dom0_lock.py'

            if not self.isRemoteLocalFileSame(node, local_script, remote_script):
                ebLogInfo('***Copying host_lock.py to remote node !')
                node.mExecuteCmdLog('/bin/mkdir -p /opt/exacloud') 
                node.mCopyFile(local_script, remote_script)
                node_exec_cmd_check(node, f'chmod 755 {remote_script}')

            # ACQUIRING lock...
            db = ebGetDefaultDB()
            db.mInsertLock(uuid=uuid,
                           lock_type=ebDBLockTypes.DOM0_LOCK_ACQUIRING,
                           lock_hostname=host)

            lock_info = self._create_lock_info(host)
            lock_info_base64 = dict2base64(lock_info)
            acquire_cmd = (f'{remote_script} acquire '
                           f'--lock-info {lock_info_base64} '
                           f'--valid-for {RemoteLock.LOCK_VALIDITY_SECONDS} '
                           f'{lock_name} {uuid}')
            exit_code, out, stderr = node_exec_cmd(node, acquire_cmd)

            # Lock NOT ACQUIRED so keep trying
            if exit_code in [LockRetCode.LOCK_NOT_ACQUIRED.value,
                             LockRetCode.LOCK_NOT_ACQUIRED_LEGACY_MODE.value,
                             LockRetCode.FILE_OPEN_ERROR.value]:

                retry_acquire_now = self.evaluate_existing_lock_information(exit_code, remote_script, lock_name, node, host)

                retry_delay_seconds = RemoteLock.INIT_RETRY_DELAY_SECONDS
                while exit_code in [LockRetCode.LOCK_NOT_ACQUIRED.value,
                                    LockRetCode.LOCK_NOT_ACQUIRED_LEGACY_MODE.value,
                                    LockRetCode.FILE_OPEN_ERROR.value]:

                    if not retry_acquire_now:
                        ebLogDebug((f'Next acquisition retry of '
                               f'{lock_name} lock on {host} in '
                               f'{retry_delay_seconds} seconds...'))
                        time.sleep(retry_delay_seconds)
                    exit_code, out, stderr = node_exec_cmd(node,
                                                           acquire_cmd)
                    retry_acquire_now = self.evaluate_existing_lock_information(exit_code, remote_script, lock_name, node, host, True)

                    # Exponential backoff
                    if not retry_acquire_now:
                        retry_delay_seconds = min(retry_delay_seconds << 1,
                                                RemoteLock.MAX_RETRY_DELAY_SECONDS)

            # STALE lock; stderr contains expired lock info
            if exit_code == LockRetCode.LOCK_EXPIRED_AND_ACQUIRED.value:
                lock_info = json.loads(stderr)
                lock_info_str = json.dumps(lock_info, sort_keys=True, indent=4)
                ebLogWarn((f'EXPIRED lock {lock_name} on {host} has '
                           f'been cleaned up and is now ACQUIRED by us. '
                           f'Expired lock information: {lock_info_str}'))
            # Lock ACQUIRED
            elif exit_code == LockRetCode.NO_ERROR.value:
                ebLogDebug((f'Partial remote lock {lock_name} ACQUIRED '
                           f'on {host} for {uuid}. {acquired_count} out of '
                           f'{host_count} locks acquired'))
            else:
                msg = (f'Lock acquisition failed unexpectedly on {host} '
                       f'lock: {lock_name} operation id: {uuid} '
                       f'exit_code: {exit_code} stdout: {out} stderr: {stderr}')
                ebLogError(msg)
                raise ExacloudRuntimeError(0x806, 0xA, msg)

            _process = ProcessStructure(
                self._lock_heartbeat,
                [host, lock_name, uuid]
            )

            self._active_processes.mStartAppend(_process)

            # At this point, the lock should be acquired
            self._update_request_state(1) # 1 for ACQUIRED  status

            db.mDeleteLock(uuid, ebDBLockTypes.DOM0_LOCK_ACQUIRING, host)
            db.mDeleteLockByHostname(ebDBLockTypes.DOM0_LOCK, host)
            db.mInsertLock(uuid=uuid,
                           lock_type=ebDBLockTypes.DOM0_LOCK,
                           lock_hostname=host)

    def release(self,
                lock_name: str = 'Default',
                uuid: Optional[str] = None) -> None:
        """ Release lock on all Hosts
        :param lock_name: A string to identify the lock to release
        :param uuid: Releases lock associated with a special uuid if provided,
                     otherwise uses clu-control's uuid.
        ExacloudRuntimeError is raised if unacquired lock is tried to be released
        or if there's an error acquiring the lock.
        """
        if not self._clu_ctrl.SharedEnv():
            ebLogInfo(f'Single VM detected, skipping remote unlocking')
            return

        self._counter = self._counter - 1
        if self._counter < 0:
            msg = "Trying to release unacquired lock, aborting!"
            ebLogError(msg)
            raise ExacloudRuntimeError(0x806, 0xA, msg)

        if not uuid:
            uuid = f"{self._clu_ctrl.mGetUUID()}_{os.getpid()}"

        if self._counter > 0:
            ebLogInfo(f'Releasing NESTED remote lock for {uuid}. No-op')
            return

        if not self._force_host_list:
            _dom0s, _domUs, _cells, _switches = self._clu_ctrl.mReturnAllClusterHosts()

            if lock_name.lower() in ["dom0", "default"]:
                host_list = _dom0s

            if lock_name.lower() in ["domu", "vm"]:
                host_list = _domUs

            if lock_name.lower() in ["cell"]:
                host_list = _cells

            if lock_name.lower() in ["switch"]:
                host_list = _switches

        else:
            host_list = copy.deepcopy(self._force_host_list)

        host_list.sort()

        total_locks = len(host_list)
        ebLogInfo(f'Releasing remote lock for {uuid} on {host_list}')

        try:
            for released_count, host in enumerate(host_list, start=1):
                self._release_per_host(host, uuid, lock_name,
                                       released_count, total_locks)

            ebLogInfo(f'Full remote lock RELEASED for {uuid}')
        except Exception as exp:
            msg = ('Remote lock release failed: '
                   f'host_list: {host_list}; uuid:{uuid}; error:"{exp}"')
            ebLogError(msg)
            raise ExacloudRuntimeError(0x806, 0xA, msg) from exp
        finally:
            ebLogInfo((f'Waiting for heartbeat process for {uuid}'
                       f' on {host_list} to stop'))
            self._cleanup_processes(uuid)

    def _release_per_host_unowned(self,
                                  host: str,
                                  uuid: str,
                                  lock_name: str,
                                  released_count: str,
                                  host_count: int) -> None:
        """ Helper method to release an unowned lock on a single host 
        :param host: Host for which lock needs to be released
        :param uuid: Releases lock associated with a special uuid provided
        :param lock_name: A string to identify the lock to release
        :param released_count: The count (of the host) for which lock is getting released
        :param host_count: The total number of hosts for which lock needs to be released
        ExacloudRuntimeError is raised if there's an error releasing the lock. """

        with connect_to_host(host, self._clu_ctrl.mGetCtx()) as node:

            # Make sure Host has our host_lock.py version
            remote_script = f'/opt/exacloud/host_lock{uuid.replace("-", "")}.py'
            local_script = 'scripts/network/dom0_lock.py'

            if not node.mFileExists(remote_script) or not self.isRemoteLocalFileSame(node, local_script, remote_script):
                ebLogInfo('***Copying host_lock.py to remote node !')
                node.mExecuteCmdLog('/bin/mkdir -p /opt/exacloud')
                node.mCopyFile(local_script, remote_script)
                node_exec_cmd_check(node, f'chmod 755 {remote_script}')

            # RELEASE lock
            release_lock_cmd = f"{remote_script} release {lock_name} {uuid}"
            exit_code, out, stderr = node_exec_cmd(node, release_lock_cmd)

            # DELETE remote_script, as this script is unique per uuid
            delete_lock_cmd = f"/bin/rm -f {remote_script}"
            node_exec_cmd_check(node, delete_lock_cmd)

            # LOCK_NOT_FOUND means lock already released so is ok.
            if exit_code not in [LockRetCode.NO_ERROR.value,
                                 LockRetCode.LOCK_NOT_FOUND.value]:
                msg = (f'Lock release failed unexpectedly on {host} '
                       f'lock: {lock_name} operation id: {uuid} '
                       f'exit_code: {exit_code} stdout: {out} stderr: {stderr}')
                ebLogError(msg)
                raise ExacloudRuntimeError(0x806, 0xA, msg)

            # Update db data
            ebGetDefaultDB().mDeleteLock(uuid, ebDBLockTypes.DOM0_LOCK, host)

            ebLogInfo((f'Partial remote lock {lock_name} RELEASED '
                       f'on {host} for {uuid}. {released_count} out of '
                       f'{host_count} locks released'))

    def release_unowned(self,
                        uuid,
                        lock_name: str = 'Default') -> None:
        """ Release lock on all Hosts
        :param lock_name: A string to identify the lock to release.
        :param uuid: Releases lock associated with a special uuid provided.

        Don't raise an exception if the lock could not be released.
        Log it, since this is for releasing unowned lock.
        """
        if not self._clu_ctrl.SharedEnv():
            ebLogInfo(f'Single VM detected, skipping remote unlocking')
            return

        if not self._force_host_list:
            _dom0s, _domUs, _cells, _switches = self._clu_ctrl.mReturnAllClusterHosts()

            if lock_name.lower() in ["dom0", "default"]:
                host_list = _dom0s

            if lock_name.lower() in ["domu", "vm"]:
                host_list = _domUs

            if lock_name.lower() in ["cell"]:
                host_list = _cells

            if lock_name.lower() in ["switch"]:
                host_list = _switches

        else:
            host_list = copy.deepcopy(self._force_host_list)

        host_list.sort()

        total_locks = len(host_list)
        ebLogInfo(f'Releasing remote lock for {uuid} on {host_list}')

        try:
            for released_count, host in enumerate(host_list, start=1):
                self._release_per_host_unowned(host, uuid, lock_name,
                                               released_count, total_locks)

            ebLogInfo(f'Full remote lock RELEASED for {uuid}')
        except Exception as exp:
            msg = ('Remote lock release failed: '
                   f'host_list: {host_list}; uuid:{uuid}; error:"{exp}".'
                   ' Manual cleanup may be required.')
            # Don't raise an exception if the lock could not be released.
            # Log it, since this is for op_cleanup command
            ebLogError(msg)

    def mGetProcessByHost(self, aHost):

        if self._active_processes:
            for _p in self._active_processes.mGetProcessList():
                if _p.mGetArgs()[0] == aHost:
                    return _p
        return None

    def _release_per_host(self,
                          host: str,
                          uuid: str,
                          lock_name: str,
                          released_count: str,
                          host_count: int) -> None:
        """ Helper method to release a lock on a single host """

        with connect_to_host(host, self._clu_ctrl.mGetCtx()) as node:

            # Make sure Host has our host_lock.py version
            remote_script = f'/opt/exacloud/host_lock{uuid.replace("-", "")}.py'
            local_script = 'scripts/network/dom0_lock.py'

            if not self.isRemoteLocalFileSame(node, local_script, remote_script):
                ebLogInfo('***Copying host_lock.py to remote node !')
                node.mExecuteCmdLog('/bin/mkdir -p /opt/exacloud')
                node.mCopyFile(local_script, remote_script)
                node_exec_cmd_check(node, f'chmod 755 {remote_script}')


            # RELEASE lock
            release_lock_cmd = f"{remote_script} release {lock_name} {uuid}"
            exit_code, out, stderr = node_exec_cmd(node, release_lock_cmd)

            # DELETE remote_script, as this script is unique per uuid
            delete_lock_cmd = f"/bin/rm -f {remote_script}"
            node_exec_cmd_check(node, delete_lock_cmd)

            # LOCK_NOT_FOUND means lock already released so is ok.
            if exit_code not in [LockRetCode.NO_ERROR.value,
                                 LockRetCode.LOCK_NOT_FOUND.value]:
                msg = (f'Lock release failed unexpectedly on {host} '
                       f'lock: {lock_name} operation id: {uuid} '
                       f'exit_code: {exit_code} stdout: {out} stderr: {stderr}')
                ebLogError(msg)
                raise ExacloudRuntimeError(0x806, 0xA, msg)

            # Stop the heartbeat process by using an event
            try:
                _process = self.mGetProcessByHost(host)

                if _process:
                    if _process.is_alive():
                        _process.terminate()
                    _process.join(5)

                    # In some cases, we might find that the process is still active
                    if _process.is_alive():

                        _killRetries, _maxKillRetries = 0, 3
                        _killRetryDelay = 5

                        while _process.is_alive() and _killRetries < _maxKillRetries:
                            ebLogInfo(f"Process {_process.pid} alive after trying to terminate it. Retrying.")
                            _killRetries += 1
                            self._active_processes.mKillProcess(_process)
                            time.sleep(_killRetryDelay)
            except Exception as ex:
                ebLogWarn(f'Failed to terminate heartbeat process for lock on host {host}.')

            # Update db data
            self._update_request_state(0) # 0 for LOCK RELEASED status
            ebGetDefaultDB().mDeleteLock(uuid, ebDBLockTypes.DOM0_LOCK, host)

            ebLogInfo((f'Partial remote lock {lock_name} RELEASED '
                       f'on {host} for {uuid}. {released_count} out of '
                       f'{host_count} locks released'))

    def clear(self, lock_name: str = 'Default') -> None:
        """
        WARNING!
        Use with caution, this method should never be used in a "normal"
        code flow (it's only meant for manual, last resource clean-up at end of
        request/operation)

        Forces the realease of locks on all Hosts owned by current process.
        If no lock has been acquired, this is a no-op.
        :param lock_name: A string to identify the lock to release
        """

        # If no lock acquired; do nothing
        if self._counter <= 0:
            self._counter = 0
            return

        self._counter = 1
        self.release(lock_name)

    def remove_all_locks(self, aHost=None) -> None:
        """
        Force deletion all locks on all host's.
        Warning! This will remove all locks even those not owned by current
        process or instance.
        """
        # Remove locks owned by current process
        self.clear()

        # Remove all other locks
        if aHost is None:
            host_list = [host for host, _ in self._clu_ctrl.mReturnDom0DomUPair()]
        else:
            host_list = [aHost]
        ebLogInfo(f'Forcefully REMOVING locks on {host_list}')
        for host in host_list:
            with connect_to_host(host, self._clu_ctrl.mGetCtx()) as node:
                # Make sure Host has our host_lock.py version
                _uuid = str(uuidx.uuid1())
                remote_script = f'/opt/exacloud/host_lock{_uuid.replace("-", "")}.py'
                local_script = 'scripts/network/dom0_lock.py'

                if not self.isRemoteLocalFileSame(node, local_script, remote_script):
                    ebLogInfo('***Copying host_lock.py to remote node !')
                    node.mExecuteCmdLog('/bin/mkdir -p /opt/exacloud') 
                    node.mCopyFile(local_script, remote_script)
                    node_exec_cmd_check(node, f'chmod 755 {remote_script}')

                # DELETING all locks
                remove_locks_cmd = f"{remote_script} remove --all"
                node_exec_cmd_check(node, remove_locks_cmd)

                # DELETE remote_script, as this script is unique per uuid
                delete_lock_cmd = f"/bin/rm -f {remote_script}"
                node_exec_cmd_check(node, delete_lock_cmd)

                ebLogInfo(f'Remote lock REMOVED on {host}')

    def __call__(self,
                 lock_name: str = "Default",
                 **extra_lock_info) -> 'RemoteLock':
        self._lock_name = lock_name
        self._extra_lock_info = extra_lock_info
        return self

    def __enter__(self) -> None:
        self.acquire(self._lock_name)

    def __exit__(self, e_type, value, traceback):
        self.release(self._lock_name)

    def _create_lock_info(self,
                          host: str) -> Dict:
        """ Return a dictionary with current host's lock information """
        user_name = pwd.getpwuid(os.getuid()).pw_name
        host_name = socket.getfqdn()
        service_path = self._clu_ctrl.mGetCtx().mGetBasePath()
        cluster_key = self._clu_ctrl.mGetKey()
        cluster_name = self._clu_ctrl.mGetClusterName()
        worker_port = self._worker_port

        lock_info = {
            "owner_user_name": user_name,
            "owner_hostname": host_name,
            "exacloud_service_path": service_path,
            "exadata_cluster_key": cluster_key,
            "exadata_cluster_name": cluster_name,
            "pid": os.getpid(),
            "exadata_host": host,
            "worker_port" : worker_port
        }

        # Request's command can give a hint of how long the lock is expected
        # to be be held
        request = self._clu_ctrl.mGetRequestObj()
        if request and request.mGetCmd():
            lock_info["exacloud_command"] = request.mGetCmd()

        if self._extra_lock_info:
            lock_info["extra_info"] = self._extra_lock_info

        return lock_info

    def _update_request_state(self, lock_state: LockState) -> None:

        self._request_lock_state = lock_state
        req_obj = self._clu_ctrl.mGetRequestObj()

        if not req_obj:
            ebLogWarn('Request Object not found - lockstate update not possible')
            return

        ebLogDebug('Request Object found updating lockstate')
        req_obj.mSetLock(lock_state)
        ebGetDefaultDB().mUpdateRequest(req_obj)

    # Heartbeat thread, keep the lock alive until release()
    def _lock_heartbeat(self, host: str, lock_name: str, uuid: str) -> None:
        """ Thread for refreshing the remote lock (a.k.a. heartbeat) """

        with connect_to_host(host, self._clu_ctrl.mGetCtx()) as thread_node:

            remote_script = f'/opt/exacloud/host_lock{uuid.replace("-", "")}.py'
            thread_cmd = (f'{remote_script} refresh '
                          f'--valid-for {RemoteLock.LOCK_VALIDITY_SECONDS} '
                          f'{lock_name} {uuid}')

            _lastUpdate = time.time()
            _lastPing = time.time()

            while True:

                time.sleep(1)

                if (time.time() - _lastPing) > RemoteLock.LOCK_PING_TIME_SECONDS:

                    if not self._clu_ctrl.mPingHost(host):
                        ebLogInfo(f"Host {host} is shutdown, stopping heartbeat process")
                        ebLogInfo(f"Once the host avaliable again, please make sure to remove the locks")
                        break
                    else:
                        ebLogInfo(f"Host {host} is pingable, continue heartbeat process")
                        _lastPing = time.time()

                if not thread_node.mFileExists(remote_script):
                    ebLogInfo(f"Complete process execution in host {host} since file is removed: {remote_script}")
                    break

                if (time.time() - _lastUpdate) > RemoteLock.LOCK_REFRESH_TIME_SECONDS:

                    ebLogInfo((f'Heartbeat refreshing '
                                f'{lock_name} lock on {host} by {uuid}'))
                    exit_code, _, _ = node_exec_cmd(thread_node, thread_cmd)

                    # Stop the thread if refresh failed, this can be due to
                    # external cleanup of the lock (e.g. calling remove_all_locks())
                    if exit_code:
                        break

                    _lastUpdate = time.time()


    def _cleanup_processes(self, uuid: str) -> None:
        """ Stop all active threads and clean it's data.

            Note: thread set() and join() in two separate loops so we minimize
            the likelihood of leaving unstopped threads due to some join()
            exception.
        """

        # Stop threads
        if self._active_processes:

            for process in self._active_processes.mGetProcessList():

                host = process.mGetArgs()[0]
                uuid = process.mGetArgs()[1]

                ebLogDebug(f'Stopping heartbeat process for {uuid} on {host}')
                if process.is_alive():
                    process.terminate()

            # Join threads
            self._active_processes.mJoinProcess()

        self._active_processes = None
        self._counter = 0

# end of file
