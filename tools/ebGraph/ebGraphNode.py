"""

 $Header: 

 Copyright (c) 2018, 2020, Oracle and/or its affiliates. All rights reserved.

 NAME:
      ebGraphNode.py - Node class to ebGraph implementation
      
 DESCRIPTION:

      Node class to ebGraph implementation

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)

        jesandov    17/12/18 - Creation of the file
"""

import json

class ebGraphNode(object):

    def __init__(self, aId=None, aElement=None):
        self.__id = aId
        self.__element = aElement

    def mGetId(self):
        return self.__id

    def mSetId(self, aObj):
        self.__id = aObj

    def mGetElement(self):
        return self.__element

    def mSetElement(self, aObj):
        self.__element = aObj

    def mToJson(self):
        _dict = {}
        _dict['id'] = self.__id
        _dict['element'] = self.__element
        return json.dumps(_dict)

    def mFromJson(self, aJson):
        if 'id' in aJson.keys():
            self.__id = aJson['id']

        if 'element' in aJson.keys():
            self.__element = aJson['element']

