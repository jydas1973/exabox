"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    ebJobRequest - Basic functionality

FUNCTION:
    provide the structure of one request on the Exacloud Database Request Table

NOTE:
    None    

History:
    aypaul      08/08/2025 - Enh#37732728 Store AQ details in the request object.
    aypaul      12/02/2024 - ER-37026034 Add sub command details to request table for persistence.
    jesandov    26/03/2019 - File Creation.
"""

import six
import time
import uuid
import json
import ast
from copy import deepcopy


class ebJobRequest(object):

    def __init__(self, aCmdType, aParams, aDB=None):
        self.__uuid    = aParams['uuid'] if 'uuid' in aParams else str(uuid.uuid1())
        self.__status  = 'Pending'
        self.__statusinfo = '000:: No status info available'
        self.__starttime = time.strftime("%c")
        self.__endtime = 'Undef'
        self.__cmdtype = aCmdType
        self.__subcommand = None
        if self.__cmdtype is not None and "." in self.__cmdtype:
            self.__subcommand = self.__cmdtype.split(".")[1]
        self.__response_sent = 'Undef'
        self.__params  = aParams
        self.__error   = 'Undef'
        self.__error_str = 'Undef'
        self.__body    = 'Empty'
        self.__data    = 'Undef'
        self.__db      = aDB
        self.__nsOpt   = nsOpt(aParams)
        self.__xml     = 'Undef'
        self.__worker  = 0
        self.__clustername = 'Undef'
        self.__lock    = 0
        self.__aq_name = '' if self.__params.get('aq_name', 'Undef') == 'Undef' else self.__params.get('aq_name')

    def mGetAqName(self):
        return self.__aq_name

    def mSetAqName(self, aValue):
        self.__aq_name = aValue

    def mGetResponseSent(self):
        return self.__response_sent

    def mSetResponseSent(self, aValue):
        self.__response_sent = aValue

    def mGetSubCommand(self):
        return self.__subcommand

    def mSetSubCommand(self, aValue):
        self.__subcommand = aValue

    def mGetLock(self):
        return self.__lock

    def mSetLock(self,aValue):
        self.__lock = aValue

    def mGetClusterName(self):
        return self.__clustername

    def mSetClusterName(self,aValue):
        self.__clustername = aValue

    def mSetWorker(self,aWorkerId):
        self.__worker = aWorkerId

    def mGetWorker(self):
        return self.__worker

    def mGetXml(self):
        return self.__xml

    def mSetXml(self,aValue):
        self.__xml = str(aValue)

    def mGetCmd(self):
        try:
            return self.__cmdtype.split('.')[1]
        except IndexError:
            return ""

    def mSetCmdType(self,aCmdType):
        self.__cmdtype = aCmdType

    def mGetType(self):
        return self.__cmdtype.split('.')[0]

    def mGetOptions(self):
        return self.__nsOpt

    def mGetStatus(self):
        return self.__status

    def mGetStatusInfo(self):
        return self.__statusinfo

    def mSetStatus(self, aStatus):
        self.__status = aStatus

    def mSetStatusInfo(self, aStastusInfo):
        self.__statusinfo = aStastusInfo

    def mGetUUID(self):
        return self.__uuid

    def mSetUUID(self,aUUID):
        self.__uuid = aUUID

    def mGetTimeStampStart(self):
        return self.__starttime

    def mSetTimeStampStart(self,aTime):
        self.__starttime = aTime

    def mGetTimeStampEnd(self):
        return self.__endtime

    def mSetTimeStampEnd(self,aTime=None):
        if aTime:
            self.__endtime = aTime
        else:
            self.__endtime = time.strftime("%c")

    def mGetCmdType(self):
        return self.__cmdtype

    def mGetParams(self):
        return self.__params

    def mSetParams(self,aParams, aMock=False):
        self.__params = aParams

        if not aMock:
            self.__nsOpt  = nsOpt(aParams)

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

    def mRegister(self):
        # Register the Request with the DB
        self.__db.mInsertNewRequest(self)

    def mLoadRequestFromDB(self, aUUID):

        _req = self.__db.mGetCompleteRequest(aUUID)
        self.mPopulate(_req)

    @staticmethod
    def mGetColumns():

        _columns = []

        _columns.append("uuid")
        _columns.append("status")
        _columns.append("starttime")
        _columns.append("endtime")
        _columns.append("cmdtype")
        _columns.append("params")
        _columns.append("error")
        _columns.append("error_str")
        _columns.append("body")
        _columns.append("xml")
        _columns.append("statusinfo")
        _columns.append("clustername")
        _columns.append("lock")
        _columns.append("data")
        _columns.append("subcmd")
        _columns.append("response_sent")
        _columns.append("aq_name")

        return _columns

    def mFromDict(self, aDict):

        _affected = 0
        _dictKeys = list(aDict.keys())
        if "uuid" in _dictKeys and aDict["uuid"] != self.mGetUUID():
            self.mSetUUID(aDict["uuid"])
            _affected += 1

        if "status" in _dictKeys and aDict["status"] != self.mGetStatus():
            self.mSetStatus(aDict["status"])
            _affected += 1

        if "starttime" in _dictKeys and aDict["starttime"] != self.mGetTimeStampStart():
            self.mSetTimeStampStart(aDict["starttime"])
            _affected += 1

        if "endtime" in _dictKeys and aDict["endtime"] != self.mGetTimeStampEnd():
            self.mSetTimeStampEnd(aDict["endtime"])
            _affected += 1

        if "cmdtype" in _dictKeys and aDict["cmdtype"] != self.mGetCmdType():
            self.mSetCmdType(aDict["cmdtype"])
            _affected += 1

        if "params" in _dictKeys and aDict["params"] != self.mGetParams():
            self.mSetParams(aDict["params"])
            _affected += 1

        if "error" in _dictKeys and aDict["error"] != self.mGetError():
            self.mSetError(aDict["error"])
            _affected += 1

        if "error_str" in _dictKeys and aDict["error_str"] != self.mGetErrorStr():
            self.mSetErrorStr(aDict["error_str"])
            _affected += 1

        if "body" in _dictKeys and aDict["body"] != self.mGetBody():
            self.mSetBody(aDict["body"])
            _affected += 1

        if "xml" in _dictKeys and aDict["xml"] != self.mGetXml():
            self.mSetXml(aDict["xml"])
            _affected += 1

        if "statusinfo" in _dictKeys and aDict["statusinfo"] != self.mGetStatusInfo():
            self.mSetStatusInfo(aDict["statusinfo"])
            _affected += 1

        if "clustername" in _dictKeys and aDict["clustername"] != self.mGetClusterName():
            self.mSetClusterName(aDict["clustername"])
            _affected += 1

        if "lock" in _dictKeys and aDict["lock"] != self.mGetLock():
            self.mSetLock(aDict["lock"])
            _affected += 1

        if "data" in _dictKeys and aDict["data"] != self.mGetData():
            self.mSetData(aDict["data"])
            _affected += 1

        if "subcmd" in _dictKeys and aDict["subcmd"] != self.mGetSubCommand():
            self.mSetSubCommand(aDict["subcmd"])
            _affected += 1

        if "response_sent" in _dictKeys and aDict["response_sent"] != self.mGetResponseSent():
            self.mSetResponseSent(aDict["response_sent"])
            _affected += 1

        if "aq_name" in _dictKeys and aDict["aq_name"] != self.mGetAqName():
            self.mSetAqName(aDict["aq_name"])
            _affected += 1

        return float(_affected) / float(len(ebJobRequest.mGetColumns()))

    def mToDictMock(self):

        _dict = {}
        _dict['uuid'] = str(self.mGetUUID())
        _dict["status"] = self.mGetStatus()
        _dict["starttime"] = self.mGetTimeStampStart()
        _dict["cmdtype"] = self.mGetCmdType()
        _dict["params"] = self.mGetParams()
        _dict["xml"] = self.mGetXml()

        return _dict

    def mToDict(self):

        _dict = {}
        _dict['uuid'] = str(self.mGetUUID())
        _dict["status"] = self.mGetStatus()
        _dict["starttime"] = self.mGetTimeStampStart()
        _dict["endtime"] = self.mGetTimeStampEnd()
        _dict["cmdtype"] = self.mGetCmdType()
        _dict["params"] = self.mGetParams()
        _dict["error"] = self.mGetError()
        _dict["error_str"] = self.mGetErrorStr()
        _dict["body"] = self.mGetBody()
        _dict["xml"] = self.mGetXml()
        _dict["statusinfo"] = self.mGetStatusInfo()
        _dict["clustername"] = self.mGetClusterName()
        _dict["lock"] = self.mGetLock()
        _dict["data"] = self.mGetData()
        _dict["subcmd"] = self.mGetSubCommand()
        _dict["response_sent"] = self.mGetResponseSent()
        _dict["aq_name"] = self.mGetAqName()

        return _dict

    def mToDictForECRA(self):

        _dict = {}
        _dict['uuid'] = str(self.mGetUUID())
        _dict["status"] = self.mGetStatus()
        _dict["start_time"] = self.mGetTimeStampStart()
        _dict["end_time"] = self.mGetTimeStampEnd()
        _dict["cmd"] = self.mGetCmdType()
        _dict["params"] = self.mGetParams()
        _dict["error"] = self.mGetError()
        _dict["error_str"] = self.mGetErrorStr()
        _dict["body"] = self.mGetBody()
        _dict["xml"] = self.mGetXml()
        _dict["statusinfo"] = self.mGetStatusInfo()
        _dict["na1"] = self.mGetClusterName()
        _dict["na2"] = self.mGetLock()
        _dict["ec_details"] = self.mGetData()
        _dict["subcmd"] = self.mGetSubCommand()
        _dict["response_sent"] = self.mGetResponseSent()
        _dict["aq_name"] = self.mGetAqName()

        return _dict

    def mUnpopulate(self, aStringfy=False):
        _req = []
        _req.append(self.mGetUUID())
        _req.append(self.mGetStatus())
        _req.append(self.mGetTimeStampStart())
        _req.append(self.mGetTimeStampEnd())
        _req.append(self.mGetCmdType())
        if aStringfy:
            _req.append(json.dumps(self.mGetParams()))
        else:
            _req.append(self.mGetParams())
        _req.append(self.mGetError())
        _req.append(self.mGetErrorStr())
        _req.append(self.mGetBody())
        _req.append(self.mGetXml())
        _req.append(self.mGetStatusInfo())
        _req.append(self.mGetClusterName())
        if aStringfy:
            _req.append(str(self.mGetLock()))
            _req.append(json.dumps(self.mGetData()))
        else:
            _req.append(self.mGetLock())
            _req.append(self.mGetData())
        _req.append(self.mGetSubCommand())
        _req.append(self.mGetResponseSent())
        _req.append(self.mGetAqName())
        return _req

    def mPopulate(self, aReq):

        _req = aReq
        if _req:
            _req_list = list(_req)
            _num_columns = len(self.mGetColumns())
            _num_fetched_columns = len(_req_list)
            #This can only happen if the SQL used is incomplete. Make sure to use mLoadRequestFromDB directly for getting all columns.
            if _num_fetched_columns < _num_columns:
                _req_list.extend("Undef"*(_num_columns-_num_fetched_columns))
            self.mSetUUID(_req_list[0])
            self.mSetStatus(_req_list[1])
            self.mSetTimeStampStart(_req_list[2])
            self.mSetTimeStampEnd(_req_list[3])
            self.mSetCmdType(_req_list[4])
            self.mSetParams(ast.literal_eval(_req_list[5]))
            self.mSetError(_req_list[6])
            self.mSetErrorStr(_req_list[7])
            self.mSetBody(_req_list[8])
            self.mSetXml(_req_list[9])
            self.mSetStatusInfo(_req_list[10])
            self.mSetClusterName(_req_list[11])
            self.mSetLock(_req_list[12])
            self.mSetData(_req_list[13])
            if _req_list[14] is None or (_req_list[14] is not None and len(_req_list[14]) == 0):
                if self.__cmdtype is not None and "." in self.__cmdtype:
                    self.__subcommand = self.__cmdtype.split(".")[1]
            else:
                self.mSetSubCommand(_req_list[14])
            self.mSetResponseSent(_req_list[15])
            self.mSetAqName(_req_list[16])

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


