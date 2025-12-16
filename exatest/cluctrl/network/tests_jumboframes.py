#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/network/tests_jumboframes.py /main/3 2024/06/17 23:37:44 scoral Exp $
#
# tests_jumboframes.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_jumboframes.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ffrrodri    02/21/22 - Creation
#
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Node import exaBoxNode
import exabox.ovm.clujumboframes as cjf


class TestJumboFrames(ebTestClucontrol):

    def test_get_client_backup_interfaces(self):
        _result = ('vmbondeth0', 'vmbondeth0', 'bondeth0', 'bondeth1')

        _commands = [
            exaMockCommand("/opt/oracle.cellos/exadata.img.hw*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands,
                ""
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _domu = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        self.assertEqual(_result, cjf.cluctrlGetClientBackupIfaces(self.mGetClubox(), _domu))

    def test_get_jumboframes_conf(self):

        _result = cjf.ebJFConf(
            dom0_client_mtu=cjf.ebMTUSize.JUMBO,
            dom0_backup_mtu=cjf.ebMTUSize.JUMBO,
            domu_client_mtu=cjf.ebMTUSize.JUMBO,
            domu_backup_mtu=cjf.ebMTUSize.JUMBO,
            dom0_client_bridge="vmbondeth0",
            dom0_backup_bridge="vmbondeth0",
            domu_client_iface="bondeth0",
            domu_backup_iface="bondeth1",
            atp_namespace=self.mGetClubox().mGetNamespace()
        )

        _payload = {
            'jumbo_frames': 'both'
        }

        _commands = [
            exaMockCommand("/opt/oracle.cellos/exadata.img.hw*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands,
                ""
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _domu = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        self.assertEqual(_result, cjf.getJumboFramesConf(self.mGetClubox(), _payload, _domu))

    def test_set_interface_mtu(self):

        _commands = [
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/sbin/ip link*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/cat*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _node = exaBoxNode(self.mGetClubox().mGetCtx())
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]

        try:
            _node.mConnect(aHost=_dom0)
            cjf.nodeSetIfaceMtu(_node, "eth0", cjf.ebMTUSize.JUMBO)
        finally:
            _node.mDisconnect()

        self.assertTrue(True, "Method nodeSetIfaceMtu executed successfully")

    def test_get_interface_mtu(self):

        _commands = [
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/sbin/ip link*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0")
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _node = exaBoxNode(self.mGetClubox().mGetCtx())
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]

        try:
            _node.mConnect(aHost=_dom0)
            self.assertEqual(0, cjf.nodeGetIfaceMtu(_node, "eth0"))
        finally:
            _node.mDisconnect()

    def test_get_bridged_ports(self):

        _commands = [
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0")
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _node = exaBoxNode(self.mGetClubox().mGetCtx())
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]

        try:
            _node.mConnect(aHost=_dom0)
            self.assertEqual(tuple(), cjf.nodeGetBridgePorts(_node, "bondeth0"))
        finally:
            _node.mDisconnect()

    def test_node_config_bridge_mtu(self):

        _commands = [
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/sbin/ip link*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/cat*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _node = exaBoxNode(self.mGetClubox().mGetCtx())
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]

        try:
            _node.mConnect(aHost=_dom0)
            cjf.nodeConfigBridgeMtu(_node, "bondeth0", cjf.ebMTUSize.JUMBO)
        finally:
            _node.mDisconnect()

        self.assertTrue(True, "Method nodeConfigBridgeMtu executed successfully")

    def test_configure_jumboframes(self):

        _payload = {
            'jumbo_frames': 'both'
        }

        _commands = [
            exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="21.2.8"),
            exaMockCommand("/opt/oracle.cellos/exadata.img.hw*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/sbin/ip link*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/cat*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/cat*", aRc=0)
        ]

        _commands_VM = [
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0"),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0"),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands,
                _commands,
                _commands
            ],
            self.mGetRegexVm(): [
                _commands_VM
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mSetExabm(True)

        cjf.configureJumboFrames(self.mGetClubox(), _payload)

        self.mGetClubox().mSetExabm(False)

        self.assertTrue(True, "Method configureJumboFrames executed successfully")

    def test_jumboframes_status(self):

        _result = ({'dom0': {'hostname': 'scaqab10adm01.us.oracle.com',
                             'client': {'bridge': 'vmbondeth0', 'mtus': {'vmbondeth0': 0}},
                             'backup': {'bridge': 'vmbondeth0', 'mtus': {'vmbondeth0': 0}}},
                    'domu': {'hostname': 'scaqab10client01vm08.us.oracle.com',
                             'client': {'mtus': {'bondeth0': 0}},
                             'backup': {'mtus': {'bondeth1': 0}}}},
                   {'dom0': {'hostname': 'scaqab10adm02.us.oracle.com',
                             'client': {'bridge': 'vmbondeth0', 'mtus': {'vmbondeth0': 0}},
                             'backup': {'bridge': 'vmbondeth0', 'mtus': {'vmbondeth0': 0}}},
                    'domu': {'hostname': 'scaqab10client02vm08.us.oracle.com',
                             'client': {'mtus': {'bondeth0': 0}},
                             'backup': {'mtus': {'bondeth1': 0}}}})

        _commands = [
            exaMockCommand("/opt/oracle.cellos/exadata.img.hw*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0"),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0"),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0")
        ]

        _commands_VM = [
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0"),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0"),
            exaMockCommand("/bin/cat*", aRc=0, aStdout="0"),
            exaMockCommand("/bin/test*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands,
                _commands,
                _commands
            ],
            self.mGetRegexVm(): [
                _commands_VM
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.assertEqual(_result, cjf.jumboFramesState(self.mGetClubox()))


if __name__ == '__main__':
    unittest.main()