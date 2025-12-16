"""
 Copyright (c) 2017, 2022, Oracle and/or its affiliates.

NAME:
    Schedular - Process monitoring schedule tasks

FUNCTION:
    Ensure the jobs status is consistent

NOTE:
    None

History:
    pbellary    07/09/2019 - Create file
"""

import os
import ast
import uuid
import time
import signal
import logging
import threading
import subprocess
import multiprocessing

from datetime import datetime, timedelta
from multiprocessing import Process
from exabox.agent.Agent import ebScheduleInfo, dispatchJobToWorker
from exabox.agent.ExaLock import ExaLock
from exabox.log.LogMgr import   (ebLogInfo, ebLogWarn, ebLogError, ebLogVerbose,
                                ebLogAddDestinationToLoggers, ebGetDefaultLoggerName, ebFormattersEnum)
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.agent.Worker import ebWorker, gGetDefaultWorkerFactory
from exabox.agent.Worker import daemonize_process, redirect_std_descriptors
from exabox.core.DBStore import ebGetDefaultDB
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure

def process_timer_jobs(aEvent):
    ebLogInfo("*** Process Timer Jobs")

    _event = aEvent
    _db = ebGetDefaultDB()

    while True:
        event_is_set = _event.wait()

        with ExaLock("scheduler_lock"):
            _db = ebGetDefaultDB()
            _rc = _db.mGetSchedule()

        for _iter in range(0, len(_rc)):

            _uuid = _rc[_iter][0]
            _mode = _rc[_iter][2]
            _job_type = _rc[_iter][4]
            _timer_type = _rc[_iter][5]
            _timestamp = _rc[_iter][6]

            ebLogVerbose("_job_type:{}".format(_job_type))
            if _job_type != 'timer_job':
                continue

            _time = datetime.strptime(_timestamp, '%Y-%m-%d %H:%M:%S')
            ebLogVerbose("_time:{}".format(_time))

            _sched_time = _time - datetime.now()
            _timeeout = _sched_time.total_seconds()

            if _timeeout <= 0:
                request_handler(_uuid)
        _event.clear()

def request_handler(aUUID):
    ebLogInfo('*** Request handler invoked...')

    _uuid = aUUID
    _db = ebGetDefaultDB()

    with ExaLock("scheduler_lock"):
        _sched_info = ebScheduleInfo(_uuid, _db)
        _sched_info.mLoadScheduleTaskFromDB(_uuid)
        _mode = _sched_info.mGetScheduleMode()
        _repeatCount = _sched_info.mGetScheduleRepeatCount()
        _lastrepeatCount = _sched_info.mGetScheduleLastRepeatCount()
        _timer_type = _sched_info.mGetScheduleTimerType()
        _interval = _sched_info.mGetScheduleInterval()

        _req = ebJobRequest(None, {}, aDB=_db)
        _req.mLoadRequestFromDB(_uuid)
        if _mode == 'generic':
            dispatchInternalJob(_uuid)
            _req.mSetStatus('Done')
            _db.mUpdateRequest(_req)
        else:
            dispatchJobToWorker(_req)

        if _timer_type == 'repeat' and (_repeatCount == 'forever' or _lastrepeatCount < int(_repeatCount)):
            _lastrepeatCount = _lastrepeatCount + 1
            _sched_info.mSetScheduleLastRepeatCount(_lastrepeatCount)

        _db.mUpdateSchedule(_sched_info)
        update_schedule_archive(_sched_info)

        if _timer_type == 'once':
            _db.mDelScheduleEntry(_sched_info)
        elif _timer_type == 'repeat':
            _hours, _min, _sec = list(map(int, _interval.split(':')))
            _repeat_interval = (_hours * 60 * 60) + (_min * 60) + _sec
            _datetime_obj = datetime.now() + timedelta(seconds=_repeat_interval)
            _timestamp = _datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

            if _repeatCount == 'forever' or _lastrepeatCount < int(_repeatCount):
                _sched_info.mSetScheduleTimestamp(_timestamp)
                _db.mUpdateSchedule(_sched_info)
            elif _lastrepeatCount == int(_repeatCount):
                _db.mDelScheduleEntry(_sched_info)

def dispatchInternalJob(aUUID):

    def _process_Job(aUUID):
       _uuid = aUUID

       _db = ebGetDefaultDB()
       _sched_info = ebScheduleInfo(_uuid, _db)
       _sched_info.mLoadScheduleTaskFromDB(_uuid)
       _command = _sched_info.mGetScheduleCommand()
       _path =  'exabox/scheduleJobs/'

       try:
           _args = _command.split(' ')
           _args.insert(0, 'bin/python')
           _path = _path + _args[1] + '.py'
           _args[1] = os.path.abspath(_path)
           _rc = subprocess.call(_args)
       except Exception as e:
           ebLogError('>>> '+str(e))

    _plist = ProcessManager()
    _p = ProcessStructure(_process_Job, [aUUID,])
    _p.mSetMaxExecutionTime(30*60) # 30 minutes
    _p.mSetJoinTimeout(60)
    _p.mSetLogTimeoutFx(ebLogWarn)
    _plist.mStartAppend(_p)

    #Terminate the process if is still alive
    _plist.mJoinProcess()

def update_schedule_archive(aSchedInfo):

    _db = ebGetDefaultDB()
    _sched_info = aSchedInfo
    _uuid = _sched_info.mGetUUID()

    _ret = _db.mGetScheduleArchiveByType(_uuid)
    if _ret:
        _db.mUpdateScheduleArchive(_sched_info)
    else:
        _db.mInsertNewScheduleArchive(_sched_info)

def get_schedule_info(aSchedInfo):

    _rc = aSchedInfo
    _db = ebGetDefaultDB()
    _uuid, _command, _mode, _operation, _job_type, _timer_type, _timestamp, _interval, _repeatCount, _lastrepeatCount, _monitorUUID, _monitorWorkerJobs, _status =  ( _rc[0], _rc[1], _rc[2], _rc[3], _rc[4], _rc[5], _rc[6], _rc[7], _rc[8], _rc[9], _rc[10], _rc[11], _rc[12])

    _sched_info = ebScheduleInfo(_uuid, _db)
    _sched_info.mSetScheduleCommand(_command)
    _sched_info.mSetScheduleMode(_mode)
    _sched_info.mSetScheduleOperation(_operation)
    _sched_info.mSetScheduleEvent(_job_type)
    _sched_info.mSetScheduleTimerType(_timer_type)
    _sched_info.mSetScheduleTimestamp(_timestamp)
    _sched_info.mSetScheduleInterval(_interval)
    _sched_info.mSetScheduleRepeatCount(_repeatCount)
    _sched_info.mSetScheduleLastRepeatCount(_lastrepeatCount)
    _sched_info.mSetScheduleMonitorUUID(_monitorUUID)
    _sched_info.mSetScheduleMonitorWorkerJobs(_monitorWorkerJobs)

    if _status == 'Idle':
        _sched_info.mSetScheduleStatus('Pending')
    else:
        _sched_info.mSetScheduleStatus(_status)

    return _sched_info

def get_worker_status(aMonitorJobs):

    _db = ebGetDefaultDB()
    _monitor_jobs = aMonitorJobs
    _rc = False

    _critical_jobs = [ 'cluctrl.vmgi_install', 'cluctrl.vmgi_preprov', 'cluctrl.db_install', 'cluctrl.vm_install', 'cluctrl.vmgi_reconfig', 'cluctrl.dg_fresh_setup', 'cluctrl.gi_install', 'cluctrl.vmgi_rollback', 'cluctrl.createservice' ]

    _rqlist = _db.mGetWorkerStatus()
    _reqobj = [ _req  for _req in _rqlist if 'Running' in _req ]
    if _monitor_jobs == 'all':
        _rc = True if _reqobj else False
    elif _monitor_jobs == 'critical':
        for _req in _reqobj:
            if _req[4] in _critical_jobs:
                return True
    return  _rc

def scheduler_running():
    db = ebGetDefaultDB()
    scheduler = db.mGetWorkerByType('scheduler')
    if scheduler:
        pid = scheduler[8]
        if os.path.exists('/proc/{0}'.format(pid)):
            with open('/proc/{0}/cmdline'.format(pid)) as fd:
                try:
                    cmd = fd.read()
                except IOError as e:
                    return ''
            if 'scheduler' in cmd:
                return pid
    return ''

def stop():
    pid = scheduler_running()
    if pid:
        os.kill(int(pid), signal.SIGTERM)

class ebScheduler(object):
    _port = 44444

    def __init__(self, timeout=60):
        self._db = None
        self._timeout = timeout
        self._running = False
        self._notify = threading.Event()
        self.__process = None

        self.__event = multiprocessing.Event()
        signal.signal(signal.SIGINT, self._mSigHandler)
        signal.signal(signal.SIGTERM, self._mSigHandler)
        signal.signal(signal.SIGUSR1, self._mSigHandler)

    def mProcessFollowupJobs(self, aSchedInfo):
        ebLogInfo("*** Process Followup Jobs")

        _rc = aSchedInfo
        _uuid = _rc[0]
        _monitorUUID = _rc[10]
        _db = ebGetDefaultDB()
        _monitor_req = _db.mGetRequest(_monitorUUID)
        _status = _monitor_req[1]
        _error = _monitor_req[6]
        _error_str = _monitor_req[7]
        if _status == 'Done' and _error == '0' and _error_str == 'No Errors':
           _req = ebJobRequest(None, {}, aDB=_db)
           _req.mLoadRequestFromDB(_uuid)
           dispatchJobToWorker(_req)

           _rc = _db.mGetScheduleByType(_uuid)
           _sched_info = get_schedule_info(_rc)
           update_schedule_archive(_sched_info)
           _db.mDelScheduleEntry(_sched_info)
        elif _status == 'Done' and _error != '0' and _error_str != 'No Errors':
           _rc = _db.mGetScheduleByType(_uuid)
           _sched_info = get_schedule_info(_rc)
           update_schedule_archive(_sched_info)
           _db.mDelScheduleEntry(_sched_info)

    def mProcessNoactiveJobs(self, aSchedInfo):

        _db = ebGetDefaultDB()
        _rc = aSchedInfo
        _uuid = _rc[0]
        _monitorWorkerJobs = _rc[11]

        _active_jobs = get_worker_status(_monitorWorkerJobs)
        if _active_jobs:
            ebLogInfo("*** Active Job Running:{}".format(_active_jobs))
        else:
            ebLogInfo("*** No Active Jobs Running:{}".format(_active_jobs))

            _req = ebJobRequest(None, {}, aDB=_db)
            _req.mLoadRequestFromDB(_uuid)
            dispatchJobToWorker(_req)

            _sched_info = get_schedule_info(_rc)
            update_schedule_archive(_sched_info)
            _db.mDelScheduleEntry(_sched_info)

    def mStart(self):
        #Daemonize Scheduler
        daemonize_process()
        redirect_std_descriptors()

        self._db = ebGetDefaultDB()
        pid = scheduler_running()
        if pid:
            ebLogWarn('Scheduler is already running with PID {0}'.format(pid))
            exit(1)
        else:
            worker = ebWorker(aDB=self._db)
            worker.mSetUUID(uuid.uuid4())
            worker.mSetType('scheduler')
            worker.mSetStatus('Scheduler')
            worker.mSetPort(self._port)
            dbworker = self._db.mGetWorkerByType('scheduler')
            if dbworker:
                self._db.mUpdateWorker(worker)
            else:
                self._db.mInsertNewWorker(worker)

        ebLogAddDestinationToLoggers([ebGetDefaultLoggerName()], 'log/workers/dflt_schedule', ebFormattersEnum.DEFAULT)

        ebLogInfo('Starting scheduler')

        self._running = True
        while self._running:
            with ExaLock("scheduler_lock"):
                _rc = self._db.mGetSchedule()

            for _iter in range(0, len(_rc)):

                _sched_parms = ( _rc[_iter][0], _rc[_iter][1], _rc[_iter][2],_rc[_iter][3], _rc[_iter][4], _rc[_iter][5],
                                _rc[_iter][6],  _rc[_iter][7], _rc[_iter][8], _rc[_iter][9], _rc[_iter][10], _rc[_iter][11], _rc[_iter][12] )
                _job_type = _rc[_iter][4]

                if _job_type == 'timer_job':
                    if not self.__process:
                        self.__process = multiprocessing.Process(name='blocking', target=process_timer_jobs, args=(self.__event, ))
                        self.__process.start()
                elif _job_type == 'follow_up_job':
                    self.mProcessFollowupJobs(_sched_parms)
                elif _job_type == 'no_active_jobs':
                    self.mProcessNoactiveJobs(_sched_parms)
            self._notify.wait(self._timeout)
            if self.__process:
                self.__event.set()

        ebLogInfo('Exiting schedular')

    def mStop(self):
        self._running = False
        self._timeout = 0
        self.__process.terminate()
        worker = ebWorker(aDB=self._db)
        worker.mSetUUID(uuid.uuid4())
        worker.mSetType('scheduler')
        worker.mSetPort(self._port)
        worker.mSetStatus('Exited')
        self._db.mUpdateWorker(worker)
        self._notify.set() # Break immediatly the loop for responsive stop

    def _mSigHandler(self, signum, frame):
        ebLogInfo('Handling signal {0}'.format(signum))
        if signal.SIGUSR1 == signum:
            _rc = ''
            with ExaLock("scheduler_lock"):
                _db = ebGetDefaultDB()
                _rc = _db.mGetSchedule()
                ebLogInfo('_rc {0}'.format(_rc))
                for _iter in range(0, len(_rc)):
                    _uuid = _rc[_iter][0]
                    _operation = _rc[_iter][3]
                    _job_type = _rc[_iter][4]
                    _timer_type = _rc[_iter][5]
                    _timestamp = _rc[_iter][6]
                    _status = _rc[_iter][12]

                    if _operation == 'cancel':

                        _sched_info = ebScheduleInfo(_uuid, _db)
                        _db.mDelScheduleEntry(_sched_info)

                        _req = _db.mGetRequest(_uuid)
                        _params = ast.literal_eval(_req[5])
                        _job = ebJobRequest(_req[4], _params, aDB=_db)
                        _job.mLoadRequestFromDB(_req[0])
                        _job.mSetStatus('Done')
                        _db.mUpdateRequest(_job)
        else:
            self.mStop()

