#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clucontrol_infrapatching.py /main/3 2026/02/16 17:28:04 ririgoye Exp $
#
# tests_clucontrol_infrapatching.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_clucontrol_infrapatching.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    02/10/26 - Enh 38337110 - CLUSTERLESS PATCHING SHOULD CONNECT
#                           TO FREE NODES FROM PAYLOAD FOR EXACS SERVICE FOR
#                           EXACLOUD VALIDATION
#    ajayasin    08/05/25 - moving handler function from clucontrol.py
#                           clucommandhandler.py to reduce the clucontrol.py
#                           size
#    araghave    05/07/25 - Enh 37892080 - TO IMPLEMENT NEWER PATCHSWITCHTYPE
#                           CHANGES APPLICABLE TO ALL SWITCH TARGET TYPES AND
#                           PATCH COMBINATIONS
#    araghave    05/22/25 - Creation
#

import json
import unittest
import warnings
import copy
import os, re
import sys
from io import StringIO
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from paramiko.ssh_exception import SSHException
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.network.Connection import exaBoxConnection
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.utils.node import connect_to_host
from exabox.ovm.clumisc import ebCluSshSetup

class mockStream():

    def __init__(self, aStreamContents=["None"]):
        self.stream_content = aStreamContents

    def readlines(self):
        return self.stream_content

    def readline(self):
        return self.stream_content[0]

    def read(self):
        return self.stream_content[0]

class mockHVInstance():

    def __init__(self):
        self.__running_domus = list()

    def mSetRunningDomUs(self, aListOfRunningDomUs):
        self.__running_domus = copy.deepcopy(aListOfRunningDomUs)

    def mRefreshDomUs(self):
        return self.__running_domus

class testOptions(object): pass

class ebTestClucontrolClasses(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestClucontrolClasses, self).setUpClass(aGenerateDatabase=True, aEnableUTFlag=False)
        warnings.filterwarnings("ignore")
        self._db = ebGetDefaultDB()

    @patch('exabox.ovm.clucontrol.exaBoxNode.mSetUser', return_value="admin")
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mConnectandExecuteonCiscoSwitches', return_value="") 
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mSetCiscoSwitchSSHPasswordless', return_value=("scaqau08sw-adm0.us.oracle.com", "scaqau08sw-adm0.us.oracle.com"))
    def test_mHandlerAdminSwitchConnect(self, mock_mSetUser, mock_mConnectandExecuteonCiscoSwitches, mock_mSetCiscoSwitchSSHPasswordless):
        ebLogInfo("Running unit test on mHandlerAdminSwitchConnect.")
        self.mGetClubox().mGetCommandHandler().mHandlerAdminSwitchConnect()
        ebLogInfo("Unit test on mHandlerAdminSwitchConnect succeeded.")
    
    @patch('exabox.ovm.clucontrol.exaBoxNode.mSetUser', return_value="admin")
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mConnectandExecuteonCiscoSwitches', return_value="")
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mSetCiscoSwitchSSHPasswordless', return_value=("scaqau08sw-adm0.us.oracle.com", "scaqau08sw-adm0.us.oracle.com"))
    def test_mReturnandConnectRoceSpineSwitches(self, mock_mSetUser, mock_mConnectandExecuteonCiscoSwitches, mock_mSetCiscoSwitchSSHPasswordless):
        ebLogInfo("Running unit test on mReturnandConnectRoceSpineSwitches")
        self.mGetClubox().mReturnandConnectRoceSpineSwitches()
        ebLogInfo("Unit test on mReturnandConnectRoceSpineSwitches succeeded.")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnandConnectRoceSpineSwitches', return_value=("scaqau08roces0.us.oracle.com"))
    def test_mReturnSwitches(self, mock_mReturnandConnectRoceSpineSwitches):
        _list_of_switches = []
        ebLogInfo("Running unit test on mReturnSwitches")
        _list_of_switches = self.mGetClubox().mReturnSwitches(True, True)
        ebLogInfo("Unit test on mReturnSwitches succeeded.")

    def test_clusterless_dom0_filtering_respects_payload(self):
        ebLogInfo("Running unit test on clusterless dom0 filtering.")
        _clubox = self.mGetClubox()
        _original_options = getattr(_clubox, '_exaBoxCluCtrl__options', None)

        _options = testOptions()
        _options.jsonconf = {
            "ComputeNodeList": [
                "dom0a.example.com",
                "dom0b.example.com"
            ],
            "StorageNodeList": [
                "cell1.example.com",
                "cell2.example.com"
            ],
            "AdditionalOptions": [
                {
                    "ExcludedNodeList": [
                        "dom0b.example.com",
                        "cell2.example.com"
                    ]
                }
            ]
        }

        setattr(_clubox, '_exaBoxCluCtrl__options', _options)

        try:
            with patch.object(
                _clubox,
                'mReadComputes',
                return_value=[
                    "dom0a.example.com",
                    "dom0b.example.com",
                    "dom0c.example.com"
                ]
            ), patch.object(
                _clubox,
                'mIsClusterLessXML',
                return_value=True
            ):
                _filtered_nodes = _clubox.mReturnDom0DomUPair(
                    aIsClusterLessXML=True,
                    aRetDummyDomu=False
                )

            self.assertEqual(_filtered_nodes, [["dom0a.example.com", ""]])
        finally:
            setattr(_clubox, '_exaBoxCluCtrl__options', _original_options)
        ebLogInfo("Unit test on clusterless dom0 filtering succeeded.")

    def test_clusterless_cell_filtering_respects_payload(self):
        ebLogInfo("Running unit test on clusterless cell filtering.")
        _clubox = self.mGetClubox()
        _original_options = getattr(_clubox, '_exaBoxCluCtrl__options', None)

        _options = testOptions()
        _options.jsonconf = {
            "ComputeNodeList": [
                "dom0a.example.com",
                "dom0b.example.com"
            ],
            "StorageNodeList": [
                "cell1.example.com",
                "cell2.example.com"
            ],
            "AdditionalOptions": [
                {
                    "ExcludedNodeList": [
                        "dom0b.example.com",
                        "cell2.example.com"
                    ]
                }
            ]
        }

        setattr(_clubox, '_exaBoxCluCtrl__options', _options)

        try:
            with patch.object(
                _clubox,
                'mReadCellMachines',
                return_value=[
                    "cell1.example.com",
                    "cell2.example.com",
                    "cell3.example.com"
                ]
            ), patch.object(
                _clubox,
                'mIsClusterLessXML',
                return_value=True
            ):
                _filtered_cells = _clubox.mReturnCellNodes(
                    aIsClusterLessXML=True
                )

            self.assertEqual(
                set(_filtered_cells.keys()),
                {"cell1.example.com"}
            )
        finally:
            setattr(_clubox, '_exaBoxCluCtrl__options', _original_options)
        ebLogInfo("Unit test on clusterless cell filtering succeeded.")

    def test_clusterless_dom0_no_payload_returns_all_nodes(self):
        ebLogInfo("Running clusterless patching with no payload")
        _clubox = self.mGetClubox()
        _original_options = getattr(_clubox, '_exaBoxCluCtrl__options', None)

        _options = testOptions()
        _options.jsonconf = {}
        setattr(_clubox, '_exaBoxCluCtrl__options', _options)

        try:
            with patch.object(
                _clubox,
                'mReadComputes',
                return_value=[
                    "dom0a.example.com",
                    "dom0b.example.com"
                ]
            ), patch.object(
                _clubox,
                'mIsClusterLessXML',
                return_value=True
            ):
                _filtered_nodes = _clubox.mReturnDom0DomUPair(
                    aIsClusterLessXML=True,
                    aRetDummyDomu=False
                )

            ebLogInfo(f"[UT] clusterless_dom0_no_payload result={_filtered_nodes}")
            self.assertEqual(
                _filtered_nodes,
                [
                    ["dom0a.example.com", ""],
                    ["dom0b.example.com", ""]
                ]
            )
        finally:
            setattr(_clubox, '_exaBoxCluCtrl__options', _original_options)

    def test_clusterless_dom0_all_filtered_out_returns_empty(self):
        ebLogInfo("Running clusterless patching with all dom0s filtered out")
        _clubox = self.mGetClubox()
        _original_options = getattr(_clubox, '_exaBoxCluCtrl__options', None)

        _options = testOptions()
        _options.jsonconf = {
            "ComputeNodeList": ["dom0a.example.com"],
            "AdditionalOptions": [
                {"ExcludedNodeList": ["dom0a.example.com"]}
            ]
        }
        setattr(_clubox, '_exaBoxCluCtrl__options', _options)

        try:
            with patch.object(
                _clubox,
                'mReadComputes',
                return_value=[
                    "dom0a.example.com",
                    "dom0b.example.com"
                ]
            ), patch.object(
                _clubox,
                'mIsClusterLessXML',
                return_value=True
            ):
                _filtered_nodes = _clubox.mReturnDom0DomUPair(
                    aIsClusterLessXML=True,
                    aRetDummyDomu=False
                )

            ebLogInfo(f"[UT] clusterless_dom0_all_filtered_out result={_filtered_nodes}")
            self.assertEqual(_filtered_nodes, [])
        finally:
            setattr(_clubox, '_exaBoxCluCtrl__options', _original_options)

    def test_clusterless_cell_no_allow_list_returns_all(self):
        ebLogInfo("Running clusterless patching with empty allow list: start")
        _clubox = self.mGetClubox()
        _original_options = getattr(_clubox, '_exaBoxCluCtrl__options', None)

        _options = testOptions()
        _options.jsonconf = {}
        setattr(_clubox, '_exaBoxCluCtrl__options', _options)

        try:
            with patch.object(
                _clubox,
                'mReadCellMachines',
                return_value=[
                    "cell1.example.com",
                    "cell2.example.com"
                ]
            ), patch.object(
                _clubox,
                'mIsClusterLessXML',
                return_value=True
            ):
                _filtered_cells = _clubox.mReturnCellNodes(
                    aIsClusterLessXML=True
                )

            ebLogInfo(f"[UT] clusterless_cell_no_allow_list result={list(_filtered_cells.keys())}")
            self.assertEqual(
                set(_filtered_cells.keys()),
                {"cell1.example.com", "cell2.example.com"}
            )
        finally:
            setattr(_clubox, '_exaBoxCluCtrl__options', _original_options)

    def test_clusterless_cell_all_filtered_out_returns_empty(self):
        ebLogInfo("Running clusterless patching with all cells filtered out")
        _clubox = self.mGetClubox()
        _original_options = getattr(_clubox, '_exaBoxCluCtrl__options', None)

        _options = testOptions()
        _options.jsonconf = {
            "StorageNodeList": ["cell1.example.com"],
            "AdditionalOptions": [
                {"ExcludedNodeList": ["cell1.example.com"]}
            ]
        }
        setattr(_clubox, '_exaBoxCluCtrl__options', _options)

        try:
            with patch.object(
                _clubox,
                'mReadCellMachines',
                return_value=[
                    "cell1.example.com",
                    "cell2.example.com"
                ]
            ), patch.object(
                _clubox,
                'mIsClusterLessXML',
                return_value=True
            ):
                _filtered_cells = _clubox.mReturnCellNodes(
                    aIsClusterLessXML=True
                )

            ebLogInfo(f"[UT] clusterless_cell_all_filtered_out result={list(_filtered_cells.keys())}")
            self.assertEqual(_filtered_cells, {})
        finally:
            setattr(_clubox, '_exaBoxCluCtrl__options', _original_options)



if __name__ == "__main__":
    unittest.main(warnings='ignore')
