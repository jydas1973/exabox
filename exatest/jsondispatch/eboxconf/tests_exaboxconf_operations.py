#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/eboxconf/tests_exaboxconf_operations.py /main/3 2026/02/05 09:17:18 kanmanic Exp $
#
# tests_exaboxconf_operations.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_exaboxconf_operations.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    joysjose    05/04/26 - Restrict exabox_conf_operations key policy
#    joysjose    04/29/26 - Implement exabox conf sensitive key deny policy
#    kanmanic    02/02/26 - update vm_clusters_limit default
#    joysjose    07/25/24 - Unit test file to include tests for the exabox.conf
#                           operations
#    joysjose    07/25/24 - Creation
#
import json
import os
import unittest
from unittest import mock
from unittest.mock import patch, mock_open
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_exabox_conf_operations import ExaboxConfOperationsHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo


MOCK_VIEW_EXABOX_CONF={
    "operation" : "view",
    "keys" : ["worker_count", "vmbackup"]
}

MOCK_VIEW_EXABOX_CONF_1 = {
    "operation" : "view"
}

MOCK_VIEW_EXABOX_CONF_2 = {
    "keys" : ["worker_count", "vmbackup"]
}

MOCK_VIEW_EXABOX_CONF_3 = {
    "operation" : "view",
    "keys" : ["invalid_key"]
}

MOCK_VIEW_EXABOX_CONF_4 = [{
    "operation" : "view",
    "keys" : ["invalid_key"]
}
]

MOCK_VIEW_EXABOX_CONF_DENIED = {
    "operation" : "view",
    "keys" : ["default_pwd", "oeda_pwd"]
}

MOCK_VIEW_EXABOX_CONF_MIXED_DENIED = {
    "operation" : "view",
    "keys" : ["worker_count", "root_spwd"]
}

MOCK_VIEW_EXABOX_CONF_REPORTED_DENIED = {
    "operation" : "view",
    "keys" : ["worker_count", "exacc_mtls"]
}

MOCK_VIEW_EXABOX_CONF_EMPTY_KEYS = {
    "operation" : "view",
    "keys" : []
}

MOCK_UPDATE_EXABOX_CONF = {
    "operation" : "update",
    "key_value_pair" : {
        "worker_count" : "10"
    }
}

MOCK_UPDATE_EXABOX_CONF_1 = {
    "operation" : "update"
}

MOCK_UPDATE_EXABOX_CONF_2 = {
    "key_value_pair" : {
        "worker_count" : "10"
    }
}

MOCK_UPDATE_EXABOX_CONF_3 = {
    "operation" : "update",
    "key_value_pair" : {
        "invalid_key" : "10"
    }
}

MOCK_UPDATE_EXABOX_CONF_4 = [{
    "operation" : "update",
    "key_value_pair" : {
        "worker_count" : "10"
    }
}
]

MOCK_UPDATE_EXABOX_CONF_5 = {
    "operation" : "invalid_op",
    "key_value_pair" : {
        "invalid_key" : "10"
    }
}

MOCK_UPDATE_EXABOX_CONF_DENIED = {
    "operation" : "update",
    "key_value_pair" : {
        "agent_auth" : ["placeholder-user", "placeholder-secret"]
    }
}

MOCK_UPDATE_EXABOX_CONF_MIXED_DENIED = {
    "operation" : "update",
    "key_value_pair" : {
        "worker_count" : "10",
        "agent_auth" : ["placeholder-user", "placeholder-secret"]
    }
}

MOCK_UPDATE_EXABOX_CONF_REPORTED_DENIED = {
    "operation" : "update",
    "key_value_pair" : {
        "enable_block_opctl" : "True"
    }
}

MOCK_UPDATE_EXABOX_CONF_NONMUTABLE = {
    "operation" : "update",
    "key_value_pair" : {
        "vmbackup" : {
            "default_timeout" : "1"
        }
    }
}

MOCK_UPDATE_EXABOX_CONF_TYPE_MISMATCH = {
    "operation" : "update",
    "key_value_pair" : {
        "worker_count" : {
            "invalid" : "shape"
        }
    }
}

MOCK_UPDATE_EXABOX_CONF_EXTRA_FIELD = {
    "operation" : "update",
    "key_value_pair" : {
        "worker_count" : "10"
    },
    "unexpected" : True
}

MOCK_EXABOX_CONF = {
    "virtual_memory_size": "",
    "vm_cfg_prev_limit": "0",
    "vm_clusters_limit": "173",
    "vm_handler": "virsh",
    "vm_prefix_dom0_version_cutoff": "23.1.90.0.0.231219",
    "vm_reboot_consolelog_markers": [
        "The selected entry will be started automatically",
        "reboot: Restarting system",
        "Starting Reboot"
    ],
    "vmbackup": {
        "default_timeout": "18000",
        "enable_vmbackup_install": "True",
        "force_ecra_oss_api": "False",
        "force_users_principals": "False",
        "max_gold_backup_timeout": "18000",
        "max_timeout": "18000",
        "root_compartment_ocid": "",
        "vmboss_group_ocid": "",
        "vmboss_key_ocid": "",
        "vmboss_vault_ocid": ""
    },
    "vmbackup2oss_skip_image": "False",
    "vmerase_pass": "3pass",
    "worker_connection_timeout": "15",
    "worker_count": "15",
    "worker_count_nonexacs": "4",
    "worker_idle_timeout_minutes": "60",
    "worker_port": "9100",
    "worker_port_extravalidation": "True",
    "worker_thread_limit": "50"
}

class ebTestExaBoxConf(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None
        
    def test_mViewExaboxConfParam(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_VIEW_EXABOX_CONF
        _handler = ExaboxConfOperationsHandler(_options)
        _handler.mExecute()
        
    def test_mViewExaboxConfParam_err1(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_VIEW_EXABOX_CONF_1
        _handler = ExaboxConfOperationsHandler(_options)
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)
        
    def test_mViewExaboxConfParam_err2(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_VIEW_EXABOX_CONF_2
        _handler = ExaboxConfOperationsHandler(_options)
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)
        
    def test_mViewExaboxConfParam_err3(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_VIEW_EXABOX_CONF_3
        _handler = ExaboxConfOperationsHandler(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 1)
        
    def test_mViewExaboxConfParam_err4(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_VIEW_EXABOX_CONF_4
        _handler = ExaboxConfOperationsHandler(_options)
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)
        
    def test_mViewExaboxConfParam_err5(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = None
        _handler = ExaboxConfOperationsHandler(_options)
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)
    
    def test_mUpdateExaboxConfParam_err1(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_1
        _handler = ExaboxConfOperationsHandler(_options)
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)
        
    def test_mUpdateExaboxConfParam_err2(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_2
        _handler = ExaboxConfOperationsHandler(_options)
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)
        
    def test_mUpdateExaboxConfParam_err3(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_3
        _handler = ExaboxConfOperationsHandler(_options)
        with patch.object(_handler, "mBackupExaboxConf") as mock_backup,\
             patch("builtins.open", mock_open()) as mock_file,\
             patch("exabox.jsondispatch.handler_exabox_conf_operations.ExaboxConfOperationsHandler.FileLockManager") as mock_lock,\
             patch("json.dump") as mock_json_dump:
            _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 1)
        self.assertEqual(_result["reason"], "keys_not_allowed_for_operation")
        self.assertEqual(_result["denied_keys"], ["invalid_key"])
        mock_backup.assert_not_called()
        mock_file.assert_not_called()
        mock_lock.assert_not_called()
        mock_json_dump.assert_not_called()
        
    def test_mUpdateExaboxConfParam_err4(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_4
        _handler = ExaboxConfOperationsHandler(_options)
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)
        
    def test_mUpdateExaboxConfParam_err5(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_5
        _handler = ExaboxConfOperationsHandler(_options)
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)
        
    def test_mUpdateExaboxConfParam_err6(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = None
        _handler = ExaboxConfOperationsHandler(_options)
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)

    def test_mUpdateExaboxConfParam_Success(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler.mUpdateExaboxConfParam")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF
        _handler = ExaboxConfOperationsHandler(_options)
        with patch.object(_handler, "mBackupExaboxConf"),\
             patch("builtins.open", mock_open(read_data='{"worker_count": "15"}')),\
             patch('exabox.jsondispatch.handler_exabox_conf_operations.ExaboxConfOperationsHandler.FileLockManager'),\
             patch('exabox.jsondispatch.handler_exabox_conf_operations.mBackupFile'),\
             patch('json.dump'):
            _handler.mExecute()

    @patch("exabox.jsondispatch.handler_exabox_conf_operations.get_gcontext")
    def test_mViewExaboxConfParam_denied_sensitive_keys(self, mock_get_gcontext):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler denied sensitive view")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_VIEW_EXABOX_CONF_DENIED
        _handler = ExaboxConfOperationsHandler(_options)

        _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 1)
        self.assertEqual(_result["status"], "denied")
        self.assertEqual(_result["operation"], "view")
        self.assertEqual(_result["reason"], "sensitive_keys_not_allowed")
        self.assertEqual(_result["denied_keys"], ["default_pwd", "oeda_pwd"])
        self.assertIn("default_pwd", _result["message"])
        self.assertIn("oeda_pwd", _result["message"])
        mock_get_gcontext.return_value.mCheckConfigOption.assert_not_called()

    @patch("exabox.jsondispatch.handler_exabox_conf_operations.get_gcontext")
    def test_mViewExaboxConfParam_denied_mixed_keys(self, mock_get_gcontext):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler denied mixed view")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_VIEW_EXABOX_CONF_MIXED_DENIED
        _handler = ExaboxConfOperationsHandler(_options)

        _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 1)
        self.assertEqual(_result["denied_keys"], ["root_spwd"])
        self.assertIn("root_spwd", _result["message"])
        mock_get_gcontext.return_value.mCheckConfigOption.assert_not_called()

    @patch("exabox.jsondispatch.handler_exabox_conf_operations.get_gcontext")
    def test_mViewExaboxConfParam_denied_reported_security_key(self, mock_get_gcontext):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler denied reported security key view")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_VIEW_EXABOX_CONF_REPORTED_DENIED
        _handler = ExaboxConfOperationsHandler(_options)

        _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 1)
        self.assertEqual(_result["reason"], "sensitive_keys_not_allowed")
        self.assertEqual(_result["denied_keys"], ["exacc_mtls"])
        self.assertIn("exacc_mtls", _result["message"])
        mock_get_gcontext.return_value.mCheckConfigOption.assert_not_called()

    def test_mUpdateExaboxConfParam_denied_sensitive_keys(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler denied sensitive update")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_DENIED
        _handler = ExaboxConfOperationsHandler(_options)

        with patch.object(_handler, "mBackupExaboxConf") as mock_backup,\
             patch("builtins.open", mock_open()) as mock_file,\
             patch("exabox.jsondispatch.handler_exabox_conf_operations.ExaboxConfOperationsHandler.FileLockManager") as mock_lock,\
             patch("json.dump") as mock_json_dump:
            _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 1)
        self.assertEqual(_result["status"], "denied")
        self.assertEqual(_result["operation"], "update")
        self.assertEqual(_result["reason"], "sensitive_keys_not_allowed")
        self.assertEqual(_result["denied_keys"], ["agent_auth"])
        self.assertIn("agent_auth", _result["message"])
        mock_backup.assert_not_called()
        mock_file.assert_not_called()
        mock_lock.assert_not_called()
        mock_json_dump.assert_not_called()

    def test_mUpdateExaboxConfParam_denied_reported_security_key(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler denied reported security key update")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_REPORTED_DENIED
        _handler = ExaboxConfOperationsHandler(_options)

        with patch.object(_handler, "mBackupExaboxConf") as mock_backup,\
             patch("builtins.open", mock_open()) as mock_file,\
             patch("exabox.jsondispatch.handler_exabox_conf_operations.ExaboxConfOperationsHandler.FileLockManager") as mock_lock,\
             patch("json.dump") as mock_json_dump:
            _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 1)
        self.assertEqual(_result["reason"], "sensitive_keys_not_allowed")
        self.assertEqual(_result["denied_keys"], ["enable_block_opctl"])
        self.assertIn("enable_block_opctl", _result["message"])
        mock_backup.assert_not_called()
        mock_file.assert_not_called()
        mock_lock.assert_not_called()
        mock_json_dump.assert_not_called()

    def test_mUpdateExaboxConfParam_denied_mixed_keys(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler denied mixed update")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_MIXED_DENIED
        _handler = ExaboxConfOperationsHandler(_options)

        with patch.object(_handler, "mBackupExaboxConf") as mock_backup,\
             patch("builtins.open", mock_open()) as mock_file,\
             patch("exabox.jsondispatch.handler_exabox_conf_operations.ExaboxConfOperationsHandler.FileLockManager") as mock_lock,\
             patch("json.dump") as mock_json_dump:
            _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 1)
        self.assertEqual(_result["denied_keys"], ["agent_auth"])
        self.assertIn("agent_auth", _result["message"])
        mock_backup.assert_not_called()
        mock_file.assert_not_called()
        mock_lock.assert_not_called()
        mock_json_dump.assert_not_called()

    def test_mUpdateExaboxConfParam_denied_nonmutable_key(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler denied nonmutable update key")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_NONMUTABLE
        _handler = ExaboxConfOperationsHandler(_options)

        with patch.object(_handler, "mBackupExaboxConf") as mock_backup,\
             patch("builtins.open", mock_open()) as mock_file,\
             patch("exabox.jsondispatch.handler_exabox_conf_operations.ExaboxConfOperationsHandler.FileLockManager") as mock_lock,\
             patch("json.dump") as mock_json_dump:
            _rc, _result = _handler.mExecute()

        self.assertEqual(_rc, 1)
        self.assertEqual(_result["reason"], "keys_not_allowed_for_operation")
        self.assertEqual(_result["denied_keys"], ["vmbackup"])
        self.assertIn("not allowed for this endpoint", _result["message"])
        mock_backup.assert_not_called()
        mock_file.assert_not_called()
        mock_lock.assert_not_called()
        mock_json_dump.assert_not_called()

    def test_mUpdateExaboxConfParam_type_mismatch(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler type mismatch update")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_TYPE_MISMATCH
        _handler = ExaboxConfOperationsHandler(_options)

        with patch.object(_handler, "mBackupExaboxConf") as mock_backup,\
             patch("builtins.open", mock_open(read_data=json.dumps(MOCK_EXABOX_CONF))) as mock_file,\
             patch("exabox.jsondispatch.handler_exabox_conf_operations.ExaboxConfOperationsHandler.FileLockManager") as mock_lock,\
             patch("json.dump") as mock_json_dump:
            self.assertRaises(ExacloudRuntimeError, _handler.mExecute)

        mock_backup.assert_called_once()
        mock_file.assert_called_once()
        mock_lock.assert_called_once()
        mock_json_dump.assert_not_called()

    def test_mHandleEndpoint_rejects_empty_view_keys(self):
        ebLogInfo("Running schema validation test on empty view keys")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_VIEW_EXABOX_CONF_EMPTY_KEYS
        _handler = ExaboxConfOperationsHandler(_options)

        self.assertRaises(ExacloudRuntimeError, _handler.mHandleEndpoint)

    def test_mHandleEndpoint_rejects_extra_update_field(self):
        ebLogInfo("Running schema validation test on extra update field")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF_EXTRA_FIELD
        _handler = ExaboxConfOperationsHandler(_options)

        self.assertRaises(ExacloudRuntimeError, _handler.mHandleEndpoint)
       
    def test_mBackupExaboxConf(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler.mBackupExaboxConf")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF
        _handler = ExaboxConfOperationsHandler(_options)
        _handler.mBackupExaboxConf()
        
        
if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
