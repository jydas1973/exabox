#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/eboxconf/tests_exaboxconf_operations.py /main/2 2025/05/06 06:50:19 aypaul Exp $
#
# tests_exaboxconf_operations.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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

MOCK_EXABOX_CONF = {
    "virtual_memory_size": "",
    "vm_cfg_prev_limit": "0",
    "vm_clusters_limit": "16",
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
        self.assertRaises(ExacloudRuntimeError, _handler.mExecute)
        
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
        with patch("builtins.open", mock_open(read_data='{"worker_count": "15"}')),\
             patch('exabox.jsondispatch.handler_exabox_conf_operations.ExaboxConfOperationsHandler.FileLockManager'),\
             patch('exabox.jsondispatch.handler_exabox_conf_operations.mBackupFile'),\
             patch('json.dump'):
            _handler = ExaboxConfOperationsHandler(_options)
            _handler.mExecute()
       
    def test_mBackupExaboxConf(self):
        ebLogInfo("Running unit test on ExaboxConfOperationsHandler.mBackupExaboxConf")
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = MOCK_UPDATE_EXABOX_CONF
        _handler = ExaboxConfOperationsHandler(_options)
        _handler.mBackupExaboxConf()
        
        
if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file