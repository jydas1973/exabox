"""
 Copyright (c) 2017, 2025, Oracle and/or its affiliates.

NAME:
    ScheduleRegistry - Insert schedule jobs

FUNCTION:
    Registry file for scheduler jobs

NOTE:
    None

History:
    prsshukl    05/20/2025 - Bug 37695971 - PROVIDE A ENABLE-DISABLE FLAG FOR METRIC_COLLECTION FEATURE IN ALL THE BRANCHES
    aypaul      07/18/2024 - Bug#36850055 Deprecate MYSQL backup functionality.
    shapatna    06/24/2024 - Bug 36732867: Add metrics_collector job to the scheduler
    aararora    12/19/2023 - Bug 35863722: Add cleanup clusters folder schedule
    dekuckre    08/02/2023 - 35663670: remove mysqldb_ossbackup
    dekuckre    03/27/2023 - 35217347: Add mysqldb_fsbackup, mysqldb_ossbackup
    pbellary    08/28/2019 - Create file
"""

from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogError
from exabox.agent.Agent import ebScheduleInfo
from datetime import datetime, timedelta
from exabox.core.Context import get_gcontext

def insert_job_exawatcher_cleanup():
    aDB=ebGetDefaultDB()
    _rc = aDB.mGetScheduleByCommand('cleanup_exawatcher_log')
    if _rc is None:
        ebLogInfo('Adding job schedule for cleanup_exawatcher_log !')
        _sched_info = ebScheduleInfo(None, aDB)
        _sched_info.mSetScheduleCommand('cleanup_exawatcher_log')
        _sched_info.mSetScheduleMode('generic')
        _sched_info.mSetScheduleOperation('schedule')
        _sched_info.mSetScheduleTimerType('repeat')
        _sched_info.mSetScheduleTimestamp(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _sched_info.mSetScheduleInterval('04:00:00')
        _sched_info.mSetScheduleRepeatCount('forever')
        _sched_info.mSetScheduleEvent('timer_job')
        _sched_info.mSetScheduleStatus('Idle')
        _sched_info.mRegister()
    else:
        ebLogInfo('job schedule for cleanup_exawatcher_log already exists !')

def insert_job_cleanup_oeda_requests():
    aDB=ebGetDefaultDB()
    _rc = aDB.mGetScheduleByCommand('cleanup_oeda_requests')
    if _rc is None:
        ebLogInfo('Adding job schedule for cleanup_oeda_requests !')
        _sched_info = ebScheduleInfo(None, aDB)
        _sched_info.mSetScheduleCommand('cleanup_oeda_requests')
        _sched_info.mSetScheduleMode('generic')
        _sched_info.mSetScheduleOperation('schedule')
        _sched_info.mSetScheduleTimerType('repeat')
        _sched_info.mSetScheduleTimestamp(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _sched_info.mSetScheduleInterval('24:00:00')
        _sched_info.mSetScheduleRepeatCount('forever')
        _sched_info.mSetScheduleEvent('timer_job')
        _sched_info.mSetScheduleStatus('Idle')
        _sched_info.mRegister()
    else:
        ebLogInfo('job schedule for cleanup_oeda_requests already exists !')

def insert_job_cleanup_incident_tar_zipfiles():
    aDB=ebGetDefaultDB()
    _rc = aDB.mGetScheduleByCommand('cleanup_incident_tar_zipfiles')
    if _rc is None:
        ebLogInfo('Adding job schedule for cleanup_incident_tar_zipfiles !')
        _sched_info = ebScheduleInfo(None, aDB)
        _sched_info.mSetScheduleCommand('cleanup_incident_tar_zipfiles')
        _sched_info.mSetScheduleMode('generic')
        _sched_info.mSetScheduleOperation('schedule')
        _sched_info.mSetScheduleTimerType('repeat')
        _sched_info.mSetScheduleTimestamp(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _sched_info.mSetScheduleInterval('06:00:00')
        _sched_info.mSetScheduleRepeatCount('forever')
        _sched_info.mSetScheduleEvent('timer_job')
        _sched_info.mSetScheduleStatus('Idle')
        _sched_info.mRegister()
    else:
        ebLogInfo('job schedule for cleanup_incident_tar_zipfiles already exists !')

def insert_job_cleanup_log_files():
    aDB=ebGetDefaultDB()
    _rc = aDB.mGetScheduleByCommand('cleanup_log_files')
    if _rc is None:
        ebLogInfo('Adding job schedule for cleanup_log_files !')
        _sched_info = ebScheduleInfo(None, aDB)
        _sched_info.mSetScheduleCommand('cleanup_log_files')
        _sched_info.mSetScheduleMode('generic')
        _sched_info.mSetScheduleOperation('schedule')
        _sched_info.mSetScheduleTimerType('repeat')
        _sched_info.mSetScheduleTimestamp(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _sched_info.mSetScheduleInterval('24:00:00')
        _sched_info.mSetScheduleRepeatCount('forever')
        _sched_info.mSetScheduleEvent('timer_job')
        _sched_info.mSetScheduleStatus('Idle')
        _sched_info.mRegister()
    else:
        ebLogInfo('job schedule for cleanup_log_files already exists !')

def insert_job_cleanup_database_log():
    aDB=ebGetDefaultDB()
    _rc = aDB.mGetScheduleByCommand('cleanup_database_log')
    if _rc is None:
        ebLogInfo('Adding job schedule for cleanup_database_log!')
        _sched_info = ebScheduleInfo(None, aDB)
        _sched_info.mSetScheduleCommand('cleanup_database_log')
        _sched_info.mSetScheduleMode('generic')
        _sched_info.mSetScheduleOperation('schedule')
        _sched_info.mSetScheduleTimerType('repeat')
        _sched_info.mSetScheduleTimestamp(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _sched_info.mSetScheduleInterval('06:00:00')
        _sched_info.mSetScheduleRepeatCount('forever')
        _sched_info.mSetScheduleEvent('timer_job')
        _sched_info.mSetScheduleStatus('Idle')
        _sched_info.mRegister()
    else:
        ebLogInfo('job schedule for cleanup_database_log already exists !')

def insert_job_cleanup_sshdiag_log():
    aDB=ebGetDefaultDB()
    _rc = aDB.mGetScheduleByCommand('cleanup_sshdiag_log')
    if _rc is None:
        ebLogInfo('Adding job schedule for cleanup_sshdiag_log!')
        _sched_info = ebScheduleInfo(None, aDB)
        _sched_info.mSetScheduleCommand('cleanup_sshdiag_log')
        _sched_info.mSetScheduleMode('generic')
        _sched_info.mSetScheduleOperation('schedule')
        _sched_info.mSetScheduleTimerType('repeat')
        _sched_info.mSetScheduleTimestamp(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _sched_info.mSetScheduleInterval('06:00:00')
        _sched_info.mSetScheduleRepeatCount('forever')
        _sched_info.mSetScheduleEvent('timer_job')
        _sched_info.mSetScheduleStatus('Idle')
        _sched_info.mRegister()
    else:
        ebLogInfo('job schedule for cleanup_sshdiag_log already exists !')                     

def insert_job_cleanup_clusters():
    aDB=ebGetDefaultDB()
    _rc = aDB.mGetScheduleByCommand('cleanup_clusters') 
    if _rc is None:
        ebLogInfo('Adding job schedule for cleanup_clusters!')
        _sched_info = ebScheduleInfo(None, aDB)
        _sched_info.mSetScheduleCommand('cleanup_clusters')
        _sched_info.mSetScheduleMode('generic')
        _sched_info.mSetScheduleOperation('schedule')
        _sched_info.mSetScheduleTimerType('repeat')
        _sched_info.mSetScheduleTimestamp(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _sched_info.mSetScheduleInterval('24:00:00')
        _sched_info.mSetScheduleRepeatCount('forever')
        _sched_info.mSetScheduleEvent('timer_job')
        _sched_info.mSetScheduleStatus('Idle')
        _sched_info.mRegister()
    else:
        ebLogInfo('job schedule for cleanup_clusters already exists !')

def insert_job_metrics_collector():
    '''
        This function inserts a new job under the Scheduler which periodically collects the metrics 
    '''
    aDB=ebGetDefaultDB()
    _rc = aDB.mGetScheduleByCommand('metrics_collector') 
    
    if _rc is None:
        _metric_collector_config = get_gcontext().mCheckConfigOption("metric_collector_config")
        if _metric_collector_config:
            _interval = _metric_collector_config.get('schedule_metric_collection_in_minutes', None)
            if not _interval:
                raise ValueError("'schedule_metric_collection_in_minutes' configure parameter not set in exabox.conf")
            # The schedule_interval obtained is in the string format and is the total number of minutes, the following methods convert it into HH:MM:SS format
            _schedule_interval = str(timedelta(minutes = int(_interval)))
            _formatted_schedule_interval = _schedule_interval.zfill(8)

            ebLogInfo('Adding job schedule for metrics_collector!')
            _sched_info = ebScheduleInfo(None, aDB)
            _sched_info.mSetScheduleCommand('metrics_collector')
            _sched_info.mSetScheduleMode('generic')
            _sched_info.mSetScheduleOperation('schedule')
            _sched_info.mSetScheduleTimerType('repeat')
            _sched_info.mSetScheduleTimestamp(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            _sched_info.mSetScheduleInterval(_formatted_schedule_interval)
            _sched_info.mSetScheduleRepeatCount('forever')
            _sched_info.mSetScheduleEvent('timer_job')
            _sched_info.mSetScheduleStatus('Idle')
            _sched_info.mRegister()
    else:
        ebLogInfo('job schedule for metrics_collector already exists !')

def register_schedule_jobs():
    """This method inserts cluster independent jobs to scheduler table """
    insert_job_exawatcher_cleanup()
    insert_job_cleanup_oeda_requests()
    insert_job_cleanup_incident_tar_zipfiles()
    insert_job_cleanup_log_files()
    insert_job_cleanup_database_log()
    insert_job_cleanup_sshdiag_log()
    insert_job_cleanup_clusters()
    _metric_collector_config = get_gcontext().mCheckConfigOption("metric_collector_config")
    if _metric_collector_config:
        _enable_metric_collection = True if _metric_collector_config.get('enable_metric_collection', None) == 'True' else False
        if _enable_metric_collection:
            insert_job_metrics_collector()
    