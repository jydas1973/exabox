#!/bin/python
#
# $Header: ecs/exacloud/exabox/sop/soputils.py /main/3 2024/05/28 21:09:47 ririgoye Exp $
#
# soputils.py
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
#    NAME
#      soputils.py - public APIs for sop tasks.
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    05/24/24 - Bug 36400562 - Added checks for corrupted or poorly
#                           formatted metadata files
#    aypaul      06/13/23 - Enh#35470717 Ilom connection support via
#                           username/password authentication.
#    aypaul      01/12/23 - Creation
#

import json
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogTrace, ebLogWarn
from exabox.sop.sopscripts import SOPScript, SOPScriptsRepo
from exabox.sop.sopexecutescripts import SOPExecution
from oci.key_management.models import DecryptDataDetails
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.kms.crypt import cryptographyAES
from exabox.ovm.clumisc import ebMiscFx
from oci._vendor.urllib3.exceptions import SSLError


# Public API
__all__ = [
    'process_sop_request'
]

DEFAULT_KEY_LENGTH = 32
DEFAULT_KEY_ALGORITHM = "AES"
OCI_RETRIES = 5

"""
def fetch_ilom_password_oci(aIlomType: str) -> str:
    _ilom_type = aIlomType
    _ilom_password = None

    if _ilom_type is None or _ilom_type not in [COMPUTE_ILOM, STORAGE_ILOM]:
        ebLogError(f"Invalid or empty ilom type specified in payload: {_ilom_type}")
        return _ilom_password

    if not get_gcontext().mCheckConfigOption('kms_key_id'):
            raise ValueError("'kms_key_id' parameter not set in exabox.conf")

    if not get_gcontext().mCheckConfigOption('kms_dp_endpoint'):
        raise ValueError("'kms_dp_endpoint' parameter not set in exabox.conf")

    if not get_gcontext().mCheckConfigOption('exakms_bucket_primary'):
        raise ValueError("'exakms_bucket_primary' parameter not set in exabox.conf")

    _ilom_password_file = f"{_ilom_type}-credentials.dat"
    _kms_key_id = get_gcontext().mCheckConfigOption('kms_key_id')
    _kms_endpoint = get_gcontext().mCheckConfigOption('kms_dp_endpoint')
    _oci_oss_bucket = get_gcontext().mCheckConfigOption('exakms_bucket_primary')

    _oci_factory = ExaOCIFactory()
    _oci_object_storage_client = _oci_factory.get_object_storage_client()
    _oci_kms_crypto_client = _oci_factory.get_crypto_client(_kms_endpoint)
    _namespace = _oci_object_storage_client.get_namespace().data

    _cur_tries = 0
    _exception_msg = None
    _file_contents = None
    while _cur_tries <= OCI_RETRIES:
        try:
            _resp = _oci_object_storage_client.get_object(_namespace, _oci_oss_bucket, _ilom_password_file)

            if not _resp:
                _cur_tries +=1
                ebLogTrace(f'Invalid response from OSS: {_resp}')
            elif _resp.status != 200:
                _cur_tries +=1
                ebLogTrace(f'Invalid response from OSS: {vars(_resp)}')
            else:
                _file_contents = _resp

        except SSLError as e:
            _cur_tries +=1
            _exception_msg = e
            ebLogTrace(f'{e} Retrying... Current retry count: {_cur_tries}')
        except Exception as e:
            _msg = f"Response unexpected: {_resp.__dict__}"
            ebLogError(_msg)
            raise ExacloudRuntimeError(aErrorMsg=_msg) from e

    if _file_contents is None:
        _err_msg = f'OCI error: {_exception_msg} Please retry operation'
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg

    _file_contents_dict = json.loads(_file_contents.data.content.decode('utf-8'))

    _enc_dek = _file_contents_dict.get("encdek", None)
    _enc_password = _file_contents_dict.get("encdata", None)

    _data_details = DecryptDataDetails()
    _data_details.key_id = _kms_key_id
    _data_details.ciphertext = _enc_dek

    _decrypted_dek = _oci_kms_crypto_client.decrypt(decrypt_data_details = _data_details)
    _plaintext_dek = _decrypted_dek.data.plaintext
    _decrypted_password = cryptographyAES().mDecrypt(_plaintext_dek, _enc_password).decode('utf-8')

    return _decrypted_password.strip()
"""

def process_sop_request(aPayload: dict, aUUID: str) -> dict:

    _payload_json = aPayload
    _uuid = aUUID
    _cmd_type = _payload_json.get("cmd", None)
    if _cmd_type is None:
        raise ExacloudRuntimeError(0x815, 0xA, "Command type is missing from payload")

    _return_json = dict()
    if _cmd_type == "start":
        _return_json = sop_execute_scripts(_payload_json, _uuid)
    elif _cmd_type == "delete":
        _return_json = sop_delete_requests_onhost(_payload_json)
    elif _cmd_type == "scriptslist":
        _return_json = sop_list_scripts(_payload_json)
    else:
        _msg = f"Unknown command type: {_cmd_type}"
        ebLogError(_msg)
        raise ExacloudRuntimeError(0x815, 0xA, _msg)

    return _return_json

def sop_execute_scripts(aPayload: dict, aUUID: str) -> dict:
    ebLogInfo(f"Sop script execution utility. Payload: {aPayload}")
    _uuid = aUUID
    _payload_json = aPayload
    _nodes = _payload_json.get("nodes", [])
    _script_name = _payload_json.get("scriptname", "")
    _script_params = _payload_json.get("scriptparams", "")
    _script_payload = _payload_json.get("script_payload", {})
    _script_version = _payload_json.get("version", None)
    _node_type = _payload_json.get("nodetype", None)
    _sop_scripts_execution = SOPExecution(_uuid, _nodes, _script_name, _script_params, _script_payload, _script_version, _node_type)
    _sop_scripts_execution.mExecuteOperation()
    return _sop_scripts_execution.mGetResult()


def sop_delete_requests_onhost(aPayload: dict) -> dict:
    return {}


def sop_list_scripts(aPayloadJSON: dict) -> dict:

    ebLogInfo("Fetching SOP scripts information.")
    _scripts_repo = SOPScriptsRepo()

    # Before retrieving scripts metadata, check if repo contains corrupt files
    _corrupt_files = _scripts_repo.mGetCorruptFiles()

    if len(_corrupt_files) > 0:
        _response = {
            "corrupt_files": _corrupt_files
        }
        return _response

    # If no corrupt files are present, retrieve scripts metadata
    _scripts_metadata = _scripts_repo.mGetScriptsMetadata()
    _payload_json = aPayloadJSON
    if "scriptname" in _payload_json.keys():
        _script_metadata_json = _scripts_metadata.get("scriptname", None)
        if _script_metadata_json is not None:
            return _script_metadata_json
    return _scripts_metadata
