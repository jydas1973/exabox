#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_dactl.py /main/1 2025/06/03 16:46:04 kkviswan Exp $
#
# handler_dactl.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      handler_dactl.py - jsondispatch handler dactl operations
#
#    DESCRIPTION
#      jsondispatch handler for Delegation Access Control Management Operations
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    kkviswan    05/28/25 - 37928955 Delegation Management New ER
#    kkviswan    05/28/25 - Creation
#



import os
import sys
import traceback
from typing import Tuple
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace
from exabox.ovm.dactlMgr import ebDactlMgr


class DaCtlHandler(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/dactl.json"))

    def mValidatePayload(self):
        _json_payload = self.mGetPayload()
        # Validate common parameters & resource Type
        _commonParameters = _json_payload.get("commonParameters")
        if _commonParameters is None:
            return -1, "Invalid payload, commonParameters missing"
        _resourceType = _commonParameters.get("resourceType")
        if _resourceType is None:
            return -1, "Invalid payload, resourceType missing in commonParameters"
        # Validate user commands
        _user_cmd = _json_payload.get("usercmd")
        if _user_cmd is None:
            return -1, "Invalid payload, usercmd missing"

        return 0, ""

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver function for the Dactl endpoint module
        This module is meant to allow the execution of 'dactl' operations
        on specific Nodes, and will NOT require an XML as input (only
        a payload in JSON format with a predefined JSON Schema)

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """
        _json_payload = self.mGetPayload()

        # json payload minimal validation is done using schema; remaining subset of validation are done here
        _rc, _err_msg = self.mValidatePayload()
        if _rc != 0:
            # Always return success; the response will be sent to dactl mid-tier.
            return 0, {"status": 301, "errorMessage": _err_msg}

        _dactl_op = _json_payload.get("usercmd")

        ebLogInfo(f"Received dactl_cmd operation: '{_dactl_op}'")
        # Create dactl object
        # NOTE: All DACTL commands does not require cluster XML file
        _dactl_handle = ebDactlMgr()
        try:
            _rc = _dactl_handle.mExecuteCmd(_json_payload)
            ebLogInfo(f"Execution of dactl_cmd operation: '{_dactl_op}' finished with return code: {_rc}")
        # We supress exceptions in here, as long as _rc is
        # non-zero, the request will be marked as error
        # with Worker.py logic
        except Exception as e:
            _err_msg = ("Exception happened while running: "
                f"'{_dactl_op}', error is: '{e}' ")
            ebLogError(_err_msg)
            ebLogTrace(f"{_err_msg} call stack '{self.mGetStackTrace()}'")
            _response = {"status": 500, "errorMessage": _err_msg, "trace_info": self.mGetStackTrace()[:300]}
        # If request is successful, we assign the json-dispatch
        # response to be the dactl response
        else:
            _response = _dactl_handle.mGetResponseData()
        # Regardless of error or success, we'll try to log the contents of
        # the _dactl_handle object
        finally:
            ebLogTrace("Dactl output: " f"'{_dactl_handle.mGetResponseData()}'")

        return 0, _response

    def mGetStackTrace(self):
        _tb = sys.exc_info()[2]
        _tb = traceback.format_tb(_tb)
        return '\n'.join(_tb)

