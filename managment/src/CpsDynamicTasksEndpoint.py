#!/bin/python
#
# $Header: ecs/exacloud/exabox/managment/src/CpsDynamicTasksEndpoint.py /main/4 2023/01/30 10:31:29 hgaldame Exp $
#
# CpsDynamicTasksEndpoint.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      CpsDynamicTasksEndpoint.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    01/25/23 - 35011646 - exacc cps sw/os upgrade v2: : dynamic
#                           tasks/one_off bundle ecra sending incorrect file
#                           name to cps
#                           /opt/oci/exacc/dyntasks/signing/pre_cpssw_ecs_22.3.1.0.0.tgz.tgz
#    hgaldame    08/02/22 - 34457946 - oci/exacc: add new parameter for send
#                           tgz file on dynamic tasks remote manager endpoint
#    hgaldame    07/26/22 - 34352482 - cps sw v2 - make sure that all logs
#                           during sw upgrade goes to the same path at cps
#    hgaldame    06/02/22 - 34237258 - oci/exacc: implement remote manager
#                           endpoint for execute dynamic tasks for cps sw/os
#                           upgrade
#    hgaldame    06/02/22 - Creation
#
from __future__ import print_function
import os
import shutil
import sys
import json
import uuid
import socket
import base64
import shlex
import traceback
from datetime import datetime, timedelta
from exabox.BaseServer.BaseEndpoint import BaseEndpoint
from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint
from exabox.utils.oci_region import load_oci_region_config, get_value
from exabox.config.Config import get_value_from_exabox_config
from typing import List, Optional, Tuple, TextIO
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.managment.src.utils.CpsExaccUtils import mGenerateUUID, mProcessCpsLog
from pathlib import Path

class CpsDynamicTasksEndpoint(AsyncTrackEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)
        self.mSetAsyncLogTag("CPSDYN")

    def mPost(self):
        if self.mGetBody()['op'] == "execute":
            self.mDynamicTaskExecutorHandler()
        elif self.mGetBody()['op'] == "cleanup":
            self.mDynamicTaskCleanupHandler()

        return

    def mGet(self):
        self.mStatusHandler()
        return
 
    def mDynamicTaskCleanupHandler(self):
        _args = ""
        if "args" in self.mGetBody().keys():
            _args =  self.mGetBody()['args']
        _task_name = self.mGetBody()['name']
        _name = "CPS Cleanup Dynamic Task Name: {0} args: [{1}]".format(_task_name, _args)
        self.mGetResponse()["text"] = self.mCreatePythonProcess(self.mAsyncmCleanupDynamicTask, _args, aName=_name)
        return

    def mDynamicTaskExecutorHandler(self):
        _args = ""
        if "args" in self.mGetBody().keys():
            _args =  self.mGetBody()['args']
        _task_name = self.mGetBody()['name']
        _name = "CPS Execute  Dynamic Task Name: {0} args: [{1}]".format(_task_name, _args)
        _uuid = mGenerateUUID()
        _on_finish_args = { "aId": _uuid }
        self.mGetResponse()["text"] = self.mCreatePythonProcess(self.mAsyncmExecuteDynamicTask, _args,\
             aId=_uuid, aOnFinish=self.mProcessCpsLogOnFinish ,aOnFinishArgs=[_on_finish_args], aName=_name)
        return

    def mStatusHandler(self):
        _name = self.mGetUrlArgs()['name']
        _name = Path(_name).stem if _name.endswith(".tgz") is True else _name
        _trace = "n"
        if "trace" in list(self.mGetUrlArgs().keys()):
            _arg_trace = self.mGetUrlArgs()['trace']
            _arg_trace = _arg_trace.strip().lower()
            if _arg_trace in ["y","n"]:
                _trace = _arg_trace
        _tasks_list = []
        _cps_host_list = self.mGetCpsHostList()
        for _cps_host in _cps_host_list: 
            _tasks_list.append(self.mGetStatusFromDynamicTask(_name, _trace, _cps_host))
        self.mGetResponse()['text'] = { _name: _tasks_list }
        return 

    def mAsyncmCleanupDynamicTask(self, aLogFilename, aProcessId, aCustomArgs):
        _task_name = self.mGetBody()['name']
        _task_name = Path(_task_name).stem if _task_name.endswith(".tgz") is True else _task_name
        _base_signing_dir = os.path.join(self.mGetBaseCpsWaInstallDir(), "signing")
        _bundle = os.path.join(self.mGetBaseCpsWaInstallDir(), "bundles", "{0}.tgz".format(_task_name))
        _bundle_payload = os.path.join(_base_signing_dir, "{0}.tgz".format(_task_name))
        _dir_task = os.path.join(self.mGetBaseCpsWaInstallDir(),"exectasks", _task_name)
        return_code = 0
        _cps_host_list = self.mGetCpsHostList()
        with open(aLogFilename, "w+") as _log:
            _cmd_list = []
            _cmd_list.append("/usr/bin/sudo /usr/bin/rm -rf {0}".format(_bundle))
            _cmd_list.append("/usr/bin/sudo /usr/bin/rm -rf {0}".format(_dir_task))
            _cmd_list.append("/usr/bin/sudo /usr/bin/rm -rf {0}".format(_bundle_payload))
            for _cps_host in _cps_host_list:
                for _cmd in _cmd_list:
                    _rc, _sysout, _syserr = self.mExecuteCmdByHost(_cmd, _log, _cps_host)
                if _rc != 0 :
                    _errorMsg = "Error detected on host:'{0}' cmd: '{1}' , rc: '{2}', sysout: '{3}' syserror: '{4}'".format(\
                        _cps_host, _cmd, _rc, _sysout, _syserr)
                    self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
        return return_code

    def mAsyncmExecuteDynamicTask(self, aLogFilename, aProcessId, aCustomArgs):
        _task_name = self.mGetBody()['name']
        _task_name =  Path(_task_name).stem if _task_name.endswith(".tgz") is True else _task_name
        _base_dir = os.path.join(self.mGetBaseCpsWaInstallDir(), "exectasks")
        _base_bundle_dir = os.path.join(self.mGetBaseCpsWaInstallDir(), "bundles")
        _local_tgz = self.mGetBody().get('local', None)
        return_code = 0
        _cps_host_list = self.mGetCpsHostList()
        with open(aLogFilename, "w+") as _log:
            _msg = "Start execution of dynamic task {0} ".format(_task_name)
            self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
            for _cps_host in _cps_host_list:
                for _dir in [_base_dir, _base_bundle_dir]:
                    self.mExecuteCmdByHost("/usr/bin/sudo /usr/bin/mkdir -p {0}".format(_dir),_log, _cps_host)
                _installUser = self.mGetCpsUser()
                _installGroup = self.mGetCpsGroup()
                _ownership = "{0}:{1}".format(_installUser, _installGroup)
                self.mExecuteCmdByHost("/usr/bin/sudo /usr/bin/chown {0} -R {1}".format(_ownership, self.mGetBaseCpsWaInstallDir()),_log, _cps_host)

            _base_bundle_dir = os.path.join(self.mGetBaseCpsWaInstallDir(),"bundles")
            _is_valid_bundle = self.mIsValidBundleFromPayload(_log, aProcessId, _local_tgz, _task_name )
            if not _is_valid_bundle:
                _errorMsg = "Can not process file from payload for taskName {0}".format(_task_name)
                self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
                return 1
            _bundle = os.path.join(_base_bundle_dir, "{0}.tgz".format(_task_name))
            if not self.mFindFileByHost(_bundle, CpsDynamicTasksEndpoint.mGetLocalHostname()):
                _errorMsg = "Expected tgz bundle {0} does not exist on local host {1}".format(_bundle, CpsDynamicTasksEndpoint.mGetLocalHostname())
                self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
                return 1
            # Replicate bundle from local to remote host if any remote cps host
            _remoteHost = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
            if _remoteHost:
                _msg = "Copy {0} to {1}:{0}".format(_bundle, _remoteHost)
                self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
                _result_copy, error_message = self.mSyncFileToRemote(_bundle, _bundle, _remoteHost)
                if not _result_copy:
                    self.mAsyncLog(_log, aProcessId, error_message, aDebug=True)
                    return 1 
            for _cps_host in _cps_host_list:
                return_code = self.mExecuteDynamicTask(_log ,aProcessId, aCustomArgs, _task_name, _cps_host)
                if return_code != 0:
                    return return_code
        return return_code

    def mExecuteDynamicTask(self, aLogFile : TextIO ,aProcessId : str, aCustomArgs : list, aTaskName: str, aCpsHost: str):
        _base_dir = os.path.join(self.mGetBaseCpsWaInstallDir(),"exectasks")
        _base_bundle_dir = os.path.join(self.mGetBaseCpsWaInstallDir(),"bundles")
        _code_sign_key = None
        _dat_file = None
        _dir_task = os.path.join(_base_dir, aTaskName)
        _token = self.mGetConfig().mGetConfigValue("ecra_token")
        _bundle = os.path.join(_base_bundle_dir, "{0}.tgz".format(aTaskName))
        _cmdList = list()
        _rc = 0
        if not self.mFindFileByHost(_bundle, aCpsHost):
            _errorMsg = "Expected bundle '{0}' does not exists on host {1}".format(_bundle, aCpsHost)
            self.mAsyncLog(aLogFile, aProcessId, _errorMsg, aDebug=True)
            return 1
        _msg = "Start execution on host: {0}, tasks name: {1} bundle: {2}".format(aCpsHost, aTaskName, _bundle)
        self.mAsyncLog(aLogFile, aProcessId, _msg , aDebug=True)
        _cmdList.append("/usr/bin/rm -rf {0}".format(_dir_task))
        _cmdList.append("/usr/bin/mkdir -p  {0}".format(_dir_task))
        _cmdList.append("/usr/bin/tar xzf {0} -C {1}".format(_bundle, _dir_task))
        _cmdList.append("/usr/bin/chmod +x {0}/entrypoint.sh".format(_dir_task))
        _cmdList.append("{0}/entrypoint.sh -c {1} {2}".format(_dir_task, _token, aCustomArgs))
        for _cmd in _cmdList:
            _rc, _sysout, _syserr = self.mExecuteCmdByHost(_cmd, aLogFile, aCpsHost)
            if _rc != 0 :
                _errorMsg = "Error detected on host:'{0}' cmd: '{1}' , rc: '{2}', sysout: '{3}' syserror: '{4}'".format(\
                    aCpsHost, _cmd, _rc, _sysout, _syserr)
                self.mAsyncLog(aLogFile, aProcessId, _errorMsg, aDebug=True)
                break
        _msg = "Execution finished on host: {0}, tasks name: {1} return code: {2}".format(aCpsHost, aTaskName, _rc)
        self.mAsyncLog(aLogFile, aProcessId, _msg , aDebug=True)
        return _rc

    def mGetCpsHostList(self) -> List[str]:
        """
        return cps host list. ensures execution first on localhost

        Returns:
            List[str]: cps hostlist
        """
        _arg_host = None
        _remote_host_from_token = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
        if self.mGetBody() and "host" in list(self.mGetBody().keys()):
            _arg_host = self.mGetBody()['host']
            _arg_host = _arg_host.strip().lower()
            _arg_host = None if _arg_host not in ["localhost","remotehost"] else _arg_host
        if _arg_host and _arg_host == "localhost":
            _cps_list = [CpsDynamicTasksEndpoint.mGetLocalHostname()]
        elif _arg_host and _arg_host == "remotehost" and _remote_host_from_token:
            _cps_list = [self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")]
        else:
            _cps_list = [CpsDynamicTasksEndpoint.mGetLocalHostname()]
            if _remote_host_from_token:
                _cps_list.append(_remote_host_from_token)
        return _cps_list

    def mSyncFileToRemote(self, aLocalSrcPath: str, aRemoteTargetPath: str, aCpsHost: str) -> Tuple[bool, Optional[str]]:
        """
        Sync file from localhost to remote host

        Args:
            aLocalSrcPath (str): Source path of local file
            aRemoteTargetPath (str): Target path for remote file
            aCpsHost (str): Target cps host
            aLogFile: Log file instance

        Returns:
            Tuple[bool, Optional[str]]: bool: True if the Sync succeeded , false otherwise
                                        str: error message if any        
        """
        _result_copy = True
        _error_msg = None
        _cmd = "/bin/rsync -avzr {0} {1}:{2}".format(aLocalSrcPath, aCpsHost, aRemoteTargetPath )
        _rc, _sysout, _syserr = self.mBashExecution(shlex.split(_cmd))
        if _rc != 0:
            _result_copy = False 
            _error_msg = "Can not rsync file from localhost file: '{0}' to host: {1}:{2}, sysout:'{3}' , syserr:'{4}'".format(\
            aLocalSrcPath, aCpsHost, aRemoteTargetPath, _sysout, _syserr)
        return (_result_copy, _error_msg)

    def mExecuteCmdByHost(self, aCmdStr : str, aLogFile: TextIO, aCpsHost: str) -> Tuple[int, Optional[str], Optional[str]]:
        """
        Execute a command on specific cps host.

        Args:
            aCmdStr (str): command to execute
            aLogInstance (Log): Log file
            aCpsHost (str): hostname of cps host

        Returns:
            Tuple[int, Optional[str], Optional[str]]: int: return code
                                                      str: sysout if any
                                                      str: syserror if any
        """
        _rc = 0
        _sysout = None
        _syserr = None
        if CpsDynamicTasksEndpoint.mIsLocalHost(aCpsHost):
            try:
                _rc, _sysout, _syserr = self.mBashExecution(shlex.split(aCmdStr),  aRedirect=aLogFile)
            except:
                _rc = 1
                _syserr = traceback.format_exc()
        else:
            _installUser = self.mGetCpsUser()
            _cpsNode = self.mBuildExaboxInstance()
            _cpsNode.mSetUser(_installUser)
            _cpsNode.mConnect(aHost=aCpsHost)
            # default 3600 secs for timeout
            _fin, _fout, _ferr = _cpsNode.mExecuteCmd(aCmdStr, aTimeout=3600)
            _sysout = _fout.readlines()
            _syserr = _ferr.readlines()
            _rc = _cpsNode.mGetCmdExitStatus()
            _cpsNode.mDisconnect()
        return  _rc, _sysout, _syserr

    def mReadFileByHost(self, aFilePath: str, aCpsHost: str) -> Tuple[bool, Optional[str]]:
        """
        Read file from specific cps host
        Args:
            aFilePath (str): path file for read
            aCpsHost (str): hostname of cps host 

        Returns:
            Tuple[bool, Optional[str]]: bool: True if file exists, false otherwise
                                        str : Content of the file
        """
        _is_file_exists = False
        _file_content = None
        if CpsDynamicTasksEndpoint.mIsLocalHost(aCpsHost):
            if os.path.exists(aFilePath):
                _is_file_exists = True
                with open(aFilePath, encoding='utf-8', mode='r') as _file:
                    _file_content = _file.read()
        else:
            _installUser = self.mGetCpsUser()
            _cpsNode = self.mBuildExaboxInstance()
            _cpsNode.mSetUser(_installUser)
            _cpsNode.mConnect(aHost=aCpsHost)
            if _cpsNode.mFileExists(aFilePath):
                _is_file_exists = True
                _file_content = _cpsNode.mReadFile(aFilePath)
            _cpsNode.mDisconnect()
            if _file_content:
                _file_content = _file_content.decode('utf-8')
        return _is_file_exists, _file_content

    def mFindFileByHost(self, aFilePath : str, aCpsHost: str) -> bool:
        """
        Find a file by path on specific cps host

        Args:
            aFilePath (str): File path
            aCpsHost (str): hostname of cps host

        Returns:
            bool: True if file exists, false otherwise
        """
        _is_file_exists = False
        if CpsDynamicTasksEndpoint.mIsLocalHost(aCpsHost) and os.path.exists(aFilePath):
            _is_file_exists = True
        else:
            _installUser = self.mGetCpsUser()
            _cpsNode = self.mBuildExaboxInstance()
            _cpsNode.mSetUser(_installUser)
            _cpsNode.mConnect(aHost=aCpsHost)
            if _cpsNode.mFileExists(aFilePath):
                _is_file_exists = True
            _cpsNode.mDisconnect()
        return _is_file_exists

    def mBuildExaboxInstance(self):
        """
        Get passphrase value for decrypt

        Returns:
            str: passphrase value
        """
        return exaBoxNode(get_gcontext())

    def mGetStatusFromDynamicTask(self, aTaskName: str, aTrace: str, aCpsHost: str) -> dict:
        """
        Get execution status from a Task from specific host

        Args:
            aTaskName (string): Task name
            aTrace (string): if status should include trace log
            aCpsHost (string): hostname of a cps host

        Returns:
            dict: Task status
        """
        _base_dir = os.path.join(self.mGetBaseCpsWaInstallDir(),"exectasks")
        _dir_task = os.path.join(_base_dir, aTaskName)
        _output_json = os.path.join(_dir_task, "output", "run_output.json")
        _trace_log = os.path.join(_dir_task, "trace_log", "trace.log")
        _output_text = None
        _trace_text = "No trace required"
        _is_file_exists, _output_text  = self.mReadFileByHost(_output_json, aCpsHost)
        if _is_file_exists and  _output_text:
            _output_text = json.loads(_output_text)
        else:
            _output_text = "Expected file {0} does not exists".format(_output_json)
        if aTrace in ["y","Y"]:
            _is_file_exists, _trace_text  = self.mReadFileByHost(_trace_log, aCpsHost)
            if not _is_file_exists:
                _trace_text = "Expected file {0} does not exists".format(_trace_log)            
        _status = {
            aCpsHost:{
                "output": _output_text,
                "trace" : _trace_text
                }
            
        }
        return _status


    def mGetBaseCpsWaInstallDir(self)  -> str:
        """
        Calculate the path of install directory where artifacts are located
        by default: "/opt/oci/exacc/dyntasks"
        Returns:
            str: absolute path of install directory
        """
        _base_install_dir = "/opt/oci/exacc"
        _tokenJson, _ = self.mLoadEcraToken()
        if _tokenJson:
            _base_install_dir = _tokenJson["install_dir"]
        _dir_wa_base_dir = os.path.abspath(os.path.join(_base_install_dir, "dyntasks"))
        return _dir_wa_base_dir

    def mGetCpsUser(self)  -> str:
        """
        Get user for cps from ocpsSetup.json ecra token

        Returns:
            str: user for cps , default : "ecra"
        """
        _installUser = "ecra"
        _tokenJson, _ = self.mLoadEcraToken()
        if _tokenJson:
            _installUser = _tokenJson["linux_users"]["installation"]
        return _installUser

    def mGetCpsGroup(self) -> str:
        """
        Get user for cps from ocpsSetup.json  token

        Returns:
            str: group of linux user for cps , default : "dba"
        """
        _installGroup = "dba"
        _tokenJson, _ = self.mLoadEcraToken()
        if _tokenJson:
            _installGroup = _tokenJson["linux_groups"]["installation"]
        return _installGroup


    def mLoadEcraToken(self) -> Tuple[Optional[dict], Optional[str]]:
        """
        Read ocpsSetup.json ecra token defined on the configuration.

        Returns:
            Tuple[Optional[dict], Optional[str]]: dict: json content from file
                                                  str: error string if any
        """
        _token = self.mGetConfig().mGetConfigValue("ecra_token")
        _error_msg = None
        _tokenJson = None
        try:
            with open(_token, "r") as _file:
                _tokenJson = json.load(_file)
        except Exception:
            _error_msg = traceback.format_exc()
        return _tokenJson, _error_msg

    @staticmethod
    def mGetLocalHostname() -> str:
        """
        get localhostname

        Returns:
            str: shortname of local host
        """
        return socket.gethostname().split('.')[0]

    @staticmethod
    def mIsLocalHost(aCpsHost: str)  -> bool:
        """
        Check if a host is localhost

        Args:
            aCpsHost (str): hostname to check

        Returns:
            bool: True if aCpsHost is localhost, false otherwise
        """
        return CpsDynamicTasksEndpoint.mGetLocalHostname() == aCpsHost.split('.')[0]
    
    def mProcessCpsLogOnFinish(self, *args):
        """
          On finish callback for process logs after cps request.
        """
        _logInfoDict = args[0] if len(args) >= 1 else {}
        if not _logInfoDict or not isinstance(_logInfoDict, dict):
            return
        _uuid = _logInfoDict.get("aId", None)
        if not _uuid:
            return
        _log_type = _logInfoDict.get("aLogType", None)
        _target_dir = _logInfoDict.get("aTargetDirName", None)
        _optional_dir = _logInfoDict.get("aOptionalDirDict", None)
        result = mProcessCpsLog(self, _uuid, aLogType=_log_type, aTargetDirName=_target_dir, aOptionalDirDict=_optional_dir)
        return

    def mIsValidBundleFromPayload(self, aLog, aProcessId, aPayloadFile, aTaskName) -> bool:
        _local_tgz = aPayloadFile
        _task_name =  Path(aTaskName).stem if aTaskName.endswith(".tgz") is True else aTaskName
        _base_bundle_dir = os.path.join(self.mGetBaseCpsWaInstallDir(), "bundles")
        _base_signing_dir = os.path.join(self.mGetBaseCpsWaInstallDir(), "signing")
        _bundle_payload = os.path.join(_base_signing_dir, "{0}.tgz".format(_task_name))
        _bundle = os.path.join(_base_bundle_dir, "{0}.tgz".format(_task_name))
        _local_host = CpsDynamicTasksEndpoint.mGetLocalHostname()
        if not os.path.exists(_base_signing_dir):
            self.mExecuteCmdByHost("/usr/bin/sudo -n /usr/bin/mkdir -p {0}".format(_base_signing_dir),
                                   aLog, _local_host)
            _installUser = self.mGetCpsUser()
            _installGroup = self.mGetCpsGroup()
            _ownership = "{0}:{1}".format(_installUser, _installGroup)
            self.mExecuteCmdByHost("/usr/bin/sudo -n /usr/bin/chown {0} -R {1}".format(
                    _ownership, self.mGetBaseCpsWaInstallDir()), aLog, _local_host)

        _result = False
        self.mExecuteCmdByHost("/usr/bin/sudo -n /usr/bin/rm -f {0}".format(_bundle), aLog, _local_host)
        if _local_tgz:
            try:
                self.mExecuteCmdByHost("/usr/bin/sudo -n /usr/bin/rm -rf {0}".format(_bundle_payload), aLog, _local_host)
                _msg = "Writing file from payload on {0}".format(_bundle_payload)
                self.mAsyncLog(aLog, aProcessId, _msg, aDebug=True)
                with open(_bundle_payload, "wb") as _f:
                    _fileC = base64.b64decode(_local_tgz)
                    _f.write(_fileC)
            except Exception as e:
                _errorMsg = "Can not create file {0} on {1}:{2}".format(
                    _bundle_payload,_local_host, traceback.format_exc())
                self.mAsyncLog(aLog, aProcessId, _errorMsg, aDebug=True)
                return _result
            _temp_dir = os.path.join(_base_signing_dir, _task_name)
            _cmdList = []
            _cmdList.append("/usr/bin/rm -rf {0} ".format(_temp_dir))
            _cmdList.append("/usr/bin/mkdir -p {0} ".format(_temp_dir))
            _cmdList.append("/usr/bin/tar xzf {0} -C {1}".format(_bundle_payload, _temp_dir))
            for _cmd in _cmdList:
                _rc, _sysout, _syserr = self.mExecuteCmdByHost(_cmd, aLog, CpsDynamicTasksEndpoint.mGetLocalHostname())
                if _rc != 0:
                    _errorMsg = "Error extracting tgz host:'{0}' cmd: '{1}' , rc: '{2}', sysout: '{3}' syserror: '{4}'".format( \
                        _local_host, _cmd, _rc, _sysout, _syserr)
                    self.mAsyncLog(aLog, aProcessId, _errorMsg, aDebug=True)
                    return _result
            _code_sign_key_path = os.path.join(_temp_dir, "oracle.Java")
            _signature_path = os.path.join(_temp_dir, "{0}.dat".format(_task_name))
            _dyn_task_path = os.path.join(_temp_dir, "{0}.tgz".format(_task_name))

            _code_sign_key_exists = os.path.exists(_code_sign_key_path)
            _signature_exists = os.path.exists(_signature_path)
            _dyn_tasks_exists = os.path.exists(_dyn_task_path)
            if not all([_code_sign_key_exists, _signature_exists, _dyn_tasks_exists]):
                _errorMsg = "Missing Required file on tgz. Existence. [code sign: {0}], [{3}.dat file: {1}] [{3}.tgz file: {2}]".format(
                    _code_sign_key_exists, _signature_exists, _dyn_tasks_exists, _task_name)
                self.mAsyncLog(aLog, aProcessId, _errorMsg, aDebug=True)
                return _result
            else:
                _cmd_verify_sign = "/usr/bin/openssl dgst -sha256 -verify {0} -signature {1} {2}".format(
                    _code_sign_key_path, _signature_path, _dyn_task_path)
                _rc, _sysout, _syserr = self.mExecuteCmdByHost(_cmd_verify_sign, aLog, CpsDynamicTasksEndpoint.mGetLocalHostname())
                if _rc != 0:
                    _errorMsg = "Can not verify digital sign on host: '{0}' cmd: '{1}' , rc: '{2}', sysout: '{3}' syserror: '{4}'".format( \
                        _local_host, _cmd_verify_sign, _rc, _sysout, _syserr)
                    self.mAsyncLog(aLog, aProcessId, _errorMsg, aDebug=True)
                    return _result
                else:
                    self.mAsyncLog(aLog, aProcessId, "digital sign verified on file {0}".format(_bundle_payload), aDebug=True)
                    _cmdList = []
                    _cmdList.append("/usr/bin/mv {0} {1} ".format(_dyn_task_path, _bundle))
                    _cmdList.append("/usr/bin/rm -rf {0} ".format(_temp_dir))
                for _cmd in _cmdList:
                    _rc, _sysout, _syserr = self.mExecuteCmdByHost(_cmd, aLog, _local_host)
                    if _rc != 0:
                        _errorMsg = "Error extracting tgz host:'{0}' cmd: '{1}' , rc: '{2}', sysout: '{3}' syserror: '{4}'".format( \
                            _local_host, _cmd, _rc, _sysout, _syserr)
                        self.mAsyncLog(aLog, aProcessId, _errorMsg, aDebug=True)
                        return _result
                    else:
                        _result = True
        return _result



# end file
