#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exakms_endpoints.py /main/25 2025/10/27 12:43:30 aararora Exp $
#
# tests_exakms_endpoints.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakms_endpoints.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    10/14/24 - Bug 37076081 - Added UT for syncing exakv.db file
#    talagusu    07/17/24 - Bug 36572957 - DEFAULT --EXAKMS-KEY-TYPE WHEN
#                           INSERTING KEYS TO OBJECTSTORE
#    naps        06/19/23 - UT case updation for keys removal logic.
#    jesandov    03/31/23 - 35241327: Enable Cross Save between ExaKms
#                           Implementations
#    jesandov    05/31/22 - Add ExaKms KeyValue Info
#    alsepulv    05/09/22 - Enh 31861263: Add ExaKmsSIV
#    jesandov    03/24/22 - 33997797 - EXACS: EXAKMS: ADD CACHE TO EXAKMS KEY
#                           MANAGEMENT
#    oespinos    01/20/22 - 33775076 - EXACC GEN2: EXAKMS SHOULD DO A FULL-SYNC
#                           OF KEYSDB
#    jesandov    01/18/22 - Remove skip unittest
#    alsepulv    10/26/21 - Add backup bucket check before OCI backup endpoint
#    alsepulv    08/31/21 - Bug 30993225: Add test for backup-restore flow
#    jesandov    08/23/21 - Creation
#

import os
import sys
import json
import unittest
import time

from random import shuffle

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import ebJsonObject

from exabox.exakms.ExaKms import ExaKms
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsFileSystem import ExaKmsFileSystem
from exabox.exakms.ExaKmsKeysDB import ExaKmsKeysDB
from exabox.exakms.ExaKmsKVDB import ExaKmsKVDB 
from exabox.exakms.ExaKmsOCI import ExaKmsOCI
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton
from exabox.exakms.ExaKmsSIV import ExaKmsSIV
from exabox.exakms.ExaKmsEndpoint import ExaKmsEndpoint
# Additional imports for new unit tests (kept at top as required)
from unittest import mock
from unittest.mock import Mock, patch
from oci._vendor.urllib3.exceptions import SSLError
from oci.key_management import KmsCryptoClient
from exabox.kms.crypt import cryptographyAES
from exabox.core.Error import ExacloudRuntimeError

class ebTestExaKms(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        super().setUpClass(aGenerateDatabase=True)
        self.exakms = None
        self.exakmsSingleton = None

    def mCleanUpKeys(self, aExaKms=None):

        _exakms = aExaKms
        if not aExaKms:
            _exakms = self.exakms

        # Delete all keys
        _entries = _exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        _entries = _entries if _entries else []

        for _entry in _entries:
            # If this is an ExaKmsKVDB entry, handle differently:
            if not isinstance(_exakms, ExaKmsKVDB):
                _exakms.mDeleteExaKmsEntry(_entry)
                continue
            _json_entry = _entry.mToJson()
            _exakms.mDeleteExaKmsEntry(_json_entry.get('key'))

        # Verify size of exakms entries
        _entries = _exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        _entries = _entries if _entries else []
        self.assertEqual(len(_entries), 0)

        # Reset history
        _exakms.mResetHistory()
        _exakms.mSetCache({})
        self.assertEqual(len(_exakms.mGetHistory()), 0)


    def mExecuteInsertDeleteDownloadEndpoint(self):

        # Clean up keys
        self.mCleanUpKeys()

        # Generate key in workdir
        _user = "root"
        _host = "localhost"
        _pkey = self.exakms.mGetEntryClass(aType="ECDSA").mGeneratePrivateKey()

        _pkeyFile1 = os.path.join(self.mGetUtil().mGetOutputDir(), "example_key1")
        _pkeyFile2 = os.path.join(self.mGetUtil().mGetOutputDir(), "example_key2")
        _keyValueFile1 = os.path.join(self.mGetUtil().mGetOutputDir(), "key_value.json")
        _keyValueFile2 = os.path.join(self.mGetUtil().mGetOutputDir(), "key_value2.json")

        _kvJson = {"X": "Y"}

        with open(_pkeyFile1, "w") as _f:
            _f.write(_pkey)

        with open(_keyValueFile1, "w") as _f:
            _f.write(json.dumps(_kvJson))
        time.sleep(10)

        # Insert key test 1 using endpoint: Success case
        _options = ebJsonObject({
            "cmd": 'insert',
            "exakms_user": _user,
            "exakms_fqdn": _host,
            "exakms_type": "DOMU",
            "exakms_privatekey_file": _pkeyFile1,
            "exakms_key_type": "ECDSA",
            "exakms_key_value_info": _keyValueFile1
        })

        _endpoint = ExaKmsEndpoint(_options)
        _endpoint.mSetExaKms(self.exakms)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        '''
        # Insert key test 2 without using keytype: Success case
        _options = ebJsonObject({
            "cmd": 'insert',
            "exakms_user": _user,
            "exakms_fqdn": _host,
            "exakms_type": "DOMU",
            "exakms_privatekey_file": _pkeyFile1,
            "exakms_key_type": "",
            "exakms_key_value_info": _keyValueFile1
        })

        _endpoint = ExaKmsEndpoint(_options)
        _endpoint.mSetExaKms(self.exakms)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        # Insert key test 3 with wrong keytype: Error case
        _options = ebJsonObject({
            "cmd": 'insert',
            "exakms_user": _user,
            "exakms_fqdn": _host,
            "exakms_type": "DOMU",
            "exakms_privatekey_file": _pkeyFile1,
            "exakms_key_type": "RSA",
            "exakms_key_value_info": _keyValueFile1
        })

        _endpoint = ExaKmsEndpoint(_options)
        _endpoint.mSetExaKms(self.exakms)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 1)

        '''
        # Download key using endpoint
        _options = ebJsonObject({
            "cmd": 'download',
            "exakms_user": _user,
            "exakms_fqdn": _host,
            "exakms_privatekey_format": "TRADITIONAL_OPENSSL",
            "exakms_privatekey_file": _pkeyFile2,
            "exakms_key_value_info": _keyValueFile2
        })

        _endpoint = ExaKmsEndpoint(_options)
        _endpoint.mSetExaKms(self.exakms)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        # Verify same key
        with open(_pkeyFile2, "r") as _f:
            self.assertEqual(_f.read().strip(), _pkey)

        # Verify same key value
        with open(_keyValueFile2, "r") as _f:
            _kvJson2 = json.load(_f)
            self.assertEqual(_kvJson, _kvJson2)

        # Delete the key using endpoint
        _cparams = {"FQDN": _host, "user": _user}
        _entry = self.exakms.mGetExaKmsEntry(_cparams, aRefreshKey=True)

        _options = ebJsonObject({
            "cmd": 'delete',
            "exakms_user": _user,
            "exakms_fqdn": _host,
            "exakms_keyhash": _entry.mGetHash()
        })

        _endpoint = ExaKmsEndpoint(_options)
        _endpoint.mSetExaKms(self.exakms)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        _entry = self.exakms.mGetExaKmsEntry(_cparams, aRefreshKey=True)
        self.assertEqual(_entry, None)

    def mExecuteCrossSaveEndpoint(self, aExaKmsType1, aExaKmsType2):

        # Create ExaKms Instances
        self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', aExaKmsType1)
        _singleton = ExaKmsSingleton()
        _exakms1 = _singleton.mGetExaKms()
        self.mCleanUpKeys(_exakms1)

        self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', aExaKmsType2)
        _singleton = ExaKmsSingleton()
        _exakms2 = _singleton.mGetExaKms()
        self.mCleanUpKeys(_exakms2)

        # Pregenerate keys
        _user = "root"
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            # Create new
            _privateKey = _exakms1.mGetEntryClass().mGeneratePrivateKey()
            _entry = _exakms1.mBuildExaKmsEntry(_dom0, _user, _privateKey)
            _entry.mSetHostType(ExaKmsHostType.DOM0)
            _exakms1.mInsertExaKmsEntry(_entry)


        # Execute cross save
        _options = ebJsonObject({
            "cmd": 'cross',
            "exakms_from": aExaKmsType1,
            "exakms_to": aExaKmsType2,
        })

        _endpoint = ExaKmsEndpoint(_options)
        _endpoint.mSetExaKms(self.exakms)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)


        # Validate number of keys
        _all1 = _exakms1.mSearchExaKmsEntries({}, aRefreshKey=True)
        _all2 = _exakms2.mSearchExaKmsEntries({}, aRefreshKey=True)

        self.assertEqual(len(_all1), len(_all2))


    def mExecuteKmsCluctrlEndpoint(self):

        # Clean up keys
        self.mCleanUpKeys()

        # Pregenerate keys in both formats
        # In fqdn format and in clustername format
        # all with unknown type

        _hostmap = self.mGetClubox().mGetExaKmsHostMap()

        _count = 0
        _countUniq = 0

        for _host, _type in _hostmap.items():

            if _type in [ExaKmsHostType.DOMU, ExaKmsHostType.DOM0]:

                _entry = self.exakms.mBuildExaKmsEntry(
                    _host,
                    "exakms",
                    self.exakms.mGetEntryClass().mGeneratePrivateKey()
                )
                _entry.mSetPkDB(self.mGetClubox().mGetKey())
                self.exakms.mInsertExaKmsEntry(_entry)

                _count += 1
                _countUniq += 1

            if _type in [ExaKmsHostType.DOMU]:

                _entry = self.exakms.mBuildExaKmsEntry(
                    _host,
                    "exakms",
                    self.exakms.mGetEntryClass().mGeneratePrivateKey()
                )
                self.exakms.mInsertExaKmsEntry(_entry)

                _count += 1

        # Validate the number of keys
        _all = self.exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_all), _count)

        # Call the clucontrol endpoint
        self.mGetClubox().mHandlerRefreshExassh()

        # Validate the number of keys and types
        _all = self.exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_all), _countUniq)

        _countDomU = 0
        _countDom0 = 0

        for _entry in _all:

            if _entry.mGetHostType() == ExaKmsHostType.DOMU:
                _countDomU += 1

            if _entry.mGetHostType() == ExaKmsHostType.DOM0:
                _countDom0 += 1

            self.assertEqual(_entry.mGetPkDB(), _entry.mGetFQDN())

        self.assertEqual(_countUniq/2, _countDomU)
        self.assertEqual(_countUniq/2, _countDom0)

    def mExecuteRestoreEndpoint(self):

        # Clean up keys
        self.mCleanUpKeys()

        # Create Mock commands
        _cmds = {
            self.mGetRegexDom0(): [
                [],
                [
                    # Detect XEN
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
                ],
                [
                    exaMockCommand('xm list'),
                ]
            ],
            self.mGetRegexVm(): [
                []
            ],
            self.mGetRegexSwitch(): [
                []
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*ping.*", aRc=1), # DomU
                    exaMockCommand(".*ping.*", aRc=0, aPersist=True), # DomU
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Pregenerate key
        _user = "exakms"
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            # Create new
            _privateKey = self.exakms.mGetEntryClass().mGeneratePrivateKey()
            _entry = self.exakms.mBuildExaKmsEntry(_dom0, _user, _privateKey)
            _entry.mSetHostType(ExaKmsHostType.DOM0)
            self.exakms.mInsertExaKmsEntry(_entry)

            # Create new
            _privateKey = self.exakms.mGetEntryClass().mGeneratePrivateKey()
            _entry = self.exakms.mBuildExaKmsEntry(_domU, _user, _privateKey)
            _entry.mSetHostType(ExaKmsHostType.DOMU)
            self.exakms.mInsertExaKmsEntry(_entry)

        # Import the keys
        self.mGetClubox().mHandlerImportKeys()

        # Rotate Keys
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            # Create new
            _privateKey = self.exakms.mGetEntryClass().mGeneratePrivateKey()
            _entry = self.exakms.mBuildExaKmsEntry(_dom0, _user, _privateKey)
            _entry.mSetHostType(ExaKmsHostType.DOM0)
            self.exakms.mInsertExaKmsEntry(_entry)

            # Create new
            _privateKey = self.exakms.mGetEntryClass().mGeneratePrivateKey()
            _entry = self.exakms.mBuildExaKmsEntry(_domU, _user, _privateKey)
            _entry.mSetHostType(ExaKmsHostType.DOMU)
            self.exakms.mInsertExaKmsEntry(_entry)

        # Export the keys
        self.mGetClubox().mSetCmd("vmgi_install")
        self.mGetClubox().mHandlerExportKeys()

        # Clean up
        self.mCleanUpKeys()


    def mExecuteKmsSyncEndpoint(self):

        # Clean up keys
        self.mCleanUpKeys()

        # Generate dummy key
        _hostDict = {"localhost": ExaKmsHostType.UNKNOWN}
        _host = "localhost"
        _user = "oracle"

        _privateKey = self.exakms.mGetEntryClass().mGeneratePrivateKey()
        _entry = self.exakms.mBuildExaKmsEntry(_host, _user, _privateKey)
        self.exakms.mInsertExaKmsEntry(_entry)

        self.assertEqual(len(self.exakms.mGetHistoryJson()), 1)

        # Rotate the key three times
        for i in range(0, 3):

            # Delete old
            self.exakms.mDeleteExaKmsEntry(_entry)

            # Create new
            _privateKey = self.exakms.mGetEntryClass().mGeneratePrivateKey()
            _entry = self.exakms.mBuildExaKmsEntry(_host, _user, _privateKey)
            self.exakms.mInsertExaKmsEntry(_entry)

        self.assertEqual(len(self.exakms.mGetHistory()), 3*2 + 1)

        # Save the history
        _historySave = self.exakms.mGetFullJson()
        self.mCleanUpKeys()

        # Execute sync endpoint
        _options = ebJsonObject({
            "cmd": 'sync',
            "history": _historySave
        })

        _endpoint = ExaKmsEndpoint(_options)
        _endpoint.mSetExaKms(self.exakms)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        # Cleanup
        self.mCleanUpKeys()

    def mExecuteKVDBSyncEndpoint(self):
        # Create temp ExaKmsKVDB object
        _exakvdb = ExaKmsKVDB()
        self.mCleanUpKeys(aExaKms=_exakvdb)

        _privateKey = _exakvdb.mGetEntryClass().mGeneratePrivateKey()

        # Create mock entry
        _mock_value = dict()
        _mock_value = {}
        _mock_value['key'] = "mock_key"
        _mock_value['label'] = "ECS_MAIN_LINUX.X64_MOCK"
        _mock_value['exacloud_hostname'] = "mock_host"
        _mock_value['creation_time'] = "mock_creation_date"
        _mock_value['walletId'] = "xxxxxxxxxxxxxxxx"
        _mock_value['encData'] = "mock_encrypted_data"
        
        # Insert mock entry
        _mock_str = json.dumps(_mock_value)
        _entry = _exakvdb.mBuildExaKmsEntry(_mock_value['key'], _mock_str)
        _exakvdb.mInsertExaKmsEntry(_entry)

        self.assertEqual(len(_exakvdb.mGetHistoryJson()), 1)

        # Rotate the key three times
        for i in range(0, 3):

            # Delete old
            _exakvdb.mDeleteExaKmsEntry(_mock_value['key'])

            # Create new entry
            _mock_value['key'] = f"mock_key_{i}"
            _mock_value['creation_time'] = f"mock_creation_date_{i}"
            _mock_value['encData'] = f"mock_encrypted_data_{i}"
            _mock_str = json.dumps(_mock_value)

            _privateKey = _exakvdb.mGetEntryClass().mGeneratePrivateKey()
            _entry = _exakvdb.mBuildExaKmsEntry(_mock_value['key'], _mock_str)
            _exakvdb.mInsertExaKmsEntry(_entry)

        self.assertEqual(len(_exakvdb.mGetHistory()), 3 * 2 + 1)

        # Save the history
        _historySave = _exakvdb.mGetFullJson()
        self.mCleanUpKeys(aExaKms=_exakvdb)

        # Execute sync endpoint
        _options = ebJsonObject({
            "cmd": 'kvdb_sync',
            "history": _historySave
        })

        _endpoint = ExaKmsEndpoint(_options)
        _endpoint.mSetExaKms(_exakvdb)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        # This number should remain unchanged since the same number of operations
        # were performed on standby DB, therefore the copy should have the same
        # number of elements in the history
        self.assertEqual(len(_historySave), len(_exakvdb.mGetFullJson()) - 1)

        # Cleanup
        self.mCleanUpKeys(aExaKms=_exakvdb)

    def mExecuteKmsDeleteOnDisk(self):

        # Create output folder
        _outFolder = os.path.join(self.mGetUtil().mGetOutputDir(), "ondisk")
        if not os.path.exists(_outFolder):
            os.mkdir(_outFolder)

        get_gcontext().mSetConfigOption('export_import_keys_folder', _outFolder)

        # Create Dom0 keys
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            open(os.path.join(_outFolder, f"id_rsa.{_dom0.split('.')[0]}.root"), 'a').close()
            open(os.path.join(_outFolder, f"id_rsa.{_dom0.split('.')[0]}.root.pub"), 'a').close()

        # Create dummy keys
        open(os.path.join(_outFolder, "id_rsa.host3.root"), 'a').close()
        open(os.path.join(_outFolder, "id_rsa.host3.root.pub"), 'a').close()

        # Create dummy file
        open(os.path.join(_outFolder, "dummy_file.json"), 'a').close()

        # Call delete keys
        self.mGetClubox().mHandlerDeleteOndiskKeys()

        # Review that all keys are moved.. including dummy keys. Only dummy non-key file should remain!
        self.assertEqual(len(os.listdir(_outFolder)), 1)


    def mExecuteMigrateEndpoint(self):

        # Clean up keys
        self.mCleanUpKeys()

        # Prepare Connect
        _cmds = {
            self.mGetRegexCell(): [
                []
            ],
            self.mGetRegexDom0(): [
                []
            ],
            self.mGetRegexVm(): [
                []
            ],
            self.mGetRegexSwitch(): [
                []
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping.*", aPersist=True),
                    exaMockCommand("rm -rf.*", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Pregenerate keys
        _hostDict = self.mGetClubox().mGetExaKmsHostMap()

        for _host in _hostDict.keys():
            _privateKey = self.exakms.mGetEntryClass().mGeneratePrivateKey()
            _entry = self.exakms.mBuildExaKmsEntry(_host, "root", _privateKey)
            self.exakms.mInsertExaKmsEntry(_entry)

        # Get the number of SSH keys in old format
        _options = ebJsonObject({
            "cmd": 'list-old-format'
        })

        _endpoint = ExaKmsEndpoint(_options)
        _endpoint.mSetExaKms(self.exakms)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        # Migrate keys
        self.mGetClubox().mSetClusterPath("clustername")
        _rc = self.mGetClubox().mHandlerExaKmsMigrate()
        self.assertEqual(_rc, 0)

    def mExecuteRotateEndpoint(self):

        # Clean up keys
        self.mCleanUpKeys()

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("echo.*", aPersist=True),
                    exaMockCommand("sed.*", aPersist=True),
                ],
                [
                    exaMockCommand("echo.*", aPersist=True),
                    exaMockCommand("sed.*", aPersist=True),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Generate dummy keys on first domU
        _host = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _user = "oracle"
        _user2 = "root"

        _privateKey = self.exakms.mGetEntryClass(aType="RSA").mGeneratePrivateKey()
        _entry = self.exakms.mBuildExaKmsEntry(_host, _user, _privateKey, aClassName="RSA")
        self.exakms.mInsertExaKmsEntry(_entry)

        _privateKey = self.exakms.mGetEntryClass(aType="ECDSA").mGeneratePrivateKey()
        _entry = self.exakms.mBuildExaKmsEntry(_host, _user2, _privateKey, aClassName="ECDSA")
        self.exakms.mInsertExaKmsEntry(_entry)

        _entries = self.exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), 2)

        # Execute rotate endpoint
        _options = ebJsonObject({
            "cmd": "rotate", 
            "exakms_fqdn": _host,
            "exakms_key_type": "ECDSA"
        })

        _endpoint = ExaKmsEndpoint(_options)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        _entries = self.exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), 2)

        _entry = _entries[0]
        self.assertTrue("ecdsa" in _entry.mGetPublicKey())
        self.assertTrue("ECDSA" in _entry.mGetVersion())

        # Execute rotate endpoint
        _options = ebJsonObject({
            "cmd": "rotate", 
            "exakms_fqdn": _host,
            "exakms_key_type": "RSA"
        })

        _endpoint = ExaKmsEndpoint(_options)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        _entries = self.exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_entries), 2)

        _entry = _entries[0]
        self.assertTrue("rsa" in _entry.mGetPublicKey())
        self.assertTrue("RSA" in _entry.mGetVersion())


        self.mCleanUpKeys()


    def mExecuteKmsBackupEndpoint(self):

        # Clean up keys
        self.mCleanUpKeys()

        # Generate dummy key
        _hostDict = {"localhost": ExaKmsHostType.UNKNOWN}
        _host = "localhost"
        _user = "oracle"

        _privateKey = self.exakms.mGetEntryClass().mGeneratePrivateKey()
        _entry = self.exakms.mBuildExaKmsEntry(_host, _user, _privateKey)
        self.exakms.mInsertExaKmsEntry(_entry)

        # Rotate the key three times
        for i in range(0, 3):

            # Delete old
            self.exakms.mDeleteExaKmsEntry(_entry)

            # Create new
            _privateKey = self.exakms.mGetEntryClass().mGeneratePrivateKey()
            _entry = self.exakms.mBuildExaKmsEntry(_host, _user, _privateKey)
            self.exakms.mInsertExaKmsEntry(_entry)

        # Execute backup endpoint
        _options = ebJsonObject({"cmd": "backup"})
        _endpoint = ExaKmsEndpoint(_options)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        # Delete all keys from main bucket
        self.mCleanUpKeys()

        _all = self.exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertEqual(len(_all), 0)

        # Execute restore backup endpoint
        _options = ebJsonObject({"cmd": "restore"})
        _endpoint = ExaKmsEndpoint(_options)

        _rc = _endpoint.mExecute()
        self.assertEqual(_rc, 0)

        # Ensure the main bucket has keys
        _all = self.exakms.mSearchExaKmsEntries({}, aRefreshKey=True)
        self.assertNotEqual(len(_all), 0)

        # Clean up test
        self.mCleanUpKeys()

    def test_001_exakms_fs(self):

        # Prepare fs env
        self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsFileSystem')
        self.exakmsSingleton = ExaKmsSingleton()
        get_gcontext().mSetExaKmsSingleton(self.exakmsSingleton)
        self.exakms = ExaKmsFileSystem()

        self.mExecuteInsertDeleteDownloadEndpoint()
        self.mExecuteKmsSyncEndpoint()
        self.mExecuteRestoreEndpoint()
        self.mExecuteKmsDeleteOnDisk()
        self.mExecuteKmsBackupEndpoint()
        self.mExecuteMigrateEndpoint()
        self.mExecuteRotateEndpoint()

    def test_002_exakms_keysdb(self):

        # Prepare keysdb env
        self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsKeysDB')
        _basepath = os.path.abspath(self.mGetUtil().mGetOutputDir())

        if not os.path.exists(f"{_basepath}/dbcli/bin/mkstore"):
            os.system(f"mkdir -p {_basepath}/dbcli/")
            os.system(f"unzip packages/wallet_util.zip -d {_basepath}/dbcli/ 2>&1 >/dev/null")

        get_gcontext().mSetRegEntry("MKSTORE_BASEPATH", _basepath)

        self.exakmsSingleton = ExaKmsSingleton()
        get_gcontext().mSetExaKmsSingleton(self.exakmsSingleton)
        self.exakms = ExaKmsKeysDB()

        self.mExecuteKmsCluctrlEndpoint()
        self.mExecuteInsertDeleteDownloadEndpoint()
        self.mExecuteKmsSyncEndpoint()
        self.mExecuteRestoreEndpoint()
        self.mExecuteKmsBackupEndpoint()
        self.mExecuteMigrateEndpoint()
        self.mExecuteRotateEndpoint()

    def test_003_exakms_oci(self):

        if not self.mGetClubox().mGetCtx().mCheckConfigOption(
                                                            'kms_dp_endpoint'):
            return

        # Prepare oci env
        self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsOCI')

        self.exakmsSingleton = ExaKmsSingleton()
        get_gcontext().mSetExaKmsSingleton(self.exakmsSingleton)
        self.exakms = ExaKmsOCI()

        self.mExecuteKmsSyncEndpoint()
        self.mExecuteInsertDeleteDownloadEndpoint()
        self.mExecuteRestoreEndpoint()
        self.mExecuteMigrateEndpoint()
        self.mExecuteRotateEndpoint()

        if self.mGetClubox().mGetCtx().mCheckConfigOption(
                                                    'exakms_bucket_secondary'):
            self.mExecuteKmsBackupEndpoint()

    def test_004_exakms_siv(self):

        if not self.mGetClubox().mGetCtx().mCheckConfigOption('enable_siv',
                                                                       'True'):
            return

        # Prepare SIV env
        self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsSIV')

        self.exakmsSingleton = ExaKmsSingleton()
        get_gcontext().mSetExaKmsSingleton(self.exakmsSingleton)
        self.exakms = ExaKmsSIV()

        self.mExecuteKmsSyncEndpoint()
        self.mExecuteInsertDeleteDownloadEndpoint()
        self.mExecuteRestoreEndpoint()
        self.mExecuteMigrateEndpoint()
        self.mExecuteKmsBackupEndpoint()
        self.mExecuteRotateEndpoint()

    def test_005_exakms_cross_save(self):

        # Prepare keysdb env
        self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsKeysDB')
        _basepath = os.path.abspath(self.mGetUtil().mGetOutputDir())

        if not os.path.exists(f"{_basepath}/dbcli/bin/mkstore"):
            os.system(f"mkdir -p {_basepath}/dbcli/")
            os.system(f"unzip packages/wallet_util.zip -d {_basepath}/dbcli/ 2>&1 >/dev/null")

        get_gcontext().mSetRegEntry("MKSTORE_BASEPATH", _basepath)

        self.mExecuteCrossSaveEndpoint("ExaKmsFileSystem", "ExaKmsKeysDB")

    def test_006_exakms_kvdb(self):
        # Prepare KVDB env
        self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsKVDB')
        self.mGetClubox().mGetCtx().mSetConfigOption('remote_cps_host', 'localhost')

        self.exakmsSingleton = ExaKmsSingleton()
        get_gcontext().mSetExaKmsSingleton(self.exakmsSingleton)

        self.mExecuteKVDBSyncEndpoint()


# ============================ New Unit Tests for ExaKmsOCI (Appended) ============================

class TestExaKmsOCIUnit(ebTestClucontrol):
    """
    Focused unit tests for ExaKmsOCI methods with complete mocking of external systems.
    These tests inherit from ebTestClucontrol to leverage shared utilities as requested.
    """

    @classmethod
    def setUpClass(cls):
        # Keep lightweight; do not generate heavy databases for these unit tests
        try:
            super().setUpClass(aGenerateDatabase=False)
        except TypeError:
            # Fallback if ebTestClucontrol.setUpClass doesn't accept the arg
            super().setUpClass()

    # ------------------------------ Helpers ------------------------------

    def _mock_ctx(self, overrides=None):
        """Return a mock gcontext with proper method signatures."""
        overrides = overrides or {}
        cfg = {
            'exakms_default_keygen_algorithm': 'RSA',
            'kms_key_id': 'mock_key_id',
            'kms_dp_endpoint': 'mock_crypto_ep',
            'exakms_bucket_primary': 'mock_bucket',
            'exakms_bucket_secondary': 'mock_backup_bucket',
            'exakms_oci_retries': '3',
            'exakms_enable_fetch_clustername': False,
        }
        cfg.update(overrides)

        mock_ctx = Mock()
        mock_ctx.mCheckRegEntry.side_effect = lambda key: key in ['exakms_default_keygen_algorithm'] and cfg.get(key) is not None
        mock_ctx.mGetRegEntry.side_effect = lambda key, default=None: cfg.get(key, default)
        mock_ctx.mCheckConfigOption.side_effect = lambda key, default=None: cfg.get(key, default)
        mock_ctx.mSetConfigOption = Mock()
        return mock_ctx

    def _mk_factory_with_clients(self, namespace='ns'):
        """Create a mocked ExaOCIFactory with object storage and crypto client."""
        obj_ns = Mock()
        obj_ns.data = namespace
        obj_client = Mock()
        obj_client.get_namespace.return_value = obj_ns

        crypto_client = Mock()

        factory = Mock()
        factory.get_object_storage_client.return_value = obj_client
        factory.get_crypto_client.return_value = crypto_client
        return factory, obj_client, crypto_client

    # ------------------------------ __init__ config validation ------------------------------

    def test_init_missing_kms_key_id_raises(self):
        with patch('exabox.exakms.ExaKmsOCI.get_gcontext', return_value=self._mock_ctx({'kms_key_id': None})):
            with self.assertRaisesRegex(ValueError, "'kms_key_id' configure parameter not set"):
                ExaKmsOCI()

    def test_init_missing_kms_dp_endpoint_raises(self):
        with patch('exabox.exakms.ExaKmsOCI.get_gcontext', return_value=self._mock_ctx({'kms_dp_endpoint': None})):
            with self.assertRaisesRegex(ValueError, "'kms_dp_endpoint' configure parameter not set"):
                ExaKmsOCI()

    def test_init_missing_bucket_primary_raises(self):
        with patch('exabox.exakms.ExaKmsOCI.get_gcontext', return_value=self._mock_ctx({'exakms_bucket_primary': None})):
            with self.assertRaisesRegex(ValueError, "'exakms_bucket_primary' configure parameter not set"):
                ExaKmsOCI()

    # ------------------------------ mObjectStoreInit ------------------------------

    def test_object_store_init_sets_clients(self):
        mock_ctx = self._mock_ctx()
        factory, obj_client, crypto_client = self._mk_factory_with_clients()

        with patch('exabox.exakms.ExaKmsOCI.get_gcontext', return_value=mock_ctx), \
             patch('exabox.exakms.ExaKmsOCI.ExaOCIFactory', return_value=factory), \
             patch('exabox.exakms.ExaKmsOCI.cryptographyAES', return_value=Mock()), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsHistoryOCI', return_value=Mock()):
            exa = ExaKmsOCI()

            # Verify factory usage
            factory.get_object_storage_client.assert_called_once()
            obj_client.get_namespace.assert_called_once()
            factory.get_crypto_client.assert_called_once_with('mock_crypto_ep')

    # ------------------------------ mSearchExaKmsEntries (retry + parsing) ------------------------------

    def test_search_entries_retries_on_sslerror_and_parses_entries(self):
        mock_ctx = self._mock_ctx()
        factory, obj_client, crypto_client = self._mk_factory_with_clients()
        # list_objects returns SSLError once, then success
        obj1 = Mock()
        obj1.name = 'host1'
        list_resp = Mock()
        list_resp.data.objects = [obj1]
        list_resp.data.next_start_with = None

        obj_client.list_objects.side_effect = [SSLError("net"), list_resp]

        # mGetOSS returns JSON content for one key
        obj_data = {
            'id_rsa.host1.user1': {
                'encData': 'ED',
                'encDEK': 'EK',
                'version': 'ECDSA',
                'hash': 'H1',
                'creationTime': '2024-01-01T00:00:00Z',
                'label': 'LBL',
                'exacloud_host': 'EXAH',
                'hostType': 'DOMU',
                'keyValueInfo': {'k': 'v'}
            }
        }
        get_resp = Mock()
        get_resp.data.content = json.dumps(obj_data).encode('utf-8')
        get_resp.status = 200

        # Build entry returns a configurable mock that stores values set by setters
        def _build_entry(fqdn, user, pkey, aHostType=ExaKmsHostType.UNKNOWN, aClassName=None):
            e = Mock()
            e._objname = None
            e._ctime = None
            e._fqdn = fqdn
            e.mSetCryptoClient = Mock()
            e.mSetEncDEK = Mock()
            e.mSetEncData = Mock()
            e.mSetObjectName = Mock(side_effect=lambda v: setattr(e, '_objname', v))
            e.mSetHash = Mock()
            e.mSetCreationTime = Mock(side_effect=lambda v: setattr(e, '_ctime', v))
            e.mSetLabel = Mock()
            e.mSetExacloudHost = Mock()
            e.mSetHostType = Mock()
            e.mSetKeyValueInfo = Mock()
            e.mGetCreationTime = Mock(side_effect=lambda: e._ctime)
            e.mGetObjectName = Mock(side_effect=lambda: e._objname)
            e.mGetFQDN = Mock(return_value=fqdn)
            return e

        with patch('exabox.exakms.ExaKmsOCI.get_gcontext', return_value=mock_ctx), \
             patch('exabox.exakms.ExaKmsOCI.ExaOCIFactory', return_value=factory), \
             patch('exabox.exakms.ExaKmsOCI.cryptographyAES', return_value=Mock()), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsHistoryOCI', return_value=Mock()):
            exa = ExaKmsOCI()

            # Patch instance-level methods
            with patch.object(exa, 'mGetOSS', return_value=get_resp) as p_getoss, \
                 patch.object(exa, 'mBuildExaKmsEntry', side_effect=_build_entry) as p_build, \
                 patch.object(exa, 'mUpdateCacheKey') as p_upd:

                entries = exa.mSearchExaKmsEntries({'FQDN': 'host1'}, aRefreshKey=True)

                self.assertEqual(len(entries), 1)
                obj_client.list_objects.assert_called()
                p_getoss.assert_called_once_with('mock_bucket', 'host1')
                p_build.assert_called_once()
                p_upd.assert_called()

    # ------------------------------ mPutOSS / mGetOSS / mDeleteOSS retry logic ------------------------------

    def _mk_exa_for_oss_calls(self):
        mock_ctx = self._mock_ctx()
        factory, obj_client, crypto_client = self._mk_factory_with_clients()
        with patch('exabox.exakms.ExaKmsOCI.get_gcontext', return_value=mock_ctx), \
             patch('exabox.exakms.ExaKmsOCI.ExaOCIFactory', return_value=factory), \
             patch('exabox.exakms.ExaKmsOCI.cryptographyAES', return_value=Mock()), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsHistoryOCI', return_value=Mock()):
            exa = ExaKmsOCI()
        return exa, factory, obj_client, crypto_client

    def test_put_oss_retries_until_success(self):
        exa, _, obj_client, _ = self._mk_exa_for_oss_calls()
        exa._ExaKmsOCI__retries = 2  # allow 3 attempts total
        success = Mock()
        success.status = 200
        obj_client.put_object.side_effect = [None, Mock(status=500), success]

        resp = exa.mPutOSS('bkt', 'obj', 'content')
        self.assertIs(resp, success)
        self.assertEqual(obj_client.put_object.call_count, 3)

    def test_get_oss_retries_until_success(self):
        exa, _, obj_client, _ = self._mk_exa_for_oss_calls()
        exa._ExaKmsOCI__retries = 1
        success = Mock()
        success.status = 200
        obj_client.get_object.side_effect = [Mock(status=500), success]

        resp = exa.mGetOSS('bkt', 'obj')
        self.assertIs(resp, success)
        self.assertEqual(obj_client.get_object.call_count, 2)

    def test_delete_oss_raises_after_exhausting_retries(self):
        exa, _, obj_client, _ = self._mk_exa_for_oss_calls()
        exa._ExaKmsOCI__retries = 1
        obj_client.delete_object.side_effect = [SSLError("net"), SSLError("net")]

        with self.assertRaises(ExacloudRuntimeError):
            exa.mDeleteOSS('obj')

    # ------------------------------ mInsertToBucket content and behavior ------------------------------

    def test_insert_to_bucket_creates_new_json_and_preserves_creation_time(self):
        exa, _, obj_client, _ = self._mk_exa_for_oss_calls()

        # No existing object
        with patch.object(exa, 'mGetOSS', side_effect=Exception("no object")), \
             patch.object(exa, 'mPutOSS') as p_put, \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsEntryOCIRSA.mGetCurrentLabel', return_value='CUR_LABEL'), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsEntryOCIRSA.mGetCurrentExacloudHost', return_value='CUR_EXAHOST'), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsEntryOCIRSA.mGetCurrentTime', return_value='NOW_TIME'):

            entry = Mock()
            entry.mGetEncData.return_value = 'ED'
            entry.mGetEncDEK.return_value = 'EK'
            entry.mGetHostType.return_value = ExaKmsHostType.DOMU
            entry.mGetKeyValueInfo.return_value = {'a': 1}
            entry.mGetVersion.return_value = 'RSA'
            entry.mGetFQDN.return_value = 'host1.domain'
            entry.mGetUser.return_value = 'root'
            entry.mGetHash.return_value = 'H1'
            entry.mGetObjectName.return_value = 'host1'
            entry.mGetCreationTime.return_value = 'CT1'

            exa.mInsertToBucket(entry, 'bkt', aPreservateCreationTime=True)

            self.assertTrue(p_put.called)
            args = p_put.call_args[0]
            self.assertEqual(args[0], 'bkt')
            self.assertEqual(args[1], 'host1')
            body = json.loads(args[2])
            key = 'id_rsa.host1.root'
            self.assertIn(key, body)
            self.assertEqual(body[key]['encData'], 'ED')
            self.assertEqual(body[key]['encDEK'], 'EK')
            self.assertEqual(body[key]['hostType'], 'DOMU')
            self.assertEqual(body[key]['keyValueInfo'], {'a': 1})
            self.assertEqual(body[key]['version'], 'RSA')
            self.assertEqual(body[key]['label'], 'CUR_LABEL')
            self.assertEqual(body[key]['exacloud_host'], 'CUR_EXAHOST')
            self.assertEqual(body[key]['creationTime'], 'CT1')
            self.assertEqual(body[key]['hash'], 'H1')

    def test_insert_to_bucket_sets_current_time_when_not_preserving(self):
        exa, _, obj_client, _ = self._mk_exa_for_oss_calls()

        with patch.object(exa, 'mGetOSS', side_effect=Exception("no object")), \
             patch.object(exa, 'mPutOSS') as p_put, \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsEntryOCIRSA.mGetCurrentTime', return_value='NOW_TIME'), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsEntryOCIRSA.mGetCurrentLabel', return_value='L'), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsEntryOCIRSA.mGetCurrentExacloudHost', return_value='EH'):

            entry = Mock()
            entry.mGetEncData.return_value = 'ED'
            entry.mGetEncDEK.return_value = 'EK'
            entry.mGetHostType.return_value = ExaKmsHostType.UNKNOWN
            entry.mGetKeyValueInfo.return_value = {}
            entry.mGetVersion.return_value = 'ECDSA'
            entry.mGetFQDN.return_value = 'host2.dom'
            entry.mGetUser.return_value = 'oracle'
            entry.mGetHash.return_value = 'H2'
            entry.mGetObjectName.return_value = 'host2'

            exa.mInsertToBucket(entry, 'bkt', aPreservateCreationTime=False)

            body = json.loads(p_put.call_args[0][2])
            key = 'id_rsa.host2.oracle'
            self.assertEqual(body[key]['creationTime'], 'NOW_TIME')

    # ------------------------------ mDeleteExaKmsEntry ------------------------------

    def test_delete_exakms_entry_success_deletes_from_oss(self):
        exa, _, obj_client, _ = self._mk_exa_for_oss_calls()

        # Existing object with single key => should call mDeleteOSS
        obj_data = {
            'id_rsa.host1.root': {
                'encData': 'ED',
                'encDEK': 'EK'
            }
        }
        get_resp = Mock()
        get_resp.data.content = json.dumps(obj_data).encode('utf-8')
        get_resp.status = 200

        with patch.object(exa, 'mGetOSS', return_value=get_resp), \
             patch.object(exa, 'mDeleteOSS', return_value=Mock(status=200)) as p_del, \
             patch.object(exa, 'mPutOSS') as p_put, \
             patch.object(ExaKms, 'mDeleteExaKmsEntry', autospec=True, return_value=None):
            entry = Mock()
            entry.mGetObjectName.return_value = 'host1'
            entry.mGetFQDN.return_value = 'host1.domain'
            entry.mGetUser.return_value = 'root'
            entry.mGetCryptoClient.return_value = None
            entry.mSetCryptoClient = Mock()

            ok = exa.mDeleteExaKmsEntry(entry)
            self.assertTrue(ok)
            p_del.assert_called_once()
            p_put.assert_not_called()

    def test_delete_exakms_entry_handles_exception_and_returns_false(self):
        exa, _, obj_client, _ = self._mk_exa_for_oss_calls()

        with patch.object(exa, 'mGetOSS', side_effect=Exception("boom")), \
             patch.object(ExaKms, 'mDeleteExaKmsEntry', autospec=True, return_value=None):
            entry = Mock()
            entry.mGetObjectName.return_value = 'host1'
            entry.mGetFQDN.return_value = 'host1.domain'
            entry.mGetUser.return_value = 'root'
            entry.mGetCryptoClient.return_value = None
            entry.mSetCryptoClient = Mock()

            ok = exa.mDeleteExaKmsEntry(entry)
            self.assertFalse(ok)

    # ------------------------------ mInsertExaKmsEntry ------------------------------

    def test_insert_exakms_entry_writes_to_primary_and_backup(self):
        # Ensure backup bucket configured
        mock_ctx = self._mock_ctx({'exakms_bucket_secondary': 'backup'})
        factory, obj_client, crypto_client = self._mk_factory_with_clients()
        with patch('exabox.exakms.ExaKmsOCI.get_gcontext', return_value=mock_ctx), \
             patch('exabox.exakms.ExaKmsOCI.ExaOCIFactory', return_value=factory), \
             patch('exabox.exakms.ExaKmsOCI.cryptographyAES', return_value=Mock()), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsHistoryOCI', return_value=Mock()):
            exa = ExaKmsOCI()

        with patch.object(exa, 'mInsertToBucket') as p_ins, \
             patch.object(ExaKms, 'mInsertExaKmsEntry', autospec=True, return_value=None):
            entry = Mock()
            entry.mGetCryptoClient.return_value = None
            entry.mSetCryptoClient = Mock()
            entry.mGetObjectName.return_value = 'obj'
            entry.mSetObjectName = Mock()
            entry.mGetFQDN.return_value = 'fqdn'
            ok = exa.mInsertExaKmsEntry(entry)
            self.assertTrue(ok)
            # Primary and backup
            self.assertEqual(p_ins.call_count, 2)

    # ------------------------------ mBackup ------------------------------

    def test_backup_copies_entries_and_merges_history(self):
        mock_ctx = self._mock_ctx({'exakms_bucket_secondary': 'backup'})
        factory, obj_client, crypto_client = self._mk_factory_with_clients()
        with patch('exabox.exakms.ExaKmsOCI.get_gcontext', return_value=mock_ctx), \
             patch('exabox.exakms.ExaKmsOCI.ExaOCIFactory', return_value=factory), \
             patch('exabox.exakms.ExaKmsOCI.cryptographyAES', return_value=Mock()), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsHistoryOCI', return_value=Mock()):
            exa = ExaKmsOCI()

        e1 = Mock()
        e2 = Mock()
        with patch.object(exa, 'mSearchExaKmsEntries', return_value=[e1, e2]) as p_search, \
             patch.object(exa, 'mInsertToBucket', side_effect=[None, Exception("fail")]) as p_ins, \
             patch.object(exa, 'mGetOSS') as p_get, \
             patch.object(exa, 'mPutOSS') as p_put:

            # Main history content (with header of 3 lines and entries)
            main_hist = "Header1\nHeader2\nHeader3\n2025-01-01 A\n2025-01-02 B\n"
            # Backup history existing with last entry at 2025-01-01
            backup_hist = "2024-12-31 X\n2025-01-01 A\n"

            # Sequence: get main changes.txt, then backup changes.txt
            main_resp = Mock()
            main_resp.data.content = main_hist.encode('utf-8')
            backup_resp = Mock()
            backup_resp.data.content = backup_hist.encode('utf-8')

            p_get.side_effect = [main_resp, backup_resp]

            ok = exa.mBackup()
            # One insert succeeded, one failed -> _suc becomes False
            self.assertFalse(ok)
            # Verify history was merged and written to backup
            self.assertTrue(p_put.called)
            args = p_put.call_args[0]
            self.assertEqual(args[0], 'backup')
            self.assertEqual(args[1], 'changes.txt')
            merged = args[2]
            self.assertIn("2025-01-02 B", merged)

    # ------------------------------ mRestoreBackup ------------------------------

    def test_restore_backup_copies_newer_entries_to_main(self):
        mock_ctx = self._mock_ctx({'exakms_bucket_secondary': 'backup'})
        factory, obj_client, crypto_client = self._mk_factory_with_clients()
        with patch('exabox.exakms.ExaKmsOCI.get_gcontext', return_value=mock_ctx), \
             patch('exabox.exakms.ExaKmsOCI.ExaOCIFactory', return_value=factory), \
             patch('exabox.exakms.ExaKmsOCI.cryptographyAES', return_value=Mock()), \
             patch('exabox.exakms.ExaKmsOCI.ExaKmsHistoryOCI', return_value=Mock()):
            exa = ExaKmsOCI()

        # Backup entries
        e_newer = Mock()
        e_newer.mGetFQDN.return_value = 'h1'
        e_newer.mGetUser.return_value = 'u1'
        e_newer.mGetCreationTime.return_value = 20

        e_older = Mock()
        e_older.mGetFQDN.return_value = 'h2'
        e_older.mGetUser.return_value = 'u2'
        e_older.mGetCreationTime.return_value = 10

        # Main entry older or missing
        main_for_newer = Mock()
        main_for_newer.mGetCreationTime.return_value = 5  # older than backup
        main_for_older = None  # not present

        with patch.object(exa, 'mSearchExaKmsEntries', return_value=[e_newer, e_older]) as p_search, \
             patch.object(exa, 'mGetExaKmsEntry', side_effect=[main_for_newer, main_for_older]) as p_get_entry, \
             patch.object(exa, 'mInsertToBucket') as p_insert:
            ok = exa.mRestoreBackup()
            self.assertTrue(ok)
            # Insert called for both (newer-than-main and main-missing)
            self.assertEqual(p_insert.call_count, 2)

# ===============================================================================================

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
