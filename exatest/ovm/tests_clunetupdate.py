#!/usr/bin/env python
#
# tests_clunetupdate.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_clunetupdate.py - Unit tests for clunetupdate.py
#
#    DESCRIPTION
#      Focused regression tests for update_networks command hardening.
#

from contextlib import nullcontext
import unittest
from unittest.mock import MagicMock, call, patch

from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.clunetupdate import (
    BOND_UTILS,
    REMOTE_ROLLBACK_VLANID,
    NetUpdates,
    NodeVMNetUpdates,
    bond_for_vlan,
    shell_join,
    update_networks,
)


NFT_RULES = '/etc/nftables/exadata.nft'
RPM_PATH = '/tmp/bondmonitor.rpm'


class TestUpdateNetworks(unittest.TestCase):

    def _make_conf(
            self,
            vm_name: str = 'exa01db01.example.com',
            net_type: str = 'client') -> NodeVMNetUpdates:
        return NodeVMNetUpdates(
            dom0='dom0.example.com',
            domu_vm_name=vm_name,
            net_updates={
                net_type: NetUpdates(
                    vlans=(None, 100),
                    macs=(None, '00:00:17:01:24:7a', '02:00:28:12:35:8b'),
                )
            })

    def _mock_node(
            self,
            update_nft_rules: bool = True,
            rollback_script: bool = True) -> MagicMock:
        node = MagicMock()

        def file_exists(path: str) -> bool:
            if path == NFT_RULES:
                return update_nft_rules
            if path == REMOTE_ROLLBACK_VLANID:
                return rollback_script
            return False

        node.mFileExists.side_effect = file_exists
        return node

    @patch('exabox.ovm.clunetupdate.clubonding.install_bond_monitor_rpm')
    @patch('exabox.ovm.clunetupdate.clubonding.node_create_bonding_dirs')
    @patch(
        'exabox.ovm.clunetupdate.clubonding.get_bond_monitor_rpm_local_path',
        return_value=RPM_PATH)
    @patch('exabox.ovm.clunetupdate.node_exec_cmd_check')
    @patch('exabox.ovm.clunetupdate.connect_to_host')
    def test_update_networks_uses_shell_joined_commands(
            self,
            mock_connect_to_host,
            mock_node_exec_cmd_check,
            _mock_rpm_path,
            _mock_create_bonding_dirs,
            _mock_install_bond_monitor_rpm):
        node = self._mock_node()
        mock_connect_to_host.return_value = nullcontext(node)

        update_networks(None, [self._make_conf()])

        old_bond = f'"{bond_for_vlan(0)}"'
        new_bond = f'"{bond_for_vlan(100)}"'
        self.assertEqual(mock_node_exec_cmd_check.call_args_list, [
            call(node, shell_join([
                BOND_UTILS, 'change_mac', 'exa01db01.example.com', 0,
                'client', '02:00:28:12:35:8b', '00:00:17:01:24:7a'
            ])),
            call(node, shell_join([
                BOND_UTILS, 'change_vlan', 'exa01db01.example.com', 'client',
                100, 0
            ])),
            call(node, shell_join([
                '/bin/sed', '-i', f's/{old_bond}/{new_bond}/g', NFT_RULES
            ])),
            call(node, '/bin/systemctl restart nftables'),
        ])

    @patch('exabox.ovm.clunetupdate.start_domu')
    @patch('exabox.ovm.clunetupdate.shutdown_domu')
    @patch('exabox.ovm.clunetupdate.clubonding.install_bond_monitor_rpm')
    @patch('exabox.ovm.clunetupdate.clubonding.node_create_bonding_dirs')
    @patch(
        'exabox.ovm.clunetupdate.clubonding.get_bond_monitor_rpm_local_path',
        return_value=RPM_PATH)
    @patch('exabox.ovm.clunetupdate.node_exec_cmd_check')
    @patch('exabox.ovm.clunetupdate.connect_to_host')
    def test_update_networks_rollback_uses_shell_joined_script(
            self,
            mock_connect_to_host,
            mock_node_exec_cmd_check,
            _mock_rpm_path,
            _mock_create_bonding_dirs,
            _mock_install_bond_monitor_rpm,
            mock_shutdown_domu,
            mock_start_domu):
        node = self._mock_node()
        mock_connect_to_host.return_value = nullcontext(node)

        update_networks(
            None,
            [NodeVMNetUpdates(
                dom0='dom0.example.com',
                domu_vm_name='exa01db01.example.com',
                net_updates={},
            )],
            rollback=True)

        mock_shutdown_domu.assert_called_once_with(
            node, 'exa01db01.example.com')
        mock_start_domu.assert_called_once_with(
            node, 'exa01db01.example.com', wait_for_connectable=False)
        self.assertIn(
            call(node, shell_join([
                REMOTE_ROLLBACK_VLANID, 'exa01db01.example.com'
            ])),
            mock_node_exec_cmd_check.call_args_list)

    @patch('exabox.ovm.clunetupdate.clubonding.install_bond_monitor_rpm')
    @patch('exabox.ovm.clunetupdate.clubonding.node_create_bonding_dirs')
    @patch(
        'exabox.ovm.clunetupdate.clubonding.get_bond_monitor_rpm_local_path',
        return_value=RPM_PATH)
    @patch('exabox.ovm.clunetupdate.node_exec_cmd_check')
    @patch('exabox.ovm.clunetupdate.connect_to_host')
    def test_update_networks_rejects_invalid_vm_name(
            self,
            mock_connect_to_host,
            mock_node_exec_cmd_check,
            _mock_rpm_path,
            _mock_create_bonding_dirs,
            _mock_install_bond_monitor_rpm):
        with self.assertRaisesRegex(
                ExacloudRuntimeError,
                r'Invalid VM name: exa01db01; touch /tmp/pwned'):
            update_networks(
                None,
                [self._make_conf(
                    vm_name='exa01db01; touch /tmp/pwned')])

        mock_connect_to_host.assert_not_called()
        mock_node_exec_cmd_check.assert_not_called()


if __name__ == '__main__':
    unittest.main()
