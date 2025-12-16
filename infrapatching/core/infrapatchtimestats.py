# $Header: ecs/exacloud/exabox/infrapatching/core/infrapatchtimestats.py /main/1 2022/06/05 20:38:59 sdevasek Exp $
#
# infrapatchtimestats.py
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
#
#    NAME
#      infrapatchtimestats.py - Contains utility classes and methods to
#                               produce timestats for infra patch operations
#
#    DESCRIPTION
#      Contains utility classes and methods to produce timestats for infra patch operations.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    sdevasek    05/25/22 - ENH 33859232 - TRACK TIME PROFILE INFORMATION FOR
#                           INFRAPATCH OPERATIONS

# class to hold timestat details
class InfrapatchingTimeStatsRecord(object):

    def __init__(self, aMasterRequestUUID, aChildRequestUUID, aTargetType, aOperation, aRackName, aPatchType,
                 aOperationStyle):
        self.__master_request_uuid = aMasterRequestUUID
        self.__child_request_uuid = aChildRequestUUID
        self.__target_type = aTargetType
        self.__operation = aOperation
        self.__rack_name = aRackName
        self.__patch_type = aPatchType
        self.__operation_style = aOperationStyle
        self.__node_names = ""
        self.__stage = ""
        self.__sub_stage = ""

    def mSetNodeNames(self, aNodeNames):
        self.__node_names = aNodeNames

    def mSetPatchingStage(self, aStageName):
        self.__stage = aStageName

    def mSetPatchingSubStage(self, aSubStageName):
        self.__sub_stage = aSubStageName

    def mGetMasterRequestUUID(self):
        return self.__master_request_uuid

    def mGetChildRequestUUID(self):
        return self.__child_request_uuid

    def mGetTargetType(self):
        return self.__target_type

    def mGetOperation(self):
        return self.__operation

    def mGetRackName(self):
        return self.__rack_name

    def mGetPatchType(self):
        return self.__patch_type

    def mGetOperationStyle(self):
        return self.__operation_style

    def mGetNodeNames(self):
        return self.__node_names

    def mGetPatchingStage(self):
        return self.__stage

    def mGetPatchingSubStage(self):
        return self.__sub_stage

