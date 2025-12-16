#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKms.py /main/32 2025/01/07 14:09:31 jesandov Exp $
#
# ExaKms.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      ExaKms.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    01/06/25 - Add PKCS8 and TraditionalOpenSSL Format export
#    joysjose    08/12/24 - Bug 36283884 - Replace debug logs with trace logs
#    talagusu    07/09/24 - Bug 36572957 - DEFAULT --EXAKMS-KEY-TYPE WHEN
#                           INSERTING KEYS TO OBJECTSTORE
#    jesandov    08/07/23 - 35683301: Create decorators for ExaKms
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    aararora    01/25/23 - When oci service exception is raised, do not delete
#                           old kms entry.
#    aypaul      06/01/22 - Enh#34207528 ExaKms entry history tracking and
#                           generation.
#    jesandov    05/31/22 - Add ExaKms KeyValue Info
#    alsepulv    05/30/22 - Bug 34220048: Skip history entry if corrupted
#    aypaul      05/12/22 - Enh#34127058 Persistent tracking for exakms entries.
#    jesandov    03/24/22 - 33997797 - EXACS: EXAKMS: ADD CACHE TO EXAKMS KEY
#                           MANAGEMENT
#    oespinos    01/20/22 - 33775076 - EXACC GEN2: EXAKMS SHOULD DO A FULL-SYNC
#                           OF KEYSDB
#    alsepulv    08/16/21 - Bug 30993225: Create backup method
#    naps        07/24/21 - move diagnostic messages to trace file.
#    jesandov    04/27/21 - Creation
#

import os
import re
import json
import time
import functools
import uuid
import shlex
import subprocess

from typing import List, Optional, Tuple


from exabox.core.Context import get_gcontext
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType, ExaKmsOperationType, ExaKmsKeyFormat
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogInfo, ebLogTrace
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

##############
# DECORATORS #
##############

def exakms_enable_fetch_clustername_decorator(func):
    @functools.wraps(func)
    def wrapper(*func_args, **func_kwargs):

        try:
            get_gcontext().mSetRegEntry("exakms_enable_fetch_clustername", "True")
            return func(*func_args, **func_kwargs)
        finally:
            if get_gcontext().mCheckRegEntry("exakms_enable_fetch_clustername"):
                get_gcontext().mDelRegEntry("exakms_enable_fetch_clustername")

    return wrapper


###########
# CLASSES #
###########


class ExaKms:

    def __init__(self):
        self.__history = []
        self.__entryClass = ExaKmsEntry
        self.__keysCache = {}
        self.__entryClasses = {}
        self.__exaKmsHistoryInstance = None
        self.__defaultKeyFormat = None

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetDefaultKeyFormat(self):

        if self.__defaultKeyFormat is None:
            self.__defaultKeyFormat = self.mCalculateDefaultKeyFormat()

        return self.__defaultKeyFormat

    def mSetDefaultKeyFormat(self, aValue):
        self.__defaultKeyFormat = aValue

    def mSetExaKmsHistoryInstance(self, exaKmsHistoryInstance):
        self.__exaKmsHistoryInstance = exaKmsHistoryInstance

    def mGetExaKmsHistoryInstance(self):
        return self.__exaKmsHistoryInstance

    def mGetHistory(self):
        return self.__history

    def mGetDefaultKeyAlgorithm(self):

        if "ECDSA" in str(self.mGetEntryClass(aType="DEFAULT")):
            return "ECDSA"

        return "RSA"

    def mGetEntryClass(self, aType="DEFAULT"):

        if "ECDSA" in str(aType):
            return self.mGetEntryClasses()["ECDSA"]

        elif "RSA" in str(aType):
            return self.mGetEntryClasses()["RSA"]

        return self.mGetEntryClasses()["DEFAULT"]

    def mGetEntryClasses(self):
        return self.__entryClasses

    def mSetEntryClass(self, aDict):

        if "ECDSA" not in aDict or \
           "RSA" not in aDict or \
           "DEFAULT" not in aDict:
            raise ValueError(f"Invalid input {aDict}")

        self.__entryClasses = aDict

    def mResetHistory(self):
        self.__history = []

    def mGetCache(self):
        return self.__keysCache

    def mSetCache(self, aValue):
        self.__keysCache = aValue

    def mUpdateCacheKey(self, aFQDN, aEntry):
        self.__keysCache[aFQDN] = aEntry

    #####################
    # INTERFACE METHODS #
    #####################

    def mSearchExaKmsEntries(self, aPatternDict, aRefreshKey=False):
        raise NotImplementedError

    def mDeleteExaKmsEntry(self, aKmsEntry):

        _historyNode = {"operation": ExaKmsOperationType.DELETE, "exakms": aKmsEntry}
        self.mGetHistory().append(_historyNode)

        if aKmsEntry.mGetFQDN() in self.mGetCache():
            del self.mGetCache()[aKmsEntry.mGetFQDN()]

        self.mGetExaKmsHistoryInstance().mPutExaKmsHistory(aKmsEntry, ExaKmsOperationType.DELETE)
        ebLogTrace(f"Deleted {aKmsEntry}")

    def mInsertExaKmsEntry(self, aKmsEntry, aPreservateCreationTime=False):

        _historyNode = {"operation": ExaKmsOperationType.INSERT, "exakms": aKmsEntry}
        self.mGetHistory().append(_historyNode)
        self.mUpdateCacheKey(aKmsEntry.mGetFQDN(), aKmsEntry)

        self.mGetExaKmsHistoryInstance().mPutExaKmsHistory(aKmsEntry, ExaKmsOperationType.INSERT)
        ebLogTrace(f"Inserted {aKmsEntry}")

    def mBuildExaKmsEntry(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN, aClassName=None):
        raise NotImplementedError

    def mBackup(self):
        raise NotImplementedError

    def mRestoreBackup(self):
        raise NotImplementedError

    #################
    # CLASS METHODS #
    #################

    def mCalculateDefaultKeyFormat(self):

        # Execute local ssh-keygen to verify if the key is PKCS#1 or PKCS#8
        _tmpfile = f"/tmp/{str(uuid.uuid1())}"
        _cmd = f'ssh-keygen -t ecdsa -b 384 -m PEM -N "" -q -f {_tmpfile}'
        _rc, _ = self.mExecuteLocal(_cmd)
        _sampleKey = ""

        if _rc == 0:
            with open(_tmpfile, "r") as _f:
                _sampleKey = _f.read()

            os.remove(_tmpfile)

            if "BEGIN PRIVATE KEY" in _sampleKey:
                return ExaKmsKeyFormat.PKCS8

        return ExaKmsKeyFormat.TRADITIONAL_OPENSSL


    def mExecuteLocal(self, aCmd: str) -> Tuple[int, str]:
        """ Executes the command given
        """

        _args = shlex.split(aCmd)
        _proc = subprocess.Popen(_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _stdOut, _ = wrapStrBytesFunctions(_proc).communicate()
        _rc = _proc.returncode

        return _rc, _stdOut
    
    def mCheckSshPrivKeyType(self, aPrivKeyFile):
        _cmd = "ssh-keygen -l -f %s " % aPrivKeyFile
        try:
             _rc, _out = self.mExecuteLocal(_cmd)
             if "RSA" in _out.upper(): 
                 return "RSA"
             elif "ECDSA" in _out.upper() and _out.upper().startswith("384"): 
             # For ECDSA we only support SHA 384
                 return "ECDSA"
             else:
                 return "UNKNOWN"
        except Exception as e:
             ebLogWarn("mCheckSshPrivKeyType: Failed to identify the key type ")
             ebLogWarn(f"Caused by: {e}")
             return "UNKNOWN"
                        


    def mFilterCache(self, aRegexDict):

        _entries = []

        for _fqdn, _entry in self.mGetCache().items():

            if "FQDN" in aRegexDict:

                if "strict" in aRegexDict and aRegexDict['strict']:

                    if not aRegexDict['FQDN'].split(".")[0] == _fqdn.split(".")[0]:
                        continue

                else:

                    if not re.search(aRegexDict['FQDN'], _fqdn):
                        continue

            if "user" in aRegexDict:

                if _entry.mGetUser() != aRegexDict['user']:
                    continue

            _entries.append(_entry)

        return _entries


    def mGetHistoryJson(self):

        _json = []

        for _histNode in self.mGetHistory():

            try:
                _newNode = {}
                _newNode['operation'] = _histNode['operation']
                _newNode['exakms'] = _histNode['exakms'].mToJson()

                _json.append(_newNode)

            except Exception as e:
                ebLogWarn("mGetHistoryJson: Invalid/corrupted entry in ExaKms "
                          "history:")
                ebLogWarn(_histNode['exakms'].mToJsonMinimal())
                ebLogWarn(f"Operation: {_histNode['operation']}")
                ebLogWarn(f"Caused by: {e}")

        return _json

    def mGetFullJson(self):

        _json = []

        for _exaKmsEntry in self.mSearchExaKmsEntries({}, aRefreshKey=True):

            try:
                _newNode = {}
                _newNode['operation'] = ExaKmsOperationType.INSERT
                _newNode['exakms'] = _exaKmsEntry.mToJson()

                _json.append(_newNode)

            except Exception as e:
                ebLogWarn(ExaKmsOperationType.INSERT)
                ebLogWarn(_exaKmsEntry.mToJsonMinimal())
                ebLogWarn(e)

        _json.extend(self.mGetHistoryJson())
        return _json


    def mGetExaKmsEntry(self, aPatternDict, aRefreshKey=False):

        _entries = self.mSearchExaKmsEntries(aPatternDict, aRefreshKey)

        if _entries:
            return _entries[0]

        return None

    def mSaveEntriesToFolder(self, aFolder, aHostDict, aExtraValidationsCallback=None):

        ebLogInfo("Running mSaveEntriesToFolder")

        # Get host list mapped with nat
        _hostDict = {}
        for _host, _type in aHostDict.items():
            _hostDict[ExaKmsEntry.mUnmaskNatHost(_host)] = _type

        # Get all active KMS entries
        for _host, _type in _hostDict.items():

            _cparams = {"FQDN": _host, "strict": True}
            _users = []
            _kmsEntries = self.mSearchExaKmsEntries(_cparams, aRefreshKey=True)

            for _kmsEntry in _kmsEntries:
                _kmsEntry.mSetDefaultKeyFormat(self.mGetDefaultKeyFormat())

                try:

                    if _kmsEntry.mGetUser() in _users:
                        ebLogTrace(f"Already user: {_kmsEntry.mGetUser()}, skip: {_kmsEntry}")
                        continue

                    if aExtraValidationsCallback:
                        if not aExtraValidationsCallback(_kmsEntry):
                            ebLogTrace(f"Extra validation fails, skip: {_kmsEntry}")
                            continue

                    _kmsEntry.mSaveToFile(aFolder)

                    # Add history entry to save the state of the initial keys
                    _historyNode = {"operation": "initial", "exakms": _kmsEntry}
                    self.mGetHistory().append(_historyNode)

                    _users.append(_kmsEntry.mGetUser())

                except Exception as e:
                    ebLogWarn(f"Skip {_kmsEntry} by {e}")


    def mRestoreEntriesFromFolder(self, aFolder, aHostDict, aExtraValidationsCallback=None):

        def mExtendHostType(aKmsEntry, aHostDict):

            for _host, _type in aHostDict.items():

                _nathost = self.mGetEntryClass().mUnmaskNatHost(_host)
                _natNewEntry = self.mGetEntryClass().mUnmaskNatHost(aKmsEntry.mGetFQDN())

                if _natNewEntry.split(".")[0] == _nathost.split(".")[0]:

                    aKmsEntry.mSetFQDN(_nathost)
                    aKmsEntry.mSetHostType(_type)
                    return True

            return False

        def mKeyfileInHostDict(aFileName, aHostDict):

            for _host, _type in aHostDict.items():

                _nathost = self.mGetEntryClass().mUnmaskNatHost(_host)

                if _nathost.split(".")[0] in aFileName:
                    return True

            return False


        ebLogTrace("Running mRestoreEntriesFromFolder")

        # Get all files from the target folder
        _history = self.mGetHistory()
        _files = os.listdir(aFolder)

        _migrate = get_gcontext().mCheckConfigOption("exakms_migrate", "True")

        _metrics = {
            "new": 0,
            "update": 0,
            "skip_old": 0,
            "already_correct": 0,
            "skip_extra": 0,
        }

        for _file in _files:

            if not mKeyfileInHostDict(_file, aHostDict):
                ebLogTrace(f"Skip file {_file} since is not present in XML")
                continue

            _keyFile = os.path.join(aFolder, _file)

            _className = "RSA"
            if "ecdsa" in str(_file).lower():
                _className = "ECDSA"

            if "id_" in _keyFile and os.path.isfile(_keyFile):
                with open(_keyFile, "r") as _f:
                    _content = _f.read()
                    if "RSA" in _content:
                        _className = "RSA"
                    elif " EC " in _content:
                        _className = "ECDSA"

            # Load the file
            _kmsEntryNew = self.mBuildExaKmsEntry(None, None, None, aClassName=_className)

            _isExaKmsFile = _kmsEntryNew.mRestoreFromFile(_keyFile)

            if not _isExaKmsFile:
                ebLogTrace(f"Skip file {_file} since is not an valid key (1)")
                continue

            # Extend information about the hostname and type
            if not mExtendHostType(_kmsEntryNew, aHostDict):
                ebLogTrace(f"Skip file {_file} since is not part of the XML clusters")
                continue

            # Validate key is correct
            try:
                _kmsEntryNew.mGetPrivateKey()
            except:
                ebLogTrace(f"Skip file {_file} since is not an valid key (2)")
                continue

            if aExtraValidationsCallback:

                if not aExtraValidationsCallback(_kmsEntryNew):
                    ebLogTrace(f"Skip file {_file} since Extra validation fails")
                    ebLogInfo(f"Extra validation fails, skip: {_kmsEntryNew}")
                    _metrics['skip_extra'] += 1
                    continue

            # Update KMS entry
            _kmsEntryOld = self.mGetExaKmsEntry(_kmsEntryNew.mGetUniqJSON())

            if _kmsEntryOld:

                try:
                    _kmsEntryOld.mGetPrivateKey()
                except Exception as ex:

                    """ When oci service is unavailable, following error is raised:
                    {'opc-request-id': '906B574075544F08813FDB423C8275AE', 'code': 'ServiceUnavailable',
                    'message': 'Virtual_vault is not fetched yet', 'status': 500}
                    """
                    ebLogWarn(f"mRestoreEntriesFromFolder - Exception raised is {ex}.")
                    if "ServiceUnavailable" in str(ex):
                        ebLogError("OCI service is currently unavailable. Not updating kms entry.")
                        continue
                    self.mDeleteExaKmsEntry(_kmsEntryOld)
                    self.mInsertExaKmsEntry(_kmsEntryNew)
                    _metrics['update'] += 1
                    ebLogTrace(f"Updated {_kmsEntryNew}")

                    continue

                mExtendHostType(_kmsEntryOld, aHostDict)

                if _kmsEntryOld.mGetPrivateKey() != _kmsEntryNew.mGetPrivateKey() or \
                   ((_kmsEntryOld.mGetIndexId() != _kmsEntryNew.mGetIndexId()) and _migrate):

                    # review if key in history
                    _inHistory = False
                    for _hist in _history:

                        if _hist["exakms"].mGetFQDN() == _kmsEntryNew.mGetFQDN():

                            try:
                                if _migrate:

                                    if (_hist['exakms'].mGetIndexId() == _kmsEntryNew.mGetIndexId()
                                              and _hist["exakms"].mGetPrivateKey() == _kmsEntryNew.mGetPrivateKey()):
                                        _inHistory = True
                                        break

                                else:
                                    if _hist['exakms'].mGetPrivateKey() == _kmsEntryNew.mGetPrivateKey():
                                        _inHistory = True
                                        break

                            except Exception as e:
                                ebLogWarn("mRestoreEntriesFromFolder: Invalid/"
                                          "corrupted entry in ExaKms history:")
                                ebLogWarn(_hist['exakms'].mToJsonMinimal())
                                ebLogWarn(f"Operation: {_hist['operation']}")
                                ebLogWarn(f"Caused by: {e}")

                    if _inHistory:
                        _metrics['skip_old'] += 1
                        ebLogTrace(f"Try to update old entry, skip {_kmsEntryNew}")

                    else:
                        self.mDeleteExaKmsEntry(_kmsEntryOld)
                        self.mInsertExaKmsEntry(_kmsEntryNew)
                        _metrics['update'] += 1
                        ebLogTrace(f"Updated {_kmsEntryNew}")

                else:
                    _metrics['already_correct'] += 1
                    ebLogTrace(f"Already Correct {_kmsEntryNew}")

            else:
                self.mInsertExaKmsEntry(_kmsEntryNew)
                ebLogTrace(f"Created New {_kmsEntryNew}")
                _metrics['new'] += 1

        return _metrics

    def mUpdateKeyValueInfo(self, aExaKmsEntry):

        ebLogTrace(f"Running mUpdateKeyValue of {aExaKmsEntry}")
        aExaKmsEntry.mGetKeyValueInfo()["EXAKMS_KV_LAST_UPDATE"] = self.__entryClass.mGetCurrentTime()

        self.mDeleteExaKmsEntry(aExaKmsEntry)
        self.mInsertExaKmsEntry(aExaKmsEntry, aPreservateCreationTime=True)

    def mCleanUpKeysFolder(self, aFolder, aHostDict=None):

        if not os.path.isdir(aFolder):
            return

        # Get all files from the taget folder
        _files = os.listdir(aFolder)
        _hostList = None

        if aHostDict:
            _hostList = list(map(lambda x: x.split(".")[0], aHostDict.keys()))

        for _keyfile in _files:

            # Find all the keys that belong to that host
            _remove = False

            if _keyfile.startswith("id_rsa") or _keyfile.startswith("id_ecdsa"):

                if _hostList:

                    try:

                        _host = _keyfile.split(".")[1]
                        if _host in _hostList:
                            _remove = True

                    except IndexError:
                        pass

                else:
                    _remove = True

            if _remove:
                os.remove(os.path.join(aFolder, _keyfile))



# end of file
