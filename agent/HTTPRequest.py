"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    Agent - Configuration File Managemenet

FUNCTION:
    Agent Core functionalities

NOTE:
    None

History:
    aypaul     06/13/2024 - Enh#36705805 Support exacloud api access control.
    vgerard    04/08/2019 - Create file
"""

import json
import os
import cgi
import shutil
from six.moves import urllib
import ast
import copy
import uuid
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebThreadLocalLog, ebLogAgent
from exabox.core.Context import get_gcontext


class HttpRequest(object):
    def __init__(self, aPath, aVerb, aHeaders, aRequestLine=None):
        """
        Wrapper class for HttpRequest to be processed by an HttpCb (callback)

        :param aPath
            Endpoint path ex: '/CLUCtrl/vmgi_install','/Status?uuid=<>',....
        :param aVerb
            Verb used to target the endpoint ex: 'GET','POST'...
        :param aHeaders
            Headers object
        """
        self.__fullpath = aPath
        self.__verb     = aVerb
        self.__headers  = aHeaders
        self.__params   = {}
        self.__requestline = aRequestLine

    def getRequestLine(self):
        return self.__requestline

    def getFullPath(self):
        return self.__fullpath

    def setBody(self, aBody):
        self.__body = copy.deepcopy(aBody)

    def getBody(self):
        return self.__body

    def setParam(self,key,value):
        self.__params[key] = value
    
    def getParam(self,key):
        return self.__params.get(key)

    def getParams(self):
        return self.__params

    def getMethod(self):
        return self.__verb

    def getHeaders(self):
        return self.__headers

    def extractParams(self, aRequestHandler,aQueryParams):
        if self.__verb == 'OPTIONS':
            return
        if self.__verb == 'GET':
            if not aQueryParams:
                return
            else:
                sp = {}
                qp = aQueryParams.replace('"', '')
                qp = qp.split('?')
                for elt in qp:
                    es = elt.split('=')
                    sp[es[0]] = es[1]
                self.__params = sp
        else:
            _ct = aRequestHandler.headers.get('content-type','application/json')

            # Assume JSON payload first, then POST FORM format
            if _ct == 'application/json':
                _cl = aRequestHandler.headers.get('content-length')
                if not _cl:
                    return
                _body = aRequestHandler.rfile.read(int(_cl))
                self.__params = json.loads(_body)

                self.setBody(_body)
            else:
                formData = cgi.FieldStorage(
                        fp=aRequestHandler.rfile,
                        headers=aRequestHandler.headers,
                        environ={'REQUEST_METHOD': self.__verb,
                                 'CONTENT_TYPE': _ct,
                                 })
                if (formData):
                    self.__params = {k: formData[k].value for k in list(formData.keys())}
       

        self.processParams()

    def processParams(self):
        _param = self.__params
        _coptions = get_gcontext().mGetConfigOptions()
        if 'uuid_based_params' in list(_coptions.keys()):
            _uuid_params = _coptions['uuid_based_params']
        else:
            _uuid_params = ["opc_request_id", "wf_uuid", "operation_uuid", "requestid", "exaOcid"]

        for k in list(_param.keys()):
            if k in ('cmd', 'vmcmd', 'uuid'):
                continue
            v = _param[k]
            if k in _uuid_params:
                #On very rare cases, uuid can have only 'e' along with other numbers , then literal_eval results in nan.
                #Hence, lets not use literval_eval for uuid.
                try:
                    #Do some basic validation
                    uuid.UUID(v)
                except ValueError:
                    #For now, Lets not error out, since most of these uuids are actually not used by exacloud.
                    #Just log a warning.
                    ebLogWarn(f'param {k} with uuid {v} appears invalid!')
                continue

            # Unmunch the Value (e.g. unquote) and eval the result to get the right Value
            # e.g. 'True','None','{}' will be stored as native type and not string in the
            # parameter array.
            try:
                if not isinstance(v, dict):
                    v = urllib.parse.unquote(v)
            except Exception as e:
                ebLogWarn(e)
            #
            # Some parameters can _not_ be evaluated while other need to - skip the one that cannot be
            #
            try:
                # Use literal_eval to only allow data
                ev = ast.literal_eval(v) 
                if type(ev).__name__ not in ['builtin_function_or_method']:
                    v = ev
            except:
                pass
            _param[k] = v

        if self.__verb == 'GET':
            self.ExaCCDBFilesProcessing(_param)
            

    # THIS DB ACCESS IS UGLY, I would like that refactored (VGE)
    def ExaCCDBFilesProcessing(self,aParam):
        # String JSONCONF and absent config path are relict of ExaCCGen1
        _db = None
        _param = aParam
        if 'jsonconf' in _param:
            if isinstance(_param['jsonconf'], str):
                _db = ebGetDefaultDB()
                ebLogInfo("loading jsonconf content from file")
                _param['jsonconf'] = json.loads(
                _db.mReadFile(_param['jsonconf'], 'ecra_files'))
                if not _param['jsonconf']:
                    _param['jsonconf'] = {}
        else:
            _param['jsonconf'] = {}

        if 'configpath' in _param:
            if os.path.isfile(_param['configpath']):
                ebLogInfo('File {0} already on file system'.format(
                _param['configpath']))
            else:
                _db = _db or ebGetDefaultDB()
                _db.export_file(_param['configpath'])
                ebLogInfo('Exporting {0} from database'.format(
                _param['configpath']))
    
