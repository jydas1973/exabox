#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_prechecks.py /main/1 2024/05/28 14:07:47 dekuckre Exp $
#
# handler_prechecks.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      handler_prechecks.py - Add prechecks for dom0
#
#    DESCRIPTION
#      Add prechecks for dom0 to be invoked prior to moving it from ExaCS 
#      to ExaDBXS
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    05/27/24 - 36663068: Add prechecks
#

import os
from typing import Tuple
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.ovm.clucontrol import exaBoxCluCtrl

class ExacomputePrechecks(JDHandler):
    # EXIT CODES
    SUCCESS = 0

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/prechecks.json"))
        
    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver func for precheck on specific Dom0, and will 
        NOT require an XML as input (only a payload in JSON format 
        with a predefined JSON Schema)

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """
        _dom0 = self.mGetOptions().jsonconf.get("hostname")        
        ebLogInfo(f"Started precheck for: '{_dom0}'")
        
        _rc = ExacomputePrechecks.SUCCESS
        _response = {}

        _ebox = exaBoxCluCtrl(get_gcontext())
        _exascale = ebCluExaScale(_ebox)
        _exascale.mRunExaDbXsChecks([[_dom0, None]])

        return _rc, _response

