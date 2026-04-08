#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_storage_utility.py /main/1 2026/02/10 12:18:51 jesandov Exp $
#
# handler_storage_utility.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      handler_storage_utility.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    01/26/26 - Creation
#

from multiprocessing import Pool, TimeoutError
import time
import json
import os
import re

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.common import mCompareModel
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check, node_exec_cmd_check,
                               node_exec_cmd, node_read_text_file, node_write_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.core.Error import ExacloudRuntimeError


class StorageUtility(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/storage_utility.json"))

    def mGetStorageStatus(self, aNode):

        _cmd = "cellcli --json -e list griddisk attributes"
        _cmd = f"{_cmd} name, status, asmDiskgroupName, asmDiskName, asmModeStatus, size, asmDeactivationOutcome"

        _, _o, _ = aNode.mExecuteCmd(_cmd)
        _out = _o.read().strip()
        _result = json.loads(_out)["cli-output"]

        return _result

    def mExecute(self):

        _rc = 0
        _response = {}

        _cells = self.mGetOptions().jsonconf.get("cells")

        for _cell in _cells:
            with connect_to_host(_cell, get_gcontext()) as _node:
                _response[_cell] = self.mGetStorageStatus(_node)

        return (0, _response)

# end of the file
