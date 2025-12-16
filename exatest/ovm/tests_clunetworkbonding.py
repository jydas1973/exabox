#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clunetworkbonding.py /main/5 2025/03/05 16:36:07 rkhemcha Exp $
#
# tests_clunetworkbonding.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clunetworkbonding.py - Unit tests for LACP post MVP endpoints
#
#    DESCRIPTION
#      Exatest unit tests for LACP modification/validation endpoints
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rkhemcha    02/26/25 - 37628410 - Add UT for bumping bond during valdate
#                           bonding mode
#    rkhemcha    10/07/22 - Creation
#
import copy
import unittest
from unittest.mock import patch
import warnings

from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.clunetworkbonding import (
    ebCluNetworkBonding,
    NetworkBondingUtils,
    NetworkBondingValidator,
    NetworkBondingModifier
)

ACTIVE_BACKUP = "active-backup"
LACP = "lacp"

NETWORK_INFO = {
    "scaqan17adm01.us.oracle.com": {
        "client": {
            "bridge": "vmbondeth0",
            "bond_master": "bondeth0",
            "bond_slaves": "eth1 eth2"
        },
        "backup": {
            "bridge": "vmbondeth1",
            "bond_master": "bondeth1",
            "bond_slaves": "eth3 eth4"
        }
    },
    "scaqan17adm02.us.oracle.com": {
        "client": {
            "bridge": "vmbondeth0",
            "bond_master": "bondeth0",
            "bond_slaves": "eth1 eth2"
        },
        "backup": {
            "bridge": "vmbondeth1",
            "bond_master": "bondeth1",
            "bond_slaves": "eth3 eth4"
        }
    }
}

NETWORK_INFO_SHARED = {
    "client": {
        "bridge": "vmbondeth0",
        "bond_master": "bondeth0",
        "bond_slaves": "eth1 eth2"
    },
    "backup": {
        "bridge": "vmbondeth1",
        "bond_master": "bondeth1",
        "bond_slaves": "eth1 eth2"
    }
}

PAYLOAD = {
    "network_types": {
        "client": {
            "bonding_mode": {
                "current": "active-backup",
                "new": "lacp"
            }
        },
        "backup": {
            "bonding_mode": {
                "current": "lacp",
                "new": "active-backup"
            }
        }
    },
    "num_participating_computes": 2,
    "participating_computes": [
        {
            "compute_node_alias": "node-1",
            "compute_node_hostname": "scaqan17adm01.us.oracle.com"
        },
        {
            "compute_node_alias": "node-2",
            "compute_node_hostname": "scaqan17adm02.us.oracle.com"
        }
    ]
}

SUCCESSFUL_NEGOTIATIONS = [
    "Ethernet Channel Bonding Driver: v3.7.1 (April 27, 2011)",
    "Bonding Mode: IEEE 802.3ad Dynamic link aggregation",
    "802.3ad info",
    "LACP rate: fast",
    "Min links: 0",
    "Aggregator selection policy (ad_select): stable",
    "System priority: 65535",
    "System MAC address: a8:69:8c:03:5b:c3",
    "Active Aggregator Info:",
    "Aggregator ID: 1",
    "Number of ports: 2",
    "Actor Key: 21",
    "Partner Key: 32889",
    "Partner Mac Address: 00:23:04:ee:be:11",

    "Actor Churn State: none",
    "Partner Churn State: none",
    "Actor Churned Count: 0",
    "Partner Churned Count: 0",

    "Actor Churn State: none",
    "Partner Churn State: none",
    "Actor Churned Count: 0",
    "Partner Churned Count: 0"
]

NEGOTIATIONS_MONITORING = [
    "Ethernet Channel Bonding Driver: v3.7.1 (April 27, 2011)",
    "Bonding Mode: IEEE 802.3ad Dynamic link aggregation",
    "802.3ad info",
    "LACP rate: fast",
    "Min links: 0",
    "Aggregator selection policy (ad_select): stable",
    "System priority: 65535",
    "System MAC address: a8:69:8c:03:5b:c3",
    "Active Aggregator Info:",
    "Aggregator ID: 1",
    "Number of ports: 2",
    "Actor Key: 21",
    "Partner Key: 32889",
    "Partner Mac Address: 00:23:04:ee:be:11",

    "Actor Churn State: monitoring",
    "Partner Churn State: monitoring",
    "Actor Churned Count: 0",
    "Partner Churned Count: 0",

    "Actor Churn State: monitoring",
    "Partner Churn State: monitoring",
    "Actor Churned Count: 0",
    "Partner Churned Count: 0"
]

NEGOTIATIONS_CHURNED = [
    "Ethernet Channel Bonding Driver: v3.7.1 (April 27, 2011)",
    "Bonding Mode: IEEE 802.3ad Dynamic link aggregation",
    "802.3ad info",
    "LACP rate: fast",
    "Min links: 0",
    "Aggregator selection policy (ad_select): stable",
    "System priority: 65535",
    "System MAC address: a8:69:8c:03:5b:c3",
    "Active Aggregator Info:",
    "Aggregator ID: 1",
    "Number of ports: 2",
    "Actor Key: 21",
    "Partner Key: 32889",
    "Partner Mac Address: 00:23:04:ee:be:11",

    "Actor Churn State: churned",
    "Partner Churn State: churned",
    "Actor Churned Count: 0",
    "Partner Churned Count: 0",

    "Actor Churn State: churned",
    "Partner Churn State: churned",
    "Actor Churned Count: 0",
    "Partner Churned Count: 0"
]

IFCFG_LACP = b"""
#### DO NOT REMOVE THESE LINES ####
#### %GENERATED BY CELL% ####
DEVICE=bondeth0
USERCTL=no
BOOTPROTO=none
ONBOOT=yes
BONDING_OPTS="mode=802.3ad miimon=100 downdelay=200 updelay=200 lacp_rate=1 xmit_hash_policy=layer3+4"
BRIDGE=vmbondeth0
NM_CONTROLLED=no
MTU=1500
"""

IFCFG_ACBKP = b"""
#### DO NOT REMOVE THESE LINES ####
#### %GENERATED BY CELL% ####
DEVICE=bondeth0
USERCTL=no
BOOTPROTO=none
ONBOOT=yes
BONDING_OPTS="mode=active-backup miimon=100 downdelay=2000 updelay=5000 num_grat_arp=100"
BRIDGE=vmbondeth0
NM_CONTROLLED=no
MTU=1500
"""

BRIDGE_CONF_ACBKP = b"""<?xml version='1.0' standalone='yes'?>
<Discovery_Set_Bridge_Bonded>
  <Interfaces>
   <Bond_type>bonded</Bond_type>
   <Bondeth_mode>active-backup</Bondeth_mode>
   <Bridge>vmbondeth0</Bridge>
   <Link_speed>default</Link_speed>
   <Name>bondeth0</Name>
   <Net_type>Dynamic</Net_type>
   <Slaves>eth1</Slaves>
   <Slaves>eth2</Slaves>
   <State>1</State>
   <Status>UP</Status>
   <Mtu_size>1500</Mtu_size>
   <Vlan_id>0</Vlan_id>
  </Interfaces>
<Interfaces>
  <Bond_type>single</Bond_type>
  <Master>bondeth0</Master>
  <Name>eth1</Name>
  <State>1</State>
  <Status>UP</Status>
</Interfaces>
<Interfaces>
  <Bond_type>single</Bond_type>
  <Master>bondeth0</Master>
  <Name>eth2</Name>
  <State>1</State>
  <Status>UP</Status>
</Interfaces>
</Discovery_Set_Bridge_Bonded>"""

MII_UP=[
    "Currently Active Slave: eth1",
    "MII Status: up",
    "--",
    "Slave Interface: eth1",
    "MII Status: up",
    "--",
    "Slave Interface: eth2",
    "MII Status: up"
]

MII_DOWN=[
    "Currently Active Slave: eth1",
    "MII Status: up",
    "--",
    "Slave Interface: eth1",
    "MII Status: up",
    "--",
    "Slave Interface: eth2",
    "MII Status: down"
]

class testOptions(object):
    def __init__(self, payload=PAYLOAD) -> None:
        self.jsonconf = payload
        self.jsonmode = False


class ebTestCluNetworkBonding(ebTestClucontrol):
    @classmethod
    def setUpClass(cls):
        super(ebTestCluNetworkBonding, cls).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding.validateSharedIntfPayload")
    def test_init(self, mock_validateSharedIntfPayload):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_validateSharedIntfPayload.return_value = True
        nwBonding = ebCluNetworkBonding(cluctrl, testOptions(), "modification")
        self.assertEqual(nwBonding.outputData["overallStatus"], "FAILURE")
        for node in nwBonding.outputData["participating_computes"]:
            for _, network in node["network_types"].items():
                self.assertEqual(network["status"], "FAILURE")
                self.assertEqual(network["msg"], "")

    def test_invalidPayload1(self):
        # Test missing "participating_computes" in the received payload
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        testPayload = copy.deepcopy(PAYLOAD)
        del testPayload["participating_computes"]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkBonding(cluctrl, testOptions(testPayload), "modification")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertEqual(
            "EXACLOUD : Invalid input payload received. Please check the payload and retry.",
            ctx.exception.mGetErrorMsg()
        )

    def test_invalidPayload2(self):
        # Test missing "network_types" in the received payload
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        testPayload = copy.deepcopy(PAYLOAD)
        del testPayload["network_types"]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkBonding(cluctrl, testOptions(testPayload), "modification")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertEqual(
            "EXACLOUD : Invalid input payload received. Please check the payload and retry.",
            ctx.exception.mGetErrorMsg()
        )

    def test_invalidPayload3(self):
        # Test missing "bonding_mode" for "backup" network in the received payload
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        testPayload = copy.deepcopy(PAYLOAD)
        del testPayload["network_types"]["backup"]["bonding_mode"]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkBonding(cluctrl, testOptions(testPayload), "modification")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertEqual(
            "EXACLOUD : Invalid input payload received. Please check the payload and retry.",
            ctx.exception.mGetErrorMsg()
        )

    def test_invalidPayload4(self):
        # Test missing "new bonding state" for "backup" network in the received payload
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        testPayload = copy.deepcopy(PAYLOAD)
        del testPayload["network_types"]["backup"]["bonding_mode"]["new"]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkBonding(cluctrl, testOptions(testPayload), "modification")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertEqual(
            "EXACLOUD : Invalid input payload received. Please check the payload and retry.",
            ctx.exception.mGetErrorMsg()
        )

    def test_invalidPayload5(self):
        # Test missing "compute_node_hostname" for a dom0 in the received payload
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        testPayload = copy.deepcopy(PAYLOAD)
        testPayload["participating_computes"][0]["compute_node_hostname"] = ""
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkBonding(cluctrl, testOptions(testPayload), "modification")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertEqual(
            "EXACLOUD : Invalid input payload received. Please check the payload and retry.",
            ctx.exception.mGetErrorMsg()
        )

    def test_empty_participating_computes(self):
        # Test empty "participating_computes" in the received payload
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        testPayload = copy.deepcopy(PAYLOAD)
        testPayload["participating_computes"] = []
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkBonding(cluctrl, testOptions(testPayload), "modification")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertEqual(
            "EXACLOUD : Invalid input payload received. Please check the payload and retry.",
            ctx.exception.mGetErrorMsg()
        )

    def test_nonOCIEXACC(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(False)
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkBonding(cluctrl, testOptions(), "modification")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8005)
        self.assertEqual(
            "EXACLOUD : Detected non-OCIEXACC environment. Network Bonding change is not supported",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_sharedIntfPayloadFail(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = NETWORK_INFO_SHARED
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkBonding(cluctrl, testOptions(), "modification")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertEqual(
            "EXACLOUD : Invalid input payload received. Please check the payload and retry.",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_sharedIntfPayloadPass(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        testPayload = copy.deepcopy(PAYLOAD)
        testPayload["network_types"]["backup"]["current"] = "active-backup"
        testPayload["network_types"]["backup"]["new"] = "lacp"
        mock_mGetNetworkSetupInformation.return_value = NETWORK_INFO["scaqan17adm01.us.oracle.com"]
        nwBonding = ebCluNetworkBonding(cluctrl, testOptions(testPayload), "modification")
        self.assertEqual(nwBonding.outputData["overallStatus"], "FAILURE")
        for node in nwBonding.outputData["participating_computes"]:
            for _, network in node["network_types"].items():
                self.assertEqual(network["status"], "FAILURE")
                self.assertEqual(network["msg"], "")

    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding._mValidatePayload")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingModifier.mPerformOp")
    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding._mUpdateRequestData")
    def test_mApply_modification(self,
                                 mock__mUpdateRequestData,
                                 mock_mPerformOp,
                                 mock__mValidatePayload
                                 ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock__mValidatePayload.return_value = None
        mock_mPerformOp.return_value = None
        mock__mUpdateRequestData.return_value = None
        nwBonding = ebCluNetworkBonding(cluctrl, testOptions(), "modification")
        nwBonding.intfInfoDom0s = NETWORK_INFO
        nwBonding.mApply("modification")
        self.assertEqual(nwBonding.outputData["overallStatus"], "SUCCESS")

    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding._mValidatePayload")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingValidator.mPerformOp")
    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding._mUpdateRequestData")
    def test_mApply_validation(self,
                               mock__mUpdateRequestData,
                               mock_mPerformOp,
                               mock__mValidatePayload
                               ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock__mValidatePayload.return_value = None
        mock_mPerformOp.return_value = None
        mock__mUpdateRequestData.return_value = None
        nwBonding = ebCluNetworkBonding(cluctrl, testOptions(), "validation")
        nwBonding.intfInfoDom0s = NETWORK_INFO
        nwBonding.mApply("validation")
        self.assertEqual(nwBonding.outputData["overallStatus"], "SUCCESS")

    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding._mValidatePayload")
    def test_mApply_invalidOp(self, mock__mValidatePayload):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock__mValidatePayload.return_value = None
        nwBonding = ebCluNetworkBonding(cluctrl, testOptions(), "validation")
        nwBonding.intfInfoDom0s = NETWORK_INFO

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nwBonding.mApply("communication")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8005)
        self.assertEqual(
            "EXACLOUD : Wrong operation communication identified. Exiting.",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding._mValidatePayload")
    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding._mUpdateRequestData")
    def test_mApply_validation_fail(self,
                                    mock__mUpdateRequestData,
                                    mock__mValidatePayload,
                                    mock_mConnect,
                                    mock_mExecuteCmd
                                    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock__mValidatePayload.return_value = None
        mock__mUpdateRequestData.return_value = None
        mock_mExecuteCmd.side_effect = [(1, "", "")]

        nwBonding = ebCluNetworkBonding(cluctrl, testOptions(), "validation")
        nwBonding.intfInfoDom0s = NETWORK_INFO
        nwBonding.mApply("validation")
        self.assertEqual(nwBonding.outputData["overallStatus"], "FAILURE")
        self.assertEqual(nwBonding.outputData["errorcode"], "0x02040008")
        self.assertEqual(
            nwBonding.outputData["msg"],
            "Network bonding validation unsuccessful on one or more nodes. "
            "Please check the report for details."
        )

    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding._mValidatePayload")
    @patch("exabox.ovm.clunetworkbonding.ebCluNetworkBonding._mUpdateRequestData")
    def test_mApply_modification_fail(self,
                                    mock__mUpdateRequestData,
                                    mock__mValidatePayload,
                                    mock_mConnect,
                                    mock_mExecuteCmd
                                    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock__mValidatePayload.return_value = None
        mock__mUpdateRequestData.return_value = None
        mock_mExecuteCmd.side_effect = [(1, "", "")]

        nwBonding = ebCluNetworkBonding(cluctrl, testOptions(), "validation")
        nwBonding.intfInfoDom0s = NETWORK_INFO
        nwBonding.mApply("modification")
        self.assertEqual(nwBonding.outputData["overallStatus"], "FAILURE")
        self.assertEqual(nwBonding.outputData["errorcode"], "0x02040007")
        self.assertEqual(
            nwBonding.outputData["msg"],
            "EXACLOUD : Failed to create backup dir /opt/exacloud/nw_bonding/exatest on scaqan17adm01.us.oracle.com"
        )

class ebTestNetworkBondingUtils(ebTestClucontrol):

    def test_init(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        bondingUtils = NetworkBondingUtils(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )
        self.assertEqual(bondingUtils.currentBonding, "active-backup")
        self.assertEqual(bondingUtils.newBonding, "lacp")

    def test_mGetUUID(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        bondingUtils = NetworkBondingUtils(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )
        self.assertEqual(bondingUtils.mGetUUID(), "exatest")

    def test_mGetBackupDir(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        bondingUtils = NetworkBondingUtils(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )
        self.assertEqual(bondingUtils._mGetBackupDir(), "/opt/exacloud/nw_bonding/exatest")

    def test_mGetNetworkInfo(self):
        # Test _mGetMasterInterface and _mGetSlaveInterfaces of NetworkBondingUtils
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)

        bondingUtils = NetworkBondingUtils(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )
        self.assertEqual(bondingUtils._mGetMasterInterface(), "bondeth0")
        self.assertEqual(bondingUtils._mGetSlaveInterfaces(), ["eth1", "eth2"])

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mBumpBondedInterface_ifdown_fail(self,
                                               mock_mExecuteCmd,
                                               mock_mConnect
                                               ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [(1, "", "")]

        bondingUtils = NetworkBondingUtils(
            cluctrl,
            "backup",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["backup"]),
            NETWORK_INFO
        )

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingUtils.mBumpBondedInterface(0x8008)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8008)
        self.assertEqual(
            "EXACLOUD : Failed to bring down the interface bondeth1 on host scaqan17adm01.us.oracle.com.",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(cmd, "ifdown bondeth1")

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mBumpBondedInterface_ifup_fail(self,
                                             mock_mExecuteCmd,
                                             mock_mConnect
                                             ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [(0, "", ""),
                                        (1, "", "")]

        bondingUtils = NetworkBondingUtils(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingUtils.mBumpBondedInterface(0x8008)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8008)
        self.assertEqual(
            "EXACLOUD : Failed to bring up the interface bondeth0 on host scaqan17adm01.us.oracle.com.",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(cmd, "ifdown bondeth0")
        _, cmd = calls[1][0]
        self.assertEqual(cmd, "ifup bondeth0")


class ebTestNetworkBondingValidator(ebTestClucontrol):

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mValidateConfigSuccess(self,
                                    mock_mExecuteCmd,
                                    mock_mConnect
                                    ):
        # Test config is in line with what is expected
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.return_value = (0, "", "")
        bondingValidifier = NetworkBondingValidator(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )
        bondingValidifier.mValidateConfig(LACP)
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/grep -ie '802.3ad Dynamic link aggregation' /proc/net/bonding/bondeth0",
        )
        mock_mExecuteCmd.reset_mock()

        bondingValidifier.mValidateConfig(ACTIVE_BACKUP)
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/grep -ie 'active-backup' /proc/net/bonding/bondeth0",
        )
        mock_mExecuteCmd.reset_mock()

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mValidateConfigFail(self,
                                 mock_mExecuteCmd,
                                 mock_mConnect
                                 ):
        # Test config is in line with what is expected
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.return_value = (1, "", "")
        bondingValidifier = NetworkBondingValidator(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingValidifier.mValidateConfig(LACP)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8009)
        self.assertEqual(
            "EXACLOUD : Bonding config is incorrect for client network on scaqan17adm01.us.oracle.com. Please check the file /proc/net/bonding/bondeth0 on the host and retry.",
            ctx.exception.mGetErrorMsg()
        )
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        mock_mExecuteCmd.reset_mock()

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mCheckInLacpduPackets(self,
                                   mock_mExecuteCmd,
                                   mock_mConnect
                                   ):
        # Test config is in line with what is expected
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.return_value = (0, "", "")
        bondingValidifier = NetworkBondingValidator(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        self.assertEqual(bondingValidifier.mCheckInLacpduPackets(), True)
        # Call count will be 2, one tcpdump for each interface i.e eth1/2
        self.assertEqual(mock_mExecuteCmd.call_count, 2)

        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "timeout 35 tcpdump --direction=in -nn -xx -i eth1 -s 0 -c 1 ether proto 0x8809 2>/dev/null",
        )
        _, cmd = calls[1][0]
        self.assertEqual(
            "timeout 35 tcpdump --direction=in -nn -xx -i eth2 -s 0 -c 1 ether proto 0x8809 2>/dev/null",
            cmd,
        )
        mock_mExecuteCmd.reset_mock()

    @patch("exabox.ovm.clunetworkbonding.NetworkBondingValidator.mValidateConfig")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingValidator.mCheckInLacpduPackets")
    def test_mValidateActiveBackup(self,
                                   mock_mCheckInLacpduPackets,
                                   mock_mValidateConfig
                                   ):
        # Test config is in line with what is expected
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mValidateConfig.return_value = None
        mock_mCheckInLacpduPackets.side_effect = [True, False]

        bondingValidifier = NetworkBondingValidator(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        # Failure Case
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingValidifier.mValidateActiveBackup()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8009)
        self.assertEqual(
            "EXACLOUD : LACPDU packets seen on one or more interfaces of the client network on host scaqan17adm01.us.oracle.com. Please check the switch configuration and try again.",
            ctx.exception.mGetErrorMsg()
        )

        # Case where current and new bonding same
        bondingValidifier.mValidateActiveBackup()
        self.assertEqual("Network bonding mode validation successful.",
                         bondingValidifier.mGetResultMessage())

    @patch("exabox.ovm.clunetworkbonding.NetworkBondingValidator.mValidateIntfsUp")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingValidator.mValidateLacp")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingValidator.mValidateActiveBackup")
    def test_mPerformOp(self,
                        mock_mValidateActiveBackup,
                        mock_mValidateLacp,
                        mock_mValidateIntfsUp
                        ):
        # Test config is in line with what is expected
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mValidateIntfsUp.return_value = None
        mock_mValidateLacp.return_value = None
        mock_mValidateActiveBackup.return_value = None

        currentNewSameBondingPayload = copy.deepcopy(PAYLOAD)
        currentNewSameBondingPayload["network_types"]["client"]["bonding_mode"]["current"] = "lacp"

        bondingValidifier = NetworkBondingValidator(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(currentNewSameBondingPayload["network_types"]["client"]),
            NETWORK_INFO
        )

        bondingValidifier.mPerformOp()
        self.assertEqual("Current and new bonding modes are same. No validation needed.",
                         bondingValidifier.mGetResultMessage())

        # New bonding is lacp
        bondingValidifier = NetworkBondingValidator(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )
        bondingValidifier.mPerformOp()
        self.assertEqual(mock_mValidateLacp.call_count, 1)

        # New bonding is active-backup
        bondingValidifier = NetworkBondingValidator(
            cluctrl,
            "backup",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["backup"]),
            NETWORK_INFO
        )
        bondingValidifier.mPerformOp()
        self.assertEqual(mock_mValidateActiveBackup.call_count, 1)

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mValidateIntfsUp(self,
                              mock_mExecuteCmd,
                              mock_mConnect
                              ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)

        mock_mExecuteCmd.side_effect = [
            (1, "", ""),
            (0, MII_UP, ""),
            (0, MII_DOWN, "")
        ]

        bondingValidifier = NetworkBondingValidator(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        # Failure Case
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingValidifier.mValidateIntfsUp()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8009)
        self.assertEqual(
            "EXACLOUD : Failed to check state of physical interface's on scaqan17adm01.us.oracle.com.",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/grep -B 1 -ie 'MII Status' /proc/net/bonding/bondeth0",
        )

        # Success Case all intf up
        bondingValidifier.mValidateIntfsUp()
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/grep -B 1 -ie 'MII Status' /proc/net/bonding/bondeth0",
        )

        # Failure Case some intf down
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingValidifier.mValidateIntfsUp()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8009)
        self.assertEqual(
            "EXACLOUD : Waiting for physical interfaces of client network to be up on the host scaqan17adm01.us.oracle.com.",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/grep -B 1 -ie 'MII Status' /proc/net/bonding/bondeth0",
        )

    @patch("exabox.ovm.clunetworkbonding.NetworkBondingValidator.mBumpBondedInterface")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingValidator.mValidateConfig")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mValidateLacp(self,
                           mock_mExecuteCmd,
                           mock_mConnect,
                           mock_mValidateConfig,
                           mock_mBumpBondedInterface
                           ):
        # Test config is in line with what is expected
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)

        mock_mValidateConfig.return_value = None
        mock_mBumpBondedInterface.return_value = None
        mock_mExecuteCmd.side_effect = [
            (1, "", ""),
            (0, SUCCESSFUL_NEGOTIATIONS, ""),
            (0, NEGOTIATIONS_MONITORING, ""),
            (0, NEGOTIATIONS_CHURNED, "")
        ]

        bondingValidifier = NetworkBondingValidator(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        # Failure Case
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingValidifier.mValidateLacp()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8009)
        self.assertEqual(
            "EXACLOUD : Failed to validate bonding mode on scaqan17adm01.us.oracle.com.",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/grep -ie 'Churn State' /proc/net/bonding/bondeth0",
        )

        # Success Case with negotiations complete
        bondingValidifier.mValidateLacp()
        self.assertEqual("Network bonding mode validation successful.",
                         bondingValidifier.mGetResultMessage())
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/grep -ie 'Churn State' /proc/net/bonding/bondeth0",
        )

        # Monitoring Case
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingValidifier.mValidateLacp()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8009)
        self.assertEqual(
            "EXACLOUD : LACP bonds currently in negotiation state. Please retry after some time.",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/grep -ie 'Churn State' /proc/net/bonding/bondeth0",
        )

        # Churned Case
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingValidifier.mValidateLacp()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8009)
        self.assertEqual(
            "EXACLOUD : LACP bonds in churned state. Please check the switch configuration for client network ports for scaqan17adm01.us.oracle.com and retry.",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/grep -ie 'Churn State' /proc/net/bonding/bondeth0",
        )


class ebTestNetworkBondingModifier(ebTestClucontrol):

    @patch("os.path.isdir", return_value=False)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mCreateBackupDir(self,
                              mock_mExecuteCmd,
                              mock_mConnect,
                              mock_isdir
                              ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [(0, "", ""),
                                        (1, "", "")]

        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        # Success path
        bondingModifier.mCreateBackupDir()
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/mkdir -p /opt/exacloud/nw_bonding/exatest",
        )

        # Failure path
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingModifier.mCreateBackupDir()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8008)
        self.assertEqual(
            "EXACLOUD : Failed to create backup dir /opt/exacloud/nw_bonding/exatest on scaqan17adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/mkdir -p /opt/exacloud/nw_bonding/exatest",
        )

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mBackupBondingConfig(self,
                                  mock_mExecuteCmd,
                                  mock_mConnect
                                  ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [(0, "", ""),
                                        (1, "", "")]

        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        # Success path
        bondingModifier.mBackupBondingConfig()
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/cp /etc/sysconfig/network-scripts/ifcfg-bondeth0 /opt/exacloud/nw_bonding/exatest",
        )

        # Failure path
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingModifier.mBackupBondingConfig()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8008)
        self.assertEqual(
            "EXACLOUD : Failed to take backup of /etc/sysconfig/network-scripts/ifcfg-bondeth0 on scaqan17adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/cp /etc/sysconfig/network-scripts/ifcfg-bondeth0 /opt/exacloud/nw_bonding/exatest",
        )

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mBackupGuestMetadata(self,
                                  mock_mExecuteCmd,
                                  mock_mConnect
                                  ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [(0, "", ""),
                                        (1, "", "")]

        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        # Success path
        bondingModifier.mBackupGuestMetadata()
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/cp /etc/exadata/ovm/bridge.conf.d/*bondeth0* /opt/exacloud/nw_bonding/exatest",
        )

        # Failure path
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingModifier.mBackupGuestMetadata()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8008)
        self.assertEqual(
            "EXACLOUD : Failed to take backup of /etc/exadata/ovm/bridge.conf.d on scaqan17adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/bin/cp /etc/exadata/ovm/bridge.conf.d/*bondeth0* /opt/exacloud/nw_bonding/exatest",
        )

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mBringBridgeUp_pass(self,
                                   mock_mExecuteCmd,
                                   mock_mConnect
                                   ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [(0, "", ""),
                                        (0, "", ""),
                                        (0, "", "")]

        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        bondingModifier.mBringBridgeUp()
        self.assertEqual(mock_mExecuteCmd.call_count, 3)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(cmd, "ifdown bondeth0")
        _, cmd = calls[1][0]
        self.assertEqual(cmd, "ifup bondeth0")
        _, cmd = calls[2][0]
        self.assertEqual(cmd, "ifup vmbondeth0")

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    def test_mBringBridgeUp_fail(self,
                                 mock_mExecuteCmd,
                                 mock_mConnect
                                 ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [(0, "", ""),
                                        (0, "", ""),
                                        (1, "", ""), ]

        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingModifier.mBringBridgeUp()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8008)
        self.assertEqual(
            "EXACLOUD : Failed to bring up the interface vmbondeth0 on scaqan17adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(cmd, "ifdown bondeth0")
        _, cmd = calls[1][0]
        self.assertEqual(cmd, "ifup bondeth0")
        _, cmd = calls[2][0]
        self.assertEqual(cmd, "ifup vmbondeth0")

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    def test_mModifyBondingConfig(self,
                                  mock_mWriteFile,
                                  mock_mReadFile,
                                  mock_mConnect
                                  ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mReadFile.side_effect = [IFCFG_ACBKP, IFCFG_LACP]
        mock_mReadFile.return_value = None

        # Success path Active-Backup to LACP
        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )
        bondingModifier.mModifyBondingConfig()

        # Success path LACP to Active-Backup
        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "backup",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["backup"]),
            NETWORK_INFO
        )
        bondingModifier.mModifyBondingConfig()

        self.assertEqual(mock_mReadFile.call_count, 2)
        self.assertEqual(mock_mWriteFile.call_count, 2)

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingUtils.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    def test_mUpdateBridgeMetadata(self,
                                   mock_mWriteFile,
                                   mock_mReadFile,
                                   mock_mExecuteCmd,
                                   mock_mConnect
                                   ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [
            (0, ["/etc/exadata/ovm/bridge.conf.d/bridge.vmbondeth0.0.bondeth0.0.eth1.eth2.xml"], ""),
            (1, "", "")
        ]
        mock_mReadFile.return_value = BRIDGE_CONF_ACBKP
        mock_mWriteFile.return_value = None

        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )
        bondingModifier.mUpdateBridgeMetadata()
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(cmd, "ls /etc/exadata/ovm/bridge.conf.d/*bondeth0*")
        self.assertEqual(mock_mReadFile.call_count, 1)
        self.assertEqual(mock_mWriteFile.call_count, 1)

        # Failure path
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            bondingModifier.mUpdateBridgeMetadata()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8008)
        self.assertEqual(
            "EXACLOUD : Failed to retrieve client bridge files on scaqan17adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg()
        )
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(cmd, "ls /etc/exadata/ovm/bridge.conf.d/*bondeth0*")

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingModifier.mCreateBackupDir")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingModifier.mBackupBondingConfig")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingModifier.mBackupGuestMetadata")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingModifier.mModifyBondingConfig")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingModifier.mUpdateBridgeMetadata")
    @patch("exabox.ovm.clunetworkbonding.NetworkBondingModifier.mBringBridgeUp")
    def test_mPerformOp(self,
                        mock_mBringBridgeUp,
                        mock_mUpdateBridgeMetadata,
                        mock_mModifyBondingConfig,
                        mock_mBackupGuestMetadata,
                        mock_mBackupBondingConfig,
                        mock_mCreateBackupDir,
                        mock_mGetNetworkSetupInformation
                        ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = None
        mock_mBringBridgeUp.return_value = None
        mock_mUpdateBridgeMetadata.return_value = None
        mock_mModifyBondingConfig.return_value = None
        mock_mBackupGuestMetadata.return_value = None
        mock_mBackupBondingConfig.return_value = None
        mock_mCreateBackupDir.return_value = None

        # current and new both bonding same flow
        currentNewSameBondingPayload = copy.deepcopy(PAYLOAD)
        currentNewSameBondingPayload["network_types"]["client"]["bonding_mode"]["current"] = "lacp"
        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(currentNewSameBondingPayload["network_types"]["client"]),
            NETWORK_INFO
        )

        bondingModifier.mPerformOp()
        self.assertEqual("Current and new bonding modes are same. No changes needed.",
                         bondingModifier.mGetResultMessage())

        # regular modify flow
        bondingModifier = NetworkBondingModifier(
            cluctrl,
            "client",
            PAYLOAD["participating_computes"][0]["compute_node_hostname"],
            copy.deepcopy(PAYLOAD["network_types"]["client"]),
            NETWORK_INFO
        )

        bondingModifier.mPerformOp()
        self.assertEqual(mock_mBringBridgeUp.call_count, 1)
        self.assertEqual(mock_mUpdateBridgeMetadata.call_count, 1)
        self.assertEqual(mock_mModifyBondingConfig.call_count, 1)
        self.assertEqual(mock_mBackupGuestMetadata.call_count, 1)
        self.assertEqual(mock_mBackupBondingConfig.call_count, 1)
        self.assertEqual(mock_mCreateBackupDir.call_count, 1)


if __name__ == "__main__":
    unittest.main()
