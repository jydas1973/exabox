#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_cps_tuner.py /main/7 2023/10/04 17:22:33 anhiguer Exp $
#
# tests_help.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_help.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    anhiguer    09/07/23 - 35787795 - Adding UT for get exec_status 
#    anhiguer    05/18/23 - 34874427 - CLI Tests for cpstuner endpoint
#    harshpa     02/15/23 - Enh 34874477 - CPSTUNER V7: REMOTEEC ENDPOINT FOR
#                           CPSTUNER_FIXBUNDLE_STATUS.JSON
#    alsepulv    04/19/21 - Enh 32789412: Change _exaccpath
#    jesandov    04/05/21 - Creation
#

import json
import os
import unittest
from unittest.mock import MagicMock
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.managment.src.CPSTunerEndpoint import CPSTunerEndpoint

class ebTestRemoteManagmentCpsTuner(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)

        _exaccPath = os.path.join(self.mGetUtil(self).mGetOutputDir(), "exacc")
        os.system("mkdir -p {0}".format(_exaccPath))

        _scriptPath = os.path.join(self.mGetUtil(self).mGetOutputDir(), "script")
        os.system("mkdir -p {0}".format(_scriptPath))


    def mCreateVersionJSON(self, aFilename, aContent):

        with open(aFilename, "w") as _f:
            _f.write("'----START-JSON-DATA----")
            _f.write(aContent)
            _f.write("'----END-JSON-DATA----")


    def test_000_mPost(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create Valid json path
        _version = os.path.join(_exaccpath, "..",  "script/version.json")
        self.mCreateVersionJSON(_version, "{}")

        # Execute endpoint
        _body = {
            "op": "status"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)

        os.remove(_version)

    def test_000_mGet(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create Valid json path
        _bundle_version = os.path.join(_exaccpath, "..",  "script/cpstuner_fixBundle_status.json")
        self.mCreateVersionJSON(_bundle_version, "{}")

        # Execute endpoint
        _body = {
            "op": "bundle_status"
        }
        _endpoint = CPSTunerEndpoint(_body, None, {}, _shared)
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)

        os.remove(_bundle_version)


    def test_001_mPost_errors(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create Valid json path
        _version = os.path.join(_exaccpath, "..",  "script/version.json")
        self.mCreateVersionJSON(_version, "{}")

        # Invalid file for read
        os.chmod(_version, 0x000)
        _body = {
            "op": "status"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # File not found
        os.remove(_version)
        _body = {
            "op": "status"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # Missing op
        self.mCreateVersionJSON(_version, "{}")
        _body = {
            "op": None
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # Invalid json
        self.mCreateVersionJSON(_version, "exatest")
        _body = {
            "op": "status"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['text'], "exatest'")

        os.remove(_version)

        # Invalid install_dir
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", None)

        _body = {
            "op": "status"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

    def test_001_mGet_errors(self):

        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create Valid json path
        _bundle_version = os.path.join(_exaccpath, "..",  "script/cpstuner_fixBundle_status.json")
        self.mCreateVersionJSON(_bundle_version, "{}")

        # Invalid file for read
        os.chmod(_bundle_version, 0x000)
        _body = {
            "op": "bundle_status"
        }
        _endpoint = CPSTunerEndpoint(_body, None, {}, _shared)
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # File not found
        os.remove(_bundle_version)
        _body = {
            "op": "bundle_status"
        }
        _endpoint = CPSTunerEndpoint(_body, None, {}, _shared)
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # Missing op
        self.mCreateVersionJSON(_bundle_version, "{}")
        _body = {
            "op": None
        }
        _endpoint = CPSTunerEndpoint(_body, None, {}, _shared)
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        os.remove(_bundle_version)

        # Invalid install_dir
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", None)

        _body = {
            "op": "bundle_status"
        }
        _endpoint = CPSTunerEndpoint(_body, None, {}, _shared)
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
    
    
    def test_mPut_wrong_flag(self):
        """
        Test cpstuner endpoint for setting up downlaodLatest flag.
        Passing wrong values
        """
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        # Execute endpoint
        _body = {
            "op": "set",
            "flag": "wrong"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)


    def test_mPut_download_specific_bundle(self):
        """
        Test cpstuner endpoint for download an specific bundle
        """
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        # Execute endpoint
        _body = {
            "op": "download",
            "flag": "wrong"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        self.mBashExecution = MagicMock(return_value=(0, "", ""))
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)


    def test_mPut_download_wrong_bundle(self):
        """
        Test cpstuner endpoint for download a wrong bundle
        """
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        # Execute endpoint
        _body = {
            "op": "download",
            "flag": "wrong"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        self.mBashExecution = MagicMock(return_value=(1, "", ""))
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)
    
    def test_mGet_exec_status(self):
        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create Valid json path
        cpstuner_execute_status_path = os.path.join(_exaccpath, "cpstuner/config/cpstuner_applyScript_execStatus.conf")
        os.makedirs(os.path.dirname(cpstuner_execute_status_path), exist_ok=True)
        with open(cpstuner_execute_status_path, "w") as f:
            f.write('{}')
        # Execute endpoint
        _body = {
            "op": "exec_status"
        }
        _endpoint = CPSTunerEndpoint(_body, None, {}, _shared)

        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        os.remove(cpstuner_execute_status_path)

    def test_add_status_to_execute_status_conf_not_keys_passed(self):
        """
        Not keys to add passed
        """
        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _version = os.path.join(_exaccpath, "..",  "script/version.json")
        self.mCreateVersionJSON(_version, "{}")
        # Execute endpoint
        _body = {
            "op": "exec_status"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        response = _endpoint.mGetResponse()
        self.assertEqual(response['status'], 500)
        self.assertEqual(response['error'], "keys_to_add flag required")
        os.remove(_version)

    def test_add_status_to_execute_status_conf_keys_passed_wrong_json(self):
        """
        Wrong json passed
        """
        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _version = os.path.join(_exaccpath, "..",  "script/version.json")
        self.mCreateVersionJSON(_version, "{}")
        # Execute endpoint
        _body = {
            "op": "exec_status",
            "keys_to_add": "{"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        response = _endpoint.mGetResponse()
        self.assertEqual(response['status'], 500)
        self.assertIn("Error adding new items.", response['error'])
        os.remove(_version)
    def test_add_status_to_execute_status_conf_keys_passed_correct_json(self):
        """
        correct json passed
        """
        # Init Args for endpoint call
        _exaccpath = os.path.join(self.mGetUtil().mGetOutputDir(), "exacc")
        
        self.mGetUtil().mGetRemoteEC().mSetBasicConfigValue("install_dir", _exaccpath)
        cpstuner_execute_status_path = os.path.join(_exaccpath, "cpstuner/config/cpstuner_applyScript_execStatus.conf")
        os.makedirs(os.path.dirname(cpstuner_execute_status_path), exist_ok=True)
        with open(cpstuner_execute_status_path, "w") as f:
            f.write('{"test":"test"}')
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _version = os.path.join(_exaccpath, "..",  "script/version.json")
        self.mCreateVersionJSON(_version, "{}")
        # Execute endpoint
        _body = {
            "op": "exec_status",
            "keys_to_add": "{}"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        with open(cpstuner_execute_status_path, "r") as f:
            json_content = json.load(f)
        self.assertEqual(json_content, {"test":"test"})

        # Test update
        _body = {
            "op": "exec_status",
            "keys_to_add": "{\"test\":\"test2\"}"
        }
        _endpoint = CPSTunerEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        with open(cpstuner_execute_status_path, "r") as f:
            json_content = json.load(f)
        self.assertEqual(json_content, {"test":"test2"})
        os.remove(_version)
if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
