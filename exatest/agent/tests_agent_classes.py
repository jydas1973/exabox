#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/agent/tests_agent_classes.py /main/11 2026/01/28 03:29:47 nisrikan Exp $
#
# tests_agent_classes.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_agent_classes.py - Unit tests for exacloud agent classes
#
#    DESCRIPTION
#      Tests agent request handling, worker lifecycle helpers, REST callbacks,
#      and shutdown behavior.
#
#    NOTES
#      Uses mocks to isolate agent logic from external services and worker
#      processes.
#
#    MODIFIED   (MM/DD/YY)
#    aypaul    06/17/26 - Add unit tests for 39392679
#    kanmanic  06/15/26 - 39560339 - Fix ECRA DB connection close guards
#    aypaul    05/26/26 - Fix unit tests for 39392771
#    kanmanic    03/17/26 - 37764703 AQ Status Tracker Support
#    shapatna  04/28/26 - Bug 39255986: Remove ecinstmaintenance endpoint
#    aypaul    04/28/26 - Add unit tests for 39261045
#    aararora  03/03/26 - Bug 38902170: Correct resource leak issues
#    nisrikan  01/20/26 - Bug 38702503 - NEED A MECHANISM TO ROUTE CALLS TO OPCTL IN CASE OF NODE CONNECTION FAILURES
#    aypaul      02/26/24 - Issue#36134753 Add unit tests for changes in
#                           AYPAUL_BUG-36120429 and AYPAUL_AGENTUNRESPONSIVEFIX
#    aypaul      09/25/23 - Add unit test cases for 35813639
#    naps        01/31/23 - Bug 34958798 - Make cpu and mem threshold values
#                           configurable.
#    aypaul      12/11/22 - Unit tests for mReturnSystemResourceUsage.
#    aypaul      02/17/22 - Creation
#
import json
import unittest
import warnings
import socket
import os
import sys
import logging
import shutil
import uuid
import copy
import posix
import errno
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, PropertyMock, mock_open

with patch('multiprocessing.Lock', return_value=MagicMock()):
    from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
    from exabox.core.Node import exaBoxNode
    from exabox.core.MockCommand import exaMockCommand
    from exabox.core.DBStore import ebGetDefaultDB
    from exabox.agent.Agent import ebRestHttpListener, ebAgentInfo, dispatchJobToWorker, isAdditionalWorkerAllowed, ebScheduleInfo, ebAgentDaemon,\
    ebSetDefaultAgent, ebSetAgentInfo
    from exabox.log.LogMgr import ebLogInfo, ebThreadLoggingClose
    from exabox.proxy.router import Router
    from multiprocessing import Lock
    from exabox.agent.ebJobRequest import ebJobRequest
    from exabox.agent.Worker import ebWorker
    from exabox.core.Core import gCoreState, gCoreObject
    from exabox.network.HTTPSHelper import ebResponse
    from exabox.agent.HTTPResponses import JSONResponse
    from exabox.core.Context import get_gcontext

DEFAULT_RESPONSE_BODY = [f"{uuid.uuid1()}", "Done", "Sat Feb 12 10:19:12 2022", "Sat Feb 12 12:19:12 2022", "sim_install", str(dict()), \
                        "0", "Undef", "[\"body contents\"]", "patchedxml", "dummy status info", "cluster_name", "lock", "data"]

global dummy_agent_daemon
dummy_agent_daemon = None

class dummyWriteOptions():

    def write(self, aString):
        ebLogInfo(aString.decode('utf8'))

class dummyCoreContext():

    def mGetVersion(self):
        return "version1", "version2"

class mockWrapStrBytesFunction():

    def __init__(self, value="oeda"):
        self.returncode = 0
        self.value = value
        self.stdout = ""

    def communicate(self):
        if self.value == "agentpids":
            return "2738500\n2738501\n2738502", "stderr"
        else:
            return "oeda_ver_123", "stderr"

class testOptions(object): pass

class ebTestAgentClasses(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestAgentClasses, self).setUpClass(aGenerateDatabase=True)
        warnings.filterwarnings("ignore")
        self._db = ebGetDefaultDB()
        self._db.mCreateProxyRequestsTable()
        self._db.mCreateExacloudInstanceTable()
        self._db.mCreateUUIDToExacloudInstanceTable()

    def test_mCheckAgentState(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mCheckAgentState")
        _job_req = ebJobRequest("mock_cmd_type", {}, self._db)
        self._db.mInsertNewRequest(_job_req)
        _job_req.mSetUUID(str(uuid.uuid1()))
        self._db.mInsertNewRequest(_job_req)
        _job_req.mSetUUID(str(uuid.uuid1()))
        _job_req.mSetStatus("Done")
        self._db.mInsertNewRequest(_job_req)
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            _agent_daemon = ebAgentDaemon()
            _agent_daemon.mCheckAgentState()

        ebLogInfo("test on ebRestHttpListener.mCheckAgentState succeeded.")

    def test_mWorkerStatus(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mWorkerStatus")

        _server_class = ebRestHttpListener(aConfig=None)
        _resp = {}
        _worker_status = [["9877","9e089474-9621-11ec-a763-fa163e8a4946","mockstatus","mockclustername","mockcommand"]]
        _check_status = {"success":False}
        mock_ebresponse = ebResponse("mockurl")
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetWorkerStatus', return_value=_worker_status),\
             patch('exabox.network.HTTPSHelper.build_opener', return_value=mock_ebresponse),\
             patch('exabox.network.HTTPSHelper.ebResponse.read', return_value=json.dumps(_check_status)):
             _server_class.mWorkerStatus({"req_auth_header":"mockauthheader"}, _resp)
        _resp = {}
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetWorkerStatus', return_value=_worker_status),\
             patch('exabox.network.HTTPSHelper.build_opener', side_effect=Exception("Mock worker exception")):
             _server_class.mWorkerStatus({"req_auth_header":"mockauthheader"}, _resp)
        ebLogInfo("test on ebRestHttpListener.mWorkerStatus succeeded.")

    def test_mAgentFetchLog(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentFetchLog")

        _server_class = ebRestHttpListener(aConfig=None)
        _resp = {}
        with patch('json.load', side_effect=Exception("hcconfig retrival failed exception")):
            _server_class.mAgentFetchLog({'jobid':'mockuuid--mockchunkid'}, _resp)
        with patch('json.load', return_value={"diag_root": "mockdiagrootvalue"}):
            _server_class.mAgentFetchLog({'jobid':'mockuuid--mockchunkid'}, _resp)
        ebLogInfo("test on ebRestHttpListener.mAgentFetchLog succeeded.")

    def test_mAgentLogDownload(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentLogDownload")

        _server_class = ebRestHttpListener(aConfig=None)
        _resp = {}
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mParseXMLConfig'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCopyDBLogFiles', return_value="mocklogfolder"),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetClusterName', return_value="mockclustername"),\
             patch('glob.glob', return_value=["file1", "file2"]),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal'):
             _server_class.mAgentLogDownload({"dbName":"mockdbname", "vmName":"mockvmname", "configpath":"mockconfigpath"}, _resp)
             self.assertEqual(_resp["file"], "mocklogfolder/mockclustername.tgz")
        ebLogInfo("test on ebRestHttpListener.mAgentLogDownload succeeded.")

    def test_serve_forever_closes_thread_logging(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.serve_forever for thread logging cleanup")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class._ebRestHttpListener__main_agent_pid = os.getpid() + 1
        _server_class.httpd = MagicMock()
        _server_class.httpd.serve_forever.return_value = None

        with patch('exabox.agent.Agent.ebThreadLocalLog') as mock_thread_local, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('exabox.agent.Agent.ebThreadLoggingClose') as mock_close:
            mock_thread_local.return_value = MagicMock(activated_by=None)
            mock_get_logger.return_value = MagicMock(handlers=[])
            _server_class.serve_forever()

        mock_close.assert_called_once()
        ebLogInfo("test on ebRestHttpListener.serve_forever succeeded.")

    def test_mAgent_Start_triggers_sync_workers(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebAgentDaemon.mAgent_Start for AQ sync worker start.")

        class FakeContext(object):
            def mCheckConfigOption(self, key, default=None):
                if key == 'ociexacc':
                    return False
                if key == 'enable_pushstatus_support':
                    return 'True'
                if key == 'backup_configuration_during_start':
                    return False
                return False

            def mGetPropagateProcOptions(self):
                return []

        agent = ebAgentDaemon.__new__(ebAgentDaemon)
        agent._ebAgentDaemon__config_opts = {
            'agent_port': 1521,
            'agent_delegation_enabled': 'FALSE',
            'supervisor': 'False',
            'scheduler': 'False'
        }
        agent._ebAgentDaemon__config = {'agent_port': 1521}
        agent._ebAgentDaemon__args_options = SimpleNamespace(proxy=False, nosupervisor=True, daemonize=False)
        agent._ebAgentDaemon__workerFactory = MagicMock()
        agent._ebAgentDaemon__proxy_client = None
        agent._ebAgentDaemon__exatest = False
        agent._ebAgentDaemon__specialWorkersPids = []
        agent._ebAgentDaemon__restlistener = MagicMock()
        agent._ebAgentDaemon__disable_monitor = True
        agent._mDaemonizedSubProcesses_mStart = MagicMock()

        previous_ld = os.environ.get('LD_LIBRARY_PATH')
        os.environ['LD_LIBRARY_PATH'] = '/tmp'
        fake_conn = MagicMock()
        fake_conn.close = MagicMock()
        fake_oracledb = SimpleNamespace(
            init_oracle_client=lambda: None,
            connect=MagicMock(return_value=fake_conn)
        )

        try:
            with patch.object(ebAgentDaemon, 'mCheckAgentState', side_effect=SystemExit), \
                 patch('exabox.agent.Agent.get_gcontext', return_value=FakeContext()), \
                 patch('exabox.agent.Agent.get_ecradb_details', return_value={
                     'user': 'user', 'password': 'pwd', 'host': 'host', 'port': '1521', 'service_name': 'svc'
                 }), \
                 patch.dict(sys.modules, {'oracledb': fake_oracledb}), \
                 patch('exabox.core.AQResponse._start_aqname_sync_worker') as start_aq_mock, \
                 patch('exabox.core.AQResponse._start_liveliness_worker') as start_live_mock:
                with self.assertRaises(SystemExit):
                    agent.mAgent_Start()
                start_aq_mock.assert_called_once()
                start_live_mock.assert_called_once()
        finally:
            if previous_ld is not None:
                os.environ['LD_LIBRARY_PATH'] = previous_ld
            else:
                del os.environ['LD_LIBRARY_PATH']

    def test_mAgent_Stop_triggers_sync_shutdown(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebAgentDaemon.mAgent_Stop for AQ sync worker shutdown.")

        agent = ebAgentDaemon.__new__(ebAgentDaemon)
        agent._ebAgentDaemon__stopped = False
        agent._ebAgentDaemon__proxy_client = None
        agent._ebAgentDaemon__restlistener = MagicMock()
        agent._ebAgentDaemon__workerFactory = MagicMock()
        agent._ebAgentDaemon__args_options = SimpleNamespace(proxy=False)
        agent._ebAgentDaemon__agent_destination_handlers = None
        agent._ebAgentDaemon__specialWorkersPids = []

        with patch('exabox.core.AQResponse._stop_aqname_sync_worker') as stop_aq_mock, \
             patch('exabox.core.AQResponse._stop_liveliness_worker') as stop_live_mock, \
             patch('exabox.agent.Agent.ebGetDefaultDB') as get_db_mock, \
             patch('exabox.agent.Agent.time.sleep', return_value=None):
            fake_db = MagicMock()
            fake_db.mGetSpecialWorkerPIDs.return_value = {}
            get_db_mock.return_value = fake_db
            agent.mAgent_Stop()

        stop_aq_mock.assert_called_once()
        stop_live_mock.assert_called_once()
        agent._ebAgentDaemon__restlistener.mStopRestListener.assert_called_once()
        agent._ebAgentDaemon__workerFactory.mShutdownFactory.assert_called_once()
        self.assertTrue(agent._ebAgentDaemon__stopped)

    def test_mBDS(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mBDS")

        _server_class = ebRestHttpListener(aConfig=None)
        _resp = {}
        _server_class.mBDS({}, _resp, "cluctrl.bds_cmd")
        _server_class.requestline = "POST https://localhost:1707/dummyendpoint HTTP/1.1"
        _server_class.request_version = "HTTP/1.1"
        _server_class.wfile = dummyWriteOptions()
        with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister'),\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True):
             _server_class.mBDS({"jsonconf": {}, "configpath":"mock config path"}, _resp, "cluctrl.bds_install")
        
        with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister'),\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=False):
             _server_class.mBDS({"jsonconf": {}, "configpath":"mock config path"}, _resp, "cluctrl.bds_install")
        ebLogInfo("test on ebRestHttpListener.mBDS succeeded.")

    def test_log_message_masks_jsonconf_in_access_logs(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.log_message")

        _server_class = ebRestHttpListener(aConfig=None)
        _request_lines = [
            'GET /AgentCtrl?jsonconf=%7B%22oeda_pwd%22%3A%22secret%22%7D HTTP/1.1',
            'GET /CLUCtrl?hostname=h?cmd=infra_patch_operation?jsonconf=%7B%22oeda_pwd%22%3A%22secret%22%7D HTTP/1.1',
            'GET /AgentCtrl?cmd=status&jsonconf=%7B%22oeda_pwd%22%3A%22secret%22%7D HTTP/1.1'
        ]

        with patch('exabox.agent.Agent.ebLogAgent') as mock_log:
            for _request_line in _request_lines:
                with self.subTest(requestline=_request_line):
                    mock_log.reset_mock()
                    _server_class.log_message('"%s" %s %s', _request_line, '200', '-')
                    _logged_message = mock_log.call_args[0][1]
                    self.assertNotIn('secret', _logged_message)
                    self.assertNotIn('%7B%22oeda_pwd%22%3A%22secret%22%7D', _logged_message)
                    self.assertIn('jsonconf=sanitized', _logged_message)
                    self.assertTrue(_logged_message.endswith('" 200 -'))

            _malformed_request_line = '/AgentCtrl?jsonconf=%7B%22oeda_pwd%22%3A%22secret%22%7D invalid syntax from client'
            mock_log.reset_mock()
            _server_class.log_message('%s', _malformed_request_line)
            _logged_message = mock_log.call_args[0][1]
            self.assertNotIn('secret', _logged_message)
            self.assertNotIn('%7B%22oeda_pwd%22%3A%22secret%22%7D', _logged_message)
            self.assertIn('jsonconf=sanitized', _logged_message)
            self.assertIn('invalid syntax from client', _logged_message)

            _error_message = '/AgentCtrl?jsonconf=%7B%22oeda_pwd%22%3A%22secret%22%7D invalid syntax from client'
            mock_log.reset_mock()
            _server_class.log_error('code %d, message %s', 400, _error_message)
            _logged_message = mock_log.call_args[0][1]
            self.assertIn('code 400, message', _logged_message)
            self.assertNotIn('secret', _logged_message)
            self.assertNotIn('%7B%22oeda_pwd%22%3A%22secret%22%7D', _logged_message)
            self.assertIn('jsonconf=sanitized', _logged_message)
            self.assertIn('invalid syntax from client', _logged_message)

        ebLogInfo("test on ebRestHttpListener.log_message succeeded.")

    def test_mHardwareInfo(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mHardwareInfo")

        _server_class = ebRestHttpListener(aConfig=None)
        with patch('exabox.elastic.HardwareInfo.ebHardwareInfo.mGetInfo', return_value="str_hw_info"):
            _resp = {}
            _server_class.mHardwareInfo({"hostname":"mockhostname", "hw_type": "mockhardwaretype", "debug":True}, _resp)
            self.assertEqual(_resp["ec_details"],"str_hw_info")
        with patch('exabox.elastic.HardwareInfo.ebHardwareInfo.mGetInfo', side_effect=Exception("Mock exception raised for hardware info.")):
            _server_class.mHardwareInfo({"hostname":"mockhostname", "hw_type": "mockhardwaretype", "debug":True}, {})
        ebLogInfo("test on ebRestHttpListener.mHardwareInfo succeeded.")

    def test_mAgentCmdRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentCmdRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        global dummy_agent_daemon
        if dummy_agent_daemon is None:
            dummy_agent_daemon = ebAgentDaemon()
        ebSetDefaultAgent(dummy_agent_daemon)
        with patch('exabox.agent.Agent.ebAgentDaemon.mAgent_Shutdown'):
            _temp_resp = {}
            _server_class.mAgentCmdRequest({"cmd":"stop"}, _temp_resp)
            self.assertEqual(_temp_resp["statusinfo"], "Agent shutdown in progress")
            _temp_resp = {}
            _server_class.mAgentCmdRequest({"cmd":"status"}, _temp_resp)
            self.assertEqual(_temp_resp["statusinfo"], "Agent is running and reachable")
        ebLogInfo("test on ebRestHttpListener.mAgentCmdRequest succeeded.")

    def test_mAgentPortal(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentPortal")

        _server_class = ebRestHttpListener(aConfig=None)
        with patch ('exabox.core.Mask.maskSensitiveData', return_value="mock COptions"),\
             patch ('exabox.agent.Agent.ebRestHttpListener.mBuildChecksums', return_value=[{"file":"file name", "tarballCS":"mock tarball", "deployedCS":"mock deployed CS"}]):
            _temp_resp = {}
            _server_class.mAgentPortal({}, _temp_resp)
            self.assertEqual(_temp_resp["output"]["checksums"][0]["file"], "file name")
        ebLogInfo("test on ebRestHttpListener.mAgentPortal succeeded.")

    def test_mBuildChecksums(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mBuildChecksums")
        _server_class = ebRestHttpListener(aConfig=None)
        with patch ('os.path.exists', return_value=True),\
             patch ("builtins.open", mock_open(read_data="120EA8A25E5D487BF68B5F7096440019 file_name")):
             _checksum_list = _server_class.mBuildChecksums()
             self.assertEqual(_checksum_list[0]["file"], "file_name")
        with patch ('os.path.exists', return_value=True),\
             patch ("builtins.open", mock_open(read_data="file_name")):
             _checksum_list = _server_class.mBuildChecksums()
             self.assertEqual(_checksum_list[0]["deployedCS"], "undefined")

        ebLogInfo("test on ebRestHttpListener.mBuildChecksums succeeded.")

    def test_mAgentWorkers(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentWorkers")
        _server_class = ebRestHttpListener(aConfig=None)
        _worker_dump = [["00000000-0000-0000-0000-000000000000","Idle","Sat Feb 12 10:19:12 2022","Undef","NULL","Undef","Undef",\
             '{"status": "000:: No status info available"}',"26447","9139","worker","Undef","2022-02-23 11:51:32.621223", "NORMAL"]]
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value=str(_worker_dump)):
            _server_class.mAgentWorkers({}, {})
        ebLogInfo("test on ebRestHttpListener.mAgentWorkers succeeded.")

    def test_mAgentTestPage(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentTestPage")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mAgentTestPage({}, {})
        ebLogInfo("test on ebRestHttpListener.mAgentTestPage succeeded.")

    def test_mAgentVersion(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentVersion")
        _server_class = ebRestHttpListener(aConfig=None)
        gCoreObject = dummyCoreContext()
        mockWrap = mockWrapStrBytesFunction()
        temp_rsp = {}
        with patch('subprocess.Popen', return_value=mockWrap),\
             patch('exabox.tools.AttributeWrapper.wrapStrBytesFunctions', return_value=mockWrap),\
             patch('exabox.core.Core.gCoreState', 1),\
             patch('exabox.core.Core.gCoreObject', gCoreObject),\
             patch('exabox.core.Context.exaBoxContext.mGetVersion', return_value="exacloud_version_123"):
             _server_class.mAgentVersion({}, temp_rsp)

        ebLogInfo("test on ebRestHttpListener.mAgentVersion succeeded.")

    def test_mAgentOedaLogs(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentOedaLogs")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mAgentOedaLogs({},{})
        params = {"uuid": f"{uuid.uuid1()}", "patch": "mockpatch"}
        response = {}
        def _mock_stat(path):
            return MagicMock(st_mtime=1 if path.endswith("logile1") else 2)

        def _mock_isfile_error(path):
            if "/log/patch/" in path or "/oeda/requests/" in path or "/log/bmcctrl/" in path:
                raise Exception("mock file error")
            return True

        with patch('os.stat', side_effect=_mock_stat),\
             patch('os.listdir', return_value=["logile1", "logfile2"]),\
             patch('os.path.isfile', return_value=True):
             _server_class.path = "https://localhost:1707/dummyendpoint"
             _server_class.mAgentOedaLogs(params, response)
             response = {}
             params = {"uuid": f"{uuid.uuid1()}", "bmcctrl": "mockbmcctrl"}
             _server_class.path = "https://localhost:1707/dummyendpoint"
             _server_class.mAgentOedaLogs(params, response)
             response = {}
             params = {"uuid": f"{uuid.uuid1()}"}
             _server_class.path = "https://localhost:1707/PatchLogs"
             _server_class.mAgentOedaLogs(params, response)
             response = {}
             _server_class.path = "https://localhost:1707/BMCCtrlLogs"
             _server_class.mAgentOedaLogs(params, response)
             response = {}
             _server_class.mAgentOedaLogs(params, response)

        params = {"uuid": f"{uuid.uuid1()}", "patch": "mockpatch"}
        response = {}
        with patch('os.stat', side_effect=_mock_stat),\
             patch('os.listdir', return_value=["logile1", "logfile2"]),\
             patch('os.path.isfile', side_effect=_mock_isfile_error):
             _server_class.path = "https://localhost:1707/dummyendpoint"
             _server_class.mAgentOedaLogs(params, response)
        
        ebLogInfo("test on ebRestHttpListener.mAgentOedaLogs succeeded.")

    def test_mAgentOedaDiags(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentOedaDiags")
        _server_class = ebRestHttpListener(aConfig=None)
        _temp_resp = {}
        _server_class.mAgentOedaDiags({},_temp_resp)
        self.assertEqual(_temp_resp["output"],{"status":"DIAG OK"})
        ebLogInfo("test on ebRestHttpListener.mAgentOedaDiags succeeded.")

    def test_mAgentHome(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentHome")
        _server_class = ebRestHttpListener(aConfig=None)

        global dummy_agent_daemon
        if dummy_agent_daemon is None:
            dummy_agent_daemon = ebAgentDaemon()
        dummy_agent_info = ebAgentInfo("6555")
        ebSetDefaultAgent(dummy_agent_daemon)
        ebSetAgentInfo(dummy_agent_info)
        gCoreObject = dummyCoreContext()

        with patch('exabox.agent.Agent.ebAgentDaemon.mAgent_Config', return_value=["dummyhost.oracle.com","4555"]) as mock1,\
             patch('exabox.agent.Agent.ebAgentInfo.mGetPid', return_value="6555") as mock2,\
             patch('exabox.core.Core.gCoreState', 1),\
             patch('exabox.core.Core.gCoreObject', gCoreObject),\
             patch('exabox.core.Context.exaBoxContext.mGetOEDAVersion', return_value="dummy_oeda_version"),\
             patch('exabox.core.Context.exaBoxContext.mGetOEDAHostname', return_value="oeadhostname.oracle.com") as mock4:
             _server_class.mAgentHome({}, {})
        ebLogInfo("test on ebRestHttpListener.mAgentHome succeeded.")

    def test_mValidatePath(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mValidatePath")

        _server_class = ebRestHttpListener(aConfig=None)
        correct_path = "/this/is/a/correct/path"
        incorrect_path = "/this/../is/a/correct/path"
        self.assertEqual(_server_class.mValidatePath(correct_path),True)
        self.assertEqual(_server_class.mValidatePath(incorrect_path),False)
        ebLogInfo("test on ebRestHttpListener.mValidatePath succeeded.")

    def test_mMonitor(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mMonitor")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mMonitor({"key1":"val1"}, {})

        _worker_dump = [["7e59b8da-9561-11ec-bdfe-fa163e8a4946","Idle","Sat Feb 12 10:19:12 2022","Undef","NULL","Undef","Undef",\
             '{"status": "000:: No status info available"}',"26447","9139","monitor","Undef","2022-02-23 11:51:32.621223", "NORMAL"]]
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value=str(_worker_dump)) as mock1,\
             patch('exabox.agent.Worker.ebWorker.mUpdateDB') as mock2:
            _server_class.mMonitor({"cmd":"refresh"}, {})

        _worker_dump = [["00000000-0000-0000-0000-000000000000","Idle","Sat Feb 12 10:19:12 2022","Undef","NULL","Undef","Undef",\
             '{"status": "000:: No status info available"}',"26447","9139","worker","Undef","2022-02-23 11:51:32.621223", "NORMAL"]]
        with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister') as mock1,\
             patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value=str(_worker_dump)) as mock3,\
             patch('exabox.agent.Worker.ebWorker.mUpdateDB') as mock2:
             _server_class.mMonitor({"cmd":"start"}, {})
        ebLogInfo("test on ebRestHttpListener.mMonitor succeeded.")

    def test_mVMRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mVMRequest")

        coptions = get_gcontext().mGetConfigOptions()
        _agent_debug = coptions.get('agent_debug')
        get_gcontext().mSetConfigOption('agent_debug', "False")

        try:
            _server_class = ebRestHttpListener(aConfig=None)
            _server_class.mVMRequest(None, {})
            _server_class.mVMRequest({"hostname":"val1"}, {})

            with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister') as mock1,\
                 patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True) as mock2:
                 _server_class.mVMRequest({"hostname":"dummyhostname", "cmd":"start"}, {})

            _params = {
                "hostname": "dummyhostname",
                "cmd": "start",
                "jsonconf": {"oeda_pwd": "secret"}
            }
            with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister'),\
                 patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True),\
                 patch('exabox.agent.Agent.ebLogInfo') as mock_log:
                 _server_class.mVMRequest(_params, {})
            _sanitized_logs = [
                _call.args[0] for _call in mock_log.call_args_list
                if _call.args and '* Request parameters (sanitized):' in _call.args[0]
            ]
            self.assertEqual(len(_sanitized_logs), 1)
            self.assertIn("'oeda_pwd': '********'", _sanitized_logs[0])
            self.assertNotIn("secret", _sanitized_logs[0])
        finally:
            get_gcontext().mSetConfigOption('agent_debug', _agent_debug)
        ebLogInfo("test on ebRestHttpListener.mVMRequest succeeded.")

    def test_mXmlGeneration(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mXmlGeneration")

        _server_class = ebRestHttpListener(aConfig=None)
        with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister') as mock1,\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True) as mock2:
             _server_class.mXmlGeneration({"jsonconf":{}}, {})
        ebLogInfo("test on ebRestHttpListener.mXmlGeneration succeeded.")

    def test_mOCIRegionUpdater(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mOCIRegionUpdater")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mOCIRegionUpdater({"jsonconf":{}}, {})

        with patch('exabox.utils.oci_region.update_oci_config'):
            _server_class.mOCIRegionUpdater({"jsonconf":{"urlmapping":[{"realm":"realm1", "realmdomain":"realmdomain1", "regionkey":"regionkey1",\
                                        "regionidentifier":"regionidentifier1"}]}}, {})
        ebLogInfo("test on ebRestHttpListener.mOCIRegionUpdater succeeded.")

    def test_mExaKmsRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mExaKmsRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mExaKmsRequest(None, {})

        with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister') as mock1,\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True) as mock3:
             _server_class.mExaKmsRequest({"cmd":"dummycommand"}, {})
        ebLogInfo("test on ebRestHttpListener.mExaKmsRequest succeeded.")

    def test_mCLURequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mCLURequest")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mCLURequest(None, {})
        _server_class.mCLURequest({"key1":"val1"}, {})
        _server_class.mCLURequest({"hostname":"dummyhost.us.oracle.com"}, {})
        _server_class.mCLURequest({"hostname":"dummyhost.us.oracle.com", "cmd":"dummycommand"}, {})
        _server_class.mCLURequest({"hostname":"dummyhost.us.oracle.com", "cmd":"patchclu_apply"}, {})
        _server_class.mCLURequest({"hostname":"dummyhost.us.oracle.com", "cmd":"diskgroup"}, {})
        _server_class.mCLURequest({"hostname":"dummyhost.us.oracle.com", "cmd":"validate_elastic_shapes"}, {})

        with patch('exabox.ovm.cluexaccatp.ebExaCCAtpSimulatePayload.mIsATPSimulateEnabled', return_value=True) as mock1,\
             patch('exabox.ovm.cluexaccatp.ebExaCCAtpSimulatePayload.mInjectATPfromAgentWorkaround') as mock2,\
             patch('exabox.agent.Agent.ebRestHttpListener.mScheduleRequest') as mock3,\
             patch('exabox.core.DBStore3.ebExacloudDB.mUpdateRequest') as mock4:
             _server_class.mCLURequest({"hostname":"dummyhost.us.oracle.com", "cmd":"checkcluster", \
                                  "jsonconf":{"scheduler_job":{"command":"dummy command","operation": "cancel","mode":"dummy mode"}}}, {})

        with patch('exabox.ovm.cluexaccatp.ebExaCCAtpSimulatePayload.mIsATPSimulateEnabled', return_value=True) as mock1,\
             patch('exabox.ovm.cluexaccatp.ebExaCCAtpSimulatePayload.mInjectATPfromAgentWorkaround') as mock2,\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True) as mock3:
             _server_class.mCLURequest({"hostname":"dummyhost.us.oracle.com", "cmd":"checkcluster"}, {})

        ebLogInfo("test on ebRestHttpListener.mCLURequest succeeded.")

    def test_mScheduleGenericRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mScheduleGenericRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mScheduleGenericRequest({}, {})

        _server_class.mScheduleGenericRequest({"jsonconf":"dummyjsonconf"}, {})
        _server_class.mScheduleGenericRequest({"jsonconf":{}, "cmd":"dummy command"}, {})
        with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister') as mock1,\
             patch('exabox.agent.Agent.ebRestHttpListener.mScheduleRequest') as mock2,\
             patch('exabox.core.DBStore3.ebExacloudDB.mUpdateRequest') as mock3:
             _server_class.mScheduleGenericRequest({"jsonconf":{"scheduler_job":{"command":"dummy command","operation": "cancel","mode":"dummy mode"}}, "cmd":"dummy command"}, {})

        with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister') as mock1,\
             patch('exabox.agent.Agent.ebRestHttpListener.mScheduleRequest') as mock2,\
             patch('exabox.core.DBStore3.ebExacloudDB.mUpdateRequest') as mock3:
             _server_class.mScheduleGenericRequest({"jsonconf":{"scheduler_job":{"command":"dummy command","operation": "schedule","mode":"dummy mode"}}, "cmd":"dummy command"}, {})

        ebLogInfo("test on ebRestHttpListener.mScheduleGenericRequest succeeded.")

    def test_mScheduleRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mScheduleRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        _temp_params = {"jsonconf":{"scheduler_job":{"command":"dummy command","operation": "schedule","mode":"dummy mode"}}}
        dummy_req = ebJobRequest(None,{})
        with patch('exabox.agent.Agent.ebRestHttpListener.mUpdateScheduleInfo') as mock1,\
             patch('exabox.agent.Agent.ebScheduleInfo.mRegister') as mock2,\
             patch('exabox.agent.Scheduler.scheduler_running', return_value=3342) as mock3,\
             patch('os.kill') as mock4:
             _server_class.mScheduleRequest(dummy_req,_temp_params)

        _temp_params = {"jsonconf":{"scheduler_job":{"uuid":uuid.uuid1(),"command":"dummy command","operation": "cancel","mode":"dummy mode"}}}
        with patch('exabox.agent.Agent.ebRestHttpListener.mUpdateScheduleInfo') as mock1,\
             patch('exabox.agent.Scheduler.scheduler_running', return_value=3342) as mock2,\
             patch('os.kill') as mock3:
             _server_class.mScheduleRequest(dummy_req,_temp_params)

        ebLogInfo("test on ebRestHttpListener.mScheduleRequest succeeded.")

    def test_mUpdateScheduleInfo(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mUpdateScheduleInfo")

        _server_class = ebRestHttpListener(aConfig=None)
        _sched_info = ebScheduleInfo(uuid.uuid1(), self._db)
        _temp_params = {"jsonconf":{"scheduler_job":{"sc_events":{"timer_job": {"timer_type": 1, "timestamp":"dummytime", \
                         "interval":"dummyinterval", "repeat_count": "30"}},"command":"dummy command","operation": "dummyoperation","mode":"dummy mode"}}}
        _updated_sched_info = _server_class.mUpdateScheduleInfo(_sched_info, 'Idle', _temp_params)

        _temp_params = {"jsonconf":{"scheduler_job":{"sc_events":{"follow_up_job": {"monitor_uuid": uuid.uuid1()}},"command":"dummy command","operation": "dummyoperation","mode":"dummy mode"}}}
        _updated_sched_info = _server_class.mUpdateScheduleInfo(_sched_info, 'Idle', _temp_params)
        _temp_params = {"jsonconf":{"scheduler_job":{"sc_events":{"no_active_jobs": {"monitor_worker_jobs": "dummyjob1"}},"command":"dummy command","operation": "dummyoperation","mode":"dummy mode"}}}
        _updated_sched_info = _server_class.mUpdateScheduleInfo(_sched_info, 'Idle', _temp_params)
        ebLogInfo("test on ebRestHttpListener.mUpdateScheduleInfo succeeded.")

    def test_mBMRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mBMRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mBMRequest(None,{})
        _server_class.mBMRequest({"cmd":"dummy command"},{})
        _server_class.mBMRequest({"cmd":"add_customer_info"},{})

        with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister') as mock1,\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True) as mock2:
             _server_class.mBMRequest({"cmd":"compose_cluster", "jsonconf":"dummy json configuration"},{})

        ebLogInfo("test on ebRestHttpListener.mBMRequest succeeded.")

    def test_mShowStatus(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mShowStatus")

        _server_class = ebRestHttpListener(aConfig=None)
        with patch('exabox.agent.Mock.MockStatus', return_value=None):
            _server_class.mShowStatus({'mock_mode':'True',"uuid":f"{uuid.uuid1()}"}, {})

        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpRequests', return_value="dummy_response"):
            _temp_resp = {}
            _server_class.mShowStatus({}, _temp_resp)
            self.assertEqual(_temp_resp['body'],"dummy_response")
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetRequest', return_value=None):
            _temp_uuid = uuid.uuid1()
            _temp_resp = {}
            _server_class.mShowStatus({'uuid':_temp_uuid}, _temp_resp)
            self.assertEqual(_temp_resp['uuid'],_temp_uuid)

        temp_response = copy.deepcopy(DEFAULT_RESPONSE_BODY)
        temp_response[6] = "777"
        temp_response[7] = "Infrapatching error message for unit tests."
        error_response = ["entry0", "mock_error_code", "mock_error_msg", "mock_error_type", "2", "mock_detail_error"]
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetRequest', return_value=temp_response) as mock1,\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetErrCodeByUUID', return_value=error_response) as mock2,\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetSELinuxViolationStatusForRequest', return_value=True) as mock3:
             _server_class.mShowStatus({"uuid":f"{uuid.uuid1()}", "frompath_uuid": True}, {})

        temp_response = copy.deepcopy(DEFAULT_RESPONSE_BODY)
        temp_response[6] = "701-614"
        temp_response[7] = "Infrapatching error message for unit tests."
        error_response = ["entry0", "mock_error_code", "mock_error_msg", "mock_error_type", "2", "mock_detail_error"]
        data_dict = {"data":{"error_code":"701-614", "error_message":"Infrapatching error message for unit tests.","error_detail":"Infrapatching error details."}}
        json_patch_report = [["patch_operation1", "Done", json.dumps(data_dict)]]
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetRequest', return_value=temp_response) as mock1,\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetErrCodeByUUID', return_value=error_response) as mock2,\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetSELinuxViolationStatusForRequest', return_value=True) as mock3,\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetChildRequestsList', return_value=json_patch_report) as mock4:
             _server_class.mShowStatus({"uuid":f"{uuid.uuid1()}", "frompath_uuid": True}, {})

        temp_response = copy.deepcopy(DEFAULT_RESPONSE_BODY)
        temp_response[6] = "701-614"
        temp_response[7] = "Infrapatching error message for unit tests."
        error_response = ["entry0", "mock_error_code", "mock_error_msg", "mock_error_type", "2", "mock_detail_error"]
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetRequest', return_value=temp_response) as mock1,\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetErrCodeByUUID', return_value=error_response) as mock2,\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetSELinuxViolationStatusForRequest', return_value=True) as mock3,\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetChildRequestsList', return_value=[]) as mock4,\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetPatchChildRequest', return_value=["Done",json.dumps({"error_code":"701-614", "error_message":"Infrapatching error message for unit tests."})]) as mock5:
             _server_class.mShowStatus({"uuid":f"{uuid.uuid1()}", "frompath_uuid": True}, {})

        ebLogInfo("test on ebRestHttpListener.mShowStatus succeeded.")

    def test_exaproxyWriteResponse(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.exaproxyWriteResponse")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.request_version = "HTTP/1.1"
        _server_class.requestline = "POST https://localhost:1707/dummyendpoint HTTP/1.1"
        _server_class.wfile = dummyWriteOptions()

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectResponseDetailsFromProxyRequests', return_value=[200,"dummybody","{\"key1\":\"value1\"}"]):
            _server_class.exaproxyWriteResponse("dummyUUID")

        ebLogInfo("test on ebRestHttpListener.exaproxyWriteResponse succeeded.")

    def test_WriteResponse(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ResponseHandler.WriteResponse")

        _request_handler = ebRestHttpListener(aConfig=None)
        _request_handler.request_version = "HTTP/1.1"
        _request_handler.requestline = "POST https://localhost:1707/dummyendpoint HTTP/1.1"
        _request_handler.wfile = dummyWriteOptions()

        _response_handler = JSONResponse()
        with patch('exabox.agent.Agent.ebRestHttpListener.send_response', side_effect=Exception("Raising a mock exception while executing send response.")):
            _response_handler.WriteResponse(_request_handler)

        ebLogInfo("test on ResponseHandler.WriteResponse succeeded.")

    def test_dispatchJobToWorker(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on dispatchJobToWorker")

        coptions = get_gcontext().mGetConfigOptions()
        configs = {'agent_debug':None,'disable_cpumem_threshold':None,'agent_delegation_enabled':None,'accept_req_during_cpumem_threshold_breach':None}
        for config in configs.keys():
            if config in list(coptions.keys()):
                configs[config] = coptions.get(config)

        get_gcontext().mSetConfigOption('agent_debug',"True")
        get_gcontext().mSetConfigOption('disable_cpumem_threshold',"True")
        get_gcontext().mSetConfigOption('agent_delegation_enabled',"True")
        get_gcontext().mSetConfigOption('accept_req_during_cpumem_threshold_breach',"True")
        worker_dump = [["00000000-0000-0000-0000-000000000000","Idle","Undef","Undef","Undef","Undef","Undef","Undef","45666","9139","worker","Undef","Undef", "NORMAL"]]


        with patch('exabox.agent.Agent.isAdditionalWorkerAllowed', return_value=True) as mock1,\
             patch('exabox.agent.Agent.literal_eval', return_value=worker_dump) as mock2:
                _reqobj = ebJobRequest(None, {}, aDB=self._db)
                self.assertEqual(dispatchJobToWorker(_reqobj,Lock()),True)

        with patch('exabox.agent.Agent.isAdditionalWorkerAllowed', return_value=False) as mock1,\
             patch('exabox.agent.Agent.literal_eval') as mock2:
                mock2.return_value = [["00000000-0000-0000-0000-000000000000","Idle","Undef","Undef","Undef","Undef","Undef","Undef","45666","9139","worker","Undef","Undef", "CORRUPTED"]]
                _reqobj = ebJobRequest(None, {}, aDB=self._db)
                self.assertEqual(dispatchJobToWorker(_reqobj,Lock()),True)

        get_gcontext().mSetConfigOption('accept_req_during_cpumem_threshold_breach',"False")
        with patch('exabox.agent.Agent.isAdditionalWorkerAllowed', return_value=False) as mock1,\
             patch('exabox.agent.Agent.literal_eval') as mock2:
                mock2.return_value = [["00000000-0000-0000-0000-000000000000","Idle","Undef","Undef","Undef","Undef","Undef","Undef","45666","9139","worker","Undef","Undef", "CORRUPTED"]]
                _reqobj = ebJobRequest(None, {}, aDB=self._db)
                self.assertEqual(dispatchJobToWorker(_reqobj,Lock()),False)

        get_gcontext().mSetConfigOption('agent_delegation_enabled',"False")
        with patch('exabox.agent.Agent.isAdditionalWorkerAllowed', return_value=True) as mock1,\
             patch('signal.signal') as mock2,\
             patch('exabox.agent.Agent.literal_eval', return_value=worker_dump),\
             patch('exabox.agent.Worker.ebWorker.mLoadWorkerFromDB') as mock3,\
             patch('exabox.agent.Worker.ebWorker.mAcquireSyncLock', return_value=True) as mock4,\
             patch('os.kill'),\
             patch('exabox.agent.Worker.ebWorker.mUpdateDB'),\
             patch('exabox.agent.Worker.ebWorker.mReleaseSyncLock'):
             mock2.side_effect = ValueError("Unit test error")
             _reqobj = ebJobRequest(None, {}, aDB=self._db)
             self.assertEqual(dispatchJobToWorker(_reqobj,Lock()),True)

        ebLogInfo("Running the last case.")

        with patch('exabox.agent.Agent.isAdditionalWorkerAllowed', return_value=False) as mock1,\
             patch('signal.signal'),\
             patch('exabox.agent.Agent.literal_eval', return_value=worker_dump),\
             patch('exabox.agent.Worker.ebWorker.mLoadWorkerFromDB'),\
             patch('exabox.agent.Worker.ebWorker.mAcquireSyncLock', return_value=True),\
             patch('os.kill') as mock2,\
             patch('exabox.agent.Worker.ebWorker.mReleaseSyncLock'):
             mock2.side_effect = OSError(errno.ESRCH, 'No such process')
             _reqobj = ebJobRequest(None, {}, aDB=self._db)
             self.assertEqual(dispatchJobToWorker(_reqobj,Lock()),False)

        with patch('exabox.agent.Agent.isAdditionalWorkerAllowed', return_value=False) as mock1,\
             patch('signal.signal'),\
             patch('exabox.agent.Agent.literal_eval', return_value=worker_dump),\
             patch('exabox.agent.Worker.ebWorker.mReleaseSyncLock'):
             _reqobj = ebJobRequest(None, {}, aDB=self._db)
             self.assertEqual(dispatchJobToWorker(_reqobj,Lock()),False)

        for config in configs.keys():
            if configs.get(config) is not None:
                get_gcontext().mSetConfigOption(config, configs.get(config))


        ebLogInfo("test on dispatchJobToWorker succeeded.")

    def test_isAdditionalWorkerAllowed(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on isAdditionalWorkerAllowed")

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectAllFromEnvironmentResourceDetails', return_value=(None, None, None)):
            self.assertEqual(isAdditionalWorkerAllowed(False, 80.0, 80.0), True)

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectAllFromEnvironmentResourceDetails', return_value=("81.0", "21.0", None)):
            self.assertEqual(isAdditionalWorkerAllowed(False, 80.0, 80.0), False)

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectAllFromEnvironmentResourceDetails', return_value=("21.0", "21.0", None)):
            self.assertEqual(isAdditionalWorkerAllowed(False, 80.0, 80.0), True)

        ebLogInfo("test on isAdditionalWorkerAllowed succeeded.")

    def test_mHandleRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mHandleRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.request_version = "HTTP/1.1"
        _server_class.path = "https://localhost:1707/dummyendpoint"
        _server_class.command = "POST"
        _server_class.requestline = "POST https://localhost:1707/dummyendpoint HTTP/1.1"
        _server_class.headers = {}
        _server_class.wfile = dummyWriteOptions()

        _server_class.mHandleRequest()

        with patch('exabox.agent.HTTPResponses.HttpCb.executeRequest', return_value="dummyresponse") as mock1,\
             patch('exabox.agent.HTTPResponses.HttpCb.returnResponse') as mock2:
             _server_class.path = "https://localhost:1707/CLUCtrl"
             _server_class.requestline = "POST https://localhost:1707/CLUCtrl HTTP/1.1"
             _server_class.mHandleRequest()

        ebLogInfo("test on ebRestHttpListener.mHandleRequest succeeded.")

    def test_mLoadAgentFromDB(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebAgentInfo.mLoadAgentFromDB")

        _agent_info = ebAgentInfo("007")
        self._db.mInsertAgent(_agent_info)

        _new_agent_info = ebAgentInfo()
        _new_agent_info.mLoadAgentFromDB("007")
        self.assertEqual(_new_agent_info.mGetUUID(), "007")
        self.assertEqual(_new_agent_info.mGetHostname(), socket.getfqdn())
        ebLogInfo("test on ebAgentInfo.mLoadAgentFromDB succeeded.")

    def test_mRefreshMock(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mRefreshMock")

        _server_class = ebRestHttpListener(None)
        self.assertEqual(_server_class.mGetMockMode(), False)
        _server_class.mRefreshMock({'mock_mode':'True'})
        self.assertEqual(_server_class.mGetMockMode(), True)
        _server_class.mRefreshMock({'mock_mode':'False'})
        self.assertEqual(_server_class.mGetMockMode(), False)
        ebLogInfo("test on ebRestHttpListener.mRefreshMock succeeded.")

    def test_do_JSON(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.do_JSON")

        _server_class = ebRestHttpListener(None)
        _server_class.request_version = "HTTP/1.0"
        _server_class.wfile = dummyWriteOptions()
        _original_response = {}
        _server_class.do_JSON(_original_response)
        ebLogInfo("test on ebRestHttpListener.do_JSON succeeded.")

    @patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True)
    @patch('exabox.proxy.router.Router.mGetECInstance', return_value=("localhost", "6733", "sampleauthkey"))
    def test_dispatchHTTPPostReqToWorker(self, mock_dispatchjobtoworker, mock_mgetecinstance):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.dispatchHTTPPostReqToWorker")

        _server_class = ebRestHttpListener(aConfig=None, aRouterInstance=Router())
        _server_class.request_version = "HTTP/1.1"
        _server_class.requestline = "POST https://localhost:1707/CLUCtrl HTTP/1.1"
        _server_class.wfile = dummyWriteOptions()
        _server_class.dispatchHTTPPostReqToWorker("CLUCtrl","https://localhost:1707/CLUCtrl", {"cmd":"sim_install"}, {'Access-Control-Allow-Origin':'*'}, None, str(uuid.uuid1()))
        ebLogInfo("test on ebRestHttpListener.dispatchHTTPPostReqToWorker succeeded.")

    def test_getResponseFromExacloud(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.getResponseFromExacloud")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.request_version = "HTTP/1.1"
        _server_class.requestline = "POST https://localhost:1707/dummyendpoint HTTP/1.1"
        _server_class.wfile = dummyWriteOptions()
        _server_class.getResponseFromExacloud("dummyendpoint", None, None, None, None)

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectStatusFromUUIDToECInstance', return_value="InitialReqPending"):
            _server_class.requestline = "GET https://localhost:1707/Status/cea45c7a-9488-11ec-ba34-5e2382e085b0 HTTP/1.1"
            _server_class.getResponseFromExacloud("Status", None, {'uuid':'cea45c7a-9488-11ec-ba34-5e2382e085b0'}, None,  None)

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectStatusFromUUIDToECInstance', return_value="InitialReqDone") as mock1,\
             patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value='dummyworkerid') as mock2:
            _server_class.requestline = "GET https://localhost:1707/Status/cea45c7a-9488-11ec-ba34-5e2382e085b0 HTTP/1.1"
            _server_class.getResponseFromExacloud("Status", None, {'uuid':'cea45c7a-9488-11ec-ba34-5e2382e085b0'}, None,  None)

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectStatusFromUUIDToECInstance', return_value="InitialReqDone") as mock1,\
             patch('exabox.core.DBStore3.ebExacloudDB.mDumpWorkers', return_value='()') as mock2,\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True) as mock3:
            _server_class.requestline = "GET https://localhost:1707/Status/cea45c7a-9488-11ec-ba34-5e2382e085b0 HTTP/1.1"
            _server_class.getResponseFromExacloud("Status", None, {'uuid':'cea45c7a-9488-11ec-ba34-5e2382e085b0'}, None,  None)

        ebLogInfo("test on ebRestHttpListener.getResponseFromExacloud succeeded.")

    def test_mReturnSystemResourceUsage(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mReturnSystemResourceUsage")

        _server_class = ebRestHttpListener(aConfig=None)

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectAllFromEnvironmentResourceDetails', return_value=(56, 78, None)):
            _temp_resp = {}
            _server_class.mReturnSystemResourceUsage({}, _temp_resp)
            _system_metrics = json.loads(_temp_resp['system_metrics'])
            self.assertEqual(_system_metrics['CPU Usage'], 56)
            self.assertEqual(_system_metrics['Memory Usage'], 78)

        with patch('exabox.core.DBStore3.ebExacloudDB.mSelectAllFromEnvironmentResourceDetails', return_value=(None, None, None)):
            _temp_resp = {}
            _server_class.mReturnSystemResourceUsage({}, _temp_resp)
            _system_metrics = json.loads(_temp_resp['system_metrics'])
            self.assertEqual(_system_metrics['CPU Usage'], 0)
            self.assertEqual(_system_metrics['Memory Usage'], 0)

    def test_mAgentForceKill(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebAgentDaemon.mAgentForceKill")
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            _agent_daemon = ebAgentDaemon()
        _mock_options = testOptions()
        _mock_options.proxy = False

        mockWrap = mockWrapStrBytesFunction(value = "agentpids")
        with patch('subprocess.Popen', return_value=mockWrap),\
             patch('exabox.tools.AttributeWrapper.wrapStrBytesFunctions', return_value=mockWrap),\
             patch('os.kill'),\
             patch('exabox.agent.Supervisor.ebSupervisor.mDeleteCrontab', return_value=True):
             _agent_daemon.mAgentForceKill(_mock_options)

        with patch('subprocess.Popen', return_value=mockWrap),\
             patch('exabox.tools.AttributeWrapper.wrapStrBytesFunctions', return_value=mockWrap),\
             patch('os.kill'),\
             patch('exabox.agent.Supervisor.ebSupervisor.mDeleteCrontab', return_value=False):
             _agent_daemon.mAgentForceKill(_mock_options)

    def test_mAgent_Start(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebAgentDaemon.mAgent_Start")
        _restorevalproxy, _restorevaldaemonize = get_gcontext().mGetArgsOptions().proxy, get_gcontext().mGetArgsOptions().daemonize
        get_gcontext().mGetArgsOptions().proxy = True
        get_gcontext().mGetArgsOptions().daemonize = False
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            _agent_daemon = ebAgentDaemon()
        

        with patch('exabox.agent.Agent.ebAgentDaemon.mCheckAgentState'),\
             patch('exabox.agent.Agent.ebWorkerFactory.mInitFactory'),\
             patch('subprocess.run'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateAgentTable'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mAgentStatus', return_value = None),\
             patch('exabox.agent.Agent.ebRestListener.mStartRestListener'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mUpdateUUIDtoexacloudForAgentStart'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mSelectAllFromRequestuuidtoExacloud', return_value=list()),\
             patch('exabox.agent.Agent.Lock'),\
             patch('exabox.agent.Agent.mBackupFile', return_value=False),\
             patch('exabox.agent.Agent.ebAgentDaemon.mAgent_Stop'),\
             patch.object(_agent_daemon,"_ebAgentDaemon__restlistener", True):
             _agent_daemon.mAgent_Start()

        get_gcontext().mGetArgsOptions().proxy, get_gcontext().mGetArgsOptions().daemonize = _restorevalproxy, _restorevaldaemonize
        ebLogInfo("Unit test on ebAgentDaemon.mAgent_Start completed successfully.")

    def test_mProcessSOPRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mProcessSOPRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mProcessSOPRequest(None,{})
        _server_class.mProcessSOPRequest({"cmd":"dummy command"},{})
        _server_class.mProcessSOPRequest({"jsonconf":"not_a_dictionary"},{})
        _server_class.mProcessSOPRequest({"jsonconf":{"key":"value"}},{})
        _server_class.mProcessSOPRequest({"jsonconf":{"cmd":"notavalidcommand","scriptname":"value"}},{})
        with patch('exabox.agent.Agent.ebJobRequest.mRegister'),\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=False),\
             patch('exabox.agent.Agent.buildErrorResponseForRequest'):
                _server_class.mProcessSOPRequest({"jsonconf":{"cmd":"start","scriptname":"newscript.py"}},{})

        with patch('exabox.agent.Agent.ebJobRequest.mRegister'),\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True):
                response = {}
                _server_class.mProcessSOPRequest({"jsonconf":{"cmd":"start","scriptname":"newscript.py"}},response)
                self.assertEqual(response.get('status'),'Pending')
                self.assertEqual(response.get('success'),'True')

        ebLogInfo("Unit test on ebRestHttpListener.mProcessSOPRequest completed successfully.")

    def test_mValidateNetworkInfoPayload(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mValidateNetworkInfoPayload")

        _server_class = ebRestHttpListener(aConfig=None)
        _response = _server_class.mValidateNetworkInfoPayload({"interface": "value", "information": "value"})
        self.assertEqual(_response, "Key: nodes is missing from payload." )

        _interface_value = 32
        _response = _server_class.mValidateNetworkInfoPayload({"interface": _interface_value, "information": "value", "nodes": "value"})
        self.assertEqual(_response, f"Interface value is expected of type string but passed {type(_interface_value)}")

        _interface_value = "bond0;touch /tmp/x"
        _response = _server_class.mValidateNetworkInfoPayload({"interface": _interface_value, "information": "value", "nodes": "value"})
        self.assertEqual(_response, f"Interface value is an improper string which doesn't contain standard interfaces values")

        _interface_value = "stre0"
        _response = _server_class.mValidateNetworkInfoPayload({"interface": _interface_value, "information": "value", "nodes": "value"})
        self.assertEqual(_response, f"Information value is either not of type list or empty list is passed in payload.")
        _response = _server_class.mValidateNetworkInfoPayload({"interface": _interface_value, "information": [], "nodes": "value"})
        self.assertEqual(_response, f"Information value is either not of type list or empty list is passed in payload.")

        _information_value = ["stre0information"]
        _response = _server_class.mValidateNetworkInfoPayload({"interface": _interface_value, "information": _information_value, "nodes": "value"})
        self.assertEqual(_response, f"Nodes value is either not of type list or empty list is passed in payload.")
        _response = _server_class.mValidateNetworkInfoPayload({"interface": _interface_value, "information": _information_value, "nodes": []})
        self.assertEqual(_response, f"Nodes value is either not of type list or empty list is passed in payload.")

        _nodes = ["host-.example.com"]
        _response = _server_class.mValidateNetworkInfoPayload({"interface": _interface_value, "information": _information_value, "nodes": _nodes})
        self.assertEqual(_response, "Hostname: host-.example.com is not a valid hostname/FQDN")
        _nodes = ["myhost.oracle.com","myhost","host..example.com"]
        _response = _server_class.mValidateNetworkInfoPayload({"interface": _interface_value, "information": _information_value, "nodes": _nodes})
        self.assertEqual(_response, "Hostname: host..example.com is not a valid hostname/FQDN")

        _nodes = ["myhost.oracle.com","myhost"]
        _response = _server_class.mValidateNetworkInfoPayload({"interface": _interface_value, "information": _information_value, "nodes": _nodes})
        self.assertEqual(_response, "")

        ebLogInfo("Unit test on ebRestHttpListener.mValidateNetworkInfoPayload completed.")

    def test_mFetchNetworkInfoRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mFetchNetworkInfoRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        _response = _server_class.mFetchNetworkInfoRequest(None,{})

        with patch('exabox.agent.Agent.ebRestHttpListener.mValidateNetworkInfoPayload', return_value="error"):
            _response = _server_class.mFetchNetworkInfoRequest({"jsonconf": ""},{})

        with patch('exabox.agent.Agent.ebRestHttpListener.mValidateNetworkInfoPayload', return_value=""),\
             patch('exabox.agent.Agent.ebJobRequest.mRegister'),\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=False):
            _response = _server_class.mFetchNetworkInfoRequest({"jsonconf": {"information":[12,23]}},{})

        with patch('exabox.agent.Agent.ebRestHttpListener.mValidateNetworkInfoPayload', return_value=""),\
             patch('exabox.agent.Agent.ebJobRequest.mRegister'),\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True):
             response = {}
             _response = _server_class.mFetchNetworkInfoRequest({"jsonconf": {"information":[12,23]}},response)
             self.assertEqual(response.get('success'), "True")
             self.assertEqual(response.get('status'),'Pending')

        ebLogInfo("Unit test on ebRestHttpListener.mFetchNetworkInfoRequest completed successfully")

    def test_mJsonDispatchRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mJsonDispatchRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        _response = _server_class.mJsonDispatchRequest(None,{})
        _response = _server_class.mJsonDispatchRequest({"key": "value"},{})

        _response = _server_class.mJsonDispatchRequest({"cmd": "vmbackup"},{})

        with patch('exabox.agent.Agent.ebJobRequest.mRegister'),\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True):
             response = {}
             _response = _server_class.mJsonDispatchRequest({"cmd": "vmbackup", "jsonconf": {"action":"value"}},response)
             self.assertEqual(response.get('success'), "True")
             self.assertEqual(response.get('status'),'Pending')

        ebLogInfo("Unit test on ebRestHttpListener.mJsonDispatchRequest completed successfully")

    def test_mEDVManagement(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mEDVManagement")

        _server_class = ebRestHttpListener(aConfig=None)
        _response = _server_class.mEDVManagement(None,{})

        _response = _server_class.mEDVManagement({"cmd": "edvcommand"},{})

        with patch('exabox.agent.Agent.ebJobRequest.mRegister'),\
             patch('exabox.agent.Agent.dispatchJobToWorker', side_effect=[False, True]):
             response = {}
             _response = _server_class.mEDVManagement({"cmd": "edvcommand"},response)
             _response = _server_class.mEDVManagement({"cmd": "edvcommand"},response)


        ebLogInfo("Unit test on ebRestHttpListener.mEDVManagement completed successfully")

    def test_mAgentCluster(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentCluster")

        _server_class = ebRestHttpListener(aConfig=None)
        with patch('exabox.agent.Agent.literal_eval', side_effect=Exception("mockexception")):
            _response = _server_class.mAgentCluster(None,{})

        jsonvalue1 = {"key": "value"}
        clusterstatusop = [["clusterid","mockhostname","mocknodetype","mocknetworkip","True","True","True","True","True",f"{json.dumps(jsonvalue1)}"]]
        mockparam = {"configpath": "mockconfig"}
        dumprequestsop = [[f"{uuid.uuid1()}","Pending","Undef","Undef","mock.cmd",f"{json.dumps(mockparam)}","0","Undef","Undef","mockxml",\
        "Undef","mockclustername","Undef",f"{json.dumps(jsonvalue1)}","mocksubcommand","Undef","Undef"]]

        with patch('exabox.agent.Agent.literal_eval', side_effect=[clusterstatusop,dumprequestsop]),\
             patch('exabox.agent.Agent.exaBoxCluCtrl.mParseXMLConfig'),\
             patch('exabox.agent.Agent.exaBoxCluCtrl.mReturnDom0DomUPair', return_value=[["mockdom0", "mockdomu"]]),\
             patch('exabox.agent.Agent.exaBoxCluCtrl.mReturnCellNodes', return_value=["mockcellnode"]):
             response = {}
             _response = _server_class.mAgentCluster(None,response)

        ebLogInfo("Unit test on ebRestHttpListener.mAgentCluster completed successfully")

    def test_mAgentWWWContent(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentWWWContent")

        _server_class = ebRestHttpListener(aConfig=None)
        response = {}
        _response = _server_class.mAgentWWWContent(None,response)
        self.assertEqual(_response["output"], {"err_msg":"No parameters supplied."})

        params = {"file": "/root/mockfile.txt"}
        with patch('exabox.agent.Agent.ebRestHttpListener.mValidatePath') as mock1,\
             patch('builtins.open', new_callable=mock_open, read_data="mock data"):
             response = {}
             mock1.return_value = True
             _server_class.mAgentWWWContent(params,response)
             self.assertEqual(response['output'], "mock data")

        params = {"file": "/root/mockfile.txt"}
        with patch('exabox.agent.Agent.ebRestHttpListener.mValidatePath') as mock1,\
             patch('builtins.open', new_callable=mock_open, read_data=None):
             response = {}
             mock1.return_value = False
             _server_class.mAgentWWWContent(params,response)
             self.assertEqual(response['output'], "Error. www/content file not found: www//root/mockfile.txt.")

        params = {"file": "/root/mockfile.txt"}
        with patch('exabox.agent.Agent.ebRestHttpListener.mValidatePath') as mock1,\
             patch('builtins.open', side_effect=Exception("open error")):
             response = {}
             mock1.return_value = True
             _server_class.mAgentWWWContent(params,response)
             self.assertEqual(response['output'], "Error while accessing www/content file: www//root/mockfile.txt.")

        ebLogInfo("Unit test on ebRestHttpListener.mAgentWWWContent completed successfully")

    def test_mAgentRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAgentRequest")

        _server_class = ebRestHttpListener(aConfig=None)
        currentuuid = uuid.uuid1()
        params = {"cmdtype": "create_service", "ccluster": f"{currentuuid}"}
        response = {}
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpRequests', return_value="()"):
            _server_class.mAgentRequest(params,response)
            self.assertEqual(response["output"], {"Error" : f"XML Cluster Configuration not available for uuid: {currentuuid}"})

        params = {"cmdtype": "create_service", "ccluster": f"{currentuuid}"}
        response = {}
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpRequests', return_value="mockvalue"),\
             patch('exabox.agent.Agent.literal_eval', return_value=[["","","","","","","","","","mockxml.xml"]]),\
             patch('builtins.open', new_callable=mock_open, read_data="mock data"):
            _server_class.mAgentRequest(params,response)
            self.assertEqual(response["output"], "mock data")

        params = {"cmdtype": "create_service", "ccluster": f"{currentuuid}"}
        response = {}
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpRequests', return_value="mockvalue"),\
             patch('exabox.agent.Agent.literal_eval', return_value=[["","","","","","","","","","mockxml.xml"]]),\
             patch('builtins.open', side_effect=Exception("open error")):
            _server_class.mAgentRequest(params,response)
            self.assertEqual(response["output"], {"Error" : f"XML Cluster Configuration not readable for uuid: {currentuuid}"})

        params = {"cmdtype": "create_service", "cparams": f"{currentuuid}"}
        response = {}
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpRequests', return_value="()"),\
             patch('exabox.agent.Agent.obfuscate_passwd_entries'):
            _server_class.mAgentRequest(params,response)
            self.assertEqual(response["output"], {"Error" : f"Request Type info not available for uuid: {currentuuid}"})

        params = {"cmdtype": "create_service", "cparams": f"{currentuuid}"}
        response = {}
        with patch('exabox.core.DBStore3.ebExacloudDB.mDumpRequests', return_value="mockvalue"),\
             patch('exabox.agent.Agent.literal_eval', return_value=[["","","","","","mockxml.xml"]]),\
             patch('exabox.agent.Agent.obfuscate_passwd_entries'):
            _server_class.mAgentRequest(params,response)
            self.assertEqual(response["output"], "mockxml.xml")


        coptions = get_gcontext().mGetConfigOptions()
        configs = {'threads_formatter':None}
        for config in configs.keys():
            if config in list(coptions.keys()):
                configs[config] = coptions.get(config)

        get_gcontext().mSetConfigOption('threads_formatter','%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        params = {"cmdtype": "create_service", "file": "mockfile.dat", "hidetime": "true"}
        response = {}
        with patch('os.path.realpath', return_value=params["file"]),\
             patch('os.path.dirname', return_value=params["file"]),\
             patch('builtins.open', new_callable=mock_open, read_data="2025-06-30 09:56:47,685 - exatest - INFO - Testing file: /scratch/aypaul/view_storage/aypaul_agentunittests/ecs/exacloud/exabox/exatest/agent/tests_agent_classes.py"):
            _server_class.mAgentRequest(params,response)

        params = {"cmdtype": "create_service", "file": "mockfile.dat", "hidetime": "true"}
        response = {}
        with patch('os.path.realpath', return_value=params["file"]),\
             patch('os.path.dirname', return_value="notmock"),\
             patch('builtins.open', new_callable=mock_open, read_data="2025-06-30 09:56:47,685 - exatest - INFO - Testing file: /scratch/aypaul/view_storage/aypaul_agentunittests/ecs/exacloud/exabox/exatest/agent/tests_agent_classes.py"):
            _server_class.mAgentRequest(params,response)

        params = {"cmdtype": "create_service", "file": "mockfile.dat", "hidetime": "true"}
        response = {}
        with patch('os.path.realpath', return_value=params["file"]),\
             patch('os.path.dirname', return_value="notmock"),\
             patch('builtins.open', side_effect=Exception("Mock error")):
            _server_class.mAgentRequest(params,response)

        get_gcontext().mSetConfigOption('threads_formatter','%(name)s - %(levelname)s - %(message)s')

        params = {"cmdtype": "create_service", "file": "mockfile.dat", "hidetime": "true"}
        response = {}
        with patch('os.path.realpath', return_value=params["file"]),\
             patch('os.path.dirname', return_value=params["file"]),\
             patch('builtins.open', new_callable=mock_open, read_data="2025-06-30 09:56:47,685 - exatest - INFO - Testing file: /scratch/aypaul/view_storage/aypaul_agentunittests/ecs/exacloud/exabox/exatest/agent/tests_agent_classes.py"):
            _server_class.mAgentRequest(params,response)

        params = {"cmdtype": "create_service"}
        response = {}
        with patch('exabox.agent.Agent.monitor.build_requests_html_page', return_value="content-from-build_requests_html_page"):
            _server_class.mAgentRequest(params,response)
            self.assertEqual(response["output"], "content-from-build_requests_html_page")

        get_gcontext().mSetConfigOption('threads_formatter', configs['threads_formatter'])

        ebLogInfo("Running unit test on ebRestHttpListener.mAgentRequest")

    def test_mAtpGetFile(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mAtpGetFile")

        coptions = get_gcontext().mGetConfigOptions()
        configs = {'atpgetfile_base_path':None}
        for config in configs.keys():
            if config in list(coptions.keys()):
                configs[config] = coptions.get(config)

        _server_class = ebRestHttpListener(aConfig=None)
        params = []
        response = {}
        _response = _server_class.mAtpGetFile(params,response)
        self.assertEqual(_response["output"], {"err_msg":"No parameters supplied."})

        params = {"type": "text"}
        response = {}
        _response = _server_class.mAtpGetFile(params,response)

        get_gcontext().mSetConfigOption('atpgetfile_base_path', "")
        params = {"type": "text", "file": "mockfile.txt"}
        response = {}
        _response = _server_class.mAtpGetFile(params,response)

        get_gcontext().mSetConfigOption('atpgetfile_base_path', "/")
        params = {"type": "text", "file": "mockfile.txt"}
        response = {}
        _response = _server_class.mAtpGetFile(params,response)

        get_gcontext().mSetConfigOption('atpgetfile_base_path', "/atpbasepath")
        params = {"type": "text", "file": "mockfile.txt"}
        response = {}
        with patch('os.path.realpath', return_value="/atpbasepath/mockfile.txt"),\
             patch('os.path.isfile', return_value=False):
             _response = _server_class.mAtpGetFile(params,response)

        params = {"type": "text", "file": "mockfile.txt"}
        response = {}
        with patch('os.path.realpath', return_value="/atpbasepath/mockfile.txt"),\
             patch('os.path.isfile', return_value=True),\
             patch('builtins.open', new_callable=mock_open, read_data="mock data"):
             _response = _server_class.mAtpGetFile(params,response)

        params = {"type": "data", "file": "mockfile.dat"}
        response = {}
        with patch('os.path.realpath', return_value="/atpbasepath/mockfile.dat"),\
             patch('os.path.isfile', return_value=True),\
             patch('builtins.open', new_callable=mock_open, read_data="mock data"),\
             patch('os.path.basename', return_value="mockbasename"):
             _response = _server_class.mAtpGetFile(params,response)

        params = {"type": "html", "file": "mockfile.html"}
        response = {}
        with patch('os.path.realpath', return_value="/atpbasepath/mockfile.html"),\
             patch('os.path.isfile', return_value=True),\
             patch('builtins.open', new_callable=mock_open, read_data="mock data"),\
             patch('exabox.agent.Agent.monitor.build_html_page_header', return_value="mock monitor header"),\
             patch('exabox.agent.Agent.monitor.build_html_page_footer', return_value="mock monitor footer"):
             _response = _server_class.mAtpGetFile(params,response)

        get_gcontext().mSetConfigOption('atpgetfile_base_path', configs['atpgetfile_base_path'])

        ebLogInfo("Running unit test on ebRestHttpListener.mAtpGetFile")

    def test_mCheckOpctlStatus(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mCheckOpctlStatus")

        _server_class = ebRestHttpListener(aConfig=None)
        body = ["mockdata1","mockdata2","mockdata3","mockdata4","mockdata5","mockdata6","mockdata7","mockdata8","mockdata9","mockdata10","mockdata11",'"status": "200"']
        params = []
        db = None
        response = {}
        _response = _server_class.mCheckOpctlStatus(body, params, db, response)

        body = ["mockdata1","mockdata2","mockdata3","mockdata4","mockdata5",f"'idemtoken': '{uuid.uuid1()}'","mockdata7","mockdata8","mockdata9","mockdata10","mockdata11"]
        params = []
        db = None
        response = {}
        with patch('exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper.check_status_for_idemtoken', return_value=None):
            _response = _server_class.mCheckOpctlStatus(body, params, db, response)

        body = ["mockdata1","mockdata2","mockdata3","mockdata4","mockdata5",f"'idemtoken': '{uuid.uuid1()}'","mockdata7","mockdata8","mockdata9","mockdata10","mockdata11"]
        params = []
        db = None
        response = {}
        opctljobreq = ebJobRequest("mockcmd.opctl", {})
        opctljobreq.mSetBody({"bodykey":"bodyvalue"})
        opctljobreq.mSetError("mockerror")
        with patch('exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper.check_status_for_idemtoken', return_value=opctljobreq):
            _response = _server_class.mCheckOpctlStatus(body, params, db, response)
            self.assertEqual(_response["body"],json.dumps({"bodykey":"bodyvalue"}))
            self.assertEqual(_response["success"], "False")

        body = ["mockdata1","mockdata2","mockdata3","mockdata4","mockdata5",f"'idemtoken': '{uuid.uuid1()}'","mockdata7","mockdata8","mockdata9","mockdata10","mockdata11"]
        params = {"uuid": f"{uuid.uuid1()}"}
        db = None
        response = {}
        with patch('exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper.check_status_for_idemtoken', side_effect=Exception("Status check exception")):
            _response = _server_class.mCheckOpctlStatus(body, params, db, response)
        
        ebLogInfo("Unit test on ebRestHttpListener.mCheckOpctlStatus completed successfully.")


class ebAgentAQStartupCoverageTest(unittest.TestCase):

    class _FakeContext(object):
        def mCheckConfigOption(self, key, default=None):
            if key == 'ociexacc':
                return False
            if key == 'enable_pushstatus_support':
                return 'True'
            if key == 'backup_configuration_during_start':
                return False
            return default

        def mGetPropagateProcOptions(self):
            return []

    def _build_agent(self):
        agent = ebAgentDaemon.__new__(ebAgentDaemon)
        agent._ebAgentDaemon__config_opts = {
            'agent_port': 1521,
            'agent_delegation_enabled': 'FALSE',
            'supervisor': 'False',
            'scheduler': 'False'
        }
        agent._ebAgentDaemon__config = {'agent_port': 1521}
        agent._ebAgentDaemon__args_options = SimpleNamespace(proxy=False, nosupervisor=True, daemonize=False)
        agent._ebAgentDaemon__workerFactory = MagicMock()
        agent._ebAgentDaemon__proxy_client = None
        agent._ebAgentDaemon__exatest = False
        agent._ebAgentDaemon__specialWorkersPids = []
        agent._ebAgentDaemon__restlistener = MagicMock()
        agent._ebAgentDaemon__disable_monitor = True
        agent._mDaemonizedSubProcesses_mStart = MagicMock()
        return agent

    def test_mAgent_Start_returns_when_ld_library_path_missing(self):
        agent = self._build_agent()
        previous_ld = os.environ.pop('LD_LIBRARY_PATH', None)

        try:
            with patch('exabox.agent.Agent.get_gcontext', return_value=self._FakeContext()), \
                 patch.object(ebAgentDaemon, 'mCheckAgentState') as check_state_mock:
                agent.mAgent_Start()

            check_state_mock.assert_not_called()
        finally:
            if previous_ld is not None:
                os.environ['LD_LIBRARY_PATH'] = previous_ld

    def test_mAgent_Start_returns_when_mandatory_conn_param_missing(self):
        agent = self._build_agent()
        previous_ld = os.environ.get('LD_LIBRARY_PATH')
        os.environ['LD_LIBRARY_PATH'] = '/tmp'
        fake_oracledb = SimpleNamespace(
            init_oracle_client=lambda: None,
            connect=MagicMock()
        )

        try:
            with patch('exabox.agent.Agent.get_gcontext', return_value=self._FakeContext()), \
                 patch('exabox.agent.Agent.get_ecradb_details', return_value={
                     'user': 'user', 'password': 'pwd', 'host': 'host', 'port': '1521'
                 }), \
                 patch.object(ebAgentDaemon, 'mCheckAgentState') as check_state_mock, \
                 patch.dict(sys.modules, {'oracledb': fake_oracledb}):
                agent.mAgent_Start()

            fake_oracledb.connect.assert_not_called()
            check_state_mock.assert_not_called()
        finally:
            if previous_ld is not None:
                os.environ['LD_LIBRARY_PATH'] = previous_ld
            else:
                del os.environ['LD_LIBRARY_PATH']

    def test_mAgent_Start_returns_on_connection_failure(self):
        agent = self._build_agent()
        previous_ld = os.environ.get('LD_LIBRARY_PATH')
        os.environ['LD_LIBRARY_PATH'] = '/tmp'
        fake_oracledb = SimpleNamespace(
            init_oracle_client=lambda: None,
            connect=MagicMock(side_effect=Exception("oracle down"))
        )

        try:
            with patch('exabox.agent.Agent.get_gcontext', return_value=self._FakeContext()), \
                 patch('exabox.agent.Agent.get_ecradb_details', return_value={
                     'user': 'user', 'password': 'pwd', 'host': 'host', 'port': '1521', 'service_name': 'svc'
                 }), \
                 patch.object(ebAgentDaemon, 'mCheckAgentState') as check_state_mock, \
                 patch.dict(sys.modules, {'oracledb': fake_oracledb}):
                agent.mAgent_Start()

            fake_oracledb.connect.assert_called_once()
            check_state_mock.assert_not_called()
        finally:
            if previous_ld is not None:
                os.environ['LD_LIBRARY_PATH'] = previous_ld
            else:
                del os.environ['LD_LIBRARY_PATH']

    def test_mAgent_Start_continues_when_sync_worker_start_fails(self):
        agent = self._build_agent()
        previous_ld = os.environ.get('LD_LIBRARY_PATH')
        os.environ['LD_LIBRARY_PATH'] = '/tmp'
        fake_oracledb = SimpleNamespace(
            init_oracle_client=lambda: None,
            connect=MagicMock(return_value=MagicMock())
        )

        try:
            with patch('exabox.agent.Agent.get_gcontext', return_value=self._FakeContext()), \
                 patch('exabox.agent.Agent.get_ecradb_details', return_value={
                     'user': 'user', 'password': 'pwd', 'host': 'host', 'port': '1521', 'service_name': 'svc'
                 }), \
                 patch.object(ebAgentDaemon, 'mCheckAgentState', side_effect=SystemExit), \
                 patch.dict(sys.modules, {'oracledb': fake_oracledb}), \
                 patch('exabox.core.AQResponse._start_aqname_sync_worker', side_effect=RuntimeError("boom")), \
                 patch('exabox.core.AQResponse._start_liveliness_worker') as start_live_mock:
                with self.assertRaises(SystemExit):
                    agent.mAgent_Start()

            start_live_mock.assert_not_called()
            fake_oracledb.connect.assert_called_once()
        finally:
            if previous_ld is not None:
                os.environ['LD_LIBRARY_PATH'] = previous_ld
            else:
                del os.environ['LD_LIBRARY_PATH']

    def test_mAgent_Start_triggers_sync_workers(self):
        agent = self._build_agent()
        previous_ld = os.environ.get('LD_LIBRARY_PATH')
        os.environ['LD_LIBRARY_PATH'] = '/tmp'
        fake_conn = MagicMock()
        fake_oracledb = SimpleNamespace(
            init_oracle_client=lambda: None,
            connect=MagicMock(return_value=fake_conn)
        )

        try:
            with patch('exabox.agent.Agent.get_gcontext', return_value=self._FakeContext()), \
                 patch('exabox.agent.Agent.get_ecradb_details', return_value={
                     'user': 'user', 'password': 'pwd', 'host': 'host', 'port': '1521', 'service_name': 'svc'
                 }), \
                 patch.object(ebAgentDaemon, 'mCheckAgentState', side_effect=SystemExit), \
                 patch.dict(sys.modules, {'oracledb': fake_oracledb}), \
                 patch('exabox.core.AQResponse._start_aqname_sync_worker') as start_aq_mock, \
                 patch('exabox.core.AQResponse._start_liveliness_worker') as start_live_mock:
                with self.assertRaises(SystemExit):
                    agent.mAgent_Start()

            fake_oracledb.connect.assert_called_once()
            fake_conn.close.assert_called_once()
            start_aq_mock.assert_called_once()
            start_live_mock.assert_called_once()
        finally:
            if previous_ld is not None:
                os.environ['LD_LIBRARY_PATH'] = previous_ld
            else:
                del os.environ['LD_LIBRARY_PATH']

    def test_mAgent_Start_import_error_still_runs_sync_workers(self):
        agent = self._build_agent()
        previous_ld = os.environ.get('LD_LIBRARY_PATH')
        os.environ['LD_LIBRARY_PATH'] = '/tmp'
        original_import = __import__

        def _import_with_oracledb_failure(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'oracledb':
                raise ImportError("missing oracledb")
            return original_import(name, globals, locals, fromlist, level)

        try:
            with patch('exabox.agent.Agent.get_gcontext', return_value=self._FakeContext()), \
                 patch.object(ebAgentDaemon, 'mCheckAgentState', side_effect=SystemExit), \
                 patch('builtins.__import__', side_effect=_import_with_oracledb_failure), \
                 patch('exabox.core.AQResponse._start_aqname_sync_worker') as start_aq_mock, \
                 patch('exabox.core.AQResponse._start_liveliness_worker') as start_live_mock:
                with self.assertRaises(SystemExit):
                    agent.mAgent_Start()

            start_aq_mock.assert_called_once()
            start_live_mock.assert_called_once()
        finally:
            if previous_ld is not None:
                os.environ['LD_LIBRARY_PATH'] = previous_ld
            else:
                del os.environ['LD_LIBRARY_PATH']

    def test_mAgent_Stop_continues_when_sync_shutdown_fails(self):
        agent = ebAgentDaemon.__new__(ebAgentDaemon)
        agent._ebAgentDaemon__stopped = False
        agent._ebAgentDaemon__proxy_client = None
        agent._ebAgentDaemon__restlistener = MagicMock()
        agent._ebAgentDaemon__workerFactory = MagicMock()
        agent._ebAgentDaemon__args_options = SimpleNamespace(proxy=False)
        agent._ebAgentDaemon__agent_destination_handlers = None
        agent._ebAgentDaemon__specialWorkersPids = []

        with patch('exabox.core.AQResponse._stop_aqname_sync_worker', side_effect=RuntimeError("stop failed")), \
             patch('exabox.agent.Agent.ebGetDefaultDB') as get_db_mock, \
             patch('exabox.agent.Agent.time.sleep', return_value=None):
            fake_db = MagicMock()
            fake_db.mGetSpecialWorkerPIDs.return_value = {}
            get_db_mock.return_value = fake_db
            agent.mAgent_Stop()

        agent._ebAgentDaemon__restlistener.mStopRestListener.assert_called_once()
        agent._ebAgentDaemon__workerFactory.mShutdownFactory.assert_called_once()
        self.assertTrue(agent._ebAgentDaemon__stopped)

    def test_mAgent_Stop_triggers_sync_shutdown(self):
        agent = ebAgentDaemon.__new__(ebAgentDaemon)
        agent._ebAgentDaemon__stopped = False
        agent._ebAgentDaemon__proxy_client = None
        agent._ebAgentDaemon__restlistener = MagicMock()
        agent._ebAgentDaemon__workerFactory = MagicMock()
        agent._ebAgentDaemon__args_options = SimpleNamespace(proxy=False)
        agent._ebAgentDaemon__agent_destination_handlers = None
        agent._ebAgentDaemon__specialWorkersPids = []

        with patch('exabox.core.AQResponse._stop_aqname_sync_worker') as stop_aq_mock, \
             patch('exabox.core.AQResponse._stop_liveliness_worker') as stop_live_mock, \
             patch('exabox.agent.Agent.ebGetDefaultDB') as get_db_mock, \
             patch('exabox.agent.Agent.time.sleep', return_value=None):
            fake_db = MagicMock()
            fake_db.mGetSpecialWorkerPIDs.return_value = {}
            get_db_mock.return_value = fake_db
            agent.mAgent_Stop()

        stop_aq_mock.assert_called_once()
        stop_live_mock.assert_called_once()
        agent._ebAgentDaemon__restlistener.mStopRestListener.assert_called_once()
        agent._ebAgentDaemon__workerFactory.mShutdownFactory.assert_called_once()
        self.assertTrue(agent._ebAgentDaemon__stopped)

    def test_mAgent_Start_proxy_path_initializes_agent_state(self):
        agent = self._build_agent()
        agent._ebAgentDaemon__args_options = SimpleNamespace(proxy=True, nosupervisor=True, daemonize=False)
        agent._ebAgentDaemon__restlistener = None
        agent._ebAgentDaemon__agent_id = 'agent-1'

        class FakeContext(object):
            def mCheckConfigOption(self, key, default=None):
                if key == 'ociexacc':
                    return False
                if key == 'enable_pushstatus_support':
                    return False
                if key == 'backup_configuration_during_start':
                    return True
                if key == 'import_tabledata':
                    return False
                return default

            def mGetPropagateProcOptions(self):
                return []

            def mGetConfigOptions(self):
                return {}

            def mGetBasePath(self):
                return '/tmp'

        class FakeAgentInfo(object):
            def __init__(self, agent_id):
                self.agent_id = agent_id
                self.port = None

            def mSetPort(self, port):
                self.port = port

        fake_db = MagicMock()
        fake_db.mAgentStatus.return_value = None
        fake_db.mSelectAllFromRequestuuidtoExacloud.return_value = []

        fake_listener = MagicMock()

        from exabox.agent import Agent as AgentModule
        previous_shutdown = AgentModule.gGlobalShutdown
        AgentModule.gGlobalShutdown = False

        try:
            with patch('exabox.agent.Agent.get_gcontext', return_value=FakeContext()), \
                 patch.object(ebAgentDaemon, 'mCheckAgentState'), \
                 patch('exabox.agent.Agent.subprocess.run') as subprocess_run, \
                 patch('exabox.agent.Agent.ebGetDefaultDB', return_value=fake_db), \
                 patch('exabox.agent.Agent.ebRestListener', return_value=fake_listener), \
                 patch('exabox.agent.Agent.ebAgentInfo', side_effect=FakeAgentInfo), \
                 patch('exabox.agent.Agent.mBackupFile', return_value=False), \
                 patch.object(ebAgentDaemon, 'mAgent_Stop') as stop_mock:
                agent.mAgent_Start()

            agent._ebAgentDaemon__workerFactory.mInitFactory.assert_called_once()
            subprocess_run.assert_called()
            fake_db.mCreateAgentTable.assert_called_once()
            fake_db.mInsertAgent.assert_called_once()
            fake_db.mStartAgent.assert_called_once()
            fake_listener.mStartRestListener.assert_called_once()
            stop_mock.assert_called_once()
        finally:
            AgentModule.gGlobalShutdown = previous_shutdown

def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestAgentClasses("test_mAgent_Start"))
    suite.addTest(ebTestAgentClasses("test_mAgent_Start_triggers_sync_workers"))
    suite.addTest(ebTestAgentClasses("test_mAgent_Stop_triggers_sync_shutdown"))
    suite.addTest(ebTestAgentClasses("test_mAgentForceKill"))
    suite.addTest(ebTestAgentClasses("test_mReturnSystemResourceUsage"))
    #suite.addTest(ebTestAgentClasses("test_getResponseFromExacloud")) Proxy code test not required
    suite.addTest(ebTestAgentClasses("test_dispatchHTTPPostReqToWorker"))
    suite.addTest(ebTestAgentClasses("test_do_JSON"))
    suite.addTest(ebTestAgentClasses("test_mRefreshMock"))
    suite.addTest(ebTestAgentClasses("test_mLoadAgentFromDB"))
    suite.addTest(ebTestAgentClasses("test_mHandleRequest"))
    suite.addTest(ebTestAgentClasses("test_isAdditionalWorkerAllowed"))
    suite.addTest(ebTestAgentClasses("test_dispatchJobToWorker"))
    suite.addTest(ebTestAgentClasses("test_WriteResponse"))
    suite.addTest(ebTestAgentClasses("test_exaproxyWriteResponse"))
    suite.addTest(ebTestAgentClasses("test_mShowStatus"))
    suite.addTest(ebTestAgentClasses("test_mUpdateScheduleInfo"))
    suite.addTest(ebTestAgentClasses("test_mScheduleRequest"))
    suite.addTest(ebTestAgentClasses("test_mScheduleGenericRequest"))
    suite.addTest(ebTestAgentClasses("test_mCLURequest"))
    suite.addTest(ebTestAgentClasses("test_mExaKmsRequest"))
    suite.addTest(ebTestAgentClasses("test_mOCIRegionUpdater"))
    suite.addTest(ebTestAgentClasses("test_mXmlGeneration"))
    suite.addTest(ebTestAgentClasses("test_mVMRequest"))
    suite.addTest(ebTestAgentClasses("test_mMonitor"))
    suite.addTest(ebTestAgentClasses("test_mValidatePath"))
    suite.addTest(ebTestAgentClasses("test_mAgentHome"))
    suite.addTest(ebTestAgentClasses("test_mAgentOedaDiags"))
    suite.addTest(ebTestAgentClasses("test_mAgentVersion"))
    suite.addTest(ebTestAgentClasses("test_mAgentTestPage"))
    suite.addTest(ebTestAgentClasses("test_mAgentWorkers"))
    suite.addTest(ebTestAgentClasses("test_mBuildChecksums"))
    suite.addTest(ebTestAgentClasses("test_mAgentPortal"))
    suite.addTest(ebTestAgentClasses("test_mAgentCmdRequest"))
    suite.addTest(ebTestAgentClasses("test_mHardwareInfo"))
    suite.addTest(ebTestAgentClasses("test_mBDS"))
    suite.addTest(ebTestAgentClasses("test_mAgentLogDownload"))
    suite.addTest(ebTestAgentClasses("test_mAgentFetchLog"))
    suite.addTest(ebTestAgentClasses("test_mWorkerStatus"))
    suite.addTest(ebTestAgentClasses("test_mCheckAgentState"))
    suite.addTest(ebTestAgentClasses("test_mProcessSOPRequest"))
    suite.addTest(ebTestAgentClasses("test_mValidateNetworkInfoPayload"))
    suite.addTest(ebTestAgentClasses("test_mFetchNetworkInfoRequest"))
    suite.addTest(ebTestAgentClasses("test_mBMRequest"))
    suite.addTest(ebTestAgentClasses("test_mJsonDispatchRequest"))
    suite.addTest(ebTestAgentClasses("test_mEDVManagement"))
    suite.addTest(ebTestAgentClasses("test_mAgentCluster"))
    suite.addTest(ebTestAgentClasses("test_mAgentWWWContent"))
    suite.addTest(ebTestAgentClasses("test_mAgentRequest"))
    suite.addTest(ebTestAgentClasses("test_mAtpGetFile"))
    suite.addTest(ebTestAgentClasses("test_mCheckOpctlStatus"))
    suite.addTest(ebTestAgentClasses("test_mAgentOedaLogs"))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
