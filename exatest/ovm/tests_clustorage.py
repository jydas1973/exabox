#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clustorage.py /main/14 2025/10/28 18:55:05 jfsaldan Exp $
#
# tests_clustorage.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
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

from unittest.mock import patch
from unittest.mock import MagicMock, Mock

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.ovm.cludiskgroups import ebDiskgroupOpConstants, ebCluManageDiskgroup
from exabox.ovm.clustorage import ebCluManageStorage, ebCluStorageConfig

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
    
    @patch("exabox.ovm.clustorage.ebCluStorageConfig.mClusterDiskGroupSuffix")
    def test_mGetCurrentClusterGridDisksFromCells_c4_griddisk_present(self,
            aMockDGSuffix):
        """
        Method to test clustorage method 'mGetCellGridDisk'
        """

        # Declare variable to use
        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _clustorage = _ebox.mGetStorage()
        _cell_list = _ebox.mReturnCellNodes()

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
        _expected_result["scaqab10celadm01.us.oracle.com"] = _expected_gd
        _expected_result["scaqab10celadm02.us.oracle.com"] = _expected_gd
        _expected_result["scaqab10celadm03.us.oracle.com"] = _expected_gd

        # Override suffix to C4 so its one of self._griddisk_list
        aMockDGSuffix.return_value = "C4"

        # Run method to test
        _results = {}
        for _cell in _cell_list:
            with connect_to_host(_cell, get_gcontext()) as _node:
                _results[_cell] = _clustorage.mGetCurrentClusterGridDisksFromCells(_node)

        self.assertEqual(_results, _expected_result)

    @patch("exabox.ovm.clustorage.ebCluStorageConfig.mClusterDiskGroupSuffix")
    def test_mGetCurrentClusterGridDisksFromCells_c6_griddisk_not_present(self,
            aMockDGSuffix):
        """
        Method to test clustorage method 'mGetCellGridDisk'
        """

        # Declare variable to use
        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _clustorage = _ebox.mGetStorage()
        _cell_list = _ebox.mReturnCellNodes()

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
        _expected_result["scaqab10celadm01.us.oracle.com"] = _expected_gd
        _expected_result["scaqab10celadm02.us.oracle.com"] = _expected_gd
        _expected_result["scaqab10celadm03.us.oracle.com"] = _expected_gd

        # Override suffix to C9 so its one of self._griddisk_list
        aMockDGSuffix.return_value = "C9"

        # Run method to test
        _results = {}
        for _cell in _cell_list:
            with connect_to_host(_cell, get_gcontext()) as _node:
                _results[_cell] = _clustorage.mGetCurrentClusterGridDisksFromCells(_node)

        self.assertEqual(_results, _expected_result)

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
        _clustorage = _ebox.mGetStorage()
        _cell_list = _ebox.mReturnCellNodes()

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

    def test_mDropCellDisks_fails_with_force(self):
        self.assertRaises(ExacloudRuntimeError,
                lambda: self.template_test_mDropCellDisks(1, 1))

    @patch("exabox.ovm.clustorage.ebCluDiskGroupConfig.mGetDiskGroupSize")
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSharedEnvironment')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRackSize')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetEsracks')
    @patch('exabox.ovm.clucontrol.ebCluEsRacksConfig.mGetDiskSize')
    def test_mPatchClusterDiskgroup(self, 
        mock_mGetDiskGroupSize, mock_mCheckSharedEnvironment, mock_mGetRackSize,
        mock_mGetEsracks, mock_mGetDiskSize):
        mock_mGetDiskGroupSize.return_value = '-1234'

        mock_mGetDiskSize.return_value = '-1234'
        mock_mGetEsracks_instance = MagicMock()
        mock_mGetEsracks_instance.mGetDiskSize = mock_mGetDiskSize
        mock_mGetEsracks.return_value = mock_mGetEsracks_instance        

        _ebox = self.mGetClubox()
        _clustorage = _ebox.mGetStorage()
        _options = _ebox.mGetArgsOptions()
        with self.assertRaises(ExacloudRuntimeError) as _context:
            _clustorage.mPatchClusterDiskgroup(
                aCreateSparse = True, 
                aBackupDisk = False, 
                aDRSdistrib = None,
                aOptions = _options)
        exception=_context.exception
        self.assertEqual(exception._ExacloudRuntimeError__ec, 0x0746)
        self.assertEqual(exception._ExacloudRuntimeError__et, 0xA)
        self.assertEqual(exception._ExacloudRuntimeError__em, 'EXACLOUD : Invalid Input')

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
    def test_mPatchClusterDiskgroupDataRecoSparse_BackupFalse_SparseTrue(
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
    def test_mPatchClusterDiskgroupDataRecoSparse_BackupTrue_SparseTrue(
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
        self.assertEqual(0,ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(_ebox.mReturnCellNodes()))

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
        self.assertEqual(0,ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(_ebox.mReturnCellNodes()))

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
        self.assertEqual(0,ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(_ebox.mReturnCellNodes()))

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
        self.assertEqual(2,ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(_ebox.mReturnCellNodes()))

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
                ebCluManageStorage.DG_NEWSIZE: 160.0
            },
            ebCluManageStorage.RECO: {
                ebCluManageStorage.DG_NAME: 'RECOC1',
                ebCluManageStorage.DG_NEWSIZE: 40.0
            },
            ebCluManageStorage.SPARSE: {
                ebCluManageStorage.DG_NAME: None,
                ebCluManageStorage.DG_NEWSIZE: None,
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


if __name__ == '__main__':
    unittest.main()
