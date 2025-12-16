#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/agent/tests_agent_classes.py /main/10 2025/07/04 06:37:53 aypaul Exp $
#
# tests_agent_classes.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_agent_classes.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
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
import logging
import shutil
import uuid
import copy
import posix
import errno
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.core.DBStore import ebGetDefaultDB
from exabox.agent.Agent import ebRestHttpListener, ebAgentInfo, dispatchJobToWorker, isAdditionalWorkerAllowed, ebScheduleInfo, ebAgentDaemon,\
ebSetDefaultAgent, ebSetAgentInfo
from exabox.log.LogMgr import ebLogInfo
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

    @patch('exabox.proxy.router.Router.mRegisterECInstance')
    @patch('exabox.proxy.router.Router.mDeregisterECInstance')
    @patch('exabox.proxy.router.Router.mUpdateECInstance')
    def test_mHandleECInstance_mHeartbeatECInstance(self, mock_router_register, mock_router_deregister, mock_router_update):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebRestHttpListener.mHandleECInstance_mHeartbeatECInstance")

        _server_class = ebRestHttpListener(aConfig=None, aRouterInstance=Router())
        _resp = {}
        _server_class.mHandleECInstance({}, _resp)
        self.assertEqual(_resp["success"], "False")

        _resp = {}
        _server_class.mHandleECInstance({"op":"mock_op"}, _resp)
        self.assertEqual(_resp["success"], "False")
        _params = {"op":"register", "host":"mockhost", "port":"mockport", "version":"mockversion", "request_type":"mock_req_type",\
                   "auth_key":"mock_auth_key", "oeda_version":"mock_oeda_version", "key":"mock_key", "value":"mockvalue"}
        _server_class.mHandleECInstance(_params, _resp)
        _params["op"] = "deregister"
        _server_class.mHandleECInstance(_params, _resp)
        _params["op"] = "update"
        _server_class.mHandleECInstance(_params, _resp)
        _server_class.mHeartbeatECInstance({}, {})
        ebLogInfo("test on ebRestHttpListener.mHandleECInstance_mHeartbeatECInstance succeeded.")

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
        with patch('os.stat'),\
             patch('os.path.join'),\
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
        with patch('os.stat'),\
             patch('os.path.join'),\
             patch('os.listdir', return_value=["logile1", "logfile2"]),\
             patch('os.path.isfile', side_effect=Exception("mock file error")):
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

        _server_class = ebRestHttpListener(aConfig=None)
        _server_class.mVMRequest(None, {})
        _server_class.mVMRequest({"hostname":"val1"}, {})
        
        with patch('exabox.agent.ebJobRequest.ebJobRequest.mRegister') as mock1,\
             patch('exabox.agent.Agent.dispatchJobToWorker', return_value=True) as mock2:
             _server_class.mVMRequest({"hostname":"dummyhostname", "cmd":"start"}, {})
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

        _nodes = ["nodesvalue"]
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
        with patch('exabox.ovm.opctlMgr.ExaCSExacloudWrapper.check_status_for_idemtoken', return_value=None):
            _response = _server_class.mCheckOpctlStatus(body, params, db, response)

        body = ["mockdata1","mockdata2","mockdata3","mockdata4","mockdata5",f"'idemtoken': '{uuid.uuid1()}'","mockdata7","mockdata8","mockdata9","mockdata10","mockdata11"]
        params = []
        db = None
        response = {}
        opctljobreq = ebJobRequest("mockcmd.opctl", {})
        opctljobreq.mSetBody({"bodykey":"bodyvalue"})
        opctljobreq.mSetError("mockerror")
        with patch('exabox.ovm.opctlMgr.ExaCSExacloudWrapper.check_status_for_idemtoken', return_value=opctljobreq):
            _response = _server_class.mCheckOpctlStatus(body, params, db, response)
            self.assertEqual(_response["body"],json.dumps({"bodykey":"bodyvalue"}))
            self.assertEqual(_response["success"], "False")

        body = ["mockdata1","mockdata2","mockdata3","mockdata4","mockdata5",f"'idemtoken': '{uuid.uuid1()}'","mockdata7","mockdata8","mockdata9","mockdata10","mockdata11"]
        params = {"uuid": f"{uuid.uuid1()}"}
        db = None
        response = {}
        with patch('exabox.ovm.opctlMgr.ExaCSExacloudWrapper.check_status_for_idemtoken', side_effect=Exception("Status check exception")):
            _response = _server_class.mCheckOpctlStatus(body, params, db, response)
        
        ebLogInfo("Unit test on ebRestHttpListener.mCheckOpctlStatus completed successfully.")

def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestAgentClasses("test_mAgent_Start"))
    suite.addTest(ebTestAgentClasses("test_mAgentForceKill"))
    suite.addTest(ebTestAgentClasses("test_mReturnSystemResourceUsage"))
    suite.addTest(ebTestAgentClasses("test_getResponseFromExacloud"))
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
    suite.addTest(ebTestAgentClasses("test_mHandleECInstance_mHeartbeatECInstance"))
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
