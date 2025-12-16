"""

 $Header: 

 Copyright (c) 2018, 2022, Oracle and/or its affiliates.

 NAME:
      ebTreeNode.py - ebTree class implementation with tree functions
      
 DESCRIPTION:

      ebTree class implementation with tree function

 NOTES:
      ebTree also implement the Tricolor Color differentiation:
         https://confluence.oraclecorp.com/confluence/display/~jonathan.sandoval@oracle.com/The+Tricolor+Tree%2C+a+Delta+diferenciation+Aproach

 History:

    MODIFIED   (MM/DD/YY)
        jesandov    16/04/20 - Bug31187942: Change DFS to BFS in tree execution
        ndesanto    09/19/19 - 30294648 - IMPLEMENT PYTHON 3 MIGRATION WHITELIST ON EXATEST
        jesandov    11/09/18 - Creation of the file
"""
from __future__ import print_function

import os
import re
import sys
import defusedxml.ElementTree as ET
import xml.dom.minidom
from .ebTreeNode import ebTreeNode

class ebTree(object):

    def __init__(self, aFile=None):
        self.__root = None

        if aFile is not None:
            self.mImportXml(aFile)

    def mGetRoot(self):
        return self.__root

    def mSetRoot(self, aRoot):
        self.__root = aRoot

    def mSearchByPath(self, aPath, aCompareCallback=None):
        _futureNodes = [self.mGetRoot()]

        _newFuture = []
        _lastMatch = None

        for _pathNode in aPath:

            _lastMatch = None

            if _newFuture != []:
                _futureNodes = _newFuture
                _newFuture = []

            for _nextTreeNode in _futureNodes:

                _cmp = False
                if aCompareCallback is not None:
                    _cmd = aCompareCallback(_nextTreeNode, _pathNode)
                else:
                    _cmd = dict(_pathNode.mGetElement()) == dict(_nextTreeNode.mGetElement())

                if _cmd:
                    if _lastMatch is None:
                        _lastMatch = _nextTreeNode
                    else:
                        if _nextTreeNode.mGetType() != "White":
                            _lastMatch = _nextTreeNode

                    _newFuture += _nextTreeNode.mGetChildren()

            if _lastMatch is None:
                return None

        return _lastMatch

    def mDFS(self, aElement=None, aCompareCallback=None, aStuffCallback=None, aStuffArgs=None, aRoot=None):

        _first = self.__root
        if aRoot is not None:
            _first = aRoot

        _stack = [_first]

        while len(_stack) != 0:
            _actual = _stack.pop()

            if aStuffCallback is not None:
                aStuffCallback(_actual, aStuffArgs)

            if aCompareCallback is None:
                if _actual.mGetElement() == aElement:
                    return _actual
            else:
                if aCompareCallback(_actual, aElement):
                    return _actual

            for _child in _actual.mGetChildren():
                _stack.append(_child)

        return None


    def mBFS(self, aElement=None, aCompareCallback=None, aStuffCallback=None, aStuffArgs=None, aRoot=None):

        _first = self.__root

        if aRoot is not None:
            _first = aRoot

        _queue = [_first]
    
        while len(_queue) != 0:
            _actual = _queue.pop(0)

            if aStuffCallback is not None:
                aStuffCallback(_actual, aStuffArgs)

            if aCompareCallback is None:
                if _actual.mGetElement() == aElement:
                    return _actual
            else:
                if aCompareCallback(_actual, aElement):
                    return _actual

            for _child in _actual.mGetChildren():
                _queue.append(_child)

        return None

    def mRemoveDuplicate(self):

        def mStuff(aNode, aArgs):
            _children = aNode.mGetChildren()
            _repeat = None

            k = j = 0
            while k < len(_children):
                j = k
                while j < len(_children):
                    if k != j and  _children[k].mGetElement() == _children[j].mGetElement():
                        _children[k].mGetElement()['count'] += 1
                        _children.pop(j)
                        k = 0
                        j = 0
                    j += 1
                k+=1

        self.mBFS(aStuffCallback=mStuff)

    def mGetStructure(self, aCount=False, aType=False):
        _struct = []

        def mStuff(aNode, aStruct):
            _str = " > ".join(aNode.mGetPath(aTagName='tag'))
            _repeat = False

            for _elem in _struct:
                if _elem[1] == _str:
                    _pass = True
                    if aType:
                        if _elem[2] == aNode.mGetType():
                            _pass = True

                    if _pass:
                        _elem[0] += 1
                        _repeat = True

            if not _repeat:
                _struct.append([1, _str, aNode.mGetType()])

        def mCompare(aNode, aStr):
            return " > ".join(aNode.mGetPath('tag')) == aStr

        def mSort(aNode, aArgs):
            aNode.mSort()

        self.mBFS(aStuffCallback=mStuff, aStuffArgs=_struct)
        _tree = ebTree()

        for _elemen in _struct:
            _parentPath = str(" > ".join(_elemen[1].split(" > ")[0:-1]))
            _tag        = {"tag": str(_elemen[1].split(" > ")[-1]), "text": ""}

            if aCount:
                _tag['count'] = str(_elemen[0])

            _newElement = ebTreeNode()

            if aType:
                _newElement.mSetType(_elemen[2])

            if _parentPath == "":
                _newElement.mSetElement(_tag)
                _tree.mSetRoot(_newElement)
            else:
                _parent = _tree.mBFS(aElement=_parentPath, aCompareCallback=mCompare)
                _newElement.mSetElement(_tag)
                _parent.mAppendChild(_newElement)

        _tree.mBFS(aStuffCallback=mSort)
        return _tree

    def mGetLeavesByType(self, aType):

        def mCompare(aNode, aArgs):
            return aNode.mGetType() == aType

        return self.mGetLeaves(aCompareCallback=mCompare)

    def mGetNodesByParentType(self, aParentType, aChildType):

        def mInmediatParent(aNode, aColors):
            _parent = aNode.mGetParent()
            if _parent is not None:
                if _parent.mGetType() == aColors[0] and aNode.mGetType() == aColors[1]:
                    return True
            return False

        return self.mGetNodes(aCompareCallback=mInmediatParent, aCompareArgs=[aParentType, aChildType])

    def mGetNodesByType(self, aType):

        def mCompare(aNode, aArgs):
            return aNode.mGetType() == aType

        return self.mGetNodes(aCompareCallback=mCompare, aCompareArgs=None)

    def mGetNodes(self, aCompareCallback=None, aCompareArgs=None):
        _nodes = []
        def mStuff(aNode, aNodes):
            if aCompareCallback is not None:
                if aCompareCallback(aNode, aCompareArgs):
                    _nodes.insert(0,aNode)
            else:
                _nodes.insert(0,aNode)

        self.mBFS(aStuffCallback=mStuff, aStuffArgs=_nodes)
        return _nodes

    def mGetLeaves(self, aCompareCallback, aCompareArgs=None):
        _leaves = []

        def mStuff(aNode, aLeaves):
            if len(aNode.mGetChildren()) == 0:
                if aCompareCallback is not None:
                    if aCompareCallback(aNode, aCompareArgs):
                        _leaves.append(aNode)
                else:
                    _leaves.append(aNode)

        self.mBFS(aStuffCallback=mStuff, aStuffArgs=_leaves)
        return _leaves

    def mTricolorTree(self, aGreenTree, aCompareCallback=None):

        _tricolorTree = ebTree()

        def mStuff(aRedNode, aGreenTree):
            aGreenNode = aGreenTree.mSearchByPath(aRedNode.mGetPathNode(), aCompareCallback=aCompareCallback)
            if aGreenNode is not None:
                aGreenNode.mSetType("White")
                aRedNode.mSetType("White")

        def mInitColor(aNode, aColor):
            aNode.mSetType(aColor)

        #Generate the colors
        self.mBFS(aStuffCallback=mInitColor, aStuffArgs="Red")
        aGreenTree.mBFS(aStuffCallback=mInitColor, aStuffArgs="Green")

        #Calculate the White color
        self.mBFS(aStuffCallback=mStuff, aStuffArgs=aGreenTree)

        #Copy the red tree to the Tricolor Tree and copy red nodes
        _tricolorTree = self.mCopy()
        _nodesCp = aGreenTree.mGetNodesByParentType("White", "Green")
        for _node in _nodesCp:

            #Add the first parent
            _tricolorParent = _tricolorTree.mSearchByPath(_node.mGetParent().mGetPathNode(), aCompareCallback=aCompareCallback)
            _tricolorChild  = _node.mCopy()
            _tricolorParent.mAppendChild(_tricolorChild)

            #Add the rest of childs
            def mIntAppendChild(aNode, aTricolorTree):
                _newNode = aTricolorTree.mSearchByPath(aNode.mGetPathNode(), aCompareCallback=aCompareCallback)
                if _newNode is None:
                    _tricolorFather = aTricolorTree.mSearchByPath(aNode.mGetParent().mGetPathNode(), aCompareCallback=aCompareCallback)
                    _newNode = aNode.mCopy()
                    _tricolorFather.mAppendChild(_newNode)

            self.mBFS(aRoot=_node, aStuffCallback=mIntAppendChild, aStuffArgs=_tricolorTree)

        _tricolorTree.mSortTree()
        return _tricolorTree

    def mFilter(self, aCompareCallback=None):
        _copy = self.mCopy()

        def mStuff(aNode, aArgs):
            if not aCompareCallback(aNode):
                aNode.mRemove()

        _copy.mBFS(aStuffCallback=mStuff)
        return _copy

    @staticmethod
    def mDeepCopyNode(aNode):

        _ref = ebTree()
        _ref.mSetRoot(aNode)

        _new = _ref.mCopy()
        return _new.mGetRoot()

    def mCopy(self):
        _root    = self.mGetRoot()
        _tree    = ebTree()
        _stack   = [[_root, None]]

        while len(_stack) != 0:
            _actual = _stack.pop(0)

            #Transform the actual node
            _newChild = _actual[0].mCopy()
  
            #In Case of Root
            if _tree.mGetRoot() is None:
                _tree.mSetRoot(_newChild)

            #In Case of non Root
            if _actual[1] is not None:
                _actual[1].mAppendChild(_newChild)

            #Iterable of the Children with the new parent
            for _child in _actual[0].mGetChildren():
                _stack.append([_child, _newChild])

        return _tree

    def mImportXml(self, aXmlFile):

        with open(aXmlFile, "r") as _xmlFile:
            _xmlStr = _xmlFile.read()

        return self.mFromStr(_xmlStr)

    def mFromStr(self, aXmlStr):

        _xmlStr = aXmlStr
        _xmlStr = re.sub("xmlns=[\'\"]{1}[a-zA-Z0-9:]{1,}[\'\"]{1}", "", _xmlStr)
        _xmlStr = re.sub("<engineeredSystem", '<engineeredSystem xmlns="model"', _xmlStr)

        _xmlRoot = ET.fromstring(_xmlStr)
        _stack   = [[None, _xmlRoot]]

        while len(_stack) != 0:
            _actual = _stack.pop()

            #Transform the actual node
            _newChild = ebTreeNode()
            _newChild.mFromTag(_actual[1])
        
            #In Case of Root
            if self.mGetRoot() is None:
                self.mSetRoot(_newChild)

            #In Case os non Root
            if _actual[0] is not None:
                _actual[0].mAppendChild(_newChild)

            #Iterable of the Children with the new parent
            for _child in _actual[1]:
                _stack.append([_newChild, _child])

    def mExportXml(self, aXmlFile, aExportType=False, aDisplaySortKey=False):

        _pretty = self.mToStr(aExportType, aDisplaySortKey)
        with open(aXmlFile, "w+") as _f:
            _f.write(_pretty)

    def mToStr(self, aExportType=False, aDisplaySortKey=False):

        _root    = self.mGetRoot()
        _xmlRoot = None
        _stack   = [[_root, None]]

        while len(_stack) != 0:
            _actual = _stack.pop()

            #In Case os non Root
            _newTag = _actual[0].mToTag(
                aParent=_actual[1],
                aForce=True,
                aExportType=aExportType,
                aDisplaySortKey=aDisplaySortKey
            )

            #In case of not root
            if _xmlRoot is None:
                _xmlRoot = _newTag

            #Iterate the Children
            for _child in _actual[0].mGetChildren():
                _stack.append([_child, _newTag])

        _file = xml.dom.minidom.parseString(ET.tostring(_xmlRoot).decode('utf8'))
        _pretty = _file.toprettyxml()
        _pretty = _pretty.replace(":ns0", "").replace("ns0:", "").replace("\t", " "*4)

        return _pretty


    def mSortTree(self):
        def mCallback(aEbTreeNode, aArgs):
            aEbTreeNode.mSort()

        self.mBFS(aStuffCallback=mCallback)

    def mPrintBFS(self):
        _str = self. mToStringBFS()
        print(_str)

    def mToStringBFS(self):
        _list = []
        _list.append("")
        def mCallback(aEbTreeNode, aArgs):
            aEbTreeNode.mSort()
            aArgs[0] += str(aEbTreeNode) + "\n"

        self.mBFS(aStuffCallback=mCallback, aStuffArgs=_list)
        return _list[0]

    def mPrintDFS(self):
        _str = self.mToStringDFS()
        print(_str)

    def mToStringDFS(self):
        _list = []
        _list.append("")
        def mCallback(aEbTreeNode, aArgs):
            aEbTreeNode.mSort()
            aArgs[0] += str(aEbTreeNode) + "\n"

        self.mDFS(aStuffCallback=mCallback, aStuffArgs=_list)
        return _list[0]

    def mPrintNodes(self, aNodes):
        if aNodes is not None:
            _str = "\n".join([str(x) for x in aNodes])
            print(_str)
            return _str

    def mStrNodesPath(self, aNodes, aLimit=None):

        if aNodes is not None:
            _str = ""
            for _node in aNodes:
                _str = "*"*80 + "\n" + _str

                _limit = aLimit
                if aLimit is None:
                    _limit = len(_node.mGetChildren())

                for _child in _node.mGetChildren()[:_limit]:
                    _str = str(_child) + "\n" + _str
                _actual = _node
                while _actual is not None:
                    if _actual == _node:
                        _str = str(_actual) + " +++ \n" + _str
                    else:
                        _str = str(_actual) + "\n" + _str
                    _actual = _actual.mGetParent()
            _str = "*"*80 + "\n" + _str
            _str = _str.strip()
            return _str

# end of file
