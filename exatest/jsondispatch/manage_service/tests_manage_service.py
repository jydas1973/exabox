#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/manage_service/tests_manage_service.py /main/1 2025/11/27 18:10:45 jepalomi Exp $
#
# tests_manage_service.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_manage_service.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jepalomi    04/28/26 - 39263021 - Update tests for changes for security 
#                           findings
#    jepalomi    11/13/25 - 38529119 - Unittests for manage service
#    jepalomi    11/13/25 - Creation
#

import unittest
from unittest import mock
from unittest.mock import MagicMock

from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand

from exabox.jsondispatch.handler_manage_service import ManageServiceHandler

TASK_CMDS = {
        'exists': '/usr/bin/systemctl cat syslens',
        'start': '/usr/bin/systemctl start syslens',
        'stop': '/usr/bin/systemctl stop syslens',
        'status': '/usr/bin/systemctl is-active syslens',
        'full_status': '/usr/bin/systemctl status syslens',
        'version': '/usr/bin/rpm -q syslens',
        'recent_logs': '/usr/bin/journalctl -u syslens --since "5 min ago" --no-pager -l --full -n 20',
    }

class ebTestManageServiceHandler(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    def test_mExecute(self):
        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler.mExecServiceCmd") as mock_mExecServiceCmd:
            
            mock_mExecServiceCmd.return_value = {
                'task_status': 'success',
                'hostname': 'test_host',
                'error': '',
                'message': 'syslens start successful for host test_host'
            }
            _options = self.mGetContext().mGetArgsOptions()
            _options.jsonconf = {
                "operation": "manage_service",
                "task": "start",
                "service": "syslens",
                "host_nodes": ['test_host']
            }
            handler = ManageServiceHandler(_options)
            rc, response = handler.mExecute()
            self.assertEqual(rc, 0)
            self.assertEqual(response['service'], 'syslens')
            self.assertEqual(response['task'], 'start')
            self.assertEqual(len(response['node_task_status']), 1)
            self.assertEqual(response['node_task_status'][0]['task_status'], 'success')
            self.assertEqual(response['node_task_status'][0]['hostname'], 'test_host')
            mock_mExecServiceCmd.assert_called_once_with('test_host', 'syslens', 'start', mock.ANY)

    def test_mExecute_multiple_hosts(self):
        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler.mExecServiceCmd") as mock_mExecServiceCmd:
            
            mock_mExecServiceCmd.side_effect = [
                {
                    'task_status': 'success',
                    'hostname': 'test_host1',
                    'error': '',
                    'message': 'syslens start successful for host test_host1'
                },
                {
                    'task_status': 'success',
                    'hostname': 'test_host2',
                    'error': '',
                    'message': 'syslens start successful for host test_host2'
                }
            ]
            _options = self.mGetContext().mGetArgsOptions()
            _options.jsonconf = {
                "operation": "manage_service",
                "task": "start",
                "service": "syslens",
                "host_nodes": ['test_host1', 'test_host2']
            }
            handler = ManageServiceHandler(_options)
            rc, response = handler.mExecute()
            self.assertEqual(rc, 0)
            self.assertEqual(response['service'], 'syslens')
            self.assertEqual(response['task'], 'start')
            self.assertEqual(len(response['node_task_status']), 2)
            self.assertEqual(response['node_task_status'][0]['task_status'], 'success')
            self.assertEqual(response['node_task_status'][0]['hostname'], 'test_host1')
            self.assertEqual(response['node_task_status'][1]['task_status'], 'success')
            self.assertEqual(response['node_task_status'][1]['hostname'], 'test_host2')
            self.assertEqual(mock_mExecServiceCmd.call_count, 2)

    def test_mBuildTaskCmds_uses_trusted_service_metadata(self):
        task_cmds = ManageServiceHandler.mBuildTaskCmds(
            {"unit": "syslens", "package": "syslens"}
        )

        self.assertEqual(task_cmds["exists"], "/usr/bin/systemctl cat syslens")
        self.assertEqual(task_cmds["start"], "/usr/bin/systemctl start syslens")
        self.assertEqual(task_cmds["stop"], "/usr/bin/systemctl stop syslens")
        self.assertEqual(task_cmds["status"], "/usr/bin/systemctl is-active syslens")
        self.assertEqual(task_cmds["full_status"], "/usr/bin/systemctl status syslens")
        self.assertEqual(task_cmds["version"], "/usr/bin/rpm -q syslens")
        self.assertEqual(
            task_cmds["recent_logs"],
            '/usr/bin/journalctl -u syslens --since "5 min ago" --no-pager -l --full -n 20'
        )

    def test_mExecute_unsupported_service(self):
        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler.mExecServiceCmd") as mock_mExecServiceCmd:

            _options = self.mGetContext().mGetArgsOptions()
            _options.jsonconf = {
                "operation": "manage_service",
                "task": "start",
                "service": "test_service",
                "host_nodes": ['test_host']
            }

            handler = ManageServiceHandler(_options)

            with self.assertRaisesRegex(ExacloudRuntimeError, "Unsupported service"):
                handler.mExecute()

            mock_mExecServiceCmd.assert_not_called()

    def test_mExecServiceCmd_stop(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.connect_to_host") as mock_connect, \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd_check" , return_value=None), \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler._handle_start_stop_task") as mock_handle_start_stop_task:
            
            mock_connect.return_value.__enter__.return_value = dummy_node
            
            ManageServiceHandler.mExecServiceCmd('test_host', 'syslens', 'stop', TASK_CMDS)
            mock_handle_start_stop_task.assert_called_once_with(dummy_node, 'test_host', 'syslens', 'stop', TASK_CMDS)

    def test_mExecServiceCmd_start(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.connect_to_host") as mock_connect, \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd_check" , return_value=None), \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler._handle_start_stop_task") as mock_handle_start_stop_task:
            
            mock_connect.return_value.__enter__.return_value = dummy_node
            
            ManageServiceHandler.mExecServiceCmd('test_host', 'syslens', 'start', TASK_CMDS)
            mock_handle_start_stop_task.assert_called_once_with(dummy_node, 'test_host', 'syslens', 'start', TASK_CMDS)

    def test_mExecServiceCmd_status(self):

        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.connect_to_host") as mock_connect, \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd_check" , return_value=None), \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler._handle_status_task") as mock_handle_status_task:
            
            mock_connect.return_value.__enter__.return_value = dummy_node
            
            ManageServiceHandler.mExecServiceCmd('test_host', 'syslens', 'status', TASK_CMDS)
            mock_handle_status_task.assert_called_once_with(dummy_node, 'test_host', 'syslens', TASK_CMDS)

    def test__handle_start_stop_task_success(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", return_value=(0, "active", "")):
            res = ManageServiceHandler._handle_start_stop_task(dummy_node, "test_host", "syslens", "start", TASK_CMDS)
            self.assertEqual(res['task_status'], 'success')
            self.assertEqual(res['message'], 'syslens start successful for host test_host')

    def test__handle_start_stop_task_failure(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", return_value=(0, "failed", "")):
            res = ManageServiceHandler._handle_start_stop_task(dummy_node, "test_host", "syslens", "start", TASK_CMDS)
            self.assertEqual(res['task_status'], 'failure')
            self.assertEqual(res['message'], 'syslens start failed for host test_host')

    def test__handle_stop_task_success_on_inactive(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", return_value=(0, "inactive", "")):
            res = ManageServiceHandler._handle_start_stop_task(dummy_node, "test_host", "syslens", "stop", TASK_CMDS)
            self.assertEqual(res['task_status'], 'success')
            self.assertEqual(res['message'], 'syslens stop successful for host test_host')

    def test__handle_stop_task_failure_on_failed(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", return_value=(0, "failed", "")):
            res = ManageServiceHandler._handle_start_stop_task(dummy_node, "test_host", "syslens", "stop", TASK_CMDS)
            self.assertEqual(res['task_status'], 'failure')
            self.assertEqual(res['message'], 'syslens stop failed for host test_host')

    def test__handle_stop_task_failure_on_unknown(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", return_value=(0, "unknown", "")):
            res = ManageServiceHandler._handle_start_stop_task(dummy_node, "test_host", "syslens", "stop", TASK_CMDS)
            self.assertEqual(res['task_status'], 'failure')
            self.assertEqual(res['message'], 'syslens stop failed for host test_host')

    def test__handle_status_task_success(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", side_effect=[(0, "active", ""), (0, "1.0", "")]):
            res = ManageServiceHandler._handle_status_task(dummy_node, "test_host", "syslens", TASK_CMDS)
            self.assertEqual(res['task_status'], 'success')
            self.assertEqual(res['status'], 'active')
            self.assertEqual(res['version'], '1.0')

    def test__handle_status_task_failure(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", return_value=(0, "", "")):
            res = ManageServiceHandler._handle_status_task(dummy_node, "test_host", "syslens", TASK_CMDS)
            self.assertEqual(res['task_status'], 'failure')
            self.assertEqual(res['status'], '')
            self.assertEqual(res['version'], '')

if __name__ == '__main__':
    unittest.main()
