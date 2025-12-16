#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsHistorySIV.py /main/5 2024/10/07 18:01:10 ririgoye Exp $
#
# ExaKmsHistorySIV.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsHistorySIV.py - Historical operations for ExaKmsSIV entries
#
#    DESCRIPTION
#      Historical operations for ExaKmsSIV entries
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    09/25/24 - Bug 36390923 - REMOVE EXAKMS HISTORY VALIDATION
#                           ACROSS HOSTS
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    alsepulv    08/23/22 - Creation
#

import base64
import oci
from oci.vault.models import (Base64SecretContentDetails, CreateSecretDetails,
                              UpdateSecretDetails)
import os
import re
import socket

from exabox.core.Context import get_gcontext
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsOperationType
from exabox.exakms.ExaKmsEntrySIV import ExaKmsEntrySIVRSA
from exabox.exakms.ExaKmsHistory import ExaKmsHistory
from exabox.exakms.ExaKmsHistoryNode import ExaKmsHistoryNode
from exabox.log.LogMgr import ebLogWarn


class ExaKmsHistorySIV(ExaKmsHistory):

    def __init__(self, aExaKmsSIVObject: ExaKmsEntrySIVRSA):

        if not get_gcontext().mCheckConfigOption("exakms_vault_id"):
            raise ValueError("'exakms_vault_id' configure parameter not set in "
                             "exabox.conf")
        self.__vault = get_gcontext().mCheckConfigOption("exakms_vault_id")
        self.__backup_vault = get_gcontext().mCheckConfigOption(
                                                      "exakms_backup_vault_id")
        self.__compartment_id = get_gcontext().mCheckConfigOption(
                                                       "exakms_compartment_id")
        self.__key_id = get_gcontext().mCheckConfigOption("kms_key_id")
        self.__exakms = aExaKmsSIVObject


    def mPutExaKmsHistory(self, aKmsEntry: ExaKmsEntry,
                          aOperationType: str) -> None:

        _curr_time = ExaKmsEntry.mGetCurrentTime()
        _local_hostname = socket.getfqdn()
        _key = f'{aKmsEntry}'
        _op = aOperationType
        _op_id = aKmsEntry.mGetHash()
        _label = aKmsEntry.mGetLabel()
        _new_entry = f'{_curr_time}\t{_local_hostname}\t{_key}\t{_op}\t{_op_id}\t{_label}\n'

        self.mModifyLogFile(_new_entry)

        if self.__backup_vault:
            self.mModifyLogFile(_new_entry, aBackup=True)

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

    def mModifyLogFile(self, aNewEntry: str, aBackup: bool = False) -> None:
        _columns = 'Timestamp\tHost\tKey\tOperation\tID\tLabel\n'
        _columns += '-' * 50 + '\n\n'
        _create_secret = False
        _vault = self.__vault
        if aBackup:
            _vault = self.__backup_vault

        # Get and modify history log file
        try:
            _secret = self.__exakms.mGetSecretsClient().get_secret_bundle_by_name(
                                                    "changes.txt", _vault).data
            _changes = base64.b64decode(
                       _secret.secret_bundle_content.content.encode(
                       "utf-8")).decode("utf-8")

            # Update log file if needed
            _changes = self.mUpdateExaKmsHistoryFile(_columns, _changes)
        except Exception:
            _changes = _columns
            _create_secret = True

        _changes += aNewEntry

        # Encode data
        _encoded_data = base64.b64encode(
                        _changes.encode("utf-8")).decode("utf-8")
        _secret_content = Base64SecretContentDetails(content_type="BASE64",
                                                     content=_encoded_data)

        if _create_secret:
            self.mCreateSecret(_secret_content, aBackup)
        else:
            self.mUpdateSecret(_secret, _secret_content, aBackup)

    def mCreateSecret(self, aSecretContent: Base64SecretContentDetails,
                      aBackup: bool) -> None:
        _vault = self.__vault
        if aBackup:
            _vault = self.__backup_vault

        # Create secret
        _secret_details = CreateSecretDetails(key_id=self.__key_id,
                                          compartment_id=self.__compartment_id,
                                          vault_id=_vault,
                                          secret_name="changes.txt",
                                          secret_content=aSecretContent)

        # Push secret to OCI Vault
        try:
            _vault_client = oci.vault.VaultsClientCompositeOperations(_vault)
            _vault_client.create_secret_and_wait_for_state(
               create_secret_details=_secret_details,
               wait_for_states=[oci.vault.models.Secret.LIFECYCLE_STATE_ACTIVE])

        except Exception as e:
            _msg = ("An error has occured while creating the secret "
                    f"'changes.txt': {e}")
            ebLogWarn(_msg)

    def mUpdateSecret(self, aSecret, aSecretContent: Base64SecretContentDetails,
                      aBackup: bool) -> None:
        _vault = self.__vault
        if aBackup:
            _vault = self.__backup_vault

        # Update secret
        _secret_details = UpdateSecretDetails(secret_content=aSecretContent)

        try:
            # Push secret to OCI Vault
            self.__exakms.mGetVaultClient().update_secret(
                                       secret_id=aSecret.secret_id,
                                       update_secret_details=_secret_details)
            # Delete previous secret version
            self.__exakms.mDeleteSecretVersions(aSecret)

        except Exception as e:
            _msg = ("An error has occured while updating the secret "
                       f"'changes.txt' {e}")
            ebLogWarn(_msg)

    def mGetExaKmsHistory(self, aUser: str, aHostName: str,
                          aNumEntries: int) -> list:
        _columns = 'Timestamp\tHost\tKey\tOperation\tID\tLabel\n'
        _columns += '-' * 50 + '\n\n'
        _exakms_history_list = list()

        try:
            _secret = self.__exakms.mGetSecretsClient().get_secret_bundle_by_name(
                      "changes.txt", self.__vault).data
            _exakms_complete_history = base64.b64decode(
                                  _secret.secret_bundle_content.content.encode(
                                  "utf-8")).decode("utf-8")

            # Update log file if needed
            _exakms_complete_history = self.mUpdateExaKmsHistoryFile(_columns, _exakms_complete_history)
        except Exception as e:
            ebLogWarn("An exception ocurred while trying to get the exakms "
                      f"history log file: {e}")
            return []

        _exakms_complete_history_list = _exakms_complete_history.split(os.linesep)
        _exakms_complete_history_list = _exakms_complete_history_list[::-1]
        _current_local_host = socket.getfqdn()

        for _exakms_entry in _exakms_complete_history_list:
             _exakms_entry = re.sub(' +', ' ', _exakms_entry)
             _exakms_entry_list = _exakms_entry.split("\t")
             if len(_exakms_entry_list) >= 6 and _exakms_entry_list[0] != "Timestamp":
                 _entry_time = f"{_exakms_entry_list[0]}"
                 _exakms_src_host = _exakms_entry_list[1]
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

                 _exakms_history_node = ExaKmsHistoryNode(_entry_time, _entry_operation, _entry_user, _entry_host, aEntryOperationId=_entry_operation_id, aEntryLabel=_entry_label, aEntrySrcHost=_exakms_src_host)
                 _exakms_history_list.append(_exakms_history_node.mToJson())
                 if len(_exakms_history_list) >= aNumEntries:
                     break

        return _exakms_history_list
