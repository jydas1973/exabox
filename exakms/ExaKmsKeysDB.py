#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsKeysDB.py /main/15 2023/10/24 09:29:02 jesandov Exp $
#
# ExaKmsKeysDB.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsKeysDB.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    10/20/23 - 35933990: Include label in ExaKmsEntry
#    jesandov    06/12/23 - 35484161: Add validation to nathostname in the search pattern dict
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    aypaul      06/02/22 - Enh#34207528 ExaKms entry history tracking and
#                           generation.
#    jesandov    05/31/22 - Add ExaKms KeyValue Info
#    jesandov    03/24/22 - 33997797 - EXACS: EXAKMS: ADD CACHE TO EXAKMS KEY
#                           MANAGEMENT
#    alsepulv    08/16/21 - Bug 30993225: Create Backup class method
#    jesandov    04/27/21 - Creation
#

import os
import re
import shutil
import json
import copy

from exabox.core.Context import get_gcontext
from exabox.core.Core import ebExit
from exabox.core.DBKeys import DBKeys
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsEntryRSA import ExaKmsEntryRSA
from exabox.exakms.ExaKmsEntryKeysDB import ExaKmsEntryKeysDBRSA, ExaKmsEntryKeysDBECDSA
from exabox.exakms.ExaKms import ExaKms
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.kms.crypt import cryptographyAES
from exabox.exakms.ExaKmsHistoryDB import ExaKmsHistoryDB
from typing import List, Optional, Tuple

class ExaKmsKeysDB(ExaKms):

    def __init__(self) -> None:
        """ Constructor for ExaKmsKeysDB object.
        """

        ExaKms.__init__(self)

        _entryClasses = {
            "ECDSA": ExaKmsEntryKeysDBECDSA,
            "RSA": ExaKmsEntryKeysDBRSA
        }

        if get_gcontext().mCheckRegEntry("exakms_default_keygen_algorithm"):

            if get_gcontext().mGetRegEntry("exakms_default_keygen_algorithm") == "ECDSA":
                _entryClasses["DEFAULT"] = _entryClasses["ECDSA"]
            else:
                _entryClasses["DEFAULT"] = _entryClasses["RSA"]

        else:

            if get_gcontext().mCheckConfigOption("exakms_default_keygen_algorithm", "ECDSA"):
                _entryClasses["DEFAULT"] = _entryClasses["ECDSA"]
            else:
                _entryClasses["DEFAULT"] = _entryClasses["RSA"]

        self.mSetEntryClass(_entryClasses)

        _config = get_gcontext().mGetConfigOptions()

        _dbPath = get_gcontext().mGetBasePath()+'/db'
        if 'db_dir' in _config.keys():
            _dbPath = _config['db_dir']

        try:
            os.lstat(_dbPath)
        except:
            ebLogError('ERR: Invalid wallet location', _dbPath)
            ebExit(-1)

        self.__databaseObj = None
        self.mSetDatabaseObj(DBKeys(os.path.join(_dbPath, 'keys.db')))

        # create keys backup folder
        self.__backuppath = "clusters/exakms_backup"
        if not os.path.exists(self.__backuppath):
            os.makedirs(self.__backuppath)

        self.mSetExaKmsHistoryInstance(ExaKmsHistoryDB())

    def mGetDatabaseObj(self) -> DBKeys:
        """ Getter for database object attribute
        """

        return self.__databaseObj

    def mSetDatabaseObj(self, aObj: DBKeys) -> None:
        """ Setter for database object attribute
        """

        self.__databaseObj = aObj

    def mBuildExaKmsEntry(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN, aClassName=None):

        _class = self.mGetEntryClass()

        if aClassName:
            if "ECDSA" in aClassName:
                _class = ExaKmsEntryKeysDBECDSA
            else:
                _class = ExaKmsEntryKeysDBRSA

        return _class(aFQDN, aUser, aPrivateKey, aHostType)


    def mSearchExaKmsEntries(self, aPatternDict: dict, aRefreshKey: bool = False) -> List[ExaKmsEntry]:
        """
        Returns a list of exaKms entries based on the patterns provided.
        If the pattern dictionary is empty, it will return all kms
        entries in the object storage.
        """

        _patternDict = copy.deepcopy(aPatternDict)
        if "FQDN" in _patternDict:
            _patternDict["FQDN"] = self.mGetEntryClass().mUnmaskNatHost(_patternDict["FQDN"])

        if not aRefreshKey:
            _entries = self.mFilterCache(_patternDict)
            if _entries:
                return _entries

        # Reload DB Cache
        self.mGetDatabaseObj().mReload()

        _entries = []
        _keysDict = self.mGetDatabaseObj().mGetDict()

        for _objectName, _objectContent in _keysDict.items():

            try:
                _data = json.loads(_objectContent)
            except:
                continue

            for _dataKey, _dataValue in _data.items():

                _patt = re.match("id_rsa.([\\w\\-\\_]+).([\\w\\-\\_]+)$", _dataKey)

                # Filter entries
                if not _patt:
                    continue

                _fqdn = _patt.group(1)
                if "." in _objectName:
                    _fqdn = _objectName

                _fqdn = self.mGetEntryClass().mUnmaskNatHost(_fqdn)

                if "FQDN" in _patternDict:

                    _pattfqdn = _patternDict['FQDN']
                    _pattfqdn = self.mGetEntryClass().mUnmaskNatHost(_pattfqdn)

                    if "strict" in _patternDict and _patternDict['strict']:

                        if _fqdn.split(".")[0] != _pattfqdn.split(".")[0]:
                            continue

                    else:

                        if not re.match(_pattfqdn, _fqdn) and \
                           _fqdn.split(".")[0] != _pattfqdn.split(".")[0]:

                            continue

                if "user" in _patternDict:

                    if _patt.group(2) != _patternDict['user']:
                        continue

                try:
                   # _realDataValue = json.loads(_dataValue)
                    _realDataValue = _dataValue
                except:
                    continue

                if "encData" not in _realDataValue:
                    continue

                if not _realDataValue['encData']:
                    continue

                _version = None
                if "version" in _realDataValue:
                    _version = _realDataValue["version"]
                else:
                    _version = "RSA"

                _entry = self.mBuildExaKmsEntry(_fqdn, _patt.group(2), "", aClassName=_version)
                _entry.mSetEncData(_realDataValue['encData'])
                _entry.mSetPkDB(_objectName)

                if "creationTime" in _realDataValue:
                    _entry.mSetCreationTime(_realDataValue['creationTime'])

                if "label" in _realDataValue:
                    _entry.mSetLabel(_realDataValue['label'])

                if "exacloud_host" in _realDataValue:
                    _entry.mSetExacloudHost(_realDataValue['exacloud_host'])

                if "hash" in _realDataValue:
                    _entry.mSetHash(_realDataValue['hash'])

                if "hostType" in _realDataValue:
                    _entry.mSetHostType(_realDataValue['hostType'])

                if "keyValueInfo" in _realDataValue:
                    _entry.mSetKeyValueInfo(_realDataValue['keyValueInfo'])

                _entries.append(_entry)

        def mGetSortKey(aEntry):

            _str = f"{aEntry.mGetCreationTime()}|"

            if aEntry.mGetPkDB() == aEntry.mGetFQDN():
                _str = "1|"
            else:
                _str = "0|"

            return _str

        _sorted = sorted(_entries, key=mGetSortKey, reverse=True)

        for _entry in _sorted:
            self.mUpdateCacheKey(_entry.mGetFQDN(), _entry)

        return _sorted

    def mDeleteExaKmsEntry(self, aKmsEntry: ExaKmsEntry) -> bool:
        """
        Deletes entry from the database object and returns True
        if successful. Otherwise, returns False
        """

        _existingEntry = aKmsEntry
        if not _existingEntry.mGetPkDB():
            _existingEntry = self.mGetExaKmsEntry(aKmsEntry.mGetUniqJSON())

        if not _existingEntry:
            return False

        _rc, _resp = self.mGetDatabaseObj().mGetSshkey(_existingEntry.mGetPkDB())
        if _rc != 0:
            return False

        _objDict = json.loads(_resp)
        _objectName = f'id_rsa.{_existingEntry.mGetFQDN().split(".")[0]}.{_existingEntry.mGetUser()}'

        try:
            del _objDict[_objectName]

            if not _objDict:
                self.mGetDatabaseObj().mDumpdb(aDelete=_existingEntry.mGetPkDB())
            else:
                self.mGetDatabaseObj().mUpsertSshkey(_existingEntry.mGetPkDB(), json.dumps(_objDict))

            super().mDeleteExaKmsEntry(_existingEntry)
            return True

        except:
            return False

    def mInsertExaKmsEntry(self, aKmsEntry: ExaKmsEntry, aPreservateCreationTime=False) -> bool:
        """
        Creates an entry in the database object given an ExaKmsEntry object
        Returns True if successful and False otherwise
        """

        # Encrypt key data
        _objDict = {}
        _dataEncryptionKeyDict = {}
        _dataEncryptionKeyDict['hash'] = aKmsEntry.mGetHash()
        _dataEncryptionKeyDict['encData'] = aKmsEntry.mGetEncData()
        _dataEncryptionKeyDict['hostType'] = str(aKmsEntry.mGetHostType().name)
        _dataEncryptionKeyDict['keyValueInfo'] = aKmsEntry.mGetKeyValueInfo()
        _dataEncryptionKeyDict['version'] = aKmsEntry.mGetVersion()
        _dataEncryptionKeyDict['label'] = ExaKmsEntryKeysDBRSA.mGetCurrentLabel()
        _dataEncryptionKeyDict['exacloud_host'] = ExaKmsEntryKeysDBRSA.mGetCurrentExacloudHost()

        if aPreservateCreationTime:
            _dataEncryptionKeyDict['creationTime'] = aKmsEntry.mGetCreationTime()
        else:
            _dataEncryptionKeyDict['creationTime'] = ExaKmsEntryKeysDBRSA.mGetCurrentTime()

        _objId = f'id_rsa.{aKmsEntry.mGetFQDN().split(".")[0]}.{aKmsEntry.mGetUser()}'
        _objDict = {}

        _rc, _resp = self.mGetDatabaseObj().mGetSshkey(aKmsEntry.mGetPkDB())
        if _rc == 0:
            _objDict = json.loads(_resp)

        _objDict[_objId] = _dataEncryptionKeyDict

        # Upload encrypted key to DB
        try:

            self.mGetDatabaseObj().mUpsertSshkey(aKmsEntry.mGetPkDB(), json.dumps(_objDict))
            super().mInsertExaKmsEntry(aKmsEntry)

            return True

        except:
            return False

    def mBackup(self) -> bool:
        """
        Creates a backup of the keys
        in a zip file in clusters/exakms_backup
        """

        self.mSetCache({})
        _entries = self.mSearchExaKmsEntries({}, aRefreshKey=True)

        if not len(_entries):
            ebLogWarn('Not able to backup keys. No keys found.')
            return False

        # Create a temporary folder in which all the entries
        # will be briefly stored as json files 
        _tmpFolder = os.path.join(self.__backuppath, 'tmp')
        os.makedirs(_tmpFolder)

        try:
            for _entry in _entries:
                _hostname = _entry.mUnmaskNatHost(_entry.mGetFQDN())
                _keyfile = f'{_entry.mGetUser()}#{_hostname}.json'
                _keyfile = os.path.join(_tmpFolder, _keyfile)

                with open(_keyfile, "w") as _f:
                    _json = _entry.mToJson()
                    _f.write(json.dumps(_json, indent=4, sort_keys=True))

            # We zip all json files in our temp folder and store the zip
            # into the backup folder
            _backupfile = os.path.join(self.__backuppath, ExaKmsEntry.mGetCurrentTime())
            shutil.make_archive(_backupfile, 'zip', _tmpFolder)
            ebLogInfo(f'Backup created at {_backupfile}.zip')
            return True

        except Exception as e:
            ebLogWarn('Not able to backup keys.')
            ebLogWarn(e)
            return False

        finally:
            shutil.rmtree(_tmpFolder)

    def mRestoreBackup(self) -> bool:
        """ Restores the entries in the backup folder
        """

        # Get all zip files
        _allzips = []
        for f in os.listdir(self.__backuppath):
            if f.endswith('.zip'):
                _allzips.append(f)

        if not len(_allzips):
            ebLogWarn('Not able to restore backup. No backup found.')
            return False

        # Get latest zip
        _latestzip = max(_allzips)
        _latestzip = os.path.join(self.__backuppath, _latestzip)

        _tmpFolder = os.path.join(self.__backuppath, 'tmp')
        os.makedirs(_tmpFolder)

        try:
            # Unzip file into tmp folder
            shutil.unpack_archive(_latestzip, _tmpFolder)
            for _file in os.listdir(_tmpFolder):
                if not _file.endswith('.json'):
                    continue

                _keyfile = os.path.join(_tmpFolder, _file)
                with open(_keyfile, 'r') as _f:
                    _json = json.loads(_f.read())

                # Use each json file to create an exakms entry
                _version = None
                if "version" in _json:
                    _version = _json["version"]

                _entry = self.mBuildExaKmsEntry('', '', '', aClassName=_version)
                _entry.mFromJson(_json)

                _entryDict = {"FQDN": _entry.mGetFQDN(),
                              "user": _entry.mGetUser()}
                _mainEntry = self.mSearchExaKmsEntries(_entryDict, aRefreshKey=True)

                # If the entry already exists, we keep the latest one
                if not _mainEntry or _mainEntry.mGetCreationTime() < _entry.mGetCreationTime():
                    self.mInsertExaKmsEntry(_entry)

            ebLogInfo('Exakms backup restored successfully.')
            return True

        except Exception as e:
            ebLogWarn('Not able to restore backup.')
            ebLogWarn(e)
            return False

        finally:
            shutil.rmtree(_tmpFolder)

# end of file
