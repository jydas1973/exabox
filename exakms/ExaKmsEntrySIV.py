#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsEntrySIV.py /main/4 2023/05/23 13:12:59 jesandov Exp $
#
# ExaKmsEntrySIVRSA.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsEntrySIVRSA.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    alsepulv    05/06/22 - Creation
#


import uuid

from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsEntryRSA import ExaKmsEntryRSA
from exabox.exakms.ExaKmsEntryECDSA import ExaKmsEntryECDSA
from exabox.kms.crypt import cryptographyAES


class ExaKmsEntrySIV(ExaKmsEntry):
    def __init__(self, aFQDN: str, aUser: str, aPrivateKey: str,
                 aHostType: ExaKmsHostType = ExaKmsHostType.UNKNOWN):

        self.__aes = cryptographyAES()

        self.__secretName = None
        self.__encData = None
        self.__keyId = None

        ExaKmsEntry.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)


    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetVersion(self) -> str:
        return "ExaKmsEntrySIVRSA"

    def mGetSecretName(self) -> str:
        return self.__secretName

    def mSetSecretName(self, aName: str) -> None:
        self.__secretName = aName

    def mGetIndexId(self) -> str:
        return f'{self.mGetSecretName()}/{self.mGetFQDN()}'

    def mSetFQDN(self, aFQDN: str) -> None:
        if not aFQDN:
            return

        _fqdn = ExaKmsEntryRSA.mUnmaskNatHost(aFQDN)
        super().mSetFQDN(_fqdn)

        if not self.mGetSecretName() or (self.mGetSecretName().split(".")[0]
                                         == _fqdn.split(".")[0]):
            self.mSetSecretName(_fqdn)

    def mGetKeyId(self) -> str:
        if not self.__keyId:
            self.__keyId = uuid.uuid4().hex

        return self.__keyId

    def mSetKeyId(self, aKeyId) -> None:
        self.__keyId = aKeyId
        self.__encData = None

    def mGetPrivateKey(self) -> str:
        if not self.__encData:
            return ""

        return self.mGetPrivateKeyFromEncData()

    def mSetPrivateKey(self, aKey, aOverride: bool = True) -> None:
        self.mSetPublicKey(None)

        _key = aKey
        if isinstance(aKey, bytes):
            _key = aKey.decode("utf-8")

        if not _key:
            return

        if aOverride:
            self.mCreateEncData(_key)
        self.mSetPublicKey(self.mCalculatePublicKey())
        self.mSetHash(self.mCalculateHash())

    def mSetEncData(self, aEncData: str) -> None:
        self.__encData = aEncData

        self.mSetPublicKey(self.mCalculatePublicKey())
        self.mSetHash(self.mCalculateHash())

    def mGetEncData(self) -> str:
        return self.__encData

    #################
    # CLASS METHODS #
    #################

    def mCreateEncData(self, aKey: str) -> None:
        _plaintextDEK = self.mGetKeyId()
        _plaintextData = aKey.encode("utf-8")

        _encData = self.__aes.mEncrypt(_plaintextDEK,
                                       _plaintextData).decode('utf-8')
        self.mSetEncData(_encData)

    def mGetPrivateKeyFromEncData(self) -> str:
        _plaintextDEK = self.mGetKeyId()
        _encKey = self.__encData

        return self.__aes.mDecrypt(_plaintextDEK,
                                   _encKey).decode("utf-8").strip()

    def mToJsonMinimal(self) -> dict:
        _dict = super().mToJsonMinimal()
        _dict["secretName"] = self.__secretName

        return _dict

    def mToJson(self) -> dict:
        _dict = super().mToJson()
        _dict["secretName"] = self.__secretName
        _dict["keyId"] = self.__keyId
        _dict["encData"] = self.__encData

        return _dict

#####################
# DERIVATED CLASSES #
#####################

class ExaKmsEntrySIVECDSA(ExaKmsEntryECDSA, ExaKmsEntrySIV):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntrySIV.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)
        ExaKmsEntryECDSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntrySIVECDSA"

class ExaKmsEntrySIVRSA(ExaKmsEntryRSA, ExaKmsEntrySIV):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntrySIV.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)
        ExaKmsEntryRSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntrySIVRSA"


# end of file
