#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/mockTaskHandler/rollbackprereqmockhandler.py /main/2 2024/11/04 07:22:22 emekala Exp $
#
# rollbackprereqmockhandler.py
#
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      rollbackprereqmockhandler.py - Wrapper Patching API to expose rollback
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
#    emekala     10/25/24 - ENH 37070223 - SYNC MOCK HANLDERS WITH LATEST CODE
#                           FROM CORE INFRAPATCHING HANDLERS AND ADD SUPPORT
#                           FOR CUSTOM RESPONSE AND RACK DETAILS
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
from exabox.infrapatching.handlers.mockTaskHandler.taskmockhandler import TaskMockHandler
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers, getTargetHandlerInstance
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *

class RollbackPreReqMockHandler(TaskMockHandler):

    def __init__(self, *initial_data, **kwargs):
        super(RollbackPreReqMockHandler, self).__init__(*initial_data, **kwargs)
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [TASK_ROLLBACK_PREREQ_CHECK], self)
        self.mPatchLogInfo("RollbackPreReqMockHandler")

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

        for _ttype in [PATCH_CELL, PATCH_DOM0, PATCH_DOMU, PATCH_IBSWITCH, PATCH_ROCESWITCH]:  # DOM0, DOMU does not have mRollBackPreCheck
            if _ttype not in self.mGetTargetTypes():
                continue

            if _ttype in [PATCH_DOMU, PATCH_DOM0]:
                self.mPatchLogWarn(f"Rollback precheck for '{_ttype}' is not supported ")
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
            raise Exception("No Target handler specified for Rollback PreReq")
        else:
            if _rc == PATCH_SUCCESS_EXIT_CODE and _no_action_taken == len(self.mGetTargetTypes()):
                _suggestion_msg = "No action required. Nodes are already at the intended version"
                self.mAddError(_rc, _suggestion_msg)
            elif _rc == PATCH_SUCCESS_EXIT_CODE:
                _suggestion_msg = f"Task: {TASK_ROLLBACK_PREREQ_CHECK} - Type: {self.mGetTargetTypes()} completed successfully."
                self.mAddError(_rc, _suggestion_msg)

        return _rc


