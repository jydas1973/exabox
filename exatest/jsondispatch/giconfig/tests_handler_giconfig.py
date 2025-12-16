#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/giconfig/tests_handler_giconfig.py /main/1 2025/11/18 03:55:10 shapatna Exp $
#
# tests_handler_giconfig.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_handler_giconfig.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    11/11/25 - Enh 38574081: Add unit tests to improve the
#                           coverage using Cline
#    shapatna    11/11/25 - Creation
#

import unittest
from unittest import mock
from unittest.mock import Mock, patch

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_giconfig import GIConfigHandler


class ebTestGIconfig(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    @patch("exabox.jsondispatch.handler_giconfig.exaBoxCluCtrl")
    def test_mExecute_invalid_when_exacc_env(self, aMagicCluCtrl):
        """
        If environment is EXACC (mIsOciEXACC returns True), handler must reject operation.
        """
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {}  # payload not needed for this early return

        # Environment check forces invalid operation
        aMagicCluCtrl.return_value.mIsOciEXACC.return_value = True

        _handler = GIConfigHandler(_options)
        _expected = (GIConfigHandler.ERR_INVALID_OPERATION, {})
        self.assertEqual(_expected, _handler.mExecute())

    @patch("exabox.jsondispatch.handler_giconfig.exaBoxCluCtrl")
    def test_mExecute_invalid_payload_missing_required_key(self, aMagicCluCtrl):
        """
        Payload missing one of the required keys should be rejected by mValidateImageInfoPayload.
        """
        _options = self.mGetContext().mGetArgsOptions()

        # Missing 'version' key on purpose; keep dict non-None to avoid AttributeError paths
        _payload = {
            "system_type": "EXADATA",
            "image_type": "GI",
            "location": "/repo/gi/images",
            "type": "ADD",
        }
        _options.jsonconf = _payload

        # Not EXACC so validation is executed
        aMagicCluCtrl.return_value.mIsOciEXACC.return_value = False

        # Provide repository_root so the first failure encountered is the missing required key
        with patch("exabox.jsondispatch.handler_giconfig.get_gcontext") as aMagicGetCtx:
            _ctx = Mock()
            _ctx.mGetConfigOptions.return_value = {"repository_root": "/repo/root"}
            aMagicGetCtx.return_value = _ctx

            _handler = GIConfigHandler(_options)
            _expected = (GIConfigHandler.ERR_INVALID_OPERATION, {})
            self.assertEqual(_expected, _handler.mExecute())

    @patch("exabox.jsondispatch.handler_giconfig.exaBoxCluCtrl")
    def test_mExecute_invalid_payload_missing_repo_root(self, aMagicCluCtrl):
        """
        If repository_root config is empty/absent, validation must fail.
        """
        _options = self.mGetContext().mGetArgsOptions()

        # Complete required keys; repository_root will be made empty via get_gcontext() mock
        _payload = {
            "system_type": "EXADATA",
            "image_type": "GI",
            "version": "19.21.0.0.0",
            "location": "/repo/gi/images",
            "type": "ADD",
        }
        _options.jsonconf = _payload

        aMagicCluCtrl.return_value.mIsOciEXACC.return_value = False

        with patch("exabox.jsondispatch.handler_giconfig.get_gcontext") as aMagicGetCtx:
            _ctx = Mock()
            # Empty string is treated as missing by the implementation
            _ctx.mGetConfigOptions.return_value = {"repository_root": ""}
            aMagicGetCtx.return_value = _ctx

            _handler = GIConfigHandler(_options)
            _expected = (GIConfigHandler.ERR_INVALID_OPERATION, {})
            self.assertEqual(_expected, _handler.mExecute())

    @patch("exabox.jsondispatch.handler_giconfig.exaBoxCluCtrl")
    def test_mExecute_valid_operation_success(self, aMagicCluCtrl):
        """
        Happy path: valid payload, EXACC check false, ebCluGiRepoUpdate executes successfully.
        Ensure realistic return structures and that the returned response matches mGetGIResponseData.
        """
        _options = self.mGetContext().mGetArgsOptions()

        # Minimal viable payload with all required keys and non-None values
        _payload = {
            "system_type": "EXADATA",
            "image_type": "GI",
            "version": "19.21.0.0.0",
            "location": "/repo/gi/images",
            "type": "ADD",
        }
        _options.jsonconf = _payload

        aMagicCluCtrl.return_value.mIsOciEXACC.return_value = False

        with patch("exabox.jsondispatch.handler_giconfig.get_gcontext") as aMagicGetCtx, \
             patch("exabox.jsondispatch.handler_giconfig.ebCluGiRepoUpdate") as aMagicGiRepo:

            # Context with valid repository_root
            _ctx = Mock()
            _ctx.mGetConfigOptions.return_value = {"repository_root": "/repo/root"}
            aMagicGetCtx.return_value = _ctx

            # Mock GI config manager returned by factory
            _gi_mgr = Mock()
            _gi_mgr.mExecute.return_value = 0
            _gi_mgr.mGetGIResponseData.return_value = {
                "status": "OK",
                "operation": "ADD",
                "details": {"image_type": "GI", "version": "19.21.0.0.0"},
            }
            aMagicGiRepo._from_payload.return_value = _gi_mgr

            _handler = GIConfigHandler(_options)
            _expected = (GIConfigHandler.SUCCESS, _gi_mgr.mGetGIResponseData())
            self.assertEqual(_expected, _handler.mExecute())

            # Validate interactions and payload propagation
            aMagicGiRepo._from_payload.assert_called_once()
            _gi_mgr.mExecute.assert_called_once_with(_payload)
            # mGetGIResponseData is called in both else and finally blocks; at least once is guaranteed
            self.assertTrue(_gi_mgr.mGetGIResponseData.called)


if __name__ == "__main__":
    unittest.main()
