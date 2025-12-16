#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/nftables/tests_nftables.py /main/2 2023/10/20 12:57:38 jesandov Exp $
#
# tests_nftables.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_nftables.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    10/16/23 - 35729701: Support of OL7 + OL8
#    jesandov    01/27/23 - Creation
#

import os
import unittest

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from unittest import mock

class ebTestIpTablesRoCEwithNFT(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.mGetClubox(self).mGetCtx().mSetConfigOption('iptables_backend', "iptables_nft")

    def test_PrevmSetupNFTablesDelete(self):

        _nftFull = self.mGetResourcesTextFile("nft_list_full")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("nft -a list ruleset", aStdout=_nftFull, aPersist=True),
                    exaMockCommand("nft delete.*", aStdout=_nftFull, aPersist=True),
                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Prevm setup
        #self.mSetOLVersion("8")
        ebIpTablesRoCE.mPrevmSetupNFTables(self.mGetClubox(), append=False)


    def test_PrevmSetupNFTablesDeleteDuplicates(self):

        _nftClean = self.mGetResourcesTextFile("nft_list_clean")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("nft -a list ruleset", aStdout=_nftClean, aPersist=True),
                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Prevm setup
        #self.mSetOLVersion("8")
        ebIpTablesRoCE.mPrevmSetupNFTables(self.mGetClubox(), append=False)


    def test_PrevmSetupNFTablesAddDuplicates(self):

        _nftFull = self.mGetResourcesTextFile("nft_list_full")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("nft -a list ruleset", aStdout=_nftFull, aPersist=True),
                    exaMockCommand("nft delete.*", aPersist=True),
                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Prevm setup
        #self.mSetOLVersion("8")
        ebIpTablesRoCE.mPrevmSetupNFTables(self.mGetClubox())


    def test_PrevmSetupNFTablesAdd(self):

        _nftClean = self.mGetResourcesTextFile("nft_list_clean")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("nft -a list ruleset", aStdout=_nftClean, aPersist=True),
                    exaMockCommand("nft add.*", aPersist=True),
                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Prevm setup
        #self.mSetOLVersion("8")
        ebIpTablesRoCE.mPrevmSetupNFTables(self.mGetClubox())

    @mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mPrevmSetupIptables")
    def test_SetupSecurityRulesExaBM_IPTables(self, prevm_setup):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("iptables.*", aPersist=True),
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #self.mSetOLVersion("7")
        ebIpTablesRoCE.mSetupSecurityRulesExaBM(self.mGetClubox(), None)

    @mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mPrevmSetupNFTables")
    def test_SetupSecurityRulesExaBM_NFTables(self, prevm_setup):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("nft.*", aPersist=True),
                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #self.mSetOLVersion("8")
        ebIpTablesRoCE.mSetupSecurityRulesExaBM(self.mGetClubox(), None)


    def test_RemoveSecurityRulesExaBM_IPTables(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("iptables.*", aPersist=True),
                ],
                [
                    exaMockCommand("iptables.*", aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #self.mSetOLVersion("7")
        ebIpTablesRoCE.mRemoveSecurityRulesExaBM(self.mGetClubox())

    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsHostOL8", return_value=True)
    def test_RemoveSecurityRulesExaBM_NFTables(self, mock_ol8):

        _nftChains = self.mGetResourcesTextFile("nft_list_chains")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("nft -a list ruleset.*", aStdout=_nftChains, aPersist=True),
                    exaMockCommand("nft.*", aPersist=True),
                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #self.mSetOLVersion("8")
        ebIpTablesRoCE.mRemoveSecurityRulesExaBM(self.mGetClubox())


    def test_ExaCC_StaticRules(self):

        _ipFilter = self.mGetResourcesTextFile("ip_filter")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("nft -as list table ip filter", aStdout=_ipFilter, aPersist=True),
                    exaMockCommand("nft -as list ruleset", aStdout=_ipFilter, aPersist=True),
                    exaMockCommand("nft .*", aPersist=True),

                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                    exaMockCommand("cat /etc/nftables/exadata.nft", aPersist=True),
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', os.path.join(self.mGetPath(), "ocpsSetup.json"))
        #self.mSetOLVersion("8")
        self.mGetClubox().mSetOciExacc(True)

        self.mGetClubox().mSetupNatNfTablesOnDom0v2()




if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end file
