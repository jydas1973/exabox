"""
$Header:

 Copyright (c) 2017, 2024, Oracle and/or its affiliates.

NAME:


NAME:
    WorkerManager - Manager workers including dynamic worker creation. 

FUNCTION:

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
"""
import json
import datetime
import os
import ast
import time
import uuid
import signal
import logging
import threading
from exabox.core.DBStore import get_db_version, ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogError, ebLogAddDestinationToLoggers, ebGetDefaultLoggerName, ebFormattersEnum
from exabox.agent.Worker import daemonize_process, redirect_std_descriptors
from exabox.agent.WClient import ebWorkerCmd
from exabox.core.Context import get_gcontext
from exabox.agent.Worker import ebWorkerFactory, ebWorker, gGetDefaultWorkerFactory

class ebWorkermanager(object):

    def __init__(self, timeout=1):
        self._db = None
        self._timeout = timeout
        self._running = False
        self._notify = threading.Event()
        signal.signal(signal.SIGINT, self._mSigHandler)
        signal.signal(signal.SIGTERM, self._mSigHandler)
        self._coptions = get_gcontext().mGetConfigOptions()
        self._worker_factory = ebWorkerFactory()
        self._port = 77777
        if 'workermanager_port' in list(self._coptions.keys()):
            self._port = int(self._coptions['workermanager_port'])
                
        self._worker_idle_timeout = "60"
        if 'worker_idle_timeout_minutes' in list(self._coptions.keys()):
            self._worker_idle_timeout = self._coptions['worker_idle_timeout_minutes']
        self._worker_idle_timeout = int(self._worker_idle_timeout)
        ebLogInfo(f'worker_idle_timeout is {self._worker_idle_timeout}')

        self._disable_cpu_mem_threshold = False
        self._cpu_threshold = 80.0
        self._mem_threshold = 80.0
        if 'disable_cpumem_threshold' in list(self._coptions.keys()) and self._coptions['disable_cpumem_threshold'].upper() == 'TRUE':
            self._disable_cpu_mem_threshold = True

        if 'cpu_threshold' in list(self._coptions.keys()):
            self._cpu_threshold = float(self._coptions['cpu_threshold'])

        if 'mem_threshold' in list(self._coptions.keys()):
            self._mem_threshold = float(self._coptions['mem_threshold'])

        self._idle_wc = 0
        self._idle_thread_pool_count = 0
        self.mGetWorkerCount()

    def mIsRunning(self):
        return self._running

    def mStart(self):
        daemonize_process()
        redirect_std_descriptors()
        # Initialize after Fork
        self._db = ebGetDefaultDB()
        pid = workermanager_running()
        if pid:
            ebLogWarn('worker manager is already running with PID {0}'.format(pid))
            exit(1)
        else:
            worker = ebWorker(aDB=self._db)
            worker.mSetUUID(uuid.uuid4())
            worker.mSetStatus('Wmanaging')
            worker.mSetType('workermanager')
            worker.mSetPort(self._port)
            dbworker = self._db.mGetWorkerByType('workermanager')
            if dbworker:
                self._db.mUpdateWorker(worker)
            else:
                self._db.mInsertNewWorker(worker)

        ebLogAddDestinationToLoggers([ebGetDefaultLoggerName()], 'log/workers/dflt_workermanager', ebFormattersEnum.DEFAULT)
        ebLogInfo('Starting workermanager')

        self._running = True

        while self._running:
            self.mWrkmanager()
            self._notify.wait(self._timeout)

        ebLogInfo('Exiting workermanager')


    def isAdditionalWorkerAllowed(self):
        if self._disable_cpu_mem_threshold:
            return True

        _cpu_percent, _mem_percent, _last_update_time = self._db.mSelectAllFromEnvironmentResourceDetails()
        ebLogInfo(f"Environment resource statistics, CPU: {_cpu_percent}, Memory: {_mem_percent}.")
        if _cpu_percent == None or _mem_percent == None:
            ebLogWarn(f"Invalid resource statistics.")
            return True
        else:
            if float(_cpu_percent) > self._cpu_threshold or float(_mem_percent) > self._mem_threshold:
                ebLogWarn(f"Environment utilisation threshold exceeded. No additional worker will be created if all workers are busy.")
                return False
            else:
                return True

    def mGetWorkerCount(self):
        #exacc type env
        if 'ociexacc' in self._coptions:
            if self._coptions['ociexacc'] == "True":
                if 'idle_worker_count_nonexacs' in self._coptions:
                    self._idle_wc = int(self._coptions['idle_worker_count_nonexacs'])
                if 'idle_thread_pool_count_nonexacs' in self._coptions:
                    self._idle_thread_pool_count = int(self._coptions['idle_thread_pool_count_nonexacs'])

        #exacs type env
        if self._idle_wc == 0 and 'deployment_target_type' in self._coptions:
            if self._coptions['deployment_target_type'] == "prod":
                if 'idle_worker_count' in self._coptions:
                    self._idle_wc = int(self._coptions['idle_worker_count'])
                if 'idle_thread_pool_count' in self._coptions:
                    self._idle_thread_pool_count = int(self._coptions['idle_thread_pool_count'])

        #dev type env
        if self._idle_wc == 0:
            if 'idle_worker_count_nonexacs' in self._coptions:
                self._idle_wc = int(self._coptions['idle_worker_count_nonexacs'])
            else:
                self._idle_wc = 4
            if 'idle_thread_pool_count_nonexacs' in self._coptions:
                self._idle_thread_pool_count = int(self._coptions['idle_thread_pool_count_nonexacs'])
            else:
                self._idle_thread_pool_count = 2


    def mGetCorruptedWorkersForTermination(self):
        _rqlist = ast.literal_eval(self._db.mDumpWorkers("00000000-0000-0000-0000-000000000000"))
        _list_of_workers_to_terminate = list()
        for _worker in _rqlist:
            if _worker[13] == "CORRUPTED":
                _port = _worker[9]
                ebLogInfo(f"Worker with port {_port} is corrupted and is selected for termination.")
                _list_of_workers_to_terminate.append(_port)

        return _list_of_workers_to_terminate

    def mGetIdleWorkersForTermination(self):
        _rqlist = ast.literal_eval(self._db.mDumpWorkers("00000000-0000-0000-0000-000000000000"))

        _workers_to_terminate = 0
        if len(_rqlist) > self._idle_wc:
            _workers_to_terminate = len(_rqlist) - self._idle_wc
        else:
            return []

        _list_of_workers_to_terminate = list()
        _workers_selected = 0
        for _worker in _rqlist:
            if _worker[1] == 'Idle':
                _lastactivetime = _worker[12]
                _port = _worker[9]
                _stime = datetime.datetime.strptime(_lastactivetime, '%Y-%m-%d %H:%M:%S.%f') + datetime.timedelta(minutes = self._worker_idle_timeout)
                _nowtime = datetime.datetime.now()
                if _nowtime > _stime and _workers_selected < _workers_to_terminate:
                    ebLogInfo(f"Worker with port {_port} queued to be killed.")
                    _list_of_workers_to_terminate.append(_port)
                    _workers_selected += 1

        return _list_of_workers_to_terminate

    def mWrkmanager(self):
        _idle_worker = 0
        _uuid = '00000000-0000-0000-0000-000000000000'
        _port = 0
        _pid = 0
        _new_worker_allowed = False

        self._worker_factory.mCheckFactory(self._db)
        self._worker_factory.mResetWorkersList(self._db)

        _rqlist = ast.literal_eval(self._db.mDumpWorkers())
        for _worker in _rqlist:
            if _worker[0] == _uuid and _worker[1] == 'Idle' and _worker[13] == "NORMAL":
                _idle_worker = _idle_worker + 1

        if _idle_worker < self._idle_thread_pool_count:
            _new_worker_allowed = self.isAdditionalWorkerAllowed()
            if _new_worker_allowed:
                _wf = gGetDefaultWorkerFactory()
                ebLogInfo(f'Begin: creating worker(s): {self._idle_thread_pool_count-_idle_worker} ')
                _wf.mStartWorkers(aWorkerCount=(self._idle_thread_pool_count-_idle_worker))
                ebLogInfo(f'End  : creating worker(s)')

        _worker_list_compute_methods = [self.mGetCorruptedWorkersForTermination, self.mGetIdleWorkersForTermination]
        for _method in _worker_list_compute_methods:
            _list_of_workers_to_terminate = _method()

            for _port in _list_of_workers_to_terminate:
                _worker = ebWorker(aDB=self._db)
                _worker.mLoadWorkerFromDB(_port)
                if _worker.mAcquireSyncLock("Wrkmanager"):
                    if _worker.mGetUUID() != "00000000-0000-0000-0000-000000000000":
                        ebLogWarn(f"Worker with port {_port} has an active request associated with it, cancelling termination.")
                        _worker.mReleaseSyncLock("Wrkmanager")
                        continue
                    ebLogInfo(f"*** Shutdown Worker on port: {_port}")
                    try:
                        _workercmd = ebWorkerCmd(aCmd='shutdown',aPort=_port)
                        _workercmd.mIssueRequest()
                        _workercmd.mWaitForCompletion()
                        _killed = False
                        _retry = 5
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
                    _worker.mReleaseSyncLock("Wrkmanager")
                else:
                    ebLogWarn(f"*** Wrkmanager lock on worker running on port {_port} could not be obtained.")


    def mStop(self):
        self._running = False
        self._timeout = 0
        worker = ebWorker(aDB=self._db)
        worker.mSetUUID(uuid.uuid4())
        worker.mSetType('workermanager')
        worker.mSetPort(self._port)
        worker.mSetStatus('Exited')
        self._db.mUpdateWorker(worker)
        self._notify.set()

    def _mSigHandler(self, signum, frame):
        ebLogInfo('Handling signal {0}'.format(signum))
        self.mStop()


def workermanager_running():
    db = ebGetDefaultDB()
    workermanager = db.mGetWorkerByType('workermanager')
    if workermanager:
        pid = workermanager[8]
        if os.path.exists('/proc/{0}'.format(pid)):
            with open('/proc/{0}/cmdline'.format(pid)) as fd:
                cmd = fd.read()
            if 'workermanager' in cmd:
                return pid
    return ''


def stop():
    pid = workermanager_running()
    if pid:
        os.kill(int(pid), signal.SIGTERM)
