"""
 Copyright (c) 2015, 2022, Oracle and/or its affiliates. 

NAME:
    Client - Client RESTFull API and CLI support

FUNCTION:
    Client Core functionalities

NOTE:
    None

History:
    pbellary    18/06/2020 - File Creation
"""

from six.moves.urllib.parse import urlparse
import ast
import json
import socket
from six.moves import urllib
from six.moves.urllib.parse import quote_plus, unquote_plus, urlencode
import base64
from exabox.core.Context import get_gcontext
from exabox.agent.AuthenticationStorage import ebGetHTTPAuthStorage
import time
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogJson
from ast import literal_eval
import traceback
import zlib
from exabox.proxy.ebJobResponse import ebJobResponse
import exabox.network.HTTPSHelper as HTTPSHelper


class ebHttpClient(object):

    def __init__(self):

        self.__options = get_gcontext().mGetArgsOptions()
        self.__config_opts = get_gcontext().mGetConfigOptions()

        self.__request  = None
        self.__response = ebJobResponse()
        self.__jsonresponse = None
        self.__uuid     = None
        self.__quiet    = False
        self.__cmdtype  = None
        self.__respHeaders = {}
        self.__rawJSONResponse = {}

    def mGetRawJSONResponse(self):
        return json.dumps(self.__rawJSONResponse, indent=4, separators=(',',': '))

    def mGetResponseHeaders(self):
        return self.__respHeaders

    def mSetCmd(self, aCmdType):
        self.__cmdtype = aCmdType

    def mSetQuietMode(self,aMode=True):
        self.__quiet=aMode

    def mBuildRequest(self, aPath):

        if HTTPSHelper.is_https_enabled():
            self.__request_url = 'https://' + self.__hostname+':' + str(self.__agent_port) + aPath
        else:
            self.__request_url = 'http://' + self.__hostname+':' + str(self.__agent_port) + aPath

        if self.__options.debug:
            ebLogInfo('*** mBuildRequest: %s' % (self.__request_url))

        self.__request = urllib.request.Request(self.__request_url)

    def mSetRequestHeader(self, aField, aValue, aType=None):

        if aField == "Authorization" and aType:
            self.__request.add_header(aField, "%s %s" % (aType, self.__authkey))
        else:
            self.__request.add_header(aField, aValue)

    def mPerformRequest(self, form_data=None, aOptions=None):

        _data = None
        _error = None
        _error_str = None
        status_code = None

        if aOptions is not None:
            options = aOptions
        else:
            options = get_gcontext().mGetArgsOptions()

        # Issue Request
        _retry = 0
        while _retry < 5:
            try:
                headers = {}
                headers["authorization"] = "Basic {}".format(self.__authkey)
                if form_data:
                    strdata = json.dumps(form_data)
                    _response = HTTPSHelper.build_opener(\
                        self.__hostname, self.__agent_port, 
                        self.__request, aData=strdata, aHeaders=headers, 
                        aTimeout=60)
                else:
                    _response = HTTPSHelper.build_opener(\
                        self.__hostname, self.__agent_port, 
                        self.__request, aHeaders=headers, aTimeout=60)
                
                _data = _response.read()
                status_code = _response.status
                self.storeResponseHeadersAsDictionary(_response)
                break
            except urllib.error.HTTPError as e:
                _error = '120'
                _error_str = str(e)
                status_code = e.code
                break
            except urllib.error.URLError as e:
                _error = '121'
                _error_str = str(e)
                break
            except socket.error as e:
                ebLogWarn(str(e))
                _retry += 1
                if _retry == 5:
                    raise e
            except Exception as e:
                ebLogInfo('*** urlopen error:{0} {1} {2}'.format(str(e), self.__request.get_full_url(), _data))
                break

        # Process Reply
        self.__response.mSetStatusCode(status_code)
        if not _error:
            try:
                _json = json.loads(_data)
                self.__rawJSONResponse = _json
                self.mBuildResponse(_json)
            except Exception as e:
                _error = '122'
                _error_str = str(e)
                self.mBuildErrorResponse(_error, _error_str, 'None')
                self.__rawJSONResponse = self.__response.mToJson()
        else:
            self.mBuildErrorResponse(_error, _error_str, 'None')
            self.__rawJSONResponse = self.__response.mToJson()

        return self.__response

    def storeResponseHeadersAsDictionary(self, _rspDataObject):
        self.__respHeaders = dict(_rspDataObject.headers)

    def mBuildResponse(self, aJson):

        _json = aJson
        for k in _json.keys():
            self.__response.mPopulate(k, _json[k])
        _body = self.__response.mGetBody()

        if self.__cmdtype == 'request_status':
            _l = _body
            if _l:
                self.__response.mSetStatus(_l[1])
                self.__response.mSetStatusInfo(_l[10])
                self.__response.mSetTimeStampStart(_l[2])
                self.__response.mSetTimeStampEnd(_l[3])
                self.__response.mSetCmdType(_l[4])
                self.__response.mSetParams(_l[5])
                self.__response.mSetError(_l[6])
                self.__response.mSetErrorStr(_l[7])
                self.__response.mSetData(_l[13])
                #self.__response.mSetXml(_l[9])
                self.__response.mSetPatchList(_l[14])
            else:
                pass

    def mBuildErrorResponse(self, aErrorCode, aErrorStr, aBody, aData=None):
        self.__response.mSetTimeStampStart(time.strftime("%c"))
        self.__response.mSetTimeStampEnd(time.strftime("%c"))
        self.__response.mSetCmdType(self.__cmdtype)
        self.__response.mSetStatus('Done')
        self.__response.mSetStatusInfo('False:100:0 - statusinfo not available')
        self.__response.mSetSuccess('False')
        self.__response.mSetError(aErrorCode)
        self.__response.mSetErrorStr(aErrorStr)
        self.__response.mSetBody(aBody)
        if aData is not None:
            self.__response.mSetData(aData)
        self.__response.mSetXml(None)

    def mDumpJson(self):

        options = self.__options

        if options.jsonmode:
            ebLogJson(self.__jsonresponse)
        else:
            ebLogInfo(self.__jsonresponse)

        if options.debug:
            try:
                for _line in json.loads(self.__jsonresponse)['body'].split('\n'):
                    if _line: ebLogInfo(_line)
            except:
                pass

    def mGetJsonResponse(self):

        return json.loads(self.__jsonresponse)

    def mIssueRequest(self, aOptions=None):

        _options = aOptions
        self.__hostname = _options.host
        self.__agent_port = int(_options.port)
        self.__authkey = _options.authKey
        _path = _options.path
        _headers = _options.headers
        _form_data= None

        self.mBuildRequest(_path)
        self.mSetRequestHeader('Authorization', self.__authkey, aType='Basic')
        if _options.data is not None:
            _form_data = _options.data
            self.mSetRequestHeader('content-type', 'application/json')

        if _headers is not None:
            for _attributes in list(_headers):
                if _attributes[0] == 'host':
                    self.mSetRequestHeader('Host', self.__hostname + ':' + _options.port)

        _response = self.mPerformRequest(_form_data)

        return _response