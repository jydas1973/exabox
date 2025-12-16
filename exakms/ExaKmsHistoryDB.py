#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsHistoryDB.py /main/1 2022/06/16 21:47:28 aypaul Exp $
#
# ExaKmsHistoryDB.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsHistoryDB.py - Histortical operations for File based exakms entries
#
#    DESCRIPTION
#      Histortical operations for File based exakms entries
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/01/22 - Creation
#
from exabox.exakms.ExaKmsHistory import ExaKmsHistory
from exabox.core.Context import get_gcontext
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsOperationType
from exabox.core.DBStore import ebGetDefaultDB
from exabox.exakms.ExaKmsHistoryNode import ExaKmsHistoryNode


class ExaKmsHistoryDB(ExaKmsHistory):


    def mPutExaKmsHistory(self, aKmsEntry: ExaKmsEntry, aOperationType: str) -> None:

        _db = ebGetDefaultDB()
        _db.mCreateExaKmsHistoryTable()
        if aOperationType == ExaKmsOperationType.INSERT:
            aOperationType = f"{ExaKmsOperationType.INSERT}ed"
        if aOperationType == ExaKmsOperationType.DELETE:
            aOperationType = f"{ExaKmsOperationType.DELETE}d"

        _db.mInsertIntoExaKmsHistory(aKmsEntry, aOperationType)

    def mGetExaKmsHistory(self, aUser: str, aHostName: str, aNumEntries: int) -> list:
        _db = ebGetDefaultDB()
        _db.mCreateExaKmsHistoryTable()
        _exakms_history_list = list()
        if aHostName is not None:
            _exakms_history_db = _db.mGetRowsFromExaKmsHistory(aUser, aHostName.split(".")[0], aNumEntries)
        else:
            _exakms_history_db = _db.mGetRowsFromExaKmsHistory(aUser, None, aNumEntries)

        for _exakms_history_node in _exakms_history_db:
            _exakms_history_list.append(_exakms_history_node.mToJson())
        return _exakms_history_list