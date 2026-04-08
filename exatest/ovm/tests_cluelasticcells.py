#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluelasticcells.py /main/35 2026/02/04 19:54:50 atgandhi Exp $
#
# tests_cluelasticcells.py
#
# Copyright (c) 2021, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluelasticcells.py - Unit tests for exabox/ovm/cluelasticcells.py
#
#    DESCRIPTION
#      Unit tests for exabox/ovm/cluelasticcells.py
#
#    NOTES
#      NA
#
#    MODIFIED   (MM/DD/YY)
#    rajsag      04/01/26 - er 38717477 - exacs:25.2.2.2: delete storage with
#                           exascale configure infrastructure fails at
#                           deleteexascalecelltask: "keyerror: 'operation'
#    aypaul      03/30/26 - Adding unit tests for aypaul_bug-38277507
#    atgandhi    01/23/26 - Enh 38367755 - UPDATE ADD STORAGE WORKFLOW WITH
#                           FETCH VOTING DISKS
#    aypaul      01/29/26 - Updating unit tests for selinux code refactor 
#    joysjose    01/15/26 - Codex UT enhancement
#    bhpati      11/20/25 - Bug 38593631 - Exadata Cell Flashcache Missing
#                           After Cell Addition
#    jfsaldan    09/22/25 - Bug 38402930 - EXACS PROD:
#                           DBAAS.ADDSTORAGEEXACSINFRA IS FAILING AT
#                           WAITFORRESIZEDGS - SEEMS TO BE CAUSED BY THE
#                           ENHANCEMENT - 37873380
#    nelango     09/09/25 - Bug 38399834: testcase for mCalculateDgResize
#    jfsaldan    07/17/25 - Bug 38205808 - SPARSE GRIDDISKS DOES NOT HAVE THE
#                           CORRECT SIZE AFTER ATTACH STORAGE | REGRESSION 2
#                           FROM RESIZE_DGS SPLIT
#    gparada     06/11/25 - 37895129 If DomU is down, try with others. 
#    jfsaldan    06/09/25 - Bug 37967738 - CELL REMAINED IN WRITETHROUGH
#                           FLASHCACHE MODE AFTER SCALE UP WHICH RESULTED IN
#                           PERFORMANCE ISSUES | ECRA DIDN'T CALL EXACLOUD FOR
#                           STEP PRECHECKS DURING ADD CELL FOR BOTH CLUSTERS
#    jfsaldan    05/27/25 - Enh 37873380 - EXACLOUD ADD STORAGE - DIVIDE
#                           RESIZEDG STEP INTO 3 STEPS | RESIZE_DGS -
#                           WAIT_RESIZE_DGS - RESIZE_GRIDDISKS
#    naps        04/28/25 - Bug 37800783 - UT updation.
#    prsshukl    12/04/24 - Bug 37353898 - ECS_MAIN: UNITTEST
#                           TESTS_CLUELASTICCELLS_PY IS FAILING FOR
#                           ECS_MAIN_LINUX.X64_241203.1103
#    prsshukl    11/29/24 - Bug 37240032 - AFTER CELL PATCHING SYSTEM DATE IS
#                           SHOWING AS JAN 1ST 2019
#    naps        09/10/24 - Bug 37038319 - Check for mandatory arguments in
#                           correct way.
#    jfsaldan    04/02/24 - Bug 36472454 - EXACLOUD: PARALLEL ADD CELL
#                           PRECHECKS FAIL IF SSH_CONNECTION POOL IS ENABLED
#                           AND CELLDISKS ARE MISSING
#    rajsag      04/01/24 - 36201584 elastic storage add: set rebalance power
#                           to 1 instead of default 4 if utilisation > 99% for
#                           any diskgroup
#    pbellary    11/03/23 - 35448716 - ADD NODE FAILED AT CREATE VM STEP AFTER RENAMING CLUSTER NAME ON DOMUS
#    aypaul      09/01/23 - Updating unit test cases for selinux update change.
#    siyarlag    02/07/22 - add test for remotePwdChange exacli command
#    aypaul      12/21/21 - Creation
#
import os
import io
import json
import unittest
import contextlib
from unittest import mock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.core.Error import ExacloudRuntimeError, gCellUpdateError, gDiskgroupError, gElasticError
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Node import exaBoxNode

from exabox.log.LogMgr import ebLogInfo

from exabox.ovm.cluelasticcells import ebCluElasticCellManager, MAX_RETRY, RETRY_WAIT_TIME

from unittest.mock import patch, MagicMock, PropertyMock, mock_open
import warnings
import copy
import uuid
import shutil
import re


class _DummyOptions(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __contains__(self, key):
        return hasattr(self, key)

REMOVED_CELLS_PAYLOAD = {
    "reshaped_node_subset": {
        "added_cells": [],
        "removed_cells": [ {
            "cell_node_hostname": "iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com"
        } ],
        "full_compute_to_virtualcompute_list": [
            {
                "compute_node_hostname": "iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com",
                "compute_node_virtual_hostname": "iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com"
            },
            {
                "compute_node_hostname": "iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com",
                "compute_node_virtual_hostname": "iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com"
            }
        ]
    }
}

REMOVED_CELLS_PAYLOAD_XS = {
    "exascale": {
        "cell_list": [
            "sea202225exdcl08.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
            "sea202225exdcl07.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
            "sea202225exdcl06.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
            "sea202225exdcl05.sea2xx2xx0111qf.adminsea2.oraclevcn.com"
        ],
        "ctrl_network": {
            "ip": "10.0.179.231",
            "name": "sea2d3cl3ff8b594bd46a4dae88c537967e092680clu01ers01.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
            "port": "5052"
        },
        "db_vault": {
            "gb_size": 10,
            "name": "vault1clu02"
        },
        "exascale_cluster_name": "sea2d3cl3ff8b594bd46a4dae88c537967e092680clu01ers",
        "host_nodes": [
            {
                "compute_hostname": "sea202123exdd012.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.0.0",
                "priv1": "sea202123exdd012-priv1",
                "priv2": "sea202123exdd012-priv2",
                "storage_ip1": "100.106.3.32",
                "storage_ip2": "100.106.3.33"
            },
            {
                "compute_hostname": "sea202123exdd010.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.0.0",
                "priv1": "sea202123exdd010-priv1",
                "priv2": "sea202123exdd010-priv2",
                "storage_ip1": "100.106.3.34",
                "storage_ip2": "100.106.3.35"
            },
            {
                "compute_hostname": "sea202123exdd009.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.0.0",
                "priv1": "sea202123exdd009-priv1",
                "priv2": "sea202123exdd009-priv2",
                "storage_ip1": "100.106.3.36",
                "storage_ip2": "100.106.3.37"
            }
        ],
        "storage_pool": {
            "gb_size": "27306",
            "name": "hcpool"
        },
        "storage_vlan_id": "4103"
    },
    "rebalance_power": 4,
    "reshaped_node_subset": {
        "added_cells": [],
        "removed_cells": [
            {
                "cell_node_hostname": "sea202225exdcl07.sea2xx2xx0111qf.adminsea2.oraclevcn.com"
            }
        ]
    },
    "storageType": "XS"
}


LIST_GRIDDISK_OP = """DATAC8_CD_01_scas22celadm08    active
     RECOC8_CD_00_scas22celadm08     active
"""

DG_SIZE_OP_FULL = {"id" : str(uuid.uuid1()), "DATAC1": {"totalgb": 367812.0, "usedgb": 3367.32421875}, "RECOC1": {"totalgb": 91944.0, "usedgb": 2.625}, "logfile": "/tmp/dummylogfile"}
DG_SIZE_OP = json.dumps(DG_SIZE_OP_FULL)
DG_SIZE_OP_DICT = {"DATAC1": {"totalgb": 367812.0, "usedgb": 3367.32421875}, "RECOC1": {"totalgb": 91944.0, "usedgb": 2.625}}
INIT_CLONE_DICT = {"DATAC1": {"totalgb": 36781.0, "usedgb": 336.32421875}, "RECOC1": {"totalgb": 9194.0, "usedgb": 2.625}, 'workflow_step': "SAVE_DG_SIZES"}

REBALANCE_POWER_PAYLOAD = {"rebalance_power" : 32}

CELL_USER_OP="""
     CELLDIAG
     cloud_user_myclu1-503
     cloud_user_myclu1-d13
     cloud_user_myclu2-503"""
CELL_IORM_PLAN="""
     name:                   iad103712exdcl04_IORMPLAN
     catPlan:
     dbPlan:
     objective:              auto
     status:                 active"""
IORM_OBJECTIVE_OP="""    objective:              auto"""
LIST_CELLDISK_DATAC1_OP="""
o/100.106.30.20;100.106.30.21/DATAC1_CD_00_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_01_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_02_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_03_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_04_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_05_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_06_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_07_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_08_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_09_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_10_iad103712exdcl05
o/100.106.30.20;100.106.30.21/DATAC1_CD_11_iad103712exdcl05"""

KFOD_CMD_OP="""
--------------------------------------------------------------------------------
 Disk          Size Path                                     User     Group
================================================================================
   1:        128 MB /dev/exadata_quorum/QD_DATAC1_QMA0MPEXPN16C grid     asmadmin
   2:        128 MB /dev/exadata_quorum/QD_DATAC1_QMA4MPEXPN15C grid     asmadmin
   3:        128 MB /dev/exadata_quorum/QD_RECOC1_QMA0MPEXPN16C grid     asmadmin
   4:        128 MB /dev/exadata_quorum/QD_RECOC1_QMA4MPEXPN15C grid     asmadmin
   5:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_00_iad103712exdcl04
   6:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_01_iad103712exdcl04
   7:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_02_iad103712exdcl04
   8:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_03_iad103712exdcl04
   9:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_04_iad103712exdcl04
  10:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_05_iad103712exdcl04
  11:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_06_iad103712exdcl04
  12:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_07_iad103712exdcl04
  13:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_08_iad103712exdcl04
  14:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_09_iad103712exdcl04
  15:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_10_iad103712exdcl04
  16:   10462208 MB o/100.106.30.18;100.106.30.19/DATAC1_CD_11_iad103712exdcl04
  17:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_00_iad103712exdcl04
  18:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_01_iad103712exdcl04
  19:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_02_iad103712exdcl04
  20:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_03_iad103712exdcl04
  21:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_04_iad103712exdcl04
  22:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_05_iad103712exdcl04
  23:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_06_iad103712exdcl04
  24:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_07_iad103712exdcl04
  25:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_08_iad103712exdcl04
  26:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_09_iad103712exdcl04
  27:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_10_iad103712exdcl04
  28:    2615296 MB o/100.106.30.18;100.106.30.19/RECOC1_CD_11_iad103712exdcl04
  29:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_00_iad103712exdcl05
  30:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_01_iad103712exdcl05
  31:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_02_iad103712exdcl05
  32:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_03_iad103712exdcl05
  33:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_04_iad103712exdcl05
  34:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_05_iad103712exdcl05
  35:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_06_iad103712exdcl05
  36:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_07_iad103712exdcl05
  37:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_08_iad103712exdcl05
  38:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_09_iad103712exdcl05
  39:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_10_iad103712exdcl05
  40:   10462208 MB o/100.106.30.20;100.106.30.21/DATAC1_CD_11_iad103712exdcl05
  41:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_00_iad103712exdcl05
  42:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_01_iad103712exdcl05
  43:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_02_iad103712exdcl05
  44:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_03_iad103712exdcl05
  45:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_04_iad103712exdcl05
  46:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_05_iad103712exdcl05
  47:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_06_iad103712exdcl05
  48:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_07_iad103712exdcl05
  49:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_08_iad103712exdcl05
  50:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_09_iad103712exdcl05
  51:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_10_iad103712exdcl05
  52:    2615296 MB o/100.106.30.20;100.106.30.21/RECOC1_CD_11_iad103712exdcl05
  53:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_00_iad103712exdcl06
  54:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_01_iad103712exdcl06
  55:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_02_iad103712exdcl06
  56:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_03_iad103712exdcl06
  57:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_04_iad103712exdcl06
  58:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_05_iad103712exdcl06
  59:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_06_iad103712exdcl06
  60:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_07_iad103712exdcl06
  61:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_08_iad103712exdcl06
  62:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_09_iad103712exdcl06
  63:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_10_iad103712exdcl06
  64:   10462208 MB o/100.106.30.22;100.106.30.23/DATAC1_CD_11_iad103712exdcl06
  65:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_00_iad103712exdcl06
  66:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_01_iad103712exdcl06
  67:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_02_iad103712exdcl06
  68:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_03_iad103712exdcl06
  69:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_04_iad103712exdcl06
  70:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_05_iad103712exdcl06
  71:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_06_iad103712exdcl06
  72:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_07_iad103712exdcl06
  73:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_08_iad103712exdcl06
  74:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_09_iad103712exdcl06
  75:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_10_iad103712exdcl06
  76:    2615296 MB o/100.106.30.22;100.106.30.23/RECOC1_CD_11_iad103712exdcl06"""

CHECK_CELL_DISKS = """
        name:                   CD_00_slcqab02celadm04
        status:                 normal
        name:                   CD_01_slcqab02celadm04
        status:                 normal
        name:                   CD_02_slcqab02celadm04
        status:                 normal
        name:                   CD_03_slcqab02celadm04
        status:                 normal
        name:                   CD_04_slcqab02celadm04
        status:                 normal
        name:                   CD_05_slcqab02celadm04
        status:                 normal
        name:                   CD_06_slcqab02celadm04
        status:                 normal
        name:                   CD_07_slcqab02celadm04
        status:                 normal
        name:                   CD_08_slcqab02celadm04
        status:                 normal
        name:                   CD_09_slcqab02celadm04
        status:                 normal
        name:                   CD_10_slcqab02celadm04
        status:                 normal
        name:                   CD_11_slcqab02celadm04
        status:                 normal
        name:                   FD_00_slcqab02celadm04
        status:                 normal
        name:                   FD_01_slcqab02celadm04
        status:                 normal
        name:                   FD_02_slcqab02celadm04
        status:                 normal
        name:                   FD_03_slcqab02celadm04
        status:                 normal
"""

class testOptions(object): pass

class ebTestCluElasticCells(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluElasticCells, self).setUpClass(aUseOeda = True, aGenerateDatabase = True, isElasticOperation="add_storage")
        warnings.filterwarnings("ignore")

    def _setup_execute_cell_clone_context(self, *, is_adbs=False, is_xs=False, is_kvm=False, is_zdlra=False):
        stack = contextlib.ExitStack()
        clubox = self.mGetClubox()
        storage_mock = MagicMock()
        cluster_obj = MagicMock()
        cluster_obj.mGetCluName.return_value = 'CLUSTER'
        clusters_mock = MagicMock()
        clusters_mock.mGetCluster.return_value = cluster_obj

        stack.enter_context(patch.object(clubox, 'mReturnCellNodes', return_value={'existingcell': object()}))
        stack.enter_context(patch.object(clubox, 'mCheckConfigOption', return_value=16))
        stack.enter_context(patch.object(clubox, 'mGetUUID', return_value='uuid-1'))
        stack.enter_context(patch.object(clubox, 'mGetOedaPath', return_value='/tmp/oeda'))
        stack.enter_context(patch.object(clubox, 'mGetPatchConfig', return_value='/tmp/patch.xml'))
        stack.enter_context(patch.object(clubox, 'mExecuteLocal'))
        stack.enter_context(patch.object(clubox, 'mAcquireRemoteLock'))
        stack.enter_context(patch.object(clubox, 'mReleaseRemoteLock'))
        stack.enter_context(patch.object(clubox, 'mGetStorage', return_value=storage_mock))
        stack.enter_context(patch.object(clubox, 'mGetClusters', return_value=clusters_mock))
        stack.enter_context(patch.object(clubox, 'mReturnDom0DomUPair', return_value=[('dom0', 'domu-host')]))
        stack.enter_context(patch.object(clubox, 'mUpdateInMemoryXmlConfig'))
        stack.enter_context(patch.object(clubox, 'mDeleteClusterDomUList'))
        stack.enter_context(patch.object(clubox, 'mSaveClusterDomUList'))
        stack.enter_context(patch.object(clubox, 'mSaveOEDASSHKeys'))
        stack.enter_context(patch.object(clubox, 'mIsAdbs', return_value=is_adbs))
        stack.enter_context(patch.object(clubox, 'mIsXS', return_value=is_xs))
        stack.enter_context(patch.object(clubox, 'mIsKVM', return_value=is_kvm))
        stack.enter_context(patch.object(clubox, 'IsZdlraProv', return_value=is_zdlra))
        stack.enter_context(patch.object(clubox, 'mUpdateErrorObject'))

        return stack, storage_mock, clusters_mock, clubox

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO("+ASM1"),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(KFOD_CMD_OP),None)]))
    def test_validateKfodCmd(self,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute, mock_clusterName):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.validateKfodCmd")
        _cmds = {
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\"", aStdout="/u01/app/19.0.0.0/grid", aRc=0,  aPersist=True)
                    ],
                    [
                        exaMockCommand("sh -c 'ORACLE_HOME=/u01/app/19.0.0.0/grid", aStdout=KFOD_CMD_OP, aRc=0,  aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.validateKfodCmd()

    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO("ASM1"),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(""),None),(0,io.StringIO("ASM1"),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(""),None)]))
    def test_mCellOperationCheck(self,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mCellOperationCheck")
        _cmds = {
            self.mGetRegexCell():
                [
                    [
                        exaMockCommand("cellcli -e list celldisk attributes name,size where disktype=HardDisk", aRc=0,  aPersist=True)
                    ]
                ],
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\"", aStdout="/u01/app/19.0.0.0/grid", aRc=0,  aPersist=True)
                    ],
                    [
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl status asm -node", aStdout="ASM is running on iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com", aRc=0,  aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/asmcmd lsdsk -G DATAC1", aStdout=LIST_CELLDISK_DATAC1_OP, aRc=0,  aPersist=True)
                    ],
                    [
                        exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep", aStdout="/u01/app/19.0.0.0/grid", aRc=0,  aPersist=True)
                    ],
                    [
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl status asm -node", aStdout="ASM is running on iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com", aRc=0,  aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/asmcmd lsdsk -G DATAC1", aStdout=LIST_CELLDISK_DATAC1_OP, aRc=0,  aPersist=True)
                    ],
                    [
                        exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\"", aStdout="/u01/app/19.0.0.0/grid", aRc=0,  aPersist=True)
                    ],
                    [
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl status asm -node", aStdout="ASM is running on iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com", aRc=0,  aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/asmcmd lsdsk -G DATAC1", aStdout=LIST_CELLDISK_DATAC1_OP, aRc=1,  aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        mock_exitstatus.side_effect=iter([None,None,None,None,None,None,ExacloudRuntimeError(0x0802, 0xA, "ADD_CELL")])
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mCellOperationCheck("iad103712exdcl05.iad103712exd.adminiad1.oraclevcn.com", "ADD_CELL")
        #DELETE_CELL check fail
        self.assertRaises(ExacloudRuntimeError, _elastic_cell_manager.mCellOperationCheck, "iad103712exdcl05.iad103712exd.adminiad1.oraclevcn.com", "DELETE_CELL")
        #ADD_CELL check fail
        self.assertRaises(ExacloudRuntimeError, _elastic_cell_manager.mCellOperationCheck, "iad103712exdcl05.iad103712exd.adminiad1.oraclevcn.com", "ADD_CELL")

    def test_mPreAddCellSetup(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mPreAddCellSetup")
        _cmds = {
            self.mGetRegexCell():
                [
                    [
                        exaMockCommand("cellcli -e list celldisk attributes name,size where disktype=HardDisk", aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e drop celldisk all", aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e create celldisk all", aRc=0,  aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mPreAddCellSetup(["iad103706exdcl05.iad103712exd.adminiad1.oraclevcn.com"])

    def test_mPreAddCellSetup_multiple_cells(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mPreAddCellSetup for multiple cells")
        _cmds = {
            "iad103706exdcl05":
                [
                    [
                        exaMockCommand("cellcli -e list celldisk attributes name,size where disktype=HardDisk", aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e drop celldisk all", aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e create celldisk all", aRc=0,  aPersist=True)
                    ]
                ],
            "iad103706exdcl06":
                [
                    [
                        exaMockCommand("cellcli -e list celldisk attributes name,size where disktype=HardDisk", aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e drop celldisk all", aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e create celldisk all", aRc=0,  aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mPreAddCellSetup(["iad103706exdcl05.iad103712exd.adminiad1.oraclevcn.com", "iad103706exdcl06.iad103712exd.adminiad1.oraclevcn.com"])

    def test_mSyncupCells(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mSyncupCells")
        _cmds = {
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/opt/exacloud/get_cs_data.py --dataonly", aRc=0, aStdout= "dummypassword", aPersist=True)
                    ],
                    [
                        exaMockCommand("cat /etc/oratab", aRc=0, aStdout= "/u01/app/19.0.0.0/grid", aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/olsnodes", aRc=0, aStdout= "c6-d89", aPersist=True)

                    ]
                ],
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/ping", aRc=0,  aPersist=True)
                    ]
                ],
            self.mGetRegexCell():
                [
                    [
                        exaMockCommand("cellcli -e list user", aStdout= CELL_USER_OP, aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e list iormplan detail |grep objective", aStdout= IORM_OBJECTIVE_OP, aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e list iormplan detail", aStdout= IORM_OBJECTIVE_OP, aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e alter iormplan objective='auto'", aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e alter iormplan objective='auto'", aRc=0,  aPersist=True),
                        exaMockCommand("cellcli -e alter cell remotePwdChangeAllowed=TRUE", aRc=0,  aPersist=True)
                    ],
                    [
                        exaMockCommand("cellcli -e alter iormplan objective='auto'", aRc=0,  aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _cell = ["iad103712exdcl04.iad103712exd.adminiad1.oraclevcn.com"]
        _elastic_cell_manager.mSyncupCells(_cell)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @patch("exabox.tools.oedacli.OedacliCmdMgr.mAddCell")
    @mock.patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd')
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDropPmemlogs')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSecureCellsSSH')
    @patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mCellOperationCheck")
    @patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mPostReshapeValidation")
    def test_mCloneCell_selinuxupdate(self, mock_maddcell, mock_mgetcmdexitstatus, mock_mexecutecmdlog, mock_mexecutecmd, mock_nodecmdabspathcheck, \
     mock_mdroppmemlogs, mock_msecurecellsssh, mock_mcelloperationcheck, mock_mpostreshapevalidation, mock_clusterName):

        ebLogInfo("Running unit test on cluelasticcells.mCloneCell, step: POST_ADDCELL_CHECK")
        mock_mgetcmdexitstatus.return_value = 0
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "POST_ADDCELL_CHECK"
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        with patch ('exabox.ovm.cluelasticcells.ebSelinuxControls.mGetSELinuxMode', return_value=True),\
             patch ('exabox.ovm.cluelasticcells.ebSelinuxControls.mProcessSELinuxUpdate', return_value=0),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.IsZdlraProv', return_value=True):
                _return_code = _elastic_cell_manager.mCloneCell(fullOptions)
                self.assertEqual(_return_code, 0)
        with patch ('exabox.ovm.cluelasticcells.ebSelinuxControls.mGetSELinuxMode', return_value=True),\
             patch ('exabox.ovm.cluelasticcells.ebSelinuxControls.mProcessSELinuxUpdate', side_effect=ExacloudRuntimeError(0x0121, 0xA, "Failed to process SELinux update.")),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.IsZdlraProv', return_value=True):
                _return_code = _elastic_cell_manager.mCloneCell(fullOptions)
                self.assertEqual(_return_code, 0)

    @mock.patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @mock.patch("exabox.tools.oedacli.OedacliCmdMgr.mAddCell")
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO("ASM1"),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(""),None),(0,io.StringIO(""),None),(0,io.StringIO("no rows selected\n"),None)]))
    def test_mCloneCell1(self, mock_mAddCell,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute,mock_clusterName):

        ebLogInfo("Running unit test on cluelasticcells.mCloneCell, step: WAIT_IF_REBALANCING")
        _cmds = {
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\"", aRc=0, aStdout= "ASM1", aPersist=True),
                        exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\"", aRc=0, aStdout= "/u01/app/19.0.0.0/grid", aPersist=True)
                    ],
                    [
                        exaMockCommand("su - grid -c", aRc=0, aStdout= "no rows selected\n", aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "WAIT_IF_REBALANCING"
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mCloneCell(fullOptions)

    @mock.patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @mock.patch("exabox.tools.oedacli.OedacliCmdMgr.mAddCell")
    def test_mCloneCell2(self, mock_mAddCell, mock_clusterName):
        ebLogInfo("Running unit test on cluelasticcells.mCloneCell, step: SAVE_DG_SIZES")
        _cmds = {
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi", aStdout="dummyoutput", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout=DG_SIZE_OP, aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i", aStdout="dummyoutput", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout="{\"status\" : \"Success\"}", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout=DG_SIZE_OP, aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i", aStdout="dummyoutput", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout="{\"status\" : \"Success\"}", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i", aStdout="dummyoutput", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout="{\"status\" : \"Success\"}", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i", aStdout="dummyoutput", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout="{\"status\" : \"Success\"}", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout="{\"status\" : \"Success\"}", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout=DG_SIZE_OP, aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/rm -f", aRc=0, aPersist=True),
                        exaMockCommand("/bin/ping -c 1", aRc=0, aPersist=True),
                        exaMockCommand("/bin/mkdir -p", aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexCell():
                [
                    [
                        exaMockCommand("cellcli -e list flashcache attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list flashlog attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list cell detail | grep flashCacheMode", aStdout = "  flashCacheMode:         WriteBack", aRc=0, aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "SAVE_DG_SIZES"
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mCloneCell(fullOptions)

    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mElasticAddNtpCellStatus")
    @mock.patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @mock.patch("exabox.tools.oedacli.OedacliCmdMgr.mAddCell")
    @mock.patch("exabox.ovm.clustorage.ebCluStorageConfig.mPatchClusterDiskgroup")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateInMemoryXmlConfig")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveClusterDomUList")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mDeleteClusterDomUList")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.validateKfodCmd")
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO(""),None),(0,io.StringIO(""),None),(0,io.StringIO("DUMMYOUT"),io.StringIO("DUMMYERR")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO(""),io.StringIO("")),(0,io.StringIO("+ASM1"),io.StringIO("")),(0,io.StringIO("/u01/app/19.0.0.0/grid"),io.StringIO("")),(0,io.StringIO(KFOD_CMD_OP),None)]))
    def test_mCloneCell3(self, mock_mAddCell, mock_mPatchClusterDiskgroup, mock_mUpdateInMemoryXmlConfig, mock_mUpdateErrorObject,mock_savecludomulist, mock_delcludomulist, mock_validatekfod, mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute,mock_clusterName,mock_mElasticAddNtpCellStatus):
        ebLogInfo("Running unit test on cluelasticcells.mCloneCell, step: INIT_CLONE_CELL")
        _cmds = {
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi", aStdout="dummyoutput", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout=DG_SIZE_OP, aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i", aStdout="dummyoutput", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout="{\"status\" : \"Success\"}", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout=DG_SIZE_OP, aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout=DG_SIZE_OP, aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("sh -c", aStdout="", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\"", aRc=0, aStdout= "ASM1", aPersist=True),
                        exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\"", aRc=0, aStdout= "/u01/app/19.0.0.0/grid", aPersist=True)
                    ],
                ],
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/rm", aRc=0, aPersist=True),
                        exaMockCommand("/bin/ping -c 1", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cp", aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexCell():
                [
                    [
                        exaMockCommand("cellcli -e list celldisk attributes name,size where disktype=HardDisk", aStdout = "EMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list flashcache attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list flashlog attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cellcli -e list flashcache attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list flashlog attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list cell detail | grep flashCacheMode", aStdout = "  flashCacheMode:         WriteBack", aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e", aRc=0, aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "INIT_CLONE_CELL"
        fullOptions.jsonconf['Workflow_data'] = copy.deepcopy(INIT_CLONE_DICT)
        fullOptions.jsonconf['workflow_step'] = "RESIZE_DGS"
        self.mGetClubox().mSetPatchConfig(self.mGetClubox().mGetConfigPath())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mCloneCell(fullOptions)

    @mock.patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @mock.patch("exabox.tools.oedacli.OedacliCmdMgr.mDropCell")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsLastCluster")
    @mock.patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun")
    def test_mCloneCell4(self, mock_mDropCell, mock_mIsLastCluster, mock_mRun, mock_clusterName):

        ebLogInfo("Running unit test on cluelasticcells.mCloneCell, step: UNDO_INIT_CLONE_CELL")
        _cmds = {
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i", aStdout="dummyoutput", aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/cp", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                        exaMockCommand("/bin/rm -rf", aRc=0, aPersist=True)

                    ]
                ],
            self.mGetRegexCell():
                [
                    [
                        exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME;", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e drop celldisk all"),
                    ]
                ],
            self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/usr/bin/sha256sum /opt/exacloud/dom0_lockexatest.py", aRc=0, aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "INIT_CLONE_CELL"
        fullOptions.undo = "true"
        fullOptions.jsonconf = REMOVED_CELLS_PAYLOAD
        fullOptions.jsonconf["reshaped_node_subset"]["removed_cells"][0]["cell_node_hostname"] = "iad103712exdcl05.iad103712exd.adminiad1.oraclevcn.com"
        exacloudConfDir = os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf")
        patchConfigXML = os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf/elastic_cell_exatest.xml")
        if not os.path.exists(exacloudConfDir):
            os.makedirs(exacloudConfDir)
        if os.path.exists(patchConfigXML):
            os.remove(patchConfigXML)

        if os.path.exists(os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf/elastic_cell_exatest.xml")):
            os.remove(os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf/elastic_cell_exatest.xml"))
        shutil.copy(self.mGetClubox().mGetConfigPath(), os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf/elastic_cell_exatest.xml"))
        if os.path.exists(os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf/delCell_exatest.xml")):
            os.remove(os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf/delCell_exatest.xml"))
        shutil.copy(self.mGetClubox().mGetConfigPath(), os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf/delCell_exatest.xml"))
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mCloneCell(fullOptions)

    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mElasticAddNtpCellStatus")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.IsZdlraProv")
    @mock.patch("exabox.tools.oedacli.OedacliCmdMgr.mAddCell")
    @mock.patch("exabox.ovm.clustorage.ebCluStorageConfig.mPatchClusterDiskgroup")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateInMemoryXmlConfig")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    def test_mCloneCellZDLRAEnv(self, mock_IsZdlraProv, mock_mAddCell, mock_mPatchClusterDiskgroup, mock_mUpdateInMemoryXmlConfig, mock_mUpdateErrorObject, mock_clusterName, mock_mElasticAddNtpCellStatus):
        ebLogInfo("Running unit test on cluelasticcells.mCloneCell, step: INIT_CLONE_CELL")
        _cmds = {
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /etc/oratab", aRc=0, aStdout= "/u01/app/19.0.0.0/grid", aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi", aStdout="dummyoutput", aRc=0, aPersist=True),
                        exaMockCommand("sh -c", aStdout="", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout=DG_SIZE_OP, aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i", aStdout="dummyoutput", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout="{\"status\" : \"Success\"}", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout=DG_SIZE_OP, aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat", aStdout=DG_SIZE_OP, aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("sh -c", aStdout="", aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/rm", aRc=0, aPersist=True),
                        exaMockCommand("/bin/ping -c 1", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cp", aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexCell():
                [
                    [
                        exaMockCommand("cellcli -e list celldisk attributes name,size where disktype=HardDisk", aStdout = "EMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list flashcache attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list flashlog attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list cell detail | grep flashCacheMode", aStdout = "  flashCacheMode:         WriteBack", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cellcli -e list flashcache attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list flashlog attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list cell detail | grep flashCacheMode", aStdout = "  flashCacheMode:         WriteBack", aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e", aRc=0, aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        mock_IsZdlraProv.return_value = True
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "INIT_CLONE_CELL"
        fullOptions.jsonconf['Workflow_data'] = copy.deepcopy(INIT_CLONE_DICT)
        fullOptions.jsonconf['workflow_step'] = "RESIZE_DGS"
        self.mGetClubox().mSetPatchConfig(self.mGetClubox().mGetConfigPath())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mCloneCell(fullOptions)

    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    def test_mClusterCellInfo(self, mock_mUpdateErrorObject):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mClusterCellInfo")
        fullOptions = testOptions()
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), self.mGetClubox().mGetArgsOptions(), True)
        _elastic_cell_manager.mClusterCellInfo()

        fullOptions.jsonconf = {'cell_info_param' : 'dummy_param'}
        _elastic_cell_manager.mClusterCellInfo(fullOptions)

    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager._mUpdateRequestData")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mDeleteExascaleCell")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mCloneExascaleCell")
    def test_mClusterExascaleCellUpdate(self, mock_mCloneExascaleCell, mock_mDeleteExascaleCell, mock_updateRequest):
        # Auto-generated test for mClusterExascaleCellUpdate
        ebLogInfo("")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager.mSetCellOperationData({})
        _update_conf = _elastic_cell_manager.mGetUpdateConf()
        _update_conf['operation'] = 'ADD_CELL'
        _update_conf['cells'] = [{'hostname': 'iad103716x8mcel04.us.oracle.com'}]
        fake_utils = MagicMock()
        with patch.object(self.mGetClubox(), 'mIsKVM', return_value=True), \
                patch.object(self.mGetClubox(), 'mIsExaScale', return_value=False), \
                patch.object(self.mGetClubox(), 'mReturnDom0DomUPair', return_value=[('dom0', 'domu')]), \
                patch.object(self.mGetClubox(), 'mGetExascaleUtils', return_value=fake_utils):
            mock_mCloneExascaleCell.return_value = 9
            _rc = _elastic_cell_manager.mClusterExascaleCellUpdate(fullOptions)
        self.assertEqual(_rc, 9)
        mock_mCloneExascaleCell.assert_called_once_with(fullOptions)
        fake_utils.mPatchStorageInterconnctIps.assert_called_once()
        mock_updateRequest.assert_called_once()
        self.assertEqual(_elastic_cell_manager.mGetCellOperationData()['Status'], 'Pass')

        mock_mCloneExascaleCell.reset_mock()
        mock_updateRequest.reset_mock()
        _elastic_cell_manager.mSetCellOperationData({})
        _update_conf['operation'] = 'DELETE_CELL'
        mock_mDeleteExascaleCell.return_value = 4
        with patch.object(self.mGetClubox(), 'mIsKVM', return_value=False), \
                patch.object(self.mGetClubox(), 'mIsExaScale', return_value=True):
            _rc = _elastic_cell_manager.mClusterExascaleCellUpdate(fullOptions)
        self.assertEqual(_rc, 4)
        mock_mCloneExascaleCell.assert_not_called()
        mock_mDeleteExascaleCell.assert_called_once_with(fullOptions)
        self.assertEqual(mock_updateRequest.call_count, 1)

    @mock.patch('exabox.ovm.cluelasticcells.getDiskGroupNames')
    @mock.patch('exabox.ovm.cluelasticcells.ebCluUtils')
    @mock.patch('exabox.ovm.cluelasticcells.ebGetDefaultDB')
    @mock.patch('exabox.ovm.cluelasticcells.OedacliCmdMgr')
    def test_mExecuteCellCloneAndSaveXml_config_cell_adbs(self, mock_OedacliCmdMgr, mock_ebGetDefaultDB, mock_ebCluUtils, mock_getDiskGroupNames):
        # Auto-generated test for mExecuteCellCloneAndSaveXml
        ebLogInfo("")
        mock_oeda = MagicMock()
        mock_OedacliCmdMgr.return_value = mock_oeda
        mock_ebCluUtils.return_value = MagicMock()
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db
        mock_getDiskGroupNames.return_value = ['DATAC1_NEW', 'RECOC1_NEW']

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = None
        fullOptions.jsonconf = {}

        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager._ebCluElasticCellManager__update_conf = {
            'operation': 'ADD_CELL',
            'cells': [{'hostname': 'iad1-cell1'}]
        }

        stack, storage_mock, _, clubox = self._setup_execute_cell_clone_context(is_adbs=True)

        dg_config_data = MagicMock()
        dg_config_data.mGetGridDiskPrefix.return_value = None
        dg_config_data.mGetDgName.return_value = 'DATAC1'
        dg_config_reco = MagicMock()
        dg_config_reco.mGetGridDiskPrefix.return_value = 'RECOC1'
        dg_config_reco.mGetDgName.return_value = 'RECOC1'
        storage_mock.mGetDiskGroupConfig.side_effect = lambda dg_id: {'DG1': dg_config_data, 'DG2': dg_config_reco}[dg_id]

        with stack:
            rc = _elastic_cell_manager.mExecuteCellCloneAndSaveXml('CONFIG_CELL', None, ['DG1', 'DG2'])

        self.assertEqual(rc, 0)
        mock_getDiskGroupNames.assert_called_once_with('domu-host')
        self.assertEqual(mock_oeda.mUpdateDiskGroupGriddiskPrefix.call_count, 2)
        mock_oeda.mAddCell.assert_called_once()
        mock_db.import_file.assert_called_once_with('/tmp/patch.xml')

    @mock.patch('exabox.ovm.cluelasticcells.ebCluUtils')
    @mock.patch('exabox.ovm.cluelasticcells.ebGetDefaultDB')
    @mock.patch('exabox.ovm.cluelasticcells.OedacliCmdMgr')
    def test_mExecuteCellCloneAndSaveXml_workflow_data(self, mock_OedacliCmdMgr, mock_ebGetDefaultDB, mock_ebCluUtils):
        # Auto-generated test for mExecuteCellCloneAndSaveXml
        ebLogInfo("")
        mock_oeda = MagicMock()
        mock_OedacliCmdMgr.return_value = mock_oeda
        mock_ebCluUtils.return_value = MagicMock()
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = 'STEP1'
        fullOptions.jsonconf = {
            'Workflow_data': {
                'DATAC1': {'totalgb': 300, 'usedgb': 150},
                'RECOC1': {'totalgb': 200, 'usedgb': 90},
                'SPRC1': {'totalgb': 150, 'usedgb': 30},
                'workflow_step': 'RESIZE_DGS'
            }
        }

        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager._ebCluElasticCellManager__update_conf = {
            'operation': 'ADD_CELL',
            'cells': [{'hostname': 'iad1-cell1'}]
        }

        stack, storage_mock, _, clubox = self._setup_execute_cell_clone_context(is_adbs=False, is_xs=False)

        storage_mock.mGetDiskGroupConfig.side_effect = lambda dg_id: {
            'DG1': MagicMock(mGetGridDiskPrefix=MagicMock(return_value='DATAC1'), mGetDgName=MagicMock(return_value='DATAC1')),
            'DG2': MagicMock(mGetGridDiskPrefix=MagicMock(return_value='RECOC1'), mGetDgName=MagicMock(return_value='RECOC1'))
        }[dg_id]
        storage_mock.mPatchClusterDiskgroup = MagicMock()

        with stack:
            with patch.object(_elastic_cell_manager, 'validateKfodCmd', return_value=0):
                rc = _elastic_cell_manager.mExecuteCellCloneAndSaveXml(aCludgroupsElement=['DG1', 'DG2'])

        self.assertEqual(rc, 0)
        storage_mock.mPatchClusterDiskgroup.assert_called_once()
        kwargs = storage_mock.mPatchClusterDiskgroup.call_args[1]
        self.assertTrue(kwargs['aCreateSparse'])
        self.assertFalse(kwargs['aBackupDisk'])
        self.assertEqual(kwargs['aTotalDGSize'], int((300 + 200 + 150) / 3))
        self.assertNotIn('workflow_step', fullOptions.jsonconf['Workflow_data'])

    @mock.patch('exabox.ovm.cluelasticcells.ebCluUtils')
    @mock.patch('exabox.ovm.cluelasticcells.ebGetDefaultDB')
    @mock.patch('exabox.ovm.cluelasticcells.OedacliCmdMgr')
    def test_mExecuteCellCloneAndSaveXml_kfod_failure(self, mock_OedacliCmdMgr, mock_ebGetDefaultDB, mock_ebCluUtils):
        # Auto-generated test for mExecuteCellCloneAndSaveXml
        ebLogInfo("")
        mock_oeda = MagicMock()
        mock_OedacliCmdMgr.return_value = mock_oeda
        mock_ebCluUtils.return_value = MagicMock()
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = None
        fullOptions.jsonconf = {}

        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager._ebCluElasticCellManager__update_conf = {
            'operation': 'ADD_CELL',
            'cells': [{'hostname': 'iad1-cell1'}]
        }

        stack, storage_mock, _, clubox = self._setup_execute_cell_clone_context(is_adbs=False)
        storage_mock.mGetDiskGroupConfig.side_effect = lambda dg_id: {
            'DG1': MagicMock(mGetGridDiskPrefix=MagicMock(return_value='DATAC1'), mGetDgName=MagicMock(return_value='DATAC1'))
        }['DG1']

        with stack:
            with patch.object(_elastic_cell_manager, 'validateKfodCmd', return_value=1), \
                    patch.object(_elastic_cell_manager, 'mRecordError', return_value=-99) as mock_mRecordError:
                rc = _elastic_cell_manager.mExecuteCellCloneAndSaveXml(aCludgroupsElement=['DG1'])
                mock_mRecordError.assert_called_once_with(gCellUpdateError['CellOperationFailed'], "*** kfod utility did not find Griddisks from new cell. Cloning operation failed.")
                clubox.mUpdateErrorObject.assert_called_with(gElasticError['CELL_CLONING_FAILED'], 'kfod utility did not find Griddisks from new cell. Cloning operation failed.')
                clubox.mSaveOEDASSHKeys.assert_not_called()

        self.assertEqual(rc, -99)

    @mock.patch('exabox.ovm.cluelasticcells.ebCluUtils')
    @mock.patch('exabox.ovm.cluelasticcells.ebGetDefaultDB')
    @mock.patch('exabox.ovm.cluelasticcells.OedacliCmdMgr')
    def test_mExecuteCellCloneAndSaveXml_zdlra_skips_patch(self, mock_OedacliCmdMgr, mock_ebGetDefaultDB, mock_ebCluUtils):
        # Auto-generated test for mExecuteCellCloneAndSaveXml
        ebLogInfo("")
        mock_oeda = MagicMock()
        mock_OedacliCmdMgr.return_value = mock_oeda
        mock_ebCluUtils.return_value = MagicMock()
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = 'STEP1'
        fullOptions.jsonconf = {
            'Workflow_data': {
                'DATAC1': {'totalgb': 120, 'usedgb': 60},
                'RECOC1': {'totalgb': 110, 'usedgb': 50},
                'workflow_step': 'RESIZE_DGS'
            }
        }

        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager._ebCluElasticCellManager__update_conf = {
            'operation': 'ADD_CELL',
            'cells': [{'hostname': 'iad1-cell1'}]
        }

        stack, storage_mock, _, clubox = self._setup_execute_cell_clone_context(is_zdlra=True)
        storage_mock.mPatchClusterDiskgroup = MagicMock()

        with stack:
            with patch.object(_elastic_cell_manager, 'validateKfodCmd', return_value=0):
                rc = _elastic_cell_manager.mExecuteCellCloneAndSaveXml(aCludgroupsElement=['DG1'])

        self.assertEqual(rc, 0)
        storage_mock.mPatchClusterDiskgroup.assert_not_called()
        self.assertNotIn('workflow_step', fullOptions.jsonconf['Workflow_data'])

    @mock.patch('exabox.ovm.cluelasticcells.ebCluUtils')
    @mock.patch('exabox.ovm.cluelasticcells.ebGetDefaultDB')
    @mock.patch('exabox.ovm.cluelasticcells.OedacliCmdMgr')
    def test_mExecuteCellCloneAndSaveXml_backup_disk_true(self, mock_OedacliCmdMgr, mock_ebGetDefaultDB, mock_ebCluUtils):
        # Auto-generated test for mExecuteCellCloneAndSaveXml
        ebLogInfo("")
        mock_oeda = MagicMock()
        mock_OedacliCmdMgr.return_value = mock_oeda
        mock_ebCluUtils.return_value = MagicMock()
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = 'STEP1'
        fullOptions.jsonconf = {
            'Workflow_data': {
                'DATAC1': {'totalgb': 100, 'usedgb': 40},
                'RECOC1': {'totalgb': 200, 'usedgb': 90},
                'workflow_step': 'RESIZE_DGS'
            }
        }

        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager._ebCluElasticCellManager__update_conf = {
            'operation': 'ADD_CELL',
            'cells': [{'hostname': 'iad1-cell1'}]
        }

        stack, storage_mock, _, clubox = self._setup_execute_cell_clone_context(is_xs=False)
        storage_mock.mPatchClusterDiskgroup = MagicMock()

        with stack:
            with patch.object(_elastic_cell_manager, 'validateKfodCmd', return_value=0):
                rc = _elastic_cell_manager.mExecuteCellCloneAndSaveXml(aCludgroupsElement=['DG1'])

        self.assertEqual(rc, 0)
        kwargs = storage_mock.mPatchClusterDiskgroup.call_args[1]
        self.assertFalse(kwargs['aCreateSparse'])
        self.assertTrue(kwargs['aBackupDisk'])
        self.assertEqual(kwargs['aTotalDGSize'], int((100 + 200) / 3))
        self.assertNotIn('workflow_step', fullOptions.jsonconf['Workflow_data'])

    @mock.patch('exabox.ovm.cluelasticcells.ebCluUtils')
    @mock.patch('exabox.ovm.cluelasticcells.ebGetDefaultDB')
    @mock.patch('exabox.ovm.cluelasticcells.OedacliCmdMgr')
    def test_mExecuteCellCloneAndSaveXml_create_griddisks_step(self, mock_OedacliCmdMgr, mock_ebGetDefaultDB, mock_ebCluUtils):
        # Auto-generated test for mExecuteCellCloneAndSaveXml
        ebLogInfo("")
        mock_oeda = MagicMock()
        mock_OedacliCmdMgr.return_value = mock_oeda
        mock_ebCluUtils.return_value = MagicMock()
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = None
        fullOptions.jsonconf = {}

        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager._ebCluElasticCellManager__update_conf = {
            'operation': 'ADD_CELL',
            'cells': [{'hostname': 'iad1-cell1'}]
        }

        stack, storage_mock, _, clubox = self._setup_execute_cell_clone_context()

        with stack:
            with patch.object(_elastic_cell_manager, 'validateKfodCmd', return_value=0) as mock_validate:
                rc = _elastic_cell_manager.mExecuteCellCloneAndSaveXml('CREATE_GRIDDISKS', None, ['DG1'])

        self.assertEqual(rc, 0)
        mock_oeda.mAddCell.assert_called_once()
        mock_validate.assert_not_called()

    @patch('exabox.ovm.cluelasticcells.time.sleep')
    @patch('exabox.ovm.cluelasticcells.ebLogWarn')
    @patch('exabox.ovm.cluelasticcells.ebLogInfo')
    @patch('exabox.ovm.cluelasticcells.ebCluPreChecks')
    def test_mElasticAddNtpCellStatus(self, mock_CluPreChecks, mock_LogInfo, mock_LogWarn, mock_sleep):
        # Auto-generated test for mElasticAddNtpCellStatus
        ebLogInfo("")
        class DummyLock(object):
            def __call__(self):
                return self
            def __enter__(self):
                return None
            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _update_conf = _elastic_cell_manager.mGetUpdateConf()
        _update_conf['cells'] = [{'hostname': 'iad103716x8mcel04.us.oracle.com'}]
        precheck_instance = mock_CluPreChecks.return_value
        with patch.object(self.mGetClubox(), 'mIsKVM', return_value=True), \
                patch.object(self.mGetClubox(), 'mGetRemoteLock', return_value=DummyLock()):
            with patch.object(self.mGetClubox(), 'mCheckCellsServicesUp', return_value=True) as mock_services_up:
                _elastic_cell_manager.mElasticAddNtpCellStatus()
                mock_services_up.assert_called_once_with(aRestart=False, aCellList=['iad103716x8mcel04.us.oracle.com'])
                mock_LogWarn.assert_not_called()
                self.assertEqual(precheck_instance.mAddMissingNtpDnsIps.call_count, 1)

            mock_LogWarn.reset_mock()
            mock_LogInfo.reset_mock()
            precheck_instance.mAddMissingNtpDnsIps.reset_mock()
            mock_sleep.reset_mock()
            with patch.object(self.mGetClubox(), 'mCheckCellsServicesUp', side_effect=[False, False, False]) as mock_services_up:
                _elastic_cell_manager.mElasticAddNtpCellStatus()
                self.assertEqual(mock_services_up.call_count, MAX_RETRY)
                self.assertEqual(mock_sleep.call_count, MAX_RETRY)
                mock_LogWarn.assert_called_once()
                self.assertEqual(precheck_instance.mAddMissingNtpDnsIps.call_count, 1)

    @patch('exabox.ovm.cluelasticcells.time.sleep')
    def test_mCheckCellsServicesStatus(self, mock_sleep):
        # Auto-generated test for mCheckCellsServicesStatus
        ebLogInfo("")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        cell_list = ['iad103716x8mcel04.us.oracle.com']
        with patch.object(self.mGetClubox(), 'mCheckCellsServicesUp', side_effect=[False, True]) as mock_services_up:
            self.assertTrue(_elastic_cell_manager.mCheckCellsServicesStatus(cell_list))
            self.assertEqual(mock_services_up.call_count, 2)
            mock_sleep.assert_called_once_with(RETRY_WAIT_TIME)

        mock_sleep.reset_mock()
        with patch.object(self.mGetClubox(), 'mCheckCellsServicesUp', return_value=False) as mock_services_up:
            self.assertFalse(_elastic_cell_manager.mCheckCellsServicesStatus(cell_list))
            self.assertEqual(mock_services_up.call_count, MAX_RETRY)
            self.assertEqual(mock_sleep.call_count, MAX_RETRY)

    @mock.patch('exabox.ovm.cluelasticcells.ebCluManageDiskgroup')
    def test_mFetchCellInfo_success(self, mock_ebCluManageDiskgroup):
        # Auto-generated test for mFetchCellInfo
        ebLogInfo("")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager.mSetCellOperationData({})
        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['DG1']
        clusters = MagicMock()
        clusters.mGetCluster.return_value = cluster
        dg_config = MagicMock()
        dg_config.mGetDiskGroupType.return_value = 'data'
        dg_config.mGetDgName.return_value = 'DATAC1'
        storage = MagicMock()
        storage.mGetDiskGroupConfig.return_value = dg_config
        dg_manager = MagicMock()
        dg_manager.mClusterDgrpInfo.return_value = 0
        dg_manager.mGetDiskGroupOperationData.return_value = {
            'DiskgroupInfo': {
                'DATAC1': {
                    'rebalance_status': {
                        'status': 'COMPLETED'
                    }
                }
            }
        }
        mock_ebCluManageDiskgroup.return_value = dg_manager
        with patch.object(self.mGetClubox(), 'mGetClusters', return_value=clusters), \
                patch.object(self.mGetClubox(), 'mGetStorage', return_value=storage):
            _rc = _elastic_cell_manager.mFetchCellInfo('cell_rbal_status')
        self.assertEqual(_rc, 0)
        self.assertEqual(_elastic_cell_manager.mGetCellOperationData()['rebalance_status']['DATAC1'], 'COMPLETED')
        dg_manager.mSetDiskGroupOperationData.assert_called()

    @mock.patch('exabox.ovm.cluelasticcells.ebCluManageDiskgroup')
    def test_mFetchCellInfo_failure(self, mock_ebCluManageDiskgroup):
        # Auto-generated test for mFetchCellInfo
        ebLogInfo("")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager.mSetCellOperationData({})
        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['DG1']
        clusters = MagicMock()
        clusters.mGetCluster.return_value = cluster
        dg_config = MagicMock()
        dg_config.mGetDiskGroupType.return_value = 'data'
        dg_config.mGetDgName.return_value = 'DATAC1'
        storage = MagicMock()
        storage.mGetDiskGroupConfig.return_value = dg_config
        dg_manager = MagicMock()
        dg_manager.mClusterDgrpInfo.return_value = 1
        mock_ebCluManageDiskgroup.return_value = dg_manager
        with patch.object(_elastic_cell_manager, 'mRecordError', return_value=-1) as mock_mRecordError, \
                patch.object(self.mGetClubox(), 'mGetClusters', return_value=clusters), \
                patch.object(self.mGetClubox(), 'mGetStorage', return_value=storage), \
                patch.object(self.mGetClubox(), 'mUpdateErrorObject') as mock_mUpdateErrorObject:
            _rc = _elastic_cell_manager.mFetchCellInfo('cell_rbal_status')
        self.assertEqual(_rc, -1)
        mock_mUpdateErrorObject.assert_called_once()
        mock_mRecordError.assert_called_once()

    @mock.patch('exabox.ovm.cluelasticcells.ebError')
    @mock.patch('exabox.ovm.cluelasticcells.ebLogError')
    def test_mRecordError(self, mock_LogError, mock_ebError):
        # Auto-generated test for mRecordError
        ebLogInfo("")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        _elastic_cell_manager.mSetCellOperationData({})
        mock_ebError.return_value = 'error'
        _rc = _elastic_cell_manager.mRecordError(('0x1', 'Base message'))
        _data = _elastic_cell_manager.mGetCellOperationData()
        self.assertEqual(_data['Status'], 'Fail')
        self.assertEqual(_data['Log'], 'Base message')
        self.assertEqual(_rc, 'error')
        mock_ebError.assert_called_once_with(int('0x1', 16))
        mock_LogError.assert_called_with('*** Base message\n')

        mock_ebError.reset_mock()
        mock_LogError.reset_mock()
        _elastic_cell_manager.mSetCellOperationData({})
        _rc = _elastic_cell_manager.mRecordError(('0x0', 'Base message'), ' - details')
        _data = _elastic_cell_manager.mGetCellOperationData()
        self.assertEqual(_data['Log'], 'Base message - details')
        self.assertEqual(_rc, 0)
        mock_ebError.assert_not_called()
        mock_LogError.assert_called_with('*** Base message - details\n')

    @mock.patch('exabox.ovm.cluelasticcells.ebCluManageDiskgroup')
    @mock.patch('exabox.ovm.cluelasticcells.ebLogError')
    def test_mUpdateRebalancePower(self, mock_LogError, mock_ebCluManageDiskgroup):
        # Auto-generated test for mUpdateRebalancePower
        ebLogInfo("")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.jsonconf = {'rebalance_power': 32}
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['DG1', 'DG2']
        clusters = MagicMock()
        clusters.mGetCluster.return_value = cluster
        dg_config_data = MagicMock()
        dg_config_data.mGetDiskGroupType.return_value = 'data'
        dg_config_data.mGetDgName.return_value = 'DATAC1'
        dg_config_reco = MagicMock()
        dg_config_reco.mGetDiskGroupType.return_value = 'reco'
        dg_config_reco.mGetDgName.return_value = 'RECOC1'
        storage = MagicMock()
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: {'DG1': dg_config_data, 'DG2': dg_config_reco}[dgid]
        dg_manager = MagicMock()
        dg_manager.mExecuteSetDGsRebalancePower.side_effect = [0, 1]
        mock_ebCluManageDiskgroup.return_value = dg_manager
        with patch.object(self.mGetClubox(), 'mGetClusters', return_value=clusters), \
                patch.object(self.mGetClubox(), 'mGetStorage', return_value=storage), \
                patch.object(self.mGetClubox(), 'mUpdateStatusOEDA') as mock_mUpdateStatusOEDA:
            _elastic_cell_manager.mUpdateRebalancePower(fullOptions)
            dg_manager.mExecuteSetDGsRebalancePower.assert_called_with(['DATAC1', 'RECOC1'], 32)
            self.assertEqual(mock_mUpdateStatusOEDA.call_count, 2)
            mock_LogError.assert_not_called()

            mock_mUpdateStatusOEDA.reset_mock()
            mock_LogError.reset_mock()
            _rc = _elastic_cell_manager.mUpdateRebalancePower(fullOptions)
            self.assertEqual(_rc, 1)
            mock_LogError.assert_called_once_with('*** Applying new rebalance power to all the diskgroups failed')
            self.assertEqual(mock_mUpdateStatusOEDA.call_count, 2)

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        fullOptions.jsonconf = {'cell_info_param' : 'cell_rbal_status'}
        _elastic_cell_manager.mClusterCellInfo(fullOptions)

    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mEnsureDgRebalanced")
    @mock.patch("exabox.ovm.clustorage.ebCluStorageConfig.mCheckGridDisks")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mCheckCellsServicesStatus")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mPreAddCellSetup")
    @mock.patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @mock.patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mASMRebalancePrecheck')
    def test_mClusterCellUpdate(self, mock_mUpdateErrorObject, mock_mEnsureDgRebalanced, mock_mCheckGridDisks, mock_mCheckCellsServicesStatus, mock_mPreAddCellSetup, mock_clusterName, mock_mASMRebalancePrecheck):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mClusterCellUpdate")
        fullOptions = testOptions()
        with open(os.path.join(self.mGetPath(), "inventory.json"), "r") as _f:
            _inventory = json.loads(_f.read())
        self.mGetClubox().mSetRepoInventory(_inventory)

        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _cmds = {
            self.mGetRegexCell():
                [
                    [
                        exaMockCommand("cellcli -e list griddisk", aRc=0, aStdout= LIST_GRIDDISK_OP, aPersist=True),
                        exaMockCommand("cellcli -e list celldisk attributes name,size where disktype=HardDisk", aStdout = "EMPTY", aRc=0, aPersist=True),
                        exaMockCommand("cellcli -e list celldisk detail | grep -E '(name|status)'", aStdout = CHECK_CELL_DISKS, aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                        exaMockCommand('cat /var/opt/oracle/creg/grid/grid.ini | grep "^sid" *', aStdout="+ASM1", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i", aRc=0, aPersist=True),
                        exaMockCommand("su - grid -c *", aStdout=["no rows selected"], aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat /var/opt/oracle/log/grid/diskgroupOp-exatest", aStdout= json.dumps(DG_SIZE_OP_DICT), aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("mkdir -p", aRc=0, aPersist=True),
                        exaMockCommand("chown -R oracle:oinstall", aRc=0, aPersist=True),
                        exaMockCommand("/bin/scp", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("cat /var/opt/oracle/log/grid/diskgroupOp-exatest", aStdout= json.dumps(DG_SIZE_OP_DICT), aRc=0, aPersist=True)
                    ]
                ],
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/rm -f", aRc=0, aPersist=True),
                        exaMockCommand("/bin/ping -c 1", aRc=0, aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        mock_mCheckGridDisks.return_value = 0
        _elastic_cell_manager.mClusterCellUpdate(self.mGetClubox().mGetArgsOptions())

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.jsonconf = REMOVED_CELLS_PAYLOAD
        fullOptions.steplist = "NOSTEP"
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mClusterCellUpdate(fullOptions)

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.jsonconf = REBALANCE_POWER_PAYLOAD
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _elastic_cell_manager.mClusterCellUpdate(fullOptions)

    def test_mUpdateNetworkConfig(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mUpdateNetworkConfig")
        fullOptions = testOptions()
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _add_storage_payload = self.mGetClubox().mGetArgsOptions().jsonconf
        _elastic_cell_manager.mGetUpdateConf()['cell'] = dict()
        if 'reshaped_node_subset' in list(_add_storage_payload.keys()):
            _reshape_config = _add_storage_payload['reshaped_node_subset']
            for _cell in _reshape_config['added_cells']:
                _networks = _cell['network_info']['cellnetworks']
                _elastic_cell_manager.mUpdateNetworkConfig(_networks)
        self.assertEqual(_elastic_cell_manager.mGetUpdateConf()['cell']['priv1']['fqdn'],"iad103712exdcl07-priv1.iad103712exd.adminiad1.oraclevcn.com")
        self.assertEqual(_elastic_cell_manager.mGetUpdateConf()['cell']['priv2']['ipaddr'],"100.106.30.25")
        self.assertEqual(_elastic_cell_manager.mGetUpdateConf()['cell']['admin']['gateway'],"10.0.4.129")
        self.assertEqual(_elastic_cell_manager.mGetUpdateConf()['cell']['ilom']['netmask'],"255.255.255.128")

    def test_initElasticCellConf(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.initElasticCellConf")
        fullOptions = testOptions()
        fullOptions.jsonconf = REMOVED_CELLS_PAYLOAD
        fullOptions.configpath = self.mGetClubox().mGetArgsOptions().configpath
        #Calling the constructor makes sure to call initElasticCellConf
        #Need to add the delete cell case for coverage.
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        self.assertEqual(_elastic_cell_manager.mGetUpdateConf()['operation'],"DELETE_CELL")
        self.assertEqual(_elastic_cell_manager.mGetUpdateConf()['cells'][0]['hostname'],"iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com")

    # Auto-generated test for mCloneExascaleCell
    @mock.patch("exabox.ovm.cluelasticcells.ebExascaleUtils")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestoreOEDASSHKeys")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mRecordError")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mDelCell")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateStatusOEDA")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCellDisks")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mPreAddCellSetup")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mElasticAddNtpCellStatus")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mExecuteCellCloneAndSaveXml")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    def test_mCloneExascaleCell_prechecks_handle_disk_failure(
            self,
            mock_update_error,
            mock_execute_clone,
            mock_elastic_ntp,
            mock_pre_add,
            mock_check_disks,
            mock_update_status,
            mock_del_cell,
            mock_record_error,
            mock_restore_keys,
            mock_exascale_utils,
    ):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mCloneExascaleCell for disk failure path")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "PRE_CHECKS,CONFIG_CELL"
        manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)

        mock_check_disks.return_value = False
        mock_record_error.return_value = ExacloudRuntimeError(0x07004, 0xA, "Input Error")
        mock_exascale = mock_exascale_utils.return_value
        mock_exascale.mRemoveVmMachines.return_value = None
        mock_exascale.mUpdateVLanId.return_value = None

        result = manager.mCloneExascaleCell(fullOptions)

        self.assertIsInstance(result, ExacloudRuntimeError)
        mock_restore_keys.assert_called_once()
        mock_pre_add.assert_called_once_with(['iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com'])
        mock_elastic_ntp.assert_called_once()
        mock_execute_clone.assert_not_called()
        mock_del_cell.assert_not_called()
        mock_update_status.assert_any_call(True, "PRE_CHECKS", mock.ANY, mock.ANY)
        mock_update_error.assert_called_once()
        mock_record_error.assert_called_once()

    # Auto-generated test for mCloneExascaleCell
    @mock.patch("exabox.ovm.cluelasticcells.ebExascaleUtils")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestoreOEDASSHKeys")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mDelCell")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateStatusOEDA")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCellDisks")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mPreAddCellSetup")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mElasticAddNtpCellStatus")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mExecuteCellCloneAndSaveXml")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    def test_mCloneExascaleCell_undo_calls_delete(
            self,
            mock_update_error,
            mock_execute_clone,
            mock_elastic_ntp,
            mock_pre_add,
            mock_check_disks,
            mock_update_status,
            mock_del_cell,
            mock_restore_keys,
            mock_exascale_utils,
    ):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mCloneExascaleCell for undo path")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.undo = "true"
        fullOptions.steplist = "CREATE_GRIDDISKS"
        manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)

        mock_exascale = mock_exascale_utils.return_value
        mock_exascale.mRemoveVmMachines.return_value = None
        mock_exascale.mUpdateVLanId.return_value = None
        mock_check_disks.return_value = True

        manager.mCloneExascaleCell(fullOptions)

        mock_restore_keys.assert_called_once()
        mock_del_cell.assert_called_once_with(fullOptions, "CREATE_GRIDDISKS")
        mock_execute_clone.assert_not_called()
        mock_pre_add.assert_not_called()
        mock_elastic_ntp.assert_not_called()
        mock_update_status.assert_any_call(True, "CREATE_GRIDDISKS", mock.ANY, mock.ANY)

    # Auto-generated test for mCloneExascaleCell
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mExecuteCellCloneAndSaveXml")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mElasticAddNtpCellStatus")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mPreAddCellSetup")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCellDisks")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateStatusOEDA")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPostVMCellPatching")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mDelCell")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mRecordError")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestoreOEDASSHKeys")
    @mock.patch("exabox.ovm.cluelasticcells.ebExascaleUtils")
    def test_mCloneExascaleCell_prechecks_success_executes_steps(
            self,
            mock_exascale_utils,
            mock_restore_keys,
            mock_record_error,
            mock_del_cell,
            mock_update_error,
            mock_post_vm_patch,
            mock_update_status,
            mock_check_disks,
            mock_pre_add,
            mock_elastic_ntp,
            mock_execute_clone,
    ):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mCloneExascaleCell for successful prechecks")

        with mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsFedramp", return_value=False), \
                mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM", return_value=False), \
                mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale", return_value=False), \
                mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExabm", return_value=False), \
                mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption", return_value=False):
            fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
            manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
            expected_cells = [cell['hostname'] for cell in manager.mGetUpdateConf()['cells']]

            mock_check_disks.return_value = True
            mock_execute_clone.return_value = 0
            mock_exascale = mock_exascale_utils.return_value
            mock_exascale.mRemoveVmMachines.return_value = None
            mock_exascale.mUpdateVLanId.return_value = None

            result = manager.mCloneExascaleCell(fullOptions)

            self.assertEqual(result, 0)
            mock_restore_keys.assert_called_once_with(fullOptions)
            mock_pre_add.assert_called_once_with(expected_cells)
            mock_elastic_ntp.assert_called()
            self.assertEqual(mock_elastic_ntp.call_count, 2)
            mock_check_disks.assert_called_once_with(expected_cells, 'celldisk')
            mock_execute_clone.assert_has_calls([mock.call('CONFIG_CELL'), mock.call('CREATE_GRIDDISKS')])
            mock_post_vm_patch.assert_called_once_with(fullOptions, expected_cells)
            mock_del_cell.assert_not_called()
            mock_record_error.assert_not_called()
            mock_update_error.assert_not_called()
            mock_update_status.assert_any_call(True, "PRE_CHECKS", mock.ANY, mock.ANY)
            mock_update_status.assert_any_call(True, "CONFIG_CELL", mock.ANY, mock.ANY)
            mock_update_status.assert_any_call(True, "CREATE_GRIDDISKS", mock.ANY, mock.ANY)

    # Auto-generated test for mCloneExascaleCell
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mExecuteCellCloneAndSaveXml")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mElasticAddNtpCellStatus")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mPreAddCellSetup")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mDelCell")
    @mock.patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mRecordError")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestoreOEDASSHKeys")
    @mock.patch("exabox.ovm.cluelasticcells.ebExascaleUtils")
    @mock.patch("exabox.ovm.cluelasticcells.connect_to_host")
    @mock.patch("exabox.ovm.cluelasticcells.get_gcontext")
    @mock.patch("exabox.ovm.cluelasticcells.csUtil")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRemoteLock")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateStatusOEDA")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption")
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsFedramp")
    def test_mCloneExascaleCell_post_addcell_fedramp_whitelists_cidr(
            self,
            mock_is_fedramp,
            mock_check_config_option,
            mock_update_status,
            mock_get_remote_lock,
            mock_cs_util,
            mock_get_gcontext,
            mock_connect_to_host,
            mock_exascale_utils,
            mock_restore_keys,
            mock_record_error,
            mock_del_cell,
            mock_update_error,
            mock_pre_add,
            mock_elastic_ntp,
            mock_execute_clone,
    ):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mCloneExascaleCell for FedRAMP whitelist branch")

        with mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM", return_value=False), \
                mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale", return_value=False), \
                mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExabm", return_value=False):
            fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
            fullOptions.steplist = "POST_ADDCELL_CHECK"
            manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
            expected_cells = [cell['hostname'] for cell in manager.mGetUpdateConf()['cells']]

            mock_is_fedramp.return_value = True

            def _check_config(key, value):
                if key == 'whitelist_admin_network_cidr':
                    return True
                return False

            mock_check_config_option.side_effect = _check_config

            lock_cm = mock.MagicMock()
            lock_cm.__enter__.return_value = None
            lock_cm.__exit__.return_value = False
            lock_factory = mock.MagicMock(return_value=lock_cm)
            mock_get_remote_lock.return_value = lock_factory

            mock_node = mock.MagicMock()
            connect_cm = mock.MagicMock()
            connect_cm.__enter__.return_value = mock_node
            connect_cm.__exit__.return_value = False
            mock_connect_to_host.return_value = connect_cm
            mock_get_gcontext.return_value = object()

            mock_execute_clone.return_value = 0
            mock_exascale = mock_exascale_utils.return_value
            mock_exascale.mRemoveVmMachines.return_value = None
            mock_exascale.mUpdateVLanId.return_value = None

            manager.mCloneExascaleCell(fullOptions)

            mock_restore_keys.assert_called_once_with(fullOptions)
            mock_update_status.assert_called_once_with(True, "POST_ADDCELL_CHECK", mock.ANY, mock.ANY)
            mock_pre_add.assert_not_called()
            mock_elastic_ntp.assert_not_called()
            mock_execute_clone.assert_not_called()
            mock_del_cell.assert_not_called()
        mock_record_error.assert_not_called()
        lock_factory.assert_called_once()
        self.assertEqual(mock_connect_to_host.call_count, len(expected_cells))
        for call, hostname in zip(mock_connect_to_host.call_args_list, expected_cells):
            args, kwargs = call
            self.assertEqual(args[0], hostname)
        mock_cs_instance = mock_cs_util.return_value
        self.assertEqual(mock_cs_instance.mWhitelistCidr.call_count, len(expected_cells))
        for call in mock_cs_instance.mWhitelistCidr.call_args_list:
            args, kwargs = call
            self.assertEqual(args[0], self.mGetClubox())
            self.assertIs(args[1], mock_node)
        mock_update_status.assert_called_once_with(True, "POST_ADDCELL_CHECK", ["POST_ADDCELL_CHECK"], mock.ANY)
        mock_update_error.assert_not_called()

    # Auto-generated test for initElasticCellConf
    def test_initElasticCellConf_prefers_actual_rack_num(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.initElasticCellConf for rack_num preference")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['rack_info']['rack_num'] = "rack-actual"
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['rack_info']['uheight'] = "rack-uheight"
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        self.assertEqual(_elastic_cell_manager.mGetUpdateConf()['operation'], "ADD_CELL")
        self.assertEqual(
            _elastic_cell_manager.mGetUpdateConf()['cells'][0]['rack_num'],
            "rack-actual"
        )

    # Auto-generated test for initElasticCellConf
    def test_initElasticCellConf_falls_back_to_uheight(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.initElasticCellConf for rack_num fallback")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        rack_info = fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['rack_info']
        rack_info.pop('rack_num', None)
        rack_info['uheight'] = "rack-uheight"
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        self.assertEqual(_elastic_cell_manager.mGetUpdateConf()['operation'], "ADD_CELL")
        self.assertEqual(
            _elastic_cell_manager.mGetUpdateConf()['cells'][0]['rack_num'],
            "rack-uheight"
        )

    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    def test_mValidateReshapePayload(self, mock_mUpdateErrorObject):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mValidateReshapePayload")
        fullOptions = testOptions()
        fullOptions.configpath = self.mGetClubox().mGetArgsOptions().configpath
        fullOptions.jsonconf = None
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions, True)
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = {"rebalance_power" : 32}
        self.assertEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)
        fullOptions.jsonconf = {"rebalance_power" : 65}
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)
        fullOptions.jsonconf = {"rebalance_power" : "NA"}
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['removed_cells'] = [{"cell_node_hostname": "iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com"}]
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = REMOVED_CELLS_PAYLOAD
        fullOptions.jsonconf['reshaped_node_subset']['removed_cells'][0]['cell_node_hostname'] = None
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['cell_hostname'] = None
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['network_info'] = None
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['network_info']['cellnetworks'][0]['admin'] = None
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['network_info']['cellnetworks'][0]['admin'][0]['fqdn'] = None
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['network_info']['cellnetworks'][1]['private'].pop(0)
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['network_info']['cellnetworks'][1]['private'][0]['ipaddr'] = None
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['network_info']['cellnetworks'][2]['ilom'][0]['fqdn'] = None
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['rack_info']= {}
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        del fullOptions.jsonconf['reshaped_node_subset']['full_compute_to_virtualcompute_list']
        self.assertNotEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

        fullOptions.jsonconf = copy.deepcopy(self.mGetClubox().mGetArgsOptions().jsonconf)
        fullOptions.jsonconf['reshaped_node_subset']['added_cells'][0]['rack_info'].pop('rack_num', None)
        self.assertEqual(_elastic_cell_manager.mValidateReshapePayload(fullOptions), 0)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateClusterName')
    @patch("exabox.tools.oedacli.OedacliCmdMgr.mAddCell")
    @mock.patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd')
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDropPmemlogs')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSecureCellsSSH')
    @patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mCellOperationCheck")
    @patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mPostReshapeValidation")
    def test_mCloneCell_Zdlra_skip_steps(self, mock_maddcell, mock_mgetcmdexitstatus, mock_mexecutecmdlog, mock_mexecutecmd, mock_nodecmdabspathcheck, \
                                         mock_mdroppmemlogs, mock_msecurecellsssh, mock_mcelloperationcheck, mock_mpostreshapevalidation, mock_clusterName):

        ebLogInfo("Running unit test on cluelasticcells.mCloneCell, step: POST_ADDCELL_CHECK")
        mock_mgetcmdexitstatus.return_value = 0
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "RESIZE_DGS"
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.IsZdlraProv', return_value=True):
            _elastic_cell_manager.mCloneCell(fullOptions)
            _elastic_cell_manager.mDeleteCell(fullOptions)


    def test_mValidateAllDiskGroupsSizes_missing_payload(self):
        """
        Validate mValidateAllDiskGroupsSizes
        """
        ebLogInfo("Running unit test on cluelasticcells.mCloneCell, method mValidateReshapePayload")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "WAIT_RESIZE_DGS"
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)

        self.assertNotEqual(0, _elastic_cell_manager.mValidateAllDiskGroupsSizes("WAIT_RESIZE_DGS"))

    @patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mCalculateDgResize.mValidateHandler")
    @patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mCalculateDgResize")
    @patch("exabox.ovm.cluelasticcells.ebCluElasticCellManager.mFetchAndSaveDGSizes")
    def test_mValidateAllDiskGroupsSizes(self, mFetchAndSaveDGSizesMock,
                                         mCalculateDgResizeMock, mValidateHandlerMock):
        """
        Validate mValidateAllDiskGroupsSizes
        """
        ebLogInfo("Running unit test on cluelasticcells.mCloneCell, method mValidateReshapePayload")
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "WAIT_RESIZE_DGS"
        fullOptions.jsonconf['Workflow_data'] = copy.deepcopy(INIT_CLONE_DICT)
        fullOptions.jsonconf['workflow_step'] = "RESIZE_DGS"
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)

        self.assertNotEqual(0, _elastic_cell_manager.mValidateAllDiskGroupsSizes("WAIT_RESIZE_DGS"))

    def test_getConnectableDomU(self):
        """
        Validate getConnectableDomU
        """
        ebLogInfo("Running unit test on cluelasticcells.getConnectableDomU")

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "DUMMY_STEP"
        fullOptions.jsonconf['Workflow_data'] = {"dummy":"test"}
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _domain = ".clientsubnet.devx8melastic.oraclevcn.com"

        def mock_mIsConnectable(aHost, aTimeout = None, aKeyOnly=None):
            if aHost == f"iad103716x8mcompexpn16c{_domain}":
                return True
            return False

        _expected_val = f"iad103716x8mcompexpn16c{_domain}"
        with patch('exabox.core.Node.exaBoxNode.mIsConnectable', \
                   side_effect=mock_mIsConnectable):
            self.assertEqual(_expected_val,
                             _elastic_cell_manager.getConnectableDomU())

    def test_getConnectableDomU_error(self):
        """
        Validate getConnectableDomU. Check for error.
        """
        ebLogInfo("Running unit test on cluelasticcells.getConnectableDomU")

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "DUMMY_STEP"
        fullOptions.jsonconf['Workflow_data'] = {"dummy":"test"}
        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        _domain = ".clientsubnet.devx8melastic.oraclevcn.com"

        _expected_val = f"iad103716x8mcompexpn16c{_domain}"
        with patch('exabox.core.Node.exaBoxNode.mIsConnectable', return_value=0):
            try:
                _elastic_cell_manager.getConnectableDomU()
            except ExacloudRuntimeError as exc:
                self.assertEqual(exc.mGetErrorCode(),0x0802)
                self.assertEqual(exc.mGetErrorMsg(),
                                 "EXACLOUD : Zero domUs connectable!")

    @patch('exabox.ovm.cluelasticcells.ebCluManageDiskgroup.mGetOutJson')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetDbaasObj')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mClusterDgrpInfo2')
    @patch('exabox.ovm.cluelasticcells.ebCluElasticCellManager.mFetchAndSaveDGSizes')
    @patch('exabox.ovm.cluelasticcells.ebCluElasticCellManager.mCalculateDgResize')
    def test_mExecuteResizeGridDisks(self, aMockCalculateDGResize,
                                     aMockFetchandSaveDGSize, aMockCluDGInfo, aMockGetCluDbaas, aMockGetJson):
        """
        Validate mExecuteResizeGridDisks. Check for error.
        """
        ebLogInfo("Running unit test on cluelasticcells.getConnectableDomU")

        aMockFetchandSaveDGSize.return_value = 0
        aMockCluDGInfo.return_value = 0
        _cmds = {
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("", aStdout="/u01/app/19.0.0.0/grid", aRc=0,  aPersist=True)
                    ],
                    [
                    ],
                    [],
                    [],
                    [],
                    []
                ],
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand(f"rm"),
                        exaMockCommand(f"ping -c 1 iad103716exddu1501.iad103716exd.adminiad1.oraclevcn.com")
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "RESIZE_GRIDDISKS"
        fullOptions.jsonconf['Workflow_step'] = "RESIZE_GRIDDISKS"
        fullOptions.jsonconf['Workflow_data'] = {
            "DATAC2": {
                "totalgb": 46080,
                "usedgb": 1684.5390625
            },
            "RECOC2": {
                "totalgb": 15358.125,
                "usedgb": 2.4609375
            },
            "SPRC2": {
                "totalgb": 15358.125,
                "usedgb": 8.484375
            },
            "workflow_step": "RESIZE_DGS"
        }

        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)


        _sizes_dict = fullOptions.jsonconf.get("Workflow_data")
        _elastic_cell_manager.mExecuteResizeGridDisks(_sizes_dict, ["RESIZE_GRIDDISKS"])

    @patch('exabox.ovm.cluelasticcells.ebCluManageDiskgroup.mGetOutJson')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetDbaasObj')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mClusterDgrpInfo2')
    @patch('exabox.ovm.cluelasticcells.ebCluElasticCellManager.mFetchAndSaveDGSizes')
    @patch('exabox.ovm.cluelasticcells.ebCluElasticCellManager.mCalculateDgResize')
    def test_mExecuteResizeGridDisks_GB_nonINT(self, aMockCalculateDGResize,
                                               aMockFetchandSaveDGSize, aMockCluDGInfo, aMockGetCluDbaas, aMockGetJson):
        """
        Validate mExecuteResizeGridDisks. Check for error.
        """
        ebLogInfo("Running unit test on cluelasticcells.getConnectableDomU")

        aMockFetchandSaveDGSize.return_value = 0
        aMockCluDGInfo.return_value = 0
        _cmds = {
            self.mGetRegexVm():
                [
                    [
                        exaMockCommand("", aStdout="/u01/app/19.0.0.0/grid", aRc=0,  aPersist=True)
                    ],
                    [
                    ],
                    [],
                    [],
                    [],
                    []
                ],
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand(f"rm"),
                        exaMockCommand(f"ping -c 1 iad103716exddu1501.iad103716exd.adminiad1.oraclevcn.com")
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.steplist = "RESIZE_GRIDDISKS"
        fullOptions.jsonconf['Workflow_step'] = "RESIZE_GRIDDISKS"
        fullOptions.jsonconf['Workflow_data'] = {
            "DATAC2": {
                "totalgb": 46080.2,
                "usedgb": 1684.5390625
            },
            "RECOC2": {
                "totalgb": 15358.125,
                "usedgb": 2.4609375
            },
            "SPRC2": {
                "totalgb": 15358.125,
                "usedgb": 8.484375
            },
            "workflow_step": "RESIZE_DGS"
        }

        _elastic_cell_manager = ebCluElasticCellManager(self.mGetClubox(), fullOptions)


        _sizes_dict = fullOptions.jsonconf.get("Workflow_data")
        _elastic_cell_manager.mExecuteResizeGridDisks(_sizes_dict, ["RESIZE_GRIDDISKS"])

    @patch("exabox.tools.oedacli.ebOedacli")
    @patch("exabox.tools.oedacli.OedacliCmdMgr")
    @patch("exabox.ovm.cluelasticcells.ebCluDbaas")
    @patch("exabox.ovm.cluelasticcells.ebCluManageDiskgroup")
    @patch("exabox.log.LogMgr.ebLogInfo")
    def test_mCalculateDgResize_usage_under_threshold(self,mock_log_info,mock_clu_dg_mgr,mock_dbaas,mock_oedacli_mgr,mock_ebOedacli):
        _ebox = copy.deepcopy(self.mGetClubox())
        fullOptions = copy.deepcopy(_ebox.mGetArgsOptions())
        fullOptions.steplist = "WAIT_RESIZE_DGS"
        fullOptions.jsonconf['Workflow_data'] = copy.deepcopy(INIT_CLONE_DICT)
        fullOptions.jsonconf['workflow_step'] = "RESIZE_DGS"
        fullOptions.jsonconf['Workflow_data']['reshape_config'] = {'added_cells': [],'removed_cells': []}
        mock_constants = mock.Mock()
        mock_constants._data_dg_type_str = "data"
        mock_constants._reco_dg_type_str = "reco"
        mock_constants._sparse_dg_type_str = "sparse"
        mock_clu_dg_mgr.return_value.mGetConstantsObj.return_value = mock_constants
        dg_data = mock.Mock()
        dg_data.mGetDiskGroupType.return_value = "data"
        dg_data.mGetDgName.return_value = "DATAC1"
        storage_obj = _ebox.mGetStorage()
        def _dg_config_lookup(dgid):
            return dg_data
        storage_obj.mGetDiskGroupConfig = _dg_config_lookup
        _ebox.mReturnCellNodes = mock.Mock(
            return_value={
                "cell1.us.oracle.com": {"status": "up"},
                "cell2.us.oracle.com": {"status": "up"},
                "cell3.us.oracle.com": {"status": "up"}
            }
        )
        elastic_manager = ebCluElasticCellManager(_ebox, fullOptions)
        cludgroups = ["DATAC1"]
        dg_sizes_before = {"DATAC1": {"totalgb": 1000.0, "usedgb": 100.0}}
        dg_sizes_after = {"DATAC1": {"totalgb": 1100.0, "usedgb": 100.0}}
        elastic_manager.mCalculateDgResize(cludgroups, dg_sizes_before, dg_sizes_after)

    # Auto-generated test for mDeleteExascaleCell
    @mock.patch("exabox.ovm.cluelasticcells.ebCluCmdCheckOptions", return_value=False)
    @mock.patch("exabox.ovm.cluelasticcells.exaBoxClusterConfig")
    def test_mDeleteExascaleCell_runs_steps(self, mock_exa_config, mock_cmd_check):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mDeleteExascaleCell step flow")

        options = _DummyOptions(
            steplist="CREATE_GRIDDISKS,DELETE_CELL_CHECK",
            undo=None,
            jsonconf={
                "reshaped_node_subset": {
                    "removed_cells": [{"cell_node_hostname": "cell1.example.com"}]
                }
            }
        )
        update_conf = {
            'operation': 'DELETE_CELL',
            'cells': [{'hostname': 'cell1.example.com'}]
        }
        ebox = mock.MagicMock()
        clusters = mock.MagicMock()
        cluster_obj = mock.MagicMock()
        cluster_obj.mGetCluName.return_value = "cluster-name"
        clusters.mGetCluster.return_value = cluster_obj
        ebox.mGetClusters.return_value = clusters
        ebox.mGetOedaPath.return_value = "/tmp/oeda"
        ebox.mGetPatchConfig.return_value = "/tmp/patch.cfg"
        ebox.mGetUUID.return_value = "uuid"
        ebox.mGetCmd.return_value = "invalid_cmd"
        ebox.mGetCtx.return_value = mock.MagicMock()
        ebox.mCheckConfigOption.return_value = 4
        ebox.mExecuteLocal = mock.MagicMock()
        ebox.mRestoreOEDASSHKeys = mock.MagicMock()
        ebox.mIsKVM.return_value = False
        ebox.mSetConfig = mock.MagicMock()
        ebox.mAcquireRemoteLock = mock.MagicMock()

        manager = object.__new__(ebCluElasticCellManager)
        manager._ebCluElasticCellManager__cellOperationData = {}
        manager.mGetEbox = mock.MagicMock(return_value=ebox)
        manager.mGetUpdateConf = mock.MagicMock(return_value=update_conf)
        mock_oeda_cli = mock.MagicMock()
        manager.mGetOedaCliMgr = mock.MagicMock(return_value=mock_oeda_cli)
        manager.mGetOedaXmlPath = mock.MagicMock(return_value="/tmp/exacloud.conf")
        mock_exa_config.return_value = mock.MagicMock()

        result = manager.mDeleteExascaleCell(options)

        self.assertEqual(result, 0)
        mock_cmd_check.assert_called_once_with("invalid_cmd", ['nooeda'])
        ebox.mRestoreOEDASSHKeys.assert_called_once_with(options)
        expected_config_xml = "/tmp/oeda/exacloud.conf/elastic_cell_uuid.xml"
        expected_oeda_xml = "/tmp/exacloud.conf/delCell_uuid.xml"
        ebox.mExecuteLocal.assert_any_call(f"/bin/cp /tmp/patch.cfg {expected_config_xml}")
        ebox.mExecuteLocal.assert_any_call(f"/bin/cp /tmp/patch.cfg {expected_oeda_xml}")
        mock_exa_config.assert_called_once_with(ebox.mGetCtx(), expected_config_xml)
        mock_oeda_cli.mDropCell.assert_called_once()
        drop_args, drop_kwargs = mock_oeda_cli.mDropCell.call_args
        self.assertEqual(drop_args[0], expected_config_xml)
        self.assertEqual(drop_args[1], expected_oeda_xml)
        self.assertEqual(drop_args[2], ["cell1.example.com"])
        self.assertTrue(drop_kwargs.get("aUserData"))

    # Auto-generated test for mDeleteExascaleCell
    @mock.patch("exabox.ovm.cluelasticcells.ebCluCmdCheckOptions", return_value=True)
    @mock.patch("exabox.ovm.cluelasticcells.exaBoxClusterConfig")
    def test_mDeleteExascaleCell_skips_key_restore_when_nooeda(self, mock_exa_config, mock_cmd_check):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mDeleteExascaleCell without key restoration")

        options = _DummyOptions(
            steplist="CREATE_GRIDDISKS",
            jsonconf={
                "reshaped_node_subset": {
                    "removed_cells": [{"cell_node_hostname": "cell1.example.com"}]
                }
            }
        )
        update_conf = {
            'operation': 'DELETE_CELL',
            'cells': [{'hostname': 'cell1.example.com'}]
        }
        ebox = mock.MagicMock()
        clusters = mock.MagicMock()
        cluster_obj = mock.MagicMock()
        cluster_obj.mGetCluName.return_value = "cluster-name"
        clusters.mGetCluster.return_value = cluster_obj
        ebox.mGetClusters.return_value = clusters
        ebox.mGetOedaPath.return_value = "/tmp/oeda"
        ebox.mGetPatchConfig.return_value = "/tmp/patch.cfg"
        ebox.mGetUUID.return_value = "uuid"
        ebox.mGetCmd.return_value = "mycmd --nooeda"
        ebox.mGetCtx.return_value = mock.MagicMock()
        ebox.mCheckConfigOption.return_value = 2
        ebox.mExecuteLocal = mock.MagicMock()
        ebox.mRestoreOEDASSHKeys = mock.MagicMock()
        ebox.mIsKVM.return_value = True
        ebox.mSetConfig = mock.MagicMock()
        ebox.mAcquireRemoteLock = mock.MagicMock()

        manager = object.__new__(ebCluElasticCellManager)
        manager._ebCluElasticCellManager__cellOperationData = {}
        manager.mGetEbox = mock.MagicMock(return_value=ebox)
        manager.mGetUpdateConf = mock.MagicMock(return_value=update_conf)
        mock_oeda_cli = mock.MagicMock()
        manager.mGetOedaCliMgr = mock.MagicMock(return_value=mock_oeda_cli)
        manager.mGetOedaXmlPath = mock.MagicMock(return_value="/tmp/exacloud.conf")
        mock_exa_config.return_value = mock.MagicMock()

        result = manager.mDeleteExascaleCell(options)

        self.assertEqual(result, 0)
        mock_cmd_check.assert_called_once_with("mycmd --nooeda", ['nooeda'])
        ebox.mRestoreOEDASSHKeys.assert_not_called()
        mock_oeda_cli.mDropCell.assert_called_once()

    # Auto-generated test for mResizeDGs
    def test_mResizeDGs_successful_flow(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mResizeDGs for success path")

        options = _DummyOptions(
            steplist="RESIZE_DGS",
            jsonconf={'Workflow_data': {
                'DATAC1': {'totalgb': 300, 'usedgb': 120},
                'RECOC1': {'totalgb': 150, 'usedgb': 60},
                'workflow_step': 'RESIZE_DGS'
            }}
        )
        ebox = mock.MagicMock()
        cluster_obj = mock.MagicMock()
        cluster_obj.mGetCluDiskGroups.return_value = ['DG1']
        clusters = mock.MagicMock()
        clusters.mGetCluster.return_value = cluster_obj
        ebox.mGetClusters.return_value = clusters
        storage = mock.MagicMock()
        dg_config = mock.MagicMock()
        dg_config.mGetDiskGroupType.side_effect = ['data', 'reco']
        dg_config.mGetDgName.side_effect = ['DATAC1', 'RECOC1']
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: dg_config
        ebox.mGetStorage.return_value = storage
        ebox.IsZdlraProv.return_value = False
        ebox.mIsOciEXACC.return_value = False
        ebox.mReturnCellNodes.return_value = {'cell1': {}, 'cell2': {}, 'cell3': {}}
        ebox.mGetStorage().mPatchClusterDiskgroup.return_value = None
        clu_utils = mock.MagicMock()
        clu_utils.mStepSpecificDetails.side_effect = lambda *args, **kwargs: "details"

        manager = object.__new__(ebCluElasticCellManager)
        manager._ebCluElasticCellManager__eboxobj = ebox
        manager._ebCluElasticCellManager__update_conf = {}
        manager._ebCluElasticCellManager__options = options
        manager._ebCluElasticCellManager__cellOperationData = {}
        manager._ebCluElasticCellManager__clu_utils = clu_utils
        manager.mFetchAndSaveDGSizes = mock.Mock(return_value=0)
        manager.mCalculateDgResize = mock.Mock()
        manager.mExecuteResizeDGs = mock.Mock(return_value=0)
        manager.mRecordError = mock.Mock()

        result = manager.mResizeDGs(options, ["RESIZE_DGS"], None)

        self.assertIsNone(result)
        manager.mFetchAndSaveDGSizes.assert_called_once()
        manager.mCalculateDgResize.assert_called_once()
        manager.mExecuteResizeDGs.assert_called_once()
        self.assertNotIn('workflow_step', options.jsonconf['Workflow_data'])
        storage.mPatchClusterDiskgroup.assert_called_once()

    # Auto-generated test for mResizeDGs
    def test_mResizeDGs_failure_records_error(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mResizeDGs failure branch")

        options = _DummyOptions(steplist=None, jsonconf={})
        ebox = mock.MagicMock()
        cluster_obj = mock.MagicMock()
        cluster_obj.mGetCluDiskGroups.return_value = ['DG1']
        clusters = mock.MagicMock()
        clusters.mGetCluster.return_value = cluster_obj
        ebox.mGetClusters.return_value = clusters
        storage = mock.MagicMock()
        dg_config = mock.MagicMock()
        dg_config.mGetDiskGroupType.return_value = 'data'
        dg_config.mGetDgName.return_value = 'DG_ONE'
        storage.mGetDiskGroupConfig.return_value = dg_config
        ebox.mGetStorage.return_value = storage
        ebox.IsZdlraProv.return_value = True
        ebox.mReturnCellNodes.return_value = {'cell1': {}, 'cell2': {}}

        manager = object.__new__(ebCluElasticCellManager)
        manager._ebCluElasticCellManager__eboxobj = ebox
        manager._ebCluElasticCellManager__update_conf = {}
        manager._ebCluElasticCellManager__options = options
        manager._ebCluElasticCellManager__cellOperationData = {}
        manager._ebCluElasticCellManager__clu_utils = mock.MagicMock()
        manager.mFetchAndSaveDGSizes = mock.Mock(return_value=0)
        manager.mCalculateDgResize = mock.Mock()
        manager.mExecuteResizeDGs = mock.Mock(return_value=1)
        manager.mRecordError = mock.Mock(return_value="error")

        dg_size_dict = {'DG_ONE': {'totalgb': 200, 'usedgb': 80}}
        result = manager.mResizeDGs(options, ["RESIZE_DGS"], dg_size_dict)

        self.assertEqual(result, "error")
        manager.mRecordError.assert_called_once_with(mock.ANY, mock.ANY)

    # Auto-generated test for _mUpdateRequestData
    @mock.patch('exabox.ovm.cluelasticcells.ebGetDefaultDB')
    def test__mUpdateRequestData_updates_request(self, mock_get_db):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells._mUpdateRequestData with request object")

        manager = object.__new__(ebCluElasticCellManager)
        request = mock.MagicMock()
        ebox = mock.MagicMock()
        ebox.mGetRequestObj.return_value = request
        db = mock.MagicMock()
        mock_get_db.return_value = db

        options = _DummyOptions(jsonmode=False)
        payload = {'key': 'value'}

        manager._mUpdateRequestData(options, payload, ebox)

        request.mSetData.assert_called_once()
        db.mUpdateRequest.assert_called_once_with(request)

    # Auto-generated test for _mUpdateRequestData
    @mock.patch('exabox.ovm.cluelasticcells.ebLogJson')
    def test__mUpdateRequestData_logs_when_jsonmode(self, mock_log_json):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells._mUpdateRequestData json logging branch")

        manager = object.__new__(ebCluElasticCellManager)
        ebox = mock.MagicMock()
        ebox.mGetRequestObj.return_value = None

        options = _DummyOptions(jsonmode=True)
        payload = {'key': 'value'}

        manager._mUpdateRequestData(options, payload, ebox)

        mock_log_json.assert_called_once()

    # Auto-generated test for mPostReshapeValidation
    @mock.patch('exabox.ovm.cluelasticcells.ebCluPreChecks')
    def test_mPostReshapeValidation_invokes_prechecks(self, mock_prechecks):
        ebLogInfo("")
        ebLogInfo("Running unit test on cluelasticcells.mPostReshapeValidation")

        manager = object.__new__(ebCluElasticCellManager)
        ebox = mock.MagicMock()
        ebox.mCheckConfigOption.return_value = 'True'
        manager._ebCluElasticCellManager__eboxobj = ebox

        manager.mPostReshapeValidation(_DummyOptions())

        mock_prechecks.assert_called_once_with(ebox)
        mock_prechecks.return_value.mCheckClusterIntegrity.assert_called_once_with(True, 'True')

    @patch("exabox.tools.oedacli.OedacliCmdMgr.mDropCell")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestoreOEDASSHKeys")
    def test_mDeleteExascaleCell_success(self, mock_restore_keys, mock_dropcell):
        ebLogInfo("Running unit test on cluelasticcells.mDeleteExascaleCell (success)")
        # Ensure OEDA conf dir exists and patch config is set so internal cp works
        exacloudConfDir = os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf")
        os.makedirs(exacloudConfDir, exist_ok=True)
        # Use existing config as patch config source
        self.mGetClubox().mSetPatchConfig(self.mGetClubox().mGetConfigPath())

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.jsonconf = copy.deepcopy(REMOVED_CELLS_PAYLOAD_XS)
        mgr = ebCluElasticCellManager(self.mGetClubox(), fullOptions)
        mgr.mDeleteExascaleCell(fullOptions)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")
    @patch("exabox.tools.oedacli.OedacliCmdMgr.mDropCell", side_effect=ExacloudRuntimeError(1, 1, "dropcell failure"))
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestoreOEDASSHKeys")
    def test_mDeleteExascaleCell_oedacli_error(self, mock_restore_keys, mock_dropcell, mock_update_err):
        ebLogInfo("Running unit test on cluelasticcells.mDeleteExascaleCell (error path)")
        exacloudConfDir = os.path.join(self.mGetClubox().mGetOedaPath(), "exacloud.conf")
        os.makedirs(exacloudConfDir, exist_ok=True)
        self.mGetClubox().mSetPatchConfig(self.mGetClubox().mGetConfigPath())

        fullOptions = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        fullOptions.jsonconf = copy.deepcopy(REMOVED_CELLS_PAYLOAD_XS)
        mgr = ebCluElasticCellManager(self.mGetClubox(), fullOptions)

        rc = mgr.mDeleteExascaleCell(fullOptions)
        # Non-zero rc expected due to mapped error via mRecordError
        self.assertNotEqual(rc, 0)
        self.assertTrue(mock_update_err.called)

if __name__ == "__main__":
    unittest.main()
