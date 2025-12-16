#!/bin/python
#
# $Header: ecs/exacloud/exabox/tools/profiling/profiler_info.py /main/1 2023/10/06 08:38:40 jesandov Exp $
#
# profiler_info.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      profiler_info.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    09/22/23 - Creation
#

import json

class ProfilerInfo(object):

    def __init__( 
            self, \
            aStep="", \
            aDetails="", \
            aExecType="", \
            aProfilerType="", \
            aStartTime="", \
            aEndTime="", \
            aElapsed="", \
            aOperationId="", \
            aWorkflowId="", \
            aExaunitId="", \
            aComponent="", \
            aCmdtype="" \
        ):
        self.__step = aStep
        self.__details = aDetails
        self.__execType = aExecType
        self.__profilerType = aProfilerType
        self.__startTime = aStartTime
        self.__endTime = aEndTime
        self.__elapsed = aElapsed
        self.__operationId = aOperationId
        self.__workflowId = aWorkflowId
        self.__exaunitId = aExaunitId
        self.__component = aComponent
        self.__cmdtype = aCmdtype

    def mGetStep(self):
        return self.__step

    def mSetStep(self, aStr):
        self.__step = aStr

    def mGetDetails(self):
        return self.__details

    def mSetDetails(self, aStr):
        self.__details = aStr

    def mGetExecType(self):
        return self.__execType

    def mSetExecType(self, aStr):
        self.__execType = aStr

    def mGetProfilerType(self):
        return self.__profilerType

    def mSetProfilerType(self, aStr):
        self.__profilerType = aStr

    def mGetStartTime(self):
        return self.__startTime

    def mSetStartTime(self, aStr):
        self.__startTime = aStr

    def mGetEndTime(self):
        return self.__endTime

    def mSetEndTime(self, aStr):
        self.__endTime = aStr

    def mGetElapsed(self):
        return self.__elapsed

    def mSetElapsed(self, aStr):
        self.__elapsed = aStr

    def mGetOperationId(self):
        return self.__operationId

    def mSetOperationId(self, aStr):
        self.__operationId = aStr

    def mGetWorkflowId(self):
        return self.__workflowId

    def mSetWorkflowId(self, aStr):
        self.__workflowId = aStr

    def mGetExaunitId(self):
        return self.__exaunitId

    def mSetExaunitId(self, aStr):
        self.__exaunitId = aStr

    def mGetComponent(self):
        return self.__component

    def mSetComponent(self, aStr):
        self.__component = aStr

    def mGetCmdType(self):
        return self.__cmdtype

    def mSetCmdType(self, aStr):
        self.__cmdtype = aStr

    def mToJson(self):
        _dict = {}
        _dict['step'] = self.__step
        _dict['details'] = self.__details
        _dict['execType'] = self.__execType
        _dict['profilerType'] = self.__profilerType
        _dict['startTime'] = self.__startTime
        _dict['endTime'] = self.__endTime
        _dict['elapsed'] = self.__elapsed
        _dict['operationId'] = self.__operationId
        _dict['workflowId'] = self.__workflowId
        _dict['exaunitId'] = self.__exaunitId
        _dict['component'] = self.__component
        _dict['cmdtype'] = self.__cmdtype
        return json.dumps(_dict)

    def mFromJson(self, aJson):
        if 'step' in aJson.keys():
            self.__step = aJson['step']

        if 'details' in aJson.keys():
            self.__details = aJson['details']

        if 'execType' in aJson.keys():
            self.__execType = aJson['execType']

        if 'profilerType' in aJson.keys():
            self.__profilerType = aJson['profilerType']

        if 'startTime' in aJson.keys():
            self.__startTime = aJson['startTime']

        if 'endTime' in aJson.keys():
            self.__endTime = aJson['endTime']

        if 'elapsed' in aJson.keys():
            self.__elapsed = aJson['elapsed']

        if 'operationId' in aJson.keys():
            self.__operationId = aJson['operationId']

        if 'workflowId' in aJson.keys():
            self.__workflowId = aJson['workflowId']

        if 'exaunitId' in aJson.keys():
            self.__exaunitId = aJson['exaunitId']

        if 'component' in aJson.keys():
            self.__component = aJson['component']

        if 'cmdtype' in aJson.keys():
            self.__cmdtype = aJson['cmdtype']

# end of file
