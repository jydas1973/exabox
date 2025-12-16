"""
$Header: ecs/exacloud/exabox/core/DBKeys.py /main/8 2022/01/20 22:31:41 oespinos Exp $

DBKeys.py

 Copyright (c) 2020, 2022, Oracle and/or its affiliates.

   NAME
     DBKeys.py - <one-line expansion of the name>

   DESCRIPTION
     <short description of component this file declares/defines>

   NOTES
     <other useful comments, qualifications, etc.>

   MODIFIED   (MM/DD/YY)
   oespinos    01/18/22 - 33761439 - keys.db not getting synced to second node
   ndesanto    12/14/21 - Increase coverage for ndesanto files.
   ndesanto    12/10/21 - Increase coverage on ndesanto files.
   ndesanto    02/26/21 - Bug 32560820 - Fixing mDump for when file does not
                          exist yet.
   vgerard     02/25/21 - Bug 32546000 - Fix Race condition
   ndesanto    02/02/21 - Bug 32374102 - Fixing encoding issue in json load
   ndesanto    12/04/20 - Fix for CPS creating empty dbkyes.db files
   ndesanto    08/10/20 - Changes to set lock file in exacloud/tmp directory.
                          Changed open to use with block
   ndesanto    05/19/20 - Creation

"""


import json
import os
import shutil
import sqlite3
from json.decoder import JSONDecodeError
from time import sleep

from exabox.agent.ExaLock import ExaLock
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB


class DBKeys():

    def __init__(self, aLocation):
        self._db = None
        self._location = aLocation
        self._locationLck = self._location + ".lock"
        self._locationBkp = self._location + ".json.bkp"
        self.mLoad(self._location)

    def __len__(self):
        return self.mSize()

    def mGetDict(self):
        return self._db

    def mLoad(self, aLocation):
        if os.path.exists(aLocation):
            self._load(aLocation)
        else:
            self._db = {}
        return True

    def mReload(self):
        self.mLoad(self._location)

    def _load(self, aLocation):
        with ExaLock(self._locationLck):
            try:
                with open(aLocation , "r") as fd:
                    self._db = json.load(fd)
            except:
                if not self._db:  # If no dict create a new one
                    self._db = {}
                try:
                    self.mMigrate(aLocation)
                except:  # pragma: no cover
                    # If migration fails for any reason just log it and move on
                    _bkp_file = aLocation + ".err"
                    self.mBackupFile(aLocation, _bkp_file)
                    ebLogWarn("Existing file is not in an expected format. " + \
                        "Please check file \"{}\".".format(_bkp_file))

    def mDumpdb(self, aUpdate=None, aDelete=None):
        try:
            with ExaLock(self._locationLck):
                # If we perform an update or deletion
                # re-read the JSON File as another cluster may have been
                # modified and the json.dump will restore an OUTDATED state
                # for all other clusterkeys
                if aUpdate or aDelete:
                    #since we run LOAD in constructor, it is always migrated
                    if os.path.exists(self._location) and os.path.getsize(self._location) > 0:
                        with open(self._location) as fd:
                            self._db = json.load(fd)
                    if aUpdate:
                        _key, _value = aUpdate
                        self._db[_key] = _value
                    if aDelete:
                        del self._db[aDelete]
                     
                # As we reread JSON and did update in the locked section for 
                # ONLY THE CHANGED DATA, it is safe now to write the JSON file
                with open(self._locationBkp, "w") as fd:
                    json.dump(self._db , fd)
                shutil.copyfile(self._locationBkp, self._location)
                return True
        except Exception as e:  # pragma: no cover
            ebLogError("DBKeys.mDumpdb - Error Saving Values to Disk : {}"\
                .format(e))
            return False

    def mBackupFile(self, aSourcePath, aDestinationPath):
        if os.path.exists(aDestinationPath):
            os.remove(aDestinationPath)
        shutil.copy(aSourcePath, aDestinationPath)

    def mMigrate(self, aDBPath):
        _is_migrated = False
        _migration_counter = 0
        # Create a backup of the DB file
        _bkp_file = aDBPath + ".sqlite.bkp"
        self.mBackupFile(aDBPath, _bkp_file)
        
        _conn = sqlite3.connect(
            _bkp_file, check_same_thread=False, isolation_level=None)
        try:
            _rc = _conn.execute("SELECT cluster_name, sshkeys FROM sshkey;")
            _list = _rc.fetchall()
            for _row in _list:
                self._set(_row[0], _row[1], False)
                _migration_counter += 1
            _is_migrated = True
        finally:
            _conn.close()
        # Delete DB file since content was migrated
        if _is_migrated:
            os.remove(aDBPath)
            if os.path.exists(aDBPath + "-shm"):
                os.remove(aDBPath + "-shm")
            if os.path.exists(aDBPath + "-wal"):
                os.remove(aDBPath + "-wal")
            self.mDumpdb()
        else:
            _migration_counter = -1
        return _migration_counter

    def mReset(self):
        self._db = {}
        self.mDumpdb()

    def mSize(self):
        return len(self._db)

    def _set(self, aKey, aValue, aDump=True):
        try:
            if aDump:
                self.mDumpdb(aUpdate=(aKey, aValue))
            else:
                self._db[aKey] = aValue
            return True
        except Exception as e:  # pragma: no cover
            ebLogError("DBKeys._set - Error Saving Values to Database : {}"\
                .format(e))
            return False

    def _get(self, aKey):
        try:
            return self._db[aKey]
        except KeyError:
            ebLogWarn("DBKeys._get - No Value Can Be Found for {}"\
                .format(aKey))
            return False

    def _delete(self, aKey):
        if not aKey in self._db:
            return False
        self.mDumpdb(aDelete=aKey)
        return True

# Compatibility methods

    def mCreateSshkeyTable(self):
        self.mLoad(self._location)

    def mUpsertSshkey(self, aCluster, aSshkey):
        self._set(aCluster, aSshkey)
        return 0, ''

    def mGetSshkey(self, aCluster):
        _resp = self._get(aCluster)
        if _resp:
            return 0, _resp
        return 1, ''

    def mDeleteSshkeyTable(self):
        self.mReset()
