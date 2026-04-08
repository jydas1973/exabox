#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/tests_template.py jesandov_bug-39039331/1 2026/03/04 14:16:49 jesandov Exp $
#
# test_template.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      test_template.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      https://confluence.oraclecorp.com/confluence/display/EDCS/Exacloud+Exatest+Framework
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    02/03/26 - Creation
#

import unittest

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

#other exacloud imports

class TestName(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_testname(self):

        _cmds = {
            ".*" : [ # <------- List of Instance of mConnect
                [
                    exaMockCommand("cmd", aRc=0, aStdout="output"), # <--- Specific mock command by instance of mConnect
                    exaMockCommand("cmd", aRc=1, aStderr="error")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Update of exabox.conf property
        #self.mGetContext().mSetConfigOption('<property_name>', <property_valye>)

        # Update jsonconf payload
        #_payload = self.mGetPayload()
        #_payload["property_name"] = "property_value"
        #self.mGetClubox().mGetArgsOptions().jsonconf = _payload

        #Additional resources goes here

        #Execute the clucontrol function
        #self.mGetClubox().<clucontrolFx>()

        #Assert test goes here

if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end file 
