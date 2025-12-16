"""
$Header:

 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    test_supervisor.py - Base Class for supervisor testing

FUNCTION:
    Use this class when is necessary to test the supervisor methods and behaviour

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    ndesanto    08/20/20 - Fixed for MysQL compatibility
    ndesanto    05/09/19 - Creation of the file
"""

import datetime
import unittest
import uuid
import time
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.DBStore import ebGetDefaultDB
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class TestSupervisor(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True, aUseAgent=True)
        self._db = ebGetDefaultDB()

    def test_supervisor_startup_request_backup(self):
        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests""")
        irc = response[0]

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests_archive""")
        irca = response[0]

        uuids = []
        uuids.append(str(uuid.uuid1(clock_seq=1)))
        uuids.append(str(uuid.uuid1(clock_seq=2)))
        uuids.append(str(uuid.uuid1(clock_seq=3)))
        now = datetime.datetime.now()
        endtimes = []
        endtimes.append((now - datetime.timedelta(days=60, minutes=10)).strftime('%a %b %d %H:%M:%S %Y (PDT)'))
        endtimes.append((now - datetime.timedelta(days=30, minutes=10)).strftime('%a %b %d %H:%M:%S %Y (PDT)'))
        endtimes.append(now.strftime('%a %b %d %H:%M:%S %Y (PDT)'))

        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": uuids[0], "status": "Done", "endtime": endtimes[0]})
        self._db.mInsertNewRequest(request)
        request.mFromDict({"uuid": uuids[1], "status": "Done", "endtime": endtimes[1]})
        self._db.mInsertNewRequest(request)
        request.mFromDict({"uuid": uuids[2], "status": "Done", "endtime": endtimes[2]})
        self._db.mInsertNewRequest(request)
        irc += 3

        # Wait for supervisor to fetch
        time.sleep(1)

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests""")
        rc = response[0]

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests_archive""")
        rca = response[0]

        ebLogInfo("irc = {}, irca = {}, rc = {}, rca = {}, (irc - rc - rca) = {}".format(irc, irca, rc, rca, irc + irca - rc - rca))

        self._db.mExecute("""DELETE FROM requests WHERE uuid IN (:1, :2, :3)""", uuids)
        self._db.mExecute("""DELETE FROM requests_archive WHERE uuid IN (:1, :2, :3)""", uuids)
        self._db.mCommit()

        self.assertTrue(irc + irca - rc - rca == 0)

