#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/proxy/tests_CustomCircularQueue.py /main/1 2021/08/23 23:05:35 aypaul Exp $
#
# tests_CustomCircularQueue.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_CustomCircularQueue.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      08/19/21 - Creation
#
import json
import unittest
from exabox.log.LogMgr import ebLogInfo
import warnings
from exabox.proxy.CustomCircularQueue import CustomCircularQueue
from exabox.core.DBStore import ebGetDefaultDB
from ast import literal_eval
import uuid

class testOptions(object): pass

class ebTestCustomCircularQueue(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        warnings.filterwarnings("ignore")

    def test_getCurrentSizeOfPool(self):
        thisQ = CustomCircularQueue()
        thisQ.insert("dummyhostname1:dummyport1")
        thisQ.insert("dummyhostname2:dummyport2")
        thisQ.insert("dummyhostname3:dummyport3")

        self.assertEqual(thisQ.getCurrentSizeOfPool(), 3)

    def test_getList(self):
        thisQ = CustomCircularQueue()
        thisQ.insert("dummyhostname1:dummyport1")
        thisQ.insert("dummyhostname2:dummyport2")
        thisQ.insert("dummyhostname3:dummyport3")

        self.assertEqual(thisQ.getList()[2], "dummyhostname3:dummyport3")

    def test_insert(self):
        thisQ = CustomCircularQueue(5)
        self.assertEqual(thisQ.insert("dummyhostname1:dummyport1"), True)
        self.assertEqual(thisQ.insert("dummyhostname2:dummyport2"), True)
        self.assertEqual(thisQ.insert("dummyhostname3:dummyport3"), True)
        self.assertEqual(thisQ.insert("dummyhostname4:dummyport4"), True)
        self.assertEqual(thisQ.insert("dummyhostname5:dummyport5"), True)
        self.assertEqual(thisQ.insert("dummyhostname6:dummyport6"), False)

    def test_remove(self):
        thisQ = CustomCircularQueue(3)
        #Empty Queue
        self.assertEqual(thisQ.remove("dummy"), False)

        thisQ.insert("dummyhostname1:dummyport1")
        thisQ.insert("dummyhostname2:dummyport2")
        thisQ.insert("dummyhostname3:dummyport3")
        self.assertEqual(thisQ.remove("dummyhostname4:dummyport4"), False)
        self.assertEqual(thisQ.remove("dummyhostname3:dummyport3"), True)

    def test_getNextAvailableElement(self):
        thisQ = CustomCircularQueue(3)
        #Empty Queue
        self.assertEqual(thisQ.getNextAvailableElement(), None)

        thisQ.insert("dummyhostname1:dummyport1")
        thisQ.insert("dummyhostname2:dummyport2")
        thisQ.insert("dummyhostname3:dummyport3")
        self.assertEqual(thisQ.getNextAvailableElement(), "dummyhostname1:dummyport1")
        self.assertEqual(thisQ.getNextAvailableElement(), "dummyhostname2:dummyport2")
        self.assertEqual(thisQ.getNextAvailableElement(), "dummyhostname3:dummyport3")
        self.assertEqual(thisQ.getNextAvailableElement(), "dummyhostname1:dummyport1")


if __name__ == "__main__":
    unittest.main()