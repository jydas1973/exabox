"""

 $Header: 

 Copyright (c) 2018, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_agent_atpgetfile.py - Unitest for exacloud agent endpoint atpgetfile
      
 DESCRIPTION:
      Run tests for the method of exacloud agent endpoint atpgetfile

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)

        jesandov    08/15/18 - Creation of the file
"""
import unittest
import json

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol, ebJsonObject

class ebTestAgentAtpGetFile(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True, aUseAgent=True)
        self._agent = self.mGetUtil(self).mGetInstallerAgent()

    def test_mAtpGetFileNoFile(self):
        _page = self._agent.mRequest(self._agent.mAgentUrl() + "AtpGetFile?one=x.txt")
        _res = 'No found param \'file\' on mAtpGetFile.\n'
        _res += 'For more information, consult the exacloud.log.'
        self.assertEqual(json.loads(_page)['err_msg'], _res)

    def test_mAtpGetFileDefault(self):
        _page = self._agent.mRequest(self._agent.mAgentUrl() + "AtpGetFile?file=x.txt")
        _res = 'AtpGetFile endpoint has not been configured, '
        _res += 'please set base path in exacloud configuration..\n'
        _res += 'For more information, consult the exacloud.log.'
        self.assertEqual(json.loads(_page)['err_msg'], _res)

