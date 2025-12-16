#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_exacompute_ingestion.py /main/1 2023/05/23 15:27:29 gparada Exp $
#
# handler_exacompute_ingestion.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      handler_exacompute_ingestion.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Executes 'Initial Ingestion' operations on specific Dom0
#
#    NOTES
#      Initial Ingestion calls edvutil command on OL8
#
#    MODIFIED   (MM/DD/YY)
#    gparada     05/18/23 - 35370215 Handle InitiatorID for ECRA.
#    gparada     05/18/23 - Creation
#

import os
from typing import Tuple
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.clumisc import ebMiscFx
from exabox.utils.node import connect_to_host

class ExacomputeIngestionHandler(JDHandler):
    # EXIT CODES
    SUCCESS = 0
    ERR_INITIAL_INGESTION = 1

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/exacomputeIngestion.json"))
        
    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver function for the Exacompute Ingestion endpoint module
        This module is meant to allow the execution of 'Initial Ingestion' operations
        on specific Dom0, and will NOT require an XML as input (only
        a payload in JSON format with a predefined JSON Schema)

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """
        def _getInitialIngestionResponse(aHost,aIngestionId):
            return {
                "ec_details": {
                    f"{aHost}": f"{aIngestionId}"
                }
            }

        _dom0 = self.mGetOptions().jsonconf.get("hostname")        
        ebLogInfo(f"Started Initial Ingestion process for: '{_dom0}'")
        
        _rc = ExacomputeIngestionHandler.SUCCESS
        _response = {}
        _ingestionId = ""

        try:
            _ingestionId = ebMiscFx.getInitialIngestion(_dom0)            
            if not _ingestionId:                
                raise Exception("Id could not be retrieved")
            _response = _getInitialIngestionResponse(_dom0,_ingestionId)
        except Exception as e:
            _err_msg = ("Exception retrieving initial ingestion: "
                f", error is: '{e}'")
            ebLogError(_err_msg)
            _rc = ExacomputeIngestionHandler.ERR_INITIAL_INGESTION
        finally:
            ebLogInfo("Initial Ingestion process finished.")

        return _rc, _response

