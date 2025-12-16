#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exakmsentryocirsa.py /main/4 2023/05/23 13:12:59 jesandov Exp $
#
# tests_exakmsentryocirsa.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakmsentryocirsa.py - <one-line expansion of the name>
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
#                           exabox/exakms.ExaKmsEntryOCI.py
#    aypaul      10/17/22 - Creation
#
import unittest
import warnings
import time
from unittest import mock
from unittest.mock import patch
from exabox.exakms.ExaKmsEntryOCI import ExaKmsEntryOCIRSA
from exabox.exakms.ExaKmsEntry import ExaKmsHostType

MOCK_KMS_KEYID = """ocid1.key.oc1.iad.bbpocc72aaeuk.abuwcljscilpg4wpl3pkqkkmvib77tbhj4cs5uxvg54dtnmvsfbuokkwqkcq"""
MOCK_JSON_MINIMAL = {'hostType': "DOM0", "FQDN": "mockhostname.oracle.com", "user": "mock_user", "version": "mock_version", "creationTime": time.strftime('%Y-%m-%d %H:%M:%S%z')}

class mockContext(object):

    def __init__(self, _json):
        self.__config = _json

    def mCheckConfigOption(self, key):
        return self.__config[key]

class ebTestExaKmsEntryOCIRSA(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        warnings.filterwarnings("ignore")

    @patch('exabox.exakms.ExaKmsEntryOCI.get_gcontext', return_value=mockContext({'kms_key_id': MOCK_KMS_KEYID}))
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mGenerateDEK', return_value="mockDEKvalue")
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mSetPrivateKey')
    def test_verify_classvariables(self, mock_context, mock_unmasknathost, mock_superunmaskhost, mock_dekvalue, mock_set_privatekeykey):
        _exakms_entry_rsa = ExaKmsEntryOCIRSA(aFQDN="mockhostname.oracle.com", aUser="mock_user", aPrivateKey="mock_private_key", aHostType=ExaKmsHostType.DOM0)
        self.assertEqual(_exakms_entry_rsa.mGetKmsKeyId(), MOCK_KMS_KEYID)
        self.assertEqual(_exakms_entry_rsa.mGetVersion(), "ExaKmsEntryOCIRSA")
        self.assertEqual(_exakms_entry_rsa.mGetObjectName(), "mockhostname.oracle.com")
        _exakms_entry_rsa.mSetObjectName("anotherhostname.oracle.com")
        self.assertEqual(_exakms_entry_rsa.mGetObjectName(), "anotherhostname.oracle.com")
        if str(type(_exakms_entry_rsa.mGetAES())) != "<class 'exabox.kms.crypt.cryptographyAES'>":
            raise Exception("mGetAES verification has failed.")
        _exakms_entry_rsa.mSetCryptoClient("mock_crypto_client")
        self.assertEqual(_exakms_entry_rsa.mGetCryptoClient(), "mock_crypto_client")
        self.assertEqual(_exakms_entry_rsa.mGetIndexId(), "anotherhostname.oracle.com/mockhostname.oracle.com")

    @patch('exabox.exakms.ExaKmsEntryOCI.get_gcontext', return_value=mockContext({'kms_key_id': MOCK_KMS_KEYID}))
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mCreateEncData')
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mGetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mSetPublicKey')
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mSetHash')
    @patch('exabox.exakms.ExaKmsEntryRSA.ExaKmsEntryRSA.mCalculatePublicKey', return_value="mock_pub_key ExaKms")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mCalculateHash')
    def test_mSetPrivateKey(self, mock_context, mock_unmaskhost, mock_superunmaks_host, mock_encdata, mock_getprivate_key, \
    mock_setpublickey, mock_sethash, mock_mcalcpubkey, mock_mcalchash):
        _exakms_entry_rsa = ExaKmsEntryOCIRSA(aFQDN="mockhostname.oracle.com", aUser="mock_user", aPrivateKey="mock_private_key", aHostType=ExaKmsHostType.DOM0)
        _exakms_entry_rsa.mSetPrivateKey("mock_private_key".encode())


    @patch('exabox.exakms.ExaKmsEntryOCI.get_gcontext', return_value=mockContext({'kms_key_id': MOCK_KMS_KEYID}))
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mGetEncData', return_value='U2FsdGVkX1+le9MME3wJfcoRmtqlSehLjy3M3TbWRMb70d+vKk3PPW1DMQYQ')
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mGetPlainEncryptionKey', return_value="mock_plain_enckey")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mGetPublicKey', return_value="super_publickey")
    def test_mCreatePrivateKeyFromEncData(self, mock_context, mock_unmaskhost, mock_superunmaskhost, mock_msetpriv_key,\
    mock_genencdata, mock_getplainenckey, mock_super_pubkey):
        _exakms_entry_rsa = ExaKmsEntryOCIRSA(aFQDN="mockhostname.oracle.com", aUser="mock_user", aPrivateKey="mock_private_key", aHostType=ExaKmsHostType.DOM0)
        self.assertEqual(_exakms_entry_rsa.mCreatePrivateKeyFromEncData(), "mock_enc_data")
        self.assertEqual(_exakms_entry_rsa.mGetPublicKey(), "super_publickey")


    @patch('exabox.exakms.ExaKmsEntryOCI.get_gcontext', return_value=mockContext({'kms_key_id': MOCK_KMS_KEYID}))
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mGetPlainEncryptionKey', return_value="mock_plain_enckey")
    def test_mCreateEncData(self, mock_context, mock_unmaskhost, mock_superunmaskhost, mock_msetpriv_key, mock_getplainenckey):
        _exakms_entry_rsa = ExaKmsEntryOCIRSA(aFQDN="mockhostname.oracle.com", aUser="mock_user", aPrivateKey="mock_private_key", aHostType=ExaKmsHostType.DOM0)
        _exakms_entry_rsa.mCreateEncData("mock_plain_data")
        self.assertEqual(_exakms_entry_rsa.mCreatePrivateKeyFromEncData(), "mock_plain_data")


    @patch('exabox.exakms.ExaKmsEntryOCI.get_gcontext', return_value=mockContext({'kms_key_id': MOCK_KMS_KEYID}))
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mGenerateDEK', return_value="mock_dek_value")
    def test_mGetEncDEK(self, mock_context, mock_unmaskhost, mock_superunmaskhost, mock_msetpriv_key, mock_gendek):
        _exakms_entry_rsa = ExaKmsEntryOCIRSA(aFQDN="mockhostname.oracle.com", aUser="mock_user", aPrivateKey="mock_private_key", aHostType=ExaKmsHostType.DOM0)
        self.assertEqual(_exakms_entry_rsa.mGetEncDEK(), "mock_dek_value")

    @patch('exabox.exakms.ExaKmsEntryOCI.get_gcontext', return_value=mockContext({'kms_key_id': MOCK_KMS_KEYID}))
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mToJsonMinimal', return_value=MOCK_JSON_MINIMAL)
    def test_mToJsonMinimal(self, mock_context, mock_unmaskhost, mock_superunmaskhost, mock_msetpriv_key, mock_super_jsonminimal):
        _exakms_entry_rsa = ExaKmsEntryOCIRSA(aFQDN="mockhostname.oracle.com", aUser="mock_user", aPrivateKey="mock_private_key", aHostType=ExaKmsHostType.DOM0)
        _current_json_minimal = _exakms_entry_rsa.mToJsonMinimal()
        self.assertEqual(_current_json_minimal.get("objectName"), "mockhostname.oracle.com")


    @patch('exabox.exakms.ExaKmsEntryOCI.get_gcontext', return_value=mockContext({'kms_key_id': MOCK_KMS_KEYID}))
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntryOCI.ExaKmsEntryOCIRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mToJson', return_value=MOCK_JSON_MINIMAL)
    def test_mToJson(self, mock_context, mock_unmaskhost, mock_superunmaskhost, mock_msetpriv_key, mock_super_json):
        _exakms_entry_rsa = ExaKmsEntryOCIRSA(aFQDN="mockhostname.oracle.com", aUser="mock_user", aPrivateKey="mock_private_key", aHostType=ExaKmsHostType.DOM0)
        _exakms_entry_rsa.mSetEncDEK("mock_enc_dek")
        _exakms_entry_rsa.mSetEncData("mock_enc_data")
        _current_json = _exakms_entry_rsa.mToJson()
        self.assertEqual(_current_json.get("encDEK"), "mock_enc_dek")


if __name__ == "__main__":
    unittest.main()
