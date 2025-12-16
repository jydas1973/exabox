"""
$Header:

 Copyright (c) 2017, 2025, Oracle and/or its affiliates.

NAME:


NAME:
    Supervisor - Process monitoring workers and assosiated jobs

FUNCTION:
    Ensure the jobs status is consistent

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
       naps        11/06/25 - Bug 38566523 - remove redundant worker
                              termination logic in supervisor.
       aypaul      03/21/24 - Bug#36391673 Enclose supervisor   main loop with
                              generic try-catch to avoid supevisor process
                              exiting.
       aypaul      01/08/24 - Bug#36150217 Additional check for agent health
       naps        01/05/24 - Bug 36157324 - partial revert of 35896839.
       naps        07/21/23 - Bug 35013360 - Dispatcher and WorkerManager
                              implementation.
       naps        12/07/23 - Bug 35896839 - Add interval for checking workers
                              for termination.
       aypaul      09/20/23 - Enh#35813639 Forceshutdown(-fsd) to make sure
                              that crontab entry to be removed if it exists.
       prsshukl    08/04/23 - Bug 35663217 - Adding supervisor_fail_recovery
                              config parameter
       naps        07/18/23 - Bug 35478867 - Log stats during high cpu/mem
                              scenarios.
       hgaldame    06/07/23 - bug 35474178 - ecs main: exacloud agent start
                              failure
       ndesanto    06/02/23 - Dissabling supervisor in crontab for ExaCC
       aypaul      03/28/23 - Enh#35221396 Register/deregister cron task to
                              check supervisor activity.
       naps        02/07/23 - 34931403 - Increase default worker threads for
                              production mode.
       aypaul      12/04/22 - Issue#34607716 Handle multiprocessing issue by
                              shutting down base manager instance explicitly.
       aypaul      07/05/22 - Bug#34347508 Worker allocation optimisation logic
                              correction.
       aypaul      01/25/22 - Enh#33611377 Worker limit and resource
                              utilisation optimisation.
       sringran    01/13/21 - 32232686-ECRA STARTUP FAILED AS EXACLOUD FAILS TO START
       jejegonz    12/01/20 - Use LogMgr API for adding handlers to logger.
       naps        10/01/19 - Orphan job cleanup fix.
       sergutie    08/09/17 - Create file
       ndesanto    05/10/19 - added code to support the request backup
       ndesanto    09/04/20 - Added code for Supervisor to ensure MySQL is up
"""
import json
import datetime
import os
import ast
import time
import uuid
import signal
import threading
import psutil
import getpass
import shlex
from subprocess import Popen
from crontab import CronTab
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.DBStore import get_db_version, ebGetDefaultDB
from exabox.core.DBStore3 import StopMySQLConnRetryException
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError, ebLogAddDestinationToLoggers, ebGetDefaultLoggerName, ebFormattersEnum
from exabox.agent.Worker import ebWorkerFactory, ebWorker
from exabox.agent.Worker import daemonize_process, redirect_std_descriptors
from exabox.agent.RequestsBackupContext import RequestsBackupContext
from exabox.agent.WClient import ebWorkerCmd
from exabox.core.Context import get_gcontext
from exabox.agent.Client import ebExaClient, ebGetClientConfig
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Node import exaBoxNode

class ebSupervisor(object):
    _port = 55555

    def __init__(self, timeout=10):
        self._db = None
        self._timeout = timeout
        self._running = False
        self._worker_factory = ebWorkerFactory()
        self._request_backup_context = None
        self._notify = threading.Event()
        self._cpu_percent = psutil.cpu_percent()
        self._memory_percent = psutil.virtual_memory().percent
        signal.signal(signal.SIGINT, self._mSigHandler)
        signal.signal(signal.SIGTERM, self._mSigHandler)
        self._cpu_threshold = 80.0
        self._mem_threshold = 80.0
        self._healthcheckstart = datetime.datetime.now() + datetime.timedelta(minutes = 2)
        self._uuid_orphan_time_minutes = 30


    def mSetupCrontab(self):
        _current_crontab = CronTab(user=getpass.getuser())
        _coptions = get_gcontext().mGetConfigOptions()
        _current_agent_port = _coptions.get("agent_port", None)
        if _current_agent_port is None:
            ebLogWarn("agent port not found. Skipping setting up cron recovery for supervisor.")
            return
        _unique_comment_string = f"supervisor_{_current_agent_port}"
        for _current_job in _current_crontab:
            if _current_job.comment == _unique_comment_string:
                ebLogInfo(f"Removing recovery cron with comment {_unique_comment_string}")
                _current_crontab.remove(_current_job)
                _current_crontab.write()
        _exacloud_base_path = get_gcontext().mGetBasePath()
        _start_cmd = f"{os.path.join(_exacloud_base_path, 'bin/exacloud')} -dc --supervisor"
        _python_exe = os.path.join(_exacloud_base_path, 'opt/py3_venv/bin/python')
        _check_script_cmd = f"{os.path.join(_exacloud_base_path, 'scripts/checkpid_and_restart.py')} -pid {os.getpid()} -sc \"{_start_cmd}\""
        _cron_command = f"{_python_exe} {_check_script_cmd} >/tmp/supervisor_{_current_agent_port}_restart_command.log 2>&1"
        ebLogInfo(f"Setting up recovery cron with command '{_cron_command}' and comment {_unique_comment_string}")
        _new_job = _current_crontab.new(command=_cron_command, comment=_unique_comment_string)
        _new_job.minute.every(1)
        _current_crontab.write()

    @staticmethod
    def mDeleteCrontab():
        _is_exacc = get_gcontext().mCheckConfigOption('ociexacc', "True")
        _supervisor_fail_recovery_enabled = get_gcontext().mCheckConfigOption('supervisor_fail_recovery', "True")
        if _is_exacc or not _supervisor_fail_recovery_enabled:
            return False
        _current_crontab = CronTab(user=getpass.getuser())
        _coptions = get_gcontext().mGetConfigOptions()
        _current_agent_port = _coptions.get("agent_port", None)
        if _current_agent_port is None:
            ebLogWarn("agent port not found. Skip removal of cron recovery for supervisor.")
            return False
        _unique_comment_string = f"supervisor_{_current_agent_port}"
        for _current_job in _current_crontab:
            if _current_job.comment == _unique_comment_string:
                ebLogInfo(f"Removing recovery cron with comment {_unique_comment_string}")
                _current_crontab.remove(_current_job)
                _current_crontab.write()
                return True
        return False

    def mCheckAgentStatus(self):
        if not self._running:
            ebLogWarn("Supervisor has been asked to gracefully shutdown. skipping restart of exacloud agent.")
            return
        _current_time = datetime.datetime.now()
        if _current_time < self._healthcheckstart:
            return
        _new_options = get_gcontext().mGetArgsOptions()
        _new_options.agent = "status"
        _client = ebExaClient()
        ebLogTrace("Agent status request in progress.")
        _client.mIssueRequest(aCmd=None,aOptions=_new_options, aRetryCount=1)
        ebLogTrace("Agent status request completed.")
        _client.mWaitForCompletion()
        _response = _client.mGetJsonResponse()
        _agentcfg = ebGetClientConfig()
        if _response is not None and _response.get('success', None) == 'True':
            ebLogTrace(f"Exacloud agent ({_agentcfg[0]}, {_agentcfg[1]}) is running and reachable.")
        else:
            ebLogError(f"Could not contact exacloud agent through REST service at ({_agentcfg[0]}, {_agentcfg[1]}) .")
            _restart_agent = False
            _current_agent_pid = int(self._db.mGetAgentsPID()[0][0])
            try:
                _agent_process = psutil.Process(_current_agent_pid)
                if _agent_process.status() in [psutil.STATUS_STOPPED, psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                    ebLogError(f"Current agent process is in {_agent_process.status} state. Will attempt to restart exacloud agent.")
                    _restart_agent = True
                _children_procs = _agent_process.children(recursive=True)
                if len(_children_procs) == 0:
                    ebLogError(f"Current agent process has no listenining processes. Will attempt to restart exacloud agent.")
                    _restart_agent = True
                else:
                    _count_invalid_listeners = 0
                    for _child_proc in _children_procs:
                        if _child_proc.status() in [psutil.STATUS_STOPPED, psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                            _count_invalid_listeners += 1

                    if len(_children_procs) == _count_invalid_listeners:
                        ebLogError(f"No active listener process available with the exacloud agent. Will attempt to restart exacloud agent.")
                        _restart_agent = True
            except psutil.NoSuchProcess:
                ebLogError(f"Agent PID listed in DB {_current_agent_pid} doesn't exist. Will attempt to restart exacloud agent.")
                _restart_agent = True

            if _restart_agent:
                _exacloud_base_path = get_gcontext().mGetBasePath()
                _stop_cmd = f"{os.path.join(_exacloud_base_path, 'bin/exacloud')} --agent stop"
                ebLogInfo(f"Stopping exacloud agent using {_stop_cmd}")
                self.mTriggerCommand(_stop_cmd)

                _start_cmd = f"{os.path.join(_exacloud_base_path, 'bin/exacloud')} --agent start -da -nosup"
                ebLogInfo(f"Starting exacloud agent using {_start_cmd}")
                self.mTriggerCommand(_start_cmd)

                self._healthcheckstart = datetime.datetime.now() + datetime.timedelta(minutes = 2)
            else:
                ebLogTrace("Exacloud agent is up and running but is busy.")

    def mCheckScheduler(self):
        if not self._running:
            ebLogWarn("Supervisor has been signaled to stop, skipping restart of scheduler.")
            return
        _current_time = datetime.datetime.now()
        if _current_time < self._healthcheckstart:
            return
        _db_data = self._db.mGetWorkerByType("scheduler")
        if _db_data:
            _scheduler_worker = ebWorker()
            _scheduler_worker.mPopulate(_db_data)
            _scheduler_pid = _scheduler_worker.mGetPid()
        if not _db_data or not psutil.pid_exists(int(_scheduler_pid)):
            ebLogError(f"Scheduler process does not exist. Will attempt to restart the same.")
            _exacloud_base_path = get_gcontext().mGetBasePath()
            _start_cmd = f"{os.path.join(_exacloud_base_path, 'bin/exacloud')} -dc --scheduler"
            self.mTriggerCommand(_start_cmd)
            self._healthcheckstart = datetime.datetime.now() + datetime.timedelta(minutes = 1)
        else:
            ebLogTrace(f"Scheduler with PID {_scheduler_pid} is up and running.")

    def mCheckDispatcher(self):
        if not self._running:
            ebLogWarn("Supervisor has been signaled to stop, skipping restart of dispatcher.")
            return
        _db_data = self._db.mGetWorkerByType("dispatcher")
        if _db_data:
            _dispatcher_worker = ebWorker()
            _dispatcher_worker.mPopulate(_db_data)
            _dispatcher_pid = _dispatcher_worker.mGetPid()
        if not _db_data or not psutil.pid_exists(int(_dispatcher_pid)):
            ebLogError(f"dispatcher process does not exist. Will attempt to restart the same.")
            _exacloud_base_path = get_gcontext().mGetBasePath()
            _start_cmd = f"{os.path.join(_exacloud_base_path, 'bin/exacloud')} -dc --dispatcher"
            self.mTriggerCommand(_start_cmd)
        else:
            ebLogTrace(f"Dispatcher with PID {_dispatcher_pid} is up and running.")

    def mCheckWrkManager(self):
        if not self._running:
            ebLogWarn("Supervisor has been signaled to stop, skipping restart of workermanager.")
            return
        _db_data = self._db.mGetWorkerByType("workermanager")
        if _db_data:
            _workermanager_worker = ebWorker()
            _workermanager_worker.mPopulate(_db_data)
            _workermanager_pid = _workermanager_worker.mGetPid()
        if not _db_data or not psutil.pid_exists(int(_workermanager_pid)):
            ebLogError(f"workermanager process does not exist. Will attempt to restart the same.")
            _exacloud_base_path = get_gcontext().mGetBasePath()
            _start_cmd = f"{os.path.join(_exacloud_base_path, 'bin/exacloud')} -dc --workermanager"
            self.mTriggerCommand(_start_cmd)
        else:
            ebLogTrace(f"workermanager with PID {_workermanager_pid} is up and running.")

    def mTriggerCommand(self, aCommand):
        _command_to_execute = aCommand
        ebLogInfo(f"Executing '{_command_to_execute}' asynchronously.")
        _args = shlex.split(_command_to_execute)
        _process_handle = Popen(_args)
        _std_out, _std_err = wrapStrBytesFunctions(_process_handle).communicate(timeout=300)
        _rc = _process_handle.returncode
        ebLogInfo(f"STDOUT messages: {_std_out}, STDERR messages: {_std_err}")
        if _rc != 0:
            ebLogError(f"Error occured during executing {_command_to_execute}")
        else:
            ebLogInfo(f"Successfully executed {_command_to_execute}")

    def mIsRunning(self):
        return self._running

    def mStart(self):
        #Daemonize Supervisor
        daemonize_process()
        redirect_std_descriptors()
        # Initialize after Fork
        self._db = ebGetDefaultDB()
        self._request_backup_context = RequestsBackupContext()
        pid = supervisor_running()
        if pid:
            ebLogWarn('Supervisor is already running with PID {0}'.format(pid))
            exit(1)
        else:
            if get_db_version() == 3:
                #Supervisor will be in charge of starting DB, it cannot wait 1h30
                self._db.mSetWaitAndRetry(False)
            worker = ebWorker(aDB=self._db)
            worker.mSetUUID(uuid.uuid4())
            worker.mSetStatus('Supervising')
            worker.mSetType('supervisor')
            worker.mSetPort(self._port)
            dbworker = self._db.mGetWorkerByType('supervisor')
            if dbworker:
                self._db.mUpdateWorker(worker)
            else:
                self._db.mInsertNewWorker(worker)

        ebLogAddDestinationToLoggers([ebGetDefaultLoggerName()], 'log/workers/dflt_supervisor', ebFormattersEnum.DEFAULT)

        self._running = True
        _mysql_restart_count = 4
        _isExaCC = get_gcontext().mCheckConfigOption('ociexacc', "True")
        _supervisor_fail_recovery_enabled = get_gcontext().mCheckConfigOption('supervisor_fail_recovery', "True")
        if not _isExaCC and _supervisor_fail_recovery_enabled:
            self.mSetupCrontab()
            ebLogInfo("Allowing exacloud agent process to start up before supervisor resumes its activities. Sleeping for 60 seconds.")
            time.sleep(60)

        _coptions = get_gcontext().mGetConfigOptions()
        if 'cpu_threshold' in list(_coptions.keys()):
            self._cpu_threshold = float(_coptions['cpu_threshold'])
        if 'mem_threshold' in list(_coptions.keys()):
            self._mem_threshold = float(_coptions['mem_threshold'])
        if 'uuid_orphan_time_minutes' in list(_coptions.keys()):
            self._uuid_orphan_time_minutes = int(_coptions['uuid_orphan_time_minutes'])

        _agent_delegation_enabled = True
        if 'agent_delegation_enabled' in list(_coptions.keys()) and _coptions['agent_delegation_enabled'].upper() == 'FALSE':
            _agent_delegation_enabled = False

        ebLogInfo('Starting supervisor')
        ebLogInfo(f"Current resource statistics: CPU percent:{self._cpu_percent}, Memory percent:{self._memory_percent}")
        if not self._db.mInsertEnvironmentResourceDetails(self._cpu_percent, self._memory_percent):
            ebLogWarn("Unsuccessful insert for environment resource statistics.")

        while self._running:
            # First verify MySQL is running
            if get_db_version() == 3 and not self._db.mIsMySQLRunning():
                try:
                    self._db.mGetDriver().mStart()
                    _mysql_restart_count = 4  # Restore retry value
                except Exception as e:
                    if _mysql_restart_count > 0:
                        ebLogWarn(f'MySQL Startup failed: {e}, retrying')
                        _mysql_restart_count -= 1
                    else:
                        raise
            try:
                for req in self._db.mOrphanRequests():
                    _stime = datetime.datetime.strptime(req[2], '%c')
                    #Lets wait till the job can be considered as orphan !
                    _stime = _stime + datetime.timedelta(minutes = self._uuid_orphan_time_minutes)
                    _nowtime = datetime.datetime.now()
                    if(_stime > _nowtime):
                        ebLogTrace('Job with uuid: {0} will be cleaned up a little later'. format(req[0]))
                        continue
                    else:
                        ebLogInfo('Will attempt to cleanup job: {0}'.format(req[0]))
    
                    job = ebJobRequest(req[4], ast.literal_eval(req[5]), aDB=ebGetDefaultDB())
                    job.mLoadRequestFromDB(req[0])
    
                    _params = ast.literal_eval(req[5])
                    _jconf = _params['jsonconf'] if 'jsonconf' in _params else None
    
                    if _jconf is not None and isinstance(_jconf,dict) and 'scheduler_job' in list(_jconf.keys()):
                        if job.mGetStatus() == 'Done':
                            self._db.mUpdateRequest(job)
                            self._db.mDelRegByUUID(job.mGetUUID())
                            ebLogWarn('Cleaning scheduler job {0}'.format(job.mGetUUID()))
                    else:
                        job.mSetError(709)
                        job.mSetErrorStr('Critical Exception caught aborting request')
                        job.mSetStatus('Done')
                        self._db.mUpdateRequest(job)
                        self._db.mDelRegByUUID(job.mGetUUID())
                        ebLogWarn('Cleaning orphan job {0}'.format(job.mGetUUID()))
    
                self._request_backup_context.mEvaluate()
                self.mUpdateResourceUtilisationInfo()
                if _agent_delegation_enabled:
                    self.mCheckDispatcher()
                    self.mCheckWrkManager()
                else:
                    #By default, logic for mManageWorkers is executed in workermanager process.
                    #But, only if this feature is disabled, this should be executed in supervisor context.
                    self.mManageWorkers()
                if not _isExaCC and _supervisor_fail_recovery_enabled:
                    self.mCheckAgentStatus()
                    self.mCheckScheduler()
            #If MYSQL is DOWN, no cleanup can be done, but trying to start MySQL can
            except StopMySQLConnRetryException:
                ebLogInfo('Supervisor detected MySQL database is DOWN')
            except Exception as excep:
                ebLogError(f"Supervisor main loop caught an exception, please review {excep}")
                    
            self._notify.wait(self._timeout)

        if not _isExaCC and _supervisor_fail_recovery_enabled:
            ebSupervisor.mDeleteCrontab()
        ebLogInfo('Exiting supervisor')

    def mLogTopStatsSorted(self, aSortby='CPU'):

        _cmd = f'/bin/top -b -n 1 -o %{aSortby}'
        eboxNodeObject = exaBoxNode(get_gcontext())
        _rc, _, _o, _ = eboxNodeObject.mExecuteLocal(_cmd)
        if _rc == 0:
            _lines = _o.split('\n')
            _ite = 0
            ebLogTrace(f'mLogTopStatsSorted: Logging stats for {aSortby}')
            for _line in _lines:
                ebLogTrace(f"{_line}")
                if _ite > 30:
                    #We are already short on mem/cpu resources!
                    #So, lets not strain the system more.
                    #Hence, lets limit to printing only top 25 procesess. This should suffice.
                    break
                _ite += 1


    def mUpdateResourceUtilisationInfo(self):

        _db_cpu_percent, _db_mem_percent, _last_update_time = self._db.mSelectAllFromEnvironmentResourceDetails()
        if _db_cpu_percent == None and _db_mem_percent == None and _last_update_time == None:
            self._db.mInsertEnvironmentResourceDetails(self._cpu_percent, self._memory_percent)
        else:
            _stime = datetime.datetime.strptime(_last_update_time, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(minutes = 1)
            _nowtime = datetime.datetime.now()
            if _nowtime > _stime:
                self._cpu_percent = psutil.cpu_percent()
                self._memory_percent = psutil.virtual_memory().percent

                if(float(self._cpu_percent) > self._cpu_threshold):
                    #Lets log the processes which are hogging the cpu
                    for i in range(5):
                        #There can sometimes be a one-off spike
                        #Hence, Lets sample it every second for 5 times.
                        self.mLogTopStatsSorted(aSortby='CPU')
                        time.sleep(1)
                if(float(self._memory_percent) > self._mem_threshold):
                    #Lets log the processes which are hogging the memory
                    for i in range(5):
                        self.mLogTopStatsSorted(aSortby='MEM')
                        time.sleep(1)
                
                ebLogInfo(f"Updating environment resource statistics to CPU percent:{self._cpu_percent} Memory percent:{self._memory_percent}")
                if not self._db.mUpdateEnvironmentResourceDetails(self._cpu_percent, self._memory_percent):
                    ebLogWarn("Unsuccessful update for environment resource statistics.")

    def mGetCorruptedWorkersForTermination(self):
        _rqlist = ast.literal_eval(self._db.mDumpWorkers("00000000-0000-0000-0000-000000000000"))
        _list_of_workers_to_terminate = list()
        for _worker in _rqlist:
            if _worker[13] == "CORRUPTED":
                _port = _worker[9]
                ebLogInfo(f"Worker with port {_port} is corrupted and is selected for termination.")
                _list_of_workers_to_terminate.append(_port)

        return _list_of_workers_to_terminate

    def mGetIdleWorkerCount(self, _coptions):
        _idle_wc = 0

        #exacc type env
        if 'ociexacc' in _coptions:
            if _coptions['ociexacc'] == "True":
                if 'idle_worker_count_nonexacs' in _coptions:
                    _idle_wc = int(_coptions['idle_worker_count_nonexacs'])

        #exacs type env
        if _idle_wc == 0 and 'deployment_target_type' in _coptions:
            if _coptions['deployment_target_type'] == "prod":
                if 'idle_worker_count' in _coptions:
                    _idle_wc = int(_coptions['idle_worker_count'])

        #dev type env
        if _idle_wc == 0:
            if 'idle_worker_count_nonexacs' in _coptions:
                _idle_wc = int(_coptions['idle_worker_count_nonexacs'])
            else:
                _idle_wc = 4

        return _idle_wc

    def mGetIdleWorkersForTermination(self):
        _coptions = get_gcontext().mGetConfigOptions()
        _rqlist = ast.literal_eval(self._db.mDumpWorkers("00000000-0000-0000-0000-000000000000"))
        _idle_wc = self.mGetIdleWorkerCount(_coptions)

        _workers_to_terminate = 0
        if len(_rqlist) > _idle_wc:
            _workers_to_terminate = len(_rqlist) - _idle_wc
        else:
            return []

        _list_of_workers_to_terminate = list()
        _workers_selected = 0
        for _worker in _rqlist:
            if _worker[1] == 'Idle':
                _lastactivetime = _worker[12]
                _port = _worker[9]
                _stime = datetime.datetime.strptime(_lastactivetime, '%Y-%m-%d %H:%M:%S.%f') + datetime.timedelta(minutes = 60)
                _nowtime = datetime.datetime.now()
                if _nowtime > _stime and _workers_selected < _workers_to_terminate:
                    ebLogInfo(f"Worker with port {_port} queued to be killed.")
                    _list_of_workers_to_terminate.append(_port)
                    _workers_selected += 1

        return _list_of_workers_to_terminate

    def mManageWorkers(self):

        _worker_list_compute_methods = [self.mGetCorruptedWorkersForTermination, self.mGetIdleWorkersForTermination]
        for _method in _worker_list_compute_methods:
            _list_of_workers_to_terminate = _method()

            for _port in _list_of_workers_to_terminate:
                _worker = ebWorker(aDB=self._db)
                _worker.mLoadWorkerFromDB(_port)
                if _worker.mAcquireSyncLock("Supervisor"):
                    if _worker.mGetUUID() != "00000000-0000-0000-0000-000000000000":
                        ebLogWarn(f"Worker with port {_port} has an active request associated with it, cancelling termination.")
                        _worker.mReleaseSyncLock("Supervisor")
                        continue
                    ebLogInfo(f"*** Shutdown Worker on port: {_port}")
                    try:
                        _workercmd = ebWorkerCmd(aCmd='shutdown',aPort=_port)
                        _workercmd.mIssueRequest()
                        _workercmd.mWaitForCompletion()
                        _killed = False
                        _retry = 2
                        while _retry > 0:
                            _worker_list = ast.literal_eval(self._db.mDumpWorkers("00000000-0000-0000-0000-000000000000"))
                            _retry -= 1
                            for curr_worker in _worker_list:
                                if curr_worker[9] == _port and curr_worker[1] == 'Exited':
                                    _killed = True
                                    break
                            if _killed:
                                ebLogInfo(f"*** Worker running on port {_port} has been successfully shutdown.")
                                break
                            time.sleep(2)
                        if not _killed:
                            ebLogWarn(f"*** Worker running on port {_port} has not been shutdown.")
                    except:
                        ebLogWarn(f"Failed to stop worker running at port {_port}.")
                    _worker.mReleaseSyncLock("Supervisor")
                else:
                    ebLogWarn(f"*** Supervisor lock on worker running on port {_port} could not be obtained.")

    def mStop(self):
        self._running = False
        self._timeout = 0
        worker = ebWorker(aDB=self._db)
        worker.mSetUUID(uuid.uuid4())
        worker.mSetType('supervisor')
        worker.mSetPort(self._port)
        worker.mSetStatus('Exited')
        self._db.mUpdateWorker(worker)
        self._notify.set()

    def _mSigHandler(self, signum, frame):
        ebLogInfo('Handling signal {0}'.format(signum))
        self.mStop()


def supervisor_running():
    db = ebGetDefaultDB()
    supervisor = db.mGetWorkerByType('supervisor')
    if supervisor:
        pid = supervisor[8]
        if psutil.pid_exists(int(pid)):
            return pid
    return ''


def stop():
    pid = supervisor_running()
    if pid:
        os.kill(int(pid), signal.SIGTERM)
