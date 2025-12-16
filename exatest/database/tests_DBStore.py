# -*- coding: utf-8 -*-
"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates. 

NAME:
    test_DBStore.py - Base Class for DBStore testing

FUNCTION:
    Use this class when is necessary to test the DBStore methods

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    aypaul      07/07/25 - Enh#38105150 Increase code coverage for dbstore3.
    avimonda    09/26/24 - Added test for mGetChildRequestError()
    avimonda    10/11/23 - Added tests for mUpdateStatusRequestWithLock()
    ndesanto    09/07/20 - Added test for MySQL being stopped
    ndesanto    05/03/19 - Creation of the file
"""

import os
import six
import datetime
import unittest
import uuid
import pymysql
from unittest.mock import MagicMock, Mock, patch, mock_open

from exabox.agent.DBService import get_mysql_id
from exabox.config.Config import get_value_from_exabox_config
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.dbpolicies.ArchivingOperation import ebDBArchivingOperation
from exabox.core.dbpolicies.PruningOperation import ebDBPruningOperation
from exabox.core.dbpolicies.TimeBasedTrigger import ebTimeBasedTrigger
from exabox.core.dbpolicies.Base import ebDBPolicy,ebDBFilter
from exabox.core.DBStore import get_db_version
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogDebug
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.DBStore3 import ebMysqlDBlite
from exabox.core.DBStore3 import ebMysqlDB
from exabox.core.Context import get_gcontext
from exabox.core.DBStore3 import StopMySQLConnTimeoutException
from exabox.core.DBStore3 import ebRacksDB
from exabox.core.DBStore3 import ebKeysDB
from exabox.core.DBStore3 import ebExacloudDB
from exabox.ovm.rackcontrol import ebRackInfo
if get_db_version() == 3:
    from exabox.core.DBStore import StopMySQLConnRetryException, StopMySQLConnTimeoutException

class MockebRackInfo():

    def __init__(self):
        self.uuid = uuid.uuid1()
        self.hostname = "mockhostname"
        self.user = "mockuser"
        self.key = "mockkey"
        self.pubkey = "mockpubkey"
        self.cttime = "mockcttime"
        self.uttime = "mockuttime"
        self.miscdata = "mockmiscdata"
        self.mrackid = "mockrackid"
        self.path = "mockpath"
        self.owner = "mockowner"
        self.status = "mockstatus"  

    def mGetStartTime(self):
        return self.cttime
    def mGetEndTime(self):
        return self.uttime
    def mGetStatus(self):
        return self.status
    def mGetUUID(self):
        return self.uuid
    def mGetHostname(self):
        return self.hostname
    def mGetUser(self):
        return self.user
    def mGetKeyData(self):
        return self.key
    def mGetKeyDataPub(self):
        return self.pubkey
    def mGetCTime(self):
        return self.cttime
    def mGetUTime(self):
        return self.uttime
    def mGetMisc(self):
        return self.miscdata
    def mGetRackID(self):
        return self.mrackid
    def mGetPath(self):
        return self.path
    def mGetOwner(self):
        return self.owner

class MyTestResult(unittest.TestResult):
    def addFailure(self, test, err):
        super(MyTestResult, self).addFailure(test, err)

    def addError(self, test, err):
        test.tearDownClass()
        super(MyTestResult, self).addError(test, err)

class mockMysqlConnection():
    def __init__(self, aRaiseException=False):
        self.__raiseexception = aRaiseException

    def begin(self):
        return None

    def rollback(self):
        if self.__raiseexception:
            raise Exception("Exception during rollback.")
        return None

    def close(self):
        return None

class mockMysqlDriver():
    def __init__(self):
        self.__inRunning = True

    def mSetRunning(self, isRunning: bool):
        self.__isRunning = isRunning

    def mIsRunning(self):
        return self.__isRunning

class TestDBStore(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)

        self._db = ebGetDefaultDB()
        self.uuids = []
        self._st1 = None
        self._et1 = None

    def test_mExecute(self):

        self.assertTrue(self._db.mCheckTableExist('requests'))

        with patch('exabox.core.DBStore3.ebMysqlDBlite.mNativeExecute', side_effect=[pymysql.err.OperationalError(pymysql.constants.CR.CR_SERVER_GONE_ERROR, "MySQL server has gone away (BrokenPipeError(32, 'Broken pipe'))"), True]):
            self._db.mExecute("DELETE FROM requests")

    def test_mPrepareDatabase(self):

        self.assertTrue(self._db.mCheckTableExist('requests'))
        self.assertTrue(self._db.mCheckTableExist('requests_archive'))

        self._db.mExecute("DELETE FROM requests")
        self._db.mExecute("DELETE FROM requests_archive")


        for i in range(1, 10):
            self.uuids.append(six.text_type(uuid.uuid1(clock_seq=i)))

        now = datetime.datetime.now()

        minus60d30 = (now - datetime.timedelta(days=60, minutes=30)).strftime('%a %b %d %H:%M:%S %Y')
        minus30d30 = (now - datetime.timedelta(days=30, minutes=30)).strftime('%a %b %d %H:%M:%S %Y')
        minus240m  = (now - datetime.timedelta(minutes=240)).strftime('%a %b %d %H:%M:%S %Y')

        minus60d10  = (now - datetime.timedelta(days=60, minutes=10)).strftime('%a %b %d %H:%M:%S %Y')
        minus30d10  = (now - datetime.timedelta(days=30, minutes=10)).strftime('%a %b %d %H:%M:%S %Y')
        minus180min = (now  - datetime.timedelta(minutes=180)).strftime('%a %b %d %H:%M:%S %Y')
        
        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": self.uuids[0], "status": "Done", "starttime": minus60d30, "endtime": minus60d10, "cmdtype": "cluctrl.sim_install"})
        self._db.mInsertNewRequest(request)
        request.mFromDict({"uuid": self.uuids[1], "status": "Done", "starttime": minus30d30, "endtime": minus30d10, "cmdtype": "cluctrl.sim_install"})
        self._db.mInsertNewRequest(request)
        request.mFromDict({"uuid": self.uuids[2], "status": "Done", "starttime": minus240m, "endtime": minus180min, "cmdtype": "cluctrl.sim_install"})
        self._db.mInsertNewRequest(request)
        request.mFromDict({"uuid": self.uuids[3], "status": "Done", "starttime": minus240m, "endtime": 'Undef', "cmdtype": "cluctrl.fetchkeys"})
        self._db.mInsertNewRequest(request)
        request.mFromDict({"uuid": self.uuids[4], "status": "Done", "starttime": minus240m, "endtime": minus180min, "cmdtype": "cluctrl.fetchkeys"})
        self._db.mInsertNewRequest(request)

        self._st1 = minus60d30
        self._et1 = minus60d10

    def test_mCommandPass(self):

        try:

            self._db.mExecute("DELETE FROM requests")

            _pass = self._db.mCommandPassThrough("patch")
            self.assertEqual(_pass, True)

            _uuid = six.text_type((uuid.uuid1()))
            _now = datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y')

            request = ebJobRequest(None, {})
            request.mFromDict({"uuid": _uuid, "status": "Processing", "starttime": _now, "endtime": "", "cmdtype": "cluctrl.createservice"})
            self._db.mInsertNewRequest(request)
            self._db.mSetRegEntry(_uuid, "cluster1", _uuid)

            _pass = self._db.mCommandPassThrough("patch", aClustername="examplecluster")
            self.assertEqual(_pass, True)

            _pass = self._db.mCommandPassThrough("vm_cmd")
            self.assertEqual(_pass, False)

            _pass = self._db.mCommandPassThrough("patch")
            self.assertEqual(_pass, False)

            _pass = self._db.mCommandPassThrough("createservice")
            self.assertEqual(_pass, False)

        finally:
            self._db.mExecute("DELETE FROM requests")
            self._db.mExecute("DELETE FROM registry")



    def test_mSetWatcherRequest(self):
        _sqldata = (self.uuids[0], '', '', '', '', '', '', None, "PENDING")
        self._db.mSetWatcherRequest(_sqldata)
        response = self._db.mFetchOne("""SELECT * FROM exawatcher WHERE uuid=:1""", [self.uuids[0]])
        self.assertEqual(_sqldata, response)

    def test_mBackupRequests(self):

        _TriggerArchive = ebTimeBasedTrigger(wait_time=datetime.timedelta(hours=24))
        _StatusDone = ebDBFilter('status',['Done'],True) # Single filter, archive ALL done requests
        _ArchivePolicy = ebDBPolicy(ebDBArchivingOperation,_TriggerArchive,[_StatusDone])
 
        _ArchivePolicy.mEvaluate()

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests""")
        rc = response[0]
        self.assertEquals(3,rc) # The three 180min ones

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests_archive""")
        rca = response[0]
        self.assertEquals(0,rca) # the 60 and 30 days ones

    def test_mGetChildRequestError(self):

        _now = datetime.datetime.now()
        _minus45d45 = (_now - datetime.timedelta(days=45, minutes=45)).strftime('%a %b %d %H:%M:%S %Y')
        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": self.uuids[8], "status": "Done", "starttime": _minus45d45, "endtime": "", "cmdtype": "cluctrl.patch_prereq_check", "statusinfo": "000:: No status info available", "error": "0x0301003F", "error_str": "Ssh connectivity check failed during patching."})
        self._db.mInsertNewRequest(request)
        _err_row = self._db.mGetChildRequestError(self.uuids[8])
        self.assertEquals(_err_row[0], "0x0301003F")
        self.assertEquals(_err_row[1], 'Ssh connectivity check failed during patching.')

    def test_mUpdateStatusRequestWithLock_Processing_Done(self):

        self._db.mExecute("DELETE FROM requests")
        _now = datetime.datetime.now()
        _minus50d50 = (_now - datetime.timedelta(days=50, minutes=50)).strftime('%a %b %d %H:%M:%S %Y')

        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": self.uuids[8], "status": "Processing", "starttime": _minus50d50, "endtime": "", "cmdtype": "cluctrl.createservice", "statusinfo": "000:: No status info available"})
        self._db.mInsertNewRequest(request)
        self._db.mSetRegEntry(self.uuids[8], "cluster1", self.uuids[8])
        response = self._db.mFetchOne("""SELECT status, statusinfo FROM requests WHERE uuid=:1""", [self.uuids[8]])
        self.assertEquals('Processing', response[0])
        self.assertEquals('000:: No status info available', response[1])

        request.mFromDict({"uuid": self.uuids[8], "status": "Done", "starttime": _minus50d50, "endtime": "", "cmdtype": "cluctrl.createservice", "statusinfo": "True:100:createservice_done"})
        self._db.mUpdateStatusRequestWithLock(request)
        response = self._db.mFetchOne("""SELECT status, statusinfo FROM requests WHERE uuid=:1""", [self.uuids[8]])
        self.assertEquals('Done', response[0])
        self.assertEquals('True:100:createservice_done', response[1])

        self._db.mExecute("DELETE FROM requests")
        self._db.mExecute("DELETE FROM registry")

    def test_mUpdateStatusRequestWithLock_Pending_Done(self):

        self._db.mExecute("DELETE FROM requests")
        _now = datetime.datetime.now()
        _minus45d45 = (_now - datetime.timedelta(days=45, minutes=45)).strftime('%a %b %d %H:%M:%S %Y')

        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": self.uuids[8], "status": "Pending", "starttime": _minus45d45, "endtime": "", "cmdtype": "cluctrl.patch_prereq_check", "statusinfo": "000:: No status info available"})
        self._db.mInsertNewRequest(request)
        self._db.mSetRegEntry(self.uuids[8], "cluster1", self.uuids[8])
        response = self._db.mFetchOne("""SELECT status, statusinfo FROM requests WHERE uuid=:1""", [self.uuids[8]])
        self.assertEquals('Pending', response[0])
        self.assertEquals('000:: No status info available', response[1])

        request.mFromDict({"uuid": self.uuids[8], "status": "Done", "starttime": _minus45d45, "endtime": "", "cmdtype": "cluctrl.patch_prereq_check", "statusinfo": "True:100:createservice_done"})
        self._db.mUpdateStatusRequestWithLock(request)
        response = self._db.mFetchOne("""SELECT status, statusinfo FROM requests WHERE uuid=:1""", [self.uuids[8]])
        self.assertEquals('Done', response[0])
        self.assertEquals('True:100:createservice_done', response[1])

        self._db.mExecute("DELETE FROM requests")
        self._db.mExecute("DELETE FROM registry")

    def test_mUpdateStatusRequestWithLock_Executing_Done(self):

        self._db.mExecute("DELETE FROM requests")
        _now = datetime.datetime.now()
        _minus40d40 = (_now - datetime.timedelta(days=40, minutes=40)).strftime('%a %b %d %H:%M:%S %Y')

        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": self.uuids[8], "status": "Executing", "starttime": _minus40d40, "endtime": "", "cmdtype": "cluctrl.patch", "statusinfo": "000:: No status info available"})
        self._db.mInsertNewRequest(request)
        self._db.mSetRegEntry(self.uuids[8], "cluster1", self.uuids[8])
        response = self._db.mFetchOne("""SELECT status, statusinfo FROM requests WHERE uuid=:1""", [self.uuids[8]])
        self.assertEquals('Executing', response[0])
        self.assertEquals('000:: No status info available', response[1])

        request.mFromDict({"uuid": self.uuids[8], "status": "Done", "starttime": _minus40d40, "endtime": "", "cmdtype": "cluctrl.patch", "statusinfo": "True:100:createservice_done"})
        self._db.mUpdateStatusRequestWithLock(request)
        response = self._db.mFetchOne("""SELECT status, statusinfo FROM requests WHERE uuid=:1""", [self.uuids[8]])
        self.assertEquals('Done', response[0])
        self.assertEquals('True:100:createservice_done', response[1])

        self._db.mExecute("DELETE FROM requests")
        self._db.mExecute("DELETE FROM registry")

    def test_mPruningRequests(self):

        _TriggerPruning = ebTimeBasedTrigger(wait_time=datetime.timedelta(hours=2))
        _StatusDone = ebDBFilter('status',['Done'],True) # Dual filter, archive ALL done requests
        # test both single and multiple arguments filters
        _Fetchkeys = ebDBFilter('cmdtype',['clucontrol.dummy','cluctrl.fetchkeys'],True) # 
        _PruningPolicy = ebDBPolicy(ebDBPruningOperation,_TriggerPruning,[_StatusDone,_Fetchkeys])
 
        _PruningPolicy.mEvaluate()

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests""")
        rc = response[0]
        self.assertEquals(3,rc) # Fetchkey one is gone as 2h < 180min, undef is untouched

        response = self._db.mFetchOne("""SELECT count(uuid) FROM requests_archive""")
        rca = response[0]
        self.assertEquals(0,rca) # the 60 and 30 days ones

    def test_mGetUIRequests(self):
        result = self._db.mGetUIRequests()
        ebLogDebug("result = {}".format(result))

    def test_unicode(self):
        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": self.uuids[5], "status": "Done", "starttime": self._st1, "endtime": self._et1, "cmdtype": "cluctrl.createservice","body":six.text_type("\u2167 aaa \u0f84")})
        self._db.mInsertNewRequest(request)
        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": self.uuids[6], "status": "Done", "starttime": self._st1, "endtime": self._et1, "cmdtype": "cluctrl.createservice","body":six.u("\u2167 aaa \u0f84")})
        self._db.mInsertNewRequest(request)
        self._db.mExecute("""DELETE FROM requests where body=:1""",[six.text_type("\u2167 aaa \u0f84")])

    def test_mysql_down(self):
        if get_db_version() == 3:
            self._db.mSetRetryKillSwitchPath(os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "log/stop_mysql_conn_retry")))
            with open(self._db.mGetRetryKillSwitchPath(), "w") as fd:
                fd.write("test")
            self._db.mSetConnRetryTimeSecs(1)
            request = ebJobRequest(None, {})
            now = datetime.datetime.now()
            minus60d30 = (now - datetime.timedelta(days=60, minutes=30)).strftime('%a %b %d %H:%M:%S %Y')
            minus60d10  = (now - datetime.timedelta(days=60, minutes=10)).strftime('%a %b %d %H:%M:%S %Y')
            request.mFromDict({"uuid": self.uuids[7], "status": "Done", "starttime": minus60d30, "endtime": minus60d10, "cmdtype": "cluctrl.sim_install"})

            # Test kill switch exeception
            self._db.mGetDriver().mManualStop()
            self.assertRaises(StopMySQLConnRetryException, self._db.mInsertNewRequest, request)

            os.remove(self._db.mGetRetryKillSwitchPath())

            # Test MySQL wait timeout
            self._db.mSetConnRetryTimeSecs(2)
            self._db.mSetConnTimeoutSecs(1)
            self.assertRaises(StopMySQLConnTimeoutException, self._db.mInsertNewRequest, request)

            self._db.mGetDriver().mStart()

            # Test that functionality is restored after MySQL is up
            self._db.mInsertNewRequest(request)
            self.assertTrue(True)

    @patch("exabox.config.Config._load_cfgfile")
    def test_fail_to_obtain_port_exception(self, aGetValue):
        aGetValue.side_effect = Exception("Resource lock issue")
        self.assertRaises(ValueError, get_mysql_id)

    @patch("exabox.agent.DBService.get_value_from_exabox_config")
    def test_fail_to_obtain_port_none(self, aGetValue):
        # Force the return of None, this simulates the file reading issue
        aGetValue.return_value = None
        self.assertRaises(ValueError, get_mysql_id)

class TestebMysqlDBlite(unittest.TestCase):

    def setUp(self):
        super().setUp()
        _method = getattr(self, self._testMethodName)

    def test_entireclass(self):

        instance = ebMysqlDBlite()

        instance.mSetWaitAndRetry(False)
        self.assertEqual(instance.mGetWaitAndRetry(), False)
        self.assertEqual(instance.mGetAffectedRows(), 0)
        self.assertEqual(instance.mGetLastSql(), "")
        self.assertEqual(instance.mGetLastArgs(), None)

        instance.mSetOciExacc(True)
        self.assertEqual(instance.mGetOciExacc(), True)
        self.assertRaises(NotImplementedError, instance.mCreateConnection, None)

        with patch('exabox.core.DBStore3.ebMysqlDBlite.mSetConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCreateConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mGetConnConfig'):
            self.assertEqual(instance.mGetConnection(), None)

        instance.mSetRetryKillSwitchPath('/home/oracle/mockretrykillswitch')
        instance.mSetConnRetryTimeSecs(90)
        instance.mSetConnTimeoutSecs(90)
        instance.mSetDebug(True)
        self.assertRaises(NotImplementedError, instance.mGetDriver)

        with patch('exabox.core.DBStore3.ebMysqlDBlite.mHasConnection', side_effect=AttributeError("Not a valid attribute")):
            instance.mShutdownDB()

        with patch('exabox.core.DBStore3.ebMysqlDBlite.mGetConnection', return_value=mockMysqlConnection()),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mSetTransaction'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mNativeExecute', side_effect=pymysql.err.InterfaceError()),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCommit'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mLogDB'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mLog'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mGetDriver') as mockgetdriver:
             mockmysqldriveinstance = mockMysqlDriver()
             mockmysqldriveinstance.mSetRunning(False)
             mockgetdriver.return_value = mockmysqldriveinstance
             instance.mExecute("mocksql ")

        with patch('exabox.core.DBStore3.ebMysqlDBlite.mGetConnection') as mockconnection,\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mSetTransaction'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mSetConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCreateConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mGetConnConfig'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mLogDB'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mLog'):
             mockconnection.return_value = mockMysqlConnection(True)
             instance.mRollback()

class TestebMysqlDB(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_entireclass(self):

        coptions = get_gcontext().mGetConfigOptions()
        configs = {
            'mysql_conn_retry_time':None,
            'mysql_conn_timeout':None,
            'database_debug':None,
            'ociexacc':None,
            'dbaccess_timeout':None,
            'db_dir':None
            }
        for config in configs.keys():
            if config in list(coptions.keys()):
                configs[config] = coptions.get(config)

        get_gcontext().mSetConfigOption('mysql_conn_retry_time',"30")
        get_gcontext().mSetConfigOption('mysql_conn_timeout',"45")
        get_gcontext().mSetConfigOption('database_debug',"True")
        get_gcontext().mSetConfigOption('ociexacc',"True")
        get_gcontext().mSetConfigOption('dbaccess_timeout',"30")
        get_gcontext().mSetConfigOption('db_dir',"/home/oracle/unittest/mockdbdolder")

        with patch('exabox.core.DBStore3.ebMysqlDBlite.mSetConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDB.mCreateConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mGetConnConfig'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mSetConnConfig'),\
             patch('exabox.core.DBStore3.ebGetConnConfig'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mSetAccessTimeout', side_effect=ValueError("Invalid value.")),\
             patch('os.lstat', side_effect=Exception("Invalid location")),\
             patch('exabox.core.DBStore3.DBKeys'),\
             patch('exabox.core.DBStore3.ebLogDB'),\
             patch('exabox.core.DBStore3.ebExit'):
             instance = ebMysqlDB(None)

        for config in configs.keys():
            if configs[config]:
                get_gcontext().mSetConfigOption(config,configs[config])

class TestStopMySQLConnTimeoutException(unittest.TestCase):

    def setUp(self):
        super().setUp()
        _method = getattr(self, self._testMethodName)

    def test_entireclass(self):

        instance = StopMySQLConnTimeoutException(aRetryNum=1, aTimeElapsed=30)

class TestebRacksDB(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_instantiateclass(self):

        coptions = get_gcontext().mGetConfigOptions()
        _old_racks_folder = coptions.get('racks_dir', None)
        get_gcontext().mSetConfigOption('racks_dir', '/home/oracle/mockracksfolder')

        with patch('os.lstat') as mocklstat,\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', return_value=False),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebLogError'),\
             patch('exabox.core.DBStore3.ebLogDB'),\
             patch('exabox.core.DBStore3.ebExit'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mSetConnConfig'),\
             patch('exabox.core.DBStore3.ebGetConnConfig'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mSetConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCreateConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mGetConnConfig'):
             instance = ebRacksDB()
             get_gcontext().mSetConfigOption('racks_dir', None)
             instance = ebRacksDB()
             mocklstat.side_effect = Exception("Mock exception")
             instance = ebRacksDB()

        get_gcontext().mSetConfigOption('racks_dir', _old_racks_folder)

    def test_delete_dropmethods(self):

        with patch('os.lstat'),\
             patch('exabox.core.DBStore3.ebRacksDB.mCreateRacksTable'),\
             patch('exabox.core.DBStore3.ebRacksDB.mCreateLocationTable'),\
             patch('exabox.core.DBStore3.ebRacksDB.mCreateKeysTable'),\
             patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist') as mocktableexist,\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mSetConnConfig'),\
             patch('exabox.core.DBStore3.ebGetConnConfig'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mSetConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCreateConnection'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mGetConnConfig'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne') as mockmfetchone,\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll') as mockmfetchall:
             mocktableexist.return_value = False
             instance = ebRacksDB()
             mocktableexist.return_value = True
             instance.mDropKeysTable()
             instance.mDropRacksTable()
             instance.mDropLocationTable()
             instance.mDeleteKey("mockhostname","mockuser")
             instance.mDeleteKey("mockhostname")
             instance.mDeleteRack()
             instance.mDeleteLocation()

             rackinfo = MockebRackInfo()
             instance.mInsertKey(rackinfo)
             instance.mInsertRack(rackinfo)
             instance.mInsertLocation(rackinfo)
             instance.mUpdateLocation(rackinfo)
             instance.mUpdateRack(rackinfo)
             instance.mUpdateKey(rackinfo)

             mockmfetchone.return_value = 0
             self.assertEqual(instance.mRackStatus(1), 0)
             self.assertEqual(instance.mLocationStatus(1), 0)
             self.assertEqual(instance.mGetKey("mockhostname"), 0)
             self.assertEqual(instance.mGetKey("mockhostname", "mockuser"), 0)

             mockmfetchall.return_value = ["row1data", "row2data", "row3data"]
             self.assertEqual(instance.mDumpKeys("mockhostname"), "(row1data,row2data,row3data,)")
             self.assertEqual(instance.mDumpRacks(), "(row1data,row2data,row3data,)")
             self.assertEqual(instance.mDumpRacks("mockrackid"), "(row1data,row2data,row3data,)")
             self.assertEqual(instance.mDumpLocation(), "(row1data,row2data,row3data,)")
             self.assertEqual(instance.mDumpLocation("mockrackid"), "(row1data,row2data,row3data,)")

class TestebKeysDB(unittest.TestCase):

    def setUp(self):
        super().setUp()
        _method = getattr(self, self._testMethodName)

    def test_entireclass(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', return_value=False),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne') as mockfetchone:
             instance = ebKeysDB()
             instance.mCreateSshkeyTable()
             instance.mDeleteSshkeyTable()
             self.assertEqual(instance.mUpsertSshkey("mockcluster", "mocksshkey"), (0,''))
             mockfetchone.return_value=["mockresponse"]
             self.assertEqual(instance.mGetSshkey("mockcluster"), (0,"mockresponse"))
             mockfetchone.return_value = None
             self.assertEqual(instance.mGetSshkey("mockcluster"), (1,''))
        
class TestebExacloudDB(unittest.TestCase):

    def setUp(self):
        super().setUp()
        _method = getattr(self, self._testMethodName)

    def test_instancecreation(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'):
             instance = ebExacloudDB()

    def test_mExportProxyMigrationTables(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mUpdateUUIDtoexacloudForAgentStart'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', return_value=["/opt/oracle/mysql/securefiles"]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mExportProxyMigrationTables(), "/opt/oracle/mysql/securefiles")

    def test_mMigrateProxyDB(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('os.lstat', side_effect=[False,True]),\
             patch('shutil.copy'),\
             patch('os.remove'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', return_value=["/opt/oracle/mysql/securefiles"]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mMigrateProxyDB("/opt/oracle/mysql/primarydbfolder"), False)
             self.assertEqual(instance.mMigrateProxyDB("/opt/oracle/mysql/primarydbfolder"), True)

    def test_mImportDataIntoTable(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', side_effect=[True,False]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', return_value=["1"]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mImportDataIntoTable("mocktable"), False)
             self.assertEqual(instance.mImportDataIntoTable("mocktable"), False)

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebLogWarn'),\
             patch('exabox.core.DBStore3.ebLogDB'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('os.remove'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', return_value=True),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=["0","/opt/oracle/mysql/securefiles","0","/opt/oracle/mysql/securefiles"]),\
             patch('os.path.exists', side_effect=[False,True,True]),\
             patch('builtins.open', new_callable=mock_open, read_data="mockcolumns"):
             instance = ebExacloudDB()
             self.assertEqual(instance.mImportDataIntoTable("mocktable"), False)
             self.assertEqual(instance.mImportDataIntoTable("mocktable"), True)

    def test_EnvironmentResourceDetails(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mUpdateEnvironmentResourceDetails', return_value=True),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', return_value=False),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=["success", None]):
             instance = ebExacloudDB()
             instance.mCreateEnvironmentResourceDetails()
             self.assertEqual(instance.mInsertEnvironmentResourceDetails(80,80), True)
             self.assertEqual(instance.mInsertEnvironmentResourceDetails(80,80), True)

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=[None,"notnone","notnone","notnone","notnone"]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mUpdateEnvironmentResourceDetails(), False)
             self.assertEqual(instance.mUpdateEnvironmentResourceDetails(), False)
             self.assertEqual(instance.mUpdateEnvironmentResourceDetails(80,80), True)
             self.assertEqual(instance.mUpdateEnvironmentResourceDetails(aUsedCPUPercent=None, aUsedMemoryPercent=80), True)
             self.assertEqual(instance.mUpdateEnvironmentResourceDetails(aUsedCPUPercent=80, aUsedMemoryPercent=None), True)

    def test_exacloudinstance(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', side_effect=[True,False]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', return_value=["mockhostname", "mockport", "mockauthkey"]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mSelectRoutingInfoFromECInstances("mockinstanceid"), ("mockhostname", "mockport", "mockauthkey"))
             self.assertEqual(instance.mSelectRoutingInfoFromECInstances("mockinstanceid"), (None, None, None))

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=[None, "NotNone"]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'):
             instance = ebExacloudDB()
             instance.mInsertExacloudInstanceInfo("mockhostname", "mockportnum", "mockversion", "mockauthkey", "mockreqtype", "mockoedaversion")
             instance.mInsertExacloudInstanceInfo("mockhostname", "mockportnum", "mockversion", "mockauthkey", "mockreqtype", "mockoedaversion")

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', side_effect=[True,True,False]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', side_effect=[["mocklist1"], []]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mSelectAllFromRequestuuidtoExacloud("NotNone"), ["mocklist1"])
             self.assertEqual(instance.mSelectAllFromRequestuuidtoExacloud(), [])
             self.assertEqual(instance.mSelectAllFromRequestuuidtoExacloud(), [])

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=[None, "NotNone", "NotNone", "NotNone"]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'):
             instance = ebExacloudDB()
             self.assertEqual(instance.mUpdateExacloudInstanceInfo("mockinstanceid", "mockkey", "mockvalue"), False)
             self.assertEqual(instance.mUpdateExacloudInstanceInfo("mockinstanceid", "status", "mockvalue"), True)
             self.assertEqual(instance.mUpdateExacloudInstanceInfo("mockinstanceid", "reqtype", "mockvalue"), True)
             self.assertEqual(instance.mUpdateExacloudInstanceInfo("mockinstanceid", "mockkey", "mockvalue"), False)

    def test_requestuuidtoexacloud(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', side_effect=[True, True, False]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=[None, ["NotNone"]]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mSelectStatusFromUUIDToECInstance("mockuuid"), "InitialReqPending")
             self.assertEqual(instance.mSelectStatusFromUUIDToECInstance("mockuuid"), "NotNone")
             self.assertEqual(instance.mSelectStatusFromUUIDToECInstance("mockuuid"), "InitialReqPending")

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=[None, "NotNone"]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mUpdateStatusForReqUUID("mockuuid", "mockstatus"), False)
             self.assertEqual(instance.mUpdateStatusForReqUUID("mockuuid", "mockstatus"), True)

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', side_effect=[False, True, True]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=[None, ["NotNone"]]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mSelectECInstanceIDFromUUIDToECInstance("mockuuid"), "None")
             self.assertEqual(instance.mSelectECInstanceIDFromUUIDToECInstance("mockuuid"), "None")
             self.assertEqual(instance.mSelectECInstanceIDFromUUIDToECInstance("mockuuid"), "NotNone")

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'):
             instance = ebExacloudDB()
             instance.mUpdateUUIDtoexacloudForAgentStart()

    def test_proxyrequests(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'):
             instance = ebExacloudDB()
             instance.mUpdateResponseDetailsInProxyRequest("mockuuid", "mockresponsecode", "mockrespbody", "mockrespurlheaders")

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', return_value=["mockreturnvalue"]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', side_effect=[True, False, False]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mSelectResponseDetailsFromProxyRequests("mockuuid"), ["mockreturnvalue"])
             self.assertEqual(instance.mSelectResponseDetailsFromProxyRequests("mockuuid"), ["None", "None", "None"])
             instance.mCreateMockCallTable()

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCommit'):
             instance = ebExacloudDB()
             jobreq = ebJobRequest(None, {})
             instance.mInsertMockCall(jobreq)

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', return_value=0),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', return_value=False):
             instance = ebExacloudDB()
             instance.mCreateAgentSignalTable()
             instance.mCreateAgentTable()
             instance.mCreateScheduleTable()
             instance.mCreateScheduleArchiveTable()
             instance.mCreateWorkersTable()
             instance.mCreateClusterStatusTable()
             instance.mCreateRegTable()
             instance.mCreateSELinuxPolicyTable()
             instance.mCreateProfilerTable()
             instance.mCreateRequestsTable()
             instance.mCreateRequestsArchiveTable()
             instance.mCreateIBFabricLocksTable()
             instance.mCreateIBFabricClusterTable()
             instance.mCreateIBFabricIBSwitchesTable()
             instance.mCreatePatchListTable()
             instance.mCreateClusterPatchOperationsTable()
             instance.mCreateInfraPatchingTimeStatsTable()
             instance.mCreateFilesTable("mocktablename")
             instance.mCreateExawatcherTable()
             instance.mCreateCCATable()
             instance.mCreateLocksTable()
             instance.mCreateErrCodeTable()
             instance.mCreateRunningDBsList()
             instance.mCreateAsyncProcessTable()
             instance.mCreateMetricsTable()
             self.assertEqual(instance.mGetDataCacheByName("mockcache"), 0)

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', return_value="mockagentpid"):
             instance = ebExacloudDB()
             self.assertEqual(instance.mGetAgentsPID(), "mockagentpid")
             instance.mDeleteAgent()

    def test_schedulearchive(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', return_value=["mockstatus", "mockerro","mockerrorstring", "mockstatusinfo", "moockclustername"]):
             instance = ebExacloudDB()
             instance.mUpdateScheduleArchiveByType("mockuuid")

    def test_workertable(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', return_value=[[8888], [9999]]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mGetWorkerPorts(), [8888, 9999])

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebLogWarn'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=[["Undef"], None, ["activesynclock"], ["Undef"]]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog', return_value=None):
             instance = ebExacloudDB()
             self.assertEqual(instance.mReleaseWorkerSyncLock(), False)
             self.assertEqual(instance.mReleaseWorkerSyncLock(8888, "workerprocess"), True)
             self.assertEqual(instance.mReleaseWorkerSyncLock(8888, "workerprocess"), True)

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', return_value=["mockrowdata1", "mockrowdata2"]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mGetIdleWorkers(), "(mockrowdata1,mockrowdata2,)")
             self.assertEqual(instance.mDumpActiveWorkers("mockuuid"), "(mockrowdata1,mockrowdata2,)")
             self.assertEqual(instance.mDumpActiveWorkers(), "(mockrowdata1,mockrowdata2,)")

    def test_mDumpClusterStatus(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', return_value=[["mockrowdata1"], ["mockrowdata2"]]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mDumpClusterStatus(), "(['mockrowdata1'],['mockrowdata2'],)")
             self.assertEqual(instance.mDumpClusterStatus("mockclusterid"), "(['mockrowdata1'],['mockrowdata2'],)")

    def test_selinuxtables(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'):
             instance = ebExacloudDB()
             instance.mInsertGeneratedSELinuxPolicy("aUUID", "aHostName", "aBase64EncodedSELinuxPolicy")
             instance.mUpdateAllPoliciesOfHostAsSynced("mockhostname")

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', side_effect=["unsyncedpolicies", "allselinuxpolicies"]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mGetUnsyncedSELinuxPolicy("mockhostname"), "unsyncedpolicies")
             self.assertEqual(instance.mGetAllSELinuxPolicy("mockhostname"), "allselinuxpolicies")

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', return_value=10),\
             patch('exabox.core.DBStore3.ebExacloudDB.mBuildUIFilter'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', side_effect=[["selinuxviolations"], [], ["mockactiverequests"]]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mGetSELinuxViolationStatusForRequest("mockuuid"), True)
             self.assertEqual(instance.mGetSELinuxViolationStatusForRequest("mockuuid"), False)
             self.assertEqual(instance.mGetActiveRequestsUUID("mockcmd"), ["mockactiverequests"])
             self.assertEqual(instance.mGetUIRowCount(), 10)

    def test_registry(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=[["88"], "mockregistryforkey", "mockregistryforuuid"]),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'):
             instance = ebExacloudDB()
             self.assertEqual(instance.mGetRegCount(), 88)
             self.assertEqual(instance.mGetRegEntryByKey("mockkey"), "mockregistryforkey")
             self.assertEqual(instance.mGetRegEntryByKey("mockuuid"), "mockregistryforuuid")

    def test_ibfabrictables(self):

        sha512sum = "5cb23f577a9a86e21801448e14622e1c49b0573ea8be95a9f7167810e261ac1d2b53d3bbaa2b9ddf84ce2683a6547dcb51197beb0a23a2307c231cf3c8d42cfd"
        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebLogWarn'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute', side_effect=[None, pymysql.err.IntegrityError("Error")]):
             instance = ebExacloudDB()
             instance.mSetIBFabricEntry(sha512sum)
             instance.mSetIBFabricEntry(sha512sum)
             self.assertRaises(Exception, instance.mSetIBFabricEntry, "notavalidsha512sum")

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', side_effect=[[], ["mockrowdata1", "mockrowdata2"]]):
             instance = ebExacloudDB()
             self.assertRaises(Exception, instance.mCheckIBFabricEntry)
             self.assertEqual(instance.mCheckIBFabricEntry(aFabricID="mockfabricid", aSha512=None), None)
             self.assertEqual(instance.mCheckIBFabricEntry(aFabricID=None, aSha512="mocksha512sum"), "mockrowdata1")

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebLogError'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute', side_effect=[None, Exception("mock execution error")]):
             instance = ebExacloudDB()
             self.assertRaises(Exception, instance.mSetDoSwitchIBFabic, None, None)
             self.assertRaises(Exception, instance.mSetDoSwitchIBFabic, "mockfabricid", None)
             self.assertEqual(instance.mSetDoSwitchIBFabic("mockfabricid", "yes"), True)
             self.assertRaises(Exception, instance.mSetDoSwitchIBFabic, "mockfabricid", "yes")

    def test_metricstable(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mCheckTableExist', side_effect=[True, False]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecuteLog'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=["mockregvalueforkey", [10], "mocklatestmetric"]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', side_effect=["mockpidfile", ["mockrow1"], "workerpids"]):
             instance = ebExacloudDB()
             self.assertEqual(instance.mGetRegValueByKey("mockkey"), "mockregvalueforkey")
             self.assertEqual(instance.mGetActiveRequestStatus(), 10)
             self.assertEqual(instance.mGetLatestMetric("mockcategory"), "mocklatestmetric")
             self.assertEqual(instance.mGetLatestMetric("mockcategory"), None)
             self.assertEqual(instance.mGetPidFile(), "mockpidfile")
             self.assertEqual(instance.mGetRequestStatus("mockcmd"), ['m', 'o', 'c', 'k', 'r', 'o', 'w', '1'])
             self.assertEqual(instance.mGetWorkerPIDs(), "workerpids")
             instance.mInsertNewMetrics({"category":"mockcategory", "created_at":"mockstarttime", "data":"mockmetricdata"})

    def test_ccadatatable(self):

        with patch('exabox.core.DBStore3.ebMysqlDB.__init__'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateRegTable'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mExecute'),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchOne', side_effect=["mockccareqid", "mockccareqtype"]),\
             patch('exabox.core.DBStore3.ebMysqlDBlite.mFetchAll', side_effect=[["mockccauserlist"], "mockccadata", "allccaresourceusertypes", "allccauserparurls", ["ccaschedulerid"], ["mockccauserstatus"]]):
             instance = ebExacloudDB()
             instance.mSetCCAData("mockdata")
             instance.mUpdateCCADataStatus("aId", "aStatus", "aDescription", "aSchedulerId")
             instance.mUpdateCCADataStatus("aId", "aStatus", "aDescription", None)
             instance.mGetCCADataStatus("mockid")
             instance.mRemoveCCAUser("mockid")
             self.assertEqual(instance.mGetCCAUserList(), ['m', 'o', 'c', 'k', 'c', 'c', 'a', 'u', 's', 'e', 'r', 'l', 'i', 's', 't'])
             self.assertEqual(instance.mGetCCAData(), "mockccadata")
             self.assertEqual(instance.mGetCCAAccessReqId("mockid"), "mockccareqid")
             self.assertEqual(instance.mGetCCARequestType("mockid"), "mockccareqtype")
             self.assertEqual(instance.mGetAllCCAUserResourceTypeList(), "allccaresourceusertypes")
             self.assertEqual(instance.mGetAllCCAUserParUrlsList(), "allccauserparurls")
             self.assertEqual(instance.mGetCCASchedulerId("mockstatus"), ['c', 'c', 'a', 's', 'c', 'h', 'e', 'd', 'u', 'l', 'e', 'r', 'i', 'd'])
             self.assertEqual(instance.mGetCCAUsersByStatus("mockstatus"), ['m', 'o', 'c', 'k', 'c', 'c', 'a', 'u', 's', 'e', 'r', 's', 't', 'a', 't', 'u', 's'])

def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(TestDBStore('test_mExecute'))
    suite.addTest(TestDBStore('test_mPrepareDatabase'))
    suite.addTest(TestDBStore('test_mSetWatcherRequest'))
    suite.addTest(TestDBStore('test_mBackupRequests'))
    suite.addTest(TestDBStore('test_mPruningRequests'))
    suite.addTest(TestDBStore('test_mGetChildRequestError'))
    suite.addTest(TestDBStore('test_mUpdateStatusRequestWithLock_Processing_Done'))
    suite.addTest(TestDBStore('test_mUpdateStatusRequestWithLock_Pending_Done'))
    suite.addTest(TestDBStore('test_mUpdateStatusRequestWithLock_Executing_Done'))
    suite.addTest(TestDBStore('test_mGetUIRequests'))
    suite.addTest(TestDBStore('test_unicode'))
    #suite.addTest(TestDBStore('test_mysql_down'))
    suite.addTest(TestDBStore('test_fail_to_obtain_port_exception'))
    suite.addTest(TestDBStore('test_fail_to_obtain_port_none'))
    suite.addTest(TestDBStore('test_mCommandPass'))
    suite.addTest(TestebMysqlDBlite('test_entireclass'))
    suite.addTest(TestebMysqlDB('test_entireclass'))
    suite.addTest(TestStopMySQLConnTimeoutException('test_entireclass'))
    suite.addTest(TestebRacksDB('test_instantiateclass'))
    suite.addTest(TestebRacksDB('test_delete_dropmethods'))
    suite.addTest(TestebKeysDB('test_entireclass'))
    suite.addTest(TestebExacloudDB('test_instancecreation'))
    suite.addTest(TestebExacloudDB('test_mExportProxyMigrationTables'))
    suite.addTest(TestebExacloudDB('test_mMigrateProxyDB'))
    suite.addTest(TestebExacloudDB('test_mImportDataIntoTable'))
    suite.addTest(TestebExacloudDB('test_EnvironmentResourceDetails'))
    suite.addTest(TestebExacloudDB('test_exacloudinstance'))
    suite.addTest(TestebExacloudDB('test_requestuuidtoexacloud'))
    suite.addTest(TestebExacloudDB('test_proxyrequests'))
    suite.addTest(TestebExacloudDB('test_schedulearchive'))
    suite.addTest(TestebExacloudDB('test_workertable'))
    suite.addTest(TestebExacloudDB('test_mDumpClusterStatus'))
    suite.addTest(TestebExacloudDB('test_selinuxtables'))
    suite.addTest(TestebExacloudDB('test_registry'))
    suite.addTest(TestebExacloudDB('test_ibfabrictables'))
    suite.addTest(TestebExacloudDB('test_metricstable'))
    suite.addTest(TestebExacloudDB('test_ccadatatable'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
