#!/bin/python
#
# $Header: tests_clu_utils.py 18-mar-2026.07:28:43 prsshukl Exp $
#
# tests_clu_utils.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_clu_utils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rajsag      05/29/26 - Bug 39283211 - support X11 no-XRMEM cell types
#    prsshukl    05/22/26 - Bug 39416987 - EXACC: SSL INSPECTION: PHASE1: EXACLOUD ISN'T
#                           COPYING CUSTOMER ROOT CA AS UNABLE TO LOGIN TO THE CPS WALLET
#    aararora    03/20/26 - 39106054: Add Falcon agent install helper
#    prsshukl    03/18/26 - Creation
#

import os
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import CmdRet
import exabox.ovm.utils.clu_utils as clu_utils
from exabox.ovm.utils.clu_utils import ebCluUtils, mRunCrsCommandsWithRetry
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

import base64
import io
import json
import types
from unittest import mock

class DummyExacloudRuntimeError(Exception):
    """Lightweight stand-in so tests can intercept raises without Error.py hooks."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

class ebTestCluUtils(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCluUtils, cls).setUpClass(False, False)

    def setUp(self):
        super().setUp()
        self._utils = ebCluUtils(self.mGetClubox())

    def test_mFindLocalRpm_returns_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rpm_path = os.path.join(tmpdir, "falcon-sensor-7.31.0-18410.el8.x86_64.rpm")
            with open(rpm_path, "w", encoding="utf-8") as rpm_file:
                rpm_file.write("payload")

            result = self._utils.mFindLocalRpm(tmpdir, "8")
            self.assertEqual(result, rpm_path)

    def test_mFindLocalRpm_returns_none_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertIsNone(self._utils.mFindLocalRpm(tmpdir, "8"))

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_happy_path(self):
        utils = self._utils

        mock_cluctrl = utils._ebCluUtils__cluctrl
        mock_node = MagicMock()
        mock_node.mFileExists.side_effect = [False, True]

        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_node
        context_manager.__exit__.return_value = False

        with patch.object(mock_cluctrl, "mIsSslInspectionEnabled", return_value=True) as mock_ssl_enabled, \
             patch.object(mock_cluctrl, "mReturnDom0DomUPair", return_value=[("dom0", "domu1")]), \
             patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
             patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_manager) as mock_connect, \
             patch("exabox.ovm.utils.clu_utils.get_gcontext") as mock_context_getter, \
             patch("exabox.ovm.utils.clu_utils.node_exec_cmd_check") as mock_exec_check:
            utils.mSetupCustomerRootCACertificates()

        mock_ssl_enabled.assert_called_once_with()
        mock_connect.assert_called_once_with("domu1", mock_context_getter.return_value, username="root")
        mock_node.mExecuteCmd.assert_called_once_with("mkdir -p /etc/pki/ca-trust/source/anchors")
        mock_node.mCopyFile.assert_called_once_with(
            "/etc/pki/ca-trust/source/anchors/customer-root-ca.crt",
            "/etc/pki/ca-trust/source/anchors/customer-root-ca.crt",
        )
        mock_exec_check.assert_called_once_with(mock_node, "update-ca-trust")

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_skips_when_not_enabled(self):
        utils = self._utils
        mock_cluctrl = utils._ebCluUtils__cluctrl
        with patch.object(mock_cluctrl, "mIsSslInspectionEnabled", return_value=False) as mock_ssl_enabled, \
             patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
             patch("exabox.ovm.utils.clu_utils.connect_to_host") as mock_connect:
            utils.mSetupCustomerRootCACertificates()

        mock_ssl_enabled.assert_called_once_with()
        mock_connect.assert_not_called()

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_raises_when_source_missing(self):
        utils = self._utils
        mock_cluctrl = utils._ebCluUtils__cluctrl

        with patch.object(mock_cluctrl, "mIsSslInspectionEnabled", return_value=True), \
             patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=False), \
             patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError):
                utils.mSetupCustomerRootCACertificates()

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_raises_when_copy_fails(self):
        utils = self._utils
        mock_cluctrl = utils._ebCluUtils__cluctrl

        with patch.object(mock_cluctrl, "mIsSslInspectionEnabled", return_value=True), \
             patch.object(mock_cluctrl, "mReturnDom0DomUPair", return_value=[("dom0", "domu1")]):
            mock_node = MagicMock()
            mock_node.mFileExists.side_effect = [True, False]

            context_manager = MagicMock()
            context_manager.__enter__.return_value = mock_node
            context_manager.__exit__.return_value = False

            with patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
                 patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_manager), \
                 patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
                 patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
                with self.assertRaises(DummyExacloudRuntimeError):
                    utils.mSetupCustomerRootCACertificates()

    def test_mDownloadFalconRpm_downloads_with_curl(self):
        utils = self._utils
        with tempfile.TemporaryDirectory() as tmpdir:
            rpm_url = "https://objectstorage/falcon-sensor-7.31.0-18410.el8.x86_64.rpm"
            target_path = os.path.join(tmpdir, "falcon-sensor-7.31.0-18410.el8.x86_64.rpm")

            def _exec_local(cmd, aLogOutError=False):
                self.assertIn("--fail --location --show-error", cmd)
                with open(target_path, "w", encoding="utf-8") as rpm_file:
                    rpm_file.write("payload")
                return (0, None, "", "")

            with patch("exabox.ovm.utils.clu_utils.shutil.which", return_value="/usr/bin/curl"), \
                 patch.object(utils._ebCluUtils__cluctrl, "mExecuteLocal", side_effect=_exec_local) as mock_exec:
                result = utils.mDownloadFalconRpm(tmpdir, rpm_url)

            self.assertEqual(result, target_path)
            mock_exec.assert_called_once()

    def test_mDownloadFalconRpm_raises_on_failure(self):
        utils = self._utils
        with tempfile.TemporaryDirectory() as tmpdir:
            rpm_url = "https://objectstorage/falcon-sensor-7.31.0-18410.el8.x86_64.rpm"

            def _exec_local(cmd, aLogOutError=False):
                return (1, None, "", "error downloading")

            with patch("exabox.ovm.utils.clu_utils.shutil.which", return_value="/usr/bin/curl"), \
                 patch.object(utils._ebCluUtils__cluctrl, "mExecuteLocal", side_effect=_exec_local):
                with self.assertRaises(ExacloudRuntimeError):
                    utils.mDownloadFalconRpm(tmpdir, rpm_url)

    # Auto-generated test for mDownloadFalconRpm
    def test_mDownloadFalconRpm_reuses_existing_file(self):
        utils = self._utils
        with tempfile.TemporaryDirectory() as tmpdir:
            rpm_path = os.path.join(tmpdir, "falcon-existing.rpm")
            with open(rpm_path, "wb") as rpm_file:
                rpm_file.write(b"payload")

            with patch.object(utils._ebCluUtils__cluctrl, "mExecuteLocal") as mock_exec:
                result = utils.mDownloadFalconRpm(tmpdir, "https://storage/falcon-existing.rpm")

            self.assertEqual(result, rpm_path)
            mock_exec.assert_not_called()

    def test_mInstallFalconAgentOnDomus_skips_when_disabled(self):
        utils = self._utils

        def _config_side_effect(option, value=None):
            if option == "falcon_agent_install":
                return False if value is not None else "False"
            return None

        with patch.object(self.mGetClubox(), "mCheckConfigOption", side_effect=_config_side_effect), \
             patch.object(utils, "mInstallFalconSensor") as mock_sensor:
            utils.mInstallFalconAgentOnDomus(["domu1"])

        mock_sensor.assert_not_called()

    def test_mInstallFalconAgentOnDomus_invokes_sensor_install(self):
        utils = self._utils

        def _config_side_effect(option, value=None):
            if option == "falcon_agent_install":
                return True if value is not None else "True"
            if option == "falcon_sensor_cid":
                return "CIDVALUE"
            if option == "falcon_sensor_rpm_urls":
                return {"ol8": "https://objectstorage/falcon.rpm", "ol9": "https://objectstorage/falcon9.rpm"}
            return None

        with patch.object(self.mGetClubox(), "mCheckConfigOption", side_effect=_config_side_effect), \
             patch.object(utils, "mInstallFalconSensor") as mock_sensor:
            utils.mInstallFalconAgentOnDomus(["domu1", "domu2"], aOperationLabel="Create Service")

        mock_sensor.assert_has_calls([
            call("domu1", os.path.join(self.mGetClubox().mGetBasePath(), "images"), {"ol8": "https://objectstorage/falcon.rpm", "ol9": "https://objectstorage/falcon9.rpm"}, "CIDVALUE", "Create Service"),
            call("domu2", os.path.join(self.mGetClubox().mGetBasePath(), "images"), {"ol8": "https://objectstorage/falcon.rpm", "ol9": "https://objectstorage/falcon9.rpm"}, "CIDVALUE", "Create Service"),
        ])

    # Auto-generated test for mInstallFalconAgentOnDomus
    def test_mInstallFalconAgentOnDomus_uses_default_cid_and_no_urls(self):
        utils = self._utils

        def _config_side_effect(option, value=None):
            if option == "falcon_agent_install":
                return True if value is not None else "True"
            if option == "falcon_sensor_cid":
                return None
            if option == "falcon_sensor_rpm_urls":
                return None
            return None

        mock_context = mock.Mock()
        mock_context.mGetBasePath.return_value = "/base"

        with patch.object(self.mGetClubox(), "mCheckConfigOption", side_effect=_config_side_effect), \
             patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock_context), \
             patch.object(utils, "mInstallFalconSensor") as mock_sensor:
            utils.mInstallFalconAgentOnDomus(["domu1"])

        mock_sensor.assert_called_once()
        args = mock_sensor.call_args[0]
        self.assertEqual(args[0], "domu1")
        self.assertEqual(args[1], os.path.join("/base", "images"))
        self.assertIsNone(args[2])
        self.assertEqual(args[3], clu_utils.FALCON_DEFAULT_CID)
        self.assertEqual(args[4], "DomU operation")

    # Auto-generated test for mInstallFalconAgentOnDomus
    def test_mInstallFalconAgentOnDomus_raises_when_url_missing_for_version(self):
        utils = self._utils

        def _config_side_effect(option, value=None):
            if option == "falcon_agent_install":
                return True if value is not None else "True"
            if option == "falcon_sensor_cid":
                return "CIDVALUE"
            if option == "falcon_sensor_rpm_urls":
                return {"ol8": "https://objectstorage/falcon.rpm"}
            return None

        mock_context = mock.Mock()
        mock_context.mGetBasePath.return_value = "/base"
        node = MagicMock()
        context_mgr = mock.MagicMock()
        context_mgr.__enter__.return_value = node
        context_mgr.__exit__.return_value = False

        with patch.object(self.mGetClubox(), "mCheckConfigOption", side_effect=_config_side_effect), \
             patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock_context), \
             patch.object(utils, "mDetectOracleLinuxMajor", return_value="9"), \
             patch.object(utils, "mFindLocalRpm", return_value=None), \
             patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_mgr), \
             patch("exabox.ovm.utils.clu_utils.ebLogWarn") as mock_warn, \
             patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                utils.mInstallFalconAgentOnDomus(["domu1"])

        self.assertIn("Falcon RPM for OL9 not found locally", str(exc.exception))
        mock_warn.assert_called_with(f"{clu_utils.FALCON_LOG_PREFIX} RPM URL for OL9 not provided; expecting RPM in images directory.")
        mock_context.mGetBasePath.assert_called_once()

    def test_mConfigureFalconSensor_invokes_expected_commands(self):
        utils = self._utils
        node = MagicMock()
        node.mFileExists.return_value = True

        command_log = []

        def _node_exec_side_effect(_node, cmd, **kwargs):
            command_log.append(cmd)
            if " -g --apd --aph --app" in cmd:
                return CmdRet(0, "apd=true\naph=foo\napp=80\n", "")
            return CmdRet(0, "", "")

        with patch("exabox.ovm.utils.clu_utils.node_exec_cmd", side_effect=_node_exec_side_effect) as mock_exec, \
             patch.object(utils, "mDetectRegionIdentifier", return_value="us-phoenix-1") as mock_region, \
             patch.object(utils, "mRestartFalconService") as mock_restart, \
             patch.object(utils, "mValidateFalconService") as mock_validate:
            utils.mConfigureFalconSensor(node, "domu1", "CIDVALUE")

        mock_region.assert_called_once()
        mock_restart.assert_called_once_with(node, "domu1")
        mock_validate.assert_not_called()
        self.assertTrue(any("falconctl -s -f --cid=CIDVALUE" in cmd for cmd in command_log))
        self.assertTrue(any("falconctl -s --apd=false --aph=prod.csproxy.us-phoenix-1.oci.oraclecloud.com --app=80" in cmd for cmd in command_log))

    def test_mStageLocalRpm_copies_remote_file(self):
        utils = self._utils
        node = MagicMock()
        node.mFileExists.return_value = True

        with tempfile.NamedTemporaryFile("w", delete=False) as tmp_rpm:
            tmp_rpm.write("payload")
            local_rpm = tmp_rpm.name

        try:
            with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", return_value="/bin/rm") as mock_cmd_check, \
                 patch("exabox.ovm.utils.clu_utils.node_exec_cmd") as mock_exec_cmd:
                utils.mStageLocalRpm(node, "domu1", local_rpm, "/tmp/falcon.rpm")
        finally:
            os.unlink(local_rpm)

        mock_cmd_check.assert_called_with(node, "rm")
        mock_exec_cmd.assert_called_once()
        node.mCopyFile.assert_called_once_with(local_rpm, "/tmp")
        node.mFileExists.assert_called_with("/tmp/falcon.rpm")

    def test_mStageLocalRpm_raises_when_copy_missing(self):
        utils = self._utils
        node = MagicMock()
        node.mFileExists.return_value = False

        with tempfile.NamedTemporaryFile("w", delete=False) as tmp_rpm:
            tmp_rpm.write("payload")
            local_rpm = tmp_rpm.name

        try:
            with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", return_value="/bin/rm"), \
                 patch("exabox.ovm.utils.clu_utils.node_exec_cmd"):
                with self.assertRaises(ExacloudRuntimeError):
                    utils.mStageLocalRpm(node, "domu1", local_rpm, "/tmp/falcon.rpm")
        finally:
            os.unlink(local_rpm)

    def test_mStageLocalRpm_raises_for_missing_local_file(self):
        utils = self._utils
        node = MagicMock()
        missing_rpm = "/tmp/does_not_exist.rpm"

        with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check"), \
             patch("exabox.ovm.utils.clu_utils.node_exec_cmd"):
            with self.assertRaises(ExacloudRuntimeError):
                utils.mStageLocalRpm(node, "domu1", missing_rpm, "/tmp/falcon.rpm")

    def test_mIsFalconInstalled_returns_true_when_rpm_present(self):
        utils = self._utils
        node = MagicMock()
        with patch("exabox.ovm.utils.clu_utils.node_exec_cmd", return_value=CmdRet(0, "", "")):
            self.assertTrue(utils.mIsFalconInstalled(node, "domu1"))

    def test_mIsFalconInstalled_returns_false_when_rpm_missing(self):
        utils = self._utils
        node = MagicMock()
        with patch("exabox.ovm.utils.clu_utils.node_exec_cmd", return_value=CmdRet(1, "", "")):
            self.assertFalse(utils.mIsFalconInstalled(node, "domu1"))

    def test_mInstallRpmOnNode_invokes_rpm_install(self):
        utils = self._utils
        node = MagicMock()
        with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", return_value="/bin/rpm"), \
             patch("exabox.ovm.utils.clu_utils.node_exec_cmd") as mock_exec:
            utils.mInstallRpmOnNode(node, "domu1", "/tmp/falcon.rpm")

        mock_exec.assert_called_once()
        invoked_cmd = mock_exec.call_args[0][1]
        self.assertIn("/bin/rpm -ivh /tmp/falcon.rpm", invoked_cmd)

    def test_mDetectOracleLinuxMajor_returns_version(self):
        utils = self._utils
        node = MagicMock()
        with patch("exabox.ovm.utils.clu_utils.node_exec_cmd", return_value=CmdRet(0, "10\n", "")):
            result = utils.mDetectOracleLinuxMajor(node, "domu1")
        self.assertEqual(result, "10")

    def test_mDetectOracleLinuxMajor_raises_on_failure(self):
        utils = self._utils
        node = MagicMock()
        with patch("exabox.ovm.utils.clu_utils.node_exec_cmd", return_value=CmdRet(1, "", "")):
            with self.assertRaises(ExacloudRuntimeError):
                utils.mDetectOracleLinuxMajor(node, "domu1")

    def test_mRestartFalconService_invokes_systemctl(self):
        utils = self._utils
        node = MagicMock()

        with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", return_value="/bin/systemctl"), \
             patch("exabox.ovm.utils.clu_utils.node_exec_cmd") as mock_exec:
            utils.mRestartFalconService(node, "domu1")

        mock_exec.assert_called_once()
        self.assertIn("/bin/systemctl restart falcon-sensor.service", mock_exec.call_args[0][1])

    def test_mValidateFalconService_success(self):
        utils = self._utils
        node = MagicMock()

        def _cmd_path_side_effect(unused_node, binary):
            if binary == "systemctl":
                return "/bin/systemctl"
            if binary == "grep":
                return "/bin/grep"
            return None

        def _exec_side_effect(unused_node, cmd, **kwargs):
            if "status falcon-sensor.service" in cmd:
                return CmdRet(0, "active (running)\n", "")
            if "is-active falcon-sensor.service" in cmd:
                return CmdRet(0, "active\n", "")
            if "CrowdStrike /var/log/messages" in cmd:
                return CmdRet(0, "Connected\n", "")
            raise AssertionError(f"Unexpected command: {cmd}")

        with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", side_effect=_cmd_path_side_effect), \
             patch("exabox.ovm.utils.clu_utils.node_exec_cmd", side_effect=_exec_side_effect):
            utils.mValidateFalconService(node, "domu1")

    def test_mValidateFalconService_raises_when_inactive(self):
        utils = self._utils
        node = MagicMock()

        def _cmd_path_side_effect(unused_node, binary):
            if binary == "systemctl":
                return "/bin/systemctl"
            if binary == "grep":
                return "/bin/grep"
            return None

        def _exec_side_effect(unused_node, cmd, **kwargs):
            if "status falcon-sensor.service" in cmd:
                return CmdRet(0, "inactive\n", "")
            if "is-active falcon-sensor.service" in cmd:
                return CmdRet(0, "inactive\n", "")
            if "CrowdStrike /var/log/messages" in cmd:
                return CmdRet(0, "", "")
            raise AssertionError(f"Unexpected command: {cmd}")

        with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", side_effect=_cmd_path_side_effect), \
             patch("exabox.ovm.utils.clu_utils.node_exec_cmd", side_effect=_exec_side_effect):
            with self.assertRaises(ExacloudRuntimeError):
                utils.mValidateFalconService(node, "domu1")

    # Auto-generated test for mValidateFalconService
    def test_mValidateFalconService_logs_warning_when_connectivity_missing(self):
        utils = self._utils
        node = MagicMock()

        def _cmd_path_side_effect(unused_node, binary):
            if binary == "systemctl":
                return "/bin/systemctl"
            if binary == "grep":
                return "/bin/grep"
            return None

        def _exec_side_effect(unused_node, cmd, **kwargs):
            if "status falcon-sensor.service" in cmd:
                return CmdRet(0, "active\n", "")
            if "is-active falcon-sensor.service" in cmd:
                return CmdRet(0, "active\n", "")
            if "CrowdStrike /var/log/messages" in cmd:
                return CmdRet(1, "", "")
            raise AssertionError(f"Unexpected command: {cmd}")

        with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", side_effect=_cmd_path_side_effect), \
             patch("exabox.ovm.utils.clu_utils.node_exec_cmd", side_effect=_exec_side_effect), \
             patch("exabox.ovm.utils.clu_utils.ebLogWarn") as mock_warn:
            utils.mValidateFalconService(node, "domu1")

        mock_warn.assert_called_once()

    def test_mDetectRegionIdentifier_returns_region(self):
        utils = self._utils
        node = MagicMock()
        with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", return_value="/usr/bin/curl"), \
             patch("exabox.ovm.utils.clu_utils.node_exec_cmd", return_value=CmdRet(0, "us-ashburn-1\n", "")):
            region = utils.mDetectRegionIdentifier(node, "domu1")
        self.assertEqual(region, "us-ashburn-1")

    def test_mDetectRegionIdentifier_returns_none_when_unavailable(self):
        utils = self._utils
        node = MagicMock()
        with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", return_value="/usr/bin/curl"), \
             patch("exabox.ovm.utils.clu_utils.node_exec_cmd", return_value=CmdRet(1, "", "")):
            region = utils.mDetectRegionIdentifier(node, "domu1")
        self.assertIsNone(region)

    def test_mDetectRegionIdentifier_returns_none_when_curl_missing(self):
        utils = self._utils
        node = MagicMock()
        with patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", return_value=None):
            region = utils.mDetectRegionIdentifier(node, "domu1")
        self.assertIsNone(region)

    def test_mExtractFilenameFromUrl_returns_basename(self):
        utils = self._utils
        filename = utils.mExtractFilenameFromUrl("https://host/path/falcon-sensor.rpm?auth=1")
        self.assertEqual(filename, "falcon-sensor.rpm")



class TestSetupCustomerRootCACertificates(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._mock_cluctrl.mIsSslInspectionEnabled = mock.Mock()
        self._mock_cluctrl.mReturnDom0DomUPair = mock.Mock()
        self._utils = ebCluUtils(self._mock_cluctrl)
        self._cert_path = "/etc/pki/ca-trust/source/anchors/customer-root-ca.crt"

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_skip_when_ssl_inspection_disabled(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists") as mock_exists,              mock.patch("exabox.ovm.utils.clu_utils.connect_to_host") as mock_connect:
            self._utils.mSetupCustomerRootCACertificates()

        mock_exists.assert_not_called()
        mock_connect.assert_not_called()
        self._mock_cluctrl.mReturnDom0DomUPair.assert_not_called()

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_raises_when_local_cert_missing(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=False),              mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                self._utils.mSetupCustomerRootCACertificates()

        self.assertIn("customer-root-ca.crt addition failed", str(exc.exception))
        self._mock_cluctrl.mReturnDom0DomUPair.assert_not_called()

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_copies_cert_to_domus(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [(mock.sentinel.dom0, mock.sentinel.domu)]

        mock_node = mock.Mock()
        mock_node.mFileExists.side_effect = [False, True]
        context_mgr = mock.MagicMock()
        context_mgr.__enter__.return_value = mock_node
        context_mgr.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True),              mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_mgr) as mock_connect,              mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx) as mock_get_context,              mock.patch("exabox.ovm.utils.clu_utils.node_exec_cmd_check") as mock_exec_check:
            self._utils.mSetupCustomerRootCACertificates()

        mock_get_context.assert_called_once()
        mock_connect.assert_called_once_with(mock.sentinel.domu, mock.sentinel.ctx, username='root')
        mock_node.mExecuteCmd.assert_called_once_with(f'mkdir -p {os.path.dirname(self._cert_path)}')
        mock_node.mCopyFile.assert_called_once_with(self._cert_path, self._cert_path)
        mock_exec_check.assert_called_once_with(mock_node, "update-ca-trust")

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_logs_directory_creation_when_missing(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [(mock.sentinel.dom0, mock.sentinel.domu)]

        mock_node = mock.Mock()
        mock_node.mFileExists.side_effect = [False, True]
        context_mgr = mock.MagicMock()
        context_mgr.__enter__.return_value = mock_node
        context_mgr.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_mgr), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx), \
             mock.patch("exabox.ovm.utils.clu_utils.ebLogTrace") as mock_log_trace, \
             mock.patch("exabox.ovm.utils.clu_utils.node_exec_cmd_check"):
            self._utils.mSetupCustomerRootCACertificates()

        mock_log_trace.assert_called_once()
        mock_node.mExecuteCmd.assert_called_once_with(f'mkdir -p {os.path.dirname(self._cert_path)}')

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_skips_directory_creation_when_present(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [
            (mock.sentinel.dom0a, mock.sentinel.domua),
            (mock.sentinel.dom0b, mock.sentinel.domub),
        ]

        node_a = mock.Mock()
        node_a.mFileExists.side_effect = [True, True]
        node_b = mock.Mock()
        node_b.mFileExists.side_effect = [True, True]

        ctx_a = mock.MagicMock()
        ctx_a.__enter__.return_value = node_a
        ctx_a.__exit__.return_value = False

        ctx_b = mock.MagicMock()
        ctx_b.__enter__.return_value = node_b
        ctx_b.__exit__.return_value = False

        ctx_iter = iter([ctx_a, ctx_b])

        def _connect_side_effect(*args, **kwargs):
            return next(ctx_iter)

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", side_effect=_connect_side_effect) as mock_connect, \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx), \
             mock.patch("exabox.ovm.utils.clu_utils.node_exec_cmd_check") as mock_exec_check:
            self._utils.mSetupCustomerRootCACertificates()

        self.assertEqual(node_a.mExecuteCmd.call_count, 0)
        self.assertEqual(node_b.mExecuteCmd.call_count, 0)
        self.assertEqual(node_a.mCopyFile.call_args_list, [mock.call(self._cert_path, self._cert_path)])
        self.assertEqual(node_b.mCopyFile.call_args_list, [mock.call(self._cert_path, self._cert_path)])
        self.assertEqual(mock_exec_check.call_count, 2)
        self.assertEqual(mock_connect.call_count, 2)

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_raises_when_remote_copy_missing(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [(mock.sentinel.dom0, mock.sentinel.domu)]

        mock_node = mock.Mock()
        mock_node.mFileExists.side_effect = [True, False]
        context_mgr = mock.MagicMock()
        context_mgr.__enter__.return_value = mock_node
        context_mgr.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True),              mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_mgr),              mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx),              mock.patch("exabox.ovm.utils.clu_utils.node_exec_cmd_check"),              mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError):
                self._utils.mSetupCustomerRootCACertificates()

        mock_node.mCopyFile.assert_called_once_with(self._cert_path, self._cert_path)

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_raises_when_update_ca_trust_fails(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [(mock.sentinel.dom0, mock.sentinel.domu)]

        mock_node = mock.Mock()
        mock_node.mFileExists.side_effect = [False, True]
        context_mgr = mock.MagicMock()
        context_mgr.__enter__.return_value = mock_node
        context_mgr.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_mgr), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx), \
             mock.patch("exabox.ovm.utils.clu_utils.node_exec_cmd_check", side_effect=DummyExacloudRuntimeError("refresh failed")), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                self._utils.mSetupCustomerRootCACertificates()

        self.assertIn("refresh failed", str(exc.exception))
        mock_node.mCopyFile.assert_called_once_with(self._cert_path, self._cert_path)

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_wraps_generic_exception(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [(mock.sentinel.dom0, mock.sentinel.domu)]

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True),              mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", side_effect=RuntimeError("boom")),              mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx),              mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                self._utils.mSetupCustomerRootCACertificates()

        self.assertIn("boom", str(exc.exception))

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_handles_empty_dom_pairs(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = []

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True),              mock.patch("exabox.ovm.utils.clu_utils.connect_to_host") as mock_connect:
            self._utils.mSetupCustomerRootCACertificates()

        mock_connect.assert_not_called()

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_raises_with_real_error_when_local_cert_missing(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=False), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                self._utils.mSetupCustomerRootCACertificates()

        self.assertIn("customer-root-ca.crt addition failed", str(exc.exception))
        self._mock_cluctrl.mReturnDom0DomUPair.assert_not_called()

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_raises_real_error_when_remote_copy_missing(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [(mock.sentinel.dom0, mock.sentinel.domu)]

        mock_node = mock.Mock()
        mock_node.mFileExists.side_effect = [True, False]
        context_mgr = mock.MagicMock()
        context_mgr.__enter__.return_value = mock_node
        context_mgr.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_mgr), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx), \
             mock.patch("exabox.ovm.utils.clu_utils.node_exec_cmd_check"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                self._utils.mSetupCustomerRootCACertificates()

        self.assertIn("customer-root-ca.crt addition failed", str(exc.exception))
        mock_node.mCopyFile.assert_called_once_with(self._cert_path, self._cert_path)

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_invokes_update_ca_trust_successfully(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [(mock.sentinel.dom0, mock.sentinel.domu)]

        mock_node = mock.Mock()
        mock_node.mFileExists.side_effect = [False, True]
        context_mgr = mock.MagicMock()
        context_mgr.__enter__.return_value = mock_node
        context_mgr.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_mgr), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx), \
             mock.patch("exabox.ovm.utils.clu_utils.node_exec_cmd_check") as mock_exec_check:
            self._utils.mSetupCustomerRootCACertificates()

        mock_exec_check.assert_called_once_with(mock_node, "update-ca-trust")

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_wraps_unexpected_exception_real_error(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [(mock.sentinel.dom0, mock.sentinel.domu)]

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", side_effect=RuntimeError("boom")), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                self._utils.mSetupCustomerRootCACertificates()

        self.assertIn("boom", str(exc.exception))

    # Auto-generated test for mSetupCustomerRootCACertificates
    def test_mSetupCustomerRootCACertificates_raises_when_directory_creation_fails(self):
        self._mock_cluctrl.mIsSslInspectionEnabled.return_value = True
        self._mock_cluctrl.mReturnDom0DomUPair.return_value = [(mock.sentinel.dom0, mock.sentinel.domu)]

        mock_node = mock.Mock()
        mock_node.mFileExists.side_effect = [False]
        mock_node.mExecuteCmd.side_effect = RuntimeError("mkdir failed")

        context_mgr = mock.MagicMock()
        context_mgr.__enter__.return_value = mock_node
        context_mgr.__exit__.return_value = False

        dest_directory_path = os.path.dirname(self._cert_path)

        with mock.patch("exabox.ovm.utils.clu_utils.os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=context_mgr), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.ctx), \
             mock.patch("exabox.ovm.utils.clu_utils.ebLogTrace") as mock_log_trace, \
             mock.patch("exabox.ovm.utils.clu_utils.ebLogError") as mock_log_error, \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                self._utils.mSetupCustomerRootCACertificates()

        mock_node.mExecuteCmd.assert_called_once_with(f'mkdir -p {dest_directory_path}')
        mock_log_trace.assert_called_once_with(f"Directory path : {dest_directory_path} does not exist , creating the path")
        mock_log_error.assert_called_once_with('Error while copying customer-root-ca.crt to domU: mkdir failed')
        self.assertIn("mkdir failed", str(exc.exception))


class TestRunCrsCommandsWithRetry(unittest.TestCase):

    def setUp(self):
        self._node = mock.Mock()

    # Auto-generated test for mRunCrsCommandsWithRetry
    def test_mRunCrsCommandsWithRetry_returns_success_on_first_attempt(self):
        stdout = io.StringIO("ok")
        stderr = io.StringIO("")
        self._node.mExecuteCmd.return_value = (None, stdout, stderr)
        self._node.mGetCmdExitStatus.return_value = 0

        result = mRunCrsCommandsWithRetry(self._node, "srvctl status resource")

        self.assertTrue(result)
        self._node.mExecuteCmd.assert_called_once_with("srvctl status resource", None)

    # Auto-generated test for mRunCrsCommandsWithRetry
    def test_mRunCrsCommandsWithRetry_retries_and_returns_false_when_not_raising(self):
        stdout_fail_1 = io.StringIO("")
        stderr_fail_1 = io.StringIO("error1")
        stdout_fail_2 = io.StringIO("")
        stderr_fail_2 = io.StringIO("error2")
        self._node.mExecuteCmd.side_effect = [
            (None, stdout_fail_1, stderr_fail_1),
            (None, stdout_fail_2, stderr_fail_2),
        ]
        self._node.mGetCmdExitStatus.side_effect = [1, 2]

        with mock.patch("exabox.ovm.utils.clu_utils.time.sleep"):
            result = mRunCrsCommandsWithRetry(
                self._node,
                ["cmd primary", "cmd fallback"],
                aAttempts=2,
                aDelay=0,
                aRaiseOnFailure=False,
            )

        self.assertFalse(result)
        self.assertEqual(self._node.mExecuteCmd.call_count, 2)

    # Auto-generated test for mRunCrsCommandsWithRetry
    def test_mRunCrsCommandsWithRetry_handles_none_exit_status(self):
        stdout = io.StringIO("")
        stderr = io.StringIO("failure")
        self._node.mExecuteCmd.return_value = (None, stdout, stderr)
        self._node.mGetCmdExitStatus.return_value = None

        result = mRunCrsCommandsWithRetry(
            self._node,
            "srvctl start svc",
            aAttempts=1,
            aRaiseOnFailure=False,
        )

        self.assertFalse(result)
        self._node.mExecuteCmd.assert_called_once_with("srvctl start svc", None)

    # Auto-generated test for mRunCrsCommandsWithRetry
    def test_mRunCrsCommandsWithRetry_raises_when_attempts_invalid(self):
        with mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError):
                mRunCrsCommandsWithRetry(self._node, [], aAttempts=0)

    # Auto-generated test for mRunCrsCommandsWithRetry
    def test_mRunCrsCommandsWithRetry_raises_after_failed_attempts(self):
        stdout_fail = io.StringIO("")
        stderr_fail = io.StringIO("error")
        self._node.mExecuteCmd.side_effect = [
            (None, stdout_fail, stderr_fail),
            (None, stdout_fail, stderr_fail),
        ]
        self._node.mGetCmdExitStatus.side_effect = [1, 1]

        with mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError), \
             mock.patch("exabox.ovm.utils.clu_utils.time.sleep"):
            with self.assertRaises(DummyExacloudRuntimeError):
                mRunCrsCommandsWithRetry(
                    self._node,
                    ["cmd1", "cmd2"],
                    aAttempts=2,
                    aDelay=0,
                )

    # Auto-generated test for mRunCrsCommandsWithRetry
    def test_mRunCrsCommandsWithRetry_reuses_last_command_on_extra_attempts(self):
        stdout_fail_primary = io.StringIO("")
        stderr_fail_primary = io.StringIO("primary failed")
        stdout_fail_retry = io.StringIO("")
        stderr_fail_retry = io.StringIO("retry failed")
        stdout_success = io.StringIO("ok")
        stderr_success = io.StringIO("")

        self._node.mExecuteCmd.side_effect = [
            (None, stdout_fail_primary, stderr_fail_primary),
            (None, stdout_fail_retry, stderr_fail_retry),
            (None, stdout_success, stderr_success),
        ]
        self._node.mGetCmdExitStatus.side_effect = [1, None, 0]

        with mock.patch("exabox.ovm.utils.clu_utils.time.sleep") as mock_sleep:
            result = mRunCrsCommandsWithRetry(
                self._node,
                ("srvctl stop", "crsctl stop crs -f"),
                aAttempts=3,
                aDelay=7,
            )

        self.assertTrue(result)
        self.assertEqual(self._node.mExecuteCmd.call_count, 3)
        # After exhausting explicit fallbacks, the helper should reuse the last entry.
        self.assertEqual(self._node.mExecuteCmd.call_args_list[2][0][0], "crsctl stop crs -f")
        self.assertEqual(mock_sleep.call_args_list, [mock.call(7), mock.call(7)])

    # Auto-generated test for mRunCrsCommandsWithRetry
    def test_mRunCrsCommandsWithRetry_honors_custom_label_and_timeout(self):
        stdout = io.StringIO("ready")
        stderr = io.StringIO("")
        self._node.mExecuteCmd.return_value = (None, stdout, stderr)
        self._node.mGetCmdExitStatus.return_value = 0

        with mock.patch("exabox.ovm.utils.clu_utils.ebLogInfo") as mock_log:
            result = mRunCrsCommandsWithRetry(
                self._node,
                ["srvctl status res"],
                aLabel="custom label",
                aTimeout=15,
            )

        self.assertTrue(result)
        self._node.mExecuteCmd.assert_called_once_with("srvctl status res", 15)
        logged_messages = " ".join(call_args[0][0] for call_args in mock_log.call_args_list)
        self.assertIn("custom label", logged_messages)

    # Auto-generated test for mRunCrsCommandsWithRetry
    def test_mRunCrsCommandsWithRetry_records_empty_streams_in_error_message(self):
        self._node.mExecuteCmd.return_value = (None, None, None)
        self._node.mGetCmdExitStatus.return_value = 3

        with mock.patch("exabox.ovm.utils.clu_utils.ebLogError") as mock_error:
            result = mRunCrsCommandsWithRetry(
                self._node,
                "srvctl relocate service",
                aAttempts=1,
                aRaiseOnFailure=False,
            )

        self.assertFalse(result)
        self._node.mExecuteCmd.assert_called_once_with("srvctl relocate service", None)
        mock_error.assert_called_once()
        message = mock_error.call_args[0][0]
        self.assertIn("exit status 3", message)
        self.assertIn("stdout: , stderr: ", message)


class TestUpdateRequestObjectData(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._utils = ebCluUtils(self._mock_cluctrl)

    # Auto-generated test for mUpdateRequestObjectData
    def test_mUpdateRequestObjectData_updates_database_when_request_present(self):
        request_obj = mock.Mock()
        self._mock_cluctrl.mGetRequestObj.return_value = request_obj
        db_mock = mock.Mock()

        with mock.patch("exabox.ovm.utils.clu_utils.ebGetDefaultDB", return_value=db_mock):
            self._utils.mUpdateRequestObjectData({"status": "ok"})

        request_obj.mSetData.assert_called_once()
        args, _ = request_obj.mSetData.call_args
        self.assertEqual(json.loads(args[0]), {"status": "ok"})
        db_mock.mUpdateRequest.assert_called_once_with(request_obj)


    # Auto-generated test for mUpdateRequestObjectData
    def test_mUpdateRequestObjectData_logs_when_request_missing(self):
        self._mock_cluctrl.mGetRequestObj.return_value = None

        with mock.patch("exabox.ovm.utils.clu_utils.ebLogInfo") as mock_log:
            self._utils.mUpdateRequestObjectData({"key": "value"})

        mock_log.assert_called_once()
        logged_payload = json.loads(mock_log.call_args[0][0])
        self.assertEqual(logged_payload, {"key": "value"})


class TestCluUtilsHelpers(unittest.TestCase):

    def setUp(self):
        self._utils = ebCluUtils(mock.Mock())

    # Auto-generated test for mIsBase64
    def test_mIsBase64_valid_and_invalid_inputs(self):
        valid = base64.b64encode(b"abc").decode("utf8")
        invalid = "not-base64"

        self.assertTrue(self._utils.mIsBase64(valid))
        self.assertFalse(self._utils.mIsBase64(invalid))

    # Auto-generated test for mExtractNtpDnsPayload
    def test_mExtractNtpDnsPayload_extracts_addresses(self):
        payload = {
            "ntp": [{"ipaddr": "1.2.3.4"}],
            "dns": [{"ipaddr": "5.6.7.8"}, {"no_ip": True}],
        }

        dns, ntp = self._utils.mExtractNtpDnsPayload(payload)

        self.assertEqual(dns, ["5.6.7.8"])
        self.assertEqual(ntp, ["1.2.3.4"])

    # Auto-generated test for mIsNumber
    def test_mIsNumber_checks_numeric_strings(self):
        self.assertTrue(self._utils.mIsNumber("42"))
        self.assertTrue(self._utils.mIsNumber("3.14"))
        self.assertFalse(self._utils.mIsNumber("not-a-number"))

 
class TestSetPropertyValueOeda(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._utils = ebCluUtils(self._mock_cluctrl)

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_returns_when_path_missing(self):
        with mock.patch("os.path.exists", return_value=False), \
             mock.patch("exabox.ovm.utils.clu_utils.ebLogWarn") as mock_warn:
            self._utils.mSetPropertyValueOeda("PROP", "VALUE", "OLD", aPropertiesPath="/tmp/es.properties")

        self._mock_cluctrl.mExecuteLocal.assert_not_called()
        mock_warn.assert_called_once()

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_uses_default_path_when_missing(self):
        self._mock_cluctrl.mGetOedaPath.return_value = "/oeda/root"

        with mock.patch("os.path.exists", return_value=False):
            self._utils.mSetPropertyValueOeda("PROP", "VALUE", "OLD")

        self._mock_cluctrl.mGetOedaPath.assert_called_once()
        self._mock_cluctrl.mExecuteLocal.assert_not_called()

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_skips_add_when_not_allowed(self):
        with mock.patch("os.path.exists", return_value=True):
            self._mock_cluctrl.mExecuteLocal.return_value = (1, None, "out", "err")
            self._utils.mSetPropertyValueOeda(
                "PROP",
                "VALUE",
                "OLD",
                aAddIfNotPresent=False,
                aPropertiesPath="/tmp/es.properties",
            )

        self.assertEqual(self._mock_cluctrl.mExecuteLocal.call_count, 1)

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_appends_property_when_missing(self):
        with mock.patch("os.path.exists", return_value=True):
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (1, None, "out", "err"),
                (0, None, "out", "err"),
                (0, None, "out", "err"),
            ]
            self._utils.mSetPropertyValueOeda("PROP", "VALUE", "OLD", aPropertiesPath="/tmp/es.properties")

        calls = self._mock_cluctrl.mExecuteLocal.call_args_list
        self.assertIn("$a PROP=VALUE", calls[1][0][0])
        self.assertIn("grep -q 'PROP=VALUE'", calls[2][0][0])

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_updates_existing_with_previous_value(self):
        with mock.patch("os.path.exists", return_value=True):
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (0, None, "out", "err"),
                (0, None, "out", "err"),
                (0, None, "out", "err"),
            ]
            self._utils.mSetPropertyValueOeda("PROP", "VALUE", "OLD", aPropertiesPath="/tmp/es.properties")

        update_cmd = self._mock_cluctrl.mExecuteLocal.call_args_list[1][0][0]
        self.assertIn("s/^PROP=OLD/PROP=VALUE/", update_cmd)

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_updates_without_previous_value(self):
        with mock.patch("os.path.exists", return_value=True):
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (0, None, "out", "err"),
                (0, None, "out", "err"),
                (0, None, "out", "err"),
            ]
            self._utils.mSetPropertyValueOeda("PROP", "VALUE", None, aPropertiesPath="/tmp/es.properties")

        update_cmd = self._mock_cluctrl.mExecuteLocal.call_args_list[1][0][0]
        self.assertIn(r"s/\<PROP\>.*$/PROP=VALUE/", update_cmd)

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_logs_error_when_verify_fails(self):
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.ebLogError") as mock_error:
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (0, None, "out", "err"),
                (0, None, "out", "err"),
                (1, None, "out", "err"),
            ]
            self._utils.mSetPropertyValueOeda("PROP", "VALUE", "OLD", aPropertiesPath="/tmp/es.properties")

        mock_error.assert_called_once()

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_logs_error_when_update_fails(self):
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.ebLogError") as mock_error:
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (0, None, "out", "err"),
                (1, None, "out", "err"),
            ]
            self._utils.mSetPropertyValueOeda("PROP", "VALUE", "OLD", aPropertiesPath="/tmp/es.properties")

        mock_error.assert_called_once()
        self.assertEqual(len(self._mock_cluctrl.mExecuteLocal.call_args_list), 2)

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_handles_exception_when_adding(self):
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.ebLogError") as mock_error:
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (1, None, "out", "err"),
                RuntimeError("sed failure"),
            ]
            self._utils.mSetPropertyValueOeda("PROP", "VALUE", "OLD", aPropertiesPath="/tmp/es.properties")

        mock_error.assert_called_once()
        self.assertEqual(len(self._mock_cluctrl.mExecuteLocal.call_args_list), 2)

    # Auto-generated test for mSetPropertyValueOeda
    def test_mSetPropertyValueOeda_uses_default_oeda_path(self):
        self._mock_cluctrl.mGetOedaPath.return_value = "/oeda/root"
        self._mock_cluctrl.mExecuteLocal.side_effect = [
            (0, None, "out", "err"),
            (0, None, "out", "err"),
            (0, None, "out", "err"),
        ]

        with mock.patch("os.path.exists", return_value=True):
            self._utils.mSetPropertyValueOeda("PROP", "VALUE", "OLD")

        self._mock_cluctrl.mGetOedaPath.assert_called_once()
        commands = [call[0][0] for call in self._mock_cluctrl.mExecuteLocal.call_args_list]
        for command in commands:
            self.assertIn("/oeda/root/properties/es.properties", command)


class TestAppendPropertyValueOeda(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._utils = ebCluUtils(self._mock_cluctrl)

    # Auto-generated test for mAppendPropertyValueOeda
    def test_mAppendPropertyValueOeda_returns_when_path_missing(self):
        with mock.patch("os.path.exists", return_value=False):
            self._utils.mAppendPropertyValueOeda("PROP", "VALUE", aPropertiesPath="/tmp/missing")

        self._mock_cluctrl.mExecuteLocal.assert_not_called()

    # Auto-generated test for mAppendPropertyValueOeda
    def test_mAppendPropertyValueOeda_uses_default_path_when_directory_missing(self):
        self._mock_cluctrl.mGetOedaPath.return_value = "/oeda/root"

        with mock.patch("os.path.exists", return_value=False):
            self._utils.mAppendPropertyValueOeda("PROP", "VALUE")

        self._mock_cluctrl.mGetOedaPath.assert_called_once()
        self._mock_cluctrl.mExecuteLocal.assert_not_called()

    # Auto-generated test for mAppendPropertyValueOeda
    def test_mAppendPropertyValueOeda_sets_property_when_missing(self):
        with mock.patch("os.path.exists", return_value=True):
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (1, None, None, None),
                (0, None, None, None),
            ]

            self._utils.mAppendPropertyValueOeda("PROP", "VALUE", aPropertiesPath="/tmp/es.properties")

        self.assertEqual(self._mock_cluctrl.mExecuteLocal.call_count, 2)
        append_cmd = self._mock_cluctrl.mExecuteLocal.call_args_list[1][0][0]
        self.assertIn("sed -i '$a PROP=VALUE'", append_cmd)

    # Auto-generated test for mAppendPropertyValueOeda
    def test_mAppendPropertyValueOeda_skips_when_value_already_present(self):
        with mock.patch("os.path.exists", return_value=True):
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (0, None, None, None),
            ]
            self._mock_cluctrl.mGetOedaProperty.return_value = "VALUE,OTHER"

            self._utils.mAppendPropertyValueOeda("PROP", "VALUE", aPropertiesPath="/tmp/es.properties")

        self.assertEqual(self._mock_cluctrl.mExecuteLocal.call_count, 1)

    # Auto-generated test for mAppendPropertyValueOeda
    def test_mAppendPropertyValueOeda_appends_new_value(self):
        with mock.patch("os.path.exists", return_value=True):
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (0, None, None, None),
                (0, None, None, None),
            ]
            self._mock_cluctrl.mGetOedaProperty.return_value = "OTHER"

            self._utils.mAppendPropertyValueOeda("PROP", "VALUE", aPropertiesPath="/tmp/es.properties")

        self.assertEqual(self._mock_cluctrl.mExecuteLocal.call_count, 2)
        append_cmd = self._mock_cluctrl.mExecuteLocal.call_args_list[1][0][0]
        self.assertIn("VALUE", append_cmd)

    # Auto-generated test for mAppendPropertyValueOeda
    def test_mAppendPropertyValueOeda_logs_error_when_append_command_raises(self):
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.ebLogError") as mock_error:
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (0, None, None, None),
                RuntimeError("sed failure"),
            ]
            self._mock_cluctrl.mGetOedaProperty.return_value = "OTHER"

            self._utils.mAppendPropertyValueOeda("PROP", "VALUE", aPropertiesPath="/tmp/es.properties")

        self.assertEqual(self._mock_cluctrl.mExecuteLocal.call_count, 2)
        mock_error.assert_called_once()

    # Auto-generated test for mAppendPropertyValueOeda
    def test_mAppendPropertyValueOeda_logs_error_when_initial_append_fails(self):
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch("exabox.ovm.utils.clu_utils.ebLogError") as mock_error:
            self._mock_cluctrl.mExecuteLocal.side_effect = [
                (1, None, None, None),
                RuntimeError("sed failure"),
            ]

            self._utils.mAppendPropertyValueOeda("PROP", "VALUE", aPropertiesPath="/tmp/es.properties")

        self.assertEqual(self._mock_cluctrl.mExecuteLocal.call_count, 2)
        mock_error.assert_called_once()

    # Auto-generated test for mAppendPropertyValueOeda
    def test_mAppendPropertyValueOeda_uses_default_oeda_path(self):
        self._mock_cluctrl.mGetOedaPath.return_value = "/oeda/root"
        self._mock_cluctrl.mGetOedaProperty.return_value = ""
        self._mock_cluctrl.mExecuteLocal.side_effect = [
            (0, None, None, None),
            (0, None, None, None),
        ]

        with mock.patch("os.path.exists", return_value=True):
            self._utils.mAppendPropertyValueOeda("PROP", "VALUE")

        self._mock_cluctrl.mGetOedaPath.assert_called_once()
        commands = [call[0][0] for call in self._mock_cluctrl.mExecuteLocal.call_args_list]
        for command in commands:
            self.assertIn("/oeda/root/properties/es.properties", command)


class TestUpdateGlobalEsProperties(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._mock_cluctrl.mGetBasePath.return_value = "/tmp/base"
        self._utils = ebCluUtils(self._mock_cluctrl)

    def test_mUpdateGlobalEsProperties_appends_noxrmem_from_added_cells(self):
        self._mock_cluctrl.mCheckConfigOption.return_value = "True"
        self._mock_cluctrl.mGetArgsOptions.return_value = types.SimpleNamespace(jsonconf={
            "reshaped_node_subset": {
                "added_cells": [
                    {
                        "cell_hostname": "cell01",
                        "model": "X11-HC",
                        "rack_info": {"description": "Exadata X11-HC Cell Node 22TB"}
                    },
                    {
                        "cell_hostname": "cell02",
                        "model": "X11-EF",
                        "rack_info": {"description": "Exadata X11-EF Cell Node 36TB"}
                    }
                ]
            }
        })
        with mock.patch("exabox.ovm.utils.clu_utils.ebCellCliUtils.mValidateX11NoXrmemMemory") as mock_validate, \
             mock.patch.object(self._utils, "mSetPropertyValueOeda") as mock_set, \
             mock.patch.object(self._utils, "mAppendPropertyValueOeda") as mock_append:
            mock_validate.return_value = True
            self._utils.mUpdateGlobalEsProperties()

        mock_set.assert_called_once()
        self.assertEqual(mock_append.call_count, 2)
        append_values = {call_args[0][0]: call_args[0][1] for call_args in mock_append.call_args_list}
        self.assertIn("CELLTYPES", append_values)
        self.assertIn("HC_CELL_TYPES", append_values)
        self.assertIn("X11MHCXRMEM:X11_XRMEM_ROCE_CELL_XC", append_values["CELLTYPES"])
        self.assertIn("X11MHCNOXRMEM:X11_NOXRMEM_ROCE_CELL_XC", append_values["CELLTYPES"])
        self.assertIn("X11MEFNOXRMEM:X11_NOXRMEM_ROCE_CELL_EF", append_values["CELLTYPES"])
        self.assertIn("X11MHCNOXRMEM:X11_NOXRMEM_ROCE_CELL_XC", append_values["HC_CELL_TYPES"])
        mock_validate.assert_has_calls([call("cell01"), call("cell02")])
        self.assertNotIn(call("append_celltypes_x11_noxrmem"),
                         self._mock_cluctrl.mCheckConfigOption.call_args_list)

    def test_mUpdateGlobalEsProperties_skips_hc_append_for_ef_noxrmem(self):
        self._mock_cluctrl.mCheckConfigOption.return_value = None
        self._mock_cluctrl.mGetArgsOptions.return_value = types.SimpleNamespace(jsonconf={
            "reshaped_node_subset": {
                "added_cells": [
                    {
                        "cell_hostname": "cell01",
                        "model": "X11-EF",
                        "rack_info": {"description": "Exadata X11-EF Cell Node 36TB"}
                    }
                ]
            }
        })
        with mock.patch("exabox.ovm.utils.clu_utils.ebCellCliUtils.mValidateX11NoXrmemMemory",
                        return_value=True), \
             mock.patch.object(self._utils, "mSetPropertyValueOeda") as mock_set, \
             mock.patch.object(self._utils, "mAppendPropertyValueOeda") as mock_append:
            self._utils.mUpdateGlobalEsProperties()

        mock_set.assert_called_once()
        self.assertEqual(mock_append.call_count, 1)
        append_values = {call_args[0][0]: call_args[0][1] for call_args in mock_append.call_args_list}
        self.assertIn("CELLTYPES", append_values)
        self.assertNotIn("HC_CELL_TYPES", append_values)
        self.assertIn("X11MEFNOXRMEM:X11_NOXRMEM_ROCE_CELL_EF", append_values["CELLTYPES"])

    # Auto-generated test for mUpdateGlobalEsProperties
    def test_mUpdateGlobalEsProperties_skips_append_when_option_disabled(self):
        self._mock_cluctrl.mCheckConfigOption.return_value = None
        self._mock_cluctrl.mGetArgsOptions.return_value = types.SimpleNamespace(jsonconf={})
        self._mock_cluctrl.mReturnCellNodes.return_value = {}
        with mock.patch.object(self._utils, "mSetPropertyValueOeda") as mock_set, \
             mock.patch.object(self._utils, "mAppendPropertyValueOeda") as mock_append:
            self._utils.mUpdateGlobalEsProperties()

        mock_set.assert_called_once()
        mock_append.assert_not_called()


class TestStepSpecificDetails(unittest.TestCase):

    def setUp(self):
        self._utils = ebCluUtils(mock.Mock())

    # Auto-generated test for mStepSpecificDetails
    def test_mStepSpecificDetails_handles_service_flows(self):
        payload = self._utils.mStepSpecificDetails(
            "createServiceDetails",
            "IN_PROGRESS",
            "Working",
            aStepName="Step1",
        )

        self.assertEqual(payload["createServiceDetails"]["stepName"], "Step1")
        self.assertNotIn("resource", payload["createServiceDetails"])

    # Auto-generated test for mStepSpecificDetails
    def test_mStepSpecificDetails_handles_generic_flows(self):
        payload = self._utils.mStepSpecificDetails(
            "otherTask",
            "DONE",
            "All good",
            aResource="dom0",
        )

        self.assertEqual(payload["otherTask"]["resource"], "dom0")
        self.assertNotIn("stepName", payload["otherTask"])


class TestUpdateTaskProgressStatus(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._utils = ebCluUtils(self._mock_cluctrl)

    # Auto-generated test for mUpdateTaskProgressStatus
    def test_mUpdateTaskProgressStatus_forwards_payload(self):
        with mock.patch.object(self._utils, "mUpdateRequestObjectData") as mock_update:
            self._utils.mUpdateTaskProgressStatus(
                aNodeCompleted=2,
                aPercentComplete=50,
                aCmdName="Rebalance",
                aStatus="RUNNING",
                aStepSpecificDetails={"details": "info"},
                aData={"extra": True},
            )

        mock_update.assert_called_once()
        payload = mock_update.call_args[0][0]
        self.assertEqual(payload["stepProgressDetails"]["completedNodes"], 2)
        self.assertTrue(payload["extra"])

    # Auto-generated test for mUpdateTaskProgressStatus
    def test_mUpdateTaskProgressStatus_handles_missing_optional_data(self):
        with mock.patch.object(self._utils, "mUpdateRequestObjectData") as mock_update:
            self._utils.mUpdateTaskProgressStatus(
                aNodeCompleted=0,
                aPercentComplete=100,
                aCmdName="Done",
                aStatus="SUCCESS",
                aStepSpecificDetails={"details": "final"},
            )

        payload = mock_update.call_args[0][0]
        self.assertEqual(payload["stepProgressDetails"]["percent_complete"], 100)
        self.assertNotIn("extra", payload)


class TestIsAllowedFlowDownInterfaces(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._utils = ebCluUtils(self._mock_cluctrl)

    # Auto-generated test for mIsAllowedFlowDownInterfaces
    def test_mIsAllowedFlowDownInterfaces_populates_healthcheck_errors(self):
        self._mock_cluctrl.mGetCmd.return_value = "deleteservice"
        self._mock_cluctrl.mSetNetDetectError = mock.Mock()

        with mock.patch("exabox.ovm.utils.clu_utils.mCompareModel", return_value=-1):
            result = self._utils.mIsAllowedFlowDownInterfaces(
                aNode=mock.Mock(),
                aMissingLink=["eth0"],
                aSingleDom0="dom0-1",
                aExadataModel="X8",
                aCause="cause",
                aAction="action",
            )

        self.assertTrue(result)
        self._mock_cluctrl.mSetNetDetectError.assert_called_once()
        error_payload = self._mock_cluctrl.mSetNetDetectError.call_args[0][1]
        self.assertEqual(error_payload["INTERFACE_DETAILS"]["OPERATIONAL_STATE"]["DOWN"], ["eth0"])

    # Auto-generated test for mIsAllowedFlowDownInterfaces
    def test_mIsAllowedFlowDownInterfaces_merges_drnet_errors(self):
        self._mock_cluctrl.mGetCmd.return_value = "checkcluster"
        self._mock_cluctrl.mGetNetDetectError.return_value = {
            "dom0-1": {
                "CAUSE": "existing cause",
                "ACTION": "existing action",
                "INTERFACE_DETAILS": {
                    "OPERATIONAL_STATE": {"DOWN": ["eth5"]},
                    "INTERFACE_TYPES": {"UNKNOWN": ["eth5"]},
                },
            }
        }

        with mock.patch("exabox.ovm.utils.clu_utils.mCompareModel", return_value=1):
            result = self._utils.mIsAllowedFlowDownInterfaces(
                aNode=mock.Mock(),
                aMissingLink=["eth1"],
                aSingleDom0="dom0-1",
                aExadataModel="X9",
                aDRNet=True,
            )

        self.assertTrue(result)
        self._mock_cluctrl.mSetNetDetectError.assert_called_once()
        merged = self._mock_cluctrl.mSetNetDetectError.call_args[0][1]
        self.assertIn("eth1", merged["INTERFACE_DETAILS"]["OPERATIONAL_STATE"]["DOWN"])

    # Auto-generated test for mIsAllowedFlowDownInterfaces
    def test_mIsAllowedFlowDownInterfaces_creates_drnet_error_payload_when_missing(self):
        self._mock_cluctrl.mGetCmd.return_value = "checkcluster"
        self._mock_cluctrl.mGetNetDetectError.return_value = None

        with mock.patch("exabox.ovm.utils.clu_utils.mCompareModel", return_value=1):
            result = self._utils.mIsAllowedFlowDownInterfaces(
                aNode=mock.Mock(),
                aMissingLink=["eth2"],
                aSingleDom0="dom0-2",
                aExadataModel="X10",
                aDRNet=True,
            )

        self.assertTrue(result)
        self._mock_cluctrl.mSetNetDetectError.assert_called_once()
        payload = self._mock_cluctrl.mSetNetDetectError.call_args[0][1]
        self.assertIn("eth2", payload["INTERFACE_DETAILS"]["OPERATIONAL_STATE"]["DOWN"])
        self.assertIn("Bring the faulty interface", payload["ACTION"])

    # Auto-generated test for mIsAllowedFlowDownInterfaces
    def test_mIsAllowedFlowDownInterfaces_prefers_explicit_cause_action_without_existing_errors(self):
        self._mock_cluctrl.mGetCmd.return_value = "checkcluster"
        self._mock_cluctrl.mGetNetDetectError.return_value = None
        self._mock_cluctrl.mSetNetDetectError = mock.Mock()

        with mock.patch("exabox.ovm.utils.clu_utils.mCompareModel", return_value=1):
            allowed = self._utils.mIsAllowedFlowDownInterfaces(
                aNode=mock.Mock(),
                aMissingLink=["eth0"],
                aSingleDom0="dom0-1",
                aExadataModel="X9",
                aCause="explicit cause",
                aAction="explicit action",
                aDRNet=True,
            )

        self.assertTrue(allowed)
        payload = self._mock_cluctrl.mSetNetDetectError.call_args[0][1]
        self.assertEqual(payload["CAUSE"], "explicit cause")
        self.assertEqual(payload["ACTION"], "explicit action")

    # Auto-generated test for mIsAllowedFlowDownInterfaces
    def test_mIsAllowedFlowDownInterfaces_allows_custom_healthcheck_profiles(self):
        self._mock_cluctrl.mGetCmd.return_value = "some_other_flow"
        custom_options = types.SimpleNamespace(
            healthcheck="custom",
            jsonconf={"profile_type": "custnet_validate"},
        )
        self._mock_cluctrl.mGetArgsOptions.return_value = custom_options
        self._mock_cluctrl.mSetNetDetectError = mock.Mock()
        node = mock.Mock()
        node.mGetHostname.return_value = "dom0-3"

        with mock.patch("exabox.ovm.utils.clu_utils.mCompareModel", return_value=-1):
            allowed = self._utils.mIsAllowedFlowDownInterfaces(
                node,
                ["eth3"],
                "dom0-3",
                "X8",
            )

        self.assertTrue(allowed)
        error_payload = self._mock_cluctrl.mSetNetDetectError.call_args[0][1]
        self.assertEqual(error_payload["INTERFACE_DETAILS"]["INTERFACE_TYPES"]["UNKNOWN"], ["eth3"])
        self.assertIn("Faulty interface found", error_payload["CAUSE"])

    # Auto-generated test for mIsAllowedFlowDownInterfaces
    def test_mIsAllowedFlowDownInterfaces_returns_false_for_disallowed_flow(self):
        self._mock_cluctrl.mGetCmd.return_value = "other"
        opts = types.SimpleNamespace(healthcheck="normal", jsonconf={})
        self._mock_cluctrl.mGetArgsOptions.return_value = opts

        result = self._utils.mIsAllowedFlowDownInterfaces(
            aNode=mock.Mock(),
            aMissingLink=["eth9"],
            aSingleDom0="dom0-1",
            aExadataModel="X9",
        )

        self.assertFalse(result)
        self._mock_cluctrl.mSetNetDetectError.assert_not_called()

    # Auto-generated test for mIsAllowedFlowDownInterfaces
    def test_mIsAllowedFlowDownInterfaces_uses_provided_cause_action_for_drnet(self):
        node = mock.Mock()
        node.mGetHostname.return_value = "dom0-1"
        self._mock_cluctrl.mGetCmd.return_value = "checkcluster"
        self._mock_cluctrl.mGetNetDetectError.return_value = {
            "dom0-1": {
                "CAUSE": "existing cause ",
                "ACTION": "existing action ",
                "INTERFACE_DETAILS": {
                    "OPERATIONAL_STATE": {"DOWN": ["eth9"]},
                    "INTERFACE_TYPES": {"UNKNOWN": ["eth9"]},
                },
            }
        }
        self._mock_cluctrl.mSetNetDetectError = mock.Mock()

        with mock.patch("exabox.ovm.utils.clu_utils.mCompareModel", return_value=0):
            allowed = self._utils.mIsAllowedFlowDownInterfaces(
                node,
                ["eth10"],
                "dom0-1",
                "X9",
                aCause="explicit cause",
                aAction="explicit action",
                aDRNet=True,
            )

        self.assertTrue(allowed)
        merged = self._mock_cluctrl.mSetNetDetectError.call_args[0][1]
        self.assertIn("explicit cause", merged["CAUSE"])
        self.assertIn("explicit action", merged["ACTION"])
        self.assertNotIn("Faulty interface found", merged["CAUSE"])
        self.assertNotIn("Bring the faulty interface", merged["ACTION"])


class TestGetNotUpDbsList(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._utils = ebCluUtils(self._mock_cluctrl)

    # Auto-generated test for getNotUpDbsList
    def test_getNotUpDbsList_returns_empty_when_no_configured_dbs(self):
        db_instance = mock.Mock()
        db_instance.mGetDBListByNode.return_value = ""

        with mock.patch("exabox.ovm.utils.clu_utils.ebGetDefaultDB", return_value=db_instance):
            result = self._utils.getNotUpDbsList("domu-1")

        self.assertEqual(result, [])

    # Auto-generated test for getNotUpDbsList
    def test_getNotUpDbsList_detects_missing_databases(self):
        db_instance = mock.Mock()
        db_instance.mGetDBListByNode.return_value = "DB1 DB2 DB3"
        self._mock_cluctrl.mGetActiveDbInstances.return_value = ["DB1", "DB3"]

        with mock.patch("exabox.ovm.utils.clu_utils.ebGetDefaultDB", return_value=db_instance):
            result = self._utils.getNotUpDbsList("domu-1")

        self.assertEqual(sorted(result), ["DB2"])


class TestValidateSharedMemSettings(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._utils = ebCluUtils(self._mock_cluctrl)

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_for_non_numeric_ratio(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "invalid"

        with mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError), \
             mock.patch("exabox.ovm.utils.clu_utils.connect_to_host") as mock_connect:
            with self.assertRaises(DummyExacloudRuntimeError):
                self._utils.mValidateSharedMemSettings("domu-1")

        mock_connect.assert_not_called()

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_for_non_positive_ratio(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0"

        with mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError):
                self._utils.mValidateSharedMemSettings("domu-1")

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_sysctl_fails(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.return_value = (None, io.StringIO(""), io.StringIO("err"))
        mock_node.mGetCmdExitStatus.return_value = 1
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError), \
             mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"):
            with self.assertRaises(DummyExacloudRuntimeError):
                self._utils.mValidateSharedMemSettings("domu-1")

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_success_path(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("2147483648\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: 4194304 kB\n"), io.StringIO("")),
            (None, io.StringIO("4096\n"), io.StringIO("")),
            (None, io.StringIO("524288\n"), io.StringIO("")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"):
            self._utils.mValidateSharedMemSettings("domu-1")

        self.assertEqual(mock_node.mExecuteCmd.call_count, 4)

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_shmall_mismatch(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("2147483648\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: 4194304 kB\n"), io.StringIO("")),
            (None, io.StringIO("4096\n"), io.StringIO("")),
            (None, io.StringIO("12345\n"), io.StringIO("")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("does not match expected value", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_shmmax_below_ratio(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.8"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("1000\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: 4096 kB\n"), io.StringIO("")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("kernel.shmmax", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_defaults_ratio_before_small_shmmax_error(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = None
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("1000\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: 4096 kB\n"), io.StringIO("")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("kernel.shmmax", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_meminfo_command_fails(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("1048576\n"), io.StringIO("")),
            (None, io.StringIO(""), io.StringIO("grep failure")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 1]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("Failed to read total memory", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_meminfo_entry_invalid(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("1048576\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: not_a_number kB\n"), io.StringIO("")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("Invalid MemTotal entry", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_getconf_fails(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("2147483648\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: 4194304 kB\n"), io.StringIO("")),
            (None, io.StringIO(""), io.StringIO("getconf failure")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0, 1]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("Failed to read PAGE_SIZE", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_getconf_returns_invalid_value(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("2147483648\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: 4194304 kB\n"), io.StringIO("")),
            (None, io.StringIO("not-an-int\n"), io.StringIO("")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0, 0]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("Invalid PAGE_SIZE value", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_shmall_command_fails(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("2147483648\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: 4194304 kB\n"), io.StringIO("")),
            (None, io.StringIO("4096\n"), io.StringIO("")),
            (None, io.StringIO(""), io.StringIO("shmall failure")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0, 0, 1]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("Failed to read kernel.shmall", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_shmall_value_invalid(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("2147483648\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: 4194304 kB\n"), io.StringIO("")),
            (None, io.StringIO("4096\n"), io.StringIO("")),
            (None, io.StringIO("not-int\n"), io.StringIO("")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("Invalid kernel.shmall runtime value", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_raises_when_shmmax_value_invalid(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = "0.5"
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.return_value = (None, io.StringIO("not-a-number\n"), io.StringIO(""))
        mock_node.mGetCmdExitStatus.return_value = 0
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as context:
                self._utils.mValidateSharedMemSettings("domu-1")

        self.assertIn("Invalid kernel.shmmax runtime value", str(context.exception))

    # Auto-generated test for mValidateSharedMemSettings
    def test_mValidateSharedMemSettings_uses_default_ratio_when_missing(self):
        self._mock_cluctrl.mCheckSubConfigOption.return_value = None
        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("4294967296\n"), io.StringIO("")),
            (None, io.StringIO("MemTotal: 4194304 kB\n"), io.StringIO("")),
            (None, io.StringIO("4096\n"), io.StringIO("")),
            (None, io.StringIO("1048576\n"), io.StringIO("")),
        ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]
        mock_cm = mock.MagicMock()
        mock_cm.__enter__.return_value = mock_node
        mock_cm.__exit__.return_value = False

        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=mock_cm), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext"):
            self._utils.mValidateSharedMemSettings("domu-1")

        self.assertEqual(mock_node.mExecuteCmd.call_count, 4)
        self._mock_cluctrl.mCheckSubConfigOption.assert_called_once_with("reshape_memory", "shmmax_ratio")

class TestInstallFalconSensor(unittest.TestCase):

    def setUp(self):
        self._mock_cluctrl = mock.Mock()
        self._utils = ebCluUtils(self._mock_cluctrl)
        self._node = mock.Mock()
        self._context_manager = mock.MagicMock()
        self._context_manager.__enter__.return_value = self._node
        self._context_manager.__exit__.return_value = False

    # Auto-generated test for mInstallFalconSensor
    def test_mInstallFalconSensor_installs_when_local_rpm_available(self):
        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=self._context_manager), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.gctx), \
             mock.patch.object(self._utils, "mDetectOracleLinuxMajor", return_value="8"), \
             mock.patch.object(self._utils, "mFindLocalRpm", return_value="/images/falcon.rpm"), \
             mock.patch.object(self._utils, "mDownloadFalconRpm") as mock_download, \
             mock.patch.object(self._utils, "mStageLocalRpm") as mock_stage, \
             mock.patch.object(self._utils, "mIsFalconInstalled", return_value=False), \
             mock.patch.object(self._utils, "mInstallRpmOnNode") as mock_install, \
             mock.patch.object(self._utils, "mConfigureFalconSensor") as mock_configure, \
             mock.patch.object(self._utils, "mValidateFalconService") as mock_validate, \
             mock.patch.object(self._utils, "mRemoveRemoteFile") as mock_remove:
            self._utils.mInstallFalconSensor(
                "domu-1",
                "/images",
                {"ol8": "https://example/falcon.rpm"},
                "CID123",
                "Create Service",
            )

        mock_download.assert_not_called()
        mock_stage.assert_called_once_with(self._node, "domu-1", "/images/falcon.rpm", os.path.join("/tmp", "falcon.rpm"))
        mock_install.assert_called_once_with(self._node, "domu-1", os.path.join("/tmp", "falcon.rpm"))
        mock_configure.assert_called_once_with(self._node, "domu-1", "CID123")
        mock_validate.assert_called_once_with(self._node, "domu-1")
        mock_remove.assert_called_once_with(self._node, "domu-1", os.path.join("/tmp", "falcon.rpm"))

    # Auto-generated test for mInstallFalconSensor
    def test_mInstallFalconSensor_skips_rpm_install_when_already_present(self):
        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=self._context_manager), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.gctx), \
             mock.patch.object(self._utils, "mDetectOracleLinuxMajor", return_value="8"), \
             mock.patch.object(self._utils, "mFindLocalRpm", return_value="/images/falcon.rpm"), \
             mock.patch.object(self._utils, "mStageLocalRpm") as mock_stage, \
             mock.patch.object(self._utils, "mIsFalconInstalled", return_value=True), \
             mock.patch.object(self._utils, "mInstallRpmOnNode") as mock_install, \
             mock.patch.object(self._utils, "mConfigureFalconSensor") as mock_configure, \
             mock.patch.object(self._utils, "mValidateFalconService") as mock_validate, \
             mock.patch.object(self._utils, "mRemoveRemoteFile") as mock_remove:
            self._utils.mInstallFalconSensor(
                "domu-2",
                "/images",
                {"ol8": "https://example/falcon.rpm"},
                "CID999",
                "Add Compute",
            )

        mock_stage.assert_called_once()
        mock_install.assert_not_called()
        mock_configure.assert_called_once_with(self._node, "domu-2", "CID999")
        mock_validate.assert_called_once_with(self._node, "domu-2")
        mock_remove.assert_called_once_with(self._node, "domu-2", os.path.join("/tmp", "falcon.rpm"))

    # Auto-generated test for mInstallFalconSensor
    def test_mInstallFalconSensor_downloads_when_local_missing(self):
        downloaded_path = "/images/downloaded/falcon.rpm"
        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=self._context_manager), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.gctx), \
             mock.patch.object(self._utils, "mDetectOracleLinuxMajor", return_value="8"), \
             mock.patch.object(self._utils, "mFindLocalRpm", return_value=None), \
             mock.patch.object(self._utils, "mDownloadFalconRpm", return_value=downloaded_path) as mock_download, \
             mock.patch.object(self._utils, "mStageLocalRpm") as mock_stage, \
             mock.patch.object(self._utils, "mIsFalconInstalled", return_value=False), \
             mock.patch.object(self._utils, "mInstallRpmOnNode") as mock_install, \
             mock.patch.object(self._utils, "mConfigureFalconSensor") as mock_configure, \
             mock.patch.object(self._utils, "mValidateFalconService") as mock_validate, \
             mock.patch.object(self._utils, "mRemoveRemoteFile") as mock_remove:
            self._utils.mInstallFalconSensor(
                "domu-3",
                "/images",
                {"ol8": "https://storage/falcon.rpm"},
                "CID777",
                "Create Service",
            )

        mock_download.assert_called_once_with("/images", "https://storage/falcon.rpm")
        mock_stage.assert_called_once_with(self._node, "domu-3", downloaded_path, os.path.join("/tmp", "falcon.rpm"))
        mock_install.assert_called_once_with(self._node, "domu-3", os.path.join("/tmp", "falcon.rpm"))
        mock_configure.assert_called_once_with(self._node, "domu-3", "CID777")
        mock_validate.assert_called_once_with(self._node, "domu-3")
        mock_remove.assert_called_once_with(self._node, "domu-3", os.path.join("/tmp", "falcon.rpm"))

    # Auto-generated test for mInstallFalconSensor
    def test_mInstallFalconSensor_raises_when_no_rpm_source_available(self):
        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=self._context_manager), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.gctx), \
             mock.patch.object(self._utils, "mDetectOracleLinuxMajor", return_value="8"), \
             mock.patch.object(self._utils, "mFindLocalRpm", return_value=None), \
             mock.patch.object(self._utils, "mDownloadFalconRpm") as mock_download, \
             mock.patch.object(self._utils, "mStageLocalRpm"), \
             mock.patch.object(self._utils, "mIsFalconInstalled", return_value=False), \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                self._utils.mInstallFalconSensor(
                    "domu-4",
                    "/images",
                    {},
                    "CID000",
                    "Create Service",
                )

        mock_download.assert_not_called()
        self.assertIn("Falcon RPM for OL8 not found locally", str(exc.exception))

    # Auto-generated test for mInstallFalconSensor
    def test_mInstallFalconSensor_propagates_exacloud_runtime_error(self):
        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=self._context_manager), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.gctx), \
             mock.patch.object(self._utils, "mDetectOracleLinuxMajor", return_value="8"), \
             mock.patch.object(self._utils, "mFindLocalRpm", return_value="/images/falcon.rpm"), \
             mock.patch.object(self._utils, "mStageLocalRpm"), \
             mock.patch.object(self._utils, "mIsFalconInstalled", return_value=False), \
             mock.patch.object(self._utils, "mInstallRpmOnNode", side_effect=ExacloudRuntimeError("install failed")):
            with self.assertRaises(ExacloudRuntimeError) as exc:
                self._utils.mInstallFalconSensor(
                    "domu-6",
                    "/images",
                    {"ol8": "https://example/falcon.rpm"},
                    "CID111",
                    "Create Service",
                )

        self.assertIn("install failed", str(exc.exception))

    # Auto-generated test for mInstallFalconSensor
    def test_mInstallFalconSensor_wraps_unexpected_errors(self):
        with mock.patch("exabox.ovm.utils.clu_utils.connect_to_host", return_value=self._context_manager), \
             mock.patch("exabox.ovm.utils.clu_utils.get_gcontext", return_value=mock.sentinel.gctx), \
             mock.patch.object(self._utils, "mDetectOracleLinuxMajor", return_value="8"), \
             mock.patch.object(self._utils, "mFindLocalRpm", return_value="/images/falcon.rpm"), \
             mock.patch.object(self._utils, "mStageLocalRpm", side_effect=RuntimeError("stage failed")), \
             mock.patch.object(self._utils, "mIsFalconInstalled", return_value=False), \
             mock.patch.object(self._utils, "mInstallRpmOnNode"), \
             mock.patch.object(self._utils, "mConfigureFalconSensor"), \
             mock.patch.object(self._utils, "mValidateFalconService"), \
             mock.patch.object(self._utils, "mRemoveRemoteFile") as mock_remove, \
             mock.patch("exabox.ovm.utils.clu_utils.ExacloudRuntimeError", DummyExacloudRuntimeError):
            with self.assertRaises(DummyExacloudRuntimeError) as exc:
                self._utils.mInstallFalconSensor(
                    "domu-5",
                    "/images",
                    {"ol8": "https://example/falcon.rpm"},
                    "CID555",
                    "Create Service",
                )

        mock_remove.assert_not_called()

    # Auto-generated test for mRemoveRemoteFile
    def test_mRemoveRemoteFile_invokes_rm_with_remote_path(self):
        with mock.patch("exabox.ovm.utils.clu_utils.node_cmd_abs_path_check", return_value="/bin/rm") as mock_cmd_check, \
             mock.patch("exabox.ovm.utils.clu_utils.node_exec_cmd") as mock_exec_cmd:
            self._utils.mRemoveRemoteFile(self._node, "domu-7", "/tmp/falcon.rpm")

        mock_cmd_check.assert_called_once_with(self._node, "rm")
        mock_exec_cmd.assert_called_once()
        invoked_cmd = mock_exec_cmd.call_args[0][1]
        self.assertIn("/bin/rm -f /tmp/falcon.rpm", invoked_cmd)


if __name__ == "__main__":
    unittest.main()
