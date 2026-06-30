#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_exascaleutils.py pbellary_bug-38972840/4 2026/02/24 07:09:16 pbellary Exp $
#
# tests_exascaleutils.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
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
#    scoral      06/22/26 - Bug 39589421: Skip default ACFS cleanup without
#                           Exascale controller
#    nelango     05/21/26 - Bug 39348637: Handle legacy acfs vol deletion
#    siyarlag    04/02/26 - Add mValidateGuest connectivity tests
#    pbellary    02/24/26 - Bug 38972840 - DELETE-SERVICE WF FAILED TO VERIFY ACL USER ID
#    pbellary    02/24/26 - Bug 38858318 - IF CHACL COMMAND FAILS CREATE SERVICE FLOW SHOULD FAIL
#    pbellary    02/24/26 - Bug 38883255 - VM BACKUP OPERATION IS NOT TAKING BACKUP OF 3RD NODE
#    shapatna    01/22/26 - Bug 38871517: Fix UT errors for exascaleutils.py
#    pbellary    01/06/26 - Codex UT enhancement
#    pbellary    11/30/25 - Enh 38708130 - EXASCALE: DELETE SERVICE SHOULD DELETE ADDITIONAL ACFS FILESYSTEMS
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
from exabox.ovm.csstep.exascale.exascaleutils import ACFS_VOL
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
   "compute_list": [
      "scaqab10adm01.us.oracle.com",
      "scaqab1adm01.us.oracle.com"
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
            "compute_hostname": "scaqab10adm01.us.oracle.com",
            "interface1": "stre0",
            "interface2": "stre1",
            "storage_ip1": "100.106.2.0",
            "storage_ip2": "100.106.2.1",
            "netmask": "255.255.0.0"
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

ASM_ACFS_PAYLOAD = """
{
   "rack": {
      "name": "clu261infra",
      "xsVmImage": "false"
   },
   "acfs": [
      {
         "name": "acfsvol01",
         "mount_path": "acfs01",
         "gb_size": 100
      }
   ]
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

    # ---------- mConfigureExascale ----------
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock(mGetConfigOptions=mock.Mock(return_value={})))
    @patch('exabox.ovm.csstep.exascale.exascaleutils.csUtil')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebCluCmdCheckOptions', return_value=True)
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mDisableNormalRedundancy')
    def test_mConfigureExascale_success(self, mock_mDisableNormalRedundancy, mock_cmd_check, mock_cs_util, _mock_ctx, mock_mIsEFRack):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)

        mock_cs_util.return_value.mGetConstants.return_value = mock.Mock(OSTP_CONFIG_STORAGE='storage')
        mock_cs_util.return_value.mExecuteOEDAStep = mock.Mock()

        with patch.object(ebExascaleUtils, 'mGetVaultName', return_value='vault1'):
            pass

        with patch.object(_utils, 'mEnableXSService') as mock_enable, \
             patch.object(_utils, 'mRemoveVmMachines') as mock_remove, \
             patch.object(_utils, 'mValidateAndCreateDisks') as mock_validate, \
             patch.object(_utils, 'mPatchEFRack') as mock_patch_ef, \
             patch.object(_utils, 'mEnableQinQIfNeeded') as mock_enable_qinq, \
             patch.object(_utils, 'mCheckRoCEIPs', return_value=True) as mock_check_roce, \
             patch.object(_utils, 'mSetupRoCEIPs') as mock_setup_roce, \
             patch.object(_utils, 'mValidateGuest') as mock_validate_guest, \
             patch.object(_utils, 'mUpdateStorageVlan') as mock_update_vlan, \
             patch.object(_utils, 'mEnableAutoFileEncryption', return_value=0), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_ebox, 'mGetNodeModel', return_value='X9M'), \
             patch.object(_ebox, 'mCompareExadataModel', return_value=1):
            _utils.mConfigureExascale(_options)

        mock_enable.assert_called_once_with(_options)
        mock_remove.assert_called_once_with(_options)
        mock_validate.assert_called_once_with(_options)
        mock_enable_qinq.assert_called_once_with(_options)
        mock_check_roce.assert_called_once()
        mock_setup_roce.assert_not_called()
        mock_validate_guest.assert_not_called()
        mock_update_vlan.assert_called_once_with(_options)
        mock_cs_util.return_value.mExecuteOEDAStep.assert_called_once()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock(mGetConfigOptions=mock.Mock(return_value={})))
    @patch('exabox.ovm.csstep.exascale.exascaleutils.csUtil')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebCluCmdCheckOptions', return_value=True)
    def test_mConfigureExascale_requires_qinq(self, mock_cmd_check, mock_cs_util, _mock_ctx):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)

        mock_cs_util.return_value.mGetConstants.return_value = mock.Mock(OSTP_CONFIG_STORAGE='storage')
        mock_cs_util.return_value.mExecuteOEDAStep = mock.Mock()

        _escli = mock.Mock()
        _escli.mIsEFRack.return_value = False
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_utils, 'mEnableXSService'), \
             patch.object(_utils, 'mRemoveVmMachines'), \
             patch.object(_utils, 'mValidateAndCreateDisks'), \
             patch.object(_utils, 'mPatchEFRack'), \
             patch.object(_utils, 'mEnableQinQIfNeeded'), \
             patch.object(_utils, 'mCheckRoCEIPs', return_value=False), \
             patch.object(_utils, 'mSetupRoCEIPs') as mock_setup_roce, \
             patch.object(_utils, 'mValidateGuest', return_value=0) as mock_validate_guest, \
             patch.object(_utils, 'mUpdateStorageVlan'), \
             patch.object(_utils, 'mDisableNormalRedundancy'), \
             patch.object(_utils, 'mEnableAutoFileEncryption', return_value=0), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_ebox, 'mGetNodeModel', return_value='X9M'), \
             patch.object(_ebox, 'mCompareExadataModel', return_value=1):
            rc = _utils.mConfigureExascale(_options)

        self.assertIsNone(rc)
        mock_setup_roce.assert_called_once()
        mock_validate_guest.assert_called_once()
        mock_cs_util.return_value.mExecuteOEDAStep.assert_called_once()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock(mGetConfigOptions=mock.Mock(return_value={})))
    @patch('exabox.ovm.csstep.exascale.exascaleutils.csUtil')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebCluCmdCheckOptions', return_value=True)
    def test_mConfigureExascale_validate_guest_failure(self, mock_cmd_check, mock_cs_util, _mock_ctx):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)

        mock_cs_util.return_value.mGetConstants.return_value = mock.Mock(OSTP_CONFIG_STORAGE='storage')

        _escli = mock.Mock()
        _escli.mIsEFRack.return_value = False
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_utils, 'mEnableXSService'), \
             patch.object(_utils, 'mRemoveVmMachines'), \
             patch.object(_utils, 'mValidateAndCreateDisks'), \
             patch.object(_utils, 'mPatchEFRack'), \
             patch.object(_utils, 'mEnableQinQIfNeeded'), \
             patch.object(_utils, 'mCheckRoCEIPs', return_value=False), \
             patch.object(_utils, 'mSetupRoCEIPs'), \
             patch.object(_utils, 'mValidateGuest', return_value=-99), \
             patch.object(_utils, 'mUpdateStorageVlan') as mock_update_vlan, \
             patch.object(_utils, 'mEnableAutoFileEncryption'), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_ebox, 'mGetNodeModel', return_value='X9M'), \
             patch.object(_ebox, 'mCompareExadataModel', return_value=1):
            rc = _utils.mConfigureExascale(_options)

        self.assertEqual(rc, -99)
        mock_update_vlan.assert_not_called()
        mock_cs_util.return_value.mExecuteOEDAStep.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock(mGetConfigOptions=mock.Mock(return_value={})))
    @patch('exabox.ovm.csstep.exascale.exascaleutils.csUtil')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebCluCmdCheckOptions', return_value=True)
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mDisableNormalRedundancy')
    def test_mConfigureExascale_auto_file_encryption_failure(self, mock_mDisableNormalRedundancy, mock_cmd_check, mock_cs_util, _mock_ctx):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)

        mock_cs_util.return_value.mGetConstants.return_value = mock.Mock(OSTP_CONFIG_STORAGE='storage')
        mock_cs_util.return_value.mExecuteOEDAStep = mock.Mock()

        _escli = mock.Mock()
        _escli.mIsEFRack.return_value = False
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_utils, 'mEnableXSService'), \
             patch.object(_utils, 'mRemoveVmMachines'), \
             patch.object(_utils, 'mValidateAndCreateDisks'), \
             patch.object(_utils, 'mPatchEFRack'), \
             patch.object(_utils, 'mEnableQinQIfNeeded'), \
             patch.object(_utils, 'mCheckRoCEIPs', return_value=True), \
             patch.object(_utils, 'mUpdateStorageVlan'), \
             patch.object(_utils, 'mEnableAutoFileEncryption', return_value=-1), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_ebox, 'mGetNodeModel', return_value='X9M'), \
             patch.object(_ebox, 'mCompareExadataModel', return_value=1):
            rc = _utils.mConfigureExascale(_options)

        self.assertEqual(rc, -1)
        mock_cs_util.return_value.mExecuteOEDAStep.assert_called_once()

    # ---------- mValidateGuest ----------
    @patch('exabox.ovm.csstep.exascale.exascaleutils.time.sleep', return_value=None)
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_connect_to_host')
    def test_mValidateGuest_filters_unreachable_domus(self, mock_node_connect, _mock_sleep):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        payload = {
            "Dom0domUDetails": {
                "dom0a": {
                    "domuDetails": [
                        {
                            "domuNatHostname": "domu1",
                            "clusterStorageType": "ASM",
                            "clusterName": "clusterA"
                        }
                    ]
                },
                "dom0b": {
                    "domuDetails": [
                        {
                            "domuNatHostname": "domu2",
                            "clusterStorageType": "ASM",
                            "clusterName": "clusterA"
                        }
                    ]
                }
            }
        }
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = payload
        _failed_list = ['dom0a', 'dom0b']

        _stdout = mock.Mock()
        _stdout.read.return_value = ''
        _stderr = mock.Mock()
        _stderr.read.return_value = ''
        _reachable_node = mock.MagicMock()
        _reachable_node.mExecuteCmd.return_value = (None, _stdout, _stderr)
        _reachable_node.mGetCmdExitStatus.return_value = 0

        def _connect_side_effect(*args, **kwargs):
            if len(args) >= 2:
                host = args[1]
            else:
                host = kwargs.get('aHost')
            if host == 'domu1':
                _ctx_success = mock.MagicMock()
                _ctx_success.__enter__.return_value = _reachable_node
                _ctx_success.__exit__.return_value = None
                return _ctx_success
            raise Exception("failed to connect")

        mock_node_connect.side_effect = _connect_side_effect

        with patch.object(_ebox, 'mCheckConfigOption', return_value=None), \
             patch.object(_ebox, 'mCheckCrsUp', return_value=True) as mock_crs_up, \
             patch.object(_ebox, 'mCheckAsmIsUp') as mock_asm_up, \
             patch.object(_ebox, 'mCheckDBIsUp', return_value=True) as mock_db_up, \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            rc = _utils.mValidateGuest(_options, _failed_list)

        self.assertEqual(rc, 0)
        mock_crs_up.assert_called_once_with('domu1')
        mock_db_up.assert_called_once_with('domu1', aExascale=True)
        mock_asm_up.assert_called_once_with('domu1', ['domu1'])
        mock_update_error.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_connect_to_host', side_effect=Exception("connect fail"))
    def test_mValidateGuest_all_unreachable_skips_checks(self, _mock_node_connect):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        payload = {
            "Dom0domUDetails": {
                "dom0a": {
                    "domuDetails": [
                        {
                            "domuNatHostname": "domu1",
                            "clusterStorageType": "ASM",
                            "clusterName": "clusterA"
                        }
                    ]
                }
            }
        }
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = payload
        _failed_list = ['dom0a']

        with patch.object(_ebox, 'mCheckConfigOption', return_value=None), \
             patch.object(_ebox, 'mCheckCrsUp') as mock_crs_up, \
             patch.object(_ebox, 'mCheckAsmIsUp') as mock_asm_up, \
             patch.object(_ebox, 'mCheckDBIsUp') as mock_db_up, \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            rc = _utils.mValidateGuest(_options, _failed_list)

        self.assertEqual(rc, 0)
        mock_crs_up.assert_not_called()
        mock_db_up.assert_not_called()
        mock_asm_up.assert_not_called()
        mock_update_error.assert_not_called()

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
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebOedacli')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebEscliUtils')
    def test_mEnableXSService_updates_cell_vlan(self, mock_escli_cls, mock_oedacli_cls, _mock_export):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(ENABLE_XS_CONFIG_PAYLOAD)
        _expected_hosts = ", ".join(_options.jsonconf['exascale']['cell_list'])

        self.mGetClubox().mSetCmd('xsconfig')

        mock_oedacli = mock.Mock()
        mock_oedacli_cls.return_value = mock_oedacli

        _mock_escli = mock.Mock()
        _mock_escli.mIsEFRack.return_value = False
        mock_escli_cls.return_value = _mock_escli

        _cluster = mock.Mock()
        _cluster.mGetCluName.return_value = 'cluster01'
        _clusters = mock.Mock()
        _clusters.mGetCluster.return_value = _cluster

        with patch.object(_ebox, 'mCheckConfigOption', return_value='true'), \
             patch.object(ebExascaleUtils, 'mCheckVaultTag', return_value=False), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'scaqab10celadm01.us.oracle.com': object(), 'cell2': object()}), \
             patch.object(_ebox, 'mGetNodeModel', return_value='X9M-2'), \
             patch.object(_ebox, 'mCompareExadataModel', return_value=1), \
             patch.object(_ebox, 'mGetStorageType', return_value='XS'), \
             patch.object(_ebox, 'mGetClusters', return_value=_clusters), \
             patch.object(_ebox, 'mSetXS'), \
             patch.object(_ebox, 'mSetRemoteConfig'), \
             patch.object(_ebox, 'mUpdateInMemoryXmlConfig'), \
             patch.object(_ebox, 'mExecuteLocal'), \
             patch.object(_ebox, 'mGetBasePath', return_value='/tmp'), \
             patch.object(_ebox, 'mGetOedaPath', return_value='/tmp/oeda_unit_test'):
            _utils.mEnableXSService(_options)

        alter_network_calls = [
            record for record in mock_oedacli.mAppendCommand.call_args_list
            if len(record.args) >= 3 and record.args[0] == 'ALTER NETWORKS'
        ]
        self.assertEqual(len(alter_network_calls), 1)

        _cmd, _options_dict, _filters_dict = alter_network_calls[0].args[:3]
        self.assertEqual(_cmd, 'ALTER NETWORKS')
        self.assertEqual(_options_dict, {'VLANID': '631'})
        self.assertEqual(_filters_dict, {'HOSTNAMES': _expected_hosts, 'NETWORKTYPE': 'private'})
        self.assertTrue(alter_network_calls[0].kwargs.get('aForce'))


    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebEscliUtils')
    def test_mEnableXSService_flag_disabled(self, mock_escli_cls):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)

        mock_escli_cls.return_value = mock.Mock()
        with patch.object(_ebox, 'mCheckConfigOption', return_value='false'), \
             patch.object(_ebox, 'mSetXS') as mock_set_xs:
            ebExascaleUtils(_ebox).mEnableXSService(_options)

        mock_set_xs.assert_called_once_with(False)
        self.assertGreaterEqual(mock_escli_cls.call_count, 1)
        _init_calls = [c for c in mock_escli_cls.mock_calls if c[0] == '']
        self.assertTrue(all(c[1] and c[1][0] is _ebox for c in _init_calls))

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebEscliUtils')
    def test_mEnableXSService_existing_tag(self, mock_escli_cls):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)

        mock_escli_cls.return_value = mock.Mock()
        with patch.object(_ebox, 'mCheckConfigOption', return_value='true'), \
             patch.object(ebExascaleUtils, 'mCheckVaultTag', return_value=True), \
             patch.object(_ebox, 'mSetXS') as mock_set_xs, \
             patch.object(_ebox, 'mSetRemoteConfig') as mock_set_remote:
            ebExascaleUtils(_ebox).mEnableXSService(_options)

        mock_set_xs.assert_called_once_with(True)
        mock_set_remote.assert_called_once_with(_ebox.mGetPatchConfig())
        self.assertGreaterEqual(mock_escli_cls.call_count, 1)
        _init_calls = [c for c in mock_escli_cls.mock_calls if c[0] == '']
        self.assertTrue(all(c[1] and c[1][0] is _ebox for c in _init_calls))

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebEscliUtils')
    def test_mEnableXSService_missing_cells_raises(self, mock_escli_cls):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        payload = json.loads(EXASCALE_CONFIG_PAYLOAD)
        payload['exascale']['cell_list'] = []
        _options.jsonconf = payload

        mock_escli_cls.return_value = mock.Mock()
        with patch.object(_ebox, 'mCheckConfigOption', return_value='true'), \
             patch.object(ebExascaleUtils, 'mCheckVaultTag', return_value=False):
            with self.assertRaises(ExacloudRuntimeError):
                ebExascaleUtils(_ebox).mEnableXSService(_options)

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebCluExascaleConfig')
    def test_mGetExascaleName_success(self, mock_cfg_cls):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        mock_config = mock.Mock()
        mock_cluster = mock.Mock()
        mock_cluster.mGetClusterName.return_value = 'ClusterA'

        mock_cfg = mock_cfg_cls.return_value
        mock_cfg.mGetExascaleClusterConfigList.return_value = ['cfg1']
        mock_cfg.mGetExascaleClusterConfig.return_value = mock_cluster

        with patch.object(_ebox, 'mGetConfig', return_value=mock_config):
            _exascale_id, _cluster_name = _utils.mGetExascaleName()

        self.assertEqual((_exascale_id, _cluster_name), ('cfg1', 'ClusterA'))
        mock_cfg_cls.assert_called_once_with(mock_config)
        mock_cfg.mGetExascaleClusterConfig.assert_called_once_with('cfg1')

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebCluExascaleConfig')
    def test_mGetExascaleName_no_clusters(self, mock_cfg_cls):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        mock_config = mock.Mock()
        mock_cfg = mock_cfg_cls.return_value
        mock_cfg.mGetExascaleClusterConfigList.return_value = []

        with patch.object(_ebox, 'mGetConfig', return_value=mock_config):
            _exascale_id, _cluster_name = _utils.mGetExascaleName()

        self.assertEqual((_exascale_id, _cluster_name), ('', ''))
        mock_cfg_cls.assert_called_once_with(mock_config)
        mock_cfg.mGetExascaleClusterConfig.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock(mGetConfigOptions=mock.Mock(return_value={})))
    @patch('exabox.ovm.csstep.exascale.exascaleutils.csUtil')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebCluCmdCheckOptions', return_value=True)
    def test_mConfigureExascale_success(self, mock_cmd_check, mock_cs_util, _mock_ctx):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)
        _options.jsonconf['exascale']['host_nodes'] = [{
            'compute_hostname': 'dom0a',
            'storage_ip1': '100.0.0.10',
            'netmask': '255.255.255.0'
        }]
        _options.jsonconf['exascale']['storage_vlan_id'] = '210'

        mock_cs_util.return_value.mGetConstants.return_value = mock.Mock(OSTP_CONFIG_STORAGE='storage')
        mock_cs_util.return_value.mExecuteOEDAStep = mock.Mock()

        _utils = ebExascaleUtils(_ebox)
        _utils._ebExascaleUtils__escli = mock.Mock(
            mIsEFRack=mock.Mock(return_value=False),
            mCheckWalletExists=mock.Mock(return_value=0),
            mListExascaleServices=mock.Mock(return_value=[{"name": "EXASCALE_dom0a", "status": "ONLINE"}]),
            mGetClusterAttribute=mock.Mock(return_value=(0, [{
                "controlServicesState": "ONLINE",
                "storageVolumeWorkersState": "ONLINE",
                "systemVaultManagersState": "ONLINE",
                "userVaultManagersState": "ONLINE",
                "volumeManagersState": "ONLINE"
            }], ""))
        )

        with patch.object(_utils, 'mEnableXSService') as mock_enable, \
             patch.object(_utils, 'mRemoveVmMachines') as mock_remove, \
             patch.object(_utils, 'mValidateAndCreateDisks') as mock_validate, \
             patch.object(_utils, 'mPatchEFRack') as mock_patch, \
             patch.object(_utils, 'mEnableQinQIfNeeded') as mock_enable_qinq, \
             patch.object(_utils, 'mCheckRoCEIPs', return_value=True) as mock_check_roce, \
             patch.object(_utils, 'mSetupRoCEIPs') as mock_setup_roce, \
             patch.object(_utils, 'mValidateGuest') as mock_validate_guest, \
             patch.object(_utils, 'mUpdateStorageVlan') as mock_update_vlan, \
             patch.object(_utils, 'mDisableNormalRedundancy', return_value=0), \
             patch.object(_utils, 'mEnableAutoFileEncryption', return_value=0), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_ebox, 'mGetNodeModel', return_value='X9M'), \
             patch.object(_ebox, 'mCompareExadataModel', return_value=1):
            _utils.mConfigureExascale(_options)

        mock_enable.assert_called_once_with(_options)
        mock_remove.assert_called_once_with(_options)
        mock_validate.assert_called_once_with(_options)
        mock_enable_qinq.assert_called_once_with(_options)
        mock_check_roce.assert_called_once()
        mock_setup_roce.assert_not_called()
        mock_validate_guest.assert_not_called()
        mock_update_vlan.assert_called_once_with(_options)
        mock_cs_util.return_value.mExecuteOEDAStep.assert_called_once()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock(mGetConfigOptions=mock.Mock(return_value={})))
    @patch('exabox.ovm.csstep.exascale.exascaleutils.csUtil')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebCluCmdCheckOptions', return_value=True)
    def test_mConfigureExascale_requires_qinq(self, mock_cmd_check, mock_cs_util, _mock_ctx):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_CONFIG_PAYLOAD)
        _options.jsonconf['exascale']['host_nodes'] = [{
            'compute_hostname': 'dom0a',
            'storage_ip1': '100.0.0.10',
            'netmask': '255.255.255.0'
        }]
        _options.jsonconf['exascale']['storage_vlan_id'] = '210'

        mock_cs_util.return_value.mGetConstants.return_value = mock.Mock(OSTP_CONFIG_STORAGE='storage')
        mock_cs_util.return_value.mExecuteOEDAStep = mock.Mock()

        _utils = ebExascaleUtils(_ebox)
        _utils._ebExascaleUtils__escli = mock.Mock(
            mIsEFRack=mock.Mock(return_value=False),
            mCheckWalletExists=mock.Mock(return_value=0),
            mListExascaleServices=mock.Mock(return_value=[{"name": "EXASCALE_dom0a", "status": "ONLINE"}]),
            mGetClusterAttribute=mock.Mock(return_value=(0, [{
                "controlServicesState": "ONLINE",
                "storageVolumeWorkersState": "ONLINE",
                "systemVaultManagersState": "ONLINE",
                "userVaultManagersState": "ONLINE",
                "volumeManagersState": "ONLINE"
            }], ""))
        )

        with patch.object(_utils, 'mEnableXSService'), \
             patch.object(_utils, 'mRemoveVmMachines'), \
             patch.object(_utils, 'mValidateAndCreateDisks'), \
             patch.object(_utils, 'mPatchEFRack'), \
             patch.object(_utils, 'mEnableQinQIfNeeded'), \
             patch.object(_utils, 'mCheckRoCEIPs', return_value=False), \
             patch.object(_utils, 'mSetupRoCEIPs') as mock_setup_roce, \
             patch.object(_utils, 'mValidateGuest', return_value=0) as mock_validate_guest, \
             patch.object(_utils, 'mUpdateStorageVlan'), \
             patch.object(_utils, 'mDisableNormalRedundancy', return_value=0), \
             patch.object(_utils, 'mEnableAutoFileEncryption', return_value=0), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_ebox, 'mGetNodeModel', return_value='X9M'), \
             patch.object(_ebox, 'mCompareExadataModel', return_value=1):
            rc = _utils.mConfigureExascale(_options)

        self.assertIsNone(rc)
        mock_setup_roce.assert_called_once()
        mock_validate_guest.assert_called_once()
        mock_cs_util.return_value.mExecuteOEDAStep.assert_called_once()

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

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterAttribute', return_value=(0, [{'controlServicesState': 'ONLINE'}], ''))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListExascaleServices', return_value=[{'name': 'svc_node', 'status': 'ONLINE'}])
    def test_mValidateExascaleConfiguration_wallet_missing_dom0(self, mock_mListExascaleServices, mock_mGetClusterAttribute):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _mock_escli = mock.Mock()
        _mock_escli.mCheckWalletExists.side_effect = [1]
        _utils.mSetEscliUtils(_mock_escli)

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mValidateExascaleConfiguration(_options)

        mock_update_error.assert_called_once_with(gExascaleError["WALLET_NOT_FOUND"], mock.ANY)
        mock_mListExascaleServices.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterAttribute', return_value=(0, [{'controlServicesState': 'ONLINE'}], ''))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListExascaleServices', return_value=[{'name': 'svc_node', 'status': 'ONLINE'}])
    def test_mValidateExascaleConfiguration_wallet_missing_cell(self, mock_mListExascaleServices, mock_mGetClusterAttribute):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _mock_escli = mock.Mock()
        _mock_escli.mCheckWalletExists.side_effect = [0, 1]
        _utils.mSetEscliUtils(_mock_escli)

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mValidateExascaleConfiguration(_options)

        mock_update_error.assert_called_once_with(gExascaleError["WALLET_NOT_FOUND"], mock.ANY)
        mock_mListExascaleServices.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterAttribute')
    def test_mValidateExascaleConfiguration_cluster_attribute_reduced(self, mock_mGetClusterAttribute):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _mock_escli = mock.Mock()
        _mock_escli.mCheckWalletExists.return_value = 0
        _mock_escli.mListExascaleServices.return_value = [{'name': 'svc_cell1', 'status': 'ONLINE'}]
        _mock_escli.mGetClusterAttribute.return_value = (
            0,
            [{'controlServicesState': 'ONLINE - reduced redundancy'}],
            ''
        )
        _utils.mSetEscliUtils(_mock_escli)

        mock_mGetClusterAttribute.return_value = (0, [{'controlServicesState': 'ONLINE - reduced redundancy'}], '')

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mValidateExascaleConfiguration(_options)

        mock_update_error.assert_called_once_with(gExascaleError["EXASCALE_DEPLOY_ERROR"], mock.ANY)

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

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeACL')
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    def test_mMigrateVMbackupJsonP01(self, mock_mReadFile, mock_changeACL):
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

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeACL')
    @patch("exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetDBServerStatus", return_value=(0, "running"))
    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    def test_mMigrateVMbackupJsonP02(self, mock_mReadFile, mock_db_status, mock_changeACL):
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

   # Auto-generated test for mGenerateVMbackupJson
    def test_mGenerateVMbackupJson_covers_all_branches(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        _utils._ebExascaleUtils__escli = mock.Mock()

        def _assert_case(backup_supported, image_supported, image_vault, backup_vault, endpoint, expected):
            _utils._ebExascaleUtils__escli.mGetERSEndpoint.return_value = endpoint
            with patch.object(_utils, 'mIsEDVBackupSupported', return_value=backup_supported), \
                 patch.object(_utils, 'mIsEDVImageSupported', return_value=image_supported), \
                 patch.object(_utils, 'mGetImageBackupVault', return_value=(image_vault, backup_vault)):
                result = _utils.mGenerateVMbackupJson(_options)
            self.assertEqual(result, expected)

        _assert_case(
            backup_supported=True,
            image_supported=True,
            image_vault='imgVault',
            backup_vault='bkpVault',
            endpoint=('10.0.0.1', 5052),
            expected={
                'backup_type': 'Exascale',
                'exascale_backup_vault': 'bkpVault',
                'source_vm_images': 'Exascale',
                'exascale_images_vault': 'imgVault',
                'exascale_retention_num': 2,
                'exascale_ers_ip_port': '10.0.0.1:5052'
            }
        )

        _assert_case(
            backup_supported=False,
            image_supported=True,
            image_vault='imgVault',
            backup_vault='',
            endpoint=('10.0.0.2', 5052),
            expected={
                'backup_type': 'Legacy',
                'exascale_backup_vault': '',
                'source_vm_images': 'Exascale',
                'exascale_images_vault': 'imgVault',
                'exascale_retention_num': 2,
                'exascale_ers_ip_port': '10.0.0.2:5052'
            }
        )

        _assert_case(
            backup_supported=True,
            image_supported=False,
            image_vault='',
            backup_vault='bkpVault',
            endpoint=('10.0.0.3', 5052),
            expected={
                'backup_type': 'Exascale',
                'exascale_backup_vault': 'bkpVault',
                'source_vm_images': 'Legacy',
                'exascale_images_vault': '',
                'exascale_retention_num': 2,
                'exascale_ers_ip_port': '10.0.0.3:5052'
            }
        )

        _assert_case(
            backup_supported=False,
            image_supported=False,
            image_vault='',
            backup_vault='',
            endpoint=('10.0.0.4', 5052),
            expected={
                'backup_type': 'Legacy',
                'exascale_backup_vault': '',
                'source_vm_images': 'Legacy',
                'exascale_images_vault': '',
                'exascale_retention_num': 2,
                'exascale_ers_ip_port': ':'
            }
        )

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
        _options.jsonconf = copy.deepcopy(json.loads(EXASCALE_PAYLOAD))

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
        _options.jsonconf = copy.deepcopy(json.loads(EXASCALE_PAYLOAD))

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
        _options.jsonconf = copy.deepcopy(json.loads(EXASCALE_PAYLOAD))

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
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("1:6cafd8310b3d49a2becd17e9c08f7919", "/acfs_1", "10.0000G", "1.0000G"))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
    def test_mGetACFSSize(self,  mock_mGetVolumeID, mock_mGetACFSFileSystem, mock_mMountACFSFileSystem):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(UNMOUNT_ACFS_PAYLOAD)

        _json_payload = {
            "data": [
                {
                    "attributes": {
                        "volume": "vol_grid",
                        "mountPath": "/acfs/grid",
                        "size": 10 * 1024 * 1024 * 1024,
                        "totalFree": 3 * 1024 * 1024 * 1024
                    }
                }
            ]
        }
        _mock_host = mock.MagicMock()
        _mock_cell = mock.MagicMock()

        def _connect_side_effect(host, *_args, **_kwargs):
            if host == "scaqab10adm01.us.oracle.com":
                return mock.MagicMock(__enter__=lambda self=_mock_host: _mock_host, __exit__=lambda *a, **k: None)
            return mock.MagicMock(__enter__=lambda self=_mock_cell: _mock_cell, __exit__=lambda *a, **k: None)

        with patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", side_effect=_connect_side_effect), \
             patch.object(ebEscliUtils, 'mGetACFSFileSystemByJsonFormat', return_value=(0, json.dumps(_json_payload), None)), \
             patch.object(ebEscliUtils, 'mGetVolumeID', return_value=('vol_grid', None)):
            _utils = ebExascaleUtils(_ebox)
            _ret = _utils.mGetACFSSize(_options)

    def test_mGetACFSSizeUsage_fetches_from_json(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(UNMOUNT_ACFS_PAYLOAD)

        _acfs_list = [{"name": "grid"}]
        _json_payload = {
            "data": [
                {
                    "attributes": {
                        "volume": "vol_grid",
                        "mountPath": "/acfs/grid",
                        "size": 10 * 1024 * 1024 * 1024,
                        "totalFree": 3 * 1024 * 1024 * 1024
                    }
                }
            ]
        }

        _mock_host = mock.MagicMock()
        _mock_cell = mock.MagicMock()

        def _connect_side_effect(host, *_args, **_kwargs):
            if host == "scaqab10adm01.us.oracle.com":
                return mock.MagicMock(__enter__=lambda self=_mock_host: _mock_host, __exit__=lambda *a, **k: None)
            return mock.MagicMock(__enter__=lambda self=_mock_cell: _mock_cell, __exit__=lambda *a, **k: None)

        _mock_host.mExecuteCmd.return_value = (0, mock.MagicMock(readlines=lambda: ["running\n"]), None)
        _mock_host.mGetCmdExitStatus.return_value = 0

        with patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", side_effect=_connect_side_effect), \
             patch.object(ebEscliUtils, 'mGetACFSFileSystemByJsonFormat', return_value=(0, json.dumps(_json_payload), None)), \
             patch.object(ebEscliUtils, 'mGetVolumeID', return_value=('vol_grid', None)):
            _utils = ebExascaleUtils(_ebox)
            _data = _utils.mGetACFSSize(_options)

        self.assertIn('acfs', _data)
        self.assertEqual(_data['acfs'][0]['size_gb'], 10)
        self.assertEqual(_data['acfs'][0]['used_gb'], 7)
        self.assertEqual(_data['acfs'][0]['mount_path'], '/acfs/grid')

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("1:6cafd8310b3d49a2becd17e9c08f7919", "", "", ""))
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
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("1:6cafd8310b3d49a2becd17e9c08f7919", "", "", ""))
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
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("1:6cafd8310b3d49a2becd17e9c08f7919", "", "", ""))
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

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetCtrlIP', return_value=("", ""))
    def test_mRemoveDefaultAcfsVolume_skips_without_exascale_controller(self, mock_mGetCtrlIP, mock_mGetVolumeID):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(ASM_ACFS_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        with patch.object(_utils, 'mUnRegisterACFS') as mock_mUnRegisterACFS, \
             patch.object(_utils, 'mDetachAcfsVolume') as mock_mDetachAcfsVolume, \
             patch.object(_utils, 'mRemoveAcfsDir') as mock_mRemoveAcfsDir:
            _utils.mRemoveDefaultAcfsVolume(_options)

        mock_mGetCtrlIP.assert_called_once()
        mock_mGetVolumeID.assert_not_called()
        mock_mUnRegisterACFS.assert_not_called()
        mock_mDetachAcfsVolume.assert_not_called()
        mock_mRemoveAcfsDir.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveACFSFileSystem')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("1:6cafd8310b3d49a2becd17e9c08f7919", "", "", ""))
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

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveACFSFileSystem')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("acfsid", '/var/opt/oracle/dbaas_acfs', '100G', '90G'))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterID', return_value=("gridclub086e35-128", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c"))
    def test_mUnRegisterACFS_legacy(self, mock_mGetClusterID, mock_mGetVolumeID, mock_mGetACFSFileSystem, mock_mUnMountACFSFileSystem, mock_mRemoveACFSFileSystem):
        mock_mGetVolumeID.side_effect = [(None, None), ("2:b4d00303b12f46d6a31b4a5339395cd3", "admin")]

        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mUnRegisterACFS(_options)

        self.assertEqual(mock_mGetVolumeID.call_count, 2)

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("acfsid", '/var/opt/oracle/dbaas_acfs', '100G', '90G'))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "dev_additional_acfs"))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVVolume')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVAttachment')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveACFSFileSystem')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("volid", 'admin'))
    def test_mRemoveACFSFileSystem(self, mock_mGetVolumeID, mock_mUnMountACFSFileSystem, mock_mRemoveACFSFileSystem, mock_mRemoveEDVAttachment, mock_mRemoveEDVVolume, mock_mGetVolumeAttachments, mock_mGetACFSFileSystem):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mRemoveACFSFileSystem('scaqab10celadm01.us.oracle.com', 'acfs_gridclub086e35-128', _options)
        mock_mGetVolumeID.assert_called_once()

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetACFSFileSystem', return_value=("acfsid", '/var/opt/oracle/dbaas_acfs', '100G', '90G'))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "dev_additional_acfs"))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVVolume')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVAttachment')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveACFSFileSystem')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mUnMountACFSFileSystem')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID')
    def test_mRemoveACFSFileSystem_legacy(self, mock_mGetVolumeID, mock_mUnMountACFSFileSystem, mock_mRemoveACFSFileSystem, mock_mRemoveEDVAttachment, mock_mRemoveEDVVolume, mock_mGetVolumeAttachments, mock_mGetACFSFileSystem):
        mock_mGetVolumeID.side_effect = [(None, None), ("volid", 'admin')]

        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mRemoveACFSFileSystem('scaqab10celadm01.us.oracle.com', 'acfs_gridclub086e35-128', _options)

        self.assertEqual(mock_mGetVolumeID.call_count, 2)

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

    @patch('time.sleep', return_value=None)
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVVolume')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVAttachment')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "dev_additional_acfs"))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetUser', return_value="gridiad1046clu040a1")
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetClusterID', return_value=("gridiad1046clu040a1", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c"))
    def test_mDetachAcfsVolume_legacy(self, mock_mGetClusterID, mock_mGetUser, mock_mGetVolumeID, mock_mGetVolumeAttachments, mock_mRemoveEDVAttachment, mock_mRemoveEDVVolume, mock_sleep):
        mock_mGetVolumeID.side_effect = [(None, None), ("2:b4d00303b12f46d6a31b4a5339395cd3", "admin")]

        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mDetachAcfsVolume(_options)

        self.assertEqual(mock_mGetVolumeID.call_count, 2)

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListFiles')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveFile')
    def test_mDeleteFilesInDbVault(self, mock_mRemoveFile, mock_mListFiles):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mDeleteFilesInDbVault(_options)

        _ebox.mSetOciExacc(True)
        _utils.mDeleteFilesInDbVault(_options)

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetEDVInitiator', return_value='initiator-1')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateEDVVolumeAttachment', return_value=0)
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=('att-1', 'vol-id', 'device-1'))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:vol-id", "admin"))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mCreateEDVVolume', return_value=0)
    def test_mCreateU02Volume(self, mock_mCreateEDVVolume, mock_mGetVolumeID, mock_mGetVolumeAttachments,
                             mock_mCreateEDVVolumeAttachment, mock_mGetEDVInitiator):
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
        with patch.object(_utils, 'mGetVaultName', return_value='systemVault'), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}):
            _device_path = _utils.mCreateU02Volume(_dom0_short_name, _u02_vol_name, _disk_u02_size, _options)

        mock_mCreateEDVVolume.assert_called_once_with('cell1', _disk_u02_size, _u02_vol_name, _options, aVaultName='systemVault')
        mock_mGetVolumeID.assert_called_once_with('cell1', _u02_vol_name, _options, aVaultName='systemVault')
        mock_mGetEDVInitiator.assert_called_once_with('cell1', _dom0_short_name, _options)
        mock_mCreateEDVVolumeAttachment.assert_called_once()
        mock_mGetVolumeAttachments.assert_called_once_with('cell1', '2:vol-id', _options)
        self.assertEqual(_device_path, '/dev/exc/device-1')

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

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mUpdateVLanId_success(self, mock_connect_to_host, mock_get_gcontext):
        mock_get_gcontext.return_value = mock.Mock()

        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '200'
        _options.jsonconf['reshaped_node_subset'] = {'added_cells': [{'cell_hostname': 'cell1'}]}

        _node = mock.MagicMock()
        _stdout = mock.Mock()
        _stdout.readlines.return_value = ['150\n']
        _node.mFileExists.return_value = True
        _node.mExecuteCmd.return_value = (None, _stdout, None)
        _node.mGetCmdExitStatus.return_value = 0
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_utils, 'update_xml_tag') as mock_update_tag, \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error, \
             patch.object(_ebox, 'mRebootNode') as mock_reboot:
            _utils.mUpdateVLanId(_options)

        mock_update_tag.assert_called_once_with('/tmp/cell.conf.new', 'Qinq_vlan_id', '200')
        _node.mCopy2Local.assert_called_once_with('/opt/oracle.cellos/cell.conf', '/tmp/cell.conf.new')
        _node.mCopyFile.assert_called_once_with('/tmp/cell.conf.new', '/opt/oracle.cellos/cell.conf.new')
        _node.mExecuteCmdLog.assert_called_once_with('/usr/local/bin/ipconf -force -newconf /opt/oracle.cellos/cell.conf.new')
        mock_reboot.assert_called_once_with('cell1')
        mock_update_error.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mUpdateVLanId_missing_file(self, mock_connect_to_host, mock_get_gcontext):
        mock_get_gcontext.return_value = mock.Mock()

        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '200'
        _options.jsonconf['reshaped_node_subset'] = {'added_cells': [{'cell_hostname': 'cell1'}]}

        _node = mock.MagicMock()
        _node.mFileExists.return_value = False
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mUpdateVLanId(_options)

        mock_update_error.assert_called_once()
        _node.mCopy2Local.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mUpdateVLanId_already_configured(self, mock_connect_to_host, mock_get_gcontext):
        mock_get_gcontext.return_value = mock.Mock()

        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '200'
        _options.jsonconf['reshaped_node_subset'] = {'added_cells': [{'cell_hostname': 'cell1'}]}

        _node = mock.MagicMock()
        _stdout = mock.Mock()
        _stdout.readlines.return_value = ['200\n']
        _node.mFileExists.return_value = True
        _node.mExecuteCmd.return_value = (None, _stdout, None)
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_utils, 'update_xml_tag') as mock_update_tag, \
             patch.object(_ebox, 'mRebootNode') as mock_reboot:
            _utils.mUpdateVLanId(_options)

        mock_update_tag.assert_not_called()
        _node.mCopy2Local.assert_not_called()
        mock_reboot.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mUpdateVLanId_ipconf_failure(self, mock_connect_to_host, mock_get_gcontext):
        mock_get_gcontext.return_value = mock.Mock()

        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '200'
        _options.jsonconf['reshaped_node_subset'] = {'added_cells': [{'cell_hostname': 'cell1'}]}

        _node = mock.MagicMock()
        _stdout = mock.Mock()
        _stdout.readlines.return_value = ['150\n']
        _node.mFileExists.return_value = True
        _node.mExecuteCmd.return_value = (None, _stdout, None)
        _node.mGetCmdExitStatus.return_value = 1
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_utils, 'update_xml_tag'), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mUpdateVLanId(_options)

        mock_update_error.assert_called_once()
        _node.mCopy2Local.assert_called_once_with('/opt/oracle.cellos/cell.conf', '/tmp/cell.conf.new')

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock())
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mValidateAcfs_success(self, mock_connect_to_host, _mock_ctx):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        payload = json.loads(EXASCALE_PAYLOAD)
        payload['exascale']['db_vault'] = {'name': 'vault1'}
        _options.jsonconf = payload

        _stdout = mock.Mock()
        _stdout.readlines.return_value = ['ONLINE,ONLINE']
        _node = mock.MagicMock()
        _node.mExecuteCmd.side_effect = [
            (None, _stdout, None),
            (None, _stdout, None)
        ]
        _node.mGetCmdExitStatus.side_effect = [0, 0]
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_ebox, 'mGetOracleBaseDirectories', return_value=('/u01/app/19c/grid', None, None)), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            _utils.mValidateAcfs('domu1', None, _options)

        self.assertEqual(_node.mExecuteCmd.call_count, 2)
        _node.mExecuteCmdLog.assert_any_call('/usr/bin/df -Th | /bin/grep acfs')
        _node.mExecuteCmdLog.assert_any_call(f'/usr/sbin/edvutil volinfo {ACFS_VOL}')
        mock_update_error.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock())
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mValidateAcfs_fallback_vault_name(self, mock_connect_to_host, _mock_ctx):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {'exascale': {}}

        _escli = mock.Mock()
        _escli.mGetDBVaultName.return_value = 'fallbackVault'
        _utils._ebExascaleUtils__escli = _escli

        _stdout = mock.Mock()
        _stdout.readlines.return_value = ['ONLINE,ONLINE']
        _node = mock.MagicMock()
        _node.mExecuteCmd.side_effect = [
            (None, _stdout, None),
            (None, _stdout, None)
        ]
        _node.mGetCmdExitStatus.side_effect = [0, 0]
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_ebox, 'mGetOracleBaseDirectories', return_value=('/u01/app/19c/grid', None, None)), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            _utils.mValidateAcfs('domu1', '/u01/app/19c/grid', _options)

        _escli.mGetDBVaultName.assert_called_once()
        mock_update_error.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock())
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mValidateAcfs_crs_offline(self, mock_connect_to_host, _mock_ctx):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        payload = json.loads(EXASCALE_PAYLOAD)
        payload['exascale']['db_vault'] = {'name': 'vault1'}
        _options.jsonconf = payload

        _stdout_offline = mock.Mock()
        _stdout_offline.readlines.return_value = ['OFFLINE,ONLINE']
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (None, _stdout_offline, None)
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_ebox, 'mGetOracleBaseDirectories', return_value=('/u01/app/19c/grid', None, None)), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mValidateAcfs('domu1', None, _options)

        mock_update_error.assert_called_once()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock())
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mValidateAcfs_acfs_offline(self, mock_connect_to_host, _mock_ctx):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        payload = json.loads(EXASCALE_PAYLOAD)
        payload['exascale']['db_vault'] = {'name': 'vault1'}
        _options.jsonconf = payload

        _stdout_online = mock.Mock()
        _stdout_online.readlines.return_value = ['ONLINE,ONLINE']
        _stdout_offline = mock.Mock()
        _stdout_offline.readlines.return_value = ['ONLINE,OFFLINE']
        _node = mock.MagicMock()
        _node.mExecuteCmd.side_effect = [
            (None, _stdout_online, None),
            (None, _stdout_offline, None)
        ]
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_ebox, 'mGetOracleBaseDirectories', return_value=('/u01/app/19c/grid', None, None)), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mValidateAcfs('domu1', None, _options)

        mock_update_error.assert_called_once()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock())
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mValidateAcfs_df_failure(self, mock_connect_to_host, _mock_ctx):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        payload = json.loads(EXASCALE_PAYLOAD)
        payload['exascale']['db_vault'] = {'name': 'vault1'}
        _options.jsonconf = payload

        _stdout = mock.Mock()
        _stdout.readlines.return_value = ['ONLINE,ONLINE']
        _node = mock.MagicMock()
        _node.mExecuteCmd.side_effect = [
            (None, _stdout, None),
            (None, _stdout, None)
        ]
        _node.mExecuteCmdLog.side_effect = [None, None]
        _node.mGetCmdExitStatus.side_effect = [0, 1]
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_ebox, 'mGetOracleBaseDirectories', return_value=('/u01/app/19c/grid', None, None)), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mValidateAcfs('domu1', None, _options)

        mock_update_error.assert_called_once()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock())
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mValidateAcfs_volinfo_failure(self, mock_connect_to_host, _mock_ctx):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        payload = json.loads(EXASCALE_PAYLOAD)
        payload['exascale']['db_vault'] = {'name': 'vault1'}
        _options.jsonconf = payload

        _stdout = mock.Mock()
        _stdout.readlines.return_value = ['ONLINE,ONLINE']
        _node = mock.MagicMock()
        _node.mExecuteCmd.side_effect = [
            (None, _stdout, None),
            (None, _stdout, None)
        ]
        # First command (df) returns 0, second command (volinfo) returns 1
        _node.mExecuteCmdLog.side_effect = [None, None]
        _node.mGetCmdExitStatus.side_effect = [0, 1]
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        with patch.object(_ebox, 'mGetOracleBaseDirectories', return_value=('/u01/app/19c/grid', None, None)), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mValidateAcfs('domu1', None, _options)

        mock_update_error.assert_called_once()

    # ---------- mCreateDbVault ----------
    def test_mCreateDbVault_success_mocked(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(CREATE_DBVAULT_PAYLOAD)

        create_out = json.dumps({
            'data': {
                'id': 'vault1-id',
                'attributes': {
                    'spaceProvHC': 32212254720,
                    'spaceUsedHC': 2147483648
                }
            }
        })

        _escli = mock.Mock()
        _escli.mListVault.return_value = (1, '', '')
        _escli.mCreateVault.return_value = (0, create_out, '')
        _escli.mIsEFRack.return_value = False
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_utils, 'mGetStoragePoolDetails', return_value={'name': 'hcpool'}) as mock_pool, \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            rc = _utils.mCreateDbVault(_options)

        self.assertEqual(rc, 0)
        _escli.mListVault.assert_called_once()
        _escli.mCreateVault.assert_called_once()
        mock_pool.assert_called_once()
        mock_update.assert_called_once()

    def test_mCreateDbVault_already_exists_mocked(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(CREATE_DBVAULT_PAYLOAD)

        _escli = mock.Mock()
        _escli.mListVault.return_value = (0, '', '')
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_utils, 'mGetStoragePoolDetails'), \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mCreateDbVault(_options)

        _escli.mCreateVault.assert_not_called()
        mock_update.assert_called_once()

    def test_mCreateDbVault_create_failure_mocked(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(CREATE_DBVAULT_PAYLOAD)

        _escli = mock.Mock()
        _escli.mListVault.return_value = (1, '', '')
        _escli.mCreateVault.return_value = (1, '', 'error')
        _escli.mIsEFRack.return_value = False
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_utils, 'mGetStoragePoolDetails'), \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mCreateDbVault(_options)

        _escli.mCreateVault.assert_called_once()
        mock_update.assert_called_once()

    def test_mDeleteDbVault_success_mocked(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        payload = json.loads(DELETE_DBVAULT_PAYLOAD)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = {
            'cell_list': payload['cell_list'],
            'db_vault': payload['db_vault'],
            'storage_pool': payload['storage_pool']
        }

        _escli = mock.Mock()
        _escli.mListVault.return_value = (0, '', '')
        _escli.mRemoveVault.return_value = (0, '', '')
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_utils, 'mGetStoragePoolDetails', return_value={'name': 'hcpool'}) as mock_pool, \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            rc = _utils.mDeleteDbVault(_options)

        self.assertEqual(rc, 0)
        _escli.mRemoveVault.assert_called_once()
        mock_pool.assert_called_once()
        mock_update.assert_called_once()

    def test_mDeleteDbVault_not_found(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        payload = json.loads(DELETE_DBVAULT_PAYLOAD)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = {
            'cell_list': payload['cell_list'],
            'db_vault': payload['db_vault'],
            'storage_pool': payload['storage_pool']
        }

        _escli = mock.Mock()
        _escli.mListVault.return_value = (1, '', '')
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_utils, 'mGetStoragePoolDetails') as mock_pool, \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            rc = _utils.mDeleteDbVault(_options)

        self.assertEqual(rc, 0)
        _escli.mRemoveVault.assert_not_called()
        mock_pool.assert_called_once()
        mock_update.assert_called_once()

    def test_mDeleteDbVault_remove_failure(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        payload = json.loads(DELETE_DBVAULT_PAYLOAD)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = {
            'cell_list': payload['cell_list'],
            'db_vault': payload['db_vault'],
            'storage_pool': payload['storage_pool']
        }

        _escli = mock.Mock()
        _escli.mListVault.return_value = (0, '', '')
        _escli.mRemoveVault.return_value = (1, '', 'error')
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_utils, 'mGetStoragePoolDetails'), \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mDeleteDbVault(_options)

        _escli.mRemoveVault.assert_called_once()
        mock_update.assert_called_once()

    def test_mUpdateDbVault_success_mocked(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        payload = json.loads(UPDATE_DBVAULT_PAYLOAD)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = {
            'cell_list': payload['cell_list'],
            'db_vault': payload['db_vault'],
            'storage_pool': payload['storage_pool']
        }

        list_response = json.dumps({
            'data': {
                'id': 'vault1',
                'attributes': {
                    'spaceProvHC': 10 * 1024 ** 3,
                    'spaceUsedHC': 2 * 1024 ** 3
                }
            }
        })

        _escli = mock.Mock()
        _escli.mListVault.return_value = (0, list_response, '')
        _escli.mChangeVault.return_value = (0, '', '')
        _escli.mIsEFRack.return_value = False
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_utils, 'mGetStoragePoolDetails', return_value={'name': 'hcpool'}) as mock_pool, \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            rc = _utils.mUpdateDbVault(_options)

        self.assertEqual(rc, 0)
        _escli.mChangeVault.assert_called_once()
        mock_pool.assert_called_once()
        mock_update.assert_called_once()

    def test_mUpdateDbVault_success_outdated_pool(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        payload = json.loads(UPDATE_DBVAULT_PAYLOAD)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = {
            'cell_list': payload['cell_list'],
            'db_vault': payload['db_vault'],
            'storage_pool': payload['storage_pool']
        }

        list_response = json.dumps({
            'data': {
                'id': 'vault1',
                'attributes': {
                    'spaceProvHC': 10 * 1024 ** 3,
                    'spaceUsedHC': 0
                }
            }
        })

        _escli = mock.Mock()
        _escli.mListVault.return_value = (0, list_response, '')
        _escli.mChangeVault.return_value = (0, '', '')
        _escli.mIsEFRack.return_value = False
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'scaqab10celadm01.us.oracle.com': object()}), \
             patch.object(_utils, 'mGetStoragePoolDetails', return_value={'name': 'hcpool', 'refreshed': True}) as mock_pool, \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            rc = _utils.mUpdateDbVault(_options)

        self.assertEqual(rc, 0)
        _escli.mChangeVault.assert_called_once()
        mock_pool.assert_called_once()
        mock_update.assert_called_once()

    def test_mUpdateDbVault_not_found_mocked(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        payload = json.loads(UPDATE_DBVAULT_PAYLOAD)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = {
            'cell_list': payload['cell_list'],
            'db_vault': payload['db_vault'],
            'storage_pool': payload['storage_pool']
        }

        _escli = mock.Mock()
        _escli.mListVault.return_value = (1, '', '')
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mUpdateDbVault(_options)

        _escli.mChangeVault.assert_not_called()
        mock_update.assert_called_once()

    def test_mUpdateDbVault_change_failure_mocked(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        payload = json.loads(UPDATE_DBVAULT_PAYLOAD)
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = {
            'cell_list': payload['cell_list'],
            'db_vault': payload['db_vault'],
            'storage_pool': payload['storage_pool']
        }

        list_response = json.dumps({
            'data': {
                'id': 'vault1',
                'attributes': {
                    'spaceProvHC': 10 * 1024 ** 3,
                    'spaceUsedHC': 2 * 1024 ** 3
                }
            }
        })

        _escli = mock.Mock()
        _escli.mListVault.return_value = (0, list_response, '')
        _escli.mChangeVault.return_value = (1, '', 'error')
        _escli.mIsEFRack.return_value = False
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_utils, '_mUpdateRequestData') as mock_update:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mUpdateDbVault(_options)

        _escli.mChangeVault.assert_called_once()
        mock_update.assert_called_once()

    def test_mRemoveUser_success(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_ebox, 'mIsOciEXACC', return_value=False), \
             patch.object(_ebox.mGetClusters().mGetCluster(), 'mGetCluName', return_value='ClusterZ'):

            _escli_mock = mock.Mock()
            _utils._ebExascaleUtils__escli = _escli_mock

            _utils.mRemoveUser(_options)

        self.assertEqual(_escli_mock.mRemoveUser.call_count, 2)
        _escli_mock.mRemoveUser.assert_has_calls([
            mock.call('cell1', 'gridClusterZ', _options),
            mock.call('cell1', 'oracleClusterZ', _options)
        ])

    def test_mRemoveUser_fetch_from_payload(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        payload = json.loads(EXASCALE_PAYLOAD)
        payload['rack'] = {'name': 'PayloadCluster'}
        _options.jsonconf = payload

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_ebox, 'mIsOciEXACC', return_value=False), \
             patch.object(_ebox.mGetClusters().mGetCluster(), 'mGetCluName', return_value='ClusterZ'):

            _escli_mock = mock.Mock()
            _utils._ebExascaleUtils__escli = _escli_mock

            _utils.mRemoveUser(_options)

        self.assertEqual(_escli_mock.mRemoveUser.call_count, 2)
        _escli_mock.mRemoveUser.assert_has_calls([
            mock.call('cell1', 'gridClusterZ', _options),
            mock.call('cell1', 'oracleClusterZ', _options)
        ])

    def test_mRemoveUser_failure(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch.object(_ebox, 'mIsOciEXACC', return_value=True):

            _escli_mock = mock.Mock()
            _escli_mock.mRemoveUser.side_effect = ExacloudRuntimeError(aErrorMsg='failure')
            _utils._ebExascaleUtils__escli = _escli_mock

            with self.assertRaises(ExacloudRuntimeError):
                _utils.mRemoveUser(_options)

        _escli_mock.mRemoveUser.assert_called_once()

    def test_mDeleteFilesInDbVault_success(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        payload = json.loads(EXASCALE_PAYLOAD)
        payload['exascale']['db_vault'] = {'name': 'vault1'}
        _options.jsonconf = payload

        _escli_mock = mock.Mock()
        _escli_mock.mListFiles.side_effect = [[], [], []]
        _utils._ebExascaleUtils__escli = _escli_mock

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}):
            _utils.mDeleteFilesInDbVault(_options)

        _escli_mock.mRemoveFile.assert_not_called()

    def test_mDeleteFilesInDbVault_retry_success(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        payload = json.loads(EXASCALE_PAYLOAD)
        payload['exascale']['db_vault'] = {'name': 'vault1'}
        _options.jsonconf = payload

        _escli_mock = mock.Mock()
        # First pass returns files, second pass returns empty
        _escli_mock.mListFiles.side_effect = [
            ['file1'], ['file2'], [],
            [], [], []
        ]
        _utils._ebExascaleUtils__escli = _escli_mock

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch('time.sleep'):
            _utils.mDeleteFilesInDbVault(_options)

        _escli_mock.mRemoveFile.assert_called()

    def test_mDeleteFilesInDbVault_failure(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        payload = json.loads(EXASCALE_PAYLOAD)
        payload['exascale']['db_vault'] = {'name': 'vault1'}
        _options.jsonconf = payload

        _escli_mock = mock.Mock()
        _escli_mock.mListFiles.side_effect = [
            ['file1'], ['file2'], ['file3']
        ] * 4
        _utils._ebExascaleUtils__escli = _escli_mock

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}), \
             patch('time.sleep'), \
             self.assertRaises(ExacloudRuntimeError):
            _utils.mDeleteFilesInDbVault(_options)

        _escli_mock.mRemoveFile.assert_called()

    def test_mResizeEDVVolume_success(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _escli = mock.Mock()
        _escli.mGetVolumeID.return_value = ('2:vol-id', None)
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}):
            _utils.mResizeEDVVolume('vol1', '60G', _options)

        _escli.mGetVolumeID.assert_called_once_with('cell1', 'vol1', _options)
        _escli.mResizeEDVVolume.assert_called_once_with('cell1', '60G', '2:vol-id', _options)

    def test_mResizeEDVVolume_fallback_ctrl_ip(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale'].pop('ctrl_network', None)

        _escli = mock.Mock()
        _escli.mGetCtrlIP.return_value = ('10.0.0.1', 'host')
        _escli.mGetVolumeID.return_value = ('2:vol-id', None)
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': object()}):
            _utils.mResizeEDVVolume('vol1', '80G', _options)

        _escli.mGetCtrlIP.assert_called_once()
        _escli.mGetVolumeID.assert_called_once_with('cell1', 'vol1', _options)
        _escli.mResizeEDVVolume.assert_called_once_with('cell1', '80G', '2:vol-id', _options)
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeACL')
    def test_mUpdateACL(self, mock_mChangeACL):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mUpdateACL(_options)

   # Auto-generated test for mUpdateACL
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeACL')
    def test_mUpdateACL_with_explicit_host(self, mock_mChangeACL):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {"rack": {"name": "rack-one"}}

        _utils = ebExascaleUtils(_ebox)
        _utils.mUpdateACL(_options, aHost='domu1', aVaultName='vaultA', aAclPriv='rw')

        mock_mChangeACL.assert_called_once_with(_cell, None, 'rw', _options, 'domu1', aVaultName='vaultA')

   # Auto-generated test for mGetVaultName
    def test_mGetVaultName_prefers_image_vault(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {
            "rack": {
                "xsVmImage": True,
                "system_vault": [
                    {"vault_type": "backup", "name": "backupVault"},
                    {"vault_type": "image", "name": "imageVault"},
                ],
            }
        }

        result = _utils.mGetVaultName(_options, aVaultType="image")
        self.assertEqual(result, "imageVault")
        _options.jsonconf["rack"]["system_vault"].reverse()
        result_rev = _utils.mGetVaultName(_options, aVaultType="image")
        self.assertEqual(result_rev, "imageVault")

   # Auto-generated test for mGetVaultName
    def test_mGetVaultName_backup_vault(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {
            "rack": {
                "xsVmBackup": True,
                "system_vault": [
                    {"vault_type": "image", "name": "imageVault"},
                    {"vault_type": "backup", "name": "backupVault"},
                ],
            }
        }

        result = _utils.mGetVaultName(_options, aVaultType="backup")
        self.assertEqual(result, "backupVault")

   # Auto-generated test for mGetVaultName
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetDBVaultName', return_value='dbVaultName')
    def test_mGetVaultName_default_dbvault(self, mock_get_db_vault):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {}

        result = _utils.mGetVaultName(_options)
        self.assertEqual(result, 'dbVaultName')
        mock_get_db_vault.assert_called_once()

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
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetDBServerStatus', return_value=(0, "running"))
    def test_mCreateSysVault(self, mock_mCreateVault, mock_mIsEFRack, mock_mGetCtrlIP, mock_db_status):
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

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeACL')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault', return_value=(0,"spaceUsedHC\n 20G",""))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVault', return_value=(0, CREATE_DBVAULT_OUTPUT, ""))
    def test_mUpdateSysVault(self, mock_mChangeVault, mock_mListVault, mock_mIsEFRack, mock_mChangeACL):
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

# Auto-generated test for mUpdateSysVault
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeACL')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetStoragePoolDetails', return_value={})
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVault', return_value=(0, '', ''))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetDBServerStatus', return_value=(0, "running"))
    def test_mUpdateSysVault_raises_when_resize_less_than_used(self, mock_GetDBServerStatus, mock_change_vault, mock_list_vault, mock_is_ef_rack, mock_get_pool, mock_ChangeACL):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _payload = json.loads(UPDATE_SYSVAULT_PAYLOAD)
        _payload['system_vault']['gb_size'] = 1
        _options.jsonconf = _payload

        _list_payload = {
            "data": {
                "attributes": {
                    "spaceUsedHC": 34359738368,
                    "spaceProvHC": 42949672960
                }
            }
        }
        mock_list_vault.return_value = (0, json.dumps(_list_payload), "")

        _utils = ebExascaleUtils(_ebox)

        with self.assertRaises(ExacloudRuntimeError) as _ctx:
            _utils.mUpdateSysVault(_options)

        _err = str(_ctx.exception)
        self.assertIn('Unable to update the vault', _err)
        mock_change_vault.assert_not_called()

# Auto-generated test for mUpdateSysVault
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeACL')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetStoragePoolDetails', return_value={})
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils._mUpdateRequestData')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVault', return_value=(1, '', 'failed change'))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetDBServerStatus', return_value=(0, "running"))
    def test_mUpdateSysVault_change_failure_propagates(self, mock_GetDBServerStatus, mock_change_vault, mock_list_vault, mock_is_ef_rack, mock_update_request, mock_get_pool, mock_ChangeACL):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(UPDATE_SYSVAULT_PAYLOAD)
        _list_payload = {
            "data": {
                "attributes": {
                    "spaceUsedHC": 10485760,
                    "spaceProvHC": 32212254720
                }
            }
        }
        mock_list_vault.return_value = (0, json.dumps(_list_payload), "")

        _utils = ebExascaleUtils(_ebox)

        with self.assertRaises(ExacloudRuntimeError) as _ctx:
            _utils.mUpdateSysVault(_options)

        _err = str(_ctx.exception)
        self.assertIn('Unable to get current DBVault', _err)
        mock_update_request.assert_called()

# Auto-generated test for mUpdateSysVault
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeACL')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetStoragePoolDetails', return_value={'pool': 'details'})
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils._mUpdateRequestData')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mIsEFRack', return_value=False)
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mListVault')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVault')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetDBServerStatus', return_value=(0, "running"))
    def test_mUpdateSysVault_success_updates_response(self, mock_GetDBServerStatus, mock_change_vault, mock_list_vault, mock_is_ef_rack, mock_update_request, mock_get_pool, mock_ChangeACL):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _payload = json.loads(UPDATE_SYSVAULT_PAYLOAD)
        _payload['system_vault']['vault_ocid'] = 'ocid1.vault'
        _payload['system_vault']['gb_size'] = 20
        _options.jsonconf = _payload

        _list_payload = {
            'data': {
                'attributes': {
                    'spaceUsedHC': 8589934592,
                    'spaceProvHC': 32212254720
                }
            }
        }
        mock_list_vault.return_value = (0, json.dumps(_list_payload), '')

        _change_payload = {
            'data': {
                'id': 'vault1clu02-ref',
                'attributes': {
                    'spaceUsedHC': 8589934592,
                    'spaceProvHC': 32212254720
                }
            }
        }
        mock_change_vault.return_value = (0, json.dumps(_change_payload), '')

        _utils = ebExascaleUtils(_ebox)
        _ret = _utils.mUpdateSysVault(_options)

        self.assertEqual(_ret, 0)
        mock_is_ef_rack.assert_called()
        mock_list_vault.assert_called_once()
        mock_change_vault.assert_called_once()
        mock_get_pool.assert_called_once_with(_payload['cell_list'][0], _payload['storage_pool'], _options)

        mock_update_request.assert_called_once()
        _args, _kwargs = mock_update_request.call_args
        self.assertEqual(_args[0], 0)
        _data = _args[1]
        self.assertIn('system_vault', _data)
        _vault_data = _data['system_vault']
        self.assertEqual(_vault_data['name'], _payload['system_vault']['name'])
        self.assertEqual(_vault_data['ref_id'], 'vault1clu02-ref')
        self.assertEqual(_vault_data['vault_ocid'], 'ocid1.vault')
        self.assertEqual(_vault_data['total_storage_gb'], 10)
        self.assertEqual(_vault_data['used_storage_gb'], 3)
        self.assertIn('storage_pool', _data)
        self.assertEqual(_data['storage_pool'], {'pool': 'details'})

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

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mIsEDVImageSupported', return_value=True)
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVolume')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
    def test_mUpdateSystemVaultAccess(self, mock_mGetVolumeID, mock_mChangeVolume, mock_mIsEDVImageSupported):
        _ebox = self.mGetClubox()

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mUpdateSystemVaultAccess(_options)

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mIsEDVImageSupported', return_value=True)
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVVolume')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mRemoveEDVAttachment')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeAttachments', return_value=("3:175ebf661f8e49c09d03f8214f6c5b39", "2:b4d00303b12f46d6a31b4a5339395cd3", "c3716n16c2_u02_6bb25ab338ee4a2298ef628c2403829a"))
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:b4d00303b12f46d6a31b4a5339395cd3", "admin"))
    def test_mRemoveGuestEDVVolumes(self, mGetVolumeID, mock_mGetVolumeAttachments, mock_mRemoveEDVAttachment,
                             mock_mRemoveEDVVolume, mock_mIsEDVImageSupported):
        _ebox = self.mGetClubox()
        _ddpair = _ebox.mReturnDom0DomUPair()
        _dom0, _domU = _ddpair[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mRemoveGuestEDVVolumes(_options)

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVolume')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:vol-id", "compute1"))
    def test_mAlterVolumeAccess_owner_match(self, mock_mGetVolumeID, mock_mChangeVolume):
        _ebox = self.mGetClubox()

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _utils.mAlterVolumeAccess("compute1", "vol1", _options)

        mock_mChangeVolume.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mChangeVolume')
    @patch('exabox.ovm.csstep.exascale.escli_util.ebEscliUtils.mGetVolumeID', return_value=("2:vol-id", "compute2"))
    def test_mAlterVolumeAccess_owner_mismatch(self, mock_mGetVolumeID, mock_mChangeVolume):
        _ebox = self.mGetClubox()

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _utils = ebExascaleUtils(_ebox)
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _utils.mAlterVolumeAccess("compute1", "vol1", _options)

        mock_mChangeVolume.assert_called_once_with(_cell, "2:vol-id", "compute1", _options)

    @patch('exabox.ovm.csstep.exascale.exascaleutils.TemporaryDirectory')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.OedacliCmdMgr')
    def test_mRemoveVmMachines_single_pair(self, mock_oedacli_cmd_mgr, mock_tempdir):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        mock_tempdir.return_value.__enter__.return_value = '/tmp/tmpdir'
        mock_tempdir.return_value.__exit__.return_value = None
        _oedacli_instance = mock_oedacli_cmd_mgr.return_value

        _xsconfig_path = '/tmp/oeda/exacloud.conf/xsconfig_uuid1.xml'
        with patch.object(_ebox, 'mReturnDom0DomUPair', return_value=[('dom0a', 'domua')]), \
             patch.object(_ebox, 'mGetUUID', return_value='uuid1'), \
             patch.object(_ebox, 'mGetOedaPath', return_value='/tmp/oeda'), \
             patch.object(_ebox, 'mGetPatchConfig', return_value='/tmp/base/config.xml'), \
             patch.object(_ebox, 'mGetBasePath', return_value='/tmp/base'), \
             patch.object(_ebox, 'mExecuteLocal') as mock_execute_local, \
             patch.object(_ebox, 'mUpdateInMemoryXmlConfig') as mock_update_xml, \
             patch.object(_ebox, 'mSetRemoteConfig') as mock_set_remote:

            _utils = ebExascaleUtils(_ebox)
            _utils.mRemoveVmMachines(_options)

        mock_oedacli_cmd_mgr.assert_called_once_with('/tmp/oeda/oedacli', '/tmp/tmpdir')
        _oedacli_instance.mDelNode.assert_called_once_with('domua', None, aSrcXml=_xsconfig_path, aDestXml=_xsconfig_path, aDeploy=False)

        _mkdir_call = mock_execute_local.call_args_list[0]
        self.assertEqual(_mkdir_call[0][0], '/bin/mkdir -p /tmp/oeda/exacloud.conf')
        self.assertEqual(_mkdir_call[1]['aCurrDir'], '/tmp/base')
        _copy_call = mock_execute_local.call_args_list[1]
        self.assertEqual(_copy_call[0][0], '/bin/cp /tmp/base/config.xml /tmp/oeda/exacloud.conf/xsconfig_uuid1.xml')
        self.assertEqual(_copy_call[1]['aCurrDir'], '/tmp/base')

        mock_update_xml.assert_called_once_with(_xsconfig_path, _options)
        mock_set_remote.assert_called_once_with('/tmp/base/config.xml')

    @patch('exabox.ovm.csstep.exascale.exascaleutils.TemporaryDirectory')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.OedacliCmdMgr')
    def test_mRemoveVmMachines_multiple_pairs(self, mock_oedacli_cmd_mgr, mock_tempdir):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        mock_tempdir.return_value.__enter__.return_value = '/tmp/tmpdir'
        mock_tempdir.return_value.__exit__.return_value = None
        _oedacli_instance = mock_oedacli_cmd_mgr.return_value

        pairs = [('dom0a', 'domua'), ('dom0b', 'domub')]
        with patch.object(_ebox, 'mReturnDom0DomUPair', return_value=pairs), \
             patch.object(_ebox, 'mGetUUID', return_value='uuid2'), \
             patch.object(_ebox, 'mGetOedaPath', return_value='/tmp/oeda'), \
             patch.object(_ebox, 'mGetPatchConfig', return_value='/tmp/base/config.xml'), \
             patch.object(_ebox, 'mGetBasePath', return_value='/tmp/base'), \
             patch.object(_ebox, 'mExecuteLocal'), \
             patch.object(_ebox, 'mUpdateInMemoryXmlConfig'), \
             patch.object(_ebox, 'mSetRemoteConfig'):

            _utils = ebExascaleUtils(_ebox)
            _utils.mRemoveVmMachines(_options)

        self.assertEqual(_oedacli_instance.mDelNode.call_count, len(pairs))
        _xsconfig_path = '/tmp/oeda/exacloud.conf/xsconfig_uuid2.xml'
        _oedacli_instance.mDelNode.assert_any_call('domua', None, aSrcXml=_xsconfig_path, aDestXml=_xsconfig_path, aDeploy=False)
        _oedacli_instance.mDelNode.assert_any_call('domub', None, aSrcXml=_xsconfig_path, aDestXml=_xsconfig_path, aDeploy=False)

    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mCheckRoCEIPs_all_interfaces_configured(self, mock_connect_to_host):
        _ebox = self.mGetClubox()

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _node = mock.MagicMock()
        _node.mGetCmdExitStatus.return_value = 0
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        _failed_list = []
        _utils = ebExascaleUtils(_ebox)
        _result = _utils.mCheckRoCEIPs(_options, _failed_list)

        self.assertTrue(_result)
        self.assertEqual(_failed_list, [])
        _node.mExecuteCmdLog.assert_any_call("/usr/sbin/ip a s stre0 | /bin/grep inet | grep 100.106.2.0")
        _node.mExecuteCmdLog.assert_any_call("/usr/sbin/ip a s stre1 | /bin/grep inet | grep 100.106.2.1")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetupNatNfTablesOnDom0v2')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.start_domu')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd_check')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd')
    def test_mSetupRoCEIPs_success(self, mock_node_exec_cmd, mock_node_exec_cmd_check,
                                   mock_start_domu, mock_connect_to_host, mock_mSetupNatNfTablesOnDom0v2):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '631'

        _failed_list = ["scaqab10adm01.us.oracle.com"]

        _node = mock.MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        mock_node_exec_cmd.return_value = (0, "configured", "")
        node_exec_result = mock.Mock()
        node_exec_result.stdout = "domu1\n"
        mock_node_exec_cmd_check.return_value = node_exec_result
        _node.mGetCmdExitStatus.side_effect = [1, 1, 0, 0]

        with patch.object(_ebox, 'mRebootNode') as mock_reboot:
            _utils.mSetupRoCEIPs(_options, _failed_list)

        mock_node_exec_cmd.assert_called_with(
            _node,
            '/usr/sbin/vm_maker --set --storage-vlan 631 --ip 100.106.2.0 --netmask 255.255.0.0'
        )
        mock_start_domu.assert_called_once_with(_node, 'domu1', wait_for_connectable=False)
        _node.mExecuteCmdLog.assert_any_call("/usr/sbin/ip a s stre0 | /bin/grep 100.106.2.0")
        _node.mExecuteCmdLog.assert_any_call("/usr/sbin/ip a s stre1 | /bin/grep inet")
        mock_reboot.assert_not_called()

    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd')
    def test_mSetupRoCEIPs_missing_payload_fields(self, mock_node_exec_cmd, mock_connect_to_host):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '631'
        del _options.jsonconf['exascale']['host_nodes'][0]['storage_ip1']

        with self.assertRaises(ExacloudRuntimeError):
            _utils.mSetupRoCEIPs(_options, ['scaqab10adm01.us.oracle.com'])

        mock_node_exec_cmd.assert_not_called()

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetupNatNfTablesOnDom0v2')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.start_domu')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd_check')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd')
    def test_mSetupRoCEIPs_filtered_dom0_list(self, mock_node_exec_cmd, mock_node_exec_cmd_check,
                                              mock_start_domu, mock_connect_to_host, mock_mSetupNatNfTablesOnDom0v2):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '631'
        _options.jsonconf['exascale']['host_nodes'].append({
            "compute_hostname": "scaqab10adm02.us.oracle.com",
            "interface1": "stre0",
            "interface2": "stre1",
            "storage_ip1": "100.106.3.0",
            "storage_ip2": "100.106.3.1",
            "netmask": None
        })

        _failed_list = ['scaqab10adm02.us.oracle.com']

        _node = mock.MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        mock_node_exec_cmd.return_value = (0, "configured", "")
        mock_node_exec_cmd_check.return_value = mock.Mock(stdout="")
        _node.mGetCmdExitStatus.side_effect = [1, 1, 0, 0]

        with patch.object(_ebox, 'mRebootNode') as mock_reboot:
            _utils.mSetupRoCEIPs(_options, _failed_list, aDom0List=['scaqab10adm02.us.oracle.com'])

        mock_node_exec_cmd.assert_called_with(
            _node,
            '/usr/sbin/vm_maker --set --storage-vlan 631 --ip 100.106.3.0 --netmask 255.255.0.0'
        )
        mock_start_domu.assert_not_called()
        mock_reboot.assert_not_called()



    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.start_domu')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd_check')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd')
    def test_mSetupRoCEIPs_requires_dom0_reboot(self, mock_node_exec_cmd, mock_node_exec_cmd_check,
                                                mock_start_domu, mock_connect_to_host):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '631'

        _failed_list = ["scaqab10adm01.us.oracle.com"]

        _node_before = mock.MagicMock()
        _node_after = mock.MagicMock()

        _ctx_before = mock.MagicMock()
        _ctx_before.__enter__.return_value = _node_before
        _ctx_before.__exit__.return_value = None
        _ctx_after = mock.MagicMock()
        _ctx_after.__enter__.return_value = _node_after
        _ctx_after.__exit__.return_value = None
        mock_connect_to_host.side_effect = [_ctx_before, _ctx_after]

        mock_node_exec_cmd.side_effect = [
            (1, "Shut down all guests", ""),
            (0, "A reboot is required", "")
        ]

        _virsh_result = mock.Mock()
        _virsh_result.stdout = "domu1\ndomu2\n"
        mock_node_exec_cmd_check.return_value = _virsh_result

        _node_before.mGetCmdExitStatus.side_effect = [0, 1, 1]
        _node_after.mGetCmdExitStatus.side_effect = [0, 0]

        with patch.object(_ebox, 'mRebootNode') as mock_reboot, \
             patch.object(_ebox, 'mSetupNatNfTablesOnDom0v2') as mock_nf_tables:
            _utils.mSetupRoCEIPs(_options, _failed_list)

        mock_node_exec_cmd.assert_has_calls([
            mock.call(_node_before, '/usr/sbin/vm_maker --set --storage-vlan 631 --ip 100.106.2.0 --netmask 255.255.0.0'),
            mock.call(_node_before, '/usr/sbin/vm_maker --set --storage-vlan 631 --ip 100.106.2.0 --netmask 255.255.0.0')
        ])
        _node_before.mExecuteCmdLog.assert_any_call('/usr/sbin/vm_maker --stop-domain --all')
        mock_reboot.assert_called_once_with('scaqab10adm01.us.oracle.com')
        mock_nf_tables.assert_called_once_with(aDom0s=['scaqab10adm01.us.oracle.com'])
        mock_start_domu.assert_has_calls([
            mock.call(_node_after, 'domu1', wait_for_connectable=False),
            mock.call(_node_after, 'domu2', wait_for_connectable=False)
        ], any_order=False)
        _node_after.mExecuteCmdLog.assert_any_call("/usr/sbin/ip a s stre0 | /bin/grep 100.106.2.0")
        _node_after.mExecuteCmdLog.assert_any_call("/usr/sbin/ip a s stre1 | /bin/grep inet")


    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.start_domu')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd_check')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd')
    def test_mSetupRoCEIPs_vm_maker_failure(self, mock_node_exec_cmd, mock_node_exec_cmd_check,
                                            mock_start_domu, mock_connect_to_host):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '631'

        _failed_list = ["scaqab10adm01.us.oracle.com"]

        _node = mock.MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        mock_node_exec_cmd.return_value = (1, "failure", "error")

        _virsh_result = mock.Mock()
        _virsh_result.stdout = "domu1\n"
        mock_node_exec_cmd_check.return_value = _virsh_result

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError):
                _utils.mSetupRoCEIPs(_options, _failed_list)

        mock_node_exec_cmd.assert_called_once_with(
            _node,
            '/usr/sbin/vm_maker --set --storage-vlan 631 --ip 100.106.2.0 --netmask 255.255.0.0'
        )
        mock_update_error.assert_called_once_with(gExascaleError["CONFIG_STRE_FAILED"], mock.ANY)
        mock_start_domu.assert_not_called()


    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_exec_cmd')
    def test_mSetStorageVlanOnCompute_success(self, mock_node_exec_cmd, mock_connect_to_host):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['exascale']['storage_vlan_id'] = '631'

        _failed_list = ["scaqab10adm01.us.oracle.com"]

        _node = mock.MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        mock_node_exec_cmd.return_value = (0, "configured", "")

        with patch.object(_ebox, 'mSetupNatNfTablesOnDom0v2') as mock_nf_tables:
            _ret = _utils.mSetStorageVlanOnCompute(_options, _failed_list, aDom0List=_failed_list)

        mock_node_exec_cmd.assert_called_once_with(
            _node,
            '/usr/sbin/vm_maker --set --storage-vlan 631 --ip 100.106.2.0 --netmask 255.255.0.0'
        )
        mock_nf_tables.assert_called_once_with(aDom0s=_failed_list)
        self.assertEqual(_ret, 0)

    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mCheckStorageVlanID_success(self, mock_connect_to_host):
        _ebox = self.mGetClubox()

        _node = mock.MagicMock()
        _stdout = mock.MagicMock()
        _stdout.readlines.return_value = ["VLAN:1234\n"]
        _node.mExecuteCmd.return_value = (None, _stdout, None)
        _node.mGetCmdExitStatus.return_value = 0
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        _utils = ebExascaleUtils(_ebox)
        _utils.mCheckStorageVlanID("scaqab10celadm01.us.oracle.com", "1234")

        _node.mExecuteCmd.assert_called_once_with("/bin/cat /etc/exadata/config/initqinq.conf | /bin/grep VLAN:")

    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mCheckStorageVlanID_mismatch(self, mock_connect_to_host):
        _ebox = self.mGetClubox()

        _node = mock.MagicMock()
        _stdout = mock.MagicMock()
        _stdout.readlines.return_value = ["VLAN:4321\n"]
        _node.mExecuteCmd.return_value = (None, _stdout, None)
        _node.mGetCmdExitStatus.return_value = 0
        mock_connect_to_host.return_value.__enter__.return_value = _node
        mock_connect_to_host.return_value.__exit__.return_value = None

        _utils = ebExascaleUtils(_ebox)

        with self.assertRaises(ExacloudRuntimeError) as _ctx:
            _utils.mCheckStorageVlanID("scaqab10celadm01.us.oracle.com", "1234")

        _self_msg = str(_ctx.exception)
        self.assertIn("Storage vlanID", _self_msg)

    def test_mRemoveClusterUserPrivilege_cluster_name(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _escli = mock.Mock()
        _utils._ebExascaleUtils__escli = _escli

        _utils.mRemoveClusterUserPrivilege(_options, aClusterName="iad123")

        self.assertEqual(_escli.mRemoveVMUserPrivilege.call_count, 2)
        _escli.mRemoveVMUserPrivilege.assert_has_calls([
            mock.call(_options.jsonconf['exascale']['cell_list'][0], "gridiad123", _options),
            mock.call(_options.jsonconf['exascale']['cell_list'][0], "oracleiad123", _options)
        ])

    def test_mRemoveClusterUserPrivilege_all_clusters(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _escli = mock.Mock()
        _escli.mGetUserDetails.return_value = [{"id": "gridcluster1"}, {"id": "oraclecluster2"}]
        _utils._ebExascaleUtils__escli = _escli

        _utils.mRemoveClusterUserPrivilege(_options)

        _escli.mGetUserDetails.assert_called_once()
        self.assertEqual(_escli.mRemoveVMUserPrivilege.call_count, 2)
        _escli.mRemoveVMUserPrivilege.assert_has_calls([
            mock.call(_options.jsonconf['exascale']['cell_list'][0], "gridcluster1", _options),
            mock.call(_options.jsonconf['exascale']['cell_list'][0], "oraclecluster2", _options)
        ])

    def test_mDisableNormalRedundancy_success(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _escli = mock.Mock()
        _escli.mGetClusterAttribute.return_value = (0, [{NORMAL_REDUNDANCY: True}], "")
        _escli.mListFiles.side_effect = [[{"name": "vault1"}], []]
        _escli.mChangeClusterAtributes.return_value = 0
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            _rc = _utils.mDisableNormalRedundancy(_options)

        self.assertEqual(_rc, 0)
        _escli.mListFiles.assert_called()
        _escli.mChangeClusterAtributes.assert_called_once_with(
            _options.jsonconf['exascale']['cell_list'][0],
            _options,
            aAttribute={"normalRedundancy": "false"}
        )
        mock_update_error.assert_not_called()

    def test_mDisableNormalRedundancy_already_disabled(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _escli = mock.Mock()
        _escli.mGetClusterAttribute.return_value = (0, [{NORMAL_REDUNDANCY: False}], "")
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            _rc = _utils.mDisableNormalRedundancy(_options)

        self.assertEqual(_rc, 0)
        _escli.mListFiles.assert_not_called()
        _escli.mChangeClusterAtributes.assert_not_called()
        mock_update_error.assert_not_called()

    def test_mDisableNormalRedundancy_detects_normal_files(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _escli = mock.Mock()
        _escli.mGetClusterAttribute.return_value = (0, [{NORMAL_REDUNDANCY: True}], "")
        _escli.mListFiles.side_effect = [[{"name": "vault1"}], [{"name": "file1", "redundancy": "normal"}]]
        _utils._ebExascaleUtils__escli = _escli

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError) as _ctx:
                _utils.mDisableNormalRedundancy(_options)

        mock_update_error.assert_called_once()
        _escli.mChangeClusterAtributes.assert_not_called()
        self.assertIn("NORMAL redundancy", str(_ctx.exception))

 
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

   # Auto-generated test for mPatchStorageInterconnctIps
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mFetchStorageInterconnectIps')
    def test_mPatchStorageInterconnctIps_requires_two_private_hosts(self, mock_fetch):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _utils = ebExascaleUtils(_ebox)

       _machine_config = mock.Mock()
       _machine_config.mGetMacNetworks.return_value = ['net1']
       _machines = mock.Mock()
       _machines.mGetMachineConfig.return_value = _machine_config

       _network = mock.Mock()
       _network.mGetNetType.return_value = 'private'
       _network.mGetNetHostName.return_value = 'host1'
       _networks = mock.Mock()
       _networks.mGetNetworkConfig.return_value = _network

       with patch.object(_ebox, 'mGetMachines', return_value=_machines), \
            patch.object(_ebox, 'mGetNetworks', return_value=_networks), \
            patch.object(_ebox, 'mReturnDom0DomUPair', return_value=[('dom0a', 'domua')]), \
            patch.object(_ebox, 'mGetExascaleUtils', return_value=_utils):
           with self.assertRaises(ExacloudRuntimeError):
               _utils.mPatchStorageInterconnctIps(_options)

       mock_fetch.assert_not_called()

   # Auto-generated test for mPatchStorageInterconnctIps
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mFetchStorageInterconnectIps', return_value=("", "", ""))
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebOedacli')
    def test_mPatchStorageInterconnctIps_skips_when_no_ips(self, mock_oedacli, mock_fetch):
       _ebox = self.mGetClubox()
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _utils = ebExascaleUtils(_ebox)

       _machine_config = mock.Mock()
       _machine_config.mGetMacNetworks.return_value = ['net1', 'net2']
       _machines = mock.Mock()
       _machines.mGetMachineConfig.return_value = _machine_config

       _network_priv1 = mock.Mock()
       _network_priv1.mGetNetType.return_value = 'private'
       _network_priv1.mGetNetHostName.return_value = 'host1'
       _network_priv2 = mock.Mock()
       _network_priv2.mGetNetType.return_value = 'private'
       _network_priv2.mGetNetHostName.return_value = 'host2'
       _networks = mock.Mock()
       _networks.mGetNetworkConfig.side_effect = [_network_priv1, _network_priv2]

       with patch.object(_ebox, 'mGetMachines', return_value=_machines), \
            patch.object(_ebox, 'mGetNetworks', return_value=_networks), \
            patch.object(_ebox, 'mReturnDom0DomUPair', return_value=[('dom0a', 'domua')]), \
            patch.object(_ebox, 'mGetExascaleUtils', return_value=_utils):
           _utils.mPatchStorageInterconnctIps(_options)

       mock_oedacli.assert_not_called()
       mock_fetch.assert_called_once()
       self.assertEqual(mock_fetch.call_args[1]['aDom0'], 'dom0a')

   # Auto-generated test for _mUpdateRequestData
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebGetDefaultDB')
    def test__mUpdateRequestData_updates_db(self, mock_get_db):
        mock_db = mock_get_db.return_value
        mock_request = mock.Mock()
        mock_controller = mock.Mock()
        mock_controller.mGetRequestObj.return_value = mock_request

        _utils = ebExascaleUtils(mock_controller)
        _utils._mUpdateRequestData(0, {'key': 'value'}, 'err-msg')

        mock_request.mSetData.assert_called_once()
        payload = mock_request.mSetData.call_args[0][0]
        parsed = json.loads(payload)
        self.assertEqual(parsed['success'], 'True')
        self.assertEqual(parsed['output'], {'key': 'value'})
        self.assertEqual(parsed['error'], 'err-msg')
        mock_db.mUpdateRequest.assert_called_once_with(mock_request)

   # Auto-generated test for _mUpdateRequestData
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebGetDefaultDB')
    def test__mUpdateRequestData_failure_payload(self, mock_get_db):
        mock_db = mock_get_db.return_value
        mock_request = mock.Mock()
        mock_controller = mock.Mock()
        mock_controller.mGetRequestObj.return_value = mock_request

        _utils = ebExascaleUtils(mock_controller)
        _utils._mUpdateRequestData(1, 'some-output', 'failure')

        payload = mock_request.mSetData.call_args[0][0]
        parsed = json.loads(payload)
        self.assertEqual(parsed['success'], 'False')
        self.assertEqual(parsed['output'], 'some-output')
        self.assertEqual(parsed['error'], 'failure')
        mock_db.mUpdateRequest.assert_called_once_with(mock_request)

   # Auto-generated test for _mUpdateRequestData
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebGetDefaultDB')
    def test__mUpdateRequestData_without_request(self, mock_get_db):
        mock_controller = mock.Mock()
        mock_controller.mGetRequestObj.return_value = None

        _utils = ebExascaleUtils(mock_controller)
        _utils._mUpdateRequestData(0, 'output', 'error')

        mock_get_db.assert_not_called()

    # Auto-generated test for mUpdateDnsNtpServers
    @patch('exabox.ovm.csstep.exascale.exascaleutils.OedacliCmdMgr')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.os.makedirs')
    @patch('os.path.exists', return_value=False)
    def test_mUpdateDnsNtpServers_creates_and_invokes_manager(self, mock_exists, mock_makedirs, mock_cmd_mgr):
        mock_controller = mock.Mock()
        mock_controller.mGetUUID.return_value = 'uuid-123'
        mock_controller.mGetOedaPath.return_value = '/tmp/oeda'
        mock_controller.mGetPatchConfig.return_value = '/tmp/patch.xml'
        mock_controller.mExecuteLocal = mock.Mock()

        hosts = ['dom0a', 'dom0b']
        dns_list = ['1.1.1.1']
        ntp_list = ['ntp.oracle.com']
   # Auto-generated test for mUpdateDnsNtpServers
        _utils = ebExascaleUtils(mock_controller)
        _utils.mUpdateDnsNtpServers(hosts, dns_list, ntp_list)

        expected_save_dir = '/tmp/oeda/exacloud.conf'
        # mUpdateDnsNtpServers checks for the directory and also verifies the
        # patch config path before copying. Since the test uses a dummy path
        # for the patch config, the second existence check is expected.
        mock_exists.assert_any_call(expected_save_dir)
        mock_makedirs.assert_called_once_with(expected_save_dir)

        self.assertTrue(mock_controller.mExecuteLocal.called)
        cp_cmd = mock_controller.mExecuteLocal.call_args[0][0]
        self.assertIn('/bin/cp', cp_cmd)
        manager = mock_cmd_mgr.return_value
        self.assertEqual(manager.mUpdateDnsNtpServers.call_count, len(hosts))
        expected_updated_xml = expected_save_dir + '/patched_ntp_dns_uuid-123.xml'
        mock_controller.mSetPatchConfig.assert_called_once_with(expected_updated_xml)

    # Auto-generated test for mUpdateDnsNtpServers
    @patch('exabox.ovm.csstep.exascale.exascaleutils.OedacliCmdMgr')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.os.makedirs')
    @patch('os.path.exists', return_value=True)
    def test_mUpdateDnsNtpServers_existing_directory(self, mock_exists, mock_makedirs, mock_cmd_mgr):
        mock_controller = mock.Mock()
        mock_controller.mGetUUID.return_value = 'uuid-456'
        mock_controller.mGetOedaPath.return_value = '/tmp/oeda'
        mock_controller.mGetPatchConfig.return_value = '/tmp/source.xml'
        mock_controller.mExecuteLocal = mock.Mock()

        _utils = ebExascaleUtils(mock_controller)
        _utils.mUpdateDnsNtpServers(['host'], ['8.8.8.8'], ['pool.ntp.org'])

        expected_save_dir = '/tmp/oeda/exacloud.conf'
        self.assertGreaterEqual(mock_exists.call_count, 1)
        self.assertEqual(mock_exists.call_args_list[0][0][0], expected_save_dir)
        mock_makedirs.assert_not_called()
        manager = mock_cmd_mgr.return_value
        manager.mUpdateDnsNtpServers.assert_called_once()

    # Auto-generated test for mGetCluCtrl
    def test_mGetCluCtrl_returns_controller(self):
        mock_controller = mock.Mock()
        _utils = ebExascaleUtils(mock_controller)

        result = _utils.mGetCluCtrl()

        self.assertIs(result, mock_controller)

    # Auto-generated test for mSetCluCtrl
    def test_mSetCluCtrl_updates_controller(self):
        mock_controller = mock.Mock()
        _utils = ebExascaleUtils(mock_controller)
        new_controller = mock.Mock()

        _utils.mSetCluCtrl(new_controller)

        self.assertIs(_utils.mGetCluCtrl(), new_controller)

    # Auto-generated test for mConvertFromCIDRToNetmask
    def test_mConvertFromCIDRToNetmask(self):
        mock_controller = mock.Mock()
        _utils = ebExascaleUtils(mock_controller)

        netmask = _utils.mConvertFromCIDRToNetmask('24')

        self.assertEqual(netmask, '255.255.255.0')

    # Auto-generated test for mParseStorageInterfaceAddress
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebLogInfo')
    def test_mParseStorageInterfaceAddress_extracts_ip(self, mock_log):
        mock_controller = mock.Mock()
        _utils = ebExascaleUtils(mock_controller)
        iface_output = """7: stre0: <BROADCAST>\n    inet 10.10.10.5/24 brd 10.10.10.255 scope global stre0\n"""

        ip, mask = _utils.mParseStorageInterfaceAddress(iface_output)

        self.assertEqual(ip, '10.10.10.5')
        self.assertEqual(mask, '255.255.255.0')
        mock_log.assert_called()

    # Auto-generated test for mParseStorageInterfaceAddress
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebLogInfo')
    def test_mParseStorageInterfaceAddress_without_inet(self, mock_log):
        mock_controller = mock.Mock()
        _utils = ebExascaleUtils(mock_controller)
        iface_output = "7: stre0: <BROADCAST>\n   RX packets 0\n"

        ip, mask = _utils.mParseStorageInterfaceAddress(iface_output)

        self.assertEqual(ip, '')
        self.assertEqual(mask, '')
        mock_log.assert_not_called()

    def test_mGetImageBackupVault(self):
       _ebox = self.mGetClubox()
       _utils = ebExascaleUtils(_ebox)
       _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
       _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)

       _image_vault, _backup_vault = _utils.mGetImageBackupVault(_options)

       self.assertEqual(_image_vault, "imagevault")
       self.assertEqual(_backup_vault, "backupvault")

   # Auto-generated test for mFetchStorageInterconnectIps
    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock())
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mFetchStorageInterconnectIps(self, mock_connect_to_host, _mock_context):
       _ebox = self.mGetClubox()
       _utils = ebExascaleUtils(_ebox)

       _stre0_stdout = mock.Mock()
       _stre0_stdout.readlines.return_value = IFCONFIG_STRE0
       _stre1_stdout = mock.Mock()
       _stre1_stdout.readlines.return_value = IFCONFIG_STRE1

       _node = mock.Mock()
       _node.mExecuteCmd.side_effect = [
           (None, _stre0_stdout, None),
           (None, _stre1_stdout, None),
       ]
       _node.mGetCmdExitStatus.return_value = 0

       mock_connect_to_host.return_value = mock.MagicMock()
       mock_connect_to_host.return_value.__enter__.return_value = _node
       mock_connect_to_host.return_value.__exit__.return_value = None

       ip1, ip2, netmask = _utils.mFetchStorageInterconnectIps(aDom0="dom0-host")

       self.assertEqual(ip1, "100.106.0.12")
       self.assertEqual(ip2, "100.106.0.13")
       self.assertEqual(netmask, "255.255.0.0")
       self.assertEqual(_node.mExecuteCmd.call_count, 2)

   # Auto-generated test for mFetchStorageInterconnectIps
    @patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext', return_value=mock.Mock())
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    def test_mFetchStorageInterconnectIps_without_output(self, mock_connect_to_host, _mock_context):
       _ebox = self.mGetClubox()
       _utils = ebExascaleUtils(_ebox)

       _node = mock.Mock()
       _node.mExecuteCmd.side_effect = [
           (None, None, None),
           (None, None, None),
       ]
       _node.mGetCmdExitStatus.return_value = 1

       mock_connect_to_host.return_value = mock.MagicMock()
       mock_connect_to_host.return_value.__enter__.return_value = _node
       mock_connect_to_host.return_value.__exit__.return_value = None

       ip1, ip2, netmask = _utils.mFetchStorageInterconnectIps(aDom0="dom0-host")

       self.assertEqual(ip1, "")
       self.assertEqual(ip2, "")
       self.assertEqual(netmask, "")
       self.assertEqual(_node.mExecuteCmd.call_count, 2)

   # Auto-generated test for mCheckExascaleTag
    @patch('os.path.exists', return_value=True)
    @patch('defusedxml.ElementTree.iterparse')
    def test_mCheckExascaleTag_detects_exascale_with_name(self, mock_iterparse, mock_exists):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _iter = mock.MagicMock()
        _iter.__iter__.return_value = iter([(None, mock.Mock(tag='prefix}exascale'))])

        def _root_getter():
            _child = mock.Mock()
            _child.tag = 'exascale'
            return [_child]

        type(_iter).root = mock.PropertyMock(side_effect=_root_getter)

        mock_iterparse.return_value = _iter

        with patch.object(_utils, 'mGetExascaleName', return_value=('exascale_id', 'clusterName')):
            self.assertTrue(_utils.mCheckExascaleTag())
            _utils.mGetExascaleName.assert_called_once()

        mock_iterparse.assert_called_once()

   # Auto-generated test for mCheckExascaleTag
    @patch('os.path.exists', return_value=True)
    @patch('defusedxml.ElementTree.iterparse')
    def test_mCheckExascaleTag_returns_false_without_cluster_name(self, mock_iterparse, mock_exists):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _iter = mock.MagicMock()
        _iter.__iter__.return_value = iter([(None, mock.Mock(tag='prefix}exascale'))])

        def _root_getter():
            _child = mock.Mock()
            _child.tag = 'exascale'
            return [_child]

        type(_iter).root = mock.PropertyMock(side_effect=_root_getter)

        mock_iterparse.return_value = _iter

        with patch.object(_utils, 'mGetExascaleName', return_value=('exascale_id', '')):
            self.assertFalse(_utils.mCheckExascaleTag())
            _utils.mGetExascaleName.assert_called_once()

        mock_iterparse.assert_called_once()

   # Auto-generated test for mCheckExascaleTag
    @patch('os.path.exists', return_value=False)
    def test_mCheckExascaleTag_returns_false_when_patchconfig_missing(self, mock_exists):
        _ebox = self.mGetClubox()
        with patch.object(_ebox, 'mGetPatchConfig', return_value='/tmp/missing-config.xml'):
            _utils = ebExascaleUtils(_ebox)
            self.assertFalse(_utils.mCheckExascaleTag())

    # Auto-generated test for mEnableEDVProperty
    def test_mEnableEDVProperty_runs_when_image_supported(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        with patch.object(_utils, 'mIsEDVImageSupported', return_value=True) as mock_supported, \
                patch.object(_ebox, 'mGetOEDARequestsPath', return_value='/tmp/oeda'), \
                patch.object(_ebox, 'mExecuteLocal') as mock_exec:
            _utils.mEnableEDVProperty(_options)

        mock_supported.assert_called_once_with(_options)
        _properties_path = os.path.join('/tmp/oeda', 'properties', 'es.properties')
        _expected_cmd = "/bin/sed 's/^FORCEEXCCLOUD=false/FORCEEXCCLOUD=true/' -i {}".format(_properties_path)
        mock_exec.assert_called_once_with(_expected_cmd, aStdOut=DEVNULL, aStdErr=DEVNULL, aCurrDir='/tmp/oeda')

    # Auto-generated test for mEnableEDVProperty
    def test_mEnableEDVProperty_skips_when_not_supported(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        with patch.object(_utils, 'mIsEDVImageSupported', return_value=False), \
                patch.object(_ebox, 'mExecuteLocal') as mock_exec:
            _utils.mEnableEDVProperty(_options)

        mock_exec.assert_not_called()

    # Auto-generated test for mDoVaultOp
    def test_mDoVaultOp_returns_error_when_disabled(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {'vault_op': 'create', 'db_vault': {'name': 'vault1'}}

        with patch.object(_ebox, 'mCheckConfigOption', return_value='false'), \
                patch.object(_ebox, 'mSetXS') as mock_set_xs, \
                patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            _rc = _utils.mDoVaultOp(_options)

        self.assertEqual(-1, _rc)
        mock_set_xs.assert_called_once_with(False)
        mock_update_error.assert_called_once()

    def test_mDoVaultOp_params_missing(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = None

        with patch.object(_ebox, 'mCheckConfigOption', return_value='TRUE'), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            _rc = _utils.mDoVaultOp(_options)

        self.assertEqual(-1, _rc)
        mock_update_error.assert_called_once()

    def test_mDoVaultOp_get_all_vaults(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {
            'vault_op': 'get',
            'db_vaults': [],
            'system_vaults': []
        }

        with patch.object(_ebox, 'mCheckConfigOption', return_value='TRUE'), \
             patch.object(_utils, 'mGetAllVaults', return_value=0) as mock_get_all:
            _rc = _utils.mDoVaultOp(_options)

        self.assertEqual(0, _rc)
        mock_get_all.assert_called_once_with(_options)

    def test_mDoVaultOp_db_vault_create(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['vault_op'] = 'create'
        _options.jsonconf['db_vaults'] = [{'name': 'vault1'}]

        with patch.object(_ebox, 'mCheckConfigOption', return_value='TRUE'), \
             patch.object(_utils, 'mCreateDbVault', return_value=0) as mock_create:
            _rc = _utils.mDoVaultOp(_options)

        self.assertEqual(0, _rc)
        mock_create.assert_called_once_with(_options)

    def test_mDoVaultOp_db_vault_invalid_op(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['vault_op'] = 'unsupported'
        _options.jsonconf['db_vault'] = {'name': 'vault1'}

        with patch.object(_ebox, 'mCheckConfigOption', return_value='TRUE'), \
             patch.object(_utils, 'mCreateDbVault'), \
             patch.object(_utils, 'mDeleteDbVault'), \
             patch.object(_utils, 'mUpdateDbVault'), \
             patch.object(_utils, 'mGetDbVault'), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:

            _rc = _utils.mDoVaultOp(_options)

        self.assertEqual(-1, _rc)
        mock_update_error.assert_called_once()

    def test_mDoVaultOp_system_vault_delete(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['vault_op'] = 'delete'
        _options.jsonconf['system_vault'] = {'name': 'sysVault'}

        with patch.object(_ebox, 'mCheckConfigOption', return_value='TRUE'), \
             patch.object(_utils, 'mDeleteSysVault', return_value=0) as mock_delete:
            _rc = _utils.mDoVaultOp(_options)

        self.assertEqual(0, _rc)
        mock_delete.assert_called_once_with(_options)

    def test_mDoVaultOp_system_vault_invalid_op(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['vault_op'] = 'unsupported'
        _options.jsonconf['system_vault'] = {'name': 'sysVault'}

        with patch.object(_ebox, 'mCheckConfigOption', return_value='TRUE'), \
             patch.object(_utils, 'mCreateSysVault'), \
             patch.object(_utils, 'mDeleteSysVault'), \
             patch.object(_utils, 'mUpdateSysVault'), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:

            _rc = _utils.mDoVaultOp(_options)

        self.assertEqual(-1, _rc)
        mock_update_error.assert_called_once()

    # Auto-generated test for mDoXsPutOp
    def test_mDoXsPutOp_returns_error_when_operation_missing(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {}

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            _rc = _utils.mDoXsPutOp(_options)

        self.assertEqual(-1, _rc)
        mock_update_error.assert_called_once()

    # Auto-generated test for mDoXsPutOp
    def test_mDoXsPutOp_enables_auto_file_encryption(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {'operation': 'config-auto-encryption'}

        with patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext') as mock_ctx, \
                patch.object(_utils, 'mEnableAutoFileEncryption', return_value=0) as mock_enable:
            _ctx = mock.Mock()
            _ctx.mGetConfigOptions.return_value = {}
            mock_ctx.return_value = _ctx

            _rc = _utils.mDoXsPutOp(_options)

        self.assertEqual(0, _rc)
        mock_enable.assert_called_once_with(_options)

    # Auto-generated test for mDoXsPutOp
    def test_mDoXsPutOp_skips_when_flag_disabled(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {'operation': 'config-auto-encryption'}

        with patch('exabox.ovm.csstep.exascale.exascaleutils.get_gcontext') as mock_ctx, \
                patch.object(_utils, 'mEnableAutoFileEncryption') as mock_enable:
            _ctx = mock.Mock()
            _ctx.mGetConfigOptions.return_value = {'exascale_autofileencryption_disable': 'TRUE'}
            mock_ctx.return_value = _ctx

            _rc = _utils.mDoXsPutOp(_options)

        self.assertEqual(0, _rc)
        mock_enable.assert_not_called()

    # Auto-generated test for mDoXsPutOp
    def test_mDoXsPutOp_invalid_operation(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {'operation': 'unsupported'}

        with patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error:
            _rc = _utils.mDoXsPutOp(_options)

        self.assertEqual(-1, _rc)
        mock_update_error.assert_called_once()

    def test_mCreateOracleEsWallet_non_exascale_payload(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {"rack": {"name": "ClusterA"}}

        with patch.object(_ebox, 'mReturnDom0DomUPair') as mock_pairs:
            _result = _utils.mCreateOracleEsWallet(_options)

        self.assertIsNone(_result)
        mock_pairs.assert_not_called()

    def test_mCreateOracleEsWallet_no_dom_pairs(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['rack'] = {"name": "ClusterA"}

        with patch.object(_ebox, 'mGetCmd', return_value='createservice'), \
             patch.object(_ebox, 'mReturnDom0DomUPair', return_value=[]), \
             patch.object(_ebox, 'mIsOciEXACC', return_value=False):
            _result = _utils.mCreateOracleEsWallet(_options)

        self.assertEqual(_result, -1)

    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_connect_to_host')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.connect_to_host')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.exaBoxNode')
    def test_mCreateOracleEsWallet_success(self, mock_exaBoxNode, mock_cmd_check,
                                           mock_connect_to_host, mock_node_connect_to_host):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _options.jsonconf['rack'] = {"name": "ClusterA"}

        mock_cmd_check.side_effect = lambda _node, _cmd, **_kwargs: _cmd

        source_node = mock.MagicMock()
        source_node.mFileExists.return_value = True

        def _source_execute(cmd, *args, **kwargs):
            _stdout = mock.MagicMock()
            if 'lswallet' in cmd:
                _stdout.readlines.return_value = ['https://exa-root-url']
            else:
                _stdout.readlines.return_value = []
            return (None, _stdout, None)

        source_node.mExecuteCmd.side_effect = _source_execute

        other_node = mock.MagicMock()
        other_node.mExecuteCmd.side_effect = lambda cmd, *a, **k: (None, mock.MagicMock(readlines=lambda: []), None)

        source_ctx = mock.MagicMock()
        source_ctx.__enter__.return_value = source_node
        source_ctx.__exit__.return_value = None

        other_ctx = mock.MagicMock()
        other_ctx.__enter__.return_value = other_node
        other_ctx.__exit__.return_value = None

        mock_node_connect_to_host.side_effect = [source_ctx, other_ctx]

        cell_node = mock.MagicMock()
        cell_ctx = mock.MagicMock()
        cell_ctx.__enter__.return_value = cell_node
        cell_ctx.__exit__.return_value = None
        mock_connect_to_host.return_value = cell_ctx

        mock_exaBoxNode.return_value = mock.MagicMock()

        pairs = [('dom0a', 'domua'), ('dom0b', 'domub')]
        cell_map = {'cell1': object()}

        with patch.object(_ebox, 'mGetCmd', return_value='createservice'), \
             patch.object(_ebox, 'mReturnDom0DomUPair', return_value=pairs), \
             patch.object(_ebox, 'mReturnCellNodes', return_value=cell_map), \
             patch.object(_ebox, 'mIsOciEXACC', return_value=False):
            _escli_mock = mock.MagicMock()
            _utils._ebExascaleUtils__escli = _escli_mock

            _utils.mCreateOracleEsWallet(_options)

        _pubkeyfile = '/tmp/ExascaleCluster-ClusterA-oracle.pub.key'
        _escli_mock.mCreateEsWalletUser.assert_called_once_with(
            _options, 'cell1', 'oracleClusterA', _pubkeyfile, _options.jsonconf['exascale']['db_vault']['name'])

        def _cmd_from_call(_call):
            _args = _call[0]
            return _args[0] if _args else ''

        self.assertTrue(any('scp' in _cmd_from_call(call) and 'domub' in _cmd_from_call(call)
                             for call in source_node.mExecuteCmd.call_args_list))
        self.assertTrue(any('chwallet' in _cmd_from_call(call)
                             for call in other_node.mExecuteCmd.call_args_list))
        cell_node.mCopyFile.assert_called_once_with(_pubkeyfile, _pubkeyfile)
        source_node.mCopy2Local.assert_called_once_with(_pubkeyfile, _pubkeyfile)

    def test_mGetCtrlIP(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _config = mock.Mock()
        _config_list = ['cfg1']
        _exascale_cfg = mock.Mock()
        _exascale_cfg.mGetMacNetworks.return_value = ['net1', 'net2']

        _net1 = mock.Mock()
        _net1.mGetNetIpAddr.return_value = '10.0.0.10'
        _net1.mGetNetHostName.return_value = 'ctrl1'
        _net1.mGetNetDomainName.return_value = 'example.com'

        _net2 = mock.Mock()
        _net2.mGetNetIpAddr.return_value = '10.0.0.11'
        _net2.mGetNetHostName.return_value = 'ctrl2'
        _net2.mGetNetDomainName.return_value = 'example.com'

        with patch('exabox.ovm.csstep.exascale.exascaleutils.ebCluExascaleConfig') as mock_cfg_cls, \
             patch.object(_ebox, 'mGetConfig', return_value=_config), \
             patch.object(_ebox, 'mGetNetworks') as mock_networks:

            mock_cfg = mock_cfg_cls.return_value
            mock_cfg.mGetExascaleClusterConfigList.return_value = _config_list
            mock_cfg.mGetExascaleClusterConfig.return_value = _exascale_cfg

            mock_networks.return_value.mGetNetworkConfig.side_effect = [_net1, _net2]

            _ip, _ers = _utils.mGetCtrlIP()

        self.assertEqual(_ip, '10.0.0.11')
        self.assertEqual(_ers, 'ctrl2.example.com')

    def test_mParseXMLForXS_disabled_flag(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        with patch.object(_ebox, 'mCheckConfigOption', return_value='FALSE'), \
             patch.object(_ebox, 'mSetXS') as mock_set_xs:
            _utils.mParseXMLForXS()

        mock_set_xs.assert_called_once_with(False)

    def test_mParseXMLForXS_missing_vault_tag(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        with patch.object(_ebox, 'mCheckConfigOption', return_value='TRUE'), \
             patch.object(_ebox, 'mSetXS'), \
             patch.object(_ebox, 'mUpdateErrorObject') as mock_update_error, \
             patch.object(_utils, 'mCheckVaultTag', return_value=False):

            with self.assertRaises(ExacloudRuntimeError) as _ctx:
                _utils.mParseXMLForXS()

        self.assertIn('INVALID XML', str(_ctx.exception))
        mock_update_error.assert_called_once()

    def test_mParseXMLForXS_valid_vault_tag(self):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        with patch.object(_ebox, 'mCheckConfigOption', return_value='TRUE'), \
             patch.object(_utils, 'mCheckVaultTag', return_value=True), \
             patch.object(_ebox, 'mSetXS') as mock_set_xs:
            _utils.mParseXMLForXS()

        mock_set_xs.assert_not_called()

    # Auto-generated test for update_xml_tag
    @patch('defusedxml.ElementTree.parse')
    def test_update_xml_tag_success(self, mock_parse):
        _ebox = self.mGetClubox()
        _utils = ebExascaleUtils(_ebox)

        _mock_tree = mock.Mock()
        _mock_root = mock.Mock()
        _mock_elem = mock.Mock()
        _mock_elem.text = 'old'
        _mock_root.iter.return_value = [_mock_elem]
        _mock_tree.getroot.return_value = _mock_root
        mock_parse.return_value = _mock_tree

        _utils.update_xml_tag('/tmp/source.xml', 'TargetTag', 'new-value', '/tmp/output.xml')

        self.assertEqual(_mock_elem.text, 'new-value')
        _mock_tree.write.assert_called_once_with('/tmp/output.xml', encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    unittest.main() 
