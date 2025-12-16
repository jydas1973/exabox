"""
 Copyright (c) 2017, 2025, Oracle and/or its affiliates.

NAME:
    cleanup_oeda_requests - cleanup oeda requests files

FUNCTION:
    Invoke cleanup routine for oeda requests

NOTE:
    None

"""

import time
import sys
import os
import re
import tarfile
import shutil
import traceback
from datetime import date
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.log.LogMgr import ebLogInit, ebLogInfo, ebLogError, ebLogWarn, ebLogTrace
from exabox.utils.common import exception_handler_decorator


class CleanUpOedaRequests():

    def __init__(self):
        """
            Description:
                Initialize the CleanUpOedaRequests job.

            Args:
                self: The instance of the class being created.

            Returns:
                None
        """
        exaBoxCoreInit({})
        self.__ctx = get_gcontext()
        self.__options = self.__ctx.mGetArgsOptions()
        ebLogInit(self.__ctx, self.__options)

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]

        self.__oeda_request_archive_directory = None

        self.__max_seconds = 0

        self.mParseConfig()

    def mParseConfig(self):
        """
            Description:
                This class method retrieves the maximum number of days for which OEDA requests can be accumulated from exabox.conf. It validates
                the parameter to ensure it is a positive integer and converts it into  seconds for further usage.
            
            Args:
                self: Instance of the class calling this method.
            
            Returns:
                None
        """
        max_days = get_gcontext().mGetConfigOptions().get("schedule_oeda_requests_in_days", "")
        if not max_days:
            ebLogInfo("Missing schedule_oeda_requests_in_days Parameter")
            return
        else:
            if not re.match("[0-9]{1,}$", str(max_days)):
                ebLogInfo("Invalid schedule_oeda_requests_in_days Parameter")
                return
            else:
                self.__max_seconds = (24*60*60) * int(max_days)

    
    def mFetchOedaRequestArchiveDirectory(self):
        """ 
            Description:
                This class method determines and sets up the path where OEDA request archives will be stored.
    
            Args:
                self: Instance of the class calling this method.
            
            Returns:
                None
        """

        # First fetch the path for the exacloudLogArchive Directory from exabox.conf
        _log_file_archive_directory = get_gcontext().mGetConfigOptions().get("log_file_archive_directory", "")
        _is_valid_path_from_exabox = False # By default this flag is False

        # Check if the path actually exists or not
        if _log_file_archive_directory is not None and _log_file_archive_directory != "":
            if os.path.isabs(_log_file_archive_directory) and os.path.exists(_log_file_archive_directory):
                _is_valid_path_from_exabox = True
            else:
                ebLogWarn(f"The log_file_archive_directory: {_log_file_archive_directory} specified from exabox.conf does not exist on the system")
                ebLogWarn("Taking the default path for log_file_archive_directory")
        
        # Create the path if the path fetched from exabox.conf is not a valid one
        if not _is_valid_path_from_exabox:
            _relativeLogArchiveDirectory = "../exacloudLogArchive"
            _log_file_archive_directory = os.path.join(self.__exacloudPath, _relativeLogArchiveDirectory)
            
        _current_date = date.today() 
        _dir_name = f"{_current_date.year}_{_current_date.month}_{_current_date.day}"
        _log_file_archive_directory = os.path.join(_log_file_archive_directory,_dir_name)
        
        if not os.path.exists(_log_file_archive_directory):
            try:
                os.makedirs(_log_file_archive_directory)
            except Exception as exp:
                ebLogError(f"There was a problem encountered while creating the {_log_file_archive_directory} directory: {exp}")
                ebLogError(traceback.format_exc())
                return


        # Next fetch the path of the oeda_request_archive_directory and assign it to the class attribute
        _oeda_request_archive_directory = os.path.join(_log_file_archive_directory, "oeda_requests")

        if not os.path.exists(_oeda_request_archive_directory):
            try:
                os.makedirs(_oeda_request_archive_directory)
            except Exception as exp:
                ebLogError(f"There was a problem encountered while creating the {_oeda_request_archive_directory} directory: {exp}")
                ebLogError(traceback.format_exc())
                return 

        self.__oeda_request_archive_directory = _oeda_request_archive_directory

        ebLogInfo(f"The location of the archive directory for the OEDA requests.bak files/folders is: {self.__oeda_request_archive_directory}")


    def mFetchEntriesInRequestsBakDir(self):
        """
            Description:
                This class method fetches the path for the requests.bak directory, if it exists or creates one if it doesn't and then lists all entries (files and directories) 
                inside it

            Args:
                self: Instance of the class calling this method.

            Returns:
                requests: A list of all entries (files and directories) inside requests.bak

        """
        requests = []
        requests_backup_dir = ""

        # Fetch the path for the requests.bak from exabox.conf
        _requests_backup_path = get_gcontext().mGetConfigOptions().get("oeda_archive_requests_path", "")
        
        # If the path provided is not valid then create one
        if _requests_backup_path == "":
            ebLogInfo(f"Missing oeda_archive_requests_path parameter from exabox.conf. Setting it to default oeda/requests.bak")
            requests_backup_dir = os.path.join(self.__exacloudPath, "oeda/requests.bak")
        else:
            requests_backup_dir = os.path.join(self.__exacloudPath, _requests_backup_path)
            ebLogInfo(f"oeda_archive_requests_path parameter from exabox.conf: {_requests_backup_path}. Backup directory to be checked: {requests_backup_dir}")
        
        # Fetch all the entries inside requests.bak directory, store them inside a list and return it
        try:
            if os.path.exists(requests_backup_dir):
                _directories = os.listdir(requests_backup_dir)
            else:
                _directories = []
            _req_bak_full_paths = [os.path.join(requests_backup_dir,_dir) for _dir in _directories]
            ebLogInfo(f"_req_bak_full_paths = {_req_bak_full_paths}")
            requests.extend(_req_bak_full_paths)
        except Exception as exp:
            ebLogError(f"There was a problem while obtaining oeda requests folders under oeda/requests.bak folder. Exception: {exp}")
            ebLogError(traceback.format_exc())

        return requests


    def mCheckAndMoveOldOedaRequests(self, requests):
        """ 
            Description:
                This class method loops over all entries (files and directories) in oeda/requests.bak and checks their respective creation dates and if that date exceeds the 
                self.__max_seconds, then it is directly moved to the self.__oeda_request_archive_directory (created from the previous methods)

            Args:
                requests: A list of all files and directories inside oeda/requests.bak directory

            Returns:
                None
        """
        for req in requests:
            try:
                reqstat = os.stat(req)

                # Detect old requests and then move them
                delta = time.time() - reqstat.st_mtime
                if delta > self.__max_seconds:
                    _valid_path = os.path.join(self.__oeda_request_archive_directory, os.path.basename(req))

                    # If file/folder with the same name already exists, remove it first
                    if os.path.exists(_valid_path):
                        if os.path.isfile(_valid_path):
                            os.remove(_valid_path)
                        elif os.path.isdir(_valid_path):
                            shutil.rmtree(_valid_path)
                    
                    # Move the new file/folder from the requests.bak dir to the _oeda_request_archive_directory
                    shutil.move(req, self.__oeda_request_archive_directory)
                    ebLogTrace(f"Successfully moved {req} to the {self.__oeda_request_archive_directory}")

            except Exception as exp:
                ebLogWarn(f"Error: {exp} encountered while moving {req} file/folder. Continue to process next file/folder.")
                ebLogWarn(traceback.format_exc())


    @exception_handler_decorator
    def mExecuteJob(self):
        """ 
            Description:
                This class method loops over all entries (files and directories) in oeda/requests.bak and checks their respective creation dates and if that date exceeds the 
                self.__max_seconds, then it is directly moved to the self.__oeda_request_archive_directory (created from the previous methods)

            Args:
                requests: A list of all files and directories inside oeda/requests.bak directory

            Returns:
                None
        """
        ebLogInfo("Calling CleanUpOedaRequests")
        self.mFetchOedaRequestArchiveDirectory()

        if self.__max_seconds == 0:
            ebLogInfo("Skipping CleanUpOedaRequests process since the max_seconds parameter has been configured to be 0 or is unassigned because of an error")
            return
        
        if self.__oeda_request_archive_directory is None:
            ebLogInfo("Skipping CleanUpOedaRequests process since oeda_request_archive_directory cannot be found")
            return

        requests = self.mFetchEntriesInRequestsBakDir()
            
        if requests:
            ebLogInfo("Initiating the process of moving the old oeda_request entries in requests.bak directory...")
            self.mCheckAndMoveOldOedaRequests(requests)
            
        ebLogInfo("Schedule Oeda Requests Done")


if __name__ == '__main__':
    """
        Description:
            Entry point for the execution of this cleanUpOedaRequests job on the scheduler.

        Args:
            None

        Returns:
            None
    """
    clean = CleanUpOedaRequests()
    clean.mExecuteJob()

