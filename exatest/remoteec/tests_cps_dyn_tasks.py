#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_cps_dyn_tasks.py /main/4 2023/01/30 10:31:29 hgaldame Exp $
#
# tests_cps_dyn_tasks.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_cps_dyn_tasks.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    01/25/23 - 35011646 - exacc cps sw/os upgrade v2: : dynamic
#                           tasks/one_off bundle ecra sending incorrect file
#                           name to cps
#                           /opt/oci/exacc/dyntasks/signing/pre_cpssw_ecs_22.3.1.0.0.tgz.tgz
#    hgaldame    08/03/22 - 34457946 - oci/exacc: add new parameter for send
#                           tgz file on dynamic tasks remote manager endpoint
#    hgaldame    07/26/22 - 34352482 - cps sw v2 - make sure that all logs
#                           during sw upgrade goes to the same path at cps
#    hgaldame    06/02/22 - 34237258 - oci/exacc: implement remote manager
#                           endpoint for execute dynamic tasks for cps sw/os
#                           upgrade
#    hgaldame    06/02/22 - Creation
#

import base64
import tempfile
import os
import unittest
import uuid
import json
import socket
import io
import traceback
from datetime import datetime
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.managment.src.CpsDynamicTasksEndpoint import CpsDynamicTasksEndpoint
from unittest.mock import patch, Mock, mock_open, call
from urllib.error import HTTPError
from exabox.network.HTTPSHelper import ebResponse

class ebTestRemoteManagmentCpsDynamicTasks(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)
        self.repository_dir = None
        self.bundle_dir = None
        self.log_dir = "log/threads"
        os.makedirs(self.log_dir, exist_ok=True)
        self.cps_dir = "dyntasks"

    def mGetRepositoryDir(self):
        if not self.repository_dir:
            self.repository_dir = os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)
            os.makedirs(self.repository_dir, mode = 0o777, exist_ok = True)
        return self.repository_dir
    
    def mGetBundleDir(self):
        if not self.bundle_dir:
            self.bundle_dir = os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir, "bundles")
            os.makedirs(self.bundle_dir, mode = 0o777, exist_ok = True)
        return self.bundle_dir
        
    def mGetMockStatusTask(self, aName):
        _currentTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S+%f')
        _test_status = {
            "RunStatus": "Success",
            "Version": "22.2.1",
            "name": aName,
            "Date": _currentTime,
            "log": "/opt/oci/exacc/dyntasks/exectasks/{0}/trace_log/trace.log".format(aName)
            }
        return _test_status

    def mGetMockStatuAsync(self):
        _uuid = str(uuid.uuid1(clock_seq=1))
        _test_status = {
            "text": {
                "id": _uuid,
                "reqtype": "async call"
                },
                "error": "",
                "http_status": 200,
                "ctype": "application/json"
        }
        return json.dumps(_test_status)

    def mGetMockEcraToken(self):
        _test_token = {
            "install_dir": "/opt/oci/exacc",
            "servers": [
                {
                    "hostname": "localhost",
                }
            ],
            "linux_users": {
                "installation": "ecra"
            },
            "linux_groups": {
                "installation": "dba"
            }

        }
        return _test_token


    def test_001_get_local_hostname(self):
        """
            Scenario: Execute task
            Given a task name
            When there is a request for execute the task
            Then response should include async response detail
        """
        self.assertEqual(CpsDynamicTasksEndpoint.mGetLocalHostname(), socket.gethostname().split('.')[0])

    def test_002_is_localhost(self):
        """
            Scenario: Check if hostname is localhost
            Given a hostname
            When is required to check provided hostname is localhost
            Then return value should be True
        """
        self.assertTrue(CpsDynamicTasksEndpoint.mIsLocalHost(socket.gethostname().split('.')[0]))

    def test_003_locad_ecra_token_info(self):
        """   
        Scenario: Load Ecra token information
        When is required to load the information of ecra
        Then return value should include all the information of ecra token
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _ecra_token_path = os.path.join(self.mGetRepositoryDir(), "test_ocpsSetup.json")
        if os.path.exists(_ecra_token_path):
            os.unlink(_ecra_token_path)
        with open(_ecra_token_path, "w") as _json:
            json.dump(self.mGetMockEcraToken(), _json)
        _mockAttrs = { "mGetConfigValue.return_value": _ecra_token_path}
        _mockConfig = Mock(**_mockAttrs)
        endpoint = CpsDynamicTasksEndpoint("", "", {}, _shared)

        with patch('exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint.mGetConfig', return_value=_mockConfig):
            _tokenJson, _error_msg = endpoint.mLoadEcraToken()
            self.assertIsNotNone(_tokenJson)
            self.assertIsNone(_error_msg)
            _cps_user = endpoint.mGetCpsUser()
            self.assertEqual(self.mGetMockEcraToken()["linux_users"]["installation"],_cps_user)
            _cps_group = endpoint.mGetCpsGroup()
            self.assertEqual(self.mGetMockEcraToken()["linux_groups"]["installation"], _cps_group)
            _cps_install_dir =  endpoint.mGetBaseCpsWaInstallDir()
            self.assertTrue(_cps_install_dir.startswith(self.mGetMockEcraToken()["install_dir"]))

        if os.path.exists(_ecra_token_path):
            os.unlink(_ecra_token_path)


    def test_004_local_execute_async_task(self):
        """
            Scenario: Execute task on localhost in async form
            Given a task name
            When there is a request for execute the task
            Then response should include async response detail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        _cmd_result_gen = lambda *args, **kwargs : (0, None, None)
        base_pkg = "exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint"
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_path = os.path.abspath(os.path.join(self.log_dir, "test_mgmt_{0}.log".format(_process_id )))
        if os.path.exists(_log_path):
            os.unlink(_log_path)
        with patch('exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint.mGetBaseCpsWaInstallDir', return_value=os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)):
            with patch('os.path.exists', return_value=True):
                with patch('exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint.mFindFileByHost', return_value=True):
                    with patch('exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint.mBashExecution', side_effect=_cmd_result_gen), \
                            patch(f'{base_pkg}.mIsValidBundleFromPayload',return_value=True):
                        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
                        _return_code = _endpoint.mAsyncmExecuteDynamicTask(_log_path,_process_id, "" )
                        self.assertEqual(_return_code, 0)
        if os.path.exists(_log_path):
            os.unlink(_log_path)

    def test_005_remote_execute_async_task(self):
        """
            Scenario: Execute task on remote cps host in async form
            Given a task name and remote cps host
            When there is a request for execute the task
            Then return value should be success
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        _remoteCps = "hostcps02"
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_path = os.path.abspath(os.path.join(self.log_dir, "test_mgmt_{0}.log".format(_process_id )))
        _mockConfig = Mock(**{ "mGetExacloudConfigValue.return_value": _remoteCps})
        _mock_exabox_node = Mock(**{"mGetCmdExitStatus.return_value":0, "mExecuteCmd.return_value": (0, io.StringIO("sysout"),io.StringIO("syserr")), "mConnect.return_value": None, "mDisconnect.return_value": None})
        if os.path.exists(_log_path):
            os.unlink(_log_path)
        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
        base_pkg = "exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint"

        with patch(f'{base_pkg}.mGetBaseCpsWaInstallDir', return_value=os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)):
            with patch(f'{base_pkg}.mGetBaseCpsWaInstallDir', return_value=os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)):
                with patch('os.path.exists', return_value=True):
                    with patch(f'{base_pkg}.mGetCpsHostList', return_value=[_remoteCps]):
                        with patch(f'{base_pkg}.mFindFileByHost', return_value=True):
                            with patch(f'{base_pkg}.mGetConfig', return_value=_mockConfig):
                                with patch(f'{base_pkg}.mSyncFileToRemote', return_value=(True, None)):
                                    with patch(f'{base_pkg}.mBuildExaboxInstance', return_value=_mock_exabox_node), \
                                            patch(f'{base_pkg}.mIsValidBundleFromPayload',return_value=True):
                                        _return_code = _endpoint.mAsyncmExecuteDynamicTask(_log_path,_process_id, "" )
                                        self.assertEqual(_return_code, 0)
        if os.path.exists(_log_path):
            os.unlink(_log_path)

    def test_006_cleanup_async_task(self):
        """
            Scenario: Cleanup task in async form 
            Given a task name and remote cps host
            When there is a required cleanup the task
            Then return value should be success
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        _remoteCps = "hostcps02"
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_path = os.path.abspath(os.path.join(self.log_dir, "test_mgmt_{0}.log".format(_process_id )))
        _install_dir = os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)
        if os.path.exists(_log_path):
            os.unlink(_log_path)
        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
        _mock_result = (0, io.StringIO("sysout"),io.StringIO("syserr"))
        base_pkg = "exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint"
        with patch(f'{base_pkg}.mGetBaseCpsWaInstallDir', side_effect =[_install_dir, _install_dir, _install_dir]):
            with patch(f'{base_pkg}.mGetCpsHostList', return_value=[socket.gethostname().split('.')[0], _remoteCps]):
                with patch(f'{base_pkg}.mExecuteCmdByHost',  return_value = _mock_result):
                    _return_code = _endpoint.mAsyncmCleanupDynamicTask(_log_path, _process_id, "" )
                    self.assertEqual(_return_code, 0)
        if os.path.exists(_log_path):
            os.unlink(_log_path)

    def test_007_read_file_by_host(self):
        """
            Scenario: Read file by host
            Given a file path an hostname
            When there is required to read a file from host
            Then return value should include the file content
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
        _mock_exabox_node = Mock(**{"mGetCmdExitStatus.return_value":0, "mFileExists.return_value": True, "mReadFile.return_value" : b'contentdata',  "mConnect.return_value": None, "mDisconnect.return_value": None})
        _base_pkg = "exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint"
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='contentdata')) as m:
                with patch(f'{_base_pkg}.mGetCpsUser', return_value="cpsuser"):
                    with patch(f'{_base_pkg}.mBuildExaboxInstance', return_value=_mock_exabox_node):
                        for _host in [socket.gethostname().split('.')[0], "cpshost02"]:
                            _result, _content = _endpoint.mReadFileByHost("/path/to_file.txt", _host)
                            self.assertTrue(_result)
                            self.assertEqual(_content,'contentdata')

    def test_008_find_file_by_host(self):
        """
            Scenario: find file by host
            Given a file path an hostname
            When there is required to find a file on host
            Then return value should validate file existence
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
        _mock_exabox_node = Mock(**{"mFileExists.return_value": True,  "mConnect.return_value": None, "mDisconnect.return_value": None})
        _base_pkg = "exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint"
        with patch('os.path.exists', return_value=True):
            with patch(f'{_base_pkg}.mGetCpsUser', return_value="cpsuser"):
                with patch(f'{_base_pkg}.mBuildExaboxInstance', return_value=_mock_exabox_node):
                    for _host in [socket.gethostname().split('.')[0], "cpshost02"]:
                        _result = _endpoint.mFindFileByHost("/path/to_file.txt", _host)
                        self.assertTrue(_result)

    def test_009_sync_file_to_host(self):
        """
            Scenario: syncronize a file to  host
            Given a file path an hostname
            When there is required to syncronize a file on host
            Then return value should include the result of synchronization
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
        _base_packace = "exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint"
        with patch(f'{_base_packace}.mBashExecution', return_value=(0, io.StringIO("sysout"),io.StringIO("syserr"))):
            _result, _error_msg = _endpoint.mSyncFileToRemote("/path/source/to_file.txt", "/path/remote/to_file.txt","cpshost02")
            self.assertTrue(_result)
            self.assertIsNone(_error_msg)


    def test_010_get_status_task_request(self):
        """
            Scenario: Get status from task
            Given a task name
            When there is a request for get status of a task
            Then response should include the status of a task
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "trace": "n"
        }
        _result_read_mock = [(True, json.dumps(self.mGetMockStatusTask(_test_task))),( True, "tracelogtestscontent")]
        with patch('exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint.mGetBaseCpsWaInstallDir', return_value=os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)):
            with patch('exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint.mReadFileByHost', side_effect= _result_read_mock):
                _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
                _endpoint.mGet()
                _http_status = _endpoint.mGetResponse()['status']
                _http_text = _endpoint.mGetResponse()['text']
                self.assertEqual(_http_status, 200)
                self.assertIn(_test_task, _http_text)
                _first_item = _http_text[_test_task][0]
                _, _content_first_entry = next(iter(_first_item.items()))               
                self.assertIn("output", _content_first_entry)
                self.assertIn("trace", _content_first_entry)

    def test_011_execute_task_request(self):
        """
            Scenario: Execute task
            Given a task name
            When there is a request for execute the task
            Then response should include async response detail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        with patch('exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint.mGetBaseCpsWaInstallDir', return_value=os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)):
            with patch('os.path.exists', return_value=True):
                with patch('exabox.managment.src.AsyncTrackEndpoint.AsyncTrackEndpoint.mCreatePythonProcess', return_value=self.mGetMockStatuAsync()):
                    _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
                    _endpoint.mPost()
                    _http_status = _endpoint.mGetResponse()['status']
                    self.assertEqual(_http_status, 200)


    def test_012_cleanup_task_request(self):
        """
            Scenario: Cleanup task
            Given a task name
            When there is a request for execute the task
            Then response should include async response detail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "cleanup"
        }
        with patch('exabox.managment.src.AsyncTrackEndpoint.AsyncTrackEndpoint.mCreatePythonProcess', return_value=self.mGetMockStatuAsync()):
            _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
            _endpoint.mPost()
            _http_status = _endpoint.mGetResponse()['status']
            self.assertEqual(_http_status, 200)

    def test_013_procces_log_on_finish(self):
        """
              Scenario: Process log file when remote manager request is complete
              Given a remote manager request id
              When the request is complete
              Then log files should be processed
        """
        _process_id = str(uuid.uuid1(clock_seq=1))
        _args = [{"aId": _process_id, "aLogType": "cpssw"}]
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
        base_pkg = "exabox.managment.src.CpsDynamicTasksEndpoint"
        with patch(f'{base_pkg}.mProcessCpsLog', return_value=None) as _spy_method:
            try:
                _endpoint.mProcessCpsLogOnFinish(*_args)
            except Exception:
                self.fail("mProcessCpsLog() should not raise exception {0}".format(traceback.format_exc()))
            _spy_method.assert_called_once_with(_endpoint, _process_id,  aLogType="cpssw",  aOptionalDirDict=None, aTargetDirName=None )

    def test_014_valid_bundle_from_payload(self):
        """
            Scenario: Validate bundle file from payload
            Given a payload for with a valid bundle
            When there is a request for execute the task
            Then return value should be success
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_path = os.path.abspath(os.path.join(self.log_dir, "test_mgmt_{0}.log".format(_process_id )))
        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
        base_pkg = "exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint"
        local_host= socket.gethostname().split('.')[0]
        _mock_result = (0, io.StringIO("sysout"), io.StringIO("syserr"))
        _base_dyntasks_dir = os.path.join(self.mGetUtil().mGetOutputDir(),"dyntasks")
        _bundle_path = os.path.join(_base_dyntasks_dir,"bundles", "{0}.tgz".format(_test_task) )
        _signed_based_dir = os.path.join(_base_dyntasks_dir, "signing")
        _signed_bundle_path = os.path.join(_signed_based_dir, "{0}.tgz".format(_test_task))
        _signed_temp_dir = os.path.join(_signed_based_dir,_test_task)
        _cps_user = "cpsuser"
        _cps_group = "dba"
        with tempfile.TemporaryFile() as _log_path:
            with patch.object(_endpoint, "mExecuteCmdByHost") as _spy_method:
                _spy_method.return_value = _mock_result
                with patch(f'{base_pkg}.mGetBaseCpsWaInstallDir', return_value=os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)), \
                        patch(f'{base_pkg}.mGetCpsUser', return_value=_cps_user), \
                        patch(f'{base_pkg}.mGetCpsGroup', return_value=_cps_group), \
                        patch('os.path.exists', side_effect=[False, True, True, True]), \
                        patch(f'{base_pkg}.mAsyncLog',  return_value = None), \
                        patch('builtins.open', mock_open(read_data='contentdata')):
                    _mock_file = base64.b64encode(b'contentfile\n')
                    _return_code = _endpoint.mIsValidBundleFromPayload(_log_path,_process_id, _mock_file,_test_task)
                    self.assertTrue(_return_code)
                calls = [
                    call(f'/usr/bin/sudo -n /usr/bin/mkdir -p {_signed_based_dir}', _log_path, local_host),
                    call(f'/usr/bin/sudo -n /usr/bin/chown {_cps_user}:{_cps_group} -R {_base_dyntasks_dir}',
                         _log_path, local_host),
                    call(f'/usr/bin/sudo -n /usr/bin/rm -f {_bundle_path}', _log_path ,  local_host),
                    call(f'/usr/bin/sudo -n /usr/bin/rm -rf {_signed_bundle_path}', _log_path, local_host),
                    call(f'/usr/bin/rm -rf {_signed_temp_dir} ', _log_path, local_host),
                    call(f'/usr/bin/mkdir -p {_signed_temp_dir} ', _log_path, local_host),
                    call(f'/usr/bin/tar xzf {_signed_bundle_path} -C {_signed_temp_dir}',
                         _log_path, local_host),
                    call(f'/usr/bin/openssl dgst -sha256 -verify {_signed_temp_dir}/oracle.Java'
                         f' -signature {_signed_temp_dir}/{_test_task}.dat {_signed_temp_dir}/{_test_task}.tgz',
                         _log_path, local_host),
                    call(f'/usr/bin/mv {_signed_temp_dir}/{_test_task}.tgz {_bundle_path} ', _log_path, local_host)
                ]
                _spy_method.assert_has_calls(calls)

    def test_015_not_valid_sign_from_payload(self):
        """
            Scenario: Reject bundle file from payload
            Given a payload for with a bundle with not valid sign
            When there is a request for execute the task
            Then return value should be false
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_path = os.path.abspath(os.path.join(self.log_dir, "test_mgmt_{0}.log".format(_process_id )))
        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
        base_pkg = "exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint"
        local_host= socket.gethostname().split('.')[0]
        _mock_result = (0, io.StringIO("sysout"), io.StringIO("syserr"))
        _base_dyntasks_dir = os.path.join(self.mGetUtil().mGetOutputDir(),"dyntasks")
        _bundle_path = os.path.join(_base_dyntasks_dir,"bundles", "{0}.tgz".format(_test_task) )
        _signed_based_dir = os.path.join(_base_dyntasks_dir, "signing")
        _signed_bundle_path = os.path.join(_signed_based_dir, "{0}.tgz".format(_test_task))
        _signed_temp_dir = os.path.join(_signed_based_dir,_test_task)

        _log_path_file= os.path.abspath(os.path.join(self.log_dir, "test_mgmt_{0}.log".format(_process_id )))
        if os.path.exists(_log_path_file):
            os.unlink(_log_path_file)
        with patch('sys.stdout', new_callable=io.StringIO) as stdout:
            with open(_log_path_file, "w+") as _log_path:
                with patch.object(_endpoint, "mExecuteCmdByHost") as _spy_method:
                    _mock_list = [ (0, io.StringIO("sysout"), io.StringIO("syserr")) for i in range(5)]
                    _mock_list.append((1, io.StringIO("sysout"), io.StringIO("syserr")))
                    _spy_method.side_effect = _mock_list

                    with patch(f'{base_pkg}.mGetBaseCpsWaInstallDir', return_value=os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)), \
                            patch('os.path.exists', return_value=True), \
                            patch('builtins.open', mock_open(read_data='contentdata')):
                        _mock_file = base64.b64encode(b'contentfile\n')
                        _return_code = _endpoint.mIsValidBundleFromPayload(_log_path,_process_id, _mock_file,_test_task)
                        _lines_from_log = _log_path.readlines()
                        self.assertFalse(_return_code)
                    calls = [
                        call(f'/usr/bin/tar xzf {_signed_bundle_path} -C {_signed_temp_dir}',
                             _log_path, local_host),
                        call(f'/usr/bin/openssl dgst -sha256 -verify {_signed_temp_dir}/oracle.Java'
                             f' -signature {_signed_temp_dir}/{_test_task}.dat {_signed_temp_dir}/{_test_task}.tgz',
                             _log_path, local_host)
                    ]
                    _spy_method.assert_has_calls(calls)
                    with self.assertRaises(AssertionError):
                        non_expectected_calls =[
                        call(f'/usr/bin/mv {_signed_temp_dir}/{_test_task}.tgz {_bundle_path} ', _log_path, local_host)
                        ]
                        _spy_method.assert_has_calls(non_expectected_calls)
            self.assertIn("Can not verify digital sign", stdout.getvalue())
        if os.path.exists(_log_path_file):
            os.unlink(_log_path_file)

    def test_016_valid_bundle_from_payload_tgz(self):
        """
            Scenario: Validate bundle file from payload
            Given a payload for with a valid bundle 
            and task name with tgz extension
            When there is a request for execute the task
            Then return value should be success
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": "{0}.tgz".format(_test_task),
            "op": "execute"
        }
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_path = os.path.abspath(os.path.join(self.log_dir, "test_mgmt_{0}.log".format(_process_id )))
        _endpoint = CpsDynamicTasksEndpoint(_args, _args, {}, _shared)
        base_pkg = "exabox.managment.src.CpsDynamicTasksEndpoint.CpsDynamicTasksEndpoint"
        local_host= socket.gethostname().split('.')[0]
        _mock_result = (0, io.StringIO("sysout"), io.StringIO("syserr"))
        _base_dyntasks_dir = os.path.join(self.mGetUtil().mGetOutputDir(),"dyntasks")
        _bundle_path = os.path.join(_base_dyntasks_dir,"bundles", "{0}.tgz".format(_test_task) )
        _signed_based_dir = os.path.join(_base_dyntasks_dir, "signing")
        _signed_bundle_path = os.path.join(_signed_based_dir, "{0}.tgz".format(_test_task))
        _signed_temp_dir = os.path.join(_signed_based_dir,_test_task)
        _cps_user = "cpsuser"
        _cps_group = "dba"
        with tempfile.TemporaryFile() as _log_path:
            with patch.object(_endpoint, "mExecuteCmdByHost") as _spy_method:
                _spy_method.return_value = _mock_result
                with patch(f'{base_pkg}.mGetBaseCpsWaInstallDir', return_value=os.path.join(self.mGetUtil().mGetOutputDir(), self.cps_dir)), \
                        patch(f'{base_pkg}.mGetCpsUser', return_value=_cps_user), \
                        patch(f'{base_pkg}.mGetCpsGroup', return_value=_cps_group), \
                        patch('os.path.exists', side_effect=[False, True, True, True]), \
                        patch(f'{base_pkg}.mAsyncLog',  return_value = None), \
                        patch('builtins.open', mock_open(read_data='contentdata')):
                    _mock_file = base64.b64encode(b'contentfile\n')
                    _return_code = _endpoint.mIsValidBundleFromPayload(_log_path,_process_id, _mock_file,_test_task)
                    self.assertTrue(_return_code)
                calls = [
                    call(f'/usr/bin/sudo -n /usr/bin/mkdir -p {_signed_based_dir}', _log_path, local_host),
                    call(f'/usr/bin/sudo -n /usr/bin/chown {_cps_user}:{_cps_group} -R {_base_dyntasks_dir}',
                         _log_path, local_host),
                    call(f'/usr/bin/sudo -n /usr/bin/rm -f {_bundle_path}', _log_path ,  local_host),
                    call(f'/usr/bin/sudo -n /usr/bin/rm -rf {_signed_bundle_path}', _log_path, local_host),
                    call(f'/usr/bin/rm -rf {_signed_temp_dir} ', _log_path, local_host),
                    call(f'/usr/bin/mkdir -p {_signed_temp_dir} ', _log_path, local_host),
                    call(f'/usr/bin/tar xzf {_signed_bundle_path} -C {_signed_temp_dir}',
                         _log_path, local_host),
                    call(f'/usr/bin/openssl dgst -sha256 -verify {_signed_temp_dir}/oracle.Java'
                         f' -signature {_signed_temp_dir}/{_test_task}.dat {_signed_temp_dir}/{_test_task}.tgz',
                         _log_path, local_host),
                    call(f'/usr/bin/mv {_signed_temp_dir}/{_test_task}.tgz {_bundle_path} ', _log_path, local_host)
                ]
                _spy_method.assert_has_calls(calls)
if __name__ == '__main__':
    unittest.main(warnings='ignore')
