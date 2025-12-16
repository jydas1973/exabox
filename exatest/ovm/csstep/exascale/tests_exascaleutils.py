#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_exascaleutils.py /main/25 2025/11/27 16:55:04 pbellary Exp $
#
# tests_exascaleutils.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_exascaleutils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    11/24/25 - Enh 38685113 - EXASCALE: POST CONFIGURE EXASCALE EXACLOUD SHOULD FETCH STRE0/STE1 FROM DOM0
#    pbellary    11/05/25 - Bug 38473536 - EXASCALE VM STORAGE CONFIGURATION FAILING:ERROR:INVALID EXASCALECLUSTER NAM
#    pbellary    10/28/25 - Bug 38512539 - INCORRECT VM BACKUP CONF FILE AFTER MIGRATE FROM LOCAL TO EXASCALE BACKUP (EXASCALE IMAGES)
#    rajsag      10/07/25 - enh 38389132 - exacloud: autoencryption support for
#                           exascale configuration
#    pbellary    09/19/25 - Bug 38450242 - EXACLOUD SHOULD UPDATE FLASHCACHEMODE TO WRITEBACK AFTER UPDATING VLANID ON CELLS 
#    jfsaldan    08/26/25 - Enh 37999800 - EXACLOUD: EXASCALE CONFIG FLOW TO
#                           ENABLE AUTOFILEENCRYPTION=TRUE AFTER EXASCALE IS
#                           CONFIGURED
#    rajsag      08/06/25 - Enh 38208138 exascale phase 2: fetch stre0 and
#                           stre1 ips from exacloud for add node operation
#    pbellary    07/15/25 - Enh 37980305 - EXACLOUD TO SUPPORT CHANGE OF VM BACKUP STORAGE FROM LOCAL TO EXASCALE STORAGE (EXISTING CLUSTERS)
#    pbellary    06/27/25 - Bug 38123526 - EXASCALE: EXACLOUD SHOULD PATCH DNS/NTP SERVER DETAILS FOR XSCONFIG COMMAND 
#    rajsag      06/24/25 - enhancement request 37966939 - exascale vm image &
#                           vm backup vault operations
#    pbellary    05/21/25 - Enh 37698277 - EXASCALE: CREATE SERVICE FLOW TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT 
#    pbellary    04/16/25 - Enh 37842812 - EXASCALE: REFACTOR ACFS CREATION DURING CREATE SERVICE
#    pbellary    04/16/25 - Creation
#
import os
import re
import json
import copy
import time
import shutil
import unittest
from unittest import mock
import hashlib
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.exascale.exascaleutils import *
from exabox.ovm.csstep.exascale.escli_util import *
from exabox.ovm.csstep.cs_constants import csXSConstants
from exabox.core.Context import get_gcontext
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
import warnings

CREATE_DBVAULT_PAYLOAD = """ 
{
   "vault_op": "create",
   "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
   "storage_pool":"hcpool",
   "db_vault":{
      "name":"vault1clu02",
      "vault_ocid":"abcd-efgh-wxyz",
      "gb_size":10
   },
   "ctrl_network":{
      "ip":"10.0.130.110",
      "port":"5052",
      "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
   }
}
"""
UPDATE_SYSVAULT_PAYLOAD = """ 
{
   "vault_op": "create",
   "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
   "storage_pool":"hcpool",
   "system_vault":{
      "name":"vault1clu02",
      "vault_type":"image",
      "gb_size":20
   },
   "ctrl_network":{
      "ip":"10.0.130.110",
      "port":"5052",
      "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
   }
}
"""
CREATE_SYSVAULT_PAYLOAD = """ 
{
   "vault_op": "create",
   "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
   "storage_pool":"hcpool",
   "system_vault":{
      "name":"vault1clu02",
      "vault_type":"image",
      "vault_ocid":"abcd-efgh-wxyz",
      "gb_size":10
   },
   "compute_list": [
      "scaqab10adm01.us.oracle.com",
      "scaqab1adm01.us.oracle.com"
   ],
   "ctrl_network":{
      "ip":"10.0.130.110",
      "port":"5052",
      "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
   }
}
"""
CREATE_DBVAULT_OUTPUT = """ 
{"data":
       {"type":"vaults",
       "id":"vault1clu02",
       "attributes":
                   {"name":"vault1clu02",
                   "createTime":"2025-06-24T10:38:58-07:00",
                   "createdBy":"admin",
                   "spaceUsedEF":0,
                   "spaceUsedHC":0,
                   "spaceProvEF":0,
                   "spaceProvHC":32212254720,
                   "iopsProvEF":0,
                   "iopsProvHC":"unlimited",
                   "flashCacheProv":"unlimited",
                   "xrmemCacheProvHC":"unlimited",
                   "xrmemCacheProvEF":0,
                   "flashLogProv":true
                   }
       }
}
"""
CREATE_SYSVAULT_OUTPUT = """
{"data":
       {"type":"vaults",
       "id":"vault1clu02",
       "attributes":
                   {"name":"vault1clu02",
                   "createTime":"2025-06-24T10:38:58-07:00",
                   "createdBy":"admin",
                   "spaceUsedEF":0,
                   "spaceUsedHC":0,
                   "spaceProvEF":0,
                   "spaceProvHC":32212254720,
                   "iopsProvEF":0,
                   "iopsProvHC":"unlimited",
                   "flashCacheProv":"unlimited",
                   "xrmemCacheProvHC":"unlimited",
                   "xrmemCacheProvEF":0,
                   "flashLogProv":true
                   }
       }
}
"""
LS_DBVAULT_OUTPUT = """ 
{"data":
       {"type":"vaults",
       "id":"vault_test",
       "attributes":
                   {"spaceProvHC":10995116277760
                   }
       }
}
"""
STORAGE_POOL_RESPONSE = """
{"data":
       {"type":"storagePools",
       "id":"hcpool",
       "attributes":
                   {"spaceRaw":98956046499840,
                  "spaceProvisioned":10995116277760,
                  "spaceUsed":6439343161344
                  }
       }
}
"""
DELETE_DBVAULT_PAYLOAD = """ 
{
   "vault_op": "delete",
   "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
   "storage_pool":"hcpool",
   "db_vault":{
      "name":"vault1clu02",
      "vault_ocid":"abcd-efgh-wxyz"
   },
   "ctrl_network":{
      "ip":"10.0.130.110",
      "port":"5052",
      "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
   }
}
"""
DELETE_SYSVAULT_PAYLOAD = """ 
{
   "vault_op": "delete",
   "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
   "storage_pool":"hcpool",
   "system_vault":{
      "name":"vault1clu02",
      "vault_ocid":"abcd-efgh-wxyz",
      "vault_type":"image"
   },
   "ctrl_network":{
      "ip":"10.0.130.110",
      "port":"5052",
      "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
   }
}
"""
UPDATE_DBVAULT_PAYLOAD = """ 
{
   "vault_op": "update",
   "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
   "storage_pool":"hcpool",
   "db_vault":{
      "name":"vault1clu02",
      "vault_ocid":"abcd-efgh-wxyz",
      "gb_size":20
   },
   "ctrl_network":{
      "ip":"10.0.130.110",
      "port":"5052",
      "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
   }
}
"""
UPDATE_DBVAULT_PAYLOAD = """ 
{
   "vault_op": "create",
   "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
   "storage_pool":"hcpool",
   "db_vault":{
      "name":"vault1clu02",
      "vault_ocid":"abcd-efgh-wxyz",
      "gb_size":15
   },
   "ctrl_network":{
      "ip":"10.0.130.110",
      "port":"5052",
      "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
   }
}
"""

GET_DBVAULT_PAYLOAD = """ 
{
    "vault_op": "get",
    "storage_pool":"hcpool",
    "db_vaults": [
    {
        "ctrl_network": {
           "ip": "10.0.130.110",
           "port": 5052
        },
        "db_vault": {
           "name": "vault1clu02",
           "vault_ocid": "abcd"
        },
        "cell_list":[
        "scaqar01celadm01.us.oracle.com",
        "scaqar01celadm02.us.oracle.com",
        "scaqar01celadm03.us.oracle.com"
        ]
     },
     {
        "ctrl_network": {
           "ip": "10.0.130.110",
           "port": 5052
        },
        "db_vault": {
           "name": "vault1clu04",
           "vault_ocid": "efgh"
        },
        "cell_list":[
        "scaqar01celadm01.us.oracle.com",
        "scaqar01celadm02.us.oracle.com",
        "scaqar01celadm03.us.oracle.com"
        ]
     }
    ]
}
"""
GETDBVAULT_RESPONSE = """
{
   "db_vaults":[
      {
         "name":"xsvlt-86782-01",
         "ref_id":"xsvlt-86782-01",
         "total_storage_gb":4096,
         "used_storage_gb":729,
         "vault_ocid":"ocid1.exascaledbstoragevault.region1.sea.anzwkljrjajnm5ia7rekol27ehjhye4riqe2ktlgzxxo6v255rbnelvmwnka"
      },
      {
         "name":"xsvlt-86782-00",
         "ref_id":"xsvlt-86782-00",
         "total_storage_gb":4096,
         "used_storage_gb":200,
         "vault_ocid":"ocid1.exascaledbstoragevault.region1.sea.anzwkljrjajnm5ialnjhhcz4g6b2yuzkh4gknltqcegnqxmyg5v5o6rzhmna"
      }
   ],
   "storage_pool":{
      "gb_provisioned_size":8192,
      "gb_total_size":57343,
      "gb_used_size":755,
      "name":"hcpool"
   }
}
"""
UPDATE_SYS_DBVAULT_PAYLOAD = """
{
    "vault_op": "get",
    "storage_pool":"hcpool",
    "db_vaults": [
    {
        "ctrl_network": {
           "ip": "10.0.130.110",
           "port": 5052
        },
        "db_vault": {
           "name": "vault1clu02",
           "vault_ocid": "abcd"
        },
        "cell_list":[
        "scaqar01celadm01.us.oracle.com",
        "scaqar01celadm02.us.oracle.com",
        "scaqar01celadm03.us.oracle.com"
        ]
     },
     {
        "ctrl_network": {
           "ip": "10.0.130.110",
           "port": 5052
        },
        "db_vault": {
           "name": "vault1clu04",
           "vault_ocid": "efgh"
        },
        "cell_list":[
        "scaqar01celadm01.us.oracle.com",
        "scaqar01celadm02.us.oracle.com",
        "scaqar01celadm03.us.oracle.com"
        ]
     }
     ],
    "system_vaults":[
      {
         "vault_type":"backup",
         "vault_ocid":"abcd-efgh-wxyz",
         "name":"backupvault1clu02"
      },
      {
         "vault_type":"image",
         "vault_ocid":"abcd-efgh-wxy",
         "name":"imagevault1clu02"
      }
      ],
      "exascale":{
         "cell_list":[
        "scaqar01celadm01.us.oracle.com",
        "scaqar01celadm02.us.oracle.com",
        "scaqar01celadm03.us.oracle.com"
        ],
        "ctrl_network":{
         "ip": "10.0.130.110",
         "port":5052
        }
      }
}
"""
CREATE_SERVICE_PAYLOAD = """ 
{
   "exascale":{
      "network_services":{
         "dns":[
            "169.254.169.254"
         ],
         "ntp":[
            "169.254.169.254"
         ]
      },
      "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
      "exascale_cluster_name":"sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers",
      "storage_pool":{
         "name":"hcpool",
         "gb_size":"10240"
      },
      "db_vault":{
         "name":"vault1clu02",
         "gb_size":10
      },
      "ctrl_network":{
         "ip":"10.0.130.110",
         "port":"5052",
         "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
      }
    },
   "rack":{
      "storageType":"XS",
      "xsVmImage": "True",
      "xsVmBackup": "True",
      "system_vault": [
            {
                "vault_type":"image",
                "name":"imagevault"
            },
             {
                "vault_type":"backup",
                "name":"backupvault",
                "xsVmBackupRetentionNum": "2"
            }
      ]
   }
}
"""

EXASCALE_PAYLOAD = """ 
{
   "exascale":{
      "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
      "exascale_cluster_name":"sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers",
      "storage_pool":{
         "name":"hcpool",
         "gb_size":"10240"
      },
      "db_vault":{
         "name":"vault1clu02",
         "gb_size":10
      },
      "ctrl_network":{
         "ip":"10.0.130.110",
         "port":"5052",
         "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
      },
      "host_nodes": [
         {
            "compute_hostname": "scaqab10adm01.us.oracle.com"
         }
      ]
    },
   "acfs":[
      {
         "name":"additional_acfs",
         "mount_path":"acfs_1",
         "gb_size":10
      }
   ],
   "acfs_op": "create",
   "exadataInfraId": "etf_infra_230603_111"
}
"""

EXASCALE_CONFIG_PAYLOAD = """ 
{
   "exascale":{
      "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
      "exascale_cluster_name":"sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers",
      "storage_pool":{
         "name":"hcpool",
         "gb_size":"10240"
      },
      "db_vault":{
         "name":"vault1clu02",
         "gb_size":10
      },
      "ctrl_network":{
         "ip":"10.0.130.110",
         "port":"5052",
         "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
      }
    },
   "acfs":[
      {
         "name":"additional_acfs",
         "mount_path":"acfs_1",
         "gb_size":10
      }
   ],
   "acfs_op": "create",
   "exadataInfraId": "etf_infra_230603_111",
   "config_op": "config"
}
"""

ENABLE_XS_CONFIG_PAYLOAD = """
{
   "exascale":{
      "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
      "exascale_cluster_name":"sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers",
      "storage_pool":{
         "name":"hcpool",
         "gb_size":"10240"
      },
      "db_vault":{
         "name":"vault1clu02",
         "gb_size":10
      },
      "ctrl_network":{
         "ip":"10.0.130.110",
         "port":"5052",
         "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
      },
      "storage_vlan_id": "631"
    },
   "config_op": "config",
   "storageType": "XS"
}
"""

UNMOUNT_ACFS_PAYLOAD = """ 
{
   "exascale":{
      "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
      "exascale_cluster_name":"sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers",
      "storage_pool":{
         "name":"hcpool",
         "gb_size":"10240"
      },
      "db_vault":{
         "name":"vault1clu02",
         "gb_size":10
      },
      "ctrl_network":{
         "ip":"10.0.130.110",
         "port":"5052",
         "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
      }
    },
   "acfs":[
      {
         "name":"additional_acfs"
      }
   ],
   "acfs_op": "create",
   "exadataInfraId": "etf_infra_230603_111"
}
"""
XS_GET_PAYLOAD = """
{
   "host_nodes": ["scaqab10adm01.us.oracle.com","scaqab10adm02.us.oracle.com","scaqab10adm03.us.oracle.com"],
   "operation": "fetch_compute_details"
}
"""
XS_GET_PAYLOAD_1 = """
{
   "host_nodes": ["scaqab10adm01.us.oracle.com"],
   "operation": "fetch_compute_details"   
}
"""
XS_PUT_PAYLOAD="""
{
    "exascale": {
        "cell_list": [
            "scaqar01celadm01.us.oracle.com",
            "scaqar01celadm02.us.oracle.com",
            "scaqar01celadm03.us.oracle.com"
        ],
        "ctrl_network": {
            "ip": "10.0.130.110",
            "name": "scaqar01ers01.us.oracle.com",
            "port": "5052"
        },
        "db_vault": {
            "gb_size": 4096,
            "name": "xsvlt-27524-02"
        },
        "storage_pool": {
            "gb_size": "61440",
            "name": "hcpool"
        }
    },
    "operation": "config-auto-encryption"
}
"""
XS_UPDATE_STORAGE_POOL="""
{
    "concurrent_operation": "true",
    "config_op": "updatestoragepool",
    "exascale": {
        "cell_list": [
            "scaqar01celadm01.us.oracle.com",
            "scaqar01celadm02.us.oracle.com",
            "scaqar01celadm03.us.oracle.com"
        ],
        "ctrl_network": {
            "ip": "10.0.130.110",
            "name": "scaqar01ers01.us.oracle.com",
            "port": "5052"
        },
        "storage_pool": {
            "gb_size": 102400,
            "name": "hcpool"
        }
    },
    "storageType": "XS"
}
"""


ADD_NODE_PAYLOAD="""
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
            "scaqar01celadm01.us.oracle.com",
            "scaqar01celadm02.us.oracle.com",
            "scaqar01celadm03.us.oracle.com"
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
                "compute_hostname": "scaqab10adm03.us.oracle.com",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.0.0",
                "priv1": "sea201733exdd007-priv1",
                "priv2": "sea201733exdd007-priv2",
                "storage_ip1": "100.106.2.0",
                "storage_ip2": "100.106.2.1"
            },
            {
                "compute_hostname": "scaqab10adm02.us.oracle.com",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.0.0",
                "priv1": "sea201733exdd006-priv1",
                "priv2": "sea201733exdd006-priv2",
                "storage_ip1": "192.168.132.18",
                "storage_ip2": "192.168.132.19"
            },
            {
                "compute_hostname": "scaqab10adm01.us.oracle.com",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.0.0",
                "priv1": "sea201733exdd005-priv1",
                "priv2": "sea201733exdd005-priv2",
                "storage_ip1": "192.168.132.20",
                "storage_ip2": "192.168.132.21"
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
                "compute_node_hostname": "scaqab10adm03.us.oracle.com",
                "db_info": [],
                "eth0_removed": "False",
                "model": "X10M-2",
                "network_info": {
                    "computenetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "scaqab10adm03.us.oracle.com",
                                    "gateway": "10.0.160.1",
                                    "ipaddr": "10.0.160.136",
                                    "master": "eth0",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "private": [
                                {
                                    "fqdn": "sea201733exdd007-priv1.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                                    "ipaddr": "192.168.132.16"
                                },
                                {
                                    "fqdn": "sea201733exdd007-priv2.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                                    "ipaddr": "192.168.132.17"
                                }
                            ]
                        },
                        {
                            "ilom": [
                                {
                                    "fqdn": "sea201733exdd007lo.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.160.1",
                                    "ipaddr": "10.0.160.150",
                                    "netmask": "255.255.240.0"
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
                    "uloc": "7"
                },
                "racktype": "1205",
                "virtual_compute_info": {
                    "compute_node_hostname": "idcxsedvaddnodetest-pipsa3.client.clusters.oraclevcn.com",
                    "network_info": {
                        "virtualcomputenetworks": [
                            {
                                "private": [
                                    {
                                        "fqdn": "sea201733exddu0701-stre0.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                                        "ipaddr": "100.106.72.4"
                                    },
                                    {
                                        "fqdn": "sea201733exddu0701-stre1.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                                        "ipaddr": "100.106.72.5"
                                    }
                                ]
                            },
                            {
                                "admin": [
                                    {
                                        "fqdn": "idcxsedvaddnodetest-pipsa3.client.clusters.oraclevcn.com"
                                    }
                                ]
                            },
                            {
                                "client": [
                                    {
                                        "fqdn": "idcxsedvaddnodetest-pipsa3.client.clusters.oraclevcn.com",
                                        "gateway": "10.0.0.1",
                                        "ipaddr": "10.0.8.120",
                                        "mac": "00:00:17:01:59:20",
                                        "mtu": "9000",
                                        "natdomain": "sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                                        "nathostname": "sea201733exddu0701",
                                        "natip": "10.0.160.181",
                                        "natnetmask": "255.255.240.0",
                                        "netmask": "255.255.240.0",
                                        "slaves": "eth1 eth2",
                                        "standby_vnic_mac": "00:00:17:01:66:54",
                                        "vlantag": "1"
                                    }
                                ]
                            },
                            {
                                "backup": [
                                    {
                                        "fqdn": "idcxsedvaddnodetest-pipsa3-backup.backup.clusters.oraclevcn.com",
                                        "gateway": "10.0.16.1",
                                        "ipaddr": "10.0.29.244",
                                        "mac": "00:00:17:01:0D:56",
                                        "mtu": "9000",
                                        "netmask": "255.255.240.0",
                                        "slaves": "eth1 eth2",
                                        "standby_vnic_mac": "00:00:17:01:8A:E0",
                                        "vlantag": "2"
                                    }
                                ]
                            },
                            {
                                "interconnect": [
                                    {
                                        "fqdn": "sea201733exddu0701-clre0.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                                        "ipaddr": "100.107.2.4"
                                    },
                                    {
                                        "fqdn": "sea201733exddu0701-clre1.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                                        "ipaddr": "100.107.2.5"
                                    }
                                ]
                            },
                            {
                                "vip": [
                                    {
                                        "fqdn": "idcxsedvaddnodetest-pipsa3-vip.client.clusters.oraclevcn.com",
                                        "ipaddr": "10.0.13.175"
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
                "compute_node_hostname": "scaqab10adm01.us.oracle.com",
                "compute_node_virtual_hostname": "idcxsedvaddnodetest-pipsa1.client.clusters.oraclevcn.com"
            },
            {
                "compute_node_hostname": "scaqab10adm02.us.oracle.com",
                "compute_node_virtual_hostname": "idcxsedvaddnodetest-pipsa3.client.clusters.oraclevcn.com"
            },
            {
                "compute_node_hostname": "scaqab10adm03.us.oracle.com",
                "compute_node_virtual_hostname": "idcxsedvaddnodetest-pipsa2.client.clusters.oraclevcn.com"
            }
        ],
        "participating_computes": [
            {
                "compute_node_alias": "dbserver-1",
                "compute_node_hostname": "scaqab10adm01.us.oracle.com",
                "eth0_removed": "False",
                "model": "X10M-2",
                "racktype": "1205",
                "volumes": []
            },
            {
                "compute_node_alias": "dbserver-2",
                "compute_node_hostname": "scaqab10adm02.us.oracle.com",
                "eth0_removed": "False",
                "model": "X10M-2",
                "racktype": "1205",
                "volumes": []
            },
            {
                "compute_node_alias": "dbserver-3",
                "compute_node_hostname": "scaqab10adm03.us.oracle.com",
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
                "compute_node_hostname": "scaqab10adm01.us.oracle.com",
                "eth0_removed": "False",
                "model": "X10M-2",
                "racktype": "1205",
                "volumes": []
            },
            {
                "compute_node_alias": "dbserver-2",
                "compute_node_hostname": "scaqab10adm02.us.oracle.com",
                "eth0_removed": "False",
                "model": "X10M-2",
                "racktype": "1205",
                "volumes": []
            }
        ]
    }
}
"""

class SSHIOObject(object):
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

IFCONFIG_STRE0 = ["""
[root@sea201732exdcl06 ~]# /usr/sbin/ip addr show stre0
7: stre0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000
    link/ether 66:c6:98:6b:ca:55 brd ff:ff:ff:ff:ff:ff
    altname enp33s0f0v0
    altname ens5f0v0
    inet 100.106.0.12/16 brd 100.106.255.255 scope global noprefixroute stre0
       valid_lft forever preferred_lft forever
"""]

IFCONFIG_STRE1 = ["""
[root@sea201732exdcl06 ~]# /usr/sbin/ip addr show stre1
8: stre1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000
    link/ether 66:07:9f:95:5e:59 brd ff:ff:ff:ff:ff:ff
    altname enp33s0f1v0
    altname ens5f1v0
    inet 100.106.0.13/16 brd 100.106.255.255 scope global noprefixroute stre1
       valid_lft forever preferred_lft forever
"""]

class ebTestExascaleUtils(ebTestClucontrol):

   @classmethod
   def setUpClass(self):
        super(ebTestExascaleUtils, self).setUpClass(aGenerateDatabase = True, aUseOeda = True)
        self.mGetClubox(self).mSetUt(True)
        warnings.filterwarnings("ignore")

   @mock.patch("exabox.tools.ebTree.ebTree.ebTree.mExportXml")
   @mock.patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun")
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetExascaleName', return_value=("", "sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers"))
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetCtrlIP', return_value=("10.0.130.110", "sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"))
   def test_mEnableXSService(self, mock_mGetExascaleName, mock_mGetCtrlIP, mock_mRun, mock_mExportXml):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)
       _cell_list = _ebox.mReturnCellNodes()
       _cell = list(_cell_list.keys())[0]
       _cmds = { 
                    self.mGetRegexCell():                                       
                    [ 
                         [
                             exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                             exaMockCommand("/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name", aRc=0 ,aStdout="exc_egs_cluster_name=iad1d2cl38d89abcae38c4e2f8b1922b6289c1384clu01ers", aPersist=True),
                         ],
                         [
                              exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                              exaMockCommand("/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name", aRc=0, aStdout="sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers" ,aPersist=True)
                         ],
                         [
                              exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True)
                         ]
                    ],
                    self.mGetRegexLocal():                           
                    [
                     [
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                    ]
                }
       self.mPrepareMockCommands(_cmds)  

       _xml_save_dir = os.getcwd() + '/' + 'clusters/' + self.mGetClubox().mGetKey() + '/config'
       if not os.path.exists(_xml_save_dir):
          os.makedirs(_xml_save_dir)
       _xs_log_dir = os.getcwd() + '/' + 'log/xs_exatest/'
       if not os.path.exists(_xs_log_dir):
          os.makedirs(_xs_log_dir)
       _path_config = _xml_save_dir + '/exascale1.xml'
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _path_config)
       ebLogInfo(f"ConfigPath: {self.mGetClubox().mGetConfigPath()}")
       _ebox.mSetPatchConfig(_path_config)
       ebLogInfo(f"PatchConfig: {_path_config}")

       _oeda_path  = _ebox.mGetOedaPath()
       _savexmlpath = _oeda_path + '/exacloud.conf'
       if not os.path.exists(_savexmlpath):
          os.makedirs(_savexmlpath)
       _dns_ntp_xml = _savexmlpath + "/patched_ntp_dns_exatest.xml"
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _dns_ntp_xml)

       with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetBasePath', return_value=_xs_log_dir):
           self.mGetClubox().mSetCmd('xsconfig')
           _utils = ebExascaleUtils(_ebox)
           _utils.mEnableXSService(_options)

   @mock.patch("exabox.tools.ebTree.ebTree.ebTree.mExportXml")
   @mock.patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun")
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mFetchStorageInterconnectIps', return_value=("100.106.2.1", "100.106.2.2", "255.255.0.0"))
   @patch('exabox.ovm.csstep.exascale.exascaleutils.OedacliCmdMgr.mUpdateEGSClusterName')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetExascaleName', return_value=("", "sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers"))
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetCtrlIP', return_value=("10.0.130.110", "sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"))
   def test_mPatchEGSClusterName(self, mock_mGetExascaleName, mock_mGetCtrlIP, mock_mUpdateEGSClusterName, mock_mFetchStorageInterconnectIps, mock_mRun, mock_mExportXml):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)
       _cell_list = _ebox.mReturnCellNodes()
       _cell = list(_cell_list.keys())[0]
       _cmds = { 
                    self.mGetRegexCell():                                       
                    [ 
                         [
                             exaMockCommand("/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name", aRc=0 ,aStdout="exc_egs_cluster_name=iad1d2cl38d89abcae38c4e2f8b1922b6289c1384clu01ers", aPersist=True),
                         ],
                         [
                              exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                              exaMockCommand("/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name", aRc=0, aStdout="sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers" ,aPersist=True)
                         ],
                         [
                              exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                              exaMockCommand("/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name", aRc=0 ,aStdout="exc_egs_cluster_name=iad1d2cl38d89abcae38c4e2f8b1922b6289c1384clu01ers", aPersist=True)
                         ]
                    ],
                    self.mGetRegexLocal():                           
                    [
                     [
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                    ]
                }
       self.mPrepareMockCommands(_cmds)  

       _xml_save_dir = os.getcwd() + '/' + 'clusters/' + self.mGetClubox().mGetKey() + '/config'
       if not os.path.exists(_xml_save_dir):
          os.makedirs(_xml_save_dir)
       _xs_log_dir = os.getcwd() + '/' + 'log/xs_exatest/'
       if not os.path.exists(_xs_log_dir):
          os.makedirs(_xs_log_dir)
       _path_config = _xml_save_dir + '/exascale1.xml'
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _path_config)
       ebLogInfo(f"ConfigPath: {self.mGetClubox().mGetConfigPath()}")
       _ebox.mSetPatchConfig(_path_config)
       ebLogInfo(f"PatchConfig: {_path_config}")

       _oeda_path  = self.mGetClubox().mGetOedaPath()
       _path = _oeda_path + '/exacloud.conf'
       if not os.path.isdir(_path):
          os.makedirs(_path)
       _updatedxml = _oeda_path + '/exacloud.conf/exascale_exatest.xml'
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _updatedxml)

       _oeda_path  = _ebox.mGetOedaPath()
       _savexmlpath = _oeda_path + '/exacloud.conf'
       if not os.path.exists(_savexmlpath):
          os.makedirs(_savexmlpath)
       _dns_ntp_xml = _savexmlpath + "/patched_ntp_dns_exatest.xml"
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _dns_ntp_xml)

       with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetBasePath', return_value=_xs_log_dir):
           self.mGetClubox().mSetCmd('info')
           _utils = ebExascaleUtils(_ebox)
           _utils.mEnableXSService(_options)
           _utils.mPatchEGSClusterName(_options)

   def test_mIsEDVImageSupported(self):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
       _ebox.mSetEnableKVM(True)

       _utils = ebExascaleUtils(_ebox)
       _status = _utils.mIsEDVImageSupported(_options)
       self.assertEqual(_status, True)

   def test_mIsEDVBackupSupported(self):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
       _ebox.mSetEnableKVM(True)

       _utils = ebExascaleUtils(_ebox)
       _status = _utils.mIsEDVBackupSupported(_options)
       self.assertEqual(_status, True)

   def test_mCreateVMbackupJson(self):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
       _ebox.mSetEnableKVM(True)

       _cmds = { 
                  self.mGetRegexDom0():                                       
                    [ 
                         [
                             exaMockCommand(f"/bin/test -e *", aRc=0, aPersist=True),
                             exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True)

                         ]
                    ]
               }
       self.mPrepareMockCommands(_cmds) 

       _utils = ebExascaleUtils(_ebox)
       _utils.mCreateVMbackupJson(_options)

   @patch("exabox.core.Node.exaBoxNode.mReadFile")
   def test_mMigrateVMbackupJsonP01(self, mock_mReadFile):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
       _ebox.mSetEnableKVM(True)
       _vm_json = """{ "backup_type": "Legacy", "exascale_backup_vault": "", "source_vm_images": "Exascale", "exascale_images_vault": "xsvlt-19789-sys-image-00", "exascale_retention_num": 2, "exascale_ers_ip_port": "10.0.163.167:5052"}"""
       mock_mReadFile.return_value = _vm_json

       _cmds = { 
                  self.mGetRegexDom0():                                       
                    [ 
                         [
                             exaMockCommand(f"/bin/test -e *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True),
                             exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/cat /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True, aStdout=_vm_json)
                         ],
                         [
                             exaMockCommand(f"/bin/test -e *", aRc=0, aPersist=True),
                             exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True)
                         ]
                    ]
               }
       self.mPrepareMockCommands(_cmds) 

       _utils = ebExascaleUtils(_ebox)
       _utils.mMigrateVMbackupJson(_options)

   @patch("exabox.core.Node.exaBoxNode.mReadFile")
   def test_mMigrateVMbackupJsonP02(self, mock_mReadFile):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
       _ebox.mSetEnableKVM(True)
       _vm_json = """{ "backup_type": "Legacy", "exascale_backup_vault": "", "source_vm_images": "Exascale", "exascale_images_vault": "xsvlt-19789-sys-image-00", "exascale_retention_num": 2, "exascale_ers_ip_port": "10.0.163.167:5052"}"""
       mock_mReadFile.return_value = _vm_json

       _cmds = { 
                  self.mGetRegexDom0():                                       
                    [ 
                         [
                             exaMockCommand(f"/bin/test -e *", aRc=1, aPersist=True),
                             exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True),
                             exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/cat /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True, aStdout=_vm_json)
                         ],
                         [
                             exaMockCommand(f"/bin/test -e *", aRc=1, aPersist=True),
                             exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/mkdir -p /opt/oracle/vmbackup/conf/", aRc=0, aPersist=True)
                         ],
                         [
                             exaMockCommand(f"/bin/test -e *", aRc=1, aPersist=True),
                             exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/mkdir -p /opt/oracle/vmbackup/conf/", aRc=0, aPersist=True)
                         ]
                    ]
               }
       self.mPrepareMockCommands(_cmds) 

       _utils = ebExascaleUtils(_ebox)
       _utils.mMigrateVMbackupJson(_options)

   def test_mRemoveVMbackupJson(self):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
       _ebox.mSetEnableKVM(True)

       _cmds = { 
                  self.mGetRegexDom0():                                       
                    [ 
                         [
                             exaMockCommand(f"/bin/test -e *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True)

                         ]
                    ]
               }
       self.mPrepareMockCommands(_cmds) 

       _utils = ebExascaleUtils(_ebox)
       _utils.mRemoveVMbackupJson(_options)

   def test_mCreateVMbackupNodesConf(self):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
       _ebox.mSetEnableKVM(True)

       _cmds = { 
                  self.mGetRegexDom0():                                       
                    [ 
                         [
                             exaMockCommand(f"/bin/test -e *", aRc=0, aPersist=True),
                             exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True)
                         ]
                    ]
               }
       self.mPrepareMockCommands(_cmds) 

       _utils = ebExascaleUtils(_ebox)
       _utils.mCreateVMbackupNodesConf(_options)

   def test_mConfigureEDVbackup(self):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
       _ebox.mSetEnableKVM(True)

       _cmds = { 
                  self.mGetRegexDom0():                                       
                    [ 
                         [
                             exaMockCommand(f"/bin/test -e *", aRc=0, aPersist=True),
                             exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                             exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True)
                         ]
                    ]
               }
       self.mPrepareMockCommands(_cmds) 

       _utils = ebExascaleUtils(_ebox)
       _utils.mConfigureEDVbackup(_options)

   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCopyFile')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.OedacliCmdMgr.mUpdateEDVVolumes')
   def test_mPatchEDVVolumes(self, mock_mUpdateEDVVolumes, mock_mCopyFile):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
       _cmds = { 
                    self.mGetRegexLocal():                           
                    [
                     [
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                    ]
                }
       self.mPrepareMockCommands(_cmds)  

       _oeda_path  = self.mGetClubox().mGetOedaPath()
       _path = _oeda_path + '/exacloud.conf'
       if not os.path.isdir(_path):
          os.makedirs(_path)
       _updatedxml = _oeda_path + '/exacloud.conf/patched_edv_volumes_exatest.xml'
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _updatedxml)

       _utils = ebExascaleUtils(_ebox)
       _utils.mPatchEDVVolumes(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateEDVVolumeAttachment')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateEDVVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterID', return_value=("gridclub086e35-128", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c"))
   def test_mRegisterACFS(self,  mock_mGetClusterID, mock_mCreateEDVVolume, mock_mGetVolumeID, mock_mCreateEDVVolumeAttachment, mock_mCreateACFSFileSystem):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mRegisterACFS(_cell, _options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateEDVVolumeAttachment')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateEDVVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterID', return_value=("gridclub086e35-128", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c"))
   def test_mCreateACFS(self,  mock_mGetClusterID, mock_mCreateEDVVolume, mock_mGetVolumeID, mock_mCreateEDVVolumeAttachment, mock_mCreateACFSFileSystem):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mCreateACFS(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   def test_mResizeACFS(self,  mock_mGetVolumeID, mock_mChangeVolume):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _cmds = { 
                    self.mGetRegexVm():                                       
                    [ 
                         [
                             exaMockCommand("/usr/sbin/acfsutil size 10GB /acfs_1", aRc=0 ,aPersist=True),
                         ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)  

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mResizeACFS(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mMountACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterID', return_value=("gridclub086e35-128", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c"))
   def test_mMountACFS(self,  mock_mGetClusterID, mock_mGetVolumeID, mock_mMountACFSFileSystem):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mMountACFS(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("1:6cafd8310b3d49a2becd17e9c08f7919", "/acfs_1", "10.0000G"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   def test_mGetACFSSize(self,  mock_mGetVolumeID, mock_mGetACFSFileSystem, mock_mMountACFSFileSystem):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(UNMOUNT_ACFS_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _data_d = _utils.mGetACFSSize(_options)
        if _data_d and "acfs" in list(_data_d.keys()):
            _size_gb = _data_d["acfs"][0]["gb_size"]
            self.assertEqual(_size_gb, 10)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("1:6cafd8310b3d49a2becd17e9c08f7919", "", ""))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   def test_mUnMountACFS(self,  mock_mGetVolumeID, mock_mGetACFSFileSystem, mock_mMountACFSFileSystem):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(UNMOUNT_ACFS_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mUnMountACFS(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVAttachment')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("1:6cafd8310b3d49a2becd17e9c08f7919", "", ""))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "dev_additional_acfs"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   def test_mRemoveACFS(self,  mock_mGetVolumeID, mock_mGetVolumeAttachments, mock_mGetACFSFileSystem, mock_mUnMountACFSFileSystem, mock_mRemoveACFSFileSystem, mock_mRemoveEDVAttachment, mock_mRemoveEDVVolume):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(UNMOUNT_ACFS_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mRemoveACFS(_options)

   @patch('exabox.utils.node.connect_to_host')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True)
   @patch('time.sleep', return_value=None)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVAttachment')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "dev_additional_acfs"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetUser', return_value="gridiad1046clu040a1")
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value="1:6cafd8310b3d49a2becd17e9c08f7919")
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterID', return_value=("gridclub086e35-128", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c"))
   def test_mRemoveDefaultAcfsVolume(self,  mock_mGetClusterID, mock_mGetVolumeID, mock_mGetACFSFileSystem, mock_mUnMountACFSFileSystem, mock_mRemoveACFSFileSystem, 
                                     mock_mGetUser, mock_mGetVolumeAttachments, mock_mRemoveEDVAttachment, mock_mRemoveEDVVolume, mock_sleep, mock_mPingHost, mock_connect_to_host):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _cmds = { 
                self.mGetRegexVm():                                       
                [ 
                     [
                         exaMockCommand("/bin/rm -rf /var/opt/oracle/dbaas_acfs/", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ]
                }
        self.mPrepareMockCommands(_cmds)  

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mRemoveDefaultAcfsVolume(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value="1:6cafd8310b3d49a2becd17e9c08f7919")
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterID', return_value=("gridclub086e35-128", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c"))
   def test_mUnRegisterACFS(self,  mock_mGetClusterID, mock_mGetVolumeID, mock_mGetACFSFileSystem, mock_mUnMountACFSFileSystem, mock_mRemoveACFSFileSystem):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mUnRegisterACFS(_options)

   @patch('time.sleep', return_value=None)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVAttachment')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "dev_additional_acfs"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetUser', return_value="gridiad1046clu040a1")
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterID', return_value=("gridiad1046clu040a1", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c"))
   def test_mDetachAcfsVolume(self, mock_mGetClusterID, mock_mGetUser, mock_mGetVolumeID, mock_mGetVolumeAttachments, mock_mRemoveEDVAttachment, mock_mRemoveEDVVolume, mock_sleep):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mDetachAcfsVolume(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveFile')
   def test_mDeleteFilesInDbVault(self, mock_mRemoveFile):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mDeleteFilesInDbVault(_options)

        _ebox.mSetOciExacc(True)
        _utils.mDeleteFilesInDbVault(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "c3716n16c2_u02_6bb25ab338ee4a2298ef628c2403829a"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateEDVVolumeAttachment')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetEDVInitiator', return_value="2:b4d00303b12f46d6a31b4a5339395cd3")
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateEDVVolume')
   def test_mCreateU02Volume(self, mock_mCreateEDVVolume, mock_mGetVolumeID, mock_mGetEDVInitiator, 
                             mock_mCreateEDVVolumeAttachment, mock_mGetVolumeAttachments):
        _ebox = self.mGetClubox()
        _ddpair = _ebox.mReturnDom0DomUPair()
        _dom0, _domU = _ddpair[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _dom0_short_name = _dom0.split('.')[0]
        _domU_short_name = _domU.split('.')[0]
        _u02_vol_name = _domU_short_name + "_u02"
        _disk_u02_size = "60GB"
        _utils = ebExascaleUtils(_ebox)
        _utils.mCreateU02Volume(_dom0_short_name, _u02_vol_name, _disk_u02_size, _options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVAttachment')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "c3716n16c2_u02_6bb25ab338ee4a2298ef628c2403829a"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   def test_mRemoveU02Volume(self, mGetVolumeID, mock_mGetVolumeAttachments, mock_mRemoveEDVAttachment, 
                             mock_mRemoveEDVVolume):
        _ebox = self.mGetClubox()
        _ddpair = _ebox.mReturnDom0DomUPair()
        _dom0, _domU = _ddpair[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _dom0_short_name = _dom0.split('.')[0]
        _domU_short_name = _domU.split('.')[0]
        _u02_vol_name = _domU_short_name + "_u02"
        _utils = ebExascaleUtils(_ebox)
        _utils.mRemoveGuestEDVVolume(_dom0_short_name, _u02_vol_name, _options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVAttachment')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "c3716n16c2_u02_6bb25ab338ee4a2298ef628c2403829a"))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   def test_mRemoveGuestEDVVolumes(self, mGetVolumeID, mock_mGetVolumeAttachments, mock_mRemoveEDVAttachment, 
                             mock_mRemoveEDVVolume):
        _ebox = self.mGetClubox()
        _ddpair = _ebox.mReturnDom0DomUPair()
        _dom0, _domU = _ddpair[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mRemoveGuestEDVVolumes(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeACL')
   def test_mUpdateACL(self, mock_mChangeACL):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mUpdateACL(_options)

   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNode')
   def test_mEnableQinQIfNeeded01(self, mock_mRebootNode):
      _ebox = self.mGetClubox()

      _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
      _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

      _cmds = { 
         self.mGetRegexDom0(): [ 
            [
               exaMockCommand("/usr/sbin/vm_maker --check", aRc=1),
               exaMockCommand("/bin/virsh list --all --name"),
               exaMockCommand("/opt/oracle.SupportTools/switch_to_ovm.sh --qinq")
            ]
         ]
      }
      self.mPrepareMockCommands(_cmds)

      _utils = ebExascaleUtils(_ebox)
      _utils.mEnableQinQIfNeeded(_options)

   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNode')
   def test_mEnableQinQIfNeeded02(self, mock_mRebootNode):
      _ebox = self.mGetClubox()

      _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
      _options.jsonconf = json.loads(ADD_NODE_PAYLOAD)

      _cmds = { 
         self.mGetRegexDom0(): [ 
            [
               exaMockCommand("/usr/sbin/vm_maker --check", aRc=1),
               exaMockCommand("/bin/virsh list --all --name"),
               exaMockCommand("/opt/oracle.SupportTools/switch_to_ovm.sh --qinq")
            ]
         ]
      }
      self.mPrepareMockCommands(_cmds)

      _utils = ebExascaleUtils(_ebox)
      _utils.mEnableQinQIfNeeded(_options, aDom0List=["scaqab10adm02.us.oracle.com"])

   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mRemoveGuestEDVVolume')
   def test_mDetachU02(self, mock_mRemoveEDVVolume):
        _ebox = self.mGetClubox()
        _ddpair = _ebox.mReturnDom0DomUPair()
        _dom0, _domU = _ddpair[0]

        _cmds = { 
                self.mGetRegexDom0():                                       
                [ 
                     [
                         
                         exaMockCommand(re.escape("/opt/exadata_ovm/vm_maker --list --disk-image --domain scaqab10client01vm08.us.oracle.com | grep 'scaqab10client01vm08_u02'"), aRc=0, aStdout="Block scaqab10client01vm08_u02_ae31ee08d402424694869229d101d62b" ,aPersist=True),
                         exaMockCommand("/bin/virsh detach-disk scaqab10client01vm08.us.oracle.com scaqab10client01vm08_u02_ae31ee08d402424694869229d101d62b --live --config", aRc=0, aStdout="" ,aPersist=True),

                     ]
                ],
                self.mGetRegexVm():                                       
                [ 
                     [
                         exaMockCommand("/bin/umount /u02", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/sbin/vgchange -an VGExaDbDisk.u02_extra.img", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/sed -i '/u02_extra/d' /etc/fstab", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ]
         }
        self.mPrepareMockCommands(_cmds)  

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _dom0_short_name = _dom0.split('.')[0]
        _domU_short_name = _domU.split('.')[0]
        _u02_vol_name = _domU_short_name + "_u02"
        _u02_name = _ebox.mCheckConfigOption('u02_name') if _ebox.mCheckConfigOption('u02_name') else 'u02_extra'
        _utils = ebExascaleUtils(_ebox)
        _utils.mDetachU02(_dom0, _domU, _u02_name, _u02_vol_name, _options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateVault', return_value=(0, CREATE_DBVAULT_OUTPUT, ""))
   def test_mCreateDbVault(self, mock_mCreateVault,mock_mIsEFRack ):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(CREATE_DBVAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-hc 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)
        _utils = ebExascaleUtils(_ebox)
        _utils.mCreateDbVault(_options)
   
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault', return_value=(0,LS_DBVAULT_OUTPUT,""))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveVault', return_value=(0, "", ""))
   def test_mDeleteDbVault(self, mock_mIsEFRack, mock_mListVault, mock_mRemoveVault ):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(DELETE_DBVAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-hc 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _utils = ebExascaleUtils(_ebox)
        _utils.mDeleteDbVault(_options)
   
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault', return_value=(0,"spaceUsedHC\n 20G",""))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVault', return_value=(0, CREATE_DBVAULT_OUTPUT, ""))
   def test_mUpdateDbVault(self, mock_mIsEFRack, mock_mListVault, mock_mChangeVault):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(UPDATE_DBVAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-hc 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _utils = ebExascaleUtils(_ebox)
        _utils.mUpdateDbVault(_options)
 
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault', return_value=(0,LS_DBVAULT_OUTPUT,""))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVault', return_value=(0, CREATE_DBVAULT_OUTPUT, ""))
   def test_mGetDbVault(self, mock_mIsEFRack, mock_mListVault, mock_mChangeVault):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(GET_DBVAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-hc 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _utils = ebExascaleUtils(_ebox)
        _utils.mGetDbVault(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateVault', return_value=(0, CREATE_SYSVAULT_OUTPUT, ""))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetCtrlIP', return_value=("10.0.130.110", ""))
   def test_mCreateSysVault(self, mock_mCreateVault,mock_mIsEFRack, mock_mGetCtrlIP ):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(CREATE_SYSVAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand("imageinfo -version", aRc=0, aStdout="25.1.7.0.0.123456\n"), 
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02 +scaqab10adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02 +scaqab1adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02 +scaqab1adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02 +scaqab1adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand("imageinfo -version", aRc=0, aStdout="25.1.7.0.0.123456\n"), 
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02  +scaqab10adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02  +scaqab1adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand("imageinfo -version", aRc=0, aStdout="25.1.7.0.0.123456\n"), 
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02  +scaqab10adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02  +scaqab1adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand("imageinfo -version", aRc=0, aStdout="25.1.7.0.0.123456\n"), 
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02  +scaqab10adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02  +scaqab1adm01:M"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand("imageinfo -version", aRc=0, aStdout="25.1.7.0.0.123456\n"), 
                                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                                          aRc=0, aStdout="autoFileEncryption\ntrue\n", aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-hc 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _utils = ebExascaleUtils(_ebox)
        _utils.mCreateSysVault(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault', return_value=(0,LS_DBVAULT_OUTPUT,""))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveVault', return_value=(0, "", ""))
   def test_mDeleteSysVault(self, mock_mIsEFRack, mock_mListVault, mock_mRemoveVault ):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(DELETE_SYSVAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-hc 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _utils = ebExascaleUtils(_ebox)
        _utils.mDeleteSysVault(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault', return_value=(0,"spaceUsedHC\n 20G",""))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVault', return_value=(0, CREATE_DBVAULT_OUTPUT, ""))
   def test_mUpdateSysVault(self, mock_mIsEFRack, mock_mListVault, mock_mChangeVault):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(UPDATE_SYSVAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-hc 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _utils = ebExascaleUtils(_ebox)
        _utils.mUpdateSysVault(_options)

   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault', return_value=(0,LS_DBVAULT_OUTPUT,""))
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVault', return_value=(0, "", ""))
   def test_mGetAllVaults(self, mock_mIsEFRack, mock_mListVault, mock_mChangeVault):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(UPDATE_SYS_DBVAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-hc 10G"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aStdout=STORAGE_POOL_RESPONSE, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aStdout=LS_DBVAULT_OUTPUT, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=1, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _utils = ebExascaleUtils(_ebox)
        _utils.mGetAllVaults(_options)
        
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   def test_mUpdateSystemVaultAccess(self, mock_mGetVolumeID, mock_mChangeVolume):
        _ebox = self.mGetClubox()

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mUpdateSystemVaultAccess(_options)
        
 
   def test_mGetComputeDetails(self):
        # Mock the dependencies
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(XS_GET_PAYLOAD)
        
        _cmds = { 
         self.mGetRegexDom0(): [ 
            [
               exaMockCommand("/usr/sbin/vm_maker --check", aRc=1),
               exaMockCommand("/bin/virsh list --all --name"),
               exaMockCommand(re.escape("/usr/sbin/ip -o -4 addr show stre0 | /usr/bin/awk '{print $4}' | cut -d/ -f1"), aStdout='100.106.0.100'),
               exaMockCommand(re.escape("/usr/sbin/ip -o -4 addr show stre1 | /usr/bin/awk '{print $4}' | cut -d/ -f1"), aStdout='100.106.0.101')
            ]
         ]
        }
        self.mPrepareMockCommands(_cmds)
        # Create an instance of ebExascaleUtils
        _utils = ebExascaleUtils(_ebox)
        #exascale_utils = ebExascaleUtils(mock_cluctrl)

        # Test the function
        result = _utils.mGetComputeDetails(_options)

        # Assert the result
        self.assertEqual(result, 0)

   def test_mGetComputeDetails_qinq_not_configured(self):
        _cmds = {
          self.mGetRegexDom0(): [
             [
                exaMockCommand("/usr/sbin/vm_maker --check", aRc=1),
                exaMockCommand("/bin/virsh list --all --name"),
                exaMockCommand(re.escape("/usr/sbin/ip -o -4 addr show stre0 | /usr/bin/awk '{print $4}' | cut -d/ -f1"), aStdout='100.106.0.100'),
                exaMockCommand(re.escape("/usr/sbin/ip -o -4 addr show stre1 | /usr/bin/awk '{print $4}' | cut -d/ -f1"), aStdout='100.106.0.101')
             ]
          ]
        }
        self.mPrepareMockCommands(_cmds)
        # Mock the dependencies
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())

        # Create an instance of ebExascaleUtils
        exascale_utils = ebExascaleUtils(_ebox)

        # Test the function
        _options.jsonconf = json.loads(XS_GET_PAYLOAD_1)
        result = exascale_utils.mGetComputeDetails(_options)

        # Assert the result
        self.assertEqual(result, 0)

   def test_mGetComputeDetails_qinq_not_configurable(self):
        _cmds = {
          self.mGetRegexDom0(): [
             [
                exaMockCommand("/usr/sbin/vm_maker --check", aRc=1),
                exaMockCommand("/bin/virsh list --all --name", aStdout='dummy.domu'),
                exaMockCommand(re.escape("/usr/sbin/ip -o -4 addr show stre0 | /usr/bin/awk '{print $4}' | cut -d/ -f1"), aStdout='100.106.0.100'),
                exaMockCommand(re.escape("/usr/sbin/ip -o -4 addr show stre1 | /usr/bin/awk '{print $4}' | cut -d/ -f1"), aStdout='100.106.0.101')
             ]
          ]
        }
        self.mPrepareMockCommands(_cmds)
        # Mock the dependencies
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())

        # Create an instance of ebExascaleUtils
        exascale_utils = ebExascaleUtils(_ebox)

        # Test the function
        _options.jsonconf = json.loads(XS_GET_PAYLOAD_1)
        result = exascale_utils.mGetComputeDetails(_options)

        # Assert the result
        self.assertEqual(result, -1)

   def test_mEnableAutoFileEncryption(self):
        """
        def mEnableAutoFileEncryption(self, aOptions)
        """
        # Mock the dependencies
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD).get("exascale")

        _cmds = {
         self.mGetRegexCell(): [
            [
               exaMockCommand("imageinfo -version", aRc=0, aStdout="25.1.7.0.0.250804\n"),
               exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
               exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                    aRc=0, aStdout="autoFileEncryption\ntrue\n", aPersist=True)
            ],
            [
                exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                    aRc=0, aStdout="autoFileEncryption\ntrue\n", aPersist=True),
               exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chcluster --attributes autoFileEncryption=true",
                   aRc=0, aPersist=True)
            ],
            [
                exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                    aRc=0, aStdout="autoFileEncryption\ntrue\n", aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chcluster --attributes autoFileEncryption=true",
                    aRc=0, aPersist=True)
            ],
            [
                exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                    aRc=0, aStdout="autoFileEncryption\ntrue\n", aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chcluster --attributes autoFileEncryption=true",
                    aRc=0, aPersist=True)
            ]
         ]
        }
        self.mPrepareMockCommands(_cmds)

        # Create an instance of ebExascaleUtils
        _utils = ebExascaleUtils(_ebox)

        # Test the function
        result = _utils.mEnableAutoFileEncryption(_options)

        # Assert the result
        self.assertEqual(result, 0)

   def test_mEnableAutoFileEncryption_version_too_low(self):
    """
    Test mEnableAutoFileEncryption where cell version is below minimum cutoff.
    Should log critical and return -1.
    """
    # Mock the dependencies
    _ebox = self.mGetClubox()
    _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
    _options.jsonconf = json.loads(EXASCALE_PAYLOAD).get("exascale")
    _ebox.mSetExadataImagesMap({})

    # NOTE: Use a version lower than the cutoff
    _cmds = {
        self.mGetRegexCell(): [
            [
                exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
                exaMockCommand("imageinfo -version", aRc=0, aStdout="25.1.6.0.0.123456\n"),  # version too low
            ],
        ]
    }
    self.mPrepareMockCommands(_cmds)

    # Create an instance of ebExascaleUtils
    _utils = ebExascaleUtils(_ebox)

    # Test the function
    result = _utils.mEnableAutoFileEncryption(_options)

    # Assert the result (should fail)
    self.assertEqual(result, -1)

   def test_mEnableAutoFileEncryption_chcluster_fails(self):
        """
        def mEnableAutoFileEncryption(self, aOptions)
        """
        # Mock the dependencies
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _cmds = {
         self.mGetRegexCell(): [
            [
               exaMockCommand("imageinfo -version", aRc=0, aStdout="25.1.7.0.0.250804\n"),
               exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
               exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                   aRc=0, aStdout="autoFileEncryption\nfalse\n"),
            ],
            [
               exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
               exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                   aRc=0, aStdout="autoFileEncryption\nfalse\n"),
               exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chcluster --attributes autoFileEncryption=true",
                   aRc=0, aPersist=True),
            ],
            [
               exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
               exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                   aRc=0, aStdout="autoFileEncryption\nfalse\n"),
            ],
            [
               exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
            ]
         ]
        }
        self.mPrepareMockCommands(_cmds)

        # Create an instance of ebExascaleUtils
        _utils = ebExascaleUtils(_ebox)

        # Test the function
        result = _utils.mEnableAutoFileEncryption(_options)

        # Assert the result
        self.assertEqual(result, -1)

   @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
   @patch('exabox.ovm.csstep.cs_util.csUtil.mGetConstants', return_value=csXSConstants)
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRestoreStorageVlan')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetGridDisks', return_value=([]))
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsXS', return_value=True)
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True)
   def test_mUpdateStorageVlan(self, mock_IsKVM, mock_mIsXS, mock_mGetGridDisks, 
                               mock_mRestoreStorageVlan, mock_mGetConstants, mock_mExecuteOEDAStep):
        _ebox = self.mGetClubox()

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(ENABLE_XS_CONFIG_PAYLOAD)
        _ebox.mSetEnableKVM(True)
        _ebox.mSetExabm(True)
        _cmds = { 
                    self.mGetRegexCell():                                       
                    [ 
                         [
                             exaMockCommand("cellcli -e list flashcache attributes name,size", aRc=0 ,aStdout="scaqab10celadm01_FLASHCACHE 23.28692626953125T", aPersist=True),
                             exaMockCommand("cellcli -e list cell detail | grep flashCacheMode", aRc=0 ,aStdout="flashCacheMode:         WriteThrough", aPersist=True),
                         ],
                         [
                             exaMockCommand("cellcli -e list flashcache attributes name,size", aRc=0 ,aStdout="scaqab10celadm01_FLASHCACHE 23.28692626953125T", aPersist=True),
                             exaMockCommand("cellcli -e list cell detail | grep flashCacheMode", aRc=0 ,aStdout="flashCacheMode:         WriteThrough", aPersist=True),
                             exaMockCommand("cellcli -e drop flashcache", aRc=0 ,aStdout="Flash cache scaqab10celadm01_FLASHCACHE successfully dropped", aPersist=True),
                             exaMockCommand("cellcli -e alter cell shutdown services cellsrv", aRc=0 ,aStdout="The SHUTDOWN of CELLSRV services was successful.", aPersist=True),
                             exaMockCommand('cellcli -e "alter cell flashCacheMode=writeback"', aRc=0 ,aStdout="Cell scaqab10celadm01 successfully altered", aPersist=True),
                             exaMockCommand("cellcli -e alter cell startup services cellsrv", aRc=0 ,aStdout="The STARTUP of CELLSRV services was successful.", aPersist=True),
                             exaMockCommand("cellcli -e create flashcache all", aRc=0 ,aStdout="Flash cache scaqab10celadm01_FLASHCACHE successfully created", aPersist=True)
                         ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)  

        _utils = ebExascaleUtils(_ebox)
        _utils.mUpdateStorageVlan(_options)
        
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVolume')
   @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
   def test_mGetRackSize(self, mock_mGetVolumeID, mock_mChangeVolume):
        _ebox = self.mGetClubox()

        _utils = ebExascaleUtils(_ebox)
        _rack_type = _utils.mGetRackSize()
        self.assertEqual(_rack_type, "normal")

   def test_mDoXsGetOp_fetch_compute_details(self):
       _cmds = {
          self.mGetRegexDom0(): [
             [
                exaMockCommand("/usr/sbin/vm_maker --check"),
                exaMockCommand(re.escape("/usr/sbin/ip -o -4 addr show stre0 | /usr/bin/awk '{print $4}' | cut -d/ -f1"), aStdout='100.106.0.100'),
                exaMockCommand(re.escape("/usr/sbin/ip -o -4 addr show stre1 | /usr/bin/awk '{print $4}' | cut -d/ -f1"), aStdout='100.106.0.101')
             ]
          ]
       }
       # Arrange
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(XS_GET_PAYLOAD)
       self.mPrepareMockCommands(_cmds)
       # Create an instance of ebExascaleUtils
       _utils = ebExascaleUtils(_ebox)

       # Act
       result = _utils.mDoXsGetOp(_options)

       # Assert the result
       self.assertEqual(result, 0)

   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebLogInfo')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebLogError')
   def test_mDoXsGetOp_invalid_operation(self, mock_ebLogError, mock_ebLogInfo):
        # Arrange
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(XS_GET_PAYLOAD)
        _options.jsonconf = {"operation": "invalid_operation"}
        # Create an instance of ebExascaleUtils
        _utils = ebExascaleUtils(_ebox)

        # Act
        rc = _utils.mDoXsGetOp(_options)

        # Assert
        self.assertEqual(rc, -1)
        
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebLogInfo')
   def test_mDoXsGetOp_missing_operation(self, mock_ebLogInfo):
        # Arrange
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {"host_nodes": ["scaqab10adm01.us.oracle.com"]}
        # Create an instance of ebExascaleUtils
        _utils = ebExascaleUtils(_ebox)

        # Act
        rc = _utils.mDoXsGetOp(_options)

        # Assert
        self.assertEqual(rc, -1)
        mock_ebLogInfo.assert_called_once_with("*** mDoXsGetOp")
   
   @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd_check')    
   def test_mDoXsPutOp_config_auto_encryption(self, mock_node_exec_cmd_check, mock_get_gcontext, mock_connect_to_host):
        _ebox = self.mGetClubox()
        exascale_utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(XS_PUT_PAYLOAD)
        _cmds = {
         self.mGetRegexCell(): [
            [
               exaMockCommand("imageinfo -version", aRc=0, aStdout="25.1.7.0.0.250804\n"),
               exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
               exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                    aRc=0, aStdout="autoFileEncryption\ntrue\n", aPersist=True)
            ],
            [
                exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                    aRc=0, aStdout="autoFileEncryption\ntrue\n", aPersist=True),
               exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chcluster --attributes autoFileEncryption=true",
                   aRc=0, aPersist=True)
            ],
            [
                exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                    aRc=0, aStdout="autoFileEncryption\ntrue\n", aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chcluster --attributes autoFileEncryption=true",
                    aRc=0, aPersist=True)
            ],
            [
                exaMockCommand("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli", aRc=0, aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lscluster --attributes autoFileEncryption",
                    aRc=0, aStdout="autoFileEncryption\ntrue\n", aPersist=True),
                exaMockCommand("escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chcluster --attributes autoFileEncryption=true",
                    aRc=0, aPersist=True)
            ]
         ]
        }
        self.mPrepareMockCommands(_cmds)
        self.assertEqual(exascale_utils.mDoXsPutOp(_options), 0)

   @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
   @patch('exabox.ovm.csstep.cs_util.csUtil.mGetConstants', return_value=csXSConstants)
   def test_mValidateAndCreateDisks(self, mock_mGetConstants, mock_mExecuteOEDAStep):
        _ebox = self.mGetClubox()

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(ENABLE_XS_CONFIG_PAYLOAD)
        _ebox.mSetEnableKVM(True)
        _ebox.mSetExabm(True)
        _cmds = { 
                    self.mGetRegexCell():                                       
                    [ 
                         [
                             exaMockCommand(re.escape("cellcli -e list celldisk attributes name,size where disktype in ('HardDisk','FlashDisk')"), aRc=0, aPersist=True),
                         ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)  

        _utils = ebExascaleUtils(_ebox)
        _utils.mValidateAndCreateDisks(_options)

   @mock.patch("exabox.tools.ebTree.ebTree.ebTree.mExportXml")
   @mock.patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun")
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mFetchStorageInterconnectIps', return_value=("100.106.2.1", "100.106.2.2", "255.255.0.0"))
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetExascaleName', return_value=("", "sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers"))
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetCtrlIP', return_value=("10.0.130.110", "sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"))
   def test_UpdateStoragePool(self, mock_mGetExascaleName, mock_mGetCtrlIP, mock_mFetchStorageInterconnectIps, mock_mRun, mock_mExportXml):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(XS_UPDATE_STORAGE_POOL)
       _cell_list = _ebox.mReturnCellNodes()
       _cell = list(_cell_list.keys())[0]
       _cmds = { 
                    self.mGetRegexCell():                                       
                    [ 
                         [
                             exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                             exaMockCommand("/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name", aRc=0 ,aStdout="exc_egs_cluster_name=iad1d2cl38d89abcae38c4e2f8b1922b6289c1384clu01ers", aPersist=True),
                         ],
                         [
                              exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                              exaMockCommand("/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name", aRc=0, aStdout="sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers" ,aPersist=True)
                         ],
                         [
                              exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True)
                         ]
                    ],
                    self.mGetRegexLocal():                           
                    [
                     [
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                    ]
                }
       self.mPrepareMockCommands(_cmds)  

       _xml_save_dir = os.getcwd() + '/' + 'clusters/' + self.mGetClubox().mGetKey() + '/config'
       if not os.path.exists(_xml_save_dir):
          os.makedirs(_xml_save_dir)
       _xs_log_dir = os.getcwd() + '/' + 'log/xs_exatest/'
       if not os.path.exists(_xs_log_dir):
          os.makedirs(_xs_log_dir)
       _path_config = _xml_save_dir + '/exascale1.xml'
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _path_config)
       ebLogInfo(f"ConfigPath: {self.mGetClubox().mGetConfigPath()}")
       _ebox.mSetPatchConfig(_path_config)
       ebLogInfo(f"PatchConfig: {_path_config}")

       _oeda_path  = _ebox.mGetOedaPath()
       _savexmlpath = _oeda_path + '/exacloud.conf'
       if not os.path.exists(_savexmlpath):
          os.makedirs(_savexmlpath)
       _dns_ntp_xml = _savexmlpath + "/patched_ntp_dns_exatest.xml"
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _dns_ntp_xml)

       _initialXml = _xs_log_dir + "/before_xs.xml"
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _initialXml)
       _updateXml = _xs_log_dir + "/after_xs.xml"
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _updateXml)

       with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetBasePath', return_value=_xs_log_dir):
           self.mGetClubox().mSetCmd('xsconfig')
           _utils = ebExascaleUtils(_ebox)
           _utils.mEnableXSService(_options)

   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mFetchStorageInterconnectIps', return_value=("100.106.2.3", "100.106.2.4", "255.255.0.0"))
   @mock.patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun")
   def test_mPatchStorageInterconnctIps(self, mock_mRun, mock_mFetchStorageInterconnectIps):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(XS_UPDATE_STORAGE_POOL)
       _cell_list = _ebox.mReturnCellNodes()
       _cell = list(_cell_list.keys())[0]
       _cmds = { 
                    self.mGetRegexCell():                                       
                    [ 
                         [
                             exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                             exaMockCommand("/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name", aRc=0 ,aStdout="exc_egs_cluster_name=iad1d2cl38d89abcae38c4e2f8b1922b6289c1384clu01ers", aPersist=True),
                         ],
                         [
                              exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True),
                              exaMockCommand("/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name", aRc=0, aStdout="sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers" ,aPersist=True)
                         ],
                         [
                              exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2" ,aPersist=True)
                         ]
                    ],
                    self.mGetRegexLocal():                           
                    [
                     [
                         exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                         exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                    ]
                }
       self.mPrepareMockCommands(_cmds)  

       _xml_save_dir = os.getcwd() + '/' + 'clusters/' + self.mGetClubox().mGetKey() + '/config'
       if not os.path.exists(_xml_save_dir):
          os.makedirs(_xml_save_dir)
       _xs_log_dir = os.getcwd() + '/' + 'log/xs_exatest/'
       if not os.path.exists(_xs_log_dir):
          os.makedirs(_xs_log_dir)
       _path_config = _xml_save_dir + '/exascale1.xml'
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _path_config)
       ebLogInfo(f"ConfigPath: {self.mGetClubox().mGetConfigPath()}")
       _ebox.mSetPatchConfig(_path_config)
       ebLogInfo(f"PatchConfig: {_path_config}")

       _oeda_path  = _ebox.mGetOedaPath()
       _savexmlpath = _oeda_path + '/exacloud.conf'
       if not os.path.exists(_savexmlpath):
          os.makedirs(_savexmlpath)
       _dns_ntp_xml = _savexmlpath + "/patched_ntp_dns_exatest.xml"
       shutil.copyfile(self.mGetClubox().mGetConfigPath(), _dns_ntp_xml)

       with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetBasePath', return_value=_xs_log_dir):
           self.mGetClubox().mSetCmd('xsconfig')
           _utils = ebExascaleUtils(_ebox)
           _utils.mPatchStorageInterconnctIps(_options)

   def test_mFetchStorageInterconnectIps(self):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

       with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(SSHIOObject("stdin"), SSHIOObject(IFCONFIG_STRE0), SSHIOObject("stderr"))):
           _utils = ebExascaleUtils(_ebox)
           _utils.mFetchStorageInterconnectIps(aDom0="scaqab10adm03.us.oracle.com")
           

if __name__ == '__main__':
    unittest.main() 
