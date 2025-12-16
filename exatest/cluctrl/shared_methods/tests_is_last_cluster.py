#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_is_last_cluster.py /main/1 2022/02/11 19:55:52 jfsaldan Exp $
#
# tests_is_last_cluster.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_is_last_cluster.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    01/31/22 - Creation
#

import unittest
from unittest.mock import patch
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class ebTestIsLastCluster(ebTestClucontrol):

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

        self._griddisk_list_complete = [
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
    def test_mIsLastCluster_is_not_last_cluster(self, aMockGDSuffix):
        """
        Method to test clustorage method 'mIsLastCluster'
        """

        # Declare variable to use
        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _cell_list = _ebox.mReturnCellNodes()

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME;",
                        aStdout = "".join(self._griddisk_list_complete),
                        aRc=0,
                        aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Override suffix to C4
        aMockGDSuffix.return_value = "C4"

        # Run method to test
        self.assertFalse(_ebox.mIsLastCluster(_cell_list))

    @patch("exabox.ovm.clustorage.ebCluStorageConfig.mClusterDiskGroupSuffix")
    def test_mIsLastCluster_c4_is_last_cluster(self, aMockGDSuffix):
        """
        Method to test clustorage method 'mIsLastCluster'
        """

        # Declare variable to use
        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _cell_list = _ebox.mReturnCellNodes()

        # Prepare Commands
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME;",
                        aStdout = "".join(self._griddisk_cluster),
                        aRc=0,
                        aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Override suffix to C4
        aMockGDSuffix.return_value = "C4"

        # Run method to test
        self.assertTrue(_ebox.mIsLastCluster(_cell_list))


if __name__ == '__main__':
    unittest.main()
