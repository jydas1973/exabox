#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluelasticcells.py /main/31 2025/11/24 10:05:37 dekuckre Exp $
#
# tests_cluelasticcells.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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
from unittest import mock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Node import exaBoxNode

from exabox.log.LogMgr import ebLogInfo

from exabox.ovm.cluelasticcells import ebCluElasticCellManager

from unittest.mock import patch, MagicMock, PropertyMock, mock_open
import warnings
import copy
import uuid
import shutil
import re

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
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=True),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mProcessSELinuxUpdate', return_value=0),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.IsZdlraProv', return_value=True):
                _return_code = _elastic_cell_manager.mCloneCell(fullOptions)
                self.assertEqual(_return_code, 0)
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=True),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mProcessSELinuxUpdate', side_effect=ExacloudRuntimeError(0x0121, 0xA, "Failed to process SELinux update.")),\
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
                            ],
                            [
                                exaMockCommand("cellcli -e list flashcache attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
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
                                exaMockCommand("cellcli -e list cell detail | grep flashCacheMode", aStdout = "  flashCacheMode:         WriteBack", aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand("cellcli -e list flashcache attributes name,size", aStdout = "NOTEMPTY", aRc=0, aPersist=True),
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

if __name__ == "__main__":
    unittest.main()
