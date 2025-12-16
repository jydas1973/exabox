#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_giconfig.py /main/4 2024/09/02 17:52:26 ivang Exp $
#
# handler_giconfig.py
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
#    NAME
#      handler_giconfig.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ivang       08/20/24 - bug-36953200: use factory pattern instead of
#                           nesting instances
#    akkar       02/14/24 - Bug-36250866:Change validation for new paylaod
#    akkar       12/08/23 - Creation
#

import os
import json
from typing import Tuple
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.clugiconfigimage import ebCluGiRepoUpdate


class GIConfigHandler(JDHandler):

    # Class attributes
    SUCCESS = 0

    # EXIT CODES
    ERR_INVALID_OPERATION = -1
    ERR_EXECUTE_GICONFIG = -2


    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/giconfigschema.json"))

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver function for the GI config endpoint module
        This module is meant to allow the execution of 'GI config' operations
        on specific Nodes, and will NOT require an XML as input (only
        a payload in JSON format with a predefined JSON Schema)

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """
        _clucontrol = exaBoxCluCtrl(get_gcontext())
        if _clucontrol.mIsOciEXACC():
            return GIConfigHandler.ERR_INVALID_OPERATION, {}
        
        _payload = self.mGetPayload()
        _err_msg = self.mValidateImageInfoPayload(_payload)
        if _err_msg:
            ebLogError(_err_msg)
            return GIConfigHandler.ERR_INVALID_OPERATION, {}

        _gi_operation = _payload.get("type", "ADD")
        ebLogInfo(f"Received GI opeartion operation: '{_gi_operation}'")

        _rc = GIConfigHandler.SUCCESS
        _response = {}

        # Create Gi config and clucontrol object
        #TODO : Add check for old repo format

        try:
            _gi_config_mgr = ebCluGiRepoUpdate._from_payload(_clucontrol, _payload)
            _rc = _gi_config_mgr.mExecute(_payload)
        except Exception as e:
            _err_msg = ("Exception happened while running: "
                f"'{_gi_operation}', error is: '{e}'")
            ebLogError(_err_msg)
            _rc = GIConfigHandler.ERR_EXECUTE_GICONFIG
        else:
            _response = _gi_config_mgr.mGetGIResponseData()

        # Regardless of error or success, we'll try to log the contents of
        # the _gi_config_mgr object
        finally:
            ebLogTrace(f"Gi config opeartion output:'{json.dumps(_gi_config_mgr.mGetGIResponseData(), indent=4)}'")

        return _rc, _response

    def mValidateImageInfoPayload(self, payload:dict) -> str:
        _required_information_list = ["system_type", "image_type", "version", "location", "type"]
        for _required_information in _required_information_list:
            if _required_information not in list(payload.keys()):
                return f"Key: {_required_information} is missing from payload."
        
        # validate repository root
        if not get_gcontext().mGetConfigOptions()['repository_root']:
            return f"Repository root not present"

        return ""