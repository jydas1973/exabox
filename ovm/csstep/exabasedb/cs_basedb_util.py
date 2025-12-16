#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exabasedb/cs_basedb_util.py /main/1 2025/06/15 06:03:10 prsshukl Exp $
#
# cs_basedb_util.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_basedb_util.py - step wise Create Service UTILities for BaseDB
#
#    DESCRIPTION
#      Invoked from create service  stepwise execution classes
#
#    NOTES
#      csBaseDbUtil
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    06/11/25 - Creation
#

from exabox.core.Error import ebError, ExacloudRuntimeError, gProvError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogTrace
from exabox.core.Node import exaBoxNode
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.clumisc import ebMigrateUsersUtil
from base64 import b64decode
import hashlib
import time, json
import os

# This class contains utility functions used by create service for BaseDB
# step wise execution classes
class csBaseDbUtil(object):

    def mCreateUser(self, aExaBoxCluCtrlObj, aOptions, aStepList, aStep):
        _ebox = aExaBoxCluCtrlObj
        steplist = aStepList
        step = aStep
        imageBom = ImageBOM(_ebox)

        if not imageBom.mIsSubStepExecuted(step, "OPC_USER"):
            _basedb_opc_config = _ebox.mCheckConfigOption("basedb_opc_config")
            if _basedb_opc_config:
                _opcgid = _basedb_opc_config.get('opc_guid', None)
                _opcuid = _basedb_opc_config.get('opc_uid', None)

                if _opcuid and _opcgid:
                    _step_time = time.time()
                    _ebox.mUpdateStatusCS(True, step, steplist, aComment='Create opc user for BaseDB')
                    _ebox.mGetBaseDB().mAddUserDomU("opc", _opcuid, _opcgid, aSudoAccess=True)
                    _ebox.mLogStepElapsedTime(_step_time, 'Create opc user for BaseDB')
                else:
                    _detail_error = f"basedb_opc_config has value {_basedb_opc_config}.Add the uid and guid for opc user in exabox.conf."
                    raise ExacloudRuntimeError(aErrorMsg=_detail_error)

            else:
                _detail_error = f"basedb_opc_config parameter is empty or does not exist: {_basedb_opc_config}"
                raise ExacloudRuntimeError(aErrorMsg=_detail_error)

