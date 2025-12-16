"""
 Copyright (c) 2015, 2024, Oracle and/or its affiliates.

NAME:
    Client - Client RESTFull API and CLI support

FUNCTION:
    Client Core functionalities

NOTE:
    None

History:
    aypaul      01/04/2025 - Forward porting changes of bug 36087830 to ECS MAIN.
    aypaul      11/29/2023 - Enh#35730776 Integration of OCI certificate service with exacloud agent.
    ndesanto    11/05/2019 - ENH 30480538: HTTPS and Certificate Rotation
    mirivier    02/09/2015 - Create file
"""

from six.moves.urllib.parse import urlparse
import ast
import http.client
import json
import socket
from six.moves import urllib
from six.moves.urllib.parse import quote_plus, unquote_plus
import base64
from exabox.core.Context import get_gcontext
from exabox.agent.AuthenticationStorage import ebGetHTTPAuthStorage
import time
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogJson
import traceback
import exabox.network.HTTPSHelper as HTTPSHelper

DEFAULT_WORKERCONN_TIMEOUT_SEC = 15
REST_API_MAP = {
    'workerctrl' : {
        'list' : '/wctrl?cmd=list',
        'status' : '/wctrl?cmd=status',
        'start' : '/wctrl?cmd=start',
        'shutdown' : '/wctrl?cmd=shutdown',
        'create' : '/wctrl?cmd=create',
        'destroy' : '/wctrl?cmd=destroy',
        'bounce' : '/wctrl?cmd=bounce',
        'uptime' : '/wctrl?cmd=uptime',
        'info' : '/wctrl?cmd=info',
        'delete' : '/wctrl?cmd=delete',
        'cleanup' : '/wctrl?cmd=cleanup'
    }
}

"""
JSON Response format and fields:
--------------------------------
uuid    : Request Unique Identifier
status  : Done | Pending | Cancelled
statusinfo : True|False:%complete: step - stepinfo
success : True | False
error   : int Code | 0 No Error
error_str : str Explanation string about the error | None No Error
body  : Body containing information about the excution of the request.
start_time: TimeStamp referring to the beginning of the request processing
end_time : TimeStamp referring to the end of the request processing
params : request parameters (if any)
"""

class ebWorkerResponse(object):

    def __init__(self):
        self.__uuid    = '00000000-0000-0000-0000-000000000000'
        self.__status  = 'Undefined'
        self.__statusinfo = 'Undefined'
        self.__starttime = None
        self.__endtime = None
        self.__cmdtype = None
        self.__params  = None
        self.__error   = None
        self.__error_str = None
        self.__body    = None
        self.__success = 'Undefined'
        self.__xml     = None

        self.__response= {}

        self.__callback = {
            'uuid' : self.mSetUUID,
            'status' : self.mSetStatus,
            'statusinfo' : self.mSetStatusInfo,
            'success' : self.mSetSuccess,
            'start_time' : self.mSetTimeStampStart,
            'end_time' : self.mSetTimeStampEnd,
            'cmd' : self.mSetCmdType,
            'error' : self.mSetError,
            'error_str' : self.mSetErrorStr,
            'body' : self.mSetBody
        }

    def mPopulate(self, aKey, aValue):

        if aKey in self.__callback.keys():
            self.__callback[aKey](aValue)

    def mToJson(self,):

        _response = self.__response

        _response['uuid'] = self.mGetUUID()
        _response['status'] = self.mGetStatus()
        _response['statusinfo'] = self.mGetStatusInfo()
        _response['success'] = self.mGetSuccess()
        if self.__starttime:
            _response['start_time'] = self.mGetTimeStampStart()
        if self.__endtime:
            _response['end_time'] = self.mGetTimeStampEnd()
        if self.__error:
            _response['error'] = self.mGetError()
        if self.__error_str:
            _response['error_str'] = self.mGetErrorStr()
        _response['cmd'] = self.mGetCmdType()
        if self.__params:
            _response['params'] = self.mGetParams()
        if self.__body:
            _response['body'] = self.mGetBody()
        if self.__xml:
            _response['xml'] = self.mGetXml()

        return json.dumps(_response, indent=4, separators=(',',': '))

    def mGetXml(self):
        return self.__xml

    def mSetXml(self, aValue):
        self.__xml = aValue

    def mGetSuccess(self):
        return self.__success

    def mSetSuccess(self, aSuccess):
        self.__success = aSuccess

    def mGetStatus(self):
        return self.__status

    def mSetStatus(self, aStatus):
        self.__status = aStatus

    def mGetStatusInfo(self):
        return self.__statusinfo

    def mSetStatusInfo(self, aStatusInfo):
        self.__statusinfo = aStatusInfo

    def mGetUUID(self):
        return self.__uuid

    def mSetUUID(self, aUUID):
        self.__uuid = aUUID

    def mSetTimeStampStart(self,aValue):
        self.__starttime = aValue

    def mGetTimeStampStart(self):
        return self.__starttime

    def mGetTimeStampEnd(self):
        return self.__endtime

    def mSetTimeStampEnd(self,aValue):
        self.__endtime = aValue

    def mGetCmdType(self):
        return self.__cmdtype

    def mSetCmdType(self, aCmdType):
        self.__cmdtype = aCmdType

    def mGetParams(self):
        return self.__params

    def mSetParams(self, aParams):
        self.__params = aParams

    def mGetError(self):
        return self.__error

    def mSetError(self, aError):
        self.__error = aError

    def mGetErrorStr(self):
        return self.__error_str

    def mSetErrorStr(self, aErrorStr):
        self.__error_str = aErrorStr

    def mGetBody(self):
        return self.__body

    def mSetBody(self, aBody):
        self.__body = aBody

class ebWorkerCmd(object):

    def __init__(self, aCmd=None, aPort=None):

        self.__options = get_gcontext().mGetArgsOptions()
        self.__config_opts = get_gcontext().mGetConfigOptions()

        self.__authkey = ebGetHTTPAuthStorage().mGetAdminCredentialForRequest()

        self.__port = 0
        if self.__options.worker_port and not aPort:
            self.__port = int(self.__options.worker_port)
        elif aPort:
            self.__port = int(aPort)
        assert(self.__port)

        self.__hostname = 'localhost'
        self.__request  = None
        self.__response = ebWorkerResponse()
        self.__jsonresponse = None

        if "use_ocicerts_https" in list(self.__config_opts.keys()):
            if isinstance(self.__config_opts["use_ocicerts_https"], str):
                _mode = self.__config_opts["use_ocicerts_https"].lower() == "true"
                if _mode:
                    self.__hostname = socket.getfqdn()

        if not aCmd:
            self.__cmdtype = self.__options.worker_cmd
        else:
            self.__cmdtype = aCmd

        self.__worker_connection_timeout = DEFAULT_WORKERCONN_TIMEOUT_SEC
        if 'worker_connection_timeout' in self.__config_opts.keys():
            self.__worker_connection_timeout = int(self.__config_opts['worker_connection_timeout'])

    def mBuildErrorResponse(self, aErrorCode, aErrorStr, aBody):
        self.__response.mSetCmdType(self.__cmdtype)
        self.__response.mSetStatus('Unavailable')
        self.__response.mSetStatusInfo('statusinfo not available')
        self.__response.mSetSuccess('False')
        self.__response.mSetError(aErrorCode)
        self.__response.mSetErrorStr(aErrorStr)
        self.__response.mSetBody(aBody)
        self.__response.mSetXml(None)

    def mBuildResponse(self, aJson):

        _json = aJson
        for k in _json.keys():
            self.__response.mPopulate(k, _json[k])

    def mBuildRequest(self, aPath):
        # Note: No trailing / required before path
        if HTTPSHelper.is_https_enabled():
            self.__request = 'https://'+self.__hostname+':'+str(self.__port)+aPath
        else:
            self.__request = 'http://'+self.__hostname+':'+str(self.__port)+aPath

    def mPerformRequest(self):

        _data = None
        _error = None
        _error_str = None

        # Issue Request
        _retry = 0
        while _retry < 5:
            try:
                headers = {}
                headers["authorization"] = "Basic {}".format(self.__authkey)
                _response = HTTPSHelper.build_opener(\
                    self.__hostname, self.__port, 
                    self.__request, aHeaders=headers, aTimeout=self.__worker_connection_timeout)
                _data = _response.read()
                break
            except urllib.error.HTTPError as e:
                _error = '120'
                _error_str = str(e)
                break
            except urllib.error.URLError as e:
                ebLogWarn(str(e))
                _retry += 1
                if _retry == 5:
                    _error = '121'
                    _error_str = str(e)
                    break
                else:
                    time.sleep(2)
            except socket.error as e:
                ebLogWarn(str(e))
                _retry += 1
                if _retry == 5:
                    raise
            except http.client.BadStatusLine as e:
                _error = '122'
                _error_str = "http.client.BadStatusLine: " + str(e)
                break
            except Exception as e:
                _error = '123'
                _error_str = str(e)
                break


        # Process Reply
        if not _error:
            try:
                _json = json.loads(_data)
                self.mBuildResponse(_json)
                self.__jsonresponse = self.__response.mToJson()
            except Exception as e:
                _error = '122'
                _error_str = str(e)
                self.mBuildErrorResponse(_error, _error_str, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
        else:
            self.mBuildErrorResponse(_error, _error_str, 'None')
            self.__jsonresponse = self.__response.mToJson()
            ebLogError(self.__jsonresponse)

    def mIssueRequest(self):

        if not self.__cmdtype in REST_API_MAP['workerctrl']:
            self.mBuildErrorResponse('100', 'Invalid or unsupported workerctrl command: '+str(self.__cmdtype), 'None')
            self.__jsonresponse = self.__response.mToJson()
            ebLogError(self.__jsonresponse)
            return

        self.__response.mSetCmdType(self.__cmdtype)
        _path = REST_API_MAP['workerctrl'][self.__cmdtype]
        self.mBuildRequest(_path)
        self.mPerformRequest()

    def mWaitForCompletion(self):

        if not self.__response:
            ebLogError('Response not found in ::mWaitForCompletion')

        if self.__response.mGetSuccess() != 'True':
            ebLogError('Request was NOT successful ::mWaitForCompletion')
            if False:
                ebLogError(self.__response.mToJson())
                ebLogJson(self.__response.mToJson())

        return ast.literal_eval(self.__response.mToJson())

