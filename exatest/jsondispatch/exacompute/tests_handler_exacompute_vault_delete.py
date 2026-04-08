#!/bin/python
#
# $Header: tests_handler_exacompute_vault_delete.py 27-mar-2026.02:43:06 avimonda Exp $
#
# tests_handler_exacompute_vault_delete.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_handler_exacompute_vault_delete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    03/27/26 - Add exatest coverage for vault delete missing
#                           config
#    avimonda    03/27/26 - Creation
#
import unittest

from unittest.mock import patch

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_exacompute_vault_delete import ExaComputeDeleteVault


class ebTestExaComputeDeleteVault(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    @patch("exabox.jsondispatch.handler_exacompute_vault_delete.connect_to_host")
    def test_001_skips_connect_when_hostname_missing(self, mock_connect_to_host):

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload_SSH_Generation.json")
        _options.jsonconf["hostname"] = "No_Given_Value"

        _handler = ExaComputeDeleteVault(_options)
        _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 0)
        self.assertEqual(_result, {})
        mock_connect_to_host.assert_not_called()

    @patch("exabox.jsondispatch.handler_exacompute_vault_delete.connect_to_host")
    def test_002_skips_connect_when_fqdn_missing(self, mock_connect_to_host):

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload_SSH_Generation.json")
        _options.jsonconf["fqdn"] = "No_Given_Value"

        _handler = ExaComputeDeleteVault(_options)
        _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 0)
        self.assertEqual(_result, {})
        mock_connect_to_host.assert_not_called()


if __name__ == "__main__":
    unittest.main()

# end of the file
