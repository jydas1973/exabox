#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsEntryRSA.py /main/10 2025/01/07 14:09:31 jesandov Exp $
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
#    joysjose    08/05/24 - Bug 36283884 UNHANDLED EXCEPTION EXAKMSENTRY FAILS
#                           TO MRESTOREFROMFILE WHEN THE FILE IS CORRUPTED
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    jesandov    04/27/21 - Creation
#

import os
import re
import json
import enum

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType, ExaKmsKeyFormat
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogTrace

class ExaKmsEntryRSA(ExaKmsEntry):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):
        ExaKmsEntry.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    #####################
    # INTERFACE METHODS #
    #####################

    def mGetVersion(self):
        return "ExaKmsEntryRSA"

    def __str__(self):
        return f"[{self.mGetVersion()}] [{self.mGetHash()}] {self.mGetUser()}@{self.mGetFQDN()}"

    def mSaveToFile(self, aFolder, aForceFilename=None):

        # Save private key
        _privfile = os.path.join(aFolder, "id_rsa.{0}.{1}")
        _privfile = _privfile.format(self.mGetFQDN().split(".")[0], self.mGetUser())

        if aForceFilename:
            _privfile = aForceFilename

        with open(_privfile, "w") as _f:

            # Export the key in the environment specific key format
            _privStr = self.mGetPrivateKey()
            _key = load_pem_private_key(_privStr.encode("utf-8"), None, default_backend())

            _privateKey = _key.private_bytes(*self.mGetDefaultKeyFormat())
            _privStr = _privateKey.decode("utf-8").strip()

            _f.write(_privStr)
            _f.write("\n")

        os.chmod(_privfile, 0o600)
        ebLogTrace(f"Saved {self} in: {_privfile} with format {ExaKmsKeyFormat.mGetName(self.mGetDefaultKeyFormat())}")

        # Save public key
        _pubfile = f"{_privfile}.pub"
        _pubfile = _pubfile.format(self.mGetFQDN().split(".")[0], self.mGetUser())

        with open(_pubfile, "w") as _f:
            _f.write(self.mGetPublicKey())
            _f.write("\n")
        os.chmod(_pubfile, 0o600)

    def mRestoreFromFile(self, aFile):
        # Always save the keys in ExaKmsKeyFormat.TRADITIONAL_OPENSSL

        _isKey = False

        if os.path.isfile(aFile):
            with open(aFile, "rb") as _f:
                _content = _f.read().strip()
                if b"RSA" in _content or b"BEGIN PRIVATE" in _content:
                    _isKey = True

        _patt = re.search("id_[\\w]+\\.([\\w\\_\\-]+).([\\w\\_\\-]+)$", aFile)

        if _patt and _isKey:

            try:

                self.mSetFQDN(_patt.group(1))
                self.mSetUser(_patt.group(2))

                with open(aFile, "r") as _f:
                    _priv = _f.read().strip()
                    if _priv:

                        _key = load_pem_private_key(_priv.encode("utf-8"), None, default_backend())
                        _privateKey = _key.private_bytes(*ExaKmsKeyFormat.TRADITIONAL_OPENSSL)

                        _priv = _privateKey.decode("utf-8").strip()
                        self.mSetPrivateKey(_priv)

                        return True

                    return False

            except Exception as e:
                ebLogError(f"mRestoreFromFile failed with Error: {str(e)}")
                return False

        return False

    def mGetUniqJSON(self):

        _dict = {}

        _dict['FQDN'] = self.mGetFQDN()
        _dict['user'] = self.mGetUser()

        return _dict

    @staticmethod
    def mGeneratePrivateKey():
        # Always save the keys in ExaKmsKeyFormat.TRADITIONAL_OPENSSL

        _key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=2048
        )

        _privateKey = _key.private_bytes(*ExaKmsKeyFormat.TRADITIONAL_OPENSSL)

        return _privateKey.decode("utf-8").strip()

    def mCalculatePublicKey(self):

        _privkey = self.mGetPrivateKey().encode("utf-8")
        _key = load_pem_private_key(_privkey, None, default_backend())

        _publicKey = _key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH
        )

        return f"{_publicKey.decode('utf-8')} ExaKms"

# end of file
