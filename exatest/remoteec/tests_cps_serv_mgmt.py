#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_cps_serv_mgmt.py /main/1 2025/09/15 20:32:51 hgaldame Exp $
#
# tests_cps_serv_mgmt.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cps_serv_mgmt.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    09/11/25 - enh 38036854 - exacc gen 2| infra patching |
#                           enhance ecra remoteec command
#    hgaldame    09/11/25 - Creation
#
import os
import unittest
import uuid
import json
import socket
import io
import re
import traceback
import tempfile
import exabox.managment.src.CpsServMgmtEndpoint as endpoint_module
from datetime import datetime
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch, Mock, call, ANY
from urllib.error import HTTPError
from pathlib import Path
#from exabox.managment.src.CpsServMgmtEndpoint import CpsServMgmtEndpoint

class ebTestRemoteManagmentCpsServMgmtEndpoint(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(aGenerateRemoteEC=True)
        cls.log_dir = "log/threads"
        os.makedirs(cls.log_dir, exist_ok=True)

    def test_001_get_invalid_service(self):
        """
            Scenario: Execute an operation on service
            Given: An service and operation
            When: the operation should be apply on service
            Then: request should fail if operation or service are not valid
        """
        _list_arguments = [
            ("invalid_service","status"),
            ("nessusd", "invalid_op")
        ]
        for _service_name, _op_name in _list_arguments:
            msg= "process log from {0}: {1}".format(_service_name,_op_name)
            with self.subTest(msg, _service_name=_service_name, _op_name=_op_name):
                _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
                _args = {
                    "service_name": _service_name,
                    "op": _op_name
                }
                _endpoint = endpoint_module.CpsServMgmtEndpoint(_args, _args, {}, _shared)
                _endpoint.mGet()
                _http_status =  _endpoint.mGetResponse()['status']
                self.assertEqual(_http_status, 500)
        
    def test_002_get_service(self):
        """
             Scenario: Execute an operation on service
            Given: An service and operation 
                   and service is valid
                   and operation is valid
            When: the operation should be apply on service
            Then: request should contain the result operation over the serviced
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _args = {
            "service_name": "nessusd",
            "op": "status"
            }
        _endpoint = endpoint_module.CpsServMgmtEndpoint(_args, _args, {}, _shared)
        _mockAttrs = { "mGetExacloudConfigValue.return_value": None}
        _mockConfig = Mock(**_mockAttrs)
        cps_localhost="cps01localhost"
        _mock_result = (0, io.StringIO("sysout"), io.StringIO("syserr"))
        with patch('exabox.managment.src.CpsServMgmtEndpoint.CpsServMgmtEndpoint.mGetConfig', return_value=_mockConfig),\
            patch("exabox.managment.src.utils.CpsExaccUtils.mGetLocalHostname", return_value=cps_localhost),\
            patch.object(endpoint_module, "mExecuteCmdByHost") as _spy_method:
            _spy_method.side_effect = [_mock_result, _mock_result]
            _endpoint.mGet()
            _http_status =  _endpoint.mGetResponse()['status']
            self.assertEqual(_http_status, 200)
            calls = [call(ANY, "/usr/bin/sudo -n /usr/bin/ls -l /etc/keepalived/MASTER", None, ANY),
                     call(ANY, "/usr/bin/sudo -n /usr/bin/systemctl status nessusd", None, ANY) 
                     ]
            _spy_method.assert_has_calls(calls)
    
    def test_003_deploy_handler(self):
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _test_task = "dbgiMetadata_test"
        _args = {
            "name": _test_task,
            "op": "execute"
        }
        _install_dir_mock = "/opt/oci/exacc"
        _token_path_mock = "/opt/oci/config_bundle/ocpsSetup.json"
        _configValues = lambda _arg : _install_dir_mock if _arg == "install_dir" else _token_path_mock
        _mockAttrs = { "mGetConfigValue.side_effect": _configValues}
        _mockConfig = Mock(**_mockAttrs)
        _endpoint = endpoint_module.CpsServMgmtEndpoint(_args, _args, {}, _shared)
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_path = os.path.abspath(os.path.join(self.log_dir, "test_deploy_mgmt_{0}.log".format(_process_id )))
        if os.path.exists(_log_path):
            os.unlink(_log_path)
        with patch('exabox.managment.src.CpsServMgmtEndpoint.CpsServMgmtEndpoint.mGetConfig', return_value=_mockConfig),\
            patch.object(_endpoint, "mBashExecution") as _spy_method:
            _spy_method.return_value = (0, io.StringIO("sysout"), io.StringIO(""))
            _return_code = _endpoint.mAsyncDeployHandlermDeployHandler(_log_path, _process_id, "" )
            print(_return_code)
            self.assertEqual(_return_code, 0)
            _spy_method.assert_called_once_with(['/usr/bin/sudo', '-n', '/opt/oci/exacc/deployer/ocps-full/cps-exacc-dpy', '-t', '/opt/oci/config_bundle/ocpsSetup.json', '--module', 'scanplatform', '--step', 'deploy_scanner'], aRedirect=ANY)


if __name__ == '__main__':
    unittest.main(warnings='ignore')
