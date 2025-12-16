"""
$Header:

 Copyright (c) 2017, 2025, Oracle and/or its affiliates.

NAME:


NAME:
    Dispatcher - Dispatch jobs to workers 

FUNCTION:
    Ensure all uuids requests are dispatched

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
       shapatna 10/08/25 - Close open sockets caused by initiating Database
                           connection
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
import psutil
import random
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.DBStore import get_db_version, ebGetDefaultDB
from exabox.core.DBStore3 import StopMySQLConnRetryException
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogError, ebLogAddDestinationToLoggers, ebGetDefaultLoggerName, ebFormattersEnum
from exabox.agent.Worker import daemonize_process, redirect_std_descriptors
from exabox.agent.WClient import ebWorkerCmd
from exabox.core.Context import get_gcontext
from exabox.agent.Worker import ebWorkerFactory, ebWorker, gGetDefaultWorkerFactory

class ebDispatcher(object):
    _port = 66666

    def __init__(self, timeout=1):
        self._db = None
        self._timeout = timeout
        self._running = False
        self._worker_factory = ebWorkerFactory()
        self._notify = threading.Event()
        signal.signal(signal.SIGINT, self._mSigHandler)
        signal.signal(signal.SIGTERM, self._mSigHandler)

    def mIsRunning(self):
        return self._running

    def mStart(self):
        daemonize_process()
        redirect_std_descriptors()
        # Initialize after Fork
        self._db = ebGetDefaultDB()
        pid = dispatcher_running(aDB=self._db)
        if pid:
            ebLogWarn(f'Dispatcher is already running with PID {pid}')
            exit(1)
        else:
            worker = ebWorker(aDB=self._db)
            worker.mSetUUID(uuid.uuid4())
            worker.mSetStatus('Dispatching')
            worker.mSetType('dispatcher')
            worker.mSetPort(self._port)
            dbworker = self._db.mGetWorkerByType('dispatcher')
            if dbworker:
                self._db.mUpdateWorker(worker)
            else:
                self._db.mInsertNewWorker(worker)

        ebLogAddDestinationToLoggers([ebGetDefaultLoggerName()], 'log/workers/dflt_dispatcher', ebFormattersEnum.DEFAULT)
        ebLogInfo('Starting dispatcher')

        self._running = True
        while self._running:
            self.mDispatcher()
            self._notify.wait(self._timeout)
        ebLogInfo('Exiting dispatcher')


    def mDispatcher(self):
        _idle_uuid = '00000000-0000-0000-0000-000000000000'
        _uuid = '00000000-0000-0000-0000-000000000000'
        _worker_assigned = False
        _port = 0
        _pid = 0
        _thisWorker = None
        _worker_lock_acquired = False

        _row = self._db.mGetPendingRequest()
        if _row and len(_row):
            _uuid = _row[0]
            ebLogInfo(f'mDispatcher: Finding a worker for uuid {_uuid}')
        else:
            return

        try:
            while _worker_assigned is False:
                _idleworkers = ast.literal_eval(self._db.mGetIdleWorkers())
                _random_idle_workers = random.sample(_idleworkers, k = len(_idleworkers))
                for _worker in _random_idle_workers:
                    _port = _worker[9]
                    _pid = _worker[8]
                    if _port == 0 or _pid == 0:
                        ebLogWarn(f'mDispatcher: Invalid worker present with port {_port} and pid {_pid}')
                        continue

                    _thisWorker = ebWorker(aDB=self._db)
                    _thisWorker.mLoadWorkerFromDB(int(_worker[9]))
                    if _thisWorker.mAcquireSyncLock("Dispatcher"):
                        _worker_lock_acquired = True
                        break

                if _thisWorker is None:
                    ebLogWarn('Unable to get a worker yet.. Will try again after 1 sec')
                    if _worker_lock_acquired:
                        _thisWorker.mReleaseSyncLock("Dispatcher")
                        _worker_lock_acquired = False
                    time.sleep(1)
                    continue

                ebLogInfo('*** LOADING WORKER')
                _thisWorker.mSetUUID(_uuid)
                _thisWorker.mUpdateDB()
                ebLogInfo(f"Request with UUID: {_uuid} is allocated to worker with port {_port}")
                _worker_assigned = True
        except Exception as e: 
            ebLogError(f"*** mDispatcher: Exception occured while dispatching request {_uuid}, Exception:{e}")
        finally:
            if _worker_lock_acquired: 
                if _thisWorker.mReleaseSyncLock("Dispatcher") == False:
                    ebLogError(f"*** mDispatcher: Unable to release lock !!!")

    def mStop(self):
        self._running = False
        self._timeout = 0
        worker = ebWorker(aDB=self._db)
        worker.mSetUUID(uuid.uuid4())
        worker.mSetType('dispatcher')
        worker.mSetPort(self._port)
        worker.mSetStatus('Exited')
        self._db.mUpdateWorker(worker)
        self._notify.set()

    def _mSigHandler(self, signum, frame):
        ebLogInfo('Handling signal {0}'.format(signum))
        self.mStop()


def dispatcher_running(aDB=None):
    if aDB:
        db = aDB
    else:
        db = ebGetDefaultDB()
    dispatcher = db.mGetWorkerByType('dispatcher')
    if dispatcher:
        pid = dispatcher[8]
        if os.path.exists('/proc/{0}'.format(pid)):
            with open('/proc/{0}/cmdline'.format(pid)) as fd:
                cmd = fd.read()
            if 'dispatcher' in cmd:
                return pid
    return ''


def stop():
    pid = dispatcher_running()
    if pid:
        os.kill(int(pid), signal.SIGTERM)
