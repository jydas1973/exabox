#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/bom_manager.py /main/2 2025/04/02 13:58:30 jesandov Exp $
#
# bom_manager.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      bom_manager.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    09/12/24 - Creation
#

import os
import json
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose

class ImageBOM:

    def __init__(self, aClubox):
        self.__data = {}
        self.__clubox = aClubox
        self.mReadData()

    def mGetClubox(self):
        return self.__clubox

    def mSetClubox(self, aClubox):
        self.__clubox = aClubox

    def mIsGoldImageProvisioning(self):

        if "jsonconf" in self.mGetClubox().mGetOptions():
            if "gold_image_provisioning" in self.mGetClubox().mGetOptions().jsonconf and \
                str(self.mGetClubox().mGetOptions().jsonconf["gold_image_provisioning"]).upper() == "TRUE":
                return True

        if get_gcontext().mCheckConfigOption("force_exadbxs_gold_image_provisioning", "True"):
            return True

        return False

    def mIsBaseDbProvisioning(self):

        if "jsonconf" in self.mGetClubox().mGetOptions():
            if "basedb_provisioning" in self.mGetClubox().mGetOptions().jsonconf and \
                str(self.mGetClubox().mGetOptions().jsonconf["basedb_provisioning"]).upper() == "TRUE":
                return True

        if get_gcontext().mCheckConfigOption("force_exadbxs_basedb_provisioning", "True"):
            return True

        return False

    def mReadData(self):
        with open("config/bom.conf") as _f:
            self.__data = json.loads(_f.read())

    def mGetStepInfo(self, aStepName):
        if aStepName in self.__data:
            return self.__data[aStepName]
        return {}

    def mGetSubStepInfo(self, aStepName, aSubStepName):
        _step = self.mGetStepInfo(aStepName)
        if aSubStepName in _step:
            return _step[aSubStepName]
        return {"status": "NOT_DONE"}

    def mIsSubStepExecuted(self, aStepName, aSubStepName):

        ebLogInfo(f"BOM INFO: Entering step {aStepName}/{aSubStepName}")

        if self.mIsGoldImageProvisioning() or self.mIsBaseDbProvisioning():

            _substep = self.mGetSubStepInfo(aStepName, aSubStepName)
            ebLogInfo(f"BOM INFO: Base Image Provisioning {aStepName}/{aSubStepName} with {_substep}")

            if "status" in _substep and _substep["status"] == "DONE":
                return True

        return False


# end of file
