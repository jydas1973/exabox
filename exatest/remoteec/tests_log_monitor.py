#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_log_monitor.py /main/4 2023/05/19 05:57:14 chandapr Exp $
# tests_log_monitor.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_log_monitoring.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    chandapr    08/05/23 - Bug#35362141 Update UT regression (PATCH string response)
#    chandapr    05/05/23 - Bug#35230563 Add tests for off-query endpoints (config params)
#    chandapr    04/11/23 - Bug#35230549 Add tests for off-query endpoints
#    chandapr    02/28/23 - Bug#35085772 Add tests for general remoteec endpoints (mock mBashExecution for tests)
#    chandapr    02/23/23 - Creation
#

import os
import json
import unittest
import subprocess
import base64

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.managment.src.LogMonitorEndpoint import LogMonitorEndpoint

import unittest
from unittest.mock import Mock, call

class ebTestRemoteManagmentLogMonitoring(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)

        _exaccPath = os.path.join(self.mGetUtil(self).mGetOutputDir(), "exacc")
        os.system("mkdir -p {0}".format(_exaccPath))

        _logManagerPath = os.path.join(_exaccPath, "logmanager")
        os.system("mkdir -p {0}".format(_logManagerPath))

        _metaDataDirPath = os.path.join(_logManagerPath, "metadata_repos")
        os.system("mkdir -p {0}".format(_metaDataDirPath))
        
        _configDirPath = os.path.join(_logManagerPath, "config")
        os.system("mkdir -p {0}".format(_configDirPath))

        _configFile = os.path.join(_configDirPath, "logmanager.conf")
        os.system("touch {0}".format(_configFile))

    def test_000_mPost(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _temp = "/tmp"
        _service_name = "monitor202302"
        _payload_json_file_path = os.path.join(_temp,  "hello.json")
        # Execute endpoint
        _body = {
            "name": _service_name,
            "payload": "e30K"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
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
        _payload_json_file_path = os.path.join(_temp,  "hello.json")
        
        #Missing payLoad json
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": None
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass json registeration file to register.")

        # Missing name
        _body = {
            "name": None,
            "payload": "e30K"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass name of the service to register.")
        

        # PayLoad File not found
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": "e30K"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "because", "No such file or directory present."))
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Error registering the service because No such file or directory present.")

        # Invalid json
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": "e30K"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
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
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], 'install_dir key is missing or pointing to an invalid directory. ' \
                                                            'Please review exacloud/exabox/managment/config/basic.conf')

    def test_000_mGet(self):
        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        __service_name = "logmon_query_monitor202212"
        # Execute endpoint
        _args = {
            "name": __service_name
        }
        _response = {}
        _endpoint = LogMonitorEndpoint(_args, None, _response, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mGet()

        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        expected_output = "Execution of service: logmon_query_monitor202212 is successful."         
        self.assertEqual(_endpoint.mGetResponse()['text'], expected_output)

    def test_000_mPatch(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _temp = "/tmp"
        _service_name = "monitor202302"
        _payload_json_file_path = os.path.join(_temp,  "hello.json")
        # Execute endpoint
        _body = {
            "name": _service_name,
            "payload": "e30K"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mPatch()
        
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        self.assertEqual(_endpoint.mGetResponse()['text'], "Execution of special query json_data is successful.")
 
    def test_001_mPatch(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _temp = "/tmp"
        _service_name = "monitor202302"
        _payload_json_file_path = os.path.join(_temp,  "hello.json")
        # Execute endpoint
        _body = {
            "payload": "e30K"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mPatch()
        
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        self.assertEqual(_endpoint.mGetResponse()['text'], "Execution of special query json_data is successful.")

    def test_001_mPatch_errors(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _temp = "/tmp"
        _payload_json_file_path = os.path.join(_temp,  "hello.json")
        
        #Missing payLoad json
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": None
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mPatch()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass json file to execute.")

        # PayLoad File not found
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": "e30K"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "because", "No such file or directory present."))
        _endpoint.mPatch()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Error copying temporary json file because No such file or directory present.")

        # Invalid json
        _body = {
            "name": "testdummylogmgmt2021",
            "payload": "e30K"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "because", "invalid json data file"))
        _endpoint.mPatch()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Error copying temporary json file because invalid json data file")

    def test_000_mPut(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        
        # Execute endpoint
        _body = {
            "query": "{}"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mPut()
        
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        self.assertEqual(_endpoint.mGetResponse()['text'], "Execution of special query is successful.")
 
    def test_001_mPut(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Execute endpoint
        _body = {
            "query": "{}",
            "name": "testXXXdummy"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mPut()
        
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        self.assertEqual(_endpoint.mGetResponse()['text'], "Execution of special query is successful.")
 
    def test_001_mPut_errors(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        
        #Missing query json
        _body = {
            "name": "testdummylogmgmt2021",
            "query": None
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "because", "JSON data as query is required, please pass json data"))
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "JSON data as query is required, please pass json data")

        #Invalid query json
        _body = {
            "query": "{}"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "because", "No such file or directory present."))
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Error executing the special query: because No such file or directory present.")

    def test_000_mDelete(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "key": "exec_duration",
            "value": "3500"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        self.assertEqual(_endpoint.mGetResponse()['text'], "New config paramater added : exec_duration is successful.")

    def test_000_mDelete_errors(self):
        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "key": None,
            "value": None
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass a key for the config value.")

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "key": None,
            "value": "2334"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass a key for the config value.")

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "key": "exec_duration",
            "value": None
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass a value for the config key.")

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "key": None,
            "value": None
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass a key for the config value.")

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "key": None,
            "value": "2334"
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass a key for the config value.")

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "key": "exec_duration",
            "value": None
        }
        _endpoint = LogMonitorEndpoint(None, _body, {}, _shared)
        _endpoint.mBashExecution = Mock(return_value=(1, "", ""))
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
        self.assertEqual(_endpoint.mGetResponse()['error'], "Please pass a value for the config key.")

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file

