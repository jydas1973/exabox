#!/bin/python
#
# $Header: ecs/exacloud/exabox/sop/sopscripts.py /main/3 2024/07/03 16:41:41 ririgoye Exp $
#
# sopscripts.py
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
#    NAME
#      sopscripts.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    06/25/24 - Enh 36741947 - ADD REMOTE EXECUTION CONFIGURATIONS
#                           TO EXABOX.CONF FOR EXACC
#    ririgoye    05/24/24 - Bug 36400562 - Adding list of corrupted or poorly
#                           formatted files for SOP scripts list endpoint
#    aypaul      01/12/23 - Creation
#
import os
import datetime
import time
import copy
import json
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogTrace, ebLogWarn

LOCAL = "local"
SCRIPT_NAME = "script_name"
SCRIPT_PATH = "script_path"
SCRIPT_PARALLEL_EXEC = "support_parallel_execution"
SCRPIPT_SHA256SUM = "sha256sum"
SCRIPT_EXEC = "script_exec"
SCRIPT_RETURN_JSON_SUPPORT = "return_json_support"
SCRIPT_VERSION = "version"
SCRIPT_COMMENTS = "comments"
LAST_REFRESH_TIME_MARKER = "last_refresh_time"
METADATA_CACHE_MARKER = "metadata_cache"

class SOPScript():

    def __init__(self, aScriptName: str, aScriptPath: str, aParallelExecution = True, aSHA256Sum = None, \
    aScriptExecutable = "/bin/sh", aScriptJSONSupport = False, aScriptVersion = "1", aScriptComments = None) -> None:
        self.__script_name = aScriptName
        self.__script_path = aScriptPath
        self.__script_parallel_execution = aParallelExecution
        self.__script_sha256sum = aSHA256Sum
        self.__script_executable = aScriptExecutable
        self.__script_returnjson_support = aScriptJSONSupport
        self.__script_version = aScriptVersion
        self.__script_comments = aScriptComments

    def mSetScriptName(self, aScriptName: str) -> None:
        self.__script_name = aScriptName

    def mSetScriptPath(self, aScriptPath: str) -> None:
        self.__script_path = aScriptPath

    def mSetScriptParallelExecution(self, aHasParallelSupport: bool) -> None:
        self.__script_parallel_execution = aHasParallelSupport

    def mSetSCriptSHA256Sum(self, aSHA256Sum: str) -> None:
        self.__script_sha256sum = aSHA256Sum

    def mSetScriptExecutable(self, aScriptExecutable: str) -> None:
        self.__script_executable = aScriptExecutable

    def mSetScriptJSONSupport(self, aScriptJSONSupport: bool) -> None:
        self.__script_returnjson_support = aScriptJSONSupport

    def mSetScriptVersion(self, aScriptVersion: str) -> None:
        self.__script_version = aScriptVersion

    def mSetScriptComments(self, aScriptComments: str) -> None:
        self.__script_comments = aScriptComments

    def mGetScriptName(self) -> str:
        return self.__script_name

    def mGetScriptPath(self) -> str:
        return self.__script_path

    def mGetScriptParallelExecution(self) -> bool:
        return self.__script_parallel_execution

    def mGetSCriptSHA256Sum(self) -> str:
        return self.__script_sha256sum

    def mGetScriptExecutable(self) -> str:
        return self.__script_executable

    def mGetScriptJSONSupport(self) -> bool:
        return self.__script_returnjson_support

    def mGetScriptVersion(self) -> str:
        return self.__script_version

    def mGetScriptComments(self) -> str:
        return self.__script_comments


class SOPScriptsRepo():

    def __init__(self) -> None:
        self.__scripts_repo = dict()#str -> SOPScripts
        self.__scripts_metadata_info = dict()#str -> {}
        self.__scripts_storage_type = get_gcontext().mGetConfigOptions()['sop_scripts_storage']
        self.__scriptsrepo_refresh_interval_hrs = int(get_gcontext().mGetConfigOptions()['sop_scripts_refresh_interval'])
        self.__corrupt_files = list() # Adding to enable SOP failure checking when listing scripts
        self.mLoadScriptsMetadata()


    def mGetScriptsRepo(self) -> dict:
        return self.__scripts_repo

    def mGetScriptsMetadata(self) -> dict:
        return self.__scripts_metadata_info

    def mLoadScriptsMetadata(self) -> None:
        if self.__scripts_storage_type == LOCAL:
            self.mLoadLocalScriptsMetadata()

    def mGetCorruptFiles(self) -> list:
        return self.__corrupt_files

    def mLocalParseAndUpdateMetadataCache(self, aScriptsDir: str) -> None:

        _sop_scripts_dir = aScriptsDir
        _all_files = os.listdir(_sop_scripts_dir)
        _complete_metadata_json = dict()

        # Browse directory and populate the metadata JSON
        for _file in _all_files:
            _file_abs_path = os.path.join(_sop_scripts_dir, _file)
            if os.path.isfile(_file_abs_path) and not _file_abs_path.endswith(METADATA_CACHE_MARKER)\
            and not _file_abs_path.endswith(LAST_REFRESH_TIME_MARKER) and not _file_abs_path.endswith(".metadata"):

                _metadata_file = f"{_file_abs_path}.metadata"

                # Parse file, if parsing fails add to corrupt file list
                _file_metadata_json = None

                try:
                    _file_metadata_json = json.load(open(_metadata_file, 'r'))
                except json.JSONDecodeError as e:
                    ebLogError(f"File {_metadata_file} is corrupted or poorly formatted.")
                    self.__corrupt_files.append(_metadata_file)
                    continue

                _file_metadata_json[SCRIPT_NAME] = _file
                _file_metadata_json[SCRIPT_PATH] = _file_abs_path
                _complete_metadata_json[_file] = copy.deepcopy(_file_metadata_json)

        self.mPopulateScriptsRepo(_complete_metadata_json)
        _metadata_lastrefresh_time_marker = os.path.join(_sop_scripts_dir, LAST_REFRESH_TIME_MARKER)
        _scripts_metadata_cache = os.path.join(_sop_scripts_dir, METADATA_CACHE_MARKER)
        if os.path.exists(_scripts_metadata_cache):
            os.remove(_scripts_metadata_cache)
        with open(_scripts_metadata_cache, 'w') as _fd:
            json.dump(_complete_metadata_json, _fd)

        if os.path.exists(_metadata_lastrefresh_time_marker):
            os.remove(_metadata_lastrefresh_time_marker)
        with open(_metadata_lastrefresh_time_marker, 'w') as _fd:
            _fd.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

        self.__scripts_metadata_info = copy.deepcopy(_complete_metadata_json)


    def mPopulateScriptsRepo(self, aMetadataJSON: dict) -> None:

        _complete_metadata_json = aMetadataJSON
        _scripts = list(aMetadataJSON.keys())
        for _script in _scripts:
            _script_name = _script
            _script_path = _complete_metadata_json[_script].get(SCRIPT_PATH, None)
            _script_parallel_execution = _complete_metadata_json[_script].get(SCRIPT_PARALLEL_EXEC, True)
            _script_sha256sum = _complete_metadata_json[_script].get(SCRPIPT_SHA256SUM, None)
            _script_executable = _complete_metadata_json[_script].get(SCRIPT_EXEC, "/bin/sh")
            _script_returnjson_support = _complete_metadata_json[_script].get(SCRIPT_RETURN_JSON_SUPPORT, False)
            _script_version = _complete_metadata_json[_script].get(SCRIPT_VERSION, "1")
            _script_comments = _complete_metadata_json[_script].get(SCRIPT_COMMENTS, "")

            _new_script = SOPScript(_script_name, _script_path, _script_parallel_execution, _script_sha256sum, \
            _script_executable, _script_returnjson_support, _script_version, _script_comments)
            self.__scripts_repo[_script_name] = _new_script


    def mLoadLocalScriptsMetadata(self) -> None:
        # If env is ExaCC, get sop scripts dir from 'sop_scripts_dir_exacc', else do as normal
        _is_exacc = get_gcontext().mCheckConfigOption('ociexacc', 'True')
        _scripts_config_key = 'sop_scripts_dir_exacc' if _is_exacc else 'sop_scripts_dir'
        _scripts_local_dir = get_gcontext().mGetConfigOptions()[_scripts_config_key]

        if _scripts_local_dir is None or not os.path.isabs(_scripts_local_dir) or not os.path.exists(_scripts_local_dir):
            raise ExacloudRuntimeError(0x815, 0xA, f"SOP scripts directory information is invalid: {_scripts_local_dir}.\
             Please provide an existing absolute path to the scripts directory.")

        _metadata_lastrefresh_time_marker = os.path.join(_scripts_local_dir, LAST_REFRESH_TIME_MARKER)
        _scripts_metadata_cache = os.path.join(_scripts_local_dir, METADATA_CACHE_MARKER)
        if not os.path.exists(_metadata_lastrefresh_time_marker) or not os.path.exists(_scripts_metadata_cache):
            self.mLocalParseAndUpdateMetadataCache(_scripts_local_dir)
        else:
            _metadata_lastrefresh_time = None
            with open(_metadata_lastrefresh_time_marker, 'r') as _fd:
                _metadata_lastrefresh_time = _fd.readline().strip()

            _stime = datetime.datetime.strptime(_metadata_lastrefresh_time, '%Y-%m-%d %H:%M:%S.%f')\
             + datetime.timedelta(hours = self.__scriptsrepo_refresh_interval_hrs)
            _nowtime = datetime.datetime.now()
            if _nowtime > _stime:
                self.mLocalParseAndUpdateMetadataCache(_scripts_local_dir)
            else:
                _complete_metadata_json = json.load(open(_scripts_metadata_cache, 'r'))
                self.__scripts_metadata_info = copy.deepcopy(_complete_metadata_json)
                self.mPopulateScriptsRepo(_complete_metadata_json)
