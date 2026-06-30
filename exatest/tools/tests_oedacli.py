#!/bin/python
#
# $Header: tests_oedacli.py 04-mar-2026.06:15:59 pbellary Exp $
#
# tests_oedacli.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_oedacli.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    03/04/26 - Bug 39037277 - CLUSTER XMLS GET BONDETH4 SET FOR BACKUP NETWORK CONFIGURATION INSTEAD OF BONDETH1
#    pbellary    03/04/26 - Creation
#
import unittest
from unittest import mock

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[4]
_repo_root_str = str(_repo_root)
if _repo_root_str not in sys.path:
    sys.path.insert(0, _repo_root_str)

from exabox.tools.oedacli import OedacliCmdMgr


class TestOedacliCmdMgr(unittest.TestCase):

    def setUp(self):
        patcher = mock.patch('exabox.tools.oedacli.ebOedacli', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_ebOedacli = patcher.start()
        self.mock_oxm = mock.Mock()
        self.mock_ebOedacli.return_value = self.mock_oxm
        self.cmd_mgr = OedacliCmdMgr('/fake/oedacli', '/fake/save_dir')

    def _make_clone_payload(self):
        return {
            'admin': {
                'fqdn': 'cell-admin',
                'ipaddr': '10.0.0.1',
                'gateway': '10.0.0.254',
                'netmask': '255.255.255.0'
            },
            'priv1': {'fqdn': 'cell-priv1', 'ipaddr': '192.168.0.1'},
            'priv2': {'fqdn': 'cell-priv2', 'ipaddr': '192.168.1.1'},
            'ilom': {'fqdn': 'cell-ilom', 'ipaddr': '10.0.1.1'},
            'rack_num': '01',
            'uloc': 'U01'
        }

    def test_mUpdateNetworkSlaves_uses_master_when_provided(self):
        self.mock_oxm.reset_mock()

        self.cmd_mgr.mUpdateNetworkSlaves(
            ['eth0', 'eth1'],
            'ID123',
            'host1',
            'client',
            '/path/src.xml',
            '/path/dest.xml',
            aMaster='bondeth0'
        )

        self.mock_oxm.oc_cmd.assert_called_once_with(
            command='ALTER NETWORK MASTER="bondeth0" SLAVE="eth0,eth1"',
            where={'ID': 'ID123', 'HOSTNAME': 'host1', 'NETWORKTYPE': 'client'}
        )
        self.mock_oxm.save_action.assert_called_once_with()
        self.mock_oxm.run_oedacli.assert_called_once_with('/path/src.xml', '/path/dest.xml', None, False)

    def test_mUpdateNetworkSlaves_without_master_uses_slave_only_command(self):
        self.mock_oxm.reset_mock()

        self.cmd_mgr.mUpdateNetworkSlaves(
            ['eth2'],
            'ID999',
            'host2',
            'backup',
            '/tmp/source.xml',
            '/tmp/dest.xml'
        )

        self.mock_oxm.oc_cmd.assert_called_once_with(
            command='ALTER NETWORK SLAVE="eth2"',
            where={'ID': 'ID999', 'HOSTNAME': 'host2', 'NETWORKTYPE': 'backup'}
        )
        self.mock_oxm.save_action.assert_called_once_with()
        self.mock_oxm.run_oedacli.assert_called_once_with('/tmp/source.xml', '/tmp/dest.xml', None, False)

    def test_mBuildCloneCell_includes_machine_type_when_provided(self):
        self.mock_oxm.reset_mock()
        payload = self._make_clone_payload()

        self.cmd_mgr.mBuildCloneCell('src-cell', payload, aKVM=True, aMachineType='X11MEF')

        first_command = self.mock_oxm.oc_cmd.call_args_list[0].kwargs['command']
        self.assertEqual(first_command, "CLONE NEWCELL SRCNAME='src-cell' TGTNAME='cell-admin' TYPE='X11MEF'")
        self.assertTrue(any("TYPE='X11MEF'" in call.kwargs['command'] for call in self.mock_oxm.oc_cmd.call_args_list))

    def test_mBuildCloneCell_omits_machine_type_when_not_provided(self):
        self.mock_oxm.reset_mock()
        payload = self._make_clone_payload()

        self.cmd_mgr.mBuildCloneCell('src-cell', payload, aKVM=True)

        first_command = self.mock_oxm.oc_cmd.call_args_list[0].kwargs['command']
        self.assertEqual(first_command, "CLONE NEWCELL SRCNAME='src-cell' TGTNAME='cell-admin'")
        self.assertFalse(any("TYPE=" in call.kwargs['command'] for call in self.mock_oxm.oc_cmd.call_args_list))


if __name__ == '__main__':
    unittest.main()
