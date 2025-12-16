#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/network/tests_ipv6_methods.py /main/6 2025/09/23 07:26:34 aararora Exp $
#
# tests_ipv6_methods.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_ipv6_methods.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    08/06/25 - ER 38132942: Single stack support for ipv6
#    rajsag      07/29/25 - bug 38249275 - exacc:24.3.2.4.0:delete node:
#                           clunoderemovegideletetask step is failing due to
#                           stale entries not getting cleaned up
#    aararora    09/26/24 - Bug 37105761: Oedacli command is failing for
#                           elastic_info call in ipv6
#    aararora    08/12/24 - Bug 36938926: Fix unit test failing due to merge
#                           with another transaction.
#    aararora    05/15/24 - File for unit testing methods consisting of IPv6
#                           related changes
#    aararora    05/15/24 - Creation
#
import copy
import os
import unittest

from unittest.mock import patch

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
import exabox.ovm.clubonding as clubonding
from exabox.ovm.cluconfig import ebCluNetworkConfig, ebCluNetworksConfig
from exabox.ovm.clubonding_config import extract_networks_from_monitor_conf,\
    extract_bonding_conf_from_common_payload, PayloadBondOp, elastic_node_payload_to_common_payload
from exabox.ovm.vmconfig import exaBoxClusterConfig
from exabox.ovm.clubasedb import exaBoxBaseDB
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.cluelasticcompute import ebCluReshapeCompute
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.tools.oedacli import OedacliCmdMgr
from exabox.ovm.cluvmreconfig import mGetReconfigParams, mGridUpdateOratab, mUpdateConfXml, mUpdateNWScripts, mDomUReconfig
from exabox.ovm.cluvmrecoveryutils import NodeRecovery
from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.network.payloads import CUSTOM_VIPS_IPv4_PAYLOAD, CUSTOM_VIPS_IPv6_PAYLOAD, CUSTOM_VIPS_DUAL_STACK_PAYLOAD,\
    VIPS_CONFIG_FILE_V4, VIPS_CONFIG_FILE_V6, VIPS_CONFIG_FILE_DUAL_STACK, PAYLOAD_CREATE_SERVICE, PAYLOAD_CREATE_SERVICE_DUAL_STACK,\
        PAYLOAD_CREATE_SERVICE_IPv6, PAYLOAD_ADD_COMPUTE, NEW_PAYLOAD_ADD_COMPUTE, PAYLOAD_ADD_COMPUTE_DUAL_STACK, NEW_PAYLOAD_ADD_COMPUTE_DUAL_STACK,\
            PAYLOAD_ADD_COMPUTE_IPv6, NEW_PAYLOAD_ADD_COMPUTE_IPv6, mGetReconfigParams_OUT, mFetchNetworkInfo_OUT, xmlGenerationPayload,\
                mGetReconfigParams_OUT_IPV6, mFetchNetworkInfo_OUT_IPV6
from exabox.tools.ebXmlGen.ebFacadeXmlGen import ebFacadeXmlGen

class testOptions(object): pass

class IOObject(object):
    def __init__(self, value):
        self.io = value

    def read(self):
        return self.io

    def readlines(self):
        return self.io

    def mExecuteCmd(self, cmd):
        ebLogInfo(f"Running command {cmd}.")

    def mFileExists(self, aFile):
        return True

class KvmMgr(object):
    def __init__(self, Dom0Dict):
        self.dom0_dict = Dom0Dict
        self.dom0_dict['CUR_MEM'] = "36"

    def mGetVMMemory(self, aVM, aParam):
        return self.dom0_dict[aParam]

class ebTestIPv6Methods(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestIPv6Methods, self).setUpClass(False,False)
        self._config = None
        self._networks = None

    def test_build_custom_vips_config(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on clubonding.build_custom_vips_config.")
        self._xmlpath = os.path.join(self.mGetUtil().mGetResourcesPath(),"sample.xml")
        self._config = exaBoxClusterConfig(self.mGetContext(), self._xmlpath)
        self._networks = self._config.mGetConfigElement('networks')
        self._monitor_json = os.path.join(self.mGetUtil().mGetResourcesPath(),"monitor_sample.json")
        domu = "scaqab10adm02vm01"
        domu_net_configs = {}
        for _network in self._networks:
            _net_object = ebCluNetworkConfig(_network)
            domu_net_configs[_net_object.mGetNetType()] = _net_object

        payload_ipv4 = CUSTOM_VIPS_IPv4_PAYLOAD
        payload_ipv6 = CUSTOM_VIPS_IPv6_PAYLOAD
        payload_dual_stack = CUSTOM_VIPS_DUAL_STACK_PAYLOAD
        _bond_monitor_json = None
        with open(self._monitor_json) as _monitor_json_file:
            _bond_monitor_json = _monitor_json_file.read()
        domu_net_configs_monitor = extract_networks_from_monitor_conf(_bond_monitor_json)
        vip_config_v4 = clubonding.build_custom_vips_config(domu, domu_net_configs, domu_net_configs_monitor, payload_ipv4)
        self.assertEqual(json.loads(vip_config_v4), VIPS_CONFIG_FILE_V4)
        vip_config_v6 = clubonding.build_custom_vips_config(domu, domu_net_configs, domu_net_configs_monitor, payload_ipv6)
        self.assertEqual(json.loads(vip_config_v6), VIPS_CONFIG_FILE_V6)
        vip_config_dual_stack = clubonding.build_custom_vips_config(domu, domu_net_configs, domu_net_configs_monitor, payload_dual_stack)
        self.assertEqual(json.loads(vip_config_dual_stack), VIPS_CONFIG_FILE_DUAL_STACK)

    def tests_extract_bonding_conf_from_common_payload(self):
        """
        Tests the method extract_bonding_conf_from_common_payload with IPv4, IPv6 and dual stack payloads
        """
        _scan_ips = ["10.0.9.124",
                    "10.0.25.120",
                    "10.0.0.121"]
        """ Monitor conf formed inside this method for iad103716exddu1101 DOMU will be:
        {'iad103716exddu1101': [{'type': 'host_ip', 'ip': '10.0.8.185', 'ipv6': '::',
        'interface_type': 'client', 'mac': '02:00:17:12:15:D4', 'standby_vnic_mac': None,
        'vlantag': 1, 'floating': False}, {'type': 'host_ip', 'ip': '10.0.38.38', 'ipv6': '::',
        'interface_type': 'backup', 'mac': '00:00:17:00:11:3F', 'standby_vnic_mac': None, 'vlantag': 2,
        'floating': False}, {'type': 'vip', 'ip': '10.0.3.203', 'ipv6': '::',
        'interface_type': 'client', 'mac': '02:00:17:12:15:D4', 'standby_vnic_mac': None, 'vlantag': 1, 'floating': True}]}
        """
        extract_bonding_conf_from_common_payload(PAYLOAD_CREATE_SERVICE["jsonconf"], True, _scan_ips, PayloadBondOp.CreateService)
        # After modifying the payload and adding ipv6 parameters - dual stack
        """
        Monitor conf created with below method for dual stack is as below for iad103716exddu1101 DOMU:
        {'iad103716exddu1101': [{'type': 'host_ip', 'ip': '10.0.8.185', 'ipv6': 'fe80::17ff:fe13:5c91',
        'interface_type': 'client', 'mac': '02:00:17:12:15:D4', 'standby_vnic_mac': None, 'vlantag': 1,
        'floating': False}, {'type': 'host_ip', 'ip': '10.0.38.38', 'ipv6': 'fe80::17ff:fe13:5d91',
        'interface_type': 'backup', 'mac': '00:00:17:00:11:3F', 'standby_vnic_mac': None, 'vlantag': 2,
        'floating': False}, {'type': 'vip', 'ip': '10.0.3.203', 'ipv6': 'fe80::17ff:fe13:5c92',
        'interface_type': 'client', 'mac': '02:00:17:12:15:D4', 'standby_vnic_mac': None, 'vlantag': 1, 'floating': True}]}
        """
        extract_bonding_conf_from_common_payload(PAYLOAD_CREATE_SERVICE_DUAL_STACK["jsonconf"], True, _scan_ips, PayloadBondOp.CreateService)
        # Having IPv6 only
        """
        Monitor conf created with below method for IPv6 is as below for iad103716exddu1101 DOMU:
        {'iad103716exddu1101': [{'type': 'host_ip', 'ip': '0.0.0.0', 'ipv6': 'fe80::17ff:fe13:5c91',
        'interface_type': 'client', 'mac': '02:00:17:12:15:D4', 'standby_vnic_mac': None, 'vlantag': 1,
        'floating': False}, {'type': 'host_ip', 'ip': '0.0.0.0', 'ipv6': 'fe80::17ff:fe13:5d91',
        'interface_type': 'backup', 'mac': '00:00:17:00:11:3F', 'standby_vnic_mac': None, 'vlantag': 2,
        'floating': False}, {'type': 'vip', 'ip': '0.0.0.0', 'ipv6': 'fe80::17ff:fe13:5c92',
        'interface_type': 'client', 'mac': '02:00:17:12:15:D4', 'standby_vnic_mac': None, 'vlantag': 1, 'floating': True}]}
        """
        extract_bonding_conf_from_common_payload(PAYLOAD_CREATE_SERVICE_IPv6["jsonconf"], True, [], PayloadBondOp.CreateService)

    def tests_elastic_node_payload_to_common_payload(self):
        # IPv4 only
        self.assertEqual(elastic_node_payload_to_common_payload(PAYLOAD_ADD_COMPUTE["jsonconf"]["reshaped_node_subset"]["added_computes"][0],
                                               PayloadBondOp.AddCompute), NEW_PAYLOAD_ADD_COMPUTE)
        # Dual stack
        self.assertEqual(elastic_node_payload_to_common_payload(PAYLOAD_ADD_COMPUTE_DUAL_STACK["jsonconf"]["reshaped_node_subset"]["added_computes"][0],
                                               PayloadBondOp.AddCompute), NEW_PAYLOAD_ADD_COMPUTE_DUAL_STACK)

        # IPv6 only
        self.assertEqual(elastic_node_payload_to_common_payload(PAYLOAD_ADD_COMPUTE_IPv6["jsonconf"]["reshaped_node_subset"]["added_computes"][0],
                                               PayloadBondOp.AddCompute), NEW_PAYLOAD_ADD_COMPUTE_IPv6)

    def tests_mPatchSSHDConfig(self):
        #IPv4 IP address check only
        _cluctrl = self.mGetClubox()
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject(["77.0.0.9"]), IOObject("stderr"))):
            _cluctrl.mPatchSSHDConfig()

    def tests_mGenerateXml(self):
        _cluctrl = self.mGetClubox()
        _uuid = _cluctrl.mGenerateUUID()
        _payload = xmlGenerationPayload
        _savedir = "./log/"
        _facade = ebFacadeXmlGen(_uuid, _payload, _savedir)
        _xml = _facade.mGenerateXml()

class ebTestIPv6MethodsCustomResources(ebTestClucontrol):
    """
    This class is used for testing with dual stack payload and dual stack xml
    """

    @classmethod
    def setUpClass(self):
        super(ebTestIPv6MethodsCustomResources, self).setUpClass(False,False,
                                                                 aResourceFolder='exabox/exatest/network/resources_ipv6/')

    def tests_mCustomerNetworkXMLUpdate(self):
        # This tests the dual stack payload
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.mGetClubox().mSetExabm(True)
        _cluctrl.mCustomerNetworkXMLUpdate(_options)

    def tests_mCustomerNetworkXMLUpdateBaseDB(self):
        # This tests the dual stack payload
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(_cluctrl.mGetArgsOptions())
        _cluctrl.mSetExabm(True)
        _basedb = exaBoxBaseDB(_cluctrl)
        _basedb.mCustomerNetworkXMLUpdateBaseDB(_options)

    def tests_mPatchSSHDConfig(self):
        # Test with dual stack - this will try to check for the given ipv4 and ipv6 addresses in
        # sshd_config and add it if not found.
        _cluctrl = self.mGetClubox()
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject(["77.0.0.9"]), IOObject("stderr"))):
            _cluctrl.mPatchSSHDConfig()

    def tests_mHandlerClusterXmlInfo(self):
        _cluctrl = self.mGetClubox()
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject(["/dev/mapper/VGExaDb-LVDbExaVMImages             1589G  204G     1385G      13% /EXAVMIMAGES"]), IOObject("stderr"))):
            _cluctrl.mHandlerClusterXmlInfo()

    def tests_mRemoveNodeFromCRS(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = PAYLOAD_ADD_COMPUTE["jsonconf"]
        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU'):
            _reshape_conf = ebCluReshapeCompute(_cluctrl, _options)
        mockCommands = {
            ".*exddu.*": [
                [
                    exaMockCommand("cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid",aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl unpin css -n ",aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl stop cluster -n ",aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl delete node -n ",aRc=0, aPersist=True),
                    exaMockCommand('/u01/app/19.0.0.0/grid/bin/srvctl config vip -n c3716n12c1 | grep "VIP IPv4 Address"',aRc=0, aStdout="VIP IPv4 Address: 10.0.3.203",aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl stop vip -vip ",aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl remove vip -vip ",aRc=0, aPersist=True),
                    exaMockCommand('/u01/app/19.0.0.0/grid/bin/srvctl config vip -n c3716n12c1 | grep "VIP IPv6 Address"',aRc=0, aStdout="VIP IPv6 Address: fe80::17ff:fe13:5c92",aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes -s -t",aRc=1, aPersist=True),
                    exaMockCommand("/bin/sed -i ",aRc=0, aPersist=True),
                ]
            ]
            
        }
        self.mPrepareMockCommands(mockCommands)
        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetSrcDomU', return_value="iad103716exddu1101.iad103716exd.adminiad1.oraclevcn.com"):
            _reshape_conf.mRemoveNodeFromCRS("c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com")

    def tests_mValidateNwOverlap(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _health_chk = ebCluHealthCheck(_cluctrl, _options)
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=False):
            _health_chk.mValidateNwOverlap(_cluctrl, [], {"XML": {}})

    def tests_mAddDomU(self):
        _oeda_cli = OedacliCmdMgr(os.path.join(self.mGetUtil().mGetResourcesPath(),"sample.xml"), "/tmp/")
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = PAYLOAD_ADD_COMPUTE_DUAL_STACK["jsonconf"]
        _json_payload = {}
        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU'):
            _reshape_obj = ebCluReshapeCompute(_cluctrl, _options)
            _json_payload = _reshape_obj.mGetReshapeConf()
        with patch('exabox.tools.oedacli.ebOedacli.run_oedacli'):
            _oeda_cli.mAddDomU("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                            "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com",
                            "/tmp/src.xml", "/tmp/dest.xml", _json_payload['nodes'][0], _cluctrl)

    def tests_mGetReconfigParams(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        PAYLOAD_CREATE_SERVICE_DUAL_STACK["jsonconf"]["preprov_network"] = PAYLOAD_CREATE_SERVICE_DUAL_STACK["jsonconf"]["customer_network"]
        _options.jsonconf = PAYLOAD_CREATE_SERVICE_DUAL_STACK["jsonconf"]
        _json_out = mGetReconfigParams(_cluctrl, _options)

    def tests_mGridUpdateOratab(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject(["DISK1 DISK1", "DISK2 DISK2"]), IOObject("stderr"))):
            mGridUpdateOratab(_cluctrl, _options, mGetReconfigParams_OUT)

    def tests_mUpdateConfXml(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'):
            _node_object = IOObject("node")
            mUpdateConfXml("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com", _node_object, mGetReconfigParams_OUT, "/EXAVMIMAGES/conf/c3716n11c1-vm.xml")

    def tests_mUpdateNWScripts(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.ovm.cluvmreconfig.mUpdateSysctlConf'),\
            patch('exabox.ovm.cluvmreconfig.getHVInstance', return_value=KvmMgr({"hostname":"iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com"})):
            _node_object = IOObject("node")
            mUpdateNWScripts(_node_object, "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com", "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                             mGetReconfigParams_OUT, _cluctrl, "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com", _options)

    def tests_mDomUReconfig(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mConfigurePasswordLessDomU'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject("stdout"), IOObject("stderr"))):
            mDomUReconfig(_cluctrl, _options, mGetReconfigParams_OUT)

    def tests_mFetchNetworkInfo(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _node_recovery = NodeRecovery(_cluctrl, _options)
        self.assertEqual(_node_recovery.mFetchNetworkInfo("iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                                         "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                                         True), mFetchNetworkInfo_OUT)

    def tests_mRemoveNodeFromCRS(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _node_recovery = NodeRecovery(_cluctrl, _options)
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0),\
            patch('exabox.ovm.cluvmrecoveryutils.node_cmd_abs_path_check'),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject(["VIP IPv6 Address: IP"]), IOObject("stderr"))),\
            self.assertRaises(ExacloudRuntimeError):
            _node_recovery.mRemoveNodeFromCRS("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                                              "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com")

    def tests_mAddVIP(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _node_recovery = NodeRecovery(_cluctrl, _options)
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mIsConnectable', return_value=False),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"),
                                                                            IOObject(["Network 1 exists", "Subnet IPv4: 198.51.100.0/255.255.255.0/bondeth0, static (inactive)",
                                                                                      "Subnet IPv6: 2001:0db8:418:1ea4:0:0:0:0/64/bondeth0, static"]),
                                                                            IOObject("stderr"))):
            _node_recovery.mAddVIP("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com")

class ebTestIPv6OnlyMethodsCustomResources(ebTestClucontrol):
    """
    This class is used for testing with single stack ipv6 payload and single stack ipv6 xml
    """

    @classmethod
    def setUpClass(self):
        super(ebTestIPv6OnlyMethodsCustomResources, self).setUpClass(False,False,
                                                                 aResourceFolder='exabox/exatest/network/resources_ipv6/ipv6_only/')

    def tests_mCustomerNetworkXMLUpdate(self):
        # This tests the single stack ipv6 payload
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.mGetClubox().mSetExabm(True)
        _cluctrl.mCustomerNetworkXMLUpdate(_options)

    def tests_mCustomerNetworkXMLUpdateBaseDB(self):
        # This tests the single stack ipv6 payload
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(_cluctrl.mGetArgsOptions())
        _cluctrl.mSetExabm(True)
        _basedb = exaBoxBaseDB(_cluctrl)
        _basedb.mCustomerNetworkXMLUpdateBaseDB(_options)

    def tests_mPatchSSHDConfig(self):
        # Test with single stack ipv6 - this will try to check for the given ipv6 addresses in
        # sshd_config and add it if not found.
        _cluctrl = self.mGetClubox()
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject(["fe80::200:17ff:fee4:6f22"]), IOObject("stderr"))):
            _cluctrl.mPatchSSHDConfig()

    def tests_mHandlerClusterXmlInfo(self):
        _cluctrl = self.mGetClubox()
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject(["/dev/mapper/VGExaDb-LVDbExaVMImages             1589G  204G     1385G      13% /EXAVMIMAGES"]), IOObject("stderr"))):
            _cluctrl.mHandlerClusterXmlInfo()

    def tests_mRemoveNodeFromCRS(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = PAYLOAD_ADD_COMPUTE_IPv6["jsonconf"]
        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU'):
            _reshape_conf = ebCluReshapeCompute(_cluctrl, _options)
        mockCommands = {
            ".*exddu.*": [
                [
                    exaMockCommand("cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid",aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl unpin css -n ",aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl delete node -n ",aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl stop vip -vip ",aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl remove vip -vip ",aRc=0, aPersist=True),
                    exaMockCommand('/u01/app/19.0.0.0/grid/bin/srvctl config vip -n c3716n12c1 | grep "VIP IPv6 Address"',aRc=0, aStdout="VIP IPv6 Address: fe80::17ff:fe13:5c92",aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes -s -t",aRc=1, aPersist=True),
                    exaMockCommand("/bin/sed -i ",aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetSrcDomU', return_value="iad103716exddu1101.iad103716exd.adminiad1.oraclevcn.com"):
            _reshape_conf.mRemoveNodeFromCRS("c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com")

    def tests_mValidateNwOverlap(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _health_chk = ebCluHealthCheck(_cluctrl, _options)
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=False):
            _health_chk.mValidateNwOverlap(_cluctrl, [], {"XML": {}})

    def tests_mAddDomU(self):
        _oeda_cli = OedacliCmdMgr(os.path.join(self.mGetUtil().mGetResourcesPath(),"sample.xml"), "/tmp/")
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = PAYLOAD_ADD_COMPUTE_IPv6["jsonconf"]
        _json_payload = {}
        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU'):
            _reshape_obj = ebCluReshapeCompute(_cluctrl, _options)
            _json_payload = _reshape_obj.mGetReshapeConf()
        with patch('exabox.tools.oedacli.ebOedacli.run_oedacli'):
            _oeda_cli.mAddDomU("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                            "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com",
                            "/tmp/src.xml", "/tmp/dest.xml", _json_payload['nodes'][0], _cluctrl)

    def tests_mGetReconfigParams(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        PAYLOAD_CREATE_SERVICE_IPv6["jsonconf"]["preprov_network"] = PAYLOAD_CREATE_SERVICE_IPv6["jsonconf"]["customer_network"]
        _options.jsonconf = PAYLOAD_CREATE_SERVICE_IPv6["jsonconf"]
        _json_out = mGetReconfigParams(_cluctrl, _options)

    def tests_mGridUpdateOratab(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject(["DISK1 DISK1", "DISK2 DISK2"]), IOObject("stderr"))):
            mGridUpdateOratab(_cluctrl, _options, mGetReconfigParams_OUT_IPV6)

    def tests_mUpdateConfXml(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'):
            _node_object = IOObject("node")
            mUpdateConfXml("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com", _node_object, mGetReconfigParams_OUT_IPV6, "/EXAVMIMAGES/conf/c3716n11c1-vm.xml")

    def tests_mUpdateNWScripts(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.ovm.cluvmreconfig.mUpdateSysctlConf'),\
            patch('exabox.ovm.cluvmreconfig.getHVInstance', return_value=KvmMgr({"hostname":"iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com"})):
            _node_object = IOObject("node")
            mUpdateNWScripts(_node_object, "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com", "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                             mGetReconfigParams_OUT_IPV6, _cluctrl, "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com", _options)

    def tests_mDomUReconfig(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mConfigurePasswordLessDomU'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject("stdout"), IOObject("stderr"))):
            mDomUReconfig(_cluctrl, _options, mGetReconfigParams_OUT_IPV6)

    def tests_mFetchNetworkInfo(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _node_recovery = NodeRecovery(_cluctrl, _options)
        self.assertEqual(_node_recovery.mFetchNetworkInfo("iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                                         "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                                         True), mFetchNetworkInfo_OUT_IPV6)

    def tests_mRemoveNodeFromCRS(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _node_recovery = NodeRecovery(_cluctrl, _options)
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0),\
            patch('exabox.ovm.cluvmrecoveryutils.node_cmd_abs_path_check'),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"), IOObject(["VIP IPv6 Address: IP"]), IOObject("stderr"))),\
            self.assertRaises(ExacloudRuntimeError):
            _node_recovery.mRemoveNodeFromCRS("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com",
                                              "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com")

    def tests_mAddVIP(self):
        _cluctrl = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _node_recovery = NodeRecovery(_cluctrl, _options)
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mIsConnectable', return_value=False),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(IOObject("stdin"),
                                                                            IOObject(["Network 1 exists",
                                                                                      "Subnet IPv6: 2001:0db8:418:1ea4:0:0:0:0/64/bondeth0, static"]),
                                                                            IOObject("stderr"))):
            _node_recovery.mAddVIP("c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com")

if __name__ == '__main__':
    unittest.main()
