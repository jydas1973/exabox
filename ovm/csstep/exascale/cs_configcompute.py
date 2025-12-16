#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/cs_configcompute.py /main/6 2025/08/05 11:43:03 rajsag Exp $
#
# cs_configexascale.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_configexascale.py - Create Service CONFIG EXASCALE
# 
#   FUNCTION:
#      Implements the Configure Exascale on Computes for exascale create service execution 
#
#    NOTES
#      Invoked from cs_driver.py
#
#    EXTERNAL INTERFACES:
#      csConfigExascale ESTP_CONFIG_EXASCALE
#
#    INTERNAL CLASSES:
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    09/11/24 - Bug 37045639 - EXASCALE: DELETE SERVICE SHOULD REMOVE STALE FILES FROM VAULT
#    pbellary    06/21/24 - ENH 36690743 - EXACLOUD: IMPLEMENT OEDA STEPS FOR EXASCALE CREATE SERVICE
#    pbellary    06/14/24 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
#    pbellary    06/06/24 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
#    pbellary    06/06/24 - Creation
#
from exabox.log.LogMgr import ebLogTrace
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.cs_constants import csXSConstants, csXSEighthConstants

# This class implements doExecute and undoExecute functions
# for the ESTP_CONFIG_COMPUTE step of create service
# This class primarily invokes OEDA do/undo Configure Exascale on Computes
class csConfigCompute(CSBase):
    def __init__(self):
        self.step = 'ESTP_CONFIG_COMPUTE'

    def doExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csConfigCompute: Entering doExecute')
        _ebox = aCluCtrlObj
        _step_list = aStepList
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, False)
        #
        # Execute OEDA Configure Exascale on Computes
        #
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_CONFIG_COMPUTE, dom0Lock=False)
        ebLogTrace('csConfigCompute: Completed doExecute Successfully')

    def undoExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csConfigCompute: Entering undoExecute')
        _ebox = aCluCtrlObj
        _step_list = aStepList
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, False)

        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_CONFIG_COMPUTE, undo=True, dom0Lock=False)

        ebLogTrace('csConfigCompute: Completed undoExecute Successfully')
