#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsFileSystem.py /main/14 2023/10/24 09:29:02 jesandov Exp $
#
# ExaKmsFileSystem.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsFileSystem.py - <one-line expansion of the name>
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
import copy
import json

from exabox.core.Context import get_gcontext
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsEntryFileSystem import ExaKmsEntryFileSystemRSA, ExaKmsEntryFileSystemECDSA
from exabox.exakms.ExaKms import ExaKms
from exabox.exakms.ExaKmsHistoryDB import ExaKmsHistoryDB
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn

class ExaKmsFileSystem(ExaKms):

    def __init__(self):

        ExaKms.__init__(self)

        _entryClasses = {
            "ECDSA": ExaKmsEntryFileSystemECDSA,
            "RSA": ExaKmsEntryFileSystemRSA
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

        self.__keypath = get_gcontext().mCheckConfigOption("exakms_fs_keypath")
        if not self.__keypath:
            self.__keypath = "clusters/exakms/"

        self.__backuppath = get_gcontext().mCheckConfigOption("exakms_fs_keypath_bk")
        if not self.__backuppath:
            self.__backuppath = "clusters/exakms_backup"

        if not os.path.exists(self.__keypath):
            os.makedirs(self.__keypath)

        if not os.path.exists(self.__backuppath):
            os.makedirs(self.__backuppath)

        self.mSetExaKmsHistoryInstance(ExaKmsHistoryDB())

    def mBuildExaKmsEntry(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN, aClassName=None):

        _class = self.mGetEntryClass()

        if aClassName:
            if "ECDSA" in aClassName.upper():
                _class = ExaKmsEntryFileSystemECDSA
            else:
                _class = ExaKmsEntryFileSystemRSA

        return _class(aFQDN, aUser, aPrivateKey, aHostType)


    def mSearchExaKmsEntries(self, aPatternDict, aRefreshKey=False):

        _patternDict = copy.deepcopy(aPatternDict)
        if "FQDN" in _patternDict:
            _patternDict["FQDN"] = self.mGetEntryClass().mUnmaskNatHost(_patternDict["FQDN"])

        if not aRefreshKey:
            _entries = self.mFilterCache(_patternDict)
            if _entries:
                return _entries

        _entries = []
        _keysFiles = os.listdir(self.__keypath)

        for _keyFile in _keysFiles:

            _regex = re.match("([\\w\\-\\_]+)\\#([\\w\\-\\.\\_]+)\\.json$", _keyFile)

            if _regex:

                _user = _regex.group(1)
                _host = _regex.group(2)

                if "FQDN" in _patternDict:

                    if "strict" in _patternDict and _patternDict['strict']:

                        if not _patternDict['FQDN'].split(".")[0] == _host.split(".")[0]:
                            continue

                    else:

                        if not re.search(_patternDict['FQDN'], _host):
                            continue

                if "user" in _patternDict:

                    if _user != _patternDict['user']:
                        continue

                _file = os.path.join(self.__keypath, _keyFile)
                _entry = self.mReadExaKmsEntry(_file)

                if _entry:
                    _entries.append(_entry)

        _sorted = sorted(_entries, key=lambda x: x.mGetCreationTime(), reverse=True)

        for _entry in _sorted:
            self.mUpdateCacheKey(_entry.mGetFQDN(), _entry)

        return _sorted

    def mReadExaKmsEntry(self, aFile):

        # Get json file
        _keyfile = aFile

        if not os.path.exists(_keyfile):
            return None

        _jsonEntry = None
        try:
            with open(_keyfile, "r") as _f:
                _jsonEntry = json.loads(_f.read())
        except Exception as e:
            ebLogWarn("Error while load file: {0}".format(_keyfile))
            ebLogWarn(e)

        if not _jsonEntry:
            return None

        # Fill datastructure
        _version = None
        if "version" in _jsonEntry:
            _version = _jsonEntry["version"]

        _entry = self.mBuildExaKmsEntry("", "", "", aClassName=_version)
        _entry.mFromJson(_jsonEntry)
        return _entry

    def mDeleteExaKmsEntry(self, aKmsEntry):

        # Get data
        _hostname = ExaKmsEntry.mUnmaskNatHost(aKmsEntry.mGetFQDN())
        _user = aKmsEntry.mGetUser()

        # Get private key
        _keyfile = "{0}#{1}.json".format(_user, _hostname)
        _keyfile = os.path.join(self.__keypath, _keyfile)

        if os.path.exists(_keyfile):
            os.remove(_keyfile)

        super().mDeleteExaKmsEntry(aKmsEntry)
        return True

    def mInsertExaKmsEntry(self, aKmsEntry, aPreservateCreationTime=False):

        _hostname = ExaKmsEntry.mUnmaskNatHost(aKmsEntry.mGetFQDN())

        if not aPreservateCreationTime:
            aKmsEntry.mSetCreationTime(self.mGetEntryClass().mGetCurrentTime())

        aKmsEntry.mSetLabel(self.mGetEntryClass().mGetCurrentLabel())
        aKmsEntry.mSetExacloudHost(self.mGetEntryClass().mGetCurrentExacloudHost())

        # Create Key on FileSystem
        _keyfile = "{0}#{1}.json".format(aKmsEntry.mGetUser(), _hostname)
        _keyfile = os.path.join(self.__keypath, _keyfile)

        with open(_keyfile, "w") as _f:
            _json = aKmsEntry.mToJson()
            _f.write(json.dumps(_json, indent=4, sort_keys=True))

        super().mInsertExaKmsEntry(aKmsEntry, aPreservateCreationTime)
        return True

    def mBackup(self):

        self.mSetCache({})
        _entries = self.mSearchExaKmsEntries({}, aRefreshKey=True)

        if not len(_entries):
            ebLogWarn("Not able to backup keys. No keys found")
            return False

        try:
            _backupfile = os.path.join(self.__backuppath, ExaKmsEntry.mGetCurrentTime())
            shutil.make_archive(_backupfile, 'zip', self.__keypath)
            ebLogInfo(f'Backup created at {_backupfile}.zip')
            return True
        except Exception as e:
            ebLogWarn("Not able to backup keys")
            ebLogWarn(e)
            return False

    def mRestoreBackup(self):

        self.mSetCache({})

        # Get all zip files
        _allzips = []
        for f in os.listdir(self.__backuppath):
            if f.endswith('.zip'):
                _allzips.append(f)

        if not len(_allzips):
            ebLogWarn("Not able to restore backup. No backups found")
            return False

        # Get latest zip file and unzip it into a temporary location
        _latestzip = max(_allzips)
        _latestzip = os.path.join(self.__backuppath, _latestzip)

        _tmpFolder = os.path.join(self.__backuppath, 'tmp')
        os.makedirs(_tmpFolder)

        try:
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

                _entry = self.mBuildExaKmsEntry("", "", "", aClassName=_version)
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
            ebLogWarn("Not able to restore backup.")
            ebLogWarn(e)
            return False

        finally:
            shutil.rmtree(_tmpFolder)

# end of file
