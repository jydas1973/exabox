#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/agent/tests_client.py /main/10 2025/09/12 16:20:01 jesandov Exp $
#
# tests_client.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_client.py
#
#    DESCRIPTION
#      Unit test cases for the file $EC_ROOT/exabox/agent/Client.py
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    abflores    07/18/25 - Fix sop ETF
#    abflores    06/18/25 - Bug 38022923 - Increase coverage
#    prsshukl    04/04/24 - Bug 36480365 - Commenting the unittest
#    avimonda    03/20/24 - Adding unit tests for mGetSystemMetricsFromDB()
#                           and mCheckSystemResourceAvailability().
#    avimonda    12/20/23 - Adding unit tests for mGetSystemMetrics().
#    aypaul      12/12/23 - Updating unit tests for jsondispatch addition.
#    aypaul      08/30/21 - Creation
#
import os
import json
import unittest
import copy
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.agent.Client import ebJobResponse, ebExaClient
import warnings, socket
from six.moves import urllib
from ast import literal_eval

SAMPLE_BODY = [
        "e8d361d4-096b-11ec-9ae6-fa163e8a4946",
        "Done",
        "Mon Aug 30 01:26:01 2021",
        "Mon Aug 30 01:26:32 2021",
        "cluctrl.sim_install",
        "{\"pkeyconf\": false, \"vmcmd\": \"None\", \"jsonconf\": {}, \"steplist\": null, \"debug\": false, \"vmid\": null, \"hostname\": \"slc17qpf.us.oracle.com\", \"enablegilatest\": false, \"log_level\": \"INFO\", \"scriptname\": null, \"disablepkey\": false, \"sshkey\": null, \"patchcluinterface\": false, \"cmd\": \"sim_install\", \"frompath_cmd\": true}",
        "0",
        "No Errors",
        "",
        "",
        "000:: No status info available",
        "scas22adm0506clu7",
        "0",
        "Undef",
        {}
    ]
SAMPLE_PARAMS = json.loads(SAMPLE_BODY[5])
SAMPLE_RESPONSE_JSON = {
            "uuid" : "e8d361d4-096b-11ec-9ae6-fa163e8a4946",
            "status" : "Done",
            "statusinfo" : "000:: No status info available",
            "success" : "True",
            "start_time" : "Mon Aug 30 01:26:01 2021",
            "end_time" : "Mon Aug 30 01:26:32 2021",
            "cmd" : "cluctrl.sim_install",
            "error" : "0",
            "error_str" : "No Errors",
            "body" : SAMPLE_BODY,
            "data" : "Sample data",
            "patch_list" : ["patch details."]
        }

def populateTestOptions(thisOptions):
    thisOptions.jsondispatch = None
    thisOptions.sop = None
    thisOptions.agent = None
    thisOptions.exakms = None
    thisOptions.vmctrl = None
    thisOptions.bmcctrl = None
    thisOptions.clusterctrl = None
    thisOptions.schedgenctrl = None
    thisOptions.status = None
    thisOptions.monitor = None
    thisOptions.patchclu = None
    thisOptions.async = None
    thisOptions.exaunitid = None
    thisOptions.workflowid = None


class testOptions(object): pass

class mockURLlibResponse():

    def __init__(self, aData="None", aStatusCode=200):
        self.status = aStatusCode
        self.data = aData

    def read(self):
        return self.data

class ebTestExaClient(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestExaClient, self).setUpClass(aGenerateDatabase=True, aUseAgent=False)
        warnings.filterwarnings("ignore")
        #Uncomment this once Agent issue in exatest is fixed
        #self.mGetUtil(self).mGetInstallerAgent().mStartAgent()

    @classmethod
    def tearDownClass(self):
        try:
            self.mGetUtil(self).mGetInstallerAgent().mStopAgent()
        except Exception as e:
            pass

    def test_ebJobResponse(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Client.ebJobResponse")

        thisResponseDetails = SAMPLE_RESPONSE_JSON
        thisResponse = ebJobResponse()
        listKeys = list(thisResponseDetails.keys())
        for thisKey in listKeys:
            thisResponse.mPopulate(thisKey, thisResponseDetails[thisKey])
        thisResponse.mSetParams(SAMPLE_PARAMS)

        #Verifying getters which are not hit as part of SRG flow.
        self.assertEqual(thisResponse.mGetXml(), None)
        self.assertEqual(thisResponse.mGetParams().get("hostname"), "slc17qpf.us.oracle.com")
        self.assertEqual(thisResponse.mGetData(), "Sample data")
        self.assertEqual(thisResponse.mGetPatchList()[0], "patch details.")

        returnedStrResponse = thisResponse.mToJson()
        returnedJSONResponse = json.loads(returnedStrResponse)
        self.assertEqual(returnedJSONResponse.get("success"), "True")
        self.assertEqual(returnedJSONResponse.get("statusinfo"), "000:: No status info available")
        self.assertEqual(returnedJSONResponse.get("end_time"), "Mon Aug 30 01:26:32 2021")
        self.assertEqual(returnedJSONResponse.get("error_str"), "No Errors")
        self.assertEqual(returnedJSONResponse.get("body")[0], "e8d361d4-096b-11ec-9ae6-fa163e8a4946")

    def test_ebExaClient(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient constructor.")

        self.mGetClubox().mGetArgsOptions().agent_port = 8090
        ebLogInfo("Agent port {}.".format(self.mGetClubox().mGetArgsOptions().agent_port))
        thisClient = ebExaClient()
        thisClient.mSetQuietMode()

    def test_mBuildResponse(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mBuildResponse.")

        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.status = "00000000-0000-0000-0000-000000000000"

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        thisClient.mBuildResponse(SAMPLE_RESPONSE_JSON)

    def test_mIssueRequest_agent(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.agent")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.agent = "start"#This is weird since agent is mapped to agentcmd which has no entry in the REST_API_MAP. Manual entry shows the status.

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        thisClient.mWaitForCompletion()
        self.assertIsNotNone(thisClient.mGetJsonResponse()['statusinfo'])
        #Uncomment this once Agent issue is fixed
        #self.assertEqual(thisClient.mGetJsonResponse()['statusinfo'], 'Agent is running and reachable')

        thisOptions.agent = "invalidvalue"
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        thisClient.mWaitForCompletion()
        self.assertIsNotNone(thisClient.mGetJsonResponse()['statusinfo'])
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'Invalid or unsupported AGENTCMD command: invalidvalue')

    def test_mIssueRequest_exakms(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.exakms")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.exakms = "sync"
        thisOptions.jsonconf = {}

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        ebLogInfo("Response: {}".format(thisClient.mGetJsonResponse()))

        thisOptions.exakms = "invalidoption"
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error'], '100')

    def test_mIssueRequest_vmctrl(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.vmctrl")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.vmctrl = "list"
        thisOptions.hostname = "scaqab10adm01.us.oracle.com"
        thisOptions.vmid = "scaqab10adm01vm03.us.oracle.com_id"

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        ebLogInfo("Response: {}".format(thisClient.mGetJsonResponse()))

        thisOptions.vmctrl = "invalidoption"
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'Invalid or unsupported VMCTRL command: invalidoption')

    def test_mIssueRequest_bmcctrl(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.bmcctrl")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.bmcctrl = "invalidoption"

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'Invalid or unsupported BMCCTRL command: invalidoption')

        thisOptions.bmcctrl = "add_customer_info"
        thisOptions.hostname = "slc17qpf.us.oracle.com"
        thisOptions.jsonconf = None
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'Invalid BMCCTRL command add_customer_info, missing json config')

        thisOptions.jsonconf = {"key1":"value1"}
        thisOptions.configpath = None
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'Invalid BMCCTRL command add_customer_info, missing xml config')

        thisOptions.configpath = os.path.join(self.mGetUtil().mGetResourcesPath(),"sample.xml")
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)

    def test_mIssueRequest_clusterctrl(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.clusterctrl")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.clusterctrl = "invalidoption"

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'Invalid or unsupported CLUCTRL command: invalidoption')

        thisOptions.clusterctrl = "env_info"
        thisOptions.steplist = None
        thisOptions.undo = None
        thisOptions.verbose = None
        thisOptions.vmid = None
        thisOptions.scriptname = None
        thisOptions.vmcmd = None
        thisOptions.hostname = None
        thisOptions.configpath = None
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], "Invalid CLUCTRL command {}, missing xml config".format(thisOptions.clusterctrl))

        thisOptions.steplist = "sample step list"
        thisOptions.undo = "True"
        thisOptions.verbose = "True"
        thisOptions.vmid = "dummy VMID"
        thisOptions.scriptname = "dummyscript1"
        thisOptions.vmcmd = "start"
        thisOptions.hostname = "hostname1"
        thisOptions.configpath = os.path.join(self.mGetUtil().mGetResourcesPath(),"sample.xml")
        thisOptions.oeda_step = "sample_oeda_step"
        thisOptions.pkeyconf = None
        thisOptions.disablepkey = None
        thisOptions.jsonconf = None
        thisOptions.debug = None
        thisOptions.sshkey = None
        thisOptions.pnode_type = "sample pnode type"
        thisOptions.patch_file_cells = "patch file cells"
        thisOptions.patch_files_dom0s = "patch files dom0"
        thisOptions.patch_version_dom0s = "patch version dom0"
        thisOptions.dgcmd = "dgcmd"
        thisOptions.username = "username"
        thisOptions.enablegilatest = None
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)

        thisOptions.clusterctrl = "diskgroup"
        thisOptions.pkeyconf = "True"
        thisOptions.disablepkey = "True"
        thisOptions.jsonconf = {"key1" : "value1"}
        thisOptions.debug = "True"
        thisOptions.sshkey = "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBDn47GuaHUvLVhOAR5Fo31GOtNtNXVvNTGCC+0PcG+JjZ+WmN01OoxCDU+KR6HbNyAMP1BgacIjm6SDmwxn4Cag="
        thisOptions.enablegilatest = "True"
        thisOptions.diskgroupOp = "invaliddgoperation"
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], "Invalid or unsupported DISKGROUP operation: invaliddgoperation")

        thisOptions.diskgroupOp = "info"
        thisOptions.jsonconf = None
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error'], "4051")

        thisOptions.jsonconf = {"key1" : "value1"}
        thisOptions.hostname = None
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error'], "4053")

        thisOptions.hostname = "hostname1"
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)

    def test_mIssueRequest_schedgenctrl(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.schedgenctrl")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.schedgenctrl = "invalidoption"

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'Invalid or unsupported SCGENCTRL command: invalidoption')

        thisOptions.schedgenctrl = "cleanup_exawatcher_log"
        thisOptions.verbose = None
        thisOptions.jsonconf = None
        thisOptions.debug = None
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)

        thisOptions.verbose = True
        thisOptions.jsonconf = {"key1" : "value1"}
        thisOptions.debug = True
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)

    def test_mIssueRequest_status(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.status")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.status = "00000000-0000-0000-0000-000000000000"

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertIsNotNone(thisClient.mGetJsonResponse()['error_str'])
        #Uncomment this once agent issue is fixed
        #self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'HTTP Error 404: Not Found')

    def test_mIssueRequest_monitor(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.monitor")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.monitor = "invalidOption"

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'Invalid or unsupported MONITOR command: invalidOption')

        thisOptions.monitor = "refresh"
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)

    def test_mIssueRequest_patchclu(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.patchclu")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.patchclu = "invalidOption"

        thisClient = ebExaClient()
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        self.assertEqual(thisClient.mGetJsonResponse()['error_str'], 'Invalid or unsupported PATCH command: invalidOption')

        thisOptions.patchclu = "patchclu_apply"
        thisOptions.hostname = "hostname1"
        thisOptions.jsonconf = {"key1" : "value1"}
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)

    def test_mDumpJson(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mDumpJson")
        self.mGetClubox().mGetArgsOptions().jsonmode = False
        self.mGetClubox().mGetArgsOptions().debug = True

        thisClient = ebExaClient()
        thisClient.mBuildResponse(SAMPLE_RESPONSE_JSON)
        thisClient.mDumpJson()

        self.mGetClubox().mGetArgsOptions().jsonmode = False
        thisClient.mDumpJson()

    def test_mWaitForCompletion(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mWaitForCompletion")

        thisClient = ebExaClient()
        thisClient.mWaitForCompletion()

        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.status = "00000000-0000-0000-0000-000000000000"
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        thisClient.mWaitForCompletion()

        thisOptions.status = None
        thisOptions.vmctrl = "list"
        thisOptions.hostname = "scaqab10adm01.us.oracle.com"
        thisOptions.vmid = "scaqab10adm01vm03.us.oracle.com_id"
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        localJSON = copy.deepcopy(SAMPLE_RESPONSE_JSON)
        localJSON["success"] = "False"
        thisClient.mBuildResponse(localJSON)
        thisClient.mWaitForCompletion()

        localJSON["success"] = "True"
        localJSON["status"] = "Pending"
        thisClient.mBuildResponse(localJSON)
        thisClient.mWaitForCompletion()

        thisClient.mBuildResponse(SAMPLE_RESPONSE_JSON)
        self.mGetClubox().mGetArgsOptions().debug = True
        thisClient.mWaitForCompletion()

    def test_mGetSystemMetricsFromDB(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on mGetSystemMetricsFromDB")
        thisClient = ebExaClient()

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectAllFromEnvironmentResourceDetails', return_value=(None, None, None)),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetNumberOfIdleWorkers', return_value=0):
            self.assertEqual(thisClient.mGetSystemMetricsFromDB(), (0.0,0.0,0))

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectAllFromEnvironmentResourceDetails', return_value=(18.23, 93.59, None)),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetNumberOfIdleWorkers', return_value=3):
            self.assertEqual(thisClient.mGetSystemMetricsFromDB(), (18.23, 93.59, 3))

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectAllFromEnvironmentResourceDetails', return_value=(85.75, 93.12, None)),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetNumberOfIdleWorkers', return_value=15):
            self.assertEqual(thisClient.mGetSystemMetricsFromDB(), (85.75, 93.12, 15))

        ebLogInfo("test on mGetSystemMetricsFromDB succeeded.")


    def test_mCheckSystemResourceAvailability(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on mCheckSystemResourceAvailability")
        thisClient = ebExaClient()

        with patch('exabox.agent.Client.ebExaClient.mGetSystemMetricsFromDB', return_value=(80.12, 85.30, 0)) as mock_mGetSystemMetricsFromDB:
            thisClient.mCheckSystemResourceAvailability(1)
            self.assertEqual(mock_mGetSystemMetricsFromDB.call_count, 10)

        with patch('exabox.agent.Client.ebExaClient.mGetSystemMetricsFromDB', return_value=(80.12, 85.30, 2)) as mock_mGetSystemMetricsFromDB:
            thisClient.mCheckSystemResourceAvailability(1)
            self.assertEqual(mock_mGetSystemMetricsFromDB.call_count, 1)

        ebLogInfo("test on mCheckSystemResourceAvailability succeeded.")

    def test_mPerformRequestWithNoError(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mPerformRequestWithNoError.monitor")

        thisClient = ebExaClient()

        form_data = {'key': 'exatest'}
        with patch('exabox.network.HTTPSHelper.build_opener') as mock_build_opener, \
            patch.object(thisClient, 'mBuildResponse') as mock_mBuildResponse,\
            patch.object(thisClient, 'mBuildErrorResponse') as mock_mBuildErrorResponse:
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"key": "value"}'
            mock_build_opener.return_value = mock_response
            
            thisClient.mPerformRequest(form_data=form_data)

            mock_mBuildResponse.assert_called_once()
            mock_mBuildErrorResponse.assassert_not_called()

    def test_mPerformRequestWithFormDataAndHTTPError(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mPerformRequestWithFormDataAndHTTPError.monitor")

        thisClient = ebExaClient()
        
        form_data = {'key': 'exatest'}
        with patch('exabox.network.HTTPSHelper.build_opener') as mock_build_opener:
            mock_build_opener.side_effect = [urllib.error.HTTPError(None, 120, None, None, None)]
            response = thisClient.mPerformRequest(form_data=form_data)

            self.assertEqual(None, response)

    def test_mPerformRequestWithFormDataAndURLError(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mPerformRequestWithFormDataAndURLError.monitor")

        thisClient = ebExaClient()
        
        form_data = {'key': 'exatest'}
        with patch('exabox.network.HTTPSHelper.build_opener') as mock_build_opener:
            mock_build_opener.side_effect = [urllib.error.URLError("Exatest")]
            response = thisClient.mPerformRequest(form_data=form_data)

            self.assertEqual(None, response)

    def test_mPerformRequestWithFormDataAndError503(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mPerformRequestWithFormDataAndError503.monitor")

        thisClient = ebExaClient()
        
        form_data = {'key': 'exatest'}
        with patch('exabox.network.HTTPSHelper.build_opener') as mock_build_opener,\
             patch.object(thisClient, 'mCheckSystemResourceAvailability') as mock_mCheckSystemResourceAvailability:
            mock_build_opener.side_effect = [urllib.error.HTTPError(None, 503, None, None, None),
                                            urllib.error.HTTPError(None, 503, None, None, None)]
            response = thisClient.mPerformRequest(form_data=form_data)

            mock_mCheckSystemResourceAvailability.assert_called_once()

    def test_mPerformRequestWithFormDataAndSocketError(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mPerformRequestWithFormDataAndSocketError.monitor")

        thisClient = ebExaClient()
        
        form_data = {'key': 'exatest'}
        with patch('exabox.network.HTTPSHelper.build_opener') as mock_build_opener, \
            patch.object(thisClient, 'mPerformTimeout') as mock_mPerformTimeout:
            mock_build_opener.side_effect = [socket.error('Test socket error'), socket.error('Test socket error')]
            
            with self.assertRaises(socket.error):
                thisClient.mPerformRequest(form_data=form_data, aRetryCount=2)
            mock_mPerformTimeout.assert_called()

    def test_mPerformRequestWithFormDataAndException(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mPerformRequestWithFormDataAndException.monitor")

        thisClient = ebExaClient()
        thisClient.mSetQuietMode(True)

        form_data = {'key': 'exatest'}
        with patch('exabox.network.HTTPSHelper.build_opener') as mock_build_opener, \
            patch.object(thisClient, 'mBuildErrorResponse') as mock_mBuildErrorResponse:

            mock_build_opener.side_effect = Exception('Test unexpected exception')
            
            thisClient.mPerformRequest(form_data=form_data, aRetryCount=1)

            mock_mBuildErrorResponse.assert_called_once()

    def test_mBuildResponse_request_status(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mBuildResponse_request_status.agent")

        thisClient = ebExaClient()
        thisClient._ebExaClient__cmdtype = 'request_status'
        aJson = {'key1': 'value1', 'key2': 'value2'}

        thisClient.mBuildResponse(SAMPLE_RESPONSE_JSON)

        thisClient.mDumpJson()

        response = thisClient.mGetJsonResponse()

        self.assertIsNotNone(response)

    def test_mBuildRequest_http_enabled(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mBuildRequest_http_enabled.agent")

        thisClient = ebExaClient()
        thisClient.mSetHostname('exatest.com')
        thisClient.mSetPort(8080)

        aPath = '/path/exatest'
        with patch('exabox.network.HTTPSHelper.is_https_enabled', return_value=False):
            thisClient.mBuildRequest(aPath)

            self.assertEqual(thisClient._ebExaClient__request, f'http://{thisClient._ebExaClient__hostname}:{thisClient._ebExaClient__agent_port}{aPath}')

    def test_mGetSystemMetricsFromDB(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mPermGetSystemMetricsFromDBt.agent")

        thisClient = ebExaClient()

        with patch('exabox.core.DBStore.ebExacloudDB.mSelectAllFromEnvironmentResourceDetails', return_value=(None, None, 2)),\
             patch('exabox.core.DBStore.ebExacloudDB.mGetNumberOfIdleWorkers', return_value=(2)):

            cpu_percent, mem_percent, free_worker = thisClient.mGetSystemMetricsFromDB()
            thisClient.mWaitForCompletion()
        
        self.assertEqual(cpu_percent, 0)
        self.assertEqual(mem_percent, 0)
        self.assertEqual(free_worker, 2)

    def test_mIssueRequestWithJsonDispatch(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequestWithJsonDispatch.monitor")

        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.jsondispatch = 'test_jsondispatch'
        thisOptions.jsonconf = '{"key": "value"}'
        
        thisClient = ebExaClient()

        with patch.object(thisClient, 'mBuildRequest') as mock_mBuildRequest, \
            patch.object(thisClient, 'mPerformRequest') as mock_mPerformRequest:
            thisClient.mIssueRequest(aOptions=thisOptions)

            mock_mBuildRequest.assert_called()
            mock_mPerformRequest.assert_called_once_with({'jsonconf': '{"key": "value"}', 'cmd': 'test_jsondispatch'})

    def test_mIssueRequestWithSop(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequestWithSop.monitor")

        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.sop = True
        thisOptions.jsonconf = None

        thisClient = ebExaClient()

        #Test without conf
        with patch.object(thisClient, 'mBuildRequest') as mock_mBuildRequest, \
            patch.object(thisClient, 'mPerformRequest') as mock_mPerformRequest:
            thisClient.mIssueRequest(aOptions=thisOptions)

            mock_mBuildRequest.assert_called()
            mock_mPerformRequest.assert_called_once_with({'jsonconf': {}})

        #Test with conf
        thisOptions.jsonconf = {"key": "value"}

        with patch.object(thisClient, 'mBuildRequest') as mock_mBuildRequest, \
            patch.object(thisClient, 'mPerformRequest') as mock_mPerformRequest:
            thisClient.mIssueRequest(aOptions=thisOptions)

            mock_mBuildRequest.assert_called()
            mock_mPerformRequest.assert_called_once_with({'jsonconf': {"key": "value"}})

        #Test with string conf
        thisOptions.jsonconf = '{"key": "value"}'

        with patch.object(thisClient, 'mBuildRequest') as mock_mBuildRequest, \
            patch.object(thisClient, 'mPerformRequest') as mock_mPerformRequest:
            thisClient.mIssueRequest(aOptions=thisOptions)

            mock_mBuildRequest.assert_called()
            mock_mPerformRequest.assert_called_once_with({'jsonconf': {"key": "value"}})


    def test_mIssueRequestWithInvalidAgentOption(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequestWithInvalidAgentOption.monitor")

        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.agent = 'exaTestAgent'

        thisClient = ebExaClient()

        with patch.object(thisClient, 'mBuildErrorResponse') as mock_mBuildErrorResponse:

            thisClient.mIssueRequest(aOptions=thisOptions)

            mock_mBuildErrorResponse.assert_called_once()

    def test_mIssueRequestWithAgentOption(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequestWithAgentOption.monitor")

        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.agent = "start"

        thisClient = ebExaClient()

        with patch.object(thisClient, 'mBuildRequest') as mock_mBuildRequest,\
             patch.object(thisClient, 'mPerformRequest') as mock_mPerformRequest:

            thisClient.mIssueRequest(aOptions=thisOptions)

            mock_mBuildRequest.assert_called_once()
            mock_mPerformRequest.assert_called_once()


if __name__ == "__main__":
    unittest.main()
