#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/manage_service/tests_manage_service.py /main/1 2025/11/27 18:10:45 jepalomi Exp $
#
# tests_manage_service.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
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
#    jepalomi    11/13/25 - 38529119 - Unittests for manage service
#    jepalomi    11/13/25 - Creation
#

import unittest
from unittest import mock
from unittest.mock import MagicMock

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand

from exabox.jsondispatch.handler_manage_service import ManageServiceHandler

TASK_CMDS = {
        'start': '/usr/bin/systemctl start {service}',
        'stop': '/usr/bin/systemctl stop {service}',
        'status': '/usr/bin/systemctl is-active {service}',
        'version': '/usr/bin/rpm -q {service}',
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
                'message': 'test_service start successful for host test_host'
            }
            _options = self.mGetContext().mGetArgsOptions()
            _options.jsonconf = {
                "task": "start",
                "service": "test_service",
                "host_nodes": ['test_host']
            }
            handler = ManageServiceHandler(_options)
            rc, response = handler.mExecute()
            self.assertEqual(rc, 0)
            self.assertEqual(response['service'], 'test_service')
            self.assertEqual(response['task'], 'start')
            self.assertEqual(len(response['node_task_status']), 1)
            self.assertEqual(response['node_task_status'][0]['task_status'], 'success')
            self.assertEqual(response['node_task_status'][0]['hostname'], 'test_host')
            mock_mExecServiceCmd.assert_called_once_with('test_host', 'test_service', 'start', mock.ANY)

    def test_mExecute_multiple_hosts(self):
        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler.mExecServiceCmd") as mock_mExecServiceCmd:
            
            mock_mExecServiceCmd.side_effect = [
                {
                    'task_status': 'success',
                    'hostname': 'test_host1',
                    'error': '',
                    'message': 'test_service start successful for host test_host1'
                },
                {
                    'task_status': 'success',
                    'hostname': 'test_host2',
                    'error': '',
                    'message': 'test_service start successful for host test_host2'
                }
            ]
            _options = self.mGetContext().mGetArgsOptions()
            _options.jsonconf = {
                "task": "start",
                "service": "test_service",
                "host_nodes": ['test_host1', 'test_host2']
            }
            handler = ManageServiceHandler(_options)
            rc, response = handler.mExecute()
            self.assertEqual(rc, 0)
            self.assertEqual(response['service'], 'test_service')
            self.assertEqual(response['task'], 'start')
            self.assertEqual(len(response['node_task_status']), 2)
            self.assertEqual(response['node_task_status'][0]['task_status'], 'success')
            self.assertEqual(response['node_task_status'][0]['hostname'], 'test_host1')
            self.assertEqual(response['node_task_status'][1]['task_status'], 'success')
            self.assertEqual(response['node_task_status'][1]['hostname'], 'test_host2')
            self.assertEqual(mock_mExecServiceCmd.call_count, 2)

    def test_mExecServiceCmd_stop(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.connect_to_host") as mock_connect, \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd_check" , return_value=None), \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler._handle_start_stop_task") as mock_handle_start_stop_task:
            
            mock_connect.return_value.__enter__.return_value = dummy_node
            
            ManageServiceHandler.mExecServiceCmd('test_host', 'test_service', 'stop', TASK_CMDS)
            mock_handle_start_stop_task.assert_called_once_with(dummy_node, 'test_host', 'test_service', 'stop', TASK_CMDS)

    def test_mExecServiceCmd_start(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.connect_to_host") as mock_connect, \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd_check" , return_value=None), \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler._handle_start_stop_task") as mock_handle_start_stop_task:
            
            mock_connect.return_value.__enter__.return_value = dummy_node
            
            ManageServiceHandler.mExecServiceCmd('test_host', 'test_service', 'start', TASK_CMDS)
            mock_handle_start_stop_task.assert_called_once_with(dummy_node, 'test_host', 'test_service', 'start', TASK_CMDS)

    def test_mExecServiceCmd_status(self):

        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.connect_to_host") as mock_connect, \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd_check" , return_value=None), \
            mock.patch("exabox.jsondispatch.handler_manage_service.ManageServiceHandler._handle_status_task") as mock_handle_status_task:
            
            mock_connect.return_value.__enter__.return_value = dummy_node
            
            ManageServiceHandler.mExecServiceCmd('test_host', 'test_service', 'status', TASK_CMDS)
            mock_handle_status_task.assert_called_once_with(dummy_node, 'test_host', 'test_service', TASK_CMDS)

    def test__handle_start_stop_task_success(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", return_value=(0, "active", "")):
            res = ManageServiceHandler._handle_start_stop_task(dummy_node, "test_host", "test_service", "start", TASK_CMDS)
            self.assertEqual(res['task_status'], 'success')
            self.assertEqual(res['message'], 'test_service start successful for host test_host')

    def test__handle_start_stop_task_failure(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", return_value=(0, "failed", "")):
            res = ManageServiceHandler._handle_start_stop_task(dummy_node, "test_host", "test_service", "start", TASK_CMDS)
            self.assertEqual(res['task_status'], 'failure')
            self.assertEqual(res['message'], 'test_service start failed for host test_host')

    def test__handle_status_task_success(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", side_effect=[(0, "active", ""), (0, "1.0", "")]):
            res = ManageServiceHandler._handle_status_task(dummy_node, "test_host", "test_service", TASK_CMDS)
            self.assertEqual(res['task_status'], 'success')
            self.assertEqual(res['status'], 'active')
            self.assertEqual(res['version'], '1.0')

    def test__handle_status_task_failure(self):
        class DummyNode:
            pass
        dummy_node = DummyNode()

        with \
            mock.patch("exabox.jsondispatch.handler_manage_service.node_exec_cmd", return_value=(0, "", "")):
            res = ManageServiceHandler._handle_status_task(dummy_node, "test_host", "test_service", TASK_CMDS)
            self.assertEqual(res['task_status'], 'failure')
            self.assertEqual(res['status'], '')
            self.assertEqual(res['version'], '')

if __name__ == '__main__':
    unittest.main()