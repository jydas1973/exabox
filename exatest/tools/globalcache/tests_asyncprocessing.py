#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/tools/globalcache/tests_asyncprocessing.py /main/1 2024/01/24 23:05:36 ririgoye Exp $
#
# tests_asyncprocessing.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_asyncprocessing.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    01/23/24 - Bug 36206720 - EXACS:EXACLOUD:MULTIPROCESS FAILED
#                           WHEN REACHING THE LIMIT
#    ririgoye    01/23/24 - Creation
#

import time
import unittest

from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Context import get_gcontext
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol


class ebTestAsyncProcessing(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_process_manager_limit(self):
        def my_sleep():
            time.sleep(1)

        get_gcontext().mSetConfigOption('multiple_process_limit', '5')
        _plist = ProcessManager()

        for i in range(1, 10):
            _p = ProcessStructure(my_sleep, [])
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()


if __name__ == '__main__':
    unittest.main(warnings='ignore')
