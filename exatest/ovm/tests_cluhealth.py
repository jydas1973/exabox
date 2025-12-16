#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluhealth.py /main/1 2025/07/15 06:42:50 aypaul Exp $
#
# tests_cluhealth.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluhealth.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      07/14/25 - Creation
#

import unittest, warnings
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, Mock

from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.log.LogMgr import ebLogInfo
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class mockexecutecmd():

    def __init__(self, buffer):
        self.data = None

    def readlines(self):
        return self.data

    def read(self):
        return self.data

class ebTestCluhealth(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluhealth, self).setUpClass()
        warnings.filterwarnings("ignore")

    def test_mValidateCluster(self):
        ebLogInfo("Running unit test on ebCluHealthCheck.mValidateCluster")
        ebox = self.mGetClubox()
        mocknetworks = Mock()
        mocknetwork = Mock()
        mocknetwork.mGetNetNatAddr.return_value = "mockip"
        mocknetworks.mGetNetworkConfigByNatName.return_value = mocknetwork

        with patch('exabox.ovm.cluhealth.ebCluHealthCheck.mReadHcConfig'),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mVerifyPkeys'),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mGetLongRunCheck', return_value=False),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mPublishHealthCheckReport'),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mEstablishSSH'),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mGetConnectCheck'),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mValidateSwitches'),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mValidateDom0s'),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mValidateDomUs'),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mValidateCells'),\
             patch('exabox.ovm.cluhealth.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.ovm.cluhealth.exaBoxNode.mGetCmdExitStatus', return_value=True),\
             patch('exabox.ovm.cluhealth.exaBoxNode.mExecuteCmd', return_value=mockexecutecmd(None)),\
             patch('exabox.ovm.cluhealth.exaBoxNode.mDisconnect'),\
             patch('exabox.ovm.cluhealth.ebClusterNode.mSetNetworkIp'),\
             patch('exabox.ovm.cluhealth.ebClusterNode.mGetSSHConnection', return_value=True),\
             patch('exabox.ovm.cluhealth.ebClusterNode.mGetPingable', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworks', new=mocknetworks),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnSwitches'),\
             patch('exabox.ovm.cluhealth.ebCluHealthCheck.mReadHcNameConfig'):
             
             ebox.mUpdateInMemoryXmlConfig(ebox.mGetConfigPath(), ebox.mGetArgsOptions())
             cluhealthinstance = ebCluHealthCheck(ebox, ebox.mGetArgsOptions())
             cluhealthinstance.mValidateCluster()

        ebLogInfo("Unit test on ebCluHealthCheck.mValidateCluster completed successfully.")

if __name__ == '__main__':
    unittest.main() 