"""

 $Header: 

 Copyright (c) 2021, Oracle and/or its affiliates.

 NAME:
      tests_scheduler.py - Unitest for Scheduler

 DESCRIPTION:
      Run tests for Scheduler file

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
    pbellary    12/07/21 - Creation of the file
"""

import unittest
from unittest import mock
from unittest.mock import patch, MagicMock
import warnings
import shutil
import multiprocessing
import signal

from exabox.log.LogMgr import ebLogInfo
from exabox.core.MockCommand import exaMockCommand
from exabox.core.DBStore import ebGetDefaultDB
from exabox.agent.Agent import ebScheduleInfo, dispatchJobToWorker
from exabox.agent.Worker import ebWorker
from exabox.agent.Scheduler import ebScheduler, process_timer_jobs, \
                 get_schedule_info, scheduler_running, stop, get_worker_status, request_handler, \
                 dispatchInternalJob, update_schedule_archive
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol


class ebTestScheduler(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super(ebTestScheduler, self).setUpClass(aGenerateDatabase=True,aUseOeda=False)
        warnings.filterwarnings("ignore")

    def test_request_handler(self):
        db = ebGetDefaultDB()

        _rc = ["70d65b0e-f81a-11ea-a0e2-fa163e241d21", "info", "default", "schedule", "follow_up_job", "once", 
                     "2021-12-07 04:04:37", "00:00:00", "0", "0", "", "", "Done"]
        sched_info = get_schedule_info(_rc)
        db.mInsertNewSchedule(sched_info)

        #with mock.patch("exabox.agent.Agent.dispatchJobToWorker", MagicMock()):
        #    request_handler("70d65b0e-f81a-11ea-a0e2-fa163e241d21")

        db.mDelScheduleEntry(sched_info)

    def test_dispatch_internal(self):
        db = ebGetDefaultDB()

        _rc = ["70d65b0e-f81a-11ea-a0e2-fa163e241d22", "cleanup_sshdiag_log", "generic", "schedule", "timer_job", "once", 
                     "2021-12-07 04:04:37", "00:00:00", "0", "0", "", "", "Done"]

        sched_info = get_schedule_info(_rc)
        db.mInsertNewSchedule(sched_info)

        dispatchInternalJob("70d65b0e-f81a-11ea-a0e2-fa163e241d22")

        db.mDelScheduleEntry(sched_info)
        
    def test_update_schedule_archive(self):
        db = ebGetDefaultDB()

        _rc = ["70d65b0e-f81a-11ea-a0e2-fa163e241d20", "info", "generic", "schedule", "timer_job", "once", 
                     "2021-12-07 04:04:37", "00:00:00", "0", "0", "", "", "Done"]
        sched_info = get_schedule_info(_rc)

        update_schedule_archive(sched_info)

        db.mDelScheduleArchiveEntry(sched_info)

    def test_get_schedule_info(self):

        _rc = ["70d65b0e-f81a-11ea-a0e2-fa163e241d20", "info", "generic", "schedule", "timer_job", "once", 
                     "2021-12-07 04:04:37", "00:00:00", "0", "0", "", "", "Done"]
        sched_info = get_schedule_info(_rc)

        _cmd = sched_info.mGetScheduleCommand()
        self.assertEqual(_cmd, "info")

        _mode = sched_info.mGetScheduleMode()
        self.assertEqual(_mode, "generic")

        _operation = sched_info.mGetScheduleOperation()
        self.assertEqual(_operation, "schedule")

        _status = sched_info.mGetScheduleStatus()
        self.assertEqual(_status, "Done")

    def test_scheduler_running(self):
        pid = scheduler_running()

    def test_stop(self):
        stop()

    def test_get_worker_status(self):

        _rc = get_worker_status("critical")
        self.assertEqual(_rc, False)
        
if __name__ == '__main__':
    unittest.main()