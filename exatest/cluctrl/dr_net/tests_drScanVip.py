#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/dr_net/tests_drScanVip.py /main/3 2025/08/22 12:02:55 aararora Exp $
#
# tests_drScanVip.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_drScanVip.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    08/07/25 - ER 37858683: Add tcps config if present in the payload
#    aararora    03/23/23 - Tests the methods for configuring dr scan and vips
#                           during provisioning and elastic compute scenarios.
#    aararora    03/23/23 - Creation
#
import unittest

from unittest.mock import patch

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.cluelasticcompute import ebCluReshapeCompute
from exabox.ovm.csstep.cs_postginid import csPostGINID
from exabox.ovm.cluconfig import ebCluDRVipConfig, ebCluDRScanConfig

ELASTIC_PAYLOAD = {
        "adb_s": "False",
        "bonding": "disabled",
        "dbaas_api": {
            "FLAGS": "",
            "action": "set",
            "object": "os",
            "operation": "cloud_properties",
            "outputfile": "/tmp/cloudProperties_2023.03.02.18.28.42",
            "params": {
                "adb_s": {
                    "enabled": "False"
                },
                "atp": {},
                "cns": {
                    "enabled": "False"
                },
                "common": {
                    "fedramp": "disabled",
                    "fips_compliance": "disabled",
                    "oss_url": "https://swiftobjectstorage.us-ashburn-1.oraclecloud.com",
                    "se_linux": "disabled"
                },
                "diag": {},
                "ords": {
                    "enable": "False"
                }
            }
        },
        "jumbo_frames": "both",
        "reshaped_node_subset": {
            "added_computes": [
                {
                    "compute_node_alias": "node-3",
                    "compute_node_hostname": "scaqan02adm07.us.oracle.com",
                    "db_info": [],
                    "network_info": {
                        "computenetworks": [
                            {
                                "admin": [
                                    {
                                        "domain": "us.oracle.com",
                                        "fqdn": "scaqan02adm07.us.oracle.com",
                                        "gateway": "10.32.8.1",
                                        "hostname": "scaqan02adm07",
                                        "ipaddr": "10.32.10.125",
                                        "netmask": "255.255.248.0"
                                    }
                                ]
                            },
                            {
                                "private": [
                                    {
                                        "domain": "us.oracle.com",
                                        "fqdn": "scaqan02db07-priv1.us.oracle.com",
                                        "hostname": "scaqan02db07-priv1",
                                        "ipaddr": "192.168.12.96"
                                    },
                                    {
                                        "domain": "us.oracle.com",
                                        "fqdn": "scaqan02db07-priv2.us.oracle.com",
                                        "hostname": "scaqan02db07-priv2",
                                        "ipaddr": "192.168.12.97"
                                    }
                                ]
                            },
                            {
                                "ilom": [
                                    {
                                        "domain": "us.oracle.com",
                                        "fqdn": "scaqan02adm07-c.us.oracle.com",
                                        "gateway": "10.32.8.1",
                                        "hostname": "scaqan02adm07-c",
                                        "ipaddr": "10.32.10.145",
                                        "netmask": "255.255.248.0"
                                    }
                                ]
                            }
                        ]
                    },
                    "rack_info": {
                        "racknum": "1",
                        "uheight": "1",
                        "uloc": "25"
                    },
                    "virtual_compute_info": {
                        "compute_node_hostname": "scaqan02dv0701.us.oracle.com",
                        "network_info": {
                            "virtualcomputenetworks": [
                                {
                                    "private": [
                                        {
                                            "fqdn": "scaqan02db07vm1clu1-priv1.us.oracle.com",
                                            "ipaddr": "192.168.12.98"
                                        },
                                        {
                                            "fqdn": "scaqan02db07vm1clu1-priv2.us.oracle.com",
                                            "ipaddr": "192.168.12.99"
                                        }
                                    ]
                                },
                                {},
                                {
                                    "client": [
                                        {
                                            "fqdn": "scaqan02dv0701.us.oracle.com",
                                            "gateway": "10.32.16.1",
                                            "ipaddr": "10.32.17.214",
                                            "natdomain": "us.oracle.com",
                                            "nathostname": "scaqan02dv0701m",
                                            "natip": "10.32.10.212",
                                            "natnetmask": "255.255.248.0",
                                            "netmask": "255.255.248.0",
                                            "vlantag": "101"
                                        }
                                    ]
                                },
                                {
                                    "backup": [
                                        {
                                            "fqdn": "scaqan02dv0701-bk.us.oracle.com",
                                            "gateway": "10.32.94.1",
                                            "ipaddr": "10.32.94.19",
                                            "netmask": "255.255.255.224",
                                            "vlantag": "129"
                                        }
                                    ]
                                },
                                {
                                    "interconnect": [
                                        {
                                            "fqdn": "scaqan0207vmclu1-priv1.us.oracle.com",
                                            "ipaddr": "192.168.21.9"
                                        },
                                        {
                                            "fqdn": "scaqan0207vmclu1-priv2.us.oracle.com",
                                            "ipaddr": "192.168.21.14"
                                        }
                                    ]
                                },
                                {
                                    "vip": [
                                        {
                                            "fqdn": "scaqan02dv0701-vip.us.oracle.com",
                                            "gateway": "null",
                                            "ipaddr": "10.32.17.222",
                                            "netmask": "null",
                                            "vlantag": "null"
                                        }
                                    ]
                                },
                                {
                                    "dr": [
                                        {
                                            "fqdn": "scaqan02dv0706-dr.us.oracle.com",
                                            "gateway": "10.214.208.1",
                                            "ipaddr": "10.214.216.166",
                                            "netmask": "255.255.240.0",
                                            "vlantag": "232"
                                        }
                                    ]
                                },
                                {
                                    "drVip": [
                                        {
                                            "fqdn": "scaqan02dv0706-vip-dr.us.oracle.com",
                                            "gateway": "10.214.208.1",
                                            "ipaddr": "10.214.216.167",
                                            "netmask": "255.255.240.0",
                                            "vlantag": "232"
                                        }
                                    ]
                                }
                            ]
                        },
                        "vm": {
                            "cores": 2,
                            "size": "Large"
                        }
                    }
                }
            ],
            "full_compute_to_virtualcompute_list": [
                {
                    "compute_node_hostname": "scaqan02adm07.us.oracle.com",
                    "compute_node_virtual_hostname": "scaqan02dv0701"
                },
                {
                    "compute_node_hostname": "scaqan02adm02.us.oracle.com",
                    "compute_node_virtual_hostname": "scaqan02dv0201.us.oracle.com"
                },
                {
                    "compute_node_hostname": "scaqan02adm01.us.oracle.com",
                    "compute_node_virtual_hostname": "scaqan02dv0101.us.oracle.com"
                }
            ],
            "participating_computes": [
                {
                    "compute_node_alias": "node-3",
                    "compute_node_hostname": "scaqan02adm07.us.oracle.com"
                },
                {
                    "compute_node_alias": "node-2",
                    "compute_node_hostname": "scaqan02adm02.us.oracle.com"
                },
                {
                    "compute_node_alias": "node-1",
                    "compute_node_hostname": "scaqan02adm01.us.oracle.com"
                }
            ],
            "removed_computes": [],
            "retained_computes": [
                {
                    "compute_node_alias": "node-1",
                    "compute_node_hostname": "scaqan02adm01.us.oracle.com"
                },
                {
                    "compute_node_alias": "node-2",
                    "compute_node_hostname": "scaqan02adm02.us.oracle.com"
                }
            ]
        }
    }

class testOptions(object): pass

class ebTestDRScanVip(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestDRScanVip, self).setUpClass(False,False)
    
    def test_mSetDRVipElastic(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on ebCluReshapeCompute.mSetDRVip.")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/usr/bin/cat /etc/oratab", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        cluctrl = self.mGetClubox()

        _options = self.mGetPayload()
        _options.jsonconf = ELASTIC_PAYLOAD

        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU'),\
             patch('exabox.ovm.cluelasticcompute.node_cmd_abs_path_check', return_value='/bin/dbaascli'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'):
             ebCluReshapeComputeInstance = ebCluReshapeCompute(cluctrl, _options)
             ebCluReshapeComputeInstance.mSetDRVip("scaqan02dv0701.us.oracle.com")

    def test_mSetDRScanVipProvisioning(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on csPostGINID.mSetDRScanVip.")

        cluctrl = self.mGetClubox()
        csPostGINIDInstance = csPostGINID()
        cluctrl.mGetArgsOptions().jsonconf = {
                                              "customer_network":
                                                  {
                                                      "drScan":
                                                          {
                                                              "tcp_ssl_port": "1560"
                                                          }
                                                  }}

        with patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnDom0DomUPair', return_value=[(None, "DOMU1")]),\
             patch('exabox.ovm.csstep.cs_base.node_cmd_abs_path_check', return_value='/bin/dbaascli'),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
             patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0):
             _dr_vip_config = ebCluDRVipConfig()
             _dr_vip_config.mSetDRVIPAddr("192.168.0.1")
             cluctrl.mSetDRVips({"scaqan02dv0701.us.oracle.com": _dr_vip_config})
             _dr_scan_config = ebCluDRScanConfig()
             _dr_scan_config.mSetScanName("scan_name-dr")
             _dr_scan_config.mSetScanPort(1521)
             cluctrl.mSetDRScans(_dr_scan_config)
             csPostGINIDInstance.mSetDRScanVip(cluctrl)

if __name__ == '__main__':
    unittest.main() 