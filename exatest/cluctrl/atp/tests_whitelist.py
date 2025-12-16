"""

 $Header:

 Copyright (c) 2018, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_whitelist.py - Unitest for whitelist related classes

 DESCRIPTION:
      Run tests for the method of whitelist on clucontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)

    jesandov   10/08/18 - Add ExacloudUtil module implementation
    nelchan    09/11/18 - Creation of the file
"""

import unittest
from exabox.exatest.common.ebExacloudUtil import ebExacloudUtil, ebJsonObject
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.atp import *
import os
import sys

MY_TEST_JSON={
    "atp": {
        "AutonomousDb": "Y",
        "whitelist": {
            "client": {
                "protocol" : {
                    "tcp" : "22,443,6200,2484"
                },
                "ip": {
                }
            },
            "backup": {
                "protocol": {
                    "tcp" : "22",
                    "udp" : "1231",
                    "icmp" : ""
                }
            }
        }
    }
}

MY_WRONG_TEST_JSON={
    "atp": {
        "AutonomousDb": "Y",
        "whitelist": {
            "clients": {
                "protocols" : {
                    "tcp" : "22,443,6200,2484"
                },
                "ip": {
                }
            },
            "backup": {
                "protocol": {
                    "tcp" : "22",
                    "udp" : "1231",
                    "icmp" : ""
                }
            }
        }
    }
}

class ebTestWhitelist(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        _path = 'exabox/exatest/resources/xmlpatching/'
        self._util = ebExacloudUtil(_path)
        self._clubox = self._util.mPrepareEnviroment()

    def test_loadJson(self):
        tcpPosts = ebAtpUtils.mGetDictFromGen2Payload(MY_TEST_JSON, "atp/whitelist/client/protocol/tcp")
        self.assertEqual(tcpPosts, "22,443,6200,2484")
        tcpPosts = ebAtpUtils.mGetDictFromGen2Payload(MY_TEST_JSON, "atp/whitelist/client/protocol/tc")
        self.assertEqual(tcpPosts, {'tcp': '22,443,6200,2484'})
        #self.assertRaises(KeyError, ebAtpUtils.mGetDictFromGen2Payload, MY_TEST_JSON, "atp/whitelist/client/protocol/tc")
        #self.assertRaises(KeyError, ebAtpUtils.mGetDictFromGen2Payload, MY_TEST_JSON, "atp/whitelist/client/protocol/tcp")

if __name__ == '__main__':
    unittest.main()
