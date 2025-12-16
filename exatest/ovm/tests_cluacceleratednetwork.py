#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluacceleratednetwork.py /main/2 2025/12/01 04:43:08 mpedapro Exp $
#
# tests_cluacceleratednetwork.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
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


    def test_getBondingOptions(self):
        """Test getBondingOptions"""
        _cluctrl = self.mGetClubox()
        gatewayIp = '10.0.0.1'
        options = ebCluAcceleratedNetwork.getBondingOptions(_cluctrl, gatewayIp, None, None)
        expected = ('mode=active-backup fail_over_mac=1 num_grat_arp=8 arp_interval=1000 '
                    'primary_reselect=failure arp_allslaves=1 arp_ip_target=10.0.0.1 primary=eth1')
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
        mock_networks.mGetNetworkConfig = MagicMock(return_value=mock_network_config)
        _cluctrl.mGetNetworks = MagicMock(return_value=mock_networks)

        listToAddOedaAction = []
        result = ebCluAcceleratedNetwork.addAcceleratedNetworkOedaAction(_cluctrl, 'net1', 'dom0', 'domu', 'sriov', listToAddOedaAction)
        self.assertEqual(len(result), 1)
        self.assertIn('ACCELERATEDNETWORK', str(result[0]))

    def test_addAcceleratedNetworkOedaAction_should_not_set(self):
        """Test addAcceleratedNetworkOedaAction when should not set accelerated network"""
        _cluctrl = self.mGetClubox()
        listToAddOedaAction = []
        result = ebCluAcceleratedNetwork.addAcceleratedNetworkOedaAction(_cluctrl, 'net1', 'dom0', 'domu', 'virtio', listToAddOedaAction)
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
        mock_networks.mGetNetworkConfig = MagicMock(return_value=mock_network_config)
        _cluctrl.mGetNetworks = MagicMock(return_value=mock_networks)

        listToAddOedaAction = []
        result = ebCluAcceleratedNetwork.addBondingConfigOedaAction(_cluctrl, 'net1', 'dom0', 'domu', 'sriov', listToAddOedaAction)
        self.assertEqual(len(result), 1)
        self.assertIn('BONDING_OPTS', str(result[0]))

    def test_addBondingConfigOedaAction_should_not_set(self):
        """Test addBondingConfigOedaAction when should not set bonding config"""
        _cluctrl = self.mGetClubox()
        listToAddOedaAction = []
        result = ebCluAcceleratedNetwork.addBondingConfigOedaAction(_cluctrl, 'net1', 'dom0', 'domu', 'virtio', listToAddOedaAction)
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
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = PAYLOAD_CREATE_SERVICE_DUAL_STACK["jsonconf"]
        for node in _options.jsonconf.get('customer_network').get('nodes'):
            node.get('client')['network_virtualization'] = "SRIOV"
            node.get('backup')['network_virtualization'] = "SRIOV"
        self.mGetClubox().mSetExabm(True)
        _cluctrl.mCustomerNetworkXMLUpdate(_options)


    def tests_mAddDomUWithacceleratedNetwork(self):
        _oeda_cli = OedacliCmdMgr(os.path.join(self.mGetUtil().mGetResourcesPath(),"sample.xml"), "/tmp/")
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = PAYLOAD_ADD_COMPUTE["jsonconf"]
        _json_payload = {}
        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU'):
            _reshape_obj = ebCluReshapeCompute(_cluctrl, _options)
            _json_payload = _reshape_obj.mGetReshapeConf()
        _json_payload['nodes'][0]['domU']['client']["network_virtualization"] = "SRIOV"
        _json_payload['nodes'][0]['domU']['backup']["network_virtualization"] = "SRIOV"
        with patch('exabox.tools.oedacli.ebOedacli.run_oedacli'):
            _oeda_cli.mAddDomU("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                            "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com",
                            "/tmp/src.xml", "/tmp/dest.xml", _json_payload['nodes'][0], _cluctrl)

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


if __name__ == '__main__':
    unittest.main()

