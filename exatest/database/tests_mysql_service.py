"""

 $Header: 

 Copyright (c) 2018, 2021, Oracle and/or its affiliates.

 NAME:
      tests_mysql_service.py - Unitest for MySQL service

 DESCRIPTION:
      Run tests for MySQL service validation

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       ndesanto 12/13/21 - Adding test to increase coverage.
       ndesanto 02/11/20 - Creation of the file for mysql_service
"""

import time
import unittest

from exabox.agent.DBService import ExaMySQL, is_mysql_running, \
                                   get_mysql_config, is_mysql_present
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class TestMySQLService(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    @classmethod
    def tearDownClass(self):
        pass

    def test_start(self):
        _service = ExaMySQL(self.mGetUtil().mGetExaboxCfg())
        _service.mInit()
        self.assertTrue(is_mysql_running())

    def test_is_running(self):
        self.assertIsNotNone(get_mysql_config("exacloud", \
            "opt/mysql/mysql_conn.cfg"))
        self.assertTrue(is_mysql_present())
        self.assertTrue(is_mysql_present("opt/mysql/init.cfg"))
        self.assertTrue(is_mysql_running())

    def test_stop(self):
        _service = ExaMySQL(self.mGetUtil().mGetExaboxCfg())
        _service.mStop()


def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(TestMySQLService('test_start'))
    suite.addTest(TestMySQLService('test_is_running'))
    suite.addTest(TestMySQLService('test_stop'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
