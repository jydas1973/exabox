#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/user_keys/tests_user_keys.py /main/3 2025/09/18 15:24:55 gparada Exp $
#
# tests_user_keys.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_user_keys.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    gparada     04/15/25 - 37828983 ssh CPS' as ecra usr, exec cmds with sudo
#    gparada     12/12/24 - Bug 36898362 Adding UT for user keys (secscan
#                           feature) - Coverage 82% for handler_user_keys.py
#    gparada     12/12/24 - Creation
#
import json
import os
import unittest

from unittest import mock
from unittest.mock import patch

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.utils.node import exaBoxNode

from exabox.jsondispatch.handler_user_keys import UserHandler

PAYLOAD_INJECT = {
    "user_handler":
    {
        "user":
        {
            "id": "secscan",
            "action": "inject",
            "create_user": "true"
        }
    }
}

PAYLOAD_DELETE = {
    "user_handler":
    {
        "user":
        {
            "id": "secscan",
            "action": "delete"
        }
    }
}

def mockMUnmaskNatHost(aHost):
    return aHost

mock_KmsEntries=[]
@patch('exabox.exakms.ExaKmsEntry.ExaKmsEntry.mUnmaskNatHost', side_effect=mockMUnmaskNatHost)
@patch("exabox.exakms.ExaKmsEntry.ExaKmsEntry.mSetPrivateKey")
def prepareKmsEntries(mockUnmask, mockSetPrivate):    
    mock_KmsEntries.append(ExaKmsEntry(aFQDN="scaqab10adm01.us.oracle.com", aUser="root", aPrivateKey="XYZ1", aHostType=ExaKmsHostType.DOM0))
    mock_KmsEntries.append(ExaKmsEntry(aFQDN="scaqab10celadm01.us.oracle.com", aUser="root", aPrivateKey="XYZ2", aHostType=ExaKmsHostType.CELL))
    # A DomU may have several entries (for diff users), but we want to be sure
    # that this flow connects with "root" user ONLY.
    mock_KmsEntries.append(ExaKmsEntry(aFQDN="scaqab10adm01vm01.us.oracle.com", aUser="root", aPrivateKey="XYZ1", aHostType=ExaKmsHostType.DOMU))
    mock_KmsEntries.append(ExaKmsEntry(aFQDN="scaqab10adm01vm01.us.oracle.com", aUser="grid", aPrivateKey="XYZ1", aHostType=ExaKmsHostType.DOMU))
    mock_KmsEntries.append(ExaKmsEntry(aFQDN="scaqab10adm01vm01.us.oracle.com", aUser="opc", aPrivateKey="XYZ1", aHostType=ExaKmsHostType.DOMU))
    mock_KmsEntries.append(ExaKmsEntry(aFQDN="scaqab10adm01vm01.us.oracle.com", aUser="oracle", aPrivateKey="XYZ1", aHostType=ExaKmsHostType.DOMU))

class ebTestUserHandler(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestUserHandler, self).setUpClass()
        # super().setUpClass()
        prepareKmsEntries()
        
    @patch("exabox.jsondispatch.handler_user_keys.UserHandler.mGetDestinationHosts", return_value=[])    
    def test_001_inject_zero_destinations(self, mockmGetDestinationHosts):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INJECT

        _handler = UserHandler(_options)
        _rc, _result = _handler.mExecute()
        print(json.dumps(_result, indent=4))
        self.assertEqual(_rc, 1)
        self.assertEqual(_result["reason"], 
            "Zero destination hosts. No entries in exassh for dom0's or cell's.")

    @patch("exabox.exakms.ExaKmsFileSystem.ExaKmsFileSystem.mSearchExaKmsEntries", return_value=mock_KmsEntries)    
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal", return_value=(0, None, None, None)) # /usr/bin/getent passwd secscan, sudo cp /tmp/tmpkynpqf_z /etc/ssh-keys/secscan.priv
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteCmdLog")# /usr/sbin/useradd --uid     
    def test_001_inject_user_exists_in_cps(self,
        mockSearchExaKmsEntries,
        mockmGetCmdExitStatus,
        mockmExecuteCmdLog):
        # This test covers 63% of handler_user_keys.py

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INJECT

        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/id 2009", aRc=1),
                    exaMockCommand("sudo /usr/sbin/useradd --uid *", aRc=0),
                ],
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/bin/id 2009", aRc=1),
                    exaMockCommand("sudo /usr/sbin/useradd --uid *", aRc=0),
                ],
            ],
        }        
        self.mPrepareMockCommands(_cmds)

        _handler = UserHandler(_options)        
        _rc, _result = _handler.mExecute()
        print(json.dumps(_result, indent=4))
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["reason"], 
            "User creation: Success on ['scaqab10adm01', 'scaqab10celadm01'], Fail on [].")


    @patch("exabox.exakms.ExaKmsFileSystem.ExaKmsFileSystem.mSearchExaKmsEntries", return_value=mock_KmsEntries)    
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal", return_value=(0, None, None, None)) # sudo /usr/bin/ls, sudo /bin/rm -rf
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteCmdLog")# /usr/sbin/userdel --uid 
    def test_002_delete(self,
        mockSearchExaKmsEntries,
        mockmExecuteLocal,
        mockmExecuteCmdLog):
        # This test covers 51% of handler_user_keys.py

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_DELETE

        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("sudo /usr/sbin/userdel *", aRc=0),
                ],
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("sudo /usr/sbin/userdel *", aRc=0),
                ],
            ],
        }        
        self.mPrepareMockCommands(_cmds)

        _handler = UserHandler(_options)        
        _rc, _result = _handler.mExecute()
        print(json.dumps(_result, indent=4))
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["reason"], 
            "User deletion: Success on ['scaqab10adm01', 'scaqab10celadm01'], Fail on [].")

    @patch("exabox.exakms.ExaKmsFileSystem.ExaKmsFileSystem.mSearchExaKmsEntries", return_value=mock_KmsEntries)    
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal", return_value=(0, None, None, None)) # /usr/bin/getent passwd secscan, sudo cp /tmp/tmpkynpqf_z /etc/ssh-keys/secscan.priv
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteCmdLog")# /usr/sbin/useradd --uid     
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.isATP")
    def test_003_adb_test(self,
        mockSearchExaKmsEntries,
        mockmGetCmdExitStatus,
        mockmExecuteCmdLog,
        mockIsATP):
        # This test covers 63% of handler_user_keys.py

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INJECT

        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/id 2009", aRc=1),
                    exaMockCommand("sudo /usr/sbin/useradd --uid *", aRc=0),
                ],
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/bin/id 2009", aRc=1),
                    exaMockCommand("sudo /usr/sbin/useradd --uid *", aRc=0),
                ],
            ],
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/bin/id 2009", aRc=1),
                    exaMockCommand("sudo /usr/sbin/useradd --uid *", aRc=0),
                ],
            ],            
        }        
        self.mPrepareMockCommands(_cmds)

        _handler = UserHandler(_options)        
        _rc, _result = _handler.mExecute()
        print(json.dumps(_result, indent=4))
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["reason"], 
            "User creation: Success on ['scaqab10adm01', 'scaqab10celadm01', 'scaqab10adm01vm01'], Fail on [].")

if __name__ == '__main__':
    unittest.main() 