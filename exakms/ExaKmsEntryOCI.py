#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsEntryOCI.py /main/11 2023/05/23 13:12:59 jesandov Exp $
#
# ExaKmsEntryOCIRSA.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsEntryOCIRSA.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    jesandov    06/23/21 - Creation
#


from exabox.core.Context import get_gcontext
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsEntryRSA import ExaKmsEntryRSA
from exabox.exakms.ExaKmsEntryECDSA import ExaKmsEntryECDSA
from exabox.kms.crypt import cryptographyAES
from oci.key_management.models import GenerateKeyDetails, DecryptDataDetails


class ExaKmsEntryOCI(ExaKmsEntry):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__objectName = None

        self.__aes = cryptographyAES()
        self.__kmsKeyId = get_gcontext().mCheckConfigOption('kms_key_id')

        self.__encDEK = None
        self.__encData = None
        self.__cryptoClient = None

        ExaKmsEntry.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetVersion(self):
        return "ExaKmsEntryOCIRSA"

    def mGetObjectName(self):
        return self.__objectName

    def mSetObjectName(self, aName):
        self.__objectName = aName

    def mGetAES(self):
        return self.__aes

    def mSetAES(self, aAES):
        self.__aes = aAES

    def mGetCryptoClient(self):
        return self.__cryptoClient

    def mSetCryptoClient(self, aCryptoClient):
        self.__cryptoClient = aCryptoClient

    def mGetKmsKeyId(self):
        return self.__kmsKeyId

    def mGetIndexId(self):
        return f'{self.mGetObjectName()}/{self.mGetFQDN()}'

    def mSetFQDN(self, aFQDN):

        if aFQDN:

            _fqdn = ExaKmsEntryOCIRSA.mUnmaskNatHost(aFQDN)
            super().mSetFQDN(_fqdn)

            if not self.mGetObjectName():
                self.mSetObjectName(_fqdn)

            if self.mGetObjectName().split(".")[0] == _fqdn.split(".")[0]:
                self.mSetObjectName(_fqdn)

    def mGetPrivateKey(self):
        _pk = self.mCreatePrivateKeyFromEncData()
        return _pk

    def mSetPrivateKey(self, aStr):

        self.mSetEncData(None)
        self.mSetEncDEK(None)
        self.mSetPublicKey(None)

        _key = aStr
        if isinstance(aStr, bytes):
            _key = aStr.decode("utf-8")

        if _key:
            self.mCreateEncData(_key)
            self.mGetPrivateKey()
            self.mSetPublicKey(self.mCalculatePublicKey())
            self.mSetHash(self.mCalculateHash())

    def mGetPublicKey(self, aComment=""):

        # Generate private key and public key pair
        self.mGetPrivateKey()

        # Return public key
        return super().mGetPublicKey(aComment)

    def mCreatePrivateKeyFromEncData(self):
        _encryptedKey = self.mGetEncData()
        _plainEncryptionKey = self.mGetPlainEncryptionKey()

        _decryptedKey = self.mGetAES().mDecrypt(_plainEncryptionKey, _encryptedKey).decode('utf-8')
        return _decryptedKey.strip()

    def mCreateEncData(self, aKey):

        _data = aKey.encode('utf-8')
        _plainEncryptionKey = self.mGetPlainEncryptionKey()
        _encryptedData = self.mGetAES().mEncrypt(_plainEncryptionKey, _data).decode('utf-8')

        self.mSetEncData(_encryptedData)

    def mGetEncData(self):
        return self.__encData

    def mSetEncData(self, aData):
        self.__encData = aData

    def mGetEncDEK(self):
        if not self.__encDEK:
            _dek = self.mGenerateDEK()
            self.mSetEncDEK(_dek)

        return self.__encDEK

    def mSetEncDEK(self, aDEK):
        self.__encDEK = aDEK

    def mGetPlainEncryptionKey(self):
        _dataDetails = DecryptDataDetails()
        _dataDetails.key_id = self.__kmsKeyId
        _dataDetails.ciphertext = self.mGetEncDEK()

        _decryptedDEK = self.mGetCryptoClient().decrypt(decrypt_data_details = _dataDetails)

        return _decryptedDEK.data.plaintext

    #################
    # CLASS METHODS #
    #################

    def mGenerateDEK(self):
        _keyDetails = GenerateKeyDetails()
        _keyDetails.key_id = self.__kmsKeyId
        _keyDetails.include_plaintext_key = True
        _keyDetails.key_shape = {'algorithm': 'AES', 'length': 32}

        _dek = self.mGetCryptoClient().generate_data_encryption_key(generate_key_details = _keyDetails)
        return _dek.data.ciphertext

    def mToJsonMinimal(self):
        _dict = super().mToJsonMinimal()
        _dict['objectName'] = self.__objectName
        return _dict

    def mToJson(self):
        _dict = super().mToJson()

        _dict['encDEK'] = self.__encDEK
        _dict['encData'] = self.__encData
        _dict['objectName'] = self.__objectName

        return _dict

#####################
# DERIVATED CLASSES #
#####################

class ExaKmsEntryOCIECDSA(ExaKmsEntryECDSA, ExaKmsEntryOCI):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntryOCI.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)
        ExaKmsEntryECDSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntryOCIECDSA"

class ExaKmsEntryOCIRSA(ExaKmsEntryRSA, ExaKmsEntryOCI):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntryOCI.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)
        ExaKmsEntryRSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntryOCIRSA"


# end of file
