#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsHistoryNode.py /main/2 2024/10/07 18:01:10 ririgoye Exp $
#
# ExaKmsHistoryNode.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsHistoryNode.py - Class to encapsulate exakms history metadata for each entry
#
#    DESCRIPTION
#      Class to encapsulate exakms history metadata for each entry
#
#    NOTES
#      NA
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    09/25/24 - Bug 36390923 - REMOVE EXAKMS HISTORY VALIDATION
#                           ACROSS HOSTS
#    aypaul      06/06/22 - Creation
#
import json

class ExaKmsHistoryNode:

    def __init__(self, aEntryTimestamp, aEntryOperation, aEntryUserName, aEntryHostName, aEntryOperationId='Unknown', aEntryLabel='Unknown', aEntrySrcHost='Unknown'):
        self.__exakmsEntryTimestamp = aEntryTimestamp
        self.__exakmsEntryOperation = aEntryOperation
        self.__exakmsEntryOperationId = aEntryOperationId
        self.__exakmsEntryUsername  = aEntryUserName
        self.__exakmsEntryHostname  = aEntryHostName
        self.__exakmsEntryLabel     = aEntryLabel
        self.__exakmsEntrySrcHost   = aEntrySrcHost

    def mToJson(self):
        _current_json = dict()
        _current_json["time"] = self.__exakmsEntryTimestamp
        _current_json["operation"] = self.__exakmsEntryOperation
        _current_json["user_hostname"] = f"{self.__exakmsEntryUsername}@{self.__exakmsEntryHostname}"
        _current_json["label"] = self.__exakmsEntryLabel
        _current_json["operation_id"] = self.__exakmsEntryOperationId
        _current_json["src_host"] = self.__exakmsEntrySrcHost
        return _current_json

    """Class setter methods"""

    def mSetEntryTimestamp(self, aEntryTimestamp):
        self.__exakmsEntryTimestamp = aEntryTimestamp

    def mSetEntryOperation(self, aEntryOperation):
        self.__exakmsEntryOperation = aEntryOperation

    def mSetEntryUserName(self, aEntryUserName):
        self.__exakmsEntryUsername  = aEntryUserName

    def mSetEntryHostName(self, aEntryHostName):
        self.__exakmsEntryHostname  = aEntryHostName


    """Class getter methods"""

    def mGetEntryTimestamp(self):
        return self.__exakmsEntryTimestamp

    def mGetEntryOperation(self):
        return self.__exakmsEntryOperation

    def mGetEntryUserName(self):
        return self.__exakmsEntryUsername

    def mGetEntryHostName(self):
        return self.__exakmsEntryHostname

