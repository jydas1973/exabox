#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_cps_switchover.py /main/4 2024/08/22 16:18:00 hgaldame Exp $
#
# tests_cps_switchover.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_cps_switchover.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    08/17/24 - 36959621 - oci/exacc fedramp: change keepalived
#                           manual-switchover.sh script location on cps remote
#                           manager
#    hgaldame    02/21/24 - oci/exacc: enhanced switchover remote manager
#                           endpoint on cps
#    oespinos    04/27/22 - Add unittest for switchover
#    oespinos    04/27/22 - Creation
#

import unittest
import tempfile
import uuid
import os

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch, Mock, ANY, call

from exabox.managment.src.CpsEndpoint import CpsEndpoint

class ebTestRemoteManagmentSwitchover(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)

    def test_000_listcps(self):

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _cps_dict = {"MASTER": {"hostname": "cps1", "cps_version":"", "image_version":""},
                     "STANDBY":{"hostname": "cps2", "cps_version":"", "image_version":""}}

        _response = {}
        _endpoint = CpsEndpoint(None, None, _response, _shared)
        _endpoint.mGet(aMock=True)

        self.assertTrue("text" in _response)
        self.assertEqual(_response["text"], _cps_dict)

    def test_001_switchover(self):

        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _body = {
            "type": "cpsswitchover", 
            "bundle": "LATEST"
        }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _endpoint.mPost(aMock=True)

        self.assertTrue("text" in _response)
        self.assertTrue("status" in _response["text"])
        self.assertEqual(_response['text']["status"], "pending")
    
    def test_002_switchover_run_no_remote_host(self):
        """
            Scenario: Run switchover on single cps host
            When switchover is attempted on single cps (no standby node)
            Then switchover should fail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsswitchover", 
            "bundle": "LATEST"
        }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_fd, _log_path = tempfile.mkstemp()

        with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetRemoteCPS', return_value=None):
            _rc = _endpoint._CpsEndpoint__mCpsSwitchoverRun(_log_path, _process_id, aCustomArgs=None)
            assert _rc 
            assert _rc.get("return_code", 0) == 1
            assert _rc.get("error_code") == "0x0702000F"

        if _log_fd:
            os.close(_log_fd)
    
    def test_003_switchover_run_same_host(self):
        """
            Scenario: Run switchover on same host
            When switchover is attempted on master cps
            and the value "remote_cps_host" on exabox.conf is the same
            than localhost
            Then switchover should fail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsswitchover", 
            "bundle": "LATEST"
        }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_fd, _log_path = tempfile.mkstemp()
        _localhost = "cpshostname01.us.oracle.com"
        _remotehost = "cpshostname01"
        with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetRemoteCPS', return_value=_remotehost),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetLocalCPS', return_value=_localhost):
            _rc = _endpoint._CpsEndpoint__mCpsSwitchoverRun(_log_path, _process_id, aCustomArgs=None)
            assert _rc 
            assert _rc.get("return_code", 0) == 1
            assert _rc.get("error_code") == "0x0702000F"
        if _log_fd:
            os.close(_log_fd)
    
        
    def test_004_switchover_ongoing_op(self):
        """
            Scenario: Run switchover meanwhile exacloud has running operations
            When exacloud has ongoing operations
            Then switchover  should fail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsswitchover", 
            "bundle": "LATEST"
        }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_fd, _log_path = tempfile.mkstemp()
        _localhost = "cpshostname01.us.oracle.com"
        _remotehost = "cpshostname02"
        with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetRemoteCPS', return_value=_remotehost),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetLocalCPS', return_value=_localhost),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mHasOngoingOperations', return_value=True):
            _rc = _endpoint._CpsEndpoint__mCpsSwitchoverRun(_log_path, _process_id, aCustomArgs=None)
            assert _rc 
            assert _rc.get("return_code", 0) == 1
            assert _rc.get("error_code") == "0x0702000F"
        if _log_fd:
            os.close(_log_fd)

    def test_005_switchover_not_master_node(self):
        """
            Scenario: Run switchover on non-master cps
            When switchover is attempted on non-master cps
            Then switchover should fail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsswitchover", 
            "bundle": "LATEST"
        }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_fd, _log_path = tempfile.mkstemp()
        _localhost = "cpshostname01.us.oracle.com"
        _remotehost = "cpshostname02"
        with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetRemoteCPS', return_value=_remotehost),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetLocalCPS', return_value=_localhost),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mHasOngoingOperations', return_value=False),\
            patch('os.path.exists', return_value=False):
            _rc = _endpoint._CpsEndpoint__mCpsSwitchoverRun(_log_path, _process_id, aCustomArgs=None)
            assert _rc 
            assert _rc.get("return_code", 0) == 1
            assert _rc.get("error_code") == "0x0702000F"
        if _log_fd:
            os.close(_log_fd)

    def test_006_switchover_run_etc(self):
        """
            Scenario: Run switchover using /etc/keepalived/manual-switchover.sh 
                      if /usr/libexec/keepalived/manual-switchover.sh is not present
            When switchover is attempted and switchover succeed 
            Then switchover response should success
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsswitchover", 
            "bundle": "LATEST"
        }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_fd, _log_path = tempfile.mkstemp()
        _master_node = "cpshostname01"
        _stanby_node = "cpshostname02"
        _remote_mode = _stanby_node
        with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetRemoteCPS', side_effect=[_remote_mode, _remote_mode]),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetLocalCPS', return_value=_master_node),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mHasOngoingOperations', return_value=False),\
            patch('os.path.exists', side_effect=[True, False]),\
            patch('time.sleep', return_value=None),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mDetectMasterCps', side_effect=[_master_node, _stanby_node, _stanby_node]),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mDetectStandbyCps', side_effect=[_stanby_node, _master_node, _master_node] ),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mBashExecution', return_value=(0,"","")) as spy_bash_exec: 
            _rc = _endpoint._CpsEndpoint__mCpsSwitchoverRun(_log_path, _process_id, aCustomArgs=None)
            assert _rc == 0
            spy_bash_exec.assert_called_once_with(['/bin/sudo', '/bin/sh', '/etc/keepalived/manual-switchover.sh', '--switchover', '--sleeptime', '60'], aRedirect=ANY)
        if _log_fd:
            os.close(_log_fd)
    
    def test_007_switchover_run_libexec(self):
        """
            Scenario: Run switchover using /usr/libexec/keepalived/manual-switchover.sh
            When switchover is attempted and switchover succeed
            Then switchover response should success
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsswitchover", 
            "bundle": "LATEST"
        }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _process_id = str(uuid.uuid1(clock_seq=1))
        _log_fd, _log_path = tempfile.mkstemp()
        _master_node = "cpshostname01"
        _stanby_node = "cpshostname02"
        _remote_mode = _stanby_node
        with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetRemoteCPS', side_effect=[_remote_mode, _remote_mode]),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mGetLocalCPS', return_value=_master_node),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mHasOngoingOperations', return_value=False),\
            patch('os.path.exists', side_effect=[True, True]),\
            patch('time.sleep', return_value=None),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mDetectMasterCps', side_effect=[_master_node, _stanby_node, _stanby_node]),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint._mDetectStandbyCps', side_effect=[_stanby_node, _master_node, _master_node] ),\
            patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mBashExecution', return_value=(0,"","")) as spy_bash_exec: 
            _rc = _endpoint._CpsEndpoint__mCpsSwitchoverRun(_log_path, _process_id, aCustomArgs=None)
            assert _rc == 0
            spy_bash_exec.assert_called_once_with(['/bin/sudo', '/bin/sh', '/usr/libexec/keepalived/manual-switchover.sh', '--switchover', '--sleeptime', '60'], aRedirect=ANY)
        if _log_fd:
            os.close(_log_fd)



if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file