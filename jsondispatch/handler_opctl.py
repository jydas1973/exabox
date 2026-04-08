#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_opctl.py /main/1 2026/01/28 03:29:47 nisrikan Exp $
#
# handler_opctl.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      handler_opctl.py - jsondispatch handler opctl operations
#
#    DESCRIPTION
#      jsondispatch handler for Operator Access Control Management Operations
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    nisrikan  01/20/26 - Bug 38702503 - NEED A MECHANISM TO ROUTE CALLS TO OPCTL IN CASE OF NODE CONNECTION FAILURES
#



import os
import sys
import traceback
from typing import Tuple
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace
from exabox.ovm.opctlExaCSMgr import ExaCSExacloudWrapper
from exabox.core.Context import get_gcontext
from exabox.ovm.clucontrol import exaBoxCluCtrl

class OpctlExaCSHandler(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):
        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/opctl_exacs.json"))
        self.requestobj = aRequestObj
        self.payload = None

    def mValidatePayload(self):
        _json_payload = self.mGetPayload()
        
        # Validate resource Type
        _resourceType = _json_payload.get("resourceType")
        if _resourceType is None:
            return -1, "Invalid payload, resourceType missing"
        elif  _resourceType != "cloudexadatainfrastructure":
            return -1, f"Unsupport exadata type. {_resourceType} is not supported"
        
        # Validate user commands
        _user_cmd = _json_payload.get("usercmd")
        if _user_cmd is None: 
            return -1, "Invalid payload, usercmd missing"
        elif _user_cmd not in ["assign", "create_user", "delete_user"]:
            return -1, f"User command {_user_cmd} is not supported"

        # Validate idemtoken
        if _json_payload.get("idemtoken") is None:
            return -1, "Invalid payload, idemtoken missing"

        # Validate host info
        _host_info = _json_payload.get("hostInfo")
        if _host_info is None: 
            return -1, "Invalid payload, hostInfo missing"
        elif "dom0s" not in _host_info or "cells" not in _host_info:
            return -1, "hostInfo does not contain dom0s and cells information"
            
        self.host_info = _host_info
        
        # Conditional validation
        if _user_cmd == "assign":
            if _json_payload.get("assignInfo") is None:
                return -1, "assignInfo required for assign operation"
            if _json_payload.get("operation") is None:
                return -1, "operation required for assign operation"
            valid_operations = ["install", "deploy", "upgrade", "undeploy", "collectDebugLog", "getVersion"]
            if _json_payload["operation"] not in valid_operations:
                return -1, f"Invalid operation: {_json_payload['operation']}"
        
        elif _user_cmd == "create_user":
            required_fields = ["username", "accessRequestId", "auditType", "publicKey", "acpRequestList", "rpmVersion"]
            for field in required_fields:
                if _json_payload.get(field) is None:
                    return -1, f"{field} required for create_user operation"
        
        elif _user_cmd == "delete_user":
            required_fields = ["username", "rpmVersion"]
            for field in required_fields:
                if _json_payload.get(field) is None:
                    return -1, f"{field} required for delete_user operation"
          
        self.payload = _json_payload
                    
        return 0, ""

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver function for the Opctl endpoint module
        This module is meant to allow the execution of 'opctl' operations
        on specific Nodes, and will NOT require an XML as input (only
        a payload in JSON format with a predefined JSON Schema)

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """
        _json_payload = self.mGetPayload()

        # json payload minimal validation is done using schema; remaining subset of validation are done here
        _rc, _err_msg = self.mValidatePayload()
        if _rc != 0:
            # Always return success; the response will be sent to opctl mid-tier.
            return 0, {"status": 301, "errorMessage": _err_msg}

        _opctl_op = self.payload["usercmd"]
        _ebox = exaBoxCluCtrl(get_gcontext())

        ebLogInfo(f"Received opctl_cmd operation: '{_opctl_op}'")
        
        # Create opctl object
        if self.payload["resourceType"] == "cloudexadatainfrastructure":
            _opctl_handle = ExaCSExacloudWrapper(_ebox, "cloudexadatainfrastructure", self.requestobj, "create_logger", self.mGetOptions(), self.host_info)
            try:
                _rc = _opctl_handle.execute_cmd()
                ebLogInfo(f"Execution of opctl_cmd operation: '{_opctl_op}' finished with return code: {_rc}")
            # We suppress exceptions in here, as long as _rc is
            # non-zero, the request will be marked as error
            # with Worker.py logic
            except Exception as e:
                _err_msg = ("Exception happened while running: "
                    f"'{_opctl_op}', error is: '{e}' ")
                ebLogError(_err_msg)
                ebLogTrace(f"{_err_msg} call stack '{self.mGetStackTrace()}'")
                _response = {"status": 500, "errorMessage": _err_msg, "trace_info": self.mGetStackTrace()[:300]}
            # If request is successful, we assign the json-dispatch
            # response to be the opctl response
            else:
                _response = {"status": 200} if _rc == 0 else {"status": 500, "errorMessage": f"Execution failed with return code {_rc}"}
            # Regardless of error or success, we'll try to log the contents of
            # the _opctl_handle object
            finally:
                ebLogTrace("Opctl output: " f"'{_response}'")  # Adjust accordingly

        return 0, _response

    def mGetStackTrace(self):
        _tb = sys.exc_info()[2]
        _tb = traceback.format_tb(_tb)
        return '\n'.join(_tb)
