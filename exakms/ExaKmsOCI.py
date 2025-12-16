#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsOCI.py /main/30 2023/10/24 09:29:02 jesandov Exp $
#
# ExaKmsOCI.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsOCI.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      </short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    10/20/23 - 35933990: Include label in ExaKmsEntry
#    jesandov    08/07/23 - 35683301: Removal of linear search in object store
#    jesandov    06/12/23 - 35484161: Add validation to nathostname in the
#                           search pattern dict
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    aypaul      06/01/22 - Enh#34207528 ExaKms entry history tracking and
#                           generation.
#    jesandov    05/31/22 - Add ExaKms KeyValue Info
#    aypaul      05/04/22 - Enh#34127058 exakms entry tracking endpoint.
#    ndesanto    04/12/22 - OCI region to come on all ECRA call and be stored
#                           on a DB cache.
#    alsepulv    03/28/22 - Bug 34009358: Bubble up oci exceptions
#    jesandov    03/24/22 - 33997797 - EXACS: EXAKMS: ADD CACHE TO EXAKMS KEY
#                           MANAGEMENT
#    jesandov    18/02/22 - Add message with the response on case of error
#    ndesanto    01/13/22 - Load the OCI regions configuration file if any.
#    alsepulv    11/18/21 - Bug 33550037: add retry to instance principal
#                           creation
#    alsepulv    10/26/21 - Bug 33506006: Move mGetOSS call inside the try
#                           block
#    alsepulv    10/19/21 - Bug 33484334: Replace SSLError import with correct
#                           one
#    alsepulv    10/13/21 - Bug 33453090: Add retries to mSearchExaKms
#    alsepulv    08/16/21 - Bug 30993225: Define Backup class method
#    alsepulv    07/21/21 - Bug 33137424: Correctly set up signer for non-R1
#                           envs with no local certificate
#    jesandov    04/27/21 - Creation
#

import json
import re
import os
import copy
import socket

from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsEntryOCI import ExaKmsEntryOCIRSA, ExaKmsEntryOCIECDSA
from exabox.exakms.ExaKms import ExaKms
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.kms.crypt import cryptographyAES
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError
from exabox.exakms.ExaKmsHistoryOCI import ExaKmsHistoryOCI
from oci.key_management import KmsCryptoClient
from oci.key_management.models import GenerateKeyDetails, DecryptDataDetails
from oci.object_storage.models import CreateBucketDetails
from typing import List, Mapping, Optional
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from typing import List
from time import sleep
from six.moves import urllib
from oci._vendor.urllib3.exceptions import SSLError
urlopen = urllib.request.urlopen
URLError = urllib.error.URLError
HTTPError = urllib.error.HTTPError


class ExaKmsOCI(ExaKms):

    def __init__(self) -> None:
        """ Initializes the object storage client and KMS crypto client
        """

        ExaKms.__init__(self)

        _entryClasses = {
            "ECDSA": ExaKmsEntryOCIECDSA,
            "RSA": ExaKmsEntryOCIRSA
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

        if not get_gcontext().mCheckConfigOption('kms_key_id'):
            raise ValueError("'kms_key_id' configure parameter not set in exabox.conf")

        if not get_gcontext().mCheckConfigOption('kms_dp_endpoint'):
            raise ValueError("'kms_dp_endpoint' configure parameter not set in exabox.conf")

        if not get_gcontext().mCheckConfigOption('exakms_bucket_primary'):
            raise ValueError("'exakms_bucket_primary' configure parameter not set in exabox.conf")

        self.__aes = cryptographyAES()
        self.__bucket = get_gcontext().mCheckConfigOption("exakms_bucket_primary")
        self.__backupBucket = get_gcontext().mCheckConfigOption("exakms_bucket_secondary")

        self.__retries = 10
        if get_gcontext().mCheckConfigOption('exakms_oci_retries'):
            self.__retries = int(get_gcontext().mCheckConfigOption('exakms_oci_retries'))

        self.mObjectStoreInit()
        self.mSetExaKmsHistoryInstance(ExaKmsHistoryOCI(self))

    def mObjectStoreInit(self) -> None:
        """ Initializes the object storage client
        """
        _factory = ExaOCIFactory()

        # Create an OCI Object Storage client
        self.__objectStorage = _factory.get_object_storage_client()
        self.__namespace = self.__objectStorage.get_namespace().data

        # Create an OCI kms Crypto client
        self.DEFAULT_KEY_LENGTH = 32
        self.DEFAULT_KEY_ALGORITHM = 'AES'
        self.__kmsKeyId = get_gcontext().mCheckConfigOption('kms_key_id')
        self.__keyShape = {'algorithm': self.DEFAULT_KEY_ALGORITHM, 'length': self.DEFAULT_KEY_LENGTH}
        self.__cryptoEndpoint = get_gcontext().mCheckConfigOption('kms_dp_endpoint')
        self.__kmsCryptoClient = _factory.get_crypto_client(self.__cryptoEndpoint)


    def mBuildExaKmsEntry(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN, aClassName=None):

        _class = self.mGetEntryClass()

        if aClassName:
            if "ECDSA" in aClassName.upper():
                _class = ExaKmsEntryOCIECDSA
            else:
                _class = ExaKmsEntryOCIRSA

        _entry = _class(aFQDN, aUser, "", aHostType)
        _entry.mSetCryptoClient(self.__kmsCryptoClient)
        _entry.mSetPrivateKey(aPrivateKey)
        return _entry


    def mSearchExaKmsEntries(self, aPatternDict: dict, aRefreshKey: bool = False, aBackup: bool = False) -> List[ExaKmsEntry]:
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

        _bucket = self.__bucket
        if aBackup:
            _bucket = self.__backupBucket

        _retries = 3
        if get_gcontext().mCheckConfigOption('exakms_oci_retries'):
            try:
                _retries = int(get_gcontext().mCheckConfigOption('exakms_oci_retries'))
                _retries = min(_retries, 10)
                _retries = max(_retries, 1)
            except ValueError:
                _msg = ('Value for "exakms_oci_retries" in config '
                       'is not an integer value: '
                      f'{get_gcontext().mCheckConfigOption("exakms_oci_retries")}'
                       '. Falling back to default value...')
                ebLogWarn(_msg)

        # Get all the objects in the bucket
        _objects = []
        _next_start = None
        _get_objects = True
        _exception_msg = None
        while _get_objects:
            # Bug 33453090: We need to retry the connection every time we get
            # an SSLError, which is a common intermittent connection issue
            for _ in range(_retries):
                try:
                    _resp = self.__objectStorage.list_objects(self.__namespace,
                                                     _bucket,start=_next_start)
                    _objects += _resp.data.objects
                    _next_start = _resp.data.next_start_with
                    _get_objects = _next_start is not None
                    break

                except SSLError as e:
                    _exception_msg = e
                    _msg = (f'SSLError during ExaKms list_objects operations: {e} '
                           'Retrying in one second...')
                    ebLogTrace(_msg)
                    sleep(1)
                except TypeError as e:
                    _exception_msg = e
                    _msg = f"TypeError: {e} Response unexpected: {_resp.__dict__}"
                    ebLogTrace(_msg)
                    sleep(1)
                except Exception as e:
                    _msg = f"Response unexpected: {e}"
                    ebLogTrace(_msg)
                    raise ExacloudRuntimeError(aErrorMsg=_msg) from e
            else:
                _err_msg = f'OCI error: {_exception_msg} Please retry operation'
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg

        _entries = []
        _objectList = []

        # try single access
        if "FQDN" in _patternDict:
            for _object in _objects:
                if _object.name == _patternDict['FQDN']:
                    _objectList.append(_object)
                    break

        # Fetch of all the object still needed when aPatternDict = {}
        if "FQDN" not in _patternDict or get_gcontext().mCheckRegEntry("exakms_enable_fetch_clustername"):
            if not _objectList:
                _objectList = _objects

        for _object in _objectList:

            if _object.name.split(".")[-1] in ["jpg", "jpge", "tar", "gz", "json", "png"]:
                continue

            try:
                _obj = self.mGetOSS(_bucket, _object.name)
                _objDict = json.loads(_obj.data.content.decode('utf-8'))
            except Exception:
                continue

            # Search for the fqdn of each object
            for _objKey, _objData in _objDict.items():
                _keyPattern = re.match(r'id_rsa.([\w\-\_]+).([\w\-\_]+)', _objKey)

                if not _keyPattern:
                    continue

                _fqdn = _keyPattern.group(1)
                if '.' in _object.name:
                    _fqdn = _object.name

                # If given an FQDN, ignore all other entries.
                if 'FQDN' in _patternDict:
                    if 'strict' in _patternDict and _patternDict['strict']:
                        if _fqdn.split('.')[0] != _patternDict['FQDN'].split('.')[0]:
                            continue

                    else:
                        if not re.match(_patternDict['FQDN'], _fqdn) and \
                               _fqdn.split('.')[0] != _patternDict['FQDN'].split('.')[0]:
                            continue

                # If given a user, ignore all other entries
                if 'user' in _patternDict:
                    if _keyPattern.group(2) != _patternDict['user']:
                        continue

                if 'encData' not in _objData or 'encDEK' not in _objData:
                    continue

                if not _objData['encDEK'] or not _objData['encData']:
                    continue

                # Add entry to list
                _version = None
                if "version" in _objData:
                    _version = _objData["version"]
                else:
                    _version = "RSA"

                _entry = self.mBuildExaKmsEntry(_fqdn, _keyPattern.group(2), '', aClassName=_version)
                _entry.mSetCryptoClient(self.__kmsCryptoClient)
                _entry.mSetEncDEK(_objData['encDEK'])
                _entry.mSetEncData(_objData['encData'])
                _entry.mSetObjectName(_object.name)

                if "hash" in _objData:
                    _entry.mSetHash(_objData['hash'])

                if "creationTime" in _objData:
                    _entry.mSetCreationTime(_objData['creationTime'])

                if "label" in _objData:
                    _entry.mSetLabel(_objData['label'])

                if "exacloud_host" in _objData:
                    _entry.mSetExacloudHost(_objData['exacloud_host'])

                if 'hostType' in _objData:
                    _entry.mSetHostType(_objData['hostType'])

                if 'keyValueInfo' in _objData:
                    _entry.mSetKeyValueInfo(_objData['keyValueInfo'])

                _entries.append(_entry)

        def mGetSortKey(aEntry):

            _str = f"{aEntry.mGetCreationTime()}|"

            if aEntry.mGetObjectName() == aEntry.mGetObjectName():
                _str = "1|"
            else:
                _str = "0|"

            return _str

        _sorted = sorted(_entries, key=mGetSortKey, reverse=True)

        for _entry in _sorted:
            self.mUpdateCacheKey(_entry.mGetFQDN(), _entry)

        return _sorted


    def mDeleteOSS(self, aObjectName):

        _cur_tries = 0
        _exception_msg = None
        while _cur_tries <= self.__retries:
            try:
                _resp = self.__objectStorage.delete_object(self.__namespace, self.__bucket, aObjectName)

                if not _resp:
                    _cur_tries +=1
                    ebLogTrace(f'Invalid response from OSS: {_resp}')
                elif _resp.status > 210:
                    _cur_tries +=1
                    ebLogTrace(f'Invalid response from OSS: {vars(_resp)}')
                else:
                    return _resp

            except SSLError as e:
                _exception_msg = e
                _cur_tries +=1
                ebLogTrace(f'{e} Retrying... Current retry count: {_cur_tries}')
            except Exception as e:
                _msg = f"Response unexpected: {_resp.__dict__}"
                ebLogError(_msg)
                raise ExacloudRuntimeError(aErrorMsg=_msg) from e

        _err_msg = f'OCI error: {_exception_msg} Please retry operation'
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg

    def mPutOSS(self, aBucket, aObjectName, aObjectContent):

        _cur_tries = 0
        _exception_msg = None
        _resp = None

        while _cur_tries <= self.__retries:
            try:
                _resp = self.__objectStorage.put_object(self.__namespace, aBucket, aObjectName, aObjectContent)

                if not _resp:
                    _cur_tries +=1
                    ebLogTrace(f'Invalid response from OSS: {_resp}')
                elif _resp.status != 200:
                    _cur_tries +=1
                    ebLogTrace(f'Invalid response from OSS: {vars(_resp)}')
                else:
                    return _resp

            except SSLError as e:
                _cur_tries +=1
                _exception_msg = e
                ebLogTrace(f'{e} Retrying... Current retry count: {_cur_tries}')
            except Exception as e:
                _msg = f"Response unexpected"
                if _resp:
                    _msg = f"Response unexpected: {_resp.__dict__}"
                ebLogError(_msg)
                raise ExacloudRuntimeError(aErrorMsg=_msg) from e

        _err_msg = f'OCI error: {_exception_msg} Please retry operation'
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg

    def mGetOSS(self, aBucket, aObjectName):

        _cur_tries = 0
        _exception_msg = None
        while _cur_tries <= self.__retries:
            try:
                _resp = self.__objectStorage.get_object(self.__namespace, aBucket, aObjectName)

                if not _resp:
                    _cur_tries +=1
                    ebLogTrace(f'Invalid response from OSS: {_resp}')
                elif _resp.status != 200:
                    _cur_tries +=1
                    ebLogTrace(f'Invalid response from OSS: {vars(_resp)}')
                else:
                    return _resp

            except SSLError as e:
                _cur_tries +=1
                _exception_msg = e
                ebLogTrace(f'{e} Retrying... Current retry count: {_cur_tries}')
            except Exception as e:
                _msg = f"Response unexpected: {_resp.__dict__}"
                ebLogError(_msg)
                raise ExacloudRuntimeError(aErrorMsg=_msg) from e

        _err_msg = f'OCI error: {_exception_msg} Please retry operation'
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg



    def mDeleteExaKmsEntry(self, aKmsEntry: ExaKmsEntry) -> bool:
        """
        Deletes entry from the object storage and returns True
        if it exists. Otherwise, returns False
        """

        _entryToDelete = aKmsEntry
        if not aKmsEntry.mGetObjectName():
            _entryToDelete = self.mGetExaKmsEntry(aKmsEntry.mGetUniqJSON())

        if not _entryToDelete:
            ebLogWarn(f'{aKmsEntry}')
            return False

        if not _entryToDelete.mGetCryptoClient():
            _entryToDelete.mSetCryptoClient(self.__kmsCryptoClient)

        try:
            _objectName = _entryToDelete.mGetObjectName()
            _obj = self.mGetOSS(self.__bucket, _objectName)
            _objDict = json.loads(_obj.data.content.decode('utf-8'))
            del _objDict[f'id_rsa.{aKmsEntry.mGetFQDN().split(".")[0]}.{aKmsEntry.mGetUser()}']

            if not _objDict:
                self.mDeleteOSS(_objectName)
            else:
                self.mPutOSS(self.__bucket, _objectName, json.dumps(_objDict))

            super().mDeleteExaKmsEntry(aKmsEntry)
            return True

        except Exception as exp:
            ebLogWarn(f'{aKmsEntry}')
            ebLogWarn(f'Could not delete KMS entry from OCI object storage: {exp}')
            return False

    def mInsertExaKmsEntry(self, aKmsEntry: ExaKmsEntry, aPreservateCreationTime = False) -> bool:
        """
        Creates an entry in the object storage given an ExaKmsEntry object.
        Returns True if successful and False if not.
        """

        if not aKmsEntry.mGetCryptoClient():
            aKmsEntry.mSetCryptoClient(self.__kmsCryptoClient)

        if not aKmsEntry.mGetObjectName():
            aKmsEntry.mSetObjectName(aKmsEntry.mGetFQDN())

        try:
            self.mInsertToBucket(aKmsEntry, self.__bucket, aPreservateCreationTime)

            if self.__backupBucket:
                self.mInsertToBucket(aKmsEntry, self.__backupBucket, aPreservateCreationTime)

            super().mInsertExaKmsEntry(aKmsEntry)
            return True

        except Exception as exp:
            ebLogError(f'{aKmsEntry}')
            _err_msg = f'Could not insert KMS entry into OCI object storage: {exp}'
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from exp

    def mBackup(self) -> bool:
        """
        Updates the backup bucket by copying every entry from the main bucket.
        Additionally, it copies the history file (changes.txt).
        Returns True if the backup was successful, False otherwise
        """

        if not self.__backupBucket:
            ebLogWarn('Could not backup the keys. Backup Bucket not set')
            return False

        # Get all entries in main bucket
        self.mSetCache({})
        _entries = self.mSearchExaKmsEntries({}, aRefreshKey=True)

        # Copy each entry into the backup bucket
        _suc = True
        for _entry in _entries:
            try:
                self.mInsertToBucket(_entry, self.__backupBucket)
            except Exception as e:
                ebLogTrace(f"Inserting entry into backup bucket failed: {e}")
                _suc = False

        # Get the current history
        try:
            _obj = self.mGetOSS(self.__bucket, 'changes.txt')
        except Exception:
            ebLogWarn('No history file found. There might not be any keys in the bucket yet.')
            return False

        _newHistory = _obj.data.content.decode('utf-8')

        # Get backup history (if there is none, we simply upload the current history)
        try:
            _obj = self.mGetOSS(self.__backupBucket, 'changes.txt')
            _backupHistory = _obj.data.content.decode('utf-8')
        except Exception:
            self.mPutOSS(self.__backupBucket, 'changes.txt', _newHistory)
            return _suc

        _newHistoryList = _newHistory.split('\n')[3:-1]
        _backupHistoryList = _backupHistory.split('\n')[:-1]
        _lastBackupEntry = _backupHistoryList[-1]

        # Copy all new entries into the backup history
        for i in range(len(_newHistoryList)-1, -1, -1):
            if _newHistoryList[i] <= _lastBackupEntry:
                _backupHistoryList += _newHistoryList[i+1:]
                break
        else:
            # If all of the entries are new, we copy all of them
            _backupHistoryList += _newHistoryList

        # Merge the new entries into the backup history and upload into OSS
        _backupHistory = '\n'.join(_backupHistoryList) + '\n'
        self.mPutOSS(self.__backupBucket, 'changes.txt', _backupHistory)

        return _suc

    def mRestoreBackup(self) -> bool:
        """
        Copies all entries in the backup bucket back into the main bucket
        """

        if not self.__backupBucket:
            ebLogWarn('Could not backup the keys. Backup Bucket not set')
            return False

        # Get all entries in the backup bucket
        self.mSetCache({})
        _entries = self.mSearchExaKmsEntries({}, aRefreshKey=True, aBackup=True)

        # Copy each entry into the main bucket
        _suc = True
        for _entry in _entries:
            _entryDict = {'FQDN': _entry.mGetFQDN(),
                          'user': _entry.mGetUser()}
            _mainEntry = self.mGetExaKmsEntry(_entryDict)
            if not _mainEntry or _mainEntry.mGetCreationTime() < _entry.mGetCreationTime():
                try:
                    self.mInsertToBucket(_entry, self.__bucket)
                except Exception:
                    _suc = False

        return _suc

    def mInsertToBucket(self, aKmsEntry: ExaKmsEntry, aBucket: str, aPreservateCreationTime=False):
        """ Inserts a key to either the main or backup bucket
        """

        _objectName = aKmsEntry.mGetObjectName()

        try:
            _obj = self.mGetOSS(aBucket, _objectName)
        except Exception:
            _obj = None

        # Put entry into object storage
        _objDict = {}
        _encryptedKey = {}

        _encryptedKey['encData'] = aKmsEntry.mGetEncData()
        _encryptedKey['encDEK'] = aKmsEntry.mGetEncDEK()
        _encryptedKey['hostType'] = str(aKmsEntry.mGetHostType().name)
        _encryptedKey['keyValueInfo'] = aKmsEntry.mGetKeyValueInfo()
        _encryptedKey['version'] = aKmsEntry.mGetVersion()
        _encryptedKey["label"] = ExaKmsEntryOCIRSA.mGetCurrentLabel()
        _encryptedKey["exacloud_host"] = ExaKmsEntryOCIRSA.mGetCurrentExacloudHost()

        if aPreservateCreationTime:
            _encryptedKey['creationTime'] = aKmsEntry.mGetCreationTime()
        else:
            _encryptedKey['creationTime'] = ExaKmsEntryOCIRSA.mGetCurrentTime()

        _encryptedKey['hash'] = aKmsEntry.mGetHash()

        if _obj:
            _objDict = json.loads(_obj.data.content.decode('utf-8'))

        _objDict[f'id_rsa.{aKmsEntry.mGetFQDN().split(".")[0]}.{aKmsEntry.mGetUser()}'] = _encryptedKey

        self.mPutOSS(aBucket, _objectName, json.dumps(_objDict))


# end of file
