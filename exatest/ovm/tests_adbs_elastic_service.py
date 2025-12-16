#!/usr/bin/env python
#
# $Header: tests_adbs_elastic_service.py
#
# tests_adbs_elastic_service.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_adbs_elastic_service.py - Unit tests for adbs_elastic_service.py
#
#    DESCRIPTION
#      Unit tests for ADBS elastic service functions and classes
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl     11/12/25 - Creation
#
import datetime
import json
import unittest
import warnings
import copy
import os, re, io
import sys
from io import StringIO
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, Mock
from paramiko.ssh_exception import SSHException
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogWarn
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.network.Connection import exaBoxConnection
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.utils.node import connect_to_host, node_exec_cmd, node_exec_cmd_check, node_cmd_abs_path_check, node_write_text_file
from exabox.ovm.clumisc import mWaitForSystemBoot, ebADBSUtil
from exabox.ovm.cluelastic import getGridHome
from exabox.ovm.cluexaccsecrets import ebExaCCSecrets
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Node import exaBoxNode
from exabox.core.Error import gDiskgroupError, gReshapeError, ExacloudRuntimeError, ebError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogVerbose, ebLogJson, ebLogTrace, ebLogCritical
from exabox.utils.node import connect_to_host, node_exec_cmd, node_exec_cmd_check, node_cmd_abs_path_check, node_write_text_file
from exabox.utils.common import mCompareModel
from exabox.ovm.clumisc import mWaitForSystemBoot, ebADBSUtil
from exabox.ovm.clustorage import ebCluStorageConfig
from exabox.ovm.cluelastic import getGridHome
import exabox.ovm.adbs_elastic_service as aes

class ebTestAdbsElasticService(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestAdbsElasticService, cls).setUpClass(aGenerateDatabase=True, aEnableUTFlag=False, aUseOeda=True)
        cls._db = ebGetDefaultDB()
        warnings.filterwarnings("ignore")

    def test_mReturnSrcDom0DomUPair(self):
        ebLogInfo("Running unit test on mReturnSrcDom0DomUPair")
        ebox = self.mGetClubox()
        all_pairs = [('dom0-1', 'domU-1'), ('dom0-2', 'domU-2')]
        new_pairs = [('dom0-2', 'domU-2')]
        with patch.object(ebox, 'mGetElasticOldDom0DomUPair', return_value=all_pairs), \
             patch.object(ebox, 'mReturnDom0DomUPair', return_value=new_pairs):
            result = aes.mReturnSrcDom0DomUPair(ebox)
            self.assertEqual(result, [('dom0-1', 'domU-1')])

    def test_mReturnFirstDom0DomUPair(self):
        ebLogInfo("Running unit test on mReturnFirstDom0DomUPair")
        ebox = self.mGetClubox()
        pairs = [('dom0-1', 'domU-1'), ('dom0-2', 'domU-2')]
        with patch.object(ebox, 'mReturnDom0DomUPair', return_value=pairs):
            result = aes.mReturnFirstDom0DomUPair(ebox)
            self.assertEqual(result, ('dom0-1', 'domU-1'))

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    @patch('exabox.ovm.adbs_elastic_service.node_exec_cmd')
    def test_mUpdateQuorumDiskConfig(self, mock_node_exec_cmd, mock_connect_to_host):
        ebLogInfo("Running unit test on mUpdateQuorumDiskConfig")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mExecuteCmdLog.return_value = None
        mock_node.mExecuteCmd.return_value = (None, MagicMock(read=MagicMock(return_value='10.0.1.1\n10.0.1.2')), None)

        with patch.object(ebox, 'mReturnDom0DomUPair', return_value=[('dom0-1', 'domU-1'), ('dom0-2', 'domU-2')]), \
             patch.object(ebox, 'mGetElasticOldDom0DomUPair', return_value=[('dom0-1', 'domU-1'), ('dom0-2', 'domU-2')]), \
             patch.object(ebox, 'mGetClusters') as mock_clusters, \
             patch.object(ebox, 'mGetStorage') as mock_storage:
            mock_cluster = MagicMock()
            mock_clusters.return_value.mGetCluster.return_value = mock_cluster
            mock_cluster.mGetCluDiskGroups.return_value = ['dg1']
            mock_dg_config = MagicMock()
            mock_storage.return_value.mGetDiskGroupConfig.return_value = mock_dg_config
            mock_dg_config.mGetDgName.side_effect = ['RECO', 'DATA']
            aes.mUpdateQuorumDiskConfig(ebox)

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    @patch('exabox.ovm.adbs_elastic_service.ebExaCCSecrets')
    def test_mAddExacliPasswdToNewDomUs(self, mock_ebExaCCSecrets, mock_connect_to_host):
        ebLogInfo("Running unit test on mAddExacliPasswdToNewDomUs")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mFileExists.return_value = True
        mock_node.mExecuteCmd.return_value = (None, MagicMock(read=MagicMock(return_value='password')), None)
        mock_node.mGetCmdExitStatus.return_value = 0
        mock_secrets = MagicMock()
        mock_ebExaCCSecrets.return_value = mock_secrets

        with patch.object(ebox, 'mCopyCreateVIP'), \
             patch.object(ebox, 'mCheckConfigOption', return_value='True'):
            aes.mAddExacliPasswdToNewDomUs(ebox, 'srcDomU', ['newDomU1'])

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    def test_mCreateGriddiskADBS(self, mock_connect_to_host):
        ebLogInfo("Running unit test on mCreateGriddiskADBS")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mExecuteCmdLog.return_value = None

        with patch.object(ebox, 'mGetClusters') as mock_clusters, \
             patch.object(ebox, 'mGetStorage') as mock_storage:
            mock_cluster = MagicMock()
            mock_clusters.return_value.mGetCluster.return_value = mock_cluster
            mock_cluster.mGetCluDiskGroups.return_value = ['datadg_id', 'recodg_id']
            mock_dg_config = MagicMock()
            mock_storage.return_value.mGetDiskGroupConfig.return_value = mock_dg_config
            mock_dg_config.mGetGridDiskPrefix.side_effect = ['DATA', 'RECO', 'SPRC']
            mock_dg_config.mGetSliceSize.side_effect = [100, 200, 300]
            aes.mCreateGriddiskADBS(ebox, 'cell1')

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    def test_mDeleteGriddiskADBS(self, mock_connect_to_host):
        ebLogInfo("Running unit test on mDeleteGriddiskADBS")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mExecuteCmdLog.return_value = None

        with patch.object(ebox, 'mGetClusters') as mock_clusters, \
             patch.object(ebox, 'mGetStorage') as mock_storage:
            mock_cluster = MagicMock()
            mock_clusters.return_value.mGetCluster.return_value = mock_cluster
            mock_cluster.mGetCluDiskGroups.return_value = ['dg1']
            mock_dg_config = MagicMock()
            mock_storage.return_value.mGetDiskGroupConfig.return_value = mock_dg_config
            mock_dg_config.mGetDgName.return_value = 'DG1'
            aes.mDeleteGriddiskADBS(ebox, 'cell1')

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    @patch('exabox.ovm.adbs_elastic_service.node_exec_cmd_check')
    @patch('exabox.ovm.adbs_elastic_service.node_cmd_abs_path_check')
    def test_mGetKeyValueCellkey(self, mock_node_cmd_abs_path_check, mock_node_exec_cmd_check, mock_connect_to_host):
        ebLogInfo("Running unit test on mGetKeyValueCellkey")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node_cmd_abs_path_check.return_value = 'cat'
        mock_node_exec_cmd_check.return_value = (None, 'key=value\nasm=cluster\n', None)

        with patch.object(ebox, 'mReturnDom0DomUPair', return_value=[('dom0-1', 'domU-1')]):
            result = aes.mGetKeyValueCellkey(ebox)
            self.assertEqual(result, {'key': 'value', 'asm': 'cluster'})

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    @patch('exabox.ovm.adbs_elastic_service.ebLogInfo')
    def test_mAssignKeyToCell(self, mock_ebLogInfo, mock_connect_to_host):
        ebLogInfo("Running unit test on mAssignKeyToCell")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mExecuteCmdLog.return_value = None
        mock_node.mGetCmdExitStatus.return_value = 0

        with patch('exabox.ovm.adbs_elastic_service.mGetKeyValueCellkey', return_value={'key': 'testkey', 'asm': 'testasm'}):
            aes.mAssignKeyToCell(ebox, 'cell1')

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    @patch('exabox.ovm.adbs_elastic_service.ebLogWarn')
    def test_mRemoveKeyFromCell(self, mock_ebLogWarn, mock_connect_to_host):
        ebLogInfo("Running unit test on mRemoveKeyFromCell")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mExecuteCmdLog.return_value = None
        mock_node.mGetCmdExitStatus.return_value = 0

        with patch('exabox.ovm.adbs_elastic_service.mGetKeyValueCellkey', return_value={'asm': 'testasm'}):
            aes.mRemoveKeyFromCell(ebox, 'cell1')

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    def test_mCheckASMScopeSecurity(self, mock_connect_to_host):
        ebLogInfo("Running unit test on mCheckASMScopeSecurity")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mFileExists.return_value = True

        with patch.object(ebox, 'mGetClusters') as mock_clusters:
            mock_cluster = MagicMock()
            mock_clusters.return_value.mGetCluster.return_value = mock_cluster
            mock_cluster.mGetCluAsmScopedSecurity.return_value = 'TRUE'
            result = aes.mCheckASMScopeSecurity(ebox)
            self.assertTrue(result)

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    @patch('exabox.ovm.adbs_elastic_service.mGetKeyValueCellkey')
    def test_mSetAvailableToOnGriddisk(self, mock_mGetKeyValueCellkey, mock_connect_to_host):
        ebLogInfo("Running unit test on mSetAvailableToOnGriddisk")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mExecuteCmdLog.return_value = None
        mock_node.mExecuteCmdCellcli.return_value = (None, MagicMock(read=MagicMock(return_value='disk1\ndisk2')), None)
        mock_node.mGetCmdExitStatus.return_value = 0
        mock_mGetKeyValueCellkey.return_value = {'asm': 'cluster'}

        with patch.object(ebox, 'mGetClusters') as mock_clusters, \
             patch.object(ebox, 'mGetStorage') as mock_storage:
            mock_cluster = MagicMock()
            mock_clusters.return_value.mGetCluster.return_value = mock_cluster
            mock_cluster.mGetCluDiskGroups.return_value = ['dg1']
            mock_dg_config = MagicMock()
            mock_storage.return_value.mGetDiskGroupConfig.return_value = mock_dg_config
            mock_dg_config.mGetGridDiskPrefix.side_effect = ['RECO', 'DATA']
            aes.mSetAvailableToOnGriddisk(ebox, 'cell1')

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    @patch('exabox.ovm.adbs_elastic_service.node_cmd_abs_path_check')
    @patch('exabox.ovm.adbs_elastic_service.node_exec_cmd_check')
    def test_mGetIpsForCellipOra(self, mock_node_exec_cmd_check, mock_node_cmd_abs_path_check, mock_connect_to_host):
        ebLogInfo("Running unit test on mGetIpsForCellipOra")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node_cmd_abs_path_check.side_effect = ['ip', 'grep']
        mock_node.mExecuteCmd.return_value = (None, MagicMock(read=MagicMock(return_value='10.0.1.1')), None)
        mock_node.mGetCmdExitStatus.return_value = 0

        result = aes.mGetIpsForCellipOra(ebox, 'cell1')
        self.assertEqual(result, 'cell="10.0.1.1;10.0.1.1"')

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    @patch('exabox.ovm.adbs_elastic_service.node_cmd_abs_path_check')
    @patch('exabox.ovm.adbs_elastic_service.node_exec_cmd_check')
    @patch('exabox.ovm.adbs_elastic_service.node_write_text_file')
    def test_mAppendCellipOraForDomU(self, mock_node_write_text_file, mock_node_exec_cmd_check, mock_node_cmd_abs_path_check, mock_connect_to_host):
        ebLogInfo("Running unit test on mAppendCellipOraForDomU")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node_cmd_abs_path_check.return_value = 'cat'
        mock_node_exec_cmd_check.return_value = (None, 'existing content', None)

        with patch.object(ebox, 'mReturnAllClusterHosts', return_value=([], ['domU1'], [], [])), \
             patch('exabox.ovm.adbs_elastic_service.mGetIpsForCellipOra', return_value='cell="10.0.1.1;10.0.1.2"'):
            aes.mAppendCellipOraForDomU(ebox, 'cell1')

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    @patch('exabox.ovm.adbs_elastic_service.node_cmd_abs_path_check')
    @patch('exabox.ovm.adbs_elastic_service.node_exec_cmd_check')
    @patch('exabox.ovm.adbs_elastic_service.node_exec_cmd')
    def test_mRemoveCellipOraForDomU(self, mock_node_exec_cmd, mock_node_exec_cmd_check, mock_node_cmd_abs_path_check, mock_connect_to_host):
        ebLogInfo("Running unit test on mRemoveCellipOraForDomU")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node_cmd_abs_path_check.side_effect = ['cat', 'sed']
        mock_node_exec_cmd_check.return_value = (None, 'content with cell="10.0.1.1;10.0.1.2"', None)

        with patch.object(ebox, 'mReturnAllClusterHosts', return_value=([], ['domU1'], [], [])), \
             patch('exabox.ovm.adbs_elastic_service.mGetIpsForCellipOra', return_value='cell="10.0.1.1;10.0.1.2"'):
            aes.mRemoveCellipOraForDomU(ebox, 'cell1')

    @patch('exabox.ovm.adbs_elastic_service.ebADBSUtil')
    def test_mCreateADBSSiteGroupConfig(self, mock_ebADBSUtil):
        ebLogInfo("Running unit test on mCreateADBSSiteGroupConfig")
        ebox = self.mGetClubox()
        mock_options = MagicMock()
        mock_adbs_util = MagicMock()
        mock_ebADBSUtil.return_value = mock_adbs_util
        mock_adbs_util.mCreateSiteGroupConfigFile.return_value = 0

        with patch.object(ebox, 'mGetArgsOptions', return_value=mock_options), \
             patch.object(ebox, 'mReturnDom0DomUPair', return_value=[('dom0-1', 'domU-1')]):
            result = aes.mCreateADBSSiteGroupConfig(ebox)
            self.assertEqual(result, 0)

    def test_mGetorCreateDomUObj(self):
        ebLogInfo("Running unit test on mGetorCreateDomUObj")
        domu_dict = {}
        result = aes.mGetorCreateDomUObj('domU1', domu_dict)
        self.assertIsInstance(result, aes.ebAdbsGrid)
        self.assertIn('domU1', domu_dict)
        # Call again to test retrieval
        result2 = aes.mGetorCreateDomUObj('domU1', domu_dict)
        self.assertEqual(result, result2)

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    def test_ebAdbsGrid_mUpdateGridHomePath(self, mock_connect_to_host):
        ebLogInfo("Running unit test on ebAdbsGrid.mUpdateGridHomePath")
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mExecuteCmd.return_value = (None, MagicMock(readlines=MagicMock(return_value=['/old/path'])), None)
        mock_node.mGetCmdExitStatus.return_value = 0
        mock_node.mExecuteCmdLog.return_value = None

        with patch('exabox.ovm.adbs_elastic_service.getGridHome', return_value='/new/path'):
            grid = aes.ebAdbsGrid('domU1')
            grid.mUpdateGridHomePath()

    @patch('exabox.ovm.adbs_elastic_service.connect_to_host')
    def test_exaBoxAdbs_mGetGridHome(self, mock_connect_to_host):
        ebLogInfo("Running unit test on exaBoxAdbs.mGetGridHome")
        ebox = self.mGetClubox()
        mock_node = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = mock_node
        mock_node.mExecuteCmd.return_value = (None, MagicMock(readlines=MagicMock(return_value=['/grid/home'])), None)

        adbs = aes.exaBoxAdbs(ebox)
        path, sid = adbs.mGetGridHome('domU1')
        self.assertEqual(path, '/grid/home')
        self.assertEqual(sid, '/grid/home')

if __name__ == "__main__":
    unittest.main(warnings='ignore')



