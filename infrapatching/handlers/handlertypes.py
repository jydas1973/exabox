#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/handlertypes.py /main/4 2024/09/24 16:45:50 araghave Exp $
#
# handlertypes.py
#
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      handlertypes.py - Choose the appropriate Task handler based on task
#
#    DESCRIPTION
#      Basic utilities functionality (abstract layer for choosing various task handlers)
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

"""
History:
    jyotdas     04/21/2020 - Created File
"""

from exabox.infrapatching.utils.utility import getTaskHandlerInstance
def getInfraPatchingTaskHandlerInstance(aDictionary):

    if aDictionary is None:
        raise Exception("Patching Parameters are not specified")

    _taskType = aDictionary["Operation"]
    if _taskType is None:
        raise Exception("Patch Operation is not specified")

    _taskHandler = None
    _taskHandler = getTaskHandlerInstance(_taskType, aDictionary)

    if _taskHandler is None:
        raise Exception(f"No handler specified for task {_taskType}")

    return _taskHandler
