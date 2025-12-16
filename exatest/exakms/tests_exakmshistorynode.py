#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exakmshistorynode.py /main/1 2022/06/16 21:47:28 aypaul Exp $
#
# tests_exakmshistorynode.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakmshistorynode.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/08/22 - Creation
#
import unittest
import re, time
from exabox.exakms.ExaKmsHistoryNode import ExaKmsHistoryNode

def getMockHistoryNode():
    _create_timestamp = re.sub("[0-9]", "0", time.strftime('%Y-%m-%d %H:%M:%S%z'))
    _exakmshistory_node = ExaKmsHistoryNode(_create_timestamp, "insert", "root", "mockhostname.us.oracle.com")
    return _exakmshistory_node

class ebTestExaKmsHistoryNode(unittest.TestCase):

    def test_mToJson(self):

        _curr_history_node = getMockHistoryNode()
        _json_repr = _curr_history_node.mToJson()
        self.assertEqual("root@mockhostname.us.oracle.com", _json_repr["user_hostname"])

    def test_setter_methods(self):

        _curr_history_node = getMockHistoryNode()
        _curr_create_time = re.sub("[0-9]", "0", time.strftime('%Y-%m-%d %H:%M:%S%z'))
        _curr_history_node.mSetEntryTimestamp(_curr_create_time)
        _curr_history_node.mSetEntryOperation("mock_operation")
        _curr_history_node.mSetEntryUserName("mock_username")
        _curr_history_node.mSetEntryHostName("mock_hostname")

        _json_repr = _curr_history_node.mToJson()
        self.assertEqual("mock_username@mock_hostname", _json_repr["user_hostname"])
        self.assertEqual("mock_operation", _json_repr["operation"])
        self.assertEqual(_curr_create_time, _json_repr["time"])

    def test_getter_methods(self):

        _curr_history_node = getMockHistoryNode()
        self.assertEqual("insert", _curr_history_node.mGetEntryOperation())
        self.assertEqual("root", _curr_history_node.mGetEntryUserName())
        self.assertEqual("mockhostname.us.oracle.com", _curr_history_node.mGetEntryHostName())

if __name__ == '__main__':
    unittest.main(warnings='ignore')