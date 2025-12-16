#!/bin/python
#
# $Header: ecs/exacloud/exabox/managment/src/utils/CpsExaccUtils.py /main/5 2025/09/15 20:32:51 hgaldame Exp $
#
# CpsExaccUtils.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      CpsExaccUtils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    09/11/25 - enh 38036854 - exacc gen 2| infra patching |
#                           enhance ecra remoteec command
#    hgaldame    02/12/25 - 37587401 - oci/exacc: oel 8 migration fails on cps
#                           remote manager endpoint
#    hgaldame    07/20/23 - 35626691 - oci/exacc: remoteec enhancement for
#                           allow to create custom log name
#    hgaldame    09/30/22 - 34627398 - exacc:bb:22.3.1:cps-sw upgrade: provide
#                           proper error code for precheck failure instead of
#                           returning generic error
#    hgaldame    07/26/22 - 34352482 - cps sw v2 - make sure that all logs
#                           during sw upgrade goes to the same path at cps
#    hgaldame    07/26/22 - Creation
#
import re
import os
import sys
import json
import copy
import math
import uuid
import base64
import time
import datetime
import shlex
import subprocess
import glob
import traceback
import socket
import exabox.managment.src.utils.CpsExaccError as error_fwk

from enum import Enum
from pathlib import Path, PurePath
from typing import List, Optional, Tuple, TextIO
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext

class CpsLogType(Enum):
    CPS_DEPLOYER    = "cps_deployer_latest"
    SANITY_TOOL     = "sanity_latest"
    CPS_CHECK_TOOL  = "cps_sw_check_latest"
    REMOTE_MGMT_REQ = "mgmt-log-latest"
    CPS_MIGRATION   = "cpssw-migr-latest"


class CpsResultProcessKeys(Enum):
    TYPE_RESULT   = "type_result"
    ASYNC_ERROR   = "async_error"
    ERROR_CODE    = "error_code"
    ERROR_MESSAGE = "error_message"
    ERROR_DETAIL  = "error_detail"
    RETURN_CODE   = "return_code"

class CpsTypeReturnCode(Enum):
    
    CPS_SW_RETURN_CODE = "CPS_SW_RETURN_CODE"
    
def get_cps_return_code(aReturnCode, aProccesDict, aProcessIsAlive=False):
    if aProcessIsAlive:
        aProccesDict[CpsResultProcessKeys.ASYNC_ERROR.value] = {}
        return
    _success_message = error_fwk.mBuildDefaultSuccessMessage()
    if isinstance(aReturnCode, dict) and CpsResultProcessKeys.TYPE_RESULT.value in aReturnCode and \
        aReturnCode[CpsResultProcessKeys.TYPE_RESULT.value] == CpsTypeReturnCode.CPS_SW_RETURN_CODE.value:
        aProccesDict["rc"]  = aReturnCode.get(CpsResultProcessKeys.RETURN_CODE.value, None) or 1
        if aProccesDict["rc"] is None or aProccesDict["rc"] != 0 :
            _error_tuple = error_fwk.mCpsFormatBuildError(aReturnCode.get(CpsResultProcessKeys.ERROR_CODE.value))
            error_message = {
            CpsResultProcessKeys.ERROR_CODE.value: aReturnCode.get(CpsResultProcessKeys.ERROR_CODE.value,
                                                                   "No information provided"),
            CpsResultProcessKeys.ERROR_MESSAGE.value : _error_tuple.get(CpsResultProcessKeys.ERROR_MESSAGE.value,
                                                                        "No information provided"),
            CpsResultProcessKeys.ERROR_DETAIL.value:  _error_tuple.get(CpsResultProcessKeys.ERROR_DETAIL.value,
                                                                       "No information provided")
            }
            aProccesDict[CpsResultProcessKeys.ASYNC_ERROR.value] = error_message
        else:
            aProccesDict[CpsResultProcessKeys.ASYNC_ERROR.value] = _success_message
    else:
        if isinstance(aReturnCode,int):
            if aReturnCode == 0:
                aProccesDict[CpsResultProcessKeys.ASYNC_ERROR.value] = _success_message
            else:
                aProccesDict[CpsResultProcessKeys.ASYNC_ERROR.value] = error_fwk.mBuildDefaultFailureMessage()
    return


def mBuildProccessResult(aReturnCode, aErrorCode=None):
    _error_str = {}
    if aErrorCode:
        _error_str = error_fwk.mCpsFormatBuildError(aErrorCode)
        process_result = {
            CpsResultProcessKeys.TYPE_RESULT.value : CpsTypeReturnCode.CPS_SW_RETURN_CODE.value,
            CpsResultProcessKeys.RETURN_CODE.value: aReturnCode,
            CpsResultProcessKeys.ERROR_CODE.value : _error_str.get(CpsResultProcessKeys.ERROR_CODE.value,
                                                                   error_fwk.NO_INFO_PROVIDED),
            CpsResultProcessKeys.ERROR_MESSAGE.value : _error_str.get(CpsResultProcessKeys.ERROR_MESSAGE.value,
                                                                      error_fwk.NO_INFO_PROVIDED),
            CpsResultProcessKeys.ERROR_DETAIL.value : _error_str.get(CpsResultProcessKeys.ERROR_DETAIL.value,
                                                                     error_fwk.NO_INFO_PROVIDED)
        }
        return process_result
    return aReturnCode



def mGenerateUUID():
    """
    Generate uuid
    Returns:
        (str): UUID
    """
    return str(uuid.uuid1())


def mProcessCpsLog(aEndpointInstance, aUUID, aLogType=None, aTargetDirName=None, aOptionalDirDict=None, aCustomLogName=None):
    """
    Process logs for remote manager request on cps host.
        It creates a softlink in a  target  location for remote manager request by default.
        Default target location: /opt/oci/exacc/chainsaw/logs/<aTargetDirName>

        For some types of log, is necessary to create an extra symlink for other log. Defined by <aLogType>
    Args:
        aEndpointInstance (AsyncTrackEndpoint): Remote manager Endpoint instance
        aUUID (str) : Remote manager request uuid. By default a symlink is created for remote manager log
        aLogType (CpsLogType) : Optional Enum for define external log location.
        aTargetDirName  (str) : Name of the directory where the symlinks are created. Default cpssw
                                Default parent directory is /opt/oci/exacc/chainsaw/logs/
                                Optional Parent directory can be defined using aOptionalDirDict
        aCustomLogName (str): Optional name if a different log name is provided.
        aOptionalDirDict (dict): Optional dict for define optional directories location.
                                 Only define required entries . Entries
                                 {
                                    "target_parent_dir": (str) Define parent directory of  'aTargetDir' argument.
                                                              Default: /opt/oci/exacc/chainsaw/logs
                                    ,
                                    "CpsLogType" : (CpsLogType) Define the root parent directory for search external logs.
                                  }
    :return: None
    """
    _uuid = aUUID
    _default_install_dir =  "/opt/oci/exacc"
    _installDir = aEndpointInstance.mGetConfig().mGetConfigValue("install_dir")
    _installDir = _installDir or _default_install_dir
    _aTargetDir = aTargetDirName or "cpssw"
    _default_target_parent_dir =  os.path.join(_installDir,"chainsaw","logs")
    aOptionalDirDict = aOptionalDirDict or {}
    _target_parent_dir = aOptionalDirDict.get("target_parent_dir", None) or _default_target_parent_dir
    _aLogType = aLogType
    _dir_target_location = os.path.abspath(os.path.join(_target_parent_dir, _aTargetDir))
    _exa_path = aEndpointInstance.mGetConfig().mGetPath()
    _exa_path = _exa_path[0: _exa_path.find("exabox")]
    _log_file = os.path.abspath("{0}/log/threads/mgnt-{1}.log".format(_exa_path, _uuid))
    if aCustomLogName:
        _log_file = aCustomLogName
    _cmdList = list()
    if os.path.exists(_log_file):
        with open(_log_file, "a") as _log:
            try:
                if not os.path.exists(_dir_target_location):
                    _cmdList.append("/usr/bin/sudo /usr/bin/mkdir -p {0}".format(_dir_target_location))
                _remote_mgmt_log_soft_link = os.path.join(_dir_target_location, CpsLogType.REMOTE_MGMT_REQ.value)
                _cmdList.append("/usr/bin/sudo /usr/bin/ln -sf {0} {1}".format(_log_file, _remote_mgmt_log_soft_link))
                if _aLogType:
                    _parent_dir, reg_expr = mGetInfoByLogType(_installDir, _aLogType, aOptionalDirDict=aOptionalDirDict)
                    if _parent_dir and reg_expr:
                        _ext_log = mGetLastFileCreateFromDir(_parent_dir, reg_expr)
                        if _ext_log and os.path.exists(_ext_log):
                            _external_log_location = os.path.join(_dir_target_location, _aLogType.value)
                            _cmdList.append(
                                "/usr/bin/sudo /usr/bin/ln -sf {0} {1}".format(_ext_log, _external_log_location))
                for _cmd in _cmdList:
                    _rc, _sysOut, _sysError = aEndpointInstance.mBashExecution(shlex.split(_cmd))
                    if _rc !=0:
                        _msg = "Command {0}, fail, sysout: {1} syserr: {2} ".format(_cmd, _sysOut, _sysError)
                        aEndpointInstance.mAsyncLog(_log, _uuid, _msg, aDebug=False)
                        break
            except Exception:
                _msg = "Can not create softlink, trace exception: {0} ".format(traceback.format_exc())
                aEndpointInstance.mAsyncLog(_log, _uuid, _msg, aDebug=False)
    return _cmdList

def mGetLastFileCreateFromDir(root_dir, filter_pattern):
    """
    Calculates the last file created from a directory.
    Filters file names using filter_pattern and sort by mtime
    Not recursive

    Args:
        root_dir (str): root directory of where the log files are located
        filter_pattern (_type_): Regex expression for filter files.

    Returns:
        (str): Last file created which matches with filter if any.
    """
    log_path = None
    def get_mtime_from_file(_aFile):
        if os.path.exists(os.path.join(root_dir, _aFile)):
            return  os.path.getmtime(os.path.join(root_dir, _aFile))
        return None
    if os.path.isdir(root_dir):
        try:
            _root_dir, _, files = next(os.walk(root_dir))
            filter_gen = (_file for _file in files if bool(filter_pattern.search(_file)))
            sorted_file = sorted(filter_gen, key=get_mtime_from_file, reverse=True)
            if sorted_file:
                last = sorted_file[0]
                log_path = os.path.abspath(os.path.join(_root_dir, last))
        except StopIteration:
            pass
    return log_path

def mGetInfoByLogType(aInstallDir, aLogType, aOptionalDirDict=None):
    """
    Get regex and parent directory for search external logs files.
    Args:
        aInstallDir (string): CPS install directory. e.g /opt/oci/exacc
        aLogType (Enum): Log type Enum CpsLogType
        aOptionalDirDict (dict): Optional dict for define optional directories location.
                                 Only define entries required. Entries
                                 {
                                 "CpsLogType" : (CpsLogType) Define the root parent directory for search external
                                                             logs.
                                }
    Returns:
        (str,str): Parent directory of logs.
                   Regex for search log files.
    """
    _sanity_root_dir = "/var/opt/Sanity/"
    _cps_deployer_dir = os.path.join(aInstallDir, "deployer", "ocps-full", "logs")
    _cps_sw_check_dir = os.path.join(aInstallDir, "prechecks", "cps_sw_check", "log")
    if aOptionalDirDict and isinstance(aOptionalDirDict, dict):
        _sanity_root_dir = aOptionalDirDict.get(CpsLogType.SANITY_TOOL, None) or _sanity_root_dir
        _cps_deployer_dir = aOptionalDirDict.get(CpsLogType.CPS_DEPLOYER, None) or _cps_deployer_dir
        _cps_sw_check_dir = aOptionalDirDict.get(CpsLogType.CPS_CHECK_TOOL, None) or _cps_sw_check_dir
    _log_regex_info = {
        CpsLogType.SANITY_TOOL: (_sanity_root_dir, re.compile(r'SANITY_\d{8}_\d{6}.log')),
        CpsLogType.CPS_DEPLOYER:(_cps_deployer_dir, \
            re.compile(r'oci_exacc_dpy_(upgrade|rollingupgrade)_\d{8}_\d{6}.log')),
        CpsLogType.CPS_CHECK_TOOL:(_cps_sw_check_dir, re.compile(r'cps_sw_check.log')),
        "default": (None ,None)
        }
    return  _log_regex_info.get(aLogType, _log_regex_info["default"])


def generate_custom_log_path(aEcConfig, aUuid, aSuffixName=None):
    """
    Generate a full path of a custom log name.
    By default ,it creates log name:
        $EC_HOME/log/threads/mgnt-{aUuid}.log
    if aSuffixName is present,it creates a log name like:
        $EC_HOME/log/threads/mgnt-{_uuid}-{aSuffixName}.log
    Args:
        aEcConfig (config): Exacloud config 
        aUuid (str): UUID for log name
        aSuffixName (str, optional): Postfix for for log name. Defaults to None
    Returns:
       str: custom log path in format: ec_home/log/threads/mgmt-{uuid}-{suffix}.log
    """
    _exapath = aEcConfig.mGetPath()
    _exapath = _exapath[0: _exapath.find("exabox")]
    _path_list = []
    _uuid = aUuid
    _path_list.append(f'{_exapath}/log/threads/mgnt-{_uuid}')
    if aSuffixName:
        _path_list.append(f"-{aSuffixName.lower()}")
    _path_str = "".join(_path_list)
    if not _path_str.endswith(".log"):
        _path_str = f'{_path_str}.log'
    return _path_str

def mGetLocalHostname() -> str:
    _attempts = 1
    while (_attempts <= 3):
        try:
            return socket.gethostname().split('.')[0]                
        except Exception:
            time.sleep(5)
            _attempts += 1

    return None
    
def mSanitizePath(file_path : str) -> str:
    """
    Sanitized path. Fortify checks.
    Only specific paths can be accessed. Avoid access to protected files
    Ensure str is a path like, avoid cmd injection
    """
    sanitized_path=""
    file_path_parts = file_path.split("/")
    white_list_cat = {"u01":"u01","opt":"opt"}
    if len(file_path_parts) > 2:
        white_list_dir = white_list_cat.get(file_path_parts[1], None)
        if  white_list_dir:
            _sub_part_list = [ PurePath(_single_part) for _single_part in file_path_parts][2:]
            sanitized_path = Path((PurePath.joinpath(PurePath("/"), PurePath(white_list_dir), *_sub_part_list))).resolve().as_posix()
    return sanitized_path

def mExecuteCmdByHost(aCpsEnpointInstance, aCmdStr : str, aLogFile: TextIO, aCpsHost: str) -> Tuple[int, Optional[str], Optional[str]]:
    _rc = 0
    _sysout = None
    _syserr = None
    _is_localhost = False
    _is_localhost =  mGetLocalHostname() == aCpsHost.split('.')[0]        
    if _is_localhost:
        try:
            _aRedirect = aLogFile if aLogFile is not None else subprocess.PIPE
            _rc, _sysout, _syserr = aCpsEnpointInstance.mBashExecution(shlex.split(aCmdStr),  aRedirect=_aRedirect)
            _sysout = _sysout.split("\n") if _sysout else _sysout
        except:
            _rc = 1
            _syserr = traceback.format_exc()
    else:
        _installUser = "ecra"
        _cpsNode =  exaBoxNode(get_gcontext())
        _cpsNode.mSetUser(_installUser)
        _cpsNode.mConnect(aHost=aCpsHost)
        _fin, _fout, _ferr = _cpsNode.mExecuteCmd(aCmdStr, aTimeout=3600)
        _sysout = _fout.readlines()
        _syserr = _ferr.readlines()
        _rc = _cpsNode.mGetCmdExitStatus()
        _cpsNode.mDisconnect()
    return  _rc, _sysout, _syserr
