#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluvmconsole_deploy.py /main/1 2025/11/18 03:55:10 shapatna Exp $
#
# tests_cluvmconsole_deploy.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluvmconsole_deploy.py - <one-line expansion of the name>
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
import unittest
import warnings
import os
import json
import copy
from types import SimpleNamespace
from unittest import mock
from unittest.mock import Mock, patch, mock_open

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError

# Import module under test using local module path while matching import grouping style from reference tests
import exabox.ovm.cluvmconsole_deploy as uut
from exabox.ovm.cluvmconsole_deploy import VMConsoleDeploy


class ebTestCluVMConsoleDeploy(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        # Keep same base init pattern as reference tests to load test infra and DB
        super(ebTestCluVMConsoleDeploy, self).setUpClass(aGenerateDatabase=True)
        warnings.filterwarnings("ignore")

    def _build_options(self, jsonconf=None):
        # Build options object consistent with reference style using clubox args template
        # Ensure jsonconf is a dict (not None) when code accesses .get on it
        base_opts = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        base_opts.jsonconf = jsonconf if jsonconf is not None else {}
        return base_opts

    def _make_deployer(self, options=None):
        if options is None:
            options = self._build_options({})
        return VMConsoleDeploy(self.mGetClubox(), options)

    def test_mGetDom0List_all_by_default(self):
        ebLogInfo("UT: mGetDom0List returns full compute list when jsonconf.dom0 not set")
        clu = self.mGetClubox()
        with patch.object(clu, "mReadComputes", return_value=["dom0a", "dom0b"]):
            d = VMConsoleDeploy(clu, self._build_options({}))
            self.assertEqual(d.mGetDom0List(), ["dom0a", "dom0b"])

    def test_mGetDom0List_filtered_valid(self):
        ebLogInfo("UT: mGetDom0List filters to selected dom0 when present")
        clu = self.mGetClubox()
        # The code checks substring presence: any(aDom0 in _dom0 for _dom0 in _dom0s)
        with patch.object(clu, "mReadComputes", return_value=["abc-host1-xyz", "host2.example"]):
            d = VMConsoleDeploy(clu, self._build_options({"dom0": "host1"}))
            self.assertEqual(d.mGetDom0List(), ["host1"])

    def test_mGetDom0List_filtered_invalid_raises(self):
        ebLogInfo("UT: mGetDom0List raises when selected dom0 not in computes")
        clu = self.mGetClubox()
        with patch.object(clu, "mReadComputes", return_value=["dom0a", "dom0b"]):
            d = VMConsoleDeploy(clu, self._build_options({"dom0": "notthere"}))
            with self.assertRaises(ExacloudRuntimeError):
                d.mGetDom0List()

    def test_mGetExadataVersionPathIfAvailable_exacc_new_stage(self):
        ebLogInfo("UT: mGetExadataVersionPathIfAvailable picks version-specific plugins on EXACC when present")
        clu = self.mGetClubox()
        d = VMConsoleDeploy(clu, self._build_options({}))

        with patch.object(clu, "mIsOciEXACC", return_value=True), \
             patch("os.path.exists", side_effect=lambda p: True), \
             patch("os.listdir", return_value=["pluginA"]), \
             patch("glob.glob", return_value=["/u01/downloads/exadata/PatchPayloads/23.1.19.0.0.241015/"]), \
             patch("os.path.getmtime", return_value=123456):
            path = d.mGetExadataVersionPathIfAvailable()
            self.assertTrue(path.endswith("exadataPrePostPlugins/dbnu_plugins/"))
            self.assertIn("PatchPayloads", path)

    def test_mGetExadataVersionPathIfAvailable_exacs_common_fallback(self):
        ebLogInfo("UT: mGetExadataVersionPathIfAvailable falls back to common plugin dir when version path empty")
        clu = self.mGetClubox()
        d = VMConsoleDeploy(clu, self._build_options({}))

        def fake_exists(p):
            # Simulate stage path exists but validation path empty/non-existent
            if p == "PatchPayloads/":
                return True
            if p.endswith("exadataPrePostPlugins/dbnu_plugins/"):
                return False
            return False

        with patch.object(clu, "mIsOciEXACC", return_value=False), \
             patch("os.path.exists", side_effect=fake_exists), \
             patch("glob.glob", return_value=[]):
            path = d.mGetExadataVersionPathIfAvailable()
            self.assertEqual(path, d.EXACS_PLUGINS_BUNDLE_DIR)

    def test_mGetLatestInstallerAvailable_prefers_plugins(self):
        ebLogInfo("UT: mGetLatestInstallerAvailable chooses plugin tgz when plugin version > images version")
        clu = self.mGetClubox()
        d = VMConsoleDeploy(clu, self._build_options({}))
        plugins_dir = "/tmp/plugins"
        plugins_tgz = os.path.join(plugins_dir, d.INSTALLER_BUNDLE_FILENAME)

        def fake_exists(p):
            if p == plugins_tgz:
                return True
            return False

        def mexec_side_effect(cmd):
            # The code expects a 4-tuple: (_, _, stdout, _)
            if cmd.startswith("/bin/cat "):
                return (0, None, "1.2.3\n", None)
            else:
                return (0, None, "", None)

        with patch.object(d, "mGetExadataVersionPathIfAvailable", return_value=plugins_dir), \
             patch("os.path.exists", side_effect=fake_exists), \
             patch("glob.glob", return_value=["images/vm_serial_console_patch.1.0.0.tgz"]), \
             patch.object(clu, "mExecuteLocal", side_effect=mexec_side_effect):
            chosen = d.mGetLatestInstallerAvailable()
            self.assertEqual(chosen, plugins_tgz)

    def test_mGetLatestInstallerAvailable_prefers_images(self):
        ebLogInfo("UT: mGetLatestInstallerAvailable chooses images tgz when images version > plugin version")
        clu = self.mGetClubox()
        d = VMConsoleDeploy(clu, self._build_options({}))
        plugins_dir = "/tmp/plugins"
        plugins_tgz = os.path.join(plugins_dir, d.INSTALLER_BUNDLE_FILENAME)
        image_tgz = "images/vm_serial_console_patch.1.2.3.tgz"

        def fake_exists(p):
            if p == plugins_tgz:
                return True
            if p == image_tgz:
                return True
            return False

        def mexec_side_effect(cmd):
            if cmd.startswith("/bin/cat "):
                return (0, None, "1.0.0\n", None)
            else:
                return (0, None, "", None)

        with patch.object(d, "mGetExadataVersionPathIfAvailable", return_value=plugins_dir), \
             patch("os.path.exists", side_effect=fake_exists), \
             patch("glob.glob", return_value=[image_tgz]), \
             patch.object(clu, "mExecuteLocal", side_effect=mexec_side_effect):
            chosen = d.mGetLatestInstallerAvailable()
            self.assertEqual(chosen, image_tgz)

    def test_mGetLatestInstallerAvailable_raises_when_missing(self):
        ebLogInfo("UT: mGetLatestInstallerAvailable raises when neither plugin nor images bundles found")
        clu = self.mGetClubox()
        d = VMConsoleDeploy(clu, self._build_options({}))
        with patch.object(d, "mGetExadataVersionPathIfAvailable", return_value="/no/such/dir"), \
             patch("os.path.exists", return_value=False), \
             patch("glob.glob", return_value=[]):
            with self.assertRaises(ExacloudRuntimeError):
                d.mGetLatestInstallerAvailable()

    def test_mDeployerExists_true_false(self):
        ebLogInfo("UT: mDeployerExists returns True/False based on exit status")
        # Mock exaBoxNode at point of use
        rc_sequence = [0, 1]  # first call -> True, second call -> False

        class FakeNode:
            def __init__(self, *_args, **_kwargs):
                pass
            def mConnect(self, **kwargs): pass
            def mExecuteCmd(self, *_a, **_k): pass
            def mGetCmdExitStatus(self):
                return rc_sequence.pop(0)
            def mDisconnect(self): pass

        d = self._make_deployer()
        with patch("exabox.ovm.cluvmconsole_deploy.exaBoxNode", return_value=FakeNode()):
            self.assertTrue(d.mDeployerExists("dom0a"))
            self.assertFalse(d.mDeployerExists("dom0b"))

    def test_mCopyInstaller_success_exacc(self):
        ebLogInfo("UT: mCopyInstaller returns 0 and touches is_exacc marker for EXACC")
        d = self._make_deployer()
        remote_dir = d.DEST_DIR
        bundle = "/tmp/vm_serial_console.tgz"

        class FakeNode:
            def __init__(self, *_a, **_k):
                self._rc = 0
            def mConnect(self, **kwargs): pass
            def mCopyFile(self, *_a, **_k): pass
            def mExecuteCmd(self, cmd):
                # simulate all commands as success
                self._rc = 0
                # Return triple (_, stdout, stderr) like real node; provide file-like .read()
                return (None, Mock(read=lambda: ""), Mock(read=lambda: ""))
            def mGetCmdExitStatus(self): return self._rc
            def mDisconnect(self): pass

        with patch.object(self.mGetClubox(), "mIsOciEXACC", return_value=True), \
             patch("exabox.ovm.cluvmconsole_deploy.exaBoxNode", return_value=FakeNode()):
            res = d.mCopyInstaller("dom0a", bundle)
            self.assertEqual(res, 0)

    def test_mCopyInstaller_extract_failure_sets_nonzero(self):
        ebLogInfo("UT: mCopyInstaller returns 1 when extracting inner tgz fails")
        d = self._make_deployer()
        bundle = "/tmp/vm_serial_console.tgz"

        class FakeNode:
            def __init__(self, *_a, **_k):
                self._rc = 0
                self._tar_calls = 0
            def mConnect(self, **kwargs): pass
            def mCopyFile(self, *_a, **_k): pass
            def mExecuteCmd(self, cmd):
                # first tar ok, second tar fails
                if "tar -xzf" in cmd:
                    self._tar_calls += 1
                    if self._tar_calls == 2:
                        self._rc = 1
                    else:
                        self._rc = 0
                return (None, Mock(read=lambda: ""), Mock(read=lambda: "error"))
            def mGetCmdExitStatus(self): return self._rc
            def mDisconnect(self): pass

        with patch("exabox.ovm.cluvmconsole_deploy.exaBoxNode", return_value=FakeNode()):
            res = d.mCopyInstaller("dom0a", bundle)
            self.assertEqual(res, 1)

    def test_mRunDeployerScript_success_and_failure(self):
        ebLogInfo("UT: mRunDeployerScript returns underlying rc and logs stdout/stderr")
        d = self._make_deployer()

        class FakeNode:
            def __init__(self, rcs):
                self._rcs = list(rcs)
                self._rc = 0
            def mConnect(self, **kwargs): pass
            def mExecuteCmd(self, cmd):
                self._rc = self._rcs.pop(0)
                return (None, Mock(read=lambda: "out"), Mock(read=lambda: "err"))
            def mGetCmdExitStatus(self): return self._rc
            def mDisconnect(self): pass

        with patch("exabox.ovm.cluvmconsole_deploy.exaBoxNode", return_value=FakeNode([0, 1])):
            # first success
            self.assertEqual(d.mRunDeployerScript("dom0a", "install"), 0)
            # then failure
            self.assertEqual(d.mRunDeployerScript("dom0a", "install"), 1)

    def test_mInstall_success_single_dom0(self):
        ebLogInfo("UT: mInstall happy path aggregates success and returns 0")
        clu = self.mGetClubox()
        d = VMConsoleDeploy(clu, self._build_options({}))
        with patch.object(d, "mGetDom0List", return_value=["host1"]), \
             patch.object(d, "mGetLatestInstallerAvailable", return_value="/tmp/bits.tgz"), \
             patch.object(d, "mCopyInstaller", return_value=0), \
             patch.object(d, "mRunDeployerScript", return_value=0), \
             patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps({
                 "host1": {
                    "serial_demux_rpm": {"status": 0},
                    "exa-hippo-serialmux_image": {"status": 0},
                    "exa-hippo-sshd_image": {"status": 0},
                    "exa-hippo-serialmux_containers_overall": 0,
                    "exa-hippo-sshd_containers_overall": 0
                 }
             }))), \
             patch.object(d, "mGetStatus", return_value=0), \
             patch.object(clu, "mGetRequestObj", return_value=None):
            res = d.mInstall()
            self.assertEqual(res, 0)

    def test_mUninstall_success_single_dom0(self):
        ebLogInfo("UT: mUninstall happy path aggregates success and returns 0")
        clu = self.mGetClubox()
        d = VMConsoleDeploy(clu, self._build_options({}))
        with patch.object(d, "mGetDom0List", return_value=["host1"]), \
             patch.object(d, "mGetLatestInstallerAvailable", return_value="/tmp/bits.tgz"), \
             patch.object(d, "mCopyInstaller", return_value=0), \
             patch.object(d, "mRunDeployerScript", return_value=0), \
             patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps({
                 "host1": {
                    # For uninstall, success condition is that these are NOT 0
                    "serial_demux_rpm": {"status": 1},
                    "exa-hippo-serialmux_image": {"status": 1},
                    "exa-hippo-sshd_image": {"status": 1},
                    "exa-hippo-serialmux_containers_overall": 1,
                    "exa-hippo-sshd_containers_overall": 1
                 }
             }))), \
             patch.object(d, "mGetStatus", return_value=0), \
             patch.object(clu, "mGetRequestObj", return_value=None):
            res = d.mUninstall()
            self.assertEqual(res, 0)

    def test_mGetStatus_success_nocopy_and_outputfile(self):
        ebLogInfo("UT: mGetStatus reads remote json and writes output file when aNoCopy=True")
        clu = self.mGetClubox()
        d = VMConsoleDeploy(clu, self._build_options({}))

        # Patch deployer existence and runner
        with patch.object(d, "mGetDom0List", return_value=["host1"]), \
             patch.object(d, "mDeployerExists", return_value=True), \
             patch.object(d, "mRunDeployerScript", return_value=0), \
             patch.object(clu, "mGetRequestObj", return_value=None):
            # Fake exaBoxNode to return the JSON content
            class FakeNode:
                def __init__(self, *_a, **_k): pass
                def mConnect(self, **kwargs): pass
                def mExecuteCmd(self, cmd):
                    content = json.dumps({"serial_demux_rpm": {"status": 0}})
                    return (None, Mock(read=lambda: content), Mock(read=lambda: ""))
                def mGetCmdExitStatus(self): return 0
                def mDisconnect(self): pass

            # Intercept file write for aOutputFile
            m_open = mock_open()
            with patch("exabox.ovm.cluvmconsole_deploy.exaBoxNode", return_value=FakeNode()), \
                 patch("builtins.open", m_open):
                res = d.mGetStatus(aNoCopy=True, aOutputFile="/tmp/vmconsole_status.json", aDom0List=["host1"])
                self.assertEqual(res, 0)
                # ensure output file write attempted
                m_open.assert_called_with("/tmp/vmconsole_status.json", "w")


if __name__ == '__main__':
    unittest.main()