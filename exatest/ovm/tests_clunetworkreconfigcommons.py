#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clunetworkreconfigcommons.py /main/1 2025/05/21 05:57:34 rkhemcha Exp $
#
# tests_clunetworkreconfigcommons.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clunetworkreconfigcommons.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rkhemcha    03/03/25 - Creation
#

import copy
import warnings
import unittest
import traceback

from unittest.mock import patch
from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.ovm.clunetworkreconfigcommons import (
    ebCluNetworkReconfigHandler,
    NodeUtils
)

from exabox.ovm.hypervisorutils import getTargetHVIType, HVIT_XEN, HVIT_KVM

DOM0_NETWORK_INFO = {
    "admin": {
        "bridge": "vmeth1",
        "bond_master": "eth1",
        "bond_slaves": ""
    },
    "client": {
        "bridge": "vmbondeth0",
        "bond_master": "bondeth0",
        "bond_slaves": "eth4 eth5"
    },
    "backup": {
        "bridge": "vmbondeth1",
        "bond_master": "bondeth1",
        "bond_slaves": "eth6 eth7"
    }
}

PAYLOAD = {
    "network": {},
    "updateNetwork": {
        "networkServices": [
            {
                "op": "dns_update",
                "payload": {}
            },
            {
                "op": "ntp_update",
                "payload": {}
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
                        }
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
                        }
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
        ]
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
    }
}

NODESUBSET_PAYLOAD = {
    "network": {},
    "updateNetwork": {
        "networkServices": [
            {
                "op": "dns_update",
                "payload": {}
            },
            {
                "op": "ntp_update",
                "payload": {}
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
                            "compute_node_alias": "node-2",
                        },
                    },
                    {
                        "op": "vlan_add",
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0312-bk",
                            "ip": "10.31.217.72",
                            "netmask": "255.255.255.128",
                            "vlantag": "154",
                            "compute_node_alias": "node-2",
                        },
                    },
                    {
                        "op": "vlan_delete",
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0312-bk",
                            "ip": "10.31.217.72",
                            "netmask": "255.255.255.128",
                            "vlantag": "1",
                            "compute_node_alias": "node-2",
                        },
                    },
                ]
            }
        ],
    },
    "node_subset": {
        "participating_computes": [
            {
                "compute_node_alias": "node-2",
                "compute_node_hostname": "scaqab10adm02.us.oracle.com",
            },
        ],
        "num_participating_computes": 1,
    },
}

CLIENT_UPDATE_PAYLOAD = {
    "network": {},
    "updateNetwork": {
        "networkServices": [],
        "nodes": [
            {
                "backup": [],
                "client": [
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
                        }
                    }
                ]
            },
            {
                "backup": []
            }
        ]
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
    }
}

SINGLE_NODE_TRANSFORMED_PAYLOAD = {
    "network": {},
    "updateNetwork": {
        "networkServices": [
            {
                "op": "dns_update",
                "payload": {
                    "compute_node_alias": "node-1"
                }
            },
            {
                "op": "ntp_update",
                "payload": {
                    "compute_node_alias": "node-1"
                }
            },
            {
                "op": "dns_update",
                "payload": {
                    "compute_node_alias": "node-2"
                }
            },
            {
                "op": "ntp_update",
                "payload": {
                    "compute_node_alias": "node-2"
                }
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
                        }
                    },
                    {
                        "op": "vlan_add",
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0312-bk",
                            "ip": "10.31.217.72",
                            "netmask": "255.255.255.128",
                            "vlantag": "154",
                            "compute_node_alias": "node-1"
                        }
                    },
                    {
                        "op": "vlan_delete",
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0412-bk",
                            "ip": "10.31.217.69",
                            "netmask": "255.255.255.128",
                            "vlantag": "129",
                            "compute_node_alias": "node-1"
                        }
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
                "backup": []
            }
        ]
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
    }
}

RESULT_PAYLOAD = {
    "node-1": {
        "ipconf_updates": {
            "entities": [
                "backup",
                "dns",
                "ntp"
            ],
            "status": "SUCCESS",
            "msg": "cidr success msg for node-1"
        },
        "vlan_add_backup": {
            "payload": {
                "domainname": "us.oracle.com",
                "gateway": "10.32.94.65",
                "hostname": "scaqan04dv0301-bk",
                "ip": "10.32.94.89",
                "netmask": "255.255.255.224",
                "vlantag": "129"
            },
            "status": "SUCCESS",
            "msg": "vlan add success msg on node-1"
        },
        "vlan_delete_backup": {
            "payload": {
                "domainname": "us.oracle.com",
                "gateway": "10.32.94.65",
                "hostname": "scaqan04dv0301-bk",
                "ip": "10.32.94.89",
                "netmask": "255.255.255.224",
                "vlantag": "129"
            },
            "status": "FAILURE",
            "msg": "vlan delete failure msg on node-1"
        }
    },
    "node-2": {
        "ipconf_updates": {
            "entities": [
                "backup",
                "dns",
                "ntp"
            ],
            "status": "FAILURE",
            "msg": "cidr failure msg for node-2"
        }
    }
}

VLAN_UPDATE_PAYLOAD = {
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

CIDR_UPDATE_PAYLOAD = {
    "ipconf_updates": {
        "entities": [
            "backup",
            "dns",
            "ntp"
        ],
        "status": "NOOP",
        "msg": ""
    }
}

ALL_OPS_PAYLOAD = {
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
            self.jsonconf = copy.deepcopy(PAYLOAD)
        else:
            self.jsonconf = copy.deepcopy(payload)
        self.jsonmode = False
        self.configpath = None


class ebTestCluNetworkReconfigHandler(ebTestClucontrol):
    @classmethod
    def setUpClass(cls):
        super(ebTestCluNetworkReconfigHandler, cls).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    def test_mGetDom0DomuPairForNode(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        dom0 = __dom0domUpairs[0][0]
        nwReconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        self.assertEqual(
            nwReconfig.mGetDom0DomuPairForNode(dom0),
            ["scaqab10adm01.us.oracle.com", "scaqab10client01vm08.us.oracle.com"]
        )

    def test_nonOCIEXACC(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(False)
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkReconfigHandler(cluctrl, testOptions())
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8005)
        self.assertEqual(
            "EXACLOUD : Detected non-OCIEXACC environment. Network reconfiguration is not supported",
            ctx.exception.mGetErrorMsg(),
        )

    def test_invalidOperation(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            payload = copy.deepcopy(PAYLOAD)
            payload["updateNetwork"]["nodes"][0]["backup"][0]["op"] = "cidr_add"
            ebCluNetworkReconfigHandler(cluctrl, testOptions(payload))
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8005)
        self.assertEqual(
            "EXACLOUD : Invalid network reconfiguration operation cidr_add",
            ctx.exception.mGetErrorMsg(),
        )

    def test_invalidServiceOperation(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            payload = copy.deepcopy(PAYLOAD)
            payload["updateNetwork"]["networkServices"][0]["op"] = "ilom_update"
            ebCluNetworkReconfigHandler(cluctrl, testOptions(payload))
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8005)
        self.assertEqual(
            "EXACLOUD : Invalid network service reconfiguration operation ilom_update",
            ctx.exception.mGetErrorMsg(),
        )

    def test_unsupportedNetwork(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            ebCluNetworkReconfigHandler(cluctrl, testOptions(payload=CLIENT_UPDATE_PAYLOAD))
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8005)
        self.assertEqual(
            "EXACLOUD : Changes in unsupported network client identified. Exiting.",
            ctx.exception.mGetErrorMsg(),
        )

    def test_invalidOperationInfo(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            payload = copy.deepcopy(PAYLOAD)
            payload["updateNetwork"]["nodes"][0]["backup"][0]["op"] = "vlan_delete"
            del payload["updateNetwork"]["nodes"][0]["backup"][0]["payload"]["vlantag"]
            ebCluNetworkReconfigHandler(cluctrl, testOptions(payload=payload))
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8005)
        self.assertEqual(
            "EXACLOUD : Missing data in payload {'domainname': 'us.oracle.com', 'gateway': '10.31.217.1', 'hostname': 'scaqan03dv0312-bk', 'ip': '10.31.217.72', 'netmask': '255.255.255.128', 'compute_node_alias': 'node-1'} to perform operation vlan_delete",
            ctx.exception.mGetErrorMsg(),
        )

    def test_invalidNodes(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            payload = copy.deepcopy(PAYLOAD)
            del payload["updateNetwork"]["nodes"][0]
            ebCluNetworkReconfigHandler(cluctrl, testOptions(payload))
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8001)
        self.assertEqual(
            "EXACLOUD : Node count mismatch in updateNetwork section of payload with num_participating_computes",
            ctx.exception.mGetErrorMsg(),
        )

    def test_mGetBackupDirCps(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        self.assertEqual(reconfig.mGetBackupDirCps(), "/opt/oci/exacc/exacloud/scratch/nw_reconfig/exatest")

    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmdLocal", return_value=(0, ""))
    def test_mCreateBackupDirCps(self, mock_mExecuteCmdLocal):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        reconfig.mCreateBackupDirCps()
        mock_mExecuteCmdLocal.assert_called_once()

    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmdLocal", return_value=(1, ""))
    def test_mCreateBackupDirCps_fail(self, mock_mExecuteCmdLocal):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            reconfig.mCreateBackupDirCps()
        mock_mExecuteCmdLocal.assert_called_once()
        assert ("EXACLOUD : Failed to create backup dir /opt/oci/exacc/exacloud/scratch/nw_reconfig/exatest on"
                in ctx.exception.mGetErrorMsg())
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)

    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmdLocal", return_value=(0, ""))
    def test_mBackupConfCps(self, mock_mExecuteCmdLocal):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        reconfig.mBackupConfCps("/etc/hosts.exacc_domu")
        mock_mExecuteCmdLocal.assert_called_once()

    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmdLocal", return_value=(1, ""))
    def test_mBackupConfCps_fail(self, mock_mExecuteCmdLocal):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            reconfig.mBackupConfCps("/etc/hosts.exacc_domu")
        mock_mExecuteCmdLocal.assert_called_once()
        assert ("EXACLOUD : Failed to take backup of /etc/hosts.exacc_domu on"
                in ctx.exception.mGetErrorMsg())
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)

    def test_errorCodes(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        # Setting ERROR code for Reconfig
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        self.assertEqual(reconfig.isRevert, False)
        self.assertEqual(reconfig.errorCode, 0x8006)

        # Setting ERROR code for Revert Reconfig
        from exabox.exatest.ovm.tests_clurevertnetworkreconfig import NOOP_PAYLOAD
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions(payload=NOOP_PAYLOAD))
        self.assertEqual(reconfig.isRevert, True)
        self.assertEqual(reconfig.errorCode, 0x8007)

    @patch("exabox.ovm.clunetworkreconfigcommons.ebCluNetworkReconfigHandler.mValidatePayload")
    def test_mUpdateDnsRecord_true(self, mock_mValidatePayload):
        payload = {
            "updateNetwork": {
                "nodes": [
                    {
                        "backup": [],
                        "updateProperties": {
                            "backup": ["ip", "hostname"]
                        }
                    },
                    {
                        "backup": [],
                        "updateProperties": {
                            "backup": ["hostname", "netmask"]
                        }
                    }
                ]
            }
        }
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mValidatePayload.return_value = None
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions(payload=payload))
        self.assertEqual(reconfig.mUpdateDnsRecord(), True)

    @patch("exabox.ovm.clunetworkreconfigcommons.ebCluNetworkReconfigHandler.mValidatePayload")
    def test_mUpdateDnsRecord_false(self, mock_mValidatePayload):
        payload = {
            "updateNetwork": {
                "nodes": [
                    {
                        "backup": [],
                        "updateProperties": {
                            "backup": ["domain", "vlantag"]
                        }
                    },
                    {
                        "backup": [],
                        "updateProperties": {
                            "backup": ["gateway", "netmask"]
                        }
                    }
                ]
            }
        }
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mValidatePayload.return_value = None
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions(payload=payload))
        self.assertEqual(reconfig.mUpdateDnsRecord(), False)

    def test_mSetResultOrgPayload(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions(SINGLE_NODE_TRANSFORMED_PAYLOAD))
        reconfig.mSetResultOrgPayload("node-1", RESULT_PAYLOAD["node-1"])
        reconfig.mSetResultOrgPayload("node-2", RESULT_PAYLOAD["node-2"])

        for serviceUpdate in reconfig.payload["updateNetwork"]["networkServices"]:
            alias = serviceUpdate["payload"]["compute_node_alias"]
            self.assertEqual(
                serviceUpdate["status"],
                RESULT_PAYLOAD[alias]["ipconf_updates"]["status"]
            )
            self.assertEqual(
                serviceUpdate["msg"],
                RESULT_PAYLOAD[alias]["ipconf_updates"]["msg"]
            )

        for nodeUpdate in reconfig.payload["updateNetwork"]["nodes"]:
            for net in nodeUpdate:
                if net in ["updateProperties"]:
                    continue
                for operation in nodeUpdate[net]:
                    if operation["op"] == "cidr_update":
                        alias = operation["payload"]["compute_node_alias"]
                        self.assertEqual(
                            operation["status"],
                            RESULT_PAYLOAD[alias]["ipconf_updates"]["status"]
                        )
                        self.assertEqual(
                            operation["msg"],
                            RESULT_PAYLOAD[alias]["ipconf_updates"]["msg"]
                        )
                    else:
                        alias = operation["payload"]["compute_node_alias"]
                        self.assertEqual(
                            operation["status"],
                            RESULT_PAYLOAD[alias][f"{operation['op']}_{net}"]["status"]
                        )
                        self.assertEqual(
                            operation["msg"],
                            RESULT_PAYLOAD[alias][f"{operation['op']}_{net}"]["msg"]
                        )

    def test_mConsolidateOperations_allOps(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        transformedPayload = reconfig.mConsolidateOperations(
            PAYLOAD["updateNetwork"]["nodes"],
            PAYLOAD["updateNetwork"]["networkServices"],
            PAYLOAD["node_subset"]["participating_computes"]
        )
        self.assertEqual(
            {
                "node-1": {
                    "ipconf_updates": {
                        "entities": [
                            "backup",
                            "dns",
                            "ntp"
                        ]
                    }
                },
                "node-2": {
                    "ipconf_updates": {
                        "entities": [
                            "backup",
                            "dns",
                            "ntp"
                        ]
                    }
                }
            },
            transformedPayload
        )

    def test_mConsolidateOperations_backup_nodeSubset(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        transformedPayload = reconfig.mConsolidateOperations(
            NODESUBSET_PAYLOAD["updateNetwork"]["nodes"],
            NODESUBSET_PAYLOAD["updateNetwork"]["networkServices"],
            NODESUBSET_PAYLOAD["node_subset"]["participating_computes"]
        )
        self.assertEqual(
            {
                "node-2": {
                    "ipconf_updates": {
                        "entities": [
                            "backup",
                            "dns",
                            "ntp"
                        ]
                    },
                    "vlan_add_backup": {
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0312-bk",
                            "ip": "10.31.217.72",
                            "netmask": "255.255.255.128",
                            "vlantag": "154",
                            "compute_node_alias": "node-2"
                        }
                    },
                    "vlan_delete_backup": {
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0312-bk",
                            "ip": "10.31.217.72",
                            "netmask": "255.255.255.128",
                            "vlantag": "1",
                            "compute_node_alias": "node-2"
                        }
                    }
                }
            },
            transformedPayload
        )

    def test_mConsolidateOperations_onlyDnsNtp(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        transformedPayload = reconfig.mConsolidateOperations(
            [{"backup": []}, {"backup": []}],
            PAYLOAD["updateNetwork"]["networkServices"],
            PAYLOAD["node_subset"]["participating_computes"]
        )
        self.assertEqual(
            {
                "node-1": {
                    "ipconf_updates": {
                        "entities": [
                            "dns",
                            "ntp"
                        ]
                    }
                },
                "node-2": {
                    "ipconf_updates": {
                        "entities": [
                            "dns",
                            "ntp"
                        ]
                    }
                }
            },
            transformedPayload
        )

    def test_mConsolidateOperations_allOps_singleNodeUpdates(self):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        reconfig = ebCluNetworkReconfigHandler(cluctrl, testOptions())
        transformedPayload = reconfig.mConsolidateOperations(
            [NODESUBSET_PAYLOAD["updateNetwork"]["nodes"][0], {"backup": []}],
            PAYLOAD["updateNetwork"]["networkServices"],
            PAYLOAD["node_subset"]["participating_computes"]
        )
        self.assertEqual(
            {
                "node-1": {
                    "ipconf_updates": {
                        "entities": [
                            "dns",
                            "ntp"
                        ]
                    }
                },
                "node-2": {
                    "ipconf_updates": {
                        "entities": [
                            "backup",
                            "dns",
                            "ntp"
                        ]
                    },
                    "vlan_add_backup": {
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0312-bk",
                            "ip": "10.31.217.72",
                            "netmask": "255.255.255.128",
                            "vlantag": "154",
                            "compute_node_alias": "node-2"
                        }
                    },
                    "vlan_delete_backup": {
                        "payload": {
                            "domainname": "us.oracle.com",
                            "gateway": "10.31.217.1",
                            "hostname": "scaqan03dv0312-bk",
                            "ip": "10.31.217.72",
                            "netmask": "255.255.255.128",
                            "vlantag": "1",
                            "compute_node_alias": "node-2"
                        }
                    }
                }
            },
            transformedPayload
        )


class ebTestNodeUtils(ebTestClucontrol):

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_init(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(utils.errorcode, "ERROR_RECONFIGURATION_FAILED")
        self.assertEqual(len(utils.operations), 1)
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        self.assertEqual(utils.errorcode, "ERROR_RECONFIGURATION_FAILED")
        self.assertEqual(len(utils.operations), 2)
        self.assertEqual(len(utils.operations), 2)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetNetVlanId(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(cluctrl, __dom0domUpairs[0], PAYLOAD)

        # Override vlan for client network
        cluConfObj = utils.mGetCluConfig("client")
        oldVlan = cluConfObj.mGetNetVlanId()
        cluConfObj.mSetNetVlanId('999')

        self.assertEqual(utils.mGetNetVlanId("client"), "999")

        # restore the Vlan ID back to original
        cluConfObj.mSetNetVlanId(oldVlan)

        self.assertEqual(utils.mGetNetVlanId("client"), None)
        self.assertEqual(utils.mGetNetVlanId("backup"), None)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetNetLacp(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(cluctrl, __dom0domUpairs[0], PAYLOAD)
        self.assertEqual(utils.mGetNetLacp("client"), False)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetBackupDir(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(
            utils.mGetBackupDir(), "/opt/exacloud/nw_reconfig/exatest"
        )

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeUtils.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mCreateBackupDir(
            self,
            mock_mGetNetworkSetupInformation,
            mock_mExecuteCmd,
            _mock_mConnect,
            _mock_mDisconnect
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [(0, "", ""), (0, "", "")]
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        utils.mCreateBackupDir()
        self.assertEqual(mock_mExecuteCmd.call_count, 2)

    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.NodeUtils.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mCreateBackupDir_fail(
            self,
            mock_mGetNetworkSetupInformation,
            mock_mExecuteCmd,
            _mock_mConnect,
            _mock_mDisconnect
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mExecuteCmd.side_effect = [(0, "", ""), (1, "", "")]
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        dom0, domU = __dom0domUpairs[0][0], __dom0domUpairs[0][1]
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )

        # Failure on dom0
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            utils.mCreateBackupDir()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            f"EXACLOUD : Failed to create backup dir /opt/exacloud/nw_reconfig/exatest on {dom0}",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(mock_mExecuteCmd.call_count, 2)

        # Failure on domU
        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [(1, "", "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            utils.mCreateBackupDir()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            f"EXACLOUD : Failed to create backup dir /opt/exacloud/nw_reconfig/exatest on {domU}",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(mock_mExecuteCmd.call_count, 1)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetBondedBridgeName(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(utils.mGetBondedBridgeName("backup"), "vmbondeth1")
        self.assertEqual(utils.mGetBondedBridgeName("backup", "129"), "vmbondeth1.129")

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetSlaveInterfaces(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(utils.mGetSlaveInterfaces("backup"), ["eth6", "eth7"])

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetSlaveInterfacesFails(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        net_info = copy.deepcopy(DOM0_NETWORK_INFO)
        net_info["backup"]["bond_slaves"] = "eth99"
        mock_mGetNetworkSetupInformation.return_value = net_info
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        utils.interfaceInfo["backup"]["slaves"] = []
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            utils.mGetSlaveInterfaces("backup")
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Incorrect slave interfaces ['eth99'] returned from exacloud for backup network.",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetServers(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(utils.mGetServers("dns"), ['77.0.0.1'])
        self.assertEqual(utils.mGetServers("ntp"), ['10.150.240.129'])

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetMasterInterface(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD),
        )
        self.assertEqual(utils.mGetMasterInterface("backup"), "bondeth1")

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("os.path.isfile")
    def test_mGetInterfaceInfoFails(self,
                                    mock_mGetNetworkSetupInformation,
                                    mock_isfile
                                    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = {}
        mock_isfile.return_value = False
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            NodeUtils(
                cluctrl,
                __dom0domUpairs[0],
                copy.deepcopy(VLAN_UPDATE_PAYLOAD),
            )
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertIn("Cannot find network info from exacloud for node", ctx.exception.mGetErrorMsg())

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mGetInterfaceInfo(self, mock_mGetNetworkSetupInformation):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        self.assertEqual(
            utils.interfaceInfo,
            DOM0_NETWORK_INFO,
        )

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mRunIpConf_fail(self,
                             mock_mGetNetworkSetupInformation,
                             mock_mExecuteCmd,
                             mock_mConnect
                             ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        mock_mExecuteCmd.return_value = (1, "", "")
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(CIDR_UPDATE_PAYLOAD)
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            utils.mRunIpConf()
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Failed to run ipconf on scaqab10client01vm08.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mAddBondedBridge_fail(self,
                                   mock_mGetNetworkSetupInformation,
                                   mock_mExecuteCmd,
                                   mock_mConnect
                                   ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        mock_mExecuteCmd.side_effect = [
            (1, "msg_out", "msg_err"),
            (1, "msg_out", "msg_err"),
        ]
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD)
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            utils.mAddBondedBridge("backup", "129", HVIT_KVM)
        self.assertEqual(
            "EXACLOUD : Couldn't add bonded bridge vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mAddBondedBridge_exists_KVM(self,
                                         mock_mGetNetworkSetupInformation,
                                         mock_mExecuteCmd,
                                         mock_mConnect
                                         ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        mock_mExecuteCmd.return_value = (0, "", "")
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD)
        )
        utils.mAddBondedBridge("backup", "129", HVIT_KVM)
        mock_mExecuteCmd.assert_called_once()

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mAddBondedBridge_exists_XEN(self,
                                         mock_mGetNetworkSetupInformation,
                                         mock_mExecuteCmd,
                                         mock_mConnect
                                         ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        mock_mExecuteCmd.return_value = (0, "", "")
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD)
        )
        utils.mAddBondedBridge("backup", "129", HVIT_XEN)
        mock_mExecuteCmd.assert_called_once()

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mDeleteBondedBridge_KVM(self,
                                     mock_mGetNetworkSetupInformation,
                                     mock_mExecuteCmd,
                                     mock_mConnect
                                     ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        mock_mExecuteCmd.return_value = (0, "", "")
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD)
        )
        utils.mDeleteBondedBridge("backup", "vmbondeth1.129", HVIT_KVM)
        mock_mExecuteCmd.assert_called_once()

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mDeleteBondedBridge_XEN(self,
                                     mock_mGetNetworkSetupInformation,
                                     mock_mExecuteCmd,
                                     mock_mConnect
                                     ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        mock_mExecuteCmd.return_value = (0, "", "")
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD)
        )
        utils.mDeleteBondedBridge("backup", "vmbondeth1.129", HVIT_XEN)
        mock_mExecuteCmd.assert_called_once()

    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfigcommons.NodeUtils.mExecuteCmd")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    def test_mDeleteBondedBridge_fail(self,
                                      mock_mGetNetworkSetupInformation,
                                      mock_mExecuteCmd,
                                      mock_mConnect
                                      ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        mock_mExecuteCmd.return_value = (1, "", "")
        utils = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD)
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            utils.mDeleteBondedBridge("backup", "vmbondeth1.129", HVIT_KVM)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't delete bonded bridge vmbondeth1.129 on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )
        mock_mExecuteCmd.assert_called_once()

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.ovm.clunetworkreconfig.NodeUtils.mExecuteCmdAsync")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.sleep", return_value=None)
    def test_mRestartDomainFails(
            self,
            mock_sleep,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mExecuteCmdAsync,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation
    ):
        def mExecuteCmdAsyncSideEffect(_, cmd):
            if "stop-domain" in cmd:
                return 1
            else:
                return 0

        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_sleep.return_value = None
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mock_mExecuteCmdAsync.side_effect = mExecuteCmdAsyncSideEffect
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mRestartDomain(HVIT_KVM)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8002)
        self.assertEqual(
            "EXACLOUD : Failed to stop domain scaqab10client01vm08.us.oracle.com while attempting to restart",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(mock_mExecuteCmdAsync.call_count, 1)

        mock_mExecuteCmdAsync.reset_mock()
        mock_mExecuteCmdAsync.side_effect = [0, 1]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mRestartDomain(HVIT_KVM)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8002)
        self.assertEqual(
            "EXACLOUD : Failed to start domain scaqab10client01vm08.us.oracle.com while attempting to restart",
            ctx.exception.mGetErrorMsg(),
        )
        self.assertEqual(mock_mExecuteCmdAsync.call_count, 2)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.ovm.clunetworkreconfig.NodeUtils.mExecuteCmdAsync")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.sleep", return_value=None)
    def test_mRestartDomain_KVM(
            self,
            mock_sleep,
            _mock_mDisconnect,
            _mock_mConnect,
            mExecuteCmdAsync,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_sleep.return_value = None
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mExecuteCmdAsync.return_value = 0
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer.mRestartDomain(HVIT_KVM)
        self.assertEqual(mExecuteCmdAsync.call_count, 2)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.cluconfig.ebCluNetworkConfig.mGetNetVlanId", return_value="129")
    @patch("exabox.ovm.clunetworkreconfig.NodeUtils.mExecuteCmdAsync")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.sleep", return_value=None)
    def test_mRestartDomain_XEN(
            self,
            mock_sleep,
            _mock_mDisconnect,
            _mock_mConnect,
            mExecuteCmdAsync,
            _mock_mGetNetVlanId,
            mock_mGetNetworkSetupInformation
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_sleep.return_value = None
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        mExecuteCmdAsync.return_value = 0
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        nodeComposer.mRestartDomain(HVIT_XEN)
        self.assertEqual(mExecuteCmdAsync.call_count, 2)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeUtils.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.sleep", return_value=None)
    def test_mDetectSharedBridge_XEN(
            self,
            mock_sleep,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation,
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_sleep.return_value = None
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        DOMAINS = ["scaqar05dv0301.us.oracle.com", "scaqab10client01vm08.us.oracle.com"]
        BRIDGE = "(bridge vmbondeth1.156)"
        wrong_domains = DOMAINS[:].remove("scaqab10client01vm08.us.oracle.com")
        mock_mExecuteCmd.side_effect = [(0, wrong_domains, ""), (0, BRIDGE, "")]
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_XEN)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't remove domain scaqab10client01vm08.us.oracle.com from the list. Please check if scaqab10client01vm08.us.oracle.com exists in xm list.",
            ctx.exception.mGetErrorMsg(),
        )

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [
            (0, DOMAINS, ""),
            (0, BRIDGE, ""),
            (0, BRIDGE, ""),
        ]
        detect = nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_XEN)
        self.assertEqual(detect, 1)

        mock_mExecuteCmd.reset_mock()
        BRIDGE = "(bridge vmbondeth1.129)"
        mock_mExecuteCmd.side_effect = [
            (0, DOMAINS, ""),
            (1, BRIDGE, ""),
            (1, BRIDGE, ""),
        ]
        detect = nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_XEN)
        self.assertEqual(detect, 0)

        mock_mExecuteCmd.reset_mock()
        BRIDGE = "(bridge vmbondeth1.129)"
        mock_mExecuteCmd.side_effect = [
            (0, DOMAINS, ""),
            (1, BRIDGE, "xm cannot list domain"),
            (1, BRIDGE, "xm cannot list domain"),
        ]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_XEN)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't list details for domain scaqar05dv0301.us.oracle.com on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

        mock_mExecuteCmd.reset_mock()
        BRIDGE = "(bridge vmbondeth1.129)"
        mock_mExecuteCmd.side_effect = [
            (1, DOMAINS, ""),
        ]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_XEN)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't list all domains on scaqab10adm01.us.oracle.com to detect shared bridges.",
            ctx.exception.mGetErrorMsg(),
        )

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation")
    @patch("exabox.ovm.clunetworkreconfig.NodeUtils.mExecuteCmd")
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=None)
    @patch("exabox.core.Node.exaBoxNode.mDisconnect", return_value=None)
    @patch("exabox.ovm.clunetworkreconfig.sleep", return_value=None)
    def test_mDetectSharedBridge_KVM(
            self,
            mock_sleep,
            _mock_mDisconnect,
            _mock_mConnect,
            mock_mExecuteCmd,
            mock_mGetNetworkSetupInformation
    ):
        cluctrl = copy.deepcopy(self.mGetClubox())
        cluctrl.mSetOciExacc(True)
        mock_sleep.return_value = None
        mock_mGetNetworkSetupInformation.return_value = DOM0_NETWORK_INFO
        DOMAINS = [
            "scaqar05dv0301.us.oracle.com",
            "scaqab10client01vm08.us.oracle.com",
            "",
        ]
        IFACE_LIST = ["vmbondeth0.181", "vmbondeth1.189", "vmeth201", "-", "-"]
        wrong_domains = DOMAINS[:].remove("scaqab10client01vm08.us.oracle.com")
        mock_mExecuteCmd.side_effect = [(0, wrong_domains, ""), (0, IFACE_LIST, "")]
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_KVM)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't remove domain scaqab10client01vm08.us.oracle.com from the list. "
            "Please check if scaqab10client01vm08.us.oracle.com exists using 'virsh list --all'.",
            ctx.exception.mGetErrorMsg(),
        )

        mock_mExecuteCmd.reset_mock()
        mock_mExecuteCmd.side_effect = [
            (0, DOMAINS, ""),
            (0, IFACE_LIST, ""),
            (0, IFACE_LIST, ""),
        ]
        detect = nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_KVM)
        self.assertEqual(detect, 0)

        mock_mExecuteCmd.reset_mock()
        IFACE_LIST.append("vmbondeth1.129")
        mock_mExecuteCmd.side_effect = [
            (0, DOMAINS, ""),
            (0, IFACE_LIST, ""),
            (0, IFACE_LIST, ""),
        ]
        detect = nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_KVM)
        self.assertEqual(detect, 1)

        mock_mExecuteCmd.reset_mock()
        IFACE_LIST.append("vmbondeth1.129")
        mock_mExecuteCmd.side_effect = [(1, DOMAINS, "")]
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_KVM)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't list all domains on scaqab10adm01.us.oracle.com",
            ctx.exception.mGetErrorMsg(),
        )

        mock_mExecuteCmd.side_effect = [(0, DOMAINS, ""), (1, IFACE_LIST, "")]
        __dom0domUpairs = cluctrl.mReturnDom0DomUPair()
        nodeComposer = NodeUtils(
            cluctrl,
            __dom0domUpairs[0],
            copy.deepcopy(VLAN_UPDATE_PAYLOAD),
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            nodeComposer.mDetectSharedBridge("vmbondeth1.129", HVIT_KVM)
        self.assertEqual(ctx.exception.mGetErrorCode(), 0x8006)
        self.assertEqual(
            "EXACLOUD : Couldn't list all interfaces for domain scaqar05dv0301.us.oracle.com "
            "on scaqab10adm01.us.oracle.com using 'virsh domiflist'.",
            ctx.exception.mGetErrorMsg()
        )


if __name__ == "__main__":
    unittest.main()
