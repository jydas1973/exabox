#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clucontrol_2.py /main/12 2025/12/01 14:45:30 remamid Exp $
#
# tests_clucontrol_2.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clucontrol_2.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    remamid     11/17/25 - Add unittest for
#                           mModifyAndUploadCloudPropertiesExaCC bug38581933
#    nelango     10/03/25 - Bug 38102710: Handle empty bond slave output
#    remamid     09/15/25 - unittest for bug 38317248
#    bhpati      08/22/25 - Bug 38240277 - memory reshape precheck failing on
#                           retry when one node is already reshaped
#    avimonda    09/04/24 - Bug 38179586 - OCI: VMLOCALSTORAGE OPERATION FAILED
#                           DUE TO RAC ONE DATABASE
#    nelango     08/11/25 - Bug 38257756: Lists failed DBs after reboot
#    bhpati      08/07/25 - Bug 38204376 - Addvmcloudvmcluster Failed Missing
#                           Nftables
#    bhpati      07/18/25 - Bug 38133410 - Memory reshape workflow fails to set
#                           hugepages
#    nelango     07/14/25 - Bug 38019309: Adding test for mStartVMAfterReshape
#                           dbs not started after reboot
#    nelango     07/07/25 - Creation
#
import datetime
import json
import unittest
import warnings
import copy
import os, re, io
import sys
from io import StringIO
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, Mock
from paramiko.ssh_exception import SSHException
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogWarn
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.network.Connection import exaBoxConnection
from exabox.ovm.clucontrol import exaBoxCluCtrl, gReshapeError
from exabox.utils.node import connect_to_host
from exabox.core.Node import exaBoxNode
from exabox.ovm.clumisc import mWaitForSystemBoot, ebCluStorageReshapePrecheck
from exabox.ovm.hypervisorutils import getHVInstance
from exabox.ovm.cludbaas import ebCluDbaas
from exabox.ovm.utils.clu_utils import ebCluUtils


class mockHVInstance():

    def __init__(self):
        self.__running_domus = list()

    def mSetRunningDomUs(self, aListOfRunningDomUs):
        self.__running_domus = copy.deepcopy(aListOfRunningDomUs)

    def mRefreshDomUs(self):
        return self.__running_domus

class ebTestClucontrolClasses_2(ebTestClucontrol):
    
    @classmethod
    def setUpClass(cls):
        super(ebTestClucontrolClasses_2, cls).setUpClass(aGenerateDatabase=True, aEnableUTFlag=False)
        warnings.filterwarnings("ignore")
        cls._db = ebGetDefaultDB()
        cls.utils = ebCluUtils()
    
    def test_mUpdateHugePagesSysctlConf(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mUpdateHugePagesSysctlConf")
        _newmem = "49152"
        _currvmem = "65536"
        _MinHugepageMem = "26"
        aDomU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("/bin/grep Hugepagesize /proc/meminfo*", aRc=0, aStdout="2", aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSysCtlConfigValue", return_value=('/etc/sysctl.conf', "13210")),\
             patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSysCtlConfigValue", return_value=True):
            self.assertEqual(0, self.mGetClubox().mUpdateHugePagesSysctlConf(aDomU, _currvmem, _newmem, _MinHugepageMem))
    
    @patch("exabox.ovm.clucontrol.exaBoxNode")
    @patch("exabox.ovm.cludbaas.ebCluDbaas")
    @patch("exabox.ovm.clucontrol.getHVInstance")    
    def test_mManageVMMemory(self, aMockHVInstance, mock_dbaasobj, mock_exaBoxNode):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mManageVMMemory")
        aOptions = MagicMock()
        aOptions.jsonconf = {
        "vms": [
            {"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": 1024},
            {"hostname": "scaqab10client02vm08.us.oracle.com", "gb_memory": 1024}
            ]
        }      
        aMockHVInstance.return_value.getDom0FreeMem.return_value = 5048576  # Mock freemem
        aMockHVInstance.return_value.mGetVMMemory.return_value = 250000  # Mock _currvmem
        aMockHVInstance.return_value.mSetVMMemory.return_value = 0
        self.mGetClubox()._host_d = {'scaqab10client01vm08.us.oracle.com': 512 }
        mock_dbaasobj.mExecuteDBaaSAPIAction.return_value = {'get': {'is_new_mem_sz_allowed': 1, 'min_reqd_hugepages_memory': 123}}
        _dbaasData = {'get': {'is_new_mem_sz_allowed': 1, 'min_reqd_hugepages_memory': 123}}
        _node = mock_exaBoxNode.return_value
        _node.mExecuteCmd.return_value = (None, MagicMock(read=MagicMock(return_value=[''])), MagicMock(read=MagicMock(return_value=[''])))
        
        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost", return_value=True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM", return_value=True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.isATPCluster", return_value=False),\
            patch("exabox.ovm.cludbaas.ebCluDbaas.mConnect"),\
            patch("exabox.ovm.cluelasticcompute.ebCluDbaas.mCopyFileToDomU"),\
            patch("exabox.ovm.cluelasticcompute.ebCluDbaas.mExecCommandOnDomU", return_value = (None, 0, 0)),\
            patch("exabox.ovm.cluelasticcompute.ebCluDbaas.mReadStatusFromDomU", return_value = {'id': 'abc','min_reqd_hugepages_memory': 123,'is_new_mem_sz_allowed': 1}),\
            patch("exabox.ovm.cluelasticcompute.ebCluDbaas.mCopyDomuInfoLog"),\
            patch("exabox.ovm.cluelasticcompute.ebCluDbaas.mWaitForJobComplete", return_value = 0),\
            patch("exabox.ovm.cludbaas.ebCluDbaas.mExecuteDBaaSAPIAction", return_value=0),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale", return_value=False),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSysCtlConfigValue", return_value=(None,2570)),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateHugePagesSysctlConf", return_value = 0),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSysCtlConfigValue", return_value = True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsUp", return_value = True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckDBIsUp", return_value = True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mShutdownVMForReshape", return_value = (True, True)),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mStartVMAfterReshape"):
            self.assertEqual(0, self.mGetClubox().mManageVMMemory('VMCmd', '_all_', aOptions))
    
    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_mManageVMMemory_retry(self, aMockHVInstance):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mManageVMMemory Retry")
        pairs = self.mGetClubox().mReturnDom0DomUPair()
        aOptions = MagicMock()
        aOptions.jsonconf = {
        "vms": [
            {"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": 1024},
            {"hostname": "scaqab10client02vm08.us.oracle.com", "gb_memory": 2048}
            ]
        }
        aMockHVInstance.return_value.getDom0FreeMem.return_value = 5048576  # Mock freemem
        aMockHVInstance.return_value.mGetVMMemory.return_value = 1048576  # Mock _currvmem
        aMockHVInstance.return_value.mSetVMMemory.return_value = 0
        self.mGetClubox()._host_d = {'scaqab10client01vm08.us.oracle.com': 1024 }  # Set _memsizeMB to 1024MB

        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost", return_value=True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM", return_value=True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.isATPCluster", return_value=False),\
            patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.ovm.cludbaas.ebCluDbaas.mExecuteDBaaSAPIAction', return_value=0),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale", return_value=False),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSysCtlConfigValue", return_value=(None,2570)),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateHugePagesSysctlConf", return_value = 0),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSysCtlConfigValue", return_value = True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsUp", return_value = True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckDBIsUp", return_value = True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mShutdownVMForReshape", return_value = (True, True)),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mStartVMAfterReshape"):
            self.assertEqual(0, self.mGetClubox().mManageVMMemory('VMCmd', '_all_', aOptions))  
    
    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_mManageVMMemory_retry_fail(self, aMockHVInstance):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mManageVMMemory Retry Fail")
        pairs = self.mGetClubox().mReturnDom0DomUPair()
        aOptions = MagicMock()
        aOptions.jsonconf = {
        "vms": [
            {"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": 1024},
            {"hostname": "scaqab10client02vm08.us.oracle.com", "gb_memory": 2048}
            ]
        }
        aMockHVInstance.return_value.getDom0FreeMem.return_value = 5048576  # Mock freemem
        aMockHVInstance.return_value.mGetVMMemory.return_value = 1048576  # Mock _currvmem
        aMockHVInstance.return_value.mSetVMMemory.return_value = 0
        self.mGetClubox()._host_d = {'scaqab10client01vm08.us.oracle.com': 1024 }  # Set _memsizeMB to 1024MB

        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost", return_value=True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM", return_value=True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.isATPCluster", return_value=False),\
            patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.ovm.cludbaas.ebCluDbaas.mExecuteDBaaSAPIAction', return_value=0),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale", return_value=False),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSysCtlConfigValue", return_value=(None,None)),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateHugePagesSysctlConf", return_value = 0),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSysCtlConfigValue", return_value = True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsUp", return_value = True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckDBIsUp", return_value = True),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mShutdownVMForReshape", return_value = (True, True)),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mStartVMAfterReshape"):
            with self.assertRaises(ExacloudRuntimeError) as cm:
                self.mGetClubox().mManageVMMemory('VMCmd', '_all_', aOptions)
            self.assertEqual(cm.exception.args[0], 0x0743)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOciExaCCServicesSetup", return_value=None)
    def test_mSetupNatNfTablesOnDom0v2_create_Nftables(self, mGetOciExaCCServicesSetupMock):
        # Test case: Error handling during NFT table creation
        aDom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand('/bin/test -e /etc/sysconfig/network-scripts/ifcfg-vmeth0')
                ],
                [
                    exaMockCommand("nft -as list table ip6 filter", aStdout="", aPersist=True),
                    exaMockCommand("/usr/sbin/nft -as list table ip filter", aStdout="", aPersist=True),
                    exaMockCommand("nft add table ip6 filter",  aRc=1, aPersist=True),
                    exaMockCommand("/usr/sbin/nft add chain ip filter INPUT '{type filter hook input priority filter; policy accept;}'",  aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/nft add chain ip filter FORWARD '{type filter hook forward priority filter; policy drop;}'",  aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/nft add chain ip filter OUTPUT '{type filter hook output priority filter; policy accept;}'",  aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/nft add rule ip filter INPUT iifname lo counter accept",  aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/nft add rule ip filter INPUT iifname lo counter accept",  aRc=0, aPersist=True),
                    exaMockCommand("nft .*", aPersist=True),
                    exaMockCommand("/usr/sbin/nft list tables | grep 'ip6 nat",  aRc=0, aPersist=True),
                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                    exaMockCommand("systemctl is-active nftables", aRc=0, aPersist=True),
                    exaMockCommand("systemctl start nftables", aRc=0, aPersist=True),
                    exaMockCommand("cat /etc/nftables/exadata.nft", aPersist=True)                    
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', os.path.join(self.mGetPath(), "ocpsSetup.json"))
        self.mGetClubox().mSetOciExacc(True)
        self.__shared_env = False       
        self.mGetClubox().mSetupNatNfTablesOnDom0v2(aDom0s=['scaqab10adm01.us.oracle.com'])
    
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOciExaCCServicesSetup", return_value=None)
    def test_mSetupNatNfTablesOnDom0v2_aModeTrue(self, mGetOciExaCCServicesSetuMock):
        aDom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        aMode=True
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand('/bin/test -e /etc/sysconfig/network-scripts/ifcfg-vmeth0')
                ],
                [
                    exaMockCommand("nft -as list table ip6 filter", aStdout="", aPersist=True),
                    exaMockCommand("nft add table ip6 filter",  aRc=0, aPersist=True),
                    exaMockCommand("nft .*", aPersist=True),
                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                    exaMockCommand("systemctl is-active nftables", aRc=0, aPersist=True),
                    exaMockCommand("systemctl start nftables", aRc=0, aPersist=True),
                    exaMockCommand("cat /etc/nftables/exadata.nft", aPersist=True)                    
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', os.path.join(self.mGetPath(), "ocpsSetup.json"))
        self.mGetClubox().mSetOciExacc(True)
        self.__shared_env = False
        self.mGetClubox().mSetupNatNfTablesOnDom0v2(aMode, aDom0s=['scaqab10adm01.us.oracle.com'])

    def test_mSetupNatNfTablesOnDom0v2_notOciExacc(self):       
        aDom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("nft -as list table ip filter", aStdout="", aPersist=True),
                    exaMockCommand("nft -as list ruleset", aStdout="", aPersist=True),
                    exaMockCommand("nft .*", aPersist=True),

                    exaMockCommand("cp.*date.*", aPersist=True),
                    exaMockCommand("nft list ruleset > /etc/nftables/exadata.nft", aPersist=True),
                    exaMockCommand("systemctl is-active nftables", aPersist=True),
                    exaMockCommand("systemctl start nftables", aRc=0, aPersist=True),
                    exaMockCommand("cat /etc/nftables/exadata.nft", aPersist=True),                    
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', os.path.join(self.mGetPath(), "ocpsSetup.json"))
        self.mGetClubox().mSetOciExacc(False)
        self.mGetClubox().mSetupNatNfTablesOnDom0v2(aDom0s=['scaqab10adm01.us.oracle.com'])
                
    def test_getNotUpDbsList_all_up(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on getNotUpDbsList - all DBs up")
        mock_db = MagicMock()
        mock_db.mGetDBListByNode.return_value = "DB1 DB2"
        mock_ctrl = MagicMock()
        mock_ctrl.mGetActiveDbInstances.return_value = ["DB1", "DB2"]
        with patch('exabox.ovm.utils.clu_utils.ebGetDefaultDB', return_value=mock_db):
            utils = ebCluUtils(aExaBoxCluCtrl=mock_ctrl) 
            result = utils.getNotUpDbsList("domU1")
        self.assertEqual(result, [])
        mock_db.mGetDBListByNode.assert_called_with("domU1")
        mock_ctrl.mGetActiveDbInstances.assert_called_with("domU1")

    def test_getNotUpDbsList_failed(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on getNotUpDbsList - not all DBs up")
        mock_db = MagicMock()
        mock_db.mGetDBListByNode.return_value = "DB1 DB2 DB3"
        mock_ctrl = MagicMock()
        mock_ctrl.mGetActiveDbInstances.return_value = ["DB1", "DB2"]
        with patch('exabox.ovm.utils.clu_utils.ebGetDefaultDB', return_value=mock_db):
            utils = ebCluUtils(aExaBoxCluCtrl=mock_ctrl)
            result = utils.getNotUpDbsList("domU1")
        self.assertEqual(result, ["DB3"])
        mock_db.mGetDBListByNode.assert_called_with("domU1")
        mock_ctrl.mGetActiveDbInstances.assert_called_with("domU1")

    @patch('exabox.ovm.clucontrol.ebGetDefaultDB', return_value=MagicMock())
    @patch('exabox.ovm.clucontrol.start_domu')
    @patch.object(exaBoxCluCtrl, 'mCheckIfCrsDbsUp')
    @patch.object(exaBoxCluCtrl, 'mCheckDBIsUp', return_value=True)
    @patch.object(exaBoxCluCtrl, 'mCheckCrsUp', return_value=True)
    def test_mStartVMAfterReshape_error(
        self,
        mock_check_crs_up,
        mock_check_db_up,
        mock_check_if_crs_dbs_up,
        mock_start_domu,
        mock_get_default_db):
        ctrl = exaBoxCluCtrl(aCtx=MagicMock())

        mock_start_domu.side_effect = ExacloudRuntimeError(0x10, 0xA, "DomU services were not up.")

        ctrl.mStartVMAfterReshape(
            aDom0="dom0",
            aDomU="domU",
            aOptions=None,
            aCRS=True,
            aDB=False,
            aNode="node1"
        )
        mock_check_if_crs_dbs_up.assert_called_once_with("domU")

    @patch('exabox.ovm.clucontrol.ebGetDefaultDB', return_value=MagicMock())
    def test_mCheckIfCrsDbsUp_crs_not_up(self, mock_get_db):
        self.obj = exaBoxCluCtrl(aCtx=MagicMock())
        self.obj.mCheckCrsUp = MagicMock(return_value=False)
        self.obj.mCheckDBIsUp = MagicMock(return_value=True)

        with self.assertRaises(ExacloudRuntimeError) as cm:
            self.obj.mCheckIfCrsDbsUp("domU1")
        self.assertIn("CRS stack did not start", str(cm.exception))

    @patch('exabox.ovm.clucontrol.ebGetDefaultDB')
    @patch.object(ebCluUtils, "getNotUpDbsList")
    def test_mCheckIfCrsDbsUp_dbs_up(self, mock_get_not_up, mock_get_db):
        mock_get_not_up.return_value = []
        self.obj = exaBoxCluCtrl(aCtx=MagicMock())
        self.obj.mCheckCrsUp = MagicMock(return_value=True)
        self.obj.mCheckDBIsUp = MagicMock(return_value=True)
        self.obj.mUpdateErrorObject = MagicMock()
        mock_db_instance = MagicMock()
        mock_get_db.return_value = mock_db_instance
        self.obj.mCheckIfCrsDbsUp("domU1")
        mock_db_instance.mRemoveDBListByNode.assert_called_once_with("domU1")

    @patch.object(ebCluUtils, "getNotUpDbsList")
    def test_mCheckIfCrsDbsUp_includes_dbs_not_up_in_error(self, mock_get_notup):
        mock_get_notup.return_value = ["DB2"]
        self.obj = exaBoxCluCtrl(aCtx=MagicMock())
        self.obj.mCheckCrsUp = MagicMock(return_value=True)
        self.obj.mCheckDBIsUp = MagicMock(return_value=False)
        self.obj.mUpdateErrorObject = MagicMock(side_effect=ExacloudRuntimeError("DBs not up list : ['DB2']"))

        with self.assertRaises(ExacloudRuntimeError) as cm:
            self.obj.mCheckIfCrsDbsUp("domU1")
        self.assertIn("DBs not up list : ['DB2']", str(cm.exception))

    @patch.object(ebCluUtils, "getNotUpDbsList")
    @patch('exabox.ovm.clucontrol.ebGetDefaultDB')
    def test_mCheckIfCrsDbsUp_final_check_raises(self, mock_get_db, mock_get_not_up):
        self.obj = exaBoxCluCtrl(aCtx=MagicMock())
        self.obj.mCheckCrsUp = MagicMock(return_value=True)
        self.obj.mCheckDBIsUp = MagicMock(return_value=True)
        mock_get_not_up.return_value=["DB3"]
        self.obj.mUpdateErrorObject = MagicMock(side_effect=ExacloudRuntimeError("DBs instances are not running"))
        with self.assertRaises(ExacloudRuntimeError) as cm:
            self.obj.mCheckIfCrsDbsUp("domU1")
        self.assertIn("DBs instances are not running", str(cm.exception))

    @patch('exabox.ovm.clucontrol.ebLogError')
    @patch.object(ebCluUtils, "getNotUpDbsList")
    @patch('exabox.ovm.clucontrol.ebGetDefaultDB')
    def test_mCheckIfCrsDbsUp_logs_and_raises(self, mock_get_db, mock_get_not_up, mock_log_error):
        self.obj = exaBoxCluCtrl(aCtx=MagicMock())
        self.obj.mCheckCrsUp = MagicMock(return_value=True)
        self.obj.mCheckDBIsUp = MagicMock(return_value=True)
        mock_get_not_up.return_value = ["DB3"]
        self.obj.mUpdateErrorObject = MagicMock()
        mock_db_instance = MagicMock()
        mock_get_db.return_value = mock_db_instance
        with self.assertRaises(ExacloudRuntimeError) as cm:
            self.obj.mCheckIfCrsDbsUp("domU1")
        self.assertIn("DBs instances are not running in domU1", str(cm.exception))
        mock_log_error.assert_any_call('***  DBs instances are not running in domU1 for DBs [\'DB3\']')
        mock_log_error.assert_any_call('*** ALL Database are not up after booting node domU1. not proceeding further')
        self.obj.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_DBS_NOT_RUNNING']," DBs instances are not running in domU1 for DBs ['DB3']"
        )

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetActiveDbInstances', return_value=[])
    def test_mCheckDBIsUp_NoActiveDBInstance(self, aMockmGetActiveDbInstances):
        _cmds = {
            self.mGetRegexLocal():
            [
                [
                    exaMockCommand("/bin/rm -f /tmp/get_exatest.json")
                ]
            ],
            self.mGetRegexVm():
            [
                [
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        aDomU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cluctrl = exaBoxCluCtrl(get_gcontext())
        with patch('exabox.utils.node.exaBoxNode.mConnect'):
            self.assertEqual(_cluctrl.mCheckDBIsUp(aDomU), False)

    @patch("exabox.ovm.clucontrol.ebLogWarn", wraps=ebLogWarn)
    @patch("exabox.ovm.clucontrol.os.listdir", return_value=["bondeth0", "bondeth1"])
    def test_mDom0PostVMCreateNetConfig_genbondmap_no_slaves_warning(self, mock_listdir, mock_logwarn):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGenBondMap with no bondeth0 slaves")
        aOnline = True
        ctrl = self.mGetClubox()
        aNode = Mock()
        def side_effect(cmd):
            if cmd.startswith('/bin/cat /sys/class/net/bondeth0'):
                return (None, io.StringIO(""), io.StringIO(""))
            elif cmd.startswith('/bin/cat /sys/class/net/bondeth1'):
                return (None, io.StringIO("eth6 eth7"), io.StringIO(""))
            else:
                raise ValueError(f"Unexpected command: {cmd}")
        aNode.mExecuteCmd.side_effect = side_effect
        aNode.mGetCmdExitStatus.return_value = 0
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bond_map = ctrl.mGenBondMap(aNode, aOnline)
            self.assertIn("The interface bondeth0 exists, but it seems to have no configured slaves.", str(ctx.exception))
            self.assertEqual(bond_map, {"eth6": "bondeth1", "eth7": "bondeth1"})

    @patch("exabox.ovm.clucontrol.os.listdir", return_value=["bondeth0", "bondeth1"])
    @patch("exabox.ovm.clucontrol.ebLogWarn")
    def test_mDom0PostVMCreateNetConfig_genbondmap_with_slaves(self, mock_logwarn, mock_listdir):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGenBondMap with bondeth0 slaves")
        aOnline = True
        ctrl = self.mGetClubox()
        aNode = Mock()
        def side_effect(cmd):
            if cmd.startswith('/bin/cat /sys/class/net/bondeth0'):
                return (None, io.StringIO("eth1 eth2"),  io.StringIO(""))
            elif cmd.startswith('/bin/cat /sys/class/net/bondeth1'):
                return (None, io.StringIO("eth6 eth7"), io.StringIO(""))
            else:
                raise ValueError(f"Unexpected command: {cmd}")
        aNode.mExecuteCmd.side_effect = side_effect
        aNode.mGetCmdExitStatus.return_value = 0
        with patch.object(self, "mPrepareMockCommands", return_value=None):
            bond_map = ctrl.mGenBondMap(aNode, aOnline)
            self.assertEqual(bond_map, {"eth1":"bondeth0", "eth2":"bondeth0", "eth6": "bondeth1", "eth7": "bondeth1"})
    
    @patch.object(exaBoxCluCtrl, 'mCheckDBIsUp', return_value=True)
    def test_mRestartDBInstance(self, mock_checkdb):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mRestartDBInstance")
        ctrl = self.mGetClubox()
        aDomU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        aOptions = MagicMock()
        aOptions.jsonconf = {
        "vms": [
            {"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": 1024},
            {"hostname": "scaqab10client02vm08.us.oracle.com", "gb_memory": 2048}
            ]
        }
        _cmds = {
            self.mGetRegexLocal():
            [
                [  
                 exaMockCommand("/bin/rm -f /tmp/get_exatest.json", aRc=0, aStdout="", aPersist=True)
                ]
            ],
            self.mGetRegexVm():
            [
                [
                 exaMockCommand("ls -ltr", aRc=0, aStdout="DB1\n", aPersist=True),
                 exaMockCommand(".*srvctl config database -d *", aStdout="AUTOMATIC\n",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl config database", aStdout="db1",aRc=0, aPersist=True),
                 exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                 exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                 exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                 exaMockCommand(".*srvctl status database -d db1*", aRc=0, aStdout="Instance db1 is running on node" ,aPersist=True)
                 
                ],
                [
                 exaMockCommand("ls -ltr", aRc=0, aStdout="DB1\n", aPersist=True),
                 exaMockCommand(".*srvctl config database -d *", aStdout="AUTOMATIC\n",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl config database", aStdout="db1",aRc=0, aPersist=True),
                 exaMockCommand("/bin/su - grid -c '/bin/cat /etc/oratab.* cut -f 2.*'", aStdout="/u01/app/19.0.0.0/grid", aRc=0,  aPersist=True),
                 exaMockCommand(".*srvctl start instance -d *",aRc=0, aStdout="Instance db1 is running on node" ,aPersist=True),
                 exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                 exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                 exaMockCommand(".*srvctl status database -d db1*", aRc=0, aStdout="Instance db1 is running on node" ,aPersist=True)
                 
                ],
                [
                 exaMockCommand("ls -ltr", aRc=0, aStdout="DB1\n", aPersist=True),
                 exaMockCommand(".*srvctl config database -d *", aStdout="AUTOMATIC\n",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl config database", aStdout="db1",aRc=0, aPersist=True),
                 exaMockCommand("/bin/cat /etc/oratab.* /bin/cut -f 2 -d.*", aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                 exaMockCommand("/bin/su - grid -c '/bin/cat /etc/oratab.* cut -f 1.*'", aStdout="sid1", aRc=0,  aPersist=True),
                 exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                 exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                 exaMockCommand(".*srvctl status database -d db1*", aRc=0, aStdout="Instance db1 is running on node" ,aPersist=True)
                 
                ],
                [
                 exaMockCommand("ls -ltr", aRc=0, aStdout="DB1\n", aPersist=True),
                 exaMockCommand(".*srvctl config database -d *", aStdout="AUTOMATIC\n",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl config database", aStdout="db1",aRc=0, aPersist=True),
                 exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                 exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                 exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                 exaMockCommand(".*srvctl status database -d db1*", aRc=0, aStdout="Instance db1 is running on node" ,aPersist=True)
                 
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        ctrl.mRestartDBInstance(aDomU, ['db1'] )
        
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/18.0.0.0/grid", None, None))
    def test_mGetActiveDbInstances(self, mock_mGetOracleBaseDirectories ):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetActiveDbInstances")
        ctrl = self.mGetClubox()
        aDomU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexLocal():
            [
                [  
                 exaMockCommand("/bin/rm -f /tmp/get_exatest.json", aRc=0, aStdout="", aPersist=True)
                ]
            ],
            self.mGetRegexVm():
            [
                [
                 exaMockCommand("ls -ltr", aRc=0, aStdout="DB1\n", aPersist=True),
                 exaMockCommand(".*srvctl config database -d *", aStdout="AUTOMATIC\n",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl config database", aStdout="db1",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl status database -d db1*", aRc=0, aStdout="Instance db1 is running on node" ,aPersist=True)
                 
                ],
                [
                 exaMockCommand("ls -ltr", aRc=0, aStdout="DB1\n", aPersist=True),
                 exaMockCommand(".*srvctl config database -d *", aStdout="AUTOMATIC\n",aRc=0, aPersist=True),
                 exaMockCommand("/bin/su - grid -c '/bin/cat /etc/oratab.* cut -f 2 -d.*'", aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                 exaMockCommand("/bin/su - grid -c '/bin/cat /etc/oratab.* cut -f 1.*'", aStdout="sid1", aRc=0,  aPersist=True),
                 exaMockCommand(".*srvctl config database", aStdout="db1",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl status database -d db1*", aRc=0, aStdout="Instance db1 is running on node" ,aPersist=True)
                ],
                [
                 exaMockCommand("ls -ltr", aRc=0, aStdout="DB1\n", aPersist=True),
                 exaMockCommand(".*/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                 exaMockCommand(".*srvctl config database -d *", aStdout="AUTOMATIC\n",aRc=0, aPersist=True),
                 exaMockCommand("/bin/cat /etc/oratab.* /bin/cut -f 2 -d.*", aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                 exaMockCommand("/bin/su - grid -c '/bin/cat /etc/oratab.* cut -f 1.*'", aStdout="sid1", aRc=0,  aPersist=True),
                 exaMockCommand(".*srvctl config database", aStdout="db1",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl status database -d db1*", aRc=0, aStdout="Instance db1 is running on node" ,aPersist=True)
                ],
                [
                 exaMockCommand("ls -ltr", aRc=0, aStdout="DB1\n", aPersist=True),
                 exaMockCommand(".*srvctl config database -d *", aStdout="AUTOMATIC\n",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl config database", aStdout="db1",aRc=0, aPersist=True),
                 exaMockCommand(".*srvctl status database -d db1*", aRc=0, aStdout="Instance db1 is running on node" ,aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        res = ctrl.mGetActiveDbInstances(aDomU)
        self.assertEqual(res, ["db1"])
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.IsZdlraProv', return_value=True):
                res = ctrl.mGetActiveDbInstances(aDomU)
                self.assertEqual(res, ["db1"])

    def test_mModifyAndUploadCloudPropertiesExaCC(self):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mModifyAndUploadCloudPropertiesExaCC")
        _dbaasapiPayload = {
                                "operation": "cloud_properties",
                                "object": "os",
                                "action": "set",
                                "params": {
                                    "diag": {},
                                    "common": {
                                                "fedramp": "disabled",
                                                "oss_url": "https://swiftobjectstorage.eu-zurich-1.oraclecloud.com",
                                                "dbsystemocid": "ocid1.exacomputevmcluster.oc1.eu-zurich-1.an5heljrhnge2iqaojsabmgckla24du4mnyamwu6qgws5g2dycj2phgtlkma",
                                                "se_linux": "disabled",
                                                "fips_compliance": "disabled",
                                                "nat_fileserver": "169.254.200.1"
                                            },
        },
        "outputfile": "/tmp/cloudProperties_tests",
        "FLAGS": ""
    }
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local.mSetDbaasApiPayload(_dbaasapiPayload)
        _ebox_local.mSetOciExacc("True")
        _cmds = {
            self.mGetRegexVm():
            [
                [
                 exaMockCommand("/usr/sbin/ip route show dev eth0 scope link*", aRc=0, aStdout="169.254.200.5")
                ],
                [
                 exaMockCommand("/bin/scp*", aRc=0, aStdout="")
                ],
                [
                 exaMockCommand("/usr/sbin/ip route show dev eth0 scope link*", aRc=0, aStdout="169.254.200.1")
                ],
                [
                 exaMockCommand("/bin/scp*", aRc=0, aStdout="")
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox_local.mModifyAndUploadCloudPropertiesExaCC()

if __name__ == "__main__":
    unittest.main(warnings='ignore')
