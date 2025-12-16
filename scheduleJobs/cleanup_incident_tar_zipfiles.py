"""
 Copyright (c) 2017, 2023, Oracle and/or its affiliates.

NAME:
    insert_job_cleanup_incident_tar_zipfiles - cleanup configurable number of incident zip files and all tar files.

FUNCTION:
    Invoke cleanup routine for Incident zip and tar archives.

NOTE:
    None

"""

import os
import glob

from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.log.LogMgr import ebLogInit, ebLogInfo, ebLogTrace

from exabox.ovm.cluincident import TFACTL_PREFIX
from exabox.ovm.kvmcpumgr import CPULOG_DIR

class CleanUpIncidentTarAndZipFiles():

    def __init__(self):
        exaBoxCoreInit({})
        self.__ctx = get_gcontext()
        self.__options = self.__ctx.mGetArgsOptions()
        ebLogInit(self.__ctx, self.__options)

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]

        self.__incident_zipfiles_limit = 10
        self.__tfactl_zipfiles_limit = 20
        self.__cpuresize_diagfiles_limit = 20
        self.mParseConfig()

    def mParseConfig(self):

        #Parse max age
        self.__incident_zipfiles_limit = int(get_gcontext().mGetConfigOptions().get("incident_zip_files_limit", ""))
        if not self.__incident_zipfiles_limit:
            self.__incident_zipfiles_limit = 10

        self.__tfactl_zipfiles_limit = int(get_gcontext().mGetConfigOptions().get("tfactl_zip_files_limit", "20"))
        self.__cpuresize_diagfiles_limit = int(get_gcontext().mGetConfigOptions().get("cpuresize_diag_files_limit", "20"))

    def mExecuteJob(self):

        _exacloud_log_dir = os.path.join(self.__exacloudPath, "log")
        ebLogInfo("Executing CleanUpIncidentTarAndZipFiles on directory: %s"%(_exacloud_log_dir))
        ebLogInfo("Incident zip and tar archive file limit is: %d"%(self.__incident_zipfiles_limit))
        ebLogInfo(f"Tfactl zip files limit is {self.__tfactl_zipfiles_limit}")
        ebLogInfo(f"Cpuresize diagnostic files limit is {self.__cpuresize_diagfiles_limit}")

        _tar_files = []
        _zip_files = []
        _tfactl_zip_files = []
        _cpuresize_log_files = []

        _cpuresize_log_files = glob.glob(os.path.join(_exacloud_log_dir, CPULOG_DIR, "*", "*tar*"))

        _tfactl_zip_files = glob.glob(os.path.join(_exacloud_log_dir, "tfactl_logs", f"{TFACTL_PREFIX}*.zip"))

        #Get list of all matching files in the exacloud/log directory.
        _path_exp = _exacloud_log_dir + "/**/*.tar*"
        _tar_files = glob.glob(_path_exp, recursive=True)
        _tar_files = list(filter(lambda x: x not in _cpuresize_log_files and x not in _tfactl_zip_files, _tar_files))

        _path_exp = _exacloud_log_dir + "/**/*.zip"
        _zip_files = glob.glob(_path_exp, recursive=True)
        _zip_files = list(filter(lambda x: x not in _cpuresize_log_files and x not in _tfactl_zip_files, _zip_files))

        _tfactl_files_removed = 0
        if len(_tfactl_zip_files) > 0:
            _tfactl_zip_files.sort(key=os.path.getmtime)
            _tfactl_files_to_remove = 0
            if len(_tfactl_zip_files) > self.__tfactl_zipfiles_limit:
                _tfactl_files_to_remove = len(_tfactl_zip_files) - self.__tfactl_zipfiles_limit

            for _file in _tfactl_zip_files:
                if _tfactl_files_removed == _tfactl_files_to_remove:
                    break
                ebLogTrace(f"Cleaning up tfactl zip file {_file}.")
                os.remove(_file)
                _tfactl_files_removed += 1

        _cpulogfiles_removed = 0
        _cpulogfiles_to_remove = 0
        if len(_cpuresize_log_files) > self.__cpuresize_diagfiles_limit:                                                                                                                                        
            _cpuresize_log_files.sort(key=os.path.getmtime)
            _cpulogfiles_to_remove = len(_cpuresize_log_files) - self.__cpuresize_diagfiles_limit

            for _file in _cpuresize_log_files:
                if _cpulogfiles_removed == _cpulogfiles_to_remove:
                    break
                ebLogTrace(f"Cleaning up cpu log file {_file}.")
                os.remove(_file)
                _cpulogfiles_removed += 1


        _tar_files_removed = 0
        if len(_tar_files) > 0:
            _tar_files.sort(key=os.path.getmtime)
            _tar_files_to_remove = 0
            if len(_tar_files) > self.__incident_zipfiles_limit:
                _tar_files_to_remove = len(_tar_files) - self.__incident_zipfiles_limit

            for _file in _tar_files:
                if _tar_files_removed == _tar_files_to_remove:
                    break
                ebLogTrace(f"Cleaning up tar file {_file}.")
                os.remove(_file)
                _tar_files_removed += 1

        _zip_files_removed = 0
        if len(_zip_files) > 0:
            _zip_files.sort(key=os.path.getmtime)
            _zip_files_to_remove = 0
            if len(_zip_files) > self.__incident_zipfiles_limit:
                _zip_files_to_remove = len(_zip_files) - self.__incident_zipfiles_limit

            for _file in _zip_files:
                if _zip_files_removed == _zip_files_to_remove:
                    break
                ebLogTrace(f"Cleaning up zip file {_file}.")
                os.remove(_file)
                _zip_files_removed += 1
        if _cpulogfiles_removed > 0:
            ebLogInfo("Number of cpuresize logs removed: %d"%(_cpulogfiles_removed))
        if _tfactl_files_removed > 0:
            ebLogInfo("Number of tfactl zip files removed: %d"%(_tfactl_files_removed))
        if _zip_files_removed > 0:
            ebLogInfo("Number of incident zip files removed: %d"%(_zip_files_removed))
        if _tar_files_removed > 0:
            ebLogInfo("Number of incident tar files (.tar, .tar.gz) removed: %d"%(_tar_files_removed))
        if _zip_files_removed == 0 and _tar_files_removed == 0 and _tfactl_files_removed == 0 and _cpulogfiles_removed == 0:
            ebLogInfo("No matching incident files to delete.")


if __name__ == '__main__':
    clean = CleanUpIncidentTarAndZipFiles()
    clean.mExecuteJob()
