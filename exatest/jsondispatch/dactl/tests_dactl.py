#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/dactl/tests_dactl.py /main/2 2025/08/05 07:01:28 kkviswan Exp $
#
# tests_dactl.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_dactl.py - Delegation Access Control test cases
#
#    DESCRIPTION
#      Delegation Access Control test cases
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    kkviswan    07/23/25 - 38225214 - DELEGATION MANAGEMENT BACKEND
#                           INTEGRATION ISSUES ON EXADB-XS ENVIRONMENT
#    kkviswan    05/28/25 - 37928955 Delegation Management New ER
#    kkviswan    05/28/25 - Creation
#


import json
import unittest
import base64
from unittest.mock import patch, MagicMock
from exabox.log.LogMgr import ebLogInfo
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_dactl import DaCtlHandler


PAYLOAD_INVALID_COMMON_PARMS = {
    "commonParameters": None,
    "usercmd": "deploy"
}

PAYLOAD_INVALID_RESOURCE_TYPE = {
    "commonParameters": {},
    "usercmd": "deploy"
}

PAYLOAD_INVALID_IDEMTOKEN = {
    "commonParameters": {
        "resourceType": "exadbvmcluster",
        "dom0domUPairs": {"DOMU": ["sea200220exddu0101"]},
        "secretId": "ocid1.seckey.xxxx",
        "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64",
        "rpmParUrl": "http://somepar/supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
        "parUrl": "http://somepar/"
    },
    "usercmd": "deploy"
}

PAYLOAD_INVALID_DOM0DOMUPAIRS1 = {
    "commonParameters": {
        "resourceType": "exadbvmcluster",
        "idemtoken": "123",
        "dom0domUPairs": None,
        "secretId": "ocid1.seckey.xxxx",
        "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64",
        "rpmParUrl": "http://somepar/supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
        "parUrl": "http://somepar/"
    },
    "usercmd": "deploy"
}

PAYLOAD_INVALID_DOM0DOMUPAIRS2 = {
    "commonParameters": {
        "resourceType": "exadbvmcluster",
        "idemtoken": "123",
        "dom0domUPairs": "invalid dict",
        "secretId": "ocid1.seckey.xxxx",
        "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64",
        "rpmParUrl": "http://somepar/supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
        "parUrl": "http://somepar/"
    },
    "usercmd": "deploy"
}

PAYLOAD_INVALID_DOMU1 = {
    "commonParameters": {
        "resourceType": "exadbvmcluster",
        "idemtoken": "123",
        "dom0domUPairs": {"DOMU": None},
        "secretId": "ocid1.seckey.xxxx",
        "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64",
        "rpmParUrl": "http://somepar/supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
        "parUrl": "http://somepar/"
    },
    "usercmd": "deploy"
}

PAYLOAD_INVALID_DOMU2 = {
    "commonParameters": {
        "resourceType": "exadbvmcluster",
        "idemtoken": "123",
        "dom0domUPairs": {"DOMU": []},
        "secretId": "ocid1.seckey.xxxx",
        "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64",
        "rpmParUrl": "http://somepar/supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
        "parUrl": "http://somepar/"
    },
    "usercmd": "deploy"
}

PAYLOAD_INVALID_SECRETID = {
    "commonParameters": {
        "resourceType": "exadbvmcluster",
        "idemtoken": "123",
        "dom0domUPairs": {"DOMU": ["sea200220exddu0101"]},
        "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64",
        "rpmParUrl": "http://somepar/supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
        "parUrl": "http://somepar/"
    },
    "usercmd": "deploy"
}

PAYLOAD_INVALID_RPMVERSION = {
    "commonParameters": {
        "resourceType": "exadbvmcluster",
        "idemtoken": "123",
        "dom0domUPairs": {"DOMU": ["sea200220exddu0101"]},
        "secretId": "ocid1.seckey.xxxx",
        "rpmParUrl": "http://somepar/supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
        "parUrl": "http://somepar/"
    },
    "usercmd": "deploy"
}

PAYLOAD_INVALID_RPMPARURL = {
    "commonParameters": {
        "resourceType": "exadbvmcluster",
        "idemtoken": "123",
        "dom0domUPairs": {"DOMU": ["sea200220exddu0101"]},
        "secretId": "ocid1.seckey.xxxx",
        "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64",
        "parUrl": "http://somepar/"
    },
    "usercmd": "deploy"
}


PAYLOAD_INVALID_USER_CMD = {
    "commonParameters": {"resourceType": "vmcluster1"},
    "usercmd": None
}

PAYLOAD_RESOURCE_TYPE_UNKNOWN = {
    "commonParameters": {    "resourceType": "unknown",
    "idemtoken": "123",
    "dom0domUPairs": {"DOMU": ["sea200220exddu0101"]},
    "secretId": "ocid1.seckey.xxxx",
    "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64",
    "rpmParUrl": "http://somepar/supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
    "parUrl": "http://somepar/"},
    "usercmd": "deploy"
}

VALID_COMMON_PARAMETERS = {
    "resourceType": "exadbvmcluster",
    "idemtoken": "123",
    "dom0domUPairs": {"DOMU": ["sea200220exddu0101"]},
    "secretId": "ocid1.seckey.xxxx",
    "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64",
    "rpmParUrl": "http://somepar/supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
    "parUrl": "http://somepar/"
}

PAYLOAD_USER_CMD_UNKNOWN = {
    "commonParameters": VALID_COMMON_PARAMETERS,
    "usercmd": "unknown"
}

PAYLOAD_ASSIGN_INFO = {
    "usercmd": "deploy",
    "commonParameters": VALID_COMMON_PARAMETERS,
    "deployInfo": {
        "parUrl": "http://somepar/",
        "rpmVersion": "supportctl-24.1.0.0.0-250326.0858.x86_64.rpm",
        "rpmParUrl": "http://somepar/"
    },
}

PAYLOAD_CREATE_USER_INFO = {
    "usercmd": "create_user",
    "commonParameters": VALID_COMMON_PARAMETERS,
    "createUserInfo": {"username": "temp-username"}
}

PAYLOAD_GET_PAR_URL_INFO = {
    "usercmd": "get_debug_parurl",
    "commonParameters": VALID_COMMON_PARAMETERS
}

PAYLOAD_EXECUTE_CMD_INFO = {
    "usercmd": "execute_commands",
    "commonParameters": VALID_COMMON_PARAMETERS,
    "commandExecutionInfo":{
        "commandExecutionUser": "testusername",
        "commandExecutionUserSecretId": "ocid1.secrect.xxxx",
        "listOfCommands": {
            "commands": [{"cmd": "echo", "args":["testing"]}],
            "hostnames": ["sea200220exddu0101"],
        }
    }
}

REMOTE_NODE_OUTPUT_JSON = {
    "idemtoken": "123", "status": "200", "output": None, "errorMessage": "some error",
    "warningMessage": "some warning", "remoteHostName": "sea200220exddu0101",
    "dlgtMgmtRpmVersion": "supportctl-24.1.0.0.0-250516.1125.x86_64\n",
    "returnCode": "0",
    "parUrl": "http://somepar/",
    "logfileName": ["filename1", "filename2"]
}


class MockDomUCommandClient:
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
        # Create mock file-like objects for stdin, stdout, stderr
        # Simulate byte stream
        stdout.read.return_value = stdout_str.encode()
        stderr.read.return_value = stderr_str.encode()
        self.return_value = return_val
        return stdin, stdout, stderr

    def fake_return_value(self):
        return self.return_value

class ebTestUserHandler(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super(ebTestUserHandler, self).setUpClass()
        # super().setUpClass()

    def prepare_secrect_factoty(self):
        oci_factory = MagicMock()
        oci_factory.get_secrets_client.return_value = mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_bundle.return_value = mock_response = MagicMock()
        mock_response.data.secret_bundle_content.content = base64.b64encode(b'{"publicKey":"some public key", "privateKey":"some private key"}')
        return oci_factory

    def prepare_mock_inputs(self, aMockExaOCIFactory, aMockGetGContext, aMockExaBoxNodeClass):
        mockExaBoxNode = MagicMock()
        cmd_client = MockDomUCommandClient()
        mockExaBoxNode.mConnect.return_value = None
        mockExaBoxNode.mSetUser.return_value = None
        mockExaBoxNode.mSetSudo.return_value = None
        mockExaBoxNode.mSetExaKmsEntry.return_value = None
        mockExaBoxNode.mDisconnect.return_value = None
        mockExaBoxNode.mIsConnectable.return_value = True

        mockExaBoxNode.mExecuteCmd.side_effect = cmd_client.fake_exec_command
        mockExaBoxNode.mGetCmdExitStatus.side_effect = cmd_client.fake_return_value
        aMockExaBoxNodeClass.return_value = mockExaBoxNode

        mockGetGContext = MagicMock()
        mockGetGContext.mGetExaKms.return_value = exakms = MagicMock()
        exakms.mBuildExaKmsEntry.return_value = None
        aMockGetGContext.return_value = mockGetGContext

        aMockExaOCIFactory.return_value = self.prepare_secrect_factoty()
        return cmd_client

    def test_invalid_common_params(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_COMMON_PARMS
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid payload, commonParameters missing")

    def test_invalid_resource_type(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_RESOURCE_TYPE
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid payload, resourceType missing in commonParameters")

    def test_invalid_idemtoken(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_IDEMTOKEN
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid commonParameters, Missing idemtoken")

    def test_invalid_dom0_domu_pair1(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_DOM0DOMUPAIRS1
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid commonParameters, Missing/Invalid dom0domUPairs")

    def test_invalid_dom0_domu_pair2(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_DOM0DOMUPAIRS2
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid commonParameters, Missing/Invalid dom0domUPairs")

    def test_invalid_domu1(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_DOMU1
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid commonParameters, Missing/Invalid DOMU parameters in dom0domUPairs")

    def test_invalid_domu2(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_DOMU2
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid commonParameters, Missing/Invalid DOMU parameters in dom0domUPairs")

    def test_invalid_secret_id(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_SECRETID
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid commonParameters, Missing secretId")

    def test_invalid_rpm_version(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_RPMVERSION
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid commonParameters, Missing rpmVersion")

    def test_invalid_rpm_par_url(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_RPMPARURL
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid commonParameters, Missing rpmParUrl")

    def test_invalid_user_cmd(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_USER_CMD
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid payload, usercmd missing")

    def test_resource_type_unknown(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_RESOURCE_TYPE_UNKNOWN
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid resource type - unknown")

    def test_user_cmd_unknown(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_USER_CMD_UNKNOWN
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual("unknown is not supported - supported operations" in _result["errorMessage"], True)

    def test_invalid_user_cmd2(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_INVALID_COMMON_PARMS
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Invalid payload, commonParameters missing")

    def test_invalid_execute_command_username(self):
        _options = self.mGetContext().mGetArgsOptions()
        command_exec_info = {}
        command_exec_info.update(PAYLOAD_EXECUTE_CMD_INFO)
        command_exec_info["commandExecutionInfo"] = {
            "commandExecutionUserSecretId": "ocid1.secrect.xxxx",
            "listOfCommands": {
                "commands": [{"cmd": "echo", "args": ["testing"]}],
                "hostnames": ["sea200220exddu0101"],
            }
        }
        _options.jsonconf = command_exec_info
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Missing commandExecutionUser for execute_commands operation")

    def test_invalid_execute_command_secret_id(self):
        _options = self.mGetContext().mGetArgsOptions()
        command_exec_info = {}
        command_exec_info.update(PAYLOAD_EXECUTE_CMD_INFO)
        command_exec_info["commandExecutionInfo"] = {
            "commandExecutionUser": "testusername",
            "listOfCommands": {
                "commands": [{"cmd": "echo", "args":["testing"]}],
                "hostnames": ["sea200220exddu0101"],
            }
        }
        _options.jsonconf = command_exec_info
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Missing commandExecutionUserSecretId for execute_commands operation")

    def test_invalid_execute_command_listofcommands(self):
        _options = self.mGetContext().mGetArgsOptions()
        command_exec_info = {}
        command_exec_info.update(PAYLOAD_EXECUTE_CMD_INFO)
        command_exec_info["commandExecutionInfo"] = {
            "commandExecutionUser": "testusername",
            "commandExecutionUserSecretId": "ocid1.secrect.xxxx",
        }
        _options.jsonconf = command_exec_info
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Missing/Invalid listOfCommands for execute_commands operation")

    def test_invalid_execute_command_listofcommands2(self):
        _options = self.mGetContext().mGetArgsOptions()
        command_exec_info = {}
        command_exec_info.update(PAYLOAD_EXECUTE_CMD_INFO)
        command_exec_info["commandExecutionInfo"] = {
            "commandExecutionUser": "testusername",
            "commandExecutionUserSecretId": "ocid1.secrect.xxxx",
            "listOfCommands": "invalid string; it must be dict"
        }
        _options.jsonconf = command_exec_info
        _handler = DaCtlHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 301)
        self.assertEqual(_result["errorMessage"], "Missing/Invalid listOfCommands for execute_commands operation")


    @patch("exabox.ovm.dactlMgr.exaBoxNode")
    @patch("exabox.ovm.dactlMgr.get_gcontext")
    @patch("exabox.ovm.dactlMgr.ExaOCIFactory")
    def test_execute_cmd_assign_operation_invalid(self, mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class):
        """
        Invalid scenarios:
            1. rpmVersion or rpmParUrl are incorrect or not reachable
            2. Unable to install RPM
            3. Unable to install delegation control operation on DOM-U
            4. Unable to deploy delegation control operation on DOM-U (install is successful)
        """
        cmd_client = self.prepare_mock_inputs(mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class)

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_ASSIGN_INFO
        _handler = DaCtlHandler(_options)

        # 1.1 Invalid test ------- "rpmVersion" is not present in input json
        ebLogInfo("Assign_operation - 1.1 rpmVersion not exists ")
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 1, '', "")
        cmd_client.add_command('/usr/bin/curl', 1, '', "Unable to download file")
        cmd_client.add_command('/usr/bin/sudo /usr/bin/rpm', 1, '', "Not a valid RPM")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

        # 1.2 Invalid test ------- Unable to install RPM
        ebLogInfo("Assign_operation - 1.2 Unable to install RPM ")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 0, '', "")
        cmd_client.add_command('/usr/bin/curl', 0, '', "Unable to download file")
        cmd_client.add_command('/usr/bin/sudo /usr/bin/rpm', 1, '', "Not a valid RPM")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

        # 1.3  Invalid test ------- Unable to install delegation control operation on DOM-U
        ebLogInfo("Assign_operation - 1.3 Unable to install delegation control operation on DOM-U ")
        cmd_client.reset()
        output_json = {}
        output_json.update(REMOTE_NODE_OUTPUT_JSON)
        output_json["status"] = "500"
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 1, '', "")
        cmd_client.add_command('/usr/bin/curl', 0, 'success', "")
        cmd_client.add_command('/usr/bin/sudo /usr/bin/rpm', 0, 'Rpm installed successfully', "")
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

        # 1.4  Invalid test ------- "install" operation successful on DOM-U, but "deploy" operation failed DOM-U
        ebLogInfo("Assign_operation - 1.4 install success; deploy failed ")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 1, '', "")
        cmd_client.add_command('/usr/bin/curl', 0, 'success', "")
        cmd_client.add_command('/usr/bin/sudo /usr/bin/rpm', 0, 'Rpm installed successfully', "")
        # INSTALL
        output_json["status"] = "202"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        output_json["status"] = "200"
        # DEPLOY
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        output_json["status"] = "500"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)


        mock_exaBoxNode = mock_exaBoxNode_class.return_value

        ebLogInfo("Other exceptions")
        mock_exaBoxNode.mExecuteCmd.side_effect = Exception("Simulated execute failure")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

        ebLogInfo("connect - Exception")
        mock_exaBoxNode.mConnect.side_effect = Exception("Simulated connection failure")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

        ebLogInfo("Factory secret - Exception")
        mock_ExaOCIFactory.side_effect = Exception("Simulated Oci Factory secret failure")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

        ebLogInfo("Exacloud Library exception- Exception")
        mock_get_gcontext.side_effect = Exception("Simulated get_gcontext failure")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

    @patch("exabox.ovm.dactlMgr.exaBoxNode")
    @patch("exabox.ovm.dactlMgr.get_gcontext")
    @patch("exabox.ovm.dactlMgr.ExaOCIFactory")
    def test_unhandled_exception_verification(self, mock_ExaOCIFactory, mock_get_gcontext,
                                                  mock_exaBoxNode_class):
        cmd_client = self.prepare_mock_inputs(mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class)
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_ASSIGN_INFO
        _handler = DaCtlHandler(_options)
        ebLogInfo("test_unhandled_exception_verification")
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 1, '', "")
        cmd_client.add_command('/usr/bin/curl', 1, '', "Unable to download file")
        cmd_client.add_command('/usr/bin/sudo /usr/bin/rpm', 1, '', "Not a valid RPM")
        mock_exaBoxNode = mock_exaBoxNode_class.return_value
        mock_exaBoxNode.mDisconnect.side_effect = Exception("Simulated get_gcontext failure")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

    @patch("exabox.ovm.dactlMgr.exaBoxNode")
    @patch("exabox.ovm.dactlMgr.get_gcontext")
    @patch("exabox.ovm.dactlMgr.ExaOCIFactory")
    def test_execute_cmd_assign_operation_valid(self, mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class):
        """
        Valid scenarios:
            1. RPM already installed on DOM-U and proceed with install and deploy successful.
            2. Install RPM on DOM-U and proceed with install and deploy successful.
        """
        cmd_client = self.prepare_mock_inputs(mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class)
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_ASSIGN_INFO
        _handler = DaCtlHandler(_options)

        output_json = {}
        output_json.update(REMOTE_NODE_OUTPUT_JSON)
        # 2.1 ------ SUCCESS : Install RPM on DOM-U and proceed with install and deploy successful.
        ebLogInfo("Assign_operation - 2.1 RPM install +  install success + deploy success ")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 1, '', "")
        cmd_client.add_command('/usr/bin/curl', 0, 'success', "")
        cmd_client.add_command('/usr/bin/sudo /usr/bin/rpm', 0, 'Rpm installed successfully', "")
        # INSTALL
        output_json["status"] = "200"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        # DEPLOY
        output_json["status"] = "200"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)

        # 2.2 ---- SUCCESS : RPM already installed on DOM-U and proceed with install and deploy successful.
        ebLogInfo("Assign_operation - 2.2 install success + deploy success ")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 0, 'supportctl-24.1.0.0.0-250326.0858.x86_64\n', "")
        output_json["status"] = "200"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)

    @patch("exabox.ovm.dactlMgr.exaBoxNode")
    @patch("exabox.ovm.dactlMgr.get_gcontext")
    @patch("exabox.ovm.dactlMgr.ExaOCIFactory")
    def test_execute_cmd_create_user_operation(self, mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class):
        """
        CREATE USER:
            Invalid scenarios:
                1. create user failed on all DOM-Us
                2. Invalid Json received from DOM-U
            Valid scenarios:
                1. create user failed on some DOM-Us [ atleast one of DOM-U is successful ]
                2. RPM is not installed on some of DOM-Us; install and assign is successful and create users also successful.
                3. create user which is already created username (twice same user creation)
        """
        cmd_client = self.prepare_mock_inputs(mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class)
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_CREATE_USER_INFO
        _handler = DaCtlHandler(_options)

        output_json = {}
        output_json.update(REMOTE_NODE_OUTPUT_JSON)
        output_json["status"] = "500"
        output_json["errorMessage"] = None
        output_json["warningMessage"] = None

        # 1.1 INVALID CASE - create user is failed in all nodes
        ebLogInfo("create_user - 1.1 create user is failed in all nodes ")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 0, 'supportctl-24.1.0.0.0-250326.0858.x86_64\n', "")
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

        # 1.2 INVALID CASE - create user is failed in all nodes [invalid Json output]
        ebLogInfo("create_user - 1.2 create user is failed Invalid Json received from DOM-U")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 0, 'supportctl-24.1.0.0.0-250326.0858.x86_64\n', "")
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, "Invalid json", "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 500)

        # 2.1 SUCCESS CASE -- Install on new node; and create user is successful
        ebLogInfo("create_user - 2.1 RPM Install + install + deploy + User creation success")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 1, '', "")
        cmd_client.add_command('/usr/bin/curl', 0, 'success', "")
        cmd_client.add_command('/usr/bin/sudo /usr/bin/rpm', 0, 'Rpm installed successfully', "")
        output_json["status"] = "200"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)

        # 2.1 SUCCESS CASE -- Deploy failed but; and create user is successful
        ebLogInfo("create_user - 2.1 RPM Install + install + deploy + User creation success")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 1, '', "")
        cmd_client.add_command('/usr/bin/curl', 0, 'success', "")
        cmd_client.add_command('/usr/bin/sudo /usr/bin/rpm', 0, 'Rpm installed successfully', "")
        output_json["status"] = "200"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        output_json["status"] = "500"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        output_json["status"] = "200"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)

        # 2.2  & 2.3  SUCCESS CASE -- Existing node; and create user is successful
        ebLogInfo("create_user - 2.2 User creation success")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 0, 'supportctl-24.1.0.0.0-250326.0858.x86_64\n', "")
        output_json["status"] = "200"
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)

    @patch("exabox.ovm.dactlMgr.exaBoxNode")
    @patch("exabox.ovm.dactlMgr.get_gcontext")
    @patch("exabox.ovm.dactlMgr.ExaOCIFactory")
    def test_execute_cmd_command_execution_operation(self, mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class):
        """
        CREATE USER:
            Invalid scenarios:
                1. create user failed on all DOM-Us
                2. Invalid Json received from DOM-U
            Valid scenarios:
                1. create user failed on some DOM-Us [ atleast one of DOM-U is successful ]
                2. RPM is not installed on some of DOM-Us; install and assign is successful and create users also successful.
                3. create user which is already created username (twice same user creation)
        """
        cmd_client = self.prepare_mock_inputs(mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class)
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_EXECUTE_CMD_INFO
        _handler = DaCtlHandler(_options)

        output_json = {}
        output_json.update(REMOTE_NODE_OUTPUT_JSON)
        output_json["status"] = "500"
        output_json["output"] = '{"commands": "result"}'

        # 1.1 INVALID CASE - failure case
        ebLogInfo("execute_commands - 1.1 failure case")
        cmd_client.reset()
        cmd_client.add_command("/usr/bin/python3", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)
        self.assertEqual(_result["async_operation_status"], "500")

        # 2.1 Success & In-progress case
        ebLogInfo("execute_commands - 2.1 In-progress case 202")
        cmd_client.reset()
        output_json["status"] = "202"
        cmd_client.add_command("/usr/bin/python3", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)
        self.assertEqual(_result["async_operation_status"], "202")

        # 2.2 Success & completed case
        ebLogInfo("execute_commands - 2.2 Success & completed case 200")
        cmd_client.reset()
        output_json["status"] = "200"
        cmd_client.add_command("/usr/bin/python3", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)
        self.assertEqual(_result["async_operation_status"], "200")

        # 1.2 INVALID -- Success but Invalid output format
        ebLogInfo("execute_commands - 1.2 INVALID -- Success 200 but Invalid output format")
        cmd_client.reset()
        output_json["status"] = "200"
        output_json["output"] = "invalid"
        cmd_client.add_command("/usr/bin/python3", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)
        self.assertEqual(_result["async_operation_status"], "200")

    @patch("exabox.ovm.dactlMgr.exaBoxNode")
    @patch("exabox.ovm.dactlMgr.get_gcontext")
    @patch("exabox.ovm.dactlMgr.ExaOCIFactory")
    def test_execute_cmd_getparutl_operation(self, mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class):
        cmd_client = self.prepare_mock_inputs(mock_ExaOCIFactory, mock_get_gcontext, mock_exaBoxNode_class)
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_GET_PAR_URL_INFO
        _handler = DaCtlHandler(_options)

        output_json = {}
        output_json.update(REMOTE_NODE_OUTPUT_JSON)
        output_json["output"] = '["filename1", "filename2"]'

        # 1.1 SUCCESS CASE
        ebLogInfo("getparurl - 1.1 SUCCESS")
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 0, 'supportctl-24.1.0.0.0-250326.0858.x86_64\n', "")
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)

        # Failure -- output format is not a list of files
        ebLogInfo("getparurl - 1.2 Failure -- output format is not a list of files")
        output_json["output"] = "filename1"
        cmd_client.reset()
        cmd_client.add_command('/usr/bin/rpm -qa supportctl', 0, 'supportctl-24.1.0.0.0-250326.0858.x86_64\n', "")
        cmd_client.add_command("/usr/bin/sudo '--' '/usr/bin/python3'", 0, json.dumps(output_json), "")
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["status"], 200)

if __name__ == '__main__':
    unittest.main()

