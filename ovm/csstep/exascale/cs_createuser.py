#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/cs_createuser.py /main/5 2025/08/05 11:43:03 rajsag Exp $
#
# cs_createuser.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_createuser - Exascale Create Service CREATE USER
# 
#   FUNCTION:
#      Implements the Create User step for exascale create service execution 
#
#    NOTES
#      Invoked from cs_driver.py
#
#    EXTERNAL INTERFACES:
#      csCreateUser     ESTP_CREATE_USER
#
#    INTERNAL CLASSES:
#
#    MODIFIED   (MM/DD/YY)
#    aararora    07/22/24 - Bug 36864046: Cleanup ssh directory for opc user
#                           during undo step of create user.
#    pbellary    06/21/24 - ENH 36690743 - EXACLOUD: IMPLEMENT OEDA STEPS FOR EXASCALE CREATE SERVICE
#    pbellary    06/14/24 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
#    pbellary    06/06/24 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
#    pbellary    06/06/24 - Creation
#
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.cs_constants import csXSConstants, csXSEighthConstants
from exabox.log.LogMgr import ebLogTrace, ebLogWarn

# This class implements doExecute and undoExecute functions
# for the ESTP_CREATE_USER step of create service
# This class primarily invokes OEDA do/undo create User, secure and remap users
class csCreateUser(CSBase):
    def __init__(self):
        self.step = 'ESTP_CREATE_USER'

    def doExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csCreateUser: Entering doExecute')
        _ebox = aCluCtrlObj

        self.mCreateUser(_ebox, aOptions, aStepList)

        ebLogTrace('csCreateUser: Completed doExecute Successfully')

    def undoExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csCreateUser: Entering undoExecute')
        _ebox = aCluCtrlObj
        _step_list = aStepList
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, False)
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_CREATE_USER, undo=True, dom0Lock=False)
        try:
            self.mDeleteOpcSSHDirectory(_ebox)
        except Exception as ex:
            ebLogWarn(f"Could not remove /home/opc/.ssh directory during undo step. Error: {ex}.")

        ebLogTrace('csCreateUser: Completed undoExecute Successfully')
