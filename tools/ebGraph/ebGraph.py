"""

 $Header: 

 Copyright (c) 2018, 2020, Oracle and/or its affiliates. All rights reserved.

 NAME:
      ebGraph.py - Graph class to ebGraph implementation
      
 DESCRIPTION:

      Node class to ebGraph implementation

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)

        jesandov    17/12/18 - Creation of the file
"""

from __future__ import print_function

from exabox.tools.ebGraph.ebGraphNode import ebGraphNode
from exabox.tools.ebGraph.ebGraphLink import ebGraphLink

import uuid

class ebGraph(object):

    def __init__(self):
        self.__nodes = []
        self.__links = []

    def mGetNodes(self):
        return self.__nodes

    def mSetNodes(self, aNodeList):
        self.__nodes = aNodeList

    def mGetLinks(self):
        return self.__links

    def mSetLinks(self, aLinkList):
        self.__links = aLinkList

    def mDefaultCompare(self, aObj1, aObj2):
        return aObj1 == aObj2

    def mFindLink(self, aNodeFrom, aNodeTo):

        for link in self.__links:

            if link.mGetNodeFrom() == aNodeFrom and link.mGetNodeTo() == aNodeTo:
                return link

        return None

    def mAddLink(self, aNodeFrom, aNodeTo):
        
        linkExists = self.mFindLink(aNodeFrom, aNodeTo)
        if linkExists is not None:
            return linkExists

        newLink = ebGraphLink(aNodeFrom, aNodeTo)
        self.__links.append(newLink)
        return newLink

    def mFetchLinks(self, aNodeFrom, aNodeTo):

        fetched = []
        for link in self.__links:

            count = 0

            if aNodeFrom is None or aNodeFrom == link.mGetNodeFrom():
                count += 1

            if aNodeTo is None or aNodeTo == link.mGetNodeTo():
                count += 1

            if count == 2:
                fetched.append(link)

        return fetched

    def mGetNodeById(self, aId):
        for node in self.__nodes:
            if node.mGetId() == aId:
                return node

    def mFetchNodes(self, aCompareCallback, aCompareArgs):

        fetched = []
        for node in self.__nodes:

            if aCompareCallback(node, aCompareArgs):
                fetched.append(node)

        return fetched

    def mFindElement(self, aElement, aCompareCallback=None):

        for node in self.__nodes:

            if aCompareCallback is not None:
                if aCompareCallback(node.mGetElement(), aElement):
                    return node

            else:
                if self.mDefaultCompare(node.mGetElement(), aElement):
                    return node

        return None

    def mAddElement(self, aElement, aCompareCallback=None):

        nodeExists = self.mFindElement(aElement, aCompareCallback)
        if nodeExists is not None:
            return nodeExists

        newNode = ebGraphNode(str(uuid.uuid1()), aElement)
        self.__nodes.append(newNode)
        return newNode

    def mAddConnection(self, aElement1, aElement2, aBidirectional=False, aCompareCallback=None):

        nodeFrom = self.mAddElement(aElement1, aCompareCallback)
        nodeTo   = self.mAddElement(aElement2, aCompareCallback)

        self.mAddLink(nodeFrom, nodeTo)

        if aBidirectional:
            self.mAddLink(nodeTo, nodeFrom)

    def mPrint(self, aPrintfx=print):

        aPrintfx("*" * 30)

        aPrintfx("*** Print Nodes ***")
        for node in self.__nodes:
            aPrintfx(node.mToJson())

        aPrintfx("*** Print Links ***")
        for link  in self.__links:
            aPrintfx(link.mToJson())

        aPrintfx("*" * 30)

    def mVisitAll(self, aStuffCallback=None, aStuffArgs=None, aType="DFS"):

        # Fetch nodes with no links
        _leaves = []
        for node in self.__nodes:

            #Assumme the node is a leave
            _leaves.append(node)

            for link in self.__links:
                if link.mGetNodeTo() == node:

                    # if there is a exit connection, delete from the leaf
                    _leaves.pop()
                    break

        # In case of not leaves, there is a circular graph
        if not _leaves:
            _leaves = self.__nodes[0]

        # Do the iteration from the leaves
        _visit = []
        while _leaves:
            _leaf = _leaves.pop(0)
            self.mRun(_leaf, aStuffCallback, aStuffArgs, aType, _visit)

        return _visit


    def mRun(self, aFirstElement, aStuffCallback=None, aStuffArgs=None, aType="DFS", aVisited=None):

        visited = aVisited
        if aVisited is None:
            visited = []

        wait = [aFirstElement]

        while wait:

            if aType == "BFS":
                current = wait.pop(0)

            else:
                # Assume DFS
                current = wait.pop()

            if current not in visited:
                visited.append(current)

                if aStuffCallback is not None:
                    aStuffCallback(current, aStuffArgs)

                links = self.mFetchLinks(current, None)

                for link in links:
                    wait.append(link.mGetNodeTo())


