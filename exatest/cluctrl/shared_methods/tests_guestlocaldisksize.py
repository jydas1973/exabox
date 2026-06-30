#!/bin/python
#
# $Header: $
#
# tests_guestlocaldisksize.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#

import sys
import types
import unittest
import xml.etree.ElementTree as etree
from unittest.mock import MagicMock


def _install_import_stubs():
    if 'pymysql' not in sys.modules:
        sys.modules['pymysql'] = types.ModuleType('pymysql')

    if 'defusedxml' not in sys.modules:
        sys.modules['defusedxml'] = types.ModuleType('defusedxml')

    if 'defusedxml.ElementTree' not in sys.modules:
        _element_tree = types.ModuleType('defusedxml.ElementTree')
        _element_tree.Element = etree.Element
        _element_tree.fromstring = etree.fromstring
        _element_tree.parse = etree.parse
        sys.modules['defusedxml.ElementTree'] = _element_tree
        sys.modules['defusedxml'].ElementTree = _element_tree


_install_import_stubs()

from exabox.ovm.clucontrol import exaBoxCluCtrl


class TestGuestLocalDiskSizeXmlPatching(unittest.TestCase):
    def _build_ctrl(self, machine_config):
        ctrl = exaBoxCluCtrl.__new__(exaBoxCluCtrl)
        ctrl._exaBoxCluCtrl__machines = MagicMock()
        ctrl._exaBoxCluCtrl__machines.mGetMachineConfig.return_value = machine_config
        ctrl._exaBoxCluCtrl__extraXmlPatchingCommands = []
        ctrl.mReturnDom0DomUPair = MagicMock(return_value=[('dom0', 'domu1')])
        return ctrl

    def test_mAddVdiskCmds_adds_setvdisk_command_from_guest_local_disk_size(self):
        machine_config = MagicMock()
        machine_config.mGetMacHostName.return_value = 'domu1'
        machine_config.mGetGuestLocalDiskSize.return_value = ' 150Gb '

        ctrl = self._build_ctrl(machine_config)
        ctrl.mAddVdiskCmds()

        self.assertEqual(
            ctrl.mGetExtrXmlPatchingCmds(),
            [[
                'ALTER MACHINE',
                {'ACTION': 'SETVDISK', 'VDISK': '150G'},
                {'HOSTNAME': 'domu1'},
            ]]
        )

    def test_mAddVdiskCmds_skips_domu_without_guest_local_disk_size(self):
        machine_config = MagicMock()
        machine_config.mGetMacHostName.return_value = 'domu1'
        machine_config.mGetGuestLocalDiskSize.return_value = None

        ctrl = self._build_ctrl(machine_config)
        ctrl.mAddVdiskCmds()

        self.assertEqual(ctrl.mGetExtrXmlPatchingCmds(), [])


if __name__ == '__main__':
    unittest.main()
