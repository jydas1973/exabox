#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsHistoryKVDB.py /main/1 2024/10/11 23:03:23 ririgoye Exp $
#
# ExaKmsHistoryKVDB.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsHistoryKVDB.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    10/08/24 - Bug 37076081 - Created ExaKmsHistoryKVDB file
#    ririgoye    10/08/24 - Creation
#

import os
import json

from exabox.exakms.ExaKmsHistory import ExaKmsHistory
from exabox.core.Context import get_gcontext
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsOperationType
from exabox.exakms.ExaKmsHistoryNode import ExaKmsHistoryNode


class ExaKmsHistoryKVDB(ExaKmsHistory):

    def mLoadJsonFile(self) -> dict:
        # Get path to exakv.db
        _config = get_gcontext().mGetConfigOptions()
        _db_path = os.path.join(get_gcontext().mGetBasePath(), 'db')

        if 'db_dir' in _config.keys():
            _db_path = _config['db_dir']
        
        _file_path = os.path.join(_db_path, 'exakv.db')

        # Convert file to JSON object
        _json_obj = None

        with open(_file_path) as _file:
            _json_obj = json.load(_file)
        
        if _json_obj:
            return _json_obj
        
        return {}


    def mPutExaKmsHistory(self, aKmsEntry: ExaKmsEntry, aOperationType: str) -> None:
        _json_obj = self.mLoadJsonFile()

        if aOperationType == ExaKmsOperationType.INSERT:
            aOperationType = f"{ExaKmsOperationType.INSERT}ed"
        if aOperationType == ExaKmsOperationType.DELETE:
            aOperationType = f"{ExaKmsOperationType.DELETE}d"

        # Insert to JSON history object
        _entry = aKmsEntry.mToJson()
        _key = _entry.mGetKey()
        _json_obj[_key] = _entry

        # Get path to exakv.db
        _config = get_gcontext().mGetConfigOptions()
        _db_path = os.path.join(get_gcontext().mGetBasePath(), 'db')

        if 'db_dir' in _config.keys():
            _db_path = _config['db_dir']
        
        _file_path = os.path.join(_db_path, 'exakv.db')

        # Update exakv.db file
        with open(_file_path) as _file:
            json.dump(_json_obj, _file, indent=4)


    def mGetExaKmsHistory(self, aUser: str, aHostName: str, aNumEntries: int) -> list:
        _json_obj = self.mLoadJsonFile()

        # Create history entry list
        _exakms_history_list = list()

        for _node in _json_obj.values():
            # Retrieve info
            _entry_time = _node.get("creation_time")
            _entry_operation = ExaKmsOperationType.INSERT
            _entry_user = _node.get("exacloud_hostname")
            _entry_host = _node.get("key")
            # Build node and add to list
            _exakms_history_node = ExaKmsHistoryNode(_entry_time, _entry_operation, _entry_user, _entry_host)
            _exakms_history_list.append(_exakms_history_node.mToJson())

        return _exakms_history_list
