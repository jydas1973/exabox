#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/opctl/tests_opctlExaCS.py /main/1 2026/01/28 03:29:47 nisrikan Exp $
#
# tests_opctlExaCS.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_opctlExaCS.py - Operator Access Control test cases for ExaCS
#
#    DESCRIPTION
#      Operator Access Control test cases for ExaCS
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    nisrikan     12/08/25 - Creation based on tests_dactl.py
#    cline        01/21/26 - Rewrote based on changes in opctlExaCSMgr.py and fixed compilation issues
#

from unittest.mock import patch, MagicMock
import unittest
from exabox.log.LogMgr import ebLogInfo
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_opctl import OpctlExaCSHandler
from exabox.ovm.opctlExaCSMgr import ExaCloudWrapper, ExaCSExacloudWrapper
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.core.Context import get_gcontext
import json
import os

# Update payloads to include new fields if necessary
PAYLOAD_INVALID_USER_CMD = {
    "resourceType": "cloudexadatainfrastructure",
    "idemtoken": "123",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]}
}

PAYLOAD_RESOURCE_TYPE_UNKNOWN = {
    "usercmd": "assign",
    "resourceType": "unknown",
    "idemtoken": "123",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]}
}

PAYLOAD_USER_CMD_UNKNOWN = {
    "usercmd": "unknown",
    "resourceType": "cloudexadatainfrastructure",
    "idemtoken": "123",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]}
}

PAYLOAD_INVALID_IDEMTOKEN = {
    "usercmd": "assign",
    "resourceType": "cloudexadatainfrastructure",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]}
}

PAYLOAD_INVALID_HOST_INFO = {
    "usercmd": "assign",
    "resourceType": "cloudexadatainfrastructure",
    "idemtoken": "123"
}

# Update VALID_PAYLOAD_ASSIGN if new fields are added
VALID_PAYLOAD_ASSIGN = {
    "usercmd": "assign",
    "resourceType": "cloudexadatainfrastructure",
    "idemtoken": "123",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]},
    "operation": "deploy",
    "assignInfo": {}
}

VALID_PAYLOAD_CREATE_USER = {
    "usercmd": "create_user",
    "resourceType": "cloudexadatainfrastructure",
    "idemtoken": "123",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]},
    "username": "testuser",
    "accessRequestId": "req123",
    "auditType": "type1",
    "publicKey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...",
    "acpRequestList": ["req1", "req2"],
    "rpmVersion": "1.0"
}

VALID_PAYLOAD_DELETE_USER = {
    "usercmd": "delete_user",
    "resourceType": "cloudexadatainfrastructure",
    "idemtoken": "123",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]},
    "username": "testuser",
    "rpmVersion": "1.0"
}

PAYLOAD_MISSING_OPERATION = {
    "usercmd": "assign",
    "resourceType": "cloudexadatainfrastructure",
    "idemtoken": "123",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]},
    "assignInfo": {}
}

PAYLOAD_INVALID_OPERATION = {
    "usercmd": "assign",
    "resourceType": "cloudexadatainfrastructure",
    "idemtoken": "123",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]},
    "operation": "invalid_op",
    "assignInfo": {}
}

PAYLOAD_COLLECT_DEBUG_LOG = {
    "usercmd": "assign",
    "resourceType": "cloudexadatainfrastructure",
    "idemtoken": "123",
    "hostInfo": {"dom0s": ["dom0host"], "cells": ["cellhost"]},
    "operation": "collectDebugLog",
    "assignInfo": {}
}

REMOTE_NODE_OUTPUT_JSON = {
    "idemtoken": "123", "status": "200", "output": None, "error": "some error",
    "remoteHostName": "host",
    "returnCode": "0",
    "logfileName": ["filename1", "filename2"]
}

class MockHostCommandClient:
    def __init__(self):
        self.command_outputs = dict()
        self.return_value = -1

    def add_command(self, cmd_starts_with, ret, stdout, stderr):
        if cmd_starts_with not in self.command_outputs:
            self.command_outputs[cmd_starts_with] = list()
        self.command_outputs[cmd_starts_with].append((ret, stdout, stderr))

    def reset(self):
        self.command_outputs = dict()

    def fake_exec_command(self, cmd, *args, **kwargs):
        stdin = MagicMock()
        stdout = MagicMock()
        stderr = MagicMock()
        return_val, stdout_str, stderr_str = (1, "", "Command not found")
        for stub_cmd, stub_cmd_info in self.command_outputs.items():
            if cmd.startswith(stub_cmd):
                if len(stub_cmd_info) > 1:
                    return_val, stdout_str, stderr_str = stub_cmd_info.pop(0)
                    break
                else:
                    return_val, stdout_str, stderr_str = stub_cmd_info[0]
                    break
        stdout.read.return_value = stdout_str.encode()
        stderr.read.return_value = stderr_str.encode()
        self.return_value = return_val
        return stdin, stdout, stderr

    def fake_return_value(self):
        return self.return_value

class ebTestOpctlExaCSHandler(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super(ebTestOpctlExaCSHandler, self).setUpClass()

    def test_invalid_user_cmd(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = PAYLOAD_INVALID_USER_CMD
        _handler = OpctlExaCSHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid payload, usercmd missing")

    def test_resource_type_unknown(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = PAYLOAD_RESOURCE_TYPE_UNKNOWN
        _handler = OpctlExaCSHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Unsupport exadata type. unknown is not supported")

    def test_user_cmd_unknown(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = PAYLOAD_USER_CMD_UNKNOWN
        _handler = OpctlExaCSHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], f"User command unknown is not supported")

    def test_invalid_idemtoken(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = PAYLOAD_INVALID_IDEMTOKEN
        _handler = OpctlExaCSHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertIn("Invalid payload, idemtoken missing", _result["errorMessage"])

    def test_invalid_host_info(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = PAYLOAD_INVALID_HOST_INFO
        _handler = OpctlExaCSHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid payload, hostInfo missing")

    @patch("exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper")
    def test_execute_cmd_assign_operation(self, mock_ExaCSExacloudWrapper):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = VALID_PAYLOAD_ASSIGN
        _handler = OpctlExaCSHandler(_options)

        mock_wrapper = mock_ExaCSExacloudWrapper.return_value
        mock_wrapper.execute_cmd.return_value = 0

        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertIn("status", _result)

    @patch("exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper")
    def test_execute_cmd_create_user(self, mock_ExaCSExacloudWrapper):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = VALID_PAYLOAD_CREATE_USER
        _handler = OpctlExaCSHandler(_options)

        mock_wrapper = mock_ExaCSExacloudWrapper.return_value
        mock_wrapper.execute_cmd.return_value = 0

        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertIn("status", _result)

    @patch("exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper")
    def test_execute_cmd_delete_user(self, mock_ExaCSExacloudWrapper):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = VALID_PAYLOAD_DELETE_USER
        _handler = OpctlExaCSHandler(_options)

        mock_wrapper = mock_ExaCSExacloudWrapper.return_value
        mock_wrapper.execute_cmd.return_value = 0

        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertIn("status", _result)

    def test_missing_create_user_fields(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        payload = VALID_PAYLOAD_CREATE_USER.copy()
        del payload["username"]
        _options.jsonconf = payload
        _handler = OpctlExaCSHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertIn("username required for create_user operation", _result["errorMessage"])

    def test_missing_delete_user_username(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        payload = VALID_PAYLOAD_DELETE_USER.copy()
        del payload["username"]
        _options.jsonconf = payload
        _handler = OpctlExaCSHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "username required for delete_user operation")

    def test_missing_operation_for_assign(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = PAYLOAD_MISSING_OPERATION
        _handler = OpctlExaCSHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "operation required for assign operation")

    def test_invalid_operation(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = PAYLOAD_INVALID_OPERATION
        _handler = OpctlExaCSHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid operation: invalid_op")

    @patch("exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper")
    def test_collect_debug_log(self, mock_ExaCSExacloudWrapper):
        _options = self.mGetContext().mGetArgsOptions()
        _options.unittest = True
        _options.jsonconf = PAYLOAD_COLLECT_DEBUG_LOG
        _handler = OpctlExaCSHandler(_options)

        mock_wrapper = mock_ExaCSExacloudWrapper.return_value
        mock_wrapper.execute_cmd.return_value = 0

        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertIn("status", _result)

class TestExaCloudWrapper(unittest.TestCase):
    def setUp(self):
        self.infra = "cloudexadatainfrastructure"
        self.requestObj = MagicMock()
        self.host_info = MagicMock()
        self.logger = "create_logger"
        self.options = MagicMock()
        self.options.unittest = True
        self.base_path = "/u01/.opctl/"
        self.patcher_gcontext = patch('exabox.ovm.opctlExaCSMgr.get_gcontext')
        self.mock_gcontext = self.patcher_gcontext.start()
        self.mock_gcontext.return_value = MagicMock()
        self.patcher_cluctrl = patch('exabox.ovm.opctlExaCSMgr.exaBoxCluCtrl')
        self.mock_cluctrl = self.patcher_cluctrl.start()
        self.mock_cluctrl.return_value = MagicMock()
        self.ebox = MagicMock()
        self.wrapper = ExaCloudWrapper(self.ebox, self.infra, self.requestObj, self.logger, self.options, self.base_path)

    def test_init(self):
        self.assertEqual(self.wrapper.infra_type, self.infra)
        self.assertEqual(self.wrapper.requestObj, self.requestObj)
        self.assertEqual(self.wrapper.options, self.options)
        self.assertEqual(self.wrapper.opctl_base_path, self.base_path)

    def test_set_infra_type_exacs(self):
        wrapper = ExaCloudWrapper.set_infra_type("cloudexadatainfrastructure")
        self.assertIsInstance(wrapper, ExaCSExacloudWrapper)

    def test_set_infra_type_other(self):
        wrapper = ExaCloudWrapper.set_infra_type("other")
        self.assertIsInstance(wrapper, ExaCloudWrapper)

# Update setUp to include any new initializations if necessary
class TestExaCSExacloudWrapper(unittest.TestCase):
    def setUp(self):
        self.infra = "cloudexadatainfrastructure"
        self.requestObj = MagicMock()
        self.logger = "create_logger"
        self.options = MagicMock()
        self.options.unittest = True
        self.host_info = {"dom0s": ["dom0host"], "cells": ["cellhost"]}
        self.patcher_cluctrl = patch('exabox.ovm.opctlExaCSMgr.exaBoxCluCtrl')
        self.mock_cluctrl = self.patcher_cluctrl.start()
        self.mock_cluctrl.return_value = MagicMock()
        self.ebox = MagicMock()
        self.wrapper = ExaCSExacloudWrapper(self.ebox, self.infra, self.requestObj, self.logger, self.options, self.host_info)
        self.wrapper.opctl_resource_path = "/tmp/test_resource"
        self.wrapper.opctl_base_path = "/u01/.opctl/"

    def test_init(self):
        self.assertEqual(self.wrapper.resource_type, self.infra)
        self.assertEqual(self.wrapper.opctl_exacs_base_path, "/u01/.opctl/")

    # Update test_execute_cmd_success to cover new functionality
    @patch("exabox.ovm.opctlExaCSMgr.get_gcontext")
    @patch("exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper.execute_local")
    def test_execute_cmd_success(self, mock_execute_local, mock_get_gcontext):
        mock_context = MagicMock()
        mock_exakms = MagicMock()
        mock_context.mGetExaKms.return_value = mock_exakms
        mock_exakms.mSearchExaKmsEntries.return_value = []
        mock_get_gcontext.return_value = mock_context

        mock_execute_local.return_value = (0, None, "output", "")

        self.options.jsonconf = VALID_PAYLOAD_ASSIGN
        self.wrapper.json_input = VALID_PAYLOAD_ASSIGN
        self.wrapper.execute_backend_script = MagicMock(return_value=(0, "output", ""))
        self.wrapper.get_status_for_idemtoken = MagicMock(return_value={"status": 200})
        self.wrapper.update_exacloud_db = MagicMock()
        self.wrapper.ebox.mCheckConfigOption.return_value = False
        rc = self.wrapper.execute_cmd()
        self.assertEqual(rc, 0)
        self.wrapper.update_exacloud_db.assert_called_with(200, {"status": 200}, aParams=None)
        # Add assertions for new functionality if applicable

    @patch("os.path.exists")
    def test_get_status_for_idemtoken(self, mock_exists):
        mock_exists.return_value = True
        idemtoken = "123"
        status_file_for_idemtoken = os.path.join(self.wrapper.backend_status_path, idemtoken, "status")
        with patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=json.dumps({"status": 200})) as mock_open:
            data = self.wrapper.get_status_for_idemtoken(idemtoken)
            mock_open.assert_called_once_with(status_file_for_idemtoken, 'r')
            self.assertEqual(data, {"status": 200})

    @patch("os.path.exists")
    def test_get_status_for_idemtoken_not_found(self, mock_exists):
        mock_exists.return_value = False
        idemtoken = "123"
        self.wrapper.backend_status_path = "/non/existent/path"
        data = self.wrapper.get_status_for_idemtoken(idemtoken)
        self.assertIsNone(data)

    def test_transform_host_info(self):
        host_info = {"dom0s": ["dom0_1", "dom0_2"], "cells": ["cell_1"]}
        self.wrapper.transform_host_info(host_info)
        expected = {
            "host_info": {
                "dom0_1": {"type": "dom0"},
                "dom0_2": {"type": "dom0"},
                "cell_1": {"type": "cell"}
            }
        }
        self.assertEqual(self.wrapper.host_info, expected)

    def test_transform_host_info_empty(self):
        host_info = {}
        self.wrapper.transform_host_info(host_info)
        self.assertEqual(self.wrapper.host_info, {"host_info": {}})

    @patch("exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper.execute_local")
    def test_execute_backend_script(self, mock_execute_local):
        backend_json_input = {"key": "value"}
        self.wrapper.json_input = {"idemtoken": "123"}
        self.wrapper.operation = "deploy"
        expected_cmd = f"{self.wrapper.backend_script_path} -i 123 -o deploy -j '{json.dumps(backend_json_input)}' -c '{json.dumps(self.wrapper.host_info)}' "
        mock_execute_local.return_value = (0, None, "out", "")
        return_code, out, error = self.wrapper.execute_backend_script(backend_json_input)
        mock_execute_local.assert_called_with(expected_cmd)
        self.assertEqual(return_code, 0)
        self.assertEqual(out, "out")
        self.assertEqual(error, "")

    @patch("exabox.ovm.opctlExaCSMgr.get_gcontext")
    @patch("exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper.execute_local")
    @patch("exabox.ovm.opctlExaCSMgr.ExaCSExacloudWrapper.enable_disable_exassh")
    def test_execute_cmd_failure(self, mock_enable_disable, mock_execute_local, mock_get_gcontext):
        mock_context = MagicMock()
        mock_get_gcontext.return_value = mock_context
        self.options.jsonconf = VALID_PAYLOAD_ASSIGN
        self.wrapper.json_input = VALID_PAYLOAD_ASSIGN
        self.wrapper.execute_backend_script = MagicMock(return_value=(1, "output", "error"))
        self.wrapper.get_status_for_idemtoken = MagicMock(return_value={"status": 500, "error_message": "failure"})
        self.wrapper.update_exacloud_db = MagicMock()
        rc = self.wrapper.execute_cmd()
        self.assertEqual(rc, 1)
        self.wrapper.update_exacloud_db.assert_called_with(500, {"status": 500, "error_message": "failure"}, aParams=None)
        mock_enable_disable.assert_not_called()

# Add more specific tests for other methods

if __name__ == '__main__':
    unittest.main()
