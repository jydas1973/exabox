#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsHistoryOCI.py /main/2 2024/10/07 18:01:10 ririgoye Exp $
#
# ExaKmsHistoryOCI.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsHistoryOCI.py - Histortical operations for ExaKmsOCI entries
#
#    DESCRIPTION
#      Histortical operations for ExaKmsOCI entries
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    09/25/24 - Bug 36390923 - REMOVE EXAKMS HISTORY VALIDATION
#                           ACROSS HOSTS
#    aypaul      06/01/22 - Creation
#
import os,re, socket
from exabox.exakms.ExaKmsHistory import ExaKmsHistory
from exabox.core.Context import get_gcontext
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsOperationType
from exabox.exakms.ExaKmsHistoryNode import ExaKmsHistoryNode

class ExaKmsHistoryOCI(ExaKmsHistory):

    def __init__(self, _exakms_oci_object):

        if not get_gcontext().mCheckConfigOption('exakms_bucket_primary'):
            raise ValueError("'exakms_bucket_primary' configure parameter not set in exabox.conf")
        self.__bucket = get_gcontext().mCheckConfigOption("exakms_bucket_primary")
        self.__backupBucket = get_gcontext().mCheckConfigOption("exakms_bucket_secondary")

        self.__exakms = _exakms_oci_object

    def mUpdateExaKmsHistoryFile(self, aColumns: str, aContent: str) -> str:
        _columns = aColumns
        # Check that column names are correct
        _rows = aContent.split('\n')
        _old_columns = _rows[0]

        if _old_columns == _columns:
            return aContent

        # Update to newest columns
        if len(_rows) <= 4:
            return _columns
        
        re.sub(_old_columns, _columns, aContent)

        # Check all entries for missing values
        _new_rows = [_columns.strip('\n') + '\n']

        for _row in _rows[3:]:
            # Skip if row is empty
            if len(_row) == 0:
                continue

            # Split the row by column
            _values = [_val.strip() for _val in _row.split('\t')]

            # Check if values match the number of columns
            _column_count = len(_columns.split('\t'))
            if _column_count > len(_values):
                for i in range(_column_count - len(_values)):
                    _values.append('Unknown')

            # Rebuild entry string
            _new_row = '\t'.join(_values)
            _new_rows.append(_new_row)

        # Rebuild whole file
        return '\n'.join(_new_rows)


    def mPutExaKmsHistory(self, aKmsEntry: ExaKmsEntry, aOperationType: str) -> None:
        _columns = 'Timestamp\tHost\tKey\tOperation\tID\tLabel\n'
        _columns += '-' * 50 + '\n\n'
        _curr_time = ExaKmsEntry.mGetCurrentTime()
        _local_hostname = socket.getfqdn()
        _key = f'{aKmsEntry}'
        _op = aOperationType
        _op_id = aKmsEntry.mGetHash()
        _label = aKmsEntry.mGetLabel()
        _new_entry = f'{_curr_time}\t{_local_hostname}\t{_key}\t{_op}\t{_op_id}\t{_label}\n'

        # Get and modify history log file in main bucket
        try:
            _obj = self.__exakms.mGetOSS(self.__bucket, 'changes.txt')
            _changes = _obj.data.content.decode('utf-8')

            # Update log file if needed
            _column_names = _columns.split('\n')[0]
            _changes = self.mUpdateExaKmsHistoryFile(_column_names, _changes)
        except:
            _changes = _columns

        _changes += _new_entry
        self.__exakms.mPutOSS(self.__bucket, 'changes.txt', _changes)

        #  Get and modify history log file in backup bucket
        if self.__backupBucket:
            try:
                _obj = self.__exakms.mGetOSS(self.__backupBucket, 'changes.txt')
                _changes = _obj.data.content.decode('utf-8')

                # Update log file if needed
                _changes = self.mUpdateExaKmsHistoryFile(_columns, _changes)
            except:
                _changes = _columns

            _changes += _new_entry
            self.__exakms.mPutOSS(self.__backupBucket, 'changes.txt', _changes)

    def mGetExaKmsHistory(self, aUser: str, aHostName: str, aNumEntries: int) -> list:
        _columns = 'Timestamp\tHost\tKey\tOperation\tID\tLabel\n'
        _columns += '-' * 50 + '\n\n'
        _exakms_history_list = list()

        try:
            _obj = self.__exakms.mGetOSS(self.__bucket, 'changes.txt')
            _exakms_complete_history = _obj.data.content.decode('utf-8')

            # Update string if needed
            _exakms_complete_history = self.mUpdateExaKmsHistoryFile(_columns, _exakms_complete_history)
            
        except:
            _exakms_complete_history = _columns

        _exakms_complete_history_list = _exakms_complete_history.split(os.linesep)
        _exakms_complete_history_list = _exakms_complete_history_list[::-1]

        for _exakms_entry in _exakms_complete_history_list:
             _exakms_entry = re.sub(' +', ' ', _exakms_entry)
             _exakms_entry_list = _exakms_entry.split("\t")
             if len(_exakms_entry_list) >= 4 and _exakms_entry_list[0] != "Timestamp":
                 _entry_time = f"{_exakms_entry_list[0]}"
                 _entry_src = f"{_exakms_entry_list[1]}"
                 _current_exakms_str = _exakms_entry_list[2]
                 _entry_user = _current_exakms_str.split(" ")[2].split("@")[0]
                 _entry_host = _current_exakms_str.split(" ")[2].split("@")[1]
                 _entry_operation = f"{_exakms_entry_list[3]}"

                 if aHostName is not None and aHostName.split(".")[0] != _entry_host.split(".")[0]:
                     continue
                 if aUser is not None and aUser != _entry_user:
                     continue

                 try:
                     _entry_operation_id = f"{_exakms_entry_list[4]}"
                     _entry_label = _exakms_entry_list[5]
                 except IndexError:
                     _entry_operation_id = 'Unknown'
                     _entry_label = 'Unknown'

                 if _exakms_entry_list[3] == ExaKmsOperationType.INSERT:
                     _entry_operation = f"{ExaKmsOperationType.INSERT}ed"
                 if _exakms_entry_list[3] == ExaKmsOperationType.DELETE:
                     _entry_operation = f"{ExaKmsOperationType.DELETE}d"

                 _exakms_history_node = ExaKmsHistoryNode(_entry_time, _entry_operation, _entry_user, _entry_host, aEntryOperationId=_entry_operation_id, aEntryLabel=_entry_label, aEntrySrcHost=_entry_src)
                 _exakms_history_list.append(_exakms_history_node.mToJson())
                 if len(_exakms_history_list) >= aNumEntries:
                     break

        return _exakms_history_list

