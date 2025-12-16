"""
$Header:

 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    tests_ecsreq.py - Base Class for ecsreq testing

FUNCTION:
    Use this class when is necessary to test the ecsreq methods. This class uses 
    exabox.conf to determine the correct DB to use.

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    ndesanto    05/27/19 - Creation of the file
"""

import datetime
import json
import os
import unittest
import uuid
import imp
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.agent.RequestsBackupContext import RequestsBackupContext
from exabox.core.DBStore import ebGetDefaultDB

# Bellow lines forcefully import the ecsreq script, since is not in a package
dir_path = os.path.dirname(os.path.realpath(__file__))
#import six
#if six.PY2:
#else:
#    from importlib.machinery import SourceFileLoader
#    ecsreq = SourceFileLoader(fullname='ecsreq', path=path_to_ecsreq).load_module()

class TestEcsreqDB(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)

        self._db = ebGetDefaultDB()
        path_to_ecsreq = os.path.join(self.mGetUtil(self).mGetExacloudPath(), 'bin/ecsreq.py')
        ecsreq_module = imp.load_source('ecsreq', path_to_ecsreq)
        self._ecsreq = self._db

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests""")
        self._irc = response[0]

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests_archive""")
        self._irca = response[0]

        self.uuids = []
        self.uuids.append(str(uuid.uuid1(clock_seq=1)))
        self.uuids.append(str(uuid.uuid1(clock_seq=2)))
        self.uuids.append(str(uuid.uuid1(clock_seq=3)))
        self.uuids.append(str(uuid.uuid1(clock_seq=4)))
        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests""")
        self._irc = response[0]

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests_archive""")
        self._irca = response[0]

        now = datetime.datetime.now()

        starttimes = []
        starttimes.append((now - datetime.timedelta(days=60, minutes=30)).strftime('%a %b %d %H:%M:%S %Y'))
        starttimes.append((now - datetime.timedelta(days=30, minutes=30)).strftime('%a %b %d %H:%M:%S %Y'))
        starttimes.append((now - datetime.timedelta(minutes=30)).strftime('%a %b %d %H:%M:%S %Y'))

        endtimes = []
        endtimes.append((now - datetime.timedelta(days=60, minutes=10)).strftime('%a %b %d %H:%M:%S %Y'))
        endtimes.append((now - datetime.timedelta(days=30, minutes=10)).strftime('%a %b %d %H:%M:%S %Y'))
        endtimes.append(now.strftime('%a %b %d %H:%M:%S %Y'))
        
        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": self.uuids[0], "status": "Done", "starttime": starttimes[0], "endtime": endtimes[0], "cmdtype": "cluctrl.sim_install"})
        self._db.mInsertNewRequest(request)
        request.mFromDict({"uuid": self.uuids[1], "status": "Done", "starttime": starttimes[1], "endtime": endtimes[1], "cmdtype": "cluctrl.sim_install"})
        self._db.mInsertNewRequest(request)
        request.mFromDict({"uuid": self.uuids[2], "status": "Done", "starttime": starttimes[2], "endtime": endtimes[2], "cmdtype": "cluctrl.sim_install"})
        self._db.mInsertNewRequest(request)
        request.mFromDict({"uuid": self.uuids[3], "status": "Done", "starttime": starttimes[2], "endtime": 'Undef', "cmdtype": "cluctrl.sim_install"})
        self._db.mInsertNewRequest(request)
        self._irc += 4

    @classmethod
    def tearDownClass(self):
        self._db.mExecute("""DELETE FROM requests WHERE uuid IN (:1, :2, :3, :4)""", self.uuids)
        self._db.mExecute("""DELETE FROM requests_archive WHERE uuid IN (:1, :2, :3, :4)""", self.uuids)

    def test_ebSqliteDB_mGetRequest(self):
        # requests_archive
        out = self._ecsreq.mGetRequest(str(self.uuids[0]))
        self.assertIsNotNone(out)
        # requests
        out = self._ecsreq.mGetRequest(str(self.uuids[2]))
        self.assertIsNotNone(out)

    def test_ebSqliteDB_mDumpRequests(self):
        out = self._ecsreq.mDumpRequests()
        self.assertIsNotNone(out)


if __name__ == '__main__':
   unittest.main()
