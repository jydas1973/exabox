"""

 $Header: 

 Copyright (c) 2018, 2024, Oracle and/or its affiliates.

 NAME:
      ebTreeNode.py - Node class to ebTree implementation
      
 DESCRIPTION:

      Node class to ebTree implementation

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
        ririgoye    06/18/24 - Bug 36746656 - PYTHON 3.11 - EXACLOUD NEEDS TO
                               UPDATE DEPRECATED/OLDER IMPORTS DYNAMICALLY
        ffrrodri    10/13/21 - Bug 33461178: Change mCalculateSortKey nested
                               function to a method of ebTreeNode class
        ndesanto    08/19/20 - Changed to OrderedDict to ensure same order for \
                               later comparison
        jesandov    11/09/18 - Creation of the file
"""
import os
import json
import re
import sys
import xml.etree.ElementTree as ET

try:
    from collections import OrderedDict
except ImportError:
    from collections.abc import OrderedDict

class ebTreeNode(object):

    def __init__(self, aElement=None, aParent=None):
        self.__parent   = None
        self.__element  = None
        self.__children = []
        self.__tag      = None
        self.__type     = ""
        self.__printMemory = False
        self.__sortKey = ""
        self.mCreate(aElement, aParent)

    def __str___(self):
        if self.__printMemory:
            _str = self.mGetPointer()
        else:
            _str = ". " * self.mGetLevel()
            _str += "[{0}] ".format(self.mGetType())
            _str += str(json.dumps(self.mGetElement()))
        return _str

    def __repr__(self):
        return self.__str___()

    def mGetPrintMemory(self):
        return self.__printMemory

    def mSetPrintMemory(self, aBool):
        self.__printMemory = aBool

    def mGetType(self):
        return self.__type

    def mSetType(self, aType):
        self.__type = aType

    def mGetParent(self):
        return self.__parent

    def mGetElement(self):
        return self.__element

    def mGetChildren(self):
        return self.__children

    def mSetParent(self, aParent):
        self.__parent = aParent

    def mSetElement(self, aElement):
        self.__element = aElement

    def mSetChildren(self, aChildren):
        self.__children = aChildren

    def mGetSortKey(self):
        return self.__sortKey

    def mSetSortKey(self, aString):
        self.__sortKey = str(aString).zfill(8)

    def mGetTag(self):
        return self.__tag

    def mSetTag(self, aTag):
        self.__tag = aTag

    def mGetPointer(self):
        return hex(id(self))

    def mGetLevel(self):
        c = 0
        p = self.mGetParent()
        while p is not None:
            p = p.mGetParent()
            c+=1
        return c

    def mGetSortElementInternal(self, aElement):
        _element = aElement.mGetElement()
        if isinstance(_element, dict) and "tag" in list(_element.keys()):
            _match = re.match(r"([\{]{1}[a-zA-Z0-9\-\_]{1,}[\}]{1})([a-zA-Z0-9\-\_]{1,})", _element['tag'])
            if _match is not None:
                return _match.group(2)
            else:
                return _element['tag']
        else:
            return _element

    def mGetXPath(self):
        _finalPath = "./"
        _pathToFetch = self.mGetPathNode()
        for _path in _pathToFetch:
            _newPath = _path.mGetElement()['tag']
            for _tag in _path.mGetElement():
                if _tag == "text":
                    _newPath += "[@{0}()='{1}']".format(_tag, _path.mGetElement()[_tag])
                elif _tag != "tag" and _path.mGetElement()[_tag] != "":
                    _newPath += "[@{0}='{1}']".format(_tag, _path.mGetElement()[_tag])

    def mGetPath(self, aTagName=None):
        _path = self.mGetPathNode()
        if aTagName is None:
            _path = [str(x.mGetSortElement()) for x in _path]
        else:
            _path = [str(x.mGetElement()[aTagName]) for x in _path]

        return _path

    def mGetPathNode(self):
        _actual = self
        _path   = []
        while _actual is not None:
            _parent = _actual.mGetParent()
            _path.insert(0, _actual)
            _actual = _parent
        return _path

    def mGetSortElement(self):
        return self.mGetSortElementInternal(self)

    def mCalculateSortKey(self):

        _sortID = self.mGetSortElement()
        _sortID += "/" + self.mGetSortKey() + "/"

        if "id" in self.mGetElement():
            _sortID += "/0{0}/".format(self.mGetElement()['id'])
        else:
            _sortID += "/1/"

        if "text" in self.mGetElement():
            _sortID += "/0{0}/".format(self.mGetElement()['text'])
        else:
            _sortID += "/1/"

        return _sortID

    def mSort(self, aReverse=True):
        self.__children.sort(key=lambda x: x.mCalculateSortKey(), reverse=aReverse)

    def mAppendChild(self, aChild):
        self.__children.append(aChild)
        aChild.mSetParent(self)

    def mAppfrontChild(self, aChild):
        self.__children.insert(0, aChild)
        aChild.mSetParent(self)

    def mCopy(self):
        _new = ebTreeNode()
        _new.mSetElement(self.mGetElement().copy())
        _new.mSetType(self.mGetType())
        return _new

    def mRemove(self):
        _parent = self.mGetParent()
        if _parent is not None:
            _parent.mGetChildren().remove(self)
            self.mSetParent(None)
        self.mSetType("Deleted")

    def mCreate(self, aElement={}, aParent=None):
        self.mSetElement(aElement)

        if aParent is not None:
            aParent.mAppendChild(self)

    def mFromTag(self, aTag):
        _element = {}
        if aTag.text is not None:
            _element['text'] = aTag.text.strip()
        else:
            _element['text'] = ""

        _element['tag']  = aTag.tag

        for _attr in aTag.attrib:
            if _attr == "ebTreeNodeType":
                self.mSetType(aTag.attrib[_attr].strip())
            else:
                _element[_attr] = aTag.attrib[_attr].strip()
        self.mSetElement(OrderedDict(sorted(_element.items(), key=lambda t: t[0])))

    def mToTag(self, aParent=None, aForce=False, aExportType=False, aDisplaySortKey=False):
        if self.mGetTag() is None or aForce:
            _element = self.mGetElement()
            if isinstance(_element, dict):
                if aParent is not None:
                    _tag = ET.SubElement(aParent, _element['tag'])
                else:
                    _tag = ET.Element(_element['tag'])

                _tag.text = ""
                for _key in _element:
                    if _key == "text":
                        if str(_element['text']).strip() != "":
                            _tag.text = str(_element['text']).strip()
                    elif _key == "tag":
                        pass
                    else:
                        _tag.attrib[_key] = str(_element[_key])

                if aExportType:
                    _tag.attrib["ebTreeNodeType"] = self.mGetType()

                if aDisplaySortKey:
                    _tag.attrib["ebTreeSortKey"] = self.mGetSortKey()

                self.mSetTag(_tag)
                return _tag
            else:
                return None


