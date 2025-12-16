#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cludiskgroups.py /main/2 2025/11/20 17:00:43 nelango Exp $
#
# tests_cludiskgroups.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cludiskgroups.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    nelango     11/04/25 - Bug 38483116: testcase for
#                           mCalculateFreeSpaceGriddisks
#    bhpati      04/03/25 - Creation
#

import math
import time
import unittest
import warnings
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch, MagicMock
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cludiskgroups import ebDiskgroupOpConstants, ebCluManageDiskgroup
from io import StringIO

dg_name = 'DATA6'
new_size_mb = 9437184
new_size_relative = None
new_sizes_dict = {
    "DATAC6": 7548928,
    "RECOC6": 1888256
}
diskgroup_data = {
    "DATAC6": {      
        "dg_storage_props" : {
            "used_mb" : "629028",
            "pct_free" : "96.43",
            "total_mb" : "17615808",
            "free_mb" : "16986780"
        }   
    },
    "RECOC6": {
        "dg_storage_props" : {
            "used_mb" : "629028",
            "pct_free" : "96.43",
            "total_mb" : "17615808",
            "free_mb" : "16986780"
        }
    }
}
precheck_dict = {
    "currentMB": 7340032,
    "osMB": 203890,
    "newMB": 9437184
}

dg_map = {
            "dg1": {"DG_NAME": "DATAC6", "DG_NEWSIZE": 9437184},
            "dg2": {"DG_NAME": "RECOC6", "DG_NEWSIZE": 1888256}
        }

class ebTestCludiskgroups(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCludiskgroups, cls).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetEbox')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetDbaasObj')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetConstantsObj')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mClusterDgrpInfo2', return_value=0)
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mValidateAndFilterStorPropDict')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mUtilCheckIfDgResizable', return_value=0)
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetOutJson')
    def test_mcheckifdgresizable_valid_input(self, mock_mGetOutJson, mock_mUtilCheckIfDgResizable, mock_mValidateAndFilterStorPropDict, mock_mClusterDgrpInfo2, mock_mGetConstantsObj, mock_mGetDbaasObj, mock_mGetEbox):
        # mock the dependencies
        mock_ebox_instance = MagicMock()
        mock_ebox_instance.mGetClusterPath = MagicMock(return_value="/u01/app/19.0.0.0/grid")

        mock_dbaas_obj = MagicMock()
        mock_dbaas_obj.mReadStatusFromDomU = MagicMock(return_value={"storprop_totalMb": 7340032, "storprop_usedMb": 629028})

        mock_constants_obj = MagicMock()
        mock_constants_obj._storprop_totalMb = "storprop_totalMb"
        mock_constants_obj._storprop_usedMb = "storprop_usedMb"
        mock_constants_obj._sparse_dg_prefix = ""
        mock_constants_obj._sparse_vsize_factor = 1

        options = MagicMock()
        options.configpath = ""

        mock_mGetEbox.return_value = mock_ebox_instance
        mock_mGetDbaasObj.return_value = mock_dbaas_obj
        mock_mGetConstantsObj.return_value = mock_constants_obj
        mock_mGetOutJson.return_value = {}

        def validate_and_filter_stor_prop_dict(infoobj, stor_prop_dict, dg_name, constants_obj):
            stor_prop_dict.update({"storprop_totalMb": 7340032, "storprop_usedMb": 629028})
            return 0

        mock_mValidateAndFilterStorPropDict.side_effect = validate_and_filter_stor_prop_dict

        # Call the method
        eb_clu_manage_diskgroup = ebCluManageDiskgroup(mock_ebox_instance, options)
        self.assertEqual(eb_clu_manage_diskgroup.mCheckIfDgResizable(options, dg_name, new_size_mb, new_size_relative, new_sizes_dict, diskgroup_data, precheck_dict), 0)

    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mCheckIfDgResizable', return_value= 0)
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mPrecheckDgSizeAvailableCells', return_value= 0)
    def test_mCheckIfDgResizableAll_valid_input(self, mock_mPrecheckDgSizeAvailableCells, mock_mCheckIfDgResizablee):
        # Define the input parameters
        mock_ebox_instance = MagicMock()
        options = MagicMock()
        
        # Call the method
        eb_clu_manage_diskgroup = ebCluManageDiskgroup(mock_ebox_instance, options)
        self.assertEqual(eb_clu_manage_diskgroup.mCheckIfDgResizableAll(options, dg_map), 0)

    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetEbox')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mCalculateFreeSpaceCelldisk', return_value=16986780)
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetCelldisks',return_value=["CD_00_slcqae13celadm04", "CD_01_slcqae13celadm04", "CD_02_slcqae13celadm04"])
    def test_mPrecheckDgSizeAvailableCells_valid_input(self, mock_mGetCelldisks, mock_mCalculateFreeSpaceCelldisk, mock_mGetEbox):
        # Mock the dependencies
        mock_ebox_instance = MagicMock()
        options = MagicMock()
        mock_ebox_instance = mock_mGetEbox.return_value
        mock_ebox_instance.mCheckConfigOption.return_value = True
        mock_ebox_instance.mReturnCellNodes.return_value = ["slcqae13celadm04", "slcqae13celadm05", "slcqae13celadm06"]

        # Call the method
        eb_clu_manage_diskgroup = ebCluManageDiskgroup(mock_ebox_instance, options)
        self.assertEqual(eb_clu_manage_diskgroup.mPrecheckDgSizeAvailableCells(precheck_dict), 0)
    
    @patch('exabox.ovm.cludiskgroups.connect_to_host')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetEbox')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetCelldisks')
    def test_mCheckGriddiskSize_valid_input(self, mock_mGetCelldisks, mock_mGetEbox, mock_connect_to_host):
        mock_ebox_instance = MagicMock()
        mock_ebox_instance.mReturnCellNodes.return_value = {
            "scaqan10celadm10": {},
            "scaqan10celadm11": {},
            "scaqan10celadm12": {},
        }
        mock_mGetEbox.return_value = mock_ebox_instance
        mock_mGetCelldisks.return_value = ['CD_00_scaqan10celadm10','CD_01_scaqan10celadm10',\
            'CD_02_scaqan10celadm10','CD_03_scaqan10celadm10','CD_04_scaqan10celadm10','CD_05_scaqan10celadm10',\
            'CD_06_scaqan10celadm10','CD_07_scaqan10celadm10','CD_08_scaqan10celadm10','CD_09_scaqan10celadm10',\
            'CD_10_scaqan10celadm10','CD_11_scaqan10celadm10']
        mock_node = MagicMock()
        mock_node.mExecuteCmd.return_value = (None, StringIO("8.33G\n"), StringIO(""))
        mock_node.mGetCmdExitStatus.return_value = 0
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        dg_name = "DATAC1"
        new_size_mb = 307200  
        options = MagicMock()
        eb_clu_manage_diskgroup = ebCluManageDiskgroup(mock_ebox_instance, options)
        result = eb_clu_manage_diskgroup.mCheckGriddiskSize(aDg=dg_name, aNewDgSize=new_size_mb)
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main(warnings='ignore')
        
