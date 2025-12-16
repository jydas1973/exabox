#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_cleanup_log_files.py /main/4 2025/09/01 07:15:02 aararora Exp $
#
# tests_cleanup_log_files.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cleanup_log_files.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    08/28/25 - Bug 38298135: Enhance exception handling and
#                           logging for cleanup logs scheduler command
#    avimonda    03/14/25 - Bug 37584489 - OC1| FRA3 | ECRA2 SERVER FILESYSTEM
#                /U02 FILLED UP WITH EXACLOUDLOGARCHIVE FILES
#    aararora    09/29/23 - Adding unit test for scheduler job of log files
#                           cleanup
#    aararora    09/29/23 - Creation
#

import unittest
import copy
import tempfile
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from unittest.mock import patch, call
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.scheduleJobs.cleanup_log_files import CleanUpLogFiles
from datetime import datetime, timedelta
from exabox.core.Context import get_gcontext

LOG_ARCHIVE="/path/to/exacloud/../exacloudLogArchive"

class ebTestCleanupLogFiles(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCleanupLogFiles, self).setUpClass(True,False)
        self.__age_limit = int(get_gcontext().mGetConfigOptions().get("log_archive_cleanup_age_limit_in_days", "180"))

    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("logging.config.fileConfig")
    @patch("exabox.scheduleJobs.cleanup_log_files.CleanUpLogFiles.mParseConfig")
    @patch("os.listdir")
    @patch("os.path.isdir", return_value=True)
    @patch("shutil.rmtree")
    @patch("os.mkdir")
    def test_mExecuteJob(self, _mock_mkdir, _mock_rmtree, _mock_isdir, _mock_listdir, _mock_mParseConfig, _mock_file_config, _mock_options):

        ebLogInfo("")
        ebLogInfo("Running unit test on CleanUpLogFiles.mExecuteJob")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _mock_options.return_value = _options
        _dir1 = (datetime.today() - timedelta(days=self.__age_limit + 1)).strftime('%Y_%m_%d')
        _dir2 = (datetime.today() - timedelta(days=self.__age_limit - 1)).strftime('%Y_%m_%d')
        _mock_listdir.return_value = [_dir1, _dir2, "InvalidPattern"]
        clean = CleanUpLogFiles()
        clean._CleanUpLogFiles__log_file_archive_directory= LOG_ARCHIVE + '/' + datetime.today().strftime('%Y_%m_%d')
        clean.mExecuteJob()
        _mock_rmtree.assert_called_once_with(LOG_ARCHIVE + "/" + _dir1)
        ebLogInfo("Unit test on CleanUpLogFiles.mExecuteJob executed successfully")

    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("logging.config.fileConfig")
    @patch("exabox.scheduleJobs.cleanup_log_files.CleanUpLogFiles.mParseConfig")
    @patch("os.listdir")
    @patch("os.path.isdir", return_value=True)
    @patch("shutil.rmtree")
    @patch("os.mkdir")
    @patch("glob.glob")
    def test_mExecuteJobErrorScenario(self, mock_glob, _mock_mkdir, _mock_rmtree, _mock_isdir, _mock_listdir, _mock_mParseConfig, _mock_file_config, _mock_options):

        ebLogInfo("")
        ebLogInfo("Running unit test on CleanUpLogFiles.mExecuteJob")
        mock_glob.side_effect = [
            ['file1.log', 'file2.log'], # for '*.log*'
            [Exception("File not found")],# for '*.trc*'
            ['error1.err'],               # for '*.err*'
            [],                           # for '*.xml*' (no matches)
            ['file1.log', 'file2.log'],   # for '*.log*'
            ['trace1.trc'],               # for '*.trc*'
            ['error1.err'],               # for '*.err*'
            ['error1.tar.gz'],            # for '*.tar.gz'
            []
        ]
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _mock_options.return_value = _options
        _dir1 = (datetime.today() - timedelta(days=self.__age_limit + 1)).strftime('%Y_%m_%d')
        _dir2 = (datetime.today() - timedelta(days=self.__age_limit - 1)).strftime('%Y_%m_%d')
        _mock_listdir.return_value = [_dir1, _dir2, "InvalidPattern"]
        clean = CleanUpLogFiles()
        clean._CleanUpLogFiles__log_file_archive_directory= LOG_ARCHIVE + '/' + datetime.today().strftime('%Y_%m_%d')
        clean.mExecuteJob()
        _mock_rmtree.assert_called_once_with(LOG_ARCHIVE + "/" + _dir1)
        ebLogInfo("Unit test on CleanUpLogFiles.mExecuteJob executed successfully")

    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("logging.config.fileConfig")
    @patch("exabox.scheduleJobs.cleanup_log_files.CleanUpLogFiles.mParseConfig")
    @patch("os.listdir")
    @patch("os.path.isdir", return_value=True)
    @patch("shutil.rmtree")
    def test_mCleanupExacloudLogArchiveDirectory(self, _mock_rmtree, _mock_isdir, _mock_listdir, _mock_mParseConfig, _mock_file_config, _mock_options):

        ebLogInfo("")
        ebLogInfo("Running unit test on CleanUpLogFiles.mCleanupExacloudLogArchiveDirectory")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _mock_options.return_value = _options
        _dir1 = (datetime.today() - timedelta(days=self.__age_limit + 15)).strftime('%Y_%m_%d')
        _dir2 = (datetime.today() - timedelta(days=self.__age_limit + 20)).strftime('%Y_%m_%d')
        _dir3 = (datetime.today() - timedelta(days=self.__age_limit - 1)).strftime('%Y_%m_%d')
        _mock_listdir.return_value = [_dir1, _dir2, _dir3, "InvalidPattern"]
        clean = CleanUpLogFiles()
        clean.mCleanupExacloudLogArchiveDirectory(LOG_ARCHIVE)
        _mock_rmtree.assert_has_calls([call(LOG_ARCHIVE + "/" + _dir1), call(LOG_ARCHIVE + "/" + _dir2)])
        ebLogInfo("Unit test on CleanUpLogFiles.mCleanupExacloudLogArchiveDirectory executed successfully")

    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("logging.config.fileConfig")
    @patch("exabox.scheduleJobs.cleanup_log_files.CleanUpLogFiles.mParseConfig")
    def test_mIsOldDir(self, _mock_mParseConfig, _mock_file_config, _mock_options):

        ebLogInfo("")
        ebLogInfo("Running unit test on CleanUpLogFiles.mIsOldDir")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _mock_options.return_value = _options
        clean = CleanUpLogFiles()
        _dir_lists = [("2024_01_01", True), (datetime.today().strftime('%Y_%m_%d'), False), ((datetime.today() - timedelta(days=self.__age_limit + 1)).strftime('%Y_%m_%d'), True), ((datetime.today() - timedelta(days=self.__age_limit - 1)).strftime('%Y_%m_%d'), False)]
        for _dir_name, _results in _dir_lists:
            with self.subTest(dir_name=_dir_name):
                self.assertEqual(clean.mIsOldDir(_dir_name), _results)
        ebLogInfo("Unit test on CleanUpLogFiles.mIsOldDir executed successfully")

if __name__ == '__main__':
    unittest.main()
