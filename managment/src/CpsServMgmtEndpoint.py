#!/bin/python
#
# $Header: ecs/exacloud/exabox/managment/src/CpsServMgmtEndpoint.py /main/1 2025/09/15 20:32:51 hgaldame Exp $
#
# CpsServMgmtEndpoint.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      CpsServMgmtEndpoint.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    08/21/25 - Creation
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
import time
import subprocess
import pathlib

from datetime import datetime, timedelta
from exabox.BaseServer.BaseEndpoint import BaseEndpoint
from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint
from exabox.utils.oci_region import load_oci_region_config, get_value
from exabox.config.Config import get_value_from_exabox_config
from typing import List, Optional, Tuple, TextIO
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.managment.src.utils.CpsExaccUtils import CpsLogType, mGenerateUUID, mProcessCpsLog,\
    mBuildProccessResult, mGetLocalHostname, mSanitizePath, mExecuteCmdByHost, generate_custom_log_path
from pathlib import Path
from enum import Enum

class CpsServiceAction(Enum):
    START_SERVICE   = "start"
    RESTART_SERVICE = "restart"
    STATUS_SERVICE  = "status"
    DEPLOY_SERVICE  = "deploy"
    

class CpsServMgmtEndpoint(AsyncTrackEndpoint):
    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)
        self.mSetAsyncLogTag("CPSSERVMGMT")
        self.__cps_service_list = self.mGetConfig().mGetConfigValue("cps_service_list")
        self.__cps_service_list = self.__cps_service_list if self.__cps_service_list else ["nessusd"]
    
    def mGet(self):
        self.mServiceActionHandler()
        return

    
    def mPost(self):
        if self.mGetBody()['action'] == CpsServiceAction.DEPLOY_SERVICE.value:
            self.mDeployHandler()
        return


    def mServiceActionHandler(self):
        _service_name = self.mGetUrlArgs()['service_name']
        if not _service_name in self.__cps_service_list:
            _error_msg = f'Service {_service_name} not allowed'
            self.mGetResponse()['text']   = "Error, {0}".format(_error_msg)
            self.mGetResponse()['error']  = "Error, {0}".format(_error_msg)
            self.mGetResponse()['status'] = 500
            return
        _action = self.mGetUrlArgs()['op']
        _filter_op = [member.value.lower() for member in CpsServiceAction if member.value.lower() == _action ]
        if not _filter_op:
            _error_msg = f'Operation {_action} not allowed'
            self.mGetResponse()['text']   = "Error, {0}".format(_error_msg)
            self.mGetResponse()['error']  = "Error, {0}".format(_error_msg)
            self.mGetResponse()['status'] = 500
            return
        _action  = _filter_op[0]
        _remoteHost = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
        _remoteHost = _remoteHost.strip() if _remoteHost else None
        _cps_list = [mGetLocalHostname()]
        if _remoteHost:
            _cps_list.append(_remoteHost)
        _cps_dict = {}
        for single_cps in _cps_list:
            _rcLocal_is_primary, _, _ = mExecuteCmdByHost(self, "/usr/bin/sudo -n /usr/bin/ls -l /etc/keepalived/MASTER", None, single_cps)
            if _rcLocal_is_primary == 0:
                cps_node = "MASTER"
            else:
                cps_node = "STANDBY"
            _cmd = f'/usr/bin/sudo -n /usr/bin/systemctl {_action} {_service_name}'
            _rcLocal, _sysOutLocal, _ = mExecuteCmdByHost(self, _cmd, None, single_cps)
            _cps_dict[cps_node] = {"hostname" : single_cps , "return_code": _rcLocal, "service": _service_name, "action": CpsServiceAction.STATUS_SERVICE.value, "output":  _sysOutLocal }
           
        self.mGetResponse()['text']   = _cps_dict
        self.mGetResponse()['status'] = 200
        return 


    def mDeployHandler(self):
        _args = ""
        if "args" in self.mGetBody().keys():
            _args =  self.mGetBody()['args']
        _service_name = self.mGetBody()['name']
        _name = "CPS Execute  Deploy Service name: {0} args: [{1}]".format(_service_name, _args)
        _uuid = mGenerateUUID()
        _custom_log_name = generate_custom_log_path(self.mGetConfig(),
                                                    _uuid, 
                                                    aSuffixName="cpsdpy-deploy-custom")
        _on_finish_args = { "aId": _uuid,"aLogType": CpsLogType.CPS_DEPLOYER,
                           "custom_log_name": _custom_log_name }
        self.mGetResponse()["text"] = self.mCreatePythonProcess(self.mAsyncDeployHandlermDeployHandler, _args,\
             aId=_uuid, aOnFinish=self.mProcessCpsLogOnFinish ,aOnFinishArgs=[_on_finish_args], aName=_name, aLogFile=_custom_log_name)
        return

    def mAsyncDeployHandlermDeployHandler(self, aLogFilename, aProcessId, aCustomArgs):
        _installDir = self.mGetConfig().mGetConfigValue("install_dir")
        _script = "{0}/deployer/ocps-full/cps-exacc-dpy".format(_installDir)
        _token = mSanitizePath(self.mGetConfig().mGetConfigValue("ecra_token"))
        _cmd_deploy = "/usr/bin/sudo -n {0} -t {1} --module scanplatform --step deploy_scanner".format(_script, _token)
        with open(aLogFilename, "w+") as _log:
            _msg = f'Running command {_cmd_deploy}'
            self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
            _rc_deploy, _sysOutUpgrade, _sysErrorUpgrade = self.mBashExecution(shlex.split(_cmd_deploy), aRedirect=_log)
            if _rc_deploy != 0 :
                _errorMsg = "Error running deploy: {3} : return code: {0}, sysout: {1} syserror: {2}".format(\
                    _rc_deploy, _sysOutUpgrade, _sysErrorUpgrade, _cmd_deploy)
                self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
            self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rc_deploy), aDebug=True)
        return mBuildProccessResult(_rc_deploy, aErrorCode=None)



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
        _custom_log_name =_logInfoDict.get("custom_log_name", None)
        mProcessCpsLog(self, _uuid, aLogType=_log_type, aTargetDirName=_target_dir, aOptionalDirDict=_optional_dir, aCustomLogName=_custom_log_name)
        return

 
