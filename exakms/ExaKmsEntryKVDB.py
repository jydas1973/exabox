#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsEntryKVDB.py /main/6 2024/12/12 18:39:38 ririgoye Exp $
#
# ExaKmsEntryKVDB.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsEntryKVDB.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    12/05/24 - Bug 37327992 - EXACC EXACLOUD FEDRAMP - FS
#                           ENCRYPTION CPS SYNC UP FAILS WITH DECRYPTION ERROR
#    jfsaldan    11/08/24 - Bug 37239457 - EXACLOUD EXACC FEDRAMP ; FS
#                           ENCRYPTION PASSPHRASE ARE NOT SYNCED PROPERLY
#                           ACROSS CPSES
#    ririgoye    10/15/24 - Backport 37176061 of ririgoye_bug-37076081 from
#                           main
#    ririgoye    10/11/24 - Bug 37160664 - BACKPORT OF BUG 37076081
#    ririgoye    10/14/24 - Bug 37076081 - Added RSA/ECDSA derivated classes.
#    aypaul      02/15/24 - Creation
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
from exabox.core.Error import ExacloudRuntimeError
from exabox.kms.crypt import cryptographyAES
from exabox.exakms.ExaKmsEntry import ExaKmsKVEntry
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsEntryRSA import ExaKmsEntryRSA
from exabox.exakms.ExaKmsEntryECDSA import ExaKmsEntryECDSA
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

class ExaKmsEntryKVDB(ExaKmsKVEntry):

    def __init__(self, aKey, aValue):

        _config = get_gcontext().mGetConfigOptions()

        _basepath = get_gcontext().mGetBasePath()

        if get_gcontext().mCheckRegEntry("MKSTORE_BASEPATH"):
            _basepath = os.path.join(get_gcontext().mGetRegEntry("MKSTORE_BASEPATH"))

        self._aes = cryptographyAES()

        self._db_path = os.path.join(_basepath, "db")
        if 'db_dir' in _config.keys():
            self._db_path = _config['db_dir']

        try:
            os.lstat(self._db_path)
        except:
            _err_msg = f"Invalid db location: {self._db_path}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        self._wallet = os.path.join(self._db_path, "cwallet.sso")
        self._mkstore = os.path.join(_basepath, "dbcli/bin/mkstore")

        ExaKmsKVEntry.__init__(self, aKey, aValue)
        self._wallet_id = None
        self._enc_data = ""
        if aValue:
            self.mCreateEncData(aValue)

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetFQDN(self):
        return self.mGetECHostname()

    def mGetWallet(self):
        return self._wallet

    def mSetWallet(self, aWallet):
        self._wallet = aWallet

    def mGetAES(self):
        return self._aes

    def mSetAES(self, aAES):
        self._aes = aAES

    def mCreateValueFromEncData(self):

        _plaintext_dek = self.mGetWalletId()
        _enc_data = self.mGetEncData()

        _decrypted_value = self.mGetAES().mDecrypt(_plaintext_dek, _enc_data).decode('utf-8')
        self.mSetValue(_decrypted_value.strip())
        return self.mGetValue()

    def mCreateEncData(self, aKey):

        _plaintext_dek = self.mGetWalletId()
        _plaintext_data = aKey.encode("utf-8")

        _enc_data = self.mGetAES().mEncrypt(_plaintext_dek, _plaintext_data).decode('utf-8')
        self.mSetEncData(_enc_data)

    def mGetEncData(self):
        return self._enc_data

    def mSetEncData(self, aData):
        self._enc_data = aData

    def mGetWalletId(self):

        if self._wallet_id:
            return self._wallet_id

        self.mCheckWallet()
        return self._wallet_id

    def mSetWalletId(self, aId):
        self._wallet_id = aId

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
        in the wallet for the key provided. If there is, it sets the id
        attribute to the corresponding id. Otherwise, it creates a new id
        and a new entry in the wallet
        """
        _current_key = self.mGetKey()
        _cmd_prefix = f'{self._mkstore} -wrl {self._db_path}'

        # Create wallet if it does not yet exist
        if not os.path.exists(self.mGetWallet()):
            ebLogTrace(f'*** Create an auto-login wallet using: {_cmd_prefix}')
            self.mExecuteLocal(f'{_cmd_prefix} -createALO')

        if os.path.exists(self.mGetWallet()):

            ebLogTrace(f'*** Check for {_current_key} entry in {self.mGetWallet()}')
            _rc, _out = self.mExecuteLocal(f'{_cmd_prefix} -viewEntry "{_current_key}"')

            # If the key is new, we create its new id and entry in the wallet
            if _rc:
                self.mSetWalletId(uuid.uuid4().hex)
                self.mExecuteLocal(f'{_cmd_prefix} -createEntry "{_current_key}" "{self.mGetWalletId()}"')

            # If the key already had an entry in the wallet, we get its id
            else:
                self.mSetWalletId(_out.strip().split('\n')[-1].split('=')[-1].strip())

            if self.mGetWalletId() is None:
                ebLogError(f'ExaKmsKVDB wallet at {self.mGetWallet()} is corrupted.')

    def mToJson(self):

        _dict = super().mToJson()
        _dict['walletId'] = self._wallet_id
        _dict['encData'] = self._enc_data

        return _dict

    def mFromJson(self, aJson):

        super().mFromJson(aJson)

        if 'walletId' in aJson.keys():
            self.mSetWalletId(aJson['walletId'])

        if 'encData' in aJson.keys():
            self.mSetEncData(aJson['encData'])

#####################
# DERIVATED CLASSES #
#####################

class ExaKmsEntryKVDBECDSA(ExaKmsEntryECDSA, ExaKmsEntryKVDB):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntryKVDB.__init__(self, "", "")
        ExaKmsEntryECDSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntryKeysDBECDSA"

class ExaKmsEntryKVDBRSA(ExaKmsEntryRSA, ExaKmsEntryKVDB):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntryKVDB.__init__(self, "", "")
        ExaKmsEntryRSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntryKeysDBRSA"

# end of file
