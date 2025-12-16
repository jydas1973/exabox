#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/hostaccesscontrol/tests_handler_hostaccesscontrol.py /main/1 2025/11/18 03:55:10 shapatna Exp $
#
# tests_handler_hostaccesscontrol.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_handler_hostaccesscontrol.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    11/13/25 - Enh 38574081: Add unit tests to improve the
#                           coverage using Cline
#    shapatna    11/13/25 - Creation
#
import io
import unittest
from unittest.mock import patch, Mock, MagicMock

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.jsondispatch.handler_hostaccesscontrol import (
    ECHostAccessControlHandler,
    validateIPV4CIDR,
)

class ebTestHostaccesscontrol(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    # -------------------------------
    # Validators truth table coverage
    # -------------------------------
    def test_validateIPV4CIDR_truth_table(self):
        # Valid CIDRs
        self.assertTrue(validateIPV4CIDR("10.0.0.0/8"))
        self.assertTrue(validateIPV4CIDR("192.168.1.10/32"))
        self.assertTrue(validateIPV4CIDR("172.16.0.0/16"))

        # Invalid inputs (note: bare IP is accepted by IPv4Network as /32)
        self.assertTrue(validateIPV4CIDR("10.0.0.0"))       # bare IP treated as /32
        self.assertFalse(validateIPV4CIDR("192.168.1.1/33"))# invalid prefix
        self.assertFalse(validateIPV4CIDR("abcd"))          # nonsensical

    # -------------------------------
    # Payload validation negative paths
    # -------------------------------
    def test_mExecute_invalid_operation(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {
            "hostnames": ["host1"],
            "cidrs": ["10.0.0.0/8"],
            "operation": "update",   # invalid
            "hosttype": "dom0"
        }
        _handler = ECHostAccessControlHandler(_options)
        self.assertEqual((ECHostAccessControlHandler.FAILURE, {}), _handler.mExecute())

    def test_mExecute_invalid_hosttype(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {
            "hostnames": ["host1"],
            "cidrs": ["10.0.0.0/8"],
            "operation": "add",
            "hosttype": "dom1"       # invalid
        }
        _handler = ECHostAccessControlHandler(_options)
        self.assertEqual((ECHostAccessControlHandler.FAILURE, {}), _handler.mExecute())

    @patch("exabox.jsondispatch.handler_hostaccesscontrol.validateIPV4CIDR", return_value=False)
    @patch("exabox.jsondispatch.handler_hostaccesscontrol.get_gcontext")
    @patch("exabox.jsondispatch.handler_hostaccesscontrol.connect_to_host")
    def test_mExecute_invalid_cidr(self, mock_connect_to_host, mock_get_ctx, mock_validate):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {
            "hostnames": ["host1"],
            "cidrs": ["10.0.0.0"],   # invalid, missing mask
            "operation": "add",
            "hosttype": "dom0"
        }
        # Even if handler validation regresses, ensure no real connection is attempted
        mock_get_ctx.return_value = object()

        _handler = ECHostAccessControlHandler(_options)
        self.assertEqual((ECHostAccessControlHandler.FAILURE, {}), _handler.mExecute())
        mock_connect_to_host.assert_not_called()

    # -------------------------------
    # Positive path: add rules (dom0)
    # -------------------------------
    @patch("exabox.jsondispatch.handler_hostaccesscontrol.get_gcontext")
    @patch("exabox.jsondispatch.handler_hostaccesscontrol.connect_to_host")
    def test_mExecute_add_dom0_success(self, mock_connect_to_host, mock_get_ctx):
        # Build Options with minimal valid payload
        _options = self.mGetContext().mGetArgsOptions()
        _payload = {
            "hostnames": ["host1"],
            "cidrs": ["10.0.0.0/8"],
            "operation": "add",
            "hosttype": "dom0"
        }
        _options.jsonconf = _payload

        # Mock context getter to return a simple object
        mock_get_ctx.return_value = object()

        # Prepare node mock with command status progression:
        # export -> 0, fetch(root) -> 1 (no existing), update(root) -> 0,
        # fetch(secscan) -> 1, update(secscan) -> 0
        node = MagicMock()
        node.mGetHostname.return_value = "host1"
        node.mGetCmdExitStatus.side_effect = [0, 1, 0, 1, 0]
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)

        # Make connect_to_host work as a context manager returning our node
        mock_connect_to_host.return_value.__enter__.return_value = node
        mock_connect_to_host.return_value.__exit__.return_value = False

        _handler = ECHostAccessControlHandler(_options)
        _rc, _resp = _handler.mExecute()

        self.assertEqual(ECHostAccessControlHandler.SUCCESS, _rc)
        # Expect success messages for root and secscan users on host1
        self.assertIn("host1", _resp)
        self.assertIn("10.0.0.0/8", _resp["host1"])
        result = _resp["host1"]["10.0.0.0/8"]
        self.assertEqual(
            result,
            {
                "root": "Successfully added hac rules for root in host1",
                "secscan": "Successfully added hac rules for secscan in host1",
            }
        )

    # -------------------------------
    # Positive path: delete rules (dom0) - nothing configured
    # -------------------------------
    @patch("exabox.jsondispatch.handler_hostaccesscontrol.get_gcontext")
    @patch("exabox.jsondispatch.handler_hostaccesscontrol.connect_to_host")
    def test_mExecute_delete_dom0_noop_success(self, mock_connect_to_host, mock_get_ctx):
        _options = self.mGetContext().mGetArgsOptions()
        _payload = {
            "hostnames": ["host1"],
            "cidrs": ["10.0.0.0/8"],
            "operation": "delete",
            "hosttype": "dom0"
        }
        _options.jsonconf = _payload

        mock_get_ctx.return_value = object()

        # export -> 0, fetch(root) -> 1 (not present), fetch(secscan) -> 1 (not present)
        node = MagicMock()
        node.mGetHostname.return_value = "host1"
        node.mGetCmdExitStatus.side_effect = [0, 1, 1]
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)

        mock_connect_to_host.return_value.__enter__.return_value = node
        mock_connect_to_host.return_value.__exit__.return_value = False

        _handler = ECHostAccessControlHandler(_options)
        _rc, _resp = _handler.mExecute()

        self.assertEqual(ECHostAccessControlHandler.SUCCESS, _rc)
        self.assertIn("host1", _resp)
        res = _resp["host1"]["10.0.0.0/8"]
        self.assertEqual(
            res,
            {
                "root": "HAC rules doesn't exist or current subnet is not configured for user root in host1",
                "secscan": "HAC rules doesn't exist or current subnet is not configured for user secscan in host1",
            }
        )

    # -------------------------------
    # Positive path: delete rules (dom0) - configured, update succeeds
    # -------------------------------
    @patch("exabox.jsondispatch.handler_hostaccesscontrol.get_gcontext")
    @patch("exabox.jsondispatch.handler_hostaccesscontrol.connect_to_host")
    def test_mExecute_delete_dom0_update_success(self, mock_connect_to_host, mock_get_ctx):
        _options = self.mGetContext().mGetArgsOptions()
        _payload = {
            "hostnames": ["host1"],
            "cidrs": ["10.0.0.0/8"],
            "operation": "delete",
            "hosttype": "dom0"
        }
        _options.jsonconf = _payload

        mock_get_ctx.return_value = object()

        # export -> 0,
        # fetch(root) -> 0 (present) -> update -> 0
        # fetch(secscan) -> 0 (present) -> update -> 0
        node = MagicMock()
        node.mGetHostname.return_value = "host1"
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0, 0]
        # Provide realistic rules lines for both users with at least 3 colon-separated fields,
        # including both the target CIDR and another one that should remain.
        root_line = "root: something: 10.1.1.0/24 10.0.0.0/8\n"
        secscan_line = "secscan: something: 10.1.1.0/24 10.0.0.0/8\n"
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO(root_line), None),
            (None, io.StringIO(secscan_line), None),
        ]

        mock_connect_to_host.return_value.__enter__.return_value = node
        mock_connect_to_host.return_value.__exit__.return_value = False

        _handler = ECHostAccessControlHandler(_options)
        _rc, _resp = _handler.mExecute()

        self.assertEqual(ECHostAccessControlHandler.SUCCESS, _rc)
        res = _resp["host1"]["10.0.0.0/8"]
        self.assertEqual(
            res,
            {
                "root": "Successfully deleted hac rules for root in host1",
                "secscan": "Successfully deleted hac rules for secscan in host1",
            }
        )


if __name__ == '__main__':
    unittest.main()