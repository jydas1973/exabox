#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exakmshistorysiv.py /main/5 2024/10/07 18:01:10 ririgoye Exp $
#
# tests_exakmshistorysiv.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakmshistorysiv.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    09/26/24 - Bug 36390923 - REMOVE EXAKMS HISTORY VALIDATION
#                           ACROSS HOSTS
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    aypaul      10/17/22 - Unit test cases for
#                           exabox/exakms/ExaKmsHistorySIV.py
#    aypaul      10/17/22 - Creation
#
import unittest
import warnings
import time
import base64
import socket
from unittest import mock
from unittest.mock import patch
from exabox.exakms.ExaKmsHistory import ExaKmsHistory
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.exakms.ExaKmsHistorySIV import ExaKmsHistorySIV
from exabox.exakms.ExaKmsEntrySIV import ExaKmsEntrySIVRSA
from exabox.exakms.ExaKmsSIV import ExaKmsSIV

MOCK_CONFIG = {'exakms_vault_id': 'mock_vault_id', 'exakms_backup_vault_id': 'mock_backup_vaultid',\
               'exakms_compartment_id': 'mock_compartment_id', 'kms_key_id': 'mock_keyid'}

class mockContent():
    def __init__(self):
        _str_data = f"{time.strftime('%Y-%m-%d %H:%M:%S%z')}\t{socket.getfqdn()}\tmock1 mock2 root@{socket.getfqdn()}\tinsert"
        self.content = base64.b64encode(_str_data.encode()).decode()

class mockSecretBundle():
    def __init__(self):
        self.secret_bundle_content = mockContent()

class mockOptions(object):
    pass

class mockVaultClient(object):
    pass

class mockSecretsClient(object):
    
    def get_secret_bundle_by_name(self, arg1, arg2):
        bundleContent = mockOptions()
        bundleContent.data = mockSecretBundle()
        return bundleContent

class mockExaOCIFactory(object):

    def __init__(self):
        self.__vault_client = mockVaultClient()
        self.__secrets_client = mockSecretsClient()

    def get_vault_client(self):
        return self.__vault_client

    def get_secrets_client(self):
        return self.__secrets_client

class mockContext(object):

    def __init__(self, _json):
        self.__config = _json

    def mCheckConfigOption(self, key):
        return self.__config.get(key, None)

class secretClient(object):

    def __init__(self, _value):
        self.data = _value

class ebTestExaKmsHistorySIV(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        warnings.filterwarnings("ignore")

    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    def test_initiate_constructor(self, mock_super_unmaskhost, mock_set_privatekeykey):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        with patch('exabox.exakms.ExaKmsHistorySIV.get_gcontext', return_value=mockContext({})):
            self.assertRaises(ValueError, ExaKmsHistorySIV, _exakms_entry_rsa)

        with patch('exabox.exakms.ExaKmsHistorySIV.get_gcontext', return_value=mockContext(MOCK_CONFIG)):
            _exakms_history_siv = ExaKmsHistorySIV(_exakms_entry_rsa)

    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsHistorySIV.get_gcontext', return_value=mockContext(MOCK_CONFIG))
    @patch('exabox.exakms.ExaKmsHistorySIV.ExaKmsHistorySIV.mModifyLogFile')
    def test_mPutExaKmsHistory(self, mock_super_unmaskhost, mock_set_privatekeykey, mock_config, mock_modifylogfile):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        _exakms_history_siv = ExaKmsHistorySIV(_exakms_entry_rsa)
        _exakms_history_siv.mPutExaKmsHistory(_exakms_entry_rsa, "insert")

    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsHistorySIV.get_gcontext', return_value=mockContext(MOCK_CONFIG))
    def test_mModifyLogFile(self, mock_super_unmaskhost, mock_set_privatekeykey, mock_config):
        _exakms_entry_rsa = ExaKmsEntrySIVRSA(aFQDN="mockhostname.oracle.com", aUser="mock_username", aPrivateKey="mock_privkey",
                 aHostType=ExaKmsHostType.DOM0)
        _exakms_history_siv = ExaKmsHistorySIV(_exakms_entry_rsa)
        _new_entry = f"{time.strftime('%Y-%m-%d %H:%M:%S%z')}\tmockhostname.oracle.com\tmock_key_details\tinsert\n"
        _exakms_history_siv.mModifyLogFile(_new_entry)


    @patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', return_value="mockhostname.oracle.com")
    @patch('exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIVRSA.mSetPrivateKey')
    @patch('exabox.exakms.ExaKmsSIV.get_gcontext', return_value=mockContext(MOCK_CONFIG))
    @patch('exabox.exakms.ExaKmsSIV.ExaOCIFactory', return_value=mockExaOCIFactory())
    @patch('exabox.exakms.ExaKmsHistorySIV.get_gcontext', return_value=mockContext(MOCK_CONFIG))
    def test_mGetExaKmsHistory(self, mock_super_unmaskhost, mock_set_privatekeykey, mock_config, mock_exaocifactory, mock_historyconfig):
        _exakms_obj = ExaKmsSIV()
        _exakms_obj.mGetExaKmsHistoryInstance().mGetExaKmsHistory("root", socket.getfqdn(), 20)

if __name__ == "__main__":
    unittest.main()
