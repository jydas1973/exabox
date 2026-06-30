#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_exabox_conf_operations.py /main/2 2025/05/06 06:50:19 aypaul Exp $
#
# handler_exabox_conf_operations.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
#
#    NAME
#      handler_exabox_conf_operations.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    joysjose    05/04/26 - Restrict exabox conf operation key policy
#    joysjose    04/29/26 - Implement exabox conf sensitive key deny policy
#    aypaul      04/23/25 - Bug#37535214 Use consistent backup before copying file.
#    joysjose    07/25/24 - Handler to control the flow of exabox.conf file
#                           operations
#    joysjose    07/25/24 - Creation
#
import json
import time
import pathlib
import fcntl
import os, subprocess, shlex
from typing import Tuple
from exabox.core.Context import get_gcontext, ReadOnlyDict
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace
from subprocess import PIPE
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.core.Error import ExacloudRuntimeError
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.tools.Utils import mBackupFile

class ExaboxConfOperationsHandler(JDHandler):
    SENSITIVE_EXABOX_CONF_KEYS = frozenset((
        "admin_switchkeys",
        "agent_auth",
        "agent_authkey",
        "default_pwd",
        "db_connstr",
        "default_tls_conf",
        "disable_spwd",
        "dom0client_certificate_path",
        "dom0client_key_path",
        "ec_agent_port",
        "enable_block_opctl",
        "exacc_auth_principals",
        "exacc_mtls",
        "ilom_compute_pwd_b64",
        "ilom_pwd_b64",
        "ilom_cell_pwd_b64",
        "oeda_pwd",
        "root_spwd",
        "ssh_private_key"
    ))
    ALLOWED_UPDATE_EXABOX_CONF_KEYS = frozenset((
        "delete_vmbackup",
        "idle_worker_count",
        "idle_worker_count_nonexacs",
        "max_oss_vmbackups",
        "vmerase_pass",
        "vmbackup2oss_skip_image",
        "worker_connection_timeout",
        "worker_count",
        "worker_count_nonexacs",
        "worker_idle_timeout_minutes",
        "worker_port",
        "worker_port_extravalidation",
        "worker_thread_limit"
    ))
    ALLOWED_VIEW_EXABOX_CONF_KEYS = ALLOWED_UPDATE_EXABOX_CONF_KEYS.union((
        "vmbackup",
    ))

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/exabox_conf_operations.json"))
        
    class FileLockManager(object):
        def __init__(self, lock_file_path):
            pathlib.Path(lock_file_path).touch()
            self.lock_file_path = lock_file_path
            self.lock_file_obj = None

        def __enter__(self):
            self.lock_file_obj = open(self.lock_file_path)
            fcntl.flock(self.lock_file_obj.fileno(), fcntl.LOCK_EX)
            ebLogTrace(f"Locked {self.lock_file_path}")
            

        def __exit__(self, type, value, traceback):
            fcntl.flock(self.lock_file_obj.fileno(), fcntl.LOCK_UN)
            self.lock_file_obj.close()
            ebLogTrace(f"unlocked {self.lock_file_path}")
        
    def mExecuteLocal(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE, aTimeOut=None,
                      aLogOutError=False):
        _args = shlex.split(aCmd)
        _current_dir = aCurrDir
        _stdin = aStdIn
        _std_out = aStdOut
        _stderr = aStdErr
        try:
            _proc = subprocess.Popen(_args, stdin=_stdin, stdout=_std_out, stderr=_stderr, cwd=_current_dir)
            _std_out, _std_err = wrapStrBytesFunctions(_proc).communicate(timeout=aTimeOut)
            _rc = _proc.returncode
        except Exception as e:
            _rc = 2
            _std_out = ""
            _std_err = str(e)

        ebLogTrace(f"*** mExecuteLocal: Executed command: {aCmd}. Return code: {_rc}.")
        if aLogOutError:
            ebLogTrace(f"*** mExecuteLocal: Output: \n{_std_out} Error: \n{_std_err}")
        return _rc, None, _std_out, _std_err
        
    @classmethod
    def _mNormalizeKey(cls, aKey):
        return str(aKey).strip().lower()

    def _mGetAllowedKeys(self, aOperation):
        if aOperation == "view":
            return self.ALLOWED_VIEW_EXABOX_CONF_KEYS
        if aOperation == "update":
            return self.ALLOWED_UPDATE_EXABOX_CONF_KEYS
        return frozenset()

    def mUpdateExaboxConfParam(self, aJsonInput):
        _json_input = aJsonInput
        _exabox_conf_params = {}
        _exabox_conf_path = os.path.join(get_gcontext().mGetBasePath(),'config','exabox.conf')
        _exabox_lock_file = os.path.join(get_gcontext().mGetBasePath(),'config','exabox.conf.lock')
        with self.FileLockManager(_exabox_lock_file):
            with open(_exabox_conf_path,"r") as _conf_file:
                _exabox_conf_params = json.load(_conf_file)
            if "key_value_pair" in list(_json_input.keys()):
                _update_params = _json_input["key_value_pair"]
                ebLogTrace(f"update params : {_update_params}")
                self._mValidateUpdateKeyValuePair(_update_params, _exabox_conf_params)
                for _key,_value in _update_params.items():
                    _normalized_key = self._mNormalizeKey(_key)
                    _exabox_conf_params[_normalized_key] = _value
            else:
                _err_str = f"key_value_pair not present in json payload. Exiting"
                ebLogError(_err_str)
                raise ExacloudRuntimeError(0x0837, 0xA, _err_str)
            
            mBackupFile(_exabox_conf_path, True)
            with open(_exabox_conf_path,"w") as _conf_file:
                json.dump(_exabox_conf_params, _conf_file, indent = 4)
        
    def mBackupExaboxConf(self):
        ebLogInfo(f"base path: {get_gcontext().mGetBasePath()}")
        _exabox_conf_path = os.path.join(get_gcontext().mGetBasePath(),'config','exabox.conf')
        _config_backup_timestamp = str(time.time()).replace(".", "")
        _backup_path = f"{_exabox_conf_path}.{_config_backup_timestamp}"
        _cmd = f"/bin/cp {_exabox_conf_path} {_backup_path}"
        _rc, _, _std_out, _std_err = self.mExecuteLocal(_cmd)
        if _rc == 0:
            ebLogInfo(f"Backup of {_exabox_conf_path} successfully taken to {_backup_path}")
        else:
            _err_str = f"Backing up of exabox.conf Failed"
            ebLogError(_err_str)
            if _std_err:
                ebLogTrace(_std_err)
            raise ExacloudRuntimeError(0x0837, 0xA, _err_str)
        
    #ReadOnlyDicts cannot be serialized. This function is useful for serializing them into JSON.
    def unorderDict(self, aDict):
        _unordered_dict = {}
        for key in list(aDict.keys()):
            if isinstance(aDict[key], ReadOnlyDict):
                _unordered_dict[key] = self.unorderDict(aDict[key]) #ordered dict becomes regular dict
            elif isinstance(aDict[key], tuple):
                _unordered_dict[key] = list(aDict[key]) #tuple becomes list
            else:
                _unordered_dict[key] = aDict[key] #strings stay strings

        return _unordered_dict

    def _mGetRequestedKeys(self, aOperation, aJsonInput):
        if aOperation == "view":
            return aJsonInput.get("keys", [])
        if aOperation == "update":
            _key_value_pair = aJsonInput.get("key_value_pair", {})
            if isinstance(_key_value_pair, dict):
                return list(_key_value_pair.keys())
        return []

    def _mGetDeniedKeys(self, aOperation, aRequestedKeys):
        _allowed_keys = self._mGetAllowedKeys(aOperation)
        return sorted({
            self._mNormalizeKey(_key)
            for _key in aRequestedKeys
            if self._mNormalizeKey(_key) not in _allowed_keys
        })

    def _mBuildDeniedResponse(self, aOperation, aDeniedKeys):
        _sensitive_keys = sorted(
            _key for _key in aDeniedKeys
            if _key in self.SENSITIVE_EXABOX_CONF_KEYS
        )
        if _sensitive_keys:
            _reason = "sensitive_keys_not_allowed"
            _message = (
                f"Operation '{aOperation}' denied because the request contains "
                f"sensitive exabox.conf keys: {', '.join(aDeniedKeys)}"
            )
        else:
            _reason = "keys_not_allowed_for_operation"
            _message = (
                f"Operation '{aOperation}' denied because the request contains "
                f"keys that are not allowed for this endpoint: {', '.join(aDeniedKeys)}"
            )
        ebLogError(_message)
        return {
            "status": "denied",
            "operation": aOperation,
            "reason": _reason,
            "denied_keys": aDeniedKeys,
            "message": _message
        }

    def _mValidateUpdateKeyValuePair(self, aUpdateParams, aExistingParams):
        for _key, _value in aUpdateParams.items():
            _normalized_key = self._mNormalizeKey(_key)
            _existing_value = aExistingParams.get(_normalized_key, None)
            if _existing_value is None and _normalized_key not in aExistingParams:
                _err_str = (
                    f"Key {_normalized_key} is not a valid parameter in exabox.conf. "
                    f"Please verify the keys in input json. Exiting"
                )
                ebLogError(_err_str)
                raise ExacloudRuntimeError(0x0837, 0xA, _err_str)
            if type(_value) is not type(_existing_value):
                _err_str = (
                    f"Key {_normalized_key} must preserve the existing exabox.conf value type. "
                    f"Expected {type(_existing_value).__name__}, got {type(_value).__name__}. Exiting"
                )
                ebLogError(_err_str)
                raise ExacloudRuntimeError(0x0837, 0xA, _err_str)
        
    def mViewExaboxConfParam(self, aJsonInput):
        _json_input = aJsonInput
        _rc = 0
        if "keys" in list(_json_input.keys()):
            _view_params = _json_input["keys"]
            ebLogInfo(f"view params : {_view_params}")
            _result = {}
            for _item in _view_params:
                _lookup_key = self._mNormalizeKey(_item)
                _ret = get_gcontext().mCheckConfigOption(_lookup_key)
                if _ret is not None:
                    _result[_lookup_key] = _ret
                else:
                    ebLogError(f"Key {_lookup_key} is not present in exabox.conf")
                    _rc = 1
                    
            _unordered_result_dict = self.unorderDict(_result) #to convert ReadOnlyDicts to normal dict
            return _rc, _unordered_result_dict
        else:
            _err_str = f"keys not specified in the json for view operation."
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0838, 0xA, _err_str)
        
    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver function to modify exabox.conf parameters.

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """
        _rc = 0
        _response = {}
        _json_input = self.mGetOptions().jsonconf
        input_data = {}
        try:
            if _json_input:
                if isinstance(_json_input, dict):
                    if "operation" in list(_json_input.keys()):
                        _operation = _json_input["operation"]
                        _requested_keys = self._mGetRequestedKeys(_operation, _json_input)
                        _denied_keys = self._mGetDeniedKeys(_operation, _requested_keys)

                        if _denied_keys:
                            _rc = 1
                            _response = self._mBuildDeniedResponse(_operation, _denied_keys)
                            return _rc, _response
                            
                        if _operation == "update":
                            self.mBackupExaboxConf()
                            self.mUpdateExaboxConfParam(_json_input)
                        elif _operation == "view":
                            _rc, _response = self.mViewExaboxConfParam(_json_input)
                        else:
                            _err_str = f"Please provide a valid operation. Either 'view' or 'update' are the valid operations."
                            ebLogError(_err_str)
                            raise ExacloudRuntimeError(0x0837, 0xA, _err_str)
                            
                    else:
                        _err_str = f"operation not specified in the json."
                        ebLogError(_err_str)
                        raise ExacloudRuntimeError(0x0837, 0xA, _err_str)
                        
                else:
                    _error_str = f"Not a valid json. Exiting"
                    raise ExacloudRuntimeError(0x0837, 0xA, _error_str)
            else:
                _error_str = f"Please provide valid input json"
                raise ExacloudRuntimeError(0x0837, 0xA, _error_str)
        except Exception as e:
            ebLogError(f"exabox_conf operation failed with the following error: {str(e)}")
            raise ExacloudRuntimeError(0x0837, 0xA, f"exabox.conf View/Updation Failed with the Error {str(e)}")
        return _rc, _response
