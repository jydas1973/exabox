#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/proxy/tests_client.py /main/1 2022/03/24 23:18:20 aypaul Exp $
#
# tests_client.py
#
# Copyright (c) 2022, Oracle and/or its affiliates. 
#
#    NAME
#      tests_client.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      03/21/22 - Creation
#
import unittest, warnings, socket, json
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.Context import get_gcontext
from exabox.proxy.Client import ebHttpClient
from six.moves import urllib

MOCK_JSON_RESPONSE="""{
    "key1": "value1"
}"""
MOCK_RESPONSE_HEADERS={"header_key1": "header_value1"}
MOCK_HEADERS_LIST = [('Authorization', 'mock_type mock_authkey'), ('Transfer-encoding', 'chunked')]
MOCK_RESPONSE_BODY = ["a0c03abe-6c08-476b-8eb1-a20ce8c1b53a", "Done", "time start value", "time end value", "mock cmd type", "mock params", \
                      567, "mock error string", "", "", "Detailed status information", "", "", "", ["patch_value1", "patch_value2"]]

class testOptions(object): pass

class mockURLlibResponse():

    def __init__(self, aData="None", aStatusCode=200):
        self.status = aStatusCode
        self.data = aData

    def read(self):
        return self.data

class ebTestProxyClient(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestProxyClient, self).setUpClass(aGenerateDatabase=True)
        warnings.filterwarnings("ignore")
        self.db = ebGetDefaultDB()

    def test_ebHttpClient_init(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebHttpClient.__init__")

        _proxy_client_handle = ebHttpClient()
        _proxy_client_handle._ebHttpClient__rawJSONResponse = {"key1": "value1"}
        _str_json_response = _proxy_client_handle.mGetRawJSONResponse()
        self.assertEqual(_str_json_response, MOCK_JSON_RESPONSE)

        _proxy_client_handle._ebHttpClient__respHeaders = MOCK_RESPONSE_HEADERS
        _resp_json_headers = _proxy_client_handle.mGetResponseHeaders()
        self.assertEqual(_resp_json_headers, MOCK_RESPONSE_HEADERS)

        _proxy_client_handle.mSetCmd("mock_command_type")
        self.assertEqual(_proxy_client_handle._ebHttpClient__cmdtype, "mock_command_type")

        _proxy_client_handle.mSetQuietMode("mock_quiet_mode")
        self.assertEqual(_proxy_client_handle._ebHttpClient__quiet, "mock_quiet_mode")
        ebLogInfo("Unit test on ebHttpClient.__init__ succeeded.")

    def test_mBuildRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebHttpClient.mBuildRequest")

        _proxy_client_handle = ebHttpClient()
        _proxy_client_handle._ebHttpClient__hostname = "mock_hostname"
        _proxy_client_handle._ebHttpClient__agent_port = "mock_agent_port"
        _proxy_client_handle._ebHttpClient__options.debug = True

        with patch('exabox.proxy.Client.HTTPSHelper.is_https_enabled', side_effect=iter([True, False])):
             _proxy_client_handle.mBuildRequest("?mock_path.html")
             _proxy_client_handle.mBuildRequest("?mock_path.html")
        ebLogInfo("Unit test on ebHttpClient.mBuildRequest succeeded.")

    def test_mSetRequestHeader(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebHttpClient.mSetRequestHeader")

        _proxy_client_handle = ebHttpClient()
        _proxy_client_handle._ebHttpClient__hostname = "mock_hostname"
        _proxy_client_handle._ebHttpClient__agent_port = "mock_agent_port"
        _proxy_client_handle._ebHttpClient__authkey = "mock_authkey"

        with patch('exabox.proxy.Client.HTTPSHelper.is_https_enabled', return_value=False):
             _proxy_client_handle.mBuildRequest("?mock_path.html")
             _proxy_client_handle.mSetRequestHeader("Authorization", "mock_value", "mock_type")
             _proxy_client_handle.mSetRequestHeader("Transfer-Encoding", "chunked", "mock_type")

             self.assertEqual(_proxy_client_handle._ebHttpClient__request.header_items(), MOCK_HEADERS_LIST)
        ebLogInfo("Unit test on ebHttpClient.mSetRequestHeader succeeded.")

    def test_mPerformRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebHttpClient.mPerformRequest")

        _proxy_client_handle = ebHttpClient()
        _proxy_client_handle._ebHttpClient__authkey = "mock_authkey"
        _proxy_client_handle._ebHttpClient__hostname = "mock_hostname"
        _proxy_client_handle._ebHttpClient__agent_port = "mock_agent_port"

        with patch('exabox.proxy.Client.HTTPSHelper.build_opener', side_effect=urllib.error.HTTPError(120, "mock http error", {}, None, None)),\
             patch('exabox.proxy.Client.ebHttpClient.mBuildErrorResponse'):
            _proxy_client_handle.mPerformRequest()

        with patch('exabox.proxy.Client.HTTPSHelper.build_opener', side_effect=urllib.error.URLError(121, "mock http error")),\
             patch('exabox.proxy.Client.ebHttpClient.mBuildErrorResponse'):
            _proxy_client_handle.mPerformRequest()

        with patch('exabox.proxy.Client.HTTPSHelper.build_opener', side_effect=socket.error(300, "mock socket error", "mock failure message", None, None)),\
             patch('exabox.proxy.Client.ebHttpClient.mBuildErrorResponse'):
            self.assertRaises(socket.error, _proxy_client_handle.mPerformRequest)

        with patch('exabox.proxy.Client.HTTPSHelper.build_opener', return_value=mockURLlibResponse(json.dumps({"key1":"value1", "key2":"value2"}))),\
             patch('exabox.proxy.Client.ebHttpClient.storeResponseHeadersAsDictionary'),\
             patch('exabox.proxy.Client.ebHttpClient.mBuildErrorResponse'),\
             patch('exabox.proxy.Client.ebHttpClient.mBuildResponse', side_effect=iter(["", Exception("Build response error")])):
            _proxy_client_handle.mPerformRequest({"key1": "formdata_val1", "key2": "formdata_val2"})
            _proxy_client_handle.mPerformRequest({"key1": "formdata_val1", "key2": "formdata_val2"})
        ebLogInfo("Unit test on ebHttpClient.mPerformRequest succeeded.")

    def test_mBuildResponse(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebHttpClient.mBuildResponse")

        _proxy_client_handle = ebHttpClient()
        _proxy_client_handle.mBuildResponse({"invalid key": {}})
        _proxy_client_handle._ebHttpClient__cmdtype = "request_status"
        _proxy_client_handle.mBuildResponse({"body": MOCK_RESPONSE_BODY})
        ebLogInfo("Unit test on ebHttpClient.mBuildResponse succeeded.")

    def test_mBuildErrorResponse(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebHttpClient.mBuildErrorResponse")

        _proxy_client_handle = ebHttpClient()
        _proxy_client_handle._ebHttpClient__cmdtype = "vm_cmd"
        _proxy_client_handle.mBuildErrorResponse(500, "mock error string", {"body": MOCK_RESPONSE_BODY}, "mock data")
        ebLogInfo("Unit test on ebHttpClient.mBuildErrorResponse succeeded.")

    def test_mDumpJson(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebHttpClient.mDumpJson")

        _proxy_client_handle = ebHttpClient()
        _proxy_client_handle._ebHttpClient__options.debug = True
        _proxy_client_handle._ebHttpClient__jsonresponse = json.dumps({"body": MOCK_RESPONSE_BODY})
        _proxy_client_handle.mDumpJson()

        _proxy_client_handle._ebHttpClient__options.jsonmode = False
        _proxy_client_handle.mDumpJson()
        ebLogInfo("Unit test on ebHttpClient.mDumpJson succeeded.")

    def test_mIssueRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebHttpClient.mIssueRequest")

        _proxy_client_handle = ebHttpClient()
        _mock_options = testOptions()
        _mock_options.host = "mockhostname"
        _mock_options.port = 7866
        _mock_options.authKey = "mock authorization key"
        _mock_options.path = "/mock_path"
        _mock_options.data = {"mock_data_key": "mock_data_value"}
        _mock_options.headers = {"host": "mock_host"}

        with patch('exabox.proxy.Client.ebHttpClient.mBuildRequest'),\
             patch('exabox.proxy.Client.ebHttpClient.mPerformRequest'),\
             patch('exabox.proxy.Client.ebHttpClient.mSetRequestHeader'):
             _proxy_client_handle.mIssueRequest(_mock_options)
        ebLogInfo("Unit test on ebHttpClient.mIssueRequest succeeded.")

if __name__ == "__main__":
    unittest.main(warnings='ignore')