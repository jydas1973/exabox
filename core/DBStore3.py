"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    DBStore - Basic DB functionality

FUNCTION:
    Provide basic/core APIs

NOTE:
    None

History:
    MODIFIED   (MM/DD/YY)
    ririgoye    11/26/25 - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT TO
                           LD_LIBRARY_PATH
    aararora    04/25/25 - ER 37732745: Exacloud to send status response to
                           ECRA using AQ
    hgaldame    03/12/25 - 37694157 - exacc gen2: cps os upgrade failed in step
                           runcpsosupgradeswitchover due to exacloud has
                           ongoing operations
    hgaldame    12/04/24 - 37356055 - oci/exacc: ecra wf for cps sw upgrade
                           fails on runcpsupgradeswitchover step
    aypaul      12/02/24 - ER-37026034 Add a new column to request table to
                           store sub command information.
    avimonda    09/26/24 - Bug 36943471 - Add mGetChildRequestError()
    aypaul      08/13/24 - Enh#34242877 Add support for import data from backup
                           for mysql tables
    naps        08/06/24 - Bug 36629391 - During exacloud stop, handle 
                           dispatcher and workermanager as special workers
    araghave    06/25/24 - Enh 36748435 - CLEANUP FABRIC ENTRIES IN CASE OF
                           INFRA PATCHING ISSUES ENCOUNTERED DUE TO SWITCH
                           REPLACEMENT
    shapatna    06/24/24 - Bug 36732867: Add methods for querying data for metrics collection
    aypaul      03/21/24 - Bug#36391673 Update resource capture time to a
                           precision of seconds.
    gparada     03/06/24 - 36368272 Avoid error when inserting duplicated row
    naps        03/06/24 - Bug 36367235 - Add retry mechanism for releasing
                           synclock.
    jesandov    01/08/24 - 35141267: Add function mGetProfilerData
    aararora    12/07/23 - Bug 36083555: Get all ports for running workers
    avimonda    10/07/23 - 35869328: Adding a method called
                           mUpdateStatusRequestWithLock 
    jesandov    09/28/23 - 35141262: Profiler enhancement to use DB tables
    naps        09/11/23 - Bug 35668909 - Ensure microseconds field is
                           populated for 0 value too.
    naps        07/21/23 - Bug 35013360 - Dispatcher and WorkerManager
                           implementation.
    aypaul      06/15/23 - Bug#35461171 Harden sql execute logic against mysql
                           server connection issue.
    aypaul      03/31/23 - Enh#35221396 DB function to return PIDs of special
                           workers.
    aypaul      01/02/23 - Enh#34822394 Add free workers information in system
                           metrics endpoint.
    aypaul      12/04/22 - Issue#34607716 Handle multiprocessing issue by
                           shutting down base manager instance explicitly.
    prsshukl    11/15/22 - Bug 34772772: Logging level change of unnecessary
                           log statement
    hgaldame    10/27/22 - 34738764 - ociexacc: exacc remoteec enhancements for
                           exacloud requests
    oespinos    08/30/22 - 34544144 - Switchover fails with ongoing operations
    aypaul      07/05/22 - Bug#34347508 Worker allocation optimisation logic
                           correction.
    aypaul      06/01/22 - Enh#34207528 ExaKms entry history tracking and
                           generation.
    sdevasek    05/22/22 - Enh 33859232 Call mCreatePatchingTimeStatsTable
    jfsaldan    05/19/22 - Bug 34185829 - Check for errors during mUpdateWorker
    hgaldame    05/06/22 - 34146854 - oci/exacc: persists exacloud remote ec
                           async request status
    ndesanto    04/13/22 - 34063272 - Adding methods to support data_cache
    rajsag      03/30/22 - 34011758 - exacc: exacloud changes to send partial
                           success error code to ecra
    alsepulv    03/15/22 - Bug 33964575: Use FQDN for adcnas472
    rajsag      02/21/22 - 33422731 - retry of vm memory workflow not checking
                           status of previous node, could cause complete outage
    nisrikan    02/17/22 - 33868806 - unit test for opctl in exacloud
    aypaul      01/25/22 - Enh#33611377 Worker limit and resource
                              utilisation optimisation.
    rajsag      11/15/21 - 33568435 - exacc:21.3.1:multiple reshape failure
                           entries in errorresponse table in exacloud
    rajsag      08/13/21 - 31985002 - ensure asm reshape flows update point in
                           time status for every step in request table
    aypaul      07/29/21 - Bug#33150016 Implement get custom policies API to
                           send back generated se linux exception policies.
    nmallego    07/12/21 - ER 32925372- introduce table clusterpatchoperations
    jyotdas     06/18/21 - Bug 32997721 - Patch wf failure does not report as
                           failure
    aypaul      06/17/21 - Bug#32677660 Generate exception policies on
                           create_service/vmgi_reshape failure.
    naps        05/18/21 - Make some of the vm_cmd commands as whitelist during
                           patching operations.
    jyotdas     03/22/21 - Enh 32415195 - error handling: return infra patching
                           dispatcher errors to caller
    ndesanto    02/04/21 - 32466126: Changing requests.data type to mediumtext
    dekuckre    01/19/21 - 32394436: Update mCheckRegEntry
    dekuckre    12/09/20 - 32239952: Update mInsertExacloudInstanceInfo 
    dekuckre    12/03/20 - 32178865: Update export, import of proxy tables. 
    dekuckre    10/07/20 - 31465951: Enhancements to proxy feature
    ndesanto    09/11/20 - Added DBKeys class support
    kkviswan    08/30/20 - OPCTL User Management
    ndesanto    08/11/20 - Changed open to use with function
    ndesanto    07/24/20 - BUG 31664384: MySQL lock issues because mCommit
                           checked on affected rows, changed to be determnistic
    gurkasin    08/01/20 - Added mClearCustomerData
    rajsag      05/12/20 - THE CCA EXACLOUD CHANGES FOR THE TWO API SUPPORT
                           CREATE USER ANDDELETE USER
    ndesanto    03/25/20 - MySQL integration
    dekuckre    03/16/20 - 30697759: Update mClearWorkers
    jesandov    01/25/20 - Create file
"""

# pylint: disable=import-error

import six
import os
import time
import copy
import threading
import re
import ast
import uuid
import json
import shutil

from typing import List, Dict
from datetime import datetime, timedelta
from glob import glob

import pymysql

from exabox.config.Config import ebCluCmdCheckOptions
from exabox.core.Context import get_gcontext
from exabox.core.Mask import maskSensitiveData, umaskSensitiveData
from exabox.agent.AgentSignal import AgentSignal
from exabox.agent.ExaLock import ExaLock
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB
from exabox.core.Core import ebExit
from exabox.core.DBKeys import DBKeys
from exabox.agent.DBService import ExaMySQL, get_mysql_config
from exabox.core.DBLockTableUtils import ebDBLockTypes, sLockDBRowToDict
from exabox.exakms.ExaKmsEntry import ExaKmsEntry
from exabox.exakms.ExaKmsHistoryNode import ExaKmsHistoryNode
from exabox.core.AQResponse import mUpdateResponseToEcra


def ebInitDBLayer(aContext, aOptions):
    pass

def ebShutdownDBLayer():
    pass

def ebGetDefaultDB():
    return ebExacloudDB()


def ebGetConnConfig(aConfigParam, aConnFile):
    return get_mysql_config(aConfigParam, aConnFile)


#################
# Mysql DB lite #
#################


class ebMysqlDBlite(object):

    def __init__(self):

        # Fetch DB path for either config file or use basepath/db
        self.__affected_rows = 0
        self.__lastsql = ""
        self.__lastargs = None
        self.__debug = False
        self.__ociexacc = False
        self.__access_timeout = 10
        self.__max_retry = 3
        self.__log = False
        self.__maskparams = False
        # The connection is the one that should be in a thread local
        # As a forked Process if not calling ebGetDefaultDB() again
        # Would simply reuse the same object/connection by calling
        # an underlying DB method
        self.__conn = threading.local()
        self.__conn_config = None
        self.__is_transaction = False
        self.__retry_conn = True
        self.__retry_kill_switch_path = os.path.abspath(\
            "tmp/stop_mysql_conn_retry")
        # Following default values will be overriten on ebMySQL class with the 
        # values from "mysql_conn_retry_time" and "mysql_conn_timeout" from 
        # exabox.conf, is done at that point since ebMySQL have access to the
        # context
        self.__conn_retry_time_secs = 60 * 1
        self.__conn_timeout_secs = 60 * 90

    # Close Connection on deletion/out of scope
    # Since object is not cached anymore that will happen fine
    def __del__(self):
        try:
            self.mShutdownDB()
        except Exception:
            # Best effort
            pass

    # This SPECIFIC DB object will have no WAIT/Retry logic
    # it is absolutely needed for the Scheduler DB object
    # as it is in charge of starting the DB if its goes down
    # so it cannot wait on DB for another task (Worker cleanup)
    def mSetWaitAndRetry(self, aBool : bool) -> None:
        self.__retry_conn = aBool

    def mGetWaitAndRetry(self) -> bool:
        return self.__retry_conn

    def mLogDB(self, aPfx, aMsg):
        ebLogDB(aPfx, aMsg)

    def mLog(self, aFunction, aMsg):
        aFunction(aMsg)
    
    def mGetAffectedRows(self):
        return self.__affected_rows

    def mGetLastSql(self):
        return self.__lastsql

    def mGetLastArgs(self):
        return self.__lastargs

    def mSetOciExacc(self, aBool):
        self.__ociexacc = aBool

    def mGetOciExacc(self):
        return self.__ociexacc

    def mSetAccessTimeout(self, aInt):
        self.__access_timeout = aInt

    def mGetAccessTimeout(self):
        return self.__access_timeout

    def mCreateConnection(self, aConfig):
        raise NotImplementedError()

    def mGetMaskParams(self):
        return self.__maskparams

    def mSetMaskParams(self, aBool):
        self.__maskparams = aBool

    def mHasConnection(self):
        return hasattr(self.__conn,'conn')

    def mGetConnection(self):
        _conn = getattr(self.__conn,'conn',None)
        if not _conn:
            self.mSetConnection(self.mCreateConnection(self.mGetConnConfig()))
            _conn = getattr(self.__conn,'conn',None)
        return _conn

    def mSetConnection(self, aConn):
        self.__conn.conn = aConn

    def mGetConnConfig(self):
        return self.__conn_config

    def mSetConnConfig(self, aConfig):
        self.__conn_config = aConfig

    def mIsTransaction(self):
        return self.__is_transaction

    def mSetTransaction(self, aBool):
        self.__is_transaction = aBool

    def mGetRetryKillSwitchPath(self):
        return self.__retry_kill_switch_path

    def mSetRetryKillSwitchPath(self, aPath):
        self.__retry_kill_switch_path = aPath

    def mGetConnRetryTimeSecs(self):
        return self.__conn_retry_time_secs

    def mSetConnRetryTimeSecs(self, aRetryTime):
        self.__conn_retry_time_secs = aRetryTime

    def mGetConnTimeoutSecs(self):
        return self.__conn_timeout_secs

    def mSetConnTimeoutSecs(self, aTimeout):
        self.__conn_timeout_secs = aTimeout

    def mGetDebug(self):
        return self.__debug

    def mSetDebug(self, aBool):
        self.__debug = aBool

    def mGetLog(self):
        return self.__log

    def mSetLog(self, aBool):
        self.__log = aBool

    def mGetDriver(self):
       raise NotImplementedError()

    def mShutdownDB(self):
        try:
            if self.mHasConnection():
                self.mGetConnection().close()
        except AttributeError:
            self.mLog(ebLogWarn, 'DB shutdown error')

    def mFetchAllDict(self, aSql, aDataList):
        def mCallback(cursor):
            _rc = []
            if cursor != None:
                desc = cursor.description
                _rc = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
            return _rc
        return self.mExecute(aSql, aDataList, mCallback)

    def mFetchAll(self, aSql, aDataList=None):
        def mCallback(cursor):
            _rc = []
            if cursor != None:
                _rc = cursor.fetchall()
            return _rc
        return self.mExecute(aSql, aDataList, mCallback)

    def mFetchOne(self, aSql, aDataList=None):
        def mCallback(cursor):
            _rc = []
            if cursor != None:
                _rc = cursor.fetchone()
            return _rc
        return self.mExecute(aSql, aDataList, mCallback)

    def mExecuteLog(self, aSql, aDataList=None):
        self.mSetLog(True)
        _res = self.mExecute(aSql, aDataList)
        self.mSetLog(False)
        return _res

    @staticmethod
    def mListToDict(aList, aStrTrimSize=None):

        _newDict = {}
        i = 1

        if isinstance(aList, dict):
            _values = list(aList.values())
            return ebMysqlDB.mListToDict(_values)

        for element in aList:

            if element == None:
                _newDict[str(i)] = element
            else:
                _strElement = ""
                _strElement = six.text_type(element)

                if isinstance(element, int):
                    _newDict[str(i)] = element
                else:
                    _newDict[str(i)] = _strElement

                if aStrTrimSize is not None:
                    if len(_strElement) > aStrTrimSize:
                        _newDict[str(i)] = _strElement[0:aStrTrimSize] + "..."

            i += 1

        return _newDict

    @staticmethod
    def mPrepareQuery(aSql):
        """
        Change bind variable classic format to MySQL format
        """

        _sql = str(aSql)
        _regex = '[(,=\ ]{1}[:]{1}([0-9]{1,})'

        _patt = re.search(_regex, _sql)
        while _patt is not None:
            _replace = "%({0})s".format(_patt.group(1))
            _sql = _sql[0:_patt.start()+1] + _replace + _sql[_patt.end():]
            _patt = re.search(_regex, _sql)

        return _sql

    @staticmethod
    def mFormat(aDataList, aQuery, aValue):

        if aValue:
            aDataList.append(aValue)

            _pat = re.search('\{([0-9]{1,})\}', aQuery)
            if _pat is not None:

                _str  = aQuery[0: _pat.start()]
                _str += " %({0})s ".format(str(len(aDataList)))
                _str += aQuery[_pat.end():]
                return _str

        return ""

    def mExecute(self, aSql, aDataList=None, aCallback=None):

        _retries = self.__max_retry

        while True:

            try:
                self.mGetConnection().begin()
                self.mSetTransaction(True)
                _rc = self.mNativeExecute(aSql, aDataList, aCallback)
                self.mCommit()
                return _rc

            except pymysql.err.InterfaceError as e:

                if _retries < 0:
                    raise

                self.mLogDB('WRN', "DBStore3, InterfaceError while execute query: {0}".format(aSql))
                self.mLogDB('WRN', "`{0}`|`{1}`".format(self.__lastsql, self.__lastargs))
                self.mLogDB('WRN', "DBStore3: InterfaceError Try Reconnection")

                if self.mGetDebug():
                    self.mLog(ebLogWarn, "DBStore3: InterfaceError while execute query: {0}".format(e))
                    self.mLog(ebLogWarn, "`{0}`|`{1}`".format(self.__lastsql, self.__lastargs))
                    self.mLog(ebLogWarn, "DBStore3: InterfaceError Try Reconnection")

                if self.mGetDriver().mIsRunning():
                    self.mSetConnection(self.mCreateConnection(self.mGetConnConfig()))
                else:
                    ebLogError("Mysql server has been stopped")
                    break

                _retries -= 1
            except pymysql.err.OperationalError as ex:

                if _retries < 0:
                    raise

                self.mLogDB('WRN', "DBStore3, OperationalError while execute query: {0}".format(aSql))
                self.mLogDB('WRN', "DBStore3, OperationalError details: {0}".format(ex))
                self.mLogDB('WRN', "`{0}`|`{1}`".format(self.__lastsql, self.__lastargs))

                if ex.args[0] == pymysql.constants.CR.CR_SERVER_GONE_ERROR:

                    if self.mGetDriver().mIsRunning():
                        if self.mHasConnection():
                            self.mGetConnection().close()
                        self.mLogDB('WRN', "DBStore3:OperationalError Try Reconnection")
                        self.mSetConnection(self.mCreateConnection(self.mGetConnConfig()))
                        self.mLogDB('NFO', "DBStore3:OperationalError Successfully created a new connection.")
                        self.mLogDB('NFO',f"DBStore3:OperationalError Retry SQL: {aSql} with new connection handler.")
                    else:
                        ebLogError("Mysql server has been stopped.")
                        break

                _retries -= 1
            except Exception as e:

                if _retries < 0:
                    raise

                self.mLogDB('WRN', "DBStore3, Error while execute query: {0}".format(e))
                self.mLogDB('WRN', "`{0}`|`{1}`".format(self.__lastsql, self.__lastargs))

                if self.mGetDebug():
                    self.mLog(ebLogWarn, "DBStore3: Error while execute query: {0}".format(e))
                    self.mLog(ebLogWarn, "`{0}`|`{1}`".format(self.__lastsql, self.__lastargs))

                self.mRollback()
                _retries -= 1

    """
    No third argument    : Execute SQL as before
    List/Tuple argument  : All member converted to String
    Dictionary argument  : Passed as-is
    """
    def mNativeExecute(self, aSql, aDataList=None, aCallback=None):

        _rc = None
        if not self.mGetConnection().open:
            self.mSetConnection(self.mCreateConnection(self.mGetConnConfig()))

        with self.mGetConnection().cursor() as _cursor:

            _sql = ebMysqlDB.mPrepareQuery(aSql)
            self.__lastsql = _sql

            if self.mGetLog():
                self.mLogDB('NFO', _sql)

            if self.mGetDebug():
                self.mLog(ebLogDebug, "DBStore3, mNativeExecute: `{0}`".format(_sql))

            if aDataList:

                if isinstance(aDataList, list) or isinstance(aDataList, tuple):
                    _dict = ebMysqlDB.mListToDict(aDataList)
                else:
                    _dict = aDataList

                _debugDict = ebMysqlDB.mListToDict(aDataList, 40)

                if self.mGetLog():
                    self.mLogDB('NFO', _debugDict)

                if self.mGetDebug():
                    self.mLog(ebLogDebug, _debugDict)

                self.__lastargs = _debugDict
                _cursor.execute(_sql, _dict)

            else:
                self.__lastargs = None
                _cursor.execute(_sql)

            if aCallback:
                _rc = aCallback(_cursor)

            self.__affected_rows = _cursor.rowcount

        if self.mGetDebug() and aCallback:
            self.mLog(ebLogDebug, "DBStore3, mNativeExecute Result")
            if _rc is None:
                self.mLog(ebLogDebug, "None")
            else:
                _out = ebMysqlDB.mListToDict(_rc, 100)
                ebLogDebug(_out)

        return _rc

    def mCommit(self):
        if self.mIsTransaction():
            self.mGetConnection().commit()

            if self.mGetDebug():
                self.mLogDB('WRN', "DBStore3, Commit Successfull")
                self.mLogDB('WRN', "`{0}`|`{1}`|`{2} affected`".format(self.__lastsql, \
                                                              self.__lastargs, \
                                                              self.__affected_rows))

            self.mSetTransaction(False)

    def mRollback(self):
        try:
            self.mGetConnection().rollback()
        except Exception as e:
            self.mLogDB('WRN', "DBStore3, Error on rollback: {0}".format(e))
            self.mLogDB('WRN', "`{0}`|`{1}`".format(self.__lastsql, self.__lastargs))

            if self.mGetDebug():
                self.mLog(ebLogWarn, "DBStore3, Error on rollback: {0}".format(e))
                self.mLog(ebLogWarn, "`{0}`|`{1}`".format(self.__lastsql, self.__lastargs))
            # Error on Rollback show that DB connection is corrupted (Packet Sequence number)
            # Recreate it
            self.mGetConnection().close()
            self.mSetConnection(self.mCreateConnection(self.mGetConnConfig()))
        finally:
            self.mSetTransaction(False)

    def mCheckTableExist(self, aTableName):
        _sql = """SHOW TABLES LIKE %(1)s"""
        _data = [aTableName]
        _fdata = self.mFetchOne(_sql, _data)
        if _fdata and len(_fdata) and _fdata[0] == aTableName:
            return True
        else:
            return False


#################
# Mysql DB Base #
#################


class ebMysqlDB(ebMysqlDBlite):

    def __init__(self, aConfigParam):
        ebMysqlDBlite.__init__(self)
        # Fetch DB path for either config file or use basepath/db
        self.__config = get_gcontext().mGetConfigOptions()
        if "mysql_conn_retry_time" in self.__config:
            self.mSetConnRetryTimeSecs(int(self.__config["mysql_conn_retry_time"]))
        if "mysql_conn_timeout" in self.__config:
            self.mSetConnTimeoutSecs(int(self.__config["mysql_conn_timeout"]))
        self.__driver = ExaMySQL(self.__config)

        if 'database_debug' in self.__config.keys() and \
            self.__config['database_debug'].upper() == 'TRUE':
            self.mSetDebug(True)

        if 'ociexacc' in self.__config.keys() and self.__config['ociexacc'] == 'True':
            self.mSetOciExacc(True)

        try:
            if 'dbaccess_timeout' in self.__config.keys():
                self.mSetAccessTimeout(int(self.__config['dbaccess_timeout']))
        except ValueError:
            ebLogWarn("Invalid value on dbaccess_timeout exabox.conf parameter")

        _confile = "opt/mysql/mysql_conn.cfg"
        if "mysql_config" in self.__config:
            _confile = self.__config["mysql_config"]
        self.mSetConnConfig(ebGetConnConfig(aConfigParam, _confile))
        self.mSetConnection(self.mCreateConnection(self.mGetConnConfig()))

        if 'db_dir' in self.__config.keys():
            self.__db_path = self.__config['db_dir']
        else:
            self.__db_path = get_gcontext().mGetBasePath()+'/db'
        try:
            os.lstat(self.__db_path)
        except:
            ebLogDB('ERR','Invalid DB location: ' + self.__db_path)
            ebExit(-1)

        if 'ociexacc' in self.__config.keys() and \
            self.__config['ociexacc'] == 'True':
            self.__ociexacc = True
        else:
            self.__ociexacc = False

        if self.__ociexacc:
            self.__keysdb = DBKeys(self.__db_path+'/keys.db')

    def mGetConfig(self):
        return self.__config

    def mCreateSshkeyTable(self):
        self.__keysdb.mCreateSshkeyTable()

    def mUpsertSshkey(self, aCluster, aSshkey):
        return self.__keysdb.mUpsertSshkey(aCluster, aSshkey)

    def mGetSshkey(self, aCluster):
        return self.__keysdb.mGetSshkey(aCluster)

    def mDeleteSshkeyTable(self):
        self.__keysdb.mDeleteSshkeyTable()

    def mGetDriver(self):
       return self.__driver

    def mCreateConnection(self, aConfig):

        aConfig['connect_timeout'] = self.mGetAccessTimeout()

        if self.mGetDebug():
            ebLogDB('NFO', "Connection Arguments: {0}".format(aConfig))
            ebLogInfo("DBStore3: Connection Arguments: {0}".format(aConfig))

        _retries = 0
        _elapsed_time = 0
        while _elapsed_time < self.mGetConnTimeoutSecs():
            try:
                _conn = pymysql.connect(**aConfig)
                break
            except pymysql.err.OperationalError as e:
                #Supervisor have this flag set to not get blocked in this
                #unescapable 1h30 loop and to try to start MySQL again.
                if not self.mGetWaitAndRetry():
                    raise StopMySQLConnRetryException()

                ebLogInfo("Cannot connect please verify MySQL status. " + \
                    "Will retry in {} seconds".format(\
                        self.mGetConnTimeoutSecs()))
                # Check for kill switch
                if os.path.exists(self.mGetRetryKillSwitchPath()):
                    ebLogError("Wait for connection kill switch found " + \
                        "{0} raising exception.".format(\
                            self.mGetRetryKillSwitchPath()))
                    raise StopMySQLConnRetryException()
                   
                time.sleep(self.mGetConnRetryTimeSecs())

            _elapsed_time += self.mGetConnRetryTimeSecs()
            _retries += 1

        if _elapsed_time >= self.mGetConnTimeoutSecs():
            ebLogError("Could not connect to MySQL. Tried {} times.".format(\
                _retries))
            raise StopMySQLConnTimeoutException(_retries, _elapsed_time)

        ebLogDB('DBG', "Create new connection: {0}".format(_conn))
        if self.mGetDebug():
            ebLogInfo("DBStore3: Create new connection: {0}".format(_conn))

        self.mSetMaskParams(self.__config['mask_db_params'])
        self.mSetLog(False)

        return _conn
    
    def mIsMySQLRunning(self):
        return self.__driver.mIsRunning()


class StopMySQLConnRetryException(Exception):
    """Raised when the kill switch file is found"""
    pass

class StopMySQLConnTimeoutException(Exception):
    """Raised when the Max wait for Exacloud to connect to MySQL is reached.

    Attributes:
        aRetryNum -- Number of connection attempts
        aElapsedTime -- Time elapsed waiting for connection
        """
    def __init__(self, aRetryNum, aTimeElapsed):
        _sec = timedelta(seconds=aTimeElapsed)
        _d = datetime(1, 1, 1) + _sec
        _time_str = "{} hours {} minutes {} seconds".format(\
            _d.hour, _d.minute, _d.second)
        super().__init__(\
            "Exacloud attempted {} connections to MySQL in {} before failing."
            .format(aRetryNum, _time_str))


###########
# RACK DB #
###########


class ebRacksDB(ebMysqlDB):

    def __init__(self):
        ebMysqlDB.__init__(self, "rackdb")

        _config = get_gcontext().mGetConfigOptions()
        if 'racks_dir' in _config.keys() and _config['racks_dir']:
            self.__db_path = _config['racks_dir']
        else:
            self.__db_path = '/net/adcnas472.us.oracle.com/export/farm_intg_metadata/large_dos/'
            self.__db_path += 'ECS/MAIN/LINUX.X64/ecs/ecra/racks/devracks'

        try:
            os.lstat(self.__db_path)
        except:
            ebLogError('*** RACK Global Repository not accessible using path: %s ' % (self.__db_path))
            ebLogDB('ERR','Invalid DB location: '+self.__db_path)
            ebExit(-1)

        self.mCreateRacksTable()
        self.mCreateLocationTable()
        self.mCreateKeysTable()

    def mCreateKeysTable(self):
        """
        Request fields:
            0. uuid
            1. hostname
            2. user
            3. keydata
            4. createtime
            5. updatetime
            6. misc
        """
        if not self.mCheckTableExist('keys'):
            self.mExecute('''CREATE TABLE keys (uuid text,
                                                hostname text,
                                                user text,
                                                keydata text,
                                                createtime text,
                                                updatetime text,
                                                misc text,
                                                keydatapub text)''')

    def mCreateRacksTable(self):
        """
        Request fields:
            0. uuid
            1. rackid
            2. status
            3. owner
            4. timestamp-start
            5. timestamp-stop
        """
        if not self.mCheckTableExist('registry'):
            self.mExecute('''CREATE TABLE registry (uuid text,
                                                    rackid text,
                                                    status text,
                                                    owner text,
                                                    starttime text,
                                                    endtime text)''')

    def mCreateLocationTable(self):
        """
        Request fields:
            0. uuid
            1. rackid
            2. hostname
            3. path
        """
        if not self.mCheckTableExist('location'):
            self.mExecute('''CREATE TABLE location (uuid text,
                                                    rackid text,
                                                    hostname text,
                                                    path text)''')

    def mDropKeysTable(self):
        if self.mCheckTableExist('keys'):
            self.mExecute("DROP TABLE keys")

    def mDropRacksTable(self):
        if self.mCheckTableExist('registry'):
            self.mExecute("DROP TABLE registry")

    def mDropLocationTable(self):
        if self.mCheckTableExist('location'):
            self.mExecute("DROP TABLE location")

    def mDeleteKey(self, aHostname, aUser=None):
        if aUser is None:
            _sql = """DELETE FROM keys WHERE hostname=%(1)s"""
            _data = [aHostname]
        else:
            _sql = """DELETE FROM keys WHERE hostname=%(1)s and user=%(2)s"""
            _data = [aHostname,aUser]
        self.mExecute(_sql, _data)

    def mDeleteRack(self, aRackId='0'):

        _sql = """DELETE from registry WHERE rackid=%(1)s"""
        _data = [aRackId]
        self.mExecute(_sql, _data)

    def mDeleteLocation(self, aRackId='0'):

        _sql = """DELETE from location WHERE rackid=%(1)s"""
        _data = [aRackId]
        self.mExecute(_sql, _data)

    def mInsertKey(self, aKeyInfo):

        _ki = aKeyInfo
        _uuid       = _ki.mGetUUID()
        _hostname   = _ki.mGetHostname()
        _user       = _ki.mGetUser()
        _keydata    = _ki.mGetKeyData()
        _keydatapub = _ki.mGetKeyDataPub()
        _createtime = _ki.mGetCTime()
        _updatetime = _ki.mGetUTime()
        _misc       = _ki.mGetMisc()

        _sql = """INSERT INTO keys VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s, %(7)s, %(8)s)"""
        _data = [_uuid, _hostname, _user, _keydata, _createtime, _updatetime, _misc, _keydatapub]
        self.mExecute(_sql, _data)

    def mInsertRack(self, aRackInfo):

        _ai = aRackInfo
        _uuid      = _ai.mGetUUID()
        _rackid    = _ai.mGetRackID()
        _status    = _ai.mGetStatus()
        _owner     = _ai.mGetOwner()
        _ttstart   = _ai.mGetStartTime()
        _ttstop    = _ai.mGetEndTime()

        _sql = """INSERT INTO registry VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s)"""
        _data = [_uuid, _rackid, _status, _owner, _ttstart, _ttstop]
        self.mExecute(_sql, _data)

    def mInsertLocation(self, aRackInfo):

        _ai = aRackInfo
        _uuid      = _ai.mGetUUID()
        _rackid    = _ai.mGetRackID()
        _host      = _ai.mGetHostname()
        _path      = _ai.mGetPath()

        _sql = """INSERT INTO location VALUES (%(1)s, %(2)s, %(3)s, %(4)s)"""
        _data = [_uuid, _rackid, _host, _path]
        self.mExecute(_sql, _data)

    def mUpdateLocation(self, aRackInfo):

        _ai = aRackInfo
        _uuid      = _ai.mGetUUID()
        _rackid    = _ai.mGetRackID()
        _host      = _ai.mGetHostname()
        _path      = _ai.mGetPath()

        _sql = """UPDATE location SET uuid=%(1)s, rackid=%(2)s, hostname=%(3)s, path=%(4)s"""
        _data = [_uuid, _rackid, _host, _path]
        self.mExecute(_sql, _data)

    def mUpdateRack(self, aRackInfo):

        _ai = aRackInfo
        _uuid      = _ai.mGetUUID()
        _rackid    = _ai.mGetRackID()
        _status    = _ai.mGetStatus()
        _owner     = _ai.mGetOwner()
        _ttstart   = _ai.mGetStartTime()
        _ttstop    = _ai.mGetEndTime()

        _sql = """UPDATE registry SET uuid=%(1)s, rackid=%(2)s, status=%(3)s, 
                                      owner=%(4)s, starttime=%(5)s, endtime=%(6)s"""
        _data = [_uuid, _rackid, _status, _owner, _ttstart, _ttstop]
        self.mExecute(_sql, _data)

    def mUpdateKey(self, aKeyInfo):

        _ki = aKeyInfo
        _uuid       = _ki.mGetUUID()
        _hostname   = _ki.mGetHostname()
        _user       = _ki.mGetUser()
        _keydata    = _ki.mGetKeyData()
        _keydatapub = _ki.mGetKeyDataPub()
        _createtime = _ki.mGetCTime()
        _updatetime = _ki.mGetUTime()
        _misc       = _ki.mGetMisc()

        _sql = """UPDATE keys SET keydata=%(4)s, createtime=%(5)s, updatetime=%(6)s,
                                  misc=%(7)s, keydatapub=%(8)s 
                  WHERE UUID=%(1)s AND hostname=%(2)s AND user=%(3)s"""
        _data = [_uuid, _hostname, _user, _keydata, _createtime, _updatetime, _misc, _keydatapub]
        self.mExecute(_sql, _data)

    def mRackStatus(self, aRackId='0'):

        _sql = """SELECT * FROM registry WHERE rackid=%(1)s"""
        _data = [aRackId]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mLocationStatus(self, aRackId='0'):

        _sql = """SELECT * FROM location WHERE rackid=%(1)s"""
        _data = [aRackId]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mGetKey(self, aHostname, aUser=None):

        _rc = None
        if aUser is None:
            _sql = """SELECT * FROM keys WHERE hostname=%(1)s"""
            _data = [aHostname]
            _rc = self.mFetchOne(_sql, _data)
        else:
            _sql = """SELECT * FROM keys WHERE hostname=%(1)s AND user=%(2)s"""
            _data = [aHostname,aUser]
            _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mDumpKeys(self, aHostname):

        _body = '('
        _sql = """SELECT * FROM keys WHERE hostname=%(1)s"""
        _data = [aHostname]
        _rows = self.mFetchAll(_sql, _data)
        for row in _rows:
            _body = _body + str(row)+','
        _body = _body + ')'
        return _body

    def mDumpRacks(self, aRackID=None):

        _body = '('
        _rows = []

        if not aRackID:
            _sql = """SELECT * FROM registry ORDER BY rackid"""
            _rows = self.mFetchAll(_sql)
        else:
            _sql = """SELECT * FROM registry WHERE rackid=%(1)s"""
            _data = [aRackID]
            _rows = self.mFetchAll(_sql, _data)

        for row in _rows:
            _body = _body + str(row)+','
        _body = _body + ')'
        return _body

    def mDumpLocation(self, aRackID=None):

        _body = '('
        _rows = []

        if not aRackID:
            _sql = 'SELECT * FROM location ORDER BY rackid'
            _rows = self.mFetchAll(_sql)
        else:
            _sql = "SELECT * FROM location WHERE rackid=%(1)s"
            _data = [aRackID]
            _rows = self.mFetchAll(_sql, _data)

        for row in _rows:
            _body = _body + str(row)+','
        _body = _body + ')'
        return _body


####################
# OCIEXACC Keys DB #
####################


class ebKeysDB(ebMysqlDB):

    def __init__(self):
        ebMysqlDB.__init__(self, "keysdb")

    def mCreateSshkeyTable(self):

        if not self.mCheckTableExist('sshkey'):
            self.mExecute('''CREATE TABLE sshkey (cluster_name VARCHAR(255) PRIMARY KEY,
                                                        sshkeys text)''')

    def mUpsertSshkey(self, aCluster, aSshkey):
        _sql = """INSERT IGNORE INTO sshkey VALUES (%(1)s, %(2)s)"""
        _data = [aCluster, aSshkey]
        self.mExecute(_sql, _data)

        _sql = """UPDATE sshkey SET cluster_name=%(1)s, sshkeys=%(2)s where cluster_name=%(1)s"""
        _data = [aCluster, aSshkey]
        self.mExecute(_sql, _data)
        return 0, ''

    def mGetSshkey(self, aCluster):
        _sql = """SELECT sshkeys FROM sshkey WHERE cluster_name=%(1)s"""
        _data = [aCluster]
        _resp = self.mFetchOne(_sql, _data)
        if _resp:
            return 0, _resp[0]
        return 1, ''

    def mDeleteSshkeyTable(self):
        _sql = """DROP TABLE sshkey"""
        self.mExecute(_sql)


#####################
# Exacloud Database #
#####################


class ebExacloudDB(ebMysqlDB):

    def __init__(self):
        ebMysqlDB.__init__(self, "exacloud")
        self.mCreateRegTable()

    def mShutdownDB(self):
        ebMysqlDB.mShutdownDB(self)

    #Export data to current proxy location under db folder.
    def mExportProxyMigrationTables(self):

        _sql = "SELECT @@secure_file_priv"
        _mysql_file_location = None

        _list = self.mFetchOne(_sql)
        if _list is not None:
            _mysql_file_location = str(_list[0])

        self.mUpdateUUIDtoexacloudForAgentStart()

        _tables_to_export = ['exacloudinstances', 'requestuuidtoexacloud', 'proxyrequests']

        for _table in _tables_to_export:
            _file = os.path.join(_mysql_file_location, _table)
            _sql1 = "SELECT * INTO OUTFILE '{0}' FIELDS TERMINATED BY ',' LINES TERMINATED BY '|' FROM {1}".format(_file, _table)
            self.mExecuteLog(_sql1)

        return _mysql_file_location

    def mMigrateProxyDB(self, aPrimaryDbLocation):
        if not os.lstat(aPrimaryDbLocation):
            return False

        _sql = "SELECT @@secure_file_priv"
        _mysql_file_location = None

        _list = self.mFetchOne(_sql)
        if _list is not None:
            _mysql_file_location = str(_list[0])

        _tables_to_export = ['exacloudinstances', 'requestuuidtoexacloud', 'proxyrequests']
        for _table in _tables_to_export:
            _srcfile = os.path.join(aPrimaryDbLocation, _table)
            _destfile = os.path.join(_mysql_file_location, _table)
            shutil.copy(_srcfile, _destfile)
            os.remove(_srcfile)
            _sql1 = "LOAD DATA INFILE '{0}' REPLACE INTO TABLE {1} FIELDS TERMINATED BY ',' LINES TERMINATED BY '|'".format(_destfile, _table)
            self.mExecuteLog(_sql1)
            os.remove(_destfile)

        return True

    def mImportDataIntoTable(self, aTableToImport):

        _table_to_import = aTableToImport
        if self.mCheckTableExist(_table_to_import):
            _sql_count_records = f"SELECT count(*) FROM {_table_to_import}"
            _handle = self.mFetchOne(_sql_count_records)
            if _handle and int(_handle[0]) > 0:
                ebLogError(f"Could not import {_table_to_import} table data from backup since table is not empty.")
                return False
        else:
            ebLogError(f"Could not import {_table_to_import} table data from backup since table does not exist.")
            return False
        
        _sql = "SELECT @@secure_file_priv"
        _mysql_file_location = None

        _list = self.mFetchOne(_sql)
        if _list is not None:
            _mysql_file_location = str(_list[0])

        _backup_file_location = os.path.join(_mysql_file_location, f"{_table_to_import}.backup")
        _backup_metadata_file_location = f"{_backup_file_location}.metadata"

        if not os.path.exists(_backup_file_location) or not os.path.exists(_backup_metadata_file_location):
            ebLogWarn(f"Could not import {_table_to_import} table data from backup since backup files are absent.")
            ebLogDB('NFO', f"Could not import {_table_to_import} table data from backup since backup files are absent.")
            return False

        _columns = None
        with open(_backup_metadata_file_location) as _fd:
            _columns = _fd.readline()
        _sql_import = f"LOAD DATA INFILE '{_backup_file_location}' REPLACE INTO TABLE {_table_to_import} FIELDS TERMINATED BY ',' LINES TERMINATED BY '|' ({_columns})"
        self.mExecuteLog(_sql_import)
        os.remove(_backup_file_location)
        os.remove(_backup_metadata_file_location)

        return True

    """
    1. exakmshostname  : Host name for the current exakms entry.
    2. exakmsusername  : User name for the current exakms entry.
    3. exakmshash      : Unique hashkey for the current exakms entry.
    4. operation       : Operation type(Insert/Delete).
    5. exakmstimestamp : timestamp when the current operation was done for this entry.
    """
    def mCreateExaKmsHistoryTable(self):

        if not self.mCheckTableExist('exakmshistory'):
            self.mExecute('''CREATE TABLE exakmshistory (rowidx INTEGER NOT NULL AUTO_INCREMENT,
                                                         exakmshostname TEXT,
                                                         exakmsusername TEXT,
                                                         exakmshash TEXT,
                                                         operation TEXT,
                                                         exakmstimestamp TEXT,
                                                         PRIMARY KEY (rowidx))''')

    def mInsertIntoExaKmsHistory(self, aExaKmsEmtry: ExaKmsEntry, aOperationType: str) -> None:

        _exakms_host_name = aExaKmsEmtry.mGetFQDN()
        _exakms_user_name = aExaKmsEmtry.mGetUser()
        _exakms_hash = f'{aExaKmsEmtry.mGetHash()}'
        _timestamp = ExaKmsEntry.mGetCurrentTime()

        _sql = """INSERT INTO exakmshistory (exakmshostname, exakmsusername, exakmshash, operation, exakmstimestamp) VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s)"""
        _data = [str(_exakms_host_name), str(_exakms_user_name), _exakms_hash, aOperationType, _timestamp]
        self.mExecute(_sql, _data)

    def mGetRowsFromExaKmsHistory(self, aUser = None, aExaKmsHost = None, aLimitEntries = None):

        if self.mCheckTableExist('exakmshistory'):
            _sql = "SELECT exakmstimestamp, operation, exakmsusername, exakmshostname FROM exakmshistory"
            if aUser is not None and aExaKmsHost is not None:
                _sql = f"{_sql} WHERE exakmsusername = '{aUser}' AND exakmshostname LIKE '{aExaKmsHost}.%'"
            elif aUser is not None:
                _sql = f"{_sql} WHERE exakmsusername = '{aUser}'"
            elif aExaKmsHost is not None:
                _sql = f"{_sql} WHERE exakmshostname LIKE '{aExaKmsHost}.%'"

            _sql = f"{_sql} ORDER BY rowidx DESC"

            if aLimitEntries is not None:
                _sql = f"{_sql} LIMIT {aLimitEntries}"

            _list_of_history_nodes = list()
            _list_of_rows = self.mFetchAll(_sql)
            for _this_row in _list_of_rows:
                _rowdata_timestamp  = _this_row[0]
                _rowdata_operation  = _this_row[1]
                _rowdata_user_name  = _this_row[2]
                _rowdata_hostname   = _this_row[3]
                _history_node = ExaKmsHistoryNode(_rowdata_timestamp, _rowdata_operation, _rowdata_user_name, _rowdata_hostname)
                _list_of_history_nodes.append(_history_node)
            return _list_of_history_nodes

        return []

    """
    1. usedcpupercent:    Percentage of CPU being used currently.
    2. usedmemorypercent: Percentage of memory being used currently.
    3. updatetime:        Statistics obtain time.
    """
    def mCreateEnvironmentResourceDetails(self):

        if not self.mCheckTableExist('environmentresourcedetails'):
            self.mExecute('''CREATE TABLE environmentresourcedetails (usedcpupercent TEXT,
                                                                      usedmemorypercent TEXT,
                                                                      updatetime TEXT)''')

    def mInsertEnvironmentResourceDetails(self, aUsedCPUPercent, aUsedMemoryPercent):

        _sql1 = """SELECT usedcpupercent, usedmemorypercent FROM environmentresourcedetails"""
        _handle = self.mFetchOne(_sql1)
        if _handle is not None:
            return self.mUpdateEnvironmentResourceDetails(aUsedCPUPercent, aUsedMemoryPercent)

        _sql = """INSERT INTO environmentresourcedetails VALUES (%(1)s, %(2)s, %(3)s)"""
        #Using this timespec will ensure precision of the set time is to sec. Supervisor uses the format '%Y-%m-%d %H:%M:%S'!
        _data = [str(aUsedCPUPercent), str(aUsedMemoryPercent), f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"]
        self.mExecuteLog(_sql, _data)
        return True

    def mUpdateEnvironmentResourceDetails(self, aUsedCPUPercent=None, aUsedMemoryPercent=None):

        _sql1 = """SELECT count(*) FROM environmentresourcedetails"""
        _handle = self.mFetchOne(_sql1)
        if _handle is None:
            return False

        #Using this timespec will ensure precision of the set time is to sec. Supervisor uses the format '%Y-%m-%d %H:%M:%S'!
        _update_time = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
        if aUsedCPUPercent != None and aUsedMemoryPercent != None:
            _sql = """UPDATE environmentresourcedetails SET usedcpupercent=%(1)s, usedmemorypercent=%(2)s, updatetime=%(3)s"""
            _data = [str(aUsedCPUPercent), str(aUsedMemoryPercent), _update_time]
            self.mExecuteLog(_sql, _data)
        elif aUsedCPUPercent != None:
            _sql = """UPDATE environmentresourcedetails SET usedcpupercent=%(1)s, updatetime=%(2)s"""
            _data = [str(aUsedCPUPercent), _update_time]
            self.mExecuteLog(_sql, _data)
        elif aUsedMemoryPercent != None:
            _sql = """UPDATE environmentresourcedetails SET usedmemorypercent=%(1)s, updatetime=%(2)s"""
            _data = [str(aUsedMemoryPercent), _update_time]
            self.mExecuteLog(_sql, _data)
        else:
            return False
        return True

    def mSelectAllFromEnvironmentResourceDetails(self):

        if self.mCheckTableExist('environmentresourcedetails'):
            _sql = "SELECT usedcpupercent, usedmemorypercent, updatetime FROM environmentresourcedetails"

            _list = self.mFetchOne(_sql)
            if _list is not None or len(_list) > 0:
                _usedcpupercent = str(_list[0])
                _usedmemorypercent = str(_list[1])
                _updatetime = str(_list[2])
                return _usedcpupercent, _usedmemorypercent, _updatetime

        return None, None, None

    def mCreateExacloudInstanceTable(self):

        if not self.mCheckTableExist('exacloudinstances'):
            self.mExecute('''CREATE TABLE exacloudinstances (ecinstanceid VARCHAR(255) PRIMARY KEY,
                                                             hostname text,
                                                             port text,
                                                             version text,
                                                             status text,
                                                             authkey text,
                                                             reqtype text,
                                                             oeda_version text)''')
        """
        exacloudinstances fields:
            0. ecinstanceid
            1. hostname
            2. port
            3. version
            4. status
            5. authkey
            6. reqtype
            7. oeda_version
        """

    def mSelectAllFromExacloudInstance(self):

        if self.mCheckTableExist('exacloudinstances'):
            _sql = "SELECT ecinstanceid, hostname, port, version, status, authkey, reqtype, oeda_version FROM exacloudinstances"

            _list = self.mFetchAll(_sql)
            if len(_list) > 0:
                return _list
            return []
        else:
            return []

    def mSelectRoutingInfoFromECInstances(self, ecInstanceID):

        if self.mCheckTableExist('exacloudinstances'):
            _sql = "SELECT hostname, port, authkey FROM exacloudinstances WHERE ecinstanceid=%(1)s"
            _data = [ecInstanceID]

            _list = self.mFetchOne(_sql, _data)
            if _list is not None:
                _echostname = str(_list[0])
                _ecport = str(_list[1])
                _ecauthkey = str(_list[2])
                return _echostname, _ecport, _ecauthkey

        return None, None, None

    def mInsertExacloudInstanceInfo(self, aHostName, aPort, aVersion, aAuthKey, aReqType, aOedaVersion):

        _ecinstanceid  = "{0}:{1}".format(aHostName, aPort)
        _status = "Inactive"

        _sql1 = """SELECT ecinstanceid FROM exacloudinstances WHERE ecinstanceid=%(1)s"""
        _data1 = [_ecinstanceid]
        _handle = self.mFetchOne(_sql1, _data1)
        if _handle is not None:
            return

        _sql = """INSERT INTO exacloudinstances VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s, %(7)s, %(8)s)"""
        _data = [_ecinstanceid, str(aHostName), str(aPort), str(aVersion), _status, str(aAuthKey), str(aReqType), str(aOedaVersion)]
        self.mExecuteLog(_sql, _data)

    def mSelectAllFromRequestuuidtoExacloud(self, aReqStatus=None):
        if self.mCheckTableExist('requestuuidtoexacloud'):
            if aReqStatus:
                _sql = "SELECT requuid, ecinstanceid, reqstatus, requestcreationtimestamp FROM requestuuidtoexacloud WHERE reqstatus=%(1)s"
                _list = self.mFetchAll(_sql, [aReqStatus])
            else:
                _sql = "SELECT requuid, ecinstanceid, reqstatus, requestcreationtimestamp FROM requestuuidtoexacloud"
                _list = self.mFetchAll(_sql)

            if len(_list) > 0:
                return _list
            return []
        else:
            return []

    #Usage for Proxy heartbeat
    def mUpdateExacloudInstanceInfo(self, aEcinstanceID, aKey, aValue):

        _sql1 = """SELECT ecinstanceid FROM exacloudinstances WHERE ecinstanceid=%(1)s"""
        _data1 = [aEcinstanceID]
        _handle = self.mFetchOne(_sql1, _data1)
        if _handle is None:
            return False

        if aKey == 'status':
            _sql = """UPDATE exacloudinstances SET status=%(2)s WHERE ecinstanceid=%(3)s"""
        elif aKey == 'reqtype':
            _sql = """UPDATE exacloudinstances SET reqtype=%(2)s WHERE ecinstanceid=%(3)s"""
        else:
            return False
        _data = [aKey, aValue, aEcinstanceID]
        self.mExecuteLog(_sql, _data)
        return True

    def mCreateUUIDToExacloudInstanceTable(self):

        if not self.mCheckTableExist('requestuuidtoexacloud'):
            self.mExecute('''CREATE TABLE requestuuidtoexacloud (requuid VARCHAR(255) PRIMARY KEY,
                                                                 ecinstanceid text,
                                                                 reqstatus text,
                                                                 requestcreationtimestamp text)''')
        """
        requestuuidtoexacloud fields:
            0. requuid
            1. ecinstanceid
            2. reqstatus
            3. requestcreationtimestamp
        """

    def mSelectStatusFromUUIDToECInstance(self, aUUID):

        if self.mCheckTableExist('requestuuidtoexacloud'):
            _sql = """SELECT reqstatus FROM requestuuidtoexacloud WHERE requuid=%(1)s"""
            _data = [aUUID]

            _list = self.mFetchOne(_sql, _data)
            if _list is not None:
                return str(_list[0])
            return "InitialReqPending"
        else:
            return "InitialReqPending"

    def mInsertUUIDtoECInstanceInfo(self, areqUUID, aECInstanceID, aRequestCreationTimestamp):

        _status = "InitialReqPending"

        _sql1 = """SELECT ecinstanceid FROM requestuuidtoexacloud WHERE requuid=%(1)s"""
        _data1 = [areqUUID]
        _handle = self.mFetchOne(_sql1, _data1)
        if _handle is not None:
            return

        _sql = """INSERT INTO requestuuidtoexacloud VALUES (%(1)s, %(2)s, %(3)s, %(4)s)"""
        _data = [str(areqUUID), str(aECInstanceID), _status, str(aRequestCreationTimestamp)]
        self.mExecuteLog(_sql, _data)

    def mUpdateStatusForReqUUID(self, aReqUUID, aStatus):

        _sql1 = """SELECT ecinstanceid FROM requestuuidtoexacloud WHERE requuid=%(1)s"""
        _data1 = [aReqUUID]
        _handle = self.mFetchOne(_sql1, _data1)
        if _handle is None:
            return False

        _sql = """UPDATE requestuuidtoexacloud SET reqstatus=%(1)s WHERE requuid=%(2)s"""
        _data = [aStatus, aReqUUID]
        self.mExecuteLog(_sql, _data)
        return True
    
    def mSelectECInstanceIDFromUUIDToECInstance(self, aUUID):

        if self.mCheckTableExist('requestuuidtoexacloud'):
            _sql = """SELECT ecinstanceid FROM requestuuidtoexacloud WHERE requuid=%(1)s"""
            _data = [aUUID]

            _list = self.mFetchOne(_sql, _data)
            if _list is not None:
                return str(_list[0])

        return "None"

    def mUpdateUUIDtoexacloudForAgentStart(self):
        _updaterequestuuidtoexacloudtablequery = "UPDATE requestuuidtoexacloud SET reqstatus='InitialReqDone' WHERE reqstatus='Pending'"
        self.mExecute(_updaterequestuuidtoexacloudtablequery)

    def mCreateProxyRequestsTable(self):

        if not self.mCheckTableExist('proxyrequests'):
            self.mExecute('''CREATE TABLE proxyrequests (uuid VARCHAR(255) PRIMARY KEY,
                                                         cmdtype TEXT, 
                                                         params LONGTEXT, 
                                                         urlfullpath LONGTEXT,
                                                         urlheaders TEXT,
                                                         respbody LONGTEXT,
                                                         respcode INTEGER,
                                                         reqtype TEXT,
                                                         reqbody LONGTEXT)''')
        """
        proxyrequests fields:
            1. uuid
            2. cmdtype
            3. params
            4. urlfullpath
            5. urlheaders
            6. respbody
            7. respcode
            8. reqtype
            9. reqbody
        """

    def mInsertNewProxyRequest(self, aRequest):

        _uuid   = aRequest.mGetUUID()
        _ctype  = aRequest.mGetCmdType()
        _params = aRequest.mGetParams()
        if self.mGetMaskParams():
            _params = maskSensitiveData(aRequest.mGetParams(), full_mask=True)

        _reqbody   = aRequest.mGetReqBody()
        _urlfullpath = aRequest.mGetUrlFullPath()
        _urlheaders = aRequest.mGetUrlHeaders()
        _respbody = aRequest.mGetRespBody()
        _respcode = aRequest.mGetRespCode()
        _reqtype = aRequest.mGetReqType()

        _sql = """INSERT INTO proxyrequests(uuid, cmdtype, params, reqbody, urlfullpath, urlheaders, respbody, respcode, reqtype)
                  VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s, %(7)s, %(8)s, %(9)s)"""
        _data = [_uuid, _ctype, _params, _reqbody, _urlfullpath, _urlheaders, _respbody, _respcode, _reqtype]
        self.mExecuteLog(_sql, _data)

    def mGetProxyRequest(self, aUUID):
        _rc = None
        _sql = """SELECT uuid, cmdtype, params, reqbody, urlfullpath, urlheaders, respbody, respcode, reqtype FROM proxyrequests WHERE uuid=%(1)s"""
        _data = [aUUID]
        _rc = self.mFetchOne(_sql, _data)
        if _rc:
            try:
                _params = umaskSensitiveData(_rc[2], full_mask=True)
            except:
                _params = ast.literal_eval(_rc[2])
                _params = umaskSensitiveData(_params, full_mask=False)
            row = list(_rc)
            row[2] = str(_params)
            return tuple(row)

    def mUpdateProxyRequest(self, aRequest):

        _uuid   = aRequest.mGetUUID()
        _ctype  = aRequest.mGetCmdType()
        _params = aRequest.mGetParams()
        if self.mGetMaskParams():
            _params = maskSensitiveData(aRequest.mGetParams(), full_mask=True)

        _reqbody   = aRequest.mGetReqBody()
        _urlfullpath = aRequest.mGetUrlFullPath()
        _urlheaders = aRequest.mGetUrlHeaders()
        _respbody = aRequest.mGetRespBody()
        _respcode = aRequest.mGetRespCode()
        _reqtype = aRequest.mGetReqType()

        _sql = """UPDATE proxyrequests
                  SET cmdtype=%(1)s, params=%(2)s, reqbody=%(3)s, urlfullpath=%(4)s,
                      urlheaders=%(5)s, respbody=%(6)s, respcode=%(7)s, reqtype=%(8)s  WHERE uuid=%(9)s"""
        _data = [_ctype, _params, _reqbody, _urlfullpath, _urlheaders, _respbody, _respcode, _reqtype, _uuid]
        self.mExecuteLog(_sql, _data)

    def mUpdateResponseDetailsInProxyRequest(self, aUUID, aRespCode, aRespBody, aRespUrlHeaders):

        _sql = """UPDATE proxyrequests SET respcode=%(1)s, respbody=%(2)s, urlheaders=%(3)s WHERE uuid=%(4)s"""
        _data = [aRespCode, aRespBody, aRespUrlHeaders, aUUID]
        self.mExecuteLog(_sql, _data)

    def mSelectResponseDetailsFromProxyRequests(self, aUUID):

        if self.mCheckTableExist('proxyrequests'):
            _sql = """SELECT respcode, respbody, urlheaders FROM proxyrequests WHERE uuid=%(1)s"""
            _data = [aUUID]

            _list = self.mFetchOne(_sql, _data)
            return _list
        else:
            return ["None", "None", "None"]

    def mCreateMockCallTable(self):

        if not self.mCheckTableExist('mock_calls'):
            self.mExecute('''CREATE TABLE mock_calls (uuid VARCHAR(255) PRIMARY KEY,
                                                      starttime TEXT, 
                                                      status TEXT,
                                                      cmdtype TEXT,
                                                      xml LONGTEXT,
                                                      params LONGTEXT)''')
                                

    def mInsertMockCall(self, aJobReqObj):

        _sql = """INSERT INTO mock_calls 
                  (uuid, starttime, status, cmdtype, xml, params)
                  VALUES 
                  (%(uuid)s, %(starttime)s, %(status)s, %(cmdtype)s, %(xml)s, %(params)s)"""

        _data = aJobReqObj.mToDictMock()

        self.mExecute(_sql, _data)
        self.mCommit()

    def mGetMockCallByUUID(self, aUUID):

        _sql = """SELECT uuid, starttime, status, cmdtype, xml, params
                  FROM mock_calls
                  WHERE uuid = %(1)s"""

        _data = [aUUID]

        return self.mFetchOne(_sql, _data)

    def mCreateAgentSignalTable(self):
        """
        Request fields:
            0. uuid
            1. name
            2. pid
            3. extra_args
        """

        if not self.mCheckTableExist('agent_signal'):
            _columns = ",".join(list(map(lambda col: f"{col} TEXT", AgentSignal.mGetColumns())))
            self.mExecute(f'''CREATE TABLE agent_signal ({_columns})''')

    def mInsertAgentSignal(self, aAgentSignal: AgentSignal) -> None:

        _signalDict = aAgentSignal.mToDict()

        # Get the columns and format the column names
        _columns = AgentSignal.mGetColumns()
        _formatCols = list(map(lambda x: f"%({x})s", _columns))

        # Transform the columns into strings
        _columns = ",".join(_columns)
        _formatCols = ",".join(_formatCols)

        # Create the final query
        _sql = f"INSERT INTO agent_signal ({_columns}) VALUES ({_formatCols})"

        # Execute the new query
        self.mExecute(_sql, _signalDict)


    def mFilterAgentSignal(self, aAgentSignalCriteria: Dict) -> List[AgentSignal]:

        # Get all valid columns
        _validCriteria = {}
        _allColumns = AgentSignal.mGetColumns()

        for _column, _value in aAgentSignalCriteria.items():
            if _column in _allColumns and re.match("[a-z0-9\-]", _value):
                _validCriteria[_column] = _value

        # Get string of all columns
        _allColumns = ",".join(_allColumns)
        _sql = f"SELECT {_allColumns} FROM agent_signal"

        if _validCriteria:

            _equals = list(map(lambda col: f"{col}=%({col})s", _validCriteria.keys()))
            _formatCols = " AND ".join(_equals)

            _sql = f"{_sql} WHERE {_formatCols}"

        # Get the data from DB
        _data = None

        if _validCriteria:
            _data = self.mFetchAll(_sql, _validCriteria)
        else:
            _data = self.mFetchAll(_sql)

        # Transform the data in List of objects
        _listSignals = []

        if _data:
            for _row in _data:
                _signal = AgentSignal()
                _signal.mPopulate(_row)
                _listSignals.append(_signal)

        return _listSignals

    def mDeleteAgentSignal(self, aAgentSignal: AgentSignal) -> None:

        _dict = aAgentSignal.mToDict()
        _pk = AgentSignal.mGetPrimaryKey()
        _pkValue = _dict[_pk]

        _sql = f"DELETE FROM agent_signal WHERE {_pk} = %(1)s"
        self.mExecute(_sql, [_pkValue])


    def mCreateDataCacheTable(self):

        if not self.mCheckTableExist('data_cache'):
            self.mExecute('''CREATE TABLE data_cache (name TEXT,
                                                 data TEXT,
                                                 creation_date TEXT)''')
        """
        data_cache fields:
            0. name
            1. data
            2. creation_date
        """

    def mInsertDataCache(self, aName: str, aData: str):

        _name = aName
        _dataStr = aData
        _sql = """INSERT INTO data_cache VALUES (%(1)s, %(2)s, %(3)s)"""
        _data = [_name, _dataStr, time.strftime("%c")]
        self.mExecute(_sql, _data)

    def mDelDataCache(self, aName: str):

        _name = aName
        _sql = """DELETE FROM data_cache WHERE name=%(1)s"""
        _data = [_name]
        self.mExecute(_sql, _data)

    def mUpdateDataCache(self, aName: str, aData: str):

        _name = aName
        _dataStr = aData
        _date = time.strftime("%c")
        _sql = """UPDATE data_cache
                  SET data=%(1)s, creation_date=%(2)s WHERE name=%(3)s"""
        _data = [_dataStr, _date, _name]
        self.mExecute(_sql, _data)

    def mGetDataCacheByName(self, aName: str):

        _name = aName
        _sql = """SELECT name, data, creation_date FROM data_cache WHERE name=%(1)s"""
        _data = [_name]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mGetDataFromDataCacheByName(self, aName: str):

        _name = aName
        _sql = """SELECT data FROM data_cache WHERE name=%(1)s"""
        _data = [_name]
        _rc = self.mFetchOne(_sql, _data)
        _out = None
        if _rc and len(_rc) > 0:
            _out = _rc[0]

        return _out

 
    def mCreateAgentTable(self):

        if not self.mCheckTableExist('agent'):
            self.mExecute('''CREATE TABLE agent (uuid TEXT,
                                                 pid TEXT,
                                                 status TEXT,
                                                 ttstart TEXT,
                                                 ttstop TEXT,
                                                 hostname TEXT,
                                                 port TEXT,
                                                 misc text)''')
        """
        Request fields:
            0. uuid
            1. pid
            2. status
            3. timestamp-start
            4. timestamp-stop
            5. hostname
            6. port
            7. misc
        """

    def mStartAgent(self, aAgentId='0', aPid='0'):

        _sql = """UPDATE agent SET pid=%(1)s, status=%(2)s, ttstart=%(3)s, ttstop=%(4)s, misc=%(5)s
                  WHERE uuid=%(6)s"""

        _data = [aPid, 'running', time.ctime(), 'None', '{}', aAgentId]
        self.mExecute(_sql, _data)

    def mStopAgent(self, aAgentId='0'):

        _sql = """UPDATE agent SET status=%(1)s, ttstop=%(2)s, misc=%(3)s WHERE uuid=%(4)s"""
        _data = ['stopped', time.ctime(), '{}', aAgentId]
        self.mExecute(_sql, _data)

    def mGetAgentsPID(self):
        _sql = """SELECT pid FROM agent"""
        return self.mFetchAll(_sql)

    def mDeleteAgent(self, aAgentId='0'):

        _sql = """DELETE FROM agent WHERE uuid=%(1)s"""
        _data = [aAgentId]
        self.mExecute(_sql, _data)

    def mInsertAgent(self, aAgentInfo):

        _ai = aAgentInfo
        _uuid      = _ai.mGetUUID()
        _pid       = _ai.mGetPid()
        _status    = _ai.mGetStatus()
        _ttstart   = _ai.mGetStartTime()
        _ttstop    = _ai.mGetEndTime()
        _hostnname = _ai.mGetHostname()
        _port      = _ai.mGetPort()
        _misc      = _ai.mGetMisc()

        _sql = """INSERT INTO agent VALUES (%(1)s, %(2)s, %(3)s, %(4)s,
                                            %(5)s, %(6)s, %(7)s, %(8)s)"""
        _data = [_uuid, _pid, _status, _ttstart, _ttstop, _hostnname, _port, _misc]
        self.mExecute(_sql, _data)

    def mUpdateAgent(self, aAgentInfo):

        _ai = aAgentInfo
        _uuid      = _ai.mGetUUID()
        _pid       = _ai.mGetPid()
        _status    = _ai.mGetStatus()
        _ttstart   = _ai.mGetStartTime()
        _ttstop    = _ai.mGetEndTime()
        _hostnname = _ai.mGetHostname()
        _port      = _ai.mGetPort()
        _misc      = _ai.mGetMisc()

        _sql = """UPDATE agent SET uuid=%(1)s, pid=%(2)s, status=%(3)s, ttstart=%(4)s,
                                   ttstop=%(5)s, hostname=%(6)s, port=%(7)s, misc=%(8)s"""
        _data = [_uuid, _pid, _status, _ttstart, _ttstop, _hostnname, _port, _misc]
        self.mExecute(_sql, _data)

    def mAgentStatus(self, aAgentId='0'):

        _sql = """SELECT * FROM agent WHERE uuid=%(1)s"""
        _data = [aAgentId]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mCreateScheduleTable(self):

        if not self.mCheckTableExist('schedule'):
            self.mExecute('''CREATE TABLE schedule (
                      uuid VARCHAR(255) PRIMARY KEY,
                      command TEXT,
                      mode TEXT,
                      operation TEXT,
                      event TEXT,
                      timer_type TEXT,
                      timestamp TEXT,
                      _interval TEXT,
                      repeat_count TEXT,
                      last_repeat_count int,
                      monitor_uuid TEXT,
                      monitor_worker_jobs TEXT,
                      status TEXT,
                      requests_uuid VARCHAR(255))''')
        """
        Request fields:
            0.  uuid
            1.  command
            2.  mode
            3.  operation
            4.  event
            5.  timer_type
            6.  timestamp
            7.  interval
            8.  repeat_count
            9.  last_repeat_count
            10.  monitor_uuid
            11. monitor_worker_jobs
            12. status
            13. request_uuid
        """

    def mInsertNewSchedule(self, aScheduleInfo):

        _uuid      = aScheduleInfo.mGetUUID()
        _command   = aScheduleInfo.mGetScheduleCommand()
        _mode = aScheduleInfo.mGetScheduleMode()
        _operation = aScheduleInfo.mGetScheduleOperation()
        _event = aScheduleInfo.mGetScheduleEvent()
        _timer_type = aScheduleInfo.mGetScheduleTimerType()
        _timestamp = aScheduleInfo.mGetScheduleTimestamp()
        _interval = aScheduleInfo.mGetScheduleInterval()
        _repeat_count = aScheduleInfo.mGetScheduleRepeatCount()
        _last_repeat_count = aScheduleInfo.mGetScheduleLastRepeatCount()
        _monitor_uuid = aScheduleInfo.mGetScheduleMonitorUUID()
        _monitor_worker_jobs = aScheduleInfo.mGetScheduleMonitorWorkerJobs()
        _status = aScheduleInfo.mGetScheduleStatus()

        _sql = """INSERT INTO schedule VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s,
                                              %(7)s, %(8)s, %(9)s, %(10)s, %(11)s,
                                              %(12)s, %(13)s, %(14)s)"""
        _data = [ _uuid, _command, _mode, _operation, _event, _timer_type, _timestamp, \
                 _interval, _repeat_count, _last_repeat_count, _monitor_uuid, \
                 _monitor_worker_jobs, _status, _uuid ]
        self.mExecute(_sql, _data)

    def mUpdateSchedule(self, aScheduleInfo):

        _uuid      = aScheduleInfo.mGetUUID()
        _command   = aScheduleInfo.mGetScheduleCommand()
        _mode = aScheduleInfo.mGetScheduleMode()
        _operation = aScheduleInfo.mGetScheduleOperation()
        _event = aScheduleInfo.mGetScheduleEvent()
        _timer_type = aScheduleInfo.mGetScheduleTimerType()
        _timestamp = aScheduleInfo.mGetScheduleTimestamp()
        _interval = aScheduleInfo.mGetScheduleInterval()
        _repeat_count = aScheduleInfo.mGetScheduleRepeatCount()
        _last_repeat_count = aScheduleInfo.mGetScheduleLastRepeatCount()
        _monitor_uuid = aScheduleInfo.mGetScheduleMonitorUUID()
        _monitor_worker_jobs = aScheduleInfo.mGetScheduleMonitorWorkerJobs()
        _status = aScheduleInfo.mGetScheduleStatus()

        _sql = """UPDATE schedule SET operation=%(1)s, timer_type=%(2)s, timestamp=%(3)s,
                                      _interval=%(4)s, repeat_count=%(5)s, last_repeat_count=%(6)s,
                                      monitor_uuid=%(7)s, monitor_worker_jobs=%(8)s,
                                      status=%(9)s  WHERE uuid=%(10)s"""
        _data = [_operation, _timer_type, _timestamp, _interval, _repeat_count, \
                 _last_repeat_count, _monitor_uuid, _monitor_worker_jobs, _status, _uuid]
        self.mExecute(_sql, _data)

    def mGetScheduleByCommand(self, aCommand):

        _sql = """SELECT * FROM schedule WHERE command=%(1)s"""
        _rc = self.mFetchOne(_sql, [aCommand])
        return _rc

    def mGetSchedule(self):

        _sql = """SELECT * FROM schedule"""
        _rc = self.mFetchAll(_sql)
        return _rc

    def mGetScheduleByType(self, aUUID):

        _uuid   = aUUID
        _sql = """SELECT * FROM schedule WHERE uuid=%(1)s"""
        _data = [_uuid]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mDelScheduleEntry(self, aScheduleInfo=None, aForce=False):

        _data = []
        if aForce:
            _sql = """DELETE FROM schedule"""
        else:
            _uuid   = aScheduleInfo.mGetUUID()
            _sql = """DELETE FROM schedule WHERE uuid=%(1)s"""
            _data = [_uuid]

        self.mExecute(_sql, _data)

    def mCreateScheduleArchiveTable(self):

        if not self.mCheckTableExist('schedule_archive'):
            self.mExecute('''CREATE TABLE schedule_archive (
                      uuid VARCHAR(255) PRIMARY KEY,
                      command TEXT,
                      mode TEXT,
                      operation TEXT,
                      event TEXT,
                      status TEXT,
                      error TEXT,
                      error_str TEXT,
                      statusinfo TEXT,
                      clustername TEXT,
                      last_repeat_count int)''')
        """
        Request fields:
            0.  uuid
            1.  command
            2.  mode
            3.  operation
            4.  event
            5.  status
            6.  error
            7.  error_str
            8.  statusinfo
            9.  clustername
           10.  last_repeat_count
        """

    def mInsertNewScheduleArchive(self, aScheduleInfo):

        _uuid      = aScheduleInfo.mGetUUID()
        _command   = aScheduleInfo.mGetScheduleCommand()
        _mode = aScheduleInfo.mGetScheduleMode()
        _operation = aScheduleInfo.mGetScheduleOperation()
        _event = aScheduleInfo.mGetScheduleEvent()
        _last_repeat_count = aScheduleInfo.mGetScheduleLastRepeatCount()

        _sql = """INSERT INTO schedule_archive
                  VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s,
                          %(6)s, %(7)s, %(8)s, %(9)s,
                          %(10)s, %(11)s)"""
        _data = [ _uuid, _command, _mode, _operation, _event, '', '', '', '', '', \
                  _last_repeat_count ]
        self.mExecute(_sql, _data)

    def mUpdateScheduleArchive(self, aScheduleInfo):

        _uuid      = aScheduleInfo.mGetUUID()
        _command   = aScheduleInfo.mGetScheduleCommand()
        _operation = aScheduleInfo.mGetScheduleOperation()
        _event = aScheduleInfo.mGetScheduleEvent()
        _timer_type = aScheduleInfo.mGetScheduleTimerType()
        _timestamp = aScheduleInfo.mGetScheduleTimestamp()
        _interval = aScheduleInfo.mGetScheduleInterval()
        _repeat_count = aScheduleInfo.mGetScheduleRepeatCount()
        _last_repeat_count = aScheduleInfo.mGetScheduleLastRepeatCount()
        _monitor_uuid = aScheduleInfo.mGetScheduleMonitorUUID()
        _status = aScheduleInfo.mGetScheduleStatus()

        _sql = """UPDATE schedule_archive
                  SET command=%(1)s, operation=%(2)s, event=%(3)s,
                      last_repeat_count=%(4)s  WHERE uuid=%(5)s"""
        _data = [ _command, _operation, _event, _last_repeat_count, _uuid ]
        self.mExecute(_sql, _data)

    def mUpdateScheduleArchiveByType(self, aUUID):

        _uuid      = aUUID
        _sql = """SELECT status, error, error_str, statusinfo, clustername
                  FROM requests WHERE uuid=%(1)s"""
        _data = [_uuid]
        _rc = self.mFetchOne(_sql, _data)

        _status = _rc[0]
        _error = _rc[1]
        _error_str = _rc[2]
        _status_info = _rc[3]
        _clustername = _rc[4]

        _sql = """UPDATE schedule_archive
                  SET status=%(1)s, error=%(2)s, error_str=%(3)s,
                      statusinfo=%(4)s, clustername=%(5)s  WHERE uuid=%(6)s"""
        _data = [ _status, _error, _error_str, _status_info, _clustername, _uuid ]
        self.mExecute(_sql, _data)

    def mGetScheduleArchiveByType(self, aUUID):

        _uuid   = aUUID
        _sql = """SELECT * FROM schedule_archive WHERE uuid=%(1)s"""
        _data = [_uuid]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mDelScheduleArchiveEntry(self, aScheduleInfo=None, aForce=False):

        _data = []
        if aForce:
            _sql = """DELETE FROM schedule_archive"""
        else:
            _uuid   = aScheduleInfo.mGetUUID()
            _sql = """DELETE FROM schedule_archive WHERE uuid=%(1)s"""
            _data = [_uuid]

        self.mExecute(_sql, _data)

    def mCreateWorkersTable(self):

        if not self.mCheckTableExist('workers'):
            self.mExecute('''CREATE TABLE workers (uuid TEXT,
                                                   status TEXT,
                                                   starttime TEXT,
                                                   endtime TEXT,
                                                   params LONGTEXT,
                                                   error TEXT,
                                                   error_str TEXT,
                                                   statusinfo TEXT,
                                                   pid TEXT,
                                                   port VARCHAR(255) PRIMARY KEY,
                                                   type TEXT,
                                                   synclock TEXT,
                                                   lastactivetime TEXT,
                                                   state TEXT)''')
        """
        Request fields:
            0. uuid
            1. status
            2. timestamp-start
            3. timestamp-stop
            4. params
            5. error
            6. error_str
            7. statusinfo
            8. pid
            9. port
           10. type
           11. synclock
           12. lastactivetime
           13. state
        """
    def mInsertNewWorker(self, aWorker):

        _uuid   = aWorker.mGetUUID()
        _status = aWorker.mGetStatus()
        _time   = aWorker.mGetTimeStampStart()
        _end    = aWorker.mGetTimeStampEnd()
        _params = aWorker.mGetParams()
        _error  = aWorker.mGetError()
        _error_str = aWorker.mGetErrorStr()
        _statusinfo = json.dumps(aWorker.mGetStatusInfo())
        _pid    = aWorker.mGetPid()
        _port   = aWorker.mGetPort()
        _type   = aWorker.mGetType()
        _synclock = "Undef"
        _lastactivetime = f"{datetime.now()}"
        _state = aWorker.mGetState()

        _sql = """INSERT INTO workers
                  VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s,
                          %(7)s, %(8)s, %(9)s, %(10)s, %(11)s, %(12)s, %(13)s, %(14)s)"""
        _data = [_uuid, _status, _time, _end, _params, _error, _error_str, \
                 _statusinfo, _pid, _port, _type, _synclock, _lastactivetime, _state]
        self.mExecute(_sql, _data)

        self.mCleanRegistryTableByWorker(_port)

    def mUpdateWorker(self, aWorker):

        _uuid   = aWorker.mGetUUID()
        _end    = aWorker.mGetTimeStampEnd()
        _status = aWorker.mGetStatus()
        _statusinfo = json.dumps(aWorker.mGetStatusInfo())
        _error  = aWorker.mGetError()
        _error_str = aWorker.mGetErrorStr()
        _port   = aWorker.mGetPort()
        _pid    = aWorker.mGetPid()
        _type   = aWorker.mGetType()
        _time   = aWorker.mGetTimeStampStart()
        _synclock = aWorker.mGetSyncLock()
        _lastactivetime = f"{aWorker.mGetLastActiveTime()}"
        _state = aWorker.mGetState()

        _sql = """UPDATE workers
                  SET status=%(1)s, statusinfo=%(6)s, endtime=%(2)s, error=%(3)s,
                      error_str=%(4)s, pid=%(7)s, uuid=%(8)s, starttime=%(9)s, type=%(10)s, synclock=%(11)s, lastactivetime=%(12)s, state= %(13)s
                  WHERE port=%(5)s"""
        _data = [_status, _end, _error, _error_str, _port, _statusinfo, _pid, _uuid, _time, _type, _synclock, _lastactivetime, _state]
        self.mExecute(_sql, _data)

    def mGetWorker(self, aPort):

        _sql = """SELECT * FROM workers WHERE port=%(1)s"""
        _data = [aPort]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mGetWorkerByPid(self, aPid):

        _sql = """SELECT * FROM workers WHERE pid=%(1)s"""
        _data = [aPid]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mGetWorkerByType(self, aType):

        _sql = """SELECT * FROM workers WHERE type=%(1)s"""
        _data = [aType]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mGetSpecialWorkerPIDs(self):

        _sql = """SELECT type, pid FROM workers WHERE type != 'worker'"""
        _rows = self.mFetchAll(_sql)
        _process_pid_mapping = dict()
        for _row in _rows:
            _process_pid_mapping[_row[0]] = int(_row[1])
        return _process_pid_mapping

    def mGetWorkerPortByUUID(self, aUUID):
        _sql = """SELECT port FROM workers WHERE uuid=%(1)s"""
        _data = [aUUID]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mGetWorkerPorts(self):

        _sql = """SELECT port FROM workers WHERE type = 'worker'"""
        _rows = self.mFetchAll(_sql)
        _port_list_workers = list()
        for _row in _rows:
            _port_list_workers.append(_row[0])
        return _port_list_workers

    def mGetWorkerStatus(self):

        _sql = """SELECT w.port, w.uuid, w.status, r.clustername, r.cmdtype
                  FROM workers w
                  LEFT OUTER JOIN requests r
                  ON w.uuid=r.uuid
                  WHERE w.type='worker'"""
        _rc = self.mFetchAll(_sql)
        return _rc

    def mDelWorkerEntry(self, aWorker):

        _port = aWorker.mGetPort()
        _sql = """DELETE FROM workers WHERE port=%(1)s"""
        _data = [_port]
        self.mExecute(_sql, _data)

        self.mCleanRegistryTableByWorker(_port)


    def mAcquireWorkerSyncLock(self, aPort=None, aProcessName=None):
        if aPort == None or aProcessName == None or aProcessName == "Undef":
            return False
        _sql = """UPDATE workers SET synclock = IF(synclock = 'Undef', %(1)s, synclock) WHERE port = %(2)s"""
        _data = [aProcessName, aPort]
        self.mExecuteLog(_sql, _data)

        _sql = """SELECT synclock from workers WHERE port = %(1)s"""
        _data = [aPort]
        _result_set = self.mFetchOne(_sql, _data)
        if _result_set[0] == aProcessName:
            return True
        return False

    def mReleaseWorkerSyncLock(self, aPort=None, aProcessName=None):
        if aPort == None or aProcessName == None or aProcessName == "Undef":
            return False

        _maxretries = 3
        _retrycnt = 0
        while _retrycnt <= _maxretries:
            _sql = """UPDATE workers SET synclock = IF(synclock = %(1)s, 'Undef', synclock) WHERE port = %(2)s"""
            _data = [aProcessName, aPort]
            _rc = self.mExecuteLog(_sql, _data)

            _sql = """SELECT synclock from workers WHERE port = %(1)s"""
            _data = [aPort]
            _result_set = self.mFetchOne(_sql, _data)
            if _result_set is None:
                ebLogWarn(f"*** mReleaseWorkerSyncLock: Result set from selecting synclock value returned None for port {aPort}")
            elif _result_set[0] == "Undef":                                                                                                                                                                          
                return True

            _retrycnt += 1
            if _result_set is not None:
                ebLogWarn(f"*** mReleaseWorkerSyncLock: Update synclock returned: {_rc}, lock owner: {_result_set[0]}")
            if _retrycnt <= _maxretries:
                ebLogWarn(f"*** mReleaseWorkerSyncLock: Retry attempt #{_retrycnt} for update operation after 1 second.")
            time.sleep(1)
        ebLogError(f"*** mReleaseWorkerSyncLock: Unable to release synclock held by {aProcessName} for port {aPort}")
        return False

    def mReleaseWorkerSyncLockForAllWorkersDuringStart(self):
        _sql = """UPDATE workers SET synclock = 'Undef'"""
        self.mExecuteLog(_sql)


    #
    # Cluster Status Table
    #
    def mCreateClusterStatusTable(self):

        if not self.mCheckTableExist('status'):
            self.mExecute("""CREATE TABLE status (cluid TEXT,
                                                  hostname VARCHAR(255) PRIMARY KEY,
                                                  nodetype TEXT,
                                                  network TEXT,
                                                  pingable TEXT,
                                                  ssh_conn TEXT,
                                                  pwd_auth TEXT,
                                                  root_sshd TEXT,
                                                  weak_pwd TEXT,
                                                  misc_dict text)""")
        """
        Request fields:
            0. cluid
            1. hostname
            2. nodetype
            3. network
            4. pingable
            5. ssh_conn
            6. pwd_auth
            7. root_sshd
            8. weak_pwd
            9. misc_dict
        """
    def mInsertNewClusterStatus(self, aCluster):

        _cluid      = aCluster.mGetClusterId()
        _hostname   = aCluster.mGetHostname()
        _nodetype   = aCluster.mGetNodeType()
        _network    = aCluster.mGetNetworkIp()
        _pingable   = aCluster.mGetPingable()
        _ssh_conn   = aCluster.mGetSSHConnection()
        _pwd_auth   = aCluster.mGetPwdAuthentication()
        _root_sshd  = aCluster.mGetRootSSHDMode()
        _weak_pwd   = aCluster.mGetWeakPassword()
        _misc_dict  = aCluster.mGetDictData()

        _sql = """INSERT INTO status
                  VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s,
                          %(7)s, %(8)s, %(9)s, %(10)s)"""
        _data = [_cluid,_hostname,_nodetype,_network,_pingable,_ssh_conn,_pwd_auth, \
                 _root_sshd,_weak_pwd,_misc_dict]
        self.mExecute(_sql, _data)

    def mUpdateClusterStatus(self, aCluster):

        _cluid      = aCluster.mGetClusterId()
        _hostname   = aCluster.mGetHostname()
        _nodetype   = aCluster.mGetNodeType()
        _network    = aCluster.mGetNetworkIp()
        _pingable   = aCluster.mGetPingable()
        _ssh_conn   = aCluster.mGetSSHConnection()
        _pwd_auth   = aCluster.mGetPwdAuthentication()
        _root_sshd  = aCluster.mGetRootSSHDMode()
        _weak_pwd   = aCluster.mGetWeakPassword()
        _misc_dict  = aCluster.mGetDictData()

        _sql = """UPDATE status
                  SET cluid=%(1)s, nodetype=%(3)s, network=%(4)s, pingable=%(5)s,
                      ssh_conn=%(6)s, pwd_auth=%(7)s, root_sshd=%(8)s, weak_pwd=%(9)s,
                      misc_dict=%(10)s WHERE hostname=%(2)s"""
        _data = [_cluid,_hostname,_nodetype,_network,_pingable,_ssh_conn,_pwd_auth, \
                 _root_sshd,_weak_pwd,_misc_dict]
        self.mExecute(_sql, _data)

    def mGetClusterStatus(self, aHost):

        _sql = """SELECT * FROM status WHERE hostname=%(1)s"""
        _data = [aHost]
        _rc = self.mFetchOne(_sql, _data)
        return _rc

    def mDumpClusterStatus(self, aCluId=None):

        _body = '('
        if not aCluId:
            _list = self.mFetchAll('SELECT * FROM status ORDER BY cluid')
            for row in _list:
                _body = _body + str(row)+','
        else:
            _sql = 'SELECT * FROM status WHERE cluid=%(1)s'
            _data = [aCluId]
            _list = self.mFetchAll(_sql, _data)
            for row in _list:
                _body = _body + str(row)+','
        _body = _body + ')'
        return _body

    #
    # Registry Table
    #
    def mCreateRegTable(self):

        if not self.mCheckTableExist('registry'):
            self.mExecute('''CREATE TABLE registry (_key TEXT,
                                                    value TEXT,
                                                    uuid TEXT,
                                                    worker TEXT)''')
    
    def mCreateSELinuxPolicyTable(self):

        if not self.mCheckTableExist('selinuxpolicystore'):
            self.mExecute('''CREATE TABLE selinuxpolicystore (requuid VARCHAR(255),
                                                              hostname TEXT,
                                                              createtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                              selinuxpolicy LONGTEXT,
                                                              syncedtoecra VARCHAR(255) DEFAULT 'F')''')

    def mInsertGeneratedSELinuxPolicy(self, aUUID, aHostName, aBase64EncodedSELinuxPolicy):

        _synced_to_ecra = "F"
        _sql = """INSERT INTO selinuxpolicystore(requuid, hostname, selinuxpolicy) VALUES (%(1)s, %(2)s, %(3)s)"""
        _data = [aUUID, aHostName, aBase64EncodedSELinuxPolicy]
        self.mExecuteLog(_sql, _data)

    def mGetUnsyncedSELinuxPolicy(self, aHostName):

        _sql = """SELECT selinuxpolicy FROM selinuxpolicystore WHERE hostname=%(1)s AND syncedtoecra = 'F'"""
        _data = [aHostName]
        return self.mFetchAll(_sql, _data)

    def mGetAllSELinuxPolicy(self, aHostName):

        _sql = """SELECT selinuxpolicy FROM selinuxpolicystore WHERE hostname=%(1)s"""
        _data = [aHostName]
        return self.mFetchAll(_sql, _data)

    def mGetSELinuxViolationStatusForRequest(self, aUUID):

        _sql = """SELECT selinuxpolicy FROM selinuxpolicystore WHERE requuid=%(1)s"""
        _data = [aUUID]
        _listOfPolicies = self.mFetchAll(_sql, _data)
        if len(_listOfPolicies) > 0:
            return True
        return False

    def mUpdateAllPoliciesOfHostAsSynced(self, aHostName):

        _sql = """UPDATE selinuxpolicystore SET syncedtoecra='T' WHERE hostname=%(1)s"""
        _data = [aHostName]
        return self.mExecuteLog(_sql, _data)


    def mCreateProfilerTable(self):

        if not self.mCheckTableExist('profiler'):
            self.mExecute('''CREATE TABLE profiler (step TEXT,
                                                    details TEXT,
                                                    exec_type TEXT,
                                                    profiler_type TEXT,
                                                    start_time TEXT,
                                                    end_time TEXT,
                                                    elapsed TEXT,
                                                    operation_id TEXT,
                                                    workflow_id TEXT,
                                                    exaunit_id TEXT,
                                                    component TEXT,
                                                    cmdtype TEXT
                                                   )''')

    def mCreateRequestsTable(self):

        if not self.mCheckTableExist('requests'):
            self.mExecute('''CREATE TABLE requests (uuid VARCHAR(255) PRIMARY KEY,
                                                    status TEXT,
                                                    starttime TEXT,
                                                    endtime TEXT,
                                                    cmdtype TEXT,
                                                    params LONGTEXT,
                                                    error TEXT,
                                                    error_str TEXT,
                                                    body LONGTEXT,
                                                    xml LONGTEXT,
                                                    statusinfo TEXT,
                                                    clustername TEXT,
                                                    _lock TEXT,
                                                    data mediumtext,
                                                    subcmd TEXT,
                                                    response_sent TEXT,
                                                    aq_name TEXT)''')
    """
    Request fields:
        0. uuid
        1. status
        2. timestamp-start
        3. timestamp-stop
        4. cmdtype
        5. params
        6. error
        7. error_str
        8. body
        9. XML (Patched)
       10. statusinfo
       11. clustername
       12. lock
       13. data
       14. subcmd
       15. response_sent
       16. aq_name
    """

    def mCreateRequestsArchiveTable(self):

        if not self.mCheckTableExist('requests_archive'):
            self.mExecute('''CREATE TABLE requests_archive (uuid TEXT,
                                                            status TEXT,
                                                            starttime TEXT,
                                                            endtime TEXT,
                                                            cmdtype TEXT,
                                                            params LONGTEXT,
                                                            error TEXT,
                                                            error_str TEXT,
                                                            body LONGTEXT,
                                                            xml LONGTEXT,
                                                            statusinfo TEXT,
                                                            clustername TEXT,
                                                            _lock TEXT,
                                                            data mediumtext,
                                                            subcmd TEXT,
                                                            response_sent TEXT,
                                                            aq_name TEXT)''')
    """
    Request Archive fields:
        0. uuid
        1. status
        2. timestamp-start
        3. timestamp-stop
        4. cmdtype
        5. params
        6. error
        7. error_str
        8. body
        9. XML (Patched)
       10. statusinfo
       11. clustername
       12. lock
       13. data
       14. subcmd
       15. response_sent
       16. aq_name
    """

    def mInsertNewRequest(self, aRequest):

        _uuid   = aRequest.mGetUUID()
        _status = aRequest.mGetStatus()
        _time   = aRequest.mGetTimeStampStart()
        _end    = aRequest.mGetTimeStampEnd()
        _ctype  = aRequest.mGetCmdType()
        if self.mGetMaskParams():
            _params = maskSensitiveData(aRequest.mGetParams(), full_mask=True)
        _error  = aRequest.mGetError()
        _error_str = aRequest.mGetErrorStr()
        _body   = aRequest.mGetBody()
        _data   = aRequest.mGetData()
        _xml    = aRequest.mGetXml()
        _statusinfo = aRequest.mGetStatusInfo()
        _clustername = aRequest.mGetClusterName()
        _lock = aRequest.mGetLock()
        _sub_command = aRequest.mGetSubCommand()
        _response_sent = aRequest.mGetResponseSent()
        _aq_name = aRequest.mGetAqName()

        _sql = """INSERT IGNORE INTO requests
                  VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s,
                          %(7)s, %(8)s, %(9)s, %(10)s, %(11)s, %(12)s, %(13)s, %(14)s, %(15)s, %(16)s,
                          %(17)s)"""
        _data = [_uuid, _status, _time, _end, _ctype, _params, _error, _error_str, \
                 _body, _xml, _statusinfo, _clustername, _lock, _data, _sub_command, _response_sent, \
                 _aq_name]
        self.mExecuteLog(_sql, _data)

    @mUpdateResponseToEcra
    def mUpdateStatusRequestWithLock(self, aRequest):

        """
        We implemented a manual retry and put the requests inside a transaction.

        We use IMMEDIATE transactions.
        It locks all the writers to the db until a commit/rollback is executed.
        """

        _uuid   = aRequest.mGetUUID()
        _status = aRequest.mGetStatus()
        _statusinfo = aRequest.mGetStatusInfo()
        _retry = 3

        _sql = """UPDATE requests
                  SET status=%(1)s, statusinfo=%(2)s
                  WHERE uuid=%(3)s"""

        while _retry > 0:
            _success = True
            try:
                # Start transaction
                self.mGetConnection().begin()
                self.mSetTransaction(True)

                _data = [_status, _statusinfo, _uuid]
                self.mNativeExecute(_sql, _data)

                break

            except pymysql.err.OperationalError as e:
                ebLogError("mUpdateStatusRequestWithLock error %s for request id=%s" %(str(e),  _uuid))
                _retry-=1
                _success = False
            except Exception as ex:
                ebLogError("mUpdateStatusRequestWithLock error %s for request id=%s" %(str(ex),  _uuid))
                raise ex
            finally:
                if _success:
                    self.mCommit()
                else:
                    self.mRollback()
                    ebLogError("Rolling back mUpdateStatusRequestWithLock for request Id=%s" % _uuid)

    @mUpdateResponseToEcra
    def mUpdateStatusRequest(self, aRequest):

        _uuid   = aRequest.mGetUUID()
        _status = aRequest.mGetStatus()
        _statusinfo = aRequest.mGetStatusInfo()
        _sql = """UPDATE requests SET status=%(1)s, statusinfo=%(2)s WHERE uuid=%(3)s"""
        _data = [_status, _statusinfo, _uuid]
        self.mExecuteLog(_sql, _data)

    @mUpdateResponseToEcra
    def mUpdateParams(self, aRequest):
        _params = None
        _uuid   = aRequest.mGetUUID()
        if self.mGetMaskParams():
            _params = maskSensitiveData(aRequest.mGetParams(), full_mask=True)
        _params = _params
        _sql = """UPDATE requests SET params=%(1)s WHERE uuid=%(2)s"""
        _data = [_params, _uuid]
        self.mExecuteLog(_sql, _data)

    @mUpdateResponseToEcra
    def mUpdateRequest(self, aRequest, aInternal=False):

        _uuid   = aRequest.mGetUUID()
        _end    = aRequest.mGetTimeStampEnd()
        _status = aRequest.mGetStatus()
        _statusinfo = aRequest.mGetStatusInfo()
        _error  = aRequest.mGetError()
        _error_str = aRequest.mGetErrorStr()
        _xml    = aRequest.mGetXml()
        _body   = aRequest.mGetBody()
        _clustername = aRequest.mGetClusterName()
        _lock   = aRequest.mGetLock()
        _data   = aRequest.mGetData()
        _sub_command = aRequest.mGetSubCommand()
        
        _sql = """UPDATE requests
                  SET status=%(1)s, statusinfo=%(8)s, endtime=%(2)s, error=%(3)s,
                      error_str=%(4)s, body=%(5)s, xml=%(6)s, clustername=%(9)s,
                      _lock=%(10)s, data=%(11)s, subcmd=%(12)s WHERE uuid=%(7)s"""
        _data = [_status, _end, _error, _error_str, _body, _xml, _uuid, \
                 _statusinfo, _clustername, _lock, _data, _sub_command]
        self.mExecuteLog(_sql, _data)

    def mGetRequest(self, aUUID):
        #[WARNING]Don't change the field list arbitrarily. Adding new field here will cause regression with ECRA.
        _rc = None
        _sql = """SELECT uuid, status, starttime, endtime, cmdtype, params, error, error_str, body, xml, statusinfo, clustername, _lock, data FROM requests WHERE uuid=%(1)s"""
        _data = [aUUID]
        _rc = self.mFetchOne(_sql, _data)
        if _rc:
            _rc = self.mUnmaskReqParams(_rc)
        return _rc

    def mGetCompleteRequest(self, aUUID):
        #Update this field list whenever a new field is added to the requests table.
        _rc = None
        _sql = """SELECT uuid, status, starttime, endtime, cmdtype, params, error, error_str, body, xml, statusinfo, clustername, _lock, data, subcmd, response_sent, aq_name FROM requests WHERE uuid=%(1)s"""
        _data = [aUUID]
        _rc = self.mFetchOne(_sql, _data)
        if _rc:
            _rc = self.mUnmaskReqParams(_rc)
        return _rc

    def mGetActiveRequestsUUID(self, aCmd):
        _sql = """SELECT uuid FROM requests WHERE cmdtype=%(1)s AND status!='Done'"""
        _data = [aCmd]
        _list = self.mFetchAll(_sql, _data)
        return _list

    def mGetPendingRequest(self):
        _sql = """SELECT uuid FROM requests WHERE requests.uuid
                   NOT IN (
                     SELECT uuid FROM workers
                   ) AND status='Pending' ORDER BY starttime ASC"""

        return self.mFetchOne(_sql)

    def mCommandPassThrough(self, aCmd, aClustername=None):

        _uuid_status = ['Done']
        _pt = True
        _set1 = False
        _set2 = False

        if ebCluCmdCheckOptions(aCmd, ["concurrent_cmds_set1"]):
            _set1 = True
        elif ebCluCmdCheckOptions(aCmd, ["concurrent_cmds_set2"]):
            _set2 = True
        else:
            return False

        _list = self.mGetRegUuid(aClustername)
        for _l in _list:
            _uuid = _l[0].lstrip().rstrip()
            _rc = self.mGetUuidStatus(_uuid)
            if not _rc:
                ebLogWarn(f"mCommandPassThrough: uuid {_uuid} not present in requests table")
                #Such stale entries will get cleaned up at the end of the command execution.
                #Lets continue to check other entries.
                continue

            _cmdtype = _rc[0].lstrip().rstrip().replace("cluctrl.", "")
            _status = _rc[1].lstrip().rstrip()

            if _status not in _uuid_status:
                if _set1:
                    if not ebCluCmdCheckOptions(_cmdtype, ["concurrent_cmds_set2_db"]):
                        _pt = False
                        break
                elif _set2:
                    if not ebCluCmdCheckOptions(_cmdtype, ["concurrent_cmds_set1_db"]):
                        _pt = False
                        break

        if _pt == False:
            ebLogWarn('*** Critical operation currently going on !')
            ebLogWarn('*** %s : %s : %s' %(_uuid, _cmdtype, _status))
            return False

        return True


    def mGetRegUuid(self, aKey=None):

        if aKey:

            _sql = """SELECT uuid FROM registry WHERE _key=%(1)s"""
            _data = [aKey]
            _list = self.mFetchAll(_sql, _data)
            return _list

        else:

            _sql = """SELECT uuid FROM registry"""
            _data = [aKey]
            _list = self.mFetchAll(_sql, _data)
            return _list

    def mGetUuidStatus(self, aUUID):
        _rc = None
        _sql = """SELECT cmdtype, status FROM requests WHERE uuid=%(1)s"""
        _data = [aUUID]
        return self.mFetchOne(_sql, _data)

    def mBuildUIFilter(self, aDataList, aClustername=None, aCmdtype=None):
        _sql = "WHERE cmdtype NOT IN ('cluctrl.info', 'cluctrl.collect_log') "

        _sql += ebMysqlDB.mFormat(aDataList, "AND cmdtype NOT LIKE {0} ", 'monitor.%')
        _sql += ebMysqlDB.mFormat(aDataList, "AND clustername = {0} ", aClustername)

        if aCmdtype is not None:
            _sql += ebMysqlDB.mFormat(aDataList, "AND cmdtype LIKE {0} ", "%{0}%".format(aCmdtype))

        return _sql


    def mGetUIRowCount(self, aClustername=None, aCmdtype=None):
        _sql = "SELECT count(1) FROM requests "
        _data = []
        _sql += self.mBuildUIFilter(_data, aClustername, aCmdtype)

        return self.mFetchOne(_sql, _data)

    def mInsertProfiler(self, aProfilerInfo):

        _pi = aProfilerInfo
        _step = _pi.mGetStep()
        _details = _pi.mGetDetails()
        _exec_type = _pi.mGetExecType()
        _profiler_type = _pi.mGetProfilerType()
        _start_time = _pi.mGetStartTime()
        _end_time = _pi.mGetEndTime()
        _elapsed = _pi.mGetElapsed()
        _operation_id = _pi.mGetOperationId()
        _workflow_id = _pi.mGetWorkflowId()
        _exaunit_id = _pi.mGetExaunitId()
        _component = _pi.mGetComponent()
        _cmdtype = _pi.mGetCmdType()

        _data = [
            _step,
            _details,
            _exec_type,
            _profiler_type,
            _start_time,
            _end_time,
            _elapsed,
            _operation_id,
            _workflow_id,
            _exaunit_id,
            _component,
            _cmdtype,
        ]

        _dynamic_sql = []
        for i in range(0, len(_data)):
            _dynamic_sql.append(f"%({i+1})s")

        _sql = f"""INSERT INTO profiler VALUES ({",".join(_dynamic_sql)})"""
        self.mExecute(_sql, _data)


    def mGetProfilerData(self, aWorkflowId, aExaunitId):

        _sql = """SELECT * FROM profiler
                WHERE workflow_id = %(1)s
                AND exaunit_id = %(2)s
                ORDER BY start_time"""

        _data = [aWorkflowId, aExaunitId]

        return self.mFetchAllDict(_sql, _data)


    def mFilterRequests(self, aDict=None, aLimit=None, aOffset=None, aNotCondition=None, aOrderBy=None):
        """
        Extract filtered records from requests table.
        Args:
            aDict <dict>: key/value pair for extract records that satisfies specific condition.
            Use for WHERE clause. key is the column's name and value is the condition
            to search. using LIKE clause to match.

            aLimit <int>: specify the number of records to return. Starting from Zero.

            aOffset <int>: specify which row to start from retrieve the records.

            aNotCondition:  key/value pair for discriminate records based on a specific condition.
            Use for WHERE clause. key is the column's name and value is the condition (or a list of values)
            to search. using NOT LIKE clause to match.

            aOrderBy: key/value pair for records ordering.  key is the column's name and the value (ASC or DESC)

        Returns: <list> : list of ebJobRequest objects in a dict form
        """
        def mMigrateRequest(aSqlResult):
            _req = ebJobRequest(None, {})
            _req.mPopulate(aSqlResult)
            return _req.mToDict()

        _columns = ebJobRequest.mGetColumns()
        _query = "SELECT * FROM requests"

        _conditions = {"sql": []}

        if aDict is not None:
            for _key in aDict.keys():
                if _key in _columns:
                    _conditions['sql'].append("{0} LIKE %({0})s".format(_key))
                    _conditions[_key] = "%{0}%".format(aDict[_key])

        if aNotCondition is not None:
            for _key in aNotCondition.keys():
                if _key in _columns:
                    _negate_condition = aNotCondition[_key]
                    if isinstance(aNotCondition[_key], list):
                        for _number, _condition in enumerate(_negate_condition):
                            _place_holder = "{0}_{1}".format(_key,_number)
                            _conditions['sql'].append("{0} NOT LIKE %({1})s".format(_key,_place_holder))
                            _conditions[_place_holder] = "%{0}%".format(_condition)
                    else:
                        _conditions['sql'].append("{0} NOT LIKE %({0})s".format(_key))
                        _conditions[_key] = "%{0}%".format(aNotCondition[_key])

        if _conditions["sql"] != []:
            _query += " WHERE " + " AND ".join(_conditions.pop("sql"))

        if aOrderBy is not None:
            _order_list = []
            for _key in list(aOrderBy.keys()):
                if _key in _columns:
                    _order_value =  aOrderBy.get(_key).upper() if  aOrderBy.get(_key).upper() in ["ASC", "DESC"] else "ASC"
                    if _key in ["starttime","endtime"]:
                        _order_list.append("STR_TO_DATE({0},'%%a %%M %%d %%H:%%i:%%s %%Y') {1}" .format(_key, _order_value))
                    else:
                        _order_list.append("{0} {1}" .format(_key, _order_value))
            if _order_list:
                _query += " ORDER BY " + ", ".join(_order_list)

        if aOffset is not None:

            if aLimit is not None:
                _query += " LIMIT {0} ".format(aLimit)
                _query += " ,{0} ".format(aOffset)
            else:
                _query += " LIMIT 0, {0} ".format(aOffset)

        else:

            if aLimit is not None:
                _query += " LIMIT {0} ".format(aLimit)

        _objs = []
        if _conditions.keys() != []:
            _objs = self.mFetchAll(_query, _conditions)
        else:
            _objs = self.mFetchAll(_query)

        _objs = [self.mUnmaskReqParams(x) for x in _objs]
        _objs = [mMigrateRequest(x) for x in _objs]
        return _objs


    def mGetUIRequests(self, aCmdtype=None, aClustername=None, aLimit=None, aOffset=None):
        # Need to re-arrange starttime to make ORDER BY work
        # YYYY = substr(starttime, 21, 4)
        # MON  = substr(starttime, 5, 3)
        # DD = substr(CONCAT('00', cast(substr(endtime, 9, 2) as signed)), -2, 2)
        # The '00' fixes the convertion, ensuring a leading 0 on months with one digit
        # HH = substr(starttime, 12, 2)
        # MI = substr(starttime, 15, 2)
        # SS = substr(starttime, 18, 2)
        _order_criteria = """
        cast(CONCAT(substr(starttime, 21, 4),
            case substr(starttime, 5, 3)
                when 'Jan' then '01'
                when 'Feb' then '02'
                when 'Mar' then '03'
                when 'Apr' then '04'
                when 'May' then '05'
                when 'Jun' then '06'
                when 'Jul' then '07'
                when 'Aug' then '08'
                when 'Sep' then '09'
                when 'Oct' then '10'
                when 'Nov' then '11'
                when 'Dec' then '12'
            end,
            substr(CONCAT('00', cast(substr(starttime, 9, 2) as signed)), -2, 2),
            substr(starttime, 12, 2),
            substr(starttime, 15, 2),
            substr(starttime, 18, 2))
        as signed) as ordertime
        """

        _data = []
        _query = """
        SELECT uuid, status, starttime,
            endtime, cmdtype, params,
            error, error_str, '',
            xml, statusinfo, clustername,
            _lock, data, ordertime
        FROM (
            SELECT uuid, status, starttime,
                endtime, cmdtype, params,
                error, error_str, '',
                xml, statusinfo, clustername,
                _lock, data, {0}
            FROM requests
            UNION ALL
            SELECT uuid, status, starttime,
                endtime, cmdtype, params,
                error, error_str, '',
                xml, statusinfo, clustername,
                _lock, data, {0}
            FROM requests_archive
        ) results
        """.format(_order_criteria)
        _query += self.mBuildUIFilter(_data, aClustername, aCmdtype)

        _query += "ORDER BY ordertime DESC "
        _query += ebMysqlDB.mFormat(_data, "LIMIT {0} ", aLimit)
        _query += ebMysqlDB.mFormat(_data, ",{0} ", aOffset)

        ebLogDebug("DBStore3.mGetUIRequests query = {} , data = {}".format(_query, _data))
        _body = '('
        for row in self.mFetchAll(_query, _data):
            row = self.mUnmaskReqParams(row)
            _body = _body + str(row)+','
        _body = _body + ')'
        return _body

    def mOrphanRequests(self):
        query = """SELECT  uuid , status , starttime , endtime , cmdtype, params,
                           error, error_str , '', xml, statusinfo, clustername, _lock, data
                   FROM requests where requests.uuid
                   NOT IN (
                     SELECT uuid FROM workers
                   ) AND status='Pending' ORDER BY endtime"""
        rows = self.mFetchAll(query)
        return map(self.mUnmaskReqParams, rows)

    def mDumpRequests(self, aUUID=None, aComplete=False):
        #Don't change the field list arbitraily. Chaging the list will cause regression with ECRA.

        _data = []
        _body = '('
        if not aUUID:
            if aComplete:
                _query = "SELECT uuid, status, starttime, endtime, cmdtype, params, error, error_str, body, xml, statusinfo, clustername, _lock, data FROM requests ORDER BY endtime"
            else:
                _query = """SELECT  uuid, status, starttime, endtime,
                                    cmdtype, params, error, error_str, '', xml,
                                    statusinfo, clustername, _lock, data
                            FROM requests ORDER BY endtime"""
        else:
            _query = """SELECT uuid, status, starttime, endtime, cmdtype, params, error, error_str, body, xml, statusinfo, clustername, _lock, data FROM requests WHERE uuid=%(1)s"""
            _data.append(aUUID)

        for row in self.mFetchAll(_query, _data):
            row = self.mUnmaskReqParams(row)
            _body = _body + str(row)+','
        _body = _body + ')'
        return _body

    def mUnmaskReqParams(self, row):
        _params_i = 5
        try:
            if "Erased" in row[_params_i]:
                _params = row[_params_i]
            else:
                _params = umaskSensitiveData(row[_params_i], full_mask=True)
        except:
            _params = ast.literal_eval(row[_params_i])
            _params = umaskSensitiveData(_params, full_mask=False)
        row = list(row)
        row[_params_i] = str(_params)
        return tuple(row)

    # Query with dynamic filters support and data FROM trigger
    def mBackupRequests(self, isoDateStr, ebDbFilters):
        _sql = """
            INSERT INTO requests_archive
            SELECT *
            FROM requests
            WHERE endtime != "Undef" AND
                (cast(CONCAT(substr(endtime, 21, 4),
                    case substr(endtime, 5, 3)
                        when 'Jan' then '01'
                        when 'Feb' then '02'
                        when 'Mar' then '03'
                        when 'Apr' then '04'
                        when 'May' then '05'
                        when 'Jun' then '06'
                        when 'Jul' then '07'
                        when 'Aug' then '08'
                        when 'Sep' then '09'
                        when 'Oct' then '10'
                        when 'Nov' then '11'
                        when 'Dec' then '12'
                    end,
                    substr(CONCAT('00', cast(substr(endtime, 9, 2) as signed)), -2, 2),
                    substr(endtime, 12, 2),
                    substr(endtime, 15, 2),
                    substr(endtime, 18, 2))
                as signed) <= cast(:1 as signed))"""
        _bind = [isoDateStr]        #only bind variable
        for _filter in ebDbFilters: #see dbpolicies/Base.py
            _sql, _bind = _filter.mAppendFilterToQuery(_sql, _bind)
        self.mExecute(_sql, _bind)
        self.mExecute("""
            DELETE FROM requests
            WHERE Status='Done' AND endtime != "Undef" AND
                cast(CONCAT(substr(endtime, 21, 4),
                    case substr(endtime, 5, 3)
                        when 'Jan' then '01'
                        when 'Feb' then '02'
                        when 'Mar' then '03'
                        when 'Apr' then '04'
                        when 'May' then '05'
                        when 'Jun' then '06'
                        when 'Jul' then '07'
                        when 'Aug' then '08'
                        when 'Sep' then '09'
                        when 'Oct' then '10'
                        when 'Nov' then '11'
                        when 'Dec' then '12'
                    end,
                    substr(CONCAT('00', cast(substr(endtime, 9, 2) as signed)), -2, 2),
                    substr(endtime, 12, 2),
                    substr(endtime, 15, 2),
                    substr(endtime, 18, 2))
                as signed) <= cast(%(1)s as signed)
        """, [isoDateStr])

    # Query with dynamic filters support and data FROM trigger
    def mPruneRequests(self, isoDateStr, ebDbFilters):
        _sql = """ DELETE FROM requests
            WHERE endtime != "Undef" AND (
                cast(CONCAT(substr(endtime, 21, 4),
                    case substr(endtime, 5, 3)
                        when 'Jan' then '01'
                        when 'Feb' then '02'
                        when 'Mar' then '03'
                        when 'Apr' then '04'
                        when 'May' then '05'
                        when 'Jun' then '06'
                        when 'Jul' then '07'
                        when 'Aug' then '08'
                        when 'Sep' then '09'
                        when 'Oct' then '10'
                        when 'Nov' then '11'
                        when 'Dec' then '12'
                    end,
                    substr(CONCAT('00', cast(substr(endtime, 9, 2) as signed)), -2, 2),
                    substr(endtime, 12, 2),
                    substr(endtime, 15, 2),
                    substr(endtime, 18, 2))
                as signed) <= cast(:1 as signed))
        """
        _bind = [isoDateStr]        #only bind variable
        for _filter in ebDbFilters: #see dbpolicies/Base.py
            _sql, _bind = _filter.mAppendFilterToQuery(_sql, _bind)
        self.mExecute(_sql, _bind)

    def mClearRegistry(self):
        self.mExecute("""DELETE FROM registry""")

    def mClearWorkers(self, aUUID=None):
        _uuid = aUUID
        _data = []
        if _uuid:
            _stmt = "DELETE FROM workers where uuid=%(1)s"
            _data = [_uuid]
        else:
            _stmt = "DELETE FROM workers"

        self.mExecute(_stmt, _data)

    def mGetIdleWorkers(self):
        _body = '('

        _list = self.mFetchAll("""SELECT * FROM workers where type='worker' and status='Idle' and state='NORMAL' and uuid='00000000-0000-0000-0000-000000000000' ORDER BY endtime""")

        for row in _list:
            _body = _body + str(row)+','
        _body = _body + ')'

        return _body
    
    def mDumpWorkers(self, aUUID=None):

        _body = '('

        if not aUUID:
            _list = self.mFetchAll("""SELECT * FROM workers ORDER BY endtime""")
        else:
            _list = self.mFetchAll("""SELECT * FROM workers WHERE uuid=%(1)s""", [aUUID])

        for row in _list:
            _body = _body + str(row)+','
        _body = _body + ')'

        return _body

    def mDumpActiveWorkers(self, aUUID=None):

        _body = '('

        if not aUUID:
            _list = self.mFetchAll("""SELECT * FROM workers
                                     WHERE status<>'Idle' AND type='worker' ORDER BY endtime""")
        else:
            _list = self.mFetchAll("""SELECT * FROM workers
                                     WHERE status<>'Idle' AND type='worker' AND uuid=%(1)s""", [aUUID])

        for row in _list:
            _body = _body + str(row)+','
        _body = _body + ')'

        return _body

    def mGetNumberOfIdleWorkers(self):

        _rc = self.mFetchOne("select count(*) from workers where type='worker' and status='Idle' and state='NORMAL'")
        _idle_worker_count = 0
        if _rc:
            _idle_worker_count = int(_rc[0])
        return _idle_worker_count

    def mGetRegCount(self):
        
        _rc = self.mFetchOne("SELECT count(*) FROM registry where uuid != 'Undefined'")
        _count = int(_rc[0])
        return _count

    def mCheckRegEntry(self, aKey):

        _inkey = aKey
        _list = self.mFetchAll("""SELECT * FROM registry WHERE LOCATE(_key, %(1)s) > 0  OR LOCATE(%(2)s, _key) > 0 """, [_inkey, _inkey])
        for _ in _list:
            return True
        return False

    def mCleanRegistryTableByWorker(self, aWorkerId):

        _sql = """DELETE FROM registry WHERE worker=%(1)s"""
        self.mExecute(_sql, [str(aWorkerId)])

    def mGetRegEntryByKey(self, aKey):

        _inkey = aKey
        _rc = self.mFetchOne("""SELECT * FROM registry WHERE LOCATE(_key, %(1)s) > 0  OR LOCATE(%(2)s, _key) > 0 """, [_inkey, _inkey])
        return _rc

    def mGetRegEntry(self, aUUID):

        _uuid = aUUID
        _rc = self.mFetchOne("""SELECT * FROM registry WHERE uuid=%(1)s""", [_uuid])
        return _rc

    def mSetRegEntry(self, aKey, aValue='Undefined', aUUID='Undefined', aWorker='Undefined'):

        _key    = aKey
        _value  = aValue
        _uuid   = aUUID
        _worker = aWorker
        _sql = """INSERT INTO registry VALUES (%(1)s, %(2)s, %(3)s, %(4)s )"""
        _data = [_key,_value, _uuid, _worker]
        self.mExecute(_sql, _data)

    def mDelRegByUUID(self, uuid):

        _sql = """DELETE FROM registry WHERE uuid=%(1)s"""
        _data = [uuid]
        self.mExecute(_sql, _data)

    def mDelRegEntry(self, aKey):

        _key = aKey
        _sql = """DELETE FROM registry WHERE _key=%(1)s"""
        _data = [_key]
        self.mExecute(_sql, _data)

    def mCreateIBFabricLocksTable(self):
        """
        Request fields:
            0. id                       -> unique db id
            1. ibswitches_output_sha512 -> sha512 sum of the sorted ibswitches in an IB fabric
            2. list_clusters_in_process -> List of busy clusters:
                                           'clu_id1:req_uuid clu_id2:req_uuid2'
            3. lockedfor                -> Indicates whether the lock holder is processing
                                           IBswitches or not:
                                           'none|ibswitch|non_ibswitch'
            4 lockcount                 -> Number of clusters doing some patch in the fabric
         """
        if not self.mCheckTableExist('ibfabriclocks'):
            self.mExecute('''CREATE TABLE ibfabriclocks (
                      id                        INTEGER PRIMARY KEY AUTO_INCREMENT,
                      ibswitches_output_sha512  VARCHAR(255) UNIQUE,
                      do_switch                 TEXT,
                      list_clusters_in_process  TEXT,
                      lockedfor                 TEXT,
                      lockcount                 INTEGER
                      )''')

    def mSetIBFabricEntry(self, aSha512):

        if len(aSha512) == 128 and re.match("[0-9a-f]{128}", aSha512):
            _sql = """INSERT INTO ibfabriclocks (ibswitches_output_sha512,
                                                 do_switch,
                                                 list_clusters_in_process,
                                                 lockedfor,
                                                 lockcount)
                      VALUES (%(1)s, 'no' ,'','none', 0)"""
            _data = [aSha512]
            try:
                self.mExecute(_sql, _data)
            except pymysql.err.IntegrityError as err:
                ebLogWarn("IBFabric with ibswitches_output_sha512 '%s' already exists. " % aSha512)

        else:
            raise Exception("Invalid sha512 sum: '%d'" % aSha512)

    def mCheckIBFabricEntry(self, aFabricID=None, aSha512=None):

        if aFabricID:
            _sql = "SELECT * FROM ibfabriclocks WHERE id=%(1)s"
            _data = [aFabricID]
        elif aSha512:
            _sql = "SELECT * FROM ibfabriclocks WHERE ibswitches_output_sha512=%(1)s"
            _data = [aSha512]
        else:
            raise Exception("mCheckIBFabricEntry: No input value specified.")

        _list = self.mFetchAll(_sql, _data)
        for _row in _list:
            return _row

        return None

    def mUpdateIBFabricEntry(self, aFabricObj):

        _id = aFabricObj.mGetIBFabricID()
        _sha512 = aFabricObj.mGetSha512()
        _do_switch = aFabricObj.mGetDoSwitch()
        _clusters = aFabricObj.mGetBusyClustersList()
        _lockedfor = aFabricObj.mGetLockedFor()
        _fabriclock = aFabricObj.mGetFabricLock()

        _sql = """UPDATE ibfabriclocks
                  SET ibswitches_output_sha512=%(1)s, do_switch=%(2)s,
                      list_clusters_in_process=%(3)s, lockedfor=%(4)s, lockcount=%(5)s
                  WHERE id=%(6)s"""
        _data = [_sha512, _do_switch, _clusters, _lockedfor, _fabriclock, _id]
        self.mExecute(_sql, _data)

    def mSetDoSwitchIBFabic(self, aFabricID, aDoSwitch):

        if not aFabricID:
            raise Exception('mSetDoSwitchIBFabic: Invalid fabric_id input provided.')

        if not aDoSwitch or aDoSwitch not in ['no', 'yes']:
            raise Exception('mSetDoSwitchIBFabic: Invalid do_switch input provided.')

        _ret = True
        _sql = "UPDATE ibfabriclocks SET do_switch=%(1)s WHERE id=%(2)s"
        _data = [aDoSwitch, aFabricID]

        try:
            self.mExecute(_sql, _data)
        except Exception as ex:
            ebLogError("mSetDoSwitchIBFabic update do_switch error. Fabric_id=%d" % aFabricID)
            _ret = False
            raise ex

        return _ret

    def mManageIBFabricLock(self, aFabricID, aClusterID, aLock, aLockedFor=None):
        """
        Lock a cluster in a fabric requires two steps:
          1) Get the cluster_ids list FROM db
          2) Update the db with our new list: original_list+new_cluster_id

        In order to ensure db doesn't change during these two steps,
        we must put them inside a transaction.

        We use IMMEDIATE transactions.
        It locks all the writers to the db until a commit/rollback is executed

        By default, when the connector finds out the db is locked, it waits for five
        seconds before return an error. I added a manual retry.
        """

        if aLock:
            _sql = """UPDATE ibfabriclocks
                      SET list_clusters_in_process=%(1)s, lockedfor=%(2)s,
                          lockcount=lockcount+1
                      WHERE id=%(3)s"""
        else:
            _sql = """UPDATE ibfabriclocks
                      SET list_clusters_in_process=%(1)s, lockedfor=%(2)s,
                          lockcount=lockcount-1
                      WHERE id=%(3)s"""

        _clusters = ''
        _lockedfor = ''
        _ret = None
        _retry = 3

        while _retry > 0:
            _flag = True
            _ret = True
            try:
                # Get ibfabric data
                _row = self.mCheckIBFabricEntry(aFabricID=aFabricID)
                if not _row:
                    _ret = False
                else:

                    # Start transaction
                    self.mGetConnection().begin()
                    self.mSetTransaction(True)

                    # Look for specified cluster_id
                    _found = False
                    _clusters = str(_row[3]).strip().split()
                    # Find cluster_id
                    for _index, _clu in enumerate(_clusters):
                        if _clu and int(_clu) == int(aClusterID):
                            _found = True
                            break

                    if aLock is True:       # Lock operation

                        # if cluster_id is in lock list or an ibswitch operation is being run
                        # in the fabric, then set to False
                        if _found or str(_row[4]).lower() == 'ibswitch':
                            _ret = False
                        else:
                            # if we want to exec an ibswitch operation,
                            #then check no patch is running in any cluster
                            if aLockedFor and aLockedFor == 'ibswitch':
                                if str(_row[4]).lower() != 'none' or int(_row[5]) != 0:
                                    _ret = False

                        if _ret:
                            # Update data
                            _clusters.append(str(aClusterID))
                            _data = [" ".join(_clusters), aLockedFor, aFabricID]
                            self.mNativeExecute(_sql, _data)

                    else:                   # Unlock operation

                        # if cluster_id not found then set to False
                        if not _found:
                            _ret = False
                        else:
                            # Delete cluster id FROM list
                            _clusters.pop(_index)
                            # Change lockedfor to 'none' if no cluster is using it
                            _lockedfor = _row[4].strip()
                            if len(_clusters) == 0:
                                _lockedfor = 'none'
                            # Update data
                            _data = [" ".join(_clusters), _lockedfor, aFabricID]
                            self.mNativeExecute(_sql, _data)

                break

            except pymysql.err.OperationalError:
                _retry-=1
                _flag = False
            except Exception as ex:
                ebLogError("mManageIBFabricLock error fabrid_id=%d" % aFabricID)
                _ret = False
                raise ex
            finally:
                if _flag:
                    if _ret:
                        self.mCommit()
                    else:
                        self.mRollback()

        return _ret

    def mCreateIBFabricClusterTable(self):
        """
        request fields:
            0. id
            1. fabric_id
            2. clustername
        """
        if not self.mCheckTableExist('ibfabricclusters'):
            self.mExecute('''CREATE TABLE ibfabricclusters (
                      id            INTEGER PRIMARY KEY AUTO_INCREMENT,
                      fabric_id     INTEGER,
                      clustername   VARCHAR(760) UNIQUE,
                      FOREIGN KEY (fabric_id) REFERENCES ibfabriclocks(id)
                      )''')

    def mCleanupSwitchFabricTables(self):

        for _table_name in [ 'clusterpatchoperations', 'ibfabricclusters', 'ibfabricibswitches', 'ibfabriclocks' ]:
            if self.mCheckTableExist(_table_name):
                # Cleanup all entries from table
                _sql = """delete from %s""" % _table_name
                self.mExecute(_sql)

    def mCheckIBFabricClusterTable(self, aClusterID=None, aClusterName=None):

        if aClusterID:
            _sql = "SELECT * FROM ibfabricclusters WHERE id=%(1)s"
            _data = [aClusterID]
        elif aClusterName:
            _sql = "SELECT * FROM ibfabricclusters WHERE clustername=%(1)s"
            _data = [aClusterName]
        else:
            raise Exception("Check ibfabricclusters entry failed. No input value specified.")

        _list = self.mFetchAll(_sql, _data)
        for _row in _list:
            return _row

        return None

    def mSetIBFabricClusterEntry(self, aClusterObj):

        _fabricID = aClusterObj.mGetIBFabricID()
        _clustername = aClusterObj.mGetClusterName()

        if not _clustername:
            raise Exception("mSetIBFabricClusterEntry: Invalid clustername provided.")
        if not _fabricID:
            raise Exception("mSetIBFabricClusterEntry: Invalid fabric_id provided.")

        _sql = "INSERT INTO ibfabricclusters (fabric_id, clustername) VALUES (%(1)s, %(2)s)"
        _data = [_fabricID, _clustername]

        try:
            self.mExecute(_sql, _data)
        except pymysql.err.IntegrityError:
            ebLogWarn("Cluster '%s' already exists. " % _clustername)

    def mCreateIBFabricIBSwitchesTable(self):
        """
        request fields:
            0. id
            1. fabric_id
            2. ibswitchname
        """

        if not self.mCheckTableExist('ibfabricibswitches'):
            self.mExecute('''CREATE TABLE ibfabricibswitches (
                      id            INTEGER PRIMARY KEY AUTO_INCREMENT,
                      fabric_id     INTEGER,
                      ibswitchname  VARCHAR(255) UNIQUE,
                      FOREIGN KEY (fabric_id) REFERENCES ibfabriclocks(id)
                      )''')

    def mCheckIBFabricIBSwitchesTable(self, aIBSwitchList):

        _list = []
        if type(aIBSwitchList) == str:
            _list = [aIBSwitchList]

        if type(aIBSwitchList) == list:
            _list = aIBSwitchList
            _list = list(map(lambda x: "{0}%".format(x), _list))

            _sql = "SELECT * FROM ibfabricibswitches WHERE "
            _swList = list(map(lambda x: "ibswitchname LIKE %({0})s".format(x), \
                                      range(1, len(_list)+1)))
            _sql += " OR ".join(_swList)
            _list = self.mFetchAll(_sql, _list)

        else:
            raise Exception("mCheckIBFabricIBSwitchesTable: Invalid ib_switch_list input provided.")

        for _row in _list:
            return _row

        return None

    def mGetListOfIBFabricIBSwitches(self, aFabricID):

        if not aFabricID:
            raise Exception("mGetListOfIBFabricIBSwitches: Invalid fabric_id input provided.")

        _sql = "SELECT * FROM ibfabricibswitches WHERE fabric_id=%(1)s"
        _data = [aFabricID]
        return self.mFetchAll(_sql, _data)

    def mSetIBFabricIBSwitchesEntry(self, aFabricID, aIBSwitchName):

        if not aFabricID:
            raise Exception('mSetIBFabricIBSwitchesEntry: Invalid fabric_id input provided.')
        if not aIBSwitchName:
            raise Exception("mSetIBFabricIBSwitchesEntry: Invalid ib_switch_name input provided.")

        _sql = "INSERT INTO ibfabricibswitches (fabric_id, ibswitchname) VALUES (%(1)s,%(2)s)"
        _data = [aFabricID, aIBSwitchName]

        try:
            self.mExecute(_sql, _data)
        except pymysql.err.IntegrityError:
            ebLogWarn("IBSwitch '%s' already exists.' " % str(aIBSwitchName))

    def mCreatePatchListTable(self):
        """
        request fields:
            0. master_uuid  -> master patch request that handles orchestration
            1. child_uuid   -> individual patch request uuid
            2. reqstatus    -> status we send to ecra
            3. json_report  -> json error report we send to ecra
        """

        if not self.mCheckTableExist('patchlist'):
            self.mExecute('''CREATE TABLE patchlist (
                      master_uuid   VARCHAR(255),
                      child_uuid    VARCHAR(255),
                      reqstatus     TEXT,
                      json_report   TEXT,
                      PRIMARY KEY (master_uuid, child_uuid)
                      )''')

    def mGetChildRequestsList(self, aMasterUUID):

        if not aMasterUUID:
            raise Exception('mGetChildRequestsList: Invalid master_uuid input provided.')

        _sql = "SELECT child_uuid, reqstatus, json_report FROM patchlist WHERE master_uuid=%(1)s"
        _data = [aMasterUUID]
        return self.mFetchAll(_sql, _data)

    def mGetPatchChildRequest(self, aChildUUID):

        if not aChildUUID:
            raise Exception('mGetPatchChildRequest: Invalid child_uuid input provided.')

        _sql = "SELECT reqstatus, json_report, master_uuid FROM patchlist WHERE child_uuid=%(1)s"
        _data = [aChildUUID]
        return self.mFetchOne(_sql, _data)

    def mGetChildRequestError(self, aChildUUID):

        if not aChildUUID:
            raise Exception('mGetChildRequestError: Invalid child_uuid input provided.')

        _sql = "SELECT error, error_str FROM requests WHERE uuid=%(1)s"
        _data = [aChildUUID]
        result = self.mFetchOne(_sql, _data)
        return self.mFetchOne(_sql, _data)

    def mInsertChildRequestToPatchList(self, aMasterUUID, aChildUUID, aStatus):

        if aMasterUUID and aChildUUID and aStatus:
            _sql = """INSERT INTO patchlist (master_uuid, child_uuid, reqstatus)
                      VALUES (%(1)s, %(2)s, %(3)s)"""
            _data = [aMasterUUID, aChildUUID, aStatus]
            try:
                self.mExecute(_sql, _data)
            except pymysql.err.IntegrityError:
                ebLogWarn("Child requests '%s' already exists.' " % str(aChildUUID))
        else:
            raise Exception('mInsertChildRequestToPatchList: Invalid input provided.')

    @mUpdateResponseToEcra
    def mUpdateChildRequestError(self, aUUID, aError, aErrorStr=None):
        if aErrorStr:
            _sql = """UPDATE requests SET error=%(1)s, error_str=%(2)s WHERE uuid=%(3)s"""
            _data = [aError, aErrorStr, aUUID]
        else:
            _sql = """UPDATE requests SET error=%(1)s WHERE uuid=%(2)s"""
            _data = [aError, aUUID]
        self.mExecuteLog(_sql, _data)

    def mUpdateChildRequestStatus(self, aMasterUUID, aChildUUID, aStatus):

        if aMasterUUID and aChildUUID and aStatus:
            _sql = """UPDATE patchlist SET reqstatus=%(1)s
                      WHERE master_uuid=%(2)s AND child_uuid=%(3)s"""
            _data = [aStatus, aMasterUUID, aChildUUID]
            self.mExecute(_sql, _data)
        else:
            raise Exception('mUpdateChildRequestStatus: Invalid input provided.')

    def mUpdateJsonPatchReport(self, aChildUUID, aData):

        if aChildUUID and aData:
            _sql = """UPDATE patchlist SET json_report=%(2)s
                      WHERE child_uuid=%(1)s"""
            _data = [aChildUUID, aData]
            self.mExecute(_sql, _data)
        else:
            raise Exception('mUpdateJsonPatchReport: Invalid input provided')

    def mCreateClusterPatchOperationsTable(self):
        """
        request fields:
            0. id
            1. cluster name/key
            2. master request id
            3. target type
            4. patch type
            5. opearation type
            6. operation style
        """
        if not self.mCheckTableExist('clusterpatchoperations'):
            self.mExecute('''CREATE TABLE clusterpatchoperations (
                      id               INTEGER PRIMARY KEY AUTO_INCREMENT,
                      clustername      VARCHAR(760),
                      master_req_uuid  VARCHAR(255) UNIQUE,
                      target_type      VARCHAR(100),
                      patch_type       VARCHAR(100),
                      operation_type   VARCHAR(100),
                      operation_style  VARCHAR(100),
                      FOREIGN KEY (clustername) REFERENCES ibfabricclusters(clustername)
                      )''')

    def mCheckClusterPatchOperationsTable(self, aClusterName=None):
        if aClusterName:
            _sql = "SELECT * FROM clusterpatchoperations WHERE clustername=%(1)s"
            _data = [aClusterName]
        else:
            raise Exception("Check clusterpatchoperations entry failed. No cluster input value specified.")

        _list = self.mFetchAll(_sql, _data)

        return _list

    def mSetClusterPatchOperationsEntry(self, aClusterName, aMasterReqID, aTargetType,
                                        aPatchType, aOperationType, aOperationStyle):
        if not aClusterName:
            raise Exception("mSetClusterPatchOperationsEntry: Invalid clustername provided.")

        if not aMasterReqID:
            raise Exception("mSetClusterPatchOperationsEntry: Invalid Master request id provided.")

        if not aTargetType:
            raise Exception("mSetClusterPatchOperationsEntry: Invalid Target type provided.")

        if not aPatchType:
            raise Exception("mSetClusterPatchOperationsEntry: Invalid Patch type provided.")

        if not aOperationType:
            raise Exception("mSetClusterPatchOperationsEntry: Invalid Operation type provided.")

        if not aOperationStyle:
            raise Exception("mSetClusterPatchOperationsEntry: Invalid Operation style provided.")

        _sql = "INSERT INTO clusterpatchoperations (clustername, master_req_uuid, target_type, patch_type, operation_type, operation_style) VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s)"
        _data = [aClusterName, aMasterReqID, aTargetType, aPatchType, aOperationType, aOperationStyle]

        try:
            self.mExecute(_sql, _data)
        except pymysql.err.IntegrityError:
            ebLogWarn(" Cluster operations entry for '%s' already exists. " % aClusterName)

    def mDeleteClusterPatchOperationsEntry(self, aClusterName, aTargetType=None):

        if not aClusterName:
            raise Exception("mDeleteClusterPatchOperationsEntry: Invalid Cluster Key provided.")

        if not aTargetType:
            raise Exception("mDeleteClusterPatchOperationsEntry: Invalid Target type is provided.")

        _sql = """DELETE from clusterpatchoperations WHERE clustername=%(1)s AND target_type=%(2)s"""
        _data = [aClusterName, aTargetType]
        self.mExecute(_sql, _data)

    def mDeleteClusterPatchOperationsEntryByUuid(self, aMasterUUID):

        if not aMasterUUID:
            raise Exception("mDeleteClusterPatchOperationsEntryByUuid: Invalid Master Request UUID.")

        _sql = """DELETE from clusterpatchoperations WHERE master_req_uuid=%(1)s"""
        _data = [aMasterUUID]
        self.mExecute(_sql, _data)

    def mGetClusterPatchOperationsCount(self, aClusterName, aTargetType, aPatchType, aTaskTypes):
        _taskTypes = ', '.join("'{" + str(i) + "}'" for i in range(len(aTaskTypes)))
        # Sample Command:
        #   SELECT count(1) FROM clusterpatchoperations WHERE where operation_type in ('patch_prereq_check', 'patch', 'postcheck') and
        #   clustername='slcs27' and target_type = 'dom0' and patch_type = 'monthly'
        _sql = "SELECT count(1) FROM clusterpatchoperations WHERE operation_type IN (%s)" % _taskTypes
        _sql = _sql.format(*aTaskTypes)
        _sql += " AND clustername = %(1)s AND target_type = %(2)s AND patch_type =  %(3)s"""
        _data = [aClusterName, aTargetType, aPatchType]

        return self.mFetchOne(_sql, _data)

    def mCreateInfraPatchingTimeStatsTable(self):
        """
        request fields:
            0. master_uuid     -> master patch request that handles orchestration
            1. child_uuid      -> individual patch request uuid
            2. target_type     -> Target type i.e dom0, domu,cell,ibswitch etc.
            3. node_names      -> Nodes where time stat details are fetched for the specific stage and substage combination
            3. operation       -> patching operation i.e patch_prereq_check/patch/rollback etc.
            4. rack_name       -> rackname
            5. patch_type      -> whether patch type is  monthly(exasplice) or quarterly
            6. operation_style -> rolling or non-rolling
            7. stage           -> name of the patching stage i.e. PRE_PATCH, PATCH_MGR and POST_PATCH
            8. sub_stage       -> name of the substage with in a stage(step)
            9. start_time      -> start time for the substage
            10. end_time       -> end time for the substage
            11. duration_in_seconds -> time spent in the entire substage within a stage
        """
        if not self.mCheckTableExist('infrapatchingtimestats'):
            self.mExecute('''CREATE TABLE infrapatchingtimestats (
        master_uuid     VARCHAR(128),
        child_uuid      VARCHAR(128),
        target_type     VARCHAR(128),
        node_names      TEXT,
        operation       VARCHAR(128),
        rack_name       VARCHAR(255),
        patch_type      VARCHAR(128),
        operation_style VARCHAR(128),
        stage           VARCHAR(128),  
        sub_stage       VARCHAR(128), 
        start_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time        TIMESTAMP,
        duration_in_seconds  int,    
      PRIMARY KEY (master_uuid, child_uuid, stage, start_time)
)''')

    def mCreateInfrapatchingTimeStatsEntry(self, aPatchingTimeStatsRecord):
        _master_uuid = aPatchingTimeStatsRecord.mGetMasterRequestUUID()
        _child_uuid = aPatchingTimeStatsRecord.mGetChildRequestUUID()
        _target_type = aPatchingTimeStatsRecord.mGetTargetType()
        _node_names = aPatchingTimeStatsRecord.mGetNodeNames()
        _operation = aPatchingTimeStatsRecord.mGetOperation()
        _rack_name = aPatchingTimeStatsRecord.mGetRackName()
        _patch_type = aPatchingTimeStatsRecord.mGetPatchType()
        _operation_style = aPatchingTimeStatsRecord.mGetOperationStyle()
        _stage = aPatchingTimeStatsRecord.mGetPatchingStage()
        _sub_stage = aPatchingTimeStatsRecord.mGetPatchingSubStage()

        _sql = """INSERT INTO infrapatchingtimestats VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s, %(7)s, %(8)s, %(9)s, %(10)s, CURRENT_TIMESTAMP(), NULL, 0)"""
        _data = [_master_uuid, _child_uuid, _target_type, _node_names, _operation, _rack_name, _patch_type, _operation_style, _stage, _sub_stage]
        self.mExecute(_sql, _data)

    def mUpdateInfrapatchingTimeStatEntry(self, aChildUUID, aStage, aSubStage, aNodes):
        _sql = ''
        _data = []
        # With current implementation PRE_PATCH has single entry and PATCH_MGR can have multiple entries in dom0[u] rolling
        # patch scenarios. So in case PATCH_MGR update scenarios, node_name is passed to update the end_time
        if aNodes:
            _sql = """UPDATE infrapatchingtimestats SET end_time=CURRENT_TIMESTAMP, duration_in_seconds=TIME_TO_SEC(TIMEDIFF(CURRENT_TIMESTAMP, start_time)) WHERE child_uuid=%(1)s AND stage=%(2)s AND sub_stage=%(3)s AND node_names=%(4)s AND end_time IS NULL"""
            _data = [aChildUUID, aStage, aSubStage, aNodes]
        else:
            _sql = """UPDATE infrapatchingtimestats SET end_time=CURRENT_TIMESTAMP, duration_in_seconds=TIME_TO_SEC(TIMEDIFF(CURRENT_TIMESTAMP, start_time)) WHERE child_uuid=%(1)s AND stage=%(2)s AND sub_stage=%(3)s AND end_time IS NULL"""
            _data = [aChildUUID, aStage, aSubStage]
        self.mExecute(_sql, _data)

    def mUpdateInfrapatchingTimeStatsForUnfilledStages(self, aChildUUID):
        _sql = """UPDATE infrapatchingtimestats SET end_time=CURRENT_TIMESTAMP, duration_in_seconds=TIME_TO_SEC(TIMEDIFF(
        CURRENT_TIMESTAMP, start_time)) WHERE child_uuid=%(1)s AND end_time IS NULL """
        _data = [aChildUUID]
        self.mExecute(_sql, _data)

    def mGetInfapatchingTimeStats(self, aChildUUID):
        _list = []
        _sql = """SELECT * FROM infrapatchingtimestats where child_uuid=%(1)s"""
        _data = [aChildUUID]
        _list = self.mFetchAll(_sql, _data)
        return _list

    def mCreateFilesTable(self, tablename):
        if not self.mCheckTableExist(tablename):
            self.mExecute(
                '''CREATE TABLE {0} (
                ID VARCHAR(255) PRIMARY KEY,
                CONTENT TEXT,
                MTIME TEXT)
                '''.format(tablename))

    def mReadFile(self, filename, tablename='ecra_files'):
        try:
            with open(filename) as fd:
                return fd.read()
        except Exception as e:
            ebLogError(str(e))
            return ''

    def import_file(self, filename, tablename='ecra_files'):
        if self.mGetDebug():
            ebLogDebug('Import file is for use with Oracle DB')

    def export_file(self, filename, tablename='ecra_files'):
        if self.mGetDebug():
            ebLogDebug('Export file is for use with Oracle DB')

    def search_files(self, search, tablename=None):
        return [(fname, '', '') for fname in glob(search)]

    def mCreateExawatcherTable(self):
        if not self.mCheckTableExist('exawatcher'):
            self.mExecute('''CREATE TABLE exawatcher (
                                                  uuid TEXT,
                                                  log_location TEXT,
                                                  filter TEXT,
                                                  fromtime TEXT,
                                                  totime TEXT,
                                                  targettypes TEXT,
                                                  targets TEXT,
                                                  exp_time FLOAT,
                                                  status TEXT)''')

    def mSetWatcherRequest(self, _data):
        _sql = """INSERT INTO exawatcher VALUES (%(1)s, %(2)s, %(3)s, %(4)s,
                                                 %(5)s, %(6)s, %(7)s, %(8)s, %(9)s)"""
        self.mExecute(_sql, _data)

    def mDeleteWatcher(self, _curtime):
        _sql = """DELETE FROM exawatcher WHERE exp_time<%(1)s"""
        _data = [_curtime]
        self.mExecute(_sql, _data)

    def mUpdateWatcher(self, _uuid, _log, _status, _etime):
        _sql = """UPDATE exawatcher
                  SET log_location=%(1)s, status=%(2)s, exp_time=%(3)s
                  WHERE uuid=%(4)s"""
        _data = [_log, _status, _etime, _uuid]
        self.mExecute(_sql, _data)

    def mGetWatcherLog(self, _rcount):
        _sql = """SELECT log_location, filter, fromtime, exp_time, status FROM exawatcher
                  ORDER BY exp_time DESC LIMIT %(1)s"""
        _rows = self.mFetchAll(_sql, [_rcount])
        _resp = [list(i) for i in _rows]
        if _resp:
            return 0, _resp
        return 1, ''

    def mRemoveWatcherLog(self, _lfile):
        _sql = """DELETE FROM exawatcher WHERE log_location=%(1)s"""
        self.mExecute(_sql, [_lfile])

    def mCreateCCATable(self):
        if not self.mCheckTableExist('ccadata'):
            self.mExecute('''CREATE TABLE ccadata (
                                                  id VARCHAR(255) PRIMARY KEY,
                                                  pid INTEGER,
                                                  parURL TEXT,
                                                  requestId TEXT,
                                                  resourceType TEXT,
                                                  auditType TEXT,
                                                  acpList TEXT,
                                                  status TEXT,
                                                  description TEXT,
                                                  schedulerid TEXT)''')
    
    def mSetCCAData(self, aData):
        _sql = """INSERT INTO ccadata VALUES (%(1)s, %(2)s, %(3)s, %(4)s,
                                              %(5)s, %(6)s, %(7)s, %(8)s, %(9)s, %(10)s)"""
        self.mExecute(_sql, aData)
    
    def mUpdateCCADataStatus(self, aId, aStatus, aDescription, aSchedulerId):
        if aSchedulerId is not None:
            _sql = """UPDATE ccadata SET status=%(1)s, description=%(2)s, schedulerid=%(3)s WHERE id=%(4)s"""
            _data = (aStatus, aDescription, aSchedulerId, aId)
        else:
            _sql = """UPDATE ccadata SET status=%(1)s, description=%(2)s WHERE id=%(3)s"""
            _data = (aStatus, aDescription, aId)
        self.mExecute(_sql, _data)

    def mGetCCADataStatus(self, aId):
        _sql = """SELECT status FROM ccadata WHERE id=%(1)s"""
        _data = [aId]
        return self.mExecute(_sql, _data)

    def mGetCCAUserList(self):
        _sql = """SELECT id FROM ccadata"""
        _list = self.mFetchAll(_sql)
        _clus = []
        if _list:
            for row in _list:
                _clus += row
        return _clus
    
    def mRemoveCCAUser(self, aId):
        _sql = """DELETE FROM ccadata WHERE id=%(1)s"""
        self.mExecute(_sql, [aId])

    def mGetCCAData(self):
        _sql = """SELECT * FROM ccadata"""
        _list = self.mFetchAll(_sql)
        return _list

    def mGetCCAAccessReqId(self, aId):
        _clus = self.mFetchOne("""SELECT requestId FROM ccadata WHERE id=%(1)s""", [aId])
        return _clus
 
    def mGetCCARequestType(self, aId):
        _clus = self.mFetchOne("""SELECT resourceType FROM ccadata WHERE id=%(1)s""", [aId])
        return _clus
 
    def mGetAllCCAUserResourceTypeList(self):
        _sql = """SELECT id, resourceType  FROM ccadata"""
        _list = self.mFetchAll(_sql)
        return _list

    def mGetAllCCAUserParUrlsList(self):
        _sql = """SELECT id, parURL FROM ccadata"""
        _list = self.mFetchAll(_sql)
        return _list

    def mGetCCASchedulerId(self, aStatus):
        _list = self.mFetchAll("""SELECT schedulerid FROM ccadata WHERE status=%(1)s""", [aStatus])
        _clus = []
        if _list:
            for row in _list:
                _clus += row
        return _clus

    def mGetCCAUsersByStatus(self, aStatus):
        _list = self.mFetchAll("""SELECT id FROM ccadata WHERE status=%(1)s""", [aStatus])
        _clus = []
        if _list:
            for row in _list:
                _clus += row
        return _clus


    # Table for locking, extra-columns for extensibility 
    # to implement Fine Grained locking and lock keepalive in the future
    def mCreateLocksTable(self):
        if not self.mCheckTableExist('locks'):
            self.mExecute('''CREATE TABLE locks (
                                                  uuid VARCHAR(128),
                                                  lock_type VARCHAR(256),
                                                  lock_hostname VARCHAR(256),
                                                  start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                  exp_time_sec INTEGER,
                                                  json_metadata TEXT)''')

    # All Get functions returns dictionary keyed with column name
    # this avoids confusing numeric access in upstream code
    def mGetAllLocks(self):
        _sql = """SELECT * FROM locks"""
        _list = self.mFetchAll(_sql)
        return list(map(sLockDBRowToDict, _list))

    def mGetLocksByType(self, aLockType):
        _sql = """SELECT * FROM locks where lock_type=%(1)s"""
        _list = self.mFetchAll(_sql, (str(aLockType),))
        return list(map(sLockDBRowToDict, _list))
    
    def mGetLocksByUUID(self, aUuid):
        _sql = """SELECT * FROM locks where uuid=%(1)s"""
        _list = self.mFetchAll(_sql, (aUuid,))
        return list(map(sLockDBRowToDict, _list))

    def mGetLocksByUUIDAndType(self, aUuid, aLockType):
        _sql = """SELECT * FROM locks where uuid=%(1)s and lock_type=%(2)s"""
        _list = self.mFetchAll(_sql, (aUuid, str(aLockType)))
        return list(map(sLockDBRowToDict, _list))

    def mInsertLock(self, uuid, lock_type='', lock_hostname='', start_time='', exp_time_sec='0', json_metadata=''):
        if not start_time:
            # Use the DEFAULT CURRENT TIMESTAMP Clause
            _sql = """INSERT INTO locks (uuid, lock_type, lock_hostname, exp_time_sec, json_metadata)
                      VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s)"""
            self.mExecute(_sql, (uuid, str(lock_type), lock_hostname, exp_time_sec, json_metadata))
        else:
            _sql = """INSERT INTO locks VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s)"""
            self.mExecute(_sql, (uuid, str(lock_type), lock_hostname, start_time, exp_time_sec, json_metadata))

    def mDeleteLock(self, uuid, lock_type, lock_hostname, ):
        _sql = """DELETE FROM locks WHERE uuid=%(1)s AND lock_type=%(2)s AND lock_hostname=%(3)s"""
        self.mExecute(_sql, (uuid, str(lock_type),lock_hostname))
    
    def mDeleteLockByHostname(self, lock_type, lock_hostname):
        _sql = """DELETE FROM locks WHERE lock_type=%(1)s AND lock_hostname=%(2)s"""
        self.mExecute(_sql, (str(lock_type), lock_hostname))

    def mDeleteAllLocks(self):
        _sql = """DELETE FROM locks"""
        self.mExecute(_sql)

    def mClearCustomerData(self, uuid):
        _sql = """UPDATE requests set body='Erased', params='{\"Erased\":\"Erased\"}', data='Erased' where uuid=%(1)s """
        self.mExecute(_sql, [uuid])

    def mUpdateResponseSent(self, uuid, value):
        _sql = """UPDATE requests set response_sent=%(1)s where uuid=%(2)s """
        self.mExecute(_sql, [value, uuid])

    def mCreateErrCodeTable(self):
        if not self.mCheckTableExist('errorresponse'):
            self.mExecute('''CREATE TABLE errorresponse (
                                                  uuid VARCHAR(128) PRIMARY KEY,
                                                  errorCode text,
                                                  errorMsg text,
                                                  errorType text,
                                                  retryCount INTEGER,
                                                  detailErr text,
                                                  nodeData LONGTEXT)''')

    def mSetErrCode(self, aData):
        _sql = """INSERT INTO errorresponse VALUES (%(1)s, %(2)s, %(3)s, %(4)s,
                                              %(5)s, %(6)s, %(7)s) ON DUPLICATE KEY UPDATE errorCode=%(2)s, 
                                              errorMsg=%(3)s, errorType=%(4)s, retryCount=%(5)s, detailErr=%(6)s, nodeData=%(7)s"""
        self.mExecute(_sql, aData)

    def mGetErrCodeByUUID(self, aUuid):
        _list = self.mFetchAll("""SELECT * FROM errorresponse where uuid=%(1)s""", [aUuid])
        _errcode = []
        if _list:
            for row in _list:
                _errcode += row
        return _errcode

    def mRemoveErrCodeByUUID(self, aUuid):
        _sql = """DELETE FROM errorresponse WHERE uuid=%(1)s"""
        self.mExecute(_sql, (aUuid,))

    def mCreateRunningDBsList(self):
        if not self.mCheckTableExist('runningdblist'):
            self.mExecute('''CREATE TABLE runningdblist (
                                                  virtualMachineName VARCHAR(128) PRIMARY KEY,
                                                  dbRunning LONGTEXT)''')

    def mSetDBlist(self, aNodeName, aDBRunningState):
        _sql = """INSERT INTO runningdblist VALUES (%(1)s, %(2)s)
                                              ON DUPLICATE KEY UPDATE virtualMachineName=%(1)s,
                                              dbRunning=%(2)s"""
        aData = [aNodeName, aDBRunningState]
        self.mExecute(_sql, aData)

    def mGetDBListByNode(self, aNodeName):
        _sql = """SELECT dbRunning FROM runningdblist where virtualMachineName=%(1)s"""
        _data = [aNodeName]
        _resp = self.mFetchOne(_sql, _data)
        if _resp:
            return _resp[0]
        return ''

    def mRemoveDBListByNode(self, aNodeName):
        _sql = """DELETE FROM runningdblist where virtualMachineName=%(1)s"""
        aData = [aNodeName]
        self.mExecute(_sql, aData)

    def mCreateAsyncProcessTable(self):
        if not self.mCheckTableExist('asyncprocess'):
            self.mExecute('''CREATE TABLE asyncprocess (uuid VARCHAR(255) PRIMARY KEY,
                                                    return_value LONGTEXT,
                                                    name LONGTEXT,
                                                    alive TINYINT,
                                                    log_file TEXT,
                                                    time_start TEXT,
                                                    time_end TEXT,
                                                    max_time TEXT,
                                                    args TEXT)''')

    def mGetAsyncProcessById(self, aId):
        _process = None
        _process = self.mFetchOne("""SELECT uuid, return_value , name, alive, log_file, time_start, time_end, max_time , args 
                                        FROM asyncprocess WHERE uuid=%(1)s""", [aId])
        return _process
    
    def mUpsertAsyncProcess(self, aProcessDict):
        _sql = """INSERT INTO asyncprocess VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s, %(7)s, %(8)s, %(9)s) 
                    ON DUPLICATE KEY UPDATE return_value=%(2)s, name=%(3)s, alive=%(4)s, log_file=%(5)s, time_start=%(6)s, time_end=%(7)s"""
        _data =[
            aProcessDict["id"],
            # return code can be ANY type, wrapping as a json for db storage
            json.dumps(aProcessDict["rc"]),
            aProcessDict["name"],
            int(aProcessDict.get("alive", False)),
            aProcessDict["log_file"],
            aProcessDict["time_start"],
            aProcessDict["time_end"],
            aProcessDict.get("max_exec_time", None),
            aProcessDict.get("args",None)
        ]
        self.mExecute(_sql, _data)
        return
    
    def mCreateMetricsTable(self):
        '''
            This method creates a metrics table with the following schema:  \\
                metricid INTEGER NOT NULL AUTO_INCREMENT, \\
                category VARCHAR(30) NOT NULL, \\ 
                created_at TIMESTAMP NOT NULL, \\
                data JSON NOT NULL, \\
                PRIMARY KEY(metricid)
        '''
        if not self.mCheckTableExist('metrics'):
            self.mExecute('''CREATE TABLE metrics (
                                metricid INTEGER NOT NULL AUTO_INCREMENT,
                                category VARCHAR(30) NOT NULL,
                                created_at TIMESTAMP NOT NULL,
                                data JSON NOT NULL,
                                PRIMARY KEY(metricid))''')

    def mInsertNewMetrics(self, aMetric):
        '''
            This method takes in input a dictionary: which has the category, created_at and JSON_data in accordance to the schema of the metrics table, the methods inserts the data provided into the metrics table
        '''
        _category = aMetric["category"]
        _created_at = aMetric["created_at"]
        _data = aMetric["data"]

        _sql = """INSERT INTO metrics (category, created_at, data)
                  VALUES (%(1)s, %(2)s, %(3)s)"""
        _command = [_category, _created_at, _data]
        
        self.mExecuteLog(_sql, _command)

    def mGetWorkerPIDs(self):
        '''
            This method fetches and returns the PIDs of the workers
        '''
        _sql = """SELECT pid FROM workers WHERE type = 'worker'"""
        _rows = self.mFetchAll(_sql)
        return _rows  

    def mGetLatestMetric(self, category):
        '''
            This method returns the JSON data of the last metric inserted to the database belonging to a particular category given as input
        '''
        if self.mCheckTableExist('metrics'):
            _sql = f"SELECT data FROM metrics WHERE category = '{category}' ORDER BY metricid DESC LIMIT 1"
            _resp = self.mFetchOne(_sql)
            return _resp
        return None
    
    def mGetRequestStatus(self, cmd):
        '''
            This method fetches and returns the commands from the requests table in the database
        '''
        _sql = f"SELECT {cmd} FROM requests"
        _list = self.mFetchAll(_sql)
        _cmds = []
        if _list:
            for row in _list:
                _cmds += row
        return _cmds

    def mGetActiveRequestStatus(self):
        '''
            This method fetches and returns the active requests from the requests table in the database
        '''
        _count = self.mFetchOne("""SELECT COUNT(*) FROM requests WHERE status='Pending'""")
        if _count:
            return _count[0]

    def mGetPidFile(self):
        '''
            This method fetches and returns the path to the file storing the PID of the given MySQL Daemon Process
        '''
        _sql = """show variables like 'pid_file'"""
        return self.mFetchAll(_sql)

    def mGetRegValueByKey(self, aKey):
        '''
            This method fetches and returns value (which is a stringified dictionary) when provided with the key as the input
        '''
        _rc = self.mFetchOne(f"""SELECT value FROM registry WHERE _key = '{aKey}'""")
        return _rc
