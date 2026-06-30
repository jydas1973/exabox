#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_cleanup_log_files.py noduri_bug-38808808/1 2026/01/24 05:38:01 noduri Exp $
#
# tests_cleanup_log_files.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
# Copyright (c) 2023,
# Oracle and/or its affiliates.
#
#    NAME
#      tests_cleanup_log_files.py - Unit tests for scheduleJobs.cleanup_log_files
#
#    MODIFIED   (MM/DD/YY)
#    aararora    05/11/26 - Bug 39097556: Tar the contents under folders being
#                           added to exacloud log archive directory
#    noduri      04/29/26 - Bug 39278508 - ECS_MAIN -> TESTS_CLEANUP_LOG_FILES_PY.DIF
#                           IS FAILING IN ECS_MAIN_LINUX.X64_260428.0817  
#    aypaul      04/16/26 - Bug#38900303 Fix unit tests for codev identified issues
#    noduri      01/22/25 - Bug 38808808 - /U01 FILESYSTEM UTILIZATION ON FRA2EDCSEC
#                           RA2 IS AROUND 90%, EXACLOUDLOGARCHIVE IS CONSUMING
#                           AROUND 421G
#    aararora    08/28/25 - Bug 38298135: Enhance exception handling and
#                           logging for cleanup logs scheduler command
#    avimonda    03/14/25 - Bug 37584489 - OC1| FRA3 | ECRA2 SERVER FILESYSTEM
#                /U02 FILLED UP WITH EXACLOUDLOGARCHIVE FILES
#    aararora    09/29/23 - Adding unit test for scheduler job of log files
#                           cleanup
#    aararora    09/29/23 - Creation
#

import os
import tarfile
import tempfile
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import six

if not hasattr(six, "ensure_binary"):
    def _ensure_binary(value, encoding='utf-8', errors='strict'):
        if isinstance(value, bytes):
            return value
        return str(value).encode(encoding, errors)

    def _ensure_text(value, encoding='utf-8', errors='strict'):
        if isinstance(value, bytes):
            return value.decode(encoding, errors)
        return str(value)

    six.ensure_binary = _ensure_binary
    six.ensure_text = _ensure_text
    six.ensure_str = _ensure_text

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.scheduleJobs.cleanup_log_files import CleanUpLogFiles


def _ctx_with_config(**overrides):
    config = {
        "log_cleanup_duration": "168",
        "log_file_archive_directory": "",
        "log_archive_cleanup_age_limit_in_days": "30",
    }
    config.update(overrides)
    ctx = MagicMock()
    ctx.mGetArgsOptions.return_value = {}
    ctx.mGetConfigOptions.return_value = config
    return ctx


def _today_dir():
    _today = date.today()
    return f"{_today.year}_{_today.month}_{_today.day}"


class ebTestCleanupLogFiles(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCleanupLogFiles, cls).setUpClass(True, False)

    def test_mParseConfig_uses_absolute_archive_dir(self):
        ctx = _ctx_with_config(
            log_cleanup_duration="24",
            log_file_archive_directory="/tmp/exalogarchive",
            log_archive_cleanup_age_limit_in_days="45",
        )
        expected_dir = f"/tmp/exalogarchive/{_today_dir()}"

        with patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.path.isabs", return_value=True), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.path.exists") as mock_exists, \
             patch("exabox.scheduleJobs.cleanup_log_files.os.mkdir") as mock_mkdir, \
             patch("exabox.scheduleJobs.cleanup_log_files.os.makedirs") as mock_makedirs, \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInfo"):

            def exists_side(path):
                if path == "/tmp/exalogarchive":
                    return True
                return False

            mock_exists.side_effect = exists_side
            job = CleanUpLogFiles()

        self.assertEqual(job._CleanUpLogFiles__log_file_persist_duration_hrs, 24)
        self.assertEqual(job._CleanUpLogFiles__log_archive_cleanup_age_limit_in_days, 45)
        self.assertEqual(job._CleanUpLogFiles__log_file_archive_directory, expected_dir)
        mock_mkdir.assert_called_once_with(expected_dir)
        mock_makedirs.assert_not_called()

    def test_mParseConfig_falls_back_when_path_missing(self):
        ctx = _ctx_with_config(
            log_cleanup_duration="12",
            log_file_archive_directory="/missing/archive",
        )
        expected_base = "/opt/app/exacloud/../exacloudLogArchive"
        expected_dir = f"{expected_base}/{_today_dir()}"

        with patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.path.isabs", return_value=True), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.path.exists", return_value=False) as mock_exists, \
             patch("exabox.scheduleJobs.cleanup_log_files.os.mkdir") as mock_mkdir, \
             patch("exabox.scheduleJobs.cleanup_log_files.os.makedirs") as mock_makedirs, \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInfo"):
            job = CleanUpLogFiles()

        self.assertEqual(job._CleanUpLogFiles__log_file_persist_duration_hrs, 12)
        self.assertEqual(job._CleanUpLogFiles__log_file_archive_directory, expected_dir)
        mock_mkdir.assert_not_called()
        mock_makedirs.assert_called_once_with(expected_dir)

    def test_mCleanupExacloudLogArchiveDirectory_handles_errors(self):
        ctx = _ctx_with_config()
        with patch.object(CleanUpLogFiles, "mParseConfig", autospec=True, return_value=None), \
             patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpLogFiles()

        with patch("exabox.scheduleJobs.cleanup_log_files.os.listdir", return_value=["old_dir", "another_dir"]), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.path.isdir", return_value=True), \
             patch.object(CleanUpLogFiles, "mIsOldDir", side_effect=[True, True]), \
             patch("exabox.scheduleJobs.cleanup_log_files.shutil.rmtree", side_effect=[Exception("boom"), None]) as mock_rmtree, \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogError") as mock_error, \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInfo"):
            job.mCleanupExacloudLogArchiveDirectory("/archive/dir")

        self.assertEqual(mock_rmtree.call_count, 2)
        mock_error.assert_called()

    def test_mIsOldDir_various_inputs(self):
        ctx = _ctx_with_config(log_archive_cleanup_age_limit_in_days="1")
        with patch.object(CleanUpLogFiles, "mParseConfig", autospec=True, return_value=None), \
             patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpLogFiles()

        today = datetime.today()
        fresh = (today - timedelta(days=0)).strftime("%Y_%m_%d")
        old = (today - timedelta(days=2)).strftime("%Y_%m_%d")

        job._CleanUpLogFiles__log_archive_cleanup_age_limit_in_days = 1
        self.assertFalse(job.mIsOldDir(fresh))
        self.assertTrue(job.mIsOldDir(old))
        self.assertFalse(job.mIsOldDir("invalid-format"))

    def test_mExecuteJob_moves_and_cleans_expected_files(self):
        ctx = _ctx_with_config()
        with patch.object(CleanUpLogFiles, "mParseConfig", autospec=True, return_value=None), \
             patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpLogFiles()

        job._CleanUpLogFiles__exacloudPath = "/opt/app/exacloud"
        job._CleanUpLogFiles__log_file_archive_directory = "/archive/dir"
        job._CleanUpLogFiles__log_file_persist_duration_hrs = 1

        class FakeDB:
            def mGetRequest(self, uuid):
                if uuid == "uuid_none":
                    return None
                if uuid == "uuid_done":
                    return (uuid, "Done")
                if uuid == "fail":
                    raise RuntimeError("db failure")
                return (uuid, "Running")

        with patch("exabox.scheduleJobs.cleanup_log_files.ebGetDefaultDB", return_value=FakeDB()), \
             patch("exabox.scheduleJobs.cleanup_log_files.CleanUpLogFiles.mCleanupExacloudLogArchiveDirectory") as mock_cleanup_archives, \
             patch("exabox.scheduleJobs.cleanup_log_files.CleanUpLogFiles.mArchiveLogDirectories") as mock_archive_dirs, \
             patch("exabox.scheduleJobs.cleanup_log_files.glob.glob") as mock_glob, \
             patch("exabox.scheduleJobs.cleanup_log_files.time.time", return_value=7200.0), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.path.getmtime", side_effect=[0.0, 7199.0]), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.remove") as mock_remove, \
             patch("exabox.scheduleJobs.cleanup_log_files.shutil.copy2") as mock_copy, \
             patch("exabox.scheduleJobs.cleanup_log_files.os.path.exists", return_value=False), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.mkdir") as mock_mkdir, \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogWarn") as mock_warn, \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInfo"):

            mock_glob.side_effect = [
                ["/opt/app/exacloud/log/threads/uuid_none.log"],
                ["/opt/app/exacloud/log/threads/uuid_done.trc"],
                ["/opt/app/exacloud/log/threads/uuid_run.err"],
                ["/opt/app/exacloud/log/threads/fail_uuid.xml"],
                ["/opt/app/exacloud/log/workers/worker.log.1"],
                [],
                [],
                ["/opt/app/exacloud/oeda/requests/file.tar.gz"],
                ["/opt/app/exacloud/oeda/requests.bak/bak.tar.gz"],
            ]

            job.mExecuteJob()

        mock_cleanup_archives.assert_called_once_with("/archive")
        mock_archive_dirs.assert_called_once_with("/archive")
        removed_paths = [call.args[0] for call in mock_remove.call_args_list]
        expected_removed = [
            "/opt/app/exacloud/log/workers/worker.log.1",
            "/opt/app/exacloud/oeda/requests/file.tar.gz",
            "/opt/app/exacloud/oeda/requests.bak/bak.tar.gz",
        ]
        self.assertCountEqual(removed_paths, expected_removed)
        self.assertEqual(mock_copy.call_count, len(expected_removed))
        mock_mkdir.assert_called_once_with("/archive/dir/oeda_requests")
        mock_warn.assert_called()

    def test_mArchiveLogDirectories_archives_payload(self):
        ctx = _ctx_with_config()
        with patch.object(CleanUpLogFiles, "mParseConfig", autospec=True, return_value=None), \
             patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpLogFiles()

        with tempfile.TemporaryDirectory() as temp_dir:
            today_dirname = _today_dir()
            today_dir = os.path.join(temp_dir, today_dirname)
            os.makedirs(today_dir)

            archive_dirname = "2025_01_08"
            archive_dir = os.path.join(temp_dir, archive_dirname)
            os.makedirs(archive_dir)

            worker_log_path = os.path.join(archive_dir, "worker.log")
            with open(worker_log_path, "w", encoding="utf-8") as worker_handle:
                worker_handle.write("worker-data")

            oeda_dir = os.path.join(archive_dir, "oeda_requests")
            os.makedirs(oeda_dir)
            oeda_file_path = os.path.join(oeda_dir, "request.tar.gz")
            with open(oeda_file_path, "w", encoding="utf-8") as oeda_handle:
                oeda_handle.write("oeda-data")

            job._CleanUpLogFiles__log_file_archive_directory = today_dir

            with patch("exabox.scheduleJobs.cleanup_log_files.ebLogWarn"), \
                 patch("exabox.scheduleJobs.cleanup_log_files.ebLogInfo"):
                job.mArchiveLogDirectories(temp_dir)

            tarball_path = os.path.join(archive_dir, f"{archive_dirname}.tgz")
            self.assertTrue(os.path.exists(tarball_path))
            self.assertEqual(os.listdir(archive_dir), [f"{archive_dirname}.tgz"])

            with tarfile.open(tarball_path, "r:gz") as tar_handle:
                archive_members = sorted(tar_handle.getnames())

            self.assertEqual(
                archive_members,
                [
                    "oeda_requests",
                    "oeda_requests/request.tar.gz",
                    "worker.log",
                ],
            )

    def test_mArchiveLogDirectories_skips_when_tarball_is_only_entry(self):
        ctx = _ctx_with_config()
        with patch.object(CleanUpLogFiles, "mParseConfig", autospec=True, return_value=None), \
             patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpLogFiles()

        with tempfile.TemporaryDirectory() as temp_dir:
            today_dir = os.path.join(temp_dir, _today_dir())
            os.makedirs(today_dir)

            archive_dirname = "2025_01_08"
            archive_dir = os.path.join(temp_dir, archive_dirname)
            os.makedirs(archive_dir)
            tarball_path = os.path.join(archive_dir, f"{archive_dirname}.tgz")
            with open(tarball_path, "w", encoding="utf-8") as tarball_handle:
                tarball_handle.write("existing archive")

            job._CleanUpLogFiles__log_file_archive_directory = today_dir

            with patch("exabox.scheduleJobs.cleanup_log_files.tarfile.open") as mock_tar_open, \
                 patch("exabox.scheduleJobs.cleanup_log_files.ebLogWarn"), \
                 patch("exabox.scheduleJobs.cleanup_log_files.ebLogInfo"):
                job.mArchiveLogDirectories(temp_dir)

            mock_tar_open.assert_not_called()
            self.assertTrue(os.path.exists(tarball_path))

    def test_mArchiveLogDirectories_removes_failed_tarball(self):
        ctx = _ctx_with_config()
        with patch.object(CleanUpLogFiles, "mParseConfig", autospec=True, return_value=None), \
             patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpLogFiles()

        with tempfile.TemporaryDirectory() as temp_dir:
            today_dir = os.path.join(temp_dir, _today_dir())
            os.makedirs(today_dir)

            archive_dirname = "2025_01_08"
            archive_dir = os.path.join(temp_dir, archive_dirname)
            os.makedirs(archive_dir)
            worker_log_path = os.path.join(archive_dir, "worker.log")
            with open(worker_log_path, "w", encoding="utf-8") as worker_handle:
                worker_handle.write("worker-data")

            job._CleanUpLogFiles__log_file_archive_directory = today_dir

            class FailingTar:
                def __enter__(self):
                    tarball_path = os.path.join(archive_dir, f"{archive_dirname}.tgz")
                    with open(tarball_path, "w", encoding="utf-8") as tarball_handle:
                        tarball_handle.write("partial archive")
                    raise RuntimeError("tar failure")

                def __exit__(self, exc_type, exc, traceback_arg):
                    return False

            with patch("exabox.scheduleJobs.cleanup_log_files.tarfile.open", return_value=FailingTar()), \
                 patch("exabox.scheduleJobs.cleanup_log_files.ebLogError") as mock_error:
                job.mArchiveLogDirectories(temp_dir)

            tarball_path = os.path.join(archive_dir, f"{archive_dirname}.tgz")
            self.assertFalse(os.path.exists(tarball_path))
            self.assertTrue(os.path.exists(worker_log_path))
            mock_error.assert_called()

    def test_mArchiveLogDirectories_removes_leftover_payload_when_tarball_is_valid(self):
        ctx = _ctx_with_config()
        with patch.object(CleanUpLogFiles, "mParseConfig", autospec=True, return_value=None), \
             patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpLogFiles()

        with tempfile.TemporaryDirectory() as temp_dir:
            today_dir = os.path.join(temp_dir, _today_dir())
            os.makedirs(today_dir)

            archive_dirname = "2025_01_08"
            archive_dir = os.path.join(temp_dir, archive_dirname)
            os.makedirs(archive_dir)
            worker_log_path = os.path.join(archive_dir, "worker.log")
            with open(worker_log_path, "w", encoding="utf-8") as worker_handle:
                worker_handle.write("leftover-data")

            tarball_path = os.path.join(archive_dir, f"{archive_dirname}.tgz")
            with tarfile.open(tarball_path, "w:gz") as tar_handle:
                tar_handle.add(worker_log_path, arcname="worker.log")

            job._CleanUpLogFiles__log_file_archive_directory = today_dir

            with patch("exabox.scheduleJobs.cleanup_log_files.ebLogError") as mock_error:
                job.mArchiveLogDirectories(temp_dir)

            self.assertTrue(os.path.exists(tarball_path))
            self.assertFalse(os.path.exists(worker_log_path))
            mock_error.assert_not_called()

            with tarfile.open(tarball_path, "r:gz") as tar_handle:
                self.assertEqual(tar_handle.extractfile("worker.log").read().decode("utf-8"), "leftover-data")

    def test_mArchiveLogDirectories_keeps_completed_tarball_on_cleanup_failure(self):
        ctx = _ctx_with_config()
        with patch.object(CleanUpLogFiles, "mParseConfig", autospec=True, return_value=None), \
             patch("exabox.scheduleJobs.cleanup_log_files.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_log_files.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_log_files.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpLogFiles()

        with tempfile.TemporaryDirectory() as temp_dir:
            today_dir = os.path.join(temp_dir, _today_dir())
            os.makedirs(today_dir)

            archive_dirname = "2025_01_08"
            archive_dir = os.path.join(temp_dir, archive_dirname)
            os.makedirs(archive_dir)
            worker_log_path = os.path.join(archive_dir, "worker.log")
            with open(worker_log_path, "w", encoding="utf-8") as worker_handle:
                worker_handle.write("worker-data")

            job._CleanUpLogFiles__log_file_archive_directory = today_dir

            with patch("exabox.scheduleJobs.cleanup_log_files.os.remove", side_effect=RuntimeError("cleanup failure")), \
                 patch("exabox.scheduleJobs.cleanup_log_files.ebLogError") as mock_error:
                job.mArchiveLogDirectories(temp_dir)

            tarball_path = os.path.join(archive_dir, f"{archive_dirname}.tgz")
            self.assertTrue(os.path.exists(tarball_path))
            self.assertTrue(os.path.exists(worker_log_path))
            mock_error.assert_called()

            with tarfile.open(tarball_path, "r:gz") as tar_handle:
                self.assertEqual(tar_handle.extractfile("worker.log").read().decode("utf-8"), "worker-data")


if __name__ == '__main__':
    unittest.main()
