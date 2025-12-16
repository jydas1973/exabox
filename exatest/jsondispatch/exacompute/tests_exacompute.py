#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/exacompute/tests_exacompute.py /main/8 2025/09/20 16:54:53 rbhandar Exp $
#
# tests_exacompute.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_exacompute.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rbhandar    09/09/25 - Bug 38338607 - OCI: EXADB-XS: EXACLOUD DOESN'T
#                           UPDATE /ETC/NFTABLES/EXADATA.NFT
#    jesandov    05/18/23 - Creation
#
#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/exacompute/tests_exacompute.py /main/8 2025/09/20 16:54:53 rbhandar Exp $
#
# tests_SLA.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_SLA.py - Unit test for SLA measurements
#
#    DESCRIPTION
#      Run tests for SLA measurements
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    aararora    11/29/24 - Bug 37025316: Fix nft rules during vault access creation
#    jesandov    06/28/23 - 35529335: Update endpoint of exacompute_vault_details
#    alsepulv    03/23/22 - Enh 33889398: Parallelism control addition
#    alsepulv    02/02/22 - Creation
#

import json
import os
import unittest

from unittest import mock
from unittest.mock import patch

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode

from exabox.jsondispatch.handler_exacompute_generate_sshkey import ExaComputeGenerateSSHHandler
from exabox.jsondispatch.handler_exacompute_vault_details import ExaComputeVaultDetails
from exabox.jsondispatch.handler_exacompute_vault_delete import ExaComputeDeleteVault
from exabox.jsondispatch.handler_exacompute_deconfigure_dom0roce import ExaComputeDeconfigureDom0Roce

class ebTestExaCompute(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    @patch("exabox.exakms.ExaKmsFileSystem.ExaKmsFileSystem.mInsertExaKmsEntry", return_value=0)
    def test_001_generate_sshkeys(self, mock_insert_entry):

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload_SSH_Generation.json")

        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(".*", aRc=0, aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Correct payload
        _handler = ExaComputeGenerateSSHHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)

    def test_002_vault_details(self):

        _lsedvnode_out = """id:                                1062f9cc-a8b4-084d-1062-f9cca8b4084d
hostName:                          sea201610exdd009
state:                             ONLINE
giClusterID:
giClusterName:
EDV Driver Base Version Info:
  EDV Driver Version               23.1.90.0.0.230531.1
EDV Driver Online Patch Version Info:
  EDV Online Patch Driver Version: None 
"""

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload_Vault_Details.json")

        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("edvutil lsedvnode", aRc=0, aStdout=_lsedvnode_out, aPersist=True),
                    exaMockCommand("dbmcli -e alter dbserver startup services ms", aRc=0, aPersist=True),
                    exaMockCommand("dbmcli -e alter dbserver interconnect1=stre0, interconnect2=stre1", aRc=0, aPersist=True),
                    exaMockCommand(".*", aRc=0, aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Correct payload
        _handler = ExaComputeVaultDetails(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)


        self.assertEqual(_result, {
            "token_id": "1062f9cc-a8b4-084d-1062-f9cca8b4084d",
            "state": "ONLINE",
            "driver_version": "23.1.90.0.0.230531.1"
        })

    @patch("exabox.exakms.ExaKmsFileSystem.ExaKmsFileSystem.mSearchExaKmsEntries", return_value=["x"])
    @patch("exabox.exakms.ExaKmsFileSystem.ExaKmsFileSystem.mDeleteExaKmsEntry", return_value=0)
    def test_003_delete_vault(self, mock_search, mock_delete):

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload_SSH_Generation.json")

        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(".*", aRc=0, aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Correct payload
        _handler = ExaComputeDeleteVault(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)

    def test_004_mAddRule(self):

        _options = self.mGetContext().mGetArgsOptions()

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/nft insert rule ip filter INPUT iifname \"stre0\" counter packets 0 bytes 0 accept", aRc=0, aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _ssh_conn = exaBoxNode(self.mGetContext())
        _ssh_conn.mConnect(_dom0)
        _handler = ExaComputeVaultDetails(_options)
        _handler.mAddRule(_ssh_conn, 'stre0')

    def test_005_deconfigure_dom0roce(self):

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload_deconfigure.json")
        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/sbin/ifconfig *", aRc=1, aPersist=True),
                    exaMockCommand("/usr/bin/dbmcli *", aRc=0, aPersist=True)                  
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Correct payload
        _handler = ExaComputeDeconfigureDom0Roce(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)

    def test_006_mCommitNFTables(self):
        
        _options = self.mGetContext().mGetArgsOptions()
        _cmds = {
            self.mGetRegexDom0(): [
                [
                     exaMockCommand("/bin/cp /etc/nftables/exadata.nft /etc/nftables/exadata*", aRc=0, aPersist=True),
                     exaMockCommand("/usr/sbin/nft list ruleset > /etc/nftables/exadata.nft", aRc=0, aPersist=True),
                ]
            ]
        }       
        
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox() 
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _ssh_conn = exaBoxNode(self.mGetContext())
        _ssh_conn.mConnect(_dom0)
        _handler = ExaComputeVaultDetails(_options)
        _handler.mCommitNFTables(_ssh_conn)       
  
   
if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
