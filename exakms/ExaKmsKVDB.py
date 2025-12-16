#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsKVDB.py /main/5 2024/10/24 19:20:56 ririgoye Exp $
#
# ExaKmsKVDB.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsKVDB.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    10/21/24 - Bug 37197710 - MSEARCHEXAKMSENTRIES 'LIST' OBJECT
#                           HAS NO ATTRIBUTE 'MCREATEVALUEFROMENCDATA'
#    ririgoye    10/14/24 - Bug 37076081 - Added optional aRefreshKey param for
#                           compatibility
#    aypaul      02/15/24 - Creation
#

import os
import re
import shutil
import json
import copy

from exabox.core.Context import get_gcontext
from exabox.core.Core import ebExit
from exabox.core.DBKeys import DBKeys
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsKVEntry, ExaKmsHostType, ExaKmsOperationType
from exabox.exakms.ExaKmsEntryKVDB import ExaKmsEntryKVDB, ExaKmsEntryKVDBRSA, ExaKmsEntryKVDBECDSA
from exabox.exakms.ExaKms import ExaKms
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.kms.crypt import cryptographyAES
from typing import List, Optional, Tuple
from exabox.core.Error import ExacloudRuntimeError

class ExaKmsKVDB(ExaKms):

    def __init__(self) -> None:

        ExaKms.__init__(self)

        _config = get_gcontext().mGetConfigOptions()

        _entryClasses = {
            "ECDSA": ExaKmsEntryKVDBECDSA,
            "RSA": ExaKmsEntryKVDBRSA
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

        _db_path = os.path.join(get_gcontext().mGetBasePath(), 'db')
        if 'db_dir' in _config.keys():
            _db_path = _config['db_dir']

        try:
            os.lstat(_db_path)
        except:
            _err_msg = f"Invalid db location: {_db_path}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        self._database_obj = None
        self.mSetDatabaseObj(DBKeys(os.path.join(_db_path, 'exakv.db')))

    def mGetDatabaseObj(self) -> DBKeys:
        return self._database_obj

    def mSetDatabaseObj(self, aObj: DBKeys) -> None:
        self._database_obj = aObj

    def mBuildExaKmsEntry(self, aKey:str, aValue:str) -> ExaKmsEntryKVDB:
        return ExaKmsEntryKVDB(aKey, aValue)

    def mDeleteExaKmsEntry(self, aKey:str) -> bool:
        """
        Deletes entry from the database object and returns True
        if successful. Otherwise, returns False
        """

        _existing_entry = aKey

        self.mGetDatabaseObj().mReload()
        _keys_dict = self.mGetDatabaseObj().mGetDict()

        if _existing_entry not in _keys_dict.keys():
            return False

        try:
            # Build copy of value
            _value = _keys_dict[_existing_entry]
            _value_str = json.dumps(_value)
            _entry = self.mBuildExaKmsEntry(_existing_entry, _value_str)
            _historyNode = {"operation": ExaKmsOperationType.DELETE, "exakms": _entry}
            self.mGetHistory().append(_historyNode)
            # Delete value
            del _keys_dict[_existing_entry]
            self.mGetDatabaseObj().mDumpdb()
            return True
        except:
            return False

    def mInsertExaKmsEntry(self, aKmsEntry: ExaKmsEntryKVDB) -> bool:
        """
        Creates an entry in the database object given an ExaKmsEntry object
        Returns True if successful and False otherwise
        """
        _keys_dict = self.mGetDatabaseObj().mGetDict()
        _keys_dict[aKmsEntry.mGetKey()] = aKmsEntry.mToJson()

        # Upload encrypted key to DB
        try:
            # Upload
            self.mGetDatabaseObj().mDumpdb()
            # Add node to history
            _historyNode = {"operation": ExaKmsOperationType.INSERT, "exakms": aKmsEntry}
            self.mGetHistory().append(_historyNode)
            return True
        except:
            return False

    def mSearchEntries(self, aPatternDict: dict, aRefreshKey: bool = False) -> List[ExaKmsEntry]:
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
                if not isinstance(_objectContent, str):
                    _objectContent = json.dumps(_objectContent)
                _data = json.loads(_objectContent)
            except:
                continue

            if "encData" not in _data.keys():
                continue

            if not _data.get('encData'):
                continue

            _version = None
            if "version" in _data.keys():
                _version = _data["version"]
            else:
                _version = "RSA"

            _entry = self.mBuildExaKmsEntry(_objectName, json.dumps(_objectContent))
            _entry.mSetEncData(_data['encData'])

            if "creationTime" in _data:
                _entry.mSetCreationTime(_data['creationTime'])

            if "label" in _data:
                _entry.mSetLabel(_data['label'])

            _entries.append(_entry)
        
        return _entries

    def mSearchEntry(self, aKey: str) -> ExaKmsEntry:
        """
        Returns a single ExaKmsKVDB entry matching the key provided.
        """
        # Reload DB Cache
        self.mGetDatabaseObj().mReload()
        _keys_dict = self.mGetDatabaseObj().mGetDict()
        
        if aKey in _keys_dict:
            _exakms_entry_dict = _keys_dict.get(aKey)
            _exakms_entry = self.mBuildExaKmsEntry(aKey, "")
            _exakms_entry.mFromJson(_exakms_entry_dict)
            return _exakms_entry
        
        return None

    def mSearchExaKmsEntries(self, aKey, aRefreshKey: bool = False) -> List[ExaKmsEntry]:
        """
        Returns either a single ExaKmsKVDB entry or a list of exaKms KV entries 
        based on the key provided.
        """
        if isinstance(aKey, str):
            return [self.mSearchEntry(aKey)]
        else:
            return self.mSearchEntries(aKey, aRefreshKey=aRefreshKey)
