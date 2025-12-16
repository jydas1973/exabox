#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/ec_ingestion/tests_exacompute_ingestion.py /main/1 2023/05/23 15:27:29 gparada Exp $
#
# tests_exacompute_ingestion.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_exacompute_ingestion.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    gparada     05/19/23 - 35370215 Added getInitialIngestion, consumed by ECRA
#    gparada     05/19/23 - Creation
#

import json
import os
import unittest

from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from unittest.mock import patch

from exabox.jsondispatch.handler_exacompute_ingestion import ExacomputeIngestionHandler

class mockStream():

    def __init__(self, aStreamContents=["None"]):
        self.stream_content = aStreamContents

    def readlines(self):
        return self.stream_content[0].split("\n")

    def read(self):
        return self.stream_content[0]
    
class ebTestExacomputeIngestionHandler(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    def test_payload(self):
        _options = self.mGetContext().mGetArgsOptions()

        # No payload
        _options.jsonconf = {}
        _handler = ExacomputeIngestionHandler(_options)
        self.assertFalse(_handler.mParseJsonConfig())

        # No hostname in payload
        _options.jsonconf = {"someKey": "someVal"}
        _handler = ExacomputeIngestionHandler(_options)
        self.assertFalse(_handler.mParseJsonConfig())

        # Correct payload
        _options.jsonconf = self.mGetResourcesJsonFile("payload_ingestion.json")
        _handler = ExacomputeIngestionHandler(_options)
        self.assertTrue(_handler.mParseJsonConfig())

    def test_executeExaComputeIngestion(self):
        #
        # Prepare test
        #
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload_ingestion.json")

        _expected_out = (
            "id:                                d9b456d3-68af-52c8-d9b4-56d368af52c8\n" 
            "hostName:                          sea201610exdd001\n"
            "state:                             REGISTERING\n"
            "giClusterID:                       \n"
            "giClusterName:                     \n"
            "EDV Driver Base Version Info:\n"
            "  EDV Driver Version               23.1.90.0.0.230402\n"
            "EDV Driver Online Patch Version Info:\n"
            "  EDV Online Patch Driver Version: None\n"
            )        

        _fail_out = (
            "id:                                \n"
            "hostName:                          \n"
            "state:                             OFFLINE\n"
            "giClusterID:                       \n"
            "giClusterName:                     \n"
            "EDV Driver Base Version Info:\n"
            "  EDV Driver Version               23.1.90.0.0.230402\n"
            "EDV Driver Online Patch Version Info:\n"
            "  EDV Online Patch Driver Version: None\n"
            )  

        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream([_expected_out]), None)),\
            patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0):
            _handler = ExacomputeIngestionHandler(_options)
            _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 0)
        self.assertEqual(_result, {'ec_details': {'dummy.dom0.us.oracle.com': 'd9b456d3-68af-52c8-d9b4-56d368af52c8'}})

        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream([_fail_out]), None)),\
            patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=1):
            _handler = ExacomputeIngestionHandler(_options)
            _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 1)
        self.assertEqual(_result, {})

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
