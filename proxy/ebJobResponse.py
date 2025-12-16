"""
 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    ebJobResponse - Basic functionality

FUNCTION:
    provide the structure of one request on the Exacloud Database Request Table

NOTE:
    None    

History:
    pbellary    18/06/2020 - File Creation
    aypaul      19/08/2021 - Corrected the logic for mSetXML function.
"""

import json
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogJson
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
status_code: Response code
"""

class ebJobResponse(object):

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
        self.__data    = None
        self.__success = 'Undefined'
        self.__xml     = None
        self.__patch_list = None
        self.__statuscode = None

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
            'body' : self.mSetBody,
            'data' : self.mSetData,
            'patch_list' : self.mSetPatchList,
            'statuscode' : self.mSetStatusCode,
            'xml' : self.mSetXml
        }

    def mPopulate(self, aKey, aValue):

        if aKey in self.__callback.keys():
            self.__callback[aKey](aValue)

    def mToJson(self):

        _response = {}

        _response['status'] = self.mGetStatus()
        _response['success'] = self.mGetSuccess()
        if self.__body is not None:
            _response['body'] = self.mGetBody()
        else:
            _response['body'] = []
        if self.mGetXml() is not None:
            _response['xml'] = self.mGetXml()
        if self.__error is not None:
            _response['error'] = self.__error
        if self.__error_str is not None:
            _response['error_str'] = self.__error_str

        return _response

    def mGetXml(self):
        return self.__xml

    def mSetXml(self, aValue):
        if self.__xml is None:
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

    def mGetStatusCode(self):
        return self.__statuscode

    def mSetStatusCode(self, aStatusCode):
        self.__statuscode = aStatusCode

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

    def mGetData(self):
        return self.__data

    def mSetData(self, aData):
        self.__data = aData

    def mGetPatchList(self):
        return self.__patch_list

    def mSetPatchList(self, aPatchList):
        self.__patch_list = aPatchList