#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_exacloud_updaterequest.py /main/1 2024/12/18 17:12:14 piyushsi Exp $
#
# handler_exacloud_updaterequest.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      handler_exacloud_updaterequest.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    piyushsi    12/13/24 - Creation
#

import os
from typing import Tuple
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.utils.node import connect_to_host
from exabox.core.DBStore import ebGetDefaultDB
from exabox.agent.ebJobRequest import ebJobRequest

class ExaCloudUpdateRequest(JDHandler):
    # EXIT CODES
    SUCCESS = 0

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/statusuuid.json"))

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver func to configure dom0 roce stre0 and stre1 interfaces.

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """

        _rc = 0
        _response = {}

        if not self.mGetOptions().jsonconf or "status_uuid" not in self.mGetOptions().jsonconf:
            raise ExacloudRuntimeError(0x0207, 0xA, f'Missing status uuid in the payload')

        _status_uuid = self.mGetOptions().jsonconf.get("status_uuid")
        ebLogInfo(f'UpdateRequestHandler: Status uuid: {_status_uuid}')

        _db = ebGetDefaultDB()
        _reqobj = ebJobRequest(None, {}, aDB=_db)
        _reqobj.mLoadRequestFromDB(_status_uuid)
        _reqobj.mSetStatus('Done')
        _reqobj.mSetError('0')
        _reqobj.mSetData({})
        _reqobj.mSetErrorStr('No Errors')
        _db.mUpdateRequest(_reqobj)

        return _rc, _response
 
