#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsEntry.py /main/19 2025/11/24 07:52:19 dekuckre Exp $
#
# ExaKmsEntry.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsEntry.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    01/06/25 - Add PKCS8 and TraditionalOpenSSL Format export
#    ybansod     11/15/24 - Enh 35973125 - EXACS:EXACLOUD:EXAKMS:ADD HASH TO
#                           PUBLIC KEY COMMENT
#    aypaul      02/15/24 - ENH#36243242 Add support for exakms entry of type
#                           KV.
#    jesandov    10/20/23 - 35933990: Include label in ExaKmsEntry
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    aypaul      06/07/22 - Enh#34207528 ExaKms entry history tracking and
#                           generation.
#    jesandov    05/31/22 - Add ExaKms KeyValue Info
#    jesandov    04/27/21 - Creation
#

import os
import re
import json
import enum
import time
import socket
import hashlib

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from exabox.core.Context import get_gcontext

class ExaKmsKeyFormat():
    TRADITIONAL_OPENSSL = ( 
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    )
    PKCS8 = ( 
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )

    @staticmethod
    def mGetName(aFormatType):
        if aFormatType == ExaKmsKeyFormat.TRADITIONAL_OPENSSL:
            return "TRADITIONAL_OPENSSL"
        elif aFormatType == ExaKmsKeyFormat.PKCS8:
            return "PKCS8"
        else:
            return "UNKNOWN"

class ExaKmsOperationType():
    INSERT = "insert"
    DELETE = "delete"

class ExaKmsHostType(enum.Enum):
    UNKNOWN = 0
    DOM0 = 1
    DOMU = 2
    CELL = 3
    SWITCH = 4
    ILOM = 5

class ExaKmsKVEntry:

    def __init__(self, aKey, aValue):
        self.__key = aKey
        self.__value = aValue#Always to contain plaintext value
        self.__label = None
        self.__exacloud_hostname = None
        self.__creation_time = time.strftime('%Y-%m-%d %H:%M:%S%z')

    def mSetKey(self, aKey):
        self.__key = aKey

    def mSetValue(self, aValue):
        self.__value = aValue

    def mSetLabel(self, aLabel=None):
        if aLabel is not None:
            self.__label = aLabel
            return
        _exacloudPath = os.getcwd()
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _labelFile = os.path.join(_exacloudPath, "config", "label.dat")
        _label = "UNKNOWN"

        if os.path.exists(_labelFile):
            with open(_labelFile, "r") as _f:
                _label = _f.read().strip()

        self.__label = _label

    def mSetECHostname(self, aECHostname=None):
        if aECHostname is not None:
            self.__exacloud_hostname = aECHostname
            return
        _fqdn = "UNKNOWN"
        try:
            _fqdn = socket.getfqdn()
        except:
            pass
        self.__exacloud_hostname = _fqdn

    def mSetCreationTime(self, aCreationTime=None):
        if aCreationTime is not None:
            self.__creation_time = aCreationTime
            return
        self.__creation_time = time.strftime('%Y-%m-%d %H:%M:%S%z')

    def mGetKey(self):
        return self.__key

    def mGetValue(self):
        return self.__value

    def mGetLabel(self):
        if not self.__label:
            self.mSetLabel()
        return self.__label

    def mGetECHostname(self):
        if not self.__exacloud_hostname:
            self.mSetECHostname()
        return self.__exacloud_hostname

    def mGetCreationTime(self):
        return self.__creation_time

    def mToJson(self):

        _dict = {}
        _dict['key'] = self.mGetKey()
        _dict['label'] = self.mGetLabel()
        _dict['exacloud_hostname'] = self.mGetECHostname()
        _dict['creation_time'] = self.mGetCreationTime()
        return _dict

    def mFromJson(self, aJson):

        if 'key' in aJson.keys():
            self.mSetKey(aJson['key'])

        if 'label' in aJson.keys():
            self.mSetLabel(aJson['label'])

        if 'exacloud_hostname' in aJson.keys():
            self.mSetECHostname(aJson['exacloud_hostname'])

        if 'creation_time' in aJson.keys():
            self.mSetCreationTime(aJson['creation_time'])


class ExaKmsEntry:

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__publicKey = None
        self.__hostType = None
        self.__fqdn = None
        self.__user = None
        self.__hash = None
        self.__label = "UNKNOWN"
        self.__exacloudHost = "UNKNOWN"
        self.__defaultKeyFormat = ExaKmsKeyFormat.TRADITIONAL_OPENSSL
        self.__keyValueInfo = {}
        self.__creationTime = re.sub("[0-9]", "0", time.strftime('%Y-%m-%d %H:%M:%S%z'))

        self.mSetHostType(aHostType)
        self.mSetFQDN(aFQDN)
        self.mSetUser(aUser)
        self.mSetPrivateKey(aPrivateKey)

    #####################
    # INTERFACE METHODS #
    #####################

    def mSaveToFile(self, aFolder, aForceFilename=None):
        raise NotImplementedError

    def mRestoreFromFile(self, aFile):
        raise NotImplementedError

    def mGetUniqJSON(self):
        raise NotImplementedError

    @staticmethod
    def mGeneratePrivateKey():
        raise NotImplementedError

    def mCalculatePublicKey(self):
        raise NotImplementedError

    def mCalculateHash(self):
        _pkey = self.mGetPrivateKey().encode("utf-8")
        _hash = hashlib.sha256(_pkey).hexdigest()
        return _hash

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetDefaultKeyFormat(self):
        return self.__defaultKeyFormat

    def mSetDefaultKeyFormat(self, aValue):
        self.__defaultKeyFormat = aValue

    def mGetIndexId(self):
        return self.mGetFQDN()

    def mGetPrivateKey(self):
        raise NotImplementedError

    def mSetPrivateKey(self, aStr):
        raise NotImplementedError

    def mGetHash(self):
        return self.__hash

    def mSetHash(self, aValue):
        self.__hash = aValue

    def mGetPublicKey(self, aComment=""):

        if not self.__publicKey:
            self.__publicKey = self.mCalculatePublicKey()

        if self.mGetHostType() in [ExaKmsHostType.SWITCH, ExaKmsHostType.UNKNOWN]:
            if aComment:
                return f"{self.__publicKey} {aComment}".strip() + "\n"
            else:
                return f"{self.__publicKey}".strip() + "\n"
        else:
            if aComment:
                return f"{self.__publicKey} {aComment} [{self.mGetHash()}]".strip() + "\n"
            else:
                return f"{self.__publicKey} [{self.mGetHash()}]".strip() + "\n"

    def mSetPublicKey(self, aStr):
        self.__publicKey = aStr

    def mGetHostType(self):
        return self.__hostType

    def mSetHostType(self, aStr):

        if isinstance(aStr, ExaKmsHostType):
            self.__hostType = aStr
        else:
            self.__hostType = ExaKmsHostType[aStr]

    def mGetLabel(self):
        return self.__label

    def mSetLabel(self, aStr):
        self.__label = aStr

    def mGetExacloudHost(self):
        return self.__exacloudHost

    def mSetExacloudHost(self, aStr):
        self.__exacloudHost = aStr

    def mGetFQDN(self):
        return self.__fqdn

    def mSetFQDN(self, aStr):
        self.__fqdn = ExaKmsEntry.mUnmaskNatHost(aStr)

    def mGetUser(self):
        return self.__user

    def mSetUser(self, aStr):
        self.__user = aStr

    def mGetVersion(self):
        return "ExaKmsEntry"

    def mGetCreationTime(self):
        return self.__creationTime

    def mSetCreationTime(self, aValue):
        self.__creationTime = aValue

    def mGetKeyValueInfo(self):
        return self.__keyValueInfo

    def mSetKeyValueInfo(self, aKV):
        self.__keyValueInfo = aKV

    ##################
    # STATIC METHODS #
    ##################

    @staticmethod
    def mUnmaskNatHost(aHost):

        _host = aHost

        _ctx = get_gcontext()
        if _ctx.mCheckRegEntry('_natHN_{0}'.format(_host)):
            _host = _ctx.mGetRegEntry('_natHN_{0}'.format(_host))

        return _host

    @staticmethod
    def mGetCurrentTime():
        return time.strftime('%Y-%m-%d %H:%M:%S%z')

    @staticmethod
    def mGetCurrentExacloudHost():
        _fqdn = "UNKNOWN"
        try:
            _fqdn = socket.getfqdn()
        except:
            pass
        return _fqdn

    @staticmethod
    def mGetCurrentLabel():

        _exacloudPath = os.getcwd()
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _labelFile = os.path.join(_exacloudPath, "config", "label.dat")
        _label = "UNKNOWN"

        if os.path.exists(_labelFile):
            with open(_labelFile, "r") as _f:
                _label = _f.read().strip()

        return _label

    @staticmethod
    def mPrivateKeyToTraditionalFormat(aKeyStr):

        _key = load_pem_private_key(aKeyStr.encode("utf-8"), None, default_backend())

        _privateKey = _key.private_bytes(*ExaKmsKeyFormat.TRADITIONAL_OPENSSL)
        _privStr = _privateKey.decode("utf-8").strip()

        return _privStr


    #################
    # CLASS METHODS #
    #################

    def mToJsonMinimal(self):

        _dict = {}

        _dict['hostType'] = self.mGetHostType().name
        _dict['FQDN'] = self.mGetFQDN()
        _dict['user'] = self.mGetUser()
        _dict['version'] = self.mGetVersion()
        _dict['creationTime'] = self.mGetCreationTime()
        _dict['label'] = self.mGetLabel()
        _dict['exacloud_host'] = self.mGetExacloudHost()

        return _dict


    def mToJson(self):

        _dict = {}

        _dict['privateKey'] = self.mGetPrivateKey()
        _dict['hostType'] = self.mGetHostType().name
        _dict['FQDN'] = self.mGetFQDN()
        _dict['user'] = self.mGetUser()
        _dict['version'] = self.mGetVersion()
        _dict['creationTime'] = self.mGetCreationTime()
        _dict['hash'] = self.mGetHash()
        _dict['keyValueInfo'] = self.mGetKeyValueInfo()
        _dict['label'] = self.mGetLabel()
        _dict['exacloud_host'] = self.mGetExacloudHost()

        return _dict

    def mFromJson(self, aJson):

        if 'hash' in aJson.keys():
            self.mSetHash(aJson['hash'])

        if 'privateKey' in aJson.keys():
            self.mSetPrivateKey(aJson['privateKey'])

        if 'hostType' in aJson.keys():
            self.mSetHostType(aJson['hostType'])

        if 'FQDN' in aJson.keys():
            self.mSetFQDN(aJson['FQDN'])

        if 'user' in aJson.keys():
            self.mSetUser(aJson['user'])

        if 'label' in aJson.keys():
            self.mSetLabel(aJson["label"])

        if 'exacloud_host' in aJson.keys():
            self.mSetExacloudHost(aJson['exacloud_host'])

        if 'creationTime' in aJson.keys():
            self.mSetCreationTime(aJson['creationTime'])

        if 'keyValueInfo' in aJson.keys():
            self.mSetKeyValueInfo(aJson["keyValueInfo"])

# end of file
