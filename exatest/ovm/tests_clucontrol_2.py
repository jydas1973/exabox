#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clucontrol_2.py /main/21 2026/03/13 08:56:06 vikasras Exp $
#
# tests_clucontrol_2.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
#       vikasras 02/17/26 -  Bug 38782517 MEMRESHAPE | CRS SERVICES WERE NOT 
#                            RESTARTED IN ROLLING FASHION BETWEEN THE NODES 
#                            CAUSING OUTAGE
#    vikasras    10/14/25 - Bug 38362546 - ADDVM FAILED WHEN ADDVM FOR NODE 1
#                           (PRIMARY IS ADDING) , ONLY SECONDARY NODE 2 IS AVAILABLE
#    naps        01/16/26 - Bug 38843402 - UT Updation.
#    remamid     12/15/25 - Add a unittest for bug38765563
#    nelango     12/09/25 - Bug 38694209: Add unit test for validate hostname
#    remamid     12/02/25 - Add a unittest for bug 38626206
#    bhpati      11/18/25 - Bug 38593631 - Exadata Cell Flashcache Not Created
#                           After Cell Addition
#    remamid     11/17/25 - Add unittest for
#                           mModifyAndUploadCloudPropertiesExaCC bug38581933
#    bhpati      11/13/25 - Bug 38467261 - Remove vm operation failed - ssh
#                           test to the vm failed during pre-check
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
import hashlib
import os, re, io
import sys
from io import StringIO
from types import SimpleNamespace
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, Mock, call
try:
    from paramiko.ssh_exception import SSHException
except ImportError:  # pragma: no cover - fallback for environments without paramiko
    class SSHException(Exception):
        pass
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
from exabox.ovm.clumisc import mWaitForSystemBoot, ebCluStorageReshapePrecheck, ebCluServerSshConnectionCheck, ebCluNodeSubsetPrecheck
from exabox.ovm.hypervisorutils import getHVInstance
from exabox.ovm.cludbaas import ebCluDbaas
from exabox.ovm.utils.clu_utils import ebCluUtils, mRunCrsCommandsWithRetry



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

    @patch('exabox.ovm.clucontrol.exaBoxNode')
    @patch('exabox.ovm.clucontrol.ebLogInfo')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnDom0DomUPair')
    def test_mGetPkeysConfig_hostname_without_digits(
        self,
        mock_return_dom_pairs,
        mock_is_kvm,
        mock_clu_loginfo,
        mock_exaBoxNode
    ):
        hostname = "domuwithoutdigits"
        dom0_primary = "dom0a.example.com"
        dom0_secondary = "dom0b.example.com"
        dom_pairs = [[dom0_primary, hostname], [dom0_secondary, "anotherdomu"]]
        ctrl = self.mGetClubox()

        dom_u_machine = MagicMock()
        dom_u_machine.mGetMacNetworks.return_value = ["net1"]
        machines_mock = MagicMock()
        machines_mock.mGetMachineConfig.return_value = dom_u_machine
        networks_mock = MagicMock()
        net_config = MagicMock()
        net_config.mGetNetVlanId.return_value = "UNDEFINED"
        networks_mock.mGetNetworkConfig.return_value = net_config

        original_machines = ctrl._exaBoxCluCtrl__machines
        original_networks = ctrl._exaBoxCluCtrl__networks
        ctrl._exaBoxCluCtrl__machines = machines_mock
        ctrl._exaBoxCluCtrl__networks = networks_mock
        self.addCleanup(setattr, ctrl, "_exaBoxCluCtrl__machines", original_machines)
        self.addCleanup(setattr, ctrl, "_exaBoxCluCtrl__networks", original_networks)

        mac_first = "01"
        mac_second = "02"
        digest_byte = hashlib.sha224(hostname.encode("utf-8")).digest()[0]
        expected_suffix = str((digest_byte % 9) + 1)
        expected_skm = hex(int("0xaa" + mac_first, 16))
        expected_ckm = hex(int("0xa" + mac_second + expected_suffix, 16))

        def _node_factory(mac_suffix):
            node = MagicMock()
            node.mExecuteCmd.return_value = (None, io.StringIO(f"aa:bb:cc:dd:ee:{mac_suffix}\n"), None)
            node.mGetCmdExitStatus.return_value = 0
            return node

        mock_return_dom_pairs.return_value = dom_pairs
        mock_clu_loginfo.side_effect = ebLogInfo
        mock_exaBoxNode.side_effect = [_node_factory(mac_first), _node_factory(mac_second)]

        skm_hex, ckm_hex = ctrl.mGetPkeysConfig()

        self.assertEqual(skm_hex, expected_skm)
        self.assertEqual(ckm_hex, expected_ckm)
        expected_digitless_log = (
            f"*** Hostname {hostname} has no digits; derived CKM suffix {expected_suffix} from SHA-224 hash"
        )
        expected_generation_log = (
            f"*** mGetPkeysConfig / KVM SKM/CKM generation : {expected_skm}/ {expected_ckm}"
        )
        mock_clu_loginfo.assert_any_call(expected_digitless_log)
        mock_clu_loginfo.assert_any_call(expected_generation_log)

    @patch('exabox.ovm.clucontrol.exaBoxNode')
    @patch('exabox.ovm.clucontrol.ebLogInfo')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnDom0DomUPair')
    def test_mGetPkeysConfig_hostname_with_digits(
        self,
        mock_return_dom_pairs,
        mock_is_kvm,
        mock_clu_loginfo,
        mock_exaBoxNode
    ):
        hostname = "domu12345"
        dom0_primary = "dom0a.example.com"
        dom0_secondary = "dom0b.example.com"
        dom_pairs = [[dom0_primary, hostname], [dom0_secondary, "anotherdomu"]]
        ctrl = self.mGetClubox()

        dom_u_machine = MagicMock()
        dom_u_machine.mGetMacNetworks.return_value = ["net1"]
        machines_mock = MagicMock()
        machines_mock.mGetMachineConfig.return_value = dom_u_machine
        networks_mock = MagicMock()
        net_config = MagicMock()
        net_config.mGetNetVlanId.return_value = "UNDEFINED"
        networks_mock.mGetNetworkConfig.return_value = net_config

        original_machines = ctrl._exaBoxCluCtrl__machines
        original_networks = ctrl._exaBoxCluCtrl__networks
        ctrl._exaBoxCluCtrl__machines = machines_mock
        ctrl._exaBoxCluCtrl__networks = networks_mock
        self.addCleanup(setattr, ctrl, "_exaBoxCluCtrl__machines", original_machines)
        self.addCleanup(setattr, ctrl, "_exaBoxCluCtrl__networks", original_networks)

        mac_first = "01"
        mac_second = "02"
        numeric_part = ''.join(filter(str.isdigit, hostname)).replace('0', '')
        expected_suffix = numeric_part[-3:][0]
        expected_skm = hex(int("0xaa" + mac_first, 16))
        expected_ckm = hex(int("0xa" + mac_second + expected_suffix, 16))

        def _node_factory(mac_suffix):
            node = MagicMock()
            node.mExecuteCmd.return_value = (None, io.StringIO(f"aa:bb:cc:dd:ee:{mac_suffix}\n"), None)
            node.mGetCmdExitStatus.return_value = 0
            return node

        mock_return_dom_pairs.return_value = dom_pairs
        mock_clu_loginfo.side_effect = ebLogInfo
        mock_exaBoxNode.side_effect = [_node_factory(mac_first), _node_factory(mac_second)]

        skm_hex, ckm_hex = ctrl.mGetPkeysConfig()

        self.assertEqual(skm_hex, expected_skm)
        self.assertEqual(ckm_hex, expected_ckm)
        expected_generation_log = (
            f"*** mGetPkeysConfig / KVM SKM/CKM generation : {expected_skm}/ {expected_ckm}"
        )
        digitless_log = (
            f"*** Hostname {hostname} has no digits; derived CKM suffix {expected_suffix} from SHA-224 hash"
        )
        logged_messages = [call.args[0] for call in mock_clu_loginfo.call_args_list]
        self.assertIn(expected_generation_log, logged_messages)
        self.assertNotIn(digitless_log, logged_messages)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnAllClusterHosts", return_value=([], ['scaqab10client01vm08.us.oracle.com','scaqab10client02vm08.us.oracle.com'], [], []))
    @patch('exabox.ovm.clumisc.ebCluServerSshConnectionCheck.mNodeSubsetSshConnectionCheck', return_value=0)  
    @patch('exabox.ovm.clumisc.ebCluNodeSubsetPrecheck.mRunNodeSubsetPrecheck', return_value=0)
    def test_mHandlerNodeSubsetPrecheck_success(self, mock_mReturnAllClusterHosts, mock_ebCluNodeSubsetPrecheck, mock_ebCluServerSshConnectionCheck):
        # Mock the dependencies
        self.mGetArgsOptions = MagicMock(return_value={})

        # Call the method
        return_code = self.mGetClubox().mHandlerNodeSubsetPrecheck()

        # Assert the results
        self.assertEqual(return_code, 0)

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
    @patch.object(ebCluUtils, 'mValidateSharedMemSettings')
    @patch.object(exaBoxCluCtrl, 'mCheckIfCrsDbsUp')
    @patch.object(exaBoxCluCtrl, 'mCheckDBIsUp', return_value=True)
    @patch.object(exaBoxCluCtrl, 'mCheckCrsUp', return_value=True)
    def test_mStartVMAfterReshape_error(
        self,
        mock_check_crs_up,
        mock_check_db_up,
        mock_check_if_crs_dbs_up,
        mock_validate_shared_mem,
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
        #mock_validate_shared_mem.assert_not_called()

    def test_mValidateSharedMemSettings_success(self):
        ctrl = self.mGetClubox()
        utils = ebCluUtils(aExaBoxCluCtrl=ctrl)
        _domU = ctrl.mReturnDom0DomUPair()[0][1]

        ctrl.mGetCtx().mSetConfigOption(
            'reshape_memory',
            {
                'shmmax_ratio': '0.8',
                'shared_memory_validation': 'True'
            }
        )

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand('/usr/sbin/sysctl -n kernel.shmmax', aStdout='68719476736\n'),
                    exaMockCommand('/bin/grep MemTotal /proc/meminfo', aStdout='MemTotal:       67108864 kB\n'),
                    exaMockCommand('getconf PAGE_SIZE', aStdout='4096\n'),
                    exaMockCommand('/usr/sbin/sysctl -n kernel.shmall', aStdout='16777216\n')
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        utils.mValidateSharedMemSettings(_domU)

    def test_mValidateSharedMemSettings_shmmax_below_threshold(self):
        ctrl = self.mGetClubox()
        utils = ebCluUtils(aExaBoxCluCtrl=ctrl)
        _domU = ctrl.mReturnDom0DomUPair()[0][1]

        ctrl.mGetCtx().mSetConfigOption(
            'reshape_memory',
            {
                'shmmax_ratio': '0.8',
                'shared_memory_validation': 'True'
            }
        )

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand('/usr/sbin/sysctl -n kernel.shmmax', aStdout=str(26843545600) + '\n'),
                    exaMockCommand('/bin/grep MemTotal /proc/meminfo', aStdout='MemTotal:       67108864 kB\n')
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        with self.assertRaises(ExacloudRuntimeError) as cm:
            utils.mValidateSharedMemSettings(_domU)

        self.assertEqual(cm.exception.mGetErrorCode(), 0x0808)

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

    @patch('exabox.ovm.clucontrol.mRunCrsCommandsWithRetry')
    @patch('exabox.ovm.clucontrol.node_exec_cmd_check')
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.ovm.clucontrol.connect_to_host')
    def test_mExecuteCRSReboot_invokes_retry(self, mock_connect, mock_cmd_abs_path, mock_exec_cmd, mock_retry):
        ctrl = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_node
        mock_connect.return_value.__exit__.return_value = False
        mock_cmd_abs_path.side_effect = ['grep_path']
        mock_exec_cmd.return_value.stdout = SimpleNamespace(splitlines=lambda: ['oracle_home=/u01/app/gi'])

        with patch.object(ctrl, 'mCheckConfigOption', return_value=False), \
             patch.object(ctrl, 'mReturnDom0DomUPair', return_value=[('dom0', 'domu1')]), \
             patch.object(ctrl, 'mCheckCrsIsUp'), \
             patch.object(ctrl, 'mCheckAsmIsUp'):
            ctrl.mExecuteCRSReboot(['stop', 'start'])

        stop_cmds = ['/u01/app/gi/bin/crsctl stop cluster -all', '/u01/app/gi/bin/crsctl stop cluster -all -f']
        start_cmds = ['/u01/app/gi/bin/crsctl start cluster -all']
        mock_retry.assert_has_calls([
            call(mock_node, stop_cmds, aLabel='CRS stop (cluster reboot)'),
            call(mock_node, start_cmds, aLabel='CRS start (cluster reboot)')
        ])
        self.assertEqual(mock_retry.call_count, 2)


    @patch('exabox.ovm.clucontrol.mRunCrsCommandsWithRetry')
    @patch('exabox.ovm.clucontrol.node_exec_cmd_check')
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.ovm.clucontrol.connect_to_host')
    def test_mExecuteCRSReboot_handles_retry_failure(self, mock_connect, mock_cmd_abs_path, mock_exec_cmd, mock_retry):
        ctrl = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_node
        mock_connect.return_value.__exit__.return_value = False
        mock_cmd_abs_path.side_effect = ['grep_path']
        mock_exec_cmd.return_value.stdout = SimpleNamespace(splitlines=lambda: ['oracle_home=/u01/app/gi'])
        mock_retry.side_effect = ExacloudRuntimeError('stop failed')

        with patch.object(ctrl, 'mCheckConfigOption', return_value=False), \
             patch.object(ctrl, 'mReturnDom0DomUPair', return_value=[('dom0', 'domu1')]), \
             patch.object(ctrl, 'mCheckCrsIsUp'), \
             patch.object(ctrl, 'mCheckAsmIsUp'):
            with self.assertRaises(ExacloudRuntimeError) as cm:
                ctrl.mExecuteCRSReboot(['stop', 'start'])

        self.assertIn('stop failed', str(cm.exception))
        stop_cmds = ['/u01/app/gi/bin/crsctl stop cluster -all', '/u01/app/gi/bin/crsctl stop cluster -all -f']
        mock_retry.assert_called_once_with(mock_node, stop_cmds, aLabel='CRS stop (cluster reboot)')

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

    def test_mGetActiveDbInstances(self):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetActiveDbInstances")

        ctrl = self.mGetClubox()
        dom_u = ctrl.mReturnDom0DomUPair()[0][1]

        class NodeStub:
            def __init__(self, plan):
                self._plan = list(plan)
                self._last_rc = 0
                self.disconnected = False
                self.history = []

            def mSetUser(self, *_args, **_kwargs):
                return None

            def mConnect(self, *_args, **_kwargs):
                return None

            def mExecuteCmd(self, command):
                if not self._plan:
                    raise AssertionError(f"Unexpected command execution: {command}")
                matcher, stdout, rc, validator = self._plan.pop(0)
                matched = False
                if matcher is None:
                    matched = True
                elif hasattr(matcher, 'search'):
                    matched = bool(matcher.search(command))
                elif callable(matcher):
                    matched = bool(matcher(command))
                else:
                    matched = matcher in command
                if not matched:
                    expectation = getattr(matcher, 'pattern', matcher)
                    raise AssertionError(f"Expected {expectation!r} in {command!r}")
                if validator:
                    validator(command)
                self._last_rc = rc
                payload = stdout if isinstance(stdout, str) else ''.join(stdout)
                self.history.append(command)
                return None, io.StringIO(payload), None

            def mGetCmdExitStatus(self):
                return self._last_rc

            def mDisconnect(self):
                self.disconnected = True

        def step(matcher, stdout='', rc=0, validator=None):
            return matcher, stdout, rc, validator

        def management_step(db_name, stdout):
            return step(
                f"srvctl config database -d {db_name}",
                stdout,
                validator=lambda command: self.assertIn("Management policy", command),
            )


        plan_success = [
            step(
                "srvctl config database",
                "\n".join([
                    "db1",
                    "db2",
                    "db3",
                    "dbretry",
                    "dbreadonly",
                    "dbnopolicy",
                ]) + "\n",
                validator=lambda command: self.assertNotIn("-d ", command),
            ),
            step("status database -d db1 -v", "Instance db1_1 info Instance status: Open\n"),
            management_step("db1", "AUTOMATIC\n"),
            step("status database -d db2 -v", "Instance db2_1 info Instance status: Starting\n"),
            step("status database -d db2 -v", "Instance db2_1 info Instance status: Open\n"),
            management_step("db2", "MANUAL\n"),
            step("status database -d dbretry -v", ""),
            step("status database -d dbretry -v", "Instance dbretry_1 info Instance status: Open\n"),
            management_step("dbretry", "AUTOMATIC\n"),
            step(
                "status database -d dbreadonly -v",
                "\n".join([
                    "Instance dbreadonly_1 info Instance status: Open,Readonly",
                    "Noise line that should be ignored",
                ]) + "\n",
            ),
            step("status database -d dbreadonly -v", "Instance dbreadonly_1 info Instance status: Open,Readonly\n"),
            management_step("dbreadonly", "AUTOMATIC\n"),
            step("status database -d dbnopolicy -v", "Instance dbnopolicy_1 info Instance status: Open\n"),
            management_step("dbnopolicy", ""),
        ]

        plan_zdlra = [
            step('su grid -c "$ORACLE_HOME/bin/srvctl config database"', "dbz\n"),
            step("status database -d dbz -v", "Instance dbz_1 info Instance status: Restricted Access\n"),
            management_step("dbz", "AUTOMATIC\n"),
        ]

        fail_status_line = "Instance dbfail_1 info Instance status: Starting\n"
        plan_failure = [
            step("srvctl config database", "dbfail\n", validator=lambda command: self.assertNotIn("-d ", command))
        ] + [step("status database -d dbfail -v", fail_status_line) for _ in range(10)]

        plan_empty = [step("srvctl config database", "", validator=lambda command: self.assertNotIn("-d ", command))]

        plan_config_failure = [
            step("srvctl config database", "", rc=1, validator=lambda command: self.assertNotIn("-d ", command))
        ]

        node_success = NodeStub(plan_success)
        node_zdlra = NodeStub(plan_zdlra)
        node_failure = NodeStub(plan_failure)
        node_empty = NodeStub(plan_empty)
        node_config_failure = NodeStub(plan_config_failure)
        sleep_calls = []

        def fake_sleep(seconds):
            sleep_calls.append(seconds)

        def _parse_args(args):
            if len(args) == 1:
                return args[0], None
            if len(args) >= 2:
                return args[0], args[1]
            raise AssertionError("mGetOracleBaseDirectories called without arguments")

        def directories_success(*args, **_kwargs):
            dom_u_arg, dbname = _parse_args(args)
            mapping = {
                None: ('/base/path', None, None),
                'db1': ('/opt/db1', None, None),
                'db2': ('/opt/db2', None, None),
                'db3': ('', None, None),
                'dbretry': ('/opt/dbretry', None, None),
                'dbreadonly': ('/opt/dbreadonly', None, None),
                'dbnopolicy': ('/opt/dbnopolicy', None, None),
            }
            return mapping.get(dbname, ('/base/path', None, None))

        def directories_zdlra(*args, **_kwargs):
            dom_u_arg, dbname = _parse_args(args)
            return ('/grid/dbz', None, None)

        def directories_failure(*args, **_kwargs):
            dom_u_arg, dbname = _parse_args(args)
            mapping = {
                None: ('/base/path', None, None),
                'dbfail': ('/opt/dbfail', None, None),
            }
            return mapping.get(dbname, ('/opt/dbfail', None, None))

        with patch('exabox.ovm.clucontrol.time.sleep', side_effect=fake_sleep):
            with patch('exabox.ovm.clucontrol.exaBoxNode', side_effect=[node_success, node_zdlra, node_failure, node_empty, node_config_failure]):
                with patch.object(exaBoxCluCtrl, 'IsZdlraProv', return_value=False), \
                     patch.object(exaBoxCluCtrl, 'mGetOracleBaseDirectories', side_effect=directories_success):
                    result_success = ctrl.mGetActiveDbInstances(dom_u)
                self.assertEqual(result_success, ['db1_1', 'dbretry_1', 'dbreadonly_1'])
                self.assertTrue(node_success.disconnected)
                self.assertFalse(node_success._plan)
                self.assertEqual(sleep_calls, [30, 30, 30])
                sleep_calls.clear()

                with patch.object(exaBoxCluCtrl, 'IsZdlraProv', return_value=True), \
                     patch.object(exaBoxCluCtrl, 'mGetGridHome', return_value=('/grid/home', 'SIDZ')), \
                     patch.object(exaBoxCluCtrl, 'mGetOracleBaseDirectories', side_effect=directories_zdlra):
                    result_zdlra = ctrl.mGetActiveDbInstances(dom_u)
                self.assertEqual(result_zdlra, ['dbz_1'])
                self.assertTrue(node_zdlra.disconnected)
                self.assertFalse(node_zdlra._plan)
                self.assertEqual(sleep_calls, [])

                with patch.object(exaBoxCluCtrl, 'IsZdlraProv', return_value=False), \
                     patch.object(exaBoxCluCtrl, 'mGetOracleBaseDirectories', side_effect=directories_failure):
                    with self.assertRaises(RuntimeError) as ctx:
                        ctrl.mGetActiveDbInstances(dom_u)
                self.assertIn('allowed state', str(ctx.exception))
                self.assertTrue(node_failure.disconnected)
                self.assertGreaterEqual(len(sleep_calls), 1)
                self.assertTrue(all(interval == 30 for interval in sleep_calls))
                sleep_calls.clear()

                with patch.object(exaBoxCluCtrl, 'IsZdlraProv', return_value=False), \
                     patch.object(exaBoxCluCtrl, 'mGetOracleBaseDirectories', return_value=('/base/path', None, None)):
                    result_empty = ctrl.mGetActiveDbInstances(dom_u)
                self.assertEqual(result_empty, [])
                self.assertTrue(node_empty.disconnected)

                with patch.object(exaBoxCluCtrl, 'IsZdlraProv', return_value=False), \
                     patch.object(exaBoxCluCtrl, 'mGetOracleBaseDirectories', side_effect=directories_success):
                    result_config_failure = ctrl.mGetActiveDbInstances(dom_u)
                self.assertEqual(result_config_failure, [])
                self.assertTrue(node_config_failure.disconnected)
            self.assertFalse(node_success._plan)

    def test_mPostVMCellPatching(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.test_mPostVMCellPatching")
        aOptions = MagicMock()
        aCellList = ['scaqan10celadm10.us.oracle.com', 'scaqan10celadm11.us.oracle.com']        
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("cellcli -e list flashcache attributes name,size", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e list flashlog attributes name,size", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e list cell detail | grep flashCacheMode", aRc=0, aStdout="flashCacheMode: WriteBack", aPersist=True),
                    exaMockCommand("cellcli -e create flashcache all", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e create flashlog all", aRc=0, aStdout="", aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.assertIsNone(self.mGetClubox().mPostVMCellPatching(aOptions, aCellList))
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

    @patch("exabox.ovm.clucontrol.ExaKmsEndpoint")
    def test_mSyncKVDBOverNetworkSend_no_kvdb_sync(self, mock_endpoint):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSyncKVDBOverNetworkSend skip path")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local.mSetOciExacc("True")
        _options = MagicMock()
        _options.vmcmd = "resizecpus"
        _ebox_local.mSetCmd('vm_cmd')
        _ebox_local.mSetOptions(_options)

        with patch.object(_ebox_local, "mIsExaCCMasterCPS", return_value=True):
            _ebox_local.mSyncKVDBOverNetworkSend(_options)

        mock_endpoint.return_value.mSyncKVDBSend.assert_not_called()

    @patch("exabox.ovm.clucontrol.ExaKmsEndpoint")
    def test_mSyncKVDBOverNetworkSend_invokes_for_other_commands(self, mock_endpoint):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSyncKVDBOverNetworkSend execute path")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local.mSetOciExacc("True")
        _options = MagicMock()
        _options.vmcmd = "addcpus"
        _ebox_local.mSetCmd('vm_cmd')
        _ebox_local.mSetOptions(_options)

        with patch.object(_ebox_local, "mIsExaCCMasterCPS", return_value=True):
            _ebox_local.mSyncKVDBOverNetworkSend(_options)

        mock_endpoint.return_value.mSyncKVDBSend.assert_called_once_with()

@patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories')
@patch('exabox.ovm.clucontrol.exaBoxNode.mIsConnectable')
@patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnDom0DomUPair')
@patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetArgsOptions')
@patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetGridConfig')
@patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetServiceType')
@patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRepoInventory')
def test_mGetVersionGiMultiImages(self, 
                                  mock_mGetRepoInventory, 
                                  mock_mGetServiceType, 
                                  mock_mGetGridConfig, 
                                  mock_mGetArgsOptions, 
                                  mock_mReturnDom0DomUPair, 
                                  mock_mIsConnectable, 
                                  mock_mGetOracleBaseDirectories):
    ebLogInfo("Running unit test on exaBoxCluCtrl.mGetVersionGiMultiImages")
    
    # Mocking the required methods
    mock_mGetRepoInventory.return_value = {
        'grid-klones': [
            {'version': '19.19.0.0', 'xmeta': {'default': True, 'latest': False}, 'service': ['gi']},
            {'version': '19.20.0.0', 'xmeta': {'default': False, 'latest': True}, 'service': ['gi']},
            {'version': '20.1.0.0', 'xmeta': {'default': False, 'latest': False}, 'service': ['other']}
        ]
    }
    mock_mGetServiceType.return_value = 'gi'
    mock_mGetGridConfig.return_value = {
        '19.19.0.0': {},
        '19.20.0.0': {},
        '20.1.0.0': {}
    }
    mock_mGetArgsOptions.return_value = MagicMock()
    mock_mReturnDom0DomUPair.return_value = [('dom0', 'domU')]
    mock_mIsConnectable.return_value = True
    mock_mGetOracleBaseDirectories.return_value = (None, '19.19.0.0', None)

    # Test case 1: GI version from payload
    self.mGetClubox().__options = MagicMock()
    self.mGetClubox().__options.jsonconf = {'grid_version': '19.20.0.0'}
    self.assertEqual(self.mGetClubox().mGetVersionGiMultiImages(), '19.20.0.0')

    # Test case 2: GI version from command line
    self.mGetClubox().__options.jsonconf = None
    self.mGetClubox().__options.grid_version = '19.19.0.0'
    self.assertEqual(self.mGetClubox().mGetVersionGiMultiImages(), '19.19.0.0')

    # Test case 3: GI latest version
    self.mGetClubox().__options.grid_version = None
    self.mGetClubox().__enable_gilatest = True
    self.assertEqual(self.mGetClubox().mGetVersionGiMultiImages(), '19.20.0.0')

    # Test case 4: GI version from DomU
    self.mGetClubox().__enable_gilatest = False
    self.assertEqual(self.mGetClubox().mGetVersionGiMultiImages(), '19.19.0.0')

    # Test case 5: GI default version
    mock_mIsConnectable.return_value = False
    self.assertEqual(self.mGetClubox().mGetVersionGiMultiImages(), '19.19.0.0')

    # Test case 6: No GI version provided
    mock_mGetRepoInventory.return_value = {
        'grid-klones': [
            {'version': '20.1.0.0', 'xmeta': {'default': False, 'latest': False}, 'service': ['other']}
        ]
    }
    with self.assertRaises(ExacloudRuntimeError) as cm:
        self.mGetClubox().mGetVersionGiMultiImages()
    self.assertEqual(cm.exception.args[0], 0x0119)

    def test_mGISupportDetection(self):
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["skip_min_dom0version_check"] = "True"
        gContext.mSetConfigOptions(writableGConfigOptions)

        self.mGetClubox().mCheck19cCapableComputeImage()

if __name__ == "__main__":
    unittest.main(warnings='ignore')
