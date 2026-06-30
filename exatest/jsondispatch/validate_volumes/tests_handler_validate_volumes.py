#!/bin/python
#
# $Header: tests_handler_validate_volumes.py 15-apr-2026.18:35:00 joysjose Exp $
#
# tests_handler_validate_volumes.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#

import unittest

from unittest import mock
from unittest.mock import patch

from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_validate_volumes import ValidateVolumesHandler


class ebTestValidateVolumesHandler(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    @staticmethod
    def _ctx_manager(aNode):
        _ctx = mock.MagicMock()
        _ctx.__enter__.return_value = aNode
        _ctx.__exit__.return_value = False
        return _ctx

    def test_001_helpers_build_expected_volume_lists(self):
        _handler = ValidateVolumesHandler(self.mGetContext().mGetArgsOptions())

        _device_output = "\n".join([
            "Device: /dev/exc/volA, State: Attached",
            "Noise line",
            "Device: /dev/exc/volB, State: Attached",
        ])
        self.assertEqual(
            ["/dev/exc/volA", "/dev/exc/volB"],
            _handler.mExtractDevicePath(_device_output),
        )
        self.assertEqual(
            ["/dev/exc/volC"],
            _handler.mCompareDevicePath(
                ["/dev/exc/volA", "/dev/exc/volB"],
                ["/dev/exc/volA", "/dev/exc/volC"],
            ),
        )
        self.assertEqual(
            {
                "volumes": [
                    {"volumename": "/dev/exc/volA", "status": "attached"},
                    {"volumename": "/dev/exc/volC", "status": "unattached"},
                    {"volumename": "/dev/exc/volD", "status": "stale"},
                ]
            },
            _handler.mBuildResponse(
                attached_vols=["/dev/exc/volA"],
                unattached_vols=["/dev/exc/volC"],
                stale_vols=["/dev/exc/volD"],
            ),
        )

    @patch("exabox.jsondispatch.handler_validate_volumes.node_cmd_abs_path_check", return_value="/usr/sbin/edvutil")
    def test_002_mReturnUnattachedStaleVolumelists_splits_devices(self, mockNodeCmdPath):
        _handler = ValidateVolumesHandler(self.mGetContext().mGetArgsOptions())
        _node = mock.MagicMock()
        _node.mExecuteCmd.side_effect = [
            (0, "No such device", ""),
            (0, "Device: /dev/exc/volB, State: Detached", ""),
        ]

        _unattached, _stale = _handler.mReturnUnattachedStaleVolumelists(
            _node,
            ["/dev/exc/volA", "/dev/exc/volB"],
        )

        self.assertEqual(["/dev/exc/volB"], _unattached)
        self.assertEqual(["/dev/exc/volA"], _stale)

    def test_003_mExecute_raises_when_payload_is_missing_required_fields(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {"hostname": "dom0-host"}

        _handler = ValidateVolumesHandler(_options)
        with self.assertRaises(ExacloudRuntimeError):
            _handler.mExecute()

    @patch("exabox.jsondispatch.handler_validate_volumes.exaBoxCluCtrl")
    @patch("exabox.jsondispatch.handler_validate_volumes.get_gcontext", return_value=object())
    @patch("exabox.jsondispatch.handler_validate_volumes.node_cmd_abs_path_check", return_value="/usr/sbin/edvutil")
    @patch("exabox.jsondispatch.handler_validate_volumes.connect_to_host")
    def test_004_mExecute_success_returns_attached_volume_response(self,
        mockConnectToHost,
        mockNodeCmdPath,
        mockGetGcontext,
        mockCluCtrl):

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {
            "hostname": "dom0-host",
            "edvvolume": ["volA", "volB"],
        }

        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (
            0,
            "Device: /dev/exc/volA, State: Attached\nDevice: /dev/exc/volB, State: Attached\n",
            "",
        )
        _node.mGetCmdExitStatus.return_value = 0
        mockConnectToHost.return_value = self._ctx_manager(_node)

        _handler = ValidateVolumesHandler(_options)
        _rc, _response = _handler.mExecute()

        self.assertEqual(ValidateVolumesHandler.SUCCESS, _rc)
        self.assertEqual(
            {
                "volumes": [
                    {"volumename": "/dev/exc/volA", "status": "attached"},
                    {"volumename": "/dev/exc/volB", "status": "attached"},
                ]
            },
            _response,
        )

    @patch("exabox.jsondispatch.handler_validate_volumes.exaBoxCluCtrl")
    @patch("exabox.jsondispatch.handler_validate_volumes.get_gcontext", return_value=object())
    @patch("exabox.jsondispatch.handler_validate_volumes.node_cmd_abs_path_check", return_value="/usr/sbin/edvutil")
    @patch("exabox.jsondispatch.handler_validate_volumes.connect_to_host")
    def test_005_mExecute_raises_when_initial_volume_lookup_fails(self,
        mockConnectToHost,
        mockNodeCmdPath,
        mockGetGcontext,
        mockCluCtrl):

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {
            "hostname": "dom0-host",
            "edvvolume": ["volA", "volB"],
        }

        _node = mock.MagicMock()
        _node.mExecuteCmd.side_effect = [
            (1, "", ""),
            (0, "No such device", ""),
            (0, "Device: /dev/exc/volB, State: Detached", ""),
        ]
        _node.mGetCmdExitStatus.return_value = 1
        mockConnectToHost.return_value = self._ctx_manager(_node)

        _handler = ValidateVolumesHandler(_options)
        with self.assertRaises(ExacloudRuntimeError) as _err:
            _handler.mExecute()

        self.assertIn("validate_volumes operation Failed with _rc status 1", str(_err.exception))


if __name__ == "__main__":
    unittest.main()
