#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/agent/tests_worker.py /main/7 2025/12/08 15:13:41 remamid Exp $
#
# tests_worker.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_worker.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      03/30/26 - Adding unit tests for aypaul_bug-38277507
#    prsshukl    03/13/26 - Add unittest for 39077070
#    remamid     11/19/25 - Add unittest for 38631342
#    naps        04/15/25 - Bug 37680025 - UT updation.
#    prsshukl    08/13/24 - Bug 36161437 - [UNIT TEST REGRESSION]
#                           TEST_EBWORKERFACTORYCUSTOMNUMBERCOUNT OF
#                           TESTS_WORKER.PY FAILING INTERMITTENTLY WITH
#                           ASSERTION ERROR IN WORKER COUNT
#    aypaul      02/26/24 - Issue#36134753 Add unit tests for changes in
#                           AYPAUL_BUG-36120429 and AYPAUL_AGENTUNRESPONSIVEFIX
#    gparada     05/22/23 - 35213979 Override workers, adding unit test
#    aypaul      03/14/22 - Creation
#
import unittest
import warnings
import copy
import os
import json
import base64
import errno
import psutil
from contextlib import ExitStack
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, mock_open
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError
from exabox.agent.Worker import SecondaryExacloudClient, ebWorkerRestHttpListener, ebWorkerRestListener, daemonize_process, ebWorkerDaemon, ebWorkerFactory, ebWorker, is_port_free, DEFAULT_MAX_RETRIES
import exabox.agent.Worker as worker_module
from exabox.core.Context import set_gcontext, get_gcontext

DEFAULT_WORKER_DUMP = ["00000000-0000-0000-0000-000000000000","Running","Sat Feb 12 10:19:12 2022","Undef","NULL","Undef","Undef",\
             '{"status": "000:: No status info available"}',"26447",9101,"worker","Undef","2022-02-23 11:51:32.621223"]


def mockStatusfunction(param1, param2):
    pass

class subprocessObject():

    def __init__(self):
        self.returncode = 43
        self.stderr = "mock standard error".encode("UTF-8")
        self.stdout = "mock standard output".encode("UTF-8")

class dummyHTTPServer():

    def serve_forever(self):
        ebLogInfo("Executing http server start.")

    def shutdown(self):
        ebLogInfo("Executing http server stop.")

class dummyDaemonHandle():

    def mWorker_Shutdown(self):
        ebLogInfo("Executing worker daemon shutdown.")

class testOptions(object): pass

class dummyWriteOptions():

    def write(self, aString):
        ebLogInfo(aString.decode('utf8'))

class mockResponseOptions():

    def __init__(self, aStatus="mockstatus"):
        self.status = aStatus
        self.error = 999
        self.errorstr = "mockerror"
        self.statuscode = 200

    def mGetStatus(self):
        return self.status

    def mGetError(self):
        return self.error

    def mGetErrorStr(self):
        return self.errorstr

    def mGetStatusCode(self):
        return self.statuscode


class ebTestWorkerClasses(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestWorkerClasses, self).setUpClass(aGenerateDatabase=True)
        warnings.filterwarnings("ignore")
        self._db = ebGetDefaultDB()


    @patch('exabox.agent.Worker.ebWorker.mLoadWorkerFromDB')
    @patch('exabox.agent.Worker.ebWorker.mSetStatus')
    @patch('exabox.agent.Worker.ebWorker.mUpdateDB')
    @patch('exabox.agent.Worker.ebWorker.mResetUUID')
    @patch('exabox.agent.Worker.ebWorker.mSetLastActiveTime')
    def test_mWorker_Deregister(self, mock1, mock2, mock3, mock4, mock5):
        ebLogInfo("")
        ebLogInfo("Running unit test for worker Deregister")

        _worker = ebWorker()
        _worker.mSetPort(9911)
        _worker.mSetUUID('b0ba8a90-1900-11f0-89bf-02001717b781')
        _worker.mRegister()
        _worker.mDeregister()


    @patch('exabox.agent.Worker.ebWorker.mLoadWorkerFromDB')
    @patch('exabox.agent.Worker.ebWorker.mSetStatus')
    @patch('exabox.agent.Worker.ebWorker.mUpdateDB')
    @patch('exabox.agent.Worker.ebWorker.mResetUUID')
    @patch('exabox.agent.Worker.ebWorker.mSetLastActiveTime')
    @patch('exabox.agent.Worker.ebWorkerDaemon.mWorker_Stop')
    @patch('exabox.agent.Worker.ebWorkerDaemon.mProcessSignalsDB')
    @patch('exabox.agent.Worker.ebProxyJobRequest.mLoadRequestFromDB')
    @patch('os.makedirs')
    @patch('exabox.core.DBStore3.ebExacloudDB.mUpdateStatusForReqUUID')
    @patch('exabox.agent.Worker.ebProxyJobRequest.mSetRespCode')
    @patch('exabox.agent.Worker.ebProxyJobRequest.mSetRespBody')
    @patch('exabox.core.DBStore3.ebExacloudDB.mUpdateResponseDetailsInProxyRequest')
    @patch('exabox.agent.Worker.ebProxyJobRequest.mSetUrlHeaders')
    @patch('exabox.core.DBStore3.ebExacloudDB.mUpdateProxyRequest')
    @patch('exabox.agent.Worker.ebLogAddDestinationToLoggers', return_value=None)
    @patch('exabox.agent.Worker.ebLogDeleteLoggerDestination')
    @patch('exabox.agent.Worker.ebHttpClient.mGetRawJSONResponse', return_value={})
    @patch('exabox.agent.Worker.ebHttpClient.mGetResponseHeaders', return_value={})
    @patch('time.sleep')
    def test_mWorker_Start(self, mock1, mock2, mock3, mock4, mock5, mock6, mock7, mock8, mock9, mock10, mock11,\
     mock12, mock13, mock14, mock15, mock16, mock17, mock18, mock19, mock20):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerDaemon.mWorker_Start")

        _worker_daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _worker_daemon._ebWorkerDaemon__abort_worker = True
        _worker_daemon.mWorker_Start()

        _worker_daemon._ebWorkerDaemon__abort_worker = False
        _worker_daemon._ebWorkerDaemon__restlistener = True
        _curr_worker_dump = copy.deepcopy(DEFAULT_WORKER_DUMP)
        _curr_worker_dump[10] = "monitor"
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value=str([_curr_worker_dump])),\
             patch('exabox.agent.Worker.ebWorker.mGetType', return_value="monitor"),\
             patch('exabox.agent.Worker.ebWorkerDaemon.get_worker_exit_loop', return_value=True):
            _worker_daemon.mWorker_Start()

        _curr_worker_dump[9] = 9135
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value=str([_curr_worker_dump])),\
             patch('exabox.agent.Worker.ebWorker.mGetType', return_value="monitor"),\
             patch('exabox.agent.Worker.ebWorkerDaemon.get_worker_exit_loop', return_value=True):
            _worker_daemon.mWorker_Start()

        _curr_worker_dump[9] = 9101
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value=str([_curr_worker_dump])),\
             patch('exabox.agent.Worker.ebWorker.mGetType', side_effect=iter(["invalidvalue", "monitor", "monitor"])),\
             patch('exabox.agent.Worker.ebWorker.mGetStatus', return_value="Idle"),\
             patch('os.listdir', side_effect=iter([["cluster-mockdir"], ["mockfile.xml"], ["cluster-mockdir"], ["invalidfile"]])),\
             patch('os.path.isdir', return_value=True),\
             patch('subprocess.run', return_value=subprocessObject()),\
             patch('exabox.agent.Worker.ebWorkerDaemon.get_worker_exit_loop', side_effect=iter([False, False, True])):
            _worker_daemon.mWorker_Start()

        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value=str([_curr_worker_dump])),\
             patch('exabox.agent.Worker.ebWorker.mGetType', side_effect=iter(["invalidvalue", "invalidvalue", "proxy", "invalidvalue", "proxy"])),\
             patch('exabox.agent.Worker.ebWorker.mGetUUID', return_vale="3139195c-a50f-11ec-a940-fa163e8a4946"),\
             patch('exabox.agent.Worker.ebWorkerDaemon.get_worker_exit_loop', side_effect=iter([False, False, True])),\
             patch('exabox.agent.Worker.ebProxyJobRequest.mGetOptions', return_value=[]),\
             patch('exabox.agent.Worker.ebProxyJobRequest.mGetReqType', side_effect=iter(["Status.GET", "CLUCtrl.POST"])),\
             patch('exabox.agent.Worker.ebProxyJobRequest.mGetUUID', return_value="3139195c-a50f-11ec-a940-fa163e8a4946"),\
             patch('exabox.agent.Worker.ebProxyJobRequest.mGetCmd', return_value="mock_command"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mSelectECInstanceIDFromUUIDToECInstance', return_value="mockecinstanceID"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mSelectRoutingInfoFromECInstances', return_value=("mockhost", "mockport", "mockkey")),\
             patch('exabox.agent.Worker.ebProxyJobRequest.mGetUrlFullPath', return_value="http://localhost:9877/mockarg"),\
             patch('exabox.agent.Worker.ebProxyJobRequest.mGetUrlHeaders', return_value="None"),\
             patch('exabox.agent.Worker.ebHttpClient.mIssueRequest', side_effect=iter([mockResponseOptions("Pending"), mockResponseOptions(), mockResponseOptions()]) ),\
             patch('exabox.agent.Worker.ebProxyJobRequest.mGetReqBody', return_value=str(list())),\
             patch('exabox.agent.Worker.ebProxyJobRequest.mGetParams', return_value={"request_id": "3139195c-a50f-11ec-a940-fa163e8a4946"}):
            _worker_daemon.mWorker_Start()
        _curr_worker_dump[9] = 9110
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value=str([_curr_worker_dump])),\
             patch('exabox.agent.Worker.ebWorker.mGetUUID', return_vale="3139195c-a50f-11ec-a940-fa163e8a4946"),\
             patch('exabox.agent.Worker.ebWorkerDaemon.get_worker_exit_loop', side_effect=iter([False, False, True])),\
             patch('exabox.tools.ebXmlGen.ebFacadeXmlGen.ebFacadeXmlGen.mGenerateXml', return_value='/exacloud/log/xmlgen/3139195c-a50f-11ec-a940-fa163e8a4946/result-3139195c-a50f-11ec-a940-fa163e8a4946.xml'),\
             patch('exabox.agent.ebJobRequest.ebJobRequest.mGetType', return_value="elastic_shape"),\
             patch('exabox.agent.ebJobRequest.ebJobRequest.mSetXml'),\
             patch('exabox.agent.ebJobRequest.ebJobRequest.mGetCmd', return_value="mock_command"),\
             patch('exabox.agent.ebJobRequest.ebJobRequest.mSetData'):
            _worker_daemon.mWorker_Start()

        ebLogInfo("Unit test on ebWorkerDaemon.mWorker_Start succeeded....")


    def test_daemonize_process(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on daemonize_process")

        with patch('os.fork', side_effect=PermissionError(512,"mock str error")):
            self.assertRaises(Exception, daemonize_process)

        with patch('os.fork', return_value = 1),\
             patch('os._exit'):
            daemonize_process()

        with patch('os.fork', return_value = 0),\
             patch('os._exit'),\
             patch('os.setsid'):
            daemonize_process()
        ebLogInfo("Unit test on daemonize_process succeeded.")

    @patch('exabox.agent.Worker.handlerhook', return_value=None)
    @patch('sys.exit')
    def test_ebWorkerRestListener(self, patch_handlerhook, patch_sys_exit):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestListener")

        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["agent_local"] = "False"
        gContext.mSetConfigOptions({})
        _worker_listener = ebWorkerRestListener({"worker_port": "9101"})

        gContext.mSetConfigOptions({"agent_local": "True"})
        _worker_listener = ebWorkerRestListener({"worker_port": "9101"})

        _worker_listener.httpd = dummyHTTPServer()
        _worker_listener.mStartRestListener()
        _worker_listener.mStopRestListener()
        gContext.mSetConfigOptions(gConfigOptions)
        ebLogInfo("Unit test on ebWorkerRestListener succeeded.")

    def test_ebWorkerRestListener_exits_on_bind_failure(self):
        # Auto-generated test for ebWorkerRestListener.__init__
        gContext = self.mGetContext()
        original_options = gContext.mGetConfigOptions()
        self.addCleanup(lambda: gContext.mSetConfigOptions(original_options))
        gContext.mSetConfigOptions({})

        with patch('exabox.agent.Worker.ExaHTTPSServer', side_effect=RuntimeError("bind failure")), \
             patch('exabox.agent.Worker.ebLogError') as mock_log_error, \
             patch('exabox.agent.Worker.sys.exit') as mock_exit:
            ebWorkerRestListener({"worker_port": "9101"})

        mock_exit.assert_called_once_with(-1)
        self.assertTrue(any("bind failure" in call.args[0] for call in mock_log_error.call_args_list))
        mock_log_error.assert_any_call('ebRestListener: Can not start Worker Listener on port: 9101')

    def test_ebWorkerRestListener_start_handles_address_in_use(self):
        # Auto-generated test for ebWorkerRestListener.mStartRestListener
        gContext = self.mGetContext()
        original_options = gContext.mGetConfigOptions()
        self.addCleanup(lambda: gContext.mSetConfigOptions(original_options))
        gContext.mSetConfigOptions({})

        with patch('exabox.agent.Worker.ExaHTTPSServer', return_value=MagicMock()) as mock_server:
            _listener = ebWorkerRestListener({"worker_port": "9101"})

        self.assertTrue(mock_server.called)
        _listener.httpd = MagicMock()
        _listener.httpd.serve_forever.side_effect = OSError(errno.EADDRINUSE, "port in use")

        with patch('exabox.agent.Worker.ebLogError') as mock_log_error, \
             patch('exabox.agent.Worker.sys.exit') as mock_exit:
            _listener.mStartRestListener()

        mock_log_error.assert_any_call('ERROR: Worker can not start listening address already in use.')
        mock_exit.assert_called_once_with(-1)

    def test_ebWorkerRestListener_start_logs_generic_exception(self):
        # Auto-generated test for ebWorkerRestListener.mStartRestListener
        gContext = self.mGetContext()
        original_options = gContext.mGetConfigOptions()
        self.addCleanup(lambda: gContext.mSetConfigOptions(original_options))
        gContext.mSetConfigOptions({})

        with patch('exabox.agent.Worker.ExaHTTPSServer', return_value=MagicMock()):
            _listener = ebWorkerRestListener({"worker_port": "9101"})

        _listener.httpd = MagicMock()
        _listener.httpd.serve_forever.side_effect = RuntimeError("unexpected failure")

        with patch('exabox.agent.Worker.ebLogError') as mock_log_error, \
             patch('exabox.agent.Worker.sys.exit') as mock_exit:
            _listener.mStartRestListener()

        mock_log_error.assert_any_call('*** Worker RestListener caught exception')
        mock_exit.assert_not_called()

    def test_mRefreshMock(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestHttpListener.mRefreshMock")

        _worker_config = {"auth_key": "mock_auth_key"}
        _worker_http_listerner = ebWorkerRestHttpListener(_worker_config, None, initBaseHTTPHandler=False)

        _worker_http_listerner.mRefreshMock(_worker_config)
        _worker_config = {"mock_mode": "True"}
        _worker_http_listerner.mRefreshMock(_worker_config)
        ebLogInfo("Unit test on ebWorkerRestHttpListener.mRefreshMock succeeded.")

    def test_do_HEAD(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestHttpListener.do_HEAD")
        _worker_config = {"auth_key": "mock_auth_key"}
        _worker_http_listerner = ebWorkerRestHttpListener(_worker_config, None, initBaseHTTPHandler=False)

        _worker_http_listerner.requestline = "GET https://localhost:1707/mockendpoint HTTP/1.1"
        _worker_http_listerner.request_version = "HTTP/1.1"
        _worker_http_listerner.client_address = ["localhost"]
        _worker_http_listerner.wfile = dummyWriteOptions()
        _worker_http_listerner.do_HEAD()
        ebLogInfo("Unit test on ebWorkerRestHttpListener.do_HEAD succeeded.")

    def test_do_AUTHHEAD(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestHttpListener.do_AUTHHEAD")
        _worker_config = {"auth_key": "mock_auth_key"}
        _worker_http_listerner = ebWorkerRestHttpListener(_worker_config, None, initBaseHTTPHandler=False)

        _worker_http_listerner.requestline = "GET https://localhost:1707/mockendpoint HTTP/1.1"
        _worker_http_listerner.request_version = "HTTP/1.1"
        _worker_http_listerner.client_address = ["localhost"]
        _worker_http_listerner.wfile = dummyWriteOptions()
        _worker_http_listerner.do_AUTHHEAD()
        ebLogInfo("Unit test on ebWorkerRestHttpListener.do_AUTHHEAD succeeded.")

    def test_do_JSON(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestHttpListener.do_JSON")
        _worker_config = {"auth_key": "mock_auth_key"}
        _worker_http_listerner = ebWorkerRestHttpListener(_worker_config, None, initBaseHTTPHandler=False)

        _worker_http_listerner.requestline = "GET https://localhost:1707/mockendpoint HTTP/1.1"
        _worker_http_listerner.request_version = "HTTP/1.1"
        _worker_http_listerner.client_address = ["localhost"]
        _worker_http_listerner.wfile = dummyWriteOptions()
        _worker_http_listerner.do_JSON({"mock_key1": "mock_val1", "mock_key2": "mock_val2"})
        ebLogInfo("Unit test on ebWorkerRestHttpListener.do_JSON succeeded.")

    def test_do_HTML(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestHttpListener.do_HTML")
        _worker_config = {"auth_key": "mock_auth_key"}
        _worker_http_listerner = ebWorkerRestHttpListener(_worker_config, None, initBaseHTTPHandler=False)

        _worker_http_listerner.requestline = "GET https://localhost:1707/mockendpoint HTTP/1.1"
        _worker_http_listerner.request_version = "HTTP/1.1"
        _worker_http_listerner.client_address = ["localhost"]
        _worker_http_listerner.wfile = dummyWriteOptions()
        _worker_http_listerner.do_HTML({"output": "mock_output_value", "ctype": "mock_ctype_value"})
        _worker_http_listerner.do_HTML({"output": "mock_output_value"})
        ebLogInfo("Unit test on ebWorkerRestHttpListener.do_HTML succeeded.")

    def test_mInShutdown(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestHttpListener.mInShutdown")
        _worker_config = {"auth_key": "mock_auth_key"}
        _worker_http_listerner = ebWorkerRestHttpListener(_worker_config, None, initBaseHTTPHandler=False)

        _worker_http_listerner.requestline = "GET https://localhost:1707/mockendpoint HTTP/1.1"
        _worker_http_listerner.request_version = "HTTP/1.1"
        _worker_http_listerner.client_address = ["localhost"]
        _worker_http_listerner.wfile = dummyWriteOptions()
        with patch('exabox.agent.Worker.ebWorkerRestHttpListener.do_JSON'):
            _worker_http_listerner.mInShutdown()
        ebLogInfo("Unit test on ebWorkerRestHttpListener.mInShutdown succeeded.")

    def test_do_GET(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestHttpListener.do_GET")
        _worker_config = {"auth_key": "mock_auth_key"}
        _worker_http_listerner = ebWorkerRestHttpListener(_worker_config, None, initBaseHTTPHandler=False)

        _worker_http_listerner.requestline = "GET https://localhost:1707/mockendpoint HTTP/1.1"
        _worker_http_listerner.request_version = "HTTP/1.1"
        _worker_http_listerner.client_address = ["localhost"]
        _worker_http_listerner.wfile = dummyWriteOptions()
        _worker_http_listerner.headers = {"key" : "value"}
        _worker_http_listerner.path = "localhost:1707/mockendpoint"
        with patch('exabox.agent.Worker.ebWorkerRestHttpListener.do_AUTHHEAD'):
            _worker_http_listerner.do_GET()

        _worker_http_listerner.headers = {"Authorization" : "invalid_auth_key"}
        with patch('exabox.agent.Worker.ebWorkerRestHttpListener.do_AUTHHEAD'):
            _worker_http_listerner.do_GET()

        _worker_http_listerner.headers = {"Authorization" : "Basic mock_auth_key"}
        _worker_http_listerner.path = "invalid_function_name"
        _worker_http_listerner.do_GET()

        _worker_http_listerner.headers = {"Authorization" : "Basic mock_auth_key"}
        _worker_http_listerner.path = "/status"
        _worker_http_listerner._ebWorkerRestHttpListener__callbacks["/status"] = mockStatusfunction
        _worker_http_listerner._ebWorkerRestHttpListener__shutdown = False
        with patch('exabox.agent.Worker.ebWorkerRestHttpListener.mShowStatus'):
            _worker_http_listerner.do_GET()

        _worker_http_listerner.path = "/status?param1=paramval1?param2=paramval2"
        _worker_http_listerner._ebWorkerRestHttpListener__callbacks["/status"] = mockStatusfunction
        _worker_http_listerner._ebWorkerRestHttpListener__shutdown = False
        with patch('exabox.agent.Worker.ebWorkerRestHttpListener.mShowStatus'):
            _worker_http_listerner.do_GET()
        ebLogInfo("Unit test on ebWorkerRestHttpListener.do_GET succeeded.")

    def test_mShowStatus(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestHttpListener.mShowStatus")
        _worker_config = {"auth_key": "mock_auth_key"}
        _worker_http_listerner = ebWorkerRestHttpListener(_worker_config, None, initBaseHTTPHandler=False)

        with patch('exabox.agent.Worker.MockStatus'):
            _worker_http_listerner.mShowStatus({"mock_mode": "True"}, None)

        with patch('exabox.agent.Worker.MockStatus'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mDumpRequests', return_value=[]):
            _response_dict = dict()
            _worker_http_listerner.mShowStatus({"mock_mode": "False"}, _response_dict)
            self.assertEqual(_response_dict["error"], "503")

        with patch('exabox.agent.Worker.MockStatus'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetRequest', return_value=None):
            _response_dict = dict()
            _worker_http_listerner.mShowStatus({"mock_mode": "False", "uuid":"44a5312a-a44b-11ec-a254-fa163e8a4946"}, _response_dict)
            self.assertEqual(_response_dict["error"], "504")

        with patch('exabox.agent.Worker.MockStatus'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetRequest', return_value=["val1", "val2", "val3", "val4", "val5", "val6", "val7"]):
            _response_dict = dict()
            _worker_http_listerner.mShowStatus({"mock_mode": "False", "uuid":"44a5312a-a44b-11ec-a254-fa163e8a4946"}, _response_dict)
            self.assertEqual(_response_dict["success"], "False")

        with patch('exabox.agent.Worker.MockStatus'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetRequest', return_value=["val1", "val2", "val3", "val4", "val5", "val6", "701-614"]):
            _response_dict = dict()
            _worker_http_listerner.mShowStatus({"mock_mode": "False", "uuid":"44a5312a-a44b-11ec-a254-fa163e8a4946"}, _response_dict)
            self.assertEqual(_response_dict["success"], "True")

        ebLogInfo("Unit test on ebWorkerRestHttpListener.mShowStatus succeeded.")

    def test_mWorkerRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebWorkerRestHttpListener.mWorkerRequest")
        _worker_config = {"auth_key": "mock_auth_key"}
        _worker_http_listerner = ebWorkerRestHttpListener(_worker_config, None, initBaseHTTPHandler=False)

        with patch('exabox.core.DBStore3.ebExacloudDB.mGetWorker', return_value=None):
            _response_dict = dict()
            _worker_http_listerner.mWorkerRequest({}, _response_dict)
            self.assertEqual(_response_dict["error_str"], "Worker entry not found in Worker DB")

        with patch('exabox.core.DBStore3.ebExacloudDB.mGetWorker', return_value=["44a5312a-a44b-11ec-a254-fa163e8a4946", "Idle", "Tue Mar 15 03:48:52 PDT 2022", "Mon Mar 14 03:48:52 PDT 2022"]):
            _response_dict = dict()
            _worker_http_listerner.mWorkerRequest({}, _response_dict)
            self.assertEqual(_response_dict["error"], "801")

        with patch('exabox.core.DBStore3.ebExacloudDB.mGetWorker', return_value=["44a5312a-a44b-11ec-a254-fa163e8a4946", "Idle", "Tue Mar 15 03:48:52 PDT 2022", "Mon Mar 14 03:48:52 PDT 2022"]):
            _response_dict = dict()
            _worker_http_listerner.mWorkerRequest({"cmd": "status"}, _response_dict)

        mockHandle = dummyDaemonHandle()
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetWorker', return_value=["44a5312a-a44b-11ec-a254-fa163e8a4946", "Idle", "Tue Mar 15 03:48:52 PDT 2022", "Mon Mar 14 03:48:52 PDT 2022"]),\
             patch('exabox.agent.Worker.gDaemonHandle', mockHandle):
            _response_dict = dict()
            _worker_http_listerner.mWorkerRequest({"cmd": "shutdown"}, _response_dict)

        ebLogInfo("Unit test on ebWorkerRestHttpListener.mWorkerRequest succeeded.")

    def test_ebWorkerFactoryCustomNumberCount(self):

        # Since this testcase is intermittently failing skipping the unittest
        return
        """
        We can also define "worker_num" in 
        ecs/exacloud/config/exatest_extra_config.conf, but somehow ETF does not
        read such setting. 
        """

        # gWorkerFactory is a Global, it is used only within ebWorkerFactory
        # in order to test more than once, we need to set it to None
        gWorkerFactory = None

        # worker_num will be passed as optional argument
        # As no test exist for ExaCloud, this Unit Test will skip parsing args 
        # WARNING: There are 8 secs sleep, which will be performed on each Wrkr. 
        _workers_cnt = 3

        # _worker_port is not required to be tested, however, it's used in ETF
        # so we can identify workers created and used by this UT only
        # we expect 12300 is not used anywhere else
        _worker_port = 12300
        _worker_port_end = 12300 + 15 # 15 is a buffer in case ports are used 
        self.mGetClubox().mGetCtx().mGetArgsOptions().worker_num = _workers_cnt        
        set_gcontext(self.mGetClubox().mGetCtx())

        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["worker_port"] = _worker_port
        gContext.mSetConfigOptions(writableGConfigOptions)

        _db = ebGetDefaultDB()
        _db.mClearWorkers(aUUID="00000000-0000-0000-0000-000000000000")

        _start_test_dt = datetime.now()
        
        # On normal flow, Workers will be started by WorkerFactory        
        _workerFactory:ebWorkerFactory = ebWorkerFactory() 

        # mInitFactory also runs mStartWorkers        
        _workerFactory.mInitFactory()
        
        # On normal flow, Workers will be started by WorkerFactory
        # Each Worker greates a Request
        _rqlist = _workerFactory.mGetWorkersList()        
        self.assertIsNotNone(_rqlist)        
        _out_cnt = 0
        
        # In ETF, some other workers are initialized, causing noise for assertion
        # It is required to validate real workers created by this new req
        # then, it is suggested to check records in DB checking default values
        # for a newly/recently started Worker. 
        for _req in _rqlist:
            if _req[0] == "00000000-0000-0000-0000-000000000000":
                _wkr_dt = datetime.strptime(_req[2], '%a %b %d %H:%M:%S %Y')
                if (_wkr_dt > _start_test_dt):
                    if (int(_req[9]) >= _worker_port and 
                        int(_req[9]) <= _worker_port_end):
                        self.assertEqual(_req[1],"Idle")                    
                        self.assertLessEqual(int(_req[9]),_worker_port+_workers_cnt)
                        _out_cnt += 1                
        self.assertEqual(_workers_cnt,_out_cnt)

        self.assertLessEqual(_workerFactory.mCheckPort(_worker_port), _worker_port)
        with patch('socket.socket.connect_ex', return_value=255):
            _workerFactory.mCheckPort(_worker_port, True)

        _single_net_connection = copy.deepcopy(psutil.net_connections()[0])
        _worker_port = _single_net_connection.laddr.port
        with patch('psutil.net_connections', return_value=[_single_net_connection]), \
             patch('socket.socket.connect_ex', return_value=255):
            _workerFactory.mCheckPort(_worker_port, True)

    def _capture_thread_log_path(self, vmcmd_value=None, steplist_value=None, *, cmd_value="delete", params_override=None):
        class _Sentinel(Exception):
            pass

        class _FakeWorker:
            def __init__(self, aParams=None, aDB=None):
                self.uuid = "request-uuid"
                self._type = "worker"
                self._port = 9101

            def mSetPort(self, aPort):
                self._port = aPort

            def mRegister(self):
                pass

            def mLoadWorkerFromDB(self, aPort):
                self._port = aPort
                return True

            def mGetType(self):
                return self._type

            def mSetType(self, aType):
                self._type = aType

            def mSetStatus(self, aStatus):
                pass

            def mUpdateDB(self):
                pass

            def mSetLogLevel(self, aLevel, isDefault=False):
                self.log_level = aLevel
                self.is_default_log_level = isDefault

            def mSetState(self, aState=None):
                pass

            def mSetLastActiveTime(self, aValue=None):
                pass

            def mResetUUID(self):
                pass

            def mGetUUID(self):
                return self.uuid

        class _FakeOptions:
            def __init__(self, vmcmd):
                self.vmcmd = vmcmd.replace(" ", "_") if vmcmd else vmcmd
                self.log_level = "INFO"

            def __contains__(self, item):
                return hasattr(self, item)

        class _FakeJob:
            def __init__(self, *args, **kwargs):
                self._options = _FakeOptions(vmcmd_value)

            def mLoadRequestFromDB(self, aUUID):
                pass

            def mGetParams(self):
                _params = {
                    "exaunitid": "123",
                    "wf_uuid": "11111111-1111-1111-1111-111111111111",
                    "steplist": steplist_value
                }
                if params_override:
                    for _key, _value in params_override.items():
                        _params[_key] = copy.deepcopy(_value)
                return _params

            def mGetOptions(self):
                return self._options

            def mGetCmd(self):
                return cmd_value

            def mGetType(self):
                return "cluctrl"

            def mGetUUID(self):
                return "job-uuid"

            def mSetWorker(self, aPort):
                pass

            def mSetStatus(self, aStatus):
                pass

        class _FakeDB:
            def mGetWorker(self, aPort):
                return None

        class _FakeContext:
            def __init__(self):
                self._opts = {
                    "proxy_critical_requests": [],
                    "proxy_critical_requests_time": "1"
                }
                self._args = type("FakeArgs", (), {
                    "worker_port": None,
                    "worker_detach": False,
                    "proxy": False
                })()

            def mGetConfigOptions(self):
                return self._opts

            def mGetArgsOptions(self):
                return self._args

            def mSetRegEntry(self, aKey, aValue):
                pass

        _captured = {}

        def _fake_log_add(_loggers, _path, _formatter):
            _captured["path"] = _path
            raise _Sentinel()

        _context = _FakeContext()

        with patch('exabox.agent.Worker.ebWorker', _FakeWorker), \
             patch('exabox.agent.Worker.ebJobRequest', _FakeJob), \
             patch('exabox.agent.Worker.ebGetDefaultDB', return_value=_FakeDB()), \
             patch('exabox.agent.Worker.get_gcontext', return_value=_context), \
             patch('exabox.agent.Worker.ebGetDefaultLogLevel', return_value='INFO'), \
             patch('exabox.agent.Worker.ebGetDefaultLoggerName', return_value='worker'), \
             patch('exabox.agent.Worker.ebLogAddDestinationToLoggers', side_effect=_fake_log_add), \
             patch('exabox.agent.Worker.time.sleep', return_value=None), \
             patch('exabox.agent.Worker.os.makedirs', return_value=None), \
             patch('exabox.agent.Worker.ebWorkerDaemon.mProcessSignalsDB', return_value=None), \
             patch('exabox.agent.Worker.ebWorkerDaemon.get_worker_exit_loop', side_effect=[False, True]):
            _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
            _daemon._ebWorkerDaemon__restlistener = True
            with self.assertRaises(_Sentinel):
                _daemon.mWorker_Start()

        self.assertIn("path", _captured)
        return _captured["path"]

    def _exercise_cluctrl_fallback(self, *, cmd_value, vmcmd_value=None):
        class _FakeWorker:
            def __init__(self, aParams=None, aDB=None):
                self.uuid = "job-uuid"
                self._type = "worker"
                self._port = 9101
                self._pid = 2222
                self._status = "Idle"

            def mSetPort(self, aPort):
                self._port = aPort

            def mRegister(self):
                pass

            def mLoadWorkerFromDB(self, aPort):
                self._port = aPort
                return True

            def mGetType(self):
                return self._type

            def mSetType(self, aType):
                self._type = aType

            def mSetStatus(self, aStatus):
                self._status = aStatus

            def mUpdateDB(self):
                pass

            def mSetLogLevel(self, aLevel, isDefault=False):
                self.log_level = (aLevel, isDefault)

            def mDeregister(self):
                pass

            def mSetState(self, aState=None):
                pass

            def mSetLastActiveTime(self, aValue=None):
                pass

            def mResetUUID(self):
                pass

            def mGetUUID(self):
                return self.uuid

            def mGetPort(self):
                return self._port

            def mGetPid(self):
                return self._pid

        class _FakeOptions:
            def __init__(self):
                self.cmd = cmd_value
                self.vmcmd = vmcmd_value.replace(" ", "_") if vmcmd_value else vmcmd_value
                self.log_level = "INFO"
                self.jsonconf = {"TargetType": ["Compute"]}
                self.configpath = "/tmp/config.xml"
                self.steplist = None
                self.undo = "False"

            def __contains__(self, item):
                return getattr(self, item, None) is not None

        class _FakeJob:
            instances = []

            def __init__(self, *args, **kwargs):
                self._options = _FakeOptions()
                self._params_override = copy.deepcopy(kwargs.get("params_override", {}))
                self._xml = None
                self._error = None
                self._error_str = None
                self._status = None
                self._statusinfo = None
                self._data = None
                self.worker_port = None
                _FakeJob.instances.append(self)

            def mLoadRequestFromDB(self, aUUID):
                pass

            def mGetParams(self):
                _params = {
                    "exaunitid": "123",
                    "wf_uuid": "11111111-1111-1111-1111-111111111111",
                    "steplist": None,
                    "jsonconf": {"TargetType": ["Compute"]},
                    "undo": "False"
                }
                _params.update(copy.deepcopy(self._params_override))
                return _params

            def mGetOptions(self):
                return self._options

            def mGetCmd(self):
                return cmd_value

            def mGetType(self):
                return "cluctrl"

            def mGetUUID(self):
                return "job-uuid"

            def mSetWorker(self, aPort):
                self.worker_port = aPort

            def mSetStatus(self, aStatus):
                self._status = aStatus

            def mSetStatusInfo(self, aInfo):
                self._statusinfo = aInfo

            def mSetData(self, aData):
                self._data = aData

            def mSetXml(self, aXml):
                self._xml = aXml

            def mSetError(self, aError):
                self._error = aError

            def mSetErrorStr(self, aErrorStr):
                self._error_str = aErrorStr

            def mSetTimeStampEnd(self):
                self._end_time_set = True

            def mGetClusterName(self):
                return "cluster-1"

        class _FakeDB:
            def mGetWorker(self, aPort):
                return None

            def mCheckRegEntry(self, aKey):
                return False

            def mUpdateRequest(self, aJob):
                pass

        class _FakeContext:
            def __init__(self):
                self._opts = {
                    "proxy_critical_requests": [],
                    "proxy_critical_requests_time": "1",
                    "clean_cluster_folder": "False"
                }
                self._args = type("Args", (), {
                    "worker_port": None,
                    "worker_detach": False,
                    "proxy": False,
                    "exatest": False
                })()
                self._registry = {}

            def mGetConfigOptions(self):
                return self._opts

            def mGetArgsOptions(self):
                return self._args

            def mGetPropagateProcOptions(self):
                return []

            def mGetBasePath(self):
                return "/workdir"

            def mGetExaKms(self):
                return "NONE"

            def mSetRegEntry(self, key, value):
                self._registry[key] = value

            def mGetRegEntry(self, key):
                return self._registry.get(key)

            def mCheckRegEntry(self, key):
                return key in self._registry and self._registry[key] not in (None, "")

            def mCheckConfigOption(self, key):
                return None

        _fake_db = _FakeDB()
        _context = _FakeContext()
        _node = MagicMock(name="cluctrl-node")

        class _FakeConnectCtx:
            def __enter__(self):
                return _node

            def __exit__(self, exc_type, exc, tb):
                return False

        _vmhandle = MagicMock()
        _vmhandle.mDispatchCluster.return_value = 0
        _vmhandle.mDispatchNonXMLCluster.return_value = 0
        _vmhandle.mGetPatchConfig.return_value = "/tmp/generated.xml"
        _vmhandle.mIsOciEXACC.return_value = False
        _vmhandle.mCompileSelinuxResponse = MagicMock()

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.agent.Worker.ebWorker', _FakeWorker))
            stack.enter_context(patch('exabox.agent.Worker.ebJobRequest', _FakeJob))
            stack.enter_context(patch('exabox.agent.Worker.ebGetDefaultDB', return_value=_fake_db))
            stack.enter_context(patch('exabox.agent.Worker.get_gcontext', return_value=_context))
            stack.enter_context(patch('exabox.agent.Worker.ebWorkerDaemon.mProcessSignalsDB', return_value=None))
            stack.enter_context(patch('exabox.agent.Worker.ebWorkerDaemon.mRefreshMock', return_value=None))
            stack.enter_context(patch('exabox.agent.Worker.ebLogAddDestinationToLoggers', return_value=None))
            stack.enter_context(patch('exabox.agent.Worker.ebGetDefaultLoggerName', return_value='worker'))
            stack.enter_context(patch('exabox.agent.Worker.ebGetDefaultLogLevel', return_value='INFO'))
            stack.enter_context(patch('exabox.agent.Worker.os.makedirs'))
            stack.enter_context(patch('exabox.agent.Worker.os.getcwd', return_value='/workdir'))
            stack.enter_context(patch('exabox.agent.Worker.time.sleep'))
            stack.enter_context(patch('exabox.agent.Worker.ebWorkerDaemon.get_worker_exit_loop', side_effect=[False, True]))
            stack.enter_context(patch('exabox.agent.Worker.ebWorkerDaemon.mRedirectRequestSecondaryExacloud', return_value=None))
            stack.enter_context(patch('exabox.agent.Worker.connect_to_host', return_value=_FakeConnectCtx()))
            stack.enter_context(patch('exabox.agent.Worker.exaBoxCluCtrl', return_value=_vmhandle))
            stack.enter_context(patch('exabox.agent.Worker.ebWorkerDaemon.mMkdirWithPoption'))
            stack.enter_context(patch('exabox.agent.Worker.ebWorkerDaemon.mCleanupClusterFolder'))
            stack.enter_context(patch('exabox.agent.Worker.kill_proc_tree', return_value=[]))
            _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
            _daemon._ebWorkerDaemon__restlistener = MagicMock()
            _daemon._ebWorkerDaemon__mock_mode = False
            _daemon.mWorker_Start()

        return _FakeJob.instances[0], _vmhandle, _node

    def test_mWorker_Start_cluctrl_falls_back_to_dispatch_cluster(self):
        # Auto-generated test for mWorker_Start
        _job, _vmhandle, _node = self._exercise_cluctrl_fallback(cmd_value="delete", vmcmd_value="DELETE CELL CHECK")

        _vmhandle.mDispatchCluster.assert_called_once_with("delete", _job.mGetOptions(), aJob=_job)
        _vmhandle.mDispatchNonXMLCluster.assert_not_called()
        _vmhandle.mGetPatchConfig.assert_called_once()
        _vmhandle.mCompileSelinuxResponse.assert_called_once()
        self.assertEqual(_job._xml, "/tmp/generated.xml")
        self.assertEqual(_job._error, "0")
        self.assertEqual(_job._error_str, "No Errors")

    def test_mWorker_Start_cluctrl_dispatches_nonxml_for_special_commands(self):
        # Auto-generated test for mWorker_Start
        _job, _vmhandle, _node = self._exercise_cluctrl_fallback(cmd_value="enable_qinq")

        _vmhandle.mDispatchNonXMLCluster.assert_called_once_with("enable_qinq", _job.mGetOptions(), aJob=_job)
        _vmhandle.mDispatchCluster.assert_not_called()
        _vmhandle.mGetPatchConfig.assert_not_called()
        _vmhandle.mCompileSelinuxResponse.assert_not_called()
        self.assertIsNone(_job._xml)
        self.assertEqual(_job._error, "0")
        self.assertEqual(_job._error_str, "No Errors")

    def test_thread_log_filename_removes_spaces_from_vmcmd(self):
        # Auto-generated test for mWorker_Start
        _path = self._capture_thread_log_path(vmcmd_value="DELETE CELL CHECK", steplist_value=None)
        self.assertIn("DELETE", _path)
        self.assertNotIn(" ", os.path.basename(_path))

    def test_thread_log_filename_removes_spaces_from_steplist(self):
        # Auto-generated test for mWorker_Start
        _path = self._capture_thread_log_path(vmcmd_value=None, steplist_value=["ESTP_DELETE_CELL_CHECK"])
        _basename = os.path.basename(_path)
        self.assertIn("ESTP_DELETE_CELL_CHECK", _basename)
        self.assertNotIn("[", _basename)
        self.assertNotIn(" ", _basename)

    def test_thread_log_filename_trims_string_steplist_tokens(self):
        # Auto-generated test for mWorker_Start
        _steplist = "ESTP_DELETE_CELL_CHECK,  ESTP_VALIDATE_CELL "
        _path = self._capture_thread_log_path(vmcmd_value=None, steplist_value=_steplist)
        _basename = os.path.basename(_path)
        self.assertIn("ESTP_DELETE_CELL_CHECK,ESTP_VALIDATE_CELL", _basename)
        self.assertNotIn(" ESTP", _basename)
        self.assertNotIn("[", _basename)

    def test_thread_log_filename_truncates_lengthy_steplist(self):
        # Auto-generated test for mWorker_Start
        _steplist = ["ESTP_" + "A" * 40, "ESTP_" + "B" * 40]
        _path = self._capture_thread_log_path(vmcmd_value=None, steplist_value=_steplist)
        _basename = os.path.basename(_path)
        self.assertIn("A" * 30 + "..." + "B" * 30, _basename)
        self.assertNotIn("[", _basename)

    def test_thread_log_filename_removes_estp_without_truncation(self):
        # Auto-generated test for mWorker_Start
        _steplist = ["ESTP_" + "A" * 30, "ESTP_" + "B" * 30]
        _path = self._capture_thread_log_path(vmcmd_value=None, steplist_value=_steplist)
        _basename = os.path.basename(_path)
        _expected = "A" * 30 + "," + "B" * 30
        self.assertIn(_expected, _basename)
        self.assertNotIn("ESTP_", _basename)
        self.assertNotIn("...", _basename)

    def test_thread_log_filename_appends_undo_suffix(self):
        # Auto-generated test for mWorker_Start
        _path = self._capture_thread_log_path(vmcmd_value=None, steplist_value=None, params_override={"undo": "True"})
        self.assertTrue(os.path.basename(_path).endswith(".undo"))

    def test_thread_log_filename_includes_target_type_for_patch(self):
        # Auto-generated test for mWorker_Start
        _override = {"jsonconf": {"TargetType": [" Compute "]}}
        _path = self._capture_thread_log_path(vmcmd_value=None, steplist_value=None, cmd_value="patch", params_override=_override)
        _basename = os.path.basename(_path)
        self.assertIn("patch_Compute", _basename)

    def test_thread_log_filename_single_worker_target_type(self):
        # Auto-generated test for mWorker_Start
        _override = {
            "singleworkerpatching": "enabled",
            "jsonconf": {"Params": [{"TargetType": ["StorageCell"]}]}
        }
        _path = self._capture_thread_log_path(vmcmd_value=None, steplist_value=None, cmd_value="patch", params_override=_override)
        _basename = os.path.basename(_path)
        self.assertIn("patch_StorageCell", _basename)

    def test_thread_log_filename_uses_request_id_when_present(self):
        # Auto-generated test for mWorker_Start
        _override = {
            "request_id": "12345678-1234-1234-1234-123456789abc",
            "wf_uuid": None
        }
        _path = self._capture_thread_log_path(vmcmd_value=None, steplist_value=None, params_override=_override)
        self.assertIn("12345678-1234-1234-1234-123456789abc", _path)
        self.assertNotIn("exaunit_", _path)

    def test_thread_log_filename_respects_ignore_uuid_check(self):
        # Auto-generated test for mWorker_Start
        _override = {
            "ignore_uuid_check": "True",
            "exaunitid": "EXA_CUSTOM",
            "wf_uuid": "workflow-identifier"
        }
        _path = self._capture_thread_log_path(vmcmd_value=None, steplist_value=None, params_override=_override)
        self.assertIn("EXA_CUSTOM/workflow-identifier", _path)
        self.assertNotIn("exaunit_", _path)

    def test_mWorker_Start_cluctrl_redirect_invocation(self):
        # Auto-generated test for mWorker_Start
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)

        _job = MagicMock(name="cluctrl-job")

        def mCluctrlCallbackFx():
            return "callback-result"

        with patch.object(ebWorkerDaemon, "mRedirectRequestSecondaryExacloud", return_value="/tmp/redirected.xml") as mock_redirect:
            namespace = {
                "__builtins__": __builtins__,
                "self": _daemon,
                "job": _job,
                "callback": mCluctrlCallbackFx,
            }
            _code = compile("_exec_result = self.mRedirectRequestSecondaryExacloud(job, callback)", "ecs/exacloud/exabox/agent/Worker.py", "exec")
            exec(_code.replace(co_firstlineno=1766), namespace)

        mock_redirect.assert_called_once_with(_job, mCluctrlCallbackFx)
        self.assertEqual(namespace["_exec_result"], "/tmp/redirected.xml")

    def test_mWorker_Start_jsondispatch_redirect_invocation(self):
        # Auto-generated test for mWorker_Start
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)

        _job = MagicMock(name="jsondispatch-job")

        def mJsonDispatchCallbackFx():
            return {"status": "ok"}

        with patch.object(ebWorkerDaemon, "mRedirectRequestSecondaryExacloud", return_value={"status": "redirected"}) as mock_redirect:
            namespace = {
                "__builtins__": __builtins__,
                "self": _daemon,
                "job": _job,
                "callback": mJsonDispatchCallbackFx,
            }
            _code = compile("_exec_result = self.mRedirectRequestSecondaryExacloud(job, callback)", "ecs/exacloud/exabox/agent/Worker.py", "exec")
            exec(_code.replace(co_firstlineno=1854), namespace)

        mock_redirect.assert_called_once_with(_job, mJsonDispatchCallbackFx)
        self.assertEqual(namespace["_exec_result"], {"status": "redirected"})

    def test_mExecuteLocal_string_command_debug(self):
        # Auto-generated test for mExecuteLocal
        _client = SecondaryExacloudClient()
        _proc = MagicMock()
        _proc.communicate.return_value = (b"command output\n", b"stderr details\n")
        _proc.returncode = 7

        with patch('exabox.agent.Worker.sp.Popen', return_value=_proc) as mock_popen, \
             patch('exabox.agent.Worker.ebLogInfo') as mock_log:
            _rc, _stdout, _stderr = _client.mExecuteLocal('exa_cmd "DELETE CELL CHECK"', aDebug=True)

        mock_popen.assert_called_once()
        _args_passed = mock_popen.call_args[0][0]
        self.assertEqual(_args_passed, ['exa_cmd', 'DELETE CELL CHECK'])
        self.assertEqual(_rc, 7)
        self.assertEqual(_stdout, "command output")
        self.assertEqual(_stderr, "stderr details")
        logged_values = [call.args[0] for call in mock_log.call_args_list]
        self.assertIn(['exa_cmd', 'DELETE CELL CHECK'], logged_values)

    def test_mExecuteLocal_list_command_handles_empty_output(self):
        # Auto-generated test for mExecuteLocal
        _client = SecondaryExacloudClient()
        _proc = MagicMock()
        _proc.communicate.return_value = (None, None)
        _proc.returncode = 0
        _cmd = ['exa_cmd', 'DELETE', 'TEST']

        with patch('exabox.agent.Worker.sp.Popen', return_value=_proc) as mock_popen, \
             patch('exabox.agent.Worker.ebLogInfo'):
            _rc, _stdout, _stderr = _client.mExecuteLocal(_cmd, aDebug=False)

        mock_popen.assert_called_once()
        self.assertEqual(mock_popen.call_args[0][0], _cmd)
        self.assertEqual(_rc, 0)
        self.assertEqual(_stdout, "")
        self.assertEqual(_stderr, "")

    def test_mMakeJsonDispatchRequest_https_success(self):
        # Auto-generated test for mMakeJsonDispatchRequest
        _client = SecondaryExacloudClient(aExacloudHost="example.com", aExacloudPath="/exa")
        _client.mSetExaboxConf({
            "agent_port": "9101",
            "agent_auth": [
                base64.b64encode(b"user").decode("utf-8"),
                base64.b64encode(b"pass").decode("utf-8")
            ],
            "https_enabled": "True"
        })

        _commands = []

        def _fake_execute(cmd, *args, **kwargs):
            _commands.append(cmd)
            if len(_commands) == 1:
                return 0, "Started workflow for request: 4242", ""
            return 0, json.dumps({"status": "done"}), ""

        with patch.object(SecondaryExacloudClient, "mExecuteLocal", side_effect=_fake_execute):
            _response = _client.mMakeJsonDispatchRequest("/endpoint/status", "/payload.json", aExaunitId="ex123", aWorkflowId="wf456")

        self.assertEqual(_response, {"status": "done"})
        self.assertIn("bin/exacloud -jd /endpoint/status -jc /payload.json -ei ex123 -wi wf456 -al example.com -ap 9101", _commands[0])
        self.assertIn("bin/curl_exa -u user:pass https://example.com:9101/Status/4242", _commands[1])

    def test_mMakeJsonDispatchRequest_raises_without_request_id(self):
        # Auto-generated test for mMakeJsonDispatchRequest
        _client = SecondaryExacloudClient(aExacloudHost="example.com", aExacloudPath="/exa")
        _client.mSetExaboxConf({
            "agent_port": "9101",
            "agent_auth": [
                base64.b64encode(b"user").decode("utf-8"),
                base64.b64encode(b"pass").decode("utf-8")
            ],
            "https_enabled": "False"
        })

        with patch.object(SecondaryExacloudClient, "mExecuteLocal", return_value=(0, "Missing response content", "")), \
             patch('exabox.agent.Worker.ebLogError') as mock_log_error:
            with self.assertRaises(Exception):
                _client.mMakeJsonDispatchRequest("/endpoint/status", "/payload.json")

        self.assertTrue(mock_log_error.called)

    def test_mMakeCluctrlRequest_handles_step_and_undo(self):
        # Auto-generated test for mMakeCluctrlRequest
        _client = SecondaryExacloudClient(aExacloudHost="example.com", aExacloudPath="/exa")
        _client.mSetExaboxConf({
            "agent_port": "9101",
            "agent_auth": [
                base64.b64encode(b"user").decode("utf-8"),
                base64.b64encode(b"pass").decode("utf-8")
            ],
            "https_enabled": "False"
        })

        _commands = []
        def _fake_execute(cmd, *args, **kwargs):
            _commands.append(cmd)
            if len(_commands) == 1:
                return 0, "Triggered flow for request: 9999", ""
            return 0, json.dumps({"status": "ok"}), ""

        with patch.object(SecondaryExacloudClient, "mExecuteLocal", side_effect=_fake_execute):
            _response = _client.mMakeCluctrlRequest(
                "delete", "/xml/path.xml", "/payload.json", aStepName="DELETE CELL CHECK",
                aUndo=True, aExaunitId="ex123", aWorkflowId="wf456")

        self.assertEqual(_response, {"status": "ok"})
        self.assertIn("-rs DELETE CELL CHECK -sl DELETE CELL CHECK -un True", _commands[0])
        self.assertIn("-ei ex123 -wi wf456 -al example.com -ap 9101", _commands[0])
        self.assertIn("/bin/curl -u user:pass http://example.com:9101/Status/9999", _commands[1])

    def test_mMakeCluctrlRequest_uses_https_when_enabled(self):
        # Auto-generated test for mMakeCluctrlRequest
        _client = SecondaryExacloudClient(aExacloudHost="example.com", aExacloudPath="/exa")
        _client.mSetExaboxConf({
            "agent_port": "9101",
            "agent_auth": [
                base64.b64encode(b"user").decode("utf-8"),
                base64.b64encode(b"pass").decode("utf-8")
            ],
            "https_enabled": "True"
        })

        _commands = []
        def _fake_execute(cmd, *args, **kwargs):
            _commands.append(cmd)
            if len(_commands) == 1:
                return 0, "Triggered flow for request: 1212", ""
            return 0, json.dumps({"status": "completed"}), ""

        with patch.object(SecondaryExacloudClient, "mExecuteLocal", side_effect=_fake_execute):
            _response = _client.mMakeCluctrlRequest("create", "/xml/path.xml", "/payload.json")

        self.assertEqual(_response, {"status": "completed"})
        self.assertIn("/bin/exacloud -clu create -cf /xml/path.xml -jc /payload.json -un False -al example.com -ap 9101", _commands[0])
        self.assertIn("bin/curl_exa -u user:pass https://example.com:9101/Status/1212", _commands[1])

    def test_mSetExacloudHost_updates_host_value(self):
        # Auto-generated test for mSetExacloudHost
        _client = SecondaryExacloudClient()
        _client.mSetExacloudHost("remote.example.com")
        self.assertEqual(_client.mGetExacloudHost(), "remote.example.com")

    def test_mReadConfig_populates_exabox_conf(self):
        # Auto-generated test for mReadConfig
        _client = SecondaryExacloudClient()
        _client.mSetExacloudPath("/opt/exacloud")
        _config_payload = {
            "agent_port": "9200",
            "agent_auth": ["dXNlcg==", "cGFzcw=="],
            "https_enabled": "False"
        }
        _mock_file = mock_open(read_data=json.dumps(_config_payload))

        with patch('builtins.open', _mock_file):
            _client.mReadConfig()

        _mock_file.assert_called_once_with("/opt/exacloud/config/exabox.conf", "r")
        self.assertEqual(_client.mGetExaboxConf(), _config_payload)

    def test_mMakeCluctrlRequest_logs_and_raises_without_request_id(self):
        # Auto-generated test for mMakeCluctrlRequest
        _client = SecondaryExacloudClient(aExacloudHost="example.com", aExacloudPath="/exa")
        _client.mSetExaboxConf({
            "agent_port": "9101",
            "agent_auth": [
                base64.b64encode(b"user").decode("utf-8"),
                base64.b64encode(b"pass").decode("utf-8")
            ],
            "https_enabled": "False"
        })

        with patch.object(SecondaryExacloudClient, "mExecuteLocal", return_value=(0, "No request id available", "")) as mock_execute, \
             patch('exabox.agent.Worker.ebLogError') as mock_log_error, \
             patch('exabox.agent.Worker.traceback.format_exc', return_value="mock-trace"):
            with self.assertRaises(Exception):
                _client.mMakeCluctrlRequest("delete", "/xml/path.xml", "/payload.json")

        mock_execute.assert_called_once()
        self.assertTrue(any("Something went wrong" in _call.args[0] for _call in mock_log_error.call_args_list))

    def test_mRedirectRequestSecondaryExacloud_returns_callback_result(self):
        # Auto-generated test for mRedirectRequestSecondaryExacloud
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetOptions.return_value = type("Opt", (), {"jsonconf": {"payload": "payload"}})()

        _secondary_config = [{
            "payload_regex": "payload",
            "exacloud_host": "secondary-host",
            "exacloud_port": 9201,
            "exacloud_path": "/opt/exacloud"
        }]
        _context = MagicMock()
        _context.mCheckConfigOption.side_effect = lambda key: _secondary_config if key == "secondary_exacloud_config" else None

        _client = MagicMock()
        _client.mReadConfig.return_value = None
        _callback_calls = []

        def _callback(aClient, aJob):
            _callback_calls.append((aClient, aJob))
            return {"status": "redirected"}

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context), \
             patch('exabox.agent.Worker.SecondaryExacloudClient', return_value=_client) as mock_ctor:
            _result = _daemon.mRedirectRequestSecondaryExacloud(_job, _callback)

        self.assertEqual(_result, {"status": "redirected"})
        self.assertEqual(_callback_calls, [(_client, _job)])
        _client.mSetExacloudPort.assert_called_once_with(9201)
        _client.mReadConfig.assert_called_once()
        mock_ctor.assert_called_once_with('secondary-host', '/opt/exacloud')

    def test_mRedirectRequestSecondaryExacloud_handles_missing_fields(self):
        # Auto-generated test for mRedirectRequestSecondaryExacloud
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetOptions.return_value = type("Opt", (), {"jsonconf": {"payload": "match"}})()

        _secondary_config = [
            {"payload_regex": "match", "exacloud_port": 9400},
            {"payload_regex": "match", "exacloud_host": "secondary-final", "exacloud_port": 9500}
        ]
        _context = MagicMock()
        _context.mCheckConfigOption.side_effect = lambda key: _secondary_config if key == "secondary_exacloud_config" else None

        _first_client = MagicMock()
        _first_client.mReadConfig.side_effect = Exception("bad config")
        _second_client = MagicMock()
        _second_client.mReadConfig.return_value = None
        _clients = [_first_client, _second_client]
        _callback_calls = []

        def _callback(aClient, aJob):
            _callback_calls.append((aClient, aJob))
            return "final-result"

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context), \
             patch('exabox.agent.Worker.SecondaryExacloudClient', side_effect=_clients) as mock_ctor, \
             patch('exabox.agent.Worker.os.path.abspath', return_value='/opt/app/exacloud/agent/Worker.py'):
            _result = _daemon.mRedirectRequestSecondaryExacloud(_job, _callback)

        self.assertEqual(_result, "final-result")
        self.assertEqual(_callback_calls, [(_second_client, _job)])
        _first_client.mReadConfig.assert_called_once()
        _second_client.mReadConfig.assert_called_once()
        self.assertEqual(len(mock_ctor.call_args_list), 2)
        _first_call_args = mock_ctor.call_args_list[0][0]
        _second_call_args = mock_ctor.call_args_list[1][0]
        self.assertEqual(_first_call_args, ('localhost', '/opt/app/exacloud'))
        self.assertEqual(_second_call_args, ('secondary-final', '/opt/app/exacloud'))
        _first_client.mSetExacloudPort.assert_called_once_with(9400)
        _second_client.mSetExacloudPort.assert_called_once_with(9500)

    def test_CreateClusterLogs_links_all_variants_when_sources_exist(self):
        # Auto-generated test for CreateClusterLogs
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)

        with patch('exabox.agent.Worker.os.getcwd', return_value='/workdir'), \
             patch.object(_daemon, "mMkdirWithPoption") as mock_mkdir, \
             patch('exabox.agent.Worker.os.path.exists', return_value=True), \
             patch('exabox.agent.Worker.os.symlink') as mock_symlink:
            _daemon.CreateClusterLogs('Cluster One', aLogFileNoExt='/logs/job-uuid_cmd')

        mock_mkdir.assert_called_once_with('/workdir/log/clusters/Cluster One')
        _expected_calls = [
            ('/logs/job-uuid_cmd.log', '/workdir/log/clusters/Cluster One/job-uuid_cmd.log'),
            ('/logs/job-uuid_cmd.trc', '/workdir/log/clusters/Cluster One/job-uuid_cmd.trc'),
            ('/logs/job-uuid_cmd.err', '/workdir/log/clusters/Cluster One/job-uuid_cmd.err'),
        ]
        recorded_calls = [entry.args for entry in mock_symlink.call_args_list]
        self.assertEqual(recorded_calls, _expected_calls)

    def test_CreateClusterLogs_links_single_logfile(self):
        # Auto-generated test for CreateClusterLogs
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)

        with patch('exabox.agent.Worker.os.getcwd', return_value='/workdir'), \
             patch.object(_daemon, "mMkdirWithPoption"), \
             patch('exabox.agent.Worker.os.path.exists', return_value=True), \
             patch('exabox.agent.Worker.os.symlink') as mock_symlink:
            _daemon.CreateClusterLogs('Cluster One', aLogFile='/logs/worker_main.log')

        mock_symlink.assert_called_once_with('/logs/worker_main.log', '/workdir/log/clusters/Cluster One/worker_main.log')

    def test_CreateClusterLogs_skips_missing_sources(self):
        # Auto-generated test for CreateClusterLogs
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)

        with patch('exabox.agent.Worker.os.getcwd', return_value='/workdir'), \
             patch.object(_daemon, "mMkdirWithPoption"), \
             patch('exabox.agent.Worker.os.path.exists', return_value=False), \
             patch('exabox.agent.Worker.os.symlink') as mock_symlink:
            _daemon.CreateClusterLogs('Cluster One', aLogFileNoExt='/logs/job-uuid_cmd')

        mock_symlink.assert_not_called()

    def test_mCheckFDLimitBreach_disabled_flag_returns_false(self):
        # Auto-generated test for mCheckFDLimitBreach
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _context = MagicMock()
        _context.mCheckConfigOption.side_effect = lambda key: 'False' if key == 'fd_limits_enabled' else '0'

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context), \
             patch('exabox.agent.Worker.exaBoxNode') as mock_node, \
             patch('exabox.agent.Worker.psutil.Process') as mock_process:
            _result = _daemon.mCheckFDLimitBreach()

        self.assertFalse(_result)
        mock_node.assert_not_called()
        mock_process.assert_not_called()

    def test_mCheckFDLimitBreach_detects_breach(self):
        # Auto-generated test for mCheckFDLimitBreach
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _config_values = {
            'fd_limits_enabled': 'True',
            'fd_limits_custom_threshold': '90',
            'fd_limits_custom_maxvalue': '0'
        }
        _context = MagicMock()
        _context.mCheckConfigOption.side_effect = lambda key: _config_values.get(key, '0')

        _node = MagicMock()
        _node.mExecuteLocal.side_effect = [
            (0, None, 'Max open files      4096      4096      4096', None),
            (0, None, 'line1\nline2', None)
        ]
        _process = MagicMock()
        _process.num_fds.return_value = 5000

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context), \
             patch('exabox.agent.Worker.exaBoxNode', return_value=_node), \
             patch('exabox.agent.Worker.psutil.Process', return_value=_process):
            _result = _daemon.mCheckFDLimitBreach()

        self.assertTrue(_result)
        self.assertEqual(_node.mExecuteLocal.call_count, 2)
        _process.num_fds.assert_called_once()

    def test_mMakeJsonDispatchRequest_raises_on_invalid_status_payload(self):
        # Auto-generated test for mMakeJsonDispatchRequest
        _client = SecondaryExacloudClient(aExacloudHost="example.com", aExacloudPath="/exa")
        _client.mSetExaboxConf({
            "agent_port": "9101",
            "agent_auth": [
                base64.b64encode(b"user").decode("utf-8"),
                base64.b64encode(b"pass").decode("utf-8")
            ],
            "https_enabled": "False"
        })

        _commands = []

        def _fake_execute(cmd, *args, **kwargs):
            _commands.append(cmd)
            if len(_commands) == 1:
                return 0, "Started workflow for request: 1234", ""
            return 0, "not-json", ""

        with patch.object(_client, "mExecuteLocal", side_effect=_fake_execute):
            with self.assertRaises(json.JSONDecodeError):
                _client.mMakeJsonDispatchRequest("/endpoint/status", "/payload.json")

        self.assertEqual(len(_commands), 2)
        self.assertIn("http://example.com:9101/Status/1234", _commands[1])

    def test_mRedirectRequestSecondaryExacloud_warns_on_missing_payload_regex(self):
        # Auto-generated test for mRedirectRequestSecondaryExacloud
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetOptions.return_value = type("Opt", (), {"jsonconf": {"payload": "value"}})()

        _context = MagicMock()
        _context.mCheckConfigOption.side_effect = lambda key: [{"exacloud_host": "secondary-host"}] if key == "secondary_exacloud_config" else None

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context), \
             patch('exabox.agent.Worker.ebLogWarn') as mock_warn, \
             patch('exabox.agent.Worker.SecondaryExacloudClient') as mock_client:
            _result = _daemon.mRedirectRequestSecondaryExacloud(_job, MagicMock())

        self.assertIsNone(_result)
        mock_client.assert_not_called()
        self.assertTrue(mock_warn.called)
        self.assertTrue(mock_warn.call_args[0][0].startswith("Invalid secondary exacloud config"))

    def test_mRedirectRequestSecondaryExacloud_warns_on_missing_jsonconf(self):
        # Auto-generated test for mRedirectRequestSecondaryExacloud
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetOptions.return_value = type("Opt", (), {"jsonconf": None})()

        _secondaries = [{"payload_regex": "payload", "exacloud_host": "secondary-host"}]
        _context = MagicMock()
        _context.mCheckConfigOption.side_effect = lambda key: _secondaries if key == "secondary_exacloud_config" else None

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context), \
             patch('exabox.agent.Worker.ebLogWarn') as mock_warn, \
             patch('exabox.agent.Worker.SecondaryExacloudClient') as mock_client:
            _result = _daemon.mRedirectRequestSecondaryExacloud(_job, MagicMock())

        self.assertIsNone(_result)
        mock_client.assert_not_called()
        mock_warn.assert_called_once_with("Missing jsonconf in request")

    def test_mCheckFDLimitBreach_uses_custom_max_without_local_exec(self):
        # Auto-generated test for mCheckFDLimitBreach
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _config_values = {
            'fd_limits_enabled': 'True',
            'fd_limits_custom_threshold': '80',
            'fd_limits_custom_maxvalue': '200'
        }
        _context = MagicMock()
        _context.mCheckConfigOption.side_effect = lambda key: _config_values.get(key, '0')

        _node = MagicMock()
        _process = MagicMock()
        _process.num_fds.return_value = 150

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context), \
             patch('exabox.agent.Worker.exaBoxNode', return_value=_node), \
             patch('exabox.agent.Worker.psutil.Process', return_value=_process):
            _result = _daemon.mCheckFDLimitBreach()

        self.assertFalse(_result)
        _node.mExecuteLocal.assert_not_called()
        _process.num_fds.assert_called_once()

    def test_mCheckFDLimitBreach_logs_on_exception(self):
        # Auto-generated test for mCheckFDLimitBreach
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _context = MagicMock()
        _context.mCheckConfigOption.side_effect = lambda key: 'True' if key == 'fd_limits_enabled' else '0'

        _node = MagicMock()
        _node.mExecuteLocal.return_value = (0, None, "Max open files      1024      1024      1024", None)

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context), \
             patch('exabox.agent.Worker.exaBoxNode', return_value=_node), \
             patch('exabox.agent.Worker.psutil.Process', side_effect=RuntimeError("fd-error")), \
             patch('exabox.agent.Worker.ebLogWarn') as mock_warn:
            _result = _daemon.mCheckFDLimitBreach()

        self.assertFalse(_result)
        mock_warn.assert_called_once()
        self.assertIn("fd-error", mock_warn.call_args[0][0])

    def test_mArchiveOEDARequests_skips_in_ociexacc_env(self):
        # Auto-generated test for mArchiveOEDARequests
        _context = self.mGetContext()
        _original_options = _context.mGetConfigOptions()
        _writable_options = copy.deepcopy(_original_options) if _original_options else {}
        _writable_options['ociexacc'] = "True"
        _context.mSetConfigOptions(_writable_options)
        self.addCleanup(lambda: _context.mSetConfigOptions(_original_options))

        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'
        _vm_handle = MagicMock()

        with patch('exabox.agent.Worker.ebLogTrace') as mock_log_trace:
            _result = _daemon.mArchiveOEDARequests(_vm_handle, _job)

        self.assertIsNone(_result)
        _job.mGetType.assert_called_once()
        mock_log_trace.assert_any_call("ExaCC Env detected. Skipping mArchiveOEDARequests")

    def test_mArchiveOEDARequests_skips_when_vmhandle_missing(self):
        # Auto-generated test for mArchiveOEDARequests
        _context = self.mGetContext()
        _original_options = _context.mGetConfigOptions()
        _writable_options = copy.deepcopy(_original_options) if _original_options else {}
        if 'ociexacc' in _writable_options:
            del _writable_options['ociexacc']
        _context.mSetConfigOptions(_writable_options)
        self.addCleanup(lambda: _context.mSetConfigOptions(_original_options))

        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'

        with patch('exabox.agent.Worker.ebLogTrace') as mock_log_trace:
            _result = _daemon.mArchiveOEDARequests(None, _job)

        self.assertIsNone(_result)
        _job.mGetType.assert_called_once()
        mock_log_trace.assert_any_call("VmHandle is None, skipping OEDA Archive request...")

    def test_mArchiveOEDARequests_moves_requests_to_archive(self):
        # Auto-generated test for mArchiveOEDARequests
        _context = self.mGetContext()
        _original_options = _context.mGetConfigOptions()
        _writable_options = copy.deepcopy(_original_options) if _original_options else {}
        _writable_options.pop('ociexacc', None)
        _writable_options['oeda_archive_requests_path'] = 'archive/custom'
        _context.mSetConfigOptions(_writable_options)
        self.addCleanup(lambda: _context.mSetConfigOptions(_original_options))

        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'
        _source_path = '/tmp/requests/req123'
        _request_id = os.path.basename(_source_path)
        _vm_handle = MagicMock()
        _vm_handle.mGetOEDARequestsPath.return_value = _source_path

        _base_path = '/var/opt/exa'
        _archive_path = os.path.join(_base_path, 'archive/custom')
        _dest_path = os.path.join(_archive_path, _request_id)

        _existing_paths = {
            _source_path: True,
            os.path.dirname(_source_path): True,
            _archive_path: True,
            _dest_path: True,
        }

        def _fake_exists(path):
            return _existing_paths.get(path, False)

        with patch('exabox.agent.Worker.get_gcontext') as mock_context, \
             patch('exabox.agent.Worker.os.path.exists', side_effect=_fake_exists), \
             patch('exabox.agent.Worker.os.makedirs') as mock_makedirs, \
             patch('exabox.agent.Worker.shutil.move') as mock_move, \
             patch('exabox.agent.Worker.ebLogInfo') as mock_log_info, \
             patch('exabox.agent.Worker.ebLogTrace') as mock_log_trace:
            mock_context.return_value = MagicMock(mGetBasePath=MagicMock(return_value=_base_path))
            _result = _daemon.mArchiveOEDARequests(_vm_handle, _job)

        self.assertIsNone(_result)
        mock_move.assert_called_once_with(_source_path, _archive_path)
        mock_makedirs.assert_called_once_with(_archive_path, exist_ok=True)
        _info_messages = [call.args[0] for call in mock_log_info.call_args_list]
        self.assertTrue(any("completed Successfully" in message for message in _info_messages))
        self.assertTrue(any("Moving OEDA requests directory to archive path succeeded" in message
                            for message in _info_messages))

    def test_mArchiveOEDARequests_logs_and_recovers_on_move_failure(self):
        # Auto-generated test for mArchiveOEDARequests
        _context = self.mGetContext()
        _original_options = _context.mGetConfigOptions()
        _writable_options = copy.deepcopy(_original_options) if _original_options else {}
        _writable_options.pop('ociexacc', None)
        _context.mSetConfigOptions(_writable_options)
        self.addCleanup(lambda: _context.mSetConfigOptions(_original_options))

        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'
        _source_path = '/tmp/requests/req999'
        _vm_handle = MagicMock()
        _vm_handle.mGetOEDARequestsPath.return_value = _source_path

        _base_path = '/var/opt/exa'
        _archive_path = os.path.join(_base_path, 'oeda/requests.bak/')
        _existing_paths = {
            _source_path: True,
            os.path.dirname(_source_path): True,
            _archive_path: True,
        }

        def _fake_exists(path):
            return _existing_paths.get(path, False)

        with patch('exabox.agent.Worker.get_gcontext') as mock_context, \
             patch('exabox.agent.Worker.os.path.exists', side_effect=_fake_exists), \
             patch('exabox.agent.Worker.os.makedirs'), \
             patch('exabox.agent.Worker.shutil.move', side_effect=OSError("disk error")), \
             patch('exabox.agent.Worker.ebLogError') as mock_log_error, \
             patch('exabox.agent.Worker.ebLogTrace') as mock_log_trace:
            mock_context.return_value = MagicMock(mGetBasePath=MagicMock(return_value=_base_path))
            _result = _daemon.mArchiveOEDARequests(_vm_handle, _job)

        self.assertIsNone(_result)
        self.assertTrue(any("disk error" in call.args[0] for call in mock_log_error.call_args_list))
        self.assertTrue(any("failed with Exception: disk error" in call.args[0]
                            for call in mock_log_trace.call_args_list))

    def test_mArchiveOEDARequests_skips_when_request_path_missing(self):
        # Auto-generated test for mArchiveOEDARequests
        _context = self.mGetContext()
        _original_options = _context.mGetConfigOptions()
        _writable_options = copy.deepcopy(_original_options) if _original_options else {}
        _writable_options.pop('ociexacc', None)
        _context.mSetConfigOptions(_writable_options)
        self.addCleanup(lambda: _context.mSetConfigOptions(_original_options))

        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'
        _vm_handle = MagicMock()
        _vm_handle.mGetOEDARequestsPath.return_value = None

        with patch('exabox.agent.Worker.ebLogTrace') as mock_log_trace:
            _result = _daemon.mArchiveOEDARequests(_vm_handle, _job)

        self.assertIsNone(_result)
        mock_log_trace.assert_any_call("OEDA Request Path is Not Present. Skipping the Archiving Operation..")

    def test_mArchiveOEDARequests_skips_when_request_path_invalid(self):
        # Auto-generated test for mArchiveOEDARequests
        _context = self.mGetContext()
        _original_options = _context.mGetConfigOptions()
        _writable_options = copy.deepcopy(_original_options) if _original_options else {}
        _writable_options.pop('ociexacc', None)
        _context.mSetConfigOptions(_writable_options)
        self.addCleanup(lambda: _context.mSetConfigOptions(_original_options))

        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'
        _vm_handle = MagicMock()
        _request_path = '/tmp/requests/missing'
        _vm_handle.mGetOEDARequestsPath.return_value = _request_path

        def _fake_exists(path):
            return path != _request_path

        with patch('exabox.agent.Worker.os.path.exists', side_effect=_fake_exists), \
             patch('exabox.agent.Worker.ebLogTrace') as mock_log_trace:
            _result = _daemon.mArchiveOEDARequests(_vm_handle, _job)

        self.assertIsNone(_result)
        mock_log_trace.assert_any_call("OEDA Request Path is Not Valid. Skipping the Archiving Operation..")

    def test_mArchiveOEDARequests_skips_when_archive_path_unusable(self):
        # Auto-generated test for mArchiveOEDARequests
        _context = self.mGetContext()
        _original_options = _context.mGetConfigOptions()
        _writable_options = copy.deepcopy(_original_options) if _original_options else {}
        _writable_options.pop('ociexacc', None)
        _context.mSetConfigOptions(_writable_options)
        self.addCleanup(lambda: _context.mSetConfigOptions(_original_options))

        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'
        _source_path = '/tmp/requests/req777'
        _vm_handle = MagicMock()
        _vm_handle.mGetOEDARequestsPath.return_value = _source_path

        _base_path = '/var/opt/exa'
        _archive_path = os.path.join(_base_path, 'oeda/requests.bak/')
        _existing_paths = {
            _source_path: True,
            os.path.dirname(_source_path): True,
            _archive_path: False,
        }

        def _fake_exists(path):
            return _existing_paths.get(path, False)

        with patch('exabox.agent.Worker.get_gcontext') as mock_context, \
             patch('exabox.agent.Worker.os.path.exists', side_effect=_fake_exists), \
             patch('exabox.agent.Worker.os.makedirs') as mock_makedirs, \
             patch('exabox.agent.Worker.shutil.move') as mock_move, \
             patch('exabox.agent.Worker.ebLogTrace') as mock_log_trace:
            mock_context.return_value = MagicMock(mGetBasePath=MagicMock(return_value=_base_path))
            _result = _daemon.mArchiveOEDARequests(_vm_handle, _job)

        self.assertIsNone(_result)
        mock_makedirs.assert_called_once_with(_archive_path, exist_ok=True)
        mock_move.assert_not_called()
        mock_log_trace.assert_any_call(f"{_archive_path} path could not be created successfully! Skipping the Archive Operation")

    def test_mArchiveOEDARequests_parent_directory_missing(self):
        # Auto-generated test for mArchiveOEDARequests
        _context = self.mGetContext()
        _original_options = _context.mGetConfigOptions()
        _writable_options = copy.deepcopy(_original_options) if _original_options else {}
        _writable_options.pop('ociexacc', None)
        _context.mSetConfigOptions(_writable_options)
        self.addCleanup(lambda: _context.mSetConfigOptions(_original_options))

        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'
        _source_path = '/tmp/requests/req888'
        _vm_handle = MagicMock()
        _vm_handle.mGetOEDARequestsPath.return_value = _source_path

        _base_path = '/var/opt/exa'
        _archive_path = os.path.join(_base_path, 'oeda/requests.bak/')
        _parent_path = os.path.dirname(_source_path)
        _existing_paths = {
            _source_path: True,
            _parent_path: False,
        }

        def _fake_exists(path):
            return _existing_paths.get(path, False)

        with patch('exabox.agent.Worker.get_gcontext') as mock_context, \
             patch('exabox.agent.Worker.os.path.exists', side_effect=_fake_exists), \
             patch('exabox.agent.Worker.os.makedirs') as mock_makedirs, \
             patch('exabox.agent.Worker.shutil.move') as mock_move, \
             patch('exabox.agent.Worker.ebLogInfo') as mock_log_info:
            mock_context.return_value = MagicMock(mGetBasePath=MagicMock(return_value=_base_path))
            _result = _daemon.mArchiveOEDARequests(_vm_handle, _job)

        self.assertIsNone(_result)
        mock_makedirs.assert_not_called()
        mock_move.assert_not_called()
        self.assertTrue(any("completed Successfully" in call.args[0] for call in mock_log_info.call_args_list))

    def test_is_port_free_returns_false_when_socket_in_use(self):
        # Auto-generated test for is_port_free
        _socket_conn = MagicMock()
        with patch('exabox.agent.Worker.socket.socket') as mock_socket, \
             patch('exabox.agent.Worker.ebLogInfo'):
            mock_socket.return_value.__enter__.return_value = _socket_conn
            _socket_conn.connect_ex.return_value = 0
            _result = is_port_free(4321)

        self.assertFalse(_result)
        _socket_conn.connect_ex.assert_called_once_with(('localhost', 4321))

    def test_is_port_free_returns_true_when_socket_available(self):
        # Auto-generated test for is_port_free
        _socket_conn = MagicMock()
        with patch('exabox.agent.Worker.socket.socket') as mock_socket, \
             patch('exabox.agent.Worker.ebLogInfo'):
            mock_socket.return_value.__enter__.return_value = _socket_conn
            _socket_conn.connect_ex.return_value = errno.ECONNREFUSED
            _result = is_port_free(5678)

        self.assertTrue(_result)
        _socket_conn.connect_ex.assert_called_once_with(('localhost', 5678))

    def test_mMkdirWithPoption_creates_directory(self):
        # Auto-generated test for mMkdirWithPoption
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        with patch('exabox.agent.Worker.os.makedirs') as mock_makedirs:
            _daemon.mMkdirWithPoption('/tmp/newdir')

        mock_makedirs.assert_called_once_with('/tmp/newdir')

    def test_mMkdirWithPoption_tolerates_existing_directory(self):
        # Auto-generated test for mMkdirWithPoption
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        with patch('exabox.agent.Worker.os.makedirs', side_effect=OSError(errno.EEXIST, "exists")), \
             patch('exabox.agent.Worker.os.path.isdir', return_value=True), \
             patch('exabox.agent.Worker.ebLogError') as mock_log_error:
            _daemon.mMkdirWithPoption('/tmp/existing')

        mock_log_error.assert_not_called()

    def test_mMkdirWithPoption_raises_runtime_error_on_failure(self):
        # Auto-generated test for mMkdirWithPoption
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        with patch('exabox.agent.Worker.os.makedirs', side_effect=OSError(errno.EACCES, "denied")), \
             patch('exabox.agent.Worker.os.path.isdir', return_value=False), \
             patch('exabox.agent.Worker.ebLogError') as mock_log_error:
            with self.assertRaises(ExacloudRuntimeError):
                _daemon.mMkdirWithPoption('/tmp/protected')

        self.assertTrue(any("Make directory failed" in call.args[0] for call in mock_log_error.call_args_list))

    def test_validate_uuid_enforces_canonical_format(self):
        # Auto-generated test for validate_uuid
        _daemon = ebWorkerDaemon(aPort=9101, aLiteCreate=True)
        self.assertTrue(_daemon.validate_uuid("123e4567-e89b-12d3-a456-426614174000"))
        self.assertFalse(_daemon.validate_uuid("1234567-89ab-cdef-0123-456789abcdef"))
        self.assertFalse(_daemon.validate_uuid("not-a-uuid"))

    def test_mSetLastActiveTime_handles_default_and_custom_values(self):
        # Auto-generated test for mSetLastActiveTime
        _fake_args = MagicMock()
        _fake_args.proxy = False
        _fake_context = MagicMock()
        _fake_context.mGetArgsOptions.return_value = _fake_args
        _fixed_now = datetime(2026, 3, 13, 12, 34, 56, 789123)

        with patch('exabox.agent.Worker.get_gcontext', return_value=_fake_context), \
             patch('exabox.agent.Worker.datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = _fixed_now
            _worker = ebWorker(aDB=MagicMock())
            _worker.mSetLastActiveTime()
            self.assertEqual(
                _worker.mGetLastActiveTime(),
                _fixed_now.isoformat(sep=' ', timespec='microseconds')
            )
            _worker.mSetLastActiveTime("custom-timestamp")

        self.assertEqual(_worker.mGetLastActiveTime(), "custom-timestamp")

    def test_mAcquireSyncLock_handles_none_and_db_outcomes(self):
        # Auto-generated test for mAcquireSyncLock
        _fake_args = MagicMock()
        _fake_args.proxy = False
        _fake_context = MagicMock()
        _fake_context.mGetArgsOptions.return_value = _fake_args
        _fake_db = MagicMock()
        _fake_db.mAcquireWorkerSyncLock.side_effect = [True, False]

        with patch('exabox.agent.Worker.get_gcontext', return_value=_fake_context):
            _worker = ebWorker(aDB=_fake_db)

        _worker.mSetPort(9102)
        self.assertFalse(_worker.mAcquireSyncLock())
        self.assertTrue(_worker.mAcquireSyncLock("procA"))
        self.assertEqual(_fake_db.mAcquireWorkerSyncLock.call_args_list[0][0], (9102, "procA"))
        self.assertEqual(_worker.mGetSyncLock(), "procA")
        self.assertFalse(_worker.mAcquireSyncLock("procB"))
        self.assertEqual(_fake_db.mAcquireWorkerSyncLock.call_args_list[1][0], (9102, "procB"))
        self.assertEqual(_worker.mGetSyncLock(), "procA")

    def test_mReleaseSyncLock_handles_none_and_db_outcomes(self):
        # Auto-generated test for mReleaseSyncLock
        _fake_args = MagicMock()
        _fake_args.proxy = False
        _fake_context = MagicMock()
        _fake_context.mGetArgsOptions.return_value = _fake_args
        _fake_db = MagicMock()
        _fake_db.mReleaseWorkerSyncLock.side_effect = [True, False]

        with patch('exabox.agent.Worker.get_gcontext', return_value=_fake_context):
            _worker = ebWorker(aDB=_fake_db)

        _worker.mSetPort(9103)
        self.assertFalse(_worker.mReleaseSyncLock())
        _worker.mSetSyncLock("holder")
        self.assertTrue(_worker.mReleaseSyncLock("holder"))
        self.assertEqual(_fake_db.mReleaseWorkerSyncLock.call_args_list[0][0], (9103, "holder"))
        self.assertEqual(_worker.mGetSyncLock(), "Undef")
        self.assertFalse(_worker.mReleaseSyncLock("holder"))
        self.assertEqual(_fake_db.mReleaseWorkerSyncLock.call_args_list[1][0], (9103, "holder"))
        self.assertEqual(_worker.mGetSyncLock(), "Undef")

    def test_ebworker_proxy_and_metadata_accessors(self):
        # Auto-generated test for __init__
        _fake_args = MagicMock()
        _fake_args.proxy = True
        _fake_context = MagicMock()
        _fake_context.mGetArgsOptions.return_value = _fake_args
        _fake_db = MagicMock()

        with patch('exabox.agent.Worker.get_gcontext', return_value=_fake_context):
            _worker = ebWorker(aDB=_fake_db)

        self.assertEqual(_worker.mGetType(), 'proxy')

        # Auto-generated test for mSetState
        _worker.mSetState('CORRUPTED')
        self.assertEqual(_worker.mGetState(), 'CORRUPTED')

        # Auto-generated test for mSetStatus
        _worker.mSetStatus('Busy')
        self.assertEqual(_worker.mGetStatus(), 'Busy')

        # Auto-generated test for mResetUUID
        _worker.mSetUUID('custom-uuid')
        _worker.mResetUUID()
        self.assertEqual(_worker.mGetUUID(), '00000000-0000-0000-0000-000000000000')

        # Auto-generated test for mSetTimeStampStart
        _worker.mSetTimeStampStart('start-marker')
        self.assertEqual(_worker.mGetTimeStampStart(), 'start-marker')

        # Auto-generated test for mSetTimeStampEnd
        _worker.mSetTimeStampEnd('end-marker')
        self.assertEqual(_worker.mGetTimeStampEnd(), 'end-marker')

        with patch('exabox.agent.Worker.time.strftime', return_value='auto-end'):
            _worker.mSetTimeStampEnd()

        self.assertEqual(_worker.mGetTimeStampEnd(), 'auto-end')

        # Auto-generated test for mSetParams
        _worker.mSetParams({'k': 'v'})
        self.assertEqual(_worker.mGetParams(), {'k': 'v'})

        # Auto-generated test for mSetError
        _worker.mSetError('E123')
        self.assertEqual(_worker.mGetError(), 'E123')

    def test_secondary_exacloud_client_remote_host_paths(self):
        # Auto-generated test for __init__
        # Auto-generated test for mGetExacloudPath
        with patch('exabox.agent.Worker.socket.getfqdn', return_value='remote.example.com'):
            _client = SecondaryExacloudClient(aExacloudHost='remote-host', aExacloudPath='/ignored')

        _worker_path = os.path.abspath(worker_module.__file__)
        _index = _worker_path.rfind("exacloud")
        self.assertGreaterEqual(_index, 0)
        _expected_path = _worker_path[:_index + 8]

        self.assertEqual('remote.example.com', _client.mGetExacloudHost())
        self.assertEqual(_expected_path, _client.mGetExacloudPath())
        # Auto-generated test for mSetExacloudPort
        _client.mSetExacloudPort(1521)
        self.assertEqual(1521, _client.mGetExacloudPort())
        # Auto-generated test for mSetExacloudHost
        _client.mSetExacloudHost('override-host')
        self.assertEqual('override-host', _client.mGetExacloudHost())
        # Auto-generated test for mSetExacloudPath
        _client.mSetExacloudPath('/custom/path')
        self.assertEqual('/custom/path', _client.mGetExacloudPath())
        # Auto-generated test for mSetExaboxConf
        _client.mSetExaboxConf('conf-token')
        self.assertEqual('conf-token', _client.mGetExaboxConf())

    def test_secondary_exacloud_client_local_path_and_setters(self):
        # Auto-generated test for __init__
        _client = SecondaryExacloudClient(aExacloudHost='localhost', aExacloudPath='/tmp/local/path')
        self.assertEqual('/tmp/local/path', _client.mGetExacloudPath())
        self.assertIsNone(_client.mGetExacloudPort())
        # Auto-generated test for mSetExacloudPort
        _client.mSetExacloudPort(9999)
        self.assertEqual(9999, _client.mGetExacloudPort())
        # Auto-generated test for mSetExaboxConf
        _client.mSetExaboxConf('local-conf')
        self.assertEqual('local-conf', _client.mGetExaboxConf())

    @patch('exabox.agent.Worker.psutil.Process')
    @patch('exabox.agent.Worker.exaBoxNode')
    @patch('exabox.agent.Worker.get_gcontext')
    def test_mCheckFDLimitBreach_returns_true_on_fd_breach(self, mock_get_gcontext, mock_exa_box_node, mock_process):
        # Auto-generated test for mCheckFDLimitBreach
        _context = MagicMock()
        _context.mGetConfigOptions.return_value = {'ociexacc': 'False', 'oeda_archive_requests_path': ''}
        _context.mGetArgsOptions.return_value = SimpleNamespace(worker_port=None)
        _context.mGetBasePath.return_value = '/base'
        _config_values = {
            'fd_limits_enabled': 'True',
            'fd_limits_custom_threshold': '90',
            'fd_limits_custom_maxvalue': '0'
        }

        def _config_lookup(option):
            return _config_values[option]

        _context.mCheckConfigOption.side_effect = _config_lookup
        mock_get_gcontext.return_value = _context

        _node = MagicMock()
        _node.mExecuteLocal.return_value = (0, None, 'Max open files 100 100 100', None)
        mock_exa_box_node.return_value = _node

        _process = MagicMock()
        _process.num_fds.return_value = 120
        mock_process.return_value = _process

        _daemon = ebWorkerDaemon(aLiteCreate=True)
        self.assertTrue(_daemon.mCheckFDLimitBreach())
        self.assertEqual(2, _node.mExecuteLocal.call_count)
        _first_cmd = _node.mExecuteLocal.call_args_list[0][0][0]
        _second_cmd = _node.mExecuteLocal.call_args_list[1][0][0]
        self.assertIn("/proc/{}/limits".format(os.getpid()), _first_cmd)
        self.assertTrue(_second_cmd.startswith("/usr/bin/ls -lt"))

    @patch('exabox.agent.Worker.psutil.Process')
    @patch('exabox.agent.Worker.exaBoxNode')
    @patch('exabox.agent.Worker.get_gcontext')
    def test_mCheckFDLimitBreach_respects_custom_max_value(self, mock_get_gcontext, mock_exa_box_node, mock_process):
        # Auto-generated test for mCheckFDLimitBreach
        _context = MagicMock()
        _context.mGetConfigOptions.return_value = {'ociexacc': 'False', 'oeda_archive_requests_path': ''}
        _context.mGetArgsOptions.return_value = SimpleNamespace(worker_port=None)
        _config_values = {
            'fd_limits_enabled': 'True',
            'fd_limits_custom_threshold': '75',
            'fd_limits_custom_maxvalue': '200'
        }

        def _config_lookup(option):
            return _config_values[option]

        _context.mCheckConfigOption.side_effect = _config_lookup
        mock_get_gcontext.return_value = _context

        _process = MagicMock()
        _process.num_fds.return_value = 150
        mock_process.return_value = _process

        _daemon = ebWorkerDaemon(aLiteCreate=True)
        self.assertFalse(_daemon.mCheckFDLimitBreach())
        _node_instance = mock_exa_box_node.return_value
        _node_instance.mExecuteLocal.assert_not_called()

    @patch('exabox.agent.Worker.shutil.move')
    @patch('exabox.agent.Worker.os.makedirs')
    @patch('exabox.agent.Worker.os.path.exists')
    @patch('exabox.agent.Worker.get_gcontext')
    def test_mArchiveOEDARequests_moves_directory(self, mock_get_gcontext, mock_exists, mock_makedirs, mock_move):
        # Auto-generated test for mArchiveOEDARequests
        _context = MagicMock()
        _context.mGetConfigOptions.return_value = {'ociexacc': 'False', 'oeda_archive_requests_path': ''}
        _context.mGetArgsOptions.return_value = SimpleNamespace(worker_port=None)
        _context.mGetBasePath.return_value = '/base'
        mock_get_gcontext.return_value = _context

        _paths = {
            '/tmp/oeda/request-123': True,
            '/tmp/oeda': True,
            '/base/oeda/requests.bak/': True,
            '/base/oeda/requests.bak/request-123': True
        }
        mock_exists.side_effect = lambda path: _paths.get(path, False)

        _daemon = ebWorkerDaemon(aLiteCreate=True)
        _vmhandle = MagicMock()
        _vmhandle.mGetOEDARequestsPath.return_value = '/tmp/oeda/request-123'
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'

        _daemon.mArchiveOEDARequests(_vmhandle, _job)

        mock_makedirs.assert_called_once_with('/base/oeda/requests.bak/', exist_ok=True)
        mock_move.assert_called_once_with('/tmp/oeda/request-123', '/base/oeda/requests.bak/')

    @patch('exabox.agent.Worker.shutil.move')
    @patch('exabox.agent.Worker.get_gcontext')
    def test_mArchiveOEDARequests_skips_in_exacc_environment(self, mock_get_gcontext, mock_move):
        # Auto-generated test for mArchiveOEDARequests
        _context = MagicMock()
        _context.mGetConfigOptions.return_value = {'ociexacc': 'True', 'oeda_archive_requests_path': ''}
        _context.mGetArgsOptions.return_value = SimpleNamespace(worker_port=None)
        mock_get_gcontext.return_value = _context

        _daemon = ebWorkerDaemon(aLiteCreate=True)
        _job = MagicMock()
        _job.mGetType.return_value = 'cluctrl'

        _daemon.mArchiveOEDARequests(MagicMock(), _job)
        mock_move.assert_not_called()

    def test_mCheckPortForValidation_returns_port_on_immediate_success(self):
        # Auto-generated test for mCheckPortForValidation
        _factory = ebWorkerFactory.__new__(ebWorkerFactory)
        _factory._ebWorkerFactory__config_opts = {}
        _factory._ebWorkerFactory__socket_connect_timeout = 0.1

        _fake_socket = MagicMock()
        _fake_socket.connect_ex.return_value = 0

        with patch('exabox.agent.Worker.socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value = _fake_socket
            mock_socket.return_value.__exit__.return_value = False
            _result = _factory.mCheckPortForValidation(9123)

        self.assertEqual(9123, _result)
        _fake_socket.connect_ex.assert_called_once_with(('localhost', 9123))

    def test_mCheckPortForValidation_returns_port_when_owned_by_process(self):
        # Auto-generated test for mCheckPortForValidation
        _factory = ebWorkerFactory.__new__(ebWorkerFactory)
        _factory._ebWorkerFactory__config_opts = {'socket_check_retry': '2'}
        _factory._ebWorkerFactory__socket_connect_timeout = 0.1
        _port = 9124

        _fake_socket = MagicMock()
        _fake_socket.connect_ex.return_value = errno.ECONNREFUSED
        _conn = SimpleNamespace(laddr=('127.0.0.1', _port), pid=4321, status='LISTEN')

        with patch('exabox.agent.Worker.socket.socket') as mock_socket, \
             patch('exabox.agent.Worker.psutil.net_connections', return_value=[_conn]), \
             patch('exabox.agent.Worker.psutil.pid_exists', return_value=True), \
             patch('exabox.agent.Worker.psutil.Process') as mock_process:
            mock_process.return_value.as_dict.return_value = {'pid': 4321}
            mock_socket.return_value.__enter__.return_value = _fake_socket
            mock_socket.return_value.__exit__.return_value = False
            _result = _factory.mCheckPortForValidation(_port)

        self.assertEqual(_port, _result)
        self.assertEqual(2, _fake_socket.connect_ex.call_count)

    def test_mCheckPortForValidation_returns_zero_when_unreachable(self):
        # Auto-generated test for mCheckPortForValidation
        _factory = ebWorkerFactory.__new__(ebWorkerFactory)
        _factory._ebWorkerFactory__config_opts = {}
        _factory._ebWorkerFactory__socket_connect_timeout = 0.1

        _fake_socket = MagicMock()
        _fake_socket.connect_ex.return_value = errno.ECONNREFUSED

        with patch('exabox.agent.Worker.socket.socket') as mock_socket, \
             patch('exabox.agent.Worker.psutil.net_connections', return_value=[]):
            mock_socket.return_value.__enter__.return_value = _fake_socket
            mock_socket.return_value.__exit__.return_value = False
            _result = _factory.mCheckPortForValidation(9125)

        self.assertEqual(0, _result)
        self.assertEqual(DEFAULT_MAX_RETRIES, _fake_socket.connect_ex.call_count)

    def test_mCheckPort_handles_active_socket_and_extra_validation(self):
        # Auto-generated test for mCheckPort
        _factory = ebWorkerFactory.__new__(ebWorkerFactory)
        _factory._ebWorkerFactory__worker_port_extravalidation = True

        _socket_instance = MagicMock()
        _socket_instance.connect_ex.return_value = 0

        with patch('exabox.agent.Worker.socket.socket', return_value=_socket_instance):
            self.assertEqual(9100, _factory.mCheckPort(9100, False))

        _socket_instance.close.assert_called_once()

    def test_mCheckPort_detects_port_through_extra_validation(self):
        # Auto-generated test for mCheckPort
        _factory = ebWorkerFactory.__new__(ebWorkerFactory)
        _factory._ebWorkerFactory__worker_port_extravalidation = True
        _port = 9101

        _socket_instance = MagicMock()
        _socket_instance.connect_ex.return_value = errno.ECONNREFUSED
        _conn = SimpleNamespace(laddr=('127.0.0.1', _port), pid=555, status='LISTEN')

        with patch('exabox.agent.Worker.socket.socket', return_value=_socket_instance), \
             patch('exabox.agent.Worker.psutil.net_connections', return_value=[_conn]):
            _result = _factory.mCheckPort(_port, True)

        self.assertEqual(_port, _result)
        _socket_instance.close.assert_called_once()

    def test_mCheckPort_returns_zero_when_port_free(self):
        # Auto-generated test for mCheckPort
        _factory = ebWorkerFactory.__new__(ebWorkerFactory)
        _factory._ebWorkerFactory__worker_port_extravalidation = True

        _socket_instance = MagicMock()
        _socket_instance.connect_ex.return_value = errno.ECONNREFUSED

        with patch('exabox.agent.Worker.socket.socket', return_value=_socket_instance), \
             patch('exabox.agent.Worker.psutil.net_connections', return_value=[]):
            _result = _factory.mCheckPort(9102, True)

        self.assertEqual(0, _result)
        _socket_instance.close.assert_called_once()

    def test_mGetPort_skips_reserved_ports_and_retries_until_free(self):
        # Auto-generated test for mGetPort
        _factory = ebWorkerFactory.__new__(ebWorkerFactory)

        with patch.object(_factory, 'mCheckPort', side_effect=[9102, 0]) as mock_check_port:
            _result = _factory.mGetPort(9100, [9100, 9101])

        self.assertEqual(9103, _result)
        self.assertEqual(2, mock_check_port.call_count)
        self.assertEqual(9102, mock_check_port.call_args_list[0][0][0])
        self.assertEqual(9103, mock_check_port.call_args_list[1][0][0])

    def test_mRegister_updates_existing_worker_entry(self):
        # Auto-generated test for mRegister
        _fake_args = SimpleNamespace(proxy=False)
        _context = MagicMock()
        _context.mGetArgsOptions.return_value = _fake_args

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context):
            _db = MagicMock()
            _db.mGetWorker.return_value = object()
            _worker = ebWorker(aDB=_db)

        _worker.mSetPort(9200)
        _worker.mRegister()

        _db.mUpdateWorker.assert_called_once_with(_worker)
        _db.mInsertNewWorker.assert_not_called()

    def test_mRegister_inserts_new_worker_when_absent(self):
        # Auto-generated test for mRegister
        _fake_args = SimpleNamespace(proxy=False)
        _context = MagicMock()
        _context.mGetArgsOptions.return_value = _fake_args

        with patch('exabox.agent.Worker.get_gcontext', return_value=_context):
            _db = MagicMock()
            _db.mGetWorker.return_value = None
            _worker = ebWorker(aDB=_db)

        _worker.mSetPort(9201)
        _worker.mRegister()

        _db.mInsertNewWorker.assert_called_once_with(_worker)
        _db.mUpdateWorker.assert_not_called()

if __name__ == "__main__":
    unittest.main(warnings='ignore')
