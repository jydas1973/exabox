#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/nftables/tests_nftables.py /main/2 2023/10/20 12:57:38 jesandov Exp $
#
# tests_nftables.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
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
#    scoral      03/27/26 - Add tests for RemoveSecurityRulesExaBM
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

    def test_RemoveSecurityRulesExaBM_NFTables_filtered_dom0(self):

        _clubox = self.mGetClubox()
        _nft_dom0 = "scaqab10adm02"
        _extra_nft_dom0 = "scaqab10adm99"
        _legacy_dom0 = "scaqab10adm01"
        _domu = "scaqab10adm02vm08"

        _mock_node = mock.Mock()
        _mock_ctx = mock.Mock()
        _mock_ctx.mCheckRegEntry.return_value = False

        def _fake_get_hosts(host_type, versions):
            if versions == ["OL8"]:
                return [_nft_dom0, _extra_nft_dom0]
            if versions == ["OL7", "OL6"]:
                return [_legacy_dom0]
            return []

        def _fake_is_host_ol8(hostname):
            return hostname in (_nft_dom0, _extra_nft_dom0)

        with mock.patch.object(_clubox, "mGetHostsByTypeAndOLVersion", side_effect=_fake_get_hosts), \
             mock.patch.object(_clubox, "mReturnDom0DomUPair", return_value=[(_nft_dom0, _domu), (_extra_nft_dom0, "unused_domu"), (_legacy_dom0, "legacy_domu")]), \
             mock.patch.object(_clubox, "mCheckConfigOption", return_value=False), \
             mock.patch.object(_clubox, "mIsHostOL8", side_effect=_fake_is_host_ol8), \
             mock.patch("exabox.ovm.cluiptablesroce.get_gcontext", return_value=_mock_ctx), \
             mock.patch("exabox.ovm.cluiptablesroce.exaBoxNode", return_value=_mock_node) as _mock_node_ctor, \
             mock.patch("exabox.ovm.cluiptablesroce.node_exec_cmd_check") as _mock_exec, \
             mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mGetNFTRuleHandle", side_effect=[11, 0, 22, 0]) as _mock_handle, \
             mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mCommitNFTables") as _mock_commit:

            ebIpTablesRoCE.mRemoveSecurityRulesExaBM(_clubox, aDom0s=[_nft_dom0])

        _mock_node_ctor.assert_called_once_with(_mock_ctx)
        _mock_node.mConnect.assert_called_once_with(aHost=_nft_dom0)
        _mock_node.mDisconnect.assert_called_once()
        self.assertEqual(_mock_handle.call_count, 4)

        _expected_cmds = [
            mock.call(_mock_node, "/usr/sbin/nft delete rule bridge filter FORWARD handle 11"),
            mock.call(_mock_node, "/usr/sbin/nft flush chain bridge filter vm_scaqab10adm02vm08"),
            mock.call(_mock_node, "/usr/sbin/nft delete chain bridge filter vm_scaqab10adm02vm08"),
            mock.call(_mock_node, "/usr/sbin/nft delete rule bridge filter FORWARD handle 22"),
            mock.call(_mock_node, "/usr/sbin/nft flush chain bridge filter vm_scaqab10adm02vm08_lock"),
            mock.call(_mock_node, "/usr/sbin/nft delete chain bridge filter vm_scaqab10adm02vm08_lock"),
        ]
        self.assertEqual(_mock_exec.call_args_list, _expected_cmds)
        _mock_commit.assert_called_once_with(_mock_node)

    def test_RemoveSecurityRulesExaBM_IPTables_filters_with_backend(self):

        _clubox = self.mGetClubox()
        _legacy_dom0 = "scaqab10adm01"
        _nft_dom0 = "scaqab10adm02"

        def _fake_get_hosts(host_type, versions):
            if versions == ["OL8"]:
                return [_nft_dom0]
            if versions == ["OL7", "OL6"]:
                return [_legacy_dom0]
            return []

        with mock.patch.object(_clubox, "mGetHostsByTypeAndOLVersion", side_effect=_fake_get_hosts), \
             mock.patch.object(_clubox, "mReturnDom0DomUPair", return_value=[(_nft_dom0, "scaqab10adm02vm08"), (_legacy_dom0, "scaqab10adm01vm08")]), \
             mock.patch.object(_clubox, "mCheckConfigOption", return_value=True) as _mock_config, \
             mock.patch.object(_clubox, "mIsHostOL8", return_value=False), \
             mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mRemoveIpTablesExaBM") as _mock_remove:

            ebIpTablesRoCE.mRemoveSecurityRulesExaBM(_clubox, aDom0s=[_legacy_dom0])

        _mock_config.assert_called_once_with("iptables_backend", "legacy")
        _mock_remove.assert_called_once_with(_clubox, onDomUSchema=False, aDom0s=[_legacy_dom0])

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
