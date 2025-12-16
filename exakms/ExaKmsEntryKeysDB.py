#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsEntryKeysDB.py /main/12 2023/05/23 13:12:59 jesandov Exp $
#
# ExaKmsEntry.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
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
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    jesandov    04/27/21 - Creation
#

import os
import re
import json
import enum
import uuid
import shlex
import subprocess

from typing import List, Optional, Tuple

from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace

from exabox.kms.crypt import cryptographyAES
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsEntryRSA import ExaKmsEntryRSA
from exabox.exakms.ExaKmsEntryECDSA import ExaKmsEntryECDSA
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

class ExaKmsEntryKeysDB(ExaKmsEntry):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__pkdb = None

        _config = get_gcontext().mGetConfigOptions()

        _basepath = get_gcontext().mGetBasePath()

        if get_gcontext().mCheckRegEntry("MKSTORE_BASEPATH"):
            _basepath = os.path.join(get_gcontext().mGetRegEntry("MKSTORE_BASEPATH"))

        self.__aes = cryptographyAES()

        self.__dbPath = os.path.join(_basepath, "db")
        if 'db_dir' in _config.keys():
            self.__dbPath = _config['db_dir']

        try:
            os.lstat(self.__dbPath)
        except:
            ebLogError('ERR: Invalid wallet location', self.__dbPath)

        self.__wallet = os.path.join(self.__dbPath, "cwallet.sso")
        self.__mkstore = os.path.join(_basepath, "dbcli/bin/mkstore")

        self.__walletId = None
        self.__encData = None

        ExaKmsEntry.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetVersion(self):
        return "ExaKmsEntryKeysDBRSA"

    def mGetPkDB(self):
        return self.__pkdb

    def mSetPkDB(self, aKey):
        self.__pkdb = aKey

        if self.__walletId:
            _privKey = self.mGetPrivateKey()
            self.mSetWalletId(None)
            self.mSetPrivateKey(_privKey)

    def mGetWallet(self):
        return self.__wallet

    def mSetWallet(self, aWallet):
        self.__wallet = aWallet

    def mGetAES(self):
        return self.__aes

    def mSetAES(self, aAES):
        self.__aes = aAES

    def mGetIndexId(self):
        return f"{self.mGetPkDB()}/{self.mGetFQDN()}"

    def mSetFQDN(self, aFQDN):

        if aFQDN:

            _fqdn = ExaKmsEntryKeysDBRSA.mUnmaskNatHost(aFQDN)
            super().mSetFQDN(_fqdn)

            if not self.mGetPkDB():
                self.mSetPkDB(_fqdn)

            if self.mGetPkDB().split(".")[0] == _fqdn.split(".")[0]:
                self.mSetPkDB(_fqdn)

    def mGetPrivateKey(self):

        if self.mGetEncData():
            _pk = self.mCreatePrivateKeyFromEncData()
            return _pk

        return ""

    def mSetPrivateKey(self, aStr):

        self.mSetEncData(None)
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

        _plainTextDEK = self.mGetWalletId()
        _enc = self.mGetEncData()

        _decryptedKey = self.mGetAES().mDecrypt(_plainTextDEK, _enc).decode('utf-8')
        return _decryptedKey.strip()

    def mCreateEncData(self, aKey):

        _plainTextDEK = self.mGetWalletId()
        _data = aKey.encode("utf-8")

        _enc = self.mGetAES().mEncrypt(_plainTextDEK, _data).decode('utf-8')
        self.mSetEncData(_enc)

    def mGetEncData(self):
        return self.__encData

    def mSetEncData(self, aData):
        self.__encData = aData

    def mGetWalletId(self):

        if self.__walletId:
            return self.__walletId

        self.mCheckWallet()
        return self.__walletId

    def mSetWalletId(self, aId):
        self.__walletId = aId

    #################
    # CLASS METHODS #
    #################

    def mExecuteLocal(self, aCmd: str) -> Tuple[int, str]:
        """ Executes the command given
        """

        _args = shlex.split(aCmd)
        _proc = subprocess.Popen(_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _stdOut, _ = wrapStrBytesFunctions(_proc).communicate()
        _rc = _proc.returncode

        return _rc, _stdOut

    def mCheckWallet(self) -> None:
        """
        Creates a wallet if needed. Then, it checks if there is an entry
        in the wallet for the FQDN provided. If there is, it sets the id
        attribute to the corresponding id. Otherwise, it creates a new id
        and a new entry in the wallet
        """
        _dbEntry = self.mGetPkDB()
        _cmdPrefix = f'{self.__mkstore} -wrl {self.__dbPath}'

        # Create wallet if it does not yet exist
        if not os.path.exists(self.mGetWallet()):
            ebLogTrace(f'*** Create an auto-login wallet: {_cmdPrefix}')
            self.mExecuteLocal(f'{_cmdPrefix} -createALO')

        if os.path.exists(self.mGetWallet()):

            ebLogTrace(f'*** Check for {_dbEntry} entry')
            _rc, _out = self.mExecuteLocal(f'{_cmdPrefix} -viewEntry "{_dbEntry}"')

            # If the host is new, we create its new id and entry in the wallet
            if _rc:
                self.mSetWalletId(uuid.uuid4().hex)
                self.mExecuteLocal(f'{_cmdPrefix} -createEntry "{_dbEntry}" "{self.mGetWalletId()}"')

            # If the host already had an entry in the wallet, we get its id
            else:
                self.mSetWalletId(_out.strip().split('\n')[-1].split('=')[-1].strip())

            if self.mGetWalletId() is None:
                ebLogError('*** Wallet is corrupted')

    def mToJsonMinimal(self):

        _dict = super().mToJsonMinimal()
        _dict['PkDB'] = self.__pkdb
        _dict['walletId'] = self.__walletId

        return _dict

    def mToJson(self):

        _dict = super().mToJson()
        _dict['walletId'] = self.__walletId
        _dict['encData'] = self.__encData
        _dict['PkDB'] = self.__pkdb

        return _dict


#####################
# DERIVATED CLASSES #
#####################

class ExaKmsEntryKeysDBECDSA(ExaKmsEntryECDSA, ExaKmsEntryKeysDB):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntryKeysDB.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)
        ExaKmsEntryECDSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntryKeysDBECDSA"

class ExaKmsEntryKeysDBRSA(ExaKmsEntryRSA, ExaKmsEntryKeysDB):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntryKeysDB.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)
        ExaKmsEntryRSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntryKeysDBRSA"


# end of file
