#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_log_management.py /main/1 2023/03/16 12:32:45 chandapr Exp $
#
# tests_log_management.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_log_management.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    chandapr    03/13/23 - Creation
#

import os
import json
import unittest
import subprocess
import base64

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.managment.src.LogManagementEndpoint import LogManagementEndpoint

import unittest
from unittest.mock import Mock, call

class ebTestRemoteManagmentLogManagement(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)

        _exaccPath = os.path.join(self.mGetUtil(self).mGetOutputDir(), "exacc")
        os.system("mkdir -p {0}".format(_exaccPath))

        _logManagerPath = os.path.join(_exaccPath, "logmanager")
        os.system("mkdir -p {0}".format(_logManagerPath))

        _metaDataDirPath = os.path.join(_logManagerPath, "metadata_repos")
        os.system("mkdir -p {0}".format(_metaDataDirPath))

    def test_000_mPost(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _temp = "/tmp"
        _service_name = "monitor202302"
        # Execute endpoint
        _body = {
            "name": _service_name,
            "payload": "e30K"
        }
        _endpoint = LogManagementEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mPost()
        
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        self.assertEqual(_endpoint.mGetResponse()['text'], "Registeration of new service is successful.")

    def test_001_mPost_errors(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _temp = "/tmp"
        
        #Missing payLoad json
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": None
        }
        _endpoint = LogManagementEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass json registeration file to register.")

        # Missing name
        _body = {
            "name": None,
            "payload": "e30K"
        }
        _endpoint = LogManagementEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass name of the service to register.")
        

        # PayLoad File not found
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": "e30K"
        }
        _endpoint = LogManagementEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "because", "No such file or directory present."))
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Error registering the service because No such file or directory present.")

        # Invalid json
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": "e30K"
        }
        _endpoint = LogManagementEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "because", "invalid json file"))
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Error registering the service because invalid json file")

        

        # Invalid install_dir
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", None)
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": "e30K"
        }
        _endpoint = LogManagementEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], 'install_dir key is missing or pointing to an invalid directory. ' \
                                                            'Please review exacloud/exabox/managment/config/basic.conf')

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file