"""
$Header: ecs/exacloud/exabox/kms/vmbkms.py /main/4 2022/08/12 03:58:12 ndesanto Exp $

 Copyright (c) 2021, 2022, Oracle and/or its affiliates.

NAME:
    vmbkms.py - vmbackup to oss - Basic KMS and Object Store functionality

FUNCTION:
    Provide basic Encryption & Decryption API for managing VMBackup to Objectstore

NOTE:


History:

    MODIFIED   (MM/DD/YY)
    ndesanto    04/12/22 - OCI region to come on all ECRA call and be stored on
                           a DB cache.
    ndesanto    01/14/22 - Load the OCI regions configuration file if any.
    gsundara    08/19/21 - fix bug 33246583
    gsundara    06/12/21 - Creation (ER 32994768)
"""
import json
import subprocess
from subprocess import Popen, PIPE

import six
from six.moves import urllib

urlopen = urllib.request.urlopen
URLError = urllib.error.URLError
HTTPError = urllib.error.HTTPError
from datetime import datetime

from exabox.kms.crypt import cryptographyAES
from oci.object_storage import UploadManager
from oci.object_storage.transfer.constants import MEBIBYTE
from oci.key_management.models import GenerateKeyDetails, DecryptDataDetails
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogDebug
from exabox.core.Core import ebExit
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory


class ebKmsVmbObjectStore(object):
    def __init__(self, aExaBoxCluCtrl, aConfig):
        self.__count = 1
        self.__ebox = aExaBoxCluCtrl
        self.__aes = cryptographyAES()

        _factory = ExaOCIFactory()
        self.__object_storage = _factory.get_object_storage_client()
        self.__namespace = self.__object_storage.get_namespace().data
        self.__bucketName = "ecra_vmbackups"

        # KMS init
        self.DEFAULT_KEY_LENGTH = 32
        self.DEFAULT_KEY_ALGORITHM = "AES"
        self.__kms_key_id = self.__ebox.mCheckConfigOption("kms_key_id")
        self.__key_shape = {"algorithm": self.DEFAULT_KEY_ALGORITHM, "length": self.DEFAULT_KEY_LENGTH}
        self.__crypto_endpoint = self.__ebox.mCheckConfigOption("kms_dp_endpoint")
        self.__kmsCryptoClient = _factory.get_crypto_client(self.__crypto_endpoint)

        self.mResetBkupDict()

    def mGetBkupDict(self):
        return json.dumps(self.__bkupdict)

    def mSetBkupDict(self, aDek, aHash, aEncHash):
        self.__bkupdict['dek'] = aDek
        self.__bkupdict['hash'] = aHash
        self.__bkupdict['enchash'] = aEncHash

    def mResetBkupDict(self):
        self.__bkupdict = {}

    def mGetAES(self):
        return self.__aes

    def mDeleteObject(self, aObjectName):
        try:
            return 0, self.__object_storage.delete_object(self.__namespace, self.__bucketName, aObjectName)
        except Exception as e:
            return 1, str(e)

    def mUploadObject(self, aObjectName, aData):
        return self.__object_storage.put_object(self.__namespace, self.__bucketName, aObjectName, aData)

    def mUploadFileObject(self, aObjectName, aFile):
        with open(aFile, 'rb') as f:
            self.__object_storage.put_object(self.__namespace, self.__bucketName, aObjectName, f)

    def mUploadMultiPartFileObject(self, aObjectName, aFile):
        # upload manager will automatically use mutlipart uploads if the part size is less than the file size
        part_size = 20 * MEBIBYTE  # part size (in bytes)
        upload_manager = UploadManager(self.__object_storage, allow_parallel_uploads=True, parallel_process_count=3)
        return upload_manager.upload_file(
            self.__namespace, self.__bucketName, aObjectName, aFile, part_size=part_size,
            progress_callback=self.progress_callback)

    def mGetObject(self, aObjectName):
        try:
            return 0, self.__object_storage.get_object(
                self.__namespace,
                self.__bucketName,
                aObjectName)
        except Exception as e:
            return 1, str(e)

    def mListObjects(self):
        try:
            return 0, json.loads(
                str(self.__object_storage.list_objects(
                    self.__namespace, self.__bucketName).data))['objects']
        except Exception as e:
            return 1, str(e)

    # Pagination is needed for 1000+ objects in a bucket
    def mSearchAllObjectsByName(self, aObjname):
        for obj in self.mListObjects():
            if obj['name'] == aObjname:
                return True
        return False

    def progress_callback(self, bytes_uploaded):
        ebLogDebug("{0} {1} additional bytes uploaded".format(self.__count, bytes_uploaded))
        self.__count += 1

    # KMS MODE
    def mGenerateDataEncryptionKey(self):
        _gkd = GenerateKeyDetails()
        _gkd.key_id = self.__kms_key_id
        _gkd.include_plaintext_key = True
        _gkd.key_shape = self.__key_shape
        _crypto_gen_dek = self.__kmsCryptoClient.generate_data_encryption_key(generate_key_details=_gkd)
        return json.loads(str(_crypto_gen_dek.data))["ciphertext"]

    # KMS MODE
    def mDecryptData(self, aCiphertext):
        _ddd = DecryptDataDetails()
        _ddd.key_id = self.__kms_key_id
        _ddd.ciphertext = aCiphertext
        _crypto_decrypt = self.__kmsCryptoClient.decrypt(decrypt_data_details=_ddd)
        return json.loads(str(_crypto_decrypt.data))["plaintext"]

    # KMS MODE
    def mPutKms(self, aObjectName, aFile, aHash):
        _local_hash = aHash
        _cipherTextDEK = self.mGenerateDataEncryptionKey()
        _plainTextDEK = self.mDecryptData(_cipherTextDEK)

        startTime = datetime.now()
        _p = Popen(
            ['/usr/bin/openssl', 'enc', '-aes-256-cbc', '-md', 'sha256', '-in', aFile, '-out', aFile + '.enc', '-pass',
             'env:PASS', '-a'], shell=False,
            env={'PASS': _plainTextDEK}, stdin=PIPE, stdout=PIPE)
        _p.communicate()

        ebLogInfo('Encryption time : ' + str(datetime.now() - startTime))

        # Upload the encrypted private data to Casper bucket ecra-vmbackups
        startTime = datetime.now()
        _resp = self.mUploadMultiPartFileObject(aObjectName, aFile + '.enc')
        ebLogInfo('Upload time : ' + str(datetime.now() - startTime))

        # CHECK for successful upload to objectstore _rc
        _o = subprocess.check_output(['/usr/bin/md5sum', aFile + '.enc']).decode()
        _local_enc_hash = _o.strip().split(' ')[0]
        # ebLogInfo(_local_enc_hash)

        self.mSetBkupDict(_cipherTextDEK, _local_hash, _local_enc_hash)
        # ebLogInfo(self.mGetBkupDict())
        self.mUploadObject(aObjectName + '.details', self.mGetBkupDict())

    # KMS MODE
    def mGetKms(self, aObjectName, aFile):
        _cipherTextDEK = ''
        _oss_hash = ''
        _oss_enc_hash = ''
        _rc, _resp = self.mGetObject(aObjectName + '{}'.format('.details'))
        if not _rc:
            _dict = json.loads(_resp.data.content)
            _cipherTextDEK = _dict['dek']
            _oss_hash = _dict['hash']
            _oss_enc_hash = _dict['enchash']
        else:
            ebLogError('*** Failed to download details file from objectstore')
            ebExit(-1)

        _plainTextDEK = self.mDecryptData(_cipherTextDEK)

        startTime = datetime.now()
        _rc, _resp = self.mGetObject(aObjectName)
        with open(aFile + '.enc_dw', 'wb') as f:
            for chunk in _resp.data.raw.stream(1024 * 1024, decode_content=False):
                f.write(chunk)
        ebLogInfo('Download time : ' + str(datetime.now() - startTime))

        _o = subprocess.check_output(['/usr/bin/md5sum', aFile + '.enc_dw']).decode()
        _local_enc_hash = _o.strip().split(' ')[0]
        if _oss_enc_hash != _local_enc_hash:
            ebLogError('*** Failed to download {} from Objectstore'.format(aFile))
            subprocess.check_output(['rm', '-f', aFile + '.enc_dw'], stderr=subprocess.STDOUT)
            ebExit(-1)

        ebLogInfo('*** Download of the encrypted backup is complete')

        startTime = datetime.now()
        _p = Popen(
            ['/usr/bin/openssl', 'enc', '-md', 'sha256', '-d', '-in', aFile + '.enc_dw', '-out', aFile + '.dec',
             '-aes-256-cbc', '-pass', 'env:PASS', '-a'], shell=False,
            env={'PASS': _plainTextDEK}, stdin=PIPE, stdout=PIPE)
        _p.communicate()

        ebLogInfo('Decryption time : ' + str(datetime.now() - startTime))

        subprocess.check_output(['rm', '-f', aFile + '.enc_dw'], stderr=subprocess.STDOUT)

        _o = subprocess.check_output(['/usr/bin/md5sum', aFile + '.dec']).decode()
        _local_dec_hash = _o.strip().split(' ')[0]
        if _oss_hash != _local_dec_hash:
            ebLogError('*** Failed to decrypt {}'.format(aFile))
            subprocess.check_output(['rm', '-f', aFile + '.dec'], stderr=subprocess.STDOUT)
            ebExit(-1)

        subprocess.check_output(['mv', aFile + '.dec', aFile], stderr=subprocess.STDOUT)

        ebLogInfo('*** Decryption of the backup is complete')

        return _local_dec_hash
