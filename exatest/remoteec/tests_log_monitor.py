#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_log_monitor.py /main/4 2023/05/19 05:57:14 chandapr Exp $
# tests_log_monitor.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
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
#    dekuckre    04/24/26 - Adjust log monitor special query request path tests
#    dekuckre    04/24/26 - Adjust LogMonitorEndpoint unit tests for resolved
#                           special-query path
#    shapatna    04/16/26 - Bug 39111671 Enhance UT Coverage for exabox/managment directory
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
from unittest.mock import Mock, call, patch

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

    def _mMakeInstallDir(self, aName, aCreateMetadata=False, aCreateConfig=False, aCreateConfigFile=False):
        _install_dir = os.path.join(self.mGetUtil().mGetOutputDir(), aName)
        os.makedirs(_install_dir, exist_ok=True)

        _logmanager_dir = os.path.join(_install_dir, "logmanager")
        if aCreateMetadata or aCreateConfig or aCreateConfigFile:
            os.makedirs(_logmanager_dir, exist_ok=True)

        if aCreateMetadata:
            os.makedirs(os.path.join(_logmanager_dir, "metadata_repos"), exist_ok=True)

        if aCreateConfig or aCreateConfigFile:
            _config_dir = os.path.join(_logmanager_dir, "config")
            os.makedirs(_config_dir, exist_ok=True)
            if aCreateConfigFile:
                with open(os.path.join(_config_dir, "logmanager.conf"), "a"):
                    pass

        return _install_dir

    def _mMakeEndpoint(self, aBody=None, aArgs=None, aResponse=None, aInstallDir=None):
        if aBody is None:
            aBody = {}
        if aResponse is None:
            aResponse = {}
        if aInstallDir is None:
            aInstallDir = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")

        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", aInstallDir)
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        return LogMonitorEndpoint(aArgs, aBody, aResponse, _shared)

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

    # Auto-generated test for mPost
    def test_002_mpost_reports_missing_metadata_directory(self):
        _install_dir = self._mMakeInstallDir("exacc_missing_metadata")
        _endpoint = self._mMakeEndpoint({
            "name": "svc1",
            "payload": "e30K"
        }, aInstallDir=_install_dir)

        _endpoint.mPost()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "{0} is an invalid config path for Log Monitoring. Please review exacloud/exabox/managment/config/basic.conf".format(
                os.path.join(_install_dir, "logmanager", "metadata_repos")
            )
        )

    # Auto-generated test for mPost
    def test_003_mpost_reports_payload_decode_error(self):
        _endpoint = self._mMakeEndpoint({
            "name": "svc1",
            "payload": "bad-data"
        })

        with patch("exabox.managment.src.LogMonitorEndpoint.base64.b64decode",
                   side_effect=Exception("bad payload")):
            _endpoint.mPost()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(_endpoint.mGetResponse()["error"], "Error decoding payload: bad payload")

    # Auto-generated test for mPost
    def test_004_mpost_reports_tempfile_exception(self):
        _endpoint = self._mMakeEndpoint({
            "name": "svc1",
            "payload": "e30K"
        })

        with patch("exabox.managment.src.LogMonitorEndpoint.tempfile.NamedTemporaryFile",
                   side_effect=Exception("temp failure")):
            _endpoint.mPost()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Error registering the service in primary host temp failure "
        )

    # Auto-generated test for mPost
    def test_005_mpost_rejects_invalid_service_name(self):
        _endpoint = self._mMakeEndpoint({
            "name": "../svc1",
            "payload": "e30K"
        })

        _endpoint.mPost()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Invalid service name. Service name must match [A-Za-z0-9_.-]+"
        )

    # Auto-generated test for mGet
    def test_001_mget_executes_all_services_without_name(self):
        _endpoint = self._mMakeEndpoint(aArgs=None)
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))

        _endpoint.mGet()

        _endpoint.mBashExecution.assert_called_once_with(
            ["/usr/bin/python3", "/opt/oci/exacc/logmanager/logMonitorProcess.py"],
            subprocess.PIPE
        )
        self.assertEqual(_endpoint.mGetResponse()["status"], 200)
        self.assertEqual(_endpoint.mGetResponse()["text"], "Execution of service: None is successful.")

    # Auto-generated test for mGet
    def test_002_mget_reports_invalid_install_dir(self):
        _endpoint = self._mMakeEndpoint(aArgs={"name": "svc1"}, aInstallDir=None)
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", None)
        _endpoint = LogMonitorEndpoint({"name": "svc1"}, {}, {}, self.mGetUtil().mGetRemoteEC().mGetShared())

        _endpoint.mGet()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "install_dir key is missing or pointing to an invalid directory. Please review exacloud/exabox/managment/config/basic.conf"
        )

    # Auto-generated test for mGet
    def test_003_mget_reports_missing_metadata_directory(self):
        _install_dir = self._mMakeInstallDir("exacc_missing_get_metadata")
        _endpoint = self._mMakeEndpoint(aArgs={"name": "svc1"}, aInstallDir=_install_dir)

        _endpoint.mGet()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "{0} is an invalid config path for Log Monitoring. Please review exacloud/exabox/managment/config/basic.conf".format(
                os.path.join(_install_dir, "logmanager", "metadata_repos")
            )
        )

    # Auto-generated test for mGet
    def test_004_mget_reports_bash_exception(self):
        _endpoint = self._mMakeEndpoint(aArgs={"name": "svc1"})
        _endpoint.mBashExecution = Mock(side_effect=RuntimeError("get failure"))

        _endpoint.mGet()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Error executing the service in primary host get failure "
        )

    # Auto-generated test for mGet
    def test_005_mget_reports_nonzero_execution_status(self):
        _endpoint = self._mMakeEndpoint(aArgs={"name": "svc1"})
        _endpoint.mBashExecution = Mock(return_value=(1, "stdout", "stderr"))

        _endpoint.mGet()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Error executing the registered service. stdout stderr"
        )

    # Auto-generated test for mGet
    def test_006_mget_rejects_invalid_service_name(self):
        _endpoint = self._mMakeEndpoint(aArgs={"name": "../svc1"})

        _endpoint.mGet()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Invalid service name. Service name must match [A-Za-z0-9_.-]+"
        )

    # Auto-generated test for validate_json_data
    def test_000_validate_json_data_handles_valid_and_invalid_json(self):
        _endpoint = self._mMakeEndpoint()

        self.assertTrue(_endpoint.validate_json_data("{}"))
        self.assertFalse(_endpoint.validate_json_data("{"))

    # Auto-generated test for validate_service_name
    def test_001_validate_service_name_rejects_paths_and_invalid_chars(self):
        _endpoint = self._mMakeEndpoint()

        self.assertTrue(_endpoint.validate_service_name("svc1.test-name_01"))
        self.assertFalse(_endpoint.validate_service_name("."))
        self.assertFalse(_endpoint.validate_service_name(".."))
        self.assertFalse(_endpoint.validate_service_name("../svc1"))
        self.assertFalse(_endpoint.validate_service_name("svc1/name"))
        self.assertFalse(_endpoint.validate_service_name("svc1?"))

    # Auto-generated test for mDelete
    def test_001_mdelete_reports_invalid_install_dir(self):
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", None)
        _endpoint = LogMonitorEndpoint(None, {"key": "exec_duration", "value": "1"}, {},
                                       self.mGetUtil().mGetRemoteEC().mGetShared())

        _endpoint.mDelete()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "install_dir key is missing or pointing to an invalid directory. Please review exacloud/exabox/managment/config/basic.conf"
        )

    # Auto-generated test for mDelete
    def test_002_mdelete_reports_missing_config_directory(self):
        _install_dir = self._mMakeInstallDir("exacc_missing_config")
        _endpoint = self._mMakeEndpoint({
            "key": "exec_duration",
            "value": "1"
        }, aInstallDir=_install_dir)

        _endpoint.mDelete()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "{0} is an invalid config path for Log Monitoring. Please review exacloud/exabox/managment/config/basic.conf".format(
                os.path.join(_install_dir, "logmanager", "config")
            )
        )

    # Auto-generated test for mDelete
    def test_003_mdelete_reports_missing_config_file(self):
        _install_dir = self._mMakeInstallDir("exacc_missing_config_file", aCreateConfig=True)
        _endpoint = self._mMakeEndpoint({
            "key": "exec_duration",
            "value": "1"
        }, aInstallDir=_install_dir)

        _endpoint.mDelete()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "{0} is an invalid config file path for Log Monitoring. Please review exacloud/exabox/managment/config/basic.conf".format(
                os.path.join(_install_dir, "logmanager", "config")
            )
        )

    # Auto-generated test for mDelete
    def test_004_mdelete_reports_bash_exception(self):
        _endpoint = self._mMakeEndpoint({
            "key": "exec_duration",
            "value": "1"
        })
        _endpoint.mBashExecution = Mock(side_effect=RuntimeError("delete failure"))

        _endpoint.mDelete()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Error updating the config in primary host delete failure "
        )

    # Auto-generated test for mDelete
    def test_005_mdelete_reports_nonzero_execution_status(self):
        _endpoint = self._mMakeEndpoint({
            "key": "exec_duration",
            "value": "1"
        })
        _endpoint.mBashExecution = Mock(return_value=(1, "stdout", "stderr"))

        _endpoint.mDelete()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Error updating the config for log monitoring service. stdout stderr"
        )

    # Auto-generated test for mPatch
    def test_002_mpatch_reports_decode_error(self):
        _endpoint = self._mMakeEndpoint({
            "payload": "bad-data"
        })

        with patch("exabox.managment.src.LogMonitorEndpoint.base64.b64decode",
                   side_effect=Exception("decode failure")):
            _endpoint.mPatch()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(_endpoint.mGetResponse()["error"], "Error decoding payload: bad-data")

    # Auto-generated test for mPatch
    def test_003_mpatch_uses_generated_json_file_without_service_name(self):
        _endpoint = self._mMakeEndpoint({
            "payload": "e30K"
        })
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _expected_temp_json_path, _expected_temp_json_file = _endpoint.resolve_special_query_file(None)

        _endpoint.mPatch()

        self.assertTrue(os.path.isdir(_expected_temp_json_path))
        self.assertEqual(
            _expected_temp_json_file,
            os.path.join(_expected_temp_json_path, "temp.json")
        )
        self.assertEqual(_endpoint.mBashExecution.call_count, 2)
        _copy_cmd = _endpoint.mBashExecution.call_args_list[0][0][0]
        _exec_cmd = _endpoint.mBashExecution.call_args_list[1][0][0]
        self.assertEqual(_copy_cmd[-1], _expected_temp_json_file)
        self.assertEqual(_exec_cmd, [
            "/usr/bin/python3",
            "/opt/oci/exacc/logmanager/logMonitorSpecialQuery.py",
            "--File={0}".format(_expected_temp_json_file)
        ])

    # Auto-generated test for mPatch
    def test_004_mpatch_uses_service_json_name_when_name_is_present(self):
        _endpoint = self._mMakeEndpoint({
            "name": "svc1",
            "payload": "e30K"
        })
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))
        _, _expected_temp_json_file = _endpoint.resolve_special_query_file("svc1")

        _endpoint.mPatch()

        _copy_cmd = _endpoint.mBashExecution.call_args_list[0][0][0]
        _exec_cmd = _endpoint.mBashExecution.call_args_list[1][0][0]
        self.assertEqual(_copy_cmd[-1], _expected_temp_json_file)
        self.assertEqual(
            _expected_temp_json_file,
            os.path.realpath(
                os.path.join(
                    self.mGetUtil().mGetOutputDir(),
                    "exacc",
                    "logmanager",
                    "svc1.json"
                )
            )
        )
        self.assertEqual(_exec_cmd, [
            "/usr/bin/python3",
            "/opt/oci/exacc/logmanager/logMonitorSpecialQuery.py",
            "--File={0}".format(_expected_temp_json_file),
            "--ServiceName=svc1"
        ])

    # Auto-generated test for mPatch
    def test_005_mpatch_reports_missing_logmanager_directory(self):
        _install_dir = self._mMakeInstallDir("exacc_missing_logmanager")
        _endpoint = self._mMakeEndpoint({
            "payload": "e30K"
        }, aInstallDir=_install_dir)

        _endpoint.mPatch()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "{0} is an invalid config path for LogMonitor. Please review exacloud/exabox/managment/config/basic.conf".format(
                os.path.join(_install_dir, "logmanager")
            )
        )

    # Auto-generated test for mPatch
    def test_006_mpatch_reports_execution_failure_after_copy(self):
        _endpoint = self._mMakeEndpoint({
            "name": "svc1",
            "payload": "e30K"
        })
        _endpoint.mBashExecution = Mock(side_effect=[
            (0, "", ""),
            (1, "stdout", "stderr")
        ])

        _endpoint.mPatch()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(_endpoint.mGetResponse()["error"], "Error executing the special query: stdout stderr")

    # Auto-generated test for mPatch
    def test_007_mpatch_reports_tempfile_exception(self):
        _endpoint = self._mMakeEndpoint({
            "payload": "e30K"
        })

        with patch("exabox.managment.src.LogMonitorEndpoint.tempfile.NamedTemporaryFile",
                   side_effect=Exception("patch temp failure")):
            _endpoint.mPatch()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Error execution of special query failed: patch temp failure "
        )

    # Auto-generated test for mPatch
    def test_008_mpatch_rejects_invalid_service_name(self):
        _endpoint = self._mMakeEndpoint({
            "name": "../svc1",
            "payload": "e30K"
        })

        _endpoint.mPatch()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Invalid service name. Service name must match [A-Za-z0-9_.-]+"
        )

    # Auto-generated test for mPut
    def test_002_mput_reports_invalid_json_query(self):
        _endpoint = self._mMakeEndpoint({
            "query": "{"
        })

        _endpoint.mPut()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(_endpoint.mGetResponse()["error"], "Found invalid JSON data, please pass valid json")

    # Auto-generated test for mPut
    def test_003_mput_appends_service_name_to_special_query_command(self):
        _endpoint = self._mMakeEndpoint({
            "query": "{}",
            "name": "svc1"
        })
        _endpoint.mBashExecution = Mock(return_value=(0, "", ""))

        _endpoint.mPut()

        _endpoint.mBashExecution.assert_called_once_with([
            "/usr/bin/python3",
            "/opt/oci/exacc/logmanager/logMonitorSpecialQuery.py",
            "--JSONData={}",
            "--ServiceName=svc1"
        ], subprocess.PIPE)
        self.assertEqual(_endpoint.mGetResponse()["status"], 200)

    # Auto-generated test for mPut
    def test_004_mput_reports_bash_exception(self):
        _endpoint = self._mMakeEndpoint({
            "query": "{}"
        })
        _endpoint.mBashExecution = Mock(side_effect=RuntimeError("put failure"))

        _endpoint.mPut()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Error execution of special query failed: put failure "
        )

    # Auto-generated test for mPut
    def test_005_mput_rejects_invalid_service_name(self):
        _endpoint = self._mMakeEndpoint({
            "query": "{}",
            "name": "../svc1"
        })

        _endpoint.mPut()

        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(
            _endpoint.mGetResponse()["error"],
            "Invalid service name. Service name must match [A-Za-z0-9_.-]+"
        )

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
