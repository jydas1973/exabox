#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/cs_createstorage.py /main/4 2025/08/05 11:43:03 rajsag Exp $
#
# cs_createstorage.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_createstorage.py - Create Service CREATE STORAGE
# 
#   FUNCTION:
#      Implements the Create Storage step for exascale create service execution 
#
#    NOTES
#      Invoked from cs_driver.py
#
#    EXTERNAL INTERFACES:
#      csCreateStorage ESTP_CREATE_STORAGE
#
#    INTERNAL CLASSES:
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    06/21/24 - ENH 36690743 - EXACLOUD: IMPLEMENT OEDA STEPS FOR EXASCALE CREATE SERVICE
#    pbellary    06/14/24 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
#    pbellary    06/06/24 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
#    pbellary    06/06/24 - Creation
#
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.log.LogMgr import ebLogTrace, ebLogWarn, ebLogError
from exabox.ovm.csstep.cs_constants import csXSConstants, csXSEighthConstants

# This class implements doExecute and undoExecute functions
# for the ESTP_CREATE_STORAGE step of create service
# This class primarily invokes OEDA do/undo Setup cell, Calibrate cell, Verify RDMA Network Fabric Connectivity
class csCreateStorage(CSBase):
    def __init__(self):
        self.step = 'ESTP_CREATE_STORAGE'

    def doExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csCreateStorage: Entering doExecute')
        _ebox = aCluCtrlObj
        _step_list = aStepList
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, False)
        _ebox.mAcquireRemoteLock()

        #
        # Execute OEDA SETUP_CELL
        #
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_SETUP_CELL, dom0Lock=False)

        _ebox.mReleaseRemoteLock()

        #
        # Execute Verify RDMA Network Fabric Connectivity
        #
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_VERIFY_FABRIC)

        #
        # Execute OEDA Calibrate Cells
        #
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_CALIBRATE_CELLS)

        ebLogTrace('csCreateStorage: Completed doExecute Successfully')

    def undoExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csCreateStorage: Entering undoExecute')
        _ebox = aCluCtrlObj
        _step_list = aStepList
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, False)
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_CALIBRATE_CELLS, undo=True, dom0Lock = False)

        try:
            _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_SETUP_CELL, undo=True, dom0Lock = False)
        except:
            ebLogWarn('*** undo OSTP_SETUP_CELL  did not completed successully')

        ebLogTrace('csCreateStorage: Completed undoExecute Successfully')
