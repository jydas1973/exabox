#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clunetworkreconfig.py /main/8 2025/05/21 05:57:34 rkhemcha Exp $
#
# tests_clunetworkreconfig.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clunetworkreconfig.py - Unittests for network reconfiguration
#
#    DESCRIPTION
#      Unitests for network reconfiguration feature of ExaCC
#
#    MODIFIED   (MM/DD/YY)
#    rkhemcha    09/10/24 - 35594100 - Unit tests for DNS/NTP reconfig
#    pvachhan    06/06/22 - BUG 34230694 - RECONFIGURING A BACKUP N/W OF A
#                           CLUSTER WITH SHARED BRIDGES FAILS TO DELETE STALE
#                           COMMON BRIDGE
#    pvachhan    05/26/22 - Creation
#
import copy
import json
import unittest
import traceback
from unittest.mock import patch
import warnings

from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.clunetworkreconfig import (
    ebCluNetworkReconfig,
    NodeNetworkComposer,
    KvmNodeNetworkComposer,
    XenNodeNetworkComposer,
)
from exabox.network.dns.DNSConfig import ebDNSConfig
from exabox.ovm.clunetworkreconfigcommons import ebCluNetworkReconfigHandler, NodeUtils
from exabox.exatest.ovm.tests_clunetworkreconfigcommons import (
    DOM0_NETWORK_INFO, PAYLOAD, VLAN_UPDATE_PAYLOAD, CIDR_UPDATE_PAYLOAD, ALL_OPS_PAYLOAD
)
from exabox.ovm.hypervisorutils import HVIT_XEN, HVIT_KVM

CELL_CONF = """<?xml version='1.0' standalone='yes'?>
<Cell>
  <Hostname>scaqan03dv0312.us.oracle.com</Hostname>
  <Active_bond_ib>yes</Active_bond_ib>
  <Default_gateway_device>bondeth0</Default_gateway_device>
  <Interfaces>
    <Bond_type>single</Bond_type>
    <Gateway>10.32.110.1</Gateway>
    <Hostname>scaqan03dv0312.us.oracle.com</Hostname>
    <IP_address>10.32.110.70</IP_address>
    <IP_enabled>yes</IP_enabled>
    <IP_ssh_listen>enabled</IP_ssh_listen>
    <Inet_protocol>IPv4</Inet_protocol>
    <Name>bondeth0</Name>
    <Net_type>SCAN</Net_type>
    <Netmask>255.255.254.0</Netmask>
    <State>1</State>
    <Status>UP</Status>
    <VSwitchNetworkParams>Vnet</VSwitchNetworkParams>
    <Vlan_id>0</Vlan_id>
  </Interfaces>
  <Interfaces>
    <Bond_type>single</Bond_type>
    <Gateway>10.32.110.1</Gateway>
    <Hostname>scaqan03dv0312-bk.us.oracle.com</Hostname>
    <IP_address>10.32.110.71</IP_address>
    <IP_enabled>yes</IP_enabled>
    <IP_ssh_listen>disabled</IP_ssh_listen>
    <Inet_protocol>IPv4</Inet_protocol>
    <Name>bondeth1</Name>
    <Net_type>Other</Net_type>
    <Netmask>255.255.255.128</Netmask>
    <State>1</State>
    <Status>UP</Status>
    <VSwitchNetworkParams>Vnet</VSwitchNetworkParams>
    <Vlan_id>0</Vlan_id>
  </Interfaces>
  <Interfaces>
    <Bond_type>single</Bond_type>
    <Gateway>169.254.200.21</Gateway>
    <Hostname>scaqan03dv0312m.localdomain</Hostname>
    <IP_address>169.254.200.22</IP_address>
    <IP_enabled>yes</IP_enabled>
    <IP_ssh_listen>enabled</IP_ssh_listen>
    <Inet_protocol>IPv4</Inet_protocol>
    <Name>eth0</Name>
    <Net_type>Other</Net_type>
    <Netmask>255.255.255.252</Netmask>
    <State>1</State>
    <Status>UP</Status>
    <Vlan_id>0</Vlan_id>
  </Interfaces>
  <Interfaces>
    <Name>stre0</Name>
    <Net_type>Private</Net_type>
    <State>1</State>
    <Status>UP</Status>
  </Interfaces>
  <Interfaces>
    <Name>stre1</Name>
    <Net_type>Private</Net_type>
    <State>1</State>
    <Status>UP</Status>
  </Interfaces>
  <Internal>
    <Interface_ethernet_prefix>eth</Interface_ethernet_prefix>
    <Interface_infiniband_prefix>stre</Interface_infiniband_prefix>
  </Internal>
  <Nameservers>206.223.27.2</Nameservers>
  <Nameservers>206.223.27.1</Nameservers>
  <Node_type>db</Node_type>
  <Ntp_drift>/var/lib/ntp/drift</Ntp_drift>
  <Ntp_servers>10.132.0.129</Ntp_servers>
  <Ntp_servers>10.132.0.121</Ntp_servers>
  <Qinq_vlan_id>0</Qinq_vlan_id>
  <System_active>non-ovs</System_active>
  <Timezone>UTC</Timezone>
  <Version>20.1.0.0.0</Version>
</Cell>"""

BRIDGE_XML = """<interface type="bridge">
  <mac address="52:54:00:84:b1:ae" />
  <source bridge="vmbondeth1.129" />
  <model type="virtio" />
  <driver queues="8" />
  <address bus="0x00" domain="0x0000" function="0x0" slot="0x04" type="pci" />
</interface>"""

NETRULES = """SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", KERNELS=="0000:00:03.0", ATTR{type}=="1", NAME="bondeth0"
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", KERNELS=="0000:00:04.0", ATTR{type}=="1", NAME="bondeth1"
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", KERNELS=="0000:00:05.0", ATTR{type}=="1", NAME="eth0"
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", KERNELS=="0000:ff:00.0", ATTR{type}=="1", NAME="clre0"
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", KERNELS=="0000:ff:00.1", ATTR{type}=="1", NAME="clre1"
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", KERNELS=="0000:ff:00.2", ATTR{type}=="1", NAME="stre0"
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", KERNELS=="0000:ff:00.3", ATTR{type}=="1", NAME="stre1"
"""

VM_CFG = """acpi = 1
apic = 1
pae = 1
builder = 'hvm'
kernel = '/usr/lib/xen/boot/hvmloader'
device_model = '/usr/lib/xen/bin/qemu-dm'
cpuid = ['1:edx=xxxxxxxxxxxxxxxxxxx0xxxxxxxxxxxx']
disk = ['file:/OVS/Repositories/7d5c116dc1a04d8786303338bd8287ed/VirtualDisks/7bffd44b2b864fc78061b31c97cb9956.img,xvda,w', 'file:/OVS/Repositories/7d5c116dc1a04d8786303338bd8287ed/VirtualDisks/a12f35939b5c4ad6936b5fb4837ca610.img,xvdb,w', 'file:/OVS/Repositories/7d5c116dc1a04d8786303338bd8287ed/VirtualDisks/0eca4216c03540bf92ae02a84c3ecc03.img,xvdh,w', u'file:///EXAVMIMAGES/GuestImages/scaqae08dv0302.usdv1.oraclecloud.com/u02_extra.img,xvdi,w']
memory = '61440'
maxmem = '61440'
OVM_simple_name = 'iad100527ex-342'
name = 'scaqae08dv0302.usdv1.oraclecloud.com'
OVM_os_type = 'Oracle Linux 7'
vcpus = 12
maxvcpus = 96
uuid = '7d5c116dc1a04d8786303338bd8287ed'
on_crash = 'restart'
on_reboot = 'restart'
serial = 'pty'
keymap = 'en-us'
vif = ['type=netfront,mac=00:16:3e:5f:24:db,bridge=vmbondeth0.155','type=netfront,mac=00:16:3e:a7:3b:39,bridge=vmbondeth1.129','type=netfront,mac=00:16:3e:36:de:55,bridge=vmeth104']
timer_mode = 2
ib_pfs = ['3b:00.0']
ib_pkeys = [{'pf':'3b:00.0','port':'1','pkey':['0x2a34','0xa342',]},{'pf':'3b:00.0','port':'2','pkey':['0x2a34','0xa342',]},]
cpus = '4-15'
"""

class testOptions(object):
    def __init__(self) -> None:
        self.jsonconf = copy.deepcopy(PAYLOAD)
        self.jsonmode = False
        self.configpath = None


class ebTestCluNetworkReconfig(ebTestClucontrol):
    @classmethod
    def setUpClass(cls):
        super(ebTestCluNetworkReconfig, cls).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    def test_init(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        nwReconfig = ebCluNetworkReconfig(cluctrl, testOptions())
        self.assertEqual(nwReconfig.payload["updateNetwork"]["status"], "NOOP")
        for node in nwReconfig.payload["updateNetwork"]["nodes"]:
            for _, operations in node.items():
                if _ in ["updateProperties"]:
                    continue
                for operation in operations:
                    self.assertEqual(operation["status"], "NOOP")
                    self.assertEqual(operation["msg"], "")

    def test_mGetUUID(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        nwReconfig = ebCluNetworkReconfig(cluctrl, testOptions())
        self.assertEqual(nwReconfig.mGetEbox().mGetUUID(), "exatest")
        self.assertEqual(nwReconfig.payload["uuid"], "exatest")

    @patch("exabox.ovm.clunetworkreconfig.getTargetHVIType", return_value=HVIT_KVM)
    @patch("exabox.network.dns.DNSConfig.ebDNSConfig.mRestartDnsmasq", return_value=None)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mReconfigure", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mUpdateExaccHostsDomU", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.ebCluNetworkReconfig.mBackupConfCps", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.ebCluNetworkReconfig.mCreateBackupDirCps", return_value=None)
    def test_applyKVM(
            self,
            mock_mCreateBackupDirCps,
            mock_mBackupConfCps,
            mock_updateExaccDomuHosts,
            mock_mReconfigure,
            mock_mGetNetworkSetupInformation,
            mock_mRestartDnsmasq,
            mock_getTargetHVIType
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        nwReconfig = ebCluNetworkReconfig(cluctrl, testOptions())
        nwReconfig.apply()
        expectedResult = {
            "network": {},
            "updateNetwork": {
                "networkServices": [
                    {
                        "op": "dns_update",
                        "payload": {
                            "compute_node_alias": "node-1"
                        },
                        "status": "NOOP",
                        "msg": ""
                    },
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
                            "compute_node_alias": "node-1"
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
                    },
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
                "status": "SUCCESS",
                "msg": "",
                "errorcode": "0x00000000"
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
            "uuid": "exatest"
        }
        self.assertEqual(nwReconfig.payload, expectedResult)

    @patch("exabox.ovm.clunetworkreconfig.getTargetHVIType", return_value=HVIT_XEN)
    @patch("exabox.network.dns.DNSConfig.ebDNSConfig.mRestartDnsmasq", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mReconfigure", return_value=None)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mUpdateExaccHostsDomU", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.ebCluNetworkReconfig.mBackupConfCps", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.ebCluNetworkReconfig.mCreateBackupDirCps", return_value=None)
    def test_applyXEN(
            self,
            mock_mCreateBackupDirCps,
            mock_mBackupConfCps,
            mock_updateExaccDomuHosts,
            mock_mGetNetworkSetupInformation,
            mock_mReconfigure,
            mock_mRestartDnsmasq,
            mock_getTargetHVIType
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        nwReconfig = ebCluNetworkReconfig(cluctrl, testOptions())
        nwReconfig.apply()
        expectedResult = {
            "network": {},
            "updateNetwork": {
                "networkServices": [
                    {
                        "op": "dns_update",
                        "payload": {
                            "compute_node_alias": "node-1"
                        },
                        "status": "NOOP",
                        "msg": ""
                    },
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
                            "compute_node_alias": "node-1"
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
                    },
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
                "status": "SUCCESS",
                "msg": "",
                "errorcode": "0x00000000"
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
            "uuid": "exatest"
        }
        self.assertEqual(nwReconfig.payload, expectedResult)

    @patch("exabox.ovm.clunetworkreconfig.getTargetHVIType")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mReconfigure", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.ebCluNetworkReconfig.mBackupConfCps", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.ebCluNetworkReconfig.mCreateBackupDirCps", return_value=None)
    def test_applyUnknownHV(
            self,
            mock_mCreateBackupDirCps,
            mock_mBackupConfCps,
            mock_mReconfigure,
            mock_mGetNetworkSetupInformation,
            mock_getTargetHVIType,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_getTargetHVIType.return_value = 0
        nwReconfig = ebCluNetworkReconfig(cluctrl, testOptions())
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nwReconfig.apply()
        self.assertEqual(nwReconfig.payload["updateNetwork"]["status"], "NOOP")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8005)
        self.assertEqual(
            "EXACLOUD : Unsupported hypervisor 0 identified. Exiting.",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clunetworkreconfig.getTargetHVIType")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.ebCluNetworkReconfig.mBackupConfCps", return_value=0)
    @patch("exabox.ovm.clunetworkreconfig.ebCluNetworkReconfig.mCreateBackupDirCps", return_value=0)
    def test_applyError(
            self,
            mock_mCreateBackupDirCps,
            mock_mBackupConfCps,
            mock_mGetNetworkSetupInformation,
            mock_getTargetHVIType,
            mock_mExecuteCmd,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mConnect,
            _mock_mDisconnect
    ):
        def mExecuteCmdSideEffect(_, cmd):
            if "ipconf" in cmd:
                return 1, "msg_out", "msg_err"
            else:
                return 0, "msg_out", "msg_err"

        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = mExecuteCmdSideEffect
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = CELL_CONF
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_getTargetHVIType.return_value = HVIT_KVM
        nwReconfig = ebCluNetworkReconfig(cluctrl, testOptions())
        nwReconfig.apply()
        self.assertEqual(nwReconfig.payload["updateNetwork"]["status"], "FAILURE")
        self.assertEqual(
            "EXACLOUD : Failed to run ipconf on scaqab10client01vm08.us.oracle.com",
            nwReconfig.payload["updateNetwork"]["msg"],
        )


class ebTestNodeNetworkComposer(ebTestClucontrol):

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer._mRunApplyIpConfUpdate", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer._mRunApplyVlanAdd", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer._mRunApplyVlanDelete", return_value=None)
    def test_mRunApplyConfiguration(
            self,
            mock_mRunApplyVlanDelete,
            mock_mRunApplyVlanAdd,
            mock_mRunApplyIpConfUpdate,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunApplyConfiguration()
        mock_mRunApplyIpConfUpdate.assert_not_called()
        mock_mRunApplyVlanAdd.assert_called_once()
        mock_mRunApplyVlanDelete.assert_called_once()

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mCreateBackupDir", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer._mBackupConfDomu", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mBackupGuestXmls", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mBackupPersistentNetRules", return_value=None)
    def test_mRunPreOperationsForCIDR(
            self,
            mock_mBackupPersistentNetRules,
            mock_mBackupGuestXmls,
            mock_mBackupConfDomu,
            mock_mCreateBackupDir,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunPreOperations()
        mock_mBackupPersistentNetRules.assert_not_called()
        mock_mBackupGuestXmls.assert_not_called()
        mock_mCreateBackupDir.assert_called_once()
        assert mock_mBackupConfDomu.call_count == 3

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mCreateBackupDir", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer._mBackupConfDomu", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mBackupGuestXmls", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mBackupPersistentNetRules", return_value=None)
    def test_mRunPreOperationsForNetworkServicesUpdate(
            self,
            mock_mBackupPersistentNetRules,
            mock_mBackupGuestXmls,
            mock_mBackupConfDomu,
            mock_mCreateBackupDir,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(
                {
                    "ipconf_updates": {
                        "entities": ["dns", "ntp"],
                        "status": "NOOP",
                        "msg": ""
                    }
                })
        )
        nodeComposer._mRunPreOperations()
        mock_mBackupPersistentNetRules.assert_not_called()
        mock_mBackupGuestXmls.assert_not_called()
        mock_mCreateBackupDir.assert_called_once()
        self.assertEqual(mock_mBackupConfDomu.call_count, 3)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mCreateBackupDir", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer._mBackupConfDomu", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mBackupGuestXmls", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mBackupPersistentNetRules", return_value=None)
    def test_mRunPreOperationsForVLAN(
            self,
            mock_mBackupPersistentNetRules,
            mock_mBackupGuestXmls,
            mock_mBackupConfDomu,
            mock_mCreateBackupDir,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunPreOperations()
        mock_mBackupPersistentNetRules.assert_called_once()
        mock_mBackupGuestXmls.assert_called_once()
        mock_mBackupConfDomu.assert_not_called()
        mock_mCreateBackupDir.assert_called_once()

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mRunIpConf", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mDeleteStaleBridge", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mRestartDomain", return_value=None)
    def test_mRunPostOperationsForCIDR(
            self,
            mock_mRestartDomain,
            mock_mDeleteStaleBridge,
            mock_mRunIpConf,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunPostOperations()
        mock_mRestartDomain.assert_not_called()
        mock_mDeleteStaleBridge.assert_not_called()
        mock_mRunIpConf.assert_called_once()

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mRunIpConf", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mDeleteStaleBridge", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mRestartDomain", return_value=None)
    def test_mRunPostOperationsForVLAN(
            self,
            mock_mRestartDomain,
            mock_mDeleteStaleBridge,
            mock_mRunIpConf,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunPostOperations()
        mock_mRestartDomain.assert_called_once()
        mock_mDeleteStaleBridge.assert_called_once()
        mock_mRunIpConf.assert_not_called()

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mRunApplyIpConfUpdate(
            self,
            mock_mGetNetworkSetupInformation,
            mock_mExecuteCmd,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mConnect,
            _mock_mDisconnect,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        mock_mReadFile.return_value = CELL_CONF
        mock_mWriteFile.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunApplyIpConfUpdate(["backup", "dns", "ntp"])
        mock_mReadFile.assert_called_once()
        mock_mWriteFile.assert_called_once()

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mRunApplyIpConfUpdateFails(
            self,
            mock_mGetNetworkSetupInformation,
            mock_mExecuteCmd,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mConnect,
            _mock_mDisconnect,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        mock_mReadFile.return_value = CELL_CONF
        mock_mWriteFile.side_effect = ExacloudRuntimeError()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyIpConfUpdate(["backup", "dns", "ntp"])
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(nodeComposer.mGetResult()["ipconf_updates"]["status"], "FAILURE")
        self.assertIn(
            "Couldn't update /opt/oracle.cellos/cell.conf on scaqab10client01vm08.us.oracle.com.",
            nodeComposer.mGetResult()["ipconf_updates"]["msg"],
        )

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_cidrUpdate(
            self,
            mock_mGetNetworkSetupInformation,
            mock_mExecuteCmd,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mConnect,
            _mock_mDisconnect,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        mock_mReadFile.return_value = CELL_CONF
        mock_mWriteFile.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        nodeComposer.mReconfigure()
        self.assertEqual(nodeComposer.mGetResult()["ipconf_updates"]["status"], "SUCCESS")
        self.assertEqual(
            "IP Conf updates operation successful on scaqab10client01vm08.us.oracle.com",
            nodeComposer.mGetResult()["ipconf_updates"]["msg"],
        )

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_cidrUpdateFailure(
            self,
            mock_mGetNetworkSetupInformation,
            mock_mExecuteCmd,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mConnect,
            _mock_mDisconnect,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (1, "msg_out", "msg_err")
        mock_mReadFile.return_value = CELL_CONF
        mock_mWriteFile.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mReconfigure()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to create backup dir /opt/exacloud/nw_reconfig/exatest on scaqab10client01vm08.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mBackupPersistentNetRules(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        nodeComposer.mBackupPersistentNetRules()
        _, cmd = mock_mExecuteCmd.call_args_list[0][0]
        mock_mExecuteCmd.assert_called_once()
        self.assertEqual(
            cmd,
            "/bin/cp /etc/udev/rules.d/70-persistent-net.rules /opt/exacloud/nw_reconfig/exatest",
        )

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.return_value = (1, "msg_out", "msg_err")
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mBackupPersistentNetRules()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to take backup of /etc/udev/rules.d/70-persistent-net.rules on scaqab10client01vm08.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_isBridgeUp_true(self, mock_mGetNetworkSetupInformation, mock_mExecuteCmd,
                             _mock_mDisconnect, _mock_mConnect):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, ["up"], "msg_err")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(nodeComposer.isBridgeUp("bridgeName.123"), True)

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_isBridgeUp_false(self, mock_mGetNetworkSetupInformation, mock_mExecuteCmd,
                              _mock_mDisconnect, _mock_mConnect):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, ["down"], "msg_err")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(nodeComposer.isBridgeUp("bridgeName.123"), False)

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mBackupConfDomu_fail(self,
                                  mock_mGetNetworkSetupInformation,
                                  mock_mExecuteCmd,
                                  _mock_mDisconnect,
                                  _mock_mConnect
                                  ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (1, "", "msg_err")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mBackupConfDomu("/opt/oracle.cellos/cell.conf")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to take backup of /opt/oracle.cellos/cell.conf on scaqab10client01vm08.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mEntriesToAddDelete(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(ALL_OPS_PAYLOAD),
        )
        add_list, delete_set = nodeComposer.mEntriesToAddDelete()
        self.assertEqual(add_list, [('scaqab10adm01vm08-bk.us.oracle.com', '76.0.0.4')])
        self.assertEqual(delete_set, {'10.32.94.88', 'scaqan04dv0301-bk'})


    @patch("exabox.network.dns.DNSConfig.ebDNSConfig.mDeleteDNSEntry", return_value=(0, "", ""))
    @patch("exabox.network.dns.DNSConfig.ebDNSConfig.mAddServiceEntry", return_value=(0, "", ""))
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mUpdateExaccHostsDomU(self,
                                   mock_mGetNetworkSetupInformation,
                                   mock_mAddServiceEntry,
                                   mock_mDeleteDNSEntry):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(ALL_OPS_PAYLOAD),
        )
        nodeComposer.mUpdateExaccHostsDomU()
        self.assertEqual(mock_mAddServiceEntry.call_count, 1)
        self.assertEqual(mock_mDeleteDNSEntry.call_count, 2)

    @patch("exabox.network.dns.DNSConfig.ebDNSConfig.mDeleteDNSEntry", return_value=(1, "", ""))
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mUpdateExaccHostsDomU_deleteFail(self,
                                              mock_mGetNetworkSetupInformation,
                                              mock_mDeleteDNSEntry):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(ALL_OPS_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mUpdateExaccHostsDomU()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertIn(
            "EXACLOUD : Failed to delete entry",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.network.dns.DNSConfig.ebDNSConfig.mDeleteDNSEntry", return_value=(0, "", ""))
    @patch("exabox.network.dns.DNSConfig.ebDNSConfig.mAddServiceEntry", return_value=(1, "", ""))
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mUpdateExaccHostsDomU_addFail(self,
                                           mock_mGetNetworkSetupInformation,
                                           mock_mAddServiceEntry,
                                           mock_mDeleteDNSEntry):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(ALL_OPS_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mUpdateExaccHostsDomU()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertIn(
            "EXACLOUD : Failed to add entry",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(mock_mDeleteDNSEntry.call_count, 2)
        self.assertEqual(mock_mAddServiceEntry.call_count, 1)


class ebTestKvmNodeNetworkComposer(ebTestClucontrol):

    @patch("exabox.ovm.clunetworkreconfig.KvmNodeNetworkComposer.mUpdatePersistentRules")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=True)
    def test_mRunApplyVlanAddWhenBridgeExists(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = BRIDGE_XML
        mock_mUpdatePersistentRules.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 2)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/usr/sbin/brctl show | grep vmbondeth1.129",
        )
        _, cmd = calls[1][0]
        self.assertEqual(
            "/opt/exadata_ovm/vm_maker --allocate-bridge vmbondeth1 --vlan 129 --domain scaqab10client01vm08.us.oracle.com",
            cmd,
        )

    @patch("exabox.ovm.clunetworkreconfig.KvmNodeNetworkComposer.mUpdatePersistentRules")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mRunApplyVlanAddWhenCannotAddBridge(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.side_effect = [
            (1, "msg_out", "msg_err"),
            (1, "msg_out", "msg_err"),
        ]
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = BRIDGE_XML
        mock_mUpdatePersistentRules.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't add bonded bridge vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clunetworkreconfig.KvmNodeNetworkComposer.mUpdatePersistentRules")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=True)
    def test_mRunApplyVlanAddWhenCannotAllocateBridge(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.side_effect = [
            (0, "msg_out", "msg_err"),
            (1, "msg_out", "msg_err"),
        ]
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = BRIDGE_XML
        mock_mUpdatePersistentRules.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't allocate bridge vmbondeth1.129 to domain scaqab10client01vm08.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clunetworkreconfig.KvmNodeNetworkComposer.mUpdatePersistentRules")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=False)
    def test_mRunApplyVlanAddWhenBringUpBridgeFails(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.side_effect = [
            (0, "msg_out", "msg_err"),
            (1, "msg_out", "msg_err"),
        ]
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = BRIDGE_XML
        mock_mUpdatePersistentRules.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to bring up vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch(
        "exabox.ovm.clunetworkreconfig.KvmNodeNetworkComposer.mUpdatePersistentRules"
    )
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=True)
    def test_mRunApplyVlan(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        def mExecuteCmdSideEffect(_, cmd):
            if "brctl" in cmd:
                return 1, "msg_out", "msg_err"
            else:
                return 0, "msg_out", "msg_err"

        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.side_effect = mExecuteCmdSideEffect
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = BRIDGE_XML
        mock_mUpdatePersistentRules.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 3)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/usr/sbin/brctl show | grep vmbondeth1.129",
        )
        _, cmd = calls[1][0]
        self.assertEqual(
            "/opt/exadata_ovm/vm_maker --add-bonded-bridge vmbondeth1 --first-slave eth6 --second-slave eth7 --vlan 129",
            cmd,
        )
        _, cmd = calls[2][0]
        self.assertEqual(
            "/opt/exadata_ovm/vm_maker --allocate-bridge vmbondeth1 --vlan 129 --domain scaqab10client01vm08.us.oracle.com",
            cmd,
        )

    @patch("exabox.ovm.clunetworkreconfig.KvmNodeNetworkComposer.mUpdatePersistentRules")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=True)
    def test_mRunApplyVlanFails(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "", "")
        mock_mUpdatePersistentRules.side_effect = Exception()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't update rules in /etc/udev/rules.d/70-persistent-net.rules on scaqab10client01vm08.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clunetworkreconfig.KvmNodeNetworkComposer.mUpdatePersistentRules")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=False)
    def test_mRunApplyVlanFails_bridgeDown(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "", "")
        mock_mUpdatePersistentRules.side_effect = Exception()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to bring up vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mRunApplyVlanDelete(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = BRIDGE_XML
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunApplyVlanDelete("backup", "129")
        self.assertEqual(mock_mExecuteCmd.call_count, 2)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            "/bin/virt-xml scaqab10client01vm08.us.oracle.com --network source=vmbondeth1.129 --remove-device",
            cmd,
        )
        _, cmd = calls[1][0]
        self.assertEqual(
            "/bin/rm -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/vmbondeth1.129.xml",
            cmd,
        )

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.return_value = (1, "", "")
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanDelete("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to update Guest XML for scaqab10client01vm08.us.oracle.com on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(0, "", ""), (1, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanDelete("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to remove /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/vmbondeth1.129.xml on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mBackupGuestXmls(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mExecuteCmd,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer.mBackupGuestXmls("backup", "129")
        self.assertEqual(mock_mExecuteCmd.call_count, 2)

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.return_value = (1, "msg_out", "msg_err")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mBackupGuestXmls("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to take backup of /etc/libvirt/qemu on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )
        mock_mExecuteCmd.assert_called_once()

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [
            (0, "msg_out", "msg_err"),
            (1, "msg_out", "msg_err"),
        ]
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mBackupGuestXmls("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to take backup of /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/vmbondeth1.129.xml on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_getUpdatedBridgeAddress(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = BRIDGE_XML
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        address = nodeComposer.getUpdatedBridgeAddress("backup")
        self.assertEqual(address, "0000:00:04.0")

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mUpdatePersistentRules(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = NETRULES.encode("utf-8")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mUpdatePersistentRules("0000:0f:04.0", "backup")
        mock_mReadFile.assert_called_once()
        mock_mWriteFile.assert_called_once()
        calls = mock_mWriteFile.call_args_list
        _, rules = calls[0][0]
        self.assertIn(
            'SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", KERNELS=="0000:0f:04.0", ATTR{type}=="1", NAME="bondeth1',
            rules.decode(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clunetworkreconfig.KvmNodeNetworkComposer.mDetectSharedBridge")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.sleep", return_value=None)
    def test_mDeleteStaleBridge(
            self,
            mock_sleep,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mDetectSharedBridge,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_sleep.return_value = None
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "", "")
        mock_mDetectSharedBridge.return_value = 0
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer.mDeleteStaleBridge("backup", "129")
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            "/opt/exadata_ovm/vm_maker --remove-bridge vmbondeth1.129 --force",
            cmd,
        )
        self.assertEqual(mock_mExecuteCmd.call_count, 1)

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.return_value = (1, "err_out", "err_err")
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mDeleteStaleBridge("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't delete bonded bridge vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(mock_mExecuteCmd.call_count, 1)

        mock_mExecuteCmd.reset_mock()
        mock_mDetectSharedBridge.reset_mock()
        mock_mDetectSharedBridge.return_value = 1
        nodeComposer.mDeleteStaleBridge("backup", "129")
        self.assertEqual(mock_mExecuteCmd.call_count, 0)

        mock_mExecuteCmd.reset_mock()
        mock_mDetectSharedBridge.reset_mock()
        payload = copy.deepcopy(VLAN_UPDATE_PAYLOAD)
        payload["vlan_add_backup"]["payload"]["vlantag"] = "1"
        nodeComposer = KvmNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            payload,
        )
        self.assertEqual(mock_mExecuteCmd.call_count, 0)
        self.assertEqual(mock_mDetectSharedBridge.call_count, 0)


class ebTestXenNodeNetworkComposer(ebTestClucontrol):

    @patch("exabox.ovm.clunetworkreconfig.XenNodeNetworkComposer.mUpdatePersistentRules")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=True)
    def test_mRunApplyVlanAddWhenBridgeExists(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = VM_CFG.encode()
        mock_mUpdatePersistentRules.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 2)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/usr/sbin/brctl show | grep vmbondeth1.129",
        )
        _, cmd = calls[1][0]
        self.assertEqual(
            "/opt/exadata_ovm/exadata.img.domu_maker allocate-bridge-domu vmbondeth1.129 scaqab10client01vm08.us.oracle.com",
            cmd,
        )

    @patch("exabox.ovm.clunetworkreconfig.XenNodeNetworkComposer.mUpdatePersistentRules")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=False)
    def test_mRunApplyVlanAddWhenBringUpBridgeFails(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = VM_CFG.encode()
        mock_mUpdatePersistentRules.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to bring up vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch(
        "exabox.ovm.clunetworkreconfig.XenNodeNetworkComposer.mUpdatePersistentRules"
    )
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=True)
    def test_mRunApplyVlan(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules,
    ):
        def mExecuteCmdSideEffect(_, cmd):
            if "brctl" in cmd:
                return 1, "msg_out", "msg_err"
            else:
                return 0, "msg_out", "msg_err"

        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.side_effect = mExecuteCmdSideEffect
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = VM_CFG.encode()
        mock_mUpdatePersistentRules.return_value = None
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(mock_mExecuteCmd.call_count, 3)
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            cmd,
            "/usr/sbin/brctl show | grep vmbondeth1.129",
        )
        _, cmd = calls[1][0]
        self.assertEqual(
            "/opt/exadata_ovm/exadata.img.domu_maker add-bonded-bridge-dom0 vmbondeth1 eth6 eth7 129",
            cmd,
        )
        _, cmd = calls[2][0]
        self.assertEqual(
            "/opt/exadata_ovm/exadata.img.domu_maker allocate-bridge-domu vmbondeth1.129 scaqab10client01vm08.us.oracle.com",
            cmd,
        )

    @patch("exabox.ovm.clunetworkreconfig.KvmNodeNetworkComposer.mUpdatePersistentRules")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=False)
    def test_mRunApplyVlanFails_bridgeDown(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
            mock_mUpdatePersistentRules
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "", "")
        mock_mUpdatePersistentRules.side_effect = Exception()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to bring up vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.isBridgeUp", return_value=True)
    def test_mRunApplyVlanFails(
            self,
            _mock_isBridgeUp,
            _mock_mDisconnect,
            _mock_mConnect,
            _mock_mGetNetVlanId,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "", "")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't update rules in /etc/udev/rules.d/70-persistent-net.rules on scaqab10client01vm08.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(0, "", ""), (1, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't allocate bridge vmbondeth1.129 to domain scaqab10client01vm08.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(1, "", ""), (1, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanAdd("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't add bonded bridge vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mRunApplyVlanDelete(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = VM_CFG.encode()
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mRunApplyVlanDelete("backup", "129")
        mock_mReadFile.assert_called_once()
        mock_mWriteFile.assert_called_once()

        mock_mReadFile.reset_mock()
        mock_mReadFile.side_effect = Exception()
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer._mRunApplyVlanDelete("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to update the file /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/vm.cfg on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mBackupGuestXmls(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mExecuteCmd,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "msg_out", "msg_err")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer.mBackupGuestXmls("backup", "129")
        mock_mExecuteCmd.assert_called_once()

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.return_value = (1, "msg_out", "msg_err")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mBackupGuestXmls("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to take backup of /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/vm.cfg on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )
        mock_mExecuteCmd.assert_called_once()

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_getUpdatedBridgeAddress(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = VM_CFG.encode()
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        address = nodeComposer.getUpdatedBridgeAddress("backup")
        self.assertEqual(address, "00:16:3e:a7:3b:39")

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_getUpdatedBridgeAddressFails(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = BRIDGE_XML
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(Exception):
            nodeComposer.getUpdatedBridgeAddress("backup")

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    @patch("exabox.core.Node.exaBoxNode.mWriteFile")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    def test_mUpdatePersistentRules(
            self,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mWriteFile,
            mock_mReadFile,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mWriteFile.return_value = None
        mock_mReadFile.return_value = NETRULES.encode("utf-8")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer._mUpdatePersistentRules("0000:0f:04.0", "backup")
        mock_mReadFile.assert_called_once()
        mock_mWriteFile.assert_called_once()
        calls = mock_mWriteFile.call_args_list
        _, rules = calls[0][0]
        self.assertIn(
            'SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="0000:0f:04.0", KERNEL=="e*", NAME="bondeth1"',
            rules.decode(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch("exabox.ovm.clunetworkreconfig.XenNodeNetworkComposer.mDetectSharedBridge", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.sleep", return_value=None)
    def test_mDeleteStaleBridge(
            self,
            mock_sleep,
            _mock_mDisconnect,
            _mock_mConnect,
            _mock_mDetectSharedBridge,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_sleep.return_value = None
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (0, "", "")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer.mDeleteStaleBridge("backup", "129")
        calls = mock_mExecuteCmd.call_args_list
        _, cmd = calls[0][0]
        self.assertEqual(
            "/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 vmbondeth1.129 -force",
            cmd,
        )
        self.assertEqual(mock_mExecuteCmd.call_count, 1)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch(
        "exabox.ovm.clunetworkreconfig.XenNodeNetworkComposer.mDetectSharedBridge",
        return_value=0,
    )
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.sleep", return_value=None)
    def test_mDeleteStaleBridgeFails(
            self,
            mock_sleep,
            _mock_mDisconnect,
            _mock_mConnect,
            _mock_mDetectSharedBridge,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_sleep.return_value = None
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (1, "", "")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mDeleteStaleBridge("backup", "129")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't delete bonded bridge vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeNetworkComposer.mExecuteCmd")
    @patch(
        "exabox.ovm.clunetworkreconfig.XenNodeNetworkComposer.mDetectSharedBridge",
        return_value=1,
    )
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.sleep", return_value=None)
    def test_mDeleteStaleBridgeWithSharedBridge(
            self,
            mock_sleep,
            _mock_mDisconnect,
            _mock_mConnect,
            _mock_mDetectSharedBridge,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_sleep.return_value = None
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmd.return_value = (1, "", "")
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = XenNodeNetworkComposer(
            cluctrl,
            ebDNSConfig(testOptions()),
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer.mDeleteStaleBridge("backup", "129")
        self.assertEqual(mock_mExecuteCmd.call_count, 0)


if __name__ == "__main__":
    unittest.main()
