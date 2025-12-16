#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exabasedb/cs_createuser.py /main/1 2025/11/25 05:03:58 prsshukl Exp $
#
# cs_createuser.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_createuser.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/19/25 - Creation
#

from exabox.core.Node import exaBoxNode
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.cs_base import CSBase
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.ovm.csstep.exabasedb.cs_basedb_util import csBaseDbUtil


# This class implements doExecute and undoExecute functions
# for the ESTP_CREATE_USER step of create service
class csCreateUser(CSBase):
    def __init__(self):
        self.step = 'ESTP_CREATE_USER'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        ebLogInfo('csCreateUser: Entering doExecute')
        _ebox = aExaBoxCluCtrlObj
        _csbdu = csBaseDbUtil()

        _csbdu.mCreateUser(_ebox, aOptions, steplist, self.step)

        ebLogInfo('csCreateUser: Completed doExecute Successfully')

  
    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aSteplist):
        ebLogInfo('csCreateUser: Entering undoExecute')
        _ebox = aExaBoxCluCtrlObj
        _step_list = aSteplist

        try:
            _ebox.mGetBaseDB().mDeleteUserDomU("opc")
            self.mDeleteOpcSSHDirectory(_ebox)
        except Exception as ex:
            ebLogWarn(f"Could not remove opc user configuration during undo step. Error: {ex}.")

        ebLogInfo('csCreateUser: Completed undoExecute Successfully')
