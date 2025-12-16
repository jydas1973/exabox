#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clucontrol_infrapatching.py /main/2 2025/09/02 17:58:33 ajayasin Exp $
#
# tests_clucontrol_infrapatching.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clucontrol_infrapatching.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ajayasin    08/05/25 - moving handler function from clucontrol.py
#                           clucommandhandler.py to reduce the clucontrol.py
#                           size
#    araghave    05/07/25 - Enh 37892080 - TO IMPLEMENT NEWER PATCHSWITCHTYPE
#                           CHANGES APPLICABLE TO ALL SWITCH TARGET TYPES AND
#                           PATCH COMBINATIONS
#    araghave    05/22/25 - Creation
#

import json
import unittest
import warnings
import copy
import os, re
import sys
from io import StringIO
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from paramiko.ssh_exception import SSHException
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.network.Connection import exaBoxConnection
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.utils.node import connect_to_host
from exabox.ovm.clumisc import ebCluSshSetup

class mockStream():

    def __init__(self, aStreamContents=["None"]):
        self.stream_content = aStreamContents

    def readlines(self):
        return self.stream_content

    def readline(self):
        return self.stream_content[0]

    def read(self):
        return self.stream_content[0]

class mockHVInstance():

    def __init__(self):
        self.__running_domus = list()

    def mSetRunningDomUs(self, aListOfRunningDomUs):
        self.__running_domus = copy.deepcopy(aListOfRunningDomUs)

    def mRefreshDomUs(self):
        return self.__running_domus

class testOptions(object): pass

class ebTestClucontrolClasses(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestClucontrolClasses, self).setUpClass(aGenerateDatabase=True, aEnableUTFlag=False)
        warnings.filterwarnings("ignore")
        self._db = ebGetDefaultDB()

    @patch('exabox.ovm.clucontrol.exaBoxNode.mSetUser', return_value="admin")
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mConnectandExecuteonCiscoSwitches', return_value="") 
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mSetCiscoSwitchSSHPasswordless', return_value=("scaqau08sw-adm0.us.oracle.com", "scaqau08sw-adm0.us.oracle.com"))
    def test_mHandlerAdminSwitchConnect(self, mock_mSetUser, mock_mConnectandExecuteonCiscoSwitches, mock_mSetCiscoSwitchSSHPasswordless):
        ebLogInfo("Running unit test on mHandlerAdminSwitchConnect.")
        self.mGetClubox().mGetCommandHandler().mHandlerAdminSwitchConnect()
        ebLogInfo("Unit test on mHandlerAdminSwitchConnect succeeded.")
    
    @patch('exabox.ovm.clucontrol.exaBoxNode.mSetUser', return_value="admin")
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mConnectandExecuteonCiscoSwitches', return_value="")
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mSetCiscoSwitchSSHPasswordless', return_value=("scaqau08sw-adm0.us.oracle.com", "scaqau08sw-adm0.us.oracle.com"))
    def test_mReturnandConnectRoceSpineSwitches(self, mock_mSetUser, mock_mConnectandExecuteonCiscoSwitches, mock_mSetCiscoSwitchSSHPasswordless):
        ebLogInfo("Running unit test on mReturnandConnectRoceSpineSwitches")
        self.mGetClubox().mReturnandConnectRoceSpineSwitches()
        ebLogInfo("Unit test on mReturnandConnectRoceSpineSwitches succeeded.")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnandConnectRoceSpineSwitches', return_value=("scaqau08roces0.us.oracle.com"))
    def test_mReturnSwitches(self, mock_mReturnandConnectRoceSpineSwitches):
        _list_of_switches = []
        ebLogInfo("Running unit test on mReturnSwitches")
        _list_of_switches = self.mGetClubox().mReturnSwitches(True, True)
        ebLogInfo("Unit test on mReturnSwitches succeeded.")

if __name__ == "__main__":
    unittest.main(warnings='ignore')
