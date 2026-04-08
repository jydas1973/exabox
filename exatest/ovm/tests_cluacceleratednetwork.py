#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluacceleratednetwork.py /main/3 2026/02/21 03:56:44 mpedapro Exp $
#
# tests_cluacceleratednetwork.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluacceleratednetwork.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    mpedapro    02/10/26 - Enh::38914367 UT coverage for code changes
#    mpedapro    11/24/25 - Enh::38602758 Cover changes with unit tests
#    mpedapro    11/14/25 - Unit tests for ebCluAcceleratedNetwork class
#                           methods
#    mpedapro    11/14/25 - Creation
#

import os
import unittest
from unittest.mock import patch, MagicMock
import copy

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.network.payloads import PAYLOAD_ADD_COMPUTE_DUAL_STACK, PAYLOAD_CREATE_SERVICE_DUAL_STACK, \
    PAYLOAD_ADD_COMPUTE
from exabox.ovm.cluelasticcompute import ebCluReshapeCompute
from exabox.tools.oedacli import OedacliCmdMgr
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cluacceleratednetwork import ebCluAcceleratedNetwork


class ebTestCluacceleratedNetwork(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCluacceleratedNetwork, cls).setUpClass(False, False, aResourceFolder='exabox/exatest/network/resources_ipv6/')

    def test_isFeatureSupported_true(self):
        """Test isFeatureSupported when feature is enabled"""
        print(f"Running test: {self._testMethodName}")
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=True)
        _cluctrl.mCheckConfigOption = MagicMock(return_value=True)
        self.assertTrue(ebCluAcceleratedNetwork.isFeatureSupported(_cluctrl))

    def test_isFeatureSupported_false_not_exabm(self):
        """Test isFeatureSupported when not ExaBM"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=False)
        self.assertFalse(ebCluAcceleratedNetwork.isFeatureSupported(_cluctrl))

    def test_isFeatureSupported_false_config_false(self):
        """Test isFeatureSupported when config option is False"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=True)
        _cluctrl.mCheckConfigOption = MagicMock(return_value=False)
        self.assertFalse(ebCluAcceleratedNetwork.isFeatureSupported(_cluctrl))

    def test_isacceleratedNetworkCapableDom0_capable(self):
        """Test isacceleratedNetworkCapableDom0 for capable Dom0"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mGetExadataDom0Model = MagicMock(return_value='X11')
        _cluctrl.mGetImageVersion = MagicMock(return_value='26.1.0')
        dom0Name = 'test-dom0'
        self.assertTrue(ebCluAcceleratedNetwork.isacceleratedNetworkCapableDom0(_cluctrl, dom0Name))

    def test_isacceleratedNetworkCapableDom0_not_capable_model(self):
        """Test isacceleratedNetworkCapableDom0 for incapable model"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mGetExadataDom0Model = MagicMock(return_value='X10')
        _cluctrl.mGetImageVersion = MagicMock(return_value='26.1.0')
        dom0Name = 'test-dom0'
        self.assertFalse(ebCluAcceleratedNetwork.isacceleratedNetworkCapableDom0(_cluctrl, dom0Name))

    def test_isacceleratedNetworkCapableDom0_not_capable_version(self):
        """Test isacceleratedNetworkCapableDom0 for incapable version"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mGetExadataDom0Model = MagicMock(return_value='X11')
        _cluctrl.mGetImageVersion = MagicMock(return_value='25.1.0')
        dom0Name = 'test-dom0'
        self.assertFalse(ebCluAcceleratedNetwork.isacceleratedNetworkCapableDom0(_cluctrl, dom0Name))

    def test_validateEnvForacceletedNetworkFeature_success(self):
        """Test validateEnvForacceletedNetworkFeature success"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=True)
        _cluctrl.mCheckConfigOption = MagicMock(return_value=True)
        _cluctrl.mGetExadataDom0Model = MagicMock(return_value='X11')
        _cluctrl.mGetImageVersion = MagicMock(return_value='26.1.0')
        _cluctrl.mUpdateErrorObject = MagicMock(return_value=None)
        dom0Name = 'test-dom0'
        # Should not raise exception
        ebCluAcceleratedNetwork.validateEnvForacceletedNetworkFeature(_cluctrl, dom0Name)

    def test_validateEnvForacceletedNetworkFeature_fail_feature_not_supported(self):
        """Test validateEnvForacceletedNetworkFeature when feature not supported"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=False)
        _cluctrl.mUpdateErrorObject = MagicMock(return_value=None)
        dom0Name = 'test-dom0'
        with self.assertRaises(ExacloudRuntimeError):
            ebCluAcceleratedNetwork.validateEnvForacceletedNetworkFeature(_cluctrl, dom0Name)

    def test_validateEnvForacceletedNetworkFeature_fail_dom0_not_capable(self):
        """Test validateEnvForacceletedNetworkFeature when Dom0 not capable"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=True)
        _cluctrl.mCheckConfigOption = MagicMock(return_value=True)
        _cluctrl.mGetExadataDom0Model = MagicMock(return_value='X10')
        _cluctrl.mGetImageVersion = MagicMock(return_value='26.1.0')
        _cluctrl.mUpdateErrorObject = MagicMock(return_value=None)
        dom0Name = 'test-dom0'
        with self.assertRaises(ExacloudRuntimeError):
            ebCluAcceleratedNetwork.validateEnvForacceletedNetworkFeature(_cluctrl, dom0Name)


    def test_getBondingOptions_with_slaves(self):
        """Test getBondingOptions with slaves provided"""
        _cluctrl = self.mGetClubox()
        gatewayIp = '10.0.0.1'
        slaves = 'eth0 eth1'
        options = ebCluAcceleratedNetwork.getBondingOptions(_cluctrl, gatewayIp, None, slaves, None)
        expected = ('mode=active-backup fail_over_mac=0 arp_interval=1000 '
                    'primary_reselect=failure arp_allslaves=0 primary=eth0 num_grat_arp=8 arp_ip_target=10.0.0.1')
        self.assertEqual(options, expected)

    def test_getBondingOptions_with_domuId(self):
        """Test getBondingOptions with domuId provided"""
        _cluctrl = self.mGetClubox()
        gatewayIp = '10.0.0.1'
        domuId = 'domu1'
        # Mock the machine config
        mock_machines = MagicMock()
        mock_machine_config = MagicMock()
        mock_machine_config.mGetMacHostName = MagicMock(return_value='testhost')
        mock_machines.mGetMachineConfig = MagicMock(return_value=mock_machine_config)
        _cluctrl.mGetMachines = MagicMock(return_value=mock_machines)
        # Mock networks for hostname lookup
        mock_networks = MagicMock()
        mock_network_config = MagicMock()
        mock_network_config.mGetNetSlave = MagicMock(return_value='eth2.0')
        mock_networks.mGetNetworkConfigByName = MagicMock(return_value=mock_network_config)
        _cluctrl.mGetNetworks = MagicMock(return_value=mock_networks)

        options = ebCluAcceleratedNetwork.getBondingOptions(_cluctrl, gatewayIp, None, None, domuId)
        expected = ('mode=active-backup fail_over_mac=0 arp_interval=1000 '
                    'primary_reselect=failure arp_allslaves=0 primary=eth2 num_grat_arp=8 arp_ip_target=10.0.0.1')
        self.assertEqual(options, expected)

    def test_getBondingOptions_default(self):
        """Test getBondingOptions default case"""
        _cluctrl = self.mGetClubox()
        gatewayIp = '10.0.0.1'
        options = ebCluAcceleratedNetwork.getBondingOptions(_cluctrl, gatewayIp, None, None, None)
        expected = ('mode=active-backup fail_over_mac=0 arp_interval=1000 '
                    'primary_reselect=failure arp_allslaves=0 primary=eth1 num_grat_arp=8 arp_ip_target=10.0.0.1')
        self.assertEqual(options, expected)

    def test_getBondingOptions_ipv6(self):
        """Test getBondingOptions with IPv6 gateway"""
        _cluctrl = self.mGetClubox()
        gatewayIp = '2001:db8::1'
        slaves = 'eth0 eth1'
        options = ebCluAcceleratedNetwork.getBondingOptions(_cluctrl, gatewayIp, None, slaves, None)
        expected = ('mode=active-backup fail_over_mac=0 arp_interval=1000 '
                    'primary_reselect=failure arp_allslaves=0 primary=eth0 num_unsol_na=8 ns_ip6_target=2001:db8::1')
        self.assertEqual(options, expected)

    def test_getBondingOptions_dual_stack(self):
        """Test getBondingOptions with dual stack gateways"""
        _cluctrl = self.mGetClubox()
        gatewayIp = '10.0.0.1'
        ipv6Gateway = '2001:db8::1'
        slaves = 'eth0 eth1'
        options = ebCluAcceleratedNetwork.getBondingOptions(_cluctrl, gatewayIp, ipv6Gateway, slaves, None)
        expected = ('mode=active-backup fail_over_mac=0 arp_interval=1000 '
                    'primary_reselect=failure arp_allslaves=0 primary=eth0 num_grat_arp=8 arp_ip_target=10.0.0.1 num_unsol_na=8 ns_ip6_target=2001:db8::1')
        self.assertEqual(options, expected)

    def test_addAcceleratedNetworkOedaAction_should_set(self):
        """Test addAcceleratedNetworkOedaAction when should set accelerated network"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=True)
        _cluctrl.mCheckConfigOption = MagicMock(return_value=True)
        _cluctrl.mGetExadataDom0Model = MagicMock(return_value='X11')
        _cluctrl.mGetImageVersion = MagicMock(return_value='26.1.0')
        # Mock networks
        mock_networks = MagicMock()
        mock_network_config = MagicMock()
        mock_network_config.mGetNetType = MagicMock(return_value='client')
        mock_network_config.mGetNetGateWay = MagicMock(return_value='10.0.0.1')
        mock_network_config.mGetNetSlave = MagicMock(return_value='eth0 eth1')
        mock_networks.mGetNetworkConfig = MagicMock(return_value=mock_network_config)
        _cluctrl.mGetNetworks = MagicMock(return_value=mock_networks)
        # Mock machines
        mock_machines = MagicMock()
        mock_machine_config = MagicMock()
        mock_machine_config.mGetMacHostName = MagicMock(return_value='testhost')
        mock_machines.mGetMachineConfig = MagicMock(return_value=mock_machine_config)
        _cluctrl.mGetMachines = MagicMock(return_value=mock_machines)

        listToAddOedaAction = []
        result = ebCluAcceleratedNetwork.addAcceleratedNetworkOedaAction(_cluctrl, 'net1', None, 'dom0', 'domu', 'sriov', listToAddOedaAction)
        self.assertEqual(len(result), 2)
        self.assertIn('ACCELERATEDNETWORK', str(result[0]))
        self.assertNotIn('slave', str(result[0]))  # For client, no slave

    def test_addAcceleratedNetworkOedaAction_should_set_backup(self):
        """Test addAcceleratedNetworkOedaAction when should set accelerated network for backup"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=True)
        _cluctrl.mCheckConfigOption = MagicMock(return_value=True)
        _cluctrl.mGetExadataDom0Model = MagicMock(return_value='X11')
        _cluctrl.mGetImageVersion = MagicMock(return_value='26.1.0')
        # Mock networks
        mock_networks = MagicMock()
        mock_network_config = MagicMock()
        mock_network_config.mGetNetType = MagicMock(return_value='backup')
        mock_network_config.mGetNetGateWay = MagicMock(return_value='10.0.0.1')
        mock_network_config.mGetNetSlave = MagicMock(return_value='eth0 eth1')
        mock_networks.mGetNetworkConfig = MagicMock(return_value=mock_network_config)
        _cluctrl.mGetNetworks = MagicMock(return_value=mock_networks)
        # Mock machines
        mock_machines = MagicMock()
        mock_machine_config = MagicMock()
        mock_machine_config.mGetMacHostName = MagicMock(return_value='testhost')
        mock_machines.mGetMachineConfig = MagicMock(return_value=mock_machine_config)
        _cluctrl.mGetMachines = MagicMock(return_value=mock_machines)

        listToAddOedaAction = []
        result = ebCluAcceleratedNetwork.addAcceleratedNetworkOedaAction(_cluctrl, 'net1', None, 'dom0', 'domu', 'sriov', listToAddOedaAction)
        self.assertEqual(len(result), 2)
        self.assertIn('ACCELERATEDNETWORK', str(result[0]))
        self.assertIn('slave', str(result[0]))  # For backup, slave is set
        self.assertIn('eth3 eth4', str(result[0]))

    def test_addAcceleratedNetworkOedaAction_should_not_set(self):
        """Test addAcceleratedNetworkOedaAction when should not set accelerated network"""
        _cluctrl = self.mGetClubox()
        listToAddOedaAction = []
        result = ebCluAcceleratedNetwork.addAcceleratedNetworkOedaAction(_cluctrl, 'net1', None, 'dom0', 'domu', 'virtio', listToAddOedaAction)
        self.assertEqual(len(result), 0)

    def test_addBondingConfigOedaAction_should_set(self):
        """Test addBondingConfigOedaAction when should set bonding config"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=True)
        _cluctrl.mCheckConfigOption = MagicMock(return_value=True)
        _cluctrl.mGetExadataDom0Model = MagicMock(return_value='X11')
        _cluctrl.mGetImageVersion = MagicMock(return_value='26.1.0')
        # Mock networks
        mock_networks = MagicMock()
        mock_network_config = MagicMock()
        mock_network_config.mGetNetType = MagicMock(return_value='client')
        mock_network_config.mGetNetGateWay = MagicMock(return_value='10.0.0.1')
        mock_network_config.mGetNetSlave = MagicMock(return_value='eth0 eth1')
        mock_networks.mGetNetworkConfig = MagicMock(return_value=mock_network_config)
        _cluctrl.mGetNetworks = MagicMock(return_value=mock_networks)
        # Mock machines
        mock_machines = MagicMock()
        mock_machine_config = MagicMock()
        mock_machine_config.mGetMacHostName = MagicMock(return_value='testhost')
        mock_machines.mGetMachineConfig = MagicMock(return_value=mock_machine_config)
        _cluctrl.mGetMachines = MagicMock(return_value=mock_machines)

        listToAddOedaAction = []
        result = ebCluAcceleratedNetwork.addBondingConfigOedaAction(_cluctrl, 'net1', None, 'dom0', 'domu', 'sriov', listToAddOedaAction)
        self.assertEqual(len(result), 1)
        self.assertIn('BONDING_OPTS', str(result[0]))

    def test_addBondingConfigOedaAction_should_not_set(self):
        """Test addBondingConfigOedaAction when should not set bonding config"""
        _cluctrl = self.mGetClubox()
        listToAddOedaAction = []
        result = ebCluAcceleratedNetwork.addBondingConfigOedaAction(_cluctrl, 'net1', None, 'dom0', 'domu', 'virtio', listToAddOedaAction)
        self.assertEqual(len(result), 0)

    def test_isClusterEnabledWithAcceleratedNetwork_true(self):
        """Test isClusterEnabledWithacceleratedNetwork when both networks are enabled"""
        _cluctrl = self.mGetClubox()
        mock_networks = MagicMock()
        mock_networks.mGetNetworkIdList = MagicMock(return_value=['net1', 'net2'])
        mock_net_client = MagicMock()
        mock_net_client.mGetNetType = MagicMock(return_value='client')
        mock_net_client.mGetAcceleratedNetwork = MagicMock(return_value='ENABLED')
        mock_net_backup = MagicMock()
        mock_net_backup.mGetNetType = MagicMock(return_value='backup')
        mock_net_backup.mGetAcceleratedNetwork = MagicMock(return_value='ENABLED')
        mock_networks.mGetNetworkConfig.side_effect = lambda netId: mock_net_client if netId == 'net1' else mock_net_backup
        _cluctrl.mGetNetworks = MagicMock(return_value=mock_networks)
        result = ebCluAcceleratedNetwork.isClusterEnabledWithAcceleratedNetwork(_cluctrl)
        self.assertTrue(result)

    def test_isClusterEnabledWithAcceleratedNetwork_false(self):
        """Test isClusterEnabledWithacceleratedNetwork when client network not enabled"""
        _cluctrl = self.mGetClubox()
        mock_networks = MagicMock()
        mock_networks.mGetNetworkIdList = MagicMock(return_value=['net1', 'net2'])
        mock_net_client = MagicMock()
        mock_net_client.mGetNetType = MagicMock(return_value='client')
        mock_net_client.mGetAcceleratedNetwork = MagicMock(return_value='DISABLED')
        mock_net_backup = MagicMock()
        mock_net_backup.mGetNetType = MagicMock(return_value='backup')
        mock_net_backup.mGetAcceleratedNetwork = MagicMock(return_value='ENABLED')
        mock_networks.mGetNetworkConfig.side_effect = lambda netId: mock_net_client if netId == 'net1' else mock_net_backup
        _cluctrl.mGetNetworks = MagicMock(return_value=mock_networks)
        result = ebCluAcceleratedNetwork.isClusterEnabledWithAcceleratedNetwork(_cluctrl)
        self.assertFalse(result)

    def tests_mCustomerNetworkXMLUpdateWithacceleratedNetwork(self):
        # This tests the single stack ipv6 payload
        _cluctrl = self.mGetClubox()
        # Mock networks to return gateway
        mock_networks = MagicMock()
        mock_network_config = MagicMock()
        mock_network_config.mGetNetGateWay = MagicMock(return_value='10.0.0.1')
        mock_networks.mGetNetworkConfig = MagicMock(return_value=mock_network_config)
        _cluctrl.mGetNetworks = MagicMock(return_value=mock_networks)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = PAYLOAD_CREATE_SERVICE_DUAL_STACK["jsonconf"]
        for node in _options.jsonconf.get('customer_network').get('nodes'):
            node.get('client')['network_virtualization'] = "SRIOV"
            node.get('backup')['network_virtualization'] = "SRIOV"
        self.mGetClubox().mSetExabm(True)
        _cluctrl.mCustomerNetworkXMLUpdate(_options)


    @patch('exabox.tools.oedacli.OedacliCmdMgr.setAcceleratedNetworkParams')
    def tests_mAddDomUWithacceleratedNetwork(self, mock_set_accelerated):
        _oeda_cli = OedacliCmdMgr(os.path.join(self.mGetUtil().mGetResourcesPath(),"sample.xml"), "/tmp/")
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = PAYLOAD_ADD_COMPUTE["jsonconf"]
        _json_payload = {}
        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU'):
            _reshape_obj = ebCluReshapeCompute(_cluctrl, _options)
            _json_payload = _reshape_obj.mGetReshapeConf()
        _json_payload['nodes'][0]['domU']['client']["network_virtualization"] = "SRIOV"
        _json_payload['nodes'][0]['domU']['client']['slaves'] = 'eth1 eth2'
        _json_payload['nodes'][0]['domU']['backup']["network_virtualization"] = "SRIOV"
        _json_payload['nodes'][0]['domU']['backup']['slaves'] = 'eth3 eth4'
        with patch('exabox.tools.oedacli.ebOedacli.run_oedacli'):
            _oeda_cli.mAddDomU("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                            "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com",
                            "/tmp/src.xml", "/tmp/dest.xml", _json_payload['nodes'][0], _cluctrl)

        # Assert setAcceleratedNetworkParams was called twice: once for client, once for backup
        self.assertEqual(mock_set_accelerated.call_count, 2)
        # Check calls
        calls = mock_set_accelerated.call_args_list
        # First call for client
        self.assertEqual(calls[0][0][1], _json_payload['nodes'][0]['dom0']['hostname'])  # dom0HostName
        self.assertEqual(calls[0][0][2], _json_payload['nodes'][0]['domU']['client']['fqdn'])  # networkHostname
        self.assertEqual(calls[0][0][3], _json_payload['nodes'][0]['domU']['client']['gateway'])  # gateWay
        self.assertEqual(calls[0][0][5], _json_payload['nodes'][0]['domU']['client'].get('slaves'))  # slaves
        self.assertEqual(calls[0][0][6], "client")
        self.assertEqual(calls[0][0][7], "SRIOV")  # network type
        # Second call for backup
        self.assertEqual(calls[1][0][1], _json_payload['nodes'][0]['dom0']['hostname'])
        self.assertEqual(calls[1][0][2], _json_payload['nodes'][0]['domU']['backup']['fqdn'])
        self.assertEqual(calls[1][0][3], _json_payload['nodes'][0]['domU']['backup']['gateway'])
        self.assertEqual(calls[1][0][5], _json_payload['nodes'][0]['domU']['backup'].get('slaves'))
        self.assertEqual(calls[1][0][6], "backup")
        self.assertEqual(calls[1][0][7], "SRIOV")

    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    def test_isDom0InterfaceEnabledWithSwitchDevMode_switchdev(self, mock_cmd_abs, mock_exec_cmd):
        """Test isDom0InterfaceEnabledWithSwitchDevMode when in switchdev mode"""
        mock_cmd_abs.side_effect = ['cat', 'devlink']
        mock_ret_obj_cat = MagicMock()
        mock_ret_obj_cat.exit_code = 0
        mock_ret_obj_cat.stdout = 'PCI_SLOT_NAME=0000:01:00.0\n'
        mock_ret_obj_devlink = MagicMock()
        mock_ret_obj_devlink.exit_code = 0
        mock_ret_obj_devlink.stdout = 'pci/0000:01:00.0: mode switchdev\n'
        mock_exec_cmd.side_effect = [mock_ret_obj_cat, mock_ret_obj_devlink]

        node = MagicMock()
        result = ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode(node, 'eth1')
        self.assertTrue(result)

    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    def test_isDom0InterfaceEnabledWithSwitchDevMode_not_switchdev(self, mock_cmd_abs, mock_exec_cmd):
        """Test isDom0InterfaceEnabledWithSwitchDevMode when not in switchdev mode"""
        mock_cmd_abs.side_effect = ['cat', 'devlink']
        mock_ret_obj_cat = MagicMock()
        mock_ret_obj_cat.exit_code = 0
        mock_ret_obj_cat.stdout = 'PCI_SLOT_NAME=0000:01:00.0\n'
        mock_ret_obj_devlink = MagicMock()
        mock_ret_obj_devlink.exit_code = 0
        mock_ret_obj_devlink.stdout = 'pci/0000:01:00.0: mode legacy\n'
        mock_exec_cmd.side_effect = [mock_ret_obj_cat, mock_ret_obj_devlink]

        node = MagicMock()
        result = ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode(node, 'eth1')
        self.assertFalse(result)

    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    def test_isDom0InterfaceEnabledWithSwitchDevMode_command_fail(self, mock_cmd_abs, mock_exec_cmd):
        """Test isDom0InterfaceEnabledWithSwitchDevMode when command fails"""
        mock_cmd_abs.return_value = 'cat'
        mock_ret_obj = MagicMock()
        mock_ret_obj.exit_code = 1
        mock_exec_cmd.return_value = mock_ret_obj

        node = MagicMock()
        result = ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode(node, 'eth1')
        self.assertFalse(result)

    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    def test_getPhysicalFnCandidatesForVirtualFn(self, mock_cmd_abs, mock_exec_cmd):
        """Test getPhysicalFnCandidatesForVirtualFn"""
        mock_cmd_abs.return_value = 'ls'
        mock_ret_obj = MagicMock()
        mock_ret_obj.exit_code = 0
        mock_ret_obj.stdout = 'eth0\neth1\n'
        mock_exec_cmd.return_value = mock_ret_obj

        node = MagicMock()
        result = ebCluAcceleratedNetwork.getPhysicalFnCandidatesForVirtualFn(node, 'vf0')
        self.assertEqual(result, ['eth0', 'eth1'])

    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.getPhysicalFnCandidatesForVirtualFn')
    def test_getVirtualFnSlaveForPhysicalFnSlave_found(self, mock_get_pf, mock_cmd_abs, mock_exec_cmd):
        """Test getVirtualFnSlaveForPhysicalFnSlave when match found"""
        mock_cmd_abs.return_value = 'cat'
        mock_ret_obj = MagicMock()
        mock_ret_obj.exit_code = 0
        mock_ret_obj.stdout = 'eth1vf1 eth2vf2\n'
        mock_exec_cmd.return_value = mock_ret_obj

        mock_get_pf.return_value = ['eth1', 'eth100', 'eth101']

        node = MagicMock()
        result = ebCluAcceleratedNetwork.getVirtualFnSlaveForPhysicalFnSlave(node, 'bond0', 'eth1')
        self.assertEqual(result, 'eth1vf1')

    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.getPhysicalFnCandidatesForVirtualFn')
    def test_getVirtualFnSlaveForPhysicalFnSlave_not_found(self, mock_get_pf, mock_cmd_abs, mock_exec_cmd):
        """Test getVirtualFnSlaveForPhysicalFnSlave when no match"""
        mock_cmd_abs.return_value = 'cat'
        mock_ret_obj = MagicMock()
        mock_ret_obj.exit_code = 0
        mock_ret_obj.stdout = 'eth0 eth1\n'
        mock_exec_cmd.return_value = mock_ret_obj

        mock_get_pf.return_value = ['eth2']

        node = MagicMock()
        result = ebCluAcceleratedNetwork.getVirtualFnSlaveForPhysicalFnSlave(node, 'bond0', 'eth0')
        self.assertIsNone(result)

    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    def test_getVirtualFnSlaveForPhysicalFnSlave_exception(self, mock_cmd_abs, mock_exec_cmd):
        """Test getVirtualFnSlaveForPhysicalFnSlave when exception"""
        mock_cmd_abs.return_value = 'cat'
        mock_exec_cmd.side_effect = Exception("Command failed")

        node = MagicMock()
        result = ebCluAcceleratedNetwork.getVirtualFnSlaveForPhysicalFnSlave(node, 'bond0', 'eth0')
        self.assertIsNone(result)

    def test_checkInputAndValidateEnvForAcceleratedNetwork_virtio(self):
        """Test checkInputAndValidateEnvForAcceleratedNetwork with virtio"""
        _cluctrl = self.mGetClubox()
        result = ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(_cluctrl, 'dom0', 'domu', 'virtio')
        self.assertFalse(result)

    def test_checkInputAndValidateEnvForAcceleratedNetwork_none(self):
        """Test checkInputAndValidateEnvForAcceleratedNetwork with None"""
        _cluctrl = self.mGetClubox()
        result = ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(_cluctrl, 'dom0', 'domu', None)
        self.assertFalse(result)

    def test_checkInputAndValidateEnvForAcceleratedNetwork_undefined(self):
        """Test checkInputAndValidateEnvForAcceleratedNetwork with UNDEFINED"""
        _cluctrl = self.mGetClubox()
        result = ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(_cluctrl, 'dom0', 'domu', 'UNDEFINED')
        self.assertFalse(result)

    def test_checkInputAndValidateEnvForAcceleratedNetwork_sriov(self):
        """Test checkInputAndValidateEnvForAcceleratedNetwork with sriov"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mIsExabm = MagicMock(return_value=True)
        _cluctrl.mCheckConfigOption = MagicMock(return_value=True)
        _cluctrl.mGetExadataDom0Model = MagicMock(return_value='X11')
        _cluctrl.mGetImageVersion = MagicMock(return_value='26.1.0')
        _cluctrl.mUpdateErrorObject = MagicMock(return_value=None)
        result = ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(_cluctrl, 'dom0', 'domu', 'sriov')
        self.assertTrue(result)

    def test_checkInputAndValidateEnvForAcceleratedNetwork_invalid(self):
        """Test checkInputAndValidateEnvForAcceleratedNetwork with invalid value"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mUpdateErrorObject = MagicMock(return_value=None)
        with self.assertRaises(ExacloudRuntimeError):
            ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(_cluctrl, 'dom0', 'domu', 'invalid')

    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.createIfcfgPfFile')
    @patch('exabox.ovm.cluacceleratednetwork.node_update_key_val_file')
    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode')
    def test_setMtuForPhysicalFunction_success(self, mock_switchdev, mock_cmd_abs, mock_exec_cmd, mock_update, mock_create_ifcfg):
        """Test setMtuForPhysicalFunction success when ifcfg file exists"""
        mock_switchdev.return_value = True
        mock_cmd_abs.return_value = '/usr/sbin/ip'
        mock_exec_cmd.return_value = MagicMock(exit_code=0)
        node = MagicMock()
        node.mFileExists.return_value = True

        result = ebCluAcceleratedNetwork.setMtuForPhysicalFunction(node, 'eth1')
        self.assertTrue(result)
        mock_exec_cmd.assert_called_once()
        mock_update.assert_called_once_with(node, '/etc/sysconfig/network-scripts/ifcfg-eth1pf', {"MTU": "9000"})
        mock_create_ifcfg.assert_not_called()

    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.createIfcfgPfFile')
    @patch('exabox.ovm.cluacceleratednetwork.node_update_key_val_file')
    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode')
    def test_setMtuForPhysicalFunction_create_ifcfg(self, mock_switchdev, mock_cmd_abs, mock_exec_cmd, mock_update, mock_create_ifcfg):
        """Test setMtuForPhysicalFunction when ifcfg file doesn't exist"""
        mock_switchdev.return_value = True
        mock_cmd_abs.return_value = '/usr/sbin/ip'
        mock_exec_cmd.return_value = MagicMock(exit_code=0)
        node = MagicMock()
        node.mFileExists.return_value = False

        result = ebCluAcceleratedNetwork.setMtuForPhysicalFunction(node, 'eth1')
        self.assertTrue(result)
        mock_exec_cmd.assert_called_once()
        mock_update.assert_not_called()
        mock_create_ifcfg.assert_called_once_with(node, 'eth1pf', '/etc/sysconfig/network-scripts/ifcfg-eth1pf')

    @patch('exabox.ovm.cluacceleratednetwork.node_write_text_file')
    def test_createIfcfgPfFile(self, mock_write_text):
        """Test createIfcfgPfFile creates correct ifcfg content"""
        node = MagicMock()
        ebCluAcceleratedNetwork.createIfcfgPfFile(node, 'eth1pf', '/etc/sysconfig/network-scripts/ifcfg-eth1pf')

        expected_content = """DEVICE=eth1pf
TYPE=Ethernet
USERCTL=no
ONBOOT=yes
BOOTPROTO=none
MTU=9000
HOTPLUG=no
IPV6INIT=no
NM_CONTROLLED=no
"""
        mock_write_text.assert_called_once_with(node, '/etc/sysconfig/network-scripts/ifcfg-eth1pf', expected_content)

    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode')
    def test_setMtuForPhysicalFunction_not_switchdev(self, mock_switchdev):
        """Test setMtuForPhysicalFunction when not in switchdev mode"""
        mock_switchdev.return_value = False
        node = MagicMock()

        result = ebCluAcceleratedNetwork.setMtuForPhysicalFunction(node, 'eth1')
        self.assertTrue(result)

    @patch('exabox.ovm.cluacceleratednetwork.node_exec_cmd')
    @patch('exabox.ovm.cluacceleratednetwork.node_cmd_abs_path_check')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode')
    def test_setMtuForPhysicalFunction_exception(self, mock_switchdev, mock_cmd_abs, mock_exec_cmd):
        """Test setMtuForPhysicalFunction when exception occurs"""
        mock_switchdev.return_value = True
        mock_cmd_abs.return_value = '/usr/sbin/ip'
        mock_exec_cmd.side_effect = Exception("Command failed")
        node = MagicMock()

        result = ebCluAcceleratedNetwork.setMtuForPhysicalFunction(node, 'eth1')
        self.assertFalse(result)

    @patch('exabox.tools.oedacli.ebOedacli')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.getBondingOptions')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork')
    def test_setAcceleratedNetworkParams_enabled(self, mock_check, mock_get_bonding, mock_ebOedacli):
        """Test setAcceleratedNetworkParams when accelerated network is enabled"""
        from exabox.tools.oedacli import OedacliCmdMgr
        mock_check.return_value = True
        mock_get_bonding.return_value = 'mode=active-backup fail_over_mac=0 num_grat_arp=8 arp_interval=1000 primary_reselect=failure arp_allslaves=1 arp_ip_target=10.0.0.1 primary=eth1'
        mock_oxm = MagicMock()
        mock_ebOedacli.return_value = mock_oxm

        oeda_cli = OedacliCmdMgr('/tmp/sample.xml', '/tmp/')
        _cluctrl = self.mGetClubox()
        oeda_cli.setAcceleratedNetworkParams(_cluctrl, 'dom0.example.com', 'domu.example.com', '10.0.0.1', 'eth1 eth2', 'client', 'sriov')

        mock_check.assert_called_once_with(_cluctrl, 'dom0.example.com', 'domu.example.com', 'virtio')
        mock_get_bonding.assert_called_once_with(_cluctrl, '10.0.0.1', 'eth1 eth2', 'client', None)
        mock_oxm.oc_cmd.assert_called_once()
        mock_oxm.save_action.assert_called_once()
        mock_oxm.merge_actions.assert_called_once_with(True)

    @patch('exabox.tools.oedacli.ebOedacli')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.getBondingOptions')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork')
    def test_setAcceleratedNetworkParams_disabled(self, mock_check, mock_get_bonding, mock_ebOedacli):
        """Test setAcceleratedNetworkParams when accelerated network is disabled"""
        from exabox.tools.oedacli import OedacliCmdMgr
        mock_check.return_value = False
        mock_oxm = MagicMock()
        mock_ebOedacli.return_value = mock_oxm

        oeda_cli = OedacliCmdMgr('/tmp/sample.xml', '/tmp/')
        _cluctrl = self.mGetClubox()
        oeda_cli.setAcceleratedNetworkParams(_cluctrl, 'dom0.example.com', 'domu.example.com', '10.0.0.1', 'eth1 eth2', 'client', 'virtio')

        mock_check.assert_called_once_with(_cluctrl, 'dom0.example.com', 'domu.example.com', 'virtio')
        mock_get_bonding.assert_not_called()
        mock_oxm.oc_cmd.assert_not_called()
        mock_oxm.save_action.assert_not_called()
        mock_oxm.merge_actions.assert_not_called()

    @patch('exabox.tools.oedacli.ebOedacli')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.getBondingOptions')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork')
    def test_setAcceleratedNetworkParams_default_slaves_client(self, mock_check, mock_get_bonding, mock_ebOedacli):
        """Test setAcceleratedNetworkParams with default slaves for client network"""
        from exabox.tools.oedacli import OedacliCmdMgr
        mock_check.return_value = True
        mock_get_bonding.return_value = 'mode=active-backup fail_over_mac=0 num_grat_arp=8 arp_interval=1000 primary_reselect=failure arp_allslaves=1 arp_ip_target=10.0.0.1 primary=eth1'
        mock_oxm = MagicMock()
        mock_ebOedacli.return_value = mock_oxm

        oeda_cli = OedacliCmdMgr('/tmp/sample.xml', '/tmp/')
        _cluctrl = self.mGetClubox()
        oeda_cli.setAcceleratedNetworkParams(_cluctrl, 'dom0.example.com', 'domu.example.com', '10.0.0.1', None, 'client', 'sriov')

        mock_get_bonding.assert_called_once_with(_cluctrl, '10.0.0.1', None, 'client', None)
        mock_oxm.oc_cmd.assert_called_once()
        args, kwargs = mock_oxm.oc_cmd.call_args
        self.assertEqual(kwargs['arguments']['ACCELERATEDNETWORK'], 'ENABLED')
        self.assertEqual(kwargs['where']['networktype'], 'sriov')

    @patch('exabox.tools.oedacli.ebOedacli')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.getBondingOptions')
    @patch('exabox.ovm.cluacceleratednetwork.ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork')
    def test_setAcceleratedNetworkParams_default_slaves_backup(self, mock_check, mock_get_bonding, mock_ebOedacli):
        """Test setAcceleratedNetworkParams with default slaves for backup network"""
        from exabox.tools.oedacli import OedacliCmdMgr
        mock_check.return_value = True
        mock_get_bonding.return_value = 'mode=active-backup fail_over_mac=0 num_grat_arp=8 arp_interval=1000 primary_reselect=failure arp_allslaves=0 arp_ip_target=10.0.0.1 primary=eth3'
        mock_oxm = MagicMock()
        mock_ebOedacli.return_value = mock_oxm

        oeda_cli = OedacliCmdMgr('/tmp/sample.xml', '/tmp/')
        _cluctrl = self.mGetClubox()
        oeda_cli.setAcceleratedNetworkParams(_cluctrl, 'dom0.example.com', 'domu.example.com', '10.0.0.1', '', 'eth1 eth2', 'backup')

        mock_get_bonding.assert_called_once_with(_cluctrl, '10.0.0.1', '', 'eth3 eth4', None)
        mock_oxm.oc_cmd.assert_called_once()
        args, kwargs = mock_oxm.oc_cmd.call_args
        self.assertEqual(kwargs['arguments']['ACCELERATEDNETWORK'], 'ENABLED')
        self.assertEqual(kwargs['where']['networktype'], 'backup')
        self.assertEqual(kwargs['where']['networkhostname'], 'domu')


if __name__ == '__main__':
    unittest.main()

