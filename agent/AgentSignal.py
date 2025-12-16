#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/agent/AgentSignal.py /main/1 2020/10/26 10:57:38 jesandov Exp $
#
# AgentSignals.py
#
# Copyright (c) 2020, Oracle and/or its affiliates. 
#
#    NAME
#      AgentSignals.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Class to store the signals of the agent and workers
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    10/05/20 - Creation
#

import json
import uuid

from enum import Enum
from typing import List, Dict, Tuple

class AgentSignalEnum(Enum):
    RELOAD = "reload"

class AgentSignal:
    """
    Class to store the signals of the agent and workers
    """

    ###############
    # Constructor #
    ###############

    def __init__(self, 
                 aUUID: str = str(uuid.uuid1()), 
                 aName: str = "",
                 aPid: str = "",
                 aExtraArgs: Dict = {}) -> None:
        """
        Class constructor

        :param aUUID: uuid of the signal
        :param aName: name of the signal defined in the enum of names
        :param aPid: pid of the agent/worker affected by the signal
        :param aExtraArgs: aditional information to handle the signals
        """

        self.__uuid = aUUID
        self.__name = aName
        self.__pid  = aPid
        self.__extraArgs = aExtraArgs

    ###################
    # Getters/Setters #
    ###################

    def mGetUUID(self):
        return self.__uuid

    def mSetUUID(self, aUUID: str):
        self.__uuid = aUUID

    def mGetName(self):
        return self.__name

    def mSetName(self, aName: str):
        self.__name = aName

    def mGetPid(self):
        return self.__pid

    def mSetPid(self, aPid: str):
        self.__pid = aPid

    def mGetExtraArgs(self):
        return self.__extraArgs

    def mSetExtraArgs(self, aExtraArgs: str):
        self.__extraArgs = aExtraArgs

    ########################
    # Data convert methods #
    ########################

    @staticmethod
    def mGetPrimaryKey() -> str:
        return "uuid"

    @staticmethod
    def mGetColumns() -> Tuple[str, str, str, str]:
        """
        Get the columns to use in the data convertion
        """
        return ("uuid", "name", "pid", "extra_args")

    def mPopulate(self, aList: List) -> None:
        """
        Read the information of one list and convert into internal information
        :param aList: List with the information of the object
        """
        _dict = dict(zip(AgentSignal.mGetColumns(), aList))
        self.mFromDict(_dict)

    def mUnpopulate(self) -> List:
        """
        Return an list with the object information
        """
        _dict = self.mToDict()
        return list(map(lambda x: _dict[x], AgentSignal.mGetColumns()))

    def mFromDict(self, aDict: dict) -> None:
        """
        Read the information of one dict and convert into internal information
        :param aDict: Dict with the information of the object
        """

        if "uuid" in aDict:
            self.mSetUUID(aDict['uuid'])

        if "name" in aDict:
            self.mSetName(aDict['name'])

        if "pid" in aDict:
            self.mSetPid(aDict['pid'])

        if "extra_args" in aDict:
            self.mSetExtraArgs(json.loads(aDict['extra_args']))

    def mToDict(self) -> Dict:
        """
        Return a Dict with the same information than the object
        """

        _dict = {}
        _dict['uuid'] = self.mGetUUID()
        _dict['name'] = self.mGetName()
        _dict['pid'] = self.mGetPid()
        _dict['extra_args'] = json.dumps(self.mGetExtraArgs())
        return _dict

# end of file
