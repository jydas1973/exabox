"""
 Copyright (c) 2014, 2023, Oracle and/or its affiliates.

NAME:
    BaseHandler - Basic functionality

FUNCTION:
    Principal Handler of the BaseServer

NOTE:
    None    

History:
    hgaldame    09/30/2023 - 35019797 - exacc - remoteec cps_tuner endpoint not
                             working
    jesandov    06/04/2020 - Add validation against base64_file, regex:, hidden, alias parameters
    jesandov    26/03/2019 - File Creation
"""


import traceback
from six.moves import urllib
import base64
import errno
import json
import sys
import os
import re
from exabox.agent.HTTPAuthentication import ebHTTPAuthentication,ebHTTPAuthResult
from exabox.network.ExaHTTPSServer import ExaHTTPSServer, ExaHTTPRequestHandler


class BaseHandler(ExaHTTPRequestHandler):

    def __init__(self, *args):

        self.__server    = args[2]
        self.__log       = self.__server.mGetLog()
        self.__config    = self.__server.mGetConfig()
        self.__callbacks = self.__config.mGetEndpointClasses()
        self.__httpAuth  = ebHTTPAuthentication(self.__config.mGetConfigValue("auth"))

        try:
            super().__init__(*args)

        except IOError as i:
            if i.errno == errno.EPIPE: #Broken pipe error
                pass
            else:
                self.__config.mGetStacktrace()

        except Exception as e:
            self.__config.mGetStacktrace()

    def log_message(self, format, *args):
        _call = "%s - [%s]" % (self.client_address[0], format%args)
        self.__log.mCall(_call)

    def mValidMandatoryParams(self, aEndpointName, aUrlArgs, aBody, aResponse):

        def mValidateGrammar(aArgsDict, aCheckDict):

            nonEmptyParams = ["base64_file", "mandatory"]
            whitelistParams = ["optional", "hidden"]

            for _key in filter(lambda x: aCheckDict[x] not in whitelistParams, aCheckDict):

                if aArgsDict is None:
                    aResponse['status'] = 500
                    aResponse['error'] = "Error, missing mandatory param '{0}', since not params".format(_key)
                    aResponse['text'] = "Error, missing mandatory param '{0}', since not params".format(_key)
                    return False

                elif aArgsDict is not None and (_key not in aArgsDict.keys() or aArgsDict[_key] == ""):
                    aResponse['status'] = 500
                    aResponse['error'] = "Error, missing mandatory param '{0}'".format(_key)
                    aResponse['text'] = "Error, missing mandatory param '{0}'".format(_key)
                    return False

                elif aCheckDict[_key] in nonEmptyParams:
                    continue

                elif aCheckDict[_key].startswith("regex:"):
                    _regex = aCheckDict[_key][6:].strip()
                    if not re.match(_regex, aArgsDict[_key]):
                        aResponse['status'] = 500
                        aResponse['error'] = "Error, the param '{0}' not match regex '{1}'".format(_key, _regex)
                        aResponse['text'] = "Error, the param '{0}' not match regex '{1}'".format(_key, _regex)
                        return False

                elif aCheckDict[_key].find("|") != -1:
                    _posibleValues = aCheckDict[_key].split("|")
                    if aArgsDict[_key] not in _posibleValues:
                        aResponse['status'] = 500
                        aResponse['error'] = "Error, the param '{0}' only accepts '{1}'".format(_key, _posibleValues)
                        aResponse['text'] = "Error, the param '{0}' only accepts '{1}'".format(_key, _posibleValues)
                        return False

            return True

        _endpointsJson = self.__config.mGetClientEndpoints()[aEndpointName]
        _check = None

        # Validate HTTP Method
        for _single in _endpointsJson:

            if _single not in ['help', 'class', 'package']:

                # alias endpoints does not contain method
                if "alias" in _endpointsJson[_single].keys():
                    continue

                if _endpointsJson[_single].pop('method') == self.command:
                    _check = _endpointsJson[_single]['params']
                    break

        if _check == False:
            aResponse['text']   = "The endpoint {0} does not support {1}".format(aEndpointName, self.command)
            aResponse['error']  = "Error, no body found"
            aResponse['status'] = 501
            return False

        # Validate body
        if self.command in ["PUT", "POST", "DELETE", "PATCH"]:

            if aBody is None:
                aResponse['text']   = "Error, no body found"
                aResponse['error']  = "Error, no body found"
                aResponse['status'] = 500
                return False

            if aBody is not None:
                for _key in list(aBody.copy().keys()):
                    if _key not in list(_check.keys()) or aBody[_key] == "":
                        aBody.pop(_key)

            return mValidateGrammar(aBody, _check)

        # Validate url arguments
        elif self.command in ["GET"]:

            if aUrlArgs is not None:
                for _key in list(aUrlArgs.copy().keys()):
                    if _key not in list(_check.keys()) or aUrlArgs[_key].strip() == "":
                        aUrlArgs.pop(_key)

            return mValidateGrammar(aUrlArgs, _check)


    def mGetBody(self):

        if self.command == "GET":
            return None

        _responseLen = int(self.headers.get('content-length', 0))
        _body = self.rfile.read(_responseLen)

        try:
            _body = json.loads(_body)
        except Exception as e:
            _body = None

        return _body

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"{0}\"'.format(self.__config.mGetPrefix()))
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_HEAD(self, aResponse):

        if "status" in list(aResponse.keys()):
            _status = aResponse.pop("status")
            aResponse['http_status'] = _status
            self.send_response(_status)
        else:
            aResponse['http_status'] = 200
            self.send_response(200)

        if "ctype" in list(aResponse.keys()):
            self.send_header('Content-type', aResponse['ctype'])
        else:
            aResponse['ctype'] = 'application/json'
            self.send_header('Content-type', 'application/json')

        self.end_headers()

    def do_GET(self):
        self.mDefaultHandler("mGet")

    def do_POST(self):
        self.mDefaultHandler("mPost")

    def do_PUT(self):
        self.mDefaultHandler("mPut")

    def do_DELETE(self):
        self.mDefaultHandler("mDelete")

    def do_PATCH(self):
        self.mDefaultHandler("mPatch")

    def mParamsUrl(self):

        _path   = urllib.parse.unquote(self.path)
        _params = {}

        if not self.path.startswith("/{0}".format(self.__config.mGetPrefix())):
            return None
        else:
            _path = _path[len("/{0}".format(self.__config.mGetPrefix())):]

        if _path == "/shutdown":
            self.__server._BaseServer__shutdown_request = True
            return "shutdown"

        #Get the grammar of the endpoint name
        _grammarEndpointL = []
        for _key in self.__callbacks:
            _grammarEndpointL.append("(\/{0}$)".format(_key))

        _grammarEndpoint = "|".join(_grammarEndpointL)

        #Match the endpoint
        _parsed_path = urllib.parse.urlparse(_path).path
        self.__log.mInfo("Match endpoint. Path received :'{0}', Parsed Path:'{1}'".format(_path, _parsed_path))
        _pattern = re.match(_grammarEndpoint, _parsed_path)
        if _pattern is None:
            _params['endpoint'] = None
            _params['endpointName'] = ""
        else:
            _endpointName = _path[_pattern.start()+1: _pattern.end()]
            _path = _path[_pattern.end():]
            _params['endpoint'] = self.__callbacks[_endpointName]
            _params['endpointName'] = _endpointName

        #Get the rest of the params
        _posQuestionMark = _path.find("?")

        if _posQuestionMark == -1:
            _params['args'] = None

            if _params['endpointName'] == "":
                _params['endpointName'] = _path[1:]

        else:

            if _params['endpointName'] == "":
                _params['endpointName'] = _path[1:_posQuestionMark]

            _path = _path[_posQuestionMark+1:]
            _params['args'] = dict(urllib.parse.parse_qsl(_path))

        return _params

    def mAuthenticate(self):
        _auth_header = self.headers.get('Authorization')

        if _auth_header is None:

            self.do_AUTHHEAD()
            self.wfile.write(self.headers.get('Authorization').encode('utf8'))
            self.wfile.write(b'Authentication failed not authorized to access this service')
            return False

        else:

            _auth  = self.__config.mGetConfigValue("auth")

            if self.__httpAuth.mEvaluateAuth(_auth_header) == ebHTTPAuthResult.AUTH_OK:
                return True

            else:
                self.do_AUTHHEAD()
                self.wfile.write(self.headers.get('Authorization').encode('utf8'))
                self.wfile.write(b'Authentication failed not authorized to access this service')
                return False

    def mDefaultHandler(self, aMethodCallback):

        if not self.mAuthenticate():
            return

        _body       = self.mGetBody()
        _params     = self.mParamsUrl()
        _response = {"text": {}, "status": 200, "error": ""}

        self.__log.mInfo({"Method": self.command, "UrlParams": _params, "Body": _body})

        if _params == "shutdown":
            _response['text']  = "Shutdown {0}".format(self.__config.mGetPrefix())

        elif _params is None:
            _response['status'] = 500
            _response['error']  = "Invalid initial signature"

        else:

            #There is no params
            if self.path == "/{0}".format(self.__config.mGetPrefix()) or self.path == "/{0}/".format(self.__config.mGetPrefix()):
                _response['text'] = "Welcome to the {0}".format(self.__config.mGetPrefix())

            else:

                if _params['endpoint'] is None:
                    _response['status'] = 404
                    _response['error'] = "Endpoint not found"

                else:
                    _endpointClass = _params['endpoint']
                    _args          = _params['args']
                    _shared = self.__server.mGetSharedData()

                    if self.mValidMandatoryParams(_params['endpointName'], _args, _body, _response):

                        _endpointInst = _endpointClass(_args, _body, _response, _shared)
                        _callback = getattr(_endpointInst, aMethodCallback)
                        _callback()

        self.do_HEAD(_response)
        self.wfile.write(json.dumps(_response).encode('utf8'))

# end of file
