#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exakms.py /main/25 2025/01/07 14:09:31 jesandov Exp $
#
# tests_exakms.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakms.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    08/07/23 - 35683301: Avoid linear search in ExaKmsOCI
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    aararora    01/27/23 - Mock Service Error in OCI
#    jesandov    05/31/22 - Add ExaKms KeyValue Info
#    alsepulv    05/30/22 - Bug 34220048: Ensure corrupted history entry is
#                           ignored
#    alsepulv    05/09/22 - Enh 31861263: Add ExaKmsSIV
#    jesandov    03/24/22 - 33997797 - EXACS: EXAKMS: ADD CACHE TO EXAKMS KEY
#                           MANAGEMENT
#    jesandov    05/05/21 - Creation
#

import oci
import os
import sys
import json
import time
import unittest
from unittest import mock

import subprocess
from unittest.mock import patch

from random import shuffle

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import ebJsonObject

from exabox.exakms.ExaKms import ExaKms, exakms_enable_fetch_clustername_decorator
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType, ExaKmsKeyFormat
from exabox.exakms.ExaKmsOCI import ExaKmsOCI
from exabox.exakms.ExaKmsKeysDB import ExaKmsKeysDB
from exabox.exakms.ExaKmsFileSystem import ExaKmsFileSystem
from exabox.exakms.ExaKmsSIV import ExaKmsSIV
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton
from exabox.exakms.ExaKmsEntryOCI import ExaKmsEntryOCIRSA

class ebTestExaKms(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        self.maxDiff = None

    def mCleanUpKeys(self, aExaKms):

        # Delete all keys
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        for _entry  in _entries:
            aExaKms.mDeleteExaKmsEntry(_entry)

        # Verfify size of exakms entries
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), 0)

        # Reset history
        aExaKms.mResetHistory()
        aExaKms.mSetCache({})
        self.assertEqual(len(aExaKms.mGetHistory()), 0)

    def mImportExportFlow(self, aExaKms):

        # Clean test
        self.mCleanUpKeys(aExaKms)

        # Calculate host list
        _dom0s, _domUs, _cells, _switches = self.mGetClubox().mReturnAllClusterHosts()
        _hostList = _dom0s + _domUs + _cells + _switches

        _hostDict = {}
        _hostDictFiltered = {}

        for _host in _hostList:

            if _host in _domUs:
                _hostDict[_host] = ExaKmsHostType.DOMU
                _hostDictFiltered[_host] = ExaKmsHostType.DOMU
            if _host in _dom0s:
                _hostDict[_host] = ExaKmsHostType.DOM0
                _hostDictFiltered[_host] = ExaKmsHostType.DOM0
            if _host in _cells:
                _hostDict[_host] = ExaKmsHostType.CELL
            if _host in _switches:
                _hostDict[_host] = ExaKmsHostType.SWITCH

        _user = "exatest"

        # Pregenerate keys
        for _host in _hostList:
            _privateKey = aExaKms.mGetEntryClass().mGeneratePrivateKey()
            _entry = aExaKms.mBuildExaKmsEntry(_host, _user, _privateKey)
            _entry.mSetHostType(_hostDict[_host])
            aExaKms.mInsertExaKmsEntry(_entry)

        # Export keys to workdir but only dom0s and domUs
        aExaKms.mSaveEntriesToFolder(self.mGetUtil().mGetOutputDir(), _hostDictFiltered)

        # Verfify size of exakms entries
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), len(_hostDict))
        self.mCleanUpKeys(aExaKms)

        # Import keys from workdir
        _restoreStatus = aExaKms.mRestoreEntriesFromFolder(self.mGetUtil().mGetOutputDir(), _hostDictFiltered)
        self.assertEqual(_restoreStatus['new'], len(_hostDictFiltered))

        # Verfify size of exakms entries
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), len(_hostDictFiltered))

        # Reset keys on folder
        aExaKms.mCleanUpKeysFolder(self.mGetUtil().mGetOutputDir())
        self.mCleanUpKeys(aExaKms)

    def mKeyTypeTest(self):

        get_gcontext().mSetConfigOption('exakms_default_keygen_algorithm', 'ECDSA')
        get_gcontext().mSetRegEntry('exakms_default_keygen_algorithm', 'RSA')

        _exakms = ExaKmsSingleton().mGetExaKms()
        _key = _exakms.mGetEntryClass().mGeneratePrivateKey()

        self.assertTrue(" RSA " in _key)

        get_gcontext().mSetConfigOption('exakms_default_keygen_algorithm', 'ECDSA')
        get_gcontext().mDelRegEntry('exakms_default_keygen_algorithm')

        _exakms = ExaKmsSingleton().mGetExaKms()
        _key = _exakms.mGetEntryClass().mGeneratePrivateKey()

        self.assertTrue(" EC " in _key)

        get_gcontext().mSetConfigOption('exakms_default_keygen_algorithm', 'RSA')
        get_gcontext().mSetRegEntry('exakms_default_keygen_algorithm', 'ECDSA')

        _exakms = ExaKmsSingleton().mGetExaKms()
        _key = _exakms.mGetEntryClass().mGeneratePrivateKey()

        self.assertTrue(" EC " in _key)

        get_gcontext().mSetConfigOption('exakms_default_keygen_algorithm', 'RSA')
        get_gcontext().mDelRegEntry('exakms_default_keygen_algorithm')

        _exakms = ExaKmsSingleton().mGetExaKms()
        _key = _exakms.mGetEntryClass().mGeneratePrivateKey()

        self.assertTrue(" RSA " in _key)


    def mCacheTest(self, aExaKms):

        # Clean keys
        self.mCleanUpKeys(aExaKms)

        # Generate dummy key
        _host = "localhost"
        _user = "oracle"
        _privateKey = aExaKms.mGetEntryClass().mGeneratePrivateKey()

        _entry = aExaKms.mBuildExaKmsEntry(
            _host, _user, _privateKey
        )
        aExaKms.mInsertExaKmsEntry(_entry)

        # Verify the key is inserted and track the time
        _startTime = time.time()

        _entryValid = aExaKms.mGetExaKmsEntry({})
        self.assertEqual(_entryValid.mGetPrivateKey(), _privateKey)

        _firstSearchTime = time.time() - _startTime

        # Do a second fetch of the keys and take the time
        _startTime = time.time()

        _entryValid = aExaKms.mGetExaKmsEntry({})
        self.assertEqual(_entryValid.mGetPrivateKey(), _privateKey)

        _secondSearchTime = time.time() - _startTime

        # Validate that the time of the second time is less than the first time
        self.assertLessEqual(_secondSearchTime, _firstSearchTime*3)

        # Verify the cache entry
        _cache = aExaKms.mGetCache()
        self.assertEqual(_cache[_entry.mGetFQDN()].mGetPrivateKey(), _privateKey)

        # Delete the key and verify the cache
        aExaKms.mDeleteExaKmsEntry(_entry)
        self.assertEqual(aExaKms.mGetCache(), {})

        # Clean up
        self.mCleanUpKeys(aExaKms)


    def mInvalidKeyTest(self, aExaKms):

        # Generate dummy key
        _hostDict = {"localhost": ExaKmsHostType.UNKNOWN}
        _host = "localhost"
        _user = "oracle"

        _privateKey1 = aExaKms.mGetEntryClass().mGeneratePrivateKey()
        _privateKey2 = aExaKms.mGetEntryClass().mGeneratePrivateKey()

        _entry = aExaKms.mBuildExaKmsEntry(_host, _user, _privateKey1)

        _entryInvalid = aExaKms.mBuildExaKmsEntry(_host, _user, _privateKey2)

        with self.assertRaises(Exception):
            _entryInvalid.mSetPrivateKey("0123456789")

        # Same metadata
        self.assertEqual(_entry.mToJsonMinimal(), _entryInvalid.mToJsonMinimal())

        # Different key information
        self.assertNotEqual(_entry.mToJson(), _entryInvalid.mToJson())


    def mValidateHistoryFlow(self, aExaKms):

        # Clean test
        self.mCleanUpKeys(aExaKms)

        # Generate dummy key
        _hostDict = {"localhost": ExaKmsHostType.UNKNOWN}
        _host = "localhost"
        _user = "oracle"

        _privateKey = aExaKms.mGetEntryClass().mGeneratePrivateKey()
        _entry = aExaKms.mBuildExaKmsEntry(_host, _user, _privateKey)
        aExaKms.mInsertExaKmsEntry(_entry)

        self.assertEqual(len(aExaKms.mGetHistoryJson()), 1)

        # Export keys to workdir
        aExaKms.mSaveEntriesToFolder(self.mGetUtil().mGetOutputDir(), _hostDict)

        # Rotate the key three times
        for i in range(0, 3):

            # Delete old
            aExaKms.mDeleteExaKmsEntry(_entry)

            # Create new
            _privateKey = aExaKms.mGetEntryClass().mGeneratePrivateKey()
            _entry = aExaKms.mBuildExaKmsEntry(_host, _user, _privateKey)
            aExaKms.mInsertExaKmsEntry(_entry)

        self.assertEqual(len(aExaKms.mGetHistory()), 3*2 + 2)

        # Insert corrupted entry into history
        if isinstance(aExaKms, ExaKmsKeysDB):

            _oldEntry = aExaKms.mGetHistory()[-1]
            aExaKms.mGetHistory().append(_oldEntry)

            _newEntry = {"operation": _oldEntry["operation"],
                         "exakms": aExaKms.mBuildExaKmsEntry(_host, _user,
                                         _oldEntry["exakms"].mGetPrivateKey())}

            _walletId = _oldEntry["exakms"].mGetWalletId()
            _newEntry["exakms"].mSetWalletId(_walletId[:5] + "\n" + _walletId[5:])
            aExaKms.mGetHistory()[-2] = _newEntry


        # Import keys from workdir
        _restoreStatus = aExaKms.mRestoreEntriesFromFolder(self.mGetUtil().mGetOutputDir(), _hostDict)
        self.assertEquals(_restoreStatus['skip_old'], 1)

        _oldEntry = aExaKms.mGetHistory()[-1]
        with patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mGetPrivateKey', side_effect=oci.exceptions.ServiceError(
            message='Virtual_vault is not fetched yet', code='ServiceUnavailable', status='500',
            headers={'opc-request-id': '906B574075544F08813FDB423C8275AE'})),\
            patch('exabox.exakms.ExaKmsEntryFileSystem.ExaKmsEntryFileSystemRSA.mRestoreFromFile', return_value=True),\
            patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mGetFQDN', return_value='localhost'),\
            patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mGetCryptoClient'),\
            patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mSetPrivateKey'),\
            patch('exabox.exakms.ExaKms.ExaKms.mGetExaKmsEntry', return_value=ExaKmsEntryOCIRSA('localhost', 'opc', 'key')):
            aExaKms.mRestoreEntriesFromFolder(self.mGetUtil().mGetOutputDir(), _hostDict)
            _log_msg = "OCI service is currently unavailable. Not updating kms entry."
            _log_dir = self.mGetUtil().mGetOutputDir()
            _find_match = subprocess.Popen(['grep','-c', _log_msg, os.path.join(_log_dir, 'exacloud.log')],
                                           shell=False, stdout=subprocess.PIPE)
            _find_output, _ = _find_match.communicate()
            _number_match_lines = int(_find_output.decode('ascii').strip())
            self.assertGreater(_number_match_lines, 0)

        # Validate last key is the last after updates
        _cparam = {"FQDN": _host, "user": _user}
        _regEntry = aExaKms.mGetExaKmsEntry(_cparam, aRefreshKey=True)

        self.assertEqual(_entry.mGetPrivateKey(), _regEntry.mGetPrivateKey())

        # Validate json
        _origJson = _regEntry.mToJsonMinimal()
        _newJson = _entry.mToJsonMinimal()

        del _origJson['creationTime']
        del _newJson['creationTime']

        del _origJson['label']
        del _newJson['label']

        del _origJson['exacloud_host']
        del _newJson['exacloud_host']

        self.assertEqual(_origJson, _newJson)

        # Clean test
        aExaKms.mCleanUpKeysFolder(self.mGetUtil().mGetOutputDir())
        self.mCleanUpKeys(aExaKms)

    def mCommonFlow(self, aExaKms):

        # clean test
        self.mCleanUpKeys(aExaKms)

        # Generate private key
        _privateKey = aExaKms.mGetEntryClass().mGeneratePrivateKey()
        _hostname = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _user = "root"

        #No key at the begin
        _cparam = {"FQDN": _hostname, "user": _user}
        _regEntry = aExaKms.mGetExaKmsEntry(_cparam, aRefreshKey=True)
        self.assertEqual(_regEntry, None)

        # Add new KMS Entry
        _entry = aExaKms.mBuildExaKmsEntry(_hostname, _user, _privateKey)
        aExaKms.mInsertExaKmsEntry(_entry)

        #Verify Entries
        _cparam = {"FQDN": _hostname, "user": _user}
        _verifyEntry = aExaKms.mGetExaKmsEntry(_cparam, aRefreshKey=True)

        _origJson = _verifyEntry.mToJson()
        _newJson = _entry.mToJson()

        del _origJson['creationTime']
        del _newJson['creationTime']

        del _origJson['label']
        del _newJson['label']

        del _origJson['exacloud_host']
        del _newJson['exacloud_host']

        self.assertEqual(_origJson, _newJson)

        # Verify public key of new key
        _readEntry = aExaKms.mGetExaKmsEntry(_cparam, aRefreshKey=True)
        self.assertNotEqual(_readEntry.mGetPublicKey(), str(None))
        self.assertEqual(_readEntry.mGetPublicKey(), _verifyEntry.mGetPublicKey())

        # Verfify size of exakms entries
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), 1)

        # Delete KMS Entry
        aExaKms.mDeleteExaKmsEntry(_entry)

        _cparam = {"FQDN": _hostname, "user": _user}
        _entry = aExaKms.mGetExaKmsEntry(_cparam, aRefreshKey=True)
        self.assertEqual(_entry, None)

        # Test new private key
        _entry = aExaKms.mBuildExaKmsEntry(_hostname, _user, _privateKey)
        aExaKms.mInsertExaKmsEntry(_entry)

        _newPriv = aExaKms.mGetEntryClass().mGeneratePrivateKey()
        _entry.mSetPrivateKey(_newPriv)

        aExaKms.mDeleteExaKmsEntry(_entry)
        aExaKms.mInsertExaKmsEntry(_entry)

        _cparam = {"FQDN": _hostname, "user": _user}
        _storedEntry = aExaKms.mGetExaKmsEntry(_cparam, aRefreshKey=True)

        _j1 = _entry.mToJson()
        _j2 = _storedEntry.mToJson()

        for _key in _j1:

            if _key in ["creationTime", "label", "exacloud_host"]:
                continue

            self.assertEqual(_j1[_key], _j2[_key])

        # Clean test
        self.mCleanUpKeys(aExaKms)

    def mTestEncryptDecryptKeysDB(self, aExaKmsKeysDB):

        self.assertTrue(isinstance(aExaKmsKeysDB, ExaKmsKeysDB))

        _pkey = aExaKmsKeysDB.mGetEntryClass().mGeneratePrivateKey()
        _entry1 = aExaKmsKeysDB.mBuildExaKmsEntry("fqdn", "user", _pkey)
        _entry1.mSetPkDB("fqdn")

        _enc = {
            "x": json.dumps({
                "encData": json.dumps(_entry1.mGetEncData())
            })
        }

        _enc = json.loads(json.loads(_enc["x"])["encData"])

        _entry2 = aExaKmsKeysDB.mBuildExaKmsEntry("fqdn", "user", "")
        _entry2.mSetPkDB("fqdn")
        _entry2.mSetEncData(_enc)

        self.assertEqual(_entry1.mGetPrivateKey(), _entry2.mGetPrivateKey())

    def mKeyValueTest(self, aExaKms):

        # Clean Test
        self.mCleanUpKeys(aExaKms)

        # Generate private key
        _privateKey = aExaKms.mGetEntryClass().mGeneratePrivateKey()
        _hostname = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _user = "root"

        # Add new KMS Entry
        _entry = aExaKms.mBuildExaKmsEntry(_hostname, _user, _privateKey)
        aExaKms.mInsertExaKmsEntry(_entry)

        #Verify Entries
        _cparam = {"FQDN": _hostname, "user": _user}
        _storedEntry = aExaKms.mGetExaKmsEntry(_cparam, aRefreshKey=True)
        self.assertEqual(_storedEntry.mGetKeyValueInfo(), {})

        # Update Key Value
        _storedEntry.mGetKeyValueInfo()["X"] = "A"
        _storedEntry.mGetKeyValueInfo()["Y"] = "B"

        aExaKms.mUpdateKeyValueInfo(_storedEntry)

        # Verify stored info
        _modifyEntry = aExaKms.mGetExaKmsEntry(_cparam, aRefreshKey=True)
        self.assertEqual(_modifyEntry.mGetKeyValueInfo()["X"], "A")
        self.assertEqual(_modifyEntry.mGetKeyValueInfo()["Y"], "B")
        self.assertEqual(_modifyEntry.mGetCreationTime(), _storedEntry.mGetCreationTime())

        # Remove Key from Key Value
        del _modifyEntry.mGetKeyValueInfo()["X"]
        aExaKms.mUpdateKeyValueInfo(_modifyEntry)

        # Verify stored info
        _lastEntry = aExaKms.mGetExaKmsEntry(_cparam, aRefreshKey=True)
        self.assertTrue("X" not in _lastEntry.mGetKeyValueInfo().keys())
        self.assertEqual(_lastEntry.mGetKeyValueInfo()["Y"], "B")
        self.assertEqual(_lastEntry.mGetCreationTime(), _storedEntry.mGetCreationTime())

    @exakms_enable_fetch_clustername_decorator
    def mIgnoreMigrateOldFormat(self, aExaKms):

        get_gcontext().mSetConfigOption('exakms_migrate', 'False')

        # Clean Test
        self.mCleanUpKeys(aExaKms)
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), 0)

        # Generate hostname
        _clustername = "scaqab01adm0102clu7"
        _hostmap = self.mGetClubox().mGetExaKmsHostMap()
        _totalEntries = 0

        for _host, _type in _hostmap.items():

            if _type not in [ExaKmsHostType.DOMU, ExaKmsHostType.CELL, ExaKmsHostType.UNKNOWN]:
                continue

            _entry = aExaKms.mBuildExaKmsEntry(
                _host, "exatest", aExaKms.mGetEntryClass().mGeneratePrivateKey()
            )

            # Insert additional data
            if "ExaKmsEntryKeysDB" in _entry.mGetVersion():
                _entry.mSetPkDB(_clustername)

            elif "ExaKmsEntryOCI" in _entry.mGetVersion():
                _entry.mSetObjectName(_clustername)

            elif "ExaKmsEntrySIV" in _entry.mGetVersion():
                _entry.mSetSecretName(_clustername)

            else:
                self.assertTrue("ExaKmsEntry" in _entry.mGetVersion())

            _totalEntries += 1

            aExaKms.mInsertExaKmsEntry(_entry)

        # Verify that the names on the db is the same as clustername
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), _totalEntries)

        for _entry in _entries:

            if "ExaKmsEntryKeysDB" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetPkDB(), _clustername)

            elif "ExaKmsEntryOCI" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetObjectName(), _clustername)

            elif "ExaKmsEntrySIV" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetSecretName(), _clustername)

        # After import/export flow the keys are in the same format
        aExaKms.mSaveEntriesToFolder(self.mGetUtil().mGetOutputDir(), _hostmap)
        _restoreStatus = aExaKms.mRestoreEntriesFromFolder(self.mGetUtil().mGetOutputDir(), _hostmap)
        self.assertEqual(_restoreStatus['update'], 0)

        # Verify that the names on the db is the same as clustername
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), _totalEntries)

        for _entry in _entries:

            if "ExaKmsEntryKeysDB" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetPkDB(), _clustername)

            elif "ExaKmsEntryOCI" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetObjectName(), _clustername)

            elif "ExaKmsEntrySIV" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetSecretName(), _clustername)

        # After run it again, there would not be changes
        aExaKms.mSaveEntriesToFolder(self.mGetUtil().mGetOutputDir(), _hostmap)
        _restoreStatus = aExaKms.mRestoreEntriesFromFolder(self.mGetUtil().mGetOutputDir(), _hostmap)
        self.assertEqual(_restoreStatus['already_correct'], len(_entries))

        # Clean Up
        aExaKms.mCleanUpKeysFolder(self.mGetUtil().mGetOutputDir())

        get_gcontext().mSetConfigOption('exakms_migrate', 'True')

    @exakms_enable_fetch_clustername_decorator
    def mMigrateOldFormat(self, aExaKms):

        # Clean Test
        self.mCleanUpKeys(aExaKms)

        # Generate hostname
        _clustername = "scaqab01adm0102clu7"
        _hostmap = self.mGetClubox().mGetExaKmsHostMap()
        _totalEntries = 0

        for _host, _type in _hostmap.items():

            if _type not in [ExaKmsHostType.DOMU, ExaKmsHostType.CELL]:
                continue

            _entry = aExaKms.mBuildExaKmsEntry(
                _host, "exatest", aExaKms.mGetEntryClass().mGeneratePrivateKey()
            )

            # Insert additional data
            if "ExaKmsEntryKeysDB" in _entry.mGetVersion():
                _entry.mSetPkDB(_clustername)

            elif "ExaKmsEntryOCI" in _entry.mGetVersion():
                _entry.mSetObjectName(_clustername)

            elif "ExaKmsEntrySIV" in _entry.mGetVersion():
                _entry.mSetSecretName(_clustername)

            _totalEntries += 1
            aExaKms.mInsertExaKmsEntry(_entry)

        # Verify that the names on the db is the same as clustername
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), _totalEntries)

        for _entry in _entries:

            if "ExaKmsEntryKeysDB" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetPkDB(), _clustername)

            elif "ExaKmsEntryOCI" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetObjectName(), _clustername)

            elif "ExaKmsEntrySIV" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetSecretName(), _clustername)

        # After import/export flow the keys are now in FQDN format
        aExaKms.mSaveEntriesToFolder(self.mGetUtil().mGetOutputDir(), _hostmap)
        _restoreStatus = aExaKms.mRestoreEntriesFromFolder(self.mGetUtil().mGetOutputDir(), _hostmap)
        self.assertEqual(_restoreStatus['update'], len(_entries))

        # Verify that the names on the db is the same as clustername
        _entries = aExaKms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), _totalEntries)

        for _entry in _entries:

            if "ExaKmsEntryKeysDB" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetPkDB(), _entry.mGetFQDN())

            elif "ExaKmsEntryOCI" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetObjectName(), _entry.mGetFQDN())

            elif "ExaKmsEntrySIV" in _entry.mGetVersion():
                self.assertEqual(_entry.mGetSecretName(), _entry.mGetFQDN())

        # After run it again, there would not be changes
        aExaKms.mSaveEntriesToFolder(self.mGetUtil().mGetOutputDir(), _hostmap)
        _restoreStatus = aExaKms.mRestoreEntriesFromFolder(self.mGetUtil().mGetOutputDir(), _hostmap)
        self.assertEqual(_restoreStatus['already_correct'], len(_entries))

        # Clean Up
        aExaKms.mCleanUpKeysFolder(self.mGetUtil().mGetOutputDir())
        self.mCleanUpKeys(aExaKms)

    def mMultipleInstanceTest(self, aKmsType):

        # Create instances
        _worker1 = aKmsType()
        _worker2 = aKmsType()

        # Clean up the keys
        self.mCleanUpKeys(_worker1)
        self.mCleanUpKeys(_worker2)

        # Create different key in both workers
        _host = "localhost"
        _user = "exatest"

        # Rotate the key three times to stress the test
        # and validate that exakms always use the latest key
        for i in range(0, 3):

            _privateKey1 = _worker1.mGetEntryClass().mGeneratePrivateKey()
            _entry = _worker1.mBuildExaKmsEntry(_host, _user, _privateKey1)
            _worker1.mInsertExaKmsEntry(_entry)

            _privateKey2 = _worker2.mGetEntryClass().mGeneratePrivateKey()
            _entry = _worker2.mBuildExaKmsEntry(_host, _user, _privateKey2)
            _worker2.mInsertExaKmsEntry(_entry)

            # Get both keys
            _cparams = {"FQDN": _host, "user": _user}
            _w1Entry = _worker1.mGetExaKmsEntry(_cparams, aRefreshKey=True)
            _w2Entry = _worker2.mGetExaKmsEntry(_cparams, aRefreshKey=True)

            # Validate is the same one since ExaKms needs to store the last one
            self.assertEqual(_w2Entry.mGetPrivateKey(), _privateKey2)
            self.assertEqual(_w1Entry.mGetPrivateKey(), _w2Entry.mGetPrivateKey())

        # Clean up the keys
        self.mCleanUpKeys(_worker1)


    def test_000_test_interface(self):

        get_gcontext().mSetConfigOption('exakms_migrate', 'True')

        _exakms = ExaKms()

        with self.assertRaises(NotImplementedError):
            _exakms.mSearchExaKmsEntries({}, aRefreshKey=True)

        with self.assertRaises(NotImplementedError):
            _cparam = {"FQDN":  "", "user": ""}
            _entry = _exakms.mGetExaKmsEntry(_cparam, aRefreshKey=True)

    def test_001_exakms_fs(self):

        # Start the test with RSA
        get_gcontext().mSetConfigOption('exakms_default_keygen_algorithm', 'RSA')

        _exakms = ExaKmsFileSystem()
        _exakms.mGetDefaultKeyFormat()

        # Force PKCS8 format and Traditional on RSA
        self.mCommonFlow(_exakms)

        _exakms.mSetDefaultKeyFormat(ExaKmsKeyFormat.PKCS8)
        self.mImportExportFlow(_exakms)
        _exakms.mSetDefaultKeyFormat(ExaKmsKeyFormat.TRADITIONAL_OPENSSL)
        self.mImportExportFlow(_exakms)

        get_gcontext().mSetConfigOption('exakms_default_keygen_algorithm', 'ECDSA')

        # Continue the rest of test with ECDSA
        self.mCommonFlow(_exakms)

        _exakms.mSetDefaultKeyFormat(ExaKmsKeyFormat.PKCS8)
        self.mImportExportFlow(_exakms)
        _exakms.mSetDefaultKeyFormat(ExaKmsKeyFormat.TRADITIONAL_OPENSSL)
        self.mImportExportFlow(_exakms)

        self.mInvalidKeyTest(_exakms)
        self.mKeyValueTest(_exakms)
        self.mValidateHistoryFlow(_exakms)
        self.mCacheTest(_exakms)
        self.mMultipleInstanceTest(ExaKmsFileSystem)

    def test_002_exakms_keysdb(self):

        get_gcontext().mSetConfigOption('exakms_default_keygen_algorithm', 'ECDSA')

        _basepath = os.path.abspath(self.mGetUtil().mGetOutputDir())

        # Prepare keysdb env
        if not os.path.exists(f"{_basepath}/dbcli/bin/mkstore"):
            os.system(f"mkdir -p {_basepath}/dbcli/")
            os.system(f"unzip packages/wallet_util.zip -d {_basepath}/dbcli/ 2>&1 >/dev/null")

        get_gcontext().mSetRegEntry("MKSTORE_BASEPATH", _basepath)

        _exakms = ExaKmsKeysDB()
        self.mTestEncryptDecryptKeysDB(_exakms)
        self.mCommonFlow(_exakms)
        self.mInvalidKeyTest(_exakms)
        self.mImportExportFlow(_exakms)
        self.mValidateHistoryFlow(_exakms)
        self.mKeyValueTest(_exakms)
        self.mIgnoreMigrateOldFormat(_exakms)
        self.mMigrateOldFormat(_exakms)
        self.mCacheTest(_exakms)
        self.mMultipleInstanceTest(ExaKmsKeysDB)

    def test_003_exakms_oci(self):

        get_gcontext().mSetConfigOption('exakms_default_keygen_algorithm', 'ECDSA')

        if self.mGetClubox().mGetCtx().mCheckConfigOption('kms_dp_endpoint'):

            _exakms = ExaKmsOCI()
            self.mCommonFlow(_exakms)
            self.mInvalidKeyTest(_exakms)
            self.mImportExportFlow(_exakms)
            self.mValidateHistoryFlow(_exakms)
            self.mKeyValueTest(_exakms)
            self.mIgnoreMigrateOldFormat(_exakms)
            self.mCacheTest(_exakms)
            self.mMigrateOldFormat(_exakms)
            self.mMultipleInstanceTest(ExaKmsOCI)

    def test_004_exakms_siv(self):

        get_gcontext().mSetConfigOption('exakms_default_keygen_algorithm', 'RSA')

        if not self.mGetClubox().mGetCtx().mCheckConfigOption("enable_siv",
                                                              "True"):
            return

        _exakms = ExaKmsSIV()
        self.mCommonFlow(_exakms)
        self.mInvalidKeyTest(_exakms)
        self.mImportExportFlow(_exakms)
        self.mValidateHistoryFlow(_exakms)
        self.mKeyValueTest(_exakms)
        self.mIgnoreMigrateOldFormat(_exakms)
        self.mMigrateOldFormat(_exakms)
        self.mCacheTest(_exakms)
        self.mMultipleInstanceTest(ExaKmsSIV)

    def test_100_singleton(self):

        # ExaKms OCI
        if self.mGetClubox().mGetCtx().mCheckConfigOption('kms_dp_endpoint'):
            _singleton = ExaKmsSingleton()

            _exakms = _singleton.mGetExaKms()
            self.assertTrue(isinstance(_exakms, ExaKmsOCI))
            self.mKeyTypeTest()

            get_gcontext().mSetConfigOption('kms_dp_endpoint', '')

        # ExaKms SIV
        if self.mGetClubox().mGetCtx().mCheckConfigOption('enable_siv', 'True'):
            _singleton = ExaKmsSingleton()

            _exakms = _singleton.mGetExaKms()
            self.assertTrue(isinstance(_exakms, ExaKmsSIV))

            get_gcontext().mSetConfigOption('enable_siv', 'False')

        # ExaKms FileSystem
        _singleton = ExaKmsSingleton()

        _exakms = _singleton.mGetExaKms()
        self.assertTrue(isinstance(_exakms, ExaKmsFileSystem))
        self.mKeyTypeTest()

        # ExaKms KeysDB
        _singleton = ExaKmsSingleton()

        get_gcontext().mSetConfigOption('ociexacc', 'True')

        _exakms = _singleton.mGetExaKms()
        self.assertTrue(isinstance(_exakms, ExaKmsKeysDB))
        self.mKeyTypeTest()

        get_gcontext().mSetConfigOption('ociexacc', 'False')

        _exakms = _singleton.mGetExaKms()
        self.assertTrue(isinstance(_exakms, ExaKmsKeysDB))
        self.mKeyTypeTest()



if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
