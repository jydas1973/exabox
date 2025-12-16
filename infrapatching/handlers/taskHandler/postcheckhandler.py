#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/taskHandler/postcheckhandler.py /main/11 2024/09/24 16:45:50 araghave Exp $
#
# postcheckhandler.py
#
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      postcheckhandler.py- Wrapper Patching API to expose rollback
#      prereq operation
#
#    DESCRIPTION
#      This module has mExecute method for Exadata rollback prereq
#      operation on  Cell and Switch.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    12/08/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    nmallego    11/11/21 - Bug33521580 - Update correct task type
#    araghave    07/08/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    araghave    01/19/21 - Bug 32395969 - MONTHLY PATCHING: FOUND FEW ISSUES
#                           WHILE TESTING AND NEED TO FIX
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

class PostCheckHandler(TaskHandler):

    def __init__(self, *initial_data, **kwargs):
        super(PostCheckHandler, self).__init__(*initial_data, **kwargs)
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [TASK_POSTCHECK], self)
        self.mPatchLogInfo("PostCheckHandler")

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

        for _ttype in [PATCH_CELL, PATCH_DOM0, PATCH_DOMU, PATCH_IBSWITCH, PATCH_ROCESWITCH]:
            if _ttype not in self.mGetTargetTypes():
                continue

            _targetHandler = getTargetHandlerInstance(_ttype, self.mGetAllArgs())
            if _targetHandler:
                _rc, _no_action_taken = _targetHandler.mPostCheck()
                self.mPatchLogInfo(f"Task: {TASK_POSTCHECK} - Type: {_ttype}\t\t[ ret_code = {_rc} ]")
                if _rc != PATCH_SUCCESS_EXIT_CODE or _break_loop:
                    break
            else:
                continue

        if _targetHandler is None:
            raise Exception("No Target handler specified for PotCheck")
        else:
            if _rc == PATCH_SUCCESS_EXIT_CODE and _no_action_taken == len(self.mGetTargetTypes()):
                _suggestion_msg = "No action required. Nodes are already at the intended version"
                self.mAddError(_rc, _suggestion_msg)
            elif _rc == PATCH_SUCCESS_EXIT_CODE:
                _suggestion_msg = f"Task: {TASK_POSTCHECK} - Type: {self.mGetTargetTypes()} completed successfully."
                self.mAddError(_rc, _suggestion_msg)

        return _rc


