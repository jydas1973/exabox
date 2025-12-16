#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_cleanup_oeda_requests.py /main/3 2025/11/18 03:55:10 shapatna Exp $
#
# tests_cleanup_oeda_requests.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cleanup_oeda_requests.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    11/07/25 - Enh 38574081: Add unit tests to improve the
#                           coverage using Cline
#    shapatna    09/14/25 - Add unit tests for moving files and folder to
#                           ExacloudLogArchive Directory
#    aararora    04/09/25 - Unit test for oeda requests cleanup scheduler
#    aararora    04/09/25 - Creation
#
import os
import shutil
import re
import time
import unittest
import tarfile
from unittest.mock import patch, MagicMock, Mock, call
from exabox.log.LogMgr import ebLogInfo
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.scheduleJobs.cleanup_oeda_requests import CleanUpOedaRequests


class ebTestCleanupOedaRequests(ebTestClucontrol):
    
    @classmethod
    def setUpClass(self):
        super(ebTestCleanupOedaRequests, self).setUpClass(True,False)

    @patch('exabox.scheduleJobs.cleanup_oeda_requests.os')
    @patch('exabox.scheduleJobs.cleanup_oeda_requests.shutil')
    @patch('exabox.scheduleJobs.cleanup_oeda_requests.time')
    @patch('exabox.scheduleJobs.cleanup_oeda_requests.re')
    @patch('exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext')
    @patch('exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit')
    @patch('exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit')
    def test_mExecuteJob_move_old_requests(self, _mock_core_init, _mock_log_init, mock_get_gctx, mock_re, mock_time, mock_shutil, mock_os):

        ebLogInfo("Running unit test on CleanUpOedaRequests.mExecuteJob")
        # Mock context/config so no real environment is used
        mock_ctx = Mock()
        mock_ctx.mGetArgsOptions.return_value = {}
        mock_ctx.mGetConfigOptions.return_value = {
            "schedule_oeda_requests_in_days": "1",
            "log_file_archive_directory": "/tmp/exalogarchive",
            "oeda_archive_requests_path": "oeda/requests.bak"
        }
        mock_get_gctx.return_value = mock_ctx

        # Mock OS/time behaviors
        mock_os.getcwd.return_value = "/opt/app/exacloud/env/exacloud/bin"
        mock_os.path.join.side_effect = lambda a, b: f"{a}/{b}"
        mock_os.path.isabs.return_value = True
        mock_os.path.exists.return_value = True
        mock_os.listdir.return_value = ["request1", "request2"]
        mock_time.time.return_value = 200
        mock_os.stat.return_value = type("S", (), {"st_mtime": 50})()
        mock_re.match.return_value = True

        inst = CleanUpOedaRequests()
        # Ensure archive dir set and threshold triggers move
        inst._CleanUpOedaRequests__oeda_request_archive_directory = "/tmp/exalogarchive/2025_1_1/oeda_requests"
        inst._CleanUpOedaRequests__max_seconds = 100

        inst.mExecuteJob()

        self.assertTrue(mock_shutil.move.called)
        ebLogInfo("Unit test on CleanUpOedaRequests.mExecuteJob executed successfully")


class ebTestCleanupOedaRequestsAdvanced(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCleanupOedaRequestsAdvanced, self).setUpClass(True, False)

    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.getcwd", return_value="/opt/oracle/exacloud/work/exacloud/project")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit")
    def test_mParseConfig_valid_sets_seconds(self, _mock_core_init, _mock_log_init, mock_get_gctx, _mock_getcwd):
        ebLogInfo("Running unit test on CleanUpOedaRequests.mParseConfig (valid)")
        mock_ctx = Mock()
        mock_ctx.mGetArgsOptions.return_value = {}
        mock_ctx.mGetConfigOptions.return_value = {
            "schedule_oeda_requests_in_days": "2",
            "log_file_archive_directory": "/tmp/exalogarchive",
            "oeda_archive_requests_path": ""
        }
        mock_get_gctx.return_value = mock_ctx

        inst = CleanUpOedaRequests()
        self.assertEqual(inst._CleanUpOedaRequests__max_seconds, 2 * 24 * 60 * 60)
        ebLogInfo("mParseConfig valid executed successfully")

    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.getcwd", return_value="/opt/oracle/exacloud/work/exacloud/project")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit")
    def test_mParseConfig_missing_and_invalid(self, _mock_core_init, _mock_log_init, mock_get_gctx, _mock_getcwd):
        ebLogInfo("Running unit test on CleanUpOedaRequests.mParseConfig (missing/invalid)")
        # Missing
        mock_ctx1 = Mock()
        mock_ctx1.mGetArgsOptions.return_value = {}
        mock_ctx1.mGetConfigOptions.return_value = {
            "schedule_oeda_requests_in_days": "",
            "log_file_archive_directory": "/tmp/exalogarchive",
            "oeda_archive_requests_path": ""
        }
        mock_get_gctx.return_value = mock_ctx1
        inst1 = CleanUpOedaRequests()
        self.assertEqual(inst1._CleanUpOedaRequests__max_seconds, 0)

        # Invalid non-numeric
        mock_ctx2 = Mock()
        mock_ctx2.mGetArgsOptions.return_value = {}
        mock_ctx2.mGetConfigOptions.return_value = {
            "schedule_oeda_requests_in_days": "abc",
            "log_file_archive_directory": "/tmp/exalogarchive",
            "oeda_archive_requests_path": ""
        }
        mock_get_gctx.return_value = mock_ctx2
        inst2 = CleanUpOedaRequests()
        self.assertEqual(inst2._CleanUpOedaRequests__max_seconds, 0)
        ebLogInfo("mParseConfig missing/invalid executed successfully")

    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.makedirs")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.path.exists")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.path.isabs", return_value=True)
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.getcwd", return_value="/opt/oracle/exacloud/exacloud/project")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.date")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit")
    def test_mFetchOedaRequestArchiveDirectory_uses_config_path(self, _mock_core_init, _mock_log_init, mock_get_gctx, mock_date, _mock_getcwd, mock_isabs, mock_exists, mock_makedirs):
        ebLogInfo("Running unit test on CleanUpOedaRequests.mFetchOedaRequestArchiveDirectory (valid config path)")
        # Provide a fake date object with year, month, day attributes
        fake_today = type("FakeDate", (), {"year": 2025, "month": 1, "day": 2})()
        mock_date.today.return_value = fake_today

        cfg = {
            "schedule_oeda_requests_in_days": "1",
            "log_file_archive_directory": "/tmp/exacloudLogArchive",
            "oeda_archive_requests_path": ""
        }
        mock_ctx = Mock()
        mock_ctx.mGetArgsOptions.return_value = {}
        mock_ctx.mGetConfigOptions.return_value = cfg
        mock_get_gctx.return_value = mock_ctx

        # exists: base path True, dated dir False, oeda_requests False
        def exists_side_effect(path):
            if path == "/tmp/exacloudLogArchive":
                return True
            if path == "/tmp/exacloudLogArchive/2025_1_2":
                return False
            if path == "/tmp/exacloudLogArchive/2025_1_2/oeda_requests":
                return False
            return False

        mock_exists.side_effect = exists_side_effect

        inst = CleanUpOedaRequests()
        inst.mFetchOedaRequestArchiveDirectory()

        expected_dated_dir = "/tmp/exacloudLogArchive/2025_1_2"
        expected_oeda_dir = "/tmp/exacloudLogArchive/2025_1_2/oeda_requests"

        mock_makedirs.assert_has_calls([call(expected_dated_dir), call(expected_oeda_dir)])
        self.assertEqual(inst._CleanUpOedaRequests__oeda_request_archive_directory, expected_oeda_dir)
        ebLogInfo("mFetchOedaRequestArchiveDirectory valid config executed successfully")

    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.makedirs")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.path.exists")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.path.isabs", return_value=True)
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.getcwd", return_value="/opt/oracle/exa/exacloud/svc")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.date")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit")
    def test_mFetchOedaRequestArchiveDirectory_fallback_to_default(self, _mock_core_init, _mock_log_init, mock_get_gctx, mock_date, _mock_getcwd, _mock_isabs, mock_exists, mock_makedirs):
        ebLogInfo("Running unit test on CleanUpOedaRequests.mFetchOedaRequestArchiveDirectory (fallback path)")
        fake_today = type("FakeDate", (), {"year": 2025, "month": 12, "day": 9})()
        mock_date.today.return_value = fake_today

        cfg = {
            "schedule_oeda_requests_in_days": "1",
            "log_file_archive_directory": "/path/not/found",
            "oeda_archive_requests_path": ""
        }
        mock_ctx = Mock()
        mock_ctx.mGetArgsOptions.return_value = {}
        mock_ctx.mGetConfigOptions.return_value = cfg
        mock_get_gctx.return_value = mock_ctx

        # Provided base path does NOT exist -> fallback to ../exacloudLogArchive relative to exacloudPath
        def exists_side_effect(path):
            if path == "/path/not/found":
                return False
            if path == "/opt/oracle/exa/exacloud/../exacloudLogArchive/2025_12_9":
                return False
            if path == "/opt/oracle/exa/exacloud/../exacloudLogArchive/2025_12_9/oeda_requests":
                return False
            return False

        mock_exists.side_effect = exists_side_effect

        inst = CleanUpOedaRequests()
        inst.mFetchOedaRequestArchiveDirectory()

        expected_dated_dir = "/opt/oracle/exa/exacloud/../exacloudLogArchive/2025_12_9"
        expected_oeda_dir = "/opt/oracle/exa/exacloud/../exacloudLogArchive/2025_12_9/oeda_requests"

        mock_makedirs.assert_has_calls([call(expected_dated_dir), call(expected_oeda_dir)])
        self.assertEqual(inst._CleanUpOedaRequests__oeda_request_archive_directory, expected_oeda_dir)
        ebLogInfo("mFetchOedaRequestArchiveDirectory fallback executed successfully")

    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.listdir")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.path.exists")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.getcwd", return_value="/opt/app/exacloud/env/exacloud/bin")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit")
    def test_mFetchEntriesInRequestsBakDir_default_and_custom(self, _mock_core_init, _mock_log_init, mock_get_gctx, _mock_getcwd, mock_exists, mock_listdir):
        ebLogInfo("Running unit test on CleanUpOedaRequests.mFetchEntriesInRequestsBakDir (default/custom)")
        # Default path when missing
        cfg1 = {
            "schedule_oeda_requests_in_days": "1",
            "log_file_archive_directory": "/tmp/exalogarchive",
            "oeda_archive_requests_path": ""
        }
        mock_ctx1 = Mock()
        mock_ctx1.mGetArgsOptions.return_value = {}
        mock_ctx1.mGetConfigOptions.return_value = cfg1
        mock_get_gctx.return_value = mock_ctx1
        mock_exists.return_value = True
        mock_listdir.return_value = ["r1", "r2"]

        inst1 = CleanUpOedaRequests()
        paths1 = inst1.mFetchEntriesInRequestsBakDir()
        expected_dir1 = "/opt/app/exacloud/env/exacloud/oeda/requests.bak"
        self.assertEqual(paths1, [expected_dir1 + "/r1", expected_dir1 + "/r2"])

        # Custom path from config
        cfg2 = {
            "schedule_oeda_requests_in_days": "1",
            "log_file_archive_directory": "/tmp/exalogarchive",
            "oeda_archive_requests_path": "var/backups/requests.bak"
        }
        mock_ctx2 = Mock()
        mock_ctx2.mGetArgsOptions.return_value = {}
        mock_ctx2.mGetConfigOptions.return_value = cfg2
        mock_get_gctx.return_value = mock_ctx2
        mock_exists.return_value = True
        mock_listdir.return_value = ["x", "y"]

        inst2 = CleanUpOedaRequests()
        paths2 = inst2.mFetchEntriesInRequestsBakDir()
        expected_dir2 = "/opt/app/exacloud/env/exacloud/var/backups/requests.bak"
        self.assertEqual(paths2, [expected_dir2 + "/x", expected_dir2 + "/y"])
        ebLogInfo("mFetchEntriesInRequestsBakDir default/custom executed successfully")

    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogTrace")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.shutil.move")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.shutil.rmtree")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.remove")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.path.isdir")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.path.isfile")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.path.exists")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.os.stat")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit")
    def test_mCheckAndMoveOldOedaRequests_moves_and_overwrites(self, _mock_core_init, _mock_log_init, mock_get_gctx, mock_stat, mock_exists, mock_isfile, mock_isdir, mock_remove, mock_rmtree, mock_move, mock_log_trace):
        ebLogInfo("Running unit test on CleanUpOedaRequests.mCheckAndMoveOldOedaRequests")
        mock_ctx = Mock()
        mock_ctx.mGetArgsOptions.return_value = {}
        mock_ctx.mGetConfigOptions.return_value = {"schedule_oeda_requests_in_days": "1"}
        mock_get_gctx.return_value = mock_ctx

        inst = CleanUpOedaRequests()
        # Force private fields for the test
        inst._CleanUpOedaRequests__oeda_request_archive_directory = "/archive/dir"
        inst._CleanUpOedaRequests__max_seconds = 100

        reqs = ["/bak/req_file", "/bak/req_dir"]

        class StatObj:
            st_mtime = 0
        mock_stat.return_value = StatObj()

        def exists_side(path):
            # both targets exist to trigger overwrite paths
            if path in ["/archive/dir/req_file", "/archive/dir/req_dir"]:
                return True
            return False
        mock_exists.side_effect = exists_side

        def isfile_side(path):
            return path == "/archive/dir/req_file"
        mock_isfile.side_effect = isfile_side

        def isdir_side(path):
            return path == "/archive/dir/req_dir"
        mock_isdir.side_effect = isdir_side

        inst.mCheckAndMoveOldOedaRequests(reqs)

        mock_remove.assert_called_once_with("/archive/dir/req_file")
        mock_rmtree.assert_called_once_with("/archive/dir/req_dir")
        mock_move.assert_has_calls([call("/bak/req_file", "/archive/dir"), call("/bak/req_dir", "/archive/dir")], any_order=False)
        self.assertGreaterEqual(mock_log_trace.call_count, 1)
        ebLogInfo("mCheckAndMoveOldOedaRequests executed successfully")

    @patch("exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit")
    def test_mExecuteJob_skip_when_max_seconds_zero(self, _mock_core_init, _mock_log_init, mock_get_gctx):
        ebLogInfo("Running unit test on CleanUpOedaRequests.mExecuteJob skip (max_seconds=0)")
        cfg = {
            "schedule_oeda_requests_in_days": "",
            "log_file_archive_directory": "/tmp/exalogarchive",
            "oeda_archive_requests_path": ""
        }
        mock_ctx = Mock()
        mock_ctx.mGetArgsOptions.return_value = {}
        mock_ctx.mGetConfigOptions.return_value = cfg
        mock_get_gctx.return_value = mock_ctx

        inst = CleanUpOedaRequests()
        with patch.object(inst, "mFetchOedaRequestArchiveDirectory") as mock_fetch_dir, \
             patch.object(inst, "mFetchEntriesInRequestsBakDir") as mock_fetch_entries, \
             patch.object(inst, "mCheckAndMoveOldOedaRequests") as mock_move:
            # ensure archive dir not None doesn't matter; logic returns before using it
            inst._CleanUpOedaRequests__oeda_request_archive_directory = "/some/dir"
            inst.mExecuteJob()
            mock_fetch_dir.assert_called_once()
            mock_fetch_entries.assert_not_called()
            mock_move.assert_not_called()
        ebLogInfo("mExecuteJob skip (max_seconds=0) executed successfully")

    @patch("exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit")
    def test_mExecuteJob_skip_when_archive_dir_none(self, _mock_core_init, _mock_log_init, mock_get_gctx):
        ebLogInfo("Running unit test on CleanUpOedaRequests.mExecuteJob skip (archive dir None)")
        cfg = {
            "schedule_oeda_requests_in_days": "1",
            "log_file_archive_directory": "/tmp/exalogarchive",
            "oeda_archive_requests_path": ""
        }
        mock_ctx = Mock()
        mock_ctx.mGetArgsOptions.return_value = {}
        mock_ctx.mGetConfigOptions.return_value = cfg
        mock_get_gctx.return_value = mock_ctx

        inst = CleanUpOedaRequests()
        with patch.object(inst, "mFetchOedaRequestArchiveDirectory") as mock_fetch_dir, \
             patch.object(inst, "mFetchEntriesInRequestsBakDir") as mock_fetch_entries, \
             patch.object(inst, "mCheckAndMoveOldOedaRequests") as mock_move:
            # Leave __oeda_request_archive_directory as None to hit the guard
            inst._CleanUpOedaRequests__oeda_request_archive_directory = None
            inst.mExecuteJob()
            mock_fetch_dir.assert_called_once()
            mock_fetch_entries.assert_not_called()
            mock_move.assert_not_called()
        ebLogInfo("mExecuteJob skip (archive dir None) executed successfully")

    @patch("exabox.scheduleJobs.cleanup_oeda_requests.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_oeda_requests.exaBoxCoreInit")
    def test_mExecuteJob_happy_path_invokes_move(self, _mock_core_init, _mock_log_init, mock_get_gctx):
        ebLogInfo("Running unit test on CleanUpOedaRequests.mExecuteJob happy path")
        cfg = {
            "schedule_oeda_requests_in_days": "1",
            "log_file_archive_directory": "/tmp/exalogarchive",
            "oeda_archive_requests_path": "oeda/requests.bak"
        }
        mock_ctx = Mock()
        mock_ctx.mGetArgsOptions.return_value = {}
        mock_ctx.mGetConfigOptions.return_value = cfg
        mock_get_gctx.return_value = mock_ctx

        inst = CleanUpOedaRequests()
        # Prepare helpers
        with patch.object(inst, "mFetchOedaRequestArchiveDirectory") as mock_fetch_dir, \
             patch.object(inst, "mFetchEntriesInRequestsBakDir", return_value=["/b/r1", "/b/r2"]) as mock_fetch_entries, \
             patch.object(inst, "mCheckAndMoveOldOedaRequests") as mock_move:
            inst._CleanUpOedaRequests__oeda_request_archive_directory = "/archive/dir"
            inst.mExecuteJob()
            mock_fetch_dir.assert_called_once()
            mock_fetch_entries.assert_called_once()
            mock_move.assert_called_once_with(["/b/r1", "/b/r2"])
        ebLogInfo("mExecuteJob happy path executed successfully")


if __name__ == '__main__':
    unittest.main()