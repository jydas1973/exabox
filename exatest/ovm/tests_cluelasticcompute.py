#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluelasticcompute.py /main/94 2025/12/03 16:38:14 jfsaldan Exp $
#
# tests_cluelasticcompute.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluelasticcompute.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    12/01/25 - Bug 38693893 - EXACS:BUTTERFLY:OC39:ADD VM FAILING
#                           AT RUN ROOTSCRIPT STEP:ERROR:OEDA-1200: ROOT.SH
#                           INITIALIZATION FOR CLUSTER CL-K3YQCYTA FAILED ON
#                           HOST
#    prsshukl    11/14/25 - Bug 36981808 - UT for mUpdateKMSRPM
#    naps        10/15/25 - Bug 38092408 - UT updation.
#    oespinos    07/30/25 - Enh 38051133: Adding check for call to delete dns
#                           in mExecDelNodeEndStep
#    gparada     07/29/25 - 38253002 allow add db instance for GPC and AWS
#    rajsag      07/29/25 - bug 38249275 - exacc:24.3.2.4.0:delete node:
#                           clunoderemovegideletetask step is failing due to
#                           stale entries not getting cleaned up
#    aararora    06/24/25 - Bug 38101818: Disable raising exception during
#                           delete compute for deconfig clusterware
#    bhpati      06/23/25 - Bug 38027097 - NEW LAUNCH STUCK AS THE OLD DELETE
#                           NODE HAD NOT DELETED VM.
#    pbellary    06/02/25 - Bug 37976663 - DB INSTANCES ARE NOT GETTING DELETED DURING DELETE NODE
#    aararora    03/04/25 - Bug 37542922: Raise exception in case oeda fails
#                           during undo of install cluster step for delete
#                           compute
#    ririgoye    01/22/25 - Bug 37265371 - Add mock commands for FS encryption
#                           checks
#    akkar       01/18/24 - Bug 37384268  Handle dbaascli faulty output
#    joysjose    12/16/24 - 37123857 Unit test for copy of resolv.conf to domUs
#                           during add node
#    joysjose    10/29/24 - 37111990: DeleteNode Unit Tests modification
#    prsshukl    07/25/24 - Enh 34014317 - Unit tests for mRemoveStoragePool
#                           method
#    akkar       07/02/24 - 36397179: Patch for dbaascli methods
#    jesandov    01/29/24 - 36207260: Add function to read/write sysctl
#                           parameters
#    rajsag      12/20/23 - exacs:23.4.1:tc2:post provisioning the
#                           hugepages_total:0 is set on the vm
#    pbellary    11/03/23 - 35448716 - ADD NODE FAILED AT CREATE VM STEP AFTER RENAMING CLUSTER NAME ON DOMUS
#    jesandov    10/16/23 - 35729701: Support of OL7 + OL8
#    aypaul      09/01/23 - Updating unit test cases for selinux update change.
#    pbellary    06/09/23 - ENH 35445802 - EXACS X9M(EXACLOUD) - ADD SUPPORT
#                           FOR 2TB MEMORY IN X9M
#    jesandov    06/07/23 - 35342930: Provisioning timing optimization in DetectOL7 and DetectOL8
#    joysjose    05/03/23 - Bug 35236850 - Patch source XML with DNS and NTP
#                           info from Source DomU before Add Node
#    rajsag      01/17/23 - ol8 support
#    rajsag      10/02/22 - 34591580 - EXACC: mSetSrcDom0DomU not setting the
#                           pingable node as src node
#    jlombera    03/22/22 - Bug 33244220: mock
#                           clubonding.is_static_monitoring_bridge_supported()
#    dekuckre    01/05/22 - Creation
#
import json
import unittest
from unittest import mock
import hashlib
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.cluelasticcompute import *
from exabox.core.Context import get_gcontext
from exabox.ovm.cludbaas import ebCluDbaas
from exabox.ovm.clunetworkdetect import ebDiscoverOEDANetwork
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, Mock
import warnings
import warnings
import shutil
import uuid
import os, re
import copy

RESHAPE_CONF = {'ADD_COMPUTES': ({'dom0': {'hostname': 'iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com', 'rack_num': 1, 'uloc': '17', 'priv1': {'fqdn': 'iad103716exdd017-priv1.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '192.168.132.4'}, 'priv2': {'fqdn': 'iad103716exdd017-priv2.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '192.168.132.5'}, 'admin': {'fqdn': 'iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com', 'gateway': '10.0.7.129', 'ipaddr': '10.0.7.146', 'netmask': '255.255.255.128'}, 'ilom': {'fqdn': 'iad103716exdd017lo.iad103716exd.adminiad1.oraclevcn.com', 'gateway': '10.0.7.129', 'ipaddr': '10.0.7.164', 'netmask': '255.255.255.128'}}, 'domU': {'hostname': 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com', 'priv1': {'fqdn': 'iad103716exddu1701-stre0.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.123.16'}, 'priv2': {'fqdn': 'iad103716exddu1701-stre1.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.123.17'}, 'admin': {'fqdn': 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com'}, 'client': {'fqdn': 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com', 'gateway': '10.0.0.1', 'ipaddr': '10.0.0.84', 'mac': '00:10:C9:C8:D4:CA', 'natdomain': 'iad103716exd.adminiad1.oraclevcn.com', 'nathostname': 'iad103716exddu1701', 'natip': '10.0.7.191', 'natnetmask': '255.255.255.128', 'netmask': '255.255.224.0', 'slaves': 'eth1 eth2', 'vlantag': None}, 'backup': {'fqdn': 'iad103716x8mcompexpn17b.backupsubnet.devx8melastic.oraclevcn.com', 'gateway': '10.0.32.1', 'ipaddr': '10.0.32.35', 'mac': '00:00:17:00:52:1A', 'netmask': '255.255.224.0', 'slaves': 'eth1 eth2', 'vlantag': '1'}, 'interconnect1': {'fqdn': 'iad103716exddu1701-clre0.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.107.181.16'}, 'interconnect2': {'fqdn': 'iad103716exddu1701-clre1.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.107.181.17'}, 'vip': {'fqdn': 'iad103716exddu1701-vip.clientsubnet.devx8melastic.oraclevcn.com', 'ipaddr': '10.0.0.90'}}},), 'DELETE_COMPUTES': (), 'ADD_CELLS': ({'hostname': 'iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com', 'rack_num': 1, 'uloc': 6, 'priv1': {'fqdn': 'iad103712exdcl07-priv1.iad103712exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.30.24'}, 'priv2': {'fqdn': 'iad103712exdcl07-priv2.iad103712exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.30.25'}, 'admin': {'fqdn': 'iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com', 'gateway': '10.0.4.129', 'ipaddr': '10.0.4.136', 'netmask': '255.255.255.128'}, 'ilom': {'fqdn': 'iad103712exdcl07lo.iad103712exd.adminiad1.oraclevcn.com', 'gateway': '10.0.4.129', 'ipaddr': '10.0.4.151', 'netmask': '255.255.255.128'}},), 'DELETE_CELLS': (), "ecra": {"servers": ["10.0.1.112/28"]}}
DELETE_CONF = {'reshaped_node_subset': {'added_computes': [], 'retained_computes': [{'compute_node_alias': 'node-1','compute_node_hostname': 'iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com'}],'removed_computes': [{'compute_node_alias': 'node-2','compute_node_hostname': 'iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'compute_node_virtual_hostname': 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'}],'participating_computes': [{'compute_node_alias': 'node-1','compute_node_hostname': 'iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com'},{'compute_node_alias':'node-2','compute_node_hostname': 'iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com'}],'full_compute_to_virtualcompute_list': [{'compute_node_hostname':'iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com','compute_node_virtual_hostname':'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'},{'compute_node_hostname': 'iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com','compute_node_virtual_hostname': 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'}]}, "ecra": {"servers": ["10.0.1.112/28"]}}

EXASCALE_ADD_NODE_PAYLOAD="""
{
    "rack": {
        "storageType": "XS",
        "system_vault": [
            {
                "name": "xsvlt-19789-sys-image-00",
                "vault_type": "image"
            },
            {
                "name": "xsvlt-19789-sys-backup-00",
                "vault_type": "backup",
                "xsVmBackupRetentionNum": "2"
            }
        ],
        "xsVmBackup": "true",
        "xsVmImage": "true"
    },
    "exascale": {
        "cell_list": [
            "iad103712exdcl04.iad103712exd.adminiad1.oraclevcn.com",
            "iad103712exdcl05.iad103712exd.adminiad1.oraclevcn.com",
            "iad103712exdcl06.iad103712exd.adminiad1.oraclevcn.com"
        ],
        "ctrl_network": {
            "ip": "10.0.163.167",
            "name": "sea2d3cl346c3eae597ad4220beda83f822140dacclu01ers01.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
            "port": "5052"
        },
        "db_vault": {
            "gb_size": "10240",
            "name": "xsvlt-19789-00"
        },
        "exascale_cluster_name": "sea2d3cl346c3eae597ad4220beda83f822140dacclu01ers",
        "host_nodes": [
            {
                "compute_hostname": "iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.254.0",
                "priv1": "iad103716exdd017-priv1",
                "priv2": "iad103716exdd017-priv2",
                "storage_ip1": "192.168.132.4",
                "storage_ip2": "192.168.132.5"
            },
            {
                "compute_hostname": "iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.254.0",
                "priv1": "iad103716exdd015-priv1",
                "priv2": "iad103716exdd015-priv2",
                "storage_ip1": "192.168.132.8",
                "storage_ip2": "192.168.132.9"
            },
            {
                "compute_hostname": "iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.254.0",
                "priv1": "iad103716exdd016-priv1",
                "priv2": "iad103716exdd016-priv2",
                "storage_ip1": "192.168.132.6",
                "storage_ip2": "192.168.132.7"
            }
        ],
        "storage_pool": {
            "gb_size": "122880",
            "name": "hcpool"
        },
        "storage_vlan_id": "131"
    },
    "reshaped_node_subset": {
        "added_computes": [
            {
                "compute_node_alias": "dbserver-3",
                "compute_node_hostname": "iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com",
                "db_info": [],
                "eth0_removed": "False",
                "model": "X10M-2",
                "network_info": {
                    "computenetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com",
                                    "gateway": "10.0.7.129",
                                    "ipaddr": "10.0.7.146",
                                    "master": "eth0",
                                    "netmask": "255.255.255.128"
                                }
                            ]
                        },
                        {
                            "private": [
                                {
                                    "fqdn": "sea201733exdd007-priv1.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                                    "ipaddr": "192.168.132.4"
                                },
                                {
                                    "fqdn": "iad103716exdd017-priv2.iad103716exd.adminiad1.oraclevcn.com",
                                    "ipaddr": "192.168.132.5"
                                }
                            ]
                        },
                        {
                            "ilom": [
                                {
                                    "fqdn": "iad103716exdd017lo.iad103716exd.adminiad1.oraclevcn.com",
                                    "gateway": "10.0.7.129",
                                    "ipaddr": "10.0.7.164",
                                    "netmask": "255.255.255.128"
                                }
                            ]
                        },
                        {
                            "ntp": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        },
                        {
                            "dns": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        }
                    ]
                },
                "rack_info": {
                    "uheight": "1",
                    "uloc": "17"
                },
                "racktype": "1205",
                "virtual_compute_info": {
                    "compute_node_hostname": "iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com",
                    "network_info": {
                        "virtualcomputenetworks": [
                            {
                                "private": [
                                    {
                                        "fqdn": "iad103716exddu1701-stre0.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "100.106.123.16"
                                    },
                                    {
                                        "fqdn": "iad103716exddu1701-stre1.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "100.106.123.17"
                                    }
                                ]
                            },
                            {
                                "admin": [
                                    {
                                        "fqdn": "iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com"
                                    }
                                ]
                            },
                            {
                                "client": [
                                    {
                                        "fqdn": "iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com",
                                        "gateway": "10.0.0.1",
                                        "ipaddr": "10.0.0.84",
                                        "mac": "00:10:C9:C8:D4:CA",
                                        "mtu": "9000",
                                        "natdomain": "iad103716exd.adminiad1.oraclevcn.com",
                                        "nathostname": "iad103716exddu1701",
                                        "natip": "10.0.7.191",
                                        "natnetmask": "255.255.255.128",
                                        "netmask": "255.255.224.0",
                                        "slaves": "eth1 eth2",
                                        "standby_vnic_mac": "00:00:17:01:66:54",
                                        "vlantag": "1"
                                    }
                                ]
                            },
                            {
                                "backup": [
                                    {
                                        "fqdn": "iad103716x8mcompexpn17b.backupsubnet.devx8melastic.oraclevcn.com",
                                        "gateway": "10.0.32.1",
                                        "ipaddr": "10.0.32.35",
                                        "mac": "00:00:17:00:52:1A",
                                        "mtu": "9000",
                                        "netmask": "255.255.224.0",
                                        "slaves": "eth1 eth2",
                                        "standby_vnic_mac": "00:00:17:01:8A:E0",
                                        "vlantag": "2"
                                    }
                                ]
                            },
                            {
                                "interconnect": [
                                    {
                                        "fqdn": "iad103716exddu1701-clre0.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "100.107.181.16"
                                    },
                                    {
                                        "fqdn": "iad103716exddu1701-clre1.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "100.107.181.17"
                                    }
                                ]
                            },
                            {
                                "vip": [
                                    {
                                        "fqdn": "iad103716exddu1701-vip.clientsubnet.devx8melastic.oraclevcn.com",
                                        "ipaddr": "10.0.0.90"
                                    }
                                ]
                            }
                        ]
                    },
                    "vm": {
                        "cores": 2,
                        "gb_memory": 30,
                        "gb_ohsize": 60,
                        "size": "Large"
                    }
                },
                "volumes": []
            }
        ],
        "full_compute_to_virtualcompute_list": [
            {
                "compute_node_hostname": "iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com",
                "compute_node_virtual_hostname": "iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com"
            },
            {
                "compute_node_hostname": "iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com",
                "compute_node_virtual_hostname": "iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com"
            },
            {
                "compute_node_hostname": "iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com",
                "compute_node_virtual_hostname": "iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com"
            }
        ],
        "participating_computes": [
            {
                "compute_node_alias": "dbserver-1",
                "compute_node_hostname": "iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com",
                "eth0_removed": "False",
                "model": "X10M-2",
                "racktype": "1205",
                "volumes": []
            },
            {
                "compute_node_alias": "dbserver-2",
                "compute_node_hostname": "iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com",
                "eth0_removed": "False",
                "model": "X10M-2",
                "racktype": "1205",
                "volumes": []
            },
            {
                "compute_node_alias": "dbserver-3",
                "compute_node_hostname": "iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com",
                "eth0_removed": "False",
                "model": "X10M-2",
                "racktype": "1205",
                "volumes": []
            }
        ],
        "removed_computes": [],
        "retained_computes": [
            {
                "compute_node_alias": "dbserver-1",
                "compute_node_hostname": "iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com",
                "eth0_removed": "False",
                "model": "X10M-2",
                "racktype": "1205",
                "volumes": []
            },
            {
                "compute_node_alias": "dbserver-2",
                "compute_node_hostname": "iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com",
                "eth0_removed": "False",
                "model": "X10M-2",
                "racktype": "1205",
                "volumes": []
            }
        ]
    }
}
"""

cmd1 = "/usr/bin/cat /etc/oratab | /usr/bin/grep '^+ASM.*'"
op1 = "+ASM1:/u01/app/19.0.0.0/grid:N"
cmd2 = "/u01/app/19.0.0.0/grid/bin/crsctl check crs"
op2 = "CRS-4638: Oracle High Availability Services is online"
cmd3 = "/u01/app/19.0.0.0/grid/bin/olsnodes -s -n|grep Active"
op3 = "iad103716x8mcompexpn15c\niad103716x8mcompexpn16c"
cmd4 = "/usr/bin/test -e /etc/chrony.conf"
cmd5 = "/usr/bin/test -e /etc/ntp.conf"
cmd6 = "/usr/bin/cat /etc/resolv.conf | /usr/bin/grep '^nameserver[[:space:]][0-9]' | /usr/bin/awk '{print $2}'"
cmd7 = "/bin/test -e /etc/resolv.conf"
op6 = """['10.246.6.65', '10.231.225.65', '206.223.27.1']"""
cmd8 = "/bin/cat /etc/oratab | /bin/grep '^+ASM.*'"
op8 = "+ASM1:/u01/app/19.0.0.0/grid:N"

authorized_keys="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDpKYpv5MRV4CclcEfqCM22vXKxHEf4/XnnIM0r6R8xn8SIO1g9r3VHIDqbTdkLNz63LLvfj9ORf0e6WOMAUIUTbJJZj6LJVTncT+NKnlhb4JDN8Ri6NlDt04CmGjTkV+RXykc/z8qk7maeA5RtJqExKNhhgaPQwsKE93sDyQsfee0MFoUyxyyOx6/NkuXD3aJj5kCN3kVV1sBW3uWActRl4EP4OnYNO83qtRVJBCIE66BNpxqkiuCSTfEebwPCEuY8rOXUMQv1PNCFSwvlWKamqkQyxePdU9/1VAZmfNxPfVA4fLOt2X/6/hzVq+GUQ6TJWqS/kQb/w2sLxorHkxBh ExaKms EXACLOUD KEY"

qemu_info = """ {
 "virtual-size": 107374182400,
 "filename": "/EXAVMIMAGES/GuestImages/clu01-xv8ni2.client.mvmvcn.oraclevcn.com/u02_extra.img",
 "format": "raw",
 "actual-size": 73048014848,
 "dirty-flag": false
}
"""

DB_INFO = """ {"DbInfo": {"DBs1": {"db_class": "oltp", "tde_kms_config": "no", "console_enabled": "", "db_home": "/u02/app/oracle/product/19.0.0.0/dbhome_1", "db_state": "open", "creg_dbtype": "rac", "pdb_names": ["PDB1"], "domain": "us.oracle.com", "db_version": "19000", "dbOkvWallet": "", "db_unique_name": "DBs1_x88_sea", "db_type": "regular", "nls_language": "AMERICAN", "db_name": "DBs1", "dbKmsKeyOcid": "", "db_edition": "enterprise", "ncharset": "AL16UTF16", "fips_enabled": "false", "dgconfigId": "7c63cfca-e50a-40bd-ac1f-d6f0f29e9a93", "pdb_name": "pdb1", "charset": "AL32UTF8", "nodelist": "scaqar07dv0301 scaqar07dv0401", "agentdbid": "774413f9-9995-4550-ba24-5e2689ecf9e2", "asm": "false", "db_full_version": "19.15.0.0.0", "db_id": "634640963", "is_cdb": "yes", "nls_territory": "AMERICA", "pdb_service_name": "", "ohome_name": "OraHome1"}, "DBs2": {"db_class": "oltp", "tde_kms_config": "no", "console_enabled": "", "db_home": "/u02/app/oracle/product/19.0.0.0/dbhome_1", "db_state": "open", "creg_dbtype": "rac", "pdb_names": ["PDB1"], "domain": "us.oracle.com", "db_version": "19000", "dbOkvWallet": "", "db_unique_name": "DBs2_mfd_sea", "db_type": "regular", "nls_language": "", "db_name": "DBs2", "dbKmsKeyOcid": "", "db_edition": "enterprise", "fips_enabled": "false", "ncharset": "AL16UTF16", "dgconfigId": "6a326e35-0290-4368-ac60-7492a7313646", "pdb_name": "PDB1", "charset": "AL32UTF8", "nodelist": "scaqar07dv0301 scaqar07dv0401", "agentdbid": "d25bd0ed-0d61-44ea-b5e2-7e181da61a9e", "createTime": "01-SEP-22", "asm": "false", "db_full_version": "19.15.0.0.0", "db_id": "1314673571", "is_cdb": "yes", "nls_territory": "", "pdb_service_name": "", "ohome_name": "OraHome1"}}, "Status": "Pass", "Command": "dbinfo", "ErrorCode": "0", "Log": "*** Info fetch operation for ALL cluster DBs succeeded on Node scaqar07dv0401.us.oracle.com"}"""
DB_ID = """{"object": "db", "recovery": "", "status": "Starting", "workflow_id": "", "dbname": "", "outputfile": "/var/opt/oracle/log/dbinfo5b25ed7e-3044-11ed-9090-0010e0fe5fa8_outfile.out", "workflow_enabled": "0", "infofile_loc": "/var/opt/oracle/log/dbinfo5b25ed7e-3044-11ed-9090-0010e0fe5fa8_infofile.out", "pid": "", "id": "3a007759-edcb-41b2-80fd-9911164c1d8e", "operation": "info", "logfile": "/var/opt/oracle/log/dbaasapi/db/info/3a007759-edcb-41b2-80fd-9911164c1d8e.log", "msg": "For security please remove your input file.", "exceptionErrorCodes": "", "progress": "0", "ts": "20220909 06:36:47", "infofile_content": "", "errmsg": "", "perl_proxy_pid": "", "dgObserverResponseDetails": "", "host": "", "jobSpecificDetailsJson": "", "resourceId": "", "action": "get", "creation": "", "start": ""}"""
NODE_INFO = """ {"DBs1": {"db_class": "oltp", "tde_kms_config": "no", "console_enabled": "", "db_home": "/u02/app/oracle/product/19.0.0.0/dbhome_1", "db_state": "open", "creg_dbtype": "rac", "pdb_names": ["PDB1"], "domain": "us.oracle.com", "db_version": "19000", "dbOkvWallet": "", "db_unique_name": "DBs1_x88_sea", "db_type": "regular", "nls_language": "AMERICAN", "db_name": "DBs1", "dbKmsKeyOcid": "", "db_edition": "enterprise", "ncharset": "AL16UTF16", "fips_enabled": "false", "dgconfigId": "7c63cfca-e50a-40bd-ac1f-d6f0f29e9a93", "pdb_name": "pdb1", "charset": "AL32UTF8", "nodelist": "iad103716x8mcompexpn16c", "agentdbid": "774413f9-9995-4550-ba24-5e2689ecf9e2", "asm": "false", "db_full_version": "19.15.0.0.0", "db_id": "634640963", "is_cdb": "yes", "nls_territory": "AMERICA", "pdb_service_name": "", "ohome_name": "OraHome1"}, "DBs2": {"db_class": "oltp", "tde_kms_config": "no", "console_enabled": "", "db_home": "/u02/app/oracle/product/19.0.0.0/dbhome_1", "db_state": "open", "creg_dbtype": "rac", "pdb_names": ["PDB1"], "domain": "us.oracle.com", "db_version": "19000", "dbOkvWallet": "", "db_unique_name": "DBs2_mfd_sea", "db_type": "regular", "nls_language": "", "db_name": "DBs2", "dbKmsKeyOcid": "", "db_edition": "enterprise", "fips_enabled": "false", "ncharset": "AL16UTF16", "dgconfigId": "6a326e35-0290-4368-ac60-7492a7313646", "pdb_name": "PDB1", "charset": "AL32UTF8", "nodelist": "iad103716x8mcompexpn16c", "agentdbid": "d25bd0ed-0d61-44ea-b5e2-7e181da61a9e", "createTime": "01-SEP-22", "asm": "false", "db_full_version": "19.15.0.0.0", "db_id": "1314673571", "is_cdb": "yes", "nls_territory": "", "pdb_service_name": "", "ohome_name": "OraHome1"}}"""
CONFIGURE_NODE = """ {'Status': 'Pass', 'Log': 'dbhome_fetch for ALL cluster DBs succeeded on Node scaqar07dv0105.us.oracle.com', 'dbhome_fetch': {'OraHome4': {'dblist': 'c18c48', 'updatedTime': '1642530209', 'version': '18.15.0.0', 'patch_level': '18.15.0.0.0', 'home_loc': '/u02/app/oracle/product/18.0.0.0/dbhome_2', 'agentdbids': '392e6af6-576a-4547-9e40-66c1a9faa812', 'createTime': '1642530209'}, 'OraHome1': {'dblist': 'c19c0', 'updatedTime': '1642530208', 'version': '18.15.0.0', 'patch_level': '18.15.0.0.0', 'home_loc': '/u02/app/oracle/product/18.0.0.0/dbhome_1', 'agentdbids': '45313a1b-627a-4002-8f60-b81921053c0e', 'createTime': '1642530208'}, 'OraHome2': {'dblist': 'c12279', 'updatedTime': '1642530207', 'version': '12.2.0.1', 'patch_level': '12.2.0.1.210720', 'home_loc': '/u02/app/oracle/product/12.2.0/dbhome_1', 'agentdbids': '40ec8822-7b55-44c4-a0e0-cc046cc6ac4f', 'createTime': '1642530207'}, 'OraHome3': {'dblist': 'c12145', 'updatedTime': '1642530210', 'version': '12.1.0.2', 'patch_level': '12.1.0.2.210720', 'home_loc': '/u02/app/oracle/product/12.1.0/dbhome_1', 'agentdbids': '4cc0b141-b6c8-43a7-bbcc-913cb0b6354b', 'createTime': '1642530210'}}} """

DELETE_DB = """ { "DBclu01" : {
    "dbName" : "DBclu01", "dbUniqueName" : "DBclu01_6bs_iad", "dbDomain" : "oadtclient.oadtmichelvcn.oraclevcn.com", "dbRole" : "PRIMARY", "dbType" : "RAC",
    "dbNodeLevelDetails" : { 
    "iad103716x8mcompexpn15c" : { "nodeName" : "iad103716x8mcompexpn15c", "instanceName" : "DBclu012", "version" : "19.22.0.0.0", "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_1", "status" : "OPEN"},
    "iad103716x8mcompexpn17c" : { "nodeName" : "iad103716x8mcompexpn17c", "instanceName" : "DBclu011", "version" : "19.22.0.0.0", "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_1", "status" : "OPEN"}}}
}
"""

class testOptions(object): pass


class MockCluDbaas(object):
    def __init__(self, aExaBoxCluCtrl, aOptions):
        self.__ebox = aExaBoxCluCtrl
        ebLogInfo("Mock MockCluDbaas:__init__ Invoked")

    def mClusterDbaas(self, aOptions, aCmd, aDbaasdata=None):
        ebLogInfo("Mock MockCluDbaas:mClusterDbaas Invoked")
        global _dbaas_data
        _json_object = json.dumps(DB_INFO)
        _dbaas_data = copy.deepcopy(json.loads(_json_object))
        aDbaasdata = _dbaas_data

        ebLogInfo(f"aDbaasdata:{aDbaasdata}")
        return 0


class ebTestCluElasticComp(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluElasticComp, self).setUpClass(aGenerateDatabase = True, aUseOeda = True, isElasticOperation="add_compute")
        self.mGetClubox(self).mSetUt(True)
        warnings.filterwarnings("ignore")

    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU")
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateOEDAProperties')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsIsUp')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetU02Size')
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetNodeU02Size")
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mPatchXML")
    @patch("exabox.tools.oedacli.ebOedacli.run_oedacli")
    def test_mAddNode_OSTP_PREVM_INSTALL(self, mock_setsrc, mock_oradb, mock_properties, mock_shared, mock_crs, mock_hostname, mock_setu02size, mock_getu02size, mock_xml, mock_runoedacli):

        ebLogInfo("Running unit test on cluelasticcompute.py:mAddNode:OSTP_PREVM_INSTALL")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "OSTP_PREVM_INSTALL"

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/usr/local/bin/imageinfo *", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                    ],
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("test -e /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("mv /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.img", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("test -e /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("mv /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.img", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                    ],
                    []
                ],
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("sed.*es.properties", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("cp.*", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("ping*", aRc=0, aStdout=""),
                        exaMockCommand("ping*", aRc=1, aStdout="", aPersist=True),
                    ]
                ]
            }                                        

        self.mPrepareMockCommands(_cmds)
        _reshape_obj = ebCluReshapeCompute( self.mGetClubox(), fullOptions)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            _reshape_obj.mSetSrcDom0(_dom0)
            _reshape_obj.mSetSrcDomU(_domU)
            break

        # This method in intended to test only until mAddDomU method
        # after that the connectivy change will fail
        try:
            _reshape_obj.mAddNode(fullOptions)
        except Exception as e:
            self.assertTrue("Connectivity checks" or "mConnectivityChecks" in str(e))

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsIsUp')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAddUserDomU')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRotateVmKeys')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateDepFiles')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateOEDAProperties')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAddPostVMInstallSteps')
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mBuildClusterDir")
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU")
    def test_mAddNode_OSTP_POSTVM_INSTALL(self, mock_mGetOracleBaseDirectories, mock_mCheckCrsIsUp, mock_mAddUserDomU,
            mock_mRotateVmKeys, mock_mUpdateDepFiles, mock_mUpdateOEDAProperties, mock_mCheckSharedEnvironment, mock_mAddPostVMInstallSteps,
            mock_mBuildClusterDir, mock_mSetSrcDom0DomU, mock_clusterName):

        ebLogInfo("Running unit test on cluelasticcompute.py:mAddNode:OSTP_POSTVM_INSTALL")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "OSTP_POSTVM_INSTALL"
        _reshape_obj = ebCluReshapeCompute( self.mGetClubox(), fullOptions)

        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mHasNatAndCustomerNet', return_value=False),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=True),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mProcessSELinuxUpdate', return_value=0),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetImageVersion', return_value="23.1.15.0.0.240605"),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveXMLClusterConfiguration', return_value=True):
             _return_code = _reshape_obj.mAddNode(fullOptions)

        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mHasNatAndCustomerNet', return_value=False),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=True),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mProcessSELinuxUpdate', side_effect=ExacloudRuntimeError(0x0121, 0xA, "Failed to process SELinux update.")),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetImageVersion', return_value="23.1.15.0.0.240605"),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveXMLClusterConfiguration', return_value=True):
             _return_code = _reshape_obj.mAddNode(fullOptions)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsIsUp')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAddUserDomU')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRotateVmKeys')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateDepFiles')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateOEDAProperties')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAddPostVMInstallSteps')
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mBuildClusterDir")
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU")
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mUpdateRPM")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mAddPostGINIDSteps")
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mIsMulticloud", return_value=(False, None))
    @patch("exabox.ovm.cluelasticcompute.mUpdateListenerPort")
    @patch("exabox.ovm.csstep.cs_util.csUtil.mInstallAhfonDomU")
    def test_mAddNode_OSTP_POSTGINID(self, mock_mGetOracleBaseDirectories, mock_mCheckCrsIsUp, mock_mAddUserDomU,
            mock_mRotateVmKeys, mock_mUpdateDepFiles, mock_mUpdateOEDAProperties, mock_mCheckSharedEnvironment, mock_mAddPostVMInstallSteps,
            mock_mBuildClusterDir, mock_mSetSrcDom0DomU, mock_clusterName, mock_mUpdateRPM, mock_mAddPostGINIDSteps, mock_mIsMulticloud, mock_mUpdateListenerPort, mock_mInstallAhfonDomU):

        ebLogInfo("Running unit test on cluelasticcompute.py:mAddNode:OSTP_POSTGI_NID")


        _cmds = {
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/bin/ls *", aRc=1, aPersist=True),
                        exaMockCommand("/usr/bin/sudo -u oracle /bin/scp*"),
                        exaMockCommand("/usr/bin/chmod -R 775 /u01/app/grid/diag/crs*")
                    ],
                    [
                        exaMockCommand("/bin/ls *", aRc=1, aPersist=True),
                        exaMockCommand("/usr/bin/sudo -u oracle /bin/scp*"),
                        exaMockCommand("/usr/bin/chmod -R 775 /u01/app/grid/diag/crs*")
                    ],
                    [
                        exaMockCommand("/bin/ls *", aRc=1, aPersist=True),
                        exaMockCommand("/usr/bin/sudo -u oracle /bin/scp*"),
                        exaMockCommand("/usr/bin/chmod -R 775 /u01/app/grid/diag/crs*")
                    ]
                ]
            }

        self.mPrepareMockCommands(_cmds)

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "OSTP_POSTGI_NID"
        _reshape_obj = ebCluReshapeCompute( self.mGetClubox(), fullOptions)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            _reshape_obj.mSetSrcDom0(_dom0)
            _reshape_obj.mSetSrcDomU(_domU)
            break

        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mHasNatAndCustomerNet', return_value=False),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=True),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mProcessSELinuxUpdate', return_value=0),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetImageVersion', return_value="23.1.15.0.0.240605"),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveXMLClusterConfiguration', return_value=True),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.IsZdlraProv', return_value=True):
             _return_code = _reshape_obj.mAddNode(fullOptions)


    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mInstallVMbackup")
    def test_mConfigureVMBackup(self, mock_installVMbackup, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mConfigureVMBackup")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [                        
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True) 
                    ]                                                      
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/mkdir -p /opt/oracle/vmbackup/conf/", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/scp vmbackup.conf /opt/oracle/vmbackup/conf/", aRc=0, aStdout="", aPersist=True)
                    ]
                ],
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/rm vmbackup.conf", aRc=0, aStdout="", aPersist=True)
                    ]
                ]
                }                                        
        self.mPrepareMockCommands(_cmds)
        mock_installVMbackup.side_effect = None
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())  
        _obj.mConfigureVMBackup(self.mGetClubox().mGetArgsOptions(), 'iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', ['iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com'])
        ebLogInfo("Unit test on cluelasticcompute.py:mConfigureVMBackup successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mCopyResolvConf(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mCopyResolvConf")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [                        
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand(re.escape(cmd7), aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/chown -f root:root /etc/resolv.conf", aRc=0, aStdout="" ,aPersist=True),
                        
                        
                    ],
                    [                        
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand(re.escape(cmd7), aRc=0, aPersist=True),
                        
                    ]                                                      
                ],
                
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/rm -f *", aRc=0, aStdout="" ,aPersist=True),
                       
                    ]
                ]
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())  
        _obj.mCopyResolvConf('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com', ['iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'])
        ebLogInfo("Unit test on cluelasticcompute.py:mCopyResolvConf successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mBuildClusterDirP01(self, mock_mGetOracleBaseDirectories):
       
        ebLogInfo("Running unit test on cluelasticcompute.py:mBuildClusterDirP01")
        _cmds = {
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2 ,aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3 ,aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        
        clusterId = self.mGetClubox().mGetClusters().mGetClusters()[0]

        self.mGetClubox().mSetDomUsDom0s(clusterId, _ddp)
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        self.assertEqual(_obj.mBuildClusterDir(self.mGetClubox().mReturnDom0DomUPair()), \
        "iad103716x8mcompexpn15ciad103716x8mcompexpn16c")                            
        ebLogInfo("Unit test on cluelasticcompute.py:mBuildClusterDirP01 successful.")                                           

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mAddCheckClusterAsm(self, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mAddCheckClusterAsm")
        _cmds = {
                self.mGetRegexVm():
                [
                     [                        
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True) 
                     ],                                                       
                     [
                         exaMockCommand("export ORACLE_HOME=/u01/app/19.0.0.0/grid; /u01/app/19.0.0.0/grid//bin/lsnrctl services | grep", aRc=0, aStdout="", aPersist=True)
                     ]
                ]
                }
        self.mPrepareMockCommands(_cmds)                     
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj.mAddCheckClusterAsm(self.mGetClubox().mGetArgsOptions(), 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com', '/u01/app/19.0.0.0/grid/')

        ebLogInfo("Unit test on cluelasticcompute.py:mAddCheckClusterAsm successful.")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_initReshapeConf(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:initReshapeConf")
        _cmds = {
                self.mGetRegexVm():
                [
                     [                        
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True) 
                     ]                                                       
                ]
                }
        self.mPrepareMockCommands(_cmds)                     
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj.initReshapeConf(self.mGetClubox().mGetArgsOptions())

        ebLogInfo("Unit test on cluelasticcompute.py:initReshapeConf successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mValidateReshapePayload(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mValidateReshapePayload")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                            
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True) 
                     ]
                ]
                }
        self.mPrepareMockCommands(_cmds)     

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())        
        _obj.mValidateReshapePayload(self.mGetClubox().mGetArgsOptions()) 
        
        ebLogInfo("Unit test on cluelasticcompute.py:mValidateReshapePayload successful")

    def test_mGetNtpConf(self):
        ebLogInfo("Running unit test on cluelasticcompute.py:mGetNtpConf")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand(re.escape(cmd4), aRc=0, aPersist=True),
                         exaMockCommand(re.escape(cmd5), aRc=0, aPersist=True),
                     ],
                     [
                         exaMockCommand(re.escape(cmd4), aRc=0, aPersist=True),
                         exaMockCommand(re.escape(cmd5), aRc=1, aPersist=True),
                     ]
                     
                ]
                }
        self.mPrepareMockCommands(_cmds)     
        try:
            _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())       
            _obj.mGetNtpConf('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com')
        except:
            ebLogInfo("Exception Caught..")

        ebLogInfo("Unit test on cluelasticcompute.py:mGetNtpConf successful")
        
    def test_mGetDomUDnsIP(self):
        ebLogInfo("Running unit test on cluelasticcompute.py:mGetDomUDnsIP")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand(re.escape(cmd6), aRc=0, aStdout=op6, aPersist=True),
                     ],
                     [
                         exaMockCommand(re.escape(cmd6), aRc=1, aStdout=op6, aPersist=True),
                     ]
                ]
                }
        self.mPrepareMockCommands(_cmds)     
        try:
            _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())       
            _obj.mGetDomUDnsIP('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com')
        except:
            ebLogInfo("Exception Caught..")

        ebLogInfo("Unit test on cluelasticcompute.py:mGetDomUDnsIP successful")
        
    def test_mGetDomUNtpIP(self):
        ebLogInfo("Running unit test on cluelasticcompute.py:mGetDomUNtpIP")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                     ],
                     [
                         exaMockCommand(re.escape(cmd6), aRc=1, aStdout=op6, aPersist=True),
                     ]
                ]
                }
        self.mPrepareMockCommands(_cmds)     
        try:
            _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())       
            _obj.mGetDomUDnsIP('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com')
        except:
            ebLogInfo("Exception Caught..")

        ebLogInfo("Unit test on cluelasticcompute.py:mGetDomUNtpIP successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mDisplayDomUDnsNtpConfig(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mDisplayDomUDnsNtpConfig")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                     ]
                ]
                }
        self.mPrepareMockCommands(_cmds)     
        
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())       
        _obj.mDisplayDomUDnsNtpConfig('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com')

        ebLogInfo("Unit test on cluelasticcompute.py:mDisplayDomUDnsNtpConfig successful")
    

    def test_mPatchXML(self):
        ebLogInfo("Running unit test on cluelasticcompute.py:mPatchXML")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                            
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                          exaMockCommand("/bin/timedatectl | grep 'Time zone:'", aRc=0, aStdout="       Time zone: UTC(PST, -0800)" ,aPersist=True)
                     ],
                     [
                         exaMockCommand("/bin/timedatectl | grep 'Time zone:'", aRc=0, aStdout="       Time zone: UTC(PST, -0800)" ,aPersist=True)
                     ],
                     [
                         exaMockCommand(re.escape(cmd4), aRc=0, aPersist=True),
                         exaMockCommand(re.escape(cmd5), aRc=0, aPersist=True)
                     ]
                ]
                }
        self.mPrepareMockCommands(_cmds)     
        try:
            _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())       
            _obj.mPatchXML('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com')
        except:
            ebLogInfo("Exception Caught..")
        ebLogInfo("Unit test on cluelasticcompute.py:mPatchXML successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mUpgradeSystemImage(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mUpgradeSystemImage")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True)                                               
                     ]
                ],
                self.mGetRegexDom0():
                [
                     [
                         exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.img", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ]
                } 
        self.mPrepareMockCommands(_cmds)                                  
                  
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())         
        
        _obj.mUpgradeSystemImage('20.1.12.0.0.210901', 'iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com')
        ebLogInfo("Unit test on cluelasticcompute.py:mUpgradeSystemImage successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mPatchPrivNames(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mPatchPrivNames")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [
                     exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                     exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                     exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True)                                               
                     ] 
                ] 
                } 
        self.mPrepareMockCommands(_cmds)                                  
                  
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions()) 
        _obj.mPatchPrivNames(_obj.mGetReshapeConf())
        ebLogInfo("Unit test on cluelasticcompute.py:mPatchPrivNames successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mUpdateRPM(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mUpdateRPM")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [            
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("/bin/hostname --fqdn", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand("/bin/rpm -qi dbaastools_exa | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa*.rpm"), aRc=0, aStdout="/u02/opt/dbaas_images/dbaastools_exa_main.rpm" ,aPersist=True),
                         exaMockCommand("/bin/rpm -qpi /u02/opt/dbaas_images/dbaastools_exa_main.rpm | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                         exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_main.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("bin/rpm --force -Uhv /u02/opt/dbaas_images/dbaastools_exa_main.rpm", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/libkmstdepkcs11.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                     ],
                     [
                         exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_main.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/rpm --force -Uhv /u02/opt/dbaas_images/dbaastools_exa_main.rpm", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/hostname --fqdn", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand("/bin/rpm -qi dbaastools_exa | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa*.rpm"), aRc=0, aStdout="/u02/opt/dbaas_images/dbaastools_exa_main.rpm" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                         exaMockCommand("/bin/rpm --force -Uhv", aRc=0, aPersist=True),
                         exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0),
                         exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=0),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls -lrt /var/opt/oracle/dbaas_acfs"), aRc=0, aStdout="some files" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                     ],
                     [
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                         exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0),
                         exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=0),
                         exaMockCommand("/bin/rpm --force -Uhv", aRc=0, aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape('/usr/bin/su - oracle -c "/bin/scp /u02/opt/dbaas_images/kmstdecli.rpm oracle@iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com:/u02/opt/dbaas_images/kmstdecli.rpm"'), aRc=1, aStdout="" ,aPersist=True),
                     ],
                     [
                         exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_main.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="", aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/libkmstdepkcs11.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                     ]
                ] 
                } 
        self.mPrepareMockCommands(_cmds)                                  
                  
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions()) 
        _obj.mUpdateRPM('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com', 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com')

        ebLogInfo("Unit test on cluelasticcompute.py:mUpdateRPM successful")
        
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mUpdateRPM_multiclud_rpm(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mUpdateRPM")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [            
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("/bin/hostname --fqdn", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand("/bin/rpm -qi dbaastools_exa | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                         exaMockCommand("/bin/rpm -qi dbaastools_exa_azure_main | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa*.rpm"), aRc=0, aStdout="/u02/opt/dbaas_images/dbaastools_exa_main.rpm" ,aPersist=True),
                         exaMockCommand("/bin/rpm -qpi /u02/opt/dbaas_images/dbaastools_exa_main.rpm | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                         exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_main.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("bin/rpm --force -Uhv /u02/opt/dbaas_images/dbaastools_exa_main.rpm", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/libkmstdepkcs11.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_azure_main-24.3.1-1.el8.x86_64.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/rpm --force -Uhv /u02/opt/dbaas_images/dbaastools_exa_azure_main-24.3.1-1.el8.x86_64.rpm"), aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [
                         exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_main.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/rpm --force -Uhv /u02/opt/dbaas_images/dbaastools_exa_main.rpm", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/hostname --fqdn", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand("/bin/rpm -qi dbaastools_exa | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa*.rpm"), aRc=0, aStdout="/u02/opt/dbaas_images/dbaastools_exa_main.rpm" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                         exaMockCommand("/bin/rpm --force -Uhv", aRc=0, aPersist=True),
                         exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0),
                         exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=0),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls -lrt /var/opt/oracle/dbaas_acfs"), aRc=0, aStdout="some files" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa_azure_main.rpm*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa_azure_main*.rpm"), aRc=1, aStdout='/u02/opt/dbaas_images/dbaastools_exa_azure_main-24.3.1-1.el8.x86_64.rpm\n' ,aPersist=True)
                         
                     ],
                     [
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                         exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0),
                         exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=0),
                         exaMockCommand("/bin/rpm --force -Uhv", aRc=0, aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape('/usr/bin/su - oracle -c "/bin/scp /u02/opt/dbaas_images/kmstdecli.rpm oracle@iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com:/u02/opt/dbaas_images/kmstdecli.rpm"'), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/hostname --fqdn", aRc=0, aPersist=True)
                         
                     ],
                     [
                         exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_main.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="", aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/libkmstdepkcs11.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                     ]
                ] 
                } 
        self.mPrepareMockCommands(_cmds)                                  
                  
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _options = self.mGetClubox().mGetOptions()
        _options.jsonconf['location'] = {}
        _options.jsonconf['location']["dbaastoolsrpm"] = 'dbaastools_exa_azure_main.rpm'
        _options.jsonconf['location']["dbaastoolsrpm_checksum"] = 'abc'
        _obj.mUpdateRPM('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com', 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com', _options)

        ebLogInfo("Unit test on cluelasticcompute.py:mUpdateRPM successful")
        
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mUpdateRPM_multicloud(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mUpdateRPM")
        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [            
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand("/bin/hostname --fqdn", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                        exaMockCommand("/bin/rpm -qi dbaastools_exa | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa*.rpm"), aRc=0, aStdout="/u02/opt/dbaas_images/dbaastools_exa_main.rpm" ,aPersist=True),
                        exaMockCommand("/bin/rpm -qpi /u02/opt/dbaas_images/dbaastools_exa_main.rpm | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                        exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_main.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("bin/rpm --force -Uhv /u02/opt/dbaas_images/dbaastools_exa_main.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=0, aStdout="/u02/app_acfs/dbmulticloud-dataplane-integ-24.1.63.0.0-250217.1504.x86_64.rpm" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=0, aStdout="/u02/app_acfs/pkcs-multicloud-driver-maz.rpm" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/libkmstdepkcs11.rpm"), aRc=1, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_main.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rpm --force -Uhv /u02/opt/dbaas_images/dbaastools_exa_main.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/hostname --fqdn", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                        exaMockCommand("/bin/rpm -qi dbaastools_exa | grep Release", aRc=0, aStdout="Release     : 1+21.4.1.1.0_211221.0003" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa*.rpm"), aRc=0, aStdout="/u02/opt/dbaas_images/dbaastools_exa_main.rpm" ,aPersist=True),
                        exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                        exaMockCommand("/bin/rpm --force -Uhv", aRc=0, aPersist=True),
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=0, aStdout="/u02/app_acfs/dbmulticloud-dataplane-integ-24.1.63.0.0-250217.1504.x86_64.rpm" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=0, aStdout="/u02/app_acfs/pkcs-multicloud-driver-maz.rpm" ,aPersist=True),
                        exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0),
                        exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=0),
                        exaMockCommand(re.escape("/bin/ls -lrt /var/opt/oracle/dbaas_acfs"), aRc=0, aStdout="some files" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=0, aStdout="/u02/app_acfs/dbmulticloud-dataplane-integ-24.1.63.0.0-250217.1504.x86_64.rpm" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=0, aStdout="/u02/app_acfs/pkcs-multicloud-driver-maz.rpm" ,aPersist=True),
                        exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                        exaMockCommand("/bin/rpm --force -Uhv", aRc=0, aPersist=True),
                        exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=0, aPersist=True),
                        exaMockCommand(re.escape("dbaascli admin updateMCKMS --nodelist iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com --keystoreProvider AZURE --extendNodes"), aRc=0, aStdout=""),
                        exaMockCommand(re.escape("dbaascli admin updateMCDP --nodelist iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com --extendNodes"), aRc=0, aStdout=""),
                        exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                        exaMockCommand(re.escape('/usr/bin/su - oracle -c "/bin/scp /u02/opt/dbaas_images/kmstdecli.rpm oracle@iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com:/u02/opt/dbaas_images/kmstdecli.rpm"'), aRc=1, aStdout="" ,aPersist=True),
                    ],
                    [
                         exaMockCommand(re.escape("sudo -u oracle rsync oracle@iad103716x8mcompexpn15c:/u02/opt/dbaas_images/dbaastools_exa_main.rpm /u02/opt/dbaas_images/"), aRc=0, aStdout="", aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/libkmstdepkcs11.rpm"), aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm"), aRc=1, aStdout="" ,aPersist=True),
                     ]
                ] 
                } 
        self.mPrepareMockCommands(_cmds)                                  
                  
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions()) 
        _obj.mUpdateRPM('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com', 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com')

        ebLogInfo("Unit test on cluelasticcompute.py:mUpdateRPM successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mSetOraBaseDirectories(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mSetOraBaseDirectories")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [            
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chown *", aRc=0, aStdout="" ,aPersist=True),
                     ],
                     [
                         exaMockCommand("/bin/test -e *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chown *", aRc=0, aStdout="" ,aPersist=True),

                     ]
                ] 
                } 
        self.mPrepareMockCommands(_cmds)  

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj.mSetOraBaseDirectories(aNewDomU="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com", aGridHome="/u02/app/19.13.0.0/gridHome2", aOraBase="/u02/app/grid19")

        ebLogInfo("Unit test on cluelasticcompute.py:mSetOraBaseDirectories successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetScanPropertyFalseOeda")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mAddEcraNatOnDomU")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mExecuteEndStep")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mUpdateRequestData")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mAddDBHomes")
    @mock.patch("exabox.ovm.cluexaccsecrets.ebExaCCSecrets.mPushExacliPasswdToDomUs")
    @mock.patch("exabox.ovm.csstep.cs_util.csUtil.mInstallAhfonDomU")
    @mock.patch("exabox.ovm.clumisc.ebMigrateUsersUtil.mExecuteRemap")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mAddPostGINIDSteps")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mAddPostGIInstallSteps")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mConfigurePasswordLessDomU")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateDBGIBPL")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchSSHDConfig")
    @mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mPrevmSetupIptables")
    @mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mSetIpTablesExaBM")
    @mock.patch("exabox.ovm.cluelasticcompute.OedacliCmdMgr.mBuildMultipleGuests")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mParallelFileLoad")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mAddPreVMInstallSteps")
    @mock.patch("exabox.ovm.cluelasticcompute.OedacliCmdMgr.mAddDomU")
    @mock.patch("exabox.ovm.cluelasticcompute.OedacliCmdMgr.mAddDom0")
    # @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mAddSecscanSshd")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment")
    @mock.patch("exabox.ovm.clubonding.is_static_monitoring_bridge_supported")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteProfileClusterCheck")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSysPassword")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateOedaUserPswd")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mCallBack")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mMoveAhfDataDir")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0PostVMCreateNetConfig")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mExecuteOEDACLIDoStep")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mUpdateHugePages")
    @mock.patch("exabox.ovm.clumisc.ebCluPreChecks.mConnectivityChecks", return_value=True)
    @mock.patch("exabox.ovm.cluserialconsole.serialConsole.mRestartContainer")
    @mock.patch("exabox.ovm.cluserialconsole.serialConsole.mRunContainer")
    def test_mAddNode(self, mock_mSetScanPropertyFalseOeda, mock_dom0, mock_domU, mock_preVM, mock_fileLoad, mock_buildGuests, mock_setIptables, 
                mock_prevmIptables, mock_pathSSHDconfig, mock_updateDBGIBPL, mock_configurePswd, mock_postGIinstall, 
                mock_postGInid, mock_rempaUsergroup, mock_ahf, mock_pushExaclipswd, mock_addDBhomes, mock_updateReqdata, 
                mock_endStep, mock_addecraNatonDomU, mock_sharedEnv,
                mock_is_static_monitoring_bridge_supported, mock_clustercheck, mock_mGetSysPassword,
                mock_mUpdateOedaUserPswd,mock_mCallBack, mock_mMoveAhfDataDir, mock_mDom0PostVMCreateNetConfig, mock_dostep, mock_hugepages, mock_mConnectivityChecks,
                mock_restartContainer, mock_runContainer, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mAddNode")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [   #0         
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("chmod *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("grep \"^PasswordAuthentication\" /etc/ssh/sshd_config")),
                         exaMockCommand(re.escape("grep \"^PermitRootLogin\" /etc/ssh/sshd_config")),
                         exaMockCommand(re.escape("grep \"^PubkeyAuthentication\" /etc/ssh/sshd_config")),
                         exaMockCommand(re.escape("grep \"OEDA_PUB\" .ssh/authorized_keys")),
                         exaMockCommand(re.escape("/bin/cat /etc/ssh/sshd_config")),
                         exaMockCommand(re.escape("/usr/bin/passwd -l root")),
                         exaMockCommand(re.escape("service sshd restart"))
                         
                     ],
                     [ #1
                         exaMockCommand("/bin/test -e *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chown *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/local/bin/imageinfo *", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check cluster | grep -c online | grep -w 3", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape('/u01/app/19.0.0.0/grid/bin/crsctl query css votedisk | grep "Located 5 voting disk"'), aRc=0, aStdout="" ,aPersist=True),

                     ],
                     [ #2
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check cluster | grep -c online | grep -w 3", aRc=0, aStdout="" ,aPersist=True)

                     ],
                     [ #3
                         exaMockCommand(re.escape("/usr/local/bin/imageinfo *"), aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("mkdir -p /root/.ssh"), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("chmod 600 /root/.ssh/authorized_keys"), aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [ #4
                         exaMockCommand("/bin/timedatectl | grep 'Time zone:'", aRc=0, aStdout="Time zone: UTC (UTC, +0000)" ,aPersist=True),
                         exaMockCommand("numactl --hardware *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/usr/local/bin/imageinfo -version"), aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True)
                         
                     ],
                     [ #5
                         exaMockCommand("sh -c *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("mkdir -p .*", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("chmod *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="welcome1" ,aPersist=True),
                         exaMockCommand("/bin/timedatectl | grep 'Time zone:'", aRc=0, aStdout="Time zone: UTC (UTC, +0000)" ,aPersist=True),
                         exaMockCommand(re.escape("/usr/local/bin/imageinfo -version"), aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         
                     ],
                     [ #6

                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                          exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                          exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="welcome1" ,aPersist=True),
                          exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                          exaMockCommand("numactl --hardware *", aRc=1, aStdout="" ,aPersist=True),
                          exaMockCommand("grep *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cat /etc/ssh/sshd_config", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/local/bin/imageinfo *", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand("/usr/bin/passwd -l root ; service sshd restart", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /etc/chrony.conf"), aRc=0, aPersist=True),
                         exaMockCommand(re.escape("/bin/test -e /etc/ntp.conf"), aRc=0, aPersist=True)
                         
                     ],
                     [ #7
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand("grep *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("sed *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e /u01/app/19.0.0.0/grid/oracle.ahf", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mv /u01/app/19.0.0.0/grid/oracle.ahf /u01/app/grid/oracle.ahf.gihome", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(".*tfactl .*", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mv /u01/app/grid/oracle.ahf.gihome /u01/app/19.0.0.0/grid/oracle.ahf", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e /u01/app/grid/oracle.ahf.gihome", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/local/bin/imageinfo *", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                         exaMockCommand("/bin/hostname --fqdn", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand(re.escape('sh -c'), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/cat /etc/ssh/sshd_config")),
                         exaMockCommand("/usr/bin/passwd -l root ; service sshd restart", aRc=0, aStdout="" ,aPersist=True)
                         
                     ],
                     [ #8
                         exaMockCommand("/usr/sbin/useradd *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("echo *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("mkdir *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("chmod *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("chown *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                         exaMockCommand("/usr/bin/hostname", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand("/usr/bin/hostnamectl set-hostname *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("numactl --hardware *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(".*tfactl .*", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mv *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape('grep "^PermitRootLogin" /etc/ssh/sshd_config'), aRc=0, aStdout="PermitRootLogin without-password" ,aPersist=True),
                         exaMockCommand(re.escape('grep "^PasswordAuthentication" /etc/ssh/sshd_config'), aRc=0, aStdout="PasswordAuthentication no" ,aPersist=True),
                         exaMockCommand(re.escape('grep "^PubkeyAuthentication" /etc/ssh/sshd_config'), aRc=0, aStdout="PubkeyAuthentication yes", aPersist=True),
                         exaMockCommand(re.escape('grep "OEDA_PUB" .ssh/authorized_keys'), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cat /etc/ssh/sshd_config", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/passwd -l root ; service sshd restart", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/sudo -u oracle /bin/scp -r /u01/app/oracle/admin/cprops/cprops_wallet *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/local/bin/imageinfo", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand("/bin/hostname --fqdn", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand("/bin/rpm -qi dbaastools_exa | grep Release", aRc=0, aStdout="Release     : 1+MAIN_220406.1234", aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa*.rpm"), aRc=0, aStdout="/u02/opt/dbaas_images/dbaastools_exa_main.rpm", aPersist=True),
                         exaMockCommand(re.escape("/usr/bin/cat /etc/chrony.conf | /usr/bin/grep '^server[[:space:]][0-9]' | /usr/bin/awk '{print $2}'"), aRc=1, aStdout="", aPersist=True),
                         
                     ],
                     [ #9
                         exaMockCommand("/usr/sbin/useradd *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("echo *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("mkdir *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("chmod *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("chown *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                         exaMockCommand("/usr/bin/hostname", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand("/usr/bin/hostnamectl set-hostname *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("numactl --hardware *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand(".*tfactl .*", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mv *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape('grep "^PermitRootLogin" /etc/ssh/sshd_config'), aRc=0, aStdout="PermitRootLogin without-password" ,aPersist=True),
                         exaMockCommand(re.escape('grep "^PasswordAuthentication" /etc/ssh/sshd_config'), aRc=0, aStdout="PasswordAuthentication no" ,aPersist=True),
                         exaMockCommand(re.escape('grep "^PubkeyAuthentication" /etc/ssh/sshd_config'), aRc=0, aStdout="PubkeyAuthentication yes", aPersist=True),
                         exaMockCommand(re.escape('grep "OEDA_PUB" .ssh/authorized_keys'), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cat /etc/ssh/sshd_config", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/passwd -l root ; service sshd restart", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/sudo -u oracle /bin/scp /var/opt/oracle/cprops/cprops.ini *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/sudo -u oracle /bin/scp -r /u01/app/oracle/admin/cprops/cprops_wallet *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/local/bin/imageinfo", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True)
                     ],
                     [ #10
                         exaMockCommand("/bin/chown *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                          exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                          exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                         exaMockCommand("/bin/chmod *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/bin/mv *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("echo.*", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="welcome1" ,aPersist=True),
                          exaMockCommand("/usr/sbin/useradd -u 2000 -d /home/opc -s /bin/bash opc", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("mkdir -p /home/opc/.ssh", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("chmod 700 /home/opc/.ssh", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("chown opc:opc /home/opc/.ssh", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chown -R `id -u opc`:`id -g opc` /home/opc/.ssh/authorized_keys", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chmod 600 /home/opc/.ssh/authorized_keys", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/opt/exacloud/get_cs_data.py --dataonly", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/sudo -u oracle /bin/scp /var/opt/oracle/cprops/cprops.ini *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/usr/local/bin/imageinfo", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                         
                     ],
                     [ #11
                          exaMockCommand("/bin/su *", aRc=0, aStdout="1234" ,aPersist=True),
                          exaMockCommand("/opt/exacloud/get_cs_data.py *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)

                     ],
                     [ #12
                          exaMockCommand("export ORACLE_HOME*", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/usr/bin/sudo  *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0, aStdout=authorized_keys ,aPersist=True),
                          exaMockCommand("cat /home/oracle/.ssh/authorized_keys", aRc=0, aStdout=authorized_keys ,aPersist=True),
                          exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/sbin/useradd -u 2000 -d /home/opc -s /bin/bash opc", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("echo 'opc ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers"), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("mkdir -p /home/opc/.ssh", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("chmod 700 /home/opc/.ssh", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/sudo -u oracle /bin/scp /var/opt/oracle/cprops/cprops.ini *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("chown opc:opc /home/opc/.ssh", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chown -R `id -u opc`:`id -g opc` /home/opc/.ssh/authorized_keys", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chmod 600 /home/opc/.ssh/authorized_keys", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/opt/exacloud/get_cs_data.py --dataonly", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/hostname --fqdn", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand("/bin/rpm -qi dbaastools_exa | grep Release", aRc=0, aStdout="Release     : 1+MAIN_220406.1234", aPersist=True),
                         exaMockCommand(re.escape("/bin/ls /u02/opt/dbaas_images/dbaastools_exa*.rpm"), aRc=0, aStdout="/u02/opt/dbaas_images/dbaastools_exa_main.rpm", aPersist=True),
                         exaMockCommand("/usr/local/bin/imageinfo", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand(re.escape('grep "^PasswordAuthentication" /etc/ssh/sshd_config'), aRc=0, aStdout="PasswordAuthentication no" ,aPersist=True),
                         exaMockCommand(re.escape('grep "^PermitRootLogin" /etc/ssh/sshd_config'), aRc=0, aStdout="PermitRootLogin without-password" ,aPersist=True),
                         exaMockCommand(re.escape('grep "^PubkeyAuthentication" /etc/ssh/sshd_config'), aRc=0, aStdout="PubkeyAuthentication yes", aPersist=True),
                         exaMockCommand(re.escape('grep "OEDA_PUB" .ssh/authorized_keys'), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cat /etc/ssh/sshd_config", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/passwd -l root ; service sshd restart", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("export ORACLE_HOME*", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [ #13
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [ #14
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [ #15
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [ #16
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [ #17
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [ #18
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [ #19
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [ #20
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ],
                self.mGetRegexDom0():
                [
                     [],
                     [
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/qemu-img info --output=json *", aRc=0, aStdout="""{"virtual-size": 214748364800,"filename": "/EXAVMIMAGES/GuestImages/c3714n5c1.clientmvm.devx8mroce.oraclevcn.com/u02_extra.img",
                                         "format": "raw", "actual-size": 55619366912, "dirty-flag": false}""" ,aPersist=True),
                         exaMockCommand("/sbin/parted /EXAVMIMAGES/GuestImages/iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com/u02_extra.img print", aStdout="Partition Table: msdos", aPersist=True),
                         exaMockCommand("/bin/mv *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("systemctl is-enabled iptables", aRc=0, aStdout="enabled" ,aPersist=True),
                         exaMockCommand("iptables -S *", aRc=0, aStdout="1" ,aPersist=True),
                          exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True)
                       
                     ],
                     [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                        exaMockCommand("/bin/cat /etc/sysconfig/network-scripts/ifcfg-vmbondeth0", aRc=0, aPersist=True),
                         exaMockCommand("systemctl is-enabled *", aRc=0, aStdout="enabled" ,aPersist=True),
                         exaMockCommand("/usr/sbin/ubiosconfig *", aRc=0, aStdout="Enabled" ,aPersist=True),
                         exaMockCommand("/bin/grep -oP *", aRc=0, aStdout="Enabled" ,aPersist=True),
                         exaMockCommand("iptables -S *", aRc=0, aStdout="1" ,aPersist=True),
                          exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e", aRc=0, aStdout="",aPersist=True),
                         exaMockCommand("/bin/qemu-img info", aRc=0, aStdout=qemu_info,aPersist=True)
                     ],
                     [
                          exaMockCommand("/usr/sbin/ubiosconfig *", aRc=0, aStdout="Enabled" ,aPersist=True),
                          exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/bin/grep -oP *", aRc=0, aStdout="Enabled" ,aPersist=True),
                           exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0" ,aPersist=True),
                           exaMockCommand("iptables -S *", aRc=0, aStdout="1" ,aPersist=True),
                          exaMockCommand("/bin/test -e", aRc=0, aStdout="",aPersist=True),
                          exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/bin/qemu-img info", aRc=0, aStdout=qemu_info,aPersist=True)
                     ],
                     [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0" ,aPersist=True),
                        exaMockCommand("xm info | grep free_memory", aRc=0, aStdout="free_memory: 7654050" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                        exaMockCommand("/bin/test -e", aRc=0, aStdout="",aPersist=True),
                        exaMockCommand("/bin/qemu-img info", aRc=0, aStdout=qemu_info,aPersist=True),
                        exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                     ],
                     [
                        exaMockCommand("/bin/cat /etc/sysconfig/network-scripts/ifcfg-vmbondeth0", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /etc/sysconfig/network-scripts/ifcfg-bondeth0", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ifdown vmbondeth0", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ifdown bondeth0", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ifup vmbondeth0", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ifup bondeth0", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ifup eth1", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ifup eth2", aRc=0, aPersist=True),
                         exaMockCommand("xm info | grep free_memory", aRc=0, aStdout="free_memory: 7654050" ,aPersist=True),
                         exaMockCommand("df -h -B G |grep EXAVMIMAGES", aRc=0, aStdout="/dev/mapper/VGExaDb-LVDbExaVMImages     3265G  196G     3069G   6% /EXAVMIMAGES" ,aPersist=True),
                         exaMockCommand("/bin/rm *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e", aRc=0, aStdout="",aPersist=True),
                         exaMockCommand("/bin/qemu-img info", aRc=0, aStdout=qemu_info,aPersist=True)
                     ],
                    [
                         exaMockCommand("xm list", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com" ,aPersist=True),
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("df -h -B G |grep EXAVMIMAGES", aRc=0, aStdout="/dev/mapper/VGExaDb-LVDbExaVMImages     3265G  196G     3069G   6% /EXAVMIMAGES" ,aPersist=True),
                         exaMockCommand("/sbin/ip link show", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ls", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e", aRc=0, aStdout="",aPersist=True),
                         exaMockCommand("/bin/qemu-img info", aRc=0, aStdout=qemu_info,aPersist=True),
                         exaMockCommand("/usr/local/bin/imageinfo *", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                         exaMockCommand("mkdir -p /opt/exacloud/clusters/config", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [
                         exaMockCommand("/sbin/ip link show", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ls", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/local/bin/imageinfo *", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                         exaMockCommand("mkdir -p /opt/exacloud/clusters/config", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [
                         exaMockCommand("/usr/local/bin/imageinfo *", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [                                                                                                                                                       
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)    
                     ],
                     [
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ],
                     [
                         exaMockCommand(".*", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/sed *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ssh-keygen -R *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ]
                } 
        self.mPrepareMockCommands(_cmds)  

        mock_mGetSysPassword = "welcome1!"
        self.mGetClubox().mSetUt(True)
        self.mGetClubox().mSetCmd('vmgi_reshape')
        self.mGetClubox().mSetOciExacc(False)
        get_gcontext().mSetConfigOption('skip_dyn_dep', 'True')
        get_gcontext().mSetConfigOption('secure_ssh_all', 'False')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _patchconfig = self.mGetClubox().mGetConfigPath()
        _oeda_path  = self.mGetClubox().mGetOedaPath()
        ebLogInfo(f"patchconfig:{_patchconfig}")
        _path = _oeda_path + '/exacloud.conf'
        if not os.path.isdir(_path):
            os.makedirs(_path)
        _addnodexml = _oeda_path + '/exacloud.conf/addnode_exatest.xml'
        shutil.copyfile(self.mGetClubox().mGetConfigPath(), _addnodexml)
        self.mGetClubox().mSetPatchConfig(self.mGetClubox().mGetConfigPath())
        with open(os.path.join(self.mGetPath(), "inventory.json"), "r") as _f:
            _inventory = json.loads(_f.read())
        self.mGetClubox().mSetRepoInventory(_inventory)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj.__cb_params =  [self.mGetClubox(), self.mGetClubox().mGetArgsOptions(), ["iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com"]]
        
        mock_dom0.side_effect = None
        mock_domU.side_effect = None
        mock_preVM.side_effect = None
        mock_fileLoad.side_effect = None
        mock_buildGuests.side_effect = None
        mock_setIptables.side_effect = None
        mock_prevmIptables.side_effect = None
        mock_pathSSHDconfig.side_effect = None
        mock_updateDBGIBPL.side_effect = None
        mock_configurePswd.side_effect = None
        mock_postGIinstall.side_effect = None
        mock_postGInid.side_effect = None
        mock_rempaUsergroup.side_effect = None
        mock_ahf.side_effect = None
        mock_pushExaclipswd.side_effect =None
        mock_addDBhomes.side_effect = None
        mock_updateReqdata.side_effect = None
        mock_endStep.side_effect = None
        mock_addecraNatonDomU = None
        mock_addsecsshd = None
        mock_sharedEnv = None
        mock_is_static_monitoring_bridge_supported.side_effects = None
        mock_is_static_monitoring_bridge_supported.return_value = False
        try:
            _obj.mReshapeVMGI(self.mGetClubox().mGetArgsOptions())
        except:
            ebLogInfo(f"Exception Caught")
        self.mGetClubox().mSetConfig(_patchconfig)
        self.mGetClubox().mSetPatchConfig(_patchconfig)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        #update Dom0DomUPair and Dom0DomUNATPair forcefully
        _ddp_nat = self.mGetClubox().mReturnDom0DomUNATPair(True)
        _ddp = self.mGetClubox().mReturnDom0DomUPair(True)
        _host_list = self.mGetClubox().mGetHostList(True)
        self.mGetClubox().mSetUt(False)

        ebLogInfo("Unit test on cluelasticcompute.py:mAddNode successful")

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mUpdateSystemVaultAccess')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mConfigureEDVbackup')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveXMLClusterConfiguration")
    @mock.patch("exabox.ovm.clumisc.ebCluPreChecks.mCheckClusterIntegrity")
    @mock.patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mInstallVMbackup")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetSrcDomU")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetSrcDom0")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSyncPSMKeys")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mStoreDomUInterconnectIps")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveClusterConfiguration")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mConfigureVMBackup")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mPostReshapeValidation")
    def test_mExecuteEndStep(self, mock_saveconfig, mock_clusterChecks, mock_installVMbackup, mock_getSrcDomU, mock_getSrcDom0, mock_sync_keys,\
                             mock_store_ic_ips, mock_save_config, mock_configure_vm_bkp, mock_post_reshape_validation, mock_mGetOracleBaseDirectories, 
                             mock_mConfigureEDVbackup, mock_mUpdateSystemVaultAccess):
        ebLogInfo("Running unit test on cluelasticcompute.py:test_mExecuteEndStep")

        _cmds = { 
                  self.mGetRegexVm():                        
                  [                                          
                      [                                      
                          exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                        
                          exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2 ,aPersist=True),                        
                          exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3 ,aPersist=True),   
                          exaMockCommand("grep -qxF *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("cp /home/opc/.ssh/authorized_keys /home/opc/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0, aStdout=authorized_keys ,aPersist=True)
                      ],                                     
                      [                                      
                          exaMockCommand("cp /home/opc/.ssh/authorized_keys /home/opc/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("cp /home/oracle/.ssh/authorized_keys /home/oracle/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("grep -qxF *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/bin/mv /u01/app/19.0.0.0/grid/oracle.ahf /u01/app/grid/oracle.ahf.gihome", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0, aStdout=authorized_keys ,aPersist=True),
                          exaMockCommand("cat /home/oracle/.ssh/authorized_keys", aRc=0, aStdout=authorized_keys ,aPersist=True),
                      ],
                      [
                          exaMockCommand("cat /home/oracle/.ssh/authorized_keys", aRc=0, aStdout=authorized_keys ,aPersist=True),
                          exaMockCommand("cp /home/oracle/.ssh/authorized_keys /home/oracle/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("cp /home/opc/.ssh/authorized_keys /home/opc/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("grep -qxF *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("cp /root/.ssh/authorized_keys /root/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("cat /root/.ssh/authorized_keys", aRc=0, aStdout=authorized_keys ,aPersist=True),
                      ],
                      [
                          exaMockCommand("cat /root/.ssh/authorized_keys", aRc=0, aStdout=authorized_keys ,aPersist=True),
                          exaMockCommand("cp /root/.ssh/authorized_keys /root/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("cp /home/oracle/.ssh/authorized_keys /home/oracle/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("grep -qxF *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                          exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                          exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                          
                      ],
                      [
                         exaMockCommand("cp /root/.ssh/authorized_keys /root/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("cp /home/oracle/.ssh/authorized_keys /home/oracle/.ssh/authorized_keys.bkup", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("grep -qxF *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes", aRc=0, aStdout="iad103716x8mcompexpn17c", aPersist=True),
                          exaMockCommand("/bin/su *", aRc=0, aStdout="" ,aPersist=True)
                      ],
                      [
                           exaMockCommand("/bin/su *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                          exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                          exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                      ],
                      [
                          exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes", aRc=0, aStdout="iad103716x8mcompexpn15c", aPersist=True),
                          exaMockCommand('/u01/app/19.0.0.0/grid/bin/srvctl config vip -node iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com', aRc=0, aStdout="", aPersist=True)
                      ],
                      [
                          exaMockCommand('/opt/oracle.cellos/host_access_control rootssh -l', aRc=0, aStdout="" ,aPersist=True)
                      ]
                  ],
                self.mGetRegexDom0():
                [
                     [
                        exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),

                     ],
                     [
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aStdout="", aPersist=True),
                     ],
                     [
                         exaMockCommand("/bin/mkdir -p /opt/oracle/vmbackup/conf/", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/scp vmbackup.conf /opt/oracle/vmbackup/conf/", aRc=0, aStdout="", aPersist=True),
                          exaMockCommand("/bin/test *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aStdout="", aPersist=True),
                     ],
                     [
                         exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aStdout="", aPersist=True),
                          exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aStdout="", aPersist=True),
                          exaMockCommand("cp -v *", aRc=0, aStdout="", aPersist=True),
                          exaMockCommand("uname -a  | awk '{print $3}'", aRc=0, aStdout="4.1.12-124.52.4.el6uek.x86_64", aPersist=True),
                     ]
                ],
                self.mGetRegexLocal():                           
                [
                     [
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/rm vmbackup.conf", aRc=0, aStdout="", aPersist=True)
                     ]
                ]
                } 
        self.mPrepareMockCommands(_cmds) 

        mock_getSrcDom0.return_value = "iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com"
        mock_getSrcDomU.return_value = "iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com"
        mock_installVMbackup.side_effect = None
        mock_clusterChecks.side_effect = None
        mock_saveconfig.side_effect = None

        self.mGetClubox().mSetCmd('vmgi_reshape')
        self.mGetClubox().mSetOciExacc(False)
        get_gcontext().mSetConfigOption('skip_dyn_dep', 'True')
        get_gcontext().mSetConfigOption('secure_ssh_all', 'False')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _patchconfig = self.mGetClubox().mGetConfigPath()
        _oeda_path  = self.mGetClubox().mGetOedaPath()
        ebLogInfo(f"patchconfig:{_patchconfig}")
        _path = _oeda_path + '/exacloud.conf'
        if not os.path.isdir(_path):
            os.makedirs(_path)
        _addnodexml = _oeda_path + '/exacloud.conf/addnode_exatest.xml'
        shutil.copyfile(self.mGetClubox().mGetConfigPath(), _addnodexml)
        self.mGetClubox().mSetPatchConfig(self.mGetClubox().mGetConfigPath())

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _obj.mExecuteEndStep(["iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com"], self.mGetClubox().mGetArgsOptions())

        ebLogInfo("Unit test on cluelasticcompute.py:test_mExecuteEndStep successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mRemoveComputePreVMDelete(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveComputePreVMDelete")

        _cmds = { 
                self.mGetRegexVm():                                       
                [
                     [            
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         
                     ],
                     [
                         exaMockCommand("/bin/test -e *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chown *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/var/opt/oracle/ocde/rops set_creg_key *", aRc=0, aStdout="" ,aPersist=True),

                     ]
                ],
                self.mGetRegexDom0():
                [
                     [
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("rm -f *", aRc=0, aStdout="" ,aPersist=True),
                     ]
                ]
                } 
        self.mPrepareMockCommands(_cmds)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        reshape_conf = _obj.mGetReshapeConf()
        reshape_conf['keep_dyndep_cache'] = False

        _obj.mRemoveComputePreVMDelete(["OSTP_PREVM_DELETE"], self.mGetClubox().mGetArgsOptions())

        ebLogInfo("Unit test on cluelasticcompute.py:mRemoveComputePreVMDelete successful") 


    @mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mRemoveSecurityRulesExaBM")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRemoveClusterConfiguration")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRunScript")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetupEbtablesOnDom0")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mDeleteNatIptablesRulesFile")
    @mock.patch("exabox.ovm.csstep.cs_util.csUtil.mRemoveStoragePool")
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU")
    def test_mRemoveComputePostVMDelete(self, mock_secure, mock_clustercfg, mock_runscript, mock_ebtables, mock_natrule, mock_rmstgpool, mock_setsrc):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveComputePostVMDelete")

        _cmds = { 
                self.mGetRegexVm():
                [
                     [
                          exaMockCommand("/var/opt/oracle/ocde/rops set_creg_key *", aRc=0, aStdout="" ,aPersist=True),
                     ]
                ],
                self.mGetRegexDom0():
                [
                     [
                         exaMockCommand(".*dumpxml.*", aRc=0, aStdout="vmeth200", aPersist=True),
                         exaMockCommand(".*test -e.*route.*", aRc=0, aPersist=True),
                         exaMockCommand(".*cat.*vmeth200.*grep", aRc=1, aPersist=True),
                         exaMockCommand(".*cat.*vmeth200", aRc=0, aStdout="10.0.1.35 via 10.1.0.1 dev vmeth0.102 table 100\nx", aPersist=True),
                         exaMockCommand(".*echo.*vmeth200", aRc=0, aPersist=True),
                         exaMockCommand(".*ifdown.*vmeth200.*", aRc=0, aPersist=True),
                         exaMockCommand(".*ifup.*vmeth200.*", aRc=0, aPersist=True),
                     ],
                     [
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("rm -f *", aRc=0, aStdout="" ,aPersist=True),
                     ]
                ],
                self.mGetRegexLocal():
                [
                    [
                         exaMockCommand(".*nslookup.*", aRc=0, aStdout="127.0.0.1", aPersist=True),
                    ]
                ]
                } 
        self.mPrepareMockCommands(_cmds)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        reshape_conf = _obj.mGetReshapeConf()
        reshape_conf['keep_dyndep_cache'] = False

        _jconf = self.mGetClubox().mGetOptions().jsonconf
        _jconf["ecra"] = {"servers": ["10.0.1.112/28", "localhost"]}

        _obj.mRemoveComputePostVMDelete(["OSTP_POSTVM_DELETE"], self.mGetClubox().mGetArgsOptions())

        ebLogInfo("Unit test on cluelasticcompute.py:mRemoveComputePostVMDelete successful") 

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mRemoveNodeFromCRSP01(self, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveComputeGIDelete")

        _vipcmd = '/u01/app/19.0.0.0/grid/bin/srvctl config vip -n iad103716x8mcompexpn16c | grep "VIP Name"'
        _vipout = 'VIP Name: iad103716x8mcompexpn16c-vip.clientsubnet.devx8melastic.oraclevcn.com'
        _cmds = { 
                self.mGetRegexVm():                                      
                [
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716exddu1601/d' /etc/hosts", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716x8mcompexpn16c/d' /etc/hosts", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes -s -t | grep iad103716x8mcompexpn16c", aRc=1, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid", aPersist=True),
                        exaMockCommand(_vipcmd, aRc=0, aStdout=_vipout, aPersist=True),
                        exaMockCommand('/u01/app/19.0.0.0/grid/bin/crsctl unpin css -n iad103716x8mcompexpn16c', aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl stop cluster -n iad103716x8mcompexpn16c",aRc=0, aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl delete node -n iad103716x8mcompexpn16c", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl stop vip -vip iad103716x8mcompexpn16c-vip.clientsubnet.devx8melastic.oraclevcn.com -force", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl remove vip -vip iad103716x8mcompexpn16c-vip.clientsubnet.devx8melastic.oraclevcn.com -force", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes -s -t | grep iad103716x8mcompexpn16c", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716exddu1601/d' /etc/hosts", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716x8mcompexpn16c/d' /etc/hosts", aRc=0, aStdout="", aPersist=True)
                    ],
                    [
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes -s -t | grep iad103716x8mcompexpn16c", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716exddu1601/d' /etc/hosts", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716x8mcompexpn16c/d' /etc/hosts", aRc=0, aStdout="", aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(DELETE_CONF)
        _options.jsonconf = json.loads(_json_object)

        _patchconfig = self.mGetClubox().mGetPatchConfig()
        _oeda_path  = self.mGetClubox().mGetOedaPath()

        _path = _oeda_path + '/exacloud.conf'
        if not os.path.isdir(_path):
            os.makedirs(_path)
        _delnodexml = _oeda_path + '/exacloud.conf/nodesubset_exatest.xml'
        shutil.copyfile(self.mGetClubox().mGetConfigPath(), _delnodexml)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj.mRemoveNodeFromCRS('iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com')

        ebLogInfo("Unit test on cluelasticcompute.py:mRemoveComputeGIDelete successful") 

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mRemoveComputeGIDelete(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveComputeGIDelete")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [            
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         
                     ],
                     [
                         exaMockCommand("/bin/test -e *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chown *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/var/opt/oracle/ocde/rops set_creg_key *", aRc=0, aStdout="" ,aPersist=True),

                     ]
                ],
                self.mGetRegexDom0():
                [
                     [
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("rm -f *", aRc=0, aStdout="" ,aPersist=True),
                     ]
                ]
                } 
        self.mPrepareMockCommands(_cmds) 

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        reshape_conf = _obj.mGetReshapeConf()
        reshape_conf['keep_dyndep_cache'] = False
        _obj.mRemoveComputeGIDelete("OSTP_PREGI_DELETE", ["OSTP_PREGI_DELETE"], self.mGetClubox().mGetArgsOptions())
        _obj.mRemoveComputeGIDelete("OSTP_POSTGI_DELETE", ["OSTP_POSTGI_DELETE"], self.mGetClubox().mGetArgsOptions())

        ebLogInfo("Unit test on cluelasticcompute.py:mRemoveComputeGIDelete successful") 

    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetScanPropertyFalseOeda")
    @mock.patch("exabox.ovm.clucontrol.OedacliCmdMgr.mDelNode")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetDbInfo")
    @mock.patch("exabox.ovm.cluelasticcompute.OedacliCmdMgr.mDeleteClusterNode")
    @mock.patch("exabox.ovm.cluelasticcompute.OedacliCmdMgr.mDeleteDBHomes")
    @mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mRemoveIpTablesExaBM")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteProfileClusterCheck")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mPostReshapeValidation")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mAddNatEgressIPs")
    def test_mDeleteNode(self, mock_mSetScanPropertyFalseOeda, mock_removeIptables, mock_deleteDBHomes, mock_deleteClusterNode, mock_getDbInfo, mock_delNode, mock_sharedEnv, mock_clustercheck, mock_post_validate, mock_add_nat_egress):
        ebLogInfo("Running unit test on cluelasticcompute.py:mDeleteNode")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [            
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),                                              
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),                                              
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="welcome1" ,aPersist=True),
                         
                     ],
                     [
                         exaMockCommand("/bin/test -e *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/chown *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/var/opt/oracle/ocde/rops set_creg_key *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':' "), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                     ],
                     [
                         exaMockCommand(re.escape("ORACLE_HOME=/u01/app/19.0.0.0/grid;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config database"), aRc=0, aStdout="c12145_mfn_sea" ,aPersist=True),
                         exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes *", aRc=1, aStdout="" ,aPersist=True),

                     ],
                     [
                         exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="welcome1" ,aPersist=True),
                         exaMockCommand("/var/opt/oracle/ocde/rops set_creg_key *", aRc=0, aStdout="" ,aPersist=True),
                     ],
                     [
                         exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="welcome1" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u02/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status database -d c12145_mfn_sea"), aRc=0, aStdout="Instance c12145_L0oon1 is running on node iad103716x8mcompexpn15c" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u02/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status service -d c12145_mfn_sea"), aRc=0, aStdout="Service c12145_pdb1.paas.oracle.com is running on instance(s) c12145_L0oon1" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u02/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep 'Preferred instances'"), aRc=0, aStdout="Preferred instances: c12145_L0oon1" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u02/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl modify service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com -modifyconfig -preferred  -available c12145_L0oon1"), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u02/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep -E 'Preferred instances|Available instances'"), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand("su - *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^c12145_mfn_sea.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/oracle/product/18.0.0.0/dbhome_2" ,aPersist=True),
                         exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/srvctl config database -db c12145_mfn_sea"), aRc=0, aStdout="c12145_mfn_sea" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2; $ORACLE_HOME/bin/oraversion -baseVersion"), aStdout="18.0.0.0", aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2; $ORACLE_HOME/bin/orabase"), aStdout="/u01/app/oracle/product/18.0.0.0", aPersist=True),
                         

                     ],
                     [
                         exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status database -d c12145_mfn_sea"), aRc=0, aStdout="Instance c12145_L0oon1 is running on node iad103716x8mcompexpn15c" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status service -d c12145_mfn_sea"), aRc=0, aStdout="Service c12145_pdb1.paas.oracle.com is running on instance(s) c12145_L0oon1" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u02/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep 'Preferred instances'"), aRc=0, aStdout="Preferred instances: c12145_L0oon1" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u02/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl modify service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com -modifyconfig -preferred  -available c12145_L0oon1"), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u02/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep -E 'Preferred instances|Available instances'"), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/su *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status database -d c12145_mfn_sea"), aRc=0, aStdout="Instance c12145_L0oon1 is running on node iad103716x8mcompexpn15c" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status service -d c12145_mfn_sea"), aRc=0, aStdout="Service c12145_pdb1.paas.oracle.com is running on instance(s) c12145_L0oon1" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep 'Preferred instances'"), aRc=0, aStdout="Preferred instances: c12145_L0oon1" ,aPersist=True),
                         exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep -E 'Preferred instances|Available instances'"), aRc=0, aStdout="" ,aPersist=True),
                         
                     ],
                     [
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes *", aRc=1, aStdout="iad103716x8mcompexpn16c" ,aPersist=True),
                     ],
                     [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True) 
                     ],
                     [
                         exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="welcome1", aPersist=True),
                     ]
                ],
                self.mGetRegexDom0():
                [
                     [
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("rm *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("virsh list *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/sbin/vm_maker --list | grep iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/virsh dumpxml *", aRc=0, aStdout="vmbondeth0.400", aPersist=True),
                     ],
                     [
                         exaMockCommand("/opt/exadata_ovm/vm_maker --remove-domain *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("virsh destroy *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("virsh undefine *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("virsh list --all *", aRc=1, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/sbin/brctl show | grep vmbondeth0", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("rm *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/bin/virsh dumpxml *", aRc=0, aStdout="vmbondeth0.400", aPersist=True),
                         
                         
                     ],
                    [
                         exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("rm -f *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aStdout="", aPersist=True),
                         
                     ],
                     [
                         exaMockCommand("/bin/rm -f *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh && vmbackup cleanall --vm iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/usr/sbin/vm_maker *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/opt/exadata_ovm/vm_maker *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("virsh undefine *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("rm -rf *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("ls *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("losetup -a", aRc=0, aStdout="", aPersist=True),
                     ],
                     [
                          exaMockCommand("mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                          exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                          

                     ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/grep *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/sed *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand(re.escape(" /bin/scp * "), aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ] 
                } 
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')
        self.mGetClubox().mSetOciExacc(False)

        mock_getDbInfo.side_effect = None
        mock_removeIptables.side_effect = None
        mock_deleteDBHomes.side_effect = None
        mock_deleteClusterNode.side_effect = None
        mock_delNode.side_effect = None
        mock_sharedEnv = None

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(DELETE_CONF)
        _options.jsonconf = json.loads(_json_object)

        _patchconfig = self.mGetClubox().mGetPatchConfig()
        _oeda_path  = self.mGetClubox().mGetOedaPath()

        _path = _oeda_path + '/exacloud.conf'
        if not os.path.isdir(_path):
            os.makedirs(_path)
        _delnodexml = _oeda_path + '/exacloud.conf/nodesubset_exatest.xml'
        shutil.copyfile(self.mGetClubox().mGetConfigPath(), _delnodexml)
        try:
            _obj = ebCluReshapeCompute( self.mGetClubox(), _options)
            _obj.mReshapeVMGI(_options)
        except:
            ebLogInfo("Exception Caught..")

        ebLogInfo("Unit test on cluelasticcompute.py:mDeleteNode successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, "/u01/app/grid"))
    def test_mUpdateHugePages(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mUpdateHugePages")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("sysctl -n vm.nr_hugepages", aRc=0, aStdout="42605"),    
                    ],
                    [
                        # Initial value
                         exaMockCommand("sysctl -n vm.nr_hugepages", aRc=0, aStdout="42605"),    
                         exaMockCommand("cat /etc/sysctl.conf", aRc=0, aStdout="vm.nr_hugepages = 42605"),

                         # Replace
                         exaMockCommand("cp /etc/sysctl.conf", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/sed -i *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/usr/sbin/sysctl -p", aRc=0, aStdout="" ,aPersist=True),

                         # New Value
                         exaMockCommand("sysctl -n vm.nr_hugepages", aRc=0, aStdout="41605"),    
                         exaMockCommand("cat /etc/sysctl.conf", aRc=0, aStdout="vm.nr_hugepages = 41605"),
                    ],
                    [                          
                         exaMockCommand("/usr/sbin/sysctl -n vm.nr_hugepages", aRc=0, aStdout="41605",aPersist=True),
                         exaMockCommand('/bin/grep "vm.nr_hugepages" /etc/sysctl.conf', aRc=0, aStdout="",aPersist=True)
                         
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        reshape_conf = _obj.mGetReshapeConf()
        _newdomUList = [x['domU']['hostname'] for x in reshape_conf['nodes']]
        for _domU in _newdomUList:
            _obj.mUpdateHugePages(_domU)

        ebLogInfo("Unit test on cluelasticcompute.py:mUpdateHugePages successful")
    
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mMoveAhfDataDir_P01(self, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mMoveAhfDataDir")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                    ],
                    [
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/mv *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl -check", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl shutdown", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl -check", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl shutdown", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/mv *", aRc=0, aStdout="", aPersist=True),
                    ]
                ]
        }


        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _srcdomU = _obj.mGetSrcDomU()

        _obj.mMoveAhfDataDir(_srcdomU, True)

        ebLogInfo("Unit test on cluelasticcompute.py:mMoveAhfDataDir successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, "/u01/app/grid"))
    def test_mMoveAhfDataDir_P02(self, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mMoveAhfDataDir")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                    ],
                    [
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/mv *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl -check", aRc=1, aStdout="", aPersist=True),
                         exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl start", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl -check", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl start", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/mv *", aRc=0, aStdout="", aPersist=True),
                    ]
                ]
        }


        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _srcdomU = _obj.mGetSrcDomU()

        _obj.mMoveAhfDataDir(_srcdomU, False, True, True)

        ebLogInfo("Unit test on cluelasticcompute.py:mMoveAhfDataDir successful")


    @patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mCheckMissingEncryptionFlag')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveOEDASSHKeys")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchVMCfg")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetGIHome")
    def test_mCallBack(self, mock_saveOEDAkeys, mock_patchVMcfg, mock_giHome, mock_mGetOracleBaseDirectories, mock_mCheckMissingEncryptionFlag):

        ebLogInfo("Running unit test on cluelasticcompute.py:mCallBack")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/usr/bin/hostname", aRc=0, aStdout="iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com", aPersist=True),
                         exaMockCommand("/usr/bin/hostnamectl set-hostname *", aRc=0, aStdout="iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno source,fstype,label *", aRc=0, aStdout="/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk xfs", aPersist=True),
                         exaMockCommand("/bin/lsblk -rno TYPE *", aRc=0, aStdout="lvm", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno target /u01", aRc=0, aStdout="/u01", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno target /u02", aRc=0, aStdout="/u02", aPersist=True),
                         exaMockCommand("/bin/lsblk -nprso NAME *", aRc=0, aStdout="/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk\n/dev/sdb1\n/dev/sdb", aPersist=True),
                    ],
                    [
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u02/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u02/app/grid" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/chown -fR *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno source,fstype,label *", aRc=0, aStdout="/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk xfs", aPersist=True),
                         exaMockCommand("/bin/lsblk -rno TYPE *", aRc=0, aStdout="lvm", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno target /u01", aRc=0, aStdout="/u01", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno target /u02", aRc=0, aStdout="/u02", aPersist=True),
                         exaMockCommand("/bin/lsblk -nprso NAME *", aRc=0, aStdout="/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk\n/dev/sdb1\n/dev/sdb", aPersist=True),
                    ],
                    [
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u02/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u02/app/grid" ,aPersist=True),
                    ],
                    [
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u02/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u02/app/grid" ,aPersist=True),
                    ]
                ]
        }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _obj.mCallBack("CELL_CONNECTIVITY")
        _obj.mCallBack("CREATE_USERS")
        _obj.mCallBack("CONFIG_CLUSTERWARE")

        ebLogInfo("Unit test on cluelasticcompute.py:mCallBack successful")

    #@patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mCheckMissingEncryptionFlag')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveOEDASSHKeys")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchVMCfg")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetGIHome")
    def test_mCallBack_FSEncNotInPayloadFailure(self, mock_saveOEDAkeys, mock_patchVMcfg, mock_giHome, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mCallBack")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/usr/bin/hostname", aRc=0, aStdout="iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com", aPersist=True),
                         exaMockCommand("/usr/bin/hostnamectl set-hostname *", aRc=0, aStdout="iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno source,fstype,label *", aRc=0, aStdout="/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk xfs", aPersist=True),
                         exaMockCommand("/bin/lsblk -rno TYPE *", aRc=0, aStdout="crypt", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno target /u01", aRc=0, aStdout="/u01", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno target /u02", aRc=0, aStdout="/u02", aPersist=True),
                         exaMockCommand("/bin/lsblk -nprso NAME *", aRc=0, aStdout="/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk\n/dev/sdb1\n/dev/sdb", aPersist=True),
                    ],
                    [
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u02/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u02/app/grid" ,aPersist=True),
                         exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/chown -fR *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno source,fstype,label *", aRc=0, aStdout="/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk xfs", aPersist=True),
                         exaMockCommand("/bin/lsblk -rno TYPE *", aRc=0, aStdout="crypt", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno target /u01", aRc=0, aStdout="/u01", aPersist=True),
                         exaMockCommand("/bin/findmnt -rno target /u02", aRc=0, aStdout="/u02", aPersist=True),
                         exaMockCommand("/bin/lsblk -nprso NAME *", aRc=0, aStdout="/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk\n/dev/sdb1\n/dev/sdb", aPersist=True),
                    ],
                    [
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u02/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u02/app/grid" ,aPersist=True),
                    ],
                    [
                         exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u02/app/19.0.0.0/grid" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                         exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u02/app/grid" ,aPersist=True),
                    ]
                ]
        }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        try:
            _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

            _obj.mCallBack("CELL_CONNECTIVITY")
            _obj.mCallBack("CREATE_USERS")
            _obj.mCallBack("CONFIG_CLUSTERWARE")
        except:
            ebLogInfo("Expected exception caught. Unit test on cluelasticcompute.py:mCallBack successful.")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveXMLClusterConfiguration")
    @mock.patch("exabox.ovm.cluelasticcompute.OedacliCmdMgr.mDeleteClusterNode")
    def test_mExecuteOEDACLIUndoStep(self, mock_saveconfig, mock_deleteClusterNode, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mExecuteOEDACLIUndoStep")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),

                    ],
                    [
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                        exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="Zl4_Qf0#397#8_12", aPersist=True),
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="Zl4_Qf0#397#8_12", aPersist=True),
                    ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                     ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        reshape_conf = _obj.mGetReshapeConf()
        _newdomUList = [x['domU']['hostname'] for x in reshape_conf['nodes']]
        _obj.mExecuteOEDACLIUndoStep(_newdomUList, "RUN_ROOTSCRIPT") 

        ebLogInfo("Unit test on cluelasticcompute.py:mExecuteOEDACLIUndoStep successful")

    def mGetNodeModel(self, aHostName):
        return 'X11'

    @patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetNodeU02Size')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetU02Size')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCopyFile')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateInMemoryXmlConfig')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchNetworkSlaves')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsOciEXACC', return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.IsHeteroConfig', return_value=(True, 'X11'))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value='X11')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, "/u01/app/grid"))
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveOEDASSHKeys")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveXMLClusterConfiguration")
    @mock.patch("exabox.ovm.cluelasticcompute.OedacliCmdMgr.mBuildMultipleGuests")
    @mock.patch("exabox.ovm.clubonding.is_static_monitoring_bridge_supported")
    @mock.patch("exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mSetIpTablesExaBM")
    def test_mExecuteOEDACLIDoStep(self, mock_saveOEDAkeys, mock_saveconfig, mock_buildGuests, mock_is_static_monitoring_bridge_supported, mock_setIptables, mock_mGetOracleBaseDirectories,
                                   mock_mGetNodeModel, mock_IsHeteroConfig, mock_mIsOciEXACC, 
                                   mock_mPatchNetworkSlaves,mock_mUpdateInMemoryXmlConfig, mock_mCopyFile,
                                   mock_mSetU02Size, mock_mGetNodeU02Size):

        ebLogInfo("Running unit test on cluelasticcompute.py:mExecuteOEDACLIDoStep")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand("/bin/test -e.*", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/cat .*ifcfg.*", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/cp *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/echo *", aRc=0, aStdout="", aPersist=True),

                    ],
                    [
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                        exaMockCommand("/bin/cp *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rm *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("/usr/local/bin/imageinfo -version"), aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                        exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="Zl4_Qf0#397#8_12", aPersist=True),
                    ],
                    [
                        exaMockCommand(re.escape("/usr/local/bin/imageinfo -version"), aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl -check", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl shutdown", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/mv *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl -check", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl shutdown", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/mv *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                        exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="Zl4_Qf0#397#8_12", aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl -check", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl start", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/mv *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="Zl4_Qf0#397#8_12", aPersist=True),

                    ],
                    [
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl -check", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/tfactl start", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/mv *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e.*", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/cat .*ifcfg.*", aRc=0, aStdout="", aPersist=True),
                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/qemu-img info --output=json *", aRc=0, aStdout="""{"virtual-size": 214748364800,"filename": "/EXAVMIMAGES/GuestImages/iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com/u02_extra.img",
                                         "format": "raw", "actual-size": 55619366912, "dirty-flag": false}""" ,aPersist=True),
                        exaMockCommand("/sbin/parted /EXAVMIMAGES/GuestImages/iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com/u02_extra.img print", aStdout="Partition Table: msdos", aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                    ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/sed -i *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/sed -r *", aRc=0, aStdout="", aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ping -c 1 *",aPersist=True),
                         exaMockCommand("/bin/grep PAAS *", aRc=0, aStdout="PASS" ,aPersist=True),
                         exaMockCommand("/bin/sed *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                     ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        mock_is_static_monitoring_bridge_supported.side_effects = None
        mock_is_static_monitoring_bridge_supported.return_value = False

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        reshape_conf = _obj.mGetReshapeConf()
        _newdomUList = [x['domU']['hostname'] for x in reshape_conf['nodes']]
        self.mGetClubox().mGetNodeModel = self.mGetNodeModel
        _node = Mock()
        _net_class = ebDiscoverOEDANetwork(_node, 'X11', self.mGetClubox())
        with patch('exabox.ovm.clunetworkdetect.ebDiscoverOEDANetwork.mGetNetwork', return_value=_net_class.SupportedX11Network.OCIEXACC_FULL_FIBER):
            _obj.mExecuteOEDACLIDoStep(_newdomUList, "RUN_ROOTSCRIPT") 

        ebLogInfo("Unit test on cluelasticcompute.py:mExecuteOEDACLIDoStep successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mSyncPSMKeys(self, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mSyncPSMKeys")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("/bin/cat *", aRc=0, aStdout="DOMU PUBLIC KEY", aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),

                    ],
                    [
                        exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/cat *", aRc=0, aStdout="DOMU PUBLIC KEY", aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/cat *", aRc=0, aStdout="DOMU PUBLIC KEY", aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/cat *", aRc=0, aStdout="DOMU PUBLIC KEY", aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/cat *", aRc=0, aStdout="DOMU PUBLIC KEY", aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                    ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                     ]
                ]
        }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        reshape_conf = _obj.mGetReshapeConf()
        _newdomUList = [x['domU']['hostname'] for x in reshape_conf['nodes']]

        _srcdomU = _obj.mGetSrcDomU()
        for _newdomU in _newdomUList:
            _obj.mSyncPSMKeys(_srcdomU, _newdomU)

        ebLogInfo("Unit test on cluelasticcompute.py:mSyncPSMKeys successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveXMLClusterConfiguration")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mRemoveNodeFromCRS")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchXMLForNodeSubset")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mStoreDomUInterconnectIps")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveClusterConfiguration")
    @mock.patch("exabox.network.dns.DNSConfig.ebDNSConfig.mRestartDnsmasq", return_value=None)
    @mock.patch("exabox.network.dns.DNSConfig.ebDNSConfig.mRemoveHostEntries")
    def test_mExecDelNodeEndStep(self, mock_dnsdelete, mock_dnsrestart, mock_saveconfig, mock_removeFromCRS, mock_patchXML, mock_storedomUpriv, mock_saveClusterConfig, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mExecDelNodeEndStep")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("/bin/su *", aRc=0, aStdout="" ,aPersist=True),

                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/rm -f *", aRc=0, aStdout="", aPersist=True),
                    ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/rsync *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')
        self.mGetClubox().mSetOciExacc(True)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)
        clusterId = self.mGetClubox().mGetClusters().mGetCluster().mGetCluId()
        self.mGetClubox().mSetDomUsDom0s(clusterId, _ddp)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(DELETE_CONF)
        _options.jsonconf = json.loads(_json_object)

        _uuid = self.mGetClubox().mGetUUID()
        _oeda_path = self.mGetClubox().mGetOedaPath()
        _path = _oeda_path + '/exacloud.conf'
        if not os.path.isdir(_path):
            os.makedirs(_path)
        _deletenodexml = _oeda_path + '/exacloud.conf/deletenode_' + _uuid + '.xml'

        _patchconfig = self.mGetClubox().mGetPatchConfig()
        shutil.copyfile(_patchconfig, _deletenodexml)

        _obj = ebCluReshapeCompute( self.mGetClubox(), _options)
        try:
            _obj.mExecDelNodeEndStep(_options)
        except:
            ebLogInfo("Exception Caught..")

        mock_dnsdelete.assert_called_once_with("iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com")

        self.mGetClubox().mSetConfig(_patchconfig)
        self.mGetClubox().mSetPatchConfig(_patchconfig)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        #update Dom0DomUPair and Dom0DomUNATPair forcefully
        _ddp_nat = self.mGetClubox().mReturnDom0DomUNATPair(True)
        _ddp = self.mGetClubox().mReturnDom0DomUPair(True)
        _host_list = self.mGetClubox().mGetHostList(True)
        self.mGetClubox().mSetUt(False)

        ebLogInfo("Unit test on cluelasticcompute.py:mExecDelNodeEndStep successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetDbInfo")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabases")
    @mock.patch("exabox.ovm.cluelasticcompute.deleteInstance")
    def test_mRemoveComputeDBDelete(self,mock_deleteInstance, mock_getdb, mock_dbInfo, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveComputeDBDelete")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),

                    ],
                    [
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                        exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/srvctl config database"), aRc=0, aStdout="c12145_mfn_sea" ,aPersist=True),

                    ],
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="Zl4_Qf0#397#8_12", aPersist=True),

                    ],
                    [
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/19.0.0.0/grid;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status database -d c12145_mfn_sea"), aRc=0, aStdout="Instance c12145_L0oon1 is running on node iad103716x8mcompexpn15c" ,aPersist=True),
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/19.0.0.0/grid;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status service -d c12145_mfn_sea"), aRc=0, aStdout="Service c12145_pdb1.paas.oracle.com is running on instance(s) c12145_L0oon1" ,aPersist=True),
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/19.0.0.0/grid;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep 'Preferred instances'"), aRc=0, aStdout="Preferred instances: c12145_L0oon1" ,aPersist=True),
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/19.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl modify service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com -modifyconfig -preferred  -available c12145_L0oon1"), aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/19.0.0.0/grid;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep -E 'Preferred instances|Available instances'"), aRc=0, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand(re.escape("cat /etc/oratab | grep c12145_mfn_sea | awk -F : '{print $2}'"), aRc=0, aStdout="/u01/app/oracle/product/18.0.0.0/dbhome_2" ,aPersist=True),
                        exaMockCommand(re.escape("cat /etc/oratab | /bin/grep '^c12145_mfn_sea.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/oracle/product/18.0.0.0/dbhome_2" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2; $ORACLE_HOME/bin/oraversion -baseVersion"), aStdout="18.0.0.0", aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2; $ORACLE_HOME/bin/orabase"), aStdout="/u01/app/oracle/product/18.0.0.0", aPersist=True),
                    ],
                    [
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status database -d c12145_mfn_sea"), aRc=0, aStdout="Instance c12145_L0oon1 is running on node iad103716x8mcompexpn15c" ,aPersist=True),
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl status service -d c12145_mfn_sea"), aRc=0, aStdout="Service c12145_pdb1.paas.oracle.com is running on instance(s) c12145_L0oon1" ,aPersist=True),
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep 'Preferred instances'"), aRc=0, aStdout="Preferred instances: c12145_L0oon1" ,aPersist=True),
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl modify service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com -modifyconfig -preferred  -available c12145_L0oon1"), aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand(re.escape("ORACLE_HOME=/u01/app/oracle/product/18.0.0.0/dbhome_2;export ORACLE_HOME;$ORACLE_HOME/bin/srvctl config service -d c12145_mfn_sea -service c12145_pdb1.paas.oracle.com | grep -E 'Preferred instances|Available instances'"), aRc=0, aStdout="" ,aPersist=True),
                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/usr/sbin/vm_maker --list *", aRc=0, aStdout="iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com(153): running", aPersist=True),
                    ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/rsync *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')
        self.mGetClubox().mSetOciExacc(False)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)
        clusterId = self.mGetClubox().mGetClusters().mGetCluster().mGetCluId()
        self.mGetClubox().mSetDomUsDom0s(clusterId, _ddp)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(DELETE_CONF)
        _options.jsonconf = json.loads(_json_object)

        _patchconfig = self.mGetClubox().mGetPatchConfig()

        _obj = ebCluReshapeCompute( self.mGetClubox(), _options)

        reshape_conf = _obj.mGetReshapeConf()
        _reshape_dom0_list = [x['dom0']['hostname'] for x in reshape_conf['nodes']] 
        _reshape_domu_list = [x['domU']['hostname'] for x in reshape_conf['nodes']]

        _obj.mRemoveComputeDBDelete("OSTP_PREDB_DELETE", _reshape_domu_list, ["OSTP_PREDB_DELETE"], _options)
        _obj.mRemoveComputeDBDelete("OSTP_CREATE_DB", _reshape_domu_list, ["OSTP_CREATE_DB"], _options)

        self.mGetClubox().mSetConfig(_patchconfig)
        self.mGetClubox().mSetPatchConfig(_patchconfig)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        #update Dom0DomUPair and Dom0DomUNATPair forcefully
        _ddp_nat = self.mGetClubox().mReturnDom0DomUNATPair(True)
        _ddp = self.mGetClubox().mReturnDom0DomUPair(True)
        _host_list = self.mGetClubox().mGetHostList(True)
        self.mGetClubox().mSetUt(False)

        ebLogInfo("Unit test on cluelasticcompute.py:mRemoveComputeDBDelete successful")

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mRemoveGuestEDVVolumes')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled', return_value = False)
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mRemoveNodeFromCRS")
    @patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mCleanVMbackup', side_effect=Exception("Test exception"))
    def test_mRemoveComputeVMDeleteP01(self, mock_removeFromCRS, mock_vmbackupInstalled, mock_mGetOracleBaseDirectories, 
                                       mock_mCleanVMbackup, mock_mRemoveGuestEDVVolumes):

        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveComputeVMDeleteP01")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),

                    ],
                    [
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True)
                    ],
                    [
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True)
                    ],
                    [
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True)
                    ],
                    [
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True)
                    ],
                    [
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True)
                    ],
                    [
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /root/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/opc/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/oracle/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True),
                        exaMockCommand(re.escape("/usr/bin/ssh-keygen -R iad103716x8mcompexpn16c -f /home/grid/.ssh/known_hosts"), aRc=0, aStdout=0 ,aPersist=True)
                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/usr/bin/virsh dumpxml *", aRc=0, aStdout="vmbondeth0.400", aPersist=True),
                        exaMockCommand("rm *", aRc=0, aStdout="", aPersist=True)
                    ],
                    [
                        exaMockCommand("source *", aRc=0, aStdout="vmbondeth0.400", aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/vm_maker *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker *", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("virsh undefine *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("rm -rf *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("ls *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("losetup -a", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/sbin/brctl show *", aRc=1, aStdout="", aPersist=True),

                    ],
                    [
                        exaMockCommand("rm *", aRc=0, aStdout="", aPersist=True)
                    ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/rsync *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')
        self.mGetClubox().mSetOciExacc(False)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)
        clusterId = self.mGetClubox().mGetClusters().mGetCluster().mGetCluId()
        self.mGetClubox().mSetDomUsDom0s(clusterId, _ddp)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(DELETE_CONF)
        _options.jsonconf = json.loads(_json_object)

        _patchconfig = self.mGetClubox().mGetPatchConfig()
        get_gcontext().mSetConfigOption('force_delete_vm', 'True')

        _obj = ebCluReshapeCompute( self.mGetClubox(), _options)

        reshape_conf = _obj.mGetReshapeConf()

        _reshape_dom0domU_list = [] 
        for x in reshape_conf['nodes']: 
            _reshape_dom0domU_list.append([x['dom0']['hostname'], x['domU']['hostname']]) 

        self.mGetContext().mSetConfigOption('vmbackup', {'force_error_on_cleanup': "False"})

        for _reshape_dom0, _reshape_domu in _reshape_dom0domU_list:
            _obj.mRemoveComputeVMDelete(_reshape_dom0, _reshape_domu, ["OSTP_CREATE_VM"], _options) 

        self.mGetClubox().mSetConfig(_patchconfig)
        self.mGetClubox().mSetPatchConfig(_patchconfig)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        #update Dom0DomUPair and Dom0DomUNATPair forcefully
        _ddp_nat = self.mGetClubox().mReturnDom0DomUNATPair(True)
        _ddp = self.mGetClubox().mReturnDom0DomUPair(True)
        _host_list = self.mGetClubox().mGetHostList(True)
        self.mGetClubox().mSetUt(False)

        ebLogInfo("Unit test on cluelasticcompute.py:mRemoveComputeVMDeleteP01 successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @mock.patch("exabox.ovm.cluelasticcompute.OedacliCmdMgr.mDeleteDBHomes")
    @mock.patch("exabox.ovm.cluelasticcompute.OedacliCmdMgr.mDeleteClusterNode")
    def test_mRemoveComputeInstallCluster(self, mock_deleteDBHomes, mock_deleteClusterNode, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveComputeInstallCluster")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                        exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="Zl4_Qf0#397#8_12", aPersist=True),

                    ],
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="Zl4_Qf0#397#8_12", aPersist=True),
                    ],
                    [

                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/usr/bin/virsh dumpxml *", aRc=0, aStdout="vmbondeth0.400", aPersist=True),
                    ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/rsync *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')
        self.mGetClubox().mSetOciExacc(False)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)
        clusterId = self.mGetClubox().mGetClusters().mGetCluster().mGetCluId()
        self.mGetClubox().mSetDomUsDom0s(clusterId, _ddp)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(DELETE_CONF)
        _options.jsonconf = json.loads(_json_object)

        _patchconfig = self.mGetClubox().mGetPatchConfig()

        _obj = ebCluReshapeCompute( self.mGetClubox(), _options)
        reshape_conf = _obj.mGetReshapeConf()
        _reshape_dom0_list = [x['dom0']['hostname'] for x in reshape_conf['nodes']] 
        _reshape_domu_list = [x['domU']['hostname'] for x in reshape_conf['nodes']] 

        _obj.mRemoveComputeInstallCluster(_reshape_domu_list, ["OSTP_INSTALL_CLUSTER"], _options)

        self.mGetClubox().mSetConfig(_patchconfig)
        self.mGetClubox().mSetPatchConfig(_patchconfig)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        #update Dom0DomUPair and Dom0DomUNATPair forcefully
        _ddp_nat = self.mGetClubox().mReturnDom0DomUNATPair(True)
        _ddp = self.mGetClubox().mReturnDom0DomUPair(True)
        _host_list = self.mGetClubox().mGetHostList(True)
        self.mGetClubox().mSetUt(False)

        ebLogInfo("Unit test on cluelasticcompute.py:mRemoveComputeInstallCluster successful")


    @mock.patch("exabox.ovm.cluelasticcompute.ebCluDbaas.mCopyFileToDomU")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluDbaas.mBaseCopyFileToDomU")
    @mock.patch("exabox.ovm.cluelasticcompute.ebCluDbaas.mWaitForJobComplete")
    def test_mGetDbInfo(self, mock_copyToDomU, mock_basecopyToDomU, mock_WaitToComplete):

        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveDBInstancesFromVM") 

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                        exaMockCommand("/var/opt/oracle/ocde/rops get_cprops_key sys", aRc=0, aStdout="Zl4_Qf0#397#8_12", aPersist=True),
                        exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i *", aRc=0, aStdout=DB_INFO, aPersist=True),
                    ],
                    [
                        exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i *", aRc=0, aStdout=DB_INFO, aPersist=True),
                        exaMockCommand("cat *", aRc=0, aStdout=DB_ID, aPersist=True),
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i *", aRc=0, aStdout=DB_ID, aPersist=True),
                        exaMockCommand("cat *", aRc=0, aStdout=DB_ID, aPersist=True),
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i *", aRc=0, aStdout=DB_INFO, aPersist=True),
                        exaMockCommand("cat *", aRc=0, aStdout=NODE_INFO, aPersist=True),
                    ],
                    [
                        exaMockCommand("cat *", aRc=0, aStdout=NODE_INFO, aPersist=True),

                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/usr/bin/virsh dumpxml *", aRc=0, aStdout="vmbondeth0.400", aPersist=True),
                    ]
                ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/rsync *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/rm -f *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')
        self.mGetClubox().mSetOciExacc(False)

        mock_WaitToComplete.return_value = 0
        mock_copyToDomU.return_value = 0

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)
        clusterId = self.mGetClubox().mGetClusters().mGetCluster().mGetCluId()
        self.mGetClubox().mSetDomUsDom0s(clusterId, _ddp)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(DELETE_CONF)
        _options.jsonconf = json.loads(_json_object)

        _patchconfig = self.mGetClubox().mGetPatchConfig()

        try:
            _obj = ebCluReshapeCompute( self.mGetClubox(), _options)
            reshape_conf = _obj.mGetReshapeConf()
            _reshape_dom0_list = [x['dom0']['hostname'] for x in reshape_conf['nodes']] 
            _reshape_domu_list = [x['domU']['hostname'] for x in reshape_conf['nodes']] 

            _domU = _reshape_domu_list[0]
            _obj.mRemoveDBInstancesFromVM(_domU, _options)
        except:
            ebLogInfo("Exception Caught..")

        self.mGetClubox().mSetConfig(_patchconfig)
        self.mGetClubox().mSetPatchConfig(_patchconfig)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        #update Dom0DomUPair and Dom0DomUNATPair forcefully
        _ddp_nat = self.mGetClubox().mReturnDom0DomUNATPair(True)
        _ddp = self.mGetClubox().mReturnDom0DomUPair(True)
        _host_list = self.mGetClubox().mGetHostList(True)
        self.mGetClubox().mSetUt(False)

        ebLogInfo("Unit test on cluelasticcompute.py:mRemoveDBInstancesFromVM successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mBuildClusterDirP02(self, mock_mGetOracleBaseDirectories):

        ebLogInfo("Running unit test on cluelasticcompute.py:mBuildClusterDirP02")

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                    [
                         exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                         exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                         exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                         exaMockCommand("/usr/bin/hostname", aRc=0, aStdout="iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com", aPersist=True),
                         exaMockCommand("/usr/bin/hostnamectl set-hostname *", aRc=0, aStdout="iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com", aPersist=True),

                    ]
                ]
        }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')
        self.mGetClubox().mSetExabm(False)

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj.mBuildClusterDir(aDom0DomUPair=_ddp)

        ebLogInfo("Unit test on cluelasticcompute.py:mBuildClusterDirP02 successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mUpdateRequestData(self, mock_mGetOracleBaseDirectories):
       
        ebLogInfo("Running unit test on cluelasticcompute.py:mUpdateRequestData")
        _cmds = {
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2 ,aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3 ,aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        
        clusterId = self.mGetClubox().mGetClusters().mGetClusters()[0]

        self.mGetClubox().mSetDomUsDom0s(clusterId, _ddp)
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _obj.mUpdateRequestData(self.mGetClubox().mGetArgsOptions(), CONFIGURE_NODE)

                        
        ebLogInfo("Unit test on cluelasticcompute.py:mUpdateRequestData successful.")   

    def test_mRemoveNodeFromCRSP02(self):

        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveNodeFromCRSP02")

        _vipcmd = '/u01/app/19.0.0.0/grid/bin/srvctl config vip -n iad103716x8mcompexpn16c | grep "VIP Name"'
        _vipout = 'VIP Name: iad103716x8mcompexpn16c-vip.clientsubnet.devx8melastic.oraclevcn.com'
        _cmds = { 
                self.mGetRegexVm():                                      
                [
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716exddu1601/d' /etc/hosts", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716x8mcompexpn16c/d' /etc/hosts", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes -s -t | grep iad103716x8mcompexpn16c", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl delete node -n iad103716x8mcompexpn16c -purge", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes -s -t | grep iad103716x8mcompexpn16c", aRc=1, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op3, aPersist=True),
                        exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid", aPersist=True),
                        exaMockCommand(_vipcmd, aRc=0, aStdout=_vipout, aPersist=True),
                        exaMockCommand('/u01/app/19.0.0.0/grid/bin/crsctl unpin css -n iad103716x8mcompexpn16c', aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl stop cluster -n iad103716x8mcompexpn16c",aRc=0, aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl delete node -n iad103716x8mcompexpn16c", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl stop vip -vip iad103716x8mcompexpn16c-vip.clientsubnet.devx8melastic.oraclevcn.com -force", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl remove vip -vip iad103716x8mcompexpn16c-vip.clientsubnet.devx8melastic.oraclevcn.com -force", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes -s -t | grep iad103716x8mcompexpn16c", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716exddu1601/d' /etc/hosts", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716x8mcompexpn16c/d' /etc/hosts", aRc=0, aStdout="", aPersist=True)
                    ],
                    [
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes -s -t | grep iad103716x8mcompexpn16c", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716exddu1601/d' /etc/hosts", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/sed -i '/iad103716x8mcompexpn16c/d' /etc/hosts", aRc=0, aStdout="", aPersist=True),

                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetOciExacc(True)
        try:
            _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
            _obj.mRemoveNodeFromCRS('iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com')
        except:
            ebLogInfo("Exception Caught..")

        ebLogInfo("Unit test on cluelasticcompute.py:mRemoveNodeFromCRSP02 successful")
    
    @patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mUpdateDBEnv')
    @patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetSid', return_value="DB1793")
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabaseHomes")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabases")
    @mock.patch("exabox.ovm.cluelasticcompute.cloneDbHome")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabaseDetails")
    @mock.patch("exabox.ovm.cluelasticcompute.addInstance")
    def test_mAddDBHomes_valid_data(self,mock_addInstance , mock_getDatabaseDetails, mock_cloneDbHome, mock_getDatabases, mock_getDatabaseHomes, mock_mSetSrcDom0DomU, mock_mGetSid, mock_mUpdateDBEnv ):

        ebLogInfo("Running unit test on cluelasticcompute.py:mAddDBHomes")

        _cmds = { 
                'iad103716x8mcompexpn17c':
                [
                    [
                        exaMockCommand("/bin/rm -rf /u02/opt/dbaas_images/dbnid/*", aRc=0, aStdout="", aPersist=True),
                    ],
                ],
                self.mGetRegexVm():
                [ 
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops set_creg_key grid nodelist 'iad103716x8mcompexpn15c iad103716x8mcompexpn16c'", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/usr/bin/sudo -u oracle /bin/scp -r /u02/opt/dbaas_images oracle@iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com:/u02/opt/", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops add_creg db_name3 iad103716x8mcompexpn17c", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=1),
                        exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=1),
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),

                    ],
                    [
                        exaMockCommand("/usr/bin/sudo -u oracle /bin/scp -p /home/oracle/db_name3.env oracle@iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com:/home/oracle/", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/var/opt/oracle/ocde/rops add_creg db_name3 iad103716x8mcompexpn17c", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/usr/bin/sudo -u oracle /bin/scp -p /home/oracle/db_name3.env oracle@iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com:/home/oracle/", aRc=0, aStdout="", aPersist=True)
                    ],
                    [
                        exaMockCommand("/usr/bin/sudo -u oracle /bin/scp -p /home/oracle/db_name3.env oracle@iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com:/home/oracle/", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/var/opt/oracle/ocde/rops add_creg db_name3 iad103716x8mcompexpn17c", aRc=0, aStdout="", aPersist=True),
                    ]
                ]
        }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj._ebCluReshapeCompute__reshape_conf['nodes'][0]['domU']['db_info'] = 'db_name3'
        reshape_conf = _obj.mGetReshapeConf()
        _srcdomU = 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'
        mock_getDatabaseHomes.return_value = {
            "OraHome1" : {
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                "homeName" : "OraHome1",
                "version" : "19.23.0.0.0",
                "createTime" : 1717316044728,
                "updateTime" : 1717316044728,
                "ohNodeLevelDetails" : {
                "c3716n15c2" : {
                    "nodeName" : "c3716n15c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                },
                "c3716n16c2" : {
                    "nodeName" : "c3716n16c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                }
                },
                "messages" : [ ]
            },
            "ETFDB64" : {
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_1",
                "homeName" : "ETFDB64",
                "version" : "19.23.0.0.0",
                "createTime" : 1717314884502,
                "updateTime" : 1717314884502,
                "ohNodeLevelDetails" : {
                "c3716n15c2" : {
                    "nodeName" : "c3716n15c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                },
                "c3716n16c2" : {
                    "nodeName" : "c3716n16c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                }
                },
                "messages" : [ ]
            }
        }
        mock_getDatabases.return_value = {
            "db_name3" : {
                "dbName" : "db_name3",
                "dbUniqueName" : "db_name3",
                "dbDomain" : "clientsubnet.devx8melastic.oraclevcn.com",
                "dbId" : 818740923,
                "dbRole" : "PRIMARY",
                "dbNodeLevelDetails" : {
                "iad103716x8mcompexpn17c" : {
                    "nodeName" : "iad103716x8mcompexpn17c",
                    "instanceName" : "db_name31",
                    "version" : "19.23.0.0.0",
                    "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                    "status" : "OPEN"
                },
                "iad103716x8mcompexpn15c" : {
                    "nodeName" : "iad103716x8mcompexpn15c",
                    "instanceName" : "db_name32",
                    "version" : "19.23.0.0.0",
                    "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                    "status" : "OPEN"
                }
                }
            }
        }
        mock_cloneDbHome.return_value = 0
        mock_getDatabaseDetails.return_value = {
            "dbSyncTime" : 1717692938133,
            "createTime" : 1717692155000,
            "updateTime" : 0,
            "dbName" : "db_name3",
            "dbUniqueName" : "db_name3",
            "dbDomain" : "clientsubnet.devx8melastic.oraclevcn.com",
            "dbId" : 818740923,
            "dbRole" : "PRIMARY",
            "dbNodeLevelDetails" : {
                "iad103716x8mcompexpn17c" : {
                "nodeName" : "iad103716x8mcompexpn17c",
                "instanceName" : "db_name31",
                "version" : "19.23.0.0.0",
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                "status" : "OPEN"
                },
                "iad103716x8mcompexpn15c" : {
                "nodeName" : "iad103716x8mcompexpn15c",
                "instanceName" : "db_name32",
                "version" : "19.23.0.0.0",
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                "status" : "OPEN"
                }
            }
            }
        mock_addInstance.return_value = 0
        
        _obj.mAddDBHomes(self.mGetClubox().mGetArgsOptions(), _srcdomU)

        ebLogInfo("Unit test on cluelasticcompute.py:mAddDBHomes successful")


    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabaseHomes")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabases")
    @mock.patch("exabox.ovm.cluelasticcompute.cloneDbHome")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabaseDetails")
    @mock.patch("exabox.ovm.cluelasticcompute.addInstance")
    def test_mAddDBHomes_Invalid_data_dbNodeLevelDetails(self,mock_addInstance , mock_getDatabaseDetails, mock_cloneDbHome, mock_getDatabases, mock_getDatabaseHomes, mock_mSetSrcDom0DomU ):

        ebLogInfo("Running unit test on cluelasticcompute.py:mAddDBHomes")

        _cmds = { 
                'iad103716x8mcompexpn17c':
                [
                    [
                        exaMockCommand("/bin/rm -rf /u02/opt/dbaas_images/dbnid/*", aRc=0, aStdout="", aPersist=True),
                    ],
                ],
                self.mGetRegexVm():
                [ 
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops set_creg_key grid nodelist 'iad103716x8mcompexpn15c iad103716x8mcompexpn16c'", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/usr/bin/sudo -u oracle /bin/scp -r /u02/opt/dbaas_images oracle@iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com:/u02/opt/", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops add_creg db_name3 iad103716x8mcompexpn17c", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=1),
                        exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=1),
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                        exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops add_creg db_name3 iad103716x8mcompexpn17c", aRc=0, aStdout="", aPersist=True),
                    ]
                ]
        }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj._ebCluReshapeCompute__reshape_conf['nodes'][0]['domU']['db_info'] = 'db_name3'
        reshape_conf = _obj.mGetReshapeConf()
        _srcdomU = 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'
        mock_getDatabaseHomes.return_value = {
            "OraHome1" : {
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                "homeName" : "OraHome1",
                "version" : "19.23.0.0.0",
                "createTime" : 1717316044728,
                "updateTime" : 1717316044728,
                "ohNodeLevelDetails" : {
                "c3716n15c2" : {
                    "nodeName" : "c3716n15c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                },
                "c3716n16c2" : {
                    "nodeName" : "c3716n16c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                }
                },
                "messages" : [ ]
            },
            "ETFDB64" : {
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_1",
                "homeName" : "ETFDB64",
                "version" : "19.23.0.0.0",
                "createTime" : 1717314884502,
                "updateTime" : 1717314884502,
                "ohNodeLevelDetails" : {
                "c3716n15c2" : {
                    "nodeName" : "c3716n15c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                },
                "c3716n16c2" : {
                    "nodeName" : "c3716n16c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                }
                },
                "messages" : [ ]
            }
        }
        mock_getDatabases.return_value = {
            "db_name3" : {
                "dbName" : "db_name3",
                "dbUniqueName" : "db_name3",
                "dbDomain" : "clientsubnet.devx8melastic.oraclevcn.com",
                "dbId" : 818740923,
                "dbNodeLevelDetails" : None
                }
            }
        mock_cloneDbHome.return_value = 0
        mock_getDatabaseDetails.return_value = {
            "dbSyncTime" : 1717692938133,
            "createTime" : 1717692155000,
            "updateTime" : 0,
            "dbName" : "db_name3",
            "dbUniqueName" : "db_name3",
            "dbDomain" : "clientsubnet.devx8melastic.oraclevcn.com",
            "dbId" : 818740923,
            "dbNodeLevelDetails" : {
                "iad103716x8mcompexpn17c" : {
                "nodeName" : "iad103716x8mcompexpn17c",
                "instanceName" : "db_name31",
                "version" : "19.23.0.0.0",
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                "status" : "OPEN"
                },
                "iad103716x8mcompexpn15c" : {
                "nodeName" : "iad103716x8mcompexpn15c",
                "instanceName" : "db_name32",
                "version" : "19.23.0.0.0",
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                "status" : "OPEN"
                }
            }
            }
        mock_addInstance.return_value = 0
        
        _obj.mAddDBHomes(self.mGetClubox().mGetArgsOptions(), _srcdomU)

        ebLogInfo("Unit test on cluelasticcompute.py:mAddDBHomes successful")


    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabaseHomes")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabases")
    @mock.patch("exabox.ovm.cluelasticcompute.cloneDbHome")
    @mock.patch("exabox.ovm.cluelasticcompute.getDatabaseDetails")
    @mock.patch("exabox.ovm.cluelasticcompute.addInstance")
    def test_mAddDBHomes_Invalid_data_dbhomes(self,mock_addInstance , mock_getDatabaseDetails, mock_cloneDbHome, mock_getDatabases, mock_getDatabaseHomes, mock_mSetSrcDom0DomU ):

        ebLogInfo("Running unit test on cluelasticcompute.py:mAddDBHomes")

        _cmds = { 
                'iad103716x8mcompexpn17c':
                [
                    [
                        exaMockCommand("/bin/rm -rf /u02/opt/dbaas_images/dbnid/*", aRc=0, aStdout="", aPersist=True),
                    ],
                ],
                self.mGetRegexVm():
                [ 
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops set_creg_key grid nodelist 'iad103716x8mcompexpn15c iad103716x8mcompexpn16c'", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/usr/bin/sudo -u oracle /bin/scp -r /u02/opt/dbaas_images oracle@iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com:/u02/opt/", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops add_creg db_name3 iad103716x8mcompexpn17c", aRc=0, aStdout="", aPersist=True)
                    ]
                ]
        }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('vmgi_reshape')

        _ddp = self.mGetClubox().mReturnDom0DomUPair()
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)
        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj._ebCluReshapeCompute__reshape_conf['nodes'][0]['domU']['db_info'] = 'db_name3'
        reshape_conf = _obj.mGetReshapeConf()
        _srcdomU = 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'
        mock_getDatabaseHomes.return_value = {}
        mock_getDatabases.return_value = {
            "db_name3" : {
                "dbName" : "db_name3",
                "dbUniqueName" : "db_name3",
                "dbDomain" : "clientsubnet.devx8melastic.oraclevcn.com",
                "dbId" : 818740923,
                "dbNodeLevelDetails" : None
                }
            }
        mock_cloneDbHome.return_value = 0
        mock_getDatabaseDetails.return_value = {
            "dbSyncTime" : 1717692938133,
            "createTime" : 1717692155000,
            "updateTime" : 0,
            "dbName" : "db_name3",
            "dbUniqueName" : "db_name3",
            "dbDomain" : "clientsubnet.devx8melastic.oraclevcn.com",
            "dbId" : 818740923,
            "dbNodeLevelDetails" : {
                "iad103716x8mcompexpn17c" : {
                "nodeName" : "iad103716x8mcompexpn17c",
                "instanceName" : "db_name31",
                "version" : "19.23.0.0.0",
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                "status" : "OPEN"
                },
                "iad103716x8mcompexpn15c" : {
                "nodeName" : "iad103716x8mcompexpn15c",
                "instanceName" : "db_name32",
                "version" : "19.23.0.0.0",
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                "status" : "OPEN"
                }
            }
            }
        mock_addInstance.return_value = 0
        
        _obj.mAddDBHomes(self.mGetClubox().mGetArgsOptions(), _srcdomU)

        ebLogInfo("Unit test on cluelasticcompute.py:mAddDBHomes successful")
        
    def test_mRemoveSSHPublicKeyFromVM(self):
        src_dom_u = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        deleted_dom_u = self.mGetClubox().mReturnDom0DomUPair()[1][1]
        user = 'oracle'
        
        # Test case 1: Valid inputs
        ebLogInfo("Testing valid inputs...")
        self.mGetClubox().mSetCmd('vmgi_reshape')
        current_health_object = ebCluSshSetup(self.mGetClubox())
        cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(re.escape('/usr/bin/ssh-keygen -R {} -f /home/{}/.ssh/known_hosts'.format(deleted_dom_u, user)), aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(cmds)
        current_health_object.mRemoveSSHPublicKeyFromVM(src_dom_u, deleted_dom_u, user)
        ebLogInfo("Valid inputs test passed.")

        # Test case 3: Invalid input - empty src_dom_u
        ebLogInfo("Testing invalid input - empty src_dom_u...")
        current_health_object = ebCluSshSetup(self.mGetClubox())
        current_health_object.mRemoveSSHPublicKeyFromVM('', deleted_dom_u, user, True)
        ebLogInfo("Empty src_dom_u test passed.")

        # Test case 4: Invalid input - empty deleted_dom_u
        ebLogInfo("Testing invalid input - empty deleted_dom_u...")
        current_health_object = ebCluSshSetup(self.mGetClubox())
        current_health_object.mRemoveSSHPublicKeyFromVM(src_dom_u, '', user, True)
        ebLogInfo("Empty deleted_dom_u test passed.")

        # Test case 5: Invalid input - empty user
        ebLogInfo("Testing invalid input - empty user...")
        current_health_object = ebCluSshSetup(self.mGetClubox())
        current_health_object.mRemoveSSHPublicKeyFromVM(src_dom_u, deleted_dom_u, '', True)
        ebLogInfo("Empty user test passed.")

        # Test case 6: Invalid input - non-boolean aUseInputUserForSSH
        ebLogInfo("Testing invalid input - non-boolean aUseInputUserForSSH...")
        current_health_object = ebCluSshSetup(self.mGetClubox())
        current_health_object.mRemoveSSHPublicKeyFromVM(src_dom_u, deleted_dom_u, user, 'invalid_bool')
        ebLogInfo("Non-boolean aUseInputUserForSSH test passed.")
        
        self.mGetClubox().mSetCmd('sim_install')
        ebLogInfo("Testing invalid input - program argument test")
        current_health_object = ebCluSshSetup(self.mGetClubox())
        current_health_object.mRemoveSSHPublicKeyFromVM('', deleted_dom_u, user, True)
        ebLogInfo("Program argument test passed.")

    @mock.patch("exabox.ovm.cluelasticcompute.getDatabases")
    @mock.patch("exabox.ovm.cluelasticcompute.deleteInstance")
    @mock.patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mRemoveDBInstancesFromVMDbaascli(self, mock_mGetOracleBaseDirectories, mock_deleteInstance, mock_getDatabases):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveDBInstancesFromVMDbaascli")

        _cmds = {
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1 ,aPersist=True),
                        exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2 ,aPersist=True),
                        exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3 ,aPersist=True),
                        exaMockCommand(re.escape('dbaascli database deleteInstance --dbname DBclu01 --nodeListForInstanceMgmt iad103716x8mcompexpn16c'), aRc=0, aPersist=True)

                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)

        _ddp = [ ['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'], 
                ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com'] ]
        
        clusterId = self.mGetClubox().mGetClusters().mGetClusters()[0]

        self.mGetClubox().mSetDomUsDom0s(clusterId, _ddp)
        self.mGetClubox().mSetOrigDom0sDomUs(_ddp)
        _targetdomU = "iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com"
        mock_getDatabases.return_value = { "DBclu01" : {
            "dbName" : "DBclu01", "dbUniqueName" : "DBclu01_6bs_iad", "dbDomain" : "oadtclient.oadtmichelvcn.oraclevcn.com", "dbRole" : "PRIMARY", "dbType" : "RAC",
            "dbNodeLevelDetails" : { 
                "iad103716x8mcompexpn15c" : { "nodeName" : "iad103716x8mcompexpn15c", "instanceName" : "DBclu012", "version" : "19.22.0.0.0", "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_1", "status" : "OPEN"},
                "iad103716x8mcompexpn16c" : { "nodeName" : "iad103716x8mcompexpn16c", "instanceName" : "DBclu011", "version" : "19.22.0.0.0", "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_1", "status" : "READ_ONLY"}}}
        }

        _reshape = ebCluReshapeCompute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _reshape.mRemoveDBInstancesFromVMDbaascli(_targetdomU, self.mGetClubox().mGetArgsOptions())


    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mIsMulticloud_AZURE_installed(self,mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveDBInstancesFromVMDbaascli")
        src_dom_u = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexVm(): [
                [                        
                    exaMockCommand(re.escape(cmd8), aRc=0, aStdout=op8 ,aPersist=True), 
                    exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                    exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0, aStdout="dbmulticloud-dataplane-integ-24.1.66.0.0-250317.1647.x86_64"),
                    exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=0, aStdout="pkcs-multicloud-driver-maz-0.1-250515.0542.x86_64"),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _reshape = ebCluReshapeCompute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
         # Identify if this is Multicloud env
        _isMulticloud, _multicloudProvider = _reshape.mIsMulticloud(src_dom_u)
        self.assertEqual(_isMulticloud, True)
        self.assertEqual(_multicloudProvider, "AZURE")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mIsMulticloud_AZURE_file(self,mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveDBInstancesFromVMDbaascli")
        src_dom_u = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexVm(): [
                [                        
                    exaMockCommand(re.escape(cmd8), aRc=0, aStdout=op8 ,aPersist=True), 
                    exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                    exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0, aStdout="dbmulticloud-dataplane-integ-24.1.66.0.0-250317.1647.x86_64"),
                    exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=1),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=0, aStdout="pkcs-multicloud-driver-maz-0.1-250515.0542.x86_64.rpm" ,aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _reshape = ebCluReshapeCompute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
         # Identify if this is Multicloud env
        _isMulticloud, _multicloudProvider = _reshape.mIsMulticloud(src_dom_u)
        self.assertEqual(_isMulticloud, True)
        self.assertEqual(_multicloudProvider, "AZURE")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mIsMulticloud_GOOGLE_installed(self,mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveDBInstancesFromVMDbaascli")
        src_dom_u = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexVm(): [
                [                        
                    exaMockCommand(re.escape(cmd8), aRc=0, aStdout=op8 ,aPersist=True), 
                    exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                    exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0, aStdout="dbmulticloud-dataplane-integ-24.1.66.0.0-250317.1647.x86_64"),
                    exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=0, aStdout="pkcs-multicloud-driver-gcp-0.1-250515.0542.x86_64"),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _reshape = ebCluReshapeCompute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
         # Identify if this is Multicloud env
        _isMulticloud, _multicloudProvider = _reshape.mIsMulticloud(src_dom_u)
        self.assertEqual(_isMulticloud, True)
        self.assertEqual(_multicloudProvider, "GOOGLE")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mIsMulticloud_GOOGLE_file(self,mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveDBInstancesFromVMDbaascli")
        src_dom_u = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexVm(): [
                [                        
                    exaMockCommand(re.escape(cmd8), aRc=0, aStdout=op8 ,aPersist=True), 
                    exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                    exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0, aStdout="dbmulticloud-dataplane-integ-24.1.66.0.0-250317.1647.x86_64"),
                    exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=1),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=0, aStdout="pkcs-multicloud-driver-gcp-0.1-250515.0542.x86_64.rpm" ,aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _reshape = ebCluReshapeCompute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
         # Identify if this is Multicloud env
        _isMulticloud, _multicloudProvider = _reshape.mIsMulticloud(src_dom_u)
        self.assertEqual(_isMulticloud, True)
        self.assertEqual(_multicloudProvider, "GOOGLE")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mIsMulticloud_AWS_installed(self,mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveDBInstancesFromVMDbaascli")
        src_dom_u = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexVm(): [
                [                        
                    exaMockCommand(re.escape(cmd8), aRc=0, aStdout=op8 ,aPersist=True), 
                    exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                    exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0, aStdout="dbmulticloud-dataplane-integ-24.1.66.0.0-250317.1647.x86_64"),
                    exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=0, aStdout="pkcs-multicloud-driver-aws-0.1-250515.0542.x86_64"),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _reshape = ebCluReshapeCompute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
         # Identify if this is Multicloud env
        _isMulticloud, _multicloudProvider = _reshape.mIsMulticloud(src_dom_u)
        self.assertEqual(_isMulticloud, True)
        self.assertEqual(_multicloudProvider, "AWS")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mIsMulticloud_AWS_file(self,mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on cluelasticcompute.py:mRemoveDBInstancesFromVMDbaascli")
        src_dom_u = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexVm(): [
                [                        
                    exaMockCommand(re.escape(cmd8), aRc=0, aStdout=op8 ,aPersist=True), 
                    exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                    exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/rpm -qa | grep dbmulticloud-dataplane-integ", aRc=0, aStdout="dbmulticloud-dataplane-integ-24.1.66.0.0-250317.1647.x86_64"),
                    exaMockCommand("/bin/rpm -qa | grep pkcs-multicloud-driver", aRc=1),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/dbmulticloud-dataplane-integ*.rpm"), aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand(re.escape("/bin/ls /u02/app_acfs/pkcs-multicloud-driver*.rpm"), aRc=0, aStdout="pkcs-multicloud-driver-aws-0.1-250515.0542.x86_64.rpm" ,aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _reshape = ebCluReshapeCompute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
         # Identify if this is Multicloud env
        _isMulticloud, _multicloudProvider = _reshape.mIsMulticloud(src_dom_u)
        self.assertEqual(_isMulticloud, True)
        self.assertEqual(_multicloudProvider, "AWS")

    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU")
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateOEDAProperties')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsIsUp')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetU02Size')
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetNodeU02Size")
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mPatchXML")
    @patch("exabox.tools.oedacli.ebOedacli.run_oedacli")
    def test_mAddNode_exascale_OSTP_PREVM_INSTALL(self, mock_setsrc, mock_oradb, mock_properties, mock_shared, mock_crs, mock_hostname, mock_setu02size, mock_getu02size, mock_xml, mock_runoedacli):

        ebLogInfo("Running unit test on cluelasticcompute.py:mAddNode:EXASCALE:OSTP_PREVM_INSTALL")
    
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.jsonconf = json.loads(EXASCALE_ADD_NODE_PAYLOAD)
        fullOptions.steplist = "OSTP_PREVM_INSTALL"

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/usr/local/bin/imageinfo *", aRc=0, aStdout="20.1.12.0.0.210901" ,aPersist=True),
                    ],
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("test -e /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("mv /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.img", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("test -e /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("mv /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.kvm.img /EXAVMIMAGES/System.first.boot.20.1.12.0.0.210901.img", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                    ],
                    []
                ],
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("sed.*es.properties", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("cp.*", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("ping*", aRc=0, aStdout=""),
                        exaMockCommand("ping*", aRc=1, aStdout="", aPersist=True),
                    ]
                ]
            }                                        

        self.mPrepareMockCommands(_cmds)
        _reshape_obj = ebCluReshapeCompute( self.mGetClubox(), fullOptions)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            _reshape_obj.mSetSrcDom0(_dom0)
            _reshape_obj.mSetSrcDomU(_domU)
            break

        # This method in intended to test only until mAddDomU method
        # after that the connectivy change will fail
        try:
            _reshape_obj.mAddNode(fullOptions)
        except Exception as e:
            self.assertTrue("Connectivity checks" or "mConnectivityChecks" in str(e))


    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mUpdateKMSRPM_rpm_exists(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on mUpdateKMSRPM rpm exists")

        _cmds = {
                self.mGetRegexVm():
                [
                    [                        
                    exaMockCommand(re.escape(cmd8), aRc=0, aStdout=op8 ,aPersist=True), 
                    exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                    exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e /u02/opt/dbaas_images/libkmstdepkcs11.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rpm --force -Uhv /u02/opt/dbaas_images/kmstdecli.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rpm --force -Uhv /u02/opt/dbaas_images/libkmstdepkcs11.rpm", aRc=0, aStdout="", aPersist=True),
                    ]
                ]
        }

        self.mPrepareMockCommands(_cmds)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj.mUpdateKMSRPM('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com')

        ebLogInfo("Unit test on mUpdateKMSRPM rpm exists successful")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    def test_mUpdateKMSRPM_copy_from_images(self, mock_mGetOracleBaseDirectories):
        ebLogInfo("Running unit test on mUpdateKMSRPM copy from images")

        _cmds = {
                self.mGetRegexVm():
                [
                    [                        
                    exaMockCommand(re.escape(cmd8), aRc=0, aStdout=op8 ,aPersist=True), 
                    exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2, aPersist=True),
                    exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3, aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e /u02/opt/dbaas_images/kmstdecli.rpm", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e /u02/opt/dbaas_images/libkmstdepkcs11.rpm", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e images/kmstdecli.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e images/libkmstdepkcs11.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/cp images/kmstdecli.rpm /u02/opt/dbaas_images/kmstdecli.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/chown -fR oracle.oinstall /u02/opt/dbaas_images/kmstdecli.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/cp images/libkmstdepkcs11.rpm /u02/opt/dbaas_images/libkmstdepkcs11.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/chown -fR oracle.oinstall /u02/opt/dbaas_images/libkmstdepkcs11.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rpm --force -Uhv /u02/opt/dbaas_images/kmstdecli.rpm", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rpm --force -Uhv /u02/opt/dbaas_images/libkmstdepkcs11.rpm", aRc=0, aStdout="", aPersist=True),
                    ]
                ]
        }

        self.mPrepareMockCommands(_cmds)

        _obj = ebCluReshapeCompute( self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _obj.mUpdateKMSRPM('iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com')

        ebLogInfo("Unit test on mUpdateKMSRPM copy from images successful")
        
if __name__ == '__main__':
    unittest.main() 
