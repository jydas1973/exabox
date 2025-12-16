"""

 $Header: 

 Copyright (c) 2018, 2024, Oracle and/or its affiliates.

 NAME:
      tests_xmlpatching.py - Unitest for exacloud agent endpoints
      
 DESCRIPTION:
      Run tests for the method of exacloud agent endpoints

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       prsshukl 04/04/24 - Bug 36480365 - Commenting the unittest

        jesandov    08/15/18 - Creation of the file
"""

import unittest
import os
import sys
import json

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol, ebJsonObject

class ebTestEndpoints(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True, aUseAgent=True)
        self.mGetUtil(self).mGetInstallerAgent().mStartAgent()

    @classmethod
    def tearDownClass(self):
        self.mGetUtil(self).mGetInstallerAgent().mSetStopFlag(True)

    def test_endpoints(self):
        loader = unittest.TestLoader()
        suite  = unittest.TestSuite()

        #Get the TestCases
        tests = loader.discover(start_dir='exabox/exatest/agent/', pattern='agent*.py')
        for test in tests:
            if str(test._tests[0]).find(".ade") == -1:
                suite.addTest(test)

        runner = unittest.runner.TextTestRunner()
        runner.run(suite)

if __name__ == '__main__':
    pass
    # unittest.main(warnings='ignore')

# end of file
