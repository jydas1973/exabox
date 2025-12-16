import six
import json
import os
import shlex
from subprocess import Popen, PIPE, STDOUT
from six.moves import urllib
urlopen = urllib.request.urlopen
URLError = urllib.error.URLError
HTTPError = urllib.error.HTTPError

from oci.key_management.models import GenerateKeyDetails, DecryptDataDetails

from exabox.log.LogMgr import ebLogInit, ebLogInfo, ebLogError, ebLogVerbose, ebLogWarn
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.kms.crypt import cryptographyAES
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory

DEVNULL = open(os.devnull, 'wb')

class ebKmsObjectStore(object):
    def __init__(self, aCtx, bucketName="ecra-keys"):
        """
            bucketName can be "ecra-keys","ExadataSystemFirstBootRepo"
        """

        _context = aCtx
        _oci_factory = ExaOCIFactory()
        self.__object_storage = _oci_factory.get_object_storage_client()
        self.__namespace = self.__object_storage.get_namespace().data
        self.__bucketName = bucketName

        # KMS init
        self.DEFAULT_KEY_LENGTH = 32
        self.DEFAULT_KEY_ALGORITHM = "AES"
        self.__kms_key_id = _context.mGetConfigOptions().get("kms_key_id", "")
        self.__key_shape = {"algorithm": self.DEFAULT_KEY_ALGORITHM, "length": self.DEFAULT_KEY_LENGTH}
        self.__crypto_endpoint = _context.mGetConfigOptions().get("kms_dp_endpoint", "")
        self.__kmsCryptoClient = _oci_factory.get_crypto_client(self.__crypto_endpoint)

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]
        self.__cluster_keys = self.__exacloudPath + '/clusters/keys/'
        self.__aes = cryptographyAES()

    def mGetAES(self):
        return self.__aes

    def mGetClusterKeyDir(self):
        return self.__cluster_keys

    def mExecuteLocal(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE):

        _current_dir = aCurrDir
        _stdin = aStdIn
        _stdout = aStdOut
        _stderr = aStdErr

        _cmd_list = shlex.split(aCmd)

        # Call the process
        _proc = Popen(_cmd_list, stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=_current_dir)
        _std_out, _std_err = wrapStrBytesFunctions(_proc).communicate()
        _rc = _proc.returncode

        return _rc, _std_out, _std_err

    def mDeleteOndiskKeys(self, aKeyFile):
        _key_file = aKeyFile

        self.mExecuteLocal("rm -rf %s" % (_key_file), aCurrDir=self.__cluster_keys)
        self.mExecuteLocal("rm -rf %s.pub" % (_key_file), aCurrDir=self.__cluster_keys)

    def mDeleteObject(self, aObjectName):
        try:
            return 0, self.__object_storage.delete_object(self.__namespace, self.__bucketName, aObjectName)
        except Exception as e:
            return 1, str(e)

    def mUploadObject(self, aObjectName, aData):
        try:
            return 0, self.__object_storage.put_object(
                self.__namespace,
                self.__bucketName,
                aObjectName,
                aData)
        except Exception as e:
            return 1, str(e)

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

    def mObjectAvailable(self, aObjectName):
        _dek_data_dict = {}
        _rc = 0
        _rc, _resp = self.mGetObject(aObjectName)
        if not _rc:
            _dek_data_dict = json.loads(_resp.data.content)
        return _dek_data_dict

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
    def mEncryptKey(self, aPrivKeyFile, aDict):
        _pk = os.path.basename(aPrivKeyFile)
        if (len(aDict) != 0 and _pk not in aDict) or (len(aDict) == 0):
            aDict[_pk] = {}
        # Generate DEK
        _cipherTextDEK = self.mGenerateDataEncryptionKey()
        _plainTextDEK = self.mDecryptData(_cipherTextDEK)

        with open(aPrivKeyFile, 'rb') as f:
            _privkey_str = f.read()
        _encryptedPrivateData = self.mGetAES().mEncrypt(_plainTextDEK, _privkey_str).decode("utf-8")

        aDict[_pk]["encDEK"] = _cipherTextDEK
        aDict[_pk]["encData"] = _encryptedPrivateData
        return aDict

    def mDecryptPrivateData(self, aEncryptedElement):

        _cipherTextDEK = aEncryptedElement["encDEK"]
        _encryptedPrivateData = aEncryptedElement["encData"]

        _plainTextDEK = self.mDecryptData(_cipherTextDEK)

        return None, self.mGetAES().mDecrypt(_plainTextDEK, _encryptedPrivateData)

    # KMS MODE
    def mDecryptKey(self, aEncKeys, aDir=None):
        _keysdir = self.mGetClusterKeyDir()
        if aDir is not None:
            _keysdir = aDir
        for k, v in six.iteritems(aEncKeys):
            if (k != 'rack'):

                _decryptedPrivateData = self.mDecryptPrivateData(v)[1].decode("utf-8")

                # update the global ctx
                _pubkeyfile = _keysdir + '/' + k + '.pub'

                if  os.path.exists(_keysdir):
                        _file = _keysdir + '/' + k
                        with open(_file, 'wb') as f:
                            f.write("{}".format(_decryptedPrivateData).encode('utf8'))
                        os.chmod(_file, 0o600)
                        self.mRegeneratePubKey(k, _keysdir)

    def mExportKeys(self, aHostname):
        _keysdir = self.mGetClusterKeyDir()
        _key_file = 'id_rsa.' + aHostname.split('.')[0] + '.root'
        if _key_file is not None and aHostname is not None:
           _file_path = _keysdir + _key_file
           if os.path.isfile(_file_path):
               self.mPutKey(aHostname, _file_path)
               ebLogInfo('*** Exported key {} successfully'.format(aHostname))
           else:
               ebLogInfo('file not exists')
           self.mDeleteOndiskKeys(_file_path)

    def mImportKeys(self, aHostname, aDir=None):
        self.mGetKey(aHostname, aDir)
        ebLogInfo('*** Imported key {} successfully'.format(aHostname))

    # KMS MODE
    def mPutKey(self, aObjectName, aPrivKeyFile):
        _dek_data_dict = self.mEncryptKey(aPrivKeyFile, self.mObjectAvailable(aObjectName))
        # Upload the encrypted private data to Casper into its corresponding bucket
        return self.mUploadObject(aObjectName, json.dumps(_dek_data_dict))

    # KMS MODE
    def mGetKey(self, aObjectName, aDir=None):
        _encKeys = {}
        _rc, _resp = self.mGetObject(aObjectName)
        if not _rc:
            _encKeys = json.loads(_resp.data.content)
        return 0, self.mDecryptKey(_encKeys, aDir)  # get a single private key only

    def mRegeneratePubKey(self, aPrivKey, aDir):
        aPrivKey = aDir + aPrivKey
        _cmd_str = '/bin/ssh-keygen -f %s -y' %(aPrivKey)
        _rc, _std_out, _std_err = self.mExecuteLocal(_cmd_str, aCurrDir=aDir)

        with open(aPrivKey + '.pub', 'w') as _fp:
            _fp.write(_std_out)

        _cmd_str = '/bin/chmod 0600 %s' %(aPrivKey + '.pub')
        _rc, _std_out, _std_err = self.mExecuteLocal(_cmd_str, aCurrDir=aDir, aStdOut=DEVNULL, aStdErr=DEVNULL)

    def mDeleteKeys(self, aObjectName):
        ebLogInfo('*** KMS: Deleting all keys for %s cluster' % (aObjectName))
        return self.mDeleteObject(aObjectName)
