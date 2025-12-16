# $Header: ecs/exacloud/exabox/infrapatching/utils/cleanup_infrapatching_logs.py /main/1 2024/05/02 04:53:41 emekala Exp $
#
# cleanup_infrapatching_logs.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      cleanup_infrapatching_logs.py
#
#    DESCRIPTION
#      Script to cleanup in-active folders specified in cleanup config file
#
#    NOTES
#      
#
#    MODIFIED   (MM/DD/YY)
#    emekala     03/14/24 - ENH 35804535 - EXACS: Cleanup of logs and
#                           patchpayloads on the Management Host (launch node)
#                           for EXACS
#    emekala     03/14/24 - Creation
#

import time
import json
import shlex
import os,sys
import logging
import subprocess
from pathlib import Path
from logging.handlers import RotatingFileHandler

file_abs_path = os.path.abspath(__file__)
exacloud_path = file_abs_path[0: file_abs_path.rfind("exacloud")+8]
cleanup_config_file = f"{exacloud_path}/exabox/infrapatching/config/cleanup_infrapatching_logs.conf"
log_folder = f"{exacloud_path}/log"
log_file_name =  "infrapatch_patchmgr_metadata_cleanup.log"
log_file_abs_path = f"{log_folder}/{log_file_name}"
exassh_path = f"{exacloud_path}/bin/exassh"

class CleanupInfrapatchingLogs():
    def __init__(self):
        self.ssh_cmd = None
        self.default_user_name = "root"

        try:
            Path(f"{log_folder}").mkdir(parents=True, exist_ok=True)
        except Exception as _e:
            print(f"Problem while creating log folder: {log_folder} - %s" %(_e))
            sys.exit(1)

        self.logger = logging.getLogger(log_file_name)
        self.logger.setLevel(logging.INFO)

        fileHandler = RotatingFileHandler(log_file_abs_path, mode='a', maxBytes=5000000, backupCount=1,
                                          encoding=None, delay=0)
        fileFormator = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
        fileHandler.setFormatter(fileFormator)
        fileHandler.setLevel(logging.DEBUG)
        self.logger.addHandler(fileHandler)

        print(f"\nLog File: {log_file_abs_path}\n")

    def mValidateCleanupConfigFile(self):
        """
        Method to check cleanup config file existance and validate for json format
        """
        if not os.path.exists(cleanup_config_file):
            self.logger.error(f"Infrapatching cleanup config file: '{cleanup_config_file}' doesn't exists!")
            return 1
        try:
            with open(cleanup_config_file) as _cleanup_config_file:
                json.load(_cleanup_config_file)
                self.logger.info(f"Infrapatching cleanup config file is well-formed json file: '{cleanup_config_file}'")
        except ValueError as _e:
            self.logger.error(f"Infrapatching cleanup config file has invalid json format: '{cleanup_config_file}'!")
            self.logger.error(_e)
            return 1
        return 0

    def mGetSshCmd(self):
        """
        Helper method to prepare the ssh cmd
        """
        if self.ssh_cmd is None:
            self.ssh_cmd = "ssh -T -o StrictHostKeyChecking=no "
            self.ssh_cmd = self.ssh_cmd + f"-o BatchMode=yes -o ConnectTimeout=30 "
            self.ssh_cmd = self.ssh_cmd + "-o ServerAliveInterval=30  "
            self.ssh_cmd = self.ssh_cmd + f"-o ServerAliveCountMax=60"
        return self.ssh_cmd

    def mPrepareCmdForExecution(self, aCmd, aUserName, **kwargs):
        """
        Helper method to check and prepare the given cmd to run via ssh where the cmd must be executed as sudo for non root users
        """
        if aUserName != "root":
            aCmd = f"sudo {aCmd}"
        _hostName = kwargs['hostName']
        # plain ssh based cmd
        #_final_cmd = self.mGetSshCmd() + f" {aUserName}@{_hostName} '{aCmd}'"
        
        # exassh based cmd
        # following cmd excludes banner msgs like WARNING that sometime show up/return as part of remote exassh cmd execution
        #_final_cmd = f"{exassh_path} -sl -u {aUserName} {_hostName} -e '{aCmd}' | grep -v WARNING"
        _final_cmd = f"{exassh_path} -sl -u {aUserName} {_hostName} -e '{aCmd}'"
        
        return _final_cmd

    def mRunCmd(self, aCmd, aUserName, **kwargs):
        """
        Helper method to run cmd 
        """
        # Check and prepare the received cmd as per the cleanup metada list
        _final_cmd_to_run = shlex.split(self.mPrepareCmdForExecution(aCmd=aCmd, aUserName=aUserName, **kwargs))
        try:
            self.logger.info(f"Running the cmd: {_final_cmd_to_run} ...")
            _process = subprocess.run(_final_cmd_to_run, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _std_output = _process.stdout.decode('utf-8').strip()
            return _std_output
        except subprocess.CalledProcessError as _e:
            _std_out = _e.stdout.decode('utf-8').strip()
            if "Key not found" in _std_out:
                self.logger.error(_std_out)
                raise SystemExit
            else:
                _std_error = _e.stderr.decode('utf-8').strip()
                # rm cmd doesn't return anything but with | grep -v WARNING added to exclude some banner msgs 
                # while executing the exassh cmd, subprocess assumes cmd execution failed 
                if _std_error:
                    self.logger.error(_std_error)
                    raise SystemExit
         

    def mGetUserName(self, **kwargs):
        """
        Helper method to check userName in cleanup metada list where userName can be defined or defined with empty value or not defined
        """
        try:
            _userName = kwargs['userName']
            if _userName is None or len(_userName.strip()) == 0:
                _userName = self.default_user_name
                self.logger.warning(f"userName attribute has an empty value in the cleanup metadata list. Default user: {_userName} will be used for remote command execution!")
        except Exception as _e:
            _userName = self.default_user_name
            self.logger.warning(f"userName attribute not defined in the cleanup metadata list. Default user: {_userName} will be used for remote command execution!")
        return _userName

    def mValidateCleanupData(self, **kwargs):
        """
        Method to validate cleanup data and decide whether to ignore or proceed further
        """
        _isValidCleanupData = True
        try:
            _hostName = kwargs['hostName']
            _folderToPurge = kwargs['folderToPurge']
            _isActive = kwargs['isActive']
        except Exception as _e:
            self.logger.warning(f"Mandatory attribute: '{_e}' not defined!")
            _isValidCleanupData = False

        if _isValidCleanupData:
            # Check if this cleanup data is enabled for processing or not
            if _isActive is None or _isActive.upper() != "YES":
                self.logger.warning(f"isActive attribute set to: {_isActive} which is != 'yes'!")
                _isValidCleanupData = False
            else:
                # cleanup data is enabled for processing. Now perform some more validations...
                self.logger.info(f"isActive attribute set to: '{_isActive}'. Proceeding with further validations...")

                # userName is optional. Cherck and get the correct user name for remote cmd execution
                _userName = self.mGetUserName(**kwargs)

                # Make sure hostName attribute has non-empty value
                if _hostName is None or len(_hostName.strip()) == 0:
                    self.logger.warning(f"hostName: {_hostName} must be valid non-empty value for remote cmd execution!")
                    _isValidCleanupData = False

                # Make sure given folderToPurge is not base os system folder
                if _folderToPurge is None or len(_folderToPurge.strip()) == 0 or _folderToPurge == "/" :
                    self.logger.warning(f"Folder to purge: {_folderToPurge} must be valid non-empty value and must not be the os root folder: '/' !")
                    _isValidCleanupData = False

                if _isValidCleanupData:
                    # Make sure given folder to purge exists
                    try:
                        self.logger.info(f"Checking for folder to purge: '{_folderToPurge}' existance...")
                        _cmd = f"ls -l {_folderToPurge}"
                        self.mRunCmd(aCmd=_cmd, aUserName=_userName, **kwargs)
                        self.logger.info(f"Folder to purge: '{_folderToPurge}' exists.")
                    except:
                        _isValidCleanupData = False

        if _isValidCleanupData is False:
            self.logger.warning("Cleanup metadata list ignored!")
        return _isValidCleanupData

    def mRunCleanup(self, **kwargs):
        """
        Method that performs the cleanup
        """
        _marker_file = "*_progress.txt"
        _folderToPurge = kwargs['folderToPurge']
        _userName = self.mGetUserName(**kwargs)
        try:
            # look for active marker file directly in the the given folder to purge. Do not look further in sub-folders. 
            # if marker file not found then exception block gets executed.
            self.logger.info(f"Checking for marker file: {_marker_file} under: '{_folderToPurge}'...")
            _cmd = f"ls -1 {_folderToPurge}/{_marker_file}"
            self.mRunCmd(aCmd=_cmd, aUserName=_userName, **kwargs)
            self.logger.info(f"Marker file: {_marker_file} found under: '{_folderToPurge}'. Patch is in progress hence skipping purging of folder!")
        except:
            # no marker file found hence purge the folder
            self.logger.info(f"Marker file: {_marker_file} not found under: '{_folderToPurge}'. Proceeding to purge the folder: '{_folderToPurge}'...")
            _cmd = f"rm -rf {_folderToPurge}"
            self.mRunCmd(aCmd=_cmd, aUserName=_userName, **kwargs)
            self.logger.info(f"Folder: '{_folderToPurge}' purged!")
        return 0

    def mExecute(self):
        """
        Method that reads cleanup.conf, iterates over nodes and cleanups folders
        """
        _start_time = time.time()
        self.logger.info("")
        self.logger.info("--------------->Cleanup activity started<---------------")
        self.logger.info("")

        _overall_exit_code = 0

        # Make sure cleanup config file is valid
        _overall_exit_code = self.mValidateCleanupConfigFile()
        if _overall_exit_code == 0:
            # Now proceed further 
            _cleanup_config_dict = {}
            with open(cleanup_config_file) as _cleanup_config_file:
                _cleanup_config_dict = json.load(_cleanup_config_file)
            self.logger.info("")
            self.logger.info(f"Infrapatching cleanup config dictionary: {_cleanup_config_dict}")

            for _cleanup_config_list in _cleanup_config_dict.get('cleanupMetadata', []):
                self.logger.info("")
                self.logger.info("")
                self.logger.info(f"--->Validating the cleanup metadata list: {_cleanup_config_list}...")

                # Validate cleanup data before proceeding further
                _isValidCleanupData = self.mValidateCleanupData(**_cleanup_config_list)
                if _isValidCleanupData:
                    # Proceed to cleanup ...
                    self.logger.info("")
                    self.logger.info(f"Proceeding with cleanup...")
                    _cleanup_status_code = self.mRunCleanup(**_cleanup_config_list)
                    if _cleanup_status_code != 0:
                        _overall_exit_code = _cleanup_status_code

        _end_time = time.time()
        _execution_time = round(_end_time - _start_time)
        self.logger.info("")
        self.logger.info("")
        self.logger.info(f"--------------->Cleanup activity took: {_execution_time}secs and completed with exit code: {_overall_exit_code}<---------------")
        return _overall_exit_code

if __name__ == "__main__":
    ret_code = CleanupInfrapatchingLogs().mExecute()
    sys.exit(ret_code)
