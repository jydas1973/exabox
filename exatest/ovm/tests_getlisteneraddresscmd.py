#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_getlisteneraddresscmd.py /main/1 2026/02/04 09:26:27 jesandov Exp $
#
# test_getlisteneraddresscmd.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      test_getlisteneraddresscmd.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    02/03/26 - Creation
#
import unittest
from unittest.mock import patch

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

#other exacloud imports

class TestHandleExaCCGetListenerAddress(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_main_endpoint_xen(self):

        _cmds = {
            self.mGetRegexDom0() : [
                [
                    exaMockCommand("imageinfo", aRc=0, aStdout="22.1.0.0.1"),
                    exaMockCommand("iptables", aRc=0, aStdout="160.100.1.1"),
                ],[
                    exaMockCommand("imageinfo", aRc=0, aStdout="22.1.0.0.1"),
                    exaMockCommand("iptables", aRc=0, aStdout="160.100.1.1"),
                ],[
                    exaMockCommand("imageinfo", aRc=0, aStdout="22.1.0.0.1"),
                    exaMockCommand("iptables", aRc=0, aStdout="160.100.1.1"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Modify Payload
        _payload = _options = self.mGetPayload()
        _options["vmid"] = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        self.mGetClubox().mGetArgsOptions().jsonconf = _payload

        #Execute the clucontrol function
        self.mGetClubox().mHandleExaCCGetListenerAddress()

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True)
    def test_main_endpoint_kvm(self, iskv):

        _cmds = {
            self.mGetRegexDom0() : [
                [
                    exaMockCommand("imageinfo", aRc=0, aStdout="26.1.0.0.1"),
                    exaMockCommand("nft", aRc=0, aStdout="160.100.1.1"),
                ],[
                    exaMockCommand("imageinfo", aRc=0, aStdout="26.1.0.0.1"),
                    exaMockCommand("nft", aRc=0, aStdout="160.100.1.1"),
                ],[
                    exaMockCommand("imageinfo", aRc=0, aStdout="26.1.0.0.1"),
                    exaMockCommand("nft", aRc=0, aStdout="160.100.1.1"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Modify Payload
        _payload = _options = self.mGetPayload()
        _options["vmid"] = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        self.mGetClubox().mGetArgsOptions().jsonconf = _payload

        #Execute the clucontrol function
        self.mGetClubox().mHandleExaCCGetListenerAddress()


if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end file 
