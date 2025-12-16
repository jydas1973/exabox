#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/healthcheck/tests_cluexachk.py /main/8 2024/09/19 16:46:22 remamid Exp $
#
# tests_cluexachk.py
#
# Copyright (c) 2021, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluexachk.py
#
#    DESCRIPTION
#      Unit test cases for the file $EC_ROOT/exabox/healthcheck/cluexachk.py
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    remamid      09/18/24 - test case for bug 37005729
#    ajayasin     04/06/22 - ut addition
#    ajayasin     01/10/22 - cluexachk unit test file added
#    ajayasin     01/06/22 - Creation
#
from asyncio.log import logger
import os
import json
import unittest
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
import copy
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.healthcheck.cluexachk import ebCluExachk as cluexachk
import warnings
from ast import literal_eval

from exabox.core.Error import ExacloudRuntimeError


class testebCluExachk(cluexachk):
    def __init__(self,aCluHealthCheck, aOptions):
        cluexachk.__init__(self,aCluHealthCheck, aOptions)
    def mInstallAhf(self,deviceType,aOptions=None,_selected_host = None):
        return {'scaqab10adm01.us.oracle.com': True}

class ebTestNode(ebTestClucontrol):

    def test_ahf_install_on_domU_case1(self):
        ebLogInfo("Running unit test for cluexachk.")
        ebLogInfo("AHF install path /u01/oracle.ahf/data")

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u01/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        #aOptions.jsonconf
        ebox.mSetOptions(_options)
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        aCluHealthCheck = "aCluHealthCheck"
        testObj = cluexachk(aCluHealthCheck,_options)
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        _remote_ahf_install_path = ebox.mCheckSubConfigOption('ahf_paths', 'remote_ahf_install_path')
        _data_path = testObj.mRetriveAhfInstallDataPath(node,_remote_ahf_install_path)
        assert _data_path == "/u01/oracle.ahf/data\n"

    def test_ahf_install_on_domU_case2(self):
        ebLogInfo("Running unit test for cluexachk.")
        ebLogInfo("/opt/oracle.ahf/install.properties does not exist")


        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=1, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        #aOptions.jsonconf
        ebox.mSetOptions(_options)
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        aCluHealthCheck = "aCluHealthCheck"
        testObj = cluexachk(aCluHealthCheck,_options)
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        _remote_ahf_install_path = ebox.mCheckSubConfigOption('ahf_paths', 'remote_ahf_install_path')
        _data_path = testObj.mRetriveAhfInstallDataPath(node,_remote_ahf_install_path)
        assert _data_path != "/u01/oracle.ahf/data\n"

    def test_ahf_install_on_domU_case3(self):
        ebLogInfo("Running unit test for cluexachk.")
        ebLogInfo("AHF install path /u02/oracle.ahf/data")

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        #aOptions.jsonconf
        ebox.mSetOptions(_options)
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        aCluHealthCheck = "aCluHealthCheck"
        testObj = cluexachk(aCluHealthCheck,_options)
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        _remote_ahf_install_path = ebox.mCheckSubConfigOption('ahf_paths', 'remote_ahf_install_path')
        _data_path = testObj.mRetriveAhfInstallDataPath(node,_remote_ahf_install_path)
        assert _data_path == "/u02/oracle.ahf/data\n"

    def test_ahf_install_on_cps(self):
        ebLogInfo("AHF install path cps")

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        ebox.mSetOciExacc(True)
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        self.mGetContext().mSetConfigOption('remote_cps_host', 'iad163933exdcp02')
        #aOptions.jsonconf
        #ebox.mSetOptions(_options)
        _hcObj = ebCluHealthCheck(ebox, _options)
        testObj = cluexachk(_hcObj,_options)
        try:
            testObj.mInstallAhfOnRemoteCps(_options)
        except Exception as e:
            logger.info(f"Exception while Installing AHF: {e}")

    def test_mAhfCtrlPlaneVersionCheck(self):
        ebLogInfo("AHF install path cps")

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        ebox.mSetOciExacc(True)
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        _hcObj = ebCluHealthCheck(ebox, _options)
        testObj = cluexachk(_hcObj,_options)
        #self.mGetContext().mSetConfigOption('remote_cps_host', 'iad163933exdcp02')
        #aOptions.jsonconf
        #ebox.mSetOptions(_options)
        if os.path.exists("./oracle.ahf/install.properties"):
            os.remove("./oracle.ahf/install.properties")
        if not os.path.exists("./oracle.ahf"):
            os.makedirs("./oracle.ahf")
        fd = open("./oracle.ahf/install.properties", "w+")
        fd.write("BUILD_VERSION=214300")
        fd.close()
        try:
            testObj.mAhfCtrlPlaneVersionCheck(".",".")
        except Exception as e:
            logger.error('*** AHF install failed on control plane with exception : %s' % (str(e)))
    
    def test_mGetHigherAHFPath(self):
        """
        CP ahf_setup path is set wrong to test file not found flow
        this shall return version as 0 if file not found
        """
        ebLogInfo("AHF install path cps")
        _cntrlPlanePath = ''

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /var/opt/oracle/misc/ahf/ahf_setup", aRc=0, aPersist=True),
                    exaMockCommand("/var/opt/oracle/misc/ahf/ahf_setup -v", aStdout="AHF Build ID : 23200020230302111526\n AHF Build Platform : Linux\n AHF Build Architecture : x86_64\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ],
            self.mGetRegexLocal(): [
                exaMockCommand(f"{_cntrlPlanePath} -v", aStdout="AHF Build ID : 22330020230116220213\n AHF Build Platform : Linux\n AHF Build Architecture : x86_64\n", aRc=0, aPersist=True)
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        _hcObj = ebCluHealthCheck(ebox, _options)
        testObj = cluexachk(_hcObj,_options)
        _path = testObj.mGetHigherAHFPath(node, _cntrlPlanePath)
        ebLogInfo(f'Selected AHF path: {_path}')
        assert _path == ebox.mCheckSubConfigOption('ahf_paths', 'remote_ahf_dbaas_path')


    def test_mCopyAhfImage(self):
        ebLogInfo("ahf_setup file copy to remote node")
        _ahf_bin_path = os.getcwd()
        _remote_ahf_bin_path = "/opt/oracle.SupportTools/ahf/ahf_setup"

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("df -PBM",aRc=0, aPersist=True),
                    exaMockCommand("rm -rf*", aRc=0, aPersist=True),
                    exaMockCommand("mkdir*", aRc=0, aPersist=True),
                    exaMockCommand("scp *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /opt/oracle.SupportTools/ahf/ahf_setup", aRc=0, aPersist=True),
                    exaMockCommand("chmod 700*", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        _hcObj = ebCluHealthCheck(ebox, _options)
        testObj = cluexachk(_hcObj,_options)
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        with patch('os.path.isfile'):
            _ret = testObj.mCopyAhfImage(node,_ahf_bin_path,_remote_ahf_bin_path)
        assert _ret != 0


def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestNode('test_ahf_install_on_domU_case1'))
    suite.addTest(ebTestNode('test_ahf_install_on_domU_case2'))
    suite.addTest(ebTestNode('test_ahf_install_on_domU_case3'))
    suite.addTest(ebTestNode('test_ahf_install_on_cps'))
    suite.addTest(ebTestNode('test_mAhfCtrlPlaneVersionCheck'))
    suite.addTest(ebTestNode('test_mGetHigherAHFPath'))
    suite.addTest(ebTestNode('test_mCopyAhfImage'))
    #suite.addTest(ebTestNode('test_ahf_local_run_exachk_shared'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
