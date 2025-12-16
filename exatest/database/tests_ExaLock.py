"""

 $Header: 

 Copyright (c) 2020, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_ExaLock.py - Unitest for ExaLock

 DESCRIPTION:
      Run tests for the class ExaLock

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
        ndesanto    08/19/20 - Added path parameter and tests
        ndesanto    08/18/20 - Creation of the file for ExaLock
"""

import datetime
import json
import os
import shutil
import time
import unittest
import uuid
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.agent.ExaLock import ExaLock

class TestExaLock(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self._tmp_path = os.path.join(self.mGetUtil(self).mGetOutputDir(), "tmp")

    @classmethod
    def tearDownClass(self):
        pass

    def test_mLock(self):
        with ExaLock(os.path.join(self._tmp_path, "test_mLock")):
            time.sleep(1)

    def test_mDirCreation(self):
        shutil.rmtree(self._tmp_path, ignore_errors=True)
        with ExaLock(os.path.join(self._tmp_path, "test_mDirCreation")):
            time.sleep(1)

    def test_mLockFileNameOnly(self):
        with ExaLock("test_mLockFileNameOnly"):
            time.sleep(1)


def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(TestExaLock('test_mLock'))
    suite.addTest(TestExaLock('test_mDirCreation'))
    suite.addTest(TestExaLock('test_mLockFileNameOnly'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
