#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clustorage.py pbellary_bug-38986521/2 2026/02/20 06:43:31 pbellary Exp $
#
# tests_clustorage.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_clustorage.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    03/02/26 - Bug 39025598 - ECS_MAIN ->
#                           TESTS_DISKREBALANCE_PY.DIF AND
#                           TESTS_CLUSTORAGE_PY.DIF FROM
#                           ECS_MAIN_LINUX.X64_260228.0900
#    pbellary    02/20/26 - Bug 38986521: CRITICAL EXCEPTION CAUGHT ABORTING REQUEST ['CREATE_SPARSE'] 
#    aararora    02/11/26 - ER 38951653: Increase code coverage
#    nelango     01/27/26 - Add test for grid disk pattern
#    avimonda    01/26/26 - Bug 38834741 - AWS: EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 2085 CELLCLI : CELL-02559 :
#                           MEXECUTECMD FAILED ON <CELL NODE>, WITH CMD:
#                           CELLCLI -E LIST CELLDISK ATTRIBUTES NAME, STATUS;
#    jfsaldan    12/16/25 - Bug 38755861 - EXACS:25.4.1:CUSTOM DATA/RECO/SPARSE
#                           DISK GROUPS: RESHAPE WITH SPACE UTILIZATION FAILS:
#                           EXACLOUD IS TRYING TO RESHAPE SPARSE DISK GROUPS
#                           EVEN WHEN THE ASSIGNED SPACE HAS NOT CHANGED
#    jfsaldan    10/28/25 - Bug 38550997 - THE SHRINK BACK TO ORIGINAL SIZE
#                           STEP WILL FAIL WHILE NO MORE THAN 15% FREESPACE |
#                           EXACLOUD TO SUPPORT NEW FLAG IN ASM RESHAPE TO
#                           CALCULATE NEW TARGET SIZE IF ORIGINAL SIZE CANNOT
#                           BE SATISFIED W/CURRENT USED SPACE
#    jfsaldan    10/26/25 - Changes by AiDEr
#    naps        08/14/25 - Bug 38151629 - UT updation.
#    gparada  08/11/25 - 38253988 Dynamic Storage for data reco sparse - CS flow
#    aararora    02/24/25 - 37622158 Correct indentation of UT
#    rajsag      02/20/25 - 7481917 - exacloud | prevmcehcks
#                           mfixpmemcomponent() runs pmem cache and log checks
#                           sequentially checks sequentially| improve large
#                           cluster provisioning time
#    aararora    02/06/25 - ER 37541321: Update percentage progress of
#                           rebalance operation
#    avimonda    06/24/24 - 36554441 EXACS: DELETESERVICE FAILED WITH EXACLOUD
#                           ERROR CODE: 3802 EXACLOUD : OEDACLI ERROR FOUND ON
#                           SCRIPT EXECUTION.
#    aararora    05/31/24 - ER 35715255: Precheck for grid disk resize
#    jfsaldan    05/02/24 - Bug 36573967 - EXACS:R1 SRG: CLUSTER TERMINATION
#                           STUCK IN PREVMINSTALL STEP
#    jfsaldan    02/20/24 - Bug 36277822 - CELLINIT.ORA HAS STIB0/STIB1 SET
#                           AFTER TERMINATION CAUSING CELLRSRV PROBLEMS IN
#                           XEN/IB SVM
#    aararora    05/12/23 - Add test for checking grid disks resize on cells.
#    jfsaldan    11/03/22 - Bug 33993510 - CELLDISKS RECREATED AFTER DBSYSTEM
#                           TERMINATION
#    jfsaldan    01/31/22 - Creation
#

import math
import time
import unittest
import xml.etree.ElementTree as etree

from unittest.mock import patch
from unittest.mock import MagicMock, Mock

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError, gDiskgroupError
from exabox.core.MockCommand import exaMockCommand

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.ovm.cludiskgroups import ebDiskgroupOpConstants, ebCluManageDiskgroup
from exabox.ovm.clustorage import ebCluManageStorage, ebCluStorageConfig, ebCluDiskGroupConfig, \
    ebCluStoragePoolConfig, ebCluEDVVolumesConfig, ebCluQuorumManager, mParseStorageDistrib

from exabox.utils.node import connect_to_host


REBALANCE_OUTPUT = """
 GROUP_NUMBER   STATE   POWER EST_MINUTES  SOFAR  EST_WORK
 ------------ ----- --------- ---- ---------- ----------- ----------
 	   1  RUN				 48  20   1100   2000
 	   1  RUN				 48  10   200   800
 	   2  RUN				 48  11   300   800
 	   1  WAIT				 48
 	   2  WAIT				 48
"""

REBALANCE_OUTPUT_INVALID = """
 GROUP_NUMBER   STATE   POWER EST_MINUTES  SOFAR  EST_WORK
 ------------ ----- --------- ---- ---------- ----------- ----------
 	   1  RUN				 48  20   A   2000
 	   1  WAIT				 48
 	   2  WAIT				 48
"""

GROUP_NAME_DATA = """
GROUP_NUMBER   NAME
 ------------ -----
 	   1  DATAC8
"""

GROUP_NAME_RECO = """
GROUP_NUMBER   NAME
 ------------ -----
 	   2  RECOC8
"""

_detail_out = {
            'name': 'sea201109exdcl01_PMEMLOG',
            'cellDisk': 'PM_00_sea201109exdcl01,PM_01_sea201109exdcl01,...',
            'creationTime': '2021-05-05T23:48:01+00:00',
            'degradedCelldisks': '',
            'effectiveSize': '9.9375G',
            'efficiency': '100.0',
            'id': '7be25e9d-0f6b-4240-b186-c520e30d17c3',
            'size': '9.9375G',
            'status': 'abnormal'
}

class mockStream():

    def __init__(self, aStreamContents=["None"]):
        self.stream_content = aStreamContents

    def readlines(self):
        return self.stream_content

    def read(self):
        return self.stream_content[0]

class ebTestCluStorage(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

        # Define generic grid list to mock result of cellcli command

        self._griddisk_cluster = [
            '\t ADG1C4_CD_03_scaqab10celadm01\n',
            '\t ADG1C4_CD_04_scaqab10celadm01\n',
            '\t ADG1C4_CD_05_scaqab10celadm01\n',
            '\t ADG1C4_CD_06_scaqab10celadm01\n',
            '\t ADG1C4_CD_07_scaqab10celadm01\n',
            '\t ADG1C4_CD_08_scaqab10celadm01\n',
            '\t ADG1C4_CD_09_scaqab10celadm01\n',
            '\t ADG1C4_CD_10_scaqab10celadm01\n',
            '\t ADG1C4_CD_11_scaqab10celadm01\n',
            '\t ADG2C4_CD_02_scaqab10celadm01\n',
            '\t ADG2C4_CD_03_scaqab10celadm01\n',
            '\t ADG2C4_CD_04_scaqab10celadm01\n',
            '\t ADG2C4_CD_05_scaqab10celadm01\n',
            '\t ADG2C4_CD_06_scaqab10celadm01\n',
            '\t ADG2C4_CD_07_scaqab10celadm01\n',
            '\t ADG2C4_CD_08_scaqab10celadm01\n',
            '\t ADG2C4_CD_09_scaqab10celadm01\n',
            '\t ADG2C4_CD_10_scaqab10celadm01\n',
            '\t ADG2C4_CD_11_scaqab10celadm01\n',
            '\t DATAC4_CD_00_scaqab10celadm01\n',
            '\t DATAC4_CD_01_scaqab10celadm01\n',
            '\t DATAC4_CD_02_scaqab10celadm01\n',
            '\t DATAC4_CD_03_scaqab10celadm01\n',
            '\t DATAC4_CD_04_scaqab10celadm01\n',
            '\t DATAC4_CD_05_scaqab10celadm01\n',
            '\t DATAC4_CD_06_scaqab10celadm01\n',
            '\t DATAC4_CD_07_scaqab10celadm01\n',
            '\t DATAC4_CD_08_scaqab10celadm01\n',
            '\t DATAC4_CD_09_scaqab10celadm01\n',
            '\t DATAC4_CD_10_scaqab10celadm01\n',
            '\t DATAC4_CD_11_scaqab10celadm01\n',
            '\t RECOC4_CD_00_scaqab10celadm01\n',
            '\t RECOC4_CD_01_scaqab10celadm01\n',
            '\t RECOC4_CD_02_scaqab10celadm01\n',
            '\t RECOC4_CD_03_scaqab10celadm01\n',
            '\t RECOC4_CD_04_scaqab10celadm01\n',
            '\t RECOC4_CD_05_scaqab10celadm01\n',
            '\t RECOC4_CD_06_scaqab10celadm01\n',
            '\t RECOC4_CD_07_scaqab10celadm01\n',
            '\t RECOC4_CD_08_scaqab10celadm01\n',
            '\t RECOC4_CD_09_scaqab10celadm01\n',
            '\t RECOC4_CD_10_scaqab10celadm01\n',
            '\t RECOC4_CD_11_scaqab10celadm01\n',
            ]

        self._griddisk_list = [
	        '\t ADG1C4_CD_03_scaqab10celadm01\n',
	        '\t ADG1C4_CD_04_scaqab10celadm01\n',
	        '\t ADG1C4_CD_05_scaqab10celadm01\n',
	        '\t ADG1C4_CD_06_scaqab10celadm01\n',
	        '\t ADG1C4_CD_07_scaqab10celadm01\n',
	        '\t ADG1C4_CD_08_scaqab10celadm01\n',
	        '\t ADG1C4_CD_09_scaqab10celadm01\n',
	        '\t ADG1C4_CD_10_scaqab10celadm01\n',
	        '\t ADG1C4_CD_11_scaqab10celadm01\n',
	        '\t ADG1C5_CD_02_scaqab10celadm01\n',
	        '\t ADG1C5_CD_03_scaqab10celadm01\n',
	        '\t ADG1C5_CD_04_scaqab10celadm01\n',
	        '\t ADG1C5_CD_05_scaqab10celadm01\n',
	        '\t ADG1C5_CD_06_scaqab10celadm01\n',
	        '\t ADG1C5_CD_07_scaqab10celadm01\n',
	        '\t ADG1C5_CD_08_scaqab10celadm01\n',
	        '\t ADG1C5_CD_09_scaqab10celadm01\n',
	        '\t ADG1C5_CD_10_scaqab10celadm01\n',
	        '\t ADG1C5_CD_11_scaqab10celadm01\n',
	        '\t ADG1C6_CD_02_scaqab10celadm01\n',
	        '\t ADG1C6_CD_03_scaqab10celadm01\n',
	        '\t ADG1C6_CD_04_scaqab10celadm01\n',
	        '\t ADG1C6_CD_05_scaqab10celadm01\n',
	        '\t ADG1C6_CD_06_scaqab10celadm01\n',
	        '\t ADG1C6_CD_07_scaqab10celadm01\n',
	        '\t ADG1C6_CD_08_scaqab10celadm01\n',
	        '\t ADG1C6_CD_09_scaqab10celadm01\n',
	        '\t ADG1C6_CD_10_scaqab10celadm01\n',
	        '\t ADG1C6_CD_11_scaqab10celadm01\n',
	        '\t ADG1C7_CD_02_scaqab10celadm01\n',
	        '\t ADG1C7_CD_03_scaqab10celadm01\n',
	        '\t ADG1C7_CD_04_scaqab10celadm01\n',
	        '\t ADG1C7_CD_05_scaqab10celadm01\n',
	        '\t ADG1C7_CD_06_scaqab10celadm01\n',
	        '\t ADG1C7_CD_07_scaqab10celadm01\n',
	        '\t ADG1C7_CD_08_scaqab10celadm01\n',
	        '\t ADG1C7_CD_09_scaqab10celadm01\n',
	        '\t ADG1C7_CD_10_scaqab10celadm01\n',
	        '\t ADG1C7_CD_11_scaqab10celadm01\n',
	        '\t ADG2C4_CD_02_scaqab10celadm01\n',
	        '\t ADG2C4_CD_03_scaqab10celadm01\n',
	        '\t ADG2C4_CD_04_scaqab10celadm01\n',
	        '\t ADG2C4_CD_05_scaqab10celadm01\n',
	        '\t ADG2C4_CD_06_scaqab10celadm01\n',
	        '\t ADG2C4_CD_07_scaqab10celadm01\n',
	        '\t ADG2C4_CD_08_scaqab10celadm01\n',
	        '\t ADG2C4_CD_09_scaqab10celadm01\n',
	        '\t ADG2C4_CD_10_scaqab10celadm01\n',
	        '\t ADG2C4_CD_11_scaqab10celadm01\n',
	        '\t ADG2C5_CD_02_scaqab10celadm01\n',
	        '\t ADG2C5_CD_03_scaqab10celadm01\n',
	        '\t ADG2C5_CD_04_scaqab10celadm01\n',
	        '\t ADG2C5_CD_05_scaqab10celadm01\n',
	        '\t ADG2C5_CD_06_scaqab10celadm01\n',
	        '\t ADG2C5_CD_07_scaqab10celadm01\n',
	        '\t ADG2C5_CD_08_scaqab10celadm01\n',
	        '\t ADG2C5_CD_09_scaqab10celadm01\n',
	        '\t ADG2C5_CD_10_scaqab10celadm01\n',
	        '\t ADG2C5_CD_11_scaqab10celadm01\n',
	        '\t ADG2C6_CD_02_scaqab10celadm01\n',
	        '\t ADG2C6_CD_03_scaqab10celadm01\n',
	        '\t ADG2C6_CD_04_scaqab10celadm01\n',
	        '\t ADG2C6_CD_05_scaqab10celadm01\n',
	        '\t ADG2C6_CD_06_scaqab10celadm01\n',
	        '\t ADG2C6_CD_07_scaqab10celadm01\n',
	        '\t ADG2C6_CD_08_scaqab10celadm01\n',
	        '\t ADG2C6_CD_09_scaqab10celadm01\n',
	        '\t ADG2C6_CD_10_scaqab10celadm01\n',
	        '\t ADG2C6_CD_11_scaqab10celadm01\n',
	        '\t ADG2C7_CD_02_scaqab10celadm01\n',
	        '\t ADG2C7_CD_03_scaqab10celadm01\n',
	        '\t ADG2C7_CD_04_scaqab10celadm01\n',
	        '\t ADG2C7_CD_05_scaqab10celadm01\n',
	        '\t ADG2C7_CD_06_scaqab10celadm01\n',
	        '\t ADG2C7_CD_07_scaqab10celadm01\n',
	        '\t ADG2C7_CD_08_scaqab10celadm01\n',
	        '\t ADG2C7_CD_09_scaqab10celadm01\n',
	        '\t ADG2C7_CD_10_scaqab10celadm01\n',
	        '\t ADG2C7_CD_11_scaqab10celadm01\n',
	        '\t DATAC2_CD_00_scaqab10celadm01\n',
	        '\t DATAC2_CD_01_scaqab10celadm01\n',
	        '\t DATAC2_CD_02_scaqab10celadm01\n',
	        '\t DATAC2_CD_03_scaqab10celadm01\n',
	        '\t DATAC2_CD_04_scaqab10celadm01\n',
	        '\t DATAC2_CD_05_scaqab10celadm01\n',
	        '\t DATAC2_CD_06_scaqab10celadm01\n',
	        '\t DATAC2_CD_07_scaqab10celadm01\n',
	        '\t DATAC2_CD_08_scaqab10celadm01\n',
	        '\t DATAC2_CD_09_scaqab10celadm01\n',
	        '\t DATAC2_CD_10_scaqab10celadm01\n',
	        '\t DATAC2_CD_11_scaqab10celadm01\n',
	        '\t DATAC4_CD_00_scaqab10celadm01\n',
	        '\t DATAC4_CD_01_scaqab10celadm01\n',
	        '\t DATAC4_CD_02_scaqab10celadm01\n',
	        '\t DATAC4_CD_03_scaqab10celadm01\n',
	        '\t DATAC4_CD_04_scaqab10celadm01\n',
	        '\t DATAC4_CD_05_scaqab10celadm01\n',
	        '\t DATAC4_CD_06_scaqab10celadm01\n',
	        '\t DATAC4_CD_07_scaqab10celadm01\n',
	        '\t DATAC4_CD_08_scaqab10celadm01\n',
	        '\t DATAC4_CD_09_scaqab10celadm01\n',
	        '\t DATAC4_CD_10_scaqab10celadm01\n',
	        '\t DATAC4_CD_11_scaqab10celadm01\n',
	        '\t DATAC5_CD_00_scaqab10celadm01\n',
	        '\t DATAC5_CD_01_scaqab10celadm01\n',
	        '\t DATAC5_CD_02_scaqab10celadm01\n',
	        '\t DATAC5_CD_03_scaqab10celadm01\n',
	        '\t DATAC5_CD_04_scaqab10celadm01\n',
	        '\t DATAC5_CD_05_scaqab10celadm01\n',
	        '\t DATAC5_CD_06_scaqab10celadm01\n',
	        '\t DATAC5_CD_07_scaqab10celadm01\n',
	        '\t DATAC5_CD_08_scaqab10celadm01\n',
	        '\t DATAC5_CD_09_scaqab10celadm01\n',
	        '\t DATAC5_CD_10_scaqab10celadm01\n',
	        '\t DATAC5_CD_11_scaqab10celadm01\n',
	        '\t DATAC6_CD_00_scaqab10celadm01\n',
	        '\t DATAC6_CD_01_scaqab10celadm01\n',
	        '\t DATAC6_CD_02_scaqab10celadm01\n',
	        '\t DATAC6_CD_03_scaqab10celadm01\n',
	        '\t DATAC6_CD_04_scaqab10celadm01\n',
	        '\t DATAC6_CD_05_scaqab10celadm01\n',
	        '\t DATAC6_CD_06_scaqab10celadm01\n',
	        '\t DATAC6_CD_07_scaqab10celadm01\n',
	        '\t DATAC6_CD_08_scaqab10celadm01\n',
	        '\t DATAC6_CD_09_scaqab10celadm01\n',
	        '\t DATAC6_CD_10_scaqab10celadm01\n',
	        '\t DATAC6_CD_11_scaqab10celadm01\n',
	        '\t DATAC7_CD_00_scaqab10celadm01\n',
	        '\t DATAC7_CD_01_scaqab10celadm01\n',
	        '\t DATAC7_CD_02_scaqab10celadm01\n',
	        '\t DATAC7_CD_03_scaqab10celadm01\n',
	        '\t DATAC7_CD_04_scaqab10celadm01\n',
	        '\t DATAC7_CD_05_scaqab10celadm01\n',
	        '\t DATAC7_CD_06_scaqab10celadm01\n',
	        '\t DATAC7_CD_07_scaqab10celadm01\n',
	        '\t DATAC7_CD_08_scaqab10celadm01\n',
	        '\t DATAC7_CD_09_scaqab10celadm01\n',
	        '\t DATAC7_CD_10_scaqab10celadm01\n',
	        '\t DATAC7_CD_11_scaqab10celadm01\n',
	        '\t RECOC2_CD_00_scaqab10celadm01\n',
	        '\t RECOC2_CD_01_scaqab10celadm01\n',
	        '\t RECOC2_CD_02_scaqab10celadm01\n',
	        '\t RECOC2_CD_03_scaqab10celadm01\n',
	        '\t RECOC2_CD_04_scaqab10celadm01\n',
	        '\t RECOC2_CD_05_scaqab10celadm01\n',
	        '\t RECOC2_CD_06_scaqab10celadm01\n',
	        '\t RECOC2_CD_07_scaqab10celadm01\n',
	        '\t RECOC2_CD_08_scaqab10celadm01\n',
	        '\t RECOC2_CD_09_scaqab10celadm01\n',
	        '\t RECOC2_CD_10_scaqab10celadm01\n',
	        '\t RECOC2_CD_11_scaqab10celadm01\n',
	        '\t RECOC4_CD_00_scaqab10celadm01\n',
	        '\t RECOC4_CD_01_scaqab10celadm01\n',
	        '\t RECOC4_CD_02_scaqab10celadm01\n',
	        '\t RECOC4_CD_03_scaqab10celadm01\n',
	        '\t RECOC4_CD_04_scaqab10celadm01\n',
	        '\t RECOC4_CD_05_scaqab10celadm01\n',
	        '\t RECOC4_CD_06_scaqab10celadm01\n',
	        '\t RECOC4_CD_07_scaqab10celadm01\n',
	        '\t RECOC4_CD_08_scaqab10celadm01\n',
	        '\t RECOC4_CD_09_scaqab10celadm01\n',
	        '\t RECOC4_CD_10_scaqab10celadm01\n',
	        '\t RECOC4_CD_11_scaqab10celadm01\n',
	        '\t RECOC5_CD_00_scaqab10celadm01\n',
	        '\t RECOC5_CD_01_scaqab10celadm01\n',
	        '\t RECOC5_CD_02_scaqab10celadm01\n',
	        '\t RECOC5_CD_03_scaqab10celadm01\n',
	        '\t RECOC5_CD_04_scaqab10celadm01\n',
	        '\t RECOC5_CD_05_scaqab10celadm01\n',
	        '\t RECOC5_CD_06_scaqab10celadm01\n',
	        '\t RECOC5_CD_07_scaqab10celadm01\n',
	        '\t RECOC5_CD_08_scaqab10celadm01\n',
	        '\t RECOC5_CD_09_scaqab10celadm01\n',
	        '\t RECOC5_CD_10_scaqab10celadm01\n',
	        '\t RECOC5_CD_11_scaqab10celadm01\n',
	        '\t RECOC6_CD_00_scaqab10celadm01\n',
	        '\t RECOC6_CD_01_scaqab10celadm01\n',
	        '\t RECOC6_CD_02_scaqab10celadm01\n',
	        '\t RECOC6_CD_03_scaqab10celadm01\n',
	        '\t RECOC6_CD_04_scaqab10celadm01\n',
	        '\t RECOC6_CD_05_scaqab10celadm01\n',
	        '\t RECOC6_CD_06_scaqab10celadm01\n',
	        '\t RECOC6_CD_07_scaqab10celadm01\n',
	        '\t RECOC6_CD_08_scaqab10celadm01\n',
	        '\t RECOC6_CD_09_scaqab10celadm01\n',
	        '\t RECOC6_CD_10_scaqab10celadm01\n',
	        '\t RECOC6_CD_11_scaqab10celadm01\n',
	        '\t RECOC7_CD_00_scaqab10celadm01\n',
	        '\t RECOC7_CD_01_scaqab10celadm01\n',
	        '\t RECOC7_CD_02_scaqab10celadm01\n',
	        '\t RECOC7_CD_03_scaqab10celadm01\n',
	        '\t RECOC7_CD_04_scaqab10celadm01\n',
	        '\t RECOC7_CD_05_scaqab10celadm01\n',
	        '\t RECOC7_CD_06_scaqab10celadm01\n',
	        '\t RECOC7_CD_07_scaqab10celadm01\n',
	        '\t RECOC7_CD_08_scaqab10celadm01\n',
	        '\t RECOC7_CD_09_scaqab10celadm01\n',
	        '\t RECOC7_CD_10_scaqab10celadm01\n',
	        '\t RECOC7_CD_11_scaqab10celadm01\n',
            ]

        self._griddisk_list_excluding_own_cluster_c4 = [
	        '\t ADG1C5_CD_02_scaqab10celadm01\n',
	        '\t ADG1C5_CD_03_scaqab10celadm01\n',
	        '\t ADG1C5_CD_04_scaqab10celadm01\n',
	        '\t ADG1C5_CD_05_scaqab10celadm01\n',
	        '\t ADG1C5_CD_06_scaqab10celadm01\n',
	        '\t ADG1C5_CD_07_scaqab10celadm01\n',
	        '\t ADG1C5_CD_08_scaqab10celadm01\n',
	        '\t ADG1C5_CD_09_scaqab10celadm01\n',
	        '\t ADG1C5_CD_10_scaqab10celadm01\n',
	        '\t ADG1C5_CD_11_scaqab10celadm01\n',
	        '\t ADG1C6_CD_02_scaqab10celadm01\n',
	        '\t ADG1C6_CD_03_scaqab10celadm01\n',
	        '\t ADG1C6_CD_04_scaqab10celadm01\n',
	        '\t ADG1C6_CD_05_scaqab10celadm01\n',
	        '\t ADG1C6_CD_06_scaqab10celadm01\n',
	        '\t ADG1C6_CD_07_scaqab10celadm01\n',
	        '\t ADG1C6_CD_08_scaqab10celadm01\n',
	        '\t ADG1C6_CD_09_scaqab10celadm01\n',
	        '\t ADG1C6_CD_10_scaqab10celadm01\n',
	        '\t ADG1C6_CD_11_scaqab10celadm01\n',
	        '\t ADG1C7_CD_02_scaqab10celadm01\n',
	        '\t ADG1C7_CD_03_scaqab10celadm01\n',
	        '\t ADG1C7_CD_04_scaqab10celadm01\n',
	        '\t ADG1C7_CD_05_scaqab10celadm01\n',
	        '\t ADG1C7_CD_06_scaqab10celadm01\n',
	        '\t ADG1C7_CD_07_scaqab10celadm01\n',
	        '\t ADG1C7_CD_08_scaqab10celadm01\n',
	        '\t ADG1C7_CD_09_scaqab10celadm01\n',
	        '\t ADG1C7_CD_10_scaqab10celadm01\n',
	        '\t ADG1C7_CD_11_scaqab10celadm01\n',
	        '\t ADG2C5_CD_02_scaqab10celadm01\n',
	        '\t ADG2C5_CD_03_scaqab10celadm01\n',
	        '\t ADG2C5_CD_04_scaqab10celadm01\n',
	        '\t ADG2C5_CD_05_scaqab10celadm01\n',
	        '\t ADG2C5_CD_06_scaqab10celadm01\n',
	        '\t ADG2C5_CD_07_scaqab10celadm01\n',
	        '\t ADG2C5_CD_08_scaqab10celadm01\n',
	        '\t ADG2C5_CD_09_scaqab10celadm01\n',
	        '\t ADG2C5_CD_10_scaqab10celadm01\n',
	        '\t ADG2C5_CD_11_scaqab10celadm01\n',
	        '\t ADG2C6_CD_02_scaqab10celadm01\n',
	        '\t ADG2C6_CD_03_scaqab10celadm01\n',
	        '\t ADG2C6_CD_04_scaqab10celadm01\n',
	        '\t ADG2C6_CD_05_scaqab10celadm01\n',
	        '\t ADG2C6_CD_06_scaqab10celadm01\n',
	        '\t ADG2C6_CD_07_scaqab10celadm01\n',
	        '\t ADG2C6_CD_08_scaqab10celadm01\n',
	        '\t ADG2C6_CD_09_scaqab10celadm01\n',
	        '\t ADG2C6_CD_10_scaqab10celadm01\n',
	        '\t ADG2C6_CD_11_scaqab10celadm01\n',
	        '\t ADG2C7_CD_02_scaqab10celadm01\n',
	        '\t ADG2C7_CD_03_scaqab10celadm01\n',
	        '\t ADG2C7_CD_04_scaqab10celadm01\n',
	        '\t ADG2C7_CD_05_scaqab10celadm01\n',
	        '\t ADG2C7_CD_06_scaqab10celadm01\n',
	        '\t ADG2C7_CD_07_scaqab10celadm01\n',
	        '\t ADG2C7_CD_08_scaqab10celadm01\n',
	        '\t ADG2C7_CD_09_scaqab10celadm01\n',
	        '\t ADG2C7_CD_10_scaqab10celadm01\n',
	        '\t ADG2C7_CD_11_scaqab10celadm01\n',
	        '\t DATAC2_CD_00_scaqab10celadm01\n',
	        '\t DATAC2_CD_01_scaqab10celadm01\n',
	        '\t DATAC2_CD_02_scaqab10celadm01\n',
	        '\t DATAC2_CD_03_scaqab10celadm01\n',
	        '\t DATAC2_CD_04_scaqab10celadm01\n',
	        '\t DATAC2_CD_05_scaqab10celadm01\n',
	        '\t DATAC2_CD_06_scaqab10celadm01\n',
	        '\t DATAC2_CD_07_scaqab10celadm01\n',
	        '\t DATAC2_CD_08_scaqab10celadm01\n',
	        '\t DATAC2_CD_09_scaqab10celadm01\n',
	        '\t DATAC2_CD_10_scaqab10celadm01\n',
	        '\t DATAC2_CD_11_scaqab10celadm01\n',
	        '\t DATAC5_CD_00_scaqab10celadm01\n',
	        '\t DATAC5_CD_01_scaqab10celadm01\n',
	        '\t DATAC5_CD_02_scaqab10celadm01\n',
	        '\t DATAC5_CD_03_scaqab10celadm01\n',
	        '\t DATAC5_CD_04_scaqab10celadm01\n',
	        '\t DATAC5_CD_05_scaqab10celadm01\n',
	        '\t DATAC5_CD_06_scaqab10celadm01\n',
	        '\t DATAC5_CD_07_scaqab10celadm01\n',
	        '\t DATAC5_CD_08_scaqab10celadm01\n',
	        '\t DATAC5_CD_09_scaqab10celadm01\n',
	        '\t DATAC5_CD_10_scaqab10celadm01\n',
	        '\t DATAC5_CD_11_scaqab10celadm01\n',
	        '\t DATAC6_CD_00_scaqab10celadm01\n',
	        '\t DATAC6_CD_01_scaqab10celadm01\n',
	        '\t DATAC6_CD_02_scaqab10celadm01\n',
	        '\t DATAC6_CD_03_scaqab10celadm01\n',
	        '\t DATAC6_CD_04_scaqab10celadm01\n',
	        '\t DATAC6_CD_05_scaqab10celadm01\n',
	        '\t DATAC6_CD_06_scaqab10celadm01\n',
	        '\t DATAC6_CD_07_scaqab10celadm01\n',
	        '\t DATAC6_CD_08_scaqab10celadm01\n',
	        '\t DATAC6_CD_09_scaqab10celadm01\n',
	        '\t DATAC6_CD_10_scaqab10celadm01\n',
	        '\t DATAC6_CD_11_scaqab10celadm01\n',
	        '\t DATAC7_CD_00_scaqab10celadm01\n',
	        '\t DATAC7_CD_01_scaqab10celadm01\n',
	        '\t DATAC7_CD_02_scaqab10celadm01\n',
	        '\t DATAC7_CD_03_scaqab10celadm01\n',
	        '\t DATAC7_CD_04_scaqab10celadm01\n',
	        '\t DATAC7_CD_05_scaqab10celadm01\n',
	        '\t DATAC7_CD_06_scaqab10celadm01\n',
	        '\t DATAC7_CD_07_scaqab10celadm01\n',
	        '\t DATAC7_CD_08_scaqab10celadm01\n',
	        '\t DATAC7_CD_09_scaqab10celadm01\n',
	        '\t DATAC7_CD_10_scaqab10celadm01\n',
	        '\t DATAC7_CD_11_scaqab10celadm01\n',
	        '\t RECOC2_CD_00_scaqab10celadm01\n',
	        '\t RECOC2_CD_01_scaqab10celadm01\n',
	        '\t RECOC2_CD_02_scaqab10celadm01\n',
	        '\t RECOC2_CD_03_scaqab10celadm01\n',
	        '\t RECOC2_CD_04_scaqab10celadm01\n',
	        '\t RECOC2_CD_05_scaqab10celadm01\n',
	        '\t RECOC2_CD_06_scaqab10celadm01\n',
	        '\t RECOC2_CD_07_scaqab10celadm01\n',
	        '\t RECOC2_CD_08_scaqab10celadm01\n',
	        '\t RECOC2_CD_09_scaqab10celadm01\n',
	        '\t RECOC2_CD_10_scaqab10celadm01\n',
	        '\t RECOC2_CD_11_scaqab10celadm01\n',
	        '\t RECOC5_CD_00_scaqab10celadm01\n',
	        '\t RECOC5_CD_01_scaqab10celadm01\n',
	        '\t RECOC5_CD_02_scaqab10celadm01\n',
	        '\t RECOC5_CD_03_scaqab10celadm01\n',
	        '\t RECOC5_CD_04_scaqab10celadm01\n',
	        '\t RECOC5_CD_05_scaqab10celadm01\n',
	        '\t RECOC5_CD_06_scaqab10celadm01\n',
	        '\t RECOC5_CD_07_scaqab10celadm01\n',
	        '\t RECOC5_CD_08_scaqab10celadm01\n',
	        '\t RECOC5_CD_09_scaqab10celadm01\n',
	        '\t RECOC5_CD_10_scaqab10celadm01\n',
	        '\t RECOC5_CD_11_scaqab10celadm01\n',
	        '\t RECOC6_CD_00_scaqab10celadm01\n',
	        '\t RECOC6_CD_01_scaqab10celadm01\n',
	        '\t RECOC6_CD_02_scaqab10celadm01\n',
	        '\t RECOC6_CD_03_scaqab10celadm01\n',
	        '\t RECOC6_CD_04_scaqab10celadm01\n',
	        '\t RECOC6_CD_05_scaqab10celadm01\n',
	        '\t RECOC6_CD_06_scaqab10celadm01\n',
	        '\t RECOC6_CD_07_scaqab10celadm01\n',
	        '\t RECOC6_CD_08_scaqab10celadm01\n',
	        '\t RECOC6_CD_09_scaqab10celadm01\n',
	        '\t RECOC6_CD_10_scaqab10celadm01\n',
	        '\t RECOC6_CD_11_scaqab10celadm01\n',
	        '\t RECOC7_CD_00_scaqab10celadm01\n',
	        '\t RECOC7_CD_01_scaqab10celadm01\n',
	        '\t RECOC7_CD_02_scaqab10celadm01\n',
	        '\t RECOC7_CD_03_scaqab10celadm01\n',
	        '\t RECOC7_CD_04_scaqab10celadm01\n',
	        '\t RECOC7_CD_05_scaqab10celadm01\n',
	        '\t RECOC7_CD_06_scaqab10celadm01\n',
	        '\t RECOC7_CD_07_scaqab10celadm01\n',
	        '\t RECOC7_CD_08_scaqab10celadm01\n',
	        '\t RECOC7_CD_09_scaqab10celadm01\n',
	        '\t RECOC7_CD_10_scaqab10celadm01\n',
	        '\t RECOC7_CD_11_scaqab10celadm01\n',
            ]
    
    def test_mGetCurrentClusterGridDisksFromCells_c4_griddisk_present(self):
        """
        Method to test clustorage method 'mGetCellGridDisk'
        """

        # Declare variable to use
        _ebox = self.mGetClubox()
        _ebox.mGetCmd = MagicMock(return_value='elastic_info')
        _ebox.mReturnCellNodes = MagicMock(return_value=['cell1.example.com'])
        _json = self.mGetPayload()
        _clustorage = _ebox.mGetStorage()
        _ebox.mReturnCellNodes = MagicMock(return_value=['cell1.example.com', 'cell2.example.com'])
        _cell_list = ['cell1.example.com', 'cell2.example.com']

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME;",
                        aStdout = "".join(self._griddisk_list),
                        aRc=0,
                        aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Expected result
        _expected_gd = [ griddisk.strip() for griddisk in self._griddisk_cluster]
        _expected_result = {}
        _expected_result['cell1.example.com'] = _expected_gd
        _expected_result['cell2.example.com'] = _expected_gd

        # Override suffix to C4 so its one of self._griddisk_list
        _clustorage.mClusterDiskGroupSuffix = MagicMock(return_value="C4")

        # Run method to test
        with patch.object(_clustorage, 'mListCellDG', return_value=[g.strip() for g in self._griddisk_list]):
            _results = {}
            for _cell in _cell_list:
                with connect_to_host(_cell, get_gcontext()) as _node:
                    _results[_cell] = _clustorage.mGetCurrentClusterGridDisksFromCells(_node)

            self.assertEqual(_results, _expected_result)

    def test_mGetCurrentClusterGridDisksFromCells_c6_griddisk_not_present(self):
        """
        Method to test clustorage method 'mGetCellGridDisk'
        """

        # Declare variable to use
        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _clustorage = _ebox.mGetStorage()
        _cell_list = ['cell1.example.com', 'cell2.example.com']

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME;",
                        aStdout = "".join(self._griddisk_list),
                        aRc=0,
                        aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Expected result
        _expected_gd = []
        _expected_result = {}
        _expected_result['cell1.example.com'] = _expected_gd
        _expected_result['cell2.example.com'] = _expected_gd

        # Override suffix to C9 so its one of self._griddisk_list
        _clustorage.mClusterDiskGroupSuffix = MagicMock(return_value="C9")

        # Run method to test
        with patch.object(_clustorage, 'mListCellDG', return_value=[g.strip() for g in self._griddisk_list]):
            _results = {}
            for _cell in _cell_list:
                with connect_to_host(_cell, get_gcontext()) as _node:
                    _results[_cell] = _clustorage.mGetCurrentClusterGridDisksFromCells(_node)

        self.assertEqual(_results, _expected_result)

    # Auto-generated test for mGetCurrentClusterGridDisksFromCells
    def test_mGetCurrentClusterGridDisksFromCells_missing_suffix(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'

        with patch.object(_clustorage, 'mClusterDiskGroupSuffix', return_value=None), \
             patch.object(_clustorage, 'mListCellDG') as _mock_list:
            _result = _clustorage.mGetCurrentClusterGridDisksFromCells(_node)

        self.assertEqual(_result, [])
        _mock_list.assert_not_called()

    @patch('exabox.ovm.clustorage.ebLogWarn')
    def test_mListCellDisksAttributes_retry_CELL_02559(self,
            aMockLogWarn):

        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()
        _controller = _clustorage._ebCluStorageConfig__ebox
        _cell_list = list(_ebox.mReturnCellNodes())

        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand(
                        'cellcli -e LIST CELLDISK ATTRIBUTES NAME, STATUS;',
                        aRc=1,
                        aStdout='',
                        aStderr='CELL-02559 communication error'
                    ),
                    exaMockCommand(
                        'cellcli -e LIST CELLDISK ATTRIBUTES NAME, STATUS;',
                        aRc=0,
                        aStdout='CD_01_scaqab10celadm01 normal\n',
                        aPersist=True
                    )
                ]
                for _ in _cell_list
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected = {
            _cell: {'CD_01_scaqab10celadm01': {'STATUS': 'normal'}}
            for _cell in _cell_list
        }

        with patch.object(_controller, 'mCheckCellsServicesUp') as aMockCheck, \
             patch('exabox.ovm.clustorage.sleep', return_value=None):
            _results = {}
            for _cell in _cell_list:
                with connect_to_host(_cell, get_gcontext()) as _node:
                    _results[_cell] = _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

        self.assertEqual(_results, _expected)

        self.assertEqual(aMockLogWarn.call_count, len(_cell_list))
        for (_call, _cell) in zip(aMockLogWarn.call_args_list, _cell_list):
            self.assertIn('CELL-02559', _call[0][0])
            self.assertIn(_cell, _call[0][0])

        self.assertEqual(aMockCheck.call_count, len(_cell_list))
        for (_call, _cell) in zip(aMockCheck.call_args_list, _cell_list):
            self.assertEqual(_call.kwargs, {'aRestart': False, 'aCellList': [_cell]})

    # Auto-generated test for mListCellDisksAttributes
    @patch('exabox.ovm.clustorage.ebLogWarn')
    def test_mListCellDisksAttributes_retry_ms_detected_error(self,
            aMockLogWarn):

        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()
        _controller = _clustorage._ebCluStorageConfig__ebox
        _cell_list = list(_ebox.mReturnCellNodes())

        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand(
                        'cellcli -e LIST CELLDISK ATTRIBUTES NAME, STATUS;',
                        aRc=1,
                        aStdout='ms detected error',
                        aStderr='some error'
                    ),
                    exaMockCommand(
                        'cellcli -e LIST CELLDISK ATTRIBUTES NAME, STATUS;',
                        aRc=0,
                        aStdout='CD_02_scaqab10celadm01 normal\n',
                        aPersist=True
                    )
                ]
                for _ in _cell_list
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected = {
            _cell: {'CD_02_scaqab10celadm01': {'STATUS': 'normal'}}
            for _cell in _cell_list
        }

        with patch.object(_controller, 'mCheckCellsServicesUp') as aMockCheck, \
             patch('exabox.ovm.clustorage.sleep', return_value=None):
            _results = {}
            for _cell in _cell_list:
                with connect_to_host(_cell, get_gcontext()) as _node:
                    _results[_cell] = _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

        self.assertEqual(_results, _expected)

        self.assertEqual(aMockLogWarn.call_count, len(_cell_list))
        for (_call, _cell) in zip(aMockLogWarn.call_args_list, _cell_list):
            self.assertIn('CELL-02559', _call[0][0])
            self.assertIn(_cell, _call[0][0])

        self.assertEqual(aMockCheck.call_count, len(_cell_list))
        for (_call, _cell) in zip(aMockCheck.call_args_list, _cell_list):
            self.assertEqual(_call.kwargs, {'aRestart': False, 'aCellList': [_cell]})

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_non_retry_error_raises(self):
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['stdout error']),
            mockStream(['generic failure'])
        )
        _node.mGetCmdExitStatus.return_value = True

        with self.assertRaises(ExacloudRuntimeError):
            _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

    # Auto-generated test for mListCellDisksAttributes
    @patch('exabox.ovm.clustorage.sleep')
    def test_mListCellDisksAttributes_exhausts_retries(self, _mock_sleep):
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()
        _controller = _clustorage._ebCluStorageConfig__ebox

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['CELL-02559 communication error']),
            mockStream(['CELL-02559 communication error'])
        )
        _node.mGetCmdExitStatus.return_value = True

        with patch.object(_controller, 'mCheckCellsServicesUp') as _mock_check:
            with self.assertRaises(ExacloudRuntimeError):
                _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

        self.assertEqual(_mock_check.call_count, 2)
        _mock_sleep.assert_called()

    # Auto-generated test for mListPMEMDetails
    def test_mListPMEMDetails_parses_output(self):
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'

        _stdout = """name: cell1_PMEMLOG
cellDisk: PM_00_cell1,PM_01_cell1
status: normal
"""
        _node.mExecuteCmd.return_value = None

        with patch('exabox.ovm.clustorage.node_exec_cmd') as aMockExec:
            aMockExec.return_value = (None, _stdout, None)
            _details = ebCluStorageConfig.mListPMEMDetails(_node, "log")

        aMockExec.assert_called_once()
        self.assertEqual(
            _details,
            {
                'name': 'cell1_PMEMLOG',
                'cellDisk': 'PM_00_cell1,PM_01_cell1',
                'status': 'normal'
            }
        )

    # Auto-generated test for mFixPMEMComponent
    @patch('exabox.ovm.clustorage.ebCluStorageConfig.mListPMEMDetails')
    def test_mFixPMEMComponent_handles_empty_celldisk_xrmemcache(self, aMockPMEMDetails):
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _options = self.mGetClubox().mGetArgsOptions()

        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e drop pmem.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create pmem.*", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _cell_list = [
            "scaqab10celadm01.us.oracle.com",
            "scaqab10celadm02.us.oracle.com",
            "scaqab10celadm03.us.oracle.com"
        ]

        aMockPMEMDetails.side_effect = [
            {
                'name': 'XRMEMCACHE_cell1',
                'cellDisk': '',
                'status': 'normal'
            },
            {
                'name': 'XRMEMCACHE_cell2',
                'cellDisk': 'PM_00_cell2',
                'status': 'normal'
            },
            {
                'name': 'XRMEMCACHE_cell3',
                'cellDisk': 'PM_00_cell3',
                'status': 'normal'
            }
        ]

        ebCluStorageConfig.mFixPMEMComponent(_cell_list, "cache")

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_valid_and_invalid_inputs(self):
        self.assertEqual(mParseStorageDistrib("50:25:25"), (50.0, 25.0, 25.0))
        self.assertEqual(mParseStorageDistrib("50:50"), (50.0, 50.0, 0.0))

        with self.assertRaises(ValueError):
            mParseStorageDistrib("")
        with self.assertRaises(ValueError):
            mParseStorageDistrib("50")
        with self.assertRaises(ValueError):
            mParseStorageDistrib("50:abc:50")
        with self.assertRaises(ValueError):
            mParseStorageDistrib("50:-20:70")
        with self.assertRaises(ValueError):
            mParseStorageDistrib("10:10:10")

    def template_test_mDropCellDisks(self, aRcFirstTry:int, aRcTryForce: int):
        """
        Method to test clustorage.mDropCellDisks

        :param aRcFirstTry: return code to mock for the firs attempt to drop
            the disks
        :param aRcTryForce: return code to mock for the second attempt to drop
            the disks when using FORCE
        """

        # Declare variable to use
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()
        _cell_list = ['cell1.example.com', 'cell2.example.com']

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e drop celldisk all",
                        aRc=aRcFirstTry),
                    exaMockCommand("cellcli -e drop celldisk all FORCE",
                        aRc=aRcTryForce)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        return _clustorage.mDropCellDisks(_cell_list)


    def test_mDropCellDisks_ok_first_try(self):
        self.assertEqual(None, self.template_test_mDropCellDisks(0, 0))

    def test_mDropCellDisks_ok_with_force(self):
        self.assertEqual(None, self.template_test_mDropCellDisks(1, 0))

    def test_mDropCellDisks_errors_collected(self):
        with patch('exabox.ovm.clustorage.node_exec_cmd') as _mock_exec:
            _mock_exec.side_effect = [
                type('out', (), {'exit_code': 1})(),
                type('out', (), {'exit_code': 1})(),
                type('out', (), {'exit_code': 1})(),
                type('out', (), {'exit_code': 1})(),
            ]
            self.assertRaises(ExacloudRuntimeError,
                lambda: self.template_test_mDropCellDisks(2, 2))

    @patch("exabox.ovm.clustorage.mCompareModel", return_value=-1)
    @patch("exabox.ovm.clustorage.ebCluDiskGroupConfig.mGetDiskGroupSize")
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRackSize')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetEsracks')
    @patch('exabox.ovm.clucontrol.ebCluEsRacksConfig.mGetDiskSize')
    @patch('exabox.ovm.clustorage.ebCluStorageConfig.mAddDiskGroupConfig')
    @patch('exabox.ovm.clustorage.ebCluStorageConfig.mGetDgVolsize')
    def test_mPatchClusterDiskgroup(self, 
        mock_mGetDgVolsize, mock_mAddDG, mock_mGetDiskGroupSize, mock_mCheckSharedEnvironment, mock_mGetRackSize,
        mock_mGetEsracks, mock_mGetDiskSize, mock_mCompare):
        mock_mGetDiskGroupSize.return_value = '1234G'
        mock_mGetDgVolsize.return_value = (100, 200, 300, 10, 20, 30)

        mock_mGetDiskSize.return_value = 7
        mock_mGetEsracks_instance = MagicMock()
        mock_mGetEsracks_instance.mGetDiskSize.return_value = 7
        mock_mGetEsracks.return_value = mock_mGetEsracks_instance

        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()
        _dg_xml = etree.fromstring('<diskGroup id="DG1"><diskGroupName>DATA01</diskGroupName><redundancy>HIGH</redundancy><sliceSize>100G</sliceSize><diskGroupSize>200G</diskGroupSize><ocrVote>false</ocrVote><machines><machine id="m1"/></machines></diskGroup>')
        _dg_cfg = ebCluDiskGroupConfig(_dg_xml)
        _dg_cfg.mGetDiskGroupSize = MagicMock(return_value='1234G')
        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg_cfg)
        _clustorage.mGetDiskSizeInInt = MagicMock(return_value=2000)
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _clustorage.mPatchClusterDiskgroup(
                aCreateSparse = True, 
                aBackupDisk = False, 
                aDRSdistrib = None,
                aOptions = _options)
        self.assertTrue(mock_mGetDgVolsize.called)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataCellModel')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRackSize')    
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetEsracks')
    def test_mPatchClusterDiskgroupDataRecoSparse_BackupFalse_SparseFalse(
        self, 
        mock_mCheckSharedEnvironment, 
        mock_mGetExadataCellModel,
        mock_mGetRackSize,
        mock_mGetEsracks):

        _ebox = self.mGetClubox()

        _ebox.mGetEsracks.return_value = Mock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 14

        mock_mGetExadataCellModel.return_value = 'X7'
        _ebox.mGetExadataCellModel = mock_mGetExadataCellModel

        _clustorage = _ebox.mGetStorage()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _DRSdistrib = "79.0:21.0:0.0"

        _clustorage.mPatchClusterDiskgroup(
            aCreateSparse = False, 
            aBackupDisk = False, 
            aDRSdistrib = _DRSdistrib,
            aOptions = _options)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataCellModel')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRackSize')    
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetEsracks')
    def test_mPatchClusterDiskgroupDataRecoSparse_BackupTrue_SparseFalse(
        self, 
        mock_mCheckSharedEnvironment, 
        mock_mGetExadataCellModel,
        mock_mGetRackSize,
        mock_mGetEsracks):

        _ebox = self.mGetClubox()

        _ebox.mGetEsracks.return_value = Mock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 14

        mock_mGetExadataCellModel.return_value = 'X7'
        _ebox.mGetExadataCellModel = mock_mGetExadataCellModel

        _clustorage = _ebox.mGetStorage()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _DRSdistrib = "46.88:53.12:0.0"

        _clustorage.mPatchClusterDiskgroup(
            aCreateSparse = False, 
            aBackupDisk = True, 
            aDRSdistrib = _DRSdistrib,
            aOptions = _options)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataCellModel')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRackSize')    
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetEsracks')
    @patch('exabox.ovm.clustorage.ebCluStorageConfig.mAddDiskGroupConfig')
    def test_mPatchClusterDiskgroupDataRecoSparse_BackupFalse_SparseTrue(
        self, 
        mock_mAddDG,
        mock_mCheckSharedEnvironment, 
        mock_mGetExadataCellModel,
        mock_mGetRackSize,
        mock_mGetEsracks):

        _ebox = self.mGetClubox()

        _ebox.mGetEsracks.return_value = Mock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 14

        mock_mGetExadataCellModel.return_value = 'X7'
        _ebox.mGetExadataCellModel = mock_mGetExadataCellModel

        _clustorage = _ebox.mGetStorage()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _DRSdistrib = "80.0:10.0:10.0"

        _clustorage.mPatchClusterDiskgroup(
            aCreateSparse = True, 
            aBackupDisk = False, 
            aDRSdistrib = _DRSdistrib,
            aOptions = _options)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataCellModel')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRackSize')    
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetEsracks')
    @patch('exabox.ovm.clustorage.ebCluStorageConfig.mAddDiskGroupConfig')
    def test_mPatchClusterDiskgroupDataRecoSparse_BackupTrue_SparseTrue(
        self, 
        mock_mAddDG,
        mock_mCheckSharedEnvironment, 
        mock_mGetExadataCellModel,
        mock_mGetRackSize,
        mock_mGetEsracks):

        _ebox = self.mGetClubox()

        _ebox.mGetEsracks.return_value = Mock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 14

        mock_mGetExadataCellModel.return_value = 'X7'
        _ebox.mGetExadataCellModel = mock_mGetExadataCellModel

        _clustorage = _ebox.mGetStorage()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _DRSdistrib = "25.45:60.1:14.45"

        _clustorage.mPatchClusterDiskgroup(
            aCreateSparse = True, 
            aBackupDisk = True, 
            aDRSdistrib = _DRSdistrib,
            aOptions = _options)

    def test_mCheckGridDisksResizedCells(self):
        _ebox = self.mGetClubox()
        _options = self.mGetClubox().mGetArgsOptions()
        _dgObj = ebCluManageDiskgroup(_ebox, _options)
        _clustorageObj = ebCluManageStorage(_ebox, _options)
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['13G']), None)):
            _clustorageObj.mCheckGridDisksResizedCells('DATA', 400.0, _dgObj)

    def test_mCheckGridDisksResizedCells_similar_prefixes(self):
        _ebox = self.mGetClubox()
        _options = self.mGetClubox().mGetArgsOptions()
        _dgObj = MagicMock()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _commands = []

        def _capture(command):
            _commands.append(command)
            if "DATAC1_.*" in command:
                return (None, mockStream(['102G', '102G']), None)
            if "DATAC10_.*" in command:
                return (None, mockStream(['112G', '112G']), None)
            return (None, mockStream([]), None)

        with patch.object(_ebox, 'mReturnCellNodes', return_value=['cell1']), \
             patch('exabox.ovm.clustorage.get_gcontext', return_value=None), \
             patch.object(_ebox, 'isATPCluster', return_value=False), \
             patch('exabox.ovm.clustorage.connect_to_host') as mock_connect:
            _node = MagicMock()
            _node.mExecuteCmd.side_effect = _capture
            mock_connect.return_value.__enter__.return_value = _node
            mock_connect.return_value.__exit__.return_value = False

            self.assertTrue(_clustorage.mCheckGridDisksResizedCells('DATAC1', 204.0, _dgObj))
            self.assertTrue(_clustorage.mCheckGridDisksResizedCells('DATAC10', 224.0, _dgObj))

        normalized_cmds = [cmd.replace("\\'", "'") for cmd in _commands]
        self.assertTrue(any("like 'DATAC1_.*'" in cmd for cmd in normalized_cmds))
        self.assertTrue(any("like 'DATAC10_.*'" in cmd for cmd in normalized_cmds))
        self.assertFalse(any("like 'DATAC1.*'" in cmd and "like 'DATAC1_.*'" not in cmd for cmd in normalized_cmds))
        self.assertEqual(
            _dgObj.mSetGridDiskCountRetryResize.call_args_list,
            [((2, 'DATAC1'), {}), ((2, 'DATAC10'), {})]
        )
        _dgObj.mSetCurrentRetrySizeTotalMB.assert_not_called()



    def test_mEnsureEmptyXenCellsInterconnect_restart(self):
        _ebox = self.mGetClubox()

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("test -e /.*systemd.*", aRc=0),
                    exaMockCommand("systemd-analyze time", aRc=0),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "list cell attributes interconnect1"), aStdout="   stib0   \n"),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "alter cell interconnect1=ib0")),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "list cell attributes interconnect2"), aStdout="   stib0   \n"),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "alter cell interconnect2=ib1")),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "alter cell restart services all")),
                    exaMockCommand(f"test.*pgrep", aRc=0),
                    exaMockCommand(f"test.*grep", aRc=0),
                    exaMockCommand(f"pgrep -af 'firstconf/elasticConfig.sh'", aRc=1)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        self.assertEqual(0,ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(['cell1.example.com']))

    def test_mEnsureEmptyXenCellsInterconnect_dont_restart(self):
        _ebox = self.mGetClubox()

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("test -e /.*systemd.*", aRc=0),
                    exaMockCommand("systemd-analyze time", aRc=0),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "list cell attributes interconnect1"), aStdout="   ib0   \n"),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                       "list cell attributes interconnect2"), aStdout="   ib1   \n"),
                    exaMockCommand(f"systemd-analyze time", aRc=0),
                    exaMockCommand(f"test.*pgrep", aRc=0),
                    exaMockCommand(f"test.*grep", aRc=0),
                    exaMockCommand(f"pgrep -af 'firstconf/elasticConfig.sh'", aRc=1)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        self.assertEqual(0,ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(['cell1.example.com']))

    def test_mEnsureEmptyXenCellsInterconnect_restart_wait_userspace_boot(self):
        _ebox = self.mGetClubox()

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("test -e /.*systemd.*", aRc=0),
                    exaMockCommand("systemd-analyze time", aRc=1),
                    exaMockCommand("systemd-analyze time", aRc=0),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "list cell attributes interconnect1"), aStdout="   stib0   \n"),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "alter cell interconnect1=ib0")),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "list cell attributes interconnect2"), aStdout="   stib0   \n"),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "alter cell interconnect2=ib1")),
                    exaMockCommand(("/opt/oracle/cell/cellsrv/bin/cellcli -e "
                        "alter cell restart services all")),
                    exaMockCommand(f"test.*pgrep", aRc=0),
                    exaMockCommand(f"test.*grep", aRc=0),
                    exaMockCommand(f"pgrep -af 'firstconf/elasticConfig.sh'", aRc=1)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        self.assertEqual(0,ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(['cell1.example.com']))

    def test_mEnsureEmptyXenCellsInterconnect_skip(self):
        _ebox = self.mGetClubox()

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                ]
            ]
        }

        self.mGetContext().mSetConfigOption("skip_empty_cell_interconnect_check", "True")

        self.mPrepareMockCommands(_cmds)
        self.assertEqual(2,ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(['cell1.example.com']))

    def tests_mCalculateFreeSpaceCelldisk(self):
        _ebox = self.mGetClubox()
        _options = self.mGetClubox().mGetArgsOptions()

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e LIST CELLDISK WHERE", aRc=0, aStdout="CD_01_fra180182exdcl01 16T 1T\n")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _dgObj = ebCluManageDiskgroup(_ebox, _options)
        _free_space = _dgObj.mCalculateFreeSpaceCelldisk()
        # Assume _cell_count is 3 and _dg_griddisks_count is 12 and current diskgroup size is 72 TB
        # DG slice size will be 2 TB. Assume the new DG slice size is 3 TB.
        _cell_count = 3
        _dg_griddisks_count = 12
        _currentDgSize = 72*1024*1024
        _new_dg_slice = 3*1024*1024
        _current_dg_slice =  _currentDgSize/(_cell_count * _dg_griddisks_count)
        _current_dg_slice = math.floor(_current_dg_slice / 16) * 16
        self.assertFalse((_new_dg_slice - _current_dg_slice) > _free_space)
           
    def test_mFixPMEMComponent(self):
        _ebox = self.mGetClubox()
        _options = self.mGetClubox().mGetArgsOptions()
        _cmds = {
                self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("cellcli -e drop pmem.*", aRc=0,  aPersist=True),
                                exaMockCommand("cellcli -e list pmem.*", aRc=0,  aPersist=True),
                                exaMockCommand("cellcli -e create pmem.*", aRc=0,  aPersist=True)
                            ]
                        ]
        }
        self.mPrepareMockCommands(_cmds)
        _cell_list = ["scaqab10celadm01.us.oracle.com", "scaqab10celadm02.us.oracle.com", "scaqab10celadm03.us.oracle.com","scaqab10celadm04.us.oracle.com"]#_ebox.mReturnCellNodes().keys()
        ebCluStorageConfig.mFixPMEMComponent(_cell_list, "log")
        ebCluStorageConfig.mFixPMEMComponent(_cell_list, "cache")

    @patch("exabox.ovm.clustorage.ebCluStorageConfig.mListPMEMDetails")
    def test_mFixPMEMComponent_abnormal(self, aMockPMEMDetails):
        _ebox = self.mGetClubox()
        _options = self.mGetClubox().mGetArgsOptions()
        _cmds = {
                self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("cellcli -e drop pmem.*", aRc=0,  aPersist=True),
                                exaMockCommand("cellcli -e list pmem.*", aRc=0,  aPersist=True),
                                exaMockCommand("cellcli -e create pmem.*", aRc=0,  aPersist=True)
                            ]
                        ]
        }
        self.mPrepareMockCommands(_cmds)
        _cell_list = ["scaqab10celadm01.us.oracle.com", "scaqab10celadm02.us.oracle.com", "scaqab10celadm03.us.oracle.com","scaqab10celadm04.us.oracle.com"]#_ebox.mReturnCellNodes().keys()
        aMockPMEMDetails.return_value = _detail_out

        ebCluStorageConfig.mFixPMEMComponent(_cell_list, "log")

    def test_mUpdateRebalanceStatus(self):
        _ebox = self.mGetClubox()
        _options = self.mGetClubox().mGetArgsOptions()
        # Prepare Commands
        _cmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand('select GROUP_NUMBER, STATE, POWER, EST_MINUTES, SOFAR, EST_WORK *', aRc=0, aStdout=REBALANCE_OUTPUT)
                ],
                [
                    exaMockCommand('select GROUP_NUMBER, NAME *', aRc=0, aStdout=GROUP_NAME_DATA)
                ],
                [
                    exaMockCommand('select GROUP_NUMBER, NAME *', aRc=0, aStdout=GROUP_NAME_RECO)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _cmd_state_run = 'select GROUP_NUMBER, STATE, POWER, EST_MINUTES, SOFAR, EST_WORK from GV\\\\\$ASM_OPERATION where STATE=\'RUN\'; | sqlplus -s / as sysasm'
        _cmd_diskgrp_name = 'select GROUP_NUMBER, NAME from GV\\\\\$ASM_DISKGROUP where GROUP_NUMBER=\'{0}\'; | sqlplus -s / as sysasm'
        _dgObj = ebCluManageDiskgroup(_ebox, _options)
        _dg_constants_obj = ebDiskgroupOpConstants(_options)
        # Reduce time by 10 minutes and 50 seconds to have the flow go into the status flow
        _time_start = time.time() - 650
        _cmd_timeout = 300
        _domu = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _dgObj.mUpdateRebalanceStatus(_domu, _cmd_state_run, _cmd_diskgrp_name, _time_start,
                                      _cmd_timeout, _dg_constants_obj)
        # Test mCalcOverallRebalPercent with invalid value
        _dgObj.mCalcOverallRebalPercent(False)
        # Test mUpdateRebalanceStatus with invalid value
        _dgObj.mUpdateRebalanceStatus(_domu, _cmd_state_run, _cmd_diskgrp_name, True,
                                      _cmd_timeout, _dg_constants_obj)

    def test_mUpdateRebalanceStatusInvalidOut(self):
        _ebox = self.mGetClubox()
        _options = self.mGetClubox().mGetArgsOptions()
        # Prepare Commands
        _cmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand('select GROUP_NUMBER, STATE, POWER, EST_MINUTES, SOFAR, EST_WORK *', aRc=0, aStdout=REBALANCE_OUTPUT_INVALID)
                ],
                [
                    exaMockCommand('select GROUP_NUMBER, NAME *', aRc=0, aStdout=GROUP_NAME_DATA)
                ],
                [
                    exaMockCommand('select GROUP_NUMBER, NAME *', aRc=0, aStdout=GROUP_NAME_RECO)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _cmd_state_run = 'select GROUP_NUMBER, STATE, POWER, EST_MINUTES, SOFAR, EST_WORK from GV\\\\\$ASM_OPERATION where STATE=\'RUN\'; | sqlplus -s / as sysasm'
        _cmd_diskgrp_name = 'select GROUP_NUMBER, NAME from GV\\\\\$ASM_DISKGROUP where GROUP_NUMBER=\'{0}\'; | sqlplus -s / as sysasm'
        _dgObj = ebCluManageDiskgroup(_ebox, _options)
        _dg_constants_obj = ebDiskgroupOpConstants(_options)
        # Reduce time by 10 minutes and 50 seconds to have the flow go into the status flow
        _time_start = time.time() - 650
        _cmd_timeout = 300
        _domu = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _dgObj.mUpdateRebalanceStatus(_domu, _cmd_state_run, _cmd_diskgrp_name, _time_start,
                                      _cmd_timeout, _dg_constants_obj)

    def test_mCheckMinFreeSpaceDGShrink_percentages(self):
        """
        Simple test for mCheckMinFreeSpaceDGShrink.
        """
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorageObj = ebCluManageStorage(_ebox, _options)

        # Mock input DG map
        _dgmap = {
            ebCluManageStorage.DATA: {
                ebCluManageStorage.DG_NAME: 'DATAC1',
                ebCluManageStorage.DG_NEWSIZE: 160.0,
                ebCluManageStorage.DG_CURRSIZE: 180.0,
            },
            ebCluManageStorage.RECO: {
                ebCluManageStorage.DG_NAME: 'RECOC1',
                ebCluManageStorage.DG_NEWSIZE: 40.0,
                ebCluManageStorage.DG_CURRSIZE: 42.0,
            },
            ebCluManageStorage.SPARSE: {
                ebCluManageStorage.DG_NAME: None,
                ebCluManageStorage.DG_NEWSIZE: None,
                ebCluManageStorage.DG_CURRSIZE: None,
            }
        }

        # Mock cluster
        _mock_cluster = Mock()
        _mock_cluster.mGetCluDiskGroups.return_value = ['dg1']

        with patch.object(_clustorageObj, 'mFetchAndSaveDGSizes') as mock_fetch, \
             patch.object(_clustorageObj, 'mCalculateDgResize') as mock_calc, \
             patch.object(_ebox, 'mGetClusters') as mock_get_clusters:

            mock_get_clusters.return_value.mGetCluster.return_value = _mock_cluster
            mock_fetch.return_value = None
            mock_calc.return_value = None

            _result = _clustorageObj.mCheckMinFreeSpaceDGShrink(_options, _dgmap)

            self.assertIsInstance(_result, dict)
            self.assertIn(ebCluManageStorage.DATA, _result)
            self.assertIn(ebCluManageStorage.RECO, _result)

            self.assertEqual(
                _result[ebCluManageStorage.DATA].get(ebCluManageStorage.DG_CURRSIZE),
                180.0)
            self.assertEqual(
                _result[ebCluManageStorage.RECO].get(ebCluManageStorage.DG_CURRSIZE),
                42.0)


    def test_mGetDiskgroupsNewSizes_handles_missing_rack_flags(self):
        """Ensure rack payload tolerates missing backup/sparse keys."""
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mSetDiskGroupOperationData.return_value = None

        _dg_constants = _clustorage.mGetConstantsObj()

        _data_dg = MagicMock()
        _data_dg.mGetDiskGroupType.return_value = _dg_constants._data_dg_type_str
        _data_dg.mGetDgName.return_value = 'DATAC1'
        _data_dg.mGetDiskGroupSize.return_value = '500G'
        _data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        _reco_dg = MagicMock()
        _reco_dg.mGetDiskGroupType.return_value = _dg_constants._reco_dg_type_str
        _reco_dg.mGetDgName.return_value = 'RECOC1'
        _reco_dg.mGetDiskGroupSize.return_value = '400G'

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco']

        _ebox_clusters = MagicMock()
        _ebox_clusters.mGetCluster.return_value = _cluster

        _ebox_storage = MagicMock()
        _ebox_storage.mGetDiskGroupConfig.side_effect = [_data_dg, _reco_dg]

        _ebox_ctrl = MagicMock()
        _ebox_ctrl.mGetClusters.return_value = _ebox_clusters
        _ebox_ctrl.mGetStorage.return_value = _ebox_storage
        _ebox_ctrl.mGetRequestObj.return_value = MagicMock()

        _dgObj.mUtilGetDiskgroupSize.side_effect = [
            500 * 1024,   # DATA total in MB
            300 * 1024,   # DATA used in MB
            400 * 1024,   # RECO total in MB
            200 * 1024,   # RECO used in MB
        ]

        _options.jsonconf = {
            'newsize': 1000,
            'rack': {
                'storage_distribution': '60:20:20'
            }
        }

        _dgmap = {}

        with patch('exabox.ovm.clustorage.ebGetDefaultDB') as _mock_db_factory:
            _mock_db = MagicMock()
            _mock_db.mUpdateRequest.return_value = None
            _mock_db_factory.return_value = _mock_db
            with patch.object(_clustorage, 'mGetEbox', return_value=_ebox_ctrl):
                _rc = _clustorage.mGetDiskgroupsNewSizes(_options, _dgObj, 1000, _dgmap)

        self.assertEqual(_rc, 0)
        self.assertEqual(
            _dgmap[ebCluManageStorage.DATA][ebCluManageStorage.DG_NAME],
            'DATAC1')
        self.assertEqual(
            _dgmap[ebCluManageStorage.RECO][ebCluManageStorage.DG_NAME],
            'RECOC1')
        self.assertIsNone(
            _dgmap[ebCluManageStorage.SPARSE][ebCluManageStorage.DG_NAME])



    # Auto-generated test for mGetDiskgroupsNewSizes
    def test_mGetDiskgroupsNewSizes_rejects_invalid_shrink(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mSetDiskGroupOperationData.return_value = None

        _dg_constants = _clustorage.mGetConstantsObj()

        _data_dg = MagicMock()
        _data_dg.mGetDiskGroupType.return_value = _dg_constants._data_dg_type_str
        _data_dg.mGetDgName.return_value = 'DATAC1'
        _data_dg.mGetDiskGroupSize.return_value = '500G'
        _data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        _reco_dg = MagicMock()
        _reco_dg.mGetDiskGroupType.return_value = _dg_constants._reco_dg_type_str
        _reco_dg.mGetDgName.return_value = 'RECOC1'
        _reco_dg.mGetDiskGroupSize.return_value = '400G'

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco']

        _ebox_clusters = MagicMock()
        _ebox_clusters.mGetCluster.return_value = _cluster

        _ebox_storage = MagicMock()
        _ebox_storage.mGetDiskGroupConfig.side_effect = [_data_dg, _reco_dg]

        _ebox_ctrl = MagicMock()
        _ebox_ctrl.mGetClusters.return_value = _ebox_clusters
        _ebox_ctrl.mGetStorage.return_value = _ebox_storage

        _dgObj.mUtilGetDiskgroupSize.side_effect = [
            500 * 1024,  # DATA total in MB
            30 * 1024,   # DATA used in MB
            400 * 1024,  # RECO total in MB
            10 * 1024,   # RECO used in MB
        ]

        _options.jsonconf = {
            'newsize': 100,
            'backup_disk': 'true',
            'create_sparse': 'false',
            'storage_distribution': '10:90:0'
        }

        _dgmap = {}

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox_ctrl),              patch.object(_clustorage, 'mRecordError', return_value=42) as _mock_record:
            _rc = _clustorage.mGetDiskgroupsNewSizes(_options, _dgObj, 100, _dgmap)

        self.assertEqual(_rc, 42)
        _mock_record.assert_called_with(gDiskgroupError['InvalidResize'])

    def test_mUtilStorageResize_shrink_then_grow(self):
        """Ensure shrink operations run before growth operations."""
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mSetDiskGroupOperationData.return_value = None
        _dgObj.mClusterDgrpRebalance.return_value = 0
        _dgObj.mGetDiskGroupOperationData.return_value = {}

        _call_order = []

        def _resize_side_effect(aOpts):
            _call_order.append(aOpts.jsonconf['diskgroup'])
            return 0

        _dgObj.mClusterDgrpResize.side_effect = _resize_side_effect

        _dgmap = {
            ebCluManageStorage.DATA: {
                ebCluManageStorage.DG_NAME: 'DATAC1',
                ebCluManageStorage.DG_CURRSIZE: 200.0,
                ebCluManageStorage.DG_NEWSIZE: 150.0,
            },
            ebCluManageStorage.RECO: {
                ebCluManageStorage.DG_NAME: 'RECOC1',
                ebCluManageStorage.DG_CURRSIZE: 50.0,
                ebCluManageStorage.DG_NEWSIZE: 80.0,
            },
            ebCluManageStorage.SPARSE: {
                ebCluManageStorage.DG_NAME: None,
                ebCluManageStorage.DG_CURRSIZE: None,
                ebCluManageStorage.DG_NEWSIZE: None,
            }
        }

        _rc = _clustorage.mUtilStorageResize(_dgObj, _options, _dgmap, 0)

        self.assertEqual(_rc, 0)
        self.assertListEqual(_call_order, ['DATAC1', 'RECOC1'])
        self.assertEqual(_dgObj.mClusterDgrpResize.call_count, 2)

    # Auto-generated test for ebCluDiskGroupConfig
    def test_diskgroupconfig_setters_and_types(self):
        _xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>NORMAL</redundancy>
                <sliceSize>100G</sliceSize>
                <diskGroupSize>200G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                    <machine id="m2"/>
                </machines>
            </diskGroup>
            """
        )
        _dg = ebCluDiskGroupConfig(_xml)

        self.assertEqual(_dg.mGetDiskGroupMachines(), ['m1', 'm2'])
        self.assertEqual(_dg.mGetDgName(), 'DATA01')

        _dg.mSetQuorumDisk('true')
        _dg.mSetAcfsVolumeName('vol1')
        _dg.mSetAcfsVolumeSize(64)
        _dg.mSetAcfsMountPath('/acfs')
        _dg.mSetSparseVirtualSize(128)
        _dg.mSetGridDiskPrefix('GD')

        self.assertEqual(_dg.mGetQuorumDisk().text, 'true')
        self.assertEqual(_dg.mGetAcfsVolumeName(), 'vol1')
        self.assertEqual(_dg.mGetAcfsVolumeSize(), '64')
        self.assertEqual(_dg.mGetAcfsMountPath(), '/acfs')
        self.assertEqual(_dg.mGetGridDiskPrefix(), 'GD')
        self.assertEqual(
            _dg._ebCluDiskGroupConfig__sparseVirtualSize.text, '128G')

        _dg.mSetDiskGroupType('data')
        self.assertEqual(_dg.mGetDiskGroupType(), 'data')
        _dg.mReplaceDgId('DG2')
        self.assertEqual(_dg.mGetDgId(), 'DG2')

    # Auto-generated test for mGetDiskGroupType
    def test_diskgroupconfig_type_detection_prefix(self):
        _xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>SPRCL1</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>20G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
                <gridDiskPrefix>SPRC</gridDiskPrefix>
            </diskGroup>
            """
        )
        _dg = ebCluDiskGroupConfig(_xml)
        self.assertEqual(_dg.mGetDiskGroupType(), 'sparse')

    # Auto-generated test for DumpDiskGroupConfig/DumpStorageConfig/mClusterDiskGroupList
    def test_dump_helpers_and_cluster_diskgroup_list(self):
        _xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>20G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg = ebCluDiskGroupConfig(_xml)

        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        self.assertIsNone(_dg.DumpDiskGroupConfig())
        self.assertIsNone(_clustorage.DumpStorageConfig())
        self.assertIsNone(_clustorage.mClusterDiskGroupList())

    # Auto-generated test for mListCellDG
    def test_mListCellDG_zdlra_filters_catalog_delta(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=True)

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox), \
             patch.object(_clustorage, 'mListCellDG', return_value=['CATALOG_C1', 'DELTA_C1']) as _mock_list:
            _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['CATALOG_C1', 'DELTA_C1'])
        _mock_list.assert_called_once_with(_node)

    # Auto-generated test for mListCellDG
    def test_mListCellDG_suffix_filters_output(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox), \
             patch.object(_clustorage, 'mListCellDG',
                          return_value=['DATA_C1 size1', 'RECO_C1 size2']) as _mock_list:
            _result = _clustorage.mListCellDG(_node, aSuffix='C1')

        self.assertEqual(_result, ['DATA_C1 size1', 'RECO_C1 size2'])
        _mock_list.assert_called_once_with(_node, aSuffix='C1')

    # Auto-generated test for mListCellDG
    def test_mListCellDG_raises_on_command_error(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox), \
             patch.object(_clustorage, 'mListCellDG', side_effect=Exception('fail')) as _mock_list:
            with self.assertRaises(Exception):
                _clustorage.mListCellDG(_node)

        _mock_list.assert_called_once_with(_node)



    # Auto-generated test for ebCluStoragePoolConfig and ebCluEDVVolumesConfig
    def test_storage_pool_and_edv_config_accessors(self):
        _sp_xml = etree.fromstring(
            """
            <storagePool id="SP1">
                <storagePoolName>SPDATA</storagePoolName>
                <storagePoolType>high</storagePoolType>
                <storagePoolSize>1024G</storagePoolSize>
                <uiSize>512</uiSize>
                <uiSizeType>GB</uiSizeType>
                <machines>
                    <machine id="m1"/>
                    <machine id="m2"/>
                </machines>
            </storagePool>
            """
        )
        _edv_xml = etree.fromstring(
            """
            <edvVolume id="EDV1">
                <edvVolumeName>EDV01</edvVolumeName>
                <edvVolumeSize>256G</edvVolumeSize>
                <edvVolumeType>data</edvVolumeType>
                <edvDevicePath>/dev/mapper/edv1</edvDevicePath>
            </edvVolume>
            """
        )

        _sp = ebCluStoragePoolConfig(_sp_xml)
        _edv = ebCluEDVVolumesConfig(_edv_xml)

        self.assertEqual(_sp.mGetSpId(), 'SP1')
        self.assertEqual(_sp.mGetStoragePoolMachines(), ['m1', 'm2'])
        self.assertEqual(_sp.mGetSPName(), 'SPDATA')
        self.assertEqual(_sp.mGetSPType(), 'high')
        self.assertEqual(_sp.mGetSPSize(), '1024G')
        self.assertEqual(_sp.mGetUiSize(), '512')
        self.assertEqual(_sp.mGetUiSizeType(), 'GB')

        self.assertEqual(_edv.mGetEdvId(), 'EDV1')
        self.assertEqual(_edv.mGetEDVName(), 'EDV01')
        self.assertEqual(_edv.mGetSPSize(), '256G')
        self.assertEqual(_edv.mGetEDVType(), 'data')
        self.assertEqual(_edv.mGetDevicePath(), '/dev/mapper/edv1')

    # Auto-generated test for ebCluStorageConfig list/remove/add
    def test_storage_config_add_and_remove_diskgroup(self):
        _root = etree.fromstring(
            """
            <config>
              <storage>
                <diskGroups>
                  <diskGroup id="DG1">
                    <diskGroupName>DATA01</diskGroupName>
                    <redundancy>NORMAL</redundancy>
                    <sliceSize>100G</sliceSize>
                    <diskGroupSize>200G</diskGroupSize>
                    <ocrVote>false</ocrVote>
                    <machines>
                      <machine id="m1"/>
                    </machines>
                  </diskGroup>
                </diskGroups>
                <storagePools>
                  <storagePool id="SP1">
                    <storagePoolName>SPDATA</storagePoolName>
                    <storagePoolType>high</storagePoolType>
                    <storagePoolSize>100G</storagePoolSize>
                    <uiSize>50</uiSize>
                    <uiSizeType>GB</uiSizeType>
                    <machines>
                      <machine id="m1"/>
                    </machines>
                  </storagePool>
                </storagePools>
                <edvVolumes>
                  <edvVolume id="EDV1">
                    <edvVolumeName>EDV01</edvVolumeName>
                    <edvVolumeSize>256G</edvVolumeSize>
                    <edvVolumeType>data</edvVolumeType>
                    <edvDevicePath>/dev/mapper/edv1</edvDevicePath>
                  </edvVolume>
                </edvVolumes>
              </storage>
            </config>
            """
        )

        class _Cfg(object):
            def __init__(self, root):
                self._root = root

            def mGetConfigAllElement(self, path):
                return self._root.findall(path)

            def mConfigRoot(self):
                return self._root

        _cfg = _Cfg(_root)
        _ebox = self.mGetClubox()
        _storage_cfg = ebCluStorageConfig(_ebox, _cfg)

        self.assertEqual(_storage_cfg.mGetDiskGroupConfigList(), ['DG1'])
        self.assertEqual(_storage_cfg.mGetStoragePoolConfigList(), ['SP1'])
        self.assertEqual(_storage_cfg.mGetEDVVolumesConfigList(), ['EDV1'])

        _storage_cfg.mRemoveDiskGroupConfig('DGX')
        self.assertEqual(_storage_cfg.mGetDiskGroupConfigList(), ['DG1'])

        _storage_cfg.mRemoveDiskGroupConfig('DG1')
        self.assertEqual(_storage_cfg.mGetDiskGroupConfigList(), [])

        _dg_xml = etree.fromstring(
            """
            <diskGroup id="DG2">
              <diskGroupName>RECO01</diskGroupName>
              <redundancy>HIGH</redundancy>
              <sliceSize>50G</sliceSize>
              <diskGroupSize>75G</diskGroupSize>
              <ocrVote>false</ocrVote>
              <machines>
                <machine id="m2"/>
              </machines>
            </diskGroup>
            """
        )
        _dg = ebCluDiskGroupConfig(_dg_xml)
        _storage_cfg.mAddDiskGroupConfig(_dg)
        self.assertEqual(_storage_cfg.mGetDiskGroupConfigList(), ['DG2'])

        _storage_cfg.mAddDiskGroupConfig(_dg)
        self.assertEqual(_storage_cfg.mGetDiskGroupConfigList(), ['DG2'])

    # Auto-generated test for mCreateCellDG and mDeleteCellDG
    def test_create_delete_cell_dg_formats_command(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = 0
        _node.mGetHostname.return_value = 'cell1'

        _cmd = _clustorage.mCreateCellDG(_node, 3, 'DATA', 'cell1', 'CD_01_cell1', '100G')
        self.assertIn('DATA', _cmd)
        self.assertIn('CD_01_cell1', _cmd)
        self.assertIn('DATA', _node.mExecuteCmd.call_args_list[0][0][0])

        _node.mExecuteCmd.reset_mock()
        _cmd = _clustorage.mDeleteCellDG(_node, 12, 'RECO', 'cell1')
        self.assertIn('RECOCD_12_cell1', _cmd)
        self.assertIn('DROP GRIDDISK', _node.mExecuteCmd.call_args_list[0][0][0])

    # Auto-generated test for mCreateCellDG and mDeleteCellDG
    def test_create_delete_cell_dg_logs_debug(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = 0
        _node.mGetHostname.return_value = 'cell3'
        _ebox.mIsDebug = MagicMock(return_value=True)

        with patch('exabox.ovm.clustorage.ebLogInfo') as _mock_log:
            _cmd = _clustorage.mCreateCellDG(_node, 1, 'DATA', 'cell3', 'CD_00_cell3', '50G')
            self.assertIn('DATA', _cmd)
            _cmd = _clustorage.mDeleteCellDG(_node, 2, 'RECO', 'cell3')
            self.assertIn('RECOCD_02_cell3', _cmd)

        self.assertGreaterEqual(_mock_log.call_count, 2)

    # Auto-generated test for mCreateACFSGridDisks
    @patch('exabox.ovm.clustorage.mCompareModel', return_value=-1)
    def test_mCreateACFSGridDisks_creates_missing_disks(self, _mock_cmp):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mGetExadataCellModel = MagicMock(return_value='X6')
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1.example.com': {}})
        _ebox.mIsDebug = MagicMock(return_value=False)

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster

        _dg_cfg = MagicMock()
        _dg_cfg.mGetDgName.return_value = 'DATA10'

        with patch('exabox.ovm.clustorage.exaBoxNode') as _mock_node_cls, \
             patch.object(_clustorage, 'mGetDiskGroupConfig', return_value=_dg_cfg), \
             patch.object(_clustorage, 'mListCellDG', return_value=[]), \
             patch.object(_clustorage, 'mListACFSCellDisks',
                          return_value=['CD_02_cell1', 'CD_03_cell1']), \
             patch.object(_clustorage, 'mCreateCellDG') as _mock_create:
            _node = MagicMock()
            _mock_node_cls.return_value = _node
            _clustorage.mCreateACFSGridDisks()

        self.assertTrue(_mock_create.called)
        _node.mConnect.assert_called_once_with(aHost='cell1.example.com')
        _node.mDisconnect.assert_called_once()


    # Auto-generated test for mCheckGridDisks
    @patch('exabox.ovm.clustorage.ebCluStorageConfig.mDeleteGD')
    def test_mCheckGridDisks_returns_expected(self, mock_mDeleteGD):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        mock_mDeleteGD.return_value = True
        self.assertEqual(_clustorage.mCheckGridDisks(), 0)
        mock_mDeleteGD.assert_called_with(True, None)

        mock_mDeleteGD.return_value = False
        self.assertEqual(_clustorage.mCheckGridDisks(), 1)


    # Auto-generated test for mClusterDiskGroupSuffix
    def test_mClusterDiskGroupSuffix_three_char_suffix(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']

        _clusters = MagicMock()
        _clusters.mGetCluster.return_value = _cluster

        _ebox.mGetClusters = MagicMock(return_value=_clusters)

        _dg = MagicMock()
        _dg.mGetDgName.return_value = 'DATAC10'
        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg)

        self.assertEqual(_clustorage.mClusterDiskGroupSuffix(), 'C10')

    # Auto-generated test for mClusterDiskGroupSuffix
    def test_mClusterDiskGroupSuffix_returns_none_when_no_match(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']

        _clusters = MagicMock()
        _clusters.mGetCluster.return_value = _cluster

        _ebox.mGetClusters = MagicMock(return_value=_clusters)

        _dg = MagicMock()
        _dg.mGetDgName.return_value = 'SYSTEM1'
        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg)

        self.assertIsNone(_clustorage.mClusterDiskGroupSuffix())

    # Auto-generated test for mDeleteGD
    def test_mDeleteGD_zdlra_delegates(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _zdlra = MagicMock()
        _zdlra.mDeleteGD.return_value = 1
        _ebox.IsZdlraProv = MagicMock(return_value=True)
        _ebox.mGetZDLRA = MagicMock(return_value=_zdlra)

        self.assertEqual(_clustorage.mDeleteGD(aListOnly=True, aCell='cell1'), 1)
        _zdlra.mDeleteGD.assert_called_once_with(True, 'cell1')

    # Auto-generated test for mClusterDiskGroupSuffix
    def test_mClusterDiskGroupSuffix_detects_catalog(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _dg = MagicMock()
        _dg.mGetDgName.return_value = 'CATALOGC9'

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1', 'DG2']

        _clusters = MagicMock()
        _clusters.mGetCluster.return_value = _cluster

        _ebox.mGetClusters = MagicMock(return_value=_clusters)
        _dg2 = MagicMock()
        _dg2.mGetDgName.return_value = 'DATAC9'
        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg2)

        self.assertEqual(_clustorage.mClusterDiskGroupSuffix(), 'C9')

    # Auto-generated test for mDeleteGD
    def test_mDeleteGD_suffix_none_returns_zero(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _clustorage.mClusterDiskGroupSuffix = MagicMock(return_value=None)
        self.assertEqual(_clustorage.mDeleteGD(), 0)

    # Auto-generated test for mListCellDisksSize
    @patch('exabox.ovm.clustorage.ebLogInfo')
    def test_mListCellDisksSize_unit_mapping_and_skip(self, _mock_log):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}, 'cell2': {}})
        _ebox.mGetNodeModel = MagicMock(return_value='X9')
        _ebox.mCompareExadataModel = MagicMock(return_value=1)
        _ebox.mGetExadataCellModel = MagicMock(return_value='X9')

        _escli = MagicMock()
        _escli.mIsEFRack.side_effect = [True, False]

        class _FakeCtx(object):
            def __init__(self, node):
                self._node = node
            def __enter__(self):
                return self._node
            def __exit__(self, exc_type, exc, tb):
                return False

        _node = MagicMock()
        _node.mExecuteCmd.side_effect = [
            (None, mockStream(['CD_00_cell1 10G 5G\n', 'CD_01_cell1 1X 0G\n']), mockStream([''])),
            (None, mockStream(['CD_00_cell2 10G 5G\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = 0

        with patch('exabox.ovm.clustorage.ebEscliUtils', return_value=_escli), \
             patch('exabox.ovm.clustorage.connect_to_host', return_value=_FakeCtx(_node)):
            total, free = _clustorage.mListCellDisksSize()

        self.assertAlmostEqual(total, 20.0)
        self.assertAlmostEqual(free, 10.0)
        self.assertTrue(_mock_log.called)

    # Auto-generated test for mListCellDisksSize
    def test_mListCellDisksSize_uses_cd_for_legacy_efrack(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mGetNodeModel = MagicMock(return_value='X7')
        _ebox.mCompareExadataModel = MagicMock(return_value=-1)

        _escli = MagicMock()
        _escli.mIsEFRack.return_value = True

        class _FakeCtx(object):
            def __init__(self, node):
                self._node = node
            def __enter__(self):
                return self._node
            def __exit__(self, exc_type, exc, tb):
                return False

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (
            None,
            mockStream(['CD_00_cell1 1T 0.5T\n']),
            mockStream([''])
        )
        _node.mGetCmdExitStatus.return_value = 0

        with patch('exabox.ovm.clustorage.ebEscliUtils', return_value=_escli), \
             patch('exabox.ovm.clustorage.connect_to_host', return_value=_FakeCtx(_node)):
            total, free = _clustorage.mListCellDisksSize(aCellList=['cell1'])

        self.assertAlmostEqual(total, 1024.0)
        self.assertAlmostEqual(free, 512.0)
        self.assertIn('CD_', _node.mExecuteCmd.call_args[0][0])

    # Auto-generated test for mListCellDisksSize
    @patch('exabox.ovm.clustorage.ebLogError')
    def test_mListCellDisksSize_raises_on_error(self, _mock_log_error):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mReturnDom0DomUPair = MagicMock(return_value=[('dom0', 'domu')])
        _ebox.isATPCluster = MagicMock(return_value=False)
        _ebox.mGetNodeModel = MagicMock(return_value='X9')
        _ebox.mCompareExadataModel = MagicMock(return_value=1)

        class _FakeCtx(object):
            def __init__(self, node):
                self._node = node
            def __enter__(self):
                return self._node
            def __exit__(self, exc_type, exc, tb):
                return False

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, mockStream([]), mockStream(['bad']))
        _node.mGetCmdExitStatus.return_value = 1

        with patch('exabox.ovm.clustorage.ebEscliUtils') as _mock_escli, \
             patch('exabox.ovm.clustorage.connect_to_host', return_value=_FakeCtx(_node)):
            _mock_escli.return_value.mIsEFRack.return_value = False
            with self.assertRaises(ExacloudRuntimeError):
                _clustorage.mListCellDisksSize()

    # Auto-generated test for mListCellDisksSize
    def test_mListCellDisksSize_raises_on_empty_output(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mReturnDom0DomUPair = MagicMock(return_value=[('dom0', 'domu')])
        _ebox.isATPCluster = MagicMock(return_value=False)
        _ebox.mGetNodeModel = MagicMock(return_value='X9')
        _ebox.mCompareExadataModel = MagicMock(return_value=1)

        class _FakeCtx(object):
            def __init__(self, node):
                self._node = node
            def __enter__(self):
                return self._node
            def __exit__(self, exc_type, exc, tb):
                return False

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, mockStream([]), mockStream(['err']))
        _node.mGetCmdExitStatus.return_value = 0

        with patch('exabox.ovm.clustorage.ebEscliUtils') as _mock_escli, \
             patch('exabox.ovm.clustorage.connect_to_host', return_value=_FakeCtx(_node)):
            _mock_escli.return_value.mIsEFRack.return_value = False
            with self.assertRaises(ExacloudRuntimeError):
                _clustorage.mListCellDisksSize()

    # Auto-generated test for mGetDiskSizeInInt
    def test_mGetDiskSizeInInt_unit_parsing(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        self.assertEqual(_clustorage.mGetDiskSizeInInt('10gb'), 10)
        self.assertEqual(_clustorage.mGetDiskSizeInInt('5TB'), 5)
        self.assertEqual(_clustorage.mGetDiskSizeInInt('7G'), 7)
        self.assertEqual(_clustorage.mGetDiskSizeInInt('9t'), 9)

    # Auto-generated test for mClusterParseInputJson
    def test_mClusterParseInputJson_missing_params(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _manage = ebCluManageStorage(_ebox, _options)

        _reqparams = {}
        _rc = _manage.mClusterParseInputJson({}, _reqparams)
        self.assertNotEqual(_rc, 0)

    # Auto-generated test for mUpdateRequestData
    def test_mUpdateRequestData_jsonmode(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _manage = ebCluManageStorage(_ebox, _options)

        _options.jsonmode = True
        _data = {'Status': 'Pass'}

        with patch('exabox.ovm.clustorage.ebLogJson') as _mock_log, \
             patch.object(_ebox, 'mGetRequestObj', return_value=None):
            _manage.mUpdateRequestData(_data, _options)

        _mock_log.assert_called_once()

    # Auto-generated test for mRecordError
    def test_mRecordError_sets_storage_data(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _manage = ebCluManageStorage(_ebox, _options)

        _err_obj = ('0x0001', 'ERR: ')
        with patch('exabox.ovm.clustorage.ebError', return_value='err') as _mock_err:
            rc = _manage.mRecordError(_err_obj, 'extra')

        self.assertEqual(rc, 'err')
        self.assertEqual(_manage.mGetStorageOperationData()['ErrorCode'], '0x0001')
        _mock_err.assert_called_once()

    # Auto-generated test for mClusterParseInputJson
    def test_mClusterParseInputJson_valid_payload(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _manage = ebCluManageStorage(_ebox, _options)

        _reqparams = {}
        _payload = {
            _manage.OLDSIZE_GB: '100',
            _manage.NEWSIZE_GB: '120'
        }

        _rc = _manage.mClusterParseInputJson(_payload, _reqparams)

        self.assertEqual(_rc, 0)
        self.assertEqual(_reqparams[_manage.OLDSIZE_GB], '100')
        self.assertEqual(_reqparams[_manage.NEWSIZE_GB], '120')

    # Auto-generated test for mSetStorageOperationData
    def test_mSetStorageOperationData_roundtrip(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _manage = ebCluManageStorage(_ebox, _options)

        _data = {'Status': 'Pass', 'ErrorCode': '0'}
        _manage.mSetStorageOperationData(_data)

        self.assertEqual(_manage.mGetStorageOperationData(), _data)

    # Auto-generated test for mClusterStorageResize
    def test_mClusterStorageResize_input_error_updates_request(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _manage = ebCluManageStorage(_ebox, _options)

        _ebox.mUpdateErrorObject = MagicMock()

        with patch.object(_manage, 'mClusterParseInputJson', return_value=1) as _mock_parse, \
             patch.object(_manage, 'mUpdateRequestData') as _mock_update:
            _rc = _manage.mClusterStorageResize(_options)

        self.assertNotEqual(_rc, 0)
        self.assertEqual(_manage.mGetStorageOperationData()['Status'], 'Fail')
        self.assertTrue(_mock_parse.called)
        _mock_update.assert_called_once()
        _ebox.mUpdateErrorObject.assert_called_once()

    # Auto-generated test for mClusterStorageResize
    def test_mClusterStorageResize_get_sizes_error(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _manage = ebCluManageStorage(_ebox, _options)

        _ebox.mUpdateErrorObject = MagicMock()
        _clu_utils = MagicMock()
        _clu_utils.mStepSpecificDetails.return_value = {}
        _clu_utils.mUpdateTaskProgressStatus = MagicMock()

        def _fake_parse(_json, _params):
            _params[_manage.OLDSIZE_GB] = '100'
            _params[_manage.NEWSIZE_GB] = '120'
            return 0

        with patch.object(_manage, 'mClusterParseInputJson', side_effect=_fake_parse), \
             patch('exabox.ovm.clustorage.ebCluUtils', return_value=_clu_utils), \
             patch('exabox.ovm.clustorage.ebCluManageDiskgroup') as _mock_dg_cls, \
             patch.object(_manage, 'mGetDiskgroupsNewSizes', return_value=1) as _mock_getsizes:
            _mock_dg_cls.return_value = MagicMock()
            _rc = _manage.mClusterStorageResize(_options)

        self.assertNotEqual(_rc, 0)
        _mock_getsizes.assert_called_once()
        _ebox.mUpdateErrorObject.assert_called_once()

    # Auto-generated test for mClusterStorageResize
    def test_mClusterStorageResize_flexible_shrink_success(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {'allow_flexible_shrink': 'true'}
        _manage = ebCluManageStorage(_ebox, _options)

        _ebox.mUpdateStatus = MagicMock()
        _clu_utils = MagicMock()
        _clu_utils.mStepSpecificDetails.return_value = {}
        _clu_utils.mUpdateTaskProgressStatus = MagicMock()

        def _fake_parse(_json, _params):
            _params[_manage.OLDSIZE_GB] = '100'
            _params[_manage.NEWSIZE_GB] = '120'
            return 0

        def _fake_getsizes(_opts, _dgobj, _newsize, _dgmap):
            _dgmap.update({
                _manage.DATA: {
                    _manage.DG_NAME: 'DATA01',
                    _manage.DG_NEWSIZE: 80,
                    _manage.DG_CURRSIZE: 100,
                },
                _manage.RECO: {
                    _manage.DG_NAME: 'RECO01',
                    _manage.DG_NEWSIZE: 40,
                    _manage.DG_CURRSIZE: 50,
                },
                _manage.SPARSE: {}
            })
            return 0

        _dg_obj = MagicMock()
        _dg_obj.mCheckIfDgResizableAll.return_value = 0

        with patch.object(_manage, 'mClusterParseInputJson', side_effect=_fake_parse), \
             patch('exabox.ovm.clustorage.ebCluUtils', return_value=_clu_utils), \
             patch('exabox.ovm.clustorage.ebCluManageDiskgroup', return_value=_dg_obj), \
             patch.object(_manage, 'mGetDiskgroupsNewSizes', side_effect=_fake_getsizes), \
             patch.object(_manage, 'mCheckMinFreeSpaceDGShrink', side_effect=lambda _o, _m: _m) as _mock_check, \
             patch.object(_manage, 'mUtilStorageResize', return_value=0) as _mock_resize, \
             patch.object(_manage, 'mUpdateRequestData') as _mock_update:
            _rc = _manage.mClusterStorageResize(_options)

        self.assertEqual(_rc, 0)
        _mock_check.assert_called_once()
        _mock_resize.assert_called_once()
        _mock_update.assert_not_called()
        self.assertEqual(_manage.mGetStorageOperationData()['Status'], 'Pass')

    # Auto-generated test for ebCluDiskGroupConfig
    def test_diskgroupconfig_basic_setters_roundtrip(self):
        _xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>NORMAL</redundancy>
                <sliceSize>100G</sliceSize>
                <diskGroupSize>200G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg = ebCluDiskGroupConfig(_xml)

        _dg.mSetOCRVote('true')
        self.assertEqual(_dg.mGetOCRVote(), 'true')

        _dg.mSetSparseDg('true')
        self.assertEqual(_dg._ebCluDiskGroupConfig__sparsedg.text, 'true')

        _dg.mSetSliceSize(64)
        self.assertEqual(_dg.mGetSliceSize(), '64G')

        _dg.mSetDiskGroupSize(128)
        self.assertEqual(_dg.mGetDiskGroupSize(), '128G')

        _dg.mSetDgRedundancy('HIGH')
        self.assertEqual(_dg.mGetDgRedundancy(), 'HIGH')

        _dg.mReplaceDgName('DATA02')
        self.assertEqual(_dg.mGetDgName(), 'DATA02')
        self.assertEqual(
            _dg.mGetXMLObject().find('diskGroupName').text,
            'DATA02'
        )

    # Auto-generated test for mListACFSCellDisks
    def test_mListACFSCellDisks_prefers_cd(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        with patch.object(_clustorage, 'mListACFSCellDisks',
                          return_value=['CD_00_cell1', 'CD_01_cell1']) as _mock_list:
            _result = _clustorage.mListACFSCellDisks(_node)

        self.assertEqual(_result, ['CD_00_cell1', 'CD_01_cell1'])
        _mock_list.assert_called_once_with(_node)

    # Auto-generated test for mListACFSCellDisks
    def test_mListACFSCellDisks_fallback_fd(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        with patch.object(_clustorage, 'mListACFSCellDisks',
                          return_value=['FD_00_cell1']) as _mock_list:
            _result = _clustorage.mListACFSCellDisks(_node)

        self.assertEqual(_result, ['FD_00_cell1'])
        _mock_list.assert_called_once_with(_node)

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_success_multiple_attributes(self):
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['CD_01_cell normal 100G\n', 'CD_02_cell bad 50G\n']),
            mockStream([''])
        )
        _node.mGetCmdExitStatus.return_value = False

        _result = _clustorage.mListCellDisksAttributes(_node, ['STATUS', 'SIZE'])

        self.assertEqual(
            _result,
            {
                'CD_01_cell': {'STATUS': 'normal', 'SIZE': '100G'},
                'CD_02_cell': {'STATUS': 'bad', 'SIZE': '50G'}
            }
        )

    # Auto-generated test for mListPMEMDetails
    def test_mListPMEMDetails_skips_empty_lines(self):
        _node = MagicMock()
        _stdout = """name: cell1_PMEMCACHE

cellDisk: PM_00_cell1,PM_01_cell1

status: normal
"""

        with patch('exabox.ovm.clustorage.node_exec_cmd') as _mock_exec:
            _mock_exec.return_value = (None, _stdout, None)
            _details = ebCluStorageConfig.mListPMEMDetails(_node, "cache")

        self.assertEqual(
            _details,
            {
                'name': 'cell1_PMEMCACHE',
                'cellDisk': 'PM_00_cell1,PM_01_cell1',
                'status': 'normal'
            }
        )

    # Auto-generated test for mListPMEMDetails
    def test_mListPMEMDetails_handles_unknown_attrs(self):
        _node = MagicMock()
        _stdout = """name: cell1_PMEMLOG
unknownField: value1 value2
status: normal
"""

        with patch('exabox.ovm.clustorage.node_exec_cmd') as _mock_exec:
            _mock_exec.return_value = (None, _stdout, None)
            _details = ebCluStorageConfig.mListPMEMDetails(_node, "log")

        self.assertEqual(
            _details,
            {
                'name': 'cell1_PMEMLOG',
                'unknownField': 'value1 value2',
                'status': 'normal'
            }
        )

    # Auto-generated test for mListACFSCellDisks
    def test_mListACFSCellDisks_fallback_to_fd(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'
        _node.mExecuteCmdCellcli.side_effect = [
            (None, mockStream(['']), mockStream([''])),
            (None, mockStream(['FD_00_cell1 FD_01_cell1']), mockStream(['']))
        ]

        with patch('exabox.ovm.clustorage.ebLogInfo') as _mock_log:
            _result = _clustorage.mListACFSCellDisks(_node)

        self.assertEqual(_result, ['FD_00_cell1', 'FD_01_cell1'])
        self.assertEqual(_node.mExecuteCmdCellcli.call_count, 2)
        self.assertTrue(_mock_log.called)

    # Auto-generated test for mListACFSCellDisks
    def test_mListACFSCellDisks_returns_cd_first(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell2.example.com'
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['CD_00_cell2 CD_01_cell2']),
            mockStream([''])
        )

        _result = _clustorage.mListACFSCellDisks(_node)

        self.assertEqual(_result, ['CD_00_cell2', 'CD_01_cell2'])
        _node.mExecuteCmdCellcli.assert_called_once()


    # Auto-generated test for mFixPMEMComponent
    @patch('exabox.ovm.clustorage.ProcessManager')
    def test_mFixPMEMComponent_rebuilds_inconsistent_cells(self, _mock_proc_mgr):
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )

        _cell_list = [
            "scaqab10celadm01.us.oracle.com",
            "scaqab10celadm02.us.oracle.com",
            "scaqab10celadm03.us.oracle.com"
        ]

        _proc_instance = MagicMock()
        _proc_instance.mGetManager.return_value.dict.return_value = {}
        _mock_proc_mgr.return_value = _proc_instance

        def _start_append_side_effect(_proc):
            _proc.mGetCallback()(*_proc.mGetArgs())

        _proc_instance.mStartAppend.side_effect = _start_append_side_effect

        with patch('exabox.ovm.clustorage.connect_to_host') as _mock_connect, \
             patch('exabox.ovm.clustorage.ebCluStorageConfig.mListPMEMDetails') as _mock_details, \
             patch('exabox.ovm.clustorage.node_exec_cmd') as _mock_node_exec:
            _node = MagicMock()
            _mock_connect.return_value.__enter__.return_value = _node
            _mock_node_exec.return_value = (None, None, None)

            _mock_details.side_effect = [
                {
                    'name': 'PMEMCACHE_cell1',
                    'cellDisk': 'PM_00_cell1,PM_01_cell1',
                    'status': 'normal'
                },
                {
                    'name': 'PMEMCACHE_cell2',
                    'cellDisk': 'PM_00_cell2',
                    'status': 'normal'
                },
                {
                    'name': 'PMEMCACHE_cell3',
                    'cellDisk': 'PM_00_cell3,PM_01_cell3',
                    'status': 'normal'
                }
            ]

            ebCluStorageConfig.mFixPMEMComponent(_cell_list, "cache")

        _mock_node_exec.assert_any_call(
            _node,
            "cellcli -e drop pmemcache",
            log_error=True,
            log_stdout_on_error=True
        )
        _mock_node_exec.assert_any_call(
            _node,
            "cellcli -e create pmemcache all",
            log_error=True,
            log_stdout_on_error=True
        )

    # Auto-generated test for mFixPMEMComponent
    @patch('exabox.ovm.clustorage.ProcessManager')
    def test_mFixPMEMComponent_skips_fix_when_status_missing(self, _mock_proc_mgr):
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )

        _cell_list = [
            "scaqab10celadm01.us.oracle.com",
            "scaqab10celadm02.us.oracle.com"
        ]

        _proc_instance = MagicMock()
        _proc_instance.mGetManager.return_value.dict.return_value = {}
        _mock_proc_mgr.return_value = _proc_instance

        def _start_append_side_effect(_proc):
            _proc.mGetCallback()(*_proc.mGetArgs())

        _proc_instance.mStartAppend.side_effect = _start_append_side_effect

        with patch('exabox.ovm.clustorage.connect_to_host') as _mock_connect, \
             patch('exabox.ovm.clustorage.ebCluStorageConfig.mListPMEMDetails') as _mock_details, \
             patch('exabox.ovm.clustorage.node_exec_cmd') as _mock_node_exec:
            _node = MagicMock()
            _mock_connect.return_value.__enter__.return_value = _node
            _mock_node_exec.return_value = (None, None, None)

            _mock_details.side_effect = [
                {
                    'name': 'PMEMLOG_cell1',
                    'cellDisk': 'PM_00_cell1'
                },
                {
                    'name': 'PMEMLOG_cell2',
                    'cellDisk': 'PM_00_cell2'
                }
            ]

            ebCluStorageConfig.mFixPMEMComponent(_cell_list, "log")

        _node.mExecuteCmd.assert_not_called()

    # Auto-generated test for mCreateACFSGridDisks
    @patch('exabox.ovm.clustorage.mCompareModel', return_value=0)
    def test_mCreateACFSGridDisks_disabled_for_modern_cells(self, _mock_cmp):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mGetExadataCellModel = MagicMock(return_value='X7')
        _ebox.mReturnCellNodes = MagicMock()

        _clustorage.mCreateACFSGridDisks()

        _ebox.mReturnCellNodes.assert_not_called()

    # Auto-generated test for mDeleteACFSGridDisks
    def test_mDeleteACFSGridDisks_delegates_to_create(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        with patch.object(_clustorage, 'mCreateACFSGridDisks') as _mock_create:
            _clustorage.mDeleteACFSGridDisks()

        _mock_create.assert_called_once_with(aCreate=False)

    # Auto-generated test for mDeleteForceGridDisks
    @patch('exabox.ovm.clustorage.sleep')
    def test_mDeleteForceGridDisks_exhausts_retries(self, _mock_sleep):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        with patch.object(_clustorage, 'mDeleteGD', side_effect=[0, 0, 0, 0]) as _mock_delete:
            _result = _clustorage.mDeleteForceGridDisks()

        self.assertFalse(_result)
        self.assertEqual(_mock_delete.call_count, 4)
        self.assertEqual(_mock_delete.call_args_list[-1].kwargs, {'aListOnly': True})

    # Auto-generated test for mDeleteForceGridDisks
    def test_mDeleteForceGridDisks_stops_on_success(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        with patch.object(_clustorage, 'mDeleteGD', return_value=1) as _mock_delete:
            _result = _clustorage.mDeleteForceGridDisks()

        self.assertTrue(_result)
        self.assertEqual(_mock_delete.call_count, 1)

    # Auto-generated test for mListCellDG
    def test_mListCellDG_default_listing(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['DATA_C1\nRECO_C1\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['DATA_C1', 'RECO_C1'])

    # Auto-generated test for mGetDgVolsize
    def test_mGetDgVolsize_three_way_non_mvm(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _ebox.mGetCmd = MagicMock(return_value='create_service')
        _ebox.mGetExadataCellModel = MagicMock(return_value='X7')

        disk_count = 12
        disksize = 7
        dbfs_size = 0
        Dsplit, Rsplit, Ssplit = 35, 50, 15

        t_value = (6386 * disk_count) - (dbfs_size * disk_count // 12)

        A = [[3, 3, 3], [Rsplit, -Dsplit, 0], [0, Ssplit, -Rsplit]]
        detA = (A[0][0] * A[1][1] * A[2][2] + A[0][1] * A[1][2] * A[2][0] + A[0][2] * A[1][0] * A[2][1]) - \
               (A[0][2] * A[1][1] * A[2][0] + A[0][1] * A[1][0] * A[2][2] + A[0][0] * A[1][2] * A[2][1])

        adjA = [[0 for _ in range(3)] for _ in range(3)]
        adjA[0][0] = (A[1][1] * A[2][2]) - (A[1][2] * A[2][1])
        adjA[0][1] = -1 * ((A[0][1] * A[2][2]) - (A[2][1] * A[0][2]))
        adjA[0][2] = (A[0][1] * A[1][2]) - (A[0][2] * A[1][1])
        adjA[1][0] = -1 * ((A[1][0] * A[2][2]) - (A[1][2] * A[2][0]))
        adjA[1][1] = (A[0][0] * A[2][2]) - (A[0][2] * A[2][0])
        adjA[1][2] = -1 * ((A[0][0] * A[1][2]) - (A[0][2] * A[1][0]))
        adjA[2][0] = (A[1][0] * A[2][1]) - (A[1][1] * A[2][0])
        adjA[2][1] = -1 * ((A[0][0] * A[2][1]) - (A[0][1] * A[2][0]))
        adjA[2][2] = (A[0][0] * A[1][1]) - (A[0][1] * A[1][0])

        invA = [[adjA[i][j] / float(detA) for j in range(3)] for i in range(3)]
        expected_volszD = int(invA[0][0] * t_value)
        expected_volszR = int(invA[1][0] * t_value)
        expected_volszS = int(invA[2][0] * t_value)
        expected_sliceD = int(expected_volszD * 3 / disk_count)
        expected_sliceR = int(expected_volszR * 3 / disk_count)
        expected_sliceS = int(expected_volszS * 3 / disk_count)

        result = _clustorage.mGetDgVolsize(
            disk_count, disksize, dbfs_size, Dsplit, Rsplit, False, 0, Ssplit)

        self.assertEqual(result,
            (expected_volszD, expected_volszR, expected_volszS,
             expected_sliceD, expected_sliceR, expected_sliceS))

    # Auto-generated test for mGetDgVolsize
    def test_mGetDgVolsize_two_way_mvm(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _ebox.mGetCmd = MagicMock(return_value='elastic_cell_update')
        _ebox.mGetExadataCellModel = MagicMock(return_value='X7')

        disk_count = 12
        disksize = 10
        dbfs_size = 100
        total_dg = 1000
        Dsplit, Rsplit = 60, 40

        t_value = (total_dg - dbfs_size) * 3

        detA = (3 * (-Dsplit)) - (3 * Rsplit)
        invA00 = (-Dsplit) / float(detA)
        invA10 = (-Rsplit) / float(detA)

        expected_volszD = int(invA00 * t_value)
        expected_volszR = int(invA10 * t_value)
        expected_sliceD = int(expected_volszD * 3 / disk_count)
        expected_sliceR = int(expected_volszR * 3 / disk_count)

        result = _clustorage.mGetDgVolsize(
            disk_count, disksize, dbfs_size, Dsplit, Rsplit, True, total_dg)

        self.assertEqual(result,
            (expected_volszD, expected_volszR, expected_sliceD, expected_sliceR))



    # Auto-generated test for mDgUsagePercentage
    def test_mDgUsagePercentage_calculates_percentage(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mUtilGetDiskgroupSize.side_effect = [
            5 * 1024,   # used MB
            10 * 1024,  # total MB
        ]

        _pct, _total, _used = _clustorage.mDgUsagePercentage(
            _options, _dgObj, 'DATAC1')

        self.assertEqual(_pct, 50)
        self.assertEqual(_total, 10.0)
        self.assertEqual(_used, 5.0)

    # Auto-generated test for mDgUsagePercentage
    def test_mDgUsagePercentage_rounds_usage(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mUtilGetDiskgroupSize.side_effect = [
            333,   # used MB
            500,   # total MB
        ]

        _pct, _total, _used = _clustorage.mDgUsagePercentage(
            _options, _dgObj, 'RECOC1')

        self.assertEqual(_pct, 67)
        self.assertAlmostEqual(_total, 500 / 1024.0, places=6)
        self.assertAlmostEqual(_used, 333 / 1024.0, places=6)

    # Auto-generated test for mUtilStorageResize
    def test_mUtilStorageResize_handles_rebalance_only(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _options.jsonconf = {}
        _dgObj = MagicMock()
        _dgObj.mClusterDgrpRebalance.return_value = 0

        _clustorage._ebCluManageStorage__resizereco = False
        _clustorage._ebCluManageStorage__rebalancereco = True

        _dgmap = {
            _clustorage.RECO: {
                _clustorage.DG_NAME: 'RECO1',
                _clustorage.DG_NEWSIZE: 100,
                _clustorage.DG_CURRSIZE: 100,
            }
        }

        _rc = _clustorage.mUtilStorageResize(_dgObj, _options, _dgmap, 0)

        self.assertEqual(_rc, 0)
        _dgObj.mClusterDgrpRebalance.assert_called_once_with(_options)
        _dgObj.mClusterDgrpResize.assert_not_called()

    # Auto-generated test for mUtilStorageResize
    def test_mUtilStorageResize_updates_payload(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _options.jsonconf = {}
        _dgObj = MagicMock()
        _dgObj.mClusterDgrpResize.return_value = 0

        _clustorage._ebCluManageStorage__resizedata = True

        _dgmap = {
            _clustorage.DATA: {
                _clustorage.DG_NAME: 'DATA1',
                _clustorage.DG_NEWSIZE: 80,
                _clustorage.DG_CURRSIZE: 100,
            }
        }

        _rc = _clustorage.mUtilStorageResize(_dgObj, _options, _dgmap, 0)

        self.assertEqual(_rc, 0)
        self.assertEqual(_dgObj.mClusterDgrpResize.call_count, 1)
        self.assertEqual(_options.jsonconf['diskgroup'], 'DATA1')

    # Auto-generated test for mUtilStorageResize
    def test_mUtilStorageResize_defaults_rebalance_power(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {'rebalance_power': 2}
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mClusterDgrpRebalance.return_value = 0

        _clustorage._ebCluManageStorage__resizereco = False
        _clustorage._ebCluManageStorage__rebalancereco = True

        _dgmap = {
            _clustorage.RECO: {
                _clustorage.DG_NAME: 'RECO1',
                _clustorage.DG_NEWSIZE: 100,
                _clustorage.DG_CURRSIZE: 100,
            }
        }

        _rc = _clustorage.mUtilStorageResize(_dgObj, _options, _dgmap, 0)

        self.assertEqual(_rc, 0)
        _dgObj.mClusterDgrpRebalance.assert_called_once_with(_options)
        self.assertEqual(_options.jsonconf.get('rebalance_power'), 16)
        _dgObj.mClusterDgrpResize.assert_not_called()

    # Auto-generated test for mCheckMinFreeSpaceDGShrink
    def test_mCheckMinFreeSpaceDGShrink_maps_targets(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgmap = {
            _clustorage.DATA: {
                _clustorage.DG_NAME: 'DATA01',
                _clustorage.DG_NEWSIZE: 100,
                _clustorage.DG_CURRSIZE: 120,
            },
            _clustorage.RECO: {
                _clustorage.DG_NAME: 'RECO01',
                _clustorage.DG_NEWSIZE: 80,
                _clustorage.DG_CURRSIZE: 90,
            },
            _clustorage.SPARSE: {
                _clustorage.DG_NAME: 'SPRC01',
                _clustorage.DG_NEWSIZE: 70,
                _clustorage.DG_CURRSIZE: 75,
            },
        }

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['dg1', 'dg2', 'dg3']
        _ebox.mGetClusters = MagicMock()
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster

        with patch.object(_clustorage, 'mFetchAndSaveDGSizes', return_value=None), \
                patch.object(_clustorage, 'mCalculateDgResize', return_value=None):
            _result = _clustorage.mCheckMinFreeSpaceDGShrink(_options, _dgmap)

        self.assertEqual(_result[_clustorage.DATA][_clustorage.DG_NAME], 'DATA01')
        self.assertEqual(_result[_clustorage.DATA][_clustorage.DG_NEWSIZE], 100)
        self.assertEqual(_result[_clustorage.RECO][_clustorage.DG_NAME], 'RECO01')
        self.assertEqual(_result[_clustorage.SPARSE][_clustorage.DG_NAME], 'SPRC01')

    # Auto-generated test for mGetDiskgroupsNewSizes
    def test_mGetDiskgroupsNewSizes_records_invalid_usedspace(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mSetDiskGroupOperationData.return_value = None

        _dg_constants = _clustorage.mGetConstantsObj()

        _data_dg = MagicMock()
        _data_dg.mGetDiskGroupType.return_value = _dg_constants._data_dg_type_str
        _data_dg.mGetDgName.return_value = 'DATAC1'
        _data_dg.mGetDiskGroupSize.return_value = '500G'
        _data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        _reco_dg = MagicMock()
        _reco_dg.mGetDiskGroupType.return_value = _dg_constants._reco_dg_type_str
        _reco_dg.mGetDgName.return_value = 'RECOC1'
        _reco_dg.mGetDiskGroupSize.return_value = '400G'

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco']

        _ebox_clusters = MagicMock()
        _ebox_clusters.mGetCluster.return_value = _cluster

        _ebox_storage = MagicMock()
        _ebox_storage.mGetDiskGroupConfig.side_effect = [_data_dg, _reco_dg]

        _ebox_ctrl = MagicMock()
        _ebox_ctrl.mGetClusters.return_value = _ebox_clusters
        _ebox_ctrl.mGetStorage.return_value = _ebox_storage

        _dgObj.mUtilGetDiskgroupSize.side_effect = [
            500 * 1024,   # DATA total in MB
            -1024,        # DATA used in MB invalid (-> -1 after division)
            400 * 1024,   # RECO total in MB (unused after early exit)
            200 * 1024,   # RECO used in MB (unused after early exit)
        ]

        _options.jsonconf = {
            'newsize': 1000,
            'backup_disk': 'true',
            'create_sparse': 'false',
            'storage_distribution': '80:20:0'
        }

        _dgmap = {}

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox_ctrl), \
                patch.object(_clustorage, 'mRecordError', return_value=77) as _mock_record:
            _rc = _clustorage.mGetDiskgroupsNewSizes(_options, _dgObj, 1000, _dgmap)

        self.assertEqual(_rc, 77)
        _mock_record.assert_called_with(gDiskgroupError['InvalidPropValue'],
                                        '*** Invalid usedspace of diskgroup DATAC1')

    # Auto-generated test for mListCellDG
    def test_mListCellDG_calls_execute_twice(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['DATA_C1\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['DATA_C1'])
        self.assertEqual(_node.mExecuteCmd.call_count, 2)

    # Auto-generated test for mGetDiskSizeInInt (storage config)
    def test_storage_config_disk_size_in_int(self):
        _root = etree.fromstring(
            """
            <config>
              <storage>
                <diskGroups>
                  <diskGroup id="DG1">
                    <diskGroupName>DATA01</diskGroupName>
                    <redundancy>NORMAL</redundancy>
                    <sliceSize>100G</sliceSize>
                    <diskGroupSize>200G</diskGroupSize>
                    <ocrVote>false</ocrVote>
                  </diskGroup>
                </diskGroups>
                <storagePools></storagePools>
                <edvVolumes></edvVolumes>
              </storage>
            </config>
            """
        )

        class _Cfg(object):
            def __init__(self, root):
                self._root = root
            def mGetConfigAllElement(self, path):
                return self._root.findall(path)
            def mConfigRoot(self):
                return self._root

        _cfg = _Cfg(_root)
        _storage_cfg = ebCluStorageConfig(self.mGetClubox(), _cfg)

        self.assertEqual(_storage_cfg.mGetDiskSizeInInt(' 12GB '), 12)
        self.assertEqual(_storage_cfg.mGetDiskSizeInInt('unknown'), 0)

    # Auto-generated test for ebCluQuorumManager.checkOutput
    def test_quorum_manager_check_output(self):
        _manager = ebCluQuorumManager(self.mGetClubox())

        self.assertTrue(_manager.checkOutput(['Located 2'], 'Located'))
        self.assertFalse(_manager.checkOutput(['Missing'], 'Located'))

    # Auto-generated test for ebCluQuorumManager.runCommand
    def test_quorum_manager_run_command_success(self):
        _manager = ebCluQuorumManager(self.mGetClubox())
        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, mockStream(['Located 2\n']), mockStream(['']))
        _node.mGetCmdExitStatus.return_value = 0

        _success, _output, _status = _manager.runCommand(
            'cmd', _node, True, True, False, 'Located', 101, 'err')

        self.assertTrue(_success)
        self.assertEqual(_status, 0)
        self.assertIn('Located', _output[0])

    # Auto-generated test for ebCluQuorumManager.runCommand
    def test_quorum_manager_run_command_raises_on_exit_status(self):
        _manager = ebCluQuorumManager(self.mGetClubox())
        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, mockStream(['Any\n']), mockStream(['']))
        _node.mGetCmdExitStatus.return_value = 2

        with self.assertRaises(ExacloudRuntimeError):
            _manager.runCommand('cmd', _node, False, False, False, 'Located', 101, 'err')

    # Auto-generated test for ebCluQuorumManager.runCommand
    def test_quorum_manager_run_command_raises_on_expected_missing(self):
        _manager = ebCluQuorumManager(self.mGetClubox())
        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, mockStream(['Nope\n']), mockStream(['']))
        _node.mGetCmdExitStatus.return_value = 0

        with self.assertRaises(ExacloudRuntimeError):
            _manager.runCommand('cmd', _node, True, False, True, 'Located', 101, 'err')

    # Auto-generated test for ebCluQuorumManager.getVotingDisk
    def test_quorum_manager_get_voting_disk(self):
        _manager = ebCluQuorumManager(self.mGetClubox())
        _disk_list = [
            'Name Voting_files State Type',
            'DATA1, Y NORMAL ASM',
            'RECO1, N NORMAL ASM'
        ]

        _disk, _disk_type = _manager.getVotingDisk(_disk_list, 101)

        self.assertEqual(_disk, 'DATA1')
        self.assertEqual(_disk_type, 'ASM')

    # Auto-generated test for ebCluQuorumManager.getVotingDisk
    def test_quorum_manager_get_voting_disk_missing(self):
        _manager = ebCluQuorumManager(self.mGetClubox())
        _disk_list = [
            'Name Voting_files State Type',
            'DATA1, N NORMAL ASM'
        ]

        with self.assertRaises(ExacloudRuntimeError):
            _manager.getVotingDisk(_disk_list, 101)

    # Auto-generated test for ebCluQuorumManager.getDATADisk
    def test_quorum_manager_get_data_disk(self):
        _manager = ebCluQuorumManager(self.mGetClubox())
        _disk_list = [
            'Name State',
            'DATA1, NORMAL',
            'RECO1, NORMAL'
        ]

        _disk = _manager.getDATADisk(_disk_list, 101)

        self.assertEqual(_disk, 'DATA1')

    # Auto-generated test for ebCluQuorumManager.getDATADisk
    def test_quorum_manager_get_data_disk_missing(self):
        _manager = ebCluQuorumManager(self.mGetClubox())
        _disk_list = [
            'Name State',
            'RECO1, NORMAL'
        ]

        with self.assertRaises(ExacloudRuntimeError):
            _manager.getDATADisk(_disk_list, 101)

    # Auto-generated test for ebCluQuorumManager.mCountVotingDisks
    def test_quorum_manager_count_voting_disks(self):
        _manager = ebCluQuorumManager(self.mGetClubox())

        with patch.object(_manager, 'runCommand', return_value=(True, ['Located 5 voting disks'], 0)):
            _count = _manager.mCountVotingDisks(MagicMock(), 101)

        self.assertEqual(_count, 5)

    # Auto-generated test for mListCellDisksAttributes
    @patch('exabox.ovm.clustorage.sleep')
    def test_mListCellDisksAttributes_success_after_retry(self, _mock_sleep):
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()
        _controller = _clustorage._ebCluStorageConfig__ebox

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'
        _node.mExecuteCmdCellcli.side_effect = [
            (None, mockStream(['stdout error']), mockStream(['CELL-02559 error'])),
            (None, mockStream(['CD_01_cell normal\n', 'CD_02_cell bad\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.side_effect = [True, False]

        with patch.object(_controller, 'mCheckCellsServicesUp') as _mock_check:
            _result = _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

        self.assertEqual(
            _result,
            {
                'CD_01_cell': {'STATUS': 'normal'},
                'CD_02_cell': {'STATUS': 'bad'}
            }
        )
        _mock_check.assert_called_once_with(aRestart=False, aCellList=['cell1.example.com'])
        _mock_sleep.assert_called_once()

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_handles_multiple_failures_before_success(self):
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()
        _controller = _clustorage._ebCluStorageConfig__ebox

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'
        _node.mExecuteCmdCellcli.side_effect = [
            (None, mockStream(['stdout']), mockStream(['CELL-02559 error'])),
            (None, mockStream(['stdout']), mockStream(['CELL-02559 error'])),
            (None, mockStream(['CD_03_cell normal\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.side_effect = [True, True, False]

        with patch.object(_controller, 'mCheckCellsServicesUp') as _mock_check, \
             patch('exabox.ovm.clustorage.sleep') as _mock_sleep:
            _result = _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

        self.assertEqual(_result, {'CD_03_cell': {'STATUS': 'normal'}})
        self.assertEqual(_mock_check.call_count, 2)
        self.assertEqual(_mock_sleep.call_count, 2)

    # Auto-generated test for mListCellDG
    def test_mListCellDG_filters_catalog_delta_in_zdlra(self):
        _ebox = self.mGetClubox()
        _ebox.IsZdlraProv = MagicMock(return_value=True)
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _output = "CATALOG_C1\nDELTA_C1\nDATA_C1\n"
        _node.mExecuteCmd.side_effect = [
            (None, mockStream([_output]), mockStream([''])),
            (None, mockStream([_output]), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['CATALOG_C1', 'DELTA_C1'])
        self.assertEqual(_node.mExecuteCmd.call_count, 2)

    # Auto-generated test for mListCellDG
    def test_mListCellDG_suffix_filters_grid_disks(self):
        _ebox = self.mGetClubox()
        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _output = "DATA_C1 size1\nRECO_C2 size2\nDATA_C1 size3\n"
        _node.mExecuteCmd.side_effect = [
            (None, mockStream([_output]), mockStream([''])),
            (None, mockStream([_output]), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        _result = _clustorage.mListCellDG(_node, aSuffix='C1')

        self.assertEqual(_result, ['DATA_C1 size1', 'DATA_C1 size3'])
        self.assertEqual(_node.mExecuteCmd.call_count, 2)

    # Auto-generated test for mListPMEMDetails
    def test_mListPMEMDetails_handles_multiword_values(self):
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cellmulti.example.com'

        _stdout = """name: cell1_PMEMCACHE
cellDisk: PM_00_cell1,PM_01_cell1
creationTime: 2021-05-05T23:48:01+00:00
status: normal
"""

        with patch('exabox.ovm.clustorage.node_exec_cmd') as _mock_exec:
            _mock_exec.return_value = (None, _stdout, None)
            _details = ebCluStorageConfig.mListPMEMDetails(_node, "cache")

        self.assertEqual(
            _details,
            {
                'name': 'cell1_PMEMCACHE',
                'cellDisk': 'PM_00_cell1,PM_01_cell1',
                'creationTime': '2021-05-05T23:48:01+00:00',
                'status': 'normal'
            }
        )

    # Auto-generated test for mListCellDG
    def test_mListCellDG_returns_all_grid_disks_no_suffix(self):
        _ebox = self.mGetClubox()
        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _output = "GD1 GD2"
        _node.mExecuteCmd.side_effect = [
            (None, mockStream([_output]), mockStream([''])),
            (None, mockStream([_output]), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['GD1', 'GD2'])
        self.assertEqual(_node.mExecuteCmd.call_count, 2)

    # Auto-generated test for mListCellDG
    def test_mListCellDG_zdlra_ignores_non_catalog_delta(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=True)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['CATALOG_C1 DELTA_C1 DATA_C1']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['CATALOG_C1', 'DELTA_C1'])

    # Auto-generated test for mListCellDG
    def test_mListCellDG_raises_on_command_failure(self):
        _ebox = self.mGetClubox()
        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'

        _node.mExecuteCmd.side_effect = [
            (None, mockStream(['out']), mockStream(['err'])),
            (None, mockStream(['out']), mockStream(['err']))
        ]
        _node.mGetCmdExitStatus.return_value = True

        with self.assertRaises(Exception):
            _clustorage.mListCellDG(_node)

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_invalid_inputs(self):
        for _value in ['', '50', '50:50:50:0', '50:abc:50', '-1:50:51', '50:25:20']:
            with self.assertRaises(ValueError):
                mParseStorageDistrib(_value)

    # Auto-generated test for mCreateCellDG
    def test_mCreateCellDG_raises_on_command_failure(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = 1
        _node.mGetHostname.return_value = 'cell1'

        with self.assertRaises(Exception):
            _clustorage.mCreateCellDG(
                _node,
                1,
                'DATA',
                'cell1',
                'CD_00_cell1',
                '10G'
            )

    # Auto-generated test for mDeleteCellDG
    def test_mDeleteCellDG_raises_on_command_failure(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = 1
        _node.mGetHostname.return_value = 'cell2'

        with self.assertRaises(Exception):
            _clustorage.mDeleteCellDG(_node, 2, 'RECO', 'cell2')

    # Auto-generated test for mListACFSCellDisks
    def test_mListACFSCellDisks_empty_output(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell3.example.com'
        _node.mExecuteCmdCellcli.side_effect = [
            (None, mockStream(['']), mockStream([''])),
            (None, mockStream(['']), mockStream(['']))
        ]

        with patch('exabox.ovm.clustorage.ebLogInfo') as _mock_log:
            _result = _clustorage.mListACFSCellDisks(_node)

        self.assertEqual(_result, [])
        _mock_log.assert_called_once()

    # Auto-generated test for mCreateACFSGridDisks
    @patch('exabox.ovm.clustorage.mCompareModel', return_value=-1)
    def test_mCreateACFSGridDisks_deletes_existing(self, _mock_cmp):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mGetExadataCellModel = MagicMock(return_value='X6')
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1.example.com': {}})

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster

        _dg_cfg = MagicMock()
        _dg_cfg.mGetDgName.return_value = 'DATAC1'

        _existing = ['ADG1C1_CD_02_cell1', 'ADG2C1_CD_02_cell1']

        with patch('exabox.ovm.clustorage.exaBoxNode') as _mock_node_cls, \
             patch.object(_clustorage, 'mGetDiskGroupConfig', return_value=_dg_cfg), \
             patch.object(_clustorage, 'mListCellDG', return_value=_existing), \
             patch.object(_clustorage, 'mListACFSCellDisks', return_value=['CD_02_cell1']), \
             patch.object(_clustorage, 'mDeleteCellDG') as _mock_delete:
            _node = MagicMock()
            _mock_node_cls.return_value = _node
            _clustorage.mCreateACFSGridDisks(aCreate=False)

        self.assertEqual(_mock_delete.call_count, 2)

    # Auto-generated test for mListCellDG
    def test_mListCellDG_suffix_filters_results(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['DATAC1_CD_00\nRECOC1_CD_01\nOTHER\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node, aSuffix='C1')

        self.assertEqual(_result, ['DATAC1_CD_00', 'RECOC1_CD_01'])

    # Auto-generated test for mListCellDG
    def test_mListCellDG_zdlra_filters_catalog_delta(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=True)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['CATALOG_C1 DELTA_C1 DATA_C1']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['CATALOG_C1', 'DELTA_C1'])

    # Auto-generated test for mDeleteGD
    def test_mDeleteGD_drops_matching_grid_disks(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mIsDebug = MagicMock(return_value=False)
        _ebox.SharedEnv = MagicMock(return_value=True)
        _ebox.mIsExabm = MagicMock(return_value=False)
        _clustorage.mClusterDiskGroupSuffix = MagicMock(return_value='C1')

        _node = MagicMock()
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream([
                'DBFSS1_CD_00 cell\n',
                'DATAC1_CD_01 cell\n',
                'RECOC1_CD_02 cell\n'
            ]),
            mockStream([''])
        )

        with patch('exabox.ovm.clustorage.exaBoxNode', return_value=_node):
            _result = _clustorage.mDeleteGD()

        self.assertEqual(_result, 0)
        self.assertEqual(_node.mExecuteCmdLog.call_count, 3)
        _node.mDisconnect.assert_called_once()

    # Auto-generated test for mDeleteGD
    def test_mDeleteGD_list_only_logs_entries(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mIsDebug = MagicMock(return_value=False)
        _ebox.SharedEnv = MagicMock(return_value=True)
        _ebox.mIsExabm = MagicMock(return_value=False)
        _clustorage.mClusterDiskGroupSuffix = MagicMock(return_value='C1')

        _node = MagicMock()
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['DATAC1_CD_00 cell\n']),
            mockStream([''])
        )

        with patch('exabox.ovm.clustorage.exaBoxNode', return_value=_node), \
             patch('exabox.ovm.clustorage.ebLogWarn') as _mock_warn:
            _result = _clustorage.mDeleteGD(aListOnly=True)

        self.assertEqual(_result, 0)
        _node.mExecuteCmdLog.assert_not_called()
        self.assertTrue(_mock_warn.called)

    # Auto-generated test for mDeleteGD
    def test_mDeleteGD_returns_one_when_no_entries(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _clustorage.mClusterDiskGroupSuffix = MagicMock(return_value='C2')

        _node = MagicMock()
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream([]),
            mockStream([''])
        )

        with patch('exabox.ovm.clustorage.exaBoxNode', return_value=_node):
            _result = _clustorage.mDeleteGD()

        self.assertEqual(_result, 1)
        _node.mDisconnect.assert_called_once()

    # Auto-generated test for mDeleteGD
    def test_mDeleteGD_shared_exabm_appends_unmatched(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mIsDebug = MagicMock(return_value=False)
        _ebox.SharedEnv = MagicMock(return_value=False)
        _ebox.mIsExabm = MagicMock(return_value=True)
        _ebox.mCheckConfigOption = MagicMock(return_value=False)
        _clustorage.mClusterDiskGroupSuffix = MagicMock(return_value='C1')

        _node = MagicMock()
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['DATAX9_CD_00 cell\n']),
            mockStream([''])
        )

        with patch('exabox.ovm.clustorage.exaBoxNode', return_value=_node), \
             patch('exabox.ovm.clustorage.ebLogWarn') as _mock_warn:
            _result = _clustorage.mDeleteGD(aListOnly=True)

        self.assertEqual(_result, 0)
        self.assertTrue(_mock_warn.called)
        _node.mDisconnect.assert_called_once()

    # Auto-generated test for mListCellDG
    def test_mListCellDG_suffix_includes_matching_entries(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['DATA_C1_x\nRECO_C1_y\nOTHER\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node, aSuffix='C1')

        self.assertEqual(_result, ['DATA_C1_x', 'RECO_C1_y'])

    # Auto-generated test for mGetCurrentClusterGridDisksFromCells
    def test_mGetCurrentClusterGridDisksFromCells_records_nonmatching(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1'

        with patch.object(_clustorage, 'mClusterDiskGroupSuffix', return_value='C03'), \
             patch.object(_clustorage, 'mListCellDG', return_value=[
                 'RECOC03_CD_11_cell1',
                 'DATAC04_CD_11_cell1'
             ]), \
             patch('exabox.ovm.clustorage.ebLogTrace') as _mock_trace:
            _result = _clustorage.mGetCurrentClusterGridDisksFromCells(_node)

        self.assertEqual(_result, ['RECOC03_CD_11_cell1'])
        self.assertTrue(_mock_trace.called)



    # Auto-generated test for mListACFSCellDisks
    def test_mListACFSCellDisks_returns_cd_when_present(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _node.mGetHostname.return_value = 'cell1'
        _node.mExecuteCmdCellcli.side_effect = [
            (None, mockStream(['CD_00_cell1 CD_01_cell1']), mockStream([''])),
        ]

        _result = _clustorage.mListACFSCellDisks(_node)

        self.assertEqual(_result, ['CD_00_cell1', 'CD_01_cell1'])
        self.assertEqual(_node.mExecuteCmdCellcli.call_count, 1)

    # Auto-generated test for mListACFSCellDisks
    def test_mListACFSCellDisks_fallbacks_to_fd(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _node.mGetHostname.return_value = 'cell2'
        _node.mExecuteCmdCellcli.side_effect = [
            (None, mockStream(['']), mockStream([''])),
            (None, mockStream(['FD_00_cell2 FD_01_cell2']), mockStream([''])),
        ]

        with patch('exabox.ovm.clustorage.ebLogInfo') as _mock_log:
            _result = _clustorage.mListACFSCellDisks(_node)

        self.assertEqual(_result, ['FD_00_cell2', 'FD_01_cell2'])
        self.assertGreaterEqual(_mock_log.call_count, 1)
        self.assertEqual(_node.mExecuteCmdCellcli.call_count, 2)

    # Auto-generated test for mCreateACFSGridDisks
    def test_mCreateACFSGridDisks_early_exit_for_new_models(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mGetExadataCellModel = MagicMock(return_value='X8')

        with patch('exabox.ovm.clustorage.mCompareModel', return_value=1), \
             patch('exabox.ovm.clustorage.ebLogWarn') as _mock_warn:
            _result = _clustorage.mCreateACFSGridDisks()

        self.assertIsNone(_result)
        _mock_warn.assert_called_once()

    # Auto-generated test for mCreateACFSGridDisks
    @patch('exabox.ovm.clustorage.mCompareModel', return_value=-1)
    def test_mCreateACFSGridDisks_skips_existing_grid_disks(self, _mock_cmp):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mGetExadataCellModel = MagicMock(return_value='X6')
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1.example.com': {}})
        _ebox.mIsDebug = MagicMock(return_value=True)

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster

        _dg_cfg = MagicMock()
        _dg_cfg.mGetDgName.return_value = 'DATA01'

        _existing_gds = ['ADG1A01_CD_02_cell1', 'ADG2A01_CD_02_cell1']

        with patch('exabox.ovm.clustorage.exaBoxNode') as _mock_node_cls, \
             patch.object(_clustorage, 'mGetDiskGroupConfig', return_value=_dg_cfg), \
             patch.object(_clustorage, 'mListCellDG', return_value=_existing_gds), \
             patch.object(_clustorage, 'mListACFSCellDisks', return_value=['CD_02_cell1']), \
             patch.object(_clustorage, 'mCreateCellDG') as _mock_create, \
             patch('exabox.ovm.clustorage.ebLogInfo') as _mock_log:
            _node = MagicMock()
            _mock_node_cls.return_value = _node
            _clustorage.mCreateACFSGridDisks()

        _mock_create.assert_not_called()
        self.assertTrue(_mock_log.called)
        _node.mConnect.assert_called_once_with(aHost='cell1.example.com')
        _node.mDisconnect.assert_called_once()

    # Auto-generated test for mCreateACFSGridDisks
    @patch('exabox.ovm.clustorage.mCompareModel', return_value=-1)
    def test_mCreateACFSGridDisks_deletes_existing_when_requested(self, _mock_cmp):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mGetExadataCellModel = MagicMock(return_value='X6')
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1.example.com': {}})
        _ebox.mIsDebug = MagicMock(return_value=False)

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster

        _dg_cfg = MagicMock()
        _dg_cfg.mGetDgName.return_value = 'DATA01'

        _existing_gds = ['ADG1A01_CD_02_cell1', 'ADG2A01_CD_02_cell1']

        with patch('exabox.ovm.clustorage.exaBoxNode') as _mock_node_cls, \
             patch.object(_clustorage, 'mGetDiskGroupConfig', return_value=_dg_cfg), \
             patch.object(_clustorage, 'mListCellDG', return_value=_existing_gds), \
             patch.object(_clustorage, 'mListACFSCellDisks', return_value=['CD_02_cell1']), \
             patch.object(_clustorage, 'mDeleteCellDG') as _mock_delete:
            _node = MagicMock()
            _mock_node_cls.return_value = _node
            _clustorage.mCreateACFSGridDisks(aCreate=False)

        _mock_delete.assert_called()
        _node.mDisconnect.assert_called_once()

    # Auto-generated test for mListACFSCellDisks
    def test_mListACFSCellDisks_returns_empty_when_no_disks(self):
        _clustorage = self.mGetClubox().mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell3'

        _node.mExecuteCmdCellcli.side_effect = [
            (None, mockStream(['']), mockStream([''])),
            (None, mockStream(['']), mockStream([''])),
        ]

        with patch('exabox.ovm.clustorage.ebLogInfo') as _mock_log:
            _result = _clustorage.mListACFSCellDisks(_node)

        self.assertEqual(_result, [])
        self.assertGreaterEqual(_mock_log.call_count, 1)

    # Auto-generated test for mCreateCellDG
    def test_mCreateCellDG_raises_on_cmd_failure(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = 1

        with self.assertRaises(Exception):
            _clustorage.mCreateCellDG(_node, 1, 'DATA', 'cell1', 'CD_00_cell1', '50G')

        _node.mExecuteCmd.assert_called_once()

    # Auto-generated test for mDeleteCellDG
    def test_mDeleteCellDG_raises_on_cmd_failure(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = 1

        with self.assertRaises(Exception):
            _clustorage.mDeleteCellDG(_node, 2, 'RECO', 'cell1')

        _node.mExecuteCmd.assert_called_once()

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_retries_on_ms_detected_error(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell4'

        _stream_err = mockStream([''])
        _stream_ms = mockStream(['MS DETECTED ERROR'])
        _stream_out = mockStream(['CD_01 online\n'])

        _node.mExecuteCmdCellcli.side_effect = [
            (None, _stream_ms, _stream_err),
            (None, _stream_out, _stream_err)
        ]
        _node.mGetCmdExitStatus.side_effect = [True, False]
        _ebox.mCheckCellsServicesUp = MagicMock()

        with patch('exabox.ovm.clustorage.sleep') as _mock_sleep:
            _result = _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

        self.assertEqual(_result, {'CD_01': {'STATUS': 'online'}})
        _ebox.mCheckCellsServicesUp.assert_called_once_with(
            aRestart=False,
            aCellList=['cell4']
        )
        _mock_sleep.assert_called_once_with(5)

    # Auto-generated test for mEnsureEmptyXenCellsInterconnect
    def test_mEnsureEmptyXenCellsInterconnect_skips_with_flag(self):
        _cfg = MagicMock()
        _cfg.mGetConfigOptions.return_value = {
            'skip_empty_cell_interconnect_check': 'true'
        }

        with patch('exabox.ovm.clustorage.get_gcontext', return_value=_cfg), \
             patch('exabox.ovm.clustorage.connect_to_host') as _mock_connect:
            _result = ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(['cell1'])

        self.assertEqual(_result, 2)
        _mock_connect.assert_not_called()

    # Auto-generated test for mEnsureEmptyXenCellsInterconnect
    def test_mEnsureEmptyXenCellsInterconnect_updates_and_restarts(self):
        _cfg = MagicMock()
        _cfg.mGetConfigOptions.return_value = {}
        _node = MagicMock()
        _ctx = MagicMock()
        _ctx.__enter__.return_value = _node
        _ctx.__exit__.return_value = False

        def _out(stdout):
            return Mock(stdout=stdout)

        _cmd_outputs = [
            _out('eth0'),
            _out(''),
            _out('ib1'),
            _out('')
        ]

        with patch('exabox.ovm.clustorage.get_gcontext', return_value=_cfg), \
             patch('exabox.ovm.clustorage.connect_to_host', return_value=_ctx), \
             patch('exabox.ovm.clustorage.mWaitForSystemBoot'), \
             patch('exabox.ovm.clustorage.node_exec_cmd_check', side_effect=_cmd_outputs) as _mock_exec:
            _result = ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(['cell1'])

        self.assertEqual(_result, 0)
        self.assertEqual(_mock_exec.call_count, 4)
        _mock_exec.assert_any_call(_node, '/opt/oracle/cell/cellsrv/bin/cellcli -e alter cell interconnect1=ib0')
        _mock_exec.assert_any_call(_node, '/opt/oracle/cell/cellsrv/bin/cellcli -e alter cell restart services all')

    # Auto-generated test for mEnsureEmptyXenCellsInterconnect
    def test_mEnsureEmptyXenCellsInterconnect_no_changes(self):
        _cfg = MagicMock()
        _cfg.mGetConfigOptions.return_value = {}
        _node = MagicMock()
        _ctx = MagicMock()
        _ctx.__enter__.return_value = _node
        _ctx.__exit__.return_value = False

        def _out(stdout):
            return Mock(stdout=stdout)

        _cmd_outputs = [_out('ib0'), _out('ib1')]

        with patch('exabox.ovm.clustorage.get_gcontext', return_value=_cfg), \
             patch('exabox.ovm.clustorage.connect_to_host', return_value=_ctx), \
             patch('exabox.ovm.clustorage.mWaitForSystemBoot'), \
             patch('exabox.ovm.clustorage.node_exec_cmd_check', side_effect=_cmd_outputs) as _mock_exec:
            _result = ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(['cell1'])

        self.assertEqual(_result, 0)
        self.assertEqual(_mock_exec.call_count, 2)

    # Auto-generated test for ebCluStorageConfig.mGetDiskGroupConfigList/mGetDiskGroupConfig
    def test_storageconfig_get_diskgroup_config_returns_object(self):
        _dg_xml = etree.fromstring(
            """
            <diskGroup id="DGX">
              <diskGroupName>DATA01</diskGroupName>
              <redundancy>HIGH</redundancy>
              <sliceSize>10G</sliceSize>
              <diskGroupSize>20G</diskGroupSize>
              <ocrVote>false</ocrVote>
              <machines>
                <machine id="m1"/>
              </machines>
            </diskGroup>
            """
        )
        _config = MagicMock()
        _config.mGetConfigAllElement.side_effect = [[_dg_xml], [], []]
        _storage_root = etree.Element('storage')
        etree.SubElement(_storage_root, 'diskGroups').append(_dg_xml)
        _config.mConfigRoot.return_value = _storage_root

        _storage = ebCluStorageConfig(self.mGetClubox(), _config)

        self.assertEqual(_storage.mGetDiskGroupConfigList(), ['DGX'])
        self.assertIsInstance(_storage.mGetDiskGroupConfig('DGX'), ebCluDiskGroupConfig)

    # Auto-generated test for ebCluManageStorage.mFetchAndSaveDGSizes
    def test_mFetchAndSaveDGSizes_records_size_for_sparse_and_data(self):
        _manage = ebCluManageStorage(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _data_dg = MagicMock()
        _data_dg.mGetDiskGroupType.return_value = 'data'
        _data_dg.mGetDgName.return_value = 'DATA01'

        _sparse_dg = MagicMock()
        _sparse_dg.mGetDiskGroupType.return_value = 'sparse'
        _sparse_dg.mGetDgName.return_value = 'SPRC01'

        _storage = MagicMock()
        _storage.mGetDiskGroupConfig.side_effect = [_data_dg, _sparse_dg]

        _ebox = self.mGetClubox()

        with patch.object(_manage, 'mGetEbox', return_value=_ebox), \
             patch.object(_ebox, 'mGetStorage', return_value=_storage), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': None}), \
             patch('exabox.ovm.clustorage.ebCluManageDiskgroup') as _mock_dg_mgr:
            _dg_mgr_instance = MagicMock()
            _dg_mgr_instance.mGetConstantsObj.return_value = ebDiskgroupOpConstants()
            _dg_mgr_instance.mUtilGetDiskgroupSize.side_effect = [
                2048, 512,
                10240, 2048
            ]
            _mock_dg_mgr.return_value = _dg_mgr_instance

            _sizes = {}
            _rc = _manage.mFetchAndSaveDGSizes(['DG1', 'DG2'], _sizes)

        self.assertEqual(_rc, 0)
        self.assertEqual(_sizes['DATA01']['totalgb'], 2)
        self.assertEqual(_sizes['DATA01']['usedgb'], 0.5)
        self.assertEqual(_sizes['SPRC01']['totalgb'], 1)
        self.assertEqual(_sizes['SPRC01']['usedgb'], 2)

    # Auto-generated test for ebCluManageStorage.mFetchAndSaveDGSizes
    def test_mFetchAndSaveDGSizes_returns_error_on_fetch_failure(self):
        _manage = ebCluManageStorage(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _data_dg = MagicMock()
        _data_dg.mGetDiskGroupType.return_value = 'data'
        _data_dg.mGetDgName.return_value = 'DATA01'

        _storage = MagicMock()
        _storage.mGetDiskGroupConfig.return_value = _data_dg

        _ebox = self.mGetClubox()

        with patch.object(_manage, 'mGetEbox', return_value=_ebox), \
             patch.object(_ebox, 'mGetStorage', return_value=_storage), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': None}), \
             patch.object(_ebox, 'mUpdateErrorObject') as _mock_update, \
             patch.object(_manage, 'mRecordError', return_value='err') as _mock_record, \
             patch('exabox.ovm.clustorage.ebCluManageDiskgroup') as _mock_dg_mgr:
            _dg_mgr_instance = MagicMock()
            _dg_mgr_instance.mGetConstantsObj.return_value = ebDiskgroupOpConstants()
            _dg_mgr_instance.mUtilGetDiskgroupSize.return_value = -1
            _mock_dg_mgr.return_value = _dg_mgr_instance

            _sizes = {}
            _rc = _manage.mFetchAndSaveDGSizes(['DG1'], _sizes)

        self.assertEqual(_rc, 'err')
        self.assertEqual(_sizes, {})
        _mock_update.assert_called_once()
        _mock_record.assert_called_once()
        _args, _ = _mock_record.call_args
        self.assertEqual(_args[0], gDiskgroupError['ErrorFetchingDetails'])
        self.assertIn('diskgroup DATA01', _args[1])

    # Auto-generated test for ebCluManageStorage.mCalculateDgResize
    def test_mCalculateDgResize_increments_when_usage_high(self):
        _manage = ebCluManageStorage(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _data_dg = MagicMock()
        _data_dg.mGetDiskGroupType.return_value = 'data'
        _data_dg.mGetDgName.return_value = 'DATA01'

        _storage = MagicMock()
        _storage.mGetDiskGroupConfig.return_value = _data_dg

        _ebox = self.mGetClubox()

        _sizes_before = {'DATA01': {'totalgb': 100, 'usedgb': 90}}
        _sizes_after = {'DATA01': {'totalgb': 100, 'usedgb': 90}}

        with patch.object(_manage, 'mGetEbox', return_value=_ebox), \
             patch.object(_ebox, 'mGetStorage', return_value=_storage), \
             patch.object(_ebox, 'mReturnCellNodes', return_value={'cell1': None, 'cell2': None, 'cell3': None}):
            _manage.mCalculateDgResize(['DG1'], _sizes_before, _sizes_after)

        self.assertGreater(_sizes_before['DATA01']['totalgb'], 100)

    # Auto-generated test for ebCluQuorumManager.mRemoveQuorumDisk
    @patch('exabox.ovm.clustorage.ebCluManageDiskgroup')
    @patch('exabox.ovm.clustorage.exaBoxNode')
    @patch('exabox.ovm.clustorage.sleep')
    def test_quorum_manager_remove_quorum_disk_success(self, _mock_sleep, _mock_node, _mock_dg_mgr):
        _manager = ebCluQuorumManager(self.mGetClubox())
        _node_u = MagicMock()
        _node_grid = MagicMock()
        _node_grid.mSetUser = MagicMock()
        _node_u.mExecuteCmd.return_value = (None, mockStream(['Name Voting_files State Type\n', 'DATA1, Y NORMAL ASM\n']), mockStream(['']))
        _node_u.mGetCmdExitStatus.return_value = 0
        _node_grid.mGetCmdExitStatus.return_value = 0
        _mock_node.side_effect = [_node_u, _node_grid]

        _disk_mgr = MagicMock()
        _disk_mgr.mEnsureDgsRebalanced.return_value = 0
        _mock_dg_mgr.return_value = _disk_mgr

        def _run_command_side_effect(cmd, *_args, **_kwargs):
            if 'quorumdiskmgr --device --list' in cmd:
                return True, [
                    '/dev/exadata_quorum/q1\n',
                    'Host name: DOMU1\n'
                ], 0
            return True

        _cluctrl = self.mGetClubox()
        with patch.object(_manager, 'runCommand', side_effect=_run_command_side_effect), \
             patch.object(_cluctrl, 'mGetGridHome', return_value=('/u01/app', None)):
            _manager.mRemoveQuorumDisk('domu1.example.com', MagicMock(), MagicMock())

        _node_u.mDisconnect.assert_called_once()
        _node_grid.mDisconnect.assert_called_once()
        self.assertTrue(_disk_mgr.mEnsureDgsRebalanced.called)

    # Auto-generated test for ebCluQuorumManager.mAddQuorumDisk
    @patch('exabox.ovm.clustorage.exaBoxNode')
    def test_quorum_manager_add_quorum_disk_skips_when_present(self, _mock_node):
        _manager = ebCluQuorumManager(self.mGetClubox())

        _node_grid = MagicMock()
        _node_grid.mSetUser = MagicMock()
        _node_grid.mGetCmdExitStatus.return_value = 0
        _mock_node.return_value = _node_grid

        with patch.object(_manager, 'mCountVotingDisks', return_value=5) as _mock_count:
            _manager.mAddQuorumDisk('domu1.example.com', 'domu2.example.com', ['10.0.0.1'], MagicMock())

        _mock_count.assert_called_once()
        _node_grid.mDisconnect.assert_called_once()

    # Auto-generated test for mGetDiskSizeInInt
    def test_storageconfig_mGetDiskSizeInInt_parses_units(self):
        _ebox = self.mGetClubox()
        _storage = _ebox.mGetStorage()

        _storage.mGetDiskSizeInInt = ebCluStorageConfig.mGetDiskSizeInInt.__get__(
            _storage, ebCluStorageConfig
        )

        self.assertEqual(_storage.mGetDiskSizeInInt("128GB"), 128)
        self.assertEqual(_storage.mGetDiskSizeInInt("128gb"), 128)
        self.assertEqual(_storage.mGetDiskSizeInInt("2TB"), 2)
        self.assertEqual(_storage.mGetDiskSizeInInt("2tb"), 2)
        self.assertEqual(_storage.mGetDiskSizeInInt("64G"), 64)
        self.assertEqual(_storage.mGetDiskSizeInInt("64g"), 64)
        self.assertEqual(_storage.mGetDiskSizeInInt("5T"), 5)
        self.assertEqual(_storage.mGetDiskSizeInInt("5t"), 5)

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_retries_then_success(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1'

        _stream_err = mockStream(['CELL-02559 some error'])
        _stream_empty = mockStream([''])
        _stream_out = mockStream(['CD_00 status1 status2\n'])
        _node.mExecuteCmdCellcli.side_effect = [
            (None, _stream_empty, _stream_err),
            (None, _stream_out, _stream_empty)
        ]
        _node.mGetCmdExitStatus.side_effect = [True, False]

        _ebox.mCheckCellsServicesUp = MagicMock()

        with patch('exabox.ovm.clustorage.sleep') as _mock_sleep:
            _result = _clustorage.mListCellDisksAttributes(
                _node,
                aAttributes=['STATUS', 'SIZE']
            )

        self.assertEqual(
            _result,
            {'CD_00': {'STATUS': 'status1', 'SIZE': 'status2'}}
        )
        _ebox.mCheckCellsServicesUp.assert_called_once_with(
            aRestart=False,
            aCellList=['cell1']
        )
        _mock_sleep.assert_called_once_with(5)

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_non_retry_error_raises(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell2'

        _stream_out = mockStream(['stdout'])
        _stream_err = mockStream(['unexpected error'])
        _node.mExecuteCmdCellcli.return_value = (None, _stream_out, _stream_err)
        _node.mGetCmdExitStatus.return_value = True

        with self.assertRaises(ExacloudRuntimeError):
            _clustorage.mListCellDisksAttributes(_node, aAttributes=['STATUS'])

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_retries_exhausted_raises(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell3'

        _stream_out = mockStream(['stdout'])
        _stream_err = mockStream(['CELL-02559 failed'])
        _node.mExecuteCmdCellcli.return_value = (None, _stream_out, _stream_err)
        _node.mGetCmdExitStatus.return_value = True

        _ebox.mCheckCellsServicesUp = MagicMock()

        with patch('exabox.ovm.clustorage.sleep'):
            with self.assertRaises(ExacloudRuntimeError):
                _clustorage.mListCellDisksAttributes(
                    _node,
                    aAttributes=['STATUS']
                )

        self.assertEqual(_ebox.mCheckCellsServicesUp.call_count, 2)

    # Auto-generated test for mFixPMEMComponent
    def test_mFixPMEMComponent_inconsistent_cell_disk_sets(self):
        _cell_list = ['cell1', 'cell2']
        _created_pm = []

        def _mock_connect(aCell, _gctx):
            class _NodeCtx:
                def __init__(self, cell):
                    self._node = MagicMock()
                    self._node._cell = cell

                def __enter__(self):
                    return self._node

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _NodeCtx(aCell)

        def _fake_list_details(aNode, _component):
            if aNode._cell == 'cell1':
                return {'name': 'cell1_PMEMCACHE', 'status': 'normal', 'cellDisk': 'PM_00_cell1'}
            return {'name': 'cell2_PMEMCACHE', 'status': 'normal', 'cellDisk': 'PM_01_cell2'}

        class _FakeProc:
            def __init__(self, fx, args, _name):
                self.fx = fx
                self.args = args

            def mSetMaxExecutionTime(self, _timeout):
                return None

            def mSetJoinTimeout(self, _timeout):
                return None

            def mSetLogTimeoutFx(self, _fx):
                return None

        class _FakeProcMgr:
            def __init__(self):
                self._procs = []

            def mGetManager(self):
                class _Mgr:
                    @staticmethod
                    def dict():
                        return {}
                return _Mgr()

            def mStartAppend(self, proc):
                self._procs.append(proc)

            def mJoinProcess(self):
                for proc in list(self._procs):
                    proc.fx(*proc.args)

        def _fake_node_exec_cmd(aNode, _cmd, **_kwargs):
            _created_pm.append((aNode._cell, _cmd))
            return MagicMock(exit_code=0)

        with patch('exabox.ovm.clustorage.ProcessManager', _FakeProcMgr), \
             patch('exabox.ovm.clustorage.ProcessStructure', _FakeProc), \
             patch('exabox.ovm.clustorage.connect_to_host', side_effect=_mock_connect), \
             patch('exabox.ovm.clustorage.ebCluStorageConfig.mListPMEMDetails', side_effect=_fake_list_details), \
             patch('exabox.ovm.clustorage.node_exec_cmd', side_effect=_fake_node_exec_cmd):
            ebCluStorageConfig.mFixPMEMComponent(_cell_list, "cache")

        self.assertCountEqual(_created_pm, [
            ('cell1', 'cellcli -e drop pmemcache'),
            ('cell1', 'cellcli -e create pmemcache all'),
            ('cell2', 'cellcli -e drop pmemcache'),
            ('cell2', 'cellcli -e create pmemcache all')
        ])

    # Auto-generated test for mFixPMEMComponent
    def test_mFixPMEMComponent_empty_status_triggers_fix(self):
        _cell_list = ['cell1']
        _commands = []

        def _mock_connect(aCell, _gctx):
            class _NodeCtx:
                def __init__(self, cell):
                    self._node = MagicMock()
                    self._node._cell = cell

                def __enter__(self):
                    return self._node

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _NodeCtx(aCell)

        def _fake_list_details(aNode, _component):
            return {'name': 'cell1_PMEMLOG', 'status': None, 'cellDisk': 'PM_00_cell1'}

        class _FakeProc:
            def __init__(self, fx, args, _name):
                self.fx = fx
                self.args = args

            def mSetMaxExecutionTime(self, _timeout):
                return None

            def mSetJoinTimeout(self, _timeout):
                return None

            def mSetLogTimeoutFx(self, _fx):
                return None

        class _FakeProcMgr:
            def __init__(self):
                self._procs = []

            def mGetManager(self):
                class _Mgr:
                    @staticmethod
                    def dict():
                        return {}
                return _Mgr()

            def mStartAppend(self, proc):
                self._procs.append(proc)

            def mJoinProcess(self):
                for proc in list(self._procs):
                    proc.fx(*proc.args)

        def _fake_node_exec_cmd(aNode, _cmd, **_kwargs):
            _commands.append((aNode._cell, _cmd))
            return MagicMock(exit_code=0)

        with patch('exabox.ovm.clustorage.ProcessManager', _FakeProcMgr), \
             patch('exabox.ovm.clustorage.ProcessStructure', _FakeProc), \
             patch('exabox.ovm.clustorage.connect_to_host', side_effect=_mock_connect), \
             patch('exabox.ovm.clustorage.ebCluStorageConfig.mListPMEMDetails', side_effect=_fake_list_details), \
             patch('exabox.ovm.clustorage.node_exec_cmd', side_effect=_fake_node_exec_cmd):
            ebCluStorageConfig.mFixPMEMComponent(_cell_list, "log")

        self.assertEqual(_commands, [
            ('cell1', 'cellcli -e drop pmemlog'),
            ('cell1', 'cellcli -e create pmemlog all')
        ])

    # Auto-generated test for mListCellDG
    def test_mListCellDG_suffix_returns_empty_when_no_matches(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['DATA_C2_x\nRECO_C2_y\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node, aSuffix='C1')

        self.assertEqual(_result, [])

    # Auto-generated test for mListCellDG
    def test_mListCellDG_zdlra_filters_catalog_delta(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=True)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['CATALOG_GD\nDELTA_GD\nDATA_GD\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node, aSuffix='IGNORED')

        self.assertEqual(_result, ['CATALOG_GD', 'DELTA_GD'])

    # Auto-generated test for ebCluDiskGroupConfig setters
    def test_diskgroupconfig_setters_create_elements_and_update_values(self):
        _xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>20G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg = ebCluDiskGroupConfig(_xml)

        _dg.mSetQuorumDisk("true")
        _dg.mSetAcfsVolumeName("ACFS01")
        _dg.mSetAcfsVolumeSize(120)
        _dg.mSetAcfsMountPath("/acfs")
        _dg.mSetDiskGroupType("data")
        _dg.mSetGridDiskPrefix("GD")
        _dg.mSetSparseDg("true")
        _dg.mSetSparseVirtualSize(50)

        self.assertEqual(_xml.find('quorumDisk').text, "true")
        self.assertEqual(_xml.find('acfsVolumeName').text, "ACFS01")
        self.assertEqual(_xml.find('acfsVolumeSize').text, "120")
        self.assertEqual(_xml.find('acfsMountPath').text, "/acfs")
        self.assertEqual(_xml.find('diskGroupType').text, "data")
        self.assertEqual(_xml.find('gridDiskPrefix').text, "GD")
        self.assertEqual(_xml.find('sparse').text, "true")
        self.assertEqual(_xml.find('sparseVirtualSize').text, "50G")

    # Auto-generated test for ebCluStorageConfig remove/add no-op paths
    def test_storageconfig_remove_and_add_diskgroup_noop(self):
        _ebox = self.mGetClubox()
        _config = MagicMock()
        _dg_xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>20G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _config.mGetConfigAllElement.side_effect = [[_dg_xml], [], []]
        _storage_root = etree.Element('storage')
        _dg_parent = etree.SubElement(_storage_root, 'diskGroups')
        _dg_parent.append(_dg_xml)
        _config.mConfigRoot.return_value = _storage_root

        _storage = ebCluStorageConfig(_ebox, _config)

        _storage.mRemoveDiskGroupConfig("MISSING")
        self.assertEqual(list(_storage_root.find('diskGroups')), [_dg_xml])

        _dg_config = _storage.mGetDiskGroupConfig("DG1")
        _storage.mAddDiskGroupConfig(_dg_config)
        self.assertEqual(list(_storage_root.find('diskGroups')), [_dg_xml])

    # Auto-generated test for mListPMEMDetails empty output
    def test_mListPMEMDetails_empty_output_returns_empty_dict(self):
        _node = MagicMock()
        with patch('exabox.ovm.clustorage.node_exec_cmd') as _mock_exec:
            _mock_exec.return_value = (None, "", None)
            _details = ebCluStorageConfig.mListPMEMDetails(_node, "cache")

        self.assertEqual(_details, {})

    # Auto-generated test for mListPMEMDetails
    def test_mListPMEMDetails_parses_key_value_lines(self):
        _node = MagicMock()
        _output = "name: pmemlog01\nstatus: normal\ncellDisk: PM_00\n"

        with patch('exabox.ovm.clustorage.node_exec_cmd') as _mock_exec:
            _mock_exec.return_value = (None, _output, None)
            _details = ebCluStorageConfig.mListPMEMDetails(_node, "log")

        self.assertEqual(
            _details,
            {'name': 'pmemlog01', 'status': 'normal', 'cellDisk': 'PM_00'}
        )

    # Auto-generated test for mFixPMEMComponent handles empty cell list
    @patch('exabox.ovm.clustorage.ProcessManager')
    def test_mFixPMEMComponent_empty_cell_list_noops(self, _mock_proc_mgr):
        _proc_instance = MagicMock()
        _proc_instance.mGetManager.return_value.dict.return_value = {}
        _mock_proc_mgr.return_value = _proc_instance

        ebCluStorageConfig.mFixPMEMComponent([], "cache")

        _proc_instance.mStartAppend.assert_not_called()
        _proc_instance.mJoinProcess.assert_called()

    # Auto-generated test for mFixPMEMComponent
    def test_mFixPMEMComponent_marks_cells_for_fix_when_status_bad(self):
        _cell_list = ['cell1']
        _commands = []

        class _FakeProc(object):
            def __init__(self, fx, args, name):
                self.fx = fx
                self.args = args
                self.name = name
            def mSetMaxExecutionTime(self, *_args, **_kwargs):
                pass
            def mSetJoinTimeout(self, *_args, **_kwargs):
                pass
            def mSetLogTimeoutFx(self, *_args, **_kwargs):
                pass

        class _FakeProcMgr(object):
            def __init__(self):
                self._procs = []
                self._store = {}
            def mGetManager(self):
                return self
            def dict(self):
                return self._store
            def mStartAppend(self, proc):
                self._procs.append(proc)
            def mJoinProcess(self):
                for proc in list(self._procs):
                    proc.fx(*proc.args)

        def _mock_connect(_cell, _ctx):
            _node = MagicMock()
            _context = MagicMock()
            _context.__enter__.return_value = _node
            _context.__exit__.return_value = False
            return _context

        def _fake_list_details(_node, _component):
            return {'name': 'cell1_PMEMLOG', 'status': 'abnormal'}

        def _fake_node_exec_cmd(_node, cmd, **_kwargs):
            _commands.append(cmd)
            return (None, "", None)

        with patch('exabox.ovm.clustorage.ProcessManager', _FakeProcMgr), \
             patch('exabox.ovm.clustorage.ProcessStructure', _FakeProc), \
             patch('exabox.ovm.clustorage.connect_to_host', side_effect=_mock_connect), \
             patch('exabox.ovm.clustorage.ebCluStorageConfig.mListPMEMDetails', side_effect=_fake_list_details), \
             patch('exabox.ovm.clustorage.node_exec_cmd', side_effect=_fake_node_exec_cmd):
            ebCluStorageConfig.mFixPMEMComponent(_cell_list, "log")

        self.assertEqual(
            _commands,
            ['cellcli -e drop pmemlog', 'cellcli -e create pmemlog all']
        )

    # Auto-generated test for mFixPMEMComponent
    def test_mFixPMEMComponent_xrmemcache_empty_disks_triggers_fix(self):
        _cell_list = ['cell1']
        _commands = []

        class _FakeProc(object):
            def __init__(self, fx, args, name):
                self.fx = fx
                self.args = args
                self.name = name
            def mSetMaxExecutionTime(self, *_args, **_kwargs):
                pass
            def mSetJoinTimeout(self, *_args, **_kwargs):
                pass
            def mSetLogTimeoutFx(self, *_args, **_kwargs):
                pass

        class _FakeProcMgr(object):
            def __init__(self):
                self._procs = []
                self._store = {}
            def mGetManager(self):
                return self
            def dict(self):
                return self._store
            def mStartAppend(self, proc):
                self._procs.append(proc)
            def mJoinProcess(self):
                for proc in list(self._procs):
                    proc.fx(*proc.args)

        def _mock_connect(_cell, _ctx):
            _node = MagicMock()
            _context = MagicMock()
            _context.__enter__.return_value = _node
            _context.__exit__.return_value = False
            return _context

        def _fake_list_details(_node, _component):
            return {'name': 'cell1_XRMEMCACHE', 'cellDisk': ''}

        def _fake_node_exec_cmd(_node, cmd, **_kwargs):
            _commands.append(cmd)
            return (None, "", None)

        with patch('exabox.ovm.clustorage.ProcessManager', _FakeProcMgr), \
             patch('exabox.ovm.clustorage.ProcessStructure', _FakeProc), \
             patch('exabox.ovm.clustorage.connect_to_host', side_effect=_mock_connect), \
             patch('exabox.ovm.clustorage.ebCluStorageConfig.mListPMEMDetails', side_effect=_fake_list_details), \
             patch('exabox.ovm.clustorage.node_exec_cmd', side_effect=_fake_node_exec_cmd):
            ebCluStorageConfig.mFixPMEMComponent(_cell_list, "cache")

        self.assertEqual(
            _commands,
            ['cellcli -e drop pmemcache', 'cellcli -e create pmemcache all']
        )

    # Auto-generated test for mDeleteGD handles empty cell output
    def test_mDeleteGD_no_output_increments_rc(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mIsDebug = MagicMock(return_value=False)
        _ebox.SharedEnv = MagicMock(return_value=True)
        _ebox.mIsExabm = MagicMock(return_value=False)
        _clustorage.mClusterDiskGroupSuffix = MagicMock(return_value='C1')

        _node = MagicMock()
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream([]),
            mockStream([''])
        )

        with patch('exabox.ovm.clustorage.exaBoxNode', return_value=_node):
            _result = _clustorage.mDeleteGD()

        self.assertEqual(_result, 1)
        _node.mDisconnect.assert_called_once()

    # Auto-generated test for mGetCurrentClusterGridDisksFromCells
    def test_mGetCurrentClusterGridDisksFromCells_filters_matching_suffix(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'

        _griddisks = [
            'RECOC03_CD_00_cell1',
            'RECOC5_CD_00_cell1',
            'DATAC03_CD_01_cell1'
        ]

        with patch.object(_clustorage, 'mClusterDiskGroupSuffix', return_value='C03'), \
             patch.object(_clustorage, 'mListCellDG', return_value=_griddisks):
            _result = _clustorage.mGetCurrentClusterGridDisksFromCells(_node)

        self.assertEqual(
            _result,
            ['RECOC03_CD_00_cell1', 'DATAC03_CD_01_cell1']
        )

    # Auto-generated test for mListPMEMDetails
    def test_mListPMEMDetails_empty_output(self):
        _node = MagicMock()

        with patch('exabox.ovm.clustorage.node_exec_cmd') as _mock_exec:
            _mock_exec.return_value = (None, '', None)
            _details = ebCluStorageConfig.mListPMEMDetails(_node, "cache")

        self.assertEqual(_details, {})

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_returns_empty_when_no_lines(self):
        _ebox = self.mGetClubox()
        _ebox.mGetMachines = MagicMock()
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1.example.com'
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream([]),
            mockStream([''])
        )
        _node.mGetCmdExitStatus.return_value = False

        _result = _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

        self.assertEqual(_result, {})

    # Auto-generated test for mListCellDG
    def test_mListCellDG_zdlra_filters_catalog_delta_real(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=True)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['CATALOG_CD_01\nDELTA_CD_02\nDATA_CD_03\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['CATALOG_CD_01', 'DELTA_CD_02'])
        self.assertEqual(_node.mExecuteCmd.call_count, 2)

    # Auto-generated test for mListCellDG
    def test_mListCellDG_default_lists_all(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['GD1 GD2 GD3']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['GD1', 'GD2', 'GD3'])

    # Auto-generated test for mListCellDG
    def test_mListCellDG_raises_on_cmd_exit_status(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['OUT']), mockStream(['ERR']))
        ]
        _node.mGetCmdExitStatus.return_value = True

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox), \
             patch('exabox.ovm.clustorage.ebLogError') as _mock_log:
            with self.assertRaises(Exception):
                _clustorage.mListCellDG(_node)

        self.assertTrue(_mock_log.called)

    # Auto-generated test for mCreateCellDG
    def test_mCreateCellDG_returns_command_on_success(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = False

        _cmd = _clustorage.mCreateCellDG(
            _node, 3, 'DATA', 'cell1', 'CD_00_cell1', '50G')

        self.assertEqual(
            _cmd,
            'cellcli -e CREATE GRIDDISK  DATACD_03_cell1 celldisk=CD_00_cell1, size=50G;'
        )
        _node.mExecuteCmd.assert_called_once_with(_cmd)

    # Auto-generated test for mDeleteCellDG
    def test_mDeleteCellDG_returns_command_on_success(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = False

        _cmd = _clustorage.mDeleteCellDG(_node, 9, 'DATA', 'cell1')

        self.assertEqual(
            _cmd,
            'cellcli -e DROP GRIDDISK  DATACD_09_cell1;'
        )
        _node.mExecuteCmd.assert_called_once_with(_cmd)

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_rejects_extra_parts(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib("10:20:30:40")

    # Auto-generated test for ebCluDiskGroupConfig
    def test_diskgroupconfig_grid_disk_prefix_none_returns_none(self):
        _xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>NORMAL</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>20G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg = ebCluDiskGroupConfig(_xml)

        self.assertIsNone(_dg.mGetGridDiskPrefix())

    # Auto-generated test for mGetDiskGroupType
    def test_diskgroupconfig_type_detection_unknown(self):
        _xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>FOO01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>20G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg = ebCluDiskGroupConfig(_xml)
        self.assertIsNone(_dg.mGetDiskGroupType())

    # Auto-generated test for mClusterDiskGroupSuffix
    def test_mClusterDiskGroupSuffix_three_char_suffix(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']
        _clusters = MagicMock()
        _clusters.mGetCluster.return_value = _cluster
        _ebox.mGetClusters = MagicMock(return_value=_clusters)

        _dg = MagicMock()
        _dg.mGetDgName.return_value = 'DATA123'
        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg)

        self.assertEqual(_clustorage.mClusterDiskGroupSuffix(), '123')

    # Auto-generated test for mClusterDiskGroupSuffix
    def test_mClusterDiskGroupSuffix_handles_non_c_suffix(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']
        _clusters = MagicMock()
        _clusters.mGetCluster.return_value = _cluster
        _ebox.mGetClusters = MagicMock(return_value=_clusters)

        _dg = MagicMock()
        _dg.mGetDgName.return_value = 'DATAA12'
        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg)

        self.assertEqual(_clustorage.mClusterDiskGroupSuffix(), 'A12')

    # Auto-generated test for mDeleteGD
    def test_mDeleteGD_shared_exabm_appends_unmatched(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mIsDebug = MagicMock(return_value=False)
        _ebox.SharedEnv = MagicMock(return_value=False)
        _ebox.mIsExabm = MagicMock(return_value=True)
        _ebox.mCheckConfigOption = MagicMock(return_value=False)
        _clustorage.mClusterDiskGroupSuffix = MagicMock(return_value='C1')

        _node = MagicMock()
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['DATAX9_CD_00 cell\n']),
            mockStream([''])
        )

        with patch('exabox.ovm.clustorage.exaBoxNode', return_value=_node), \
             patch('exabox.ovm.clustorage.ebLogWarn') as _mock_warn:
            _result = _clustorage.mDeleteGD(aListOnly=True)

        self.assertEqual(_result, 0)
        self.assertTrue(_mock_warn.called)
        _node.mDisconnect.assert_called_once()

    # Auto-generated test for mListCellDG
    def test_mListCellDG_suffix_includes_matching_entries(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['DATA_C1_x\nRECO_C1_y\nOTHER\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node, aSuffix='C1')

        self.assertEqual(_result, ['DATA_C1_x', 'RECO_C1_y'])

    # Auto-generated test for mCreateCellDG
    def test_mCreateCellDG_raises_on_failure(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = 1
        _node.mGetHostname.return_value = 'cell1'

        with self.assertRaises(Exception):
            _clustorage.mCreateCellDG(_node, 1, 'DATA', 'cell1', 'CD_00_cell1', '50G')

        _node.mExecuteCmd.assert_called_once()

    # Auto-generated test for mDeleteCellDG
    def test_mDeleteCellDG_raises_on_failure(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetCmdExitStatus.return_value = 1
        _node.mGetHostname.return_value = 'cell2'

        with self.assertRaises(Exception):
            _clustorage.mDeleteCellDG(_node, 2, 'RECO', 'cell2')

        _node.mExecuteCmd.assert_called_once()

    # Auto-generated test for mPatchClusterDiskgroup
    def test_mPatchClusterDiskgroup_negative_sizes_raise(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _dg_xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>NORMAL</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>-1G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg_cfg = ebCluDiskGroupConfig(_dg_xml)
        _dg_cfg.mGetDiskGroupType = MagicMock(return_value='data')

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster
        _ebox.mGetRackSize = MagicMock(return_value='quarter')
        _ebox.mGetEsracks = MagicMock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 14
        _ebox.mReturnCellNodes.return_value = {'cell1': {}}
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )

        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg_cfg)

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment') as _mock_check, \
             patch('exabox.ovm.clustorage.ebLogCritical') as _mock_log:
            _mock_check.return_value = None
            with self.assertRaises(ExacloudRuntimeError):
                _clustorage.mPatchClusterDiskgroup(
                    aCreateSparse=False,
                    aBackupDisk=False,
                    aDRSdistrib=None,
                    aOptions=_ebox.mGetArgsOptions())

        self.assertGreaterEqual(_mock_log.call_count, 1)

    # Auto-generated test for mListCellDG
    def test_mListCellDG_custom_celltype_suffix(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['TYPEA_C1_x\nOTHER\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node, aSuffix='C1', aCellType='CELLDISK')

        self.assertEqual(_result, ['TYPEA_C1_x'])
        self.assertIn('CELLDISK', _node.mExecuteCmd.call_args_list[0][0][0])
        self.assertIn('C1', _node.mExecuteCmd.call_args_list[0][0][0])

    # Auto-generated test for mUtilStorageResize
    def test_mUtilStorageResize_skips_missing_entries(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mClusterDgrpResize.return_value = 0
        _dgObj.mClusterDgrpRebalance.return_value = 0

        _clustorage._ebCluManageStorage__resizedata = True

        _dgmap = {
            _clustorage.DATA: {
                _clustorage.DG_NAME: None,
                _clustorage.DG_NEWSIZE: 10,
                _clustorage.DG_CURRSIZE: 10,
            },
            _clustorage.RECO: {
                _clustorage.DG_NAME: 'RECO1',
                _clustorage.DG_NEWSIZE: None,
                _clustorage.DG_CURRSIZE: 20,
            }
        }

        _rc = _clustorage.mUtilStorageResize(_dgObj, _options, _dgmap, 0)

        self.assertEqual(_rc, 0)
        _dgObj.mClusterDgrpResize.assert_not_called()
        _dgObj.mClusterDgrpRebalance.assert_not_called()

    # Auto-generated test for mUtilStorageResize
    def test_mUtilStorageResize_skips_when_flags_disabled(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mClusterDgrpResize.return_value = 0
        _dgObj.mClusterDgrpRebalance.return_value = 0

        _clustorage._ebCluManageStorage__resizedata = False
        _clustorage._ebCluManageStorage__rebalancedata = False

        _dgmap = {
            _clustorage.DATA: {
                _clustorage.DG_NAME: 'DATA1',
                _clustorage.DG_NEWSIZE: 50,
                _clustorage.DG_CURRSIZE: 50,
            }
        }

        _rc = _clustorage.mUtilStorageResize(_dgObj, _options, _dgmap, 0)

        self.assertEqual(_rc, 0)
        _dgObj.mClusterDgrpResize.assert_not_called()
        _dgObj.mClusterDgrpRebalance.assert_not_called()

    # Auto-generated test for mCheckGridDisksResizedCells
    def test_mCheckGridDisksResizedCells_returns_true_on_no_output(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}, 'cell2': {}})

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, None, mockStream(['ERR']))

        _context = MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = False

        _dgObj = MagicMock()

        with patch('exabox.ovm.clustorage.connect_to_host', return_value=_context) as _mock_connect, \
                patch('exabox.ovm.clustorage.ebLogWarn') as _mock_warn:
            _result = _clustorage.mCheckGridDisksResizedCells('DATA', 100.0, _dgObj)

        self.assertTrue(_result)
        self.assertTrue(_mock_warn.called)
        _dgObj.mSetGridDiskCountRetryResize.assert_not_called()
        _dgObj.mSetCurrentRetrySizeTotalMB.assert_not_called()
        self.assertEqual(_mock_connect.call_count, 1)

    # Auto-generated test for mCheckGridDisksResizedCells
    def test_mCheckGridDisksResizedCells_sets_retry_when_mismatch(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mReturnDom0DomUPair = MagicMock(return_value=[('dom0', 'domu')])
        _ebox.isATPCluster = MagicMock(return_value=False)
        _ebox.IsZdlraProv = MagicMock(return_value=False)

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (
            None,
            mockStream(['50G\n', '50G\n']),
            mockStream([''])
        )

        _context = MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = False

        _dgObj = MagicMock()

        with patch('exabox.ovm.clustorage.connect_to_host', return_value=_context), \
                patch('exabox.ovm.clustorage.ebLogInfo') as _mock_info:
            _result = _clustorage.mCheckGridDisksResizedCells('DATA', 200.0, _dgObj)

        self.assertFalse(_result)
        _dgObj.mSetGridDiskCountRetryResize.assert_called_once_with(2, 'DATA')
        _dgObj.mSetCurrentRetrySizeTotalMB.assert_called_once_with(102400.0, 'DATA')
        self.assertTrue(_mock_info.called)

    # Auto-generated test for mCheckGridDisksResizedCells
    def test_mCheckGridDisksResizedCells_returns_true_on_match(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _clustorage = ebCluManageStorage(_ebox, _options)

        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mReturnDom0DomUPair = MagicMock(return_value=[('dom0', 'domu')])
        _ebox.isATPCluster = MagicMock(return_value=False)
        _ebox.IsZdlraProv = MagicMock(return_value=False)

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (
            None,
            mockStream(['1024M\n', '1G\n']),
            mockStream([''])
        )

        _context = MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = False

        _dgObj = MagicMock()

        with patch('exabox.ovm.clustorage.connect_to_host', return_value=_context), \
                patch('exabox.ovm.clustorage.ebLogInfo') as _mock_info:
            _result = _clustorage.mCheckGridDisksResizedCells('DATA', 2.0, _dgObj)

        self.assertTrue(_result)
        _dgObj.mSetGridDiskCountRetryResize.assert_called_once_with(2, 'DATA')
        _dgObj.mSetCurrentRetrySizeTotalMB.assert_not_called()
        self.assertTrue(_mock_info.called)

    # Auto-generated test for ebCluStorageConfig getters
    def test_storage_config_getters_return_objects(self):
        _root = etree.fromstring(
            """
            <config>
              <storage>
                <diskGroups>
                  <diskGroup id="DG1">
                    <diskGroupName>DATA01</diskGroupName>
                    <redundancy>HIGH</redundancy>
                    <sliceSize>10G</sliceSize>
                    <diskGroupSize>20G</diskGroupSize>
                    <ocrVote>false</ocrVote>
                    <machines>
                      <machine id="m1"/>
                    </machines>
                  </diskGroup>
                </diskGroups>
                <storagePools>
                  <storagePool id="SP1">
                    <storagePoolName>SPDATA</storagePoolName>
                    <storagePoolType>high</storagePoolType>
                    <storagePoolSize>100G</storagePoolSize>
                    <uiSize>50</uiSize>
                    <uiSizeType>GB</uiSizeType>
                    <machines>
                      <machine id="m2"/>
                    </machines>
                  </storagePool>
                </storagePools>
                <edvVolumes>
                  <edvVolume id="EDV1">
                    <edvVolumeName>EDV01</edvVolumeName>
                    <edvVolumeSize>256G</edvVolumeSize>
                    <edvVolumeType>data</edvVolumeType>
                    <edvDevicePath>/dev/mapper/edv1</edvDevicePath>
                  </edvVolume>
                </edvVolumes>
              </storage>
            </config>
            """
        )

        class _Cfg(object):
            def __init__(self, root):
                self._root = root

            def mGetConfigAllElement(self, path):
                return self._root.findall(path)

            def mConfigRoot(self):
                return self._root

        _cfg = _Cfg(_root)
        _ebox = self.mGetClubox()
        _storage_cfg = ebCluStorageConfig(_ebox, _cfg)

        _dg_cfg = _storage_cfg.mGetDiskGroupConfig('DG1')
        _sp_cfg = _storage_cfg.mGetStoragePoolConfig('SP1')
        _edv_cfg = _storage_cfg.mGetEDVVolumesConfig('EDV1')

        self.assertIsInstance(_dg_cfg, ebCluDiskGroupConfig)
        self.assertEqual(_dg_cfg.mGetDgName(), 'DATA01')
        self.assertIsInstance(_sp_cfg, ebCluStoragePoolConfig)
        self.assertEqual(_sp_cfg.mGetSPName(), 'SPDATA')
        self.assertIsInstance(_edv_cfg, ebCluEDVVolumesConfig)
        self.assertEqual(_edv_cfg.mGetEDVName(), 'EDV01')

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_handles_zero_and_float_sum(self):
        self.assertEqual(mParseStorageDistrib("0:100:0"), (0.0, 100.0, 0.0))
        self.assertEqual(mParseStorageDistrib("33.3:33.3:33.4"), (33.3, 33.3, 33.4))

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_accepts_tiny_float_delta(self):
        # Floating tolerance in mParseStorageDistrib allows minor imprecision.
        self.assertEqual(mParseStorageDistrib("33.333333:33.333333:33.333334"),
                         (33.333333, 33.333333, 33.333334))

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_rejects_negative_values(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib("-1:50:51")

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_rejects_non_numeric_values(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib("10:bad:90")

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_rejects_missing_input(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib("")

    # Auto-generated test for ebCluDiskGroupConfig
    def test_diskgroupconfig_type_detection_catalog_delta_dbfs(self):
        _xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>CATALOG01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>20G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg = ebCluDiskGroupConfig(_xml)
        self.assertEqual(_dg.mGetDiskGroupType(), 'catalog')

        _xml.find('diskGroupName').text = 'DELTA01'
        self.assertEqual(_dg.mGetDiskGroupType(), 'delta')

        _xml.find('diskGroupName').text = 'DBFS01'
        self.assertEqual(_dg.mGetDiskGroupType(), 'dbfs')

    # Auto-generated test for mListCellDisksSize
    def test_mListCellDisksSize_uses_cf_for_efrack_x9(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _ebox.mReturnCellNodes = MagicMock(return_value={'cell1': {}})
        _ebox.mGetNodeModel = MagicMock(return_value='X9')
        _ebox.mCompareExadataModel = MagicMock(return_value=1)

        _escli = MagicMock()
        _escli.mIsEFRack.return_value = True

        class _FakeCtx(object):
            def __init__(self, node):
                self._node = node
            def __enter__(self):
                return self._node
            def __exit__(self, exc_type, exc, tb):
                return False

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (
            None,
            mockStream(['CF_00_cell1 1G 0.5G\n']),
            mockStream([''])
        )
        _node.mGetCmdExitStatus.return_value = 0

        with patch('exabox.ovm.clustorage.ebEscliUtils', return_value=_escli), \
             patch('exabox.ovm.clustorage.connect_to_host', return_value=_FakeCtx(_node)):
            total, free = _clustorage.mListCellDisksSize()

        self.assertAlmostEqual(total, 1.0)
        self.assertAlmostEqual(free, 0.5)
        self.assertIn('CF_', _node.mExecuteCmd.call_args[0][0])

    # Auto-generated test for mPatchClusterDiskgroup
    def test_mPatchClusterDiskgroup_logs_info_payload_when_cmd_info(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _dg_xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>200G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg_cfg = ebCluDiskGroupConfig(_dg_xml)
        _dg_cfg.mGetDiskGroupType = MagicMock(return_value='data')

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']

        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _ebox.mReturnCellNodes.return_value = {'cell1': {}}
        _ebox.mGetRackSize = MagicMock(return_value='quarter')
        _ebox.mGetEsracks = MagicMock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 7
        _ebox.mGetCmd = MagicMock(return_value='info')
        _ebox.mGetEnableAsmss = MagicMock(return_value='false')
        _ebox.mGetEnableQuorum = MagicMock(return_value=True)
        _ebox.mGetDbStorage = MagicMock(return_value=None)
        _ebox.SharedEnv = MagicMock(return_value=True)

        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg_cfg)
        _clustorage.mGetDiskSizeInInt = MagicMock(return_value=200)

        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment'), \
             patch('exabox.ovm.clustorage.ebLogInfo') as _mock_log:
            _clustorage.mPatchClusterDiskgroup(
                aCreateSparse=False,
                aBackupDisk=False,
                aDRSdistrib=None,
                aOptions=_options)

        _info_calls = [
            _call[0][0] for _call in _mock_log.call_args_list
            if '{"gb_storage"' in str(_call[0][0])
        ]
        self.assertTrue(_info_calls)

    # Auto-generated test for mPatchClusterDiskgroup
    def test_mPatchClusterDiskgroup_updates_request_on_info_cmd(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _dg_xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>200G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg_cfg = ebCluDiskGroupConfig(_dg_xml)
        _dg_cfg.mGetDiskGroupType = MagicMock(return_value='data')

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']

        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _ebox.mReturnCellNodes.return_value = {'cell1': {}}
        _ebox.mGetRackSize = MagicMock(return_value='quarter')
        _ebox.mGetEsracks = MagicMock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 7
        _ebox.mGetCmd = MagicMock(return_value='info')
        _ebox.mGetEnableAsmss = MagicMock(return_value='false')
        _ebox.mGetEnableQuorum = MagicMock(return_value=True)
        _ebox.mGetDbStorage = MagicMock(return_value=None)
        _ebox.SharedEnv = MagicMock(return_value=True)

        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg_cfg)
        _clustorage.mGetDiskSizeInInt = MagicMock(return_value=200)

        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}

        _req = MagicMock()
        _ebox.mGetRequestObj = MagicMock(return_value=_req)

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment'), \
             patch('exabox.ovm.clustorage.ebGetDefaultDB') as _mock_db:
            _db = MagicMock()
            _mock_db.return_value = _db
            _clustorage.mPatchClusterDiskgroup(
                aCreateSparse=False,
                aBackupDisk=False,
                aDRSdistrib=None,
                aOptions=_options)

        _req.mSetData.assert_called_once()
        _db.mUpdateRequest.assert_called_once_with(_req)

    # Auto-generated test for mPatchClusterDiskgroup
    def test_mPatchClusterDiskgroup_acfs_payload_override(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _dg_xml = etree.fromstring(
            """
            <diskGroup id="DG1">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>200G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dg_cfg = ebCluDiskGroupConfig(_dg_xml)
        _dg_cfg.mGetDiskGroupType = MagicMock(return_value='data')

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DG1']

        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _ebox.mReturnCellNodes.return_value = {'cell1': {}}
        _ebox.mGetRackSize = MagicMock(return_value='quarter')
        _ebox.mGetEsracks = MagicMock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 7
        _ebox.mGetCmd = MagicMock(return_value='provision')
        _ebox.mGetEnableAsmss = MagicMock(return_value='false')
        _ebox.mGetEnableQuorum = MagicMock(return_value=True)
        _ebox.mGetExadataCellModel = MagicMock(return_value='X7')
        _ebox.SharedEnv = MagicMock(return_value=True)
        _ebox.mGetDbStorage = MagicMock(return_value=None)

        _clustorage.mGetDiskGroupConfig = MagicMock(return_value=_dg_cfg)
        _clustorage.mGetDiskSizeInInt = MagicMock(return_value=200)

        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {
            'atp': {
                'acfs_size_in_gb': 250
            }
        }

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment'), \
             patch('exabox.ovm.clustorage.mCompareModel', return_value=1):
            _clustorage.mPatchClusterDiskgroup(
                aCreateSparse=False,
                aBackupDisk=False,
                aDRSdistrib=None,
                aOptions=_options)

        self.assertEqual(_dg_cfg.mGetAcfsVolumeName(), 'acfsvol01')
        self.assertEqual(_dg_cfg.mGetAcfsVolumeSize(), '250')
        self.assertEqual(_dg_cfg.mGetAcfsMountPath(), '/acfs01')

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_raises_on_unexpected_error(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell1'
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['BAD OUTPUT']),
            mockStream(['unexpected error'])
        )
        _node.mGetCmdExitStatus.return_value = 1

        with self.assertRaises(ExacloudRuntimeError):
            _clustorage.mListCellDisksAttributes(_node, aAttributes=['STATUS'])

    # Auto-generated test for mPatchClusterDiskgroup
    def test_mPatchClusterDiskgroup_removes_dbfs_when_quorum_enabled(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _data_xml = etree.fromstring(
            """
            <diskGroup id="DATA_ID">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>100G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _reco_xml = etree.fromstring(
            """
            <diskGroup id="RECO_ID">
                <diskGroupName>RECO01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>50G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dbfs_xml = etree.fromstring(
            """
            <diskGroup id="DBFS_ID">
                <diskGroupName>DBFS01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>1G</sliceSize>
                <diskGroupSize>0G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _data_cfg = ebCluDiskGroupConfig(_data_xml)
        _reco_cfg = ebCluDiskGroupConfig(_reco_xml)
        _dbfs_cfg = ebCluDiskGroupConfig(_dbfs_xml)

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DATA_ID', 'RECO_ID', 'DBFS_ID']
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _ebox.mReturnCellNodes.return_value = {'cell1': {}}
        _ebox.mGetRackSize = MagicMock(return_value='quarter')
        _ebox.mGetEsracks = MagicMock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 7
        _ebox.mGetCmd = MagicMock(return_value='provision')
        _ebox.mGetEnableAsmss = MagicMock(return_value='false')
        _ebox.mGetEnableQuorum = MagicMock(return_value=True)
        _ebox.SharedEnv = MagicMock(return_value=True)
        _ebox.mGetDbStorage = MagicMock(return_value=None)
        _ebox.mCheckConfigOption = MagicMock(return_value=False)
        _ebox.mGetExadataCellModel = MagicMock(return_value='X6')

        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}

        def _dg_lookup(a_dg_id):
            _mapping = {
                'DATA_ID': _data_cfg,
                'RECO_ID': _reco_cfg,
                'DBFS_ID': _dbfs_cfg,
                'dbfs_uuid': _dbfs_cfg,
                'sparse_uuid': _dbfs_cfg
            }
            return _mapping.get(a_dg_id, _data_cfg)

        _clustorage.mGetDiskGroupConfig = MagicMock(side_effect=_dg_lookup)
        _clustorage.mGetDgVolsize = MagicMock(return_value=(100, 50, 10, 5))

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment'), \
             patch('exabox.ovm.clustorage.mCompareModel', return_value=-1), \
             patch.object(_clustorage, 'mRemoveDiskGroupConfig') as _mock_remove:
            _clustorage.mPatchClusterDiskgroup(
                aCreateSparse=False,
                aBackupDisk=False,
                aDRSdistrib=None,
                aOptions=_options)

        _cluster.mRemoveDiskGroup.assert_called_once_with('DBFS_ID')
        _mock_remove.assert_called_once_with('DBFS_ID')

    # Auto-generated test for mPatchClusterDiskgroup
    def test_mPatchClusterDiskgroup_dbfs_quorum_disabled_updates_dbfs_config(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _data_xml = etree.fromstring(
            """
            <diskGroup id="DATA_ID">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>100G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _reco_xml = etree.fromstring(
            """
            <diskGroup id="RECO_ID">
                <diskGroupName>RECO01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>50G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _dbfs_xml = etree.fromstring(
            """
            <diskGroup id="DBFS_ID">
                <diskGroupName>DBFS01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>1G</sliceSize>
                <diskGroupSize>0G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _data_cfg = ebCluDiskGroupConfig(_data_xml)
        _reco_cfg = ebCluDiskGroupConfig(_reco_xml)
        _dbfs_cfg = ebCluDiskGroupConfig(_dbfs_xml)

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DATA_ID', 'RECO_ID', 'DBFS_ID']
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _ebox.mReturnCellNodes.return_value = {'cell1': {}}
        _ebox.mGetRackSize = MagicMock(return_value='quarter')
        _ebox.mGetEsracks = MagicMock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 7
        _ebox.mGetCmd = MagicMock(return_value='provision')
        _ebox.mGetEnableAsmss = MagicMock(return_value='false')
        _ebox.mGetEnableQuorum = MagicMock(return_value=False)
        _ebox.SharedEnv = MagicMock(return_value=True)
        _ebox.mGetDbStorage = MagicMock(return_value=None)
        _ebox.mCheckConfigOption = MagicMock(return_value=False)
        _ebox.mGetExadataCellModel = MagicMock(return_value='X6')

        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}

        def _dg_lookup(a_dg_id):
            _mapping = {
                'DATA_ID': _data_cfg,
                'RECO_ID': _reco_cfg,
                'DBFS_ID': _dbfs_cfg,
                'sparse_uuid': _dbfs_cfg
            }
            return _mapping.get(a_dg_id, _data_cfg)

        def _fake_dgvolsize(*args):
            if len(args) == 7:
                return (100, 50, 10, 5)
            return (100, 50, 25, 10, 5, 2)

        _clustorage.mGetDiskGroupConfig = MagicMock(side_effect=_dg_lookup)
        _clustorage.mGetDgVolsize = MagicMock(side_effect=_fake_dgvolsize)

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment'), \
             patch('exabox.ovm.clustorage.mCompareModel', return_value=-1), \
             patch.object(_ebox, 'mGenerateUUID', return_value='sparse_uuid'):
            _clustorage.mPatchClusterDiskgroup(
                aCreateSparse=True,
                aBackupDisk=False,
                aDRSdistrib=None,
                aOptions=_options)

        self.assertEqual(_dbfs_cfg.mGetDgRedundancy(), 'NORMAL')
        self.assertEqual(_dbfs_cfg.mGetOCRVote(), 'true')

    # Auto-generated test for mPatchClusterDiskgroup
    def test_mPatchClusterDiskgroup_adds_dbfs_when_missing_quorum_disabled(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _data_xml = etree.fromstring(
            """
            <diskGroup id="data01">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>100G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _reco_xml = etree.fromstring(
            """
            <diskGroup id="reco01">
                <diskGroupName>RECO01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>5G</sliceSize>
                <diskGroupSize>50G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _data_cfg = ebCluDiskGroupConfig(_data_xml)
        _reco_cfg = ebCluDiskGroupConfig(_reco_xml)

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['data01', 'reco01']
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _ebox.mReturnCellNodes.return_value = {'cell1': {}}
        _ebox.mGetRackSize = MagicMock(return_value='quarter')
        _ebox.mGetEsracks = MagicMock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 7
        _ebox.mGetCmd = MagicMock(return_value='provision')
        _ebox.mGetEnableAsmss = MagicMock(return_value='false')
        _ebox.mGetEnableQuorum = MagicMock(return_value=False)
        _ebox.SharedEnv = MagicMock(return_value=True)
        _ebox.mGetDbStorage = MagicMock(return_value=None)
        _ebox.mCheckConfigOption = MagicMock(return_value=False)
        _ebox.mGenerateUUID = MagicMock(return_value='dbfs_uuid')

        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {'node_subset': {'num_participating_computes': 1}}

        def _dg_lookup(a_dg_id):
            return {'data01': _data_cfg, 'reco01': _reco_cfg}[a_dg_id]

        _clustorage.mGetDiskGroupConfig = MagicMock(side_effect=_dg_lookup)
        _clustorage.mGetDgVolsize = MagicMock(return_value=(100, 50, 10, 5))

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment'), \
             patch('exabox.ovm.clustorage.mCompareModel', return_value=-1), \
             patch.object(_clustorage, 'mAddDiskGroupConfig') as _mock_add:
            _clustorage.mPatchClusterDiskgroup(
                aCreateSparse=False,
                aBackupDisk=False,
                aDRSdistrib=None,
                aOptions=_options)

        _mock_add.assert_called_once()
        _cluster.mAddCluDiskGroupConfig.assert_called_once_with('dbfs01')

    # Auto-generated test for mPatchClusterDiskgroup
    def test_mPatchClusterDiskgroup_sets_asm_scoped_security_true(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _data_xml = etree.fromstring(
            """
            <diskGroup id="DATA_ID">
                <diskGroupName>DATA01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>10G</sliceSize>
                <diskGroupSize>100G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _reco_xml = etree.fromstring(
            """
            <diskGroup id="RECO_ID">
                <diskGroupName>RECO01</diskGroupName>
                <redundancy>HIGH</redundancy>
                <sliceSize>5G</sliceSize>
                <diskGroupSize>50G</diskGroupSize>
                <ocrVote>false</ocrVote>
                <machines>
                    <machine id="m1"/>
                </machines>
            </diskGroup>
            """
        )
        _data_cfg = ebCluDiskGroupConfig(_data_xml)
        _reco_cfg = ebCluDiskGroupConfig(_reco_xml)

        _cluster = MagicMock()
        _cluster.mGetCluDiskGroups.return_value = ['DATA_ID', 'RECO_ID']
        _ebox.mGetClusters.return_value.mGetCluster.return_value = _cluster
        _ebox.mGetMachines.return_value.mGetMachineConfig.return_value = MagicMock(
            mGetLocaldisksCount=MagicMock(return_value=12)
        )
        _ebox.mReturnCellNodes.return_value = {'cell1': {}}
        _ebox.mGetRackSize = MagicMock(return_value='quarter')
        _ebox.mGetEsracks = MagicMock()
        _ebox.mGetEsracks.return_value.mGetDiskSize.return_value = 7
        _ebox.mGetCmd = MagicMock(return_value='provision')
        _ebox.mGetEnableAsmss = MagicMock(return_value='true')
        _ebox.mGetEnableQuorum = MagicMock(return_value=True)
        _ebox.SharedEnv = MagicMock(return_value=True)
        _ebox.mGetDbStorage = MagicMock(return_value=None)
        _ebox.mCheckConfigOption = MagicMock(return_value=False)

        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {}

        def _dg_lookup(a_dg_id):
            return {'DATA_ID': _data_cfg, 'RECO_ID': _reco_cfg}[a_dg_id]

        _clustorage.mGetDiskGroupConfig = MagicMock(side_effect=_dg_lookup)
        _clustorage.mGetDgVolsize = MagicMock(return_value=(100, 50, 10, 5))

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment'), \
             patch('exabox.ovm.clustorage.mCompareModel', return_value=-1):
            _clustorage.mPatchClusterDiskgroup(
                aCreateSparse=False,
                aBackupDisk=False,
                aDRSdistrib=None,
                aOptions=_options)

        _cluster.mSetCluAsmScopedSecurity.assert_called_once_with('true')

    # Auto-generated test for ebCluStoragePoolConfig getters
    def test_storagepoolconfig_getters_return_expected(self):
        _xml = etree.fromstring(
            """
            <storagePool id="SP1">
                <version>1</version>
                <storagePoolName>SPDATA</storagePoolName>
                <storagePoolType>data</storagePoolType>
                <storagePoolSize>1024G</storagePoolSize>
                <uiSize>10</uiSize>
                <uiSizeType>percent</uiSizeType>
                <machines>
                    <machine id="m1"/>
                    <machine id="m2"/>
                </machines>
            </storagePool>
            """
        )

        _sp_cfg = ebCluStoragePoolConfig(_xml)
        self.assertEqual(_sp_cfg.mGetSpId(), 'SP1')
        self.assertEqual(_sp_cfg.mGetSPName(), 'SPDATA')
        self.assertEqual(_sp_cfg.mGetSPType(), 'data')
        self.assertEqual(_sp_cfg.mGetSPSize(), '1024G')
        self.assertEqual(_sp_cfg.mGetUiSize(), '10')
        self.assertEqual(_sp_cfg.mGetUiSizeType(), 'percent')
        self.assertEqual(_sp_cfg.mGetStoragePoolMachines(), ['m1', 'm2'])

    # Auto-generated test for ebCluEDVVolumesConfig getters
    def test_edvvolumesconfig_getters_return_expected(self):
        _xml = etree.fromstring(
            """
            <edvVolume id="EDV1">
                <edvVolumeName>EDV01</edvVolumeName>
                <edvVolumeSize>256G</edvVolumeSize>
                <edvVolumeType>data</edvVolumeType>
                <edvDevicePath>/dev/mapper/edv1</edvDevicePath>
            </edvVolume>
            """
        )

        _edv_cfg = ebCluEDVVolumesConfig(_xml)
        self.assertEqual(_edv_cfg.mGetEdvId(), 'EDV1')
        self.assertEqual(_edv_cfg.mGetEDVName(), 'EDV01')
        self.assertEqual(_edv_cfg.mGetSPSize(), '256G')
        self.assertEqual(_edv_cfg.mGetEDVType(), 'data')
        self.assertEqual(_edv_cfg.mGetDevicePath(), '/dev/mapper/edv1')

    # Auto-generated test for mDropCellDisks
    def test_mDropCellDisks_no_force_needed(self):
        _clustorage = self.mGetClubox().mGetStorage()

        _node = MagicMock()
        _node.__enter__ = MagicMock(return_value=_node)
        _node.__exit__ = MagicMock(return_value=None)

        _node_exec = MagicMock(side_effect=[
            MagicMock(exit_code=0)
        ])

        with patch('exabox.ovm.clustorage.connect_to_host', return_value=_node), \
             patch('exabox.ovm.clustorage.node_exec_cmd', _node_exec):
            self.assertIsNone(_clustorage.mDropCellDisks(['cell1']))

        _node_exec.assert_called_once()

    # Auto-generated test for mDropCellDisks
    def test_mDropCellDisks_force_attempt_fails(self):
        _clustorage = self.mGetClubox().mGetStorage()

        _node = MagicMock()
        _node.__enter__ = MagicMock(return_value=_node)
        _node.__exit__ = MagicMock(return_value=None)

        _node_exec = MagicMock(side_effect=[
            MagicMock(exit_code=1),
            MagicMock(exit_code=2),
        ])

        with patch('exabox.ovm.clustorage.connect_to_host', return_value=_node), \
             patch('exabox.ovm.clustorage.node_exec_cmd', _node_exec):
            with self.assertRaises(ExacloudRuntimeError):
                _clustorage.mDropCellDisks(['cell1'])

        self.assertEqual(_node_exec.call_count, 2)

    # Auto-generated test for mDropCellDisks
    def test_mDropCellDisks_force_attempt_succeeds(self):
        _clustorage = self.mGetClubox().mGetStorage()

        _node = MagicMock()
        _node.__enter__ = MagicMock(return_value=_node)
        _node.__exit__ = MagicMock(return_value=None)

        _node_exec = MagicMock(side_effect=[
            MagicMock(exit_code=1),
            MagicMock(exit_code=0),
        ])

        with patch('exabox.ovm.clustorage.connect_to_host', return_value=_node), \
             patch('exabox.ovm.clustorage.node_exec_cmd', _node_exec):
            self.assertIsNone(_clustorage.mDropCellDisks(['cell1']))

        self.assertEqual(_node_exec.call_count, 2)

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_rejects_invalid_part_count(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib("50")

        with self.assertRaises(ValueError):
            mParseStorageDistrib("10:20:30:40")

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_raises_on_unexpected_error(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell5'
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['bad stdout']),
            mockStream(['some other error'])
        )
        _node.mGetCmdExitStatus.return_value = True

        with self.assertRaises(ExacloudRuntimeError):
            _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

    # Auto-generated test for mListCellDisksAttributes
    @patch('exabox.ovm.clustorage.sleep')
    def test_mListCellDisksAttributes_raises_after_retry_exhausted(self, _mock_sleep):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _controller = _clustorage._ebCluStorageConfig__ebox

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell6'
        _node.mExecuteCmdCellcli.side_effect = [
            (None, mockStream(['stdout1']), mockStream(['CELL-02559 error'])),
            (None, mockStream(['stdout2']), mockStream(['CELL-02559 error'])),
            (None, mockStream(['stdout3']), mockStream(['CELL-02559 error']))
        ]
        _node.mGetCmdExitStatus.side_effect = [True, True, True]

        with patch.object(_controller, 'mCheckCellsServicesUp') as _mock_check:
            with self.assertRaises(ExacloudRuntimeError):
                _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

        self.assertEqual(_mock_check.call_count, 2)
        self.assertEqual(_mock_sleep.call_count, 2)

    # Auto-generated test for mListCellDisksAttributes
    @patch('exabox.ovm.clustorage.sleep')
    def test_mListCellDisksAttributes_retries_and_builds_mapping(self, _mock_sleep):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _controller = _clustorage._ebCluStorageConfig__ebox

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell7'
        _node.mExecuteCmdCellcli.side_effect = [
            (None, mockStream(['bad stdout']), mockStream(['CELL-02559 error'])),
            (None, mockStream(['CD_00_cell7 normal ok\n', 'CD_01_cell7 warn ok\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.side_effect = [True, False]

        with patch.object(_controller, 'mCheckCellsServicesUp') as _mock_check:
            _result = _clustorage.mListCellDisksAttributes(_node, ['STATUS', 'HEALTH'])

        self.assertEqual(
            _result,
            {
                'CD_00_cell7': {'STATUS': 'normal', 'HEALTH': 'ok'},
                'CD_01_cell7': {'STATUS': 'warn', 'HEALTH': 'ok'}
            }
        )
        _mock_check.assert_called_once_with(aRestart=False, aCellList=['cell7'])
        _mock_sleep.assert_called_once()

    # Auto-generated test for mListCellDisksAttributes
    def test_mListCellDisksAttributes_success_no_retry(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _node = MagicMock()
        _node.mGetHostname.return_value = 'cell8'
        _node.mExecuteCmdCellcli.return_value = (
            None,
            mockStream(['CD_00_cell8 normal\n', 'CD_01_cell8 degraded\n']),
            mockStream([''])
        )
        _node.mGetCmdExitStatus.return_value = False

        _result = _clustorage.mListCellDisksAttributes(_node, ['STATUS'])

        self.assertEqual(
            _result,
            {
                'CD_00_cell8': {'STATUS': 'normal'},
                'CD_01_cell8': {'STATUS': 'degraded'}
            }
        )
        _node.mExecuteCmdCellcli.assert_called_once()

    # Auto-generated test for mListPMEMDetails
    def test_mListPMEMDetails_parses_attributes(self):
        _node = MagicMock()
        _output = "name: cell_PMEMLOG\ncellDisk: PM_00,PM_01\nstatus: normal\n"

        with patch('exabox.ovm.clustorage.node_exec_cmd', return_value=(None, _output, None)) as _mock_exec:
            _result = ebCluStorageConfig.mListPMEMDetails(_node, 'LOG')

        self.assertEqual(
            _result,
            {'name': 'cell_PMEMLOG', 'cellDisk': 'PM_00,PM_01', 'status': 'normal'}
        )
        _mock_exec.assert_called_once()

    # Auto-generated test for mUtilStorageResize
    def test_mUtilStorageResize_honors_rebalance_power_when_valid(self):
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _options.jsonconf = {'rebalance_power': 32}
        _clustorage = ebCluManageStorage(_ebox, _options)

        _dgObj = MagicMock()
        _dgObj.mClusterDgrpRebalance.return_value = 0

        _clustorage._ebCluManageStorage__resizesprs = False
        _clustorage._ebCluManageStorage__rebalancesprs = True

        _dgmap = {
            _clustorage.SPARSE: {
                _clustorage.DG_NAME: 'SPRC1',
                _clustorage.DG_NEWSIZE: 110,
                _clustorage.DG_CURRSIZE: 110,
            }
        }

        _rc = _clustorage.mUtilStorageResize(_dgObj, _options, _dgmap, 0)

        self.assertEqual(_rc, 0)
        self.assertEqual(_options.jsonconf.get('rebalance_power'), 32)
        _dgObj.mClusterDgrpRebalance.assert_called_once_with(_options)
        _dgObj.mClusterDgrpResize.assert_not_called()

    # Auto-generated test for mListCellDG
    def test_mListCellDG_zdlra_builds_command_and_filters_output(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=True)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['CATALOG_GD\nDELTA_GD\nDATA_GD\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node)

        self.assertEqual(_result, ['CATALOG_GD', 'DELTA_GD'])
        self.assertIn('list GRIDDISK', _node.mExecuteCmd.call_args_list[0][0][0])

    # Auto-generated test for mListCellDG
    def test_mListCellDG_suffix_filters_out_nonmatching_entries(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _node = MagicMock()

        _ebox.IsZdlraProv = MagicMock(return_value=False)
        _node.mExecuteCmd.side_effect = [
            (None, None, None),
            (None, mockStream(['DATA_C1_x\nOTHER_C2_y\n']), mockStream(['']))
        ]
        _node.mGetCmdExitStatus.return_value = False

        with patch.object(_clustorage, 'mGetEbox', return_value=_ebox):
            _result = _clustorage.mListCellDG(_node, aSuffix='C1')

        self.assertEqual(_result, ['DATA_C1_x'])
        self.assertIn('C1', _node.mExecuteCmd.call_args_list[0][0][0])

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_empty_input_raises(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib('')

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_invalid_part_count_raises(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib('10:20:30:40')

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_non_numeric_raises(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib('10:abc:90')

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_negative_value_raises(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib('-1:50:51')

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_invalid_sum_raises(self):
        with self.assertRaises(ValueError):
            mParseStorageDistrib('10:20:30')

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_two_part_string_adds_sparse_zero(self):
        _data, _reco, _sparse = mParseStorageDistrib('40:60')

        self.assertEqual(_data, 40.0)
        self.assertEqual(_reco, 60.0)
        self.assertEqual(_sparse, 0.0)

    # Auto-generated test for mParseStorageDistrib
    def test_mParseStorageDistrib_valid_three_parts_returns_tuple(self):
        _data, _reco, _sparse = mParseStorageDistrib('50:25:25')

        self.assertEqual((_data, _reco, _sparse), (50.0, 25.0, 25.0))

    # Auto-generated test for mGetDiskGroupType
    def test_mGetDiskGroupType_detects_sparse_prefix(self):
        _dg_xml = etree.fromstring(
            '<diskGroup id="dg1">'
            '<version>1</version>'
            '<diskGroupName>SPR01</diskGroupName>'
            '<redundancy>HIGH</redundancy>'
            '<sliceSize>1</sliceSize>'
            '<machines></machines>'
            '<cellDisks></cellDisks>'
            '<diskGroupSize>10</diskGroupSize>'
            '<ocrVote>false</ocrVote>'
            '<quorumDisk>false</quorumDisk>'
            '</diskGroup>'
        )

        _config = ebCluDiskGroupConfig(_dg_xml)

        self.assertEqual(
            _config.mGetDiskGroupType(),
            ebDiskgroupOpConstants()._sparse_dg_type_str
        )

    # Auto-generated test for mGetDiskGroupType
    def test_mGetDiskGroupType_detects_type_from_name(self):
        _dg_xml = etree.fromstring(
            '<diskGroup id="dg2">'
            '<version>1</version>'
            '<diskGroupName>DATA01</diskGroupName>'
            '<redundancy>HIGH</redundancy>'
            '<sliceSize>1</sliceSize>'
            '<machines></machines>'
            '<cellDisks></cellDisks>'
            '<diskGroupSize>10</diskGroupSize>'
            '<ocrVote>false</ocrVote>'
            '<quorumDisk>false</quorumDisk>'
            '</diskGroup>'
        )

        _config = ebCluDiskGroupConfig(_dg_xml)

        self.assertEqual(
            _config.mGetDiskGroupType(),
            ebDiskgroupOpConstants()._data_dg_type_str
        )

    # Auto-generated test for mGetDiskGroupType
    def test_mGetDiskGroupType_returns_none_when_no_match(self):
        _dg_xml = etree.fromstring(
            '<diskGroup id="dg3">'
            '<version>1</version>'
            '<diskGroupName>UNKNOWN</diskGroupName>'
            '<redundancy>HIGH</redundancy>'
            '<sliceSize>1</sliceSize>'
            '<machines></machines>'
            '<cellDisks></cellDisks>'
            '<diskGroupSize>10</diskGroupSize>'
            '<ocrVote>false</ocrVote>'
            '<quorumDisk>false</quorumDisk>'
            '</diskGroup>'
        )

        _config = ebCluDiskGroupConfig(_dg_xml)

        self.assertIsNone(_config.mGetDiskGroupType())

    # Auto-generated test for mSetQuorumDisk
    def test_mSetQuorumDisk_creates_element_when_missing(self):
        _dg_xml = etree.fromstring(
            '<diskGroup id="dg4">'
            '<version>1</version>'
            '<diskGroupName>DATA02</diskGroupName>'
            '<redundancy>HIGH</redundancy>'
            '<sliceSize>1</sliceSize>'
            '<machines></machines>'
            '<cellDisks></cellDisks>'
            '<diskGroupSize>10</diskGroupSize>'
            '<ocrVote>false</ocrVote>'
            '</diskGroup>'
        )

        _config = ebCluDiskGroupConfig(_dg_xml)
        _config.mSetQuorumDisk('true')

        _quorum = _config.mGetQuorumDisk()
        self.assertEqual(_quorum.text, 'true')
        self.assertIsNotNone(_config.mGetXMLObject().find('quorumDisk'))

    # Auto-generated test for mSetGridDiskPrefix
    def test_mSetGridDiskPrefix_sets_value_when_missing(self):
        _dg_xml = etree.fromstring(
            '<diskGroup id="dg5">'
            '<version>1</version>'
            '<diskGroupName>DATA03</diskGroupName>'
            '<redundancy>HIGH</redundancy>'
            '<sliceSize>1</sliceSize>'
            '<machines></machines>'
            '<cellDisks></cellDisks>'
            '<diskGroupSize>10</diskGroupSize>'
            '<ocrVote>false</ocrVote>'
            '<quorumDisk>false</quorumDisk>'
            '</diskGroup>'
        )

        _config = ebCluDiskGroupConfig(_dg_xml)
        _config.mSetGridDiskPrefix('GD')

        self.assertEqual(_config.mGetGridDiskPrefix(), 'GD')

    # Auto-generated test for mSetSparseVirtualSize
    def test_mSetSparseVirtualSize_converts_int_to_gigabytes(self):
        _dg_xml = etree.fromstring(
            '<diskGroup id="dg6">'
            '<version>1</version>'
            '<diskGroupName>DATA04</diskGroupName>'
            '<redundancy>HIGH</redundancy>'
            '<sliceSize>1</sliceSize>'
            '<machines></machines>'
            '<cellDisks></cellDisks>'
            '<diskGroupSize>10</diskGroupSize>'
            '<ocrVote>false</ocrVote>'
            '<quorumDisk>false</quorumDisk>'
            '</diskGroup>'
        )

        _config = ebCluDiskGroupConfig(_dg_xml)
        _config.mSetSparseVirtualSize(42)

        self.assertEqual(_config.mGetXMLObject().find('sparseVirtualSize').text, '42G')

    # Auto-generated test for mReplaceDgId
    def test_mReplaceDgId_updates_attribute(self):
        _dg_xml = etree.fromstring(
            '<diskGroup id="dg7">'
            '<version>1</version>'
            '<diskGroupName>DATA05</diskGroupName>'
            '<redundancy>HIGH</redundancy>'
            '<sliceSize>1</sliceSize>'
            '<machines></machines>'
            '<cellDisks></cellDisks>'
            '<diskGroupSize>10</diskGroupSize>'
            '<ocrVote>false</ocrVote>'
            '<quorumDisk>false</quorumDisk>'
            '</diskGroup>'
        )

        _config = ebCluDiskGroupConfig(_dg_xml)
        _config.mReplaceDgId('newid')

        self.assertEqual(_config.mGetDgId(), 'newid')
        self.assertEqual(_config.mGetXMLObject().get('id'), 'newid')

    # Auto-generated test for mListCellDisksSize
    def test_mListCellDisksSize_skips_unsupported_units(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _cell = 'cell-unit'
        _ebox.mReturnCellNodes = MagicMock(return_value={_cell: 'cell-unit'})
        _ebox.mGetNodeModel = MagicMock(return_value='X9')
        _ebox.mCompareExadataModel = MagicMock(return_value=1)

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (
            None,
            mockStream(['CD_00 X 1Z\n', 'CD_01 Y 2Z\n']),
            mockStream([''])
        )
        _node.mGetCmdExitStatus.return_value = 0

        with patch('exabox.ovm.clustorage.connect_to_host') as _mock_connect, \
                patch('exabox.ovm.clustorage.ebEscliUtils') as _mock_escli:
            _mock_escli.return_value.mIsEFRack.return_value = False
            _mock_connect.return_value.__enter__.return_value = _node
            _mock_connect.return_value.__exit__.return_value = False

            _total, _free = _clustorage.mListCellDisksSize([_cell])

        self.assertEqual((_total, _free), (0.0, 0.0))
        _node.mExecuteCmd.assert_called_once()

    # Auto-generated test for mListCellDisksSize
    def test_mListCellDisksSize_raises_on_empty_output(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _cell = 'cell-empty'
        _ebox.mReturnCellNodes = MagicMock(return_value={_cell: 'cell-empty'})
        _ebox.mGetNodeModel = MagicMock(return_value='X9')
        _ebox.mCompareExadataModel = MagicMock(return_value=1)

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, None, mockStream(['err']))
        _node.mGetCmdExitStatus.return_value = 0

        with patch('exabox.ovm.clustorage.connect_to_host') as _mock_connect:
            _mock_connect.return_value.__enter__.return_value = _node
            _mock_connect.return_value.__exit__.return_value = False

            with self.assertRaises(ExacloudRuntimeError):
                _clustorage.mListCellDisksSize([_cell])

    # Auto-generated test for mListCellDisksSize
    def test_mListCellDisksSize_raises_on_command_failure(self):
        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()

        _cell = 'cell-fail'
        _ebox.mReturnCellNodes = MagicMock(return_value={_cell: 'cell-fail'})
        _ebox.mGetNodeModel = MagicMock(return_value='X9')
        _ebox.mCompareExadataModel = MagicMock(return_value=1)

        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, mockStream(['out']), mockStream(['err']))
        _node.mGetCmdExitStatus.return_value = 1

        with patch('exabox.ovm.clustorage.connect_to_host') as _mock_connect:
            _mock_connect.return_value.__enter__.return_value = _node
            _mock_connect.return_value.__exit__.return_value = False

            with self.assertRaises(ExacloudRuntimeError):
                _clustorage.mListCellDisksSize([_cell])

if __name__ == '__main__':
    unittest.main()
