"""

 $Header: 

 Copyright (c) 2021, 2022, Oracle and/or its affiliates.

 NAME:
      tests_schedule_registry.py - Unitest for ScheduleRegistry

 DESCRIPTION:
      Run tests for ScheduleRegistry file

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
    pbellary    12/07/21 - Creation of the file
"""

import unittest
import warnings
import shutil

from exabox.log.LogMgr import ebLogInfo
from exabox.core.MockCommand import exaMockCommand
from exabox.core.DBStore import ebGetDefaultDB
from exabox.agent.Scheduler import get_schedule_info
from exabox.agent.ScheduleRegistry import register_schedule_jobs
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol


class ebTestScheduleRegistry(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super(ebTestScheduleRegistry, self).setUpClass(aGenerateDatabase=True,aUseOeda=False)
        warnings.filterwarnings("ignore")

    def test_register_schedule_jobs(self):
        db = ebGetDefaultDB()
        #cleanup schedule entries from the DB
        db.mDelScheduleEntry(aForce=True)

        #registry schedule entries to the DB
        register_schedule_jobs()
        _rc = db.mGetScheduleByCommand('cleanup_exawatcher_log')
        self.assertNotEqual(_rc, None)

        sched_info = get_schedule_info(_rc)
        db.mDelScheduleEntry(sched_info)

        _rc = db.mGetScheduleByCommand('cleanup_oeda_requests')
        self.assertNotEqual(_rc, None)

        sched_info = get_schedule_info(_rc)
        db.mDelScheduleEntry(sched_info)

        _rc = db.mGetScheduleByCommand('cleanup_incident_tar_zipfiles')
        self.assertNotEqual(_rc, None)

        sched_info = get_schedule_info(_rc)
        db.mDelScheduleEntry(sched_info)

        _rc = db.mGetScheduleByCommand('cleanup_log_files')
        self.assertNotEqual(_rc, None)

        sched_info = get_schedule_info(_rc)
        db.mDelScheduleEntry(sched_info)

        _rc = db.mGetScheduleByCommand('cleanup_database_log')
        self.assertNotEqual(_rc, None)

        sched_info = get_schedule_info(_rc)
        db.mDelScheduleEntry(sched_info)

        _rc = db.mGetScheduleByCommand('cleanup_sshdiag_log')
        self.assertNotEqual(_rc, None)

        sched_info = get_schedule_info(_rc)
        db.mDelScheduleEntry(sched_info)

if __name__ == '__main__':
    unittest.main()