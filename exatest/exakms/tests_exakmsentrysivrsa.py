#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exakmsentrysivrsa.py /main/4 2023/05/23 13:12:59 jesandov Exp $
#
# tests_exakmsentrysivrsa.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakmsentrysivrsa.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    aypaul      10/17/22 - Unit test cases for
#                           exabox/exakms.ExaKmsEntrySIV.py
#    aypaul      10/17/22 - Creation
#
import unittest
import warnings
import time
from unittest import mock
from unittest.mock import patch
from exabox.exakms.ExaKmsEntrySIV import ExaKmsEntrySIVRSA
from exabox.exakms.ExaKmsEntry import ExaKmsHostType

MOCK_JSON_MINIMAL = {'hostType': "DOM0", "FQDN": "mockhostname.oracle.com", "user": "mock_user", "version": "mock_version", "creationTime": time.strftime('%Y-%m-%d %H:%M:%S%z')}


class ebTestExaKmsEntrySIVRSA(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        warnings.filterwarnings("ignore")

    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mGetPrivateKeyFromEncData')
    def test_verify_classvariables(self, mock_unmasknathost, mock_set_privkey, mock_getprivkeyfromencdata):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        self.assertEqual(_exakms_entry_rsa.mGetVersion(), "ExaKmsEntrySIVRSA")
        _exakms_entry_rsa.mSetSecretName("mock_secret_name")
        self.assertEqual(_exakms_entry_rsa.mGetSecretName(), "mock_secret_name")
        self.assertEqual(_exakms_entry_rsa.mGetIndexId(), "mock_secret_name/mockhostname.oracle.com")
        _exakms_entry_rsa.mSetFQDN("anotherhostname.oracle.com")
        _exakms_entry_rsa.mGetKeyId()
        _exakms_entry_rsa.mSetKeyId("mock_key_id")
        self.assertEqual(_exakms_entry_rsa.mGetKeyId(), "mock_key_id")
        _exakms_entry_rsa._ExaKmsEntrySIVRSA__encData = "mock_enc_data"
        _exakms_entry_rsa.mGetPrivateKey()


    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mSetPublicKey')
    @patch('exabox.exakms.ExaKmsEntryRSA.ExaKmsEntryRSA.mCalculatePublicKey')
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mCalculateHash', return_value="mock_hashvalue")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mCreateEncData')
    def test_mSetPrivateKey(self, mock_unmasknathost, mock_setpubkey, mock_calpubkey, mock_sethash, mock_calchash):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        _exakms_entry_rsa.mSetPrivateKey(aKey="mock_key_data".encode())
        self.assertEqual(_exakms_entry_rsa.mGetHash(), "mock_hashvalue")

    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mSetPublicKey')
    @patch('exabox.exakms.ExaKmsEntryRSA.ExaKmsEntryRSA.mCalculatePublicKey')
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mCalculateHash', return_value="mock_hashvalue")
    def test_mSetEncData(self, mock_unmasknathost, mock_set_privkey, mock_setpubkey, mock_calpubkey, mock_sethash):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        _exakms_entry_rsa.mSetEncData("mock_enc_data")
        self.assertEqual(_exakms_entry_rsa.mGetEncData(), "mock_enc_data")

    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetEncData')
    def test_mCreateEncData(self, mock_unmasknathost, mock_set_privkey, mock_setencdata):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        _exakms_entry_rsa.mCreateEncData("mock_enc_key")

    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    @patch('exabox.kms.crypt.cryptographyAES.mDecrypt', return_value="mock_decrypted_value".encode())
    def test_mGetPrivateKeyFromEncData(self, mock_unmasknathost, mock_set_privkey, mock_aes_decrypt):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        self.assertEqual(_exakms_entry_rsa.mGetPrivateKeyFromEncData(), "mock_decrypted_value")


    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mToJsonMinimal', return_value=MOCK_JSON_MINIMAL)
    def test_mToJsonMinimal(self, mock_unmasknathost, mock_set_privkey, mock_super_jsonminimal):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        _exakms_entry_rsa.mSetSecretName("mock_secret_name")
        self.assertEqual(_exakms_entry_rsa.mToJsonMinimal().get('secretName'), "mock_secret_name")

    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mToJson', return_value=MOCK_JSON_MINIMAL)
    def test_mToJson(self, mock_unmasknathost, mock_set_privkey, mock_super_jsonminimal):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        _exakms_entry_rsa.mSetSecretName("mock_secret_name")
        _exakms_entry_rsa.mSetKeyId("mock_key_id")
        self.assertEqual(_exakms_entry_rsa.mToJson().get('keyId'), "mock_key_id")


if __name__ == "__main__":
    unittest.main()
