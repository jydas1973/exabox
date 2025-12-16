#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/scheduleJobs/cleanup_sshdiag_log.py /main/1 2021/04/05 03:43:28 gurkasin Exp $
#
# cleanup_sshdiag_log.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      cleanup_sshdiag_log.py - To cleanup sshdiag logs in exacloud/log directory
#
#    DESCRIPTION
#      Runs through exacloud scheduler to clean up sshdiag logs in exacloud/log directory
#
#    NOTES
#      Needs sshdiag_age_limit_in_days and sshdiag_files_limit integers defined in exacloud config
#
#    MODIFIED   (MM/DD/YY)
#    gurkasin    03/18/21 - Creation
#
import os
import time
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.log.LogMgr import ebLogInit, ebLogInfo


class CleanUpSshDiagLog():

    def __init__(self):
        exaBoxCoreInit({})
        self.__ctx = get_gcontext()
        self.__options = self.__ctx.mGetArgsOptions()
        ebLogInit(self.__ctx, self.__options)

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]

        self.__sshdiag_files_limit = 30
        self.__max_age_in_days = 30
        self.__max_age_in_seconds = (24*60*60) * int(self.__max_age_in_days)

        self.mParseConfig()

    def mParseConfig(self):

        #Parse max age
        self.__max_age_in_days = int(get_gcontext().mGetConfigOptions().get("sshdiag_age_limit_in_days", ""))
        if not self.__max_age_in_days:
            self.__max_age_in_days = 30
        self.__max_age_in_seconds = (24*60*60) * int(self.__max_age_in_days)

        #Parse max files limit
        self.__sshdiag_files_limit = int(get_gcontext().mGetConfigOptions().get("sshdiag_files_limit", ""))
        if not self.__sshdiag_files_limit:
            self.__sshdiag_files_limit = 30

    def mExecuteJob(self):

        _exacloud_log_dir = os.path.join(self.__exacloudPath, "log")
        ebLogInfo("Executing CleanUpSshDiagLog on directory: %s"%(_exacloud_log_dir))
        ebLogInfo("SSH Diag file limit is: %d"%(self.__sshdiag_files_limit))
        ebLogInfo("SSH Diag file age limit is: %d"%(self.__max_age_in_days))

        _ssh_diag_files = []

        #Get list of all matching files in the exacloud/log directory.
        for _root, _dirs, _files in os.walk(_exacloud_log_dir):
            for _file in _files:
                if _file.startswith("ssh_diag_"):
                    _ssh_diag_files.append(os.path.join(_root, _file))

        # Delete files
        _ssh_diag_files_removed = 0
        if len(_ssh_diag_files) > 0:
            _ssh_diag_files.sort(key=os.path.getmtime)
            _ssh_diag_files_to_remove = 0
            if len(_ssh_diag_files) > self.__sshdiag_files_limit:
                _ssh_diag_files_to_remove = len(_ssh_diag_files) - self.__sshdiag_files_limit

            for _file in _ssh_diag_files:
                if _ssh_diag_files_removed == _ssh_diag_files_to_remove:
                    break
                os.remove(_file)
                _ssh_diag_files_removed += 1

            # Update files list by removing deleted files
            _ssh_diag_files = _ssh_diag_files[_ssh_diag_files_removed:]

        # Delete files older than the max age
        for _file in _ssh_diag_files:
            _filestat = os.stat(_file)
            delta = time.time() - _filestat.st_mtime
            if delta <= self.__max_age_in_seconds:
                # The file list is sorted. All the files remaining will be younger.
                break
            os.remove(_file)
            _ssh_diag_files_removed += 1


        if _ssh_diag_files_removed > 0:
            ebLogInfo("Number of ssh_diag files removed: %d"%(_ssh_diag_files_removed))
        else:
            ebLogInfo("No matching ssh_diag files to delete.")

if __name__ == '__main__':
    clean = CleanUpSshDiagLog()
    clean.mExecuteJob()
