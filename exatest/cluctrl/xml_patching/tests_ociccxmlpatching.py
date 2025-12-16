"""

 $Header: 

 Copyright (c) 2018, 2022, Oracle and/or its affiliates.

 NAME:
      tests_ociccxmlpatching.py - Unitest for xmlpatching on clucontrol

 DESCRIPTION:
      Run tests for the method of xmlpatching on clucontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)

        jesandov    07/27/18 - Creation of the file for xmlpatching
        vgerard     05/09/19 - Adapt test for OCICC
"""

import unittest
import os
import sys
import time
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from exabox.tools.ebTree.ebTree import ebTree
from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class ebTestXmlPatching(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        _resources = "exabox/exatest/cluctrl/xml_patching/resources/ociccpatching/"
        super().setUpClass(aResourceFolder=_resources)

        self.__resultXml = ebTree(_resources + 'result.xml')
        self.__payload = self.mGetResourcesJsonFile(self, 'ocicc_payload.json')
        self.__payloadMin  = self.mGetResourcesJsonFile(self, 'ocicc_min_payload.json')
        self.__payloadDom0 = self.mGetResourcesJsonFile(self, 'ocicc_dom0only_payload.json')
        self.__payloadBad  = self.mGetResourcesJsonFile(self, 'ocicc_payload_bad.json')

    def mTestPatching(self, aPayload, aReference, aIdx):

        # Execute XML Patching
        self.mGetClubox().mSetOciExacc(True)
        self.mGetClubox().mParseXMLConfig(aPayload)

        # Save patched XML
        _xmlText = self.mGetClubox().mGetConfig().mGetConfigXMLData()
        _filename = "test_ocicc_patching_result{0}.xml".format(aIdx)
        _filename = os.path.join(self.mGetUtil().mGetOutputDir(), _filename)
        
        with open(_filename, "w") as f:
            f.write(_xmlText)

        # Compare with result
        _resultXML = ebTree(_filename)
        _diff = _resultXML.mTricolorTree(self.__resultXml)

        _skipTags = ["TimeZone", "slave", "natVlanId", "natGateway"]
        _nodeDiffs = _diff.mGetNodesByType("Red") + _diff.mGetNodesByType("Green")

        for _node in _nodeDiffs:
            if _node.mGetSortElement() not in _skipTags:
                self.assertEqual(_node, None)

    def test__patching(self):
        self.mTestPatching(self.__payload,self.__resultXml,1)

    def test__patching_min(self):
        self.mTestPatching(self.__payloadMin,self.__resultXml,2)

    def test__patching_dom0(self):
        self.mTestPatching(self.__payloadDom0,self.__resultXml,3)

    def test__patching_bad(self):
        self.assertRaises(Exception, self.mGetClubox().mParseXMLConfig, self.__payloadBad)

    def test__network_patching(self):
        # Expected result
        _result = [
            "eth6 eth7",
            "eth4 eth5",
            "eth6 eth7",
            "eth4 eth5"
        ]

        # Adding networking set
        self.mGetClubox().mSetNetworkDiscovered(aAdminNet='vmeth1::eth1',
                                                aClientNet='vmbondeth0:eth4,eth5:bondeth0',
                                                aBackupNet='vmbondeth1:eth6,eth7:bondeth1')

        # Execute XML Patching
        self.mGetClubox().mSetOciExacc(True)
        self.mGetClubox().mParseXMLConfig(self.__payloadDom0)

        # Save patched XML
        _xmlText = self.mGetClubox().mGetConfig().mGetConfigXMLData()
        _filename = "test_ocicc_patching_result{0}.xml".format(4)
        _filename = os.path.join(self.mGetUtil().mGetOutputDir(), _filename)

        with open(_filename, "w") as f:
            f.write(_xmlText)

        # Compare with result
        _resultXML = ebTree(_filename)
        _diff = _resultXML.mTricolorTree(self.__resultXml)

        _nodeDiffs = _diff.mGetNodesByType("Red")

        _network_patched_interfaces = []

        for _node in _nodeDiffs:
            if _node.mGetSortElement() == 'slave':
                _network_patched_interfaces.append(_node.mGetElement()["text"])

        self.assertEqual(_result, _network_patched_interfaces)


if __name__ == '__main__':
    unittest.main()

