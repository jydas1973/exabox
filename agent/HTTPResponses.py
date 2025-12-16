"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    HttpResponse - Configuration File Managemenet

FUNCTION:
    HttpResponses functionalities

NOTE:
    None

History:
    aypaul     06/12/24   - Enh#36705805 Support API access control from exacloud
    aypaul     12/21/23   - Bug#36120429 Add exception handling during response write.
    aypaul     11/06/2023 - Enh#35730789 Set application stickiness cookie for session persistence.
    vgerard    09/08/2019 - Wrap Authentication into callback/endpoint
    seha       05/27/2019 - Bug 29679165 log collection for OCI-ExaCC
    vgerard    04/08/2019 - Create file
"""

import six
import os
import json
import cgi
import shutil
import base64
from exabox.agent.HTTPProcessors import MethodWrapper
from exabox.agent.HTTPAuthentication import ebHTTPAuthentication,ebHTTPAuthResult
from exabox.agent.AuthenticationStorage import ebGetHTTPAuthStorage
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebThreadLocalLog, ebLogAgent
from exabox.core.Context import get_gcontext
from exabox.agent.HTTPSignatureVerification import HTTPSignatureVerify

# RESPONSE Builder, to factorize common responses (errors)
class ErrorBuilder(object):

    @staticmethod
    def response(aErrNum, aErrMsg, aResponse=dict()):
        aResponse['status']    = 'Done'
        aResponse['error']     = str(aErrNum)
        aResponse['error_str'] = aErrMsg
        aResponse['success']   = 'False'
        return aResponse 

# RESPONSE HANDLERS, sends Response dict content to caller.

class ResponseHandler(object):

    def __init__(self):
        self.enable_application_persistence = get_gcontext().mCheckConfigOption('ecra_exacloud_application_persistence')

    def GetHeaders(self, aResponse=None):
        return []

    def ProcessResponse(self, aResponse=None):
        return aResponse

    def GetReturnCode(self, aResponse=None):
        return 200

    def WriteResponse(self, aRequestHandler, aResponse=None):

        try:
            aRequestHandler.send_response(self.GetReturnCode(aResponse))

            for _hName, _hValue in self.GetHeaders(aResponse):
                aRequestHandler.send_header(_hName,_hValue)

            aRequestHandler.end_headers()

            if aResponse:
                aRequestHandler.wfile.write(six.ensure_binary(self.ProcessResponse(aResponse)))
                aRequestHandler.wfile.write(b'\n\n')
        except Exception as exp:
            ebLogError(f"Exception while sending the JSONResponse response. Exception: {exp}")

class JSONResponse(ResponseHandler):

    def __init__(self) -> None:
        ResponseHandler.__init__(self)

    def GetReturnCode(self,aResponse=None):

        if not aResponse:
            return 200

        return int(aResponse.get('error', 200)) #default to 200 if no error

    def GetHeaders(self,aResponse=None):

        _headers = [
            ('Content-type',                 'application/json'),
            ('Access-Control-Allow-Origin',  '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        ]
        _response = aResponse
        if self.enable_application_persistence and _response is not None and type(_response) is dict and _response.get("uuid", None) is not None:
            _headers.append(('Set-Cookie', f'X-Oracle-ExaCS-Backend={_response.get("uuid")}'))

        return _headers

    def ProcessResponse(self,aResponse):
        return json.dumps(aResponse, indent=4, separators=(',',': '))

class HTMLResponse(ResponseHandler):

    def __init__(self) -> None:
        ResponseHandler.__init__(self)

    def GetHeaders(self, aResponse):

        _headers = [
            ('Access-Control-Allow-Origin',  '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        ]

        #set content type (assume HTML if unspecified)
        if 'ctype' in list(aResponse.keys()):
            _headers.append(('Content-type', aResponse['ctype']))
        else:
            aResponse['ctype'] = 'text/html'
            _headers.append(('Content-type', 'text/html'))

        #set content filename
        if 'cname' in list(aResponse.keys()):
            _headers.append(('Content-Disposition', 'attachment; filename="{}"'.format(aResponse['cname'])))

        #set content size
        if 'clength' in list(aResponse.keys()):
            _headers.append(('Content-Length', aResponse['clength']))

        #set cache control
        if aResponse.get('cache_control'):
            _headers.append(("Cache-Control", "public, max-age=31536000"))
            del aResponse['cache_control']

        if self.enable_application_persistence and aResponse is not None and type(aResponse) is dict and aResponse.get("uuid", None) is not None:
            _headers.append(('Set-Cookie', f'X-Oracle-ExaCS-Backend={aResponse.get("uuid")}'))

        return _headers

    def ProcessResponse(self,aResponse):

        #From the class Agent.ebRestHttpListener:
        #methods with HTMLResponse callback...
            #mAgentRequest    (endpoint: /AgentCtrl)
            #mAtpGetFile      (endpoint: /AtpGetFile)
            #mAgentWWWContent (endpoint: /WWW)
        #can return many content types...
            #mAgentRequest    can return: JSON / XML / TXT
            #mAtpGetFile      can return: HTML / JSON / TXT / BIN
            #mAgentWWWContent can return: HTML / CSS / JS / JSON / XML / TXT / JPG
        #with JSON being the most common, after the migration of the UI to Oracle JET.
        #Therefore it is necessary to stringify the output for JSON.
        #All other content types can be returned as-is.

        #stringify JSON if necessary
        if aResponse["ctype"]=="application/json" and (isinstance(aResponse["output"], dict) or isinstance(aResponse["output"], list)):
            aResponse["output"] = json.dumps(aResponse["output"], indent=4, separators=(',',': '))
        #if

        return aResponse["output"]

class AuthResponse(JSONResponse):

    def __init__(self) -> None:
        ResponseHandler.__init__(self)

    def GetReturnCode(self,aResponse=None):
        return 401

    def GetHeaders(self,aResponse=None):
        _headers = [
            ('Access-Control-Allow-Origin',  '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ('WWW-Authenticate',             'Basic realm=\"ExaCloud Agent\"'),
            ('Content-type',                 'text/html')
        ]

        _response = aResponse
        if self.enable_application_persistence and _response is not None and type(_response) is dict and _response.get("uuid", None) is not None:
            _headers.append(('Set-Cookie', f'X-Oracle-ExaCS-Backend={_response.get("uuid")}'))

        return _headers

class FileResponse(ResponseHandler):

    def __init__(self) -> None:
        ResponseHandler.__init__(self)

    def GetReturnCode(self, aResponse=None):

        if not aResponse:
            return 200

        return int(aResponse.get('error', 200)) #default to 200 if no error

    def GetHeaders(self, aFileInfo):

        #All requests are synchronous calls hence application persistence is not required.
        _headers = [
            ('Access-Control-Allow-Origin',  '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ("Content-Type",                 'application/octet-stream'),
            ("Content-Disposition",          'attachment; filename="{}"'.format(aFileInfo['filename'])),
            ("Content-Length",               aFileInfo['length']),
            ("Last-Modified",                aFileInfo['mtime'])
        ]

        return _headers

    def WriteResponse(self, aRequestHandler, aResponse):

        if (not 'file' in aResponse) or (not os.path.isfile(aResponse['file'])):
            aRequestHandler.send_response(404)
            return

        _filePath = aResponse['file']
        with open(_filePath,'rb') as _f:

            aRequestHandler.send_response(self.GetReturnCode(aResponse))
            _fs = os.fstat(_f.fileno())

            _header = self.GetHeaders({
                'filename' : os.path.basename(_filePath),
                'length'   : _fs.st_size,
                'mtime'    : _fs.st_mtime
            })

            for _hName, _hValue in _header:
                aRequestHandler.send_header(_hName, _hValue)

            aRequestHandler.end_headers()
            shutil.copyfileobj(_f, aRequestHandler.wfile)

        if aResponse.get('delete_temp'):
            os.remove(_filePath)
            del aResponse['delete_temp']

class OptionsResponse(ResponseHandler):

    def __init__(self) -> None:
        ResponseHandler.__init__(self)

    def GetHeaders(self,aResponse):
        _headers = [('Allow', ', '.join(aResponse['verbs']))]

        _response = aResponse
        if self.enable_application_persistence and _response is not None and type(_response) is dict and _response.get("uuid", None) is not None:
            _headers.append(('Set-Cookie', f'X-Oracle-ExaCS-Backend={_response.get("uuid")}'))

        return _headers

class HttpCb(object):

    def __init__(self, aMethods, aResponseType=JSONResponse, aAuthenticated=True):
        """ 
        Callback Method definition (can be assigned to multiple endpoints)

        :param aMethods
            Map between HTTP verb and handling method {"GET":<method>}
            Method can have wrappers (pre/post Processors using the MethodWrapper class)
        :param aResponseType
            Type of response (used for headers setups/customization)
        :param aAuthenticated
            True: Will check Authentication before executing the <method>
            False: Unauthenticated Callback (TO BE USED only for UI css/js files)
        """
        self.__funcs            = aMethods
        # Append for all callback OPTIONS method putting verbs in response
        self.__funcs['OPTIONS'] = self.optionsFunc
        self.__responseType     = aResponseType
        self.__authenticationProcessor = None
        if aAuthenticated:
            self.__authenticationProcessor = ebHTTPAuthentication(ebGetHTTPAuthStorage())
            

    #OPTIONS HTTP verb
    def optionsFunc(self, aParams, aResponse):
        aResponse['verbs'] = list(self.__funcs.keys())



    def invalidVerb(self, aMethod, aResponse):
        ErrorBuilder.response(404,
                             'Service {} not valid for verb {}'.format(self.__funcs, aMethod),
                              aResponse)
 
    def mProcessAuth(self, aHttpRequest, aResponse):        
        if self.__authenticationProcessor:
            _auth_header = aHttpRequest.getHeaders().get('Authorization')
            _auth_result = self.__authenticationProcessor.mEvaluateAuth(_auth_header)
            if _auth_result != ebHTTPAuthResult.AUTH_OK:
                self.__responseType = AuthResponse
                if _auth_result == ebHTTPAuthResult.AUTH_ERROR:
                    aResponse['output'] = 'Authentication failed. Not authorized to access this service.'
                    aResponse['success'] = 'False'
                return False

        return True # No Auth or Auth successful

    def mVerifyHTTPSignature(self, aHttpRequest):
        _http_signature_processor = HTTPSignatureVerify(aHttpRequest)
        return _http_signature_processor.mVerifySignature()

    def executeRequest(self, aHttpRequest):
        
        _response = {}
        _method = aHttpRequest.getMethod()
        _wrapper = None

        #_response: {}
        #_method:   GET
        #_wrapper:  None

        if not _method in self.__funcs:
            self.invalidVerb(_method,_response)
            return _response
        
        if not self.mProcessAuth(aHttpRequest, _response):
            return _response
        
        _func = self.__funcs[_method]
        if isinstance(_func, MethodWrapper): #for the endpoints: /CLUCtrl, /CLUDiags, /Patch, /Status
            _wrapper = self.__funcs[_method]
            _wrapper.applyPreProcessors(aHttpRequest)
            _func = _wrapper.getWrappedMethod()
        
        if not self.mVerifyHTTPSignature(aHttpRequest):#TODO: Ideally would like to do this before preprocessor to save time but need to check the level of APIs which need to be restricted.
            _response['output'] = 'HTTP signature verification has failed. Unauthorised access of the requested target.'
            _response['success'] = 'False'
            return _response
        
        # EXECUTE THE CALLBACK (either with original or wrapped method)
        _func(aHttpRequest.getParams(), _response) #a method from Agent.ebRestHttpListener is run here

        if _wrapper:
            _wrapper.applyPostProcessors(_response)

        return _response # _response is returned to Agent.ebRestHttpListener.mHandleRequest

    def returnResponse(self, aRequestHandler, aResponse):

        if aRequestHandler.command=='OPTIONS':
            _responseType = OptionsResponse
        else:
            _responseType = self.__responseType
        
        _responseType().WriteResponse(aRequestHandler, aResponse) #the method ResponseHandler.WriteResponse is run here


#EOF
