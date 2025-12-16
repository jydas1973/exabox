#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluconfig.py 
#
# tests_cluconfig.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluconfig.py - xml parsing
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#
#    ajayasin     06/02/25 - Creation
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
from exabox.ovm.cluconfig import ebCluHeaderConfig, ebCluMachinesConfig, \
ebCluClustersConfig, ebCluClusterScansConfig, ebCluDatabaseHomesConfig, \
ebCluDabasesConfig, ebCluNetworkConfig, ebCluNetworksConfig, ebCluVMSizesConfig, \
ebCluSwitchesConfig, ebCluEsRacksConfig, ebCluUsersConfig, ebCluGroupsConfig,\
ebCluIlomsConfig, ebCluStorageDesc, ebCluDRVipConfig, ebCluDRScanConfig
import os, sys, subprocess, uuid, os.path, shlex, select, pwd, math, pty, stat


class ebTestNode(ebTestClucontrol):

    def test_mCluConfig_ebCluMachinesConfig_mDumpConfig(self):
        #Init new Args
        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _cluconfig = ebCluMachinesConfig(_ebox.mGetConfig())
        _cluconfig.mDumpConfig()


    def test_mCluConfig_ebCluNetworksConfig_mDumpConfig(self):
        #Init new Args
        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _cluconfig = ebCluNetworksConfig(_ebox.mGetConfig())
        _cluconfig.mDumpConfig()
        _ebox.mExecuteCmdLog(f"/bin/mkdir -p /tmp/WorkDir")
        _ebox.mExecuteCmdLog(f"/bin/mkdir -p /tmp/WorkDir")
        _ebox.mExecuteCmdLog(f"/bin/mkdir -p /tmp/WorkDir",aLogAsWarn=True)
        #_ebox.mSetupOedaStaging(aJob)

def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestNode('test_mCluConfig_ebCluMachinesConfig_mDumpConfig'))
    suite.addTest(ebTestNode('test_mCluConfig_ebCluNetworksConfig_mDumpConfig'))
    
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())


