#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/scheduleJobs/cleanup_database_log.py /main/1 2021/04/05 03:43:28 gurkasin Exp $
#
# cleanup_database_log.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      cleanup_database_log.py - To cleanup database logs in exacloud/log directory
#
#    DESCRIPTION
#      Runs through exacloud scheduler to clean up database logs
#
#    NOTES
#      Needs database_files_limit and database_age_limit_in_days defined in exacloud config
#
#    MODIFIED   (MM/DD/YY)
#    gurkasin    03/18/21 - Creation
#

import os
import time
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.log.LogMgr import ebLogInit, ebLogInfo


class CleanUpDatabaseLog():

    def __init__(self):
        exaBoxCoreInit({})
        self.__ctx = get_gcontext()
        self.__options = self.__ctx.mGetArgsOptions()
        ebLogInit(self.__ctx, self.__options)

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]

        self.__database_files_limit = 30
        self.__max_age_in_days = 30
        self.__max_age_in_seconds = (24*60*60) * int(self.__max_age_in_days)

        self.mParseConfig()

    def mParseConfig(self):

        #Parse max age
        self.__max_age_in_days = int(get_gcontext().mGetConfigOptions().get("database_age_limit_in_days", ""))
        if not self.__max_age_in_days:
            self.__max_age_in_days = 30
        self.__max_age_in_seconds = (24*60*60) * int(self.__max_age_in_days)

        #Parse max files limit
        self.__database_files_limit = int(get_gcontext().mGetConfigOptions().get("database_files_limit", ""))
        if not self.__database_files_limit:
            self.__database_files_limit = 30

    def mExecuteJob(self):

        _exacloud_log_dir = os.path.join(self.__exacloudPath, "log")
        ebLogInfo("Executing CleanUpDatabaseLog on directory: %s"%(_exacloud_log_dir))
        ebLogInfo("Database file limit is: %d"%(self.__database_files_limit))
        ebLogInfo("Database file age limit is: %d"%(self.__max_age_in_days))

        _database_files = []

        #Get list of all matching files in the exacloud/log directory.
        for _root, _dirs, _files in os.walk(_exacloud_log_dir):
            for _file in _files:
                if (_file.startswith("database_") and not _file.endswith("err")):
                    _database_files.append(os.path.join(_root, _file))

        # Delete files
        _database_files_removed = 0
        if len(_database_files) > 0:
            _database_files.sort(key=os.path.getmtime)
            _database_files_to_remove = 0
            if len(_database_files) > self.__database_files_limit:
                _database_files_to_remove = len(_database_files) - self.__database_files_limit

            for _file in _database_files:
                if _database_files_removed == _database_files_to_remove:
                    break
                os.remove(_file)
                _database_files_removed += 1

            # Update files list by removing deleted files
            _database_files = _database_files[_database_files_removed:]

        # Delete files older than the max age
        for _file in _database_files:
            _filestat = os.stat(_file)
            delta = time.time() - _filestat.st_mtime
            if delta <= self.__max_age_in_seconds:
                # The file list is sorted. All the files remaining will be younger.
                break
            os.remove(_file)
            _database_files_removed += 1


        if _database_files_removed > 0:
            ebLogInfo("Number of database files removed: %d"%(_database_files_removed))
        else:
            ebLogInfo("No matching database files to delete.")


if __name__ == '__main__':
    clean = CleanUpDatabaseLog()
    clean.mExecuteJob()
