"""

 $Header: 

 Copyright (c) 2018, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_json_syntax.py - Unitest for json_syntax on clucontrol

 DESCRIPTION:
      Run tests for the method of json_syntax on clucontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       rajsag   11/05/20 - add to the exatest -srg -txn the JSON check for
                           program_arguments.conf

        jesandov    07/27/18 - Creation of the file for json_syntax
"""

import os
import sys
import unittest
import xml.etree.ElementTree as ET

from exabox.exatest.common.ebExacloudUtil import ebExacloudUtil, ebJsonObject
from exabox.core.Error import ExacloudRuntimeError

class ebTestJsonSyntax(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self._util = ebExacloudUtil(aGenerateDatabase=False, aUseOeda=False)
        self._files = ['config/dyndep.conf', 'config/hc_master_checklist.conf']
        self._files += ['config/healthcheck.conf', 'config/hcname.conf', 'config/program_arguments.conf']
        self._files += ['config/exabox.conf', 'config/exabox.conf.oradb.template', 'config/exabox.conf.template']
        self._files += ['exabox/managment/config/endpoints.conf', 'exabox/managment/config/basic.conf']

    def test_jsons(self):

        for _file in self._files:
            _msj = 'Testing: "{0}"'.format(_file)

            try:
                self._util.mReadJson(_file)
                self.assertEqual(_msj, _msj)
            except Exception as e:
                self.assertEqual(_msj, str(e))

        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()

