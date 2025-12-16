#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_cron_job.py /main/1 2022/12/13 15:57:01 anhiguer Exp $
#
# tests_cron_job.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_cron_job.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    anhiguer    11/24/22 - Creation
#
import unittest
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.managment.src.CronJobEndPoint import CronJobEndPoint

from unittest.mock import Mock, patch
import subprocess
class ebTestRemoteManagmentEditor(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)
    
    @patch("subprocess.Popen")
    def test_mGet(self, _mock_subproc_popen):
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Execute endpoint
        _args = {}
        _endpoint = CronJobEndPoint(_args, _args, _args, _shared)
        _process_mock = Mock()
        _attrs = {"communicate.return_value": ("test_list", ""), "returncode" : 0}
        _process_mock.configure_mock(**_attrs)
        _mock_subproc_popen.return_value = _process_mock
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()["status"], 200)
        self.assertEqual(_endpoint.mGetResponse()["text"], "test_list")

    @patch("subprocess.Popen")
    def test_mGet_different_user(self, _mock_subproc_popen):
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Execute endpoint
        _args = {
            "user": "my_user"
        }
        _endpoint = CronJobEndPoint(_args, _args, _args, _shared)
        _process_mock = Mock()
        _attrs = {"communicate.return_value": ("test_list", ""), "returncode" : 0}
        _process_mock.configure_mock(**_attrs)
        _mock_subproc_popen.return_value = _process_mock
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()["status"], 200)
        self.assertEqual(_endpoint.mGetResponse()["text"], "test_list")

    @patch("subprocess.Popen")
    def test_mPut_problem_during_cmd(self, _mock_subproc_popen):
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        # Execute endpoint
        _args = {}
        _endpoint = CronJobEndPoint(_args, _args, _args, _shared)
        _process_mock = Mock()
        _attrs = {"communicate.return_value": ("", ""), "returncode" : 1}
        _process_mock.configure_mock(**_attrs)
        _mock_subproc_popen.return_value = _process_mock
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()["status"], 500)
        self.assertEqual(_endpoint.mGetResponse()["error"], "Error listing crons ")
if __name__ == "__main__":
    unittest.main(warnings="ignore")
