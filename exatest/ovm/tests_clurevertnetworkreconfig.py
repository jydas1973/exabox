#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clurevertnetworkreconfig.py /main/7 2025/05/21 05:57:34 rkhemcha Exp $
#
# tests_clurevertnetworkreconfig.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clurevertnetworkreconfig.py - Unittests for revert network reconfiguration for ExaCC
#
#    DESCRIPTION
#      Unittests for revert network reconfiguration for ExaCC
#
#    MODIFIED   (MM/DD/YY)
#    rkhemcha    09/10/24 - 35594111 - Unit tests for DNS/NTP revert reconfig
#    pvachhan    06/06/22 - BUG 34230694 - RECONFIGURING A BACKUP N/W OF A
#                           CLUSTER WITH SHARED BRIDGES FAILS TO DELETE STALE
#                           COMMON BRIDGE
#    pvachhan    05/25/22 - Unittests for revert network reconfiguration for
#                           ExaCC
#    pvachhan    05/25/22 - Creation
#

import copy
import warnings
import unittest

from unittest.mock import mock_open, patch
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.hypervisorutils import HVIT_XEN, HVIT_KVM
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.ovm.clurevertnetworkreconfig import (
    ebCluRevertNetworkReconfig,
    NodeRevertor,
    KvmNodeRevertor,
    XenNodeRevertor,
)
from exabox.exatest.ovm.tests_clunetworkreconfigcommons import (
    DOM0_NETWORK_INFO, VLAN_UPDATE_PAYLOAD, CIDR_UPDATE_PAYLOAD
)

NOOP_PAYLOAD = {
    "network": {},
    "updateNetwork": {
        "networkServices": [
            {
                "op": "dns_update",
                "payload": {
                    "compute_node_alias": "node-2"
                },
                "status": "NOOP",
                "msg": ""
            },
            {
                "op": "ntp_update",
                "payload": {
                    "compute_node_alias": "node-2"
                },
                "status": "NOOP",
                "msg": ""
            }
        ],
        "errorcode": "0x00000001",
        "nodes": [
            {
                "backup": [
                    {
                        "op": "cidr_update",
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0412-bkp",
                            "ip": "10.31.217.76",
                            "netmask": "255.255.255.128",
                            "vlantag": "411",
                            "compute_node_alias": "node-2"
                        },
                        "status": "FAILURE",
                        "msg": ""
                    }
                ],
                "updateProperties": {
                    "backup": [
                        "gateway",
                        "hostname",
                        "ip",
                        "netmask",
                        "vlantag"
                    ]
                }
            }
        ],
        "status": "NOOP",
        "msg": "Failed to take backup"
    },
    "uuid": "apply_uuid",
    "node_subset": {
        "participating_computes": [
            {
                "compute_node_alias": "node-2",
                "compute_node_hostname": "scaqab10adm02.us.oracle.com",
            },
        ],
        "num_participating_computes": 1,
    }
}

FAILURE_PAYLOAD = {
    "network": {},
    "updateNetwork": {
        "networkServices": [
            {
                "op": "dns_update",
                "payload": {
                    "compute_node_alias": "node-1"
                },
                "status": "FAILURE",
                "msg": "Failed to run ipconf"
            },
            {
                "op": "ntp_update",
                "payload": {
                    "compute_node_alias": "node-1"
                },
                "status": "FAILURE",
                "msg": "Failed to run ipconf"
            },
            {
                "op": "dns_update",
                "payload": {
                    "compute_node_alias": "node-2"
                },
                "status": "FAILURE",
                "msg": "Failed to run ipconf"
            },
            {
                "op": "ntp_update",
                "payload": {
                    "compute_node_alias": "node-2"
                },
                "status": "FAILURE",
                "msg": "Failed to run ipconf"
            }
        ],
        "nodes": [
            {
                "backup": [
                    {
                        "op": "cidr_update",
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0312-bk",
                            "ip": "10.31.217.72",
                            "netmask": "255.255.255.128",
                            "vlantag": "154",
                            "compute_node_alias": "node-1"
                        },
                        "status": "FAILURE",
                        "msg": "Failed to run ipconf on host"
                    }
                ],
                "updateProperties": {
                    "backup": [
                        "gateway",
                        "hostname",
                        "ip",
                        "netmask",
                        "vlantag"
                    ]
                }
            },
            {
                "backup": [
                    {
                        "op": "vlan_delete",
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0412-bkp",
                            "ip": "10.31.217.76",
                            "netmask": "255.255.255.128",
                            "vlantag": "411",
                            "compute_node_alias": "node-2"
                        },
                        "status": "NOOP",
                        "msg": ""
                    }
                ],
                "updateProperties": {
                    "backup": [
                        "gateway",
                        "hostname",
                        "ip",
                        "netmask",
                        "vlantag"
                    ]
                }
            }
        ],
        "status": "FAILURE",
        "msg": "Failed to run ipconf",
        "errorcode": "0x00000001"
    },
    "node_subset": {
        "num_participating_computes": 2,
        "participating_computes": [
            {
                "compute_node_alias": "node-1",
                "compute_node_hostname": "scaqab10adm01.us.oracle.com"
            },
            {
                "compute_node_alias": "node-2",
                "compute_node_hostname": "scaqab10adm02.us.oracle.com"
            }
        ]
    },
    "uuid": "apply_uuid"
}

NOOP_WORKING_PAYLOAD = {
    "ipconf_updates": {
        "entities": [
            "backup",
            "dns",
            "ntp"
        ],
        "status": "NOOP",
        "msg": ""
    },
    "vlan_add_backup": {
        "payload": {
            "domainname": "us.oracle.com",
            "gateway": "10.32.94.65",
            "hostname": "scaqan04dv0302-bk",
            "ip": "10.32.94.89",
            "netmask": "255.255.255.224",
            "vlantag": "129",
        },
        "status": "NOOP",
        "msg": ""
    },
    "vlan_delete_backup": {
        "payload": {
            "domainname": "us.oracle.com",
            "gateway": "10.32.94.65",
            "hostname": "scaqan04dv0301-bk",
            "ip": "10.32.94.88",
            "netmask": "255.255.255.224",
            "vlantag": "130",
        },
        "status": "NOOP",
        "msg": ""
    }
}

class testOptions(object):
    def __init__(self, payload=None) -> None:
        if payload is None:
            self.jsonconf = copy.deepcopy(FAILURE_PAYLOAD)
        else:
            self.jsonconf = copy.deepcopy(payload)
        self.jsonmode = False
        self.configpath = None


class ebTestCluRevertNetworkReconfig(ebTestClucontrol):
    @classmethod
    def setUpClass(cls):
        super(ebTestCluRevertNetworkReconfig, cls).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    def test_init(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOptions(testOptions(payload=FAILURE_PAYLOAD))
        cluctrl.mSetOciExacc(True)
        revertNwReconfig = ebCluRevertNetworkReconfig(cluctrl, testOptions())
        self.assertEqual(revertNwReconfig.jsonmode, False)

    @patch("exabox.network.dns.DNSConfig.ebDNSConfig.mRestartDnsmasq", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.ebCluRevertNetworkReconfig.mRevertExaccHosts", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.ebCluRevertNetworkReconfig.mCreateBackupDirCps", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.getTargetHVIType")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRevertConfiguration", return_value=None)
    def test_applyXen(
            self,
            _mock_mRevertConfiguration,
            _mock_mCheckDom0NetworkType,
            mock_getTargetHVIType,
            mock_createBackupDirCps,
            mock_revertExaccHosts,
            mock_restartDnsmasq
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        options = testOptions(payload=FAILURE_PAYLOAD)
        cluctrl.mSetOptions(options)
        mock_getTargetHVIType.return_value = HVIT_XEN

        revertNwReconfig = ebCluRevertNetworkReconfig(cluctrl, testOptions())
        revertNwReconfig.apply()
        self.assertEqual(
            revertNwReconfig.payload["updateNetwork"]["status"], "SUCCESS"
        )
        mock_getTargetHVIType.reset_mock()

        mock_getTargetHVIType.return_value = HVIT_KVM
        revertNwReconfig.apply()

        self.assertEqual(
            revertNwReconfig.payload["updateNetwork"]["status"], "SUCCESS"
        )
        mock_getTargetHVIType.reset_mock()

        mock_getTargetHVIType.return_value = 0
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertNwReconfig.apply()
        self.assertEqual(revertNwReconfig.payload["updateNetwork"]["status"], "NOOP")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8005)
        self.assertIn("Unsupported hypervisor", ctx.exception.mGetErrorMsg())

    @patch("exabox.ovm.clurevertnetworkreconfig.ebCluRevertNetworkReconfig.mRevertExaccHosts", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.ebCluRevertNetworkReconfig.mCreateBackupDirCps", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.getTargetHVIType")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRevertConfiguration")
    def test_applyFails(
            self,
            mock_mRevertConfiguration,
            _mock_mCheckDom0NetworkType,
            mock_getTargetHVIType,
            mock_createBackupDirCps,
            mock_revertExaccHosts,
    ):
        mock_mRevertConfiguration.side_effect = ExacloudRuntimeError(
            0x8007, 0xA, "test_msg"
        )
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        options = testOptions(payload=FAILURE_PAYLOAD)
        cluctrl.mSetOptions(options)
        mock_getTargetHVIType.return_value = HVIT_XEN
        revertNwReconfig = ebCluRevertNetworkReconfig(cluctrl, testOptions())
        revertNwReconfig.apply()
        self.assertEqual(
            revertNwReconfig.payload["updateNetwork"]["status"], "FAILURE"
        )

    @patch("exabox.ovm.clurevertnetworkreconfig.ebCluRevertNetworkReconfig.mRevertExaccHosts", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.ebCluRevertNetworkReconfig.mCreateBackupDirCps", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.getTargetHVIType", return_value = HVIT_KVM)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRevertConfiguration", return_value=None)
    def test_apply_NOOP(
            self,
            _mock_mRevertConfiguration,
            _mock_mCheckDom0NetworkType,
            mock_getTargetHVIType,
            mock_createBackupDirCps,
            mock_revertExaccHosts
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        revertNwReconfig = ebCluRevertNetworkReconfig(cluctrl, testOptions(payload=NOOP_PAYLOAD))
        revertNwReconfig.apply()
        _mock_mRevertConfiguration.assert_not_called()
        mock_revertExaccHosts.assert_not_called()
        mock_createBackupDirCps.assert_not_called()
        self.assertEqual(
            revertNwReconfig.payload["updateNetwork"]["status"], "NOOP"
        )

    def test_mValidateRevertPayload_statusMissing(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        payload = copy.deepcopy(NOOP_PAYLOAD)
        payload["updateNetwork"]["nodes"][0]["backup"][0]["status"] = ""
        revertNwReconfig = ebCluRevertNetworkReconfig(cluctrl, testOptions(payload=NOOP_PAYLOAD))
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertNwReconfig.mValidateRevertPayload(payload)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertIn("Status missing for the operation", ctx.exception.mGetErrorMsg())

    def test_mValidateRevertPayload_serviceStatusMissing(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        payload = copy.deepcopy(NOOP_PAYLOAD)
        payload["updateNetwork"]["networkServices"][0]["status"] = ""
        revertNwReconfig = ebCluRevertNetworkReconfig(cluctrl, testOptions(payload=NOOP_PAYLOAD))
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertNwReconfig.mValidateRevertPayload(payload)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertIn("Status missing for the operation", ctx.exception.mGetErrorMsg())

    def test_mValidateRevertPayload_missingUUID(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        payload = copy.deepcopy(NOOP_PAYLOAD)
        del payload["uuid"]
        revertNwReconfig = ebCluRevertNetworkReconfig(cluctrl, testOptions(payload=NOOP_PAYLOAD))
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertNwReconfig.mValidateRevertPayload(payload)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertIn("UUID missing in payload", ctx.exception.mGetErrorMsg())

    @patch("exabox.ovm.clurevertnetworkreconfig.ebCluRevertNetworkReconfig.mBackupConfCps", return_value=None)
    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmdLocal", return_value=(1, ""))
    def test_mRevertExaccHosts_fail(self,
                                    mock_mExecuteCmdLocal,
                                    mock_mBackupConfCps):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        payload = copy.deepcopy(NOOP_PAYLOAD)
        del payload["uuid"]
        revertNwReconfig = ebCluRevertNetworkReconfig(cluctrl, testOptions(payload=NOOP_PAYLOAD))
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertNwReconfig.mRevertExaccHosts()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "EXACLOUD : Failed to revert /etc/hosts.exacc_domu on",
            ctx.exception.mGetErrorMsg()
        )


class ebTestNodeRevertor(ebTestClucontrol):

    def mGetCluCtrl(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        return cluctrl

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_init(self, mGetNetworkSetupInformation):
        cluctrl = self.mGetCluCtrl()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(revertor.result, CIDR_UPDATE_PAYLOAD)
        self.assertEqual(revertor.errorcode, "ERROR_RECONFIGURATION_REVERT_FAILED")
        mGetNetworkSetupInformation.assert_called_once()

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetRevertUUID(self, mGetNetworkSetupInformation):
        cluctrl = self.mGetCluCtrl()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(revertor.mGetRevertUUID(), "apply_uuid")

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_mGetRevertDir(self, _mock_mCheckDom0NetworkType):
        cluctrl = self.mGetCluCtrl()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(
            revertor._mGetRevertDir(), "/opt/exacloud/nw_reconfig/apply_uuid"
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_mSetResult(self, _mock_mCheckDom0NetworkType):
        cluctrl = self.mGetCluCtrl()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        revertor.mSetResult("ipconf_updates", "REVERTED", "success")
        self.assertEqual(revertor.result["ipconf_updates"]["status"], "REVERTED")
        self.assertEqual(revertor.result["ipconf_updates"]["msg"], "success")

    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mCreateBackupDir", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRunRevertConfiguration",return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRunPostOperations", return_value=None)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_mRevertConfiguration(
            self,
            _mock_mCheckDom0NetworkType,
            mock_mRunPostOperations,
            mock_mRunRevertConfiguration,
            mock_createBackupDir,
    ):
        cluctrl = self.mGetCluCtrl()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()

        # for a node without any updates
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy({}),
        )
        revertor.mRevertConfiguration()
        mock_mRunPostOperations.assert_not_called()
        mock_mRunRevertConfiguration.assert_not_called()
        mock_createBackupDir.assert_not_called()

        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        revertor.mRevertConfiguration()
        mock_mRunPostOperations.assert_called_once()
        mock_mRunRevertConfiguration.assert_called_once()
        mock_createBackupDir.assert_called_once()

    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mDeleteStaleBridge", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRestartDomain", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRunIpConf", return_value=None)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_mRunPostOperations(
            self,
            _mock_mCheckDom0NetworkType,
            mock_mRunIpConf,
            mock_mRestartDomain,
            mock_mDeleteStaleBridge,
    ):
        cluctrl = self.mGetCluCtrl()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        payload = copy.deepcopy(VLAN_UPDATE_PAYLOAD)
        payload["vlan_add_backup"]["status"] = "FAILED"
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(payload),
        )
        revertor.mRunPostOperations()
        mock_mRunIpConf.assert_not_called()
        mock_mRestartDomain.assert_called_once()
        mock_mDeleteStaleBridge.assert_called_once()

        mock_mRunIpConf.reset_mock()
        mock_mRestartDomain.reset_mock()
        mock_mDeleteStaleBridge.reset_mock()

        # Test for CIDR updates
        payload = copy.deepcopy(CIDR_UPDATE_PAYLOAD)
        payload["ipconf_updates"]["status"] = "FAILED"
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(payload),
        )
        revertor.mRunPostOperations()
        mock_mRunIpConf.assert_called_once()
        mock_mRestartDomain.assert_not_called()
        mock_mDeleteStaleBridge.assert_not_called()
        self.assertEqual(revertor.mGetResult()["ipconf_updates"]["status"], "REVERTED")
        self.assertEqual(
            revertor.mGetResult()["ipconf_updates"]["msg"],
            "IP Conf updates reverted successfully on scaqab10client01vm08.us.oracle.com",
        )

        mock_mRunIpConf.reset_mock()
        mock_mRestartDomain.reset_mock()
        mock_mDeleteStaleBridge.reset_mock()

        # Test for NOOP payload
        payload = copy.deepcopy(NOOP_WORKING_PAYLOAD)
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(payload),
        )
        revertor.mRunPostOperations()
        mock_mRunIpConf.assert_not_called()
        mock_mRestartDomain.assert_called_once()
        mock_mDeleteStaleBridge.assert_not_called()


    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRevertCellConf", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRunRevertBridges", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRevertGuestXmls", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mRevertPersistentNetRules", return_value=None)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_mRunRevertConfiguration(
            self,
            _mock_mCheckDom0NetworkType,
            mock_mRevertPersistentNetRules,
            mock_mRevertGuestXmls,
            mock_mRunRevertBridges,
            mock_mRevertCellConf,
    ):
        cluctrl = self.mGetCluCtrl()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()

        # Test for VLAN Operations
        payload = copy.deepcopy(VLAN_UPDATE_PAYLOAD)
        payload["vlan_add_backup"]["status"] = "SUCCESS"
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            payload
        )
        revertor.mRunRevertConfiguration()
        mock_mRevertCellConf.assert_not_called()
        mock_mRevertPersistentNetRules.assert_called_once()
        mock_mRevertGuestXmls.assert_called_once()
        mock_mRunRevertBridges.assert_called_once()
        self.assertEqual(payload["vlan_add_backup"]["status"], "SUCCESS")
        self.assertEqual(payload["vlan_delete_backup"]["status"], "REVERTED")
        self.assertEqual(
            payload["vlan_delete_backup"]["msg"],
            "VLAN delete operation reverted successfully on scaqab10adm01.us.oracle.com"
        )

        # Reset mocks
        mock_mRevertCellConf.reset_mock()
        mock_mRevertPersistentNetRules.reset_mock()
        mock_mRevertGuestXmls.reset_mock()
        mock_mRunRevertBridges.reset_mock()

        # Test for CIDR Operations only
        payload = copy.deepcopy(CIDR_UPDATE_PAYLOAD)
        payload["ipconf_updates"]["status"] = "FAILED"
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(payload),
        )
        revertor.mRunRevertConfiguration()
        mock_mRevertCellConf.assert_called_once()
        mock_mRevertPersistentNetRules.assert_not_called()
        mock_mRevertGuestXmls.assert_not_called()
        mock_mRunRevertBridges.assert_not_called()

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mExecuteCmd", return_value=(0, "", ""))
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_mRevertCellConf(
            self,
            _mock_mCheckDom0NetworkType,
            mock_mExecuteCmd,
            _mock_mConnect,
            _mock_mDisconnect,
    ):
        cluctrl = self.mGetCluCtrl()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        revertor.mRevertCellConf()
        self.assertEqual(mock_mExecuteCmd.call_count, 2)

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(1, "", ""), (0, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertor.mRevertCellConf()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "Failed to take backup",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(mock_mExecuteCmd.call_count, 1)

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(0, "", ""), (1, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertor.mRevertCellConf()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "Failed to revert",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(mock_mExecuteCmd.call_count, 2)

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mExecuteCmd", return_value=(0, "", ""))
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_mRevertPersistentNetRules(
            self,
            _mock_mCheckDom0NetworkType,
            mock_mExecuteCmd,
            _mock_mConnect,
            _mock_mDisconnect,
    ):
        cluctrl = self.mGetCluCtrl()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        revertor.mRevertPersistentNetRules("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 2)

        # Failure Case - 1
        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(1, "", ""), (0, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertor.mRevertPersistentNetRules("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "Failed to take backup",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(revertor.result["vlan_add_backup"]["status"], "FAILURE")
        self.assertEqual(revertor.result["vlan_delete_backup"]["status"], "FAILURE")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)

        # Failure Case - 2
        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(0, "", ""), (1, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertor.mRevertPersistentNetRules("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "Failed to revert",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(revertor.result["vlan_add_backup"]["status"], "FAILURE")
        self.assertEqual(revertor.result["vlan_delete_backup"]["status"], "FAILURE")
        self.assertEqual(mock_mExecuteCmd.call_count, 2)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mAddBondedBridge", return_value=None)
    def test_mRunRevertBridges(
            self,
            mock_mAddBondedBridge,
            _mock_mCheckDom0NetworkType,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        revertor = NodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        # vlan to vlan move
        revertor.mRunRevertBridges("backup", "129")
        mock_mAddBondedBridge.assert_called_once()

        # When cluster was no-vlan initially
        mock_mAddBondedBridge.reset_mock()
        revertor.mRunRevertBridges("backup", "1")
        mock_mAddBondedBridge.assert_not_called()

class ebTestKvmNodeRevertor(ebTestClucontrol):

    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mDeleteBondedBridge")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mExecuteCmd")
    @patch("exabox.ovm.clurevertnetworkreconfig.KvmNodeRevertor.mDetectSharedBridge")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mDeleteStaleBridge(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            _mock_mDetectSharedBridge,
            mock_mExecuteCmd,
            mGetNetworkSetupInformation,
            mock_deleteBondedBridge,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()

        revertor = KvmNodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        # Bridge does not exist
        _mock_mDetectSharedBridge.return_value = 1
        mock_mExecuteCmd.return_value = (1, "", "")
        revertor.mDeleteStaleBridge("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        mock_deleteBondedBridge.assert_not_called()

        # Bridge exists and shared
        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.return_value = (0, "", "")
        _mock_mDetectSharedBridge.return_value = 1
        revertor.mDeleteStaleBridge("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        mock_deleteBondedBridge.assert_not_called()

        # Bridge exists and not shared
        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.return_value = (0, "", "")
        _mock_mDetectSharedBridge.return_value = 0
        revertor.mDeleteStaleBridge("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        mock_deleteBondedBridge.assert_called_once()

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mExecuteCmd", return_value=(0, "", ""))
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_mRevertGuestXmls(
            self,
            _mock_mCheckDom0NetworkType,
            mock_mExecuteCmd,
            _mock_mConnect,
            _mock_mDisconnect,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        revertor = KvmNodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        revertor.mRevertGuestXmls("backup", "129")
        self.assertEqual(mock_mExecuteCmd.call_count, 5)

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(1, "", ""), (0, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertor.mRevertGuestXmls("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "Failed to take backup",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(revertor.result["vlan_add_backup"]["status"], "FAILURE")
        self.assertEqual(revertor.result["vlan_delete_backup"]["status"], "FAILURE")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(0, "", ""), (1, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertor.mRevertGuestXmls("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "Failed to revert",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(revertor.result["vlan_add_backup"]["status"], "FAILURE")
        self.assertEqual(revertor.result["vlan_delete_backup"]["status"], "FAILURE")
        self.assertEqual(mock_mExecuteCmd.call_count, 2)

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [
            (0, "", ""),
            (0, "", ""),
            (1, "", ""),
            (1, "", ""),
        ]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertor.mRevertGuestXmls("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "Failed to revert",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(revertor.result["vlan_add_backup"]["status"], "FAILURE")
        self.assertEqual(revertor.result["vlan_delete_backup"]["status"], "FAILURE")
        self.assertEqual(mock_mExecuteCmd.call_count, 4)

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [
            (0, "", ""),
            (0, "", ""),
            (1, "", ""),
            (0, "", ""),
            (1, "", ""),
        ]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertor.mRevertGuestXmls("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "Failed to define",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(revertor.result["vlan_add_backup"]["status"], "FAILURE")
        self.assertEqual(revertor.result["vlan_delete_backup"]["status"], "FAILURE")
        self.assertEqual(mock_mExecuteCmd.call_count, 5)


class ebTestXenNodeRevertor(ebTestClucontrol):

    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mDeleteBondedBridge")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mExecuteCmd")
    @patch("exabox.ovm.clurevertnetworkreconfig.XenNodeRevertor.mDetectSharedBridge", return_value=1)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mDeleteStaleBridge(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            _mock_mDetectSharedBridge,
            mock_mExecuteCmd,
            mGetNetworkSetupInformation,
            mock_deleteBondedBridge
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (1, "", "")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        revertor = XenNodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )

        # Bridge does not exist
        _mock_mDetectSharedBridge.return_value = 1
        mock_mExecuteCmd.return_value = (1, "", "")
        revertor.mDeleteStaleBridge("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        mock_deleteBondedBridge.assert_not_called()

        # Bridge exists and shared
        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.return_value = (0, "", "")
        _mock_mDetectSharedBridge.return_value = 1
        revertor.mDeleteStaleBridge("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        mock_deleteBondedBridge.assert_not_called()

        # Bridge exists and not shared
        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.return_value = (0, "", "")
        _mock_mDetectSharedBridge.return_value = 0
        revertor.mDeleteStaleBridge("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)
        mock_deleteBondedBridge.assert_called_once()

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clurevertnetworkreconfig.NodeRevertor.mExecuteCmd", return_value=(0, "", ""))
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=DOM0_NETWORK_INFO)
    def test_mRevertGuestXmls(
            self,
            _mock_mCheckDom0NetworkType,
            mock_mExecuteCmd,
            _mock_mConnect,
            _mock_mDisconnect,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        revertor = XenNodeRevertor(
            cluctrl,
            "apply_uuid",
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        revertor.mRevertGuestXmls("backup", "129")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(1, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            revertor.mRevertGuestXmls("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8007)
        self.assertIn(
            "Failed to revert",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(revertor.result["vlan_add_backup"]["status"], "FAILURE")
        self.assertEqual(revertor.result["vlan_delete_backup"]["status"], "FAILURE")
        self.assertEqual(mock_mExecuteCmd.call_count, 1)


if __name__ == "__main__":
    unittest.main()
