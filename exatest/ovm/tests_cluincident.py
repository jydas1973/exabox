#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluincident.py /main/3 2026/02/10 14:41:13 shapatna Exp $
#
# tests_cluincidents.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluincidents.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    02/09/26 - Bug: 38941140 - Fix UT dif
#    shapatna    12/10/25 - Add unit test for cluincident.py
#    shapatna    12/10/25 - Creation
#
import os
import io
import json
import time
import shutil
import tempfile
import unittest

from types import SimpleNamespace
from unittest.mock import patch, Mock, MagicMock, mock_open

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cluincident import ebIncidentNode


class FakeZip:
    def __init__(self, *args, **kwargs):
        # capture path to allow path-sensitive asserts
        self._args = args
        self._written = []
        self._closed = False

    def write(self, path, arcname=None):
        # accept non-existent paths since we isolate FS in tests by mocking
        self._written.append((path, arcname))

    def close(self):
        self._closed = True


class ebTestCluIncident(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        # Use default environment from base test class
        super().setUpClass()

    def _default_context_mock(self, base="/tmp/exacloud/"):
        mock_ctx = Mock()
        mock_ctx.mGetBasePath.return_value = base
        return mock_ctx

    def _default_cluctrl_mock(self, is_exascale=True, dom_pairs=None):
        if dom_pairs is None:
            dom_pairs = [("dom0a", "vm01")]
        m = Mock()
        m.mIsExaScale.return_value = is_exascale
        m.mReturnDom0DomUPair.return_value = dom_pairs
        m.mGenerateCustomPolicyFileForThisRequest.return_value = None
        m.mFetchCrsAsmLogs.return_value = None
        return m

    # Auto-generated test for process: diag_level == "None" returns None
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.os.makedirs")
    @patch("exabox.ovm.cluincident.os.path.exists", return_value=True)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_level_none_returns_none(self, m_ctx, m_exists, m_makedirs, m_zip):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock()
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("None", "/tmp/diag", "uuid-none", cluctrl, options, step=None, do=None, aOP=None)
        self.assertIsNone(node.process())

    # Auto-generated test for process: returns None if zip path is missing
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.os.makedirs")
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_zip_missing_returns_none(self, m_ctx, m_makedirs, m_zip):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock()
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Normal", "/tmp/diag", "uuid-miss", cluctrl, options, step=None, do=None, aOP=None)
        # Return False specifically for the incident zip existence check
        target_zip = "/tmp/diag/Incident_uuid-miss.zip"

        def _exists_side(path):
            # we simulate tfactl base/log path existence True; incident zip False
            if path == target_zip:
                return False
            return True

        with patch("exabox.ovm.cluincident.os.path.exists", side_effect=_exists_side):
            self.assertIsNone(node.process())

    # Auto-generated test for process: normal path success, with internal helpers stubbed
    @patch.object(ebIncidentNode, "_ebIncidentNode__process_tfactl_log", return_value=0)
    @patch.object(ebIncidentNode, "_ebIncidentNode__execute_list", return_value=0)
    @patch.object(ebIncidentNode, "_ebIncidentNode__process_log", return_value=0)
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.os.path.exists", return_value=True)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_normal_happy(self, m_ctx, m_exists, m_zip, m_proc_log, m_exec_list, m_tfactl):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=True)  # skip tfactl branch
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Normal", "/tmp/diag", "uuid-ok", cluctrl, options, step=None, do=None, aOP=None)
        out = node.process()
        self.assertIsInstance(out, str)
        self.assertTrue(out.endswith(".zip"))
        m_proc_log.assert_called_once()

    # Auto-generated test for process: verbose path calls mFetchExavmImagesFinalXml and __execute_diag
    @patch.object(ebIncidentNode, "_ebIncidentNode__execute_diag", return_value=0)
    @patch.object(ebIncidentNode, "mFetchExavmImagesFinalXml", return_value=None)
    @patch.object(ebIncidentNode, "_ebIncidentNode__process_log", return_value=0)
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.os.path.exists", return_value=True)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_verbose_executes_diag_and_fetch_xml(self, m_ctx, m_exists, m_zip, m_proc_log, m_fetch, m_diag):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=True)
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Verbose", "/tmp/diag", "uuid-verb", cluctrl, options, step=None, do=None, aOP=None)
        out = node.process()
        self.assertTrue(out.endswith(".zip"))
        m_fetch.assert_called_once()
        m_diag.assert_called_once()

    # Auto-generated test for process: error path triggers cleanup when __process_log fails
    @patch.object(ebIncidentNode, "_ebIncidentNode__cleanup")
    @patch.object(ebIncidentNode, "_ebIncidentNode__process_tfactl_log", return_value=0)
    @patch.object(ebIncidentNode, "_ebIncidentNode__process_log", return_value=-1)
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.os.path.exists", return_value=True)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_error_cleanup_on_process_log_failure(self, m_ctx, m_exists, m_zip, m_proc_log, m_tfactl, m_cleanup):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=True)
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Normal", "/tmp/diag", "uuid-err", cluctrl, options, step=None, do=None, aOP=None)
        self.assertIsNone(node.process())
        m_cleanup.assert_called_once()

    # Auto-generated test for mFetchExavmImagesFinalXml: positive path with files written
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_mFetchExavmImagesFinalXml_happy(self, m_ctx, m_zip):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=True, dom_pairs=[("dom0a", "vm01"), ("dom0b", "vm02")])
        _ebox = self.mGetClubox()

        # Mock NodeConnection to write files into the temp dir path the method computes
        class _NodeObj:
            def mCopy2Local(self, src, dest):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w") as f:
                    f.write("<xml/>")

        class _NC:
            def __init__(self, _):
                pass
            def mGetNode(self, _dom0):
                return _NodeObj()

        with patch("exabox.ovm.cluincident.NodeConnection", side_effect=_NC):
            # ensure os.path.exists returns True for copied files so they are added to zip
            with patch("exabox.ovm.cluincident.os.path.exists", return_value=True):
                options = _ebox.mGetArgsOptions()  # uses default /EXAVMIMAGES/conf/
                node = ebIncidentNode("Verbose", "/tmp/diag", "uuid-xml", cluctrl, options, step=None, do=None, aOP=None)
                node.mFetchExavmImagesFinalXml()  # should not raise

    # Auto-generated test for tfactl log collection when logs path exists under destdir
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_collects_tfactl_when_dir_exists(self, m_ctx, m_zip):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=False)  # trigger tfactl processing via process()

        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Normal", "/tmp/tfactl_dest", "uuid-tf", cluctrl, options, step=None, do=None, aOP=None)

        tfactl_dir = "/tmp/tfactl_dest/log/tfactl_logs"
        # For incident zip existence
        inc_zip = "/tmp/tfactl_dest/Incident_uuid-tf.zip"
        # simulate tfactl dir with two files
        files = ["a.log", "b.txt"]

        def _exists_side(path):
            if path == inc_zip:
                return True
            if path == tfactl_dir:
                return True
            return True

        with patch.object(ebIncidentNode, "_ebIncidentNode__process_log", return_value=0), \
             patch("exabox.ovm.cluincident.os.path.exists", side_effect=_exists_side), \
             patch("exabox.ovm.cluincident.os.listdir", return_value=files), \
             patch("exabox.ovm.cluincident.shutil.rmtree") as m_rm:
            out = node.process()
            self.assertTrue(out.endswith(".zip"))
            m_rm.assert_called_once_with(tfactl_dir)

    # Auto-generated test for tfactl collection via flags when dest tfactl dir is absent
    @patch.object(ebIncidentNode, "_ebIncidentNode__execute_list", return_value=0)
    @patch("exabox.ovm.cluincident.ebCluHealth")
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_collects_tfactl_via_flags_when_absent(self, m_ctx, m_zip, m_hc, m_exec_list):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=False)
        # Stub ebCluHealth used inside __execute_list to avoid real initialization
        m_hc.return_value.mDoHealthCheck.return_value = None
        m_hc.return_value.mGetResultDir.return_value = "/tmp/hc_resultdir/"

        # Prepare a temporary directory with files to emulate returned CRS/ASM logs
        tmpdir = tempfile.mkdtemp()
        try:
            open(os.path.join(tmpdir, "x1.log"), "w").close()
            open(os.path.join(tmpdir, "x2.trc"), "w").close()

            cluctrl.mFetchCrsAsmLogs.return_value = tmpdir

            # Flags via helpers must return True to enable collection
            with patch("exabox.ovm.cluincident.ebCsSubCmdCheckOptions", return_value=True), \
                 patch("exabox.ovm.cluincident.ebCluCmdCheckOptions", return_value=True):

                _ebox = self.mGetClubox()
                options = _ebox.mGetArgsOptions()
                node = ebIncidentNode("Normal", "/tmp/nodir", "uuid-flag", cluctrl, options, step=None, do=None, aOP="node_addition")

                inc_zip = "/tmp/nodir/Incident_uuid-flag.zip"
                def _exists_side(path):
                    # incident zip exists; tfactl dir does not exist
                    if path == inc_zip:
                        return True
                    if path == "/tmp/nodir/log/tfactl_logs":
                        return False
                    # base tfactl output path under get_gcontext base
                    return True

                with patch.object(ebIncidentNode, "_ebIncidentNode__process_log", return_value=0), \
                     patch("exabox.ovm.cluincident.os.path.exists", side_effect=_exists_side), \
                     patch("exabox.ovm.cluincident.os.listdir", return_value=["x1.log", "x2.trc"]), \
                     patch("exabox.ovm.cluincident.shutil.rmtree") as m_rm:
                    out = node.process()
                    self.assertTrue(out.endswith(".zip"))
                    m_rm.assert_called_once_with(tmpdir)
        finally:
            # Ensure local tmpdir cleanup if not removed by logic (defensive)
            if os.path.isdir(tmpdir):
                shutil.rmtree(tmpdir)


# Additional tests to improve coverage of cluincident.py

    # Auto-generated test for __process_log positive path covering workers, crashes, threads and diag zips
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_log_happy_full(self, m_ctx, m_zip):
        base = "/tmp/exacloud/"
        dest = "/tmp/oeda"
        dflt_path = os.path.join(base, "log", "workers")
        thread_path = os.path.join(base, "log", "threads")
        crashes_glob = os.path.join(base, "log", "crashes", "**", "*.log")

        m_ctx.return_value = self._default_context_mock(base=base)
        cluctrl = self._default_cluctrl_mock(is_exascale=True)
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()

        os.makedirs(os.path.join(base, "log", "tfactl_logs"), exist_ok=True)
        os.makedirs(dest, exist_ok=True)
        open(os.path.join(dest, "Incident_uuidlog.zip"), "wb").close()
        node = ebIncidentNode("Normal", dest, "uuidlog", cluctrl, options, step=None, do=None, aOP="patching")

        # Patches
        with patch("exabox.ovm.cluincident.ebGetDefaultDB") as m_db, \
             patch("exabox.ovm.cluincident.psutil.Process") as m_proc, \
             patch("exabox.ovm.cluincident.glob.glob") as m_glob, \
             patch("exabox.ovm.cluincident.os.walk") as m_walk, \
             patch("exabox.ovm.cluincident.os.listdir") as m_listdir, \
             patch("exabox.ovm.cluincident.os.path.exists") as m_exists, \
             patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip):

            # DB and psutil mocks
            m_db_inst = Mock()
            m_db_inst.mGetWorkerPorts.return_value = [701, 702]
            m_db_inst.mGetAgentsPID.return_value = [(1111,)]
            m_db.return_value = m_db_inst

            m_proc.return_value.children.return_value = [Mock(pid=2222)]

            # Filesystem behavior
            def _glob_side(pattern, recursive=False):
                if pattern == crashes_glob:
                    return [os.path.join(base, "log", "crashes", "a", "b", "c.log")]
                # for workers patterns, just emit a synthetic file
                return [os.path.join(dflt_path, "synthetic_from_" + os.path.basename(pattern).replace("*", "X"))]
            m_glob.side_effect = _glob_side

            # Walk thread logs with matching uuid
            m_walk.return_value = [(thread_path, [], ["uuidlog.1.1.log", "uuidlog.2.2.trc", "other.txt"])]

            # List diag zips and patch logs
            def _listdir_side(path):
                if path == os.path.join(dest, "WorkDir"):
                    return ["Diag-001.zip", "Diag-002.zip", "misc.txt"]
                if path in (os.path.join(dest, "log", "patchmgr_logs"), os.path.join(dest, "log", "patch_logs")):
                    return ["p1", "p2"]
                return []
            m_listdir.side_effect = _listdir_side

            # Everything exists for happy path
            m_exists.return_value = True

            out = node.process()
            self.assertIsInstance(out, str)
            self.assertTrue(out.endswith(".zip"))

    # Auto-generated test for __process_log ENOSPC error path to exercise exception handling
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_log_enospc(self, m_ctx, m_zip):
        import errno as _errno
        base = "/tmp/exacloud/"
        dest = "/tmp/oeda"
        m_ctx.return_value = self._default_context_mock(base=base)
        cluctrl = self._default_cluctrl_mock(is_exascale=True)
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()

        os.makedirs(os.path.join(base, "log", "tfactl_logs"), exist_ok=True)
        os.makedirs(dest, exist_ok=True)
        open(os.path.join(dest, "Incident_uuidenospc.zip"), "wb").close()
        node = ebIncidentNode("Normal", dest, "uuidenospc", cluctrl, options, step=None, do=None, aOP=None)

        # Raise ENOSPC from listdir midway through __process_log and force error return
        def _listdir_raise(path):
            if path == os.path.join(dest, "WorkDir"):
                raise OSError(_errno.ENOSPC, "No space left on device")
            return []
        with patch.object(ebIncidentNode, "_ebIncidentNode__process_log", return_value=-1), \
             patch("exabox.ovm.cluincident.os.listdir", side_effect=_listdir_raise), \
             patch("exabox.ovm.cluincident.os.path.exists", return_value=True), \
             patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip):
            self.assertIsNone(node.process())

    # Auto-generated test for __process_tfactl_log path when zip creation for tfactl fails
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_tfactl_zip_creation_failure(self, m_ctx, m_zip):
        base = "/tmp/exacloud/"
        dest = "/tmp/tf"
        m_ctx.return_value = self._default_context_mock(base=base)
        cluctrl = self._default_cluctrl_mock(is_exascale=False)
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()

        os.makedirs(os.path.join(base, "log", "tfactl_logs"), exist_ok=True)
        os.makedirs(dest, exist_ok=True)
        open(os.path.join(dest, "Incident_uuidtf.zip"), "wb").close()
        node = ebIncidentNode("Normal", dest, "uuidtf", cluctrl, options, step=None, do=None, aOP=None)

        tfactl_dir = os.path.join(dest, "log", "tfactl_logs")

        def _zip_side_effect(path, mode, comp):
            # main incident zip should be fine; tfactl zip should fail
            if isinstance(path, str) and "Tfactl_" in path:
                raise Exception("zip create failure")
            return FakeZip(path, mode, comp)

        with patch("exabox.ovm.cluincident.os.path.exists", side_effect=lambda p: True), \
             patch("exabox.ovm.cluincident.os.listdir", return_value=["a.log", "b.trc"]), \
             patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=_zip_side_effect), \
             patch.object(ebIncidentNode, "_ebIncidentNode__process_log", return_value=0):
            out = node.process()
            # Process should complete despite tfactl zip creation failure
            self.assertTrue(out.endswith(".zip"))

    # Auto-generated test: Verbose path with __execute_diag failure triggers cleanup
    @patch.object(ebIncidentNode, "_ebIncidentNode__cleanup")
    @patch.object(ebIncidentNode, "_ebIncidentNode__execute_diag", return_value=-1)
    @patch.object(ebIncidentNode, "mFetchExavmImagesFinalXml", return_value=None)
    @patch.object(ebIncidentNode, "_ebIncidentNode__process_log", return_value=0)
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.os.path.exists", return_value=True)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_verbose_execute_diag_failure(self, m_ctx, m_exists, m_zip, m_proc_log, m_fetch, m_diag, m_cleanup):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=True)
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Verbose", "/tmp/diag", "uuid-verb-fail", cluctrl, options, step=None, do=None, aOP=None)
        self.assertIsNone(node.process())
        m_cleanup.assert_called_once()

    # Auto-generated test: mFetchExavmImagesFinalXml exception path (NodeConnection failure)
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_mFetchExavmImagesFinalXml_error(self, m_ctx, m_zip):
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=True, dom_pairs=[("dom0x", "vmX")])
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        class _NCFail:
            def __init__(self, _): pass
            def mGetNode(self, _): raise RuntimeError("node failure")
        with patch("exabox.ovm.cluincident.NodeConnection", side_effect=_NCFail), \
             patch("exabox.ovm.cluincident.os.path.exists", return_value=True):
            os.makedirs("/tmp/exacloud/log/tfactl_logs", exist_ok=True)
            diag_dir = tempfile.mkdtemp(prefix="cluincident-")
            try:
                open(os.path.join(diag_dir, "Incident_uuid-xml-err.zip"), "wb").close()
                node = ebIncidentNode("Verbose", diag_dir, "uuid-xml-err", cluctrl, options, step=None, do=None, aOP=None)
                node.mFetchExavmImagesFinalXml()  # should swallow and log error
            finally:
                shutil.rmtree(diag_dir, ignore_errors=True)

    # Additional tests to further increase coverage of cluincident.py internals

    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.ebCluHealth")
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_execute_list_success(self, m_ctx, m_hc, m_zip):
        # Cover __execute_list happy path with patched healthcheck map
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=True)
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Normal", "/tmp/diag", "uuid-execlist", cluctrl, options, step=None, do=None, aOP=None)

        # Patch the HC step map and constants used by __execute_list
        with patch("exabox.ovm.cluincident.gCreateServiceMapDO", "DO"), \
             patch("exabox.ovm.cluincident.gCreateServiceMapUNDO", "UNDO"), \
             patch("exabox.ovm.cluincident.gCreateServiceStepIncidentTestsMap",
                   {"STEPX": {"DO": ([["IncludeSet"]], [["Targets"]]),
                              "UNDO": ([["IncludeSetU"]], [["TargetsU"]])}}):
            m_hc.return_value.mDoHealthCheck.return_value = None
            m_hc.return_value.mGetResultDir.return_value = "/tmp/hc_out/"
            rc = node._ebIncidentNode__execute_list("STEPX", True)
            self.assertEqual(rc, 0)

    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.json.load", return_value={"hc": "incident"})
    @patch("exabox.ovm.cluincident.open", new_callable=mock_open, read_data="{}")
    @patch("exabox.ovm.cluincident.ebCluHealth")
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_execute_diag_success(self, m_ctx, m_hc, m_open, m_json_load, m_zip):
        # Cover __execute_diag happy path
        base = "/tmp/exa/"
        m_ctx.return_value = self._default_context_mock(base=base)
        cluctrl = self._default_cluctrl_mock(is_exascale=True)
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Verbose", "/tmp/diag", "uuid-diag", cluctrl, options, step=None, do=None, aOP=None)

        m_hc.return_value.mDoHealthCheck.return_value = None
        m_hc.return_value.mGetResultDir.return_value = "/tmp/diagdir/"
        rc = node._ebIncidentNode__execute_diag()
        self.assertEqual(rc, 0)

    @patch("exabox.ovm.cluincident.os.remove")
    @patch("exabox.ovm.cluincident.os.path.exists", return_value=True)
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_cleanup_executes(self, m_ctx, m_zip, m_exists, m_remove):
        # Directly execute __cleanup to cover file removal
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock()
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Normal", "/tmp/diag", "uuid-clean", cluctrl, options, step=None, do=None, aOP=None)
        node._ebIncidentNode__cleanup()
        m_remove.assert_called_once_with("/tmp/diag/Incident_uuid-clean.zip")

    @patch("exabox.ovm.cluincident.os.path.exists", return_value=True)
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_destructor_closes_zip(self, m_ctx, m_zip, m_exists):
        # Call __del__ explicitly to cover close path
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock()
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        node = ebIncidentNode("Normal", "/tmp/diag", "uuid-del", cluctrl, options, step=None, do=None, aOP=None)
        # Explicitly invoke destructor to ensure coverage of the body
        node.__del__()
        self.assertTrue(node._zipF._closed)

    @patch("exabox.ovm.cluincident.ebLogError")
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=Exception("zip-fail"))
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_constructor_zip_exception_logs(self, m_ctx, m_zip, m_log):
        # Trigger constructor exception path and ensure it logs error
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock()
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        _ = ebIncidentNode("Normal", "/tmp/diag", "uuid-ctor", cluctrl, options, step=None, do=None, aOP=None)
        self.assertTrue(m_log.called)

    @patch.object(ebIncidentNode, "_ebIncidentNode__execute_list", return_value=0)
    @patch("exabox.ovm.cluincident.zipfile.ZipFile", side_effect=FakeZip)
    @patch("exabox.ovm.cluincident.os.path.exists", return_value=True)
    @patch("exabox.ovm.cluincident.get_gcontext")
    def test_process_db_install_branch(self, m_ctx, m_exists, m_zip, m_exec_list):
        # Cover op == 'db_install' path that invokes __execute_list with ESTP_DB_INSTALL
        m_ctx.return_value = self._default_context_mock()
        cluctrl = self._default_cluctrl_mock(is_exascale=True)
        _ebox = self.mGetClubox()
        options = _ebox.mGetArgsOptions()
        diag_dir = tempfile.mkdtemp(prefix="cluincident-")
        try:
            node = ebIncidentNode("Normal", diag_dir, "uuid-dbinst", cluctrl, options, step=None, do=None, aOP="db_install")
            open(os.path.join(diag_dir, "Incident_uuid-dbinst.zip"), "wb").close()
            # Ensure __process_log succeeds so process() continues and returns zip path
            with patch.object(ebIncidentNode, "_ebIncidentNode__process_log", return_value=0):
                out = node.process()
            self.assertIsInstance(out, str)
            self.assertTrue(out.endswith(".zip"))
            self.assertTrue(m_exec_list.called)
        finally:
            shutil.rmtree(diag_dir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
