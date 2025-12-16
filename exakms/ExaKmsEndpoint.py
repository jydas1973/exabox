#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsEndpoint.py /main/26 2025/01/07 14:09:31 jesandov Exp $
#
# ExaKmsEndpoint.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsEndpoint.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    01/06/25 - Add PKCS8 and TraditionalOpenSSL Format export
#    jfsaldan    11/08/24 - Bug 37239457 - EXACLOUD EXACC FEDRAMP ; FS
#                           ENCRYPTION PASSPHRASE ARE NOT SYNCED PROPERLY
#                           ACROSS CPSES
#    ririgoye    10/15/24 - Backport 37176061 of ririgoye_bug-37076081 from
#                           main
#    ririgoye    10/11/24 - Bug 37160664 - BACKPORT OF BUG 37076081
#    ririgoye    10/14/24 - Bug 37076081 - Created function to sync exakv.db
#    oespinos    09/09/24 - Bug 37034316 - ExaKms mSyncKeys copying ECDSA keys as RSA
#    talagusu    05/15/24 - Bug 36572957 - DEFAULT --EXAKMS-KEY-TYPE WHEN
#                           INSERTING KEYS TO OBJECTSTORE
#    ririgoye    09/18/23 - Bug 35819018 - EXAMS DOWNLOAD OF A SINGLE KEY FAILS
#                           WITH TYPEERROR: EXPECTED STR, BYTES OR OS.PATHLIKE
#                           OBJECT, NOT NONETYPE
#    jesandov    06/26/23 - 35526748: Do not raise and exception in case of rotate keys
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    jesandov    03/31/23 - 35241327: Enable Cross Save between ExaKms
#                           Implementations
#    aypaul      06/07/22 - Enh#34207528 ExaKms entry history tracking and
#                           generation.
#    jesandov    05/31/22 - Add ExaKms KeyValue Info
#    oespinos    05/06/22 - 34100125 - CREATE VM CLUSTER REQUEST IS STUCK IN ADD SSHKEY
#    oespinos    01/25/22 - 33789303 - Add command to execute full-sync of
#                           keys.db
#    alsepulv    09/01/21 - Bug 30993225: Add mBackup and mRestoreBackup
#    jesandov    06/02/21 - Creation
#

import os
import json

from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType, ExaKmsOperationType, ExaKmsKeyFormat
from exabox.agent.ebJobRequest import nsOpt 
from exabox.agent.Client import ebExaClient
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton
from exabox.utils.node import connect_to_host, node_exec_cmd_check, node_exec_cmd
from exabox.exakms.ExaKmsOCI import ExaKmsOCI
from exabox.exakms.ExaKmsKVDB import ExaKmsKVDB
from exabox.kms.crypt import cryptographyAES_CBC

class ExaKmsEndpoint:

    def __init__(self, aOptions):
        self.__options = aOptions
        self.__exakms = get_gcontext().mGetExaKms()

    def mGetExaKms(self):
        return self.__exakms

    def mSetExaKms(self, aValue):
        self.__exakms = aValue

    def mExecute(self):

        if "cmd" not in self.__options:
            ebLogError(f"'cmd' not found on options")
            return 1

        _cmd = self.__options.pop("cmd")

        if _cmd == "list-old-format":
            self.mListOldFormat()
            return 0

        if _cmd == "migrate-old-format":
            self.mMigrateOldFormat()
            return 0

        if _cmd == "migrate-cbc":
            self.mMigrateCBC()
            return 0

        if _cmd == "cross":
            return self.mCrossSave()

        if _cmd == "sync":
            return self.mSyncKeys()

        if _cmd == "full-sync":
            return self.mSyncKeysSend(aFullSync=True)

        if _cmd == "kvdb_sync":
            return self.mSyncKVDB()

        if _cmd == "backup":
            return self.mBackupKeys()
        if _cmd == ExaKmsOperationType.INSERT:
            return self.mInsertKey()

        if _cmd == "restore":
            return self.mRestoreKeys()

        if _cmd == "rotate":
            return self.mRotateKey()

        if _cmd == "download":
            return self.mDownloadKey()

        if _cmd == ExaKmsOperationType.DELETE:
            return self.mDeleteKey()

        return 127


    def mSearchExaKmsEntry(self, aFQDN, aUser, aHash=None):

        # Search the key
        _exakms = self.mGetExaKms()
        _cparams = {
            "FQDN": aFQDN,
            "user": aUser
        }

        _entries = _exakms.mSearchExaKmsEntries(_cparams)
        _foundEntry = None

        for _entry in _entries:

            if not aHash:
                _foundEntry = _entry
                break

            try:

                _entry.mGetPrivateKey()
                if _entry.mGetHash() == aHash:
                    _foundEntry = _entry
                    break

            except:
                continue

        if not _foundEntry:
            _cparams['hash'] = self.__options['exakms_keyhash']
            ebLogError(f"Could not search exakms with params {_cparams}")

        return _foundEntry

    def mDownloadKey(self):

        # Validate command line options
        _mandatories = [
            "exakms_fqdn",
            "exakms_user",
            "exakms_privatekey_file",
            "exakms_privatekey_format"
        ]

        for _mandatory in _mandatories:
            if _mandatory not in self.__options or not self.__options[_mandatory]:
                ebLogError(f"'{_mandatory}' not found on options")
                return 1

        _entry = self.mSearchExaKmsEntry(
            self.__options['exakms_fqdn'],
            self.__options['exakms_user']
        )

        if _entry:

            _file = os.path.abspath(self.__options.get('exakms_privatekey_file'))

            if self.__options.get('exakms_privatekey_format') == "PKCS8":
                _entry.mSetDefaultKeyFormat(ExaKmsKeyFormat.PKCS8)
            else:
                _entry.mSetDefaultKeyFormat(ExaKmsKeyFormat.TRADITIONAL_OPENSSL)

            _entry.mSaveToFile("/tmp", _file)
            ebLogInfo(f"Saved private key: {_file}")

            _kvFile = self.__options.get("exakms_key_value_info")

            if not _kvFile:
                ebLogWarn(f"Skipping file '{_kvFile}' since it wasn't found on options.")
                return 0

            with open(_kvFile, "w") as _f:
                _f.write(json.dumps(_entry.mGetKeyValueInfo()))

            ebLogInfo(f"Saved key value info in: {_kvFile}")

            return 0

        return 1

    def mMigrateOldFormat(self):

        _statics = {
            "total": 0,
            "correct": 0,
            "corrupted": 0,
            "duplicated": 0,
            "migrated": 0
        }

        _exakms = self.mGetExaKms()

        if not isinstance(_exakms, ExaKmsOCI):
            ebLogInfo("This command only work with ExaKmsOCI")

        _alreadyCorrect = []

        ebLogInfo("Fetching all SSH Keys, this could take a while")
        _entries = _exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        _entries = sorted(_entries, key=lambda x: x.mGetCreationTime(), reverse=True)

        for _entry in _entries:

            _statics["total"] += 1

            _map = {
                "fqdn": _entry.mGetFQDN().split(".")[0],
                "user": _entry.mGetUser()
            }

            if _map in _alreadyCorrect:
                ebLogInfo(f"Key duplicated: {_entry.mToJsonMinimal()}")
                _exakms.mDeleteExaKmsEntry(_entry)
                _statics["duplicated"] += 1
                continue

            _idx = _entry.mGetIndexId()
            _host = _entry.mGetFQDN()

            if "FileSystem" not in _entry.mGetVersion():
                _host = f"{_entry.mGetFQDN()}/{_entry.mGetFQDN()}"

            if _entry.mGetUser() not in ["root", "opc", "oracle", "grid", "ilom", "admin", "ilom-admin", "admin-ilom"]:
                ebLogInfo(f"Found corrupted entry: {_entry.mToJsonMinimal()}")
                _exakms.mDeleteExaKmsEntry(_entry)
                _statics["corrupted"] += 1
                continue

            if _host != _idx or _entry.mGetHostType() == ExaKmsHostType.UNKNOWN:

                ebLogInfo(f"Found old format entry: {_idx} in {_entry.mToJsonMinimal()}")
                _exakms.mDeleteExaKmsEntry(_entry)

                _newEntry = _exakms.mBuildExaKmsEntry(
                    _entry.mGetFQDN(),
                    _entry.mGetUser(),
                    _entry.mGetPrivateKey(),
                    _entry.mGetHostType()
                )

                if _entry.mGetHostType() == ExaKmsHostType.UNKNOWN:

                    if "cl" in _entry.mGetFQDN().split(".")[0]:
                        _newEntry.mSetHostType(ExaKmsHostType.CELL)

                    elif "dd0" in _entry.mGetFQDN().split(".")[0]:
                        _newEntry.mSetHostType(ExaKmsHostType.DOM0)

                    elif "ddu" in _entry.mGetFQDN().split(".")[0]:
                        _newEntry.mSetHostType(ExaKmsHostType.DOMU)

                    elif "ib" in _entry.mGetFQDN().split(".")[0]:
                        _newEntry.mSetHostType(ExaKmsHostType.SWITCH)

                    else:
                        ebLogInfo(f"Found corrupted entry: {_entry.mToJsonMinimal()}")
                        _statics["corrupted"] += 1
                        continue

                ebLogInfo(f"New Entry: {_newEntry.mToJsonMinimal()}")
                _exakms.mInsertExaKmsEntry(_newEntry)
                _statics["migrated"] += 1

            else:
                ebLogInfo(f"Already correct: {_entry.mToJsonMinimal()}")
                _statics["correct"] += 1

            _alreadyCorrect.append(_map)

        ebLogInfo(f"")
        _statics["uniques"] = len(_alreadyCorrect)
        ebLogInfo(_statics)


    def mMigrateCBC(self):

        _statics = {
            "total": 0,
            "corrupted": 0,
            "migrated": 0
        }

        _exakms = self.mGetExaKms()

        if not isinstance(_exakms, ExaKmsOCI):
            ebLogInfo("This command only work with ExaKmsOCI")

        _decrypter = cryptographyAES_CBC()
        _alreadyCorrect = []

        ebLogInfo("Fetching all SSH Keys, this could take a while")
        _entries = _exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        _entries = sorted(_entries, key=lambda x: x.mGetCreationTime(), reverse=True)

        for _entry in _entries:

            _statics["total"] += 1

            _encryptedKey = _entry.mGetEncData()
            _plainEncryptionKey = _entry.mGetPlainEncryptionKey()

            try:
                _decrypter.mDecrypt(_plainEncryptionKey, _encryptedKey)
                ebLogInfo(f"Found CBC Entry: {_entry.mToJsonMinimal()}")

                _exakms.mDeleteExaKmsEntry(_entry)

                _newEntry = _exakms.mBuildExaKmsEntry(
                    _entry.mGetFQDN(),
                    _entry.mGetUser(),
                    _entry.mGetPrivateKey(),
                    _entry.mGetHostType()
                )

                if _entry.mGetHostType() == ExaKmsHostType.UNKNOWN:

                    if "cl" in _entry.mGetFQDN().split(".")[0]:
                        _newEntry.mSetHostType(ExaKmsHostType.CELL)

                    elif "dd0" in _entry.mGetFQDN().split(".")[0]:
                        _newEntry.mSetHostType(ExaKmsHostType.DOM0)

                    elif "ddu" in _entry.mGetFQDN().split(".")[0]:
                        _newEntry.mSetHostType(ExaKmsHostType.DOMU)

                    elif "ib" in _entry.mGetFQDN().split(".")[0]:
                        _newEntry.mSetHostType(ExaKmsHostType.SWITCH)

                    else:
                        ebLogInfo(f"Found corrupted entry: {_entry.mToJsonMinimal()}")
                        _statics["corrupted"] += 1
                        continue

                ebLogInfo(f"New Entry: {_newEntry.mToJsonMinimal()}")
                _exakms.mInsertExaKmsEntry(_newEntry)
                _statics["migrated"] += 1

            except:
                pass

        ebLogInfo(_statics)


    def mListOldFormat(self):

        _count = 0
        _exakms = self.mGetExaKms()

        ebLogInfo("Fetching all SSH Keys, this could take a while")
        _entries = _exakms.mSearchExaKmsEntries({}, aRefreshKey=True)

        for _entry in _entries:

            _idx = _entry.mGetIndexId()
            _host = _entry.mGetFQDN()

            if "FileSystem" not in _entry.mGetVersion():
                _host = f"{_entry.mGetFQDN()}/{_entry.mGetFQDN()}"

            if _host != _idx:
                ebLogInfo(f"Found old format entry: {_idx} in {_entry.mToJsonMinimal()}")
                _count += 1

        ebLogInfo(f"Total entries found: {_count}")
        return _count

    def mDeleteKey(self):

        # Validate command line options
        _mandatories = [
            "exakms_fqdn",
            "exakms_user",
            "exakms_keyhash"
        ]

        for _mandatory in _mandatories:
            if _mandatory not in self.__options or not self.__options[_mandatory]:
                ebLogError(f"'{_mandatory}' not found on options")
                return 1

        _entry = self.mSearchExaKmsEntry(
            self.__options['exakms_fqdn'],
            self.__options['exakms_user'],
            self.__options['exakms_keyhash']
        )

        if _entry:

            _exakms = self.mGetExaKms()
            _status = _exakms.mDeleteExaKmsEntry(_entry)

            if _status:
                return 0
            else:
                return 1

        return 1


    def mInsertKey(self):

        # Validate command line options
        _mandatories = [
            "exakms_fqdn",
            "exakms_user",
            "exakms_type",
            "exakms_privatekey_file"
        ]

        for _mandatory in _mandatories:
            if _mandatory not in self.__options or not self.__options[_mandatory]:
                ebLogError(f"'{_mandatory}' not found on options")
                return 1

        # Get private key data
        _privateFile = os.path.abspath(self.__options['exakms_privatekey_file'])

        if not os.path.exists(_privateFile):
            ebLogError(f"'{_privateFile}' not found in FileSystem")
            return 1

        _privateData = None
        with open(_privateFile, "r") as _f:
            _privateData = _f.read().strip()

        _keyValueInfo = {}
        if "exakms_key_value_info" in self.__options:

            _kvLocation = self.__options["exakms_key_value_info"]
            if _kvLocation and os.path.exists(_kvLocation):
                with open(_kvLocation, "r") as _f:
                    _keyValueInfo = json.load(_f)

        # Insert key
        _exakms = self.mGetExaKms()

        if self.__options["exakms_key_type"]:
            ebLogDebug("exakms_key_type is specified.")
        else:
            ebLogInfo("exakms_key_type is not specified. checking priv key type")
            priv_key_type = _exakms.mCheckSshPrivKeyType(_privateFile)
            if priv_key_type == "RSA":
                self.__options["exakms_key_type"]="RSA"
            elif priv_key_type == "ECDSA": 
                self.__options["exakms_key_type"]="ECDSA"
            else:
                ebLogError(f" exakms_key_type not found on options")
                return 1


        _entry = _exakms.mBuildExaKmsEntry("", "", "", aClassName=self.__options["exakms_key_type"])

        _entry.mSetFQDN(self.__options['exakms_fqdn'])
        _entry.mSetUser(self.__options['exakms_user'])
        _entry.mSetPrivateKey(ExaKmsEntry.mPrivateKeyToTraditionalFormat(_privateData))
        _entry.mSetHostType(self.__options['exakms_type'])

        if _keyValueInfo:
            _entry.mSetKeyValueInfo(_keyValueInfo)

        _status = _exakms.mInsertExaKmsEntry(_entry)

        if _status:
            return 0
        else:
            return 1

    def mSyncKVDB(self):
        # Check that we have a remote CPS to sync up
        _remoteCps = get_gcontext().mCheckConfigOption('remote_cps_host')

        if not _remoteCps:
            ebLogInfo("No remote host to sync up")
            return 0

        # Check that KVDB history is sent in the payload
        if "history" not in self.__options:
            raise ValueError("No history found on options")

        if not self.__options['history']:
            raise ValueError("'history' not set as an option.")

        # Get ExaKMS object
        _exakms = self.mGetExaKms()

        if not isinstance(_exakms, ExaKmsKVDB):
            _exakms = ExaKmsKVDB()

        for _historyNode in self.__options['history']:

            # Ref 37239457
            # Intention:
            # Create dummy ExaKMS Entry in memory without writing to the Wallet
            # Use that entry to decrypt content received in payload
            # Create a real Wallet Entry with this contents
            # Write the contents to the KV DB file
            _dummy_entry = _exakms.mBuildExaKmsEntry("", "")
            _entryJson = _historyNode.get("exakms")
            _dummy_entry.mFromJson(_entryJson)
            _plaintext = _dummy_entry.mCreateValueFromEncData()
            _new_entry = _exakms.mBuildExaKmsEntry(_entryJson.get(
                'key'), _plaintext)

            _op = _historyNode.get('operation')
            ebLogInfo(f"Requested '{_op}' over {_new_entry.mGetECHostname()}")

            _rc = False
            if _op == ExaKmsOperationType.INSERT:
                _rc = _exakms.mInsertExaKmsEntry(_new_entry)
            elif _op == ExaKmsOperationType.DELETE:
                _key = _entryJson.get('key')
                _rc = _exakms.mDeleteExaKmsEntry(_key)

            ebLogInfo(f"The result was {_rc}")

        return 0

    def mSyncKeys(self):

        if "history" not in self.__options:
            raise ValueError("No history found on options")

        _exakms = self.mGetExaKms()

        if self.__options['history']:
            for _historyNode in self.__options['history']:

                _classname = None
                if 'version' in _historyNode['exakms']:
                    _classname = _historyNode['exakms']['version']

                _entry = _exakms.mBuildExaKmsEntry("", "", "", aClassName=_classname)
                _entry.mFromJson(_historyNode['exakms'])

                _op = _historyNode['operation']

                ebLogInfo(f"Requested '{_op}' over {_entry.mGetUser()}@{_entry.mGetFQDN()}")

                _rc = 0

                if _op == ExaKmsOperationType.DELETE:
                    _rc = _exakms.mDeleteExaKmsEntry(_entry)

                elif _op == ExaKmsOperationType.INSERT:
                    _rc = _exakms.mInsertExaKmsEntry(_entry)

                ebLogInfo(f"The result was {_rc}")

        return 0

    def mSyncKeysSend(self, aFullSync=True):

        _remoteCps = get_gcontext().mCheckConfigOption('remote_cps_host')
        if not _remoteCps:
            ebLogInfo("No remote host to sync up")
            return 0

        _exakms = get_gcontext().mGetExaKms()

        if aFullSync:
            _history = _exakms.mGetFullJson()
        else:
            _history = _exakms.mGetHistoryJson()

        if not _history:
            ebLogInfo("Keys are already updated")
            return 0

        _options = nsOpt({
            "exakms": 'sync',
            "jsonconf": {
                "history": _history
            }
        })

        _client = ebExaClient()
        _client.mSetHostname(_remoteCps)
        _client.mIssueRequest(aOptions=_options)
        _client.mWaitForCompletion()
        _response = _client.mGetJsonResponse()

        if _response['success'] == 'False': #agent doesn't response
            ebLogInfo(f'*** Could not contact Agent on {_remoteCps}')
            return 1
        else:
            _exakms.mResetHistory()

        ebLogInfo(f"Keys sync done with {_remoteCps}")
        return 0

    def mSyncKVDBSend(self):
        # Check for remote CPS
        _remoteCps = get_gcontext().mCheckConfigOption('remote_cps_host')
        if not _remoteCps:
            ebLogInfo("No remote host to sync up")
            return 0
        
        # Get KVDB history
        _exakms = self.mGetExaKms()

        if not isinstance(_exakms, ExaKmsKVDB):
            _exakms = ExaKmsKVDB()

        _history = _exakms.mGetFullJson()

        if not _history:
            ebLogInfo("KVDB is already up-to-date")
            return 0
        
        _options = nsOpt({
            "exakms": 'kvdb_sync',
            "jsonconf": {
                "history": _history
            }
        })

        _client = ebExaClient()
        _client.mSetHostname(_remoteCps)
        _client.mIssueRequest(aOptions=_options)
        _client.mWaitForCompletion()
        _response = _client.mGetJsonResponse()

        if _response['success'] == 'False': #agent doesn't respond
            ebLogInfo(f'*** Could not contact Agent on {_remoteCps}')
            return 1
        else:
            _exakms.mResetHistory()

        ebLogInfo(f"KVDB sync done with {_remoteCps}")
        return 0

    def mRotateKey(self):

        # Validate command line options
        _mandatories = [
            "exakms_fqdn",
            "exakms_key_type",
        ]

        for _mandatory in _mandatories:
            if _mandatory not in self.__options or not self.__options[_mandatory]:
                ebLogError(f"'{_mandatory}' not found on options")
                return 1

        return self.mSingleRotateKey(self.__options["exakms_fqdn"], self.__options["exakms_key_type"], aForce=True)


    def mSingleRotateKey(self, aHost, aClassName=None, aForce=False):

        _cparams = {"FQDN": aHost}
        _entries = self.mGetExaKms().mSearchExaKmsEntries(_cparams, aRefreshKey=True)
        _newEntries = []

        _className = aClassName
        if not _className:
            _className = self.mGetExaKms().mGetDefaultKeyAlgorithm()

        if _entries:

            # Verify the users to migrate
            _users = []
            for _entry in _entries:
                if _className not in _entry.mGetVersion():
                    _users.append(_entry.mGetUser())

            # Migrate all users
            if aForce:
                _users = list(map(lambda x: x.mGetUser(), _entries))

            # Get all the users and generate entries
            for _user in _users:

                _newEntry = self.mGetExaKms().mBuildExaKmsEntry(
                    aHost,
                    _user,
                    self.mGetExaKms().mGetEntryClass(_className).mGeneratePrivateKey(),
                    _entries[0].mGetHostType(),
                    aClassName=_className
                )

                _newEntries.append(_newEntry)

            with connect_to_host(aHost, get_gcontext()) as _node:

                # Insert all the public keys in the /home of the hosts
                for _newEntry in _newEntries:

                    _cmd = f'/bin/echo "{_newEntry.mGetPublicKey()}"'

                    if _newEntry.mGetUser() == "root":
                        _cmd = f'{_cmd} >> /root/.ssh/authorized_keys'
                    else:
                        _cmd = f'{_cmd} >> /home/{_newEntry.mGetUser()}/.ssh/authorized_keys'

                    node_exec_cmd(_node, _cmd)

                # Delete ExaKms Entries
                for _entry in _entries:

                    if _entry.mGetUser() not in _users:
                        continue

                    _cmd = f"/bin/sed -i 's@{_entry.mGetPublicKey().strip()}@@g'"

                    if _entry.mGetUser() == "root":
                        _cmd = f'{_cmd} /root/.ssh/authorized_keys'
                    else:
                        _cmd = f'{_cmd} /home/{_entry.mGetUser()}/.ssh/authorized_keys'

                    node_exec_cmd(_node, _cmd)
                    self.mGetExaKms().mDeleteExaKmsEntry(_entry)

            # Add ExaKms Entries
            for _entry in _newEntries:
                self.mGetExaKms().mInsertExaKmsEntry(_entry)

        return 0

    def mBackupKeys(self):

        _exakms = self.mGetExaKms()
        _suc = _exakms.mBackup()

        if _suc:
            return 0
        else:
            return 1

    def mRestoreKeys(self):

        _exakms = self.mGetExaKms()
        _suc = _exakms.mRestoreBackup()

        if _suc:
            return 0
        else:
            return 1


    def mCrossSave(self):

        # Validate command line options
        _mandatories = [
            "exakms_from",
            "exakms_to"
        ]

        for _mandatory in _mandatories:
            if _mandatory not in self.__options or not self.__options[_mandatory]:
                ebLogError(f"'{_mandatory}' not found on options")
                return 1

        _exakmsFrom = self.__options["exakms_from"]
        _exakmsTo = self.__options["exakms_to"]

        get_gcontext().mSetConfigOption("exakms_type", _exakmsFrom)
        _singleton = ExaKmsSingleton()
        _exakms1 = _singleton.mGetExaKms()

        get_gcontext().mSetConfigOption("exakms_type", _exakmsTo)
        _singleton = ExaKmsSingleton()
        _exakms2 = _singleton.mGetExaKms()

        get_gcontext().mSetConfigOption("exakms_type", None)
        ebLogInfo("Cross Sync operation in progress, this could take a while")

        _entries = _exakms1.mSearchExaKmsEntries({}, aRefreshKey=True)

        for _entry in _entries:

            _newEntry = _exakms2.mBuildExaKmsEntry(
                _entry.mGetFQDN(), 
                _entry.mGetUser(),
                _entry.mGetPrivateKey(),
                aClassName=_entry.mGetVersion()
            )

            _newEntry.mSetHostType(_entry.mGetHostType())
            _exakms2.mInsertExaKmsEntry(_newEntry)

        return 0


# end of file
