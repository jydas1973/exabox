"""
 Copyright (c) 2014, 2022, Oracle and/or its affiliates.

NAME:
    RequestsHandler - Basic functionality

FUNCTION:
    Request endpoint of the managment

NOTE:
    None    

History:
    hgaldame    10/27/2022 - 34738764 - ociexacc: exacc remoteec enhancements
                             for exacloud requests
    jesandov    26/03/2019 - File Creation
"""



import os
import sys
import uuid

from exabox.exatest.common.ebExacloudUtil import ebExacloudUtil
from exabox.BaseServer.BaseEndpoint import BaseEndpoint
from exabox.agent.ebJobRequest import ebJobRequest

class RequestsEndpoint(BaseEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        #Initialization of the base class
        BaseEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

        #Extra params
        self.__exacloudUtil = self.mGetShared()['util']
        self.__database = self.mGetShared()['db']
        self.__exacloudCmdBlackList = self.mGetConfig().mGetConfigValue("exacloud_request_qry_blacklist")
        self.__exacloudRequestDefaultOrder = self.mGetConfig().mGetConfigValue("exacloud_default_order_qry_request")

    def mFilterByColumns(self, aColumnsStr, aRequests):
        _columns = aColumnsStr.split(",")

        for _req in aRequests:
            for _col in list(_req.copy().keys()):
                if _col not in _columns:
                    _req.pop(_col)

    def mGet(self):

        _requests = ""
        _default_limit_rows_exacc = 20
        _order_by = self.__exacloudRequestDefaultOrder
        _notCondition = self.__exacloudCmdBlackList
        if self.mGetUrlArgs() is None:
            _requests = self.__database.mFilterRequests(aLimit=_default_limit_rows_exacc,
                                                        aNotCondition=_notCondition,
                                                        aOrderBy=_order_by)
        else:
            _offset = None
            _limit  = None

            if self.mGetUrlArgs() is not None:
                for _key in self.mGetUrlArgs().copy():
                    if _key == "offset":
                        _offset = self.mGetUrlArgs().pop(_key)
                    elif _key == "limit":
                        _limit  = self.mGetUrlArgs().pop(_key)
            _limit = _default_limit_rows_exacc if _limit is None else _limit
            _offset = _offset if _offset and _limit and _offset >= _limit else None
            _notCondition = self.__exacloudCmdBlackList if "cmdtype" not in self.mGetUrlArgs().keys() else None
            _requests = self.__database.mFilterRequests(self.mGetUrlArgs(), _limit, _offset, aNotCondition=_notCondition,
                                                        aOrderBy=_order_by)

        for _req in _requests:
            _req['body'] = _req['body'].split("\n")

        if self.mGetUrlArgs() is not None and "columns" in list(self.mGetUrlArgs().keys()):
            self.mFilterByColumns(self.mGetUrlArgs()['columns'], _requests)

        self.mGetResponse()["text"] = _requests

    def mPut(self):

        _oldReq = self.mGetShared()['db'].mGetRequest(self.mGetBody()['uuid'])

        if _oldReq is None:
            self.mGetResponse()['text'] = "Request not found"
            self.mGetResponse()['error'] = "Request not found"
            self.mGetResponse()['status'] = 404

        else:
            _newReq = ebJobRequest(None, {})
            _newReq.mPopulate(_oldReq)

            _disimilitud = _newReq.mFromDict(self.mGetBody())

            if _disimilitud == 0:
                self.mGetResponse()['text'] = "Same data, nothing changed"
                self.mGetResponse()['error'] = "Same data, nothing changed"
            else:
                self.mGetShared()['db'].mUpdateRequest(_newReq)
                self.mGetShared()['db'].mUpdateParams(_newReq)

                _dict = _newReq.mToDict()
                _dict['body'] = _dict['body'].split("\n")
                self.mGetResponse()['text'] = _dict

    def mPost(self):

        _newReq = ebJobRequest(None, {})
        _newReq.mFromDict(self.mGetBody())
        _newReq.mSetUUID(uuid.uuid1())

        self.mGetShared()['db'].mInsertNewRequest(_newReq)

        _dict = _newReq.mToDict()
        _dict['body'] = _dict['body'].split("\n")
        self.mGetResponse()['text'] = _dict



