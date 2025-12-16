#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/managment/src/apiv2/AsyncTrackEndpointCps.py /main/4 2022/10/07 10:56:43 hgaldame Exp $
#
# AsyncTrackEndpointCps.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      AsyncTrackEndpointCps.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    09/30/22 - 34627398 - exacc:bb:22.3.1:cps-sw upgrade: provide
#                           proper error code for precheck failure instead of
#                           returning generic error
#    hgaldame    05/15/22 - 34172836 - oci/exacc: check exacloud remote manager 
#                           async request status on remote cps
#    hgaldame    05/06/22 - 34146854 - oci/exacc: persists exacloud remote ec
#                           async request status
#    hgaldame    04/06/22 - 33643036 - remote ec to return text as json object
#                           in case of success & failure
#    hgaldame    04/06/22 - Creation
#

import os
import sys
import json
import time
import uuid
import subprocess
import urllib
import socket
import traceback
import exabox.network.HTTPSHelper as HTTPSHelper
import exabox.managment.src.utils.CpsExaccUtils as utils

from datetime import datetime
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.BaseServer.BaseEndpoint import BaseEndpoint
from exabox.BaseServer.AsyncProcessing import ProcessStructure
from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint
from exabox.core.DBStore import ebGetDefaultDB

class AsyncTrackEndpointCps(AsyncTrackEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        #Initialization of the base class
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

    def mGet(self):
        _pruid = None
        if self.mGetUrlArgs() is not None:
            if "id" in list(self.mGetUrlArgs().keys()):
                _pruid = self.mGetUrlArgs()['id']
        _limitRetry = 0
        if self.mGetUrlArgs() is not None:
            if "limit_retry" in list(self.mGetUrlArgs().keys()):
                _limitRetry = self.mGetUrlArgs()['limit_retry']
        self.mGetResponse()['text'] = []
        if _pruid:
            _processFiltered = self.mGetSharedData().mGetProcess(_pruid)
            if _processFiltered:
                 self.mGetResponse()['text'] = self.__mGetResponseFromProcess(_processFiltered)
            else:
                    # Failover DB
                    _process = self.__mGetResponseFromDb(_pruid)
                    if _process:
                        self.mGetResponse()['text'] = _process 
                    else:
                        # Check on remote cps host for uuid
                        _remoteCpsResponse = self.mGetStatusFromRemoteCps(_pruid, ALimitRetry = _limitRetry)
                        if _remoteCpsResponse:
                            self.mGetResponse()['text']   = _remoteCpsResponse["text"]
                            self.mGetResponse()['status'] = _remoteCpsResponse["http_status"]
                            self.mGetResponse()['error']  = _remoteCpsResponse["error"]
                        else:
                            self.mGetResponse()['status'] = 404
                            self.mGetResponse()['error']  = "Process id {0} does not exist".format(_pruid)
                            self.mGetResponse()['text']   = self.mBuildGenericErrorResponse(_pruid)
        else:
            for _process in self.mGetSharedData().mGetProcessList():
                _processDict = self.__mGetResponseFromProcess(_process)
                self.mGetResponse()['text'].append(_processDict)
        return

    def mBuildGenericErrorResponse(self, aPruid, aReturnCode=1, aProcName=""):
        _current_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S+%f')
        _processDict = {}
        _processDict["id"]         = aPruid
        _processDict["rc"]         = aReturnCode
        _processDict["name"]       = aProcName
        _processDict["alive"]      = False
        _processDict["log_file"]   = ""
        _processDict["time_start"] = _current_time
        _processDict["time_end"]   = _current_time
        return _processDict

    def __mGetResponseFromProcess(self, aProcess):
        _processDict = {}
        _processDict["id"]         = aProcess.mGetId()
        _processDict["rc"]         = aProcess.mGetReturn()
        _processDict["name"]       = aProcess.mGetName()
        _processDict["alive"]      = aProcess.is_alive()
        _processDict["log_file"]   = aProcess.mGetLogFile()
        _processDict["time_start"] = aProcess.mGetStartTime()
        if _processDict['alive']:
            _processDict["time_end"] = None
        else:
            _processDict["time_end"] = aProcess.mGetEndTime()
        utils.get_cps_return_code(aProcess.mGetReturn(), _processDict, aProcess.is_alive() )
        return _processDict

    def __mGetResponseFromDb(self, aPruid):
        _db = ebGetDefaultDB()
        _processDict = {}
        _rowdb = _db.mGetAsyncProcessById(aPruid)
        if _rowdb:
            _tmpjson = None
            try:
                _tmpjson = json.loads(_rowdb[1])
            except Exception:
                _tmpjson =_rowdb[1]
            _processDict["id"]         = _rowdb[0]
            _processDict["rc"]         = _tmpjson
            utils.get_cps_return_code(_processDict["rc"], _processDict)
            _processDict["name"]       = _rowdb[2]
            _processDict["alive"]      = bool(_rowdb[3])
            _processDict["log_file"]   = _rowdb[4]
            _processDict["time_start"] = _rowdb[5]
            _processDict["time_end"]   = _rowdb[6]
            # Process could not update status
            if _processDict['alive']:
                _current_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S+%f')
                _processDict['alive'] = False
                _processDict["rc"] = _tmpjson if _tmpjson else 1
                _processDict["time_end"] = _current_time
                _db.mUpsertAsyncProcess(_processDict)
        return _processDict

    def mGetStatusFromRemoteCps(self, aPruid, ALimitRetry=0):
        """
        Check status uuid on remote cps

        Args:
            aPruid (string): uuid request to check
            ALimitRetry (int, optional): Limit for avoid cyclic requests between cps. Defaults to 0.

        Returns:
            json: json dictionary with the details of the requests. Defaults to None 
        """
        _remoteHost = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
        _reponse_json = None
        if _remoteHost and ALimitRetry==0:
            _ecauthkey = self.mGetConfig().mGetConfigValue("auth").mGetAdminCredentialForRequest()
            _ecport = self.mGetConfig().mGetConfigValue("port")
            _path = "managment/v2/async"
            # Check once https is enabled on exacc, may different exacloud certs between cps hosts
            if HTTPSHelper.is_https_enabled():
                _request = "https://{0}:{1}/{2}?id={3}&&limit_retry=1".format(_remoteHost, _ecport, _path , aPruid)
            else:
                _request = "http://{0}:{1}/{2}?id={3}&&limit_retry=1".format(_remoteHost, _ecport,_path ,aPruid)
            headers = {}
            headers["authorization"] = "Basic {0}".format(_ecauthkey)            
            _retry = 0
            _maxRetry = 3
            while _retry <= _maxRetry:
                try:
                    _response = HTTPSHelper.build_opener(\
                            _remoteHost, _ecport, 
                            _request,
                            aMethod="GET",
                            aHeaders=headers, aTimeout=5)
                    _reponse_json = json.loads(_response.read())
                    break
                # Network transient failures
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        _errMsg = "Http 404 management. UUID: '{0}' not found in host '{1}'. retry not required".format(aPruid, _remoteHost)
                        self.mGetLog().mWarn(_errMsg)   
                        break
                    _traceBack = traceback.format_exc()
                    _errMsg = "HTTPError management. Trace {0}, retry: {1} of {2}".format(_traceBack, (_retry + 1), _maxRetry)
                    self.mGetLog().mWarn(_errMsg)   
                except socket.error:
                    _traceBack = traceback.format_exc()
                    _errMsg = "Socket.Error management. Trace {0}, retry: {1} of {2}".format(_traceBack, (_retry + 1), _maxRetry )
                    self.mGetLog().mWarn(_errMsg)
                except Exception:
                    _traceBack = traceback.format_exc()
                    _errMsg = "General Exception management. Trace {0}, retry: {1} of {2}".format(_traceBack, (_retry + 1), _maxRetry )
                    self.mGetLog().mWarn(_errMsg)
                _retry += 1
                if _retry == _maxRetry:
                    break
                # Wait 1 sec before retry
                time.sleep(1)
        return _reponse_json

# end of file

