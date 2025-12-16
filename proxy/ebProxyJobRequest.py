#
# $Header: ecs/exacloud/exabox/proxy/ebProxyJobRequest.py /main/1 2020/10/01 09:08:34 aypaul Exp $
#
# ebProxyJobRequest.py
#
# Copyright (c) 2020, Oracle and/or its affiliates. 
#
#    NAME
#      ebProxyJobRequest.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      07/23/20 - Creation
#

import six
import time
import uuid
import json
import ast
from copy import deepcopy

class ebProxyJobRequest(object):

    def __init__(self, aCmdType, aParams, aDB=None):
        self.__uuid    = aParams['uuid'] if 'uuid' in aParams else str(uuid.uuid1())
        self.__cmdtype = aCmdType
        self.__params  = aParams
        self.__nsOpt   = nsOpt(aParams)
        self.__db      = aDB
        self.__urlfullpath = 'Undef'
        self.__headers = 'Undef'
        self.__respbody = 'Undef'
        self.__respCode = 9999
        self.__reqType = 'Undef'
        self.__reqbody    = 'Empty'

    def mSetCmdType(self,aCmdType):
        self.__cmdtype = aCmdType

    def mSetUUID(self,aUUID):
        self.__uuid = aUUID

    def mSetParams(self,aParams):
        self.__params = aParams
        self.__nsOpt  = nsOpt(aParams)

    def mSetUrlFullPath(self, aValue):
        self.__urlfullpath = aValue

    def mSetUrlHeaders(self, aValue):
        self.__headers = aValue

    def mSetRespBody(self, aValue):
        self.__respbody = aValue

    def mSetRespCode(self, aintRespCode):
        self.__respCode = aintRespCode

    def mSetReqType(self, aReqType):
        self.__reqType = aReqType

    def mSetReqBody(self, aBody):
        self.__reqbody = aBody

    def mGetReqBody(self):
        return self.__reqbody

    def mGetReqType(self):
        return self.__reqType

    def mGetRespCode(self):
        return self.__respCode

    def mGetRespBody(self):
        return self.__respbody

    def mGetUrlHeaders(self):
        return self.__headers

    def mGetUrlFullPath(self):
        return self.__urlfullpath

    def mGetOptions(self):
        return self.__nsOpt

    def mGetParams(self):
        return self.__params

    def mGetUUID(self):
        return self.__uuid

    def mGetCmdType(self):
        return self.__cmdtype

    def mGetType(self):
        return self.__cmdtype.split('.')[0]

    def mGetCmd(self):
        return self.__cmdtype.split('.')[1]

    def mRegister(self):
        self.__db.mInsertNewProxyRequest(self)

    def mLoadRequestFromDB(self, aUUID):

        _req = self.__db.mGetProxyRequest(aUUID)
        self.mPopulate(_req)

    def mPopulate(self, aReq):

        _req = aReq
        if _req:
            self.mSetUUID(_req[0])
            self.mSetCmdType(_req[1])
            self.mSetParams(ast.literal_eval(_req[2]))
            self.mSetReqBody(_req[3])
            self.mSetUrlFullPath(_req[4])
            self.mSetUrlHeaders(_req[5])
            self.mSetRespBody(_req[6])
            self.mSetRespCode(_req[7])
            self.mSetReqType(_req[8])

class nsOpt(object):

    def __init__(self, kwargs):
        for name in kwargs:
            setattr(self, name, kwargs[name])

    def __eq__(self, other):
        return vars(self) == vars(other)

    def __ne__(self, other):
        return not (self == other)

    def __contains__(self, key):
        return key in self.__dict__

    def __getattr__(self, key):
        if key not in self.__dict__:
            return None

    def __str__(self):
        return str(self.__dict__)

    def __deepcopy__(self, memo=None):
        return nsOpt(deepcopy(self.__dict__, memo=memo))