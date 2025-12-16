"""

 $Header: 

 Copyright (c) 2018, 2020, Oracle and/or its affiliates. All rights reserved.

 NAME:
      ebGraphLink.py - Link class to ebGraph implementation
      
 DESCRIPTION:

      Node class to ebGraph implementation

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)

        jesandov    17/12/18 - Creation of the file
"""

import json

class ebGraphLink(object):

    def __init__(self, aNodeFrom=None, aNodeTo=None, aWeight=None):
        self.__nodeFrom = aNodeFrom
        self.__nodeTo = aNodeTo
        self.__weight = aWeight

    def mGetNodeFrom(self):
        return self.__nodeFrom

    def mSetNodeFrom(self, aObj):
        self.__nodeFrom = aObj

    def mGetNodeTo(self):
        return self.__nodeTo

    def mSetNodeTo(self, aObj):
        self.__nodeTo = aObj

    def mGetWeight(self):
        return self.__weight

    def mSetWeight(self, aObj):
        self.__weight = aObj

    def mToJson(self):
        _dict = {}
        _dict['nodeFrom'] = self.__nodeFrom.mGetId()
        _dict['nodeTo'] = self.__nodeTo.mGetId()
        _dict['weight'] = self.__weight
        return json.dumps(_dict)

    def mFromJson(self, aJson):
        if 'nodeFrom' in aJson.keys():
            self.__nodeFrom = aJson['nodeFrom']

        if 'nodeTo' in aJson.keys():
            self.__nodeTo = aJson['nodeTo']

        if 'weight' in aJson.keys():
            self.__weight = aJson['weight']

