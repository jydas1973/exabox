#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/exacompute/handlers/exacomputehandlertypes.py /main/2 2024/09/04 05:18:19 araghave Exp $
#
# exacomputehandlertypes.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      exacomputehandlertypes.py
#
#    DESCRIPTION
#      Returns appropriate handler for ExaCompute patching
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    08/27/24 - Enh 36971710 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE EXACOMPUTE FILES
#    jyotdas     07/22/22 - ENH 34350151 - Exacompute Infrapatching
#    jyotdas     07/22/22 - Creation

import importlib
from exabox.infrapatching.utils.constants import EXACOMPUTE_HANDLER_MAP
from exabox.log.LogMgr import ebLogError

def getExaComputeHandlerInstance(aDictionary):
    _handler_name = None
    _handler_instance = None
    _handler_class = None

    if aDictionary is None:
        raise Exception("ExaCompute Patching Parameters are not specified")

    _taskType = aDictionary["Operation"]
    if _taskType is None:
        raise Exception("ExaCompute Patch Operation is not specified")

    _handler_name = EXACOMPUTE_HANDLER_MAP[_taskType]
    if _handler_name:
        _module_name, _class_name = _handler_name.rsplit(".", 1)
        try:
            _handler_class = getattr(importlib.import_module(_module_name), _class_name)
        except ImportError:
            ebLogError(f"Module {_module_name} does not exist")
    _handler_instance = _handler_class(aDictionary)
    if _handler_instance:
        return _handler_instance
    else:
        ebLogError(f"No handler specified for task {_taskType}")

    return _handler_instance
