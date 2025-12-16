#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/network/tests_network_validations.py /main/5 2025/05/19 14:20:00 akkar Exp $
#
# tests_network_validations.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_network_validations.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    akkar       04/06/25 - 37641178: 100gbs client network support
#    jfsaldan    02/24/25 - Bug 37570873 - EXADB-D|XS -- EXACLOUD |
#                           PROVISIONING | REVIEW AND ORGANIZE PREVM_CHECKS AND
#                           PREVM_SETUP STEPS
#    aararora    07/17/24 - Bug 36799782: mGenBondMap raising index error when
#                           bondeth1 points to non existing slaves
#    aararora    11/22/23 - Bug 35796665: Add unit test for storage resize
#                           precheck for ssh connectivity
#    jfsaldan    09/29/23 - Creation
#

import copy
import unittest
import re
import os
import json
from pathlib import Path
from unittest.mock import patch
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.clumisc import ebCluServerSshConnectionCheck
from exabox.utils.node import connect_to_host
from exabox.ovm.clunetworkvalidations import ebNetworkValidations
from exabox.ovm.clunetworkdetect import ebOEDANetworkConfiguration, ebDiscoverOEDANetwork, ebNetworkType, \
    ebPortState, generateSupportedNetworkMap

class mockStream():

    def __init__(self, aStreamContents=["None"]):
        self.stream_content = aStreamContents

    def readlines(self):
        return self.stream_content

    def read(self):
        return self.stream_content[0]

class Node:

    def mExecuteCmd(self, aCmd):
        if "bondeth0" in aCmd:
            return mockStream([]), mockStream(["eth1 eth2"]), mockStream([])
        else:
            return mockStream([]), mockStream([]), mockStream([])

    def mGetCmdExitStatus(self):
        return 0

class TestXTablesExaCCNAT(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(False, False)

    def test_reload_both(self):
        """
        Test ebNetworkValidations.mCheckClientBackupIPSet
        """

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),

                    # bondeth0
                    exaMockCommand(
                        '/sbin/ip a s bondeth0 | /bin/grep ".*"',
                        aRc=1),
                    exaMockCommand("ifdown bondeth0", aRc=0),
                    exaMockCommand("ifup bondeth0", aRc=0),
                    exaMockCommand(
                        '/sbin/ip a s bondeth0 | /bin/grep ".*"',
                        aRc=0),
                    exaMockCommand("systemctl restart sshd", aRc=0),

                    # bondeth1
                    exaMockCommand(
                        '/sbin/ip a s bondeth1 | /bin/grep ".*"',
                        aRc=1),
                    exaMockCommand("ifdown bondeth1", aRc=0),
                    exaMockCommand("ifup bondeth1", aRc=0),
                    exaMockCommand(
                        '/sbin/ip a s bondeth1 | /bin/grep ".*"',
                        aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0domUlist = _ebox.mReturnDom0DomUPair()
        _net_val_mgr = ebNetworkValidations(_ebox, _dom0domUlist)
        self.assertIsNone(_net_val_mgr.mCheckClientBackupIPSet())

    def test_reload_bondeth0(self):
        """
        Test ebNetworkValidations.mCheckClientBackupIPSet
        """

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),

                    # bondeth0
                    exaMockCommand(
                        '/sbin/ip a s bondeth0 | /bin/grep ".*"',
                        aRc=1),
                    exaMockCommand("ifdown bondeth0", aRc=0),
                    exaMockCommand("ifup bondeth0", aRc=0),
                    exaMockCommand(
                        '/sbin/ip a s bondeth0 | /bin/grep ".*"',
                        aRc=0),
                    exaMockCommand("systemctl restart sshd", aRc=0),

                    # bondeth1
                    exaMockCommand(
                        '/sbin/ip a s bondeth1 | /bin/grep ".*"',
                        aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0domUlist = _ebox.mReturnDom0DomUPair()
        _net_val_mgr = ebNetworkValidations(_ebox, _dom0domUlist)
        self.assertIsNone(_net_val_mgr.mCheckClientBackupIPSet())

    def test_reload_none(self):
        """
        Test ebNetworkValidations.mCheckClientBackupIPSet
        """

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),

                    # bondeth0
                    exaMockCommand(
                        '/sbin/ip a s bondeth0 | /bin/grep ".*"',
                        aRc=0),

                    # bondeth1
                    exaMockCommand(
                        '/sbin/ip a s bondeth1 | /bin/grep ".*"',
                        aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0domUlist = _ebox.mReturnDom0DomUPair()
        _net_val_mgr = ebNetworkValidations(_ebox, _dom0domUlist)
        self.assertIsNone(_net_val_mgr.mCheckClientBackupIPSet())

    def test_reload_and_fail(self):
        """
        Test ebNetworkValidations.mCheckClientBackupIPSet
        """

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),

                    # bondeth0
                    exaMockCommand(
                        '/sbin/ip a s bondeth0 | /bin/grep ".*"',
                        aRc=1),
                    exaMockCommand("ifdown bondeth0", aRc=0),
                    exaMockCommand("ifup bondeth0", aRc=0),
                    exaMockCommand(
                        '/sbin/ip a s bondeth0 | /bin/grep ".*"',
                        aRc=1),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0domUlist = _ebox.mReturnDom0DomUPair()
        _net_val_mgr = ebNetworkValidations(_ebox, _dom0domUlist)

        # Should raise an error
        with self.assertRaises(ExacloudRuntimeError):
            _net_val_mgr.mCheckClientBackupIPSet()

    def test_mServerSshConnectionCheck(self):
        """
        Tests the mServerSshConnectionCheck method in clumisc.py
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _ssh_conn_check = ebCluServerSshConnectionCheck(self.mGetClubox())
        _ssh_conn_check.mServerSshConnectionCheck(_options, [], [], [])

    def test_mGenBondMap(self):
        """
        Tests the mGenBondMap method in clucontrol
        """
        _node = Node()
        # If stale bondeth1 interface exists, raise run time error.
        with self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mGenBondMap(_node, True)

    def test_mCheckDom0EthernetSpeed_exacc(self):
        """
        Test mCheckDom0EthernetSpeed()
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/bondeth0/bonding/slaves",
                        aRc=0, aStdout="eth10 eth9\n"),
                ]
            ]
        }
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/bondeth0/bonding/slaves",
                        aRc=0, aStdout="eth10 eth9\n"),
                    exaMockCommand("/bin/cat /sys/class/net/bondeth1/bonding/slaves",
                        aRc=0, aStdout="eth29 eth30\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth10/operstate",
                        aRc=0, aStdout="up\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth10/speed",
                        aRc=0, aStdout="50000\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth10/carrier",
                        aRc=0, aStdout="1\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth9/operstate",
                        aRc=0, aStdout="up\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth9/speed",
                        aRc=0, aStdout="50000\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth9/carrier",
                        aRc=0, aStdout="1\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth29/operstate",
                        aRc=0, aStdout="up\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth29/speed",
                        aRc=0, aStdout="50000\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth29/carrier",
                        aRc=0, aStdout="1\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth30/operstate",
                        aRc=0, aStdout="up\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth30/speed",
                        aRc=0, aStdout="50000\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth30/carrier",
                        aRc=0, aStdout="1\n"),
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model",
                        aRc=0, aStdout="ORACLE SERVER E4-2c\n"),
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model",
                        aRc=0, aStdout="ORACLE SERVER E4-2c\n"),
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model",
                        aRc=0, aStdout="ORACLE SERVER E4-2c\n"),
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model",
                        aRc=0, aStdout="ORACLE SERVER E4-2c\n"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0domUlist = _ebox.mReturnDom0DomUPair()
        _net_val_mgr = ebNetworkValidations(_ebox, _dom0domUlist)

        self.assertEqual({}, _net_val_mgr.mCheckDom0EthernetSpeed())


    def test_mCheckDom0EthernetSpeed_exacs(self):
        """
        Test mCheckDom0EthernetSpeed()
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/bondeth0/bonding/slaves",
                        aRc=0, aStdout="eth1 eth2\n"),
                    exaMockCommand("/bin/cat /sys/class/net/bondeth1/bonding/slaves",
                        aRc=1),
                    exaMockCommand("/bin/cat /sys/class/net/eth1/operstate",
                        aRc=0, aStdout="up\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth1/speed",
                        aRc=0, aStdout="50000\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth1/carrier",
                        aRc=0, aStdout="1\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth2/operstate",
                        aRc=0, aStdout="up\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth2/speed",
                        aRc=0, aStdout="50000\n"),
                    exaMockCommand("/bin/cat /sys/class/net/eth2/carrier",
                        aRc=0, aStdout="1\n"),
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model",
                        aRc=0, aStdout="ORACLE SERVER E4-2c\n"),
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model",
                        aRc=0, aStdout="ORACLE SERVER E4-2c\n"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0domUlist = _ebox.mReturnDom0DomUPair()
        _net_val_mgr = ebNetworkValidations(_ebox, _dom0domUlist)

        self.assertEqual({}, _net_val_mgr.mCheckDom0EthernetSpeed())



    def test_mUpdateDom0EthernetSpeeds(self):
        """
        Test mUpdateDom0EthernetSpeeds()
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/ethtool -s eth1 speed 50000 autoneg on"),
                    exaMockCommand("/bin/cat /sys/class/net/eth1/speed",
                        aRc=0, aStdout="50000\n"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0domUlist = _ebox.mReturnDom0DomUPair()
        _net_val_mgr = ebNetworkValidations(_ebox, _dom0domUlist)


        _dom0 = _ebox.mReturnDom0DomUPair()[0][0]
        self.assertEqual(None, _net_val_mgr.mUpdateDom0EthernetSpeeds({_dom0: { "eth1" : (50000, True)}}))


    def test_mGenerateSupportedNetworkMap(self):
        """_sample_output = {
        "OCIEXACC_FULL_FIBER": ebOEDANetworkConfiguration(
            client_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth1",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=False,
            half_net=False,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_FULL_COPPER": ebOEDANetworkConfiguration(
            client_net=(
                COPPER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                COPPER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth1",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=False,
            half_net=False,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_CLIENT_FIBER_BACKUP_COPPER": ebOEDANetworkConfiguration(
            client_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                COPPER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth1",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=False,
            half_net=False,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_CLIENT_COPPER_BACKUP_FIBER": ebOEDANetworkConfiguration(
            client_net=(
                COPPER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth1",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=False,
            half_net=False,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_BASE_FULL_FIBER": ebOEDANetworkConfiguration(
            client_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth1",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=False,
            half_net=False,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_BASE_HALF_FIBER": ebOEDANetworkConfiguration(
            client_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=True,
            half_net=False,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_BASE_HALF_COPPER": ebOEDANetworkConfiguration(
            client_net=(
                COPPER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                COPPER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=True,
            half_net=False,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_BASE_CLIENT_FIBER_BACKUP_COPPER": ebOEDANetworkConfiguration(
            client_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                COPPER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth1",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=False,
            half_net=False,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_BASE_CLIENT_COPPER_BACKUP_FIBER": ebOEDANetworkConfiguration(
            client_net=(
                COPPER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth1",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=False,
            half_net=False,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_CLIENT_FIBER_BACKUP_COPPER_HALF_NET": ebOEDANetworkConfiguration(
            client_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=False,
            half_net=True,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        "OCIEXACC_BASE_HALF_FIBER_HALF_NET": ebOEDANetworkConfiguration(
            client_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth1", "eth2"],
                    domU_name="bondeth0",
                ),
            ),
            backup_net=(
                FIBER,
                ebOEDANetwork(
                    dom0_bridge="vmbondeth0",
                    dom0_interfaces=["eth5", "eth6"],
                    domU_name="bondeth1",
                ),
            ),
            degraded_net=False,
            half_net=True,
            admin_net=ebOEDANetwork(
                dom0_bridge="vmeth0", dom0_interfaces=[], domU_name="eth0"
            ),
        ),
        }"""
        _100gbs_interfaces = {}
        _backup_interfaces = ["eth5", "eth6"]
        _client_interfaces = ["eth1", "eth2"]
        _100gbs_interfaces['backup'] = _backup_interfaces
        _100gbs_interfaces['client'] = _client_interfaces
        
        abs_path = os.path.dirname(__file__)
        path = str(Path(abs_path).parents[2])
        SUPPORTED_NETWORK_PATH = 'properties/supportedNetworks.json'
        abs_file_path = os.path.join(path, SUPPORTED_NETWORK_PATH)
        with open(abs_file_path) as json_data_file:
            supportedNetworks = json.load(json_data_file)
        OCIEXACC_FULL_FIBER_interface = supportedNetworks['models']['x11']['OCIEXACC_FULL_FIBER']['client']['dom0_interfaces']
        _mapping = generateSupportedNetworkMap('x10',a100GbsInterfaces=_100gbs_interfaces)
        obj = _mapping['OCIEXACC_FULL_FIBER']
        self.assertEqual(obj.client_net[1].dom0_bridge, 'vmbondeth0')
        self.assertEqual(obj.client_net[1].dom0_interfaces, ['eth1', 'eth2'])
        

    def test_Is100GbsSpeedSupported_client_x10(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/ethtool -s eth1 speed 50000 autoneg on"),
                    exaMockCommand("/bin/cat /sys/class/net/eth1/speed", aRc=0, aStdout="50000\n"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER E5-2L\n"),
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _dom0 = _ebox.mReturnDom0DomUPair()[0][0]
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPhysicalInterfaceList', return_value="eth10,re0vf21,eth9,re0vf11,eth5,re1vf23repr,eth6,eth30,eth1,eth2,eth10,"), \
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPCISlot', return_value="1"), \
            patch('exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface', return_value=True):
            is_supported = _ebox.Is100GbsSpeedSupported(_dom0, 'client')
            self.assertEqual(is_supported, True)
    
    def test_Is100GbsSpeedSupported_backup_x10(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/ethtool -s eth1 speed 50000 autoneg on"),
                    exaMockCommand("/bin/cat /sys/class/net/eth1/speed", aRc=0, aStdout="50000\n"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER E5-2L\n"),
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _dom0 = _ebox.mReturnDom0DomUPair()[0][0]
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPhysicalInterfaceList', return_value="eth5,re0vf21,eth6,re0vf11,eth5,re1vf23repr,eth6,eth30,eth1,eth2,eth10,"), \
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPCISlot', return_value="2"), \
            patch('exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface', return_value=True):
            is_supported = _ebox.Is100GbsSpeedSupported(_dom0, 'backup')
            self.assertEqual(is_supported, True)
            
    def test_Is100GbsSpeedSupported_client_x11(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/ethtool -s eth1 speed 50000 autoneg on"),
                    exaMockCommand("/bin/cat /sys/class/net/eth1/speed", aRc=0, aStdout="50000\n"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER E6-2L\n"),
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _dom0 = _ebox.mReturnDom0DomUPair()[0][0]
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPhysicalInterfaceList', return_value="eth10,re0vf21,eth9,re0vf11,eth5,re1vf23repr,eth6,eth30,eth1,eth2,eth10,"), \
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPCISlot', return_value="1"), \
            patch('exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface', return_value=True):
            is_supported = _ebox.Is100GbsSpeedSupported(_dom0, 'client')
            self.assertEqual(is_supported, True)
            
    def test_Is100GbsSpeedSupported_client_x11_interface_missing(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/ethtool -s eth1 speed 50000 autoneg on"),
                    exaMockCommand("/bin/cat /sys/class/net/eth1/speed", aRc=0, aStdout="50000\n"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER E6-2L\n"),
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _dom0 = _ebox.mReturnDom0DomUPair()[0][0]
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPhysicalInterfaceList', return_value="eth100"), \
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPCISlot', return_value="1"), \
            patch('exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface', return_value=True):
            is_supported = _ebox.Is100GbsSpeedSupported(_dom0, 'client')
            self.assertEqual(is_supported, False)


    def test_Is100GbsSpeedSupported_client_x11_set_custom_speed(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/ethtool -s eth1 speed 50000 autoneg on"),
                    exaMockCommand("/bin/cat /sys/class/net/eth1/speed", aRc=0, aStdout="50000\n"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER E6-2L\n")
                    
                    
                ],
                [
                    exaMockCommand("/bin/cat /sys/class/net/eth1/speed", aRc=0, aStdout="2500"),
                    exaMockCommand("/usr/sbin/ethtool -s eth1 speed 100000 autoneg on", aRc=0)
                ],
                [
                    exaMockCommand("/bin/cat /sys/class/net/eth1/speed", aRc=0, aStdout="2500"),
                    exaMockCommand("/usr/sbin/ethtool -s eth1 speed 100000 autoneg on", aRc=0)
                ]
                
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _dom0 = _ebox.mReturnDom0DomUPair()[0][0]
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPhysicalInterfaceList', return_value="eth100"), \
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPCISlot', return_value="1"), \
            patch('exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface', return_value=False):
            is_supported = _ebox.Is100GbsSpeedSupported(_dom0, 'client')
            self.assertEqual(is_supported, False)
    

if __name__ == '__main__':
    unittest.main()
