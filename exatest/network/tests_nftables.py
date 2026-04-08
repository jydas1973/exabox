#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/network/tests_nftables.py /main/1 2026/04/03 00:00:00 codex Exp $
#
# tests_nftables.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
import unittest
from unittest import mock

from exabox.network.NfTables import NfTables


class TestNfTables(unittest.TestCase):
    def test_convert_config_to_command_appends_strings(self):
        nft = NfTables()
        with mock.patch.object(nft, 'convertConfigToJson', return_value=[{'dummy': 'value'}]):
            with mock.patch.object(nft, 'convertJsonConfigToCmd', return_value='my command') as mock_conv:
                result = nft.convertConfigToCommand('config')
        self.assertEqual(result, ['my command'])
        mock_conv.assert_called_once()

    def test_convert_config_to_command_skips_empty_strings(self):
        nft = NfTables()
        with mock.patch.object(nft, 'convertConfigToJson', return_value=[{'dummy': 'value'}]):
            with mock.patch.object(nft, 'convertJsonConfigToCmd', return_value=''):
                result = nft.convertConfigToCommand('config')
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
