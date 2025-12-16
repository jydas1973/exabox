#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/taskHandler/plugintaskshandler.py /main/4 2024/08/16 10:00:25 araghave Exp $
#
# plugintaskshandler.py
#
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      plugintaskshandler.py - Wrapper Patching API to expose exacloud
#      and dbnu plugins operation.
#
#    DESCRIPTION
#      This module has mExecute method for running exacloud plugins operation
#      on dom0 and domU.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    araghave    01/07/21 - Bug 32320030 - ROCE SWITCH REFACTOR CODE CHANGES
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#
from exabox.infrapatching.handlers.targetHandler.cellhandler import CellHandler
from exabox.infrapatching.handlers.targetHandler.dom0handler import Dom0Handler
from exabox.infrapatching.handlers.targetHandler.domuhandler import DomUHandler
from exabox.infrapatching.handlers.targetHandler.switchhandler import SwitchHandler
from exabox.infrapatching.handlers.taskHandler.taskhandler import TaskHandler
from exabox.infrapatching.utils.constants import PATCH_DOM0, PATCH_DOMU, PATCH_CELL, PATCH_IBSWITCH, \
    TASK_ONEOFF, PATCH_ROCESWITCH, TASK_ONEOFFV2

#Handles plugin task : one off
class PluginTasksHandler(TaskHandler):

    def __init__(self, *initial_data, **kwargs):
        super(PluginTasksHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("PluginTasksHandler")

    def mExecute(self):
        _rc = 0
        if self.mGetTargetTypes() is None:
            raise Exception("No Target is specified")

        _targetHandler = None
        _operation = self.mGetTask()
        _len = len(self.mGetTargetTypes())
        for _ttype in self.mGetTargetTypes():
            if _len == 1 and PATCH_DOM0 in self.mGetTargetTypes():
                _targetHandler = Dom0Handler(self.mGetAllArgs())
                if _operation == TASK_ONEOFF:
                    _rc = _targetHandler.mOneOff()
                elif _operation == TASK_ONEOFFV2:
                    _rc = _targetHandler.mOneOffv2()
                break
            elif _len == 1 and PATCH_DOMU in self.mGetTargetTypes():
                _targetHandler = DomUHandler(self.mGetAllArgs())
                if _operation == TASK_ONEOFF:
                    _rc = _targetHandler.mOneOff()
                break
            elif _len == 1 and PATCH_CELL in self.mGetTargetTypes():
                _targetHandler = CellHandler(self.mGetAllArgs())
                if _operation == TASK_ONEOFF:
                    _rc = _targetHandler.mOneOff()
                elif _operation == TASK_ONEOFFV2:
                    _rc = _targetHandler.mOneOffv2()
                break
            elif _len == 1 and (any(x in self.mGetTargetTypes() for x in [PATCH_IBSWITCH,PATCH_ROCESWITCH])):
                _targetHandler = SwitchHandler(self.mGetAllArgs())
                if _operation == TASK_ONEOFF:
                    _rc = _targetHandler.mOneOff()
                break

        if _targetHandler is None:
            raise Exception("No Target handler specified for Patching")

        return _rc

