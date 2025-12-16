#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_requests.py /main/2 2023/12/14 12:37:54 aypaul Exp $
#
# SLA.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      requests.py - requests jsondispatch endpoint
#
#    DESCRIPTION
#      Provide functionality of endpoint to fetch requests
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      12/07/2023 - Enh#36060629 Pending exacloud operations list.
#    jesandov    21/09/22 - Creation
#

from multiprocessing import Pool, TimeoutError
import time
import os

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
                               node_exec_cmd, node_read_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler


class RequestsHandler(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetEmptyPayloadAllowed(True)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/requests.json"))


    def mFilterByColumns(self, aColumnsStr, aRequests):
        _columns = aColumnsStr.split(",")

        for _req in aRequests:
            for _col in list(_req.copy().keys()):
                if _col not in _columns:
                    _req.pop(_col)

    def mExecute(self):

        _requests = []

        if self.mGetOptions().jsonconf is None:
            _requests = self.mGetDB().mFilterRequests()
        else:
            _offset = None
            _limit  = None
            _args = self.mGetOptions().jsonconf.copy()

            for _key in _args.copy():
                if _key == "offset":
                    _offset = _args.pop(_key)
                elif _key == "limit":
                    _limit  = _args.pop(_key)

            ebLogTrace(f"Querying DB using args: {_args}, limit: {_limit}, offset: {_offset}")
            _requests = self.mGetDB().mFilterRequests(_args, _limit, _offset)

        for _req in _requests:
            _req['body'] = _req['body'].split("\n")

        if _args is not None and "columns" in list(_args.keys()):
            self.mFilterByColumns(_args['columns'], _requests)

        ebLogTrace(f"Requested data from the requests table: {_requests}")

        return (0, _requests)


# end of file
