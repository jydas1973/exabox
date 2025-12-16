#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/taskHandler/rollbackprereqhandler.py /main/13 2025/03/14 04:03:37 avimonda Exp $
#
# rollbackprereqhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      rollbackprereqhandler.py - Wrapper Patching API to expose rollback
#      prereq operation
#
#    DESCRIPTION
#      This module has mExecute method for Exadata rollback prereq
#      operation on Cell and Switch.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    03/03/25 - Bug 37541893 - EXACS |DOM0 ROLLBACK | FAILED (NOT
#                           SUPPORTED)
#    emekala     08/13/24 - ENH 36679949 - REMOVE OVERHEAD OF INDEPENDENT
#                           MONITORING PROCESS FROM INFRAPATCHING
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    12/08/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    nmallego    11/10/21 - Bug33521580 - Run cell rollback precheck before
#                           dom0
#    araghave    07/08/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    araghave    03/08/21 - Bug32593118 - Collect the actual patchmgr status
#                           only when patchmgr is success
#    araghave    01/07/21 - Bug 32320030 - ROCE SWITCH REFACTOR CODE CHANGES
#    araghave    10/21/20 - Enh 31925002 - Error code handling implementation 
#                           for Monthly Patching
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#
from exabox.infrapatching.handlers.taskHandler.taskhandler import TaskHandler
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers, getTargetHandlerInstance
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *

class RollbackPreReqHandler(TaskHandler):

    def __init__(self, *initial_data, **kwargs):
        super(RollbackPreReqHandler, self).__init__(*initial_data, **kwargs)
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [TASK_ROLLBACK_PREREQ_CHECK], self)
        self.mPatchLogInfo("RollbackPreReqHandler")

    def mExecute(self):

        _rc = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        if self.mGetTargetTypes() is None:
            raise Exception("No Target is specified")

        _targetHandler = None
        _break_loop = False
        _len = len(self.mGetTargetTypes())
        if _len == 1:
            _break_loop = True

        for _ttype in [PATCH_CELL, PATCH_IBSWITCH, PATCH_ROCESWITCH]:  # DOM0, DOMU does not have mRollBackPreCheck
            if _ttype not in self.mGetTargetTypes():
                continue

            _targetHandler = getTargetHandlerInstance(_ttype, self.mGetAllArgs())
            if _targetHandler:
                self.mPatchLogInfo(f"Task: {TASK_ROLLBACK_PREREQ_CHECK} - Type: {_ttype}\t\t[ ret_code = {_rc} ]")
                _rc, _no_action_taken = _targetHandler.mRollBackPreCheck()
                if _rc != PATCH_SUCCESS_EXIT_CODE or _break_loop:
                    break
            else:
                continue

        if _targetHandler is None:
            _rc = ROLLBACK_PRECHECK_NOT_SUPPORTED
            _suggestion_msg = f"Rollback precheck is not supported for '{self.mGetTargetTypes()[0]}'"
            self.mPatchLogError(_suggestion_msg)
            self.mAddError(_rc, _suggestion_msg)
        else:
            if _rc == PATCH_SUCCESS_EXIT_CODE and _no_action_taken == len(self.mGetTargetTypes()):
                _suggestion_msg = "No action required. Nodes are already at the intended version"
                self.mAddError(_rc, _suggestion_msg)
            elif _rc == PATCH_SUCCESS_EXIT_CODE:
                _suggestion_msg = f"Task: {TASK_ROLLBACK_PREREQ_CHECK} - Type: {self.mGetTargetTypes()} completed successfully."
                self.mAddError(_rc, _suggestion_msg)

        return _rc


