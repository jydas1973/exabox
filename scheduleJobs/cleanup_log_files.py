#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/scheduleJobs/cleanup_log_files.py /main/8 2025/09/19 11:40:33 shapatna Exp $
#
# cleanup_log_files.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cleanup_log_files.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    08/26/25 - Bug 38298135: Enhance exception handling and
#                           logging for cleanup logs scheduler command
#    aararora    04/07/25 - Bug 37779410: Move oeda request archive paths from
#                           oeda request folder to exacloud log archive
#                           directory
#    avimonda    03/12/25 - Bug 37584489: Cleanup exacloud log archive directory
#    aararora    01/10/24 - Bug 35863722: Add xml file for the cluster
#                           operation to the files to be cleaned up in threads
#                           folder.
#    aararora    09/29/23 - Bug 35855520: Move worker and thread logs to
#                           archive
#    aararora    06/30/22 - Add thread logs to target archive list if request
#                           db does not have the request uuid.
#    aypaul      02/23/21 - 32449563 Adding a scheduler job to cleanup old log
#                           files.
#    aypaul      02/23/21 - Creation
#
import glob
import os
import time
import shutil
import traceback
from datetime import date, datetime, timedelta
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.log.LogMgr import ebLogInit, ebLogInfo
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogError
from exabox.core.DBStore import ebGetDefaultDB
from exabox.utils.common import exception_handler_decorator


class CleanUpLogFiles():

    def __init__(self):
        exaBoxCoreInit({})
        self.__ctx = get_gcontext()
        self.__options = self.__ctx.mGetArgsOptions()
        ebLogInit(self.__ctx, self.__options)

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]

        self.__log_file_persist_duration_hrs = 168
        self.__log_file_archive_directory = None
        self.__log_archive_cleanup_age_limit_in_days = 180

        self.mParseConfig()

    def mParseConfig(self):

        _log_file_persist_duration_hrs = int(get_gcontext().mGetConfigOptions().get("log_cleanup_duration", "168"))
        if _log_file_persist_duration_hrs:
            self.__log_file_persist_duration_hrs = _log_file_persist_duration_hrs

        _log_file_archive_directory = get_gcontext().mGetConfigOptions().get("log_file_archive_directory", "")
        if _log_file_archive_directory is not None and _log_file_archive_directory != "":
            if os.path.isabs(_log_file_archive_directory) and os.path.exists(_log_file_archive_directory):
                todays_date = date.today() 
                _dir_name = "{0}_{1}_{2}".format(todays_date.year, todays_date.month, todays_date.day)
                self.__log_file_archive_directory = os.path.join(_log_file_archive_directory,_dir_name)
                if not os.path.exists(self.__log_file_archive_directory):
                    os.mkdir(self.__log_file_archive_directory)
            else:
                ebLogWarn("Log archive directory does not exist: {0}. Older log files will be deleted.".format(_log_file_archive_directory))
        else:
            _relativeLogArchiveDirectory = "../exacloudLogArchive"
            self.__log_file_archive_directory = os.path.join(self.__exacloudPath, _relativeLogArchiveDirectory)
            todays_date = date.today() 
            _dir_name = "{0}_{1}_{2}".format(todays_date.year, todays_date.month, todays_date.day)
            self.__log_file_archive_directory = os.path.join(self.__log_file_archive_directory,_dir_name)
            if not os.path.exists(self.__log_file_archive_directory):
                os.makedirs(self.__log_file_archive_directory)
            ebLogInfo("Archiving old exacloud log files to: {0}".format(self.__log_file_archive_directory))

        _log_archive_cleanup_age_limit_in_days = int(get_gcontext().mGetConfigOptions().get("log_archive_cleanup_age_limit_in_days", "180"))
        if _log_archive_cleanup_age_limit_in_days:
            self.__log_archive_cleanup_age_limit_in_days = _log_archive_cleanup_age_limit_in_days

    def mIsOldDir(self, aLogDir):

        try:
            _dir_date = datetime.strptime(aLogDir, "%Y_%m_%d")
            _cutoff_date = datetime.today() - timedelta(days=self.__log_archive_cleanup_age_limit_in_days)

            return _dir_date < _cutoff_date

        except ValueError:

            return False

    def mCleanupExacloudLogArchiveDirectory(self, aLogBaseArchiveDir):

        for _child_log_dir in os.listdir(aLogBaseArchiveDir):
            if self.mIsOldDir(_child_log_dir):
                _absolute_log_archive_directory = os.path.join(aLogBaseArchiveDir, _child_log_dir)

                if os.path.isdir(_absolute_log_archive_directory):
                    try:
                        ebLogInfo(f"Removing exacloud log archive directory {_absolute_log_archive_directory}")
                        shutil.rmtree(_absolute_log_archive_directory)

                    except Exception as e:
                        ebLogError(f"Error: {e} encountered while removing old exacloud log archive directory {_absolute_log_archive_directory}")
                        ebLogError(traceback.format_exc())

    @exception_handler_decorator
    def mExecuteJob(self):

        aDB=ebGetDefaultDB()

        _exacloud_logthreads_dir = os.path.join(self.__exacloudPath, "log/threads")
        ebLogInfo("Executing CleanUpLogFiles on directory: {0}".format(_exacloud_logthreads_dir))

        # Before executing the cleanup of log files in the directory, first,
        # check if the archive log directory contains any files older than
        # 180 days. If such files exist, remove the log archive directories
        # that are older than 180 days.
        _log_base_archive_directory = os.path.dirname(self.__log_file_archive_directory)
        ebLogInfo(f"First checking and removing archive log directories from {_log_base_archive_directory} older than {self.__log_archive_cleanup_age_limit_in_days} days.")
        self.mCleanupExacloudLogArchiveDirectory(_log_base_archive_directory)

        _move_files = False
        if self.__log_file_archive_directory is not None:
            ebLogInfo("Moving all log files older than {0} hours to {1} directory.".format(self.__log_file_persist_duration_hrs, self.__log_file_archive_directory))
            _move_files = True

        _all_log_files = []
        _log_files_to_remove = []

        # Get list of all matching files in the exacloud/log/threads directory.
        # Below will take care of ad07abb9-152b-4cb8-92d8-916b17436119_cluctrl.createservice.ESTP_PREVM_CHECKS.log.1
        # or ad07abb9-152b-4cb8-92d8-916b17436119_cluctrl.createservice.ESTP_PREVM_CHECKS.log.gz
        # or ad07abb9-152b-4cb8-92d8-916b17436119_cluctrl.createservice.ESTP_PREVM_CHECKS.log
        # xml file for the cluster operation will be copied to the same threads directory as the thread log
        # The xml from threads folder will also be moved to archive along with log file in 7 days
        _log_types = ('*.log*', '*.trc*', '*.err*', '*.xml*') # the tuple of file types
        for _type in _log_types:
            _all_log_files.extend(glob.glob(os.path.join(_exacloud_logthreads_dir, "**", _type), recursive = True))

        for _file in  _all_log_files:
            try:
                _uuid = str(os.path.basename(_file).split("_")[0])
                _resultSet = aDB.mGetRequest(_uuid)
                if (_resultSet is None) or (_resultSet is not None and _resultSet[1] == "Done"):
                    _log_files_to_remove.append(_file)
            except Exception as ex:
                ebLogWarn(f"Error: {ex} encountered while appending log files to remove for {_file}. Continue to process next file.")
                ebLogWarn(traceback.format_exc())

        _current_time = time.time()
        _n_logfiles_removed = 0
        _persist_duration_sec = self.__log_file_persist_duration_hrs * 3600
        for _logfile in _log_files_to_remove:
            try:
                _last_modification_time = os.path.getmtime(_logfile)
                if (_current_time - _last_modification_time) > _persist_duration_sec:
                    _n_logfiles_removed = _n_logfiles_removed + 1
                    if _move_files:
                        shutil.copy2(_logfile, self.__log_file_archive_directory)
                    os.remove(_logfile)
            except Exception as ex:
                ebLogWarn(f"Error: {ex} encountered while moving/deleting log file: {_logfile}. Continue to process next file.")
                ebLogWarn(traceback.format_exc())

        if _move_files:
            ebLogInfo("Moved {0} log files from log/threads folder to {1} directory.".format(_n_logfiles_removed, self.__log_file_archive_directory))
        else:
            ebLogInfo("Removed {0} log files from log/threads folder.".format(_n_logfiles_removed))

        _worker_logs_to_move = []
        # Select worker logs which have been rotated i.e. something like dflt_supervisor.trc.1
        _log_types = ('*.log.*', '*.trc.*', '*.err.*') # the tuple of file types
        _exacloud_workers_dir = os.path.join(self.__exacloudPath, "log/workers")
        for _type in _log_types:
            _worker_logs_to_move.extend(glob.glob(os.path.join(_exacloud_workers_dir, "**", _type), recursive = True))

        for _logfile in _worker_logs_to_move:
            try:
                shutil.copy2(_logfile, self.__log_file_archive_directory)
                os.remove(_logfile)
            except Exception as ex:
                ebLogWarn(f"Error: {ex} encountered while moving worker log file: {_logfile}. Continue to process next file.")
                ebLogWarn(traceback.format_exc())

        ebLogInfo("Moved {0} log files from log/workers folder to {1} directory.".format(len(_worker_logs_to_move), self.__log_file_archive_directory))

        # For oeda request tar.gz folders, we will create a oeda_requests folder under ../exacloudLogArchive folder 
        _oeda_request_archive_directory = os.path.join(self.__log_file_archive_directory, "oeda_requests")
        if not os.path.exists(_oeda_request_archive_directory):
            os.mkdir(_oeda_request_archive_directory)
        _oeda_request_folders_to_move = []
        # Select oeda request folders which have been archived like exaunit_000001_fcdh2323b3b43hb4.tar.gz
        # A comma is necessary below to create a tuple instead of str type.
        _log_types = ('*.tar*',) # the tuple of file types
        _oeda_request_dir = os.path.join(self.__exacloudPath, "oeda/requests")
        _oeda_request_bak_dir = os.path.join(self.__exacloudPath, "oeda/requests.bak")
        for _type in _log_types:
            _oeda_request_folders_to_move.extend(glob.glob(f'{_oeda_request_dir}/{_type}'))
            _oeda_request_folders_to_move.extend(glob.glob(f'{_oeda_request_bak_dir}/{_type}'))

        for _request_folder in _oeda_request_folders_to_move:
            try:
                shutil.copy2(_request_folder, _oeda_request_archive_directory)
                os.remove(_request_folder)
            except Exception as ex:
                ebLogWarn(f"Error: {ex} encountered while moving tar files from oeda/requests folder: {_request_folder}. Continue to process next file.")
                ebLogWarn(traceback.format_exc())

        ebLogInfo("Moved {0} oeda request folders from oeda/requests and oeda/requests.bak folders to {1} directory.".format(len(_oeda_request_folders_to_move), _oeda_request_archive_directory))

        _all_log_files.clear()
        _log_files_to_remove.clear()
        _worker_logs_to_move.clear()
        _oeda_request_folders_to_move.clear()


if __name__ == '__main__':
    clean = CleanUpLogFiles()
    clean.mExecuteJob()
