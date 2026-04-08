#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cludiskgroups.py /main/6 2026/01/29 18:05:46 zpallare Exp $
#
# tests_cludiskgroups.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
#    zpallare    01/29/26 - Bug 38890053 - EXACS:25.4.1 ONEOFF2:26.1.1
#                           Dbaas:custom data-reco-sparse: even when reshape
#                           fails, exacloud passes as success
#    shapatna    12/23/25 - Bug 38791495: Modify Unit tests
#                           to include keys: growMB, shrinkMB
#    aararora    12/10/25 - 38714897: Codex UT enhancement
#    nelango     11/04/25 - Bug 38483116: testcase for
#                           mCalculateFreeSpaceGriddisks
#    bhpati      04/03/25 - Creation
#

import itertools
import math
import time
import unittest
import warnings
import xml.etree.ElementTree as ET
from unittest import mock
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch, MagicMock
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError, gDiskgroupError, gElasticError, gReshapeError
from exabox.ovm.cludiskgroups import ebDiskgroupOpConstants, ebCluManageDiskgroup
from exabox.ovm.cludiskgroups import ebCluDbaas, ebCluUtils, exaBoxNode, universal_converter
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

    def _create_manager_with_stubs(self, mock_get_gcontext, mock_ebCluDbaas, extra_traces=True, time_check_seconds="600"):
        context = MagicMock()
        context.mGetConfigOptions.return_value = {}
        context.mGetBasePath.return_value = "/tmp"
        mock_get_gcontext.return_value = context

        dbaas_obj = MagicMock()
        mock_ebCluDbaas.return_value = dbaas_obj

        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        def config_option(key, default=None):
            if key == 'extra_traces':
                return "True" if extra_traces else default
            if key == 'time_check_rebalance_seconds':
                return time_check_seconds
            return default

        ebox.mCheckConfigOption.side_effect = config_option
        ebox.mGetGridHome.return_value = ("/grid", "+ASM1")

        options = MagicMock()
        options.configpath = "/tmp"
        options.jsonconf = {}

        manager = ebCluManageDiskgroup(ebox, options)
        manager.mSetDbaasObj(dbaas_obj)
        manager.mSetOutJson({})
        manager.mSetOutFile('/tmp/outfile')
        manager.mSetLastDomUused('domu1')

        return manager, ebox, dbaas_obj, options
    def _mock_cluster_with_sparse(self, ebox, constants, sparse_name=None):
        cluster_ctrl = MagicMock()
        cluster = MagicMock()
        storage = MagicMock()

        data_dg = MagicMock()
        data_dg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_dg.mGetDgName.return_value = 'DATAC'
        data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        reco_dg = MagicMock()
        reco_dg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        reco_dg.mGetDgName.return_value = 'RECOC'

        sparse_dg = MagicMock()
        sparse_dg.mGetDiskGroupType.return_value = constants._sparse_dg_type_str
        sparse_dg.mGetDgName.return_value = sparse_name or 'SPRC'

        dgid_map = {
            'dg_data': data_dg,
            'dg_reco': reco_dg,
            'dg_sparse': sparse_dg
        }

        cluster.mGetCluDiskGroups.return_value = list(dgid_map.keys())

        def get_config(dgid):
            return dgid_map[dgid]

        storage.mGetDiskGroupConfig.side_effect = get_config

        cluster_ctrl.mGetCluster.return_value = cluster
        ebox.mGetClusters.return_value = cluster_ctrl
        ebox.mGetStorage.return_value = storage

        return data_dg, reco_dg, sparse_dg

    def _mock_diskgroup_size(self, manager, constants, size_map):
        def size_lookup(options, dg_name, consts, aUsedMB=0):
            key = (dg_name, bool(aUsedMB))
            if key not in size_map:
                raise AssertionError('Unexpected diskgroup lookup: %s' % (key,))
            return size_map[key]

        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=size_lookup)

    def _stub_cluster_io(self, manager):
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=0)
        manager.mValidateAndGetFailgroupDetails = MagicMock(return_value=0)
        manager._extract_cell_vs_griddisks_map = MagicMock(return_value=0)
        manager.mGetCelldisks = MagicMock(return_value=['CD_01'])
        manager.mCalculateFreeSpaceCelldisk = MagicMock(return_value=1024)

    def _stub_parse_input_for_drop(self, manager, constants):
        def fake_parse_input(options, req_params, diskgroup_data=None):
            req_params[constants._diskgroupname_key] = 'SPRC1'
            req_params[constants._diskgrouptype_key] = 'sparse'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse_input)

    def _stub_rollback_helpers(self, manager):
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)

    def _mock_diskgroup_sizes_sequence(self, manager, size_pairs):
        def lookup(options, dg, constants, aUsedMB=0):
            key = (dg, aUsedMB)
            if key not in size_pairs:
                raise AssertionError('Unexpected diskgroup size lookup: %s' % (key,))
            return size_pairs[key]

        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=lookup)

    def _setup_sparse_cluster(self, manager, ebox, constants, dg_name='SPRC1'):
        data_dg, reco_dg, sparse_dg = self._mock_cluster_with_sparse(ebox, constants, sparse_name=dg_name)
        data_dg.mGetDgName.return_value = 'DATAC1'
        reco_dg.mGetDgName.return_value = 'RECOC1'
        sparse_dg.mGetDgName.return_value = dg_name
        return data_dg, reco_dg, sparse_dg

    def _mock_mCalculateNewDgSizes_inputs(self, manager, constants, ratio="60:20:20", total_storage_gb=None):
        ebox = manager.mGetEbox()
        storage = MagicMock()
        data_dg = MagicMock()
        reco_dg = MagicMock()

        data_dg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        reco_dg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        data_dg.mGetDgName.return_value = 'DATAC1'
        reco_dg.mGetDgName.return_value = 'RECOC1'
        data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        storage.mGetDiskGroupConfig.side_effect = lambda name: {
            'dg_data': data_dg,
            'dg_reco': reco_dg
        }[name]

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco']
        cluster_ctrl = MagicMock()
        cluster_ctrl.mGetCluster.return_value = cluster
        ebox.mGetClusters.return_value = cluster_ctrl
        ebox.mGetStorage.return_value = storage

        cur_sizes = {
            constants._data_dg_rawname: 6000,
            constants._reco_dg_rawname: 2000,
            constants._redundancy_factor: 2
        }

        diskgroup_data = {}

        options = MagicMock()
        options.diskgroupOp = 'update'

        in_params = {
            constants._diskgrouptype_key: constants._sparse_dg_type_str,
            constants._diskgroup_ratios_key: ratio
        }
        if total_storage_gb is not None:
            in_params[constants._total_storagegb_key] = total_storage_gb

        return cur_sizes, diskgroup_data, options, in_params

    def _configure_mCalculateNewDgSizes_dependencies(self, manager, diskgroup_data, cur_sizes, ratio='60:20:20'):
        manager.mClusterParseInput = MagicMock(return_value=0)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mSetDiskGroupOperationData(diskgroup_data)
        manager.mCheckIfDgsResizable = MagicMock(return_value=0)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mCalculateFreeSpaceCelldisk = MagicMock(return_value=1024)
        manager.mGetCelldisks = MagicMock(return_value=['CD_01'])
        manager.mGetGridDiskCountRetryResize = MagicMock(return_value=None)
        manager.mResizeDgAndGriddisks = MagicMock(return_value=0)
        manager.mDropGridDisks = MagicMock(return_value=0)
        manager.mDropDiskGroup = MagicMock(return_value=0)
        manager.mRollback = MagicMock(return_value=0)
        manager.mSetDiskGroupOperationData(diskgroup_data)
        manager._rollback_stack = []
        manager.mCalculateNewDgSizes = mock.MagicMock(side_effect=manager.mCalculateNewDgSizes)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=lambda opts, dg_name, consts, aUsedMB=0: cur_sizes[dg_name])
        manager.mClusterParseInput.side_effect = lambda options, inparams, data=None: inparams.update({
            manager.mGetConstantsObj()._diskgrouptype_key: manager.mGetConstantsObj()._sparse_dg_type_str,
            manager.mGetConstantsObj()._diskgroupname_key: 'SPRC1',
            manager.mGetConstantsObj()._diskgroup_ratios_key: ratio
        }) or 0

    def _invoke_mCalculateNewDgSizes(self, manager, options, diskgroup_data, cur_sizes, shrink=True, precheck_only=False):
        return manager.mCalculateNewDgSizes(options, diskgroup_data, cur_sizes, shrink)

    def test_universal_converter_handles_complex_objects(self):
        element = ET.Element('root', attrib={'attr': 'value'})
        element.text = ' text '
        child = ET.SubElement(element, 'child')
        child.text = 'child-text'

        class Sample(object):
            def __init__(self):
                self.public = 'pub'
                self._private = 'priv'
                self.__mangled = 'secret'

        sample = Sample()

        payload = {
            'number': 42,
            'tuple': (1, 2),
            'set': {3, 4},
            'element': element,
            'object': sample
        }

        converted = universal_converter(payload)

        self.assertEqual(converted['number'], 42)
        self.assertEqual(converted['tuple'], [1, 2])
        self.assertIn('element', converted)
        element_dict = converted['element']
        self.assertEqual(element_dict['__class__'], 'Element')
        self.assertEqual(element_dict['tag'], 'root')
        self.assertEqual(element_dict['attrib'], {'attr': 'value'})
        self.assertEqual(element_dict['text'], 'text')
        self.assertEqual(len(element_dict['children']), 1)
        child_dict = element_dict['children'][0]
        self.assertEqual(child_dict['tag'], 'child')
        self.assertEqual(child_dict['text'], 'child-text')

        obj_dict = converted['object']
        self.assertEqual(obj_dict['__class__'], 'Sample')
        self.assertEqual(obj_dict['public'], 'pub')
        self.assertEqual(obj_dict['_private'], 'priv')
        self.assertIn('mangled', obj_dict)

    # Auto-generated test for mSetResizeDataOnCells/mSetResizeRecoOnCells/mSetResizeSparseOnCells/mSetCurrentRetrySizeTotalMB
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_resize_retry_setters_and_getters_update_state(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)

        manager.mSetResizeDataOnCells(True)
        manager.mSetResizeRecoOnCells(True)
        manager.mSetResizeSparseOnCells(True)
        manager.mSetCurrentRetrySizeTotalMB(4096, 'DATADG')
        manager.mSetGridDiskCountRetryResize(2, 'DATADG')

        self.assertTrue(manager.mGetResizeDataOnCells())
        self.assertTrue(manager.mGetResizeRecoOnCells())
        self.assertTrue(manager.mGetResizeSparseOnCells())
        self.assertEqual(manager.mGetCurrentRetrySizeTotalMB('DATADG'), 4096)
        self.assertEqual(manager.mGetGridDiskCountRetryResize('DATADG'), 2)

    def _setup_rebalance_estimate(self, manager, aOptions=None, rebalance_power=None, include_eta=True):
        constants = manager.mGetConstantsObj()
        ebox = manager.mGetEbox()
        dbaas = manager.mGetDbaasObj()

        dom_u = 'domu-main'
        manager.mSetDomUs([dom_u])

        ebox.mGetUUID.return_value = 'uuid123'

        in_json = {
            constants._params_key: {
                constants._newsizeMB_key: 2048
            }
        }
        if rebalance_power is not None:
            in_json[constants._params_key][constants._rebalancepower_key] = rebalance_power

        def _populate(action, obj, out, dom, params, opts, flag):
            payload = {
                'Status': 'Pass',
                'rebalance_time_estimate': {
                    'error_code': 0,
                    'diskgroup': params[constants._diskgroupname_key]
                }
            }
            if include_eta:
                payload['rebalance_time_estimate']['rebalance_eta_sec'] = 123
            out.update(payload)

        dbaas.mExecuteDBaaSAPIAction.side_effect = _populate

        return in_json, constants, dom_u

    # Auto-generated test for mDropGridDisks
    @patch('exabox.ovm.cludiskgroups.exaBoxNode')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mDropGridDisks_success(self, mock_ebCluDbaas, mock_get_gcontext, mock_exaBoxNode):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        ebox.mReturnCellNodes.return_value = {'cell2': object(), 'cell1': object()}

        node_instance = MagicMock()
        node_instance.mGetCmdExitStatus.return_value = 0
        mock_exaBoxNode.return_value = node_instance

        rc = manager.mDropGridDisks(options, 'DG_PREFIX', aForce=True)

        self.assertEqual(rc, 0)
        expected_command = "cellcli -e drop griddisk all prefix=DG_PREFIX force"
        self.assertEqual(
            mock_exaBoxNode.call_args_list,
            [mock.call(mock_get_gcontext.return_value), mock.call(mock_get_gcontext.return_value)]
        )
        self.assertEqual(node_instance.mConnect.call_args_list, [mock.call(aHost='cell1'), mock.call(aHost='cell2')])
        for call_args in node_instance.mExecuteCmdLog.call_args_list:
            self.assertEqual(call_args.args[0], expected_command)
        self.assertEqual(node_instance.mDisconnect.call_count, 2)

    # Auto-generated test for mLogRebalanceTimeEstimate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mLogRebalanceTimeEstimate_logs_success_with_rebalance_power(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        in_json, constants, _ = self._setup_rebalance_estimate(manager, options, rebalance_power=8)

        with patch('exabox.ovm.cludiskgroups.ebLogInfo') as mock_log_info:
            manager.mLogRebalanceTimeEstimate(in_json, options, 'DATAC1')

        dbaas_obj.mExecuteDBaaSAPIAction.assert_called_once()
        action_args = dbaas_obj.mExecuteDBaaSAPIAction.call_args[0]
        self.assertEqual(action_args[0], 'rebalance_time_estimate')
        params = action_args[4]
        self.assertEqual(params['diskgroup'], 'DATAC1')
        self.assertEqual(params[constants._rebalancepower_key], 8)
        self.assertIn(constants._newsizeMB_key, params)
        info_messages = [call.args[0] for call in mock_log_info.call_args_list]
        self.assertIn('*** The JSON for operation diskgroup action is rebalance_time_estimate', info_messages)
        self.assertTrue(any('"rebalance_eta_sec": 123' in msg for msg in info_messages))

    # Auto-generated test for mLogRebalanceTimeEstimate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mLogRebalanceTimeEstimate_no_rebalance_power(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        in_json, constants, _ = self._setup_rebalance_estimate(manager, options)

        with patch('exabox.ovm.cludiskgroups.ebLogInfo') as mock_log_info:
            manager.mLogRebalanceTimeEstimate(in_json, options, 'DATAC2')

        params = dbaas_obj.mExecuteDBaaSAPIAction.call_args[0][4]
        self.assertNotIn(constants._rebalancepower_key, params)
        self.assertEqual(params[constants._diskgroupname_key], 'DATAC2')
        info_messages = [call.args[0] for call in mock_log_info.call_args_list]
        self.assertIn('*** The JSON for operation diskgroup action is rebalance_time_estimate', info_messages)
        self.assertTrue(any('"rebalance_eta_sec": 123' in msg for msg in info_messages))

    # Auto-generated test for mLogRebalanceTimeEstimate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mLogRebalanceTimeEstimate_no_success_log_when_fail(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        in_json, constants, _ = self._setup_rebalance_estimate(manager, options)

        def failing_exec(action, obj, out, dom, params, opts, flag):
            out.update({'Status': 'Fail', 'rebalance_time_estimate': {'error_code': 5}})

        dbaas_obj.mExecuteDBaaSAPIAction.side_effect = failing_exec

        with patch('exabox.ovm.cludiskgroups.ebLogInfo') as mock_log_info:
            manager.mLogRebalanceTimeEstimate(in_json, options, 'DATAC3')

        info_messages = [call.args[0] for call in mock_log_info.call_args_list]
        self.assertFalse(any('"rebalance_eta_sec":' in msg for msg in info_messages))

    # Auto-generated test for mLogRebalanceTimeEstimate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mLogRebalanceTimeEstimate_no_eta_field_when_not_provided(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        in_json, constants, _ = self._setup_rebalance_estimate(manager, options, include_eta=False)

        with patch('exabox.ovm.cludiskgroups.ebLogInfo') as mock_log_info:
            manager.mLogRebalanceTimeEstimate(in_json, options, 'DATAC4')

        params = dbaas_obj.mExecuteDBaaSAPIAction.call_args[0][4]
        self.assertNotIn('rebalance_eta_sec', dbaas_obj.mExecuteDBaaSAPIAction.call_args[0][4])
        info_messages = [call.args[0] for call in mock_log_info.call_args_list]
        self.assertTrue(any('rebalance_time_estimate' in msg for msg in info_messages))
        self.assertFalse(any('rebalance_eta_sec' in msg for msg in info_messages))

    # Auto-generated test for mRelocateVotedisk
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mRelocateVotedisk_success_logs_info(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        ebox.mGetUUID.return_value = 'uuid-success'

        with patch.object(manager, 'mHandleDbaasapiSynchronousCall', return_value=0) as mock_handle, \
                patch('exabox.ovm.cludiskgroups.ebLogInfo') as mock_log_info:
            rc = manager.mRelocateVotedisk(options, 'DATA1')

        self.assertEqual(rc, 0)
        mock_handle.assert_called_once()
        call_args = mock_handle.call_args[0]
        self.assertEqual(call_args[0], options)
        self.assertFalse(call_args[2])
        injson = call_args[1]
        self.assertEqual(injson[constants._action_key], 'relocate_votedisk')
        params = injson[constants._params_key]
        self.assertEqual(params[constants._diskgroupname_key], 'DATA1')
        self.assertEqual(params[constants._param_infofile_key], '/var/opt/oracle/log/validate_uuid-success_infofile.json')
        self.assertEqual(injson[constants._flags_key], '')
        info_messages = [call.args[0] for call in mock_log_info.call_args_list]
        self.assertIn('*** Successfully relocated votedisk back to DATA1', info_messages)

    # Auto-generated test for mRelocateVotedisk
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mRelocateVotedisk_failure_logs_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        ebox.mGetUUID.return_value = 'uuid-failure'

        with patch.object(manager, 'mHandleDbaasapiSynchronousCall', return_value=9) as mock_handle, \
                patch('exabox.ovm.cludiskgroups.ebLogError') as mock_log_error:
            rc = manager.mRelocateVotedisk(options, 'DATA2')

        self.assertEqual(rc, 9)
        mock_handle.assert_called_once()
        error_messages = [call.args[0] for call in mock_log_error.call_args_list]
        self.assertIn('Relocation of votedisk back to DATA2 failed', error_messages)

    # Auto-generated test for mDropGridDisks
    @patch('exabox.ovm.cludiskgroups.exaBoxNode')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mDropGridDisks_failure_records_error(self, mock_ebCluDbaas, mock_get_gcontext, mock_exaBoxNode):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        ebox.mReturnCellNodes.return_value = {'cell0': object()}

        node_instance = MagicMock()
        node_instance.mGetCmdExitStatus.return_value = 1
        mock_exaBoxNode.return_value = node_instance

        with patch.object(manager, 'mRecordError', return_value=99) as mock_record_error:
            rc = manager.mDropGridDisks(options, 'DG_PREFIX', aForce=False)

        self.assertEqual(rc, 99)
        mock_record_error.assert_called_once_with(gDiskgroupError['GDDropFailed'], mock.ANY)
        node_instance.mDisconnect.assert_not_called()

    # Auto-generated test for mDropDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDropDiskGroup_success_calls_handle_and_updates_xml(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg1', 'dg2']
        cluster_ctrl = MagicMock()
        cluster_ctrl.mGetCluster.return_value = cluster
        ebox.mGetClusters.return_value = cluster_ctrl

        storage = MagicMock()
        ebox.mGetStorage.return_value = storage

        dg1 = MagicMock()
        dg1.mGetDgName.return_value = 'OTHER'
        dg2 = MagicMock()
        dg2.mGetDgName.return_value = 'TARGET'
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: {'dg1': dg1, 'dg2': dg2}[dgid]

        ebox.mSaveXMLClusterConfiguration = MagicMock()

        with patch.object(manager, 'mHandleDbaasapiSynchronousCall', return_value=0) as mock_handle:
            rc = manager.mDropDiskGroup(options, 'TARGET', aForceDrop='yes')

        self.assertEqual(rc, 0)
        constants = manager.mGetConstantsObj()
        injson = mock_handle.call_args[0][1]
        self.assertEqual(injson[constants._params_key][constants._diskgroupname_key], 'TARGET')
        self.assertEqual(injson[constants._params_key][constants._force_drop_key], 'yes')
        storage.mRemoveDiskGroupConfig.assert_called_once_with('dg2')
        cluster.mRemoveCluDiskGroupConfig.assert_called_once_with('dg2')
        ebox.mSaveXMLClusterConfiguration.assert_called_once()

    # Auto-generated test for mDropDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDropDiskGroup_returns_error_when_handle_fails(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        ebox.mGetClusters.return_value = MagicMock(mGetCluster=MagicMock(return_value=MagicMock()))
        ebox.mGetStorage.return_value = MagicMock()
        ebox.mSaveXMLClusterConfiguration = MagicMock()

        with patch.object(manager, 'mRecordError', return_value=55) as mock_record_error:
            with patch.object(manager, 'mHandleDbaasapiSynchronousCall', return_value=55):
                rc = manager.mDropDiskGroup(options, 'DG_FAIL')

        self.assertEqual(rc, 55)
        mock_record_error.assert_called_once_with(gDiskgroupError['DgOperationError'], mock.ANY)
        ebox.mSaveXMLClusterConfiguration.assert_not_called()

    # Auto-generated test for mUpdateDgrpData
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mUpdateDgrpData_success_populates_sparse_fields(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {constants._sparse_dg_rawname: 'SPRC1'}

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        dbaas_obj.mReadStatusFromDomU.return_value = {}

        def fake_validate(info, dg_name, consts, out_dict):
            out_dict.update({
                'CELL1': {
                    consts._fgrpprop_numdisks: '2',
                    consts._fgrpprop_celldisks: ['FD_00A', 'FD_01B']
                }
            })
            return 0

        manager.mValidateAndGetFailgroupDetails = MagicMock(side_effect=fake_validate)

        def fake_extract(dg, failgroups, cell_map):
            cell_map['CELL1'] = failgroups['CELL1'][constants._fgrpprop_celldisks]
            return 0

        with patch.object(manager, '_extract_cell_vs_griddisks_map', side_effect=fake_extract):
            rc = manager.mUpdateDgrpData(options, diskgroup_data, 'SPRC1', 8192, aDeleteSparse=True)

        self.assertEqual(rc, 0)
        manager.mClusterDgrpInfo2.assert_called_once_with(options, 'SPRC1', [constants._propkey_failgroup])
        self.assertEqual(diskgroup_data['griddisk_count'], 2)
        self.assertEqual(diskgroup_data['cell_count'], 1)
        self.assertEqual(diskgroup_data[constants._celldisk_type], 'flashdisk')
        self.assertAlmostEqual(diskgroup_data['sparse_size'], 819.2)
        self.assertAlmostEqual(diskgroup_data['sparse_slice_size'], 409.6)

    # Auto-generated test for mUpdateDgrpData
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mUpdateDgrpData_missing_args_returns_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)

        with patch.object(manager, 'mRecordError', return_value=66) as mock_record_error:
            rc = manager.mUpdateDgrpData(options, {}, None, None)

        self.assertEqual(rc, 66)
        mock_record_error.assert_called_once_with(gDiskgroupError['MissingArgs'], mock.ANY)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_drop_success_updates_request(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'drop'
        diskgroup_data = {'Status': 'OldStatus'}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        constants = manager.mGetConstantsObj()
        data_dg, reco_dg, sparse_dg = self._mock_cluster_with_sparse(ebox, constants)
        data_dg.mGetDgName.return_value = 'DATAC1'
        reco_dg.mGetDgName.return_value = 'RECOC1'
        sparse_dg.mGetDgName.return_value = 'SPRC1'

        diskgroup_data.update({
            constants._diskgroupname_key: 'SPRC1',
            constants._diskgrouptype_key: 'sparse',
            'datadg_new_size': 2048,
            'recodg_new_size': 1024,
            'sparsedg_new_size': 512,
            constants._sparse_dg_rawname: 'SPRC1'
        })

        self._mock_diskgroup_size(
            manager,
            constants,
            {
                ('DATAC1', False): 1024,
                ('RECOC1', False): 512,
                ('SPRC1', False): 256
            }
        )

        self._stub_cluster_io(manager)
        self._stub_rollback_helpers(manager)

        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        self._stub_parse_input_for_drop(manager, constants)
        manager.mDropDiskGroup = MagicMock(return_value=0)
        manager.mDropGridDisks = MagicMock(return_value=0)
        manager.mCheckIfDgsResizable = MagicMock(return_value=0)
        manager.mResizeDgAndGriddisks = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mValidateDgsPostRebalance = MagicMock(return_value=0)
        manager.mCheckDgExist = MagicMock(return_value=1)

        rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['Status'], 'Pass')
        self.assertEqual(diskgroup_data['Command'], 'dg_drop')
        manager.mDropDiskGroup.assert_called_once_with(options, 'SPRC1')
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_drop_failure_sets_status_and_bails(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'drop'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        constants = manager.mGetConstantsObj()
        data_dg, reco_dg, sparse_dg = self._mock_cluster_with_sparse(ebox, constants)
        data_dg.mGetDgName.return_value = 'DATAC1'
        reco_dg.mGetDgName.return_value = 'RECOC1'
        sparse_dg.mGetDgName.return_value = 'SPRC1'

        diskgroup_data.update({
            constants._diskgroupname_key: 'SPRC1',
            constants._diskgrouptype_key: 'sparse',
            'datadg_new_size': 2048,
            'recodg_new_size': 1024,
            'sparsedg_new_size': 512,
            constants._sparse_dg_rawname: 'SPRC1'
        })

        manager.mCheckDgExist = MagicMock(return_value=1)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        self._stub_parse_input_for_drop(manager, constants)
        self._stub_cluster_io(manager)
        self._stub_rollback_helpers(manager)
        manager.mDropDiskGroup = MagicMock(return_value=5)

        rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 5)
        self.assertEqual(diskgroup_data['Status'], 'Fail')
        dbaas_obj._mUpdateRequestData.assert_not_called()

    # Auto-generated test for mEnsureDgsRebalanced
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mEnsureDgsRebalanced_waits_for_both_diskgroups(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        manager.mSetDiskGroupOperationData({
            constants._data_dg_rawname: 'DG_DATA',
            constants._reco_dg_rawname: 'DG_RECO'
        })

        manager.mWaitUntilDgRebalanced = MagicMock(return_value=0)

        rc = manager.mEnsureDgsRebalanced(options)

        self.assertEqual(rc, 0)
        self.assertEqual(manager.mWaitUntilDgRebalanced.call_count, 2)
        manager.mWaitUntilDgRebalanced.assert_any_call(options, 'DG_DATA', constants)
        manager.mWaitUntilDgRebalanced.assert_any_call(options, 'DG_RECO', constants)

    # Auto-generated test for mWaitUntilDgRebalanced
    @patch('exabox.ovm.cludiskgroups.time.sleep')
    @patch('exabox.ovm.cludiskgroups.exaBoxNode')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mWaitUntilDgRebalanced_returns_success_when_done(self, mock_ebCluDbaas, mock_get_gcontext, mock_exaBoxNode, mock_sleep):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(
            mock_get_gcontext, mock_ebCluDbaas, extra_traces=False
        )

        constants = manager.mGetConstantsObj()
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=0)
        dbaas_obj.mReadStatusFromDomU.return_value = {
            'DG_DATA': {
                constants._propkey_rebstat: {
                    constants._rebstatprop_status: 'DONE'
                }
            }
        }

        node = MagicMock()
        mock_exaBoxNode.return_value = node

        rc = manager.mWaitUntilDgRebalanced(options, 'DG_DATA', constants)

        self.assertEqual(rc, 0)
        manager.mClusterDgrpInfo2.assert_called_once_with(options, 'DG_DATA', [constants._propkey_rebstat])
        manager.mCheckDgPropertyInDbaasOutJson.assert_called_once()
        mock_sleep.assert_not_called()

    # Auto-generated test for mWaitUntilDgRebalanced
    @patch('exabox.ovm.cludiskgroups.time.sleep')
    @patch('exabox.ovm.cludiskgroups.time.time')
    @patch('exabox.ovm.cludiskgroups.exaBoxNode')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mWaitUntilDgRebalanced_triggers_update_on_incomplete(self, mock_ebCluDbaas, mock_get_gcontext, mock_exaBoxNode, mock_time, mock_sleep):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(
            mock_get_gcontext, mock_ebCluDbaas, extra_traces=True
        )

        constants = manager.mGetConstantsObj()
        manager.mClusterDgrpInfo2 = MagicMock(side_effect=[0, 0])
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=0)

        incomplete_status = {
            'DG_DATA': {
                constants._propkey_rebstat: {
                    constants._rebstatprop_status: 'INCOMPLETE'
                }
            }
        }
        done_status = {
            'DG_DATA': {
                constants._propkey_rebstat: {
                    constants._rebstatprop_status: 'DONE'
                }
            }
        }
        dbaas_obj.mReadStatusFromDomU.side_effect = [incomplete_status, done_status]

        cmd_output = MagicMock()
        cmd_output.readlines.return_value = ['1 RUN 5 10 20 10\n']
        node = MagicMock()
        node.mExecuteCmd.return_value = (None, cmd_output, None)
        mock_exaBoxNode.return_value = node

        manager.mUpdateRebalanceStatus = MagicMock(return_value=1600)
        mock_time.side_effect = itertools.chain([1000], itertools.repeat(2000))

        rc = manager.mWaitUntilDgRebalanced(options, 'DG_DATA', constants)

        self.assertEqual(rc, 0)
        manager.mUpdateRebalanceStatus.assert_called_once()
        node.mConnect.assert_called_once_with(aHost='domu1')
        node.mDisconnect.assert_called_once()
        mock_sleep.assert_called_once_with(30)

    # Auto-generated test for mUpdateRebalanceStatus
    @patch('exabox.ovm.cludiskgroups.connect_to_host')
    @patch('exabox.ovm.cludiskgroups.ebCluUtils')
    @patch('exabox.ovm.cludiskgroups.time.time')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mUpdateRebalanceStatus_returns_original_start_when_interval_not_elapsed(
        self, mock_ebCluDbaas, mock_get_gcontext, mock_time, mock_ebCluUtils, mock_connect
    ):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(
            mock_get_gcontext, mock_ebCluDbaas, extra_traces=True
        )

        mock_time.side_effect = [1000, 1050]
        mock_ebCluUtils.return_value = MagicMock()

        returned = manager.mUpdateRebalanceStatus('domu1', 'cmd_run', 'cmd_name {0}', 1000, 300, manager.mGetConstantsObj())

        self.assertEqual(returned, 1000)
        mock_connect.assert_not_called()
        dbaas_obj._mUpdateRequestData.assert_not_called()

    # Auto-generated test for mUpdateRebalanceStatus

    @patch('exabox.ovm.cludiskgroups.connect_to_host')
    @patch('exabox.ovm.cludiskgroups.ebCluUtils')
    @patch('exabox.ovm.cludiskgroups.time.time')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mUpdateRebalanceStatus_updates_rebalance_details(self, mock_ebCluDbaas, mock_get_gcontext,
                                                              mock_time, mock_ebCluUtils, mock_connect):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(
            mock_get_gcontext, mock_ebCluDbaas, extra_traces=True
        )

        constants = manager.mGetConstantsObj()
        mock_time.side_effect = itertools.repeat(1700)

        utils_instance = MagicMock()
        utils_instance.mIsNumber.return_value = True
        mock_ebCluUtils.return_value = utils_instance

        out_state = MagicMock()
        out_state.readlines.return_value = ['1 RUN 5 10 20 40\n']
        node_state = MagicMock()
        node_state.mExecuteCmd.return_value = (None, out_state, None)

        out_name = MagicMock()
        out_name.readlines.return_value = ['DATA some_name\n']
        node_name = MagicMock()
        node_name.mExecuteCmd.return_value = (None, out_name, None)

        ctx_state = MagicMock()
        ctx_state.__enter__.return_value = node_state
        ctx_state.__exit__.return_value = False

        ctx_name = MagicMock()
        ctx_name.__enter__.return_value = node_name
        ctx_name.__exit__.return_value = False

        mock_connect.side_effect = [ctx_state, ctx_name]

        manager.mCalcOverallRebalPercent = MagicMock(return_value=37)

        returned = manager.mUpdateRebalanceStatus('domu1', 'cmd_run', 'cmd_name {0}', 1000, 300, constants)

        self.assertEqual(returned, 1600)
        dbaas_obj._mUpdateRequestData.assert_called_once()
        manager.mCalcOverallRebalPercent.assert_called_once_with(constants)

    # Auto-generated test for mUpdateRebalanceStatus
    @patch('exabox.ovm.cludiskgroups.connect_to_host')
    @patch('exabox.ovm.cludiskgroups.time.time')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mUpdateRebalanceStatus_handles_no_rows_selected(self, mock_ebCluDbaas, mock_get_gcontext,
                                                             mock_time, mock_connect):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(
            mock_get_gcontext, mock_ebCluDbaas, extra_traces=True
        )

        constants = manager.mGetConstantsObj()
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=0)
        manager.mSetLastDomUused('domu1')
        manager.mSetOutJson('/tmp/out.json')

        dbaas_obj.mReadStatusFromDomU.return_value = {
            'DG_DATA': {
                constants._propkey_rebstat: {
                    constants._rebstatprop_status: 'INCOMPLETE'
                }
            }
        }

        stream = MagicMock()
        stream.readlines.return_value = ['no rows selected\n']
        node = MagicMock()
        node.mExecuteCmd.return_value = (None, stream, None)
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        mock_time.side_effect = itertools.repeat(1700)

        returned = manager.mUpdateRebalanceStatus('domu1', 'cmd_run', 'cmd_name {0}', 1000, 300, constants)

        self.assertEqual(returned, 1600)
        dbaas_obj._mUpdateRequestData.assert_called_once()
        payload = dbaas_obj._mUpdateRequestData.call_args[0][1]
        self.assertEqual(payload['stepProgressDetails']['percent_complete'], 0)
        self.assertEqual(payload['stepProgressDetails']['stepSpecificDetails']['diskgroup_rbal_details'], [])
        node.mExecuteCmd.assert_called_once()

    # Auto-generated test for mUpdateRebalanceStatus
    @patch('exabox.ovm.cludiskgroups.connect_to_host')
    @patch('exabox.ovm.cludiskgroups.time.time')
    @patch('exabox.ovm.cludiskgroups.ebCluUtils')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mUpdateRebalanceStatus_returns_updated_start_on_exception(
        self, mock_ebCluDbaas, mock_get_gcontext, mock_ebCluUtils, mock_time, mock_connect
    ):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(
            mock_get_gcontext, mock_ebCluDbaas, extra_traces=True
        )

        constants = manager.mGetConstantsObj()
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=0)

        dbaas_obj.mReadStatusFromDomU.return_value = {
            'DG_DATA': {
                constants._propkey_rebstat: {
                    constants._rebstatprop_status: 'INCOMPLETE'
                }
            }
        }

        utils_instance = MagicMock()
        utils_instance.mIsNumber.return_value = True
        mock_ebCluUtils.return_value = utils_instance

        mock_connect.side_effect = RuntimeError('connection failed')
        mock_time.side_effect = itertools.repeat(1700)

        returned = manager.mUpdateRebalanceStatus('domu1', 'cmd_run', 'cmd_name {0}', 1000, 300, constants)

        self.assertEqual(returned, 1600)
        dbaas_obj._mUpdateRequestData.assert_not_called()

    # Auto-generated test for mUpdateRebalanceStatus
    @patch('exabox.ovm.cludiskgroups.connect_to_host')
    @patch('exabox.ovm.cludiskgroups.ebCluUtils')
    @patch('exabox.ovm.cludiskgroups.time.time')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mUpdateRebalanceStatus_calculates_weighted_average_for_parallel_runs(
        self, mock_ebCluDbaas, mock_get_gcontext, mock_time, mock_ebCluUtils, mock_connect
    ):
        manager, _, dbaas_obj, _ = self._create_manager_with_stubs(
            mock_get_gcontext, mock_ebCluDbaas, extra_traces=True
        )

        constants = manager.mGetConstantsObj()
        manager._dict_groups_percent_avg = {}

        mock_time.side_effect = itertools.repeat(2000)

        utils_instance = MagicMock()
        utils_instance.mIsNumber.side_effect = lambda value: value is not None
        mock_ebCluUtils.return_value = utils_instance

        # First command returns two RUN entries for the same group to verify averaging and max eta logic
        out_state = MagicMock()
        out_state.readlines.return_value = [
            '1 RUN 5 10 30 40\n',
            '1 RUN 5 12 30 40\n',
            '2 RUN 3 15 15 30\n'
        ]

        node_state = MagicMock()
        node_state.mExecuteCmd.return_value = (None, out_state, None)

        # Second command fetches diskgroup names for group numbers 1 and 2
        out_name_group1 = MagicMock()
        out_name_group1.readlines.return_value = ['DATA DG_DATA\n']

        out_name_group2 = MagicMock()
        out_name_group2.readlines.return_value = ['RECO DG_RECO\n']

        node_name_group1 = MagicMock()
        node_name_group1.mExecuteCmd.return_value = (None, out_name_group1, None)

        node_name_group2 = MagicMock()
        node_name_group2.mExecuteCmd.return_value = (None, out_name_group2, None)

        ctx_state = MagicMock()
        ctx_state.__enter__.return_value = node_state
        ctx_state.__exit__.return_value = False

        ctx_name_group1 = MagicMock()
        ctx_name_group1.__enter__.return_value = node_name_group1
        ctx_name_group1.__exit__.return_value = False

        ctx_name_group2 = MagicMock()
        ctx_name_group2.__enter__.return_value = node_name_group2
        ctx_name_group2.__exit__.return_value = False

        mock_connect.side_effect = [ctx_state, ctx_name_group1, ctx_name_group2]

        manager.mCalcOverallRebalPercent = MagicMock(return_value=42)

        returned = manager.mUpdateRebalanceStatus('domu1', 'cmd_run {0}', 'diskgrp {0}', 1000, 300, constants)

        self.assertEqual(returned, 1600)
        dbaas_obj._mUpdateRequestData.assert_called_once()

        payload = dbaas_obj._mUpdateRequestData.call_args[0][1]
        self.assertEqual(payload['stepProgressDetails']['percent_complete'], 42)
        details = payload['stepProgressDetails']['stepSpecificDetails']['diskgroup_rbal_details']

        self.assertEqual(len(details), 2)

        data_entry = next(item for item in details if item['name'] == 'DG_DATA')
        self.assertEqual(data_entry['Rebalance_power'], '5')
        self.assertEqual(data_entry['est_time_remaining'], str(12 * 60))
        self.assertEqual(data_entry['percentage_task_completed'], 75)

        reco_entry = next(item for item in details if item['name'] == 'DG_RECO')
        self.assertEqual(reco_entry['Rebalance_power'], '3')
        self.assertEqual(reco_entry['est_time_remaining'], str(15 * 60))
        self.assertEqual(reco_entry['percentage_task_completed'], 50)

        manager.mCalcOverallRebalPercent.assert_called_once_with(constants)

    # Auto-generated test for mUpdateRebalanceStatus
    @patch('exabox.ovm.cludiskgroups.connect_to_host')
    @patch('exabox.ovm.cludiskgroups.time.time')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mUpdateRebalanceStatus_retains_max_overall_when_no_run_entries(
        self, mock_get_gcontext, mock_ebCluDbaas, mock_time, mock_connect
    ):
        manager, _, dbaas_obj, _ = self._create_manager_with_stubs(
            mock_get_gcontext, mock_ebCluDbaas, extra_traces=True
        )

        constants = manager.mGetConstantsObj()
        manager.mCalcOverallRebalPercent = MagicMock(return_value=55)

        manager._max_overall_percent = 60
        manager._dict_groups_percent_avg = {'DG_DATA': 60}

        mock_time.side_effect = itertools.repeat(2000)

        stream = MagicMock()
        stream.readlines.return_value = []
        node = MagicMock()
        node.mExecuteCmd.return_value = (None, stream, None)
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        # Simulate elapsed interval without any RUN state entries
        manager.mUpdateRebalanceStatus('domu1', 'cmd_run {0}', 'diskgrp {0}', 1000, 300, constants)

        dbaas_obj._mUpdateRequestData.assert_called_once()
        payload = dbaas_obj._mUpdateRequestData.call_args[0][1]
        self.assertEqual(payload['stepProgressDetails']['percent_complete'], 60)
        self.assertEqual(payload['stepProgressDetails']['stepSpecificDetails']['diskgroup_rbal_details'], [])

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

    # Auto-generated test for mValidateAndFilterStorPropDict
    def test_mValidateAndFilterStorPropDict_missing_storage_values(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()
        payload = {
            "DG1": {
                constants._propkey_storage: {}
            }
        }
        container = {}

        with patch.object(manager, 'mRecordError', return_value=123) as mock_record:
            result = manager.mValidateAndFilterStorPropDict(payload, container, "DG1", constants)

        self.assertEqual(result, 123)
        mock_record.assert_called_once_with(gDiskgroupError['MissingStorPropDict'], mock.ANY)

    # Auto-generated test for mValidateAndFilterStorPropDict
    def test_mValidateAndFilterStorPropDict_success_updates_container(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()
        payload = {
            "DG1": {
                constants._propkey_storage: {
                    constants._storprop_totalMb: "1000",
                    constants._storprop_usedMb: "200"
                }
            }
        }
        container = {}

        result = manager.mValidateAndFilterStorPropDict(payload, container, "DG1", constants)

        self.assertEqual(result, 0)
        self.assertEqual(container[constants._storprop_totalMb], "1000")
        self.assertEqual(container[constants._storprop_usedMb], "200")

    # Auto-generated test for mCheckDgPropertyInDbaasOutJson
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCheckDgPropertyInDbaasOutJson_records_error_for_null_payload(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        with patch.object(manager, 'mRecordError', return_value=111) as mock_record:
            rc = manager.mCheckDgPropertyInDbaasOutJson(None, 'DG1', constants._propkey_storage)

        self.assertEqual(rc, 111)
        mock_record.assert_called_once()
        args, _ = mock_record.call_args
        self.assertIn(
            args[0],
            (gDiskgroupError['MissingPropDict'], gDiskgroupError['NullOutputPayload'])
        )

    # Auto-generated test for mCheckDgPropertyInDbaasOutJson
    def test_mCheckDgPropertyInDbaasOutJson_records_error_for_missing_diskgroup(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)

        with patch.object(manager, 'mRecordError', return_value=222) as mock_record:
            rc = manager.mCheckDgPropertyInDbaasOutJson({}, 'DG_MISSING', manager.mGetConstantsObj()._propkey_storage)

        self.assertEqual(rc, 222)
        mock_record.assert_called_once()
        args, _ = mock_record.call_args
        self.assertEqual(args[0], gDiskgroupError['NullOutputPayload'])

    # Auto-generated test for mCheckDgPropertyInDbaasOutJson
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas', autospec=True)
    @patch('exabox.ovm.cludiskgroups.get_gcontext', autospec=True)
    def test_mCheckDgPropertyInDbaasOutJson_records_error_for_missing_property(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        info = {'DG1': {constants._propkey_storage: None}}

        with patch.object(manager, 'mRecordError', return_value=333) as mock_record:
            rc = manager.mCheckDgPropertyInDbaasOutJson(info, 'DG1', constants._propkey_storage)

        self.assertEqual(rc, 333)
        mock_record.assert_called_once()
        args, _ = mock_record.call_args
        self.assertEqual(args[0], gDiskgroupError['MissingStorPropDict'])

    # Auto-generated test for mCheckDgPropertyInDbaasOutJson
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas', autospec=True)
    @patch('exabox.ovm.cludiskgroups.get_gcontext', autospec=True)
    def test_mCheckDgPropertyInDbaasOutJson_success(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        info = {
            'DG1': {
                constants._propkey_storage: {
                    constants._storprop_totalMb: '1000'
                }
            }
        }

        rc = manager.mCheckDgPropertyInDbaasOutJson(info, 'DG1', constants._propkey_storage)

        self.assertEqual(rc, 0)

    # Auto-generated test for mUtilGetDiskgroupSize
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas', autospec=True)
    @patch('exabox.ovm.cludiskgroups.get_gcontext', autospec=True)
    def test_mUtilGetDiskgroupSize_returns_total_mb(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        manager.mSetOutJson('/tmp/out.json')
        manager.mSetLastDomUused('domu1')

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        dbaas_obj.mReadStatusFromDomU.return_value = {
            'DGX': {
                constants._propkey_storage: {
                    constants._storprop_totalMb: '2048'
                }
            }
        }

        rc = manager.mUtilGetDiskgroupSize(options, 'DGX', constants)

        self.assertEqual(rc, 2048)
        manager.mClusterDgrpInfo2.assert_called_once_with(options, 'DGX', [constants._propkey_storage])
        dbaas_obj.mReadStatusFromDomU.assert_called_once()

    # Auto-generated test for mUtilGetDiskgroupSize
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas', autospec=True)
    @patch('exabox.ovm.cludiskgroups.get_gcontext', autospec=True)
    def test_mUtilGetDiskgroupSize_returns_used_mb_when_requested(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        manager.mSetOutJson('/tmp/out.json')
        manager.mSetLastDomUused('domu1')

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        dbaas_obj.mReadStatusFromDomU.return_value = {
            'DGY': {
                constants._propkey_storage: {
                    constants._storprop_usedMb: '512'
                }
            }
        }

        rc = manager.mUtilGetDiskgroupSize(options, 'DGY', constants, aUsedMB=1)

        self.assertEqual(rc, 512)
        manager.mClusterDgrpInfo2.assert_called_once_with(options, 'DGY', [constants._propkey_storage])

    # Auto-generated test for mUtilGetDiskgroupSize
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas', autospec=True)
    @patch('exabox.ovm.cludiskgroups.get_gcontext', autospec=True)
    def test_mUtilGetDiskgroupSize_records_error_when_cluster_info_fails(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        manager.mClusterDgrpInfo2 = MagicMock(return_value=-1)

        with patch.object(manager, 'mRecordError', return_value=444) as mock_record:
            rc = manager.mUtilGetDiskgroupSize(options, 'DGZ', constants)

        self.assertEqual(rc, 444)
        mock_record.assert_called_once()
        args, _ = mock_record.call_args
        self.assertEqual(args[0], gDiskgroupError['ErrorFetchingDetails'])

    # Auto-generated test for mUtilGetDiskgroupSize
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas', autospec=True)
    @patch('exabox.ovm.cludiskgroups.get_gcontext', autospec=True)
    def test_mUtilGetDiskgroupSize_records_error_when_property_missing(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        manager.mSetOutJson('/tmp/out.json')
        manager.mSetLastDomUused('domu1')

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        dbaas_obj.mReadStatusFromDomU.return_value = {
            'DGX': {
                constants._propkey_storage: {}
            }
        }

        with patch.object(manager, 'mRecordError', side_effect=[555, 666]) as mock_record:
            rc = manager.mUtilGetDiskgroupSize(options, 'DGX', constants)

        self.assertEqual(rc, 666)
        self.assertEqual(mock_record.call_count, 2)
        first_args, _ = mock_record.call_args_list[0]
        second_args, _ = mock_record.call_args_list[1]
        self.assertEqual(first_args[0], gDiskgroupError['MissingStorPropDict'])
        self.assertEqual(second_args[0], gDiskgroupError['DbaasApiFail'])

    # Auto-generated test for mUtilGetDiskgroupSize
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mUtilGetDiskgroupSize_records_error_when_property_validation_fails(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        manager.mSetOutJson('/tmp/out.json')
        manager.mSetLastDomUused('domu1')

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=999)

        with patch.object(manager, 'mRecordError', return_value=666) as mock_record:
            rc = manager.mUtilGetDiskgroupSize(options, 'DGW', constants)

        self.assertEqual(rc, 666)
        manager.mCheckDgPropertyInDbaasOutJson.assert_called_once_with(mock.ANY, 'DGW', constants._propkey_storage)
        mock_record.assert_called_once_with(gDiskgroupError['DbaasApiFail'], mock.ANY)

    # Auto-generated test for isDgResized
    def test_isDgResized_allows_one_gb_tolerance(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)

        self.assertEqual(manager.isDgResized(1024, 1024), 1)
        self.assertEqual(manager.isDgResized(2048, 1024), 1)
        self.assertEqual(manager.isDgResized(0, 1024), 1)

    # Auto-generated test for isDgResized
    def test_isDgResized_returns_zero_for_large_difference(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)

        self.assertEqual(manager.isDgResized(4096, 1024), 0)

    # Auto-generated test for mUtilCheckIfDgResizable
    def test_mUtilCheckIfDgResizable_returns_error_for_low_free_space(self):
        ebox = MagicMock()
        ebox.mReturnCellNodes.return_value = {
            "c1": {}, "c2": {}, "c3": {}, "c4": {}
        }
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)

        result = manager.mUtilCheckIfDgResizable(950, 1000)

        self.assertEqual(result, -1)

    # Auto-generated test for mUtilCheckIfDgResizable
    def test_mUtilCheckIfDgResizable_allows_resize_when_threshold_met(self):
        ebox = MagicMock()
        ebox.mReturnCellNodes.return_value = {
            "c1": {}, "c2": {}, "c3": {}, "c4": {}, "c5": {}
        }
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)

        result = manager.mUtilCheckIfDgResizable(100, 1000)

        self.assertEqual(result, 0)

    # Auto-generated test for mCheckIfDgResizable
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mValidateAndFilterStorPropDict')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mClusterDgrpInfo2')
    def test_mCheckIfDgResizable_shrink_failure_returns_error(self, mock_info, mock_validate):
        ebox = MagicMock()
        ebox.mReturnCellNodes.return_value = {
            "c1": {}, "c2": {}, "c3": {}, "c4": {}
        }
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        dbaas = MagicMock()
        manager.mSetDbaasObj(dbaas)
        manager.mSetOutJson({})
        manager.mSetLastDomUused('domu1')
        mock_info.return_value = 0

        def validate(_info, container, _dg, constants):
            container.update({
                constants._storprop_totalMb: "1000",
                constants._storprop_usedMb: "950",
                constants._storprop_osMb: "50"
            })
            return 0

        mock_validate.side_effect = validate
        dbaas.mReadStatusFromDomU.return_value = {'DG1': {}}

        with patch.object(manager, 'mUtilCheckIfDgResizable', return_value=-1):
            with patch.object(manager, 'mRecordError', return_value=99) as mock_record:
                result = manager.mCheckIfDgResizable(options, 'DG1', aNewDgSizeMb=900)

        self.assertEqual(result, 99)
        mock_record.assert_called_once_with(gDiskgroupError['NonModifiable'], mock.ANY)

    # Auto-generated test for mCheckIfDgResizable
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mCheckGriddiskSize', return_value=0)
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mValidateAndFilterStorPropDict')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mClusterDgrpInfo2')
    def test_mCheckIfDgResizable_success_updates_mappings(self, mock_info, mock_validate, mock_check_grid):
        ebox = MagicMock()
        ebox.mReturnCellNodes.return_value = {
            "c1": {}, "c2": {}, "c3": {}, "c4": {}, "c5": {}
        }
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        dbaas = MagicMock()
        manager.mSetDbaasObj(dbaas)
        manager.mSetOutJson({})
        manager.mSetLastDomUused('domu1')
        mock_info.return_value = 0

        def validate(_info, container, _dg, constants):
            container.update({
                constants._storprop_totalMb: "1000",
                constants._storprop_usedMb: "100",
                constants._storprop_osMb: "40"
            })
            return 0

        mock_validate.side_effect = validate
        dbaas.mReadStatusFromDomU.return_value = {'DG2': {}}

        new_sizes = {'dg1': 0}
        diskgroup_data = {'dg1': 'DG2'}
        precheck = {'currentMB': 100, 'newMB': 200, 'osMB': 10, 'growMB': 0, 'shrinkMB': 0}

        result = manager.mCheckIfDgResizable(
            options,
            'DG2',
            aNewDgSizeMb=1500,
            aNewSizesDict=new_sizes,
            aDiskgroupData=diskgroup_data,
            aPrecheckDict=precheck
        )

        self.assertEqual(result, 0)
        self.assertEqual(new_sizes['dg1'], 1500)
        self.assertEqual(precheck['currentMB'], 1100)
        self.assertEqual(precheck['newMB'], 1700)
        self.assertEqual(precheck['osMB'], 50)

    # Auto-generated test for mCheckIfDgResizable
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mCalculateFreeSpaceCelldisk', return_value=1024)
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mCheckGriddiskSize', return_value=8192)
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mValidateAndFilterStorPropDict')
    @patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mClusterDgrpInfo2')
    def test_mCheckIfDgResizable_skip_celldisk_precheck_when_griddisk_resized(self, mock_info, mock_validate, mock_check_grid, mock_calc_free):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        dbaas = MagicMock()
        manager.mSetDbaasObj(dbaas)
        manager.mSetOutJson({})
        manager.mSetLastDomUused('domu2')
        mock_info.return_value = 0

        def populate_storage_props(_info, container, _dg, constants):
            container.update({
                constants._storprop_totalMb: "8192",
                constants._storprop_usedMb: "4096",
                constants._storprop_osMb: "256"
            })
            return 0

        mock_validate.side_effect = populate_storage_props
        dbaas.mReadStatusFromDomU.return_value = {'DG3': {}}

        precheck = {'currentMB': 100, 'newMB': 200, 'osMB': 10, 'growMB': 0, 'shrinkMB': 0}

        result = manager.mCheckIfDgResizable(
            options,
            'DG3',
            aNewDgSizeMb=12288,
            aDiskgroupData={'dg_key': 'DG3'},
            aPrecheckDict=precheck
        )

        self.assertEqual(result, 0)
        self.assertEqual(precheck['currentMB'], 100)
        self.assertEqual(precheck['newMB'], 200)
        self.assertEqual(precheck['osMB'], 10)
        mock_check_grid.assert_called_once_with('DG3', 12288)
        mock_calc_free.assert_not_called()

    # Auto-generated test for mCheckIfDgsResizable
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCheckIfDgsResizable_missing_data_diskgroup_records_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        cluster_ctrl = MagicMock()
        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_reco']
        cluster_ctrl.mGetCluster.return_value = cluster
        ebox.mGetClusters.return_value = cluster_ctrl

        storage = MagicMock()
        ebox.mGetStorage.return_value = storage
        reco_cfg = MagicMock()
        reco_cfg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        reco_cfg.mGetDgName.return_value = 'RECOC1'
        storage.mGetDiskGroupConfig.side_effect = lambda dg: {'dg_reco': reco_cfg}[dg]

        current_sizes = {
            constants._data_dg_rawname: 8192,
            constants._reco_dg_rawname: 4096
        }
        new_sizes = {}
        diskgroup_data = {
            'datadg_new_size': 5000,
            'recodg_new_size': 2500,
            'sparsedg_new_size': 1200
        }

        with patch.object(manager, 'mRecordError', return_value=55) as mock_record:
            rc = manager.mCheckIfDgsResizable(options, current_sizes, new_sizes, diskgroup_data)

        self.assertEqual(rc, 55)
        mock_record.assert_called_once_with(gDiskgroupError['DgDoesNotExist'], constants._data_dg_prefix)
        self.assertEqual(new_sizes, {})

    # Auto-generated test for mCheckIfDgsResizable
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCheckIfDgsResizable_missing_reco_diskgroup_records_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        cluster_ctrl = MagicMock()
        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_data']
        cluster_ctrl.mGetCluster.return_value = cluster
        ebox.mGetClusters.return_value = cluster_ctrl

        storage = MagicMock()
        ebox.mGetStorage.return_value = storage
        data_cfg = MagicMock()
        data_cfg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_cfg.mGetDgName.return_value = 'DATAC1'
        storage.mGetDiskGroupConfig.side_effect = lambda dg: {'dg_data': data_cfg}[dg]

        current_sizes = {
            constants._data_dg_rawname: 8192,
            constants._reco_dg_rawname: 4096
        }
        new_sizes = {}
        diskgroup_data = {
            'datadg_new_size': 4800,
            'recodg_new_size': 2400,
            'sparsedg_new_size': 1000
        }

        with patch.object(manager, 'mRecordError', return_value=66) as mock_record:
            rc = manager.mCheckIfDgsResizable(options, current_sizes, new_sizes, diskgroup_data)

        self.assertEqual(rc, 66)
        mock_record.assert_called_once_with(gDiskgroupError['DgDoesNotExist'], constants._reco_dg_prefix)
        self.assertEqual(new_sizes, {})

    # Auto-generated test for mCheckIfDgsResizable
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCheckIfDgsResizable_data_resize_failure_propagates_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._setup_sparse_cluster(manager, ebox, constants, dg_name='SPRC1')

        current_sizes = {
            constants._data_dg_rawname: 12288,
            constants._reco_dg_rawname: 8192
        }
        new_sizes = {}
        diskgroup_data = {
            'datadg_new_size': 5000,
            'recodg_new_size': 2500,
            'sparsedg_new_size': 1200
        }

        manager.mCheckIfDgResizable = MagicMock(side_effect=[77])

        rc = manager.mCheckIfDgsResizable(options, current_sizes, new_sizes, diskgroup_data)

        self.assertEqual(rc, 77)
        self.assertEqual(manager.mCheckIfDgResizable.call_count, 1)
        self.assertEqual(new_sizes, {})

    # Auto-generated test for mCheckIfDgsResizable
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCheckIfDgsResizable_reco_resize_failure_propagates_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._setup_sparse_cluster(manager, ebox, constants, dg_name='SPRC1')

        current_sizes = {
            constants._data_dg_rawname: 14336,
            constants._reco_dg_rawname: 9216
        }
        new_sizes = {}
        diskgroup_data = {
            'datadg_new_size': 6400,
            'recodg_new_size': 3200,
            'sparsedg_new_size': 1600
        }

        manager.mCheckIfDgResizable = MagicMock(side_effect=[0, 88])

        rc = manager.mCheckIfDgsResizable(options, current_sizes, new_sizes, diskgroup_data)

        self.assertEqual(rc, 88)
        self.assertEqual(manager.mCheckIfDgResizable.call_count, 2)
        self.assertEqual(new_sizes, {})

    # Auto-generated test for mCheckIfDgsResizable
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCheckIfDgsResizable_success_updates_new_sizes_and_sparse_metadata(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._setup_sparse_cluster(manager, ebox, constants, dg_name='SPRC1')

        current_sizes = {
            constants._data_dg_rawname: 16384,
            constants._reco_dg_rawname: 12288
        }
        new_sizes = {}
        diskgroup_data = {
            'datadg_new_size': 4100,
            'recodg_new_size': 2150,
            'sparsedg_new_size': 1035
        }

        manager.mCheckIfDgResizable = MagicMock(side_effect=[0, 0])

        rc = manager.mCheckIfDgsResizable(options, current_sizes, new_sizes, diskgroup_data)

        self.assertEqual(rc, 0)
        self.assertEqual(new_sizes[constants._data_dg_rawname], 4096)
        self.assertEqual(new_sizes[constants._reco_dg_rawname], 2144)
        self.assertEqual(new_sizes[constants._sparse_dg_rawname], 1024)
        self.assertEqual(diskgroup_data['sparse_size'], 1024)
        self.assertEqual(diskgroup_data[constants._sparse_dg_rawname], 'SPRC1')
        self.assertEqual(manager.mCheckIfDgResizable.call_count, 2)

    # Auto-generated test for mCheckIfDgsResizable
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCheckIfDgsResizable_delete_sparse_skips_sparse_size(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._setup_sparse_cluster(manager, ebox, constants, dg_name='SPRC1')

        current_sizes = {
            constants._data_dg_rawname: 20480,
            constants._reco_dg_rawname: 15360
        }
        new_sizes = {}
        diskgroup_data = {
            'datadg_new_size': 3210,
            'recodg_new_size': 1618,
            'sparsedg_new_size': 777
        }

        manager.mCheckIfDgResizable = MagicMock(side_effect=[0, 0])

        rc = manager.mCheckIfDgsResizable(options, current_sizes, new_sizes, diskgroup_data, aDeleteSparse=True)

        self.assertEqual(rc, 0)
        self.assertEqual(new_sizes[constants._data_dg_rawname], 3200)
        self.assertEqual(new_sizes[constants._reco_dg_rawname], 1616)
        self.assertNotIn(constants._sparse_dg_rawname, new_sizes)
        self.assertNotIn('sparse_size', diskgroup_data)
        self.assertEqual(diskgroup_data[constants._sparse_dg_rawname], 'SPRC1')
        self.assertEqual(manager.mCheckIfDgResizable.call_count, 2)

    # Auto-generated test for mCheckIfSizeChangePermitted
    def test_mCheckIfSizeChangePermitted_small_delta_triggers_error(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        dg_map = {
            'entry1': {'DG_NAME': 'DG_DATA', 'DG_NEWSIZE': '100'}
        }

        manager.mUtilGetDiskgroupSize = MagicMock(return_value=102400)

        with patch.object(manager, 'mRecordError', return_value=77) as mock_record:
            result = manager.mCheckIfSizeChangePermitted(options, dg_map)

        self.assertEqual(result, 77)
        mock_record.assert_called_once_with(
            gDiskgroupError['DgSizeChangeNotPermitted'],
            'Disk Groups Size Change Not Permitted'
        )

    # Auto-generated test for mCheckIfSizeChangePermitted
    def test_mCheckIfSizeChangePermitted_allows_resize_for_large_diff(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        dg_map = {
            'entry1': {'DG_NAME': 'DG_DATA', 'DG_NEWSIZE': '300'},
            'entry2': {'DG_NAME': None, 'DG_NEWSIZE': '0'}
        }

        manager.mUtilGetDiskgroupSize = MagicMock(return_value=102400)

        with patch.object(manager, 'mRecordError', side_effect=AssertionError('should not be called')):
            result = manager.mCheckIfSizeChangePermitted(options, dg_map)

        self.assertEqual(result, 0)

    # Auto-generated test for mUtilGetDiskgroupSize
    def test_mUtilGetDiskgroupSize_returns_error_when_info_fetch_fails(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        manager.mSetDbaasObj(MagicMock())

        manager.mClusterDgrpInfo2 = MagicMock(return_value=1)

        with patch.object(manager, 'mRecordError', return_value=55) as mock_record:
            result = manager.mUtilGetDiskgroupSize(options, 'DG_DATA', manager.mGetConstantsObj())

        self.assertEqual(result, 55)
        mock_record.assert_called_once()
        self.assertEqual(mock_record.call_args[0][0], gDiskgroupError['ErrorFetchingDetails'])
        message = mock_record.call_args[0][1]
        self.assertTrue(message.strip().startswith('*** Could not fetch'))
        self.assertIn('diskgroup DG_DATA', message)

    # Auto-generated test for mUtilGetDiskgroupSize
    def test_mUtilGetDiskgroupSize_returns_total_size_when_available(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()
        dbaas = MagicMock()
        manager.mSetDbaasObj(dbaas)
        manager.mSetOutJson({})
        manager.mSetLastDomUused('domu1')

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=0)
        dbaas.mReadStatusFromDomU.return_value = {
            'DG_DATA': {
                constants._propkey_storage: {
                    constants._storprop_totalMb: '2048'
                }
            }
        }

        result = manager.mUtilGetDiskgroupSize(options, 'DG_DATA', constants)

        self.assertEqual(result, 2048)
        manager.mClusterDgrpInfo2.assert_called_once_with(options, 'DG_DATA', [constants._propkey_storage])
        dbaas.mReadStatusFromDomU.assert_called_once()

    # Auto-generated test for mUtilGetDiskgroupSize
    def test_mUtilGetDiskgroupSize_uses_used_mb_when_requested(self):
        ebox = MagicMock()
        options = MagicMock()
        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()
        dbaas = MagicMock()
        manager.mSetDbaasObj(dbaas)
        manager.mSetOutJson({})
        manager.mSetLastDomUused('domu2')

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=0)
        dbaas.mReadStatusFromDomU.return_value = {
            'DG_DATA': {
                constants._propkey_storage: {
                    constants._storprop_usedMb: '512'
                }
            }
        }

        result = manager.mUtilGetDiskgroupSize(options, 'DG_DATA', constants, aUsedMB=1)

        self.assertEqual(result, 512)
        manager.mClusterDgrpInfo2.assert_called_once_with(options, 'DG_DATA', [constants._propkey_storage])

    # Auto-generated test for mCalculateNewDgSizes
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalculateNewDgSizes_sparse_infers_ratio_and_totals(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {'Command': 'dg_update_add_sparse'}
        current_sizes = {
            constants._data_dg_rawname: 4000,
            constants._reco_dg_rawname: 5000,
            constants._redundancy_factor: 2
        }

        manager.mSetDiskGroupOperationData(diskgroup_data)
        manager._ebCluManageDiskgroup__shrink_existing_dgs = True

        options.jsonconf = {}

        def fake_parse(_options, inparams, opdata):
            return 0

        manager.mSetDiskGroupOperationData(diskgroup_data)

        def fake_calc_total(opdata, sizes_dict, ratio):
            opdata['_total_storage_size'] = 10
            return 0

        def fake_validate(opdata, ratio, sparse):
            opdata['ratio_split'] = ['35', '50', '15']
            return 0

        with patch.object(manager, 'mClusterParseInput', side_effect=fake_parse), \
             patch.object(manager, 'mCalcCurrentDgRatio', return_value=0), \
             patch.object(manager, 'mCalcTotalStorageForUpdate', side_effect=fake_calc_total), \
             patch.object(manager, 'mValidateNewDgRatio', side_effect=fake_validate):
            rc = manager.mCalculateNewDgSizes(options, diskgroup_data, current_sizes, True)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data[constants._shrink_key], True)
        self.assertEqual(diskgroup_data['datadg_new_pct'], 35)
        self.assertEqual(diskgroup_data['recodg_new_pct'], 50)
        self.assertEqual(diskgroup_data['sparsedg_new_pct'], 15)
        self.assertEqual(diskgroup_data['ratio_split'], ['35', '50', '15'])
        self.assertEqual(diskgroup_data['datadg_new_size'], 7168.0)
        self.assertEqual(diskgroup_data['recodg_new_size'], 10240.0)
        self.assertEqual(diskgroup_data['sparsedg_new_size'], 3072.0)
        self.assertEqual(diskgroup_data['_total_storage_size'], 10)

    # Auto-generated test for mCalculateNewDgSizes
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalculateNewDgSizes_non_sparse_defaults_to_backup_ratio(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {'Command': 'dg_resize'}
        current_sizes = {
            constants._data_dg_rawname: 3000,
            constants._reco_dg_rawname: 5000,
            constants._redundancy_factor: 2
        }

        manager.mSetDiskGroupOperationData(diskgroup_data)
        manager._ebCluManageDiskgroup__shrink_existing_dgs = False

        options.jsonconf = {}

        def fake_parse(_options, inparams, opdata):
            return 0

        def fake_calc_ratio(opdata, data_size, reco_size):
            opdata['curr_dg_ratio'] = '40:60'
            return 0

        def fake_calc_total(opdata, sizes_dict, ratio):
            opdata['_total_storage_size'] = 5
            return 0

        def fake_validate(opdata, ratio, sparse):
            opdata['ratio_split'] = ['40', '60']
            return 0

        with patch.object(manager, 'mClusterParseInput', side_effect=fake_parse), \
             patch.object(manager, 'mCalcCurrentDgRatio', side_effect=fake_calc_ratio), \
             patch.object(manager, 'mCalcTotalStorageForUpdate', side_effect=fake_calc_total), \
             patch.object(manager, 'mValidateNewDgRatio', side_effect=fake_validate):
            rc = manager.mCalculateNewDgSizes(options, diskgroup_data, current_sizes, False)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['datadg_new_pct'], 40)
        self.assertEqual(diskgroup_data['recodg_new_pct'], 60)
        self.assertEqual(diskgroup_data['datadg_new_size'], current_sizes[constants._data_dg_rawname])
        self.assertEqual(diskgroup_data['recodg_new_size'], current_sizes[constants._reco_dg_rawname])
        self.assertEqual(diskgroup_data['_total_storage_size'], 5)
        self.assertNotIn('sparsedg_new_pct', diskgroup_data)

    # Auto-generated test for mCalculateNewDgSizes
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalculateNewDgSizes_non_sparse_defaults_to_non_backup_ratio(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {'Command': 'dg_resize'}
        current_sizes = {
            constants._data_dg_rawname: 5000,
            constants._reco_dg_rawname: 2000,
            constants._redundancy_factor: 2
        }

        manager.mSetDiskGroupOperationData(diskgroup_data)
        manager._ebCluManageDiskgroup__shrink_existing_dgs = True

        options.jsonconf = {}

        def fake_parse(_options, inparams, opdata):
            return 0

        def fake_calc_total(opdata, sizes_dict, ratio):
            opdata['_total_storage_size'] = 5
            return 0

        def fake_validate(opdata, ratio, sparse):
            opdata['ratio_split'] = ['80', '20']
            return 0

        with patch.object(manager, 'mClusterParseInput', side_effect=fake_parse), \
             patch.object(manager, 'mCalcTotalStorageForUpdate', side_effect=fake_calc_total), \
             patch.object(manager, 'mValidateNewDgRatio', side_effect=fake_validate):
            rc = manager.mCalculateNewDgSizes(options, diskgroup_data, current_sizes, False)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['datadg_new_pct'], 80)
        self.assertEqual(diskgroup_data['recodg_new_pct'], 20)
        self.assertEqual(diskgroup_data['datadg_new_size'], 8192.0)
        self.assertEqual(diskgroup_data['recodg_new_size'], 2048.0)
        self.assertEqual(diskgroup_data['_total_storage_size'], 5)

    # Auto-generated test for mCalculateNewDgSizes
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalculateNewDgSizes_sparse_respects_explicit_backup_true(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {'Command': 'dg_update_add_sparse'}
        current_sizes = {
            constants._data_dg_rawname: 3200,
            constants._reco_dg_rawname: 6400,
            constants._redundancy_factor: 2
        }

        manager.mSetDiskGroupOperationData(diskgroup_data)
        manager._ebCluManageDiskgroup__shrink_existing_dgs = True
        options.jsonconf = {}

        def fake_parse(_options, inparams, opdata):
            inparams[constants._disk_backup_key] = True
            return 0

        def fake_calc_total(opdata, sizes_dict, ratio):
            opdata['_total_storage_size'] = 10
            return 0

        def fake_validate(opdata, ratio, sparse):
            opdata['ratio_split'] = ['35', '50', '15']
            return 0

        with patch.object(manager, 'mClusterParseInput', side_effect=fake_parse), \
             patch.object(manager, 'mCalcTotalStorageForUpdate', side_effect=fake_calc_total), \
             patch.object(manager, 'mValidateNewDgRatio', side_effect=fake_validate):
            rc = manager.mCalculateNewDgSizes(options, diskgroup_data, current_sizes, True)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['datadg_new_pct'], 35)
        self.assertEqual(diskgroup_data['recodg_new_pct'], 50)
        self.assertEqual(diskgroup_data['sparsedg_new_pct'], 15)
        self.assertEqual(diskgroup_data['datadg_new_size'], 7168.0)
        self.assertEqual(diskgroup_data['recodg_new_size'], 10240.0)
        self.assertEqual(diskgroup_data['sparsedg_new_size'], 3072.0)

    # Auto-generated test for mCalculateNewDgSizes
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalculateNewDgSizes_non_sparse_explicit_backup_true(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {'Command': 'dg_resize'}
        current_sizes = {
            constants._data_dg_rawname: 3000,
            constants._reco_dg_rawname: 4500,
            constants._redundancy_factor: 2
        }

        manager.mSetDiskGroupOperationData(diskgroup_data)
        manager._ebCluManageDiskgroup__shrink_existing_dgs = False
        options.jsonconf = {}

        def fake_parse(_options, inparams, opdata):
            inparams[constants._disk_backup_key] = True
            return 0

        def fake_calc_ratio(opdata, data_size, reco_size):
            opdata['curr_dg_ratio'] = '40:60'
            return 0

        def fake_calc_total(opdata, sizes_dict, ratio):
            opdata['_total_storage_size'] = 5
            return 0

        def fake_validate(opdata, ratio, sparse):
            opdata['ratio_split'] = ['40', '60']
            return 0

        with patch.object(manager, 'mClusterParseInput', side_effect=fake_parse), \
             patch.object(manager, 'mCalcCurrentDgRatio', side_effect=fake_calc_ratio) as mock_calc_ratio, \
             patch.object(manager, 'mCalcTotalStorageForUpdate', side_effect=fake_calc_total) as mock_calc_total, \
             patch.object(manager, 'mValidateNewDgRatio', side_effect=fake_validate):
            rc = manager.mCalculateNewDgSizes(options, diskgroup_data, current_sizes, False)

        self.assertEqual(rc, 0)
        mock_calc_ratio.assert_called_once_with(diskgroup_data, current_sizes[constants._data_dg_rawname], current_sizes[constants._reco_dg_rawname])
        mock_calc_total.assert_called_once_with(diskgroup_data, current_sizes, '40:60')
        self.assertEqual(diskgroup_data['datadg_new_pct'], 40)
        self.assertEqual(diskgroup_data['recodg_new_pct'], 60)
        self.assertEqual(diskgroup_data['datadg_new_size'], current_sizes[constants._data_dg_rawname])
        self.assertEqual(diskgroup_data['recodg_new_size'], current_sizes[constants._reco_dg_rawname])

    # Auto-generated test for mCalculateNewDgSizes
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalculateNewDgSizes_non_sparse_explicit_backup_false(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {'Command': 'dg_resize'}
        current_sizes = {
            constants._data_dg_rawname: 5600,
            constants._reco_dg_rawname: 2800,
            constants._redundancy_factor: 2
        }

        manager.mSetDiskGroupOperationData(diskgroup_data)
        manager._ebCluManageDiskgroup__shrink_existing_dgs = False
        options.jsonconf = {}

        def fake_parse(_options, inparams, opdata):
            inparams[constants._disk_backup_key] = False
            return 0

        def fake_calc_ratio(opdata, data_size, reco_size):
            opdata['curr_dg_ratio'] = '80:20'
            return 0

        def fake_calc_total(opdata, sizes_dict, ratio):
            opdata['_total_storage_size'] = 7
            return 0

        def fake_validate(opdata, ratio, sparse):
            opdata['ratio_split'] = ['80', '20']
            return 0

        with patch.object(manager, 'mClusterParseInput', side_effect=fake_parse), \
             patch.object(manager, 'mCalcCurrentDgRatio', side_effect=fake_calc_ratio) as mock_calc_ratio, \
             patch.object(manager, 'mCalcTotalStorageForUpdate', side_effect=fake_calc_total) as mock_calc_total, \
             patch.object(manager, 'mValidateNewDgRatio', side_effect=fake_validate):
            rc = manager.mCalculateNewDgSizes(options, diskgroup_data, current_sizes, False)

        self.assertEqual(rc, 0)
        mock_calc_ratio.assert_called_once_with(diskgroup_data, current_sizes[constants._data_dg_rawname], current_sizes[constants._reco_dg_rawname])
        mock_calc_total.assert_called_once_with(diskgroup_data, current_sizes, '80:20')
        self.assertEqual(diskgroup_data['datadg_new_pct'], 80)
        self.assertEqual(diskgroup_data['recodg_new_pct'], 20)
        self.assertEqual(diskgroup_data['datadg_new_size'], current_sizes[constants._data_dg_rawname])
        self.assertEqual(diskgroup_data['recodg_new_size'], current_sizes[constants._reco_dg_rawname])

    # Auto-generated test for mCalcTotalStorageForUpdate
    def test_mCalcTotalStorageForUpdate_sets_total_storage_size(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"
        options.jsonconf = {}

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()

        diskgroup_data = {}
        current_sizes = {
            constants._data_dg_rawname: 6144,
            constants._reco_dg_rawname: 2048
        }

        rc = manager.mCalcTotalStorageForUpdate(diskgroup_data, current_sizes, '60:20:20')

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['_total_storage_size'], 10)

    # Auto-generated test for mValidateNewDgRatio
    @patch('exabox.ovm.clustorage.mParseStorageDistrib', return_value=(60, 20, 20))
    def test_mValidateNewDgRatio_records_ratio_split(self, _mock_parse):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"
        options.jsonconf = {}

        manager = ebCluManageDiskgroup(ebox, options)

        diskgroup_data = {}
        rc = manager.mValidateNewDgRatio(diskgroup_data, '60:20:20', True)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['ratio_split'], ['60', '20', '20'])

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_shrink_false_skips_resize_paths(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}
        rollback_stack = []

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=rollback_stack)
        manager.mGetEbox = MagicMock(return_value=ebox)

        data_dg, reco_dg, _ = self._setup_sparse_cluster(manager, ebox, constants)
        data_dg.mGetDgName.return_value = 'DATAC1'
        reco_dg.mGetDgName.return_value = 'RECOC1'

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            req_params[constants._rebalancepower_key] = '6'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)

        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[8128, 2048])

        def populate_new_sizes(options, current_sizes, new_sizes, dg_data, delete_sparse=False):
            new_sizes[constants._data_dg_rawname] = 2048
            new_sizes[constants._reco_dg_rawname] = 1024
            dg_data[constants._sparse_dg_rawname] = 'SPRC1'
            return 0

        manager.mCheckIfDgsResizable = MagicMock(side_effect=populate_new_sizes)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        manager.mResizeDgAndGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mRollback = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aShrinkExistingDgs=False)

        self.assertEqual(rc, 0)
        manager.mCheckIfDgsResizable.assert_called_once()
        #manager.mResizeDgAndGriddisks.assert_not_called()
        manager.mCreateSparseGriddisks.assert_called_once_with(options, diskgroup_data)
        manager.mCreateSparseDg.assert_called_once()
        manager.mEnsureDgsRebalanced.assert_called_once()
        manager.mRollback.assert_not_called()
        self.assertIn(constants._sparse_dg_rawname, diskgroup_data)
        self.assertEqual(diskgroup_data[constants._sparse_dg_rawname], 'SPRC1')

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_populates_expected_request_params(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()

        options.jsonconf = {
            constants._diskgrouptype_key: 'sparse',
            constants._diskgroupname_key: 'DG_DATA',
            constants._rebalancepower_key: 5,
            constants._newsizeGB_key: 12,
            constants._diskgroup_ratios_key: '60:20:20',
            constants._disk_backup_key: 'true',
            constants._total_storagegb_key: 42
        }
        manager.mSetDiskGroupOperationData({'Command': 'dg_resize'})

        req_params = {}

        with patch.object(manager, 'mRecordError', side_effect=AssertionError('unexpected error logging')):
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 0)
        self.assertEqual(req_params[constants._diskgrouptype_key], 'sparse')
        self.assertEqual(req_params[constants._diskgroupname_key], 'DG_DATA')
        self.assertEqual(req_params[constants._rebalancepower_key], 5)
        self.assertEqual(req_params[constants._newsizeGB_key], 12)
        self.assertEqual(req_params[constants._diskgroup_ratios_key], '60:20:20')
        self.assertTrue(req_params[constants._disk_backup_key])
        self.assertEqual(req_params[constants._total_storagegb_key], 42)

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_returns_error_when_missing_new_size(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()

        options.jsonconf = {
            constants._diskgrouptype_key: 'sparse',
            constants._diskgroupname_key: 'DG_DATA'
        }
        manager.mSetDiskGroupOperationData({'Command': 'dg_resize'})

        req_params = {}

        with patch.object(manager, 'mRecordError', return_value=321) as mock_record:
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 321)
        mock_record.assert_called_once()
        self.assertEqual(mock_record.call_args[0][0], gDiskgroupError['MissingDiskgroupSize'])

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_returns_error_when_payload_missing(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        manager.mSetDiskGroupOperationData({'Command': 'dg_resize'})
        options.jsonconf = {}

        req_params = {}

        with patch.object(manager, 'mRecordError', return_value=987) as mock_record:
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 987)
        mock_record.assert_called_once_with(gDiskgroupError['MissingInputPayload'])

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_create_missing_type_returns_error(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()
        manager.mSetDiskGroupOperationData({'Command': 'dg_create'})

        options.jsonconf = {
            constants._diskgroupname_key: 'DG_DATA'
        }
        req_params = {}

        with patch.object(manager, 'mRecordError', return_value=432) as mock_record:
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 432)
        mock_record.assert_called_once_with(gDiskgroupError['MissingDiskgroupType'])

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_drop_sparse_populates_name_from_config(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()

        sparse_config = MagicMock()
        sparse_config.mGetDiskGroupType.return_value = constants._sparse_dg_type_str
        sparse_config.mGetDgName.return_value = 'SPRDG'

        data_config = MagicMock()
        data_config.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_config.mGetDgName.return_value = 'DATADG'

        storage = MagicMock()
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: data_config if dgid == 'cluster_datadg_1' else sparse_config

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['cluster_datadg_1', 'cluster_sparsedg_1']

        clusters = MagicMock()
        clusters.mGetCluster.return_value = cluster

        ebox.mGetStorage.return_value = storage
        ebox.mGetClusters.return_value = clusters

        options.jsonconf = {
            constants._diskgrouptype_key: 'sparse',
            constants._diskgroupname_key: ''
        }
        manager.mSetDiskGroupOperationData({'Command': 'dg_drop'})

        req_params = {}

        with patch.object(manager, 'mRecordError', side_effect=AssertionError('unexpected error')):
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 0)
        self.assertEqual(options.jsonconf[constants._diskgroupname_key], 'SPRDG')
        self.assertEqual(req_params[constants._diskgroupname_key], 'SPRDG')

    # Auto-generated test for mClusterParseInput
    @patch('exabox.ovm.cludiskgroups.copy.deepcopy')
    def test_mClusterParseInput_drop_sparse_clones_from_data_when_sparse_missing(self, mock_deepcopy):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()

        manager.mSetDiskGroupOperationData({'Command': 'dg_drop'})

        storage = MagicMock()
        data_config = MagicMock()
        storage.mGetDiskGroupConfig.return_value = data_config
        ebox.mGetStorage.return_value = storage

        sparse_clone = MagicMock()
        sparse_clone.mGetDgName.side_effect = ['DATADG', 'SPRDG']
        mock_deepcopy.return_value = sparse_clone

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['cluster_datadg_1', 'cluster_other_1']
        clusters = MagicMock()
        clusters.mGetCluster.return_value = cluster
        ebox.mGetClusters.return_value = clusters

        options.jsonconf = {
            constants._diskgrouptype_key: 'sparse',
            constants._diskgroupname_key: ''
        }

        req_params = {}

        with patch.object(manager, 'mRecordError', side_effect=AssertionError('unexpected error')):
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 0)
        mock_deepcopy.assert_called_once_with(data_config)
        sparse_clone.mReplaceDgId.assert_called_once_with('cluster_sparsedg_1')
        sparse_clone.mReplaceDgName.assert_called_once_with('SPRDG')
        self.assertEqual(options.jsonconf[constants._diskgroupname_key], 'SPRDG')
        self.assertEqual(req_params[constants._diskgroupname_key], 'SPRDG')

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_drop_sparse_without_matching_diskgroup_errors(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()

        manager.mSetDiskGroupOperationData({'Command': 'dg_drop'})

        storage = MagicMock()
        ebox.mGetStorage.return_value = storage

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = []
        clusters = MagicMock()
        clusters.mGetCluster.return_value = cluster
        ebox.mGetClusters.return_value = clusters

        options.jsonconf = {
            constants._diskgrouptype_key: 'sparse'
        }

        req_params = {}

        with patch.object(manager, 'mRecordError', return_value=444) as mock_record:
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 444)
        mock_record.assert_called_once_with(gDiskgroupError['DgDoesNotExist'])

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_precheck_requires_optype(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()
        manager.mSetDiskGroupOperationData({'Command': 'dg_precheck'})

        options.jsonconf = {
            constants._diskgroupname_key: 'DG_DATA'
        }
        req_params = {}

        with patch.object(manager, 'mRecordError', return_value=654) as mock_record:
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 654)
        mock_record.assert_called_once_with(gDiskgroupError['MissingArgs'])

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_precheck_sets_diskgroup_type_sparse(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()

        manager.mSetDiskGroupOperationData({'Command': 'dg_precheck'})

        options.jsonconf = {
            constants._optype_key: 'ENABLE_SPARSE'
        }

        req_params = {}

        with patch.object(manager, 'mRecordError', side_effect=AssertionError('unexpected error')):
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 0)
        self.assertEqual(options.jsonconf[constants._diskgrouptype_key], 'sparse')
        self.assertEqual(req_params[constants._diskgrouptype_key], 'sparse')

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_requires_diskgroup_name_for_non_sparse(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        constants = manager.mGetConstantsObj()

        manager.mSetDiskGroupOperationData({'Command': 'dg_resize'})

        options.jsonconf = {
            constants._diskgrouptype_key: 'data',
            constants._newsizeGB_key: 24
        }
        req_params = {}

        with patch.object(manager, 'mRecordError', return_value=777) as mock_record:
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 777)
        mock_record.assert_called_once_with(gDiskgroupError['MissingDiskgroupName'])

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_update_add_sparse_needs_type(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        manager.mSetDiskGroupOperationData({'Command': 'dg_update_add_sparse'})
        constants = manager.mGetConstantsObj()

        options.jsonconf = {
            constants._diskgroupname_key: 'DG_DATA'
        }

        req_params = {}

        with patch.object(manager, 'mRecordError', return_value=555) as mock_record:
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 555)
        mock_record.assert_called_once_with(gDiskgroupError['MissingDiskgroupType'])

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_drop_requires_name_for_non_sparse(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        manager.mSetDiskGroupOperationData({'Command': 'dg_drop'})
        constants = manager.mGetConstantsObj()

        options.jsonconf = {
            constants._diskgrouptype_key: 'data'
        }

        req_params = {}

        with patch.object(manager, 'mRecordError', return_value=654) as mock_record:
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 654)
        mock_record.assert_called_once_with(gDiskgroupError['MissingDiskgroupName'])

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_update_add_sparse_with_type_succeeds(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        manager.mSetDiskGroupOperationData({'Command': 'dg_update_add_sparse'})
        constants = manager.mGetConstantsObj()

        options.jsonconf = {
            constants._diskgrouptype_key: 'sparse',
            constants._diskgroupname_key: 'DG_SPARSE'
        }

        req_params = {}

        with patch.object(manager, 'mRecordError', side_effect=AssertionError('unexpected error during validation')):
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 0)
        self.assertEqual(req_params[constants._diskgrouptype_key], 'sparse')
        self.assertEqual(req_params[constants._diskgroupname_key], 'DG_SPARSE')

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_drop_non_sparse_with_name_passes(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        manager.mSetDiskGroupOperationData({'Command': 'dg_drop'})
        constants = manager.mGetConstantsObj()

        options.jsonconf = {
            constants._diskgrouptype_key: 'data',
            constants._diskgroupname_key: 'DG_DATA'
        }

        req_params = {}

        with patch.object(manager, 'mRecordError', side_effect=AssertionError('unexpected error during drop validation')):
            rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 0)
        self.assertEqual(req_params[constants._diskgrouptype_key], 'data')
        self.assertEqual(req_params[constants._diskgroupname_key], 'DG_DATA')

    # Auto-generated test for mClusterParseInput
    def test_mClusterParseInput_drop_missing_name_for_non_sparse_errors(self):
        ebox = MagicMock()
        ebox.mGetClusterPath.return_value = "/u01"
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetVerbose.return_value = False

        options = MagicMock()
        options.configpath = "/tmp"

        manager = ebCluManageDiskgroup(ebox, options)
        manager.mSetDiskGroupOperationData({'Command': 'dg_drop'})
        constants = manager.mGetConstantsObj()

        options.jsonconf = {
            constants._diskgrouptype_key: 'data'
        }

        with patch.object(manager, 'mRecordError', return_value=901) as mock_record:
            rc = manager.mClusterParseInput(options, {})

        self.assertEqual(901, rc)
        mock_record.assert_called_once_with(gDiskgroupError['MissingDiskgroupName'])

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_invalid_option_records_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = None
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)

        with patch.object(manager, 'mRecordError', return_value=111) as mock_record:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 111)
        self.assertEqual(diskgroup_data['Status'], 'Fail')
        self.assertIn('Log', diskgroup_data)
        mock_record.assert_called_once_with(gDiskgroupError['DiskGroupLCMInvocationError'], mock.ANY)
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_create_success_updates_request(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'create'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)

        with patch.object(manager, 'mClusterDgrpCreate', return_value=0) as mock_create:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 0)
        mock_create.assert_called_once_with(options)
        self.assertEqual(diskgroup_data['Command'], 'dg_create')
        self.assertEqual(diskgroup_data['Status'], 'Pass')
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_create_failure_short_circuits_update(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'create'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mClusterDgrpCreate', return_value=77):
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 77)
        self.assertEqual(diskgroup_data['Command'], 'dg_create')
        self.assertEqual(diskgroup_data['Status'], 'Fail')
        dbaas_obj._mUpdateRequestData.assert_not_called()

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_update_add_sparse_invokes_create_with_flag(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'update_add_sparse'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mClusterDgrpCreate', return_value=0) as mock_create:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 0)
        mock_create.assert_called_once_with(options, False)
        self.assertEqual(diskgroup_data['Command'], 'dg_update_add_sparse')
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_resize_calls_resize_and_updates_request(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'resize'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mClusterDgrpResize', return_value=0) as mock_resize:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 0)
        mock_resize.assert_called_once_with(options)
        self.assertEqual(diskgroup_data['Command'], 'dg_resize')
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_rebalance_failure_propagates_code(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'rebalance'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mClusterDgrpRebalance', return_value=13) as mock_rebalance:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 13)
        mock_rebalance.assert_called_once_with(options)
        self.assertEqual(diskgroup_data['Command'], 'dg_rebalance')
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_info_calls_info_handler(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'info'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mClusterDgrpInfo', return_value=0) as mock_info:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 0)
        mock_info.assert_called_once_with(options)
        self.assertEqual(diskgroup_data['Command'], 'dg_info')
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_precheck_success_sets_validation_flag(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'precheck'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mClusterDgrpCreate', return_value=0) as mock_create:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 0)
        mock_create.assert_called_once_with(options, True, True)
        self.assertEqual(diskgroup_data['Command'], 'dg_precheck')
        self.assertEqual(diskgroup_data['validatePrecheckSparseCreation'], 'Success')
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_none_operation_records_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = None
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mRecordError', return_value=77) as mock_record:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 77)
        self.assertEqual(diskgroup_data['Status'], 'Fail')
        self.assertEqual(diskgroup_data['Log'], 'Invalid invocation or unsupported DiskGroup LCM option')
        mock_record.assert_called_once_with(
            gDiskgroupError['DiskGroupLCMInvocationError'],
            '***Invalid invocation or unsupported DiskGroup LCM option'
        )
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_precheck_failure_marks_status_fail(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'precheck'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mClusterDgrpCreate', return_value=9) as mock_create:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 9)
        mock_create.assert_called_once_with(options, True, True)
        self.assertEqual(diskgroup_data['Status'], 'Fail')
        self.assertEqual(diskgroup_data['validatePrecheckSparseCreation'], 'Failed')
        dbaas_obj._mUpdateRequestData.assert_not_called()

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_unsupported_operation_records_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'archive'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mRecordError', return_value=55) as mock_record:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 55)
        mock_record.assert_called_once_with(gDiskgroupError['InvalidOp'], mock.ANY)
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_resets_status_before_each_operation(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'create'
        diskgroup_data = {'Status': 'Fail', 'Log': 'previous failure'}
        manager.mSetDiskGroupOperationData(diskgroup_data)

        with patch.object(manager, 'mClusterDgrpCreate', return_value=0):
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['Status'], 'Pass')
        self.assertEqual(diskgroup_data['Log'], 'previous failure')
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterManageDiskGroup
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterManageDiskGroup_update_add_sparse_bubbles_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        options.diskgroupOp = 'update_add_sparse'
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        dbaas_obj._mUpdateRequestData.reset_mock()

        with patch.object(manager, 'mClusterDgrpCreate', return_value=777) as mock_create:
            rc = manager.mClusterManageDiskGroup(options)

        self.assertEqual(rc, 777)
        mock_create.assert_called_once_with(options, False)
        dbaas_obj._mUpdateRequestData.assert_called_once_with(options, diskgroup_data, ebox)

    # Auto-generated test for mClusterDgrpInfo
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpInfo_success_populates_diskgroup_info(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        diskgroup_data = {}
        manager.mSetDiskGroupOperationData(diskgroup_data)
        constants = manager.mGetConstantsObj()
        ebox.mUpdateStatusOEDA.reset_mock()

        sample_info = {
            'DG_DATA': {
                constants._propkey_storage: {
                    constants._storprop_totalMb: '1000'
                }
            }
        }

        def fake_parse(options, req_params, op_data=None):
            req_params[constants._diskgroupname_key] = 'DG_DATA'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        dbaas_obj.mReadStatusFromDomU.return_value = sample_info

        rc = manager.mClusterDgrpInfo(options, ['props'])

        self.assertEqual(rc, 0)
        called_inparams = manager.mClusterParseInput.call_args[0][1]
        self.assertEqual(called_inparams[constants._diskgroupname_key], 'DG_DATA')
        manager.mClusterDgrpInfo2.assert_called_once_with(options, 'DG_DATA', ['props'])
        dbaas_obj.mReadStatusFromDomU.assert_called_once_with(options, 'domu1', manager.mGetOutJson())
        self.assertEqual(diskgroup_data['DiskgroupInfo'], sample_info)
        expected_status_calls = [
            mock.call(True, 'InfoFetch', ['InfoFetch', 'Complete'], 'Diskgroup Info Fetch operation for DG_DATA'),
            mock.call(True, 'Complete', ['InfoFetch', 'Complete'], 'Diskgroup Info Fetch operation for DG_DATA')
        ]
        self.assertEqual(ebox.mUpdateStatusOEDA.call_args_list, expected_status_calls)

    # Auto-generated test for mClusterDgrpInfo
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpInfo_returns_parse_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        manager.mClusterParseInput = MagicMock(return_value=222)
        manager.mClusterDgrpInfo2 = MagicMock()

        rc = manager.mClusterDgrpInfo(options)

        self.assertEqual(rc, 222)
        ebox.mUpdateStatusOEDA.assert_not_called()
        manager.mClusterDgrpInfo2.assert_not_called()
        dbaas_obj.mReadStatusFromDomU.assert_not_called()

    # Auto-generated test for mClusterDgrpInfo
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpInfo_records_error_when_fetch_fails(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        ebox.mUpdateStatusOEDA.reset_mock()

        def fake_parse(options, req_params, op_data=None):
            req_params[constants._diskgroupname_key] = 'DG_DATA'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mClusterDgrpInfo2 = MagicMock(return_value=5)

        with patch.object(manager, 'mRecordError', return_value=999) as mock_record:
            rc = manager.mClusterDgrpInfo(options, ['props'])

        self.assertEqual(rc, 999)
        mock_record.assert_called_once_with(gDiskgroupError['ErrorFetchingDetails'], mock.ANY)
        manager.mClusterDgrpInfo2.assert_called_once_with(options, 'DG_DATA', ['props'])
        dbaas_obj.mReadStatusFromDomU.assert_not_called()
        self.assertEqual(
            ebox.mUpdateStatusOEDA.call_args_list,
            [mock.call(True, 'InfoFetch', ['InfoFetch', 'Complete'], 'Diskgroup Info Fetch operation for DG_DATA')]
        )

    # Auto-generated test for mCalcCurrentDgRatio
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalcCurrentDgRatio_handles_backup_ratio(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        diskgroup_data = {}

        rc = manager.mCalcCurrentDgRatio(diskgroup_data, 1000, 1500)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['curr_dg_ratio'], '40:60')

    # Auto-generated test for mCalcCurrentDgRatio
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalcCurrentDgRatio_handles_sparse_ratio(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        diskgroup_data = {}

        rc = manager.mCalcCurrentDgRatio(diskgroup_data, 700, 1000)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['curr_dg_ratio'], '35:50:15')

    # Auto-generated test for mCalcCurrentDgRatio
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalcCurrentDgRatio_handles_non_backup_ratio(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        diskgroup_data = {}

        rc = manager.mCalcCurrentDgRatio(diskgroup_data, 6000, 2000)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['curr_dg_ratio'], '60:20:20')

    # Auto-generated test for mCalcCurrentDgRatio
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalcCurrentDgRatio_returns_error_for_unrecognized_ratio(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error):
        manager, _, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        diskgroup_data = {}

        rc = manager.mCalcCurrentDgRatio(diskgroup_data, 1000, 1000)

        self.assertEqual(rc, 1)
        self.assertNotIn('curr_dg_ratio', diskgroup_data)
        mock_log_error.assert_called_once()

    # Auto-generated test for mExecuteSetDGsRebalancePower
    def test_mExecuteSetDGsRebalancePower_updates_each_diskgroup(self):
        ebox = MagicMock()
        manager = ebCluManageDiskgroup(ebox, MagicMock())
        manager.mGetEbox = MagicMock(return_value=ebox)
        manager.mGetAoptions = MagicMock()
        manager.mGetAoptions.return_value.jsonconf = {}
        manager.mGetAoptions.return_value.configpath = None
        manager.mSetDiskGroupOperationData = MagicMock()
        manager.mClusterDgrpRebalance = MagicMock(return_value=0)
        manager.mRecordError = MagicMock()

        rc = manager.mExecuteSetDGsRebalancePower(['DG_DATA', 'DG_RECO'], 7)

        self.assertEqual(rc, 0)
        self.assertEqual(manager.mClusterDgrpRebalance.call_count, 2)
        manager.mSetDiskGroupOperationData.assert_has_calls([
            mock.call({'Command': 'dg_rebalance', 'diskgroup': 'DG_DATA', 'rebalance_power': 7}),
            mock.call({'Command': 'dg_rebalance', 'diskgroup': 'DG_RECO', 'rebalance_power': 7})
        ])
        self.assertEqual(manager.mGetAoptions.return_value.jsonconf['diskgroup'], 'DG_RECO')
        self.assertEqual(manager.mGetAoptions.return_value.jsonconf['rebalance_power'], 7)
        manager.mRecordError.assert_not_called()

    # Auto-generated test for mExecuteSetDGsRebalancePower
    def test_mExecuteSetDGsRebalancePower_reuses_existing_payload_when_hint_present(self):
        ebox = MagicMock()
        options = MagicMock()
        options.jsonconf = {'existing': 'value'}
        manager = ebCluManageDiskgroup(ebox, options)
        manager.mGetEbox = MagicMock(return_value=ebox)
        manager.mGetAoptions = MagicMock(return_value=options)
        manager.mSetDiskGroupOperationData = MagicMock()
        manager.mClusterDgrpRebalance = MagicMock(return_value=0)
        manager.mRecordError = MagicMock()

        rc = manager.mExecuteSetDGsRebalancePower(['DG_ONE'], 12)

        self.assertEqual(rc, 0)
        manager.mClusterDgrpRebalance.assert_called_once()
        manager.mSetDiskGroupOperationData.assert_called_once_with({'Command': 'dg_rebalance', 'diskgroup': 'DG_ONE', 'rebalance_power': 12})
        self.assertEqual(options.jsonconf['diskgroup'], 'DG_ONE')
        self.assertEqual(options.jsonconf['rebalance_power'], 12)
        manager.mRecordError.assert_not_called()

    # Auto-generated test for mExecuteSetDGsRebalancePower
    def test_mExecuteSetDGsRebalancePower_records_error_when_command_fails(self):
        ebox = MagicMock()
        manager = ebCluManageDiskgroup(ebox, MagicMock())
        manager.mGetEbox = MagicMock(return_value=ebox)
        manager.mGetAoptions = MagicMock()
        manager.mGetAoptions.return_value.jsonconf = {}
        manager.mSetDiskGroupOperationData = MagicMock()
        manager.mClusterDgrpRebalance = MagicMock(return_value=1)
        manager.mRecordError = MagicMock(return_value='error')
        ebox.mUpdateErrorObject = MagicMock()

        rc = manager.mExecuteSetDGsRebalancePower(['DG_FAIL'], 3)

        self.assertEqual(rc, 'error')
        manager.mClusterDgrpRebalance.assert_called_once()
        manager.mSetDiskGroupOperationData.assert_called_once_with({'Command': 'dg_rebalance', 'diskgroup': 'DG_FAIL', 'rebalance_power': 3})
        ebox.mUpdateErrorObject.assert_called_once_with(
            gElasticError['CELL_DG_REBAL_POWER_SET_FAILED'],
            'Could not set new rebalance power for diskgroup DG_FAIL'
        )
        manager.mRecordError.assert_called_once_with(
            gDiskgroupError['DgOperationError'],
            '*** Could not set new rebalance power for diskgroup DG_FAIL'
        )

    # Auto-generated test for mHandleDbaasapiSynchronousCall
    @patch('exabox.ovm.cludiskgroups.secrets.randbelow', return_value=123456)
    @patch('builtins.open', new_callable=mock.mock_open)
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mHandleDbaasapiSynchronousCall_success_with_info_and_resize(
        self, mock_get_gcontext, mock_ebCluDbaas, mock_open_file, mock_rand
    ):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        payload = {
            constants._operation_key: constants._operation_value,
            constants._action_key: 'resize',
            constants._params_key: {
                constants._diskgroupname_key: 'DG_DATA',
                constants._param_infofile_key: None
            }
        }
        msg = {}

        ebox.mGetUUID.return_value = 'UUID'
        ebox.mExecuteLocal = MagicMock()

        dbaas_obj.mBaseCopyFileToDomU = MagicMock()
        dbaas_obj.mExecCommandOnDomU = MagicMock(return_value=(0, 'output', 0))
        dbaas_obj.mReadStatusFromDomU = MagicMock(side_effect=[
            {'id': 'JOB1', 'logfile': '/var/log/job.log'},
            {'msg': 'resize complete'}
        ])
        dbaas_obj.mWaitForJobComplete = MagicMock(return_value=0)
        dbaas_obj.mCopyDomuInfoLog = MagicMock()

        rc = manager.mHandleDbaasapiSynchronousCall(options, payload, aInfo=True, aMsg=msg)

        self.assertEqual(rc, 0)
        diskgroup_data = manager.mGetDiskGroupOperationData()
        self.assertEqual(diskgroup_data['Status'], 'Pass')
        self.assertEqual(manager.mGetJobId(), 'JOB1')
        self.assertEqual(manager.mGetLogFile(), '/var/log/job.log')
        self.assertEqual(msg['msg'], 'resize complete')
        self.assertNotIn('errmsg', msg)

        uniq_suffix = '-UUID-0.123456'
        expected_local = f"/tmp/diskgroupOp{uniq_suffix}_input_UUID.json"
        expected_remote = f"/var/opt/oracle/log/dbaasapi/diskgroupOp{uniq_suffix}_input_UUID.json"
        expected_outfile = f"/var/opt/oracle/log/{constants._dbname_value}/diskgroupOp{uniq_suffix}.resize_UUID.out"
        expected_outjson = f"/var/opt/oracle/log/{constants._dbname_value}/diskgroupOp{uniq_suffix}.resize_UUID.json"

        mock_open_file.assert_called_once_with(expected_local, 'w')
        ebox.mExecuteLocal.assert_called_once_with(f"/bin/rm -f {expected_local}")
        dbaas_obj.mBaseCopyFileToDomU.assert_called_once_with('domu1', expected_local, expected_remote)
        self.assertEqual(payload[constants._outfile_key], expected_outfile)
        self.assertEqual(payload[constants._params_key][constants._param_infofile_key], expected_outjson)
        self.assertEqual(manager.mGetOutJson(), expected_outjson)
        self.assertEqual(manager.mGetLastDomUused(), 'domu1')
        self.assertEqual(dbaas_obj.mReadStatusFromDomU.call_count, 2)
        dbaas_obj.mCopyDomuInfoLog.assert_not_called()

    # Auto-generated test for mHandleDbaasapiSynchronousCall
    @patch('exabox.ovm.cludiskgroups.secrets.randbelow', return_value=999999)
    @patch('builtins.open', new_callable=mock.mock_open)
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mHandleDbaasapiSynchronousCall_records_error_when_jobid_missing(
        self, mock_get_gcontext, mock_ebCluDbaas, mock_open_file, mock_rand
    ):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        payload = {
            constants._operation_key: constants._operation_value,
            constants._action_key: 'info',
            constants._params_key: {}
        }

        ebox.mGetUUID.return_value = 'UUID2'
        ebox.mExecuteLocal = MagicMock()

        dbaas_obj.mBaseCopyFileToDomU = MagicMock()
        dbaas_obj.mExecCommandOnDomU = MagicMock(return_value=(0, '', 0))
        dbaas_obj.mReadStatusFromDomU = MagicMock(return_value={})
        dbaas_obj.mWaitForJobComplete = MagicMock()
        dbaas_obj.mCopyDomuInfoLog = MagicMock()

        manager.mRecordError = MagicMock(return_value='ERR42')

        rc = manager.mHandleDbaasapiSynchronousCall(options, payload, aInfo=False, aMsg={})

        self.assertEqual(rc, 'ERR42')
        manager.mRecordError.assert_called_once_with(
            gDiskgroupError['DbaasObjJobIDReadFail'],
            '*** Dbaas Obj Failed to read Job ID from domU'
        )
        diskgroup_data = manager.mGetDiskGroupOperationData()
        self.assertEqual(diskgroup_data['Status'], 'Fail')
        self.assertEqual(diskgroup_data['Log'], '*** Failed to read Job ID from domU')
        dbaas_obj.mWaitForJobComplete.assert_not_called()
        dbaas_obj.mCopyDomuInfoLog.assert_not_called()

    # Auto-generated test for mHandleDbaasapiSynchronousCall
    @patch('exabox.ovm.cludiskgroups.secrets.randbelow', return_value=555555)
    @patch('builtins.open', new_callable=mock.mock_open)
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mHandleDbaasapiSynchronousCall_handles_wait_failure_and_logs(
        self, mock_get_gcontext, mock_ebCluDbaas, mock_open_file, mock_rand
    ):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        payload = {
            constants._operation_key: constants._operation_value,
            constants._action_key: 'resize',
            constants._params_key: {}
        }
        status_msg = {}

        ebox.mGetUUID.return_value = 'UUID3'
        ebox.mExecuteLocal = MagicMock()

        dbaas_obj.mBaseCopyFileToDomU = MagicMock()
        dbaas_obj.mExecCommandOnDomU = MagicMock(return_value=(0, 'out', 0))
        dbaas_obj.mReadStatusFromDomU = MagicMock(side_effect=[
            {'id': 'JOB_FAIL'},
            {'msg': 'resizing', 'errmsg': 'ASM-123'}
        ])
        dbaas_obj.mWaitForJobComplete = MagicMock(return_value=1)
        dbaas_obj.mCopyDomuInfoLog = MagicMock()

        rc = manager.mHandleDbaasapiSynchronousCall(options, payload, aInfo=False, aMsg=status_msg)

        self.assertIsNone(rc)
        diskgroup_data = manager.mGetDiskGroupOperationData()
        self.assertEqual(diskgroup_data['Status'], 'Pass')
        self.assertEqual(status_msg['msg'], 'resizing')
        self.assertEqual(status_msg['errmsg'], 'ASM-123')
        self.assertEqual(manager.mGetJobId(), 'JOB_FAIL')
        self.assertIsNone(manager.mGetLogFile())
        dbaas_obj.mWaitForJobComplete.assert_called_once()
        dbaas_obj.mCopyDomuInfoLog.assert_called_once()
        uniq_suffix = '-UUID3-0.555555'
        expected_local = f"/tmp/diskgroupOp{uniq_suffix}_input_UUID3.json"
        dbaas_obj.mBaseCopyFileToDomU.assert_called_once_with('domu1', expected_local, mock.ANY)

    # Auto-generated test for mHandleDbaasapiSynchronousCall
    @patch('exabox.ovm.cludiskgroups.secrets.randbelow', return_value=101010)
    @patch('builtins.open', new_callable=mock.mock_open)
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mHandleDbaasapiSynchronousCall_sets_failure_status_on_exec_error(
        self, mock_get_gcontext, mock_ebCluDbaas, mock_open_file, mock_rand
    ):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        payload = {
            constants._operation_key: constants._operation_value,
            constants._action_key: 'resize',
            constants._params_key: {}
        }

        ebox.mGetUUID.return_value = 'UUID5'
        ebox.mExecuteLocal = MagicMock()
        dbaas_obj.mBaseCopyFileToDomU = MagicMock()
        dbaas_obj.mExecCommandOnDomU = MagicMock(return_value=(None, None, 9))

        rc = manager.mHandleDbaasapiSynchronousCall(options, payload, aInfo=False, aMsg={})

        self.assertIsNone(rc)
        diskgroup_data = manager.mGetDiskGroupOperationData()
        self.assertEqual(diskgroup_data['Status'], 'Fail')
        expected_msg = '*** Failed to execute dbaasapi command for action resize under operation diskgroup'
        self.assertEqual(diskgroup_data['Log'], expected_msg)
        self.assertEqual(manager.mGetJobId(), None)
        dbaas_obj.mExecCommandOnDomU.assert_called_once()

    # Auto-generated test for mHandleDbaasapiSynchronousCall
    @patch('exabox.ovm.cludiskgroups.secrets.randbelow', return_value=202020)
    @patch('builtins.open', new_callable=mock.mock_open)
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mHandleDbaasapiSynchronousCall_returns_error_when_wait_fails(
        self, mock_get_gcontext, mock_ebCluDbaas, mock_open_file, mock_rand
    ):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        payload = {
            constants._operation_key: constants._operation_value,
            constants._action_key: 'drop',
            constants._params_key: {}
        }

        ebox.mGetUUID.return_value = 'UUID6'
        ebox.mExecuteLocal = MagicMock()
        dbaas_obj.mBaseCopyFileToDomU = MagicMock()
        dbaas_obj.mExecCommandOnDomU = MagicMock(return_value=(0, '', 0))
        dbaas_obj.mReadStatusFromDomU = MagicMock(side_effect=[
            {'id': 'JOB_ERR', 'logfile': '/var/log/job_err.log'},
            {'msg': 'failing drop', 'errmsg': 'ASM-999'}
        ])
        dbaas_obj.mWaitForJobComplete = MagicMock(return_value=44)
        dbaas_obj.mCopyDomuInfoLog = MagicMock()
        manager.mRecordError = MagicMock(return_value='ERR_WAIT')

        rc = manager.mHandleDbaasapiSynchronousCall(options, payload, aInfo=False, aMsg={})

        self.assertIsNone(rc)
        self.assertEqual(manager.mRecordError.call_count, 0)
        self.assertEqual(manager.mGetJobId(), 'JOB_ERR')
        self.assertEqual(manager.mGetLogFile(), '/var/log/job_err.log')
        copy_args = dbaas_obj.mCopyDomuInfoLog.call_args[0]
        self.assertEqual(copy_args[0], options)
        self.assertEqual(copy_args[1], 'domu1')
        self.assertEqual(copy_args[2], '/var/log/job_err.log')

    # Auto-generated test for mWaitUntilDgRebalanced
    @patch('exabox.ovm.cludiskgroups.time.sleep')
    @patch('exabox.ovm.cludiskgroups.exaBoxNode')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mWaitUntilDgRebalanced_missing_status_records_error(
        self, mock_ebCluDbaas, mock_get_gcontext, mock_exaBoxNode, mock_sleep
    ):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=0)
        dbaas_obj.mReadStatusFromDomU.return_value = {
            'DG_X': {
                constants._propkey_rebstat: {}
            }
        }

        node = MagicMock()
        mock_exaBoxNode.return_value = node
        manager.mRecordError = MagicMock(return_value=55)

        rc = manager.mWaitUntilDgRebalanced(options, 'DG_X', constants)

        self.assertEqual(rc, 55)
        manager.mRecordError.assert_called_once()
        mock_sleep.assert_not_called()

    # Auto-generated test for mCalcOverallRebalPercent
    @patch('exabox.ovm.cludiskgroups.ebLogWarn')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalcOverallRebalPercent_weighted_average_success(
        self, mock_get_gcontext, mock_ebCluDbaas, mock_log_warn
    ):
        manager, ebox, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco', 'dg_sparse']
        storage = MagicMock()

        def diskgroup_config(name, dg_type, size):
            cfg = MagicMock()
            cfg.mGetDiskGroupType.return_value = dg_type
            cfg.mGetDgName.return_value = name
            cfg.mGetDiskGroupSize.return_value = size
            return cfg

        storage.mGetDiskGroupConfig.side_effect = [
            diskgroup_config('DATAC1', constants._data_dg_type_str, '100G'),
            diskgroup_config('RECOC1', constants._reco_dg_type_str, '50G'),
            diskgroup_config('SPRC1', constants._sparse_dg_type_str, '25G')
        ]
        storage.mGetDiskSizeInInt.side_effect = [100, 50, 25]

        cluster_ctrl = MagicMock()
        cluster_ctrl.mGetCluster.return_value = cluster
        ebox.mGetClusters.return_value = cluster_ctrl
        ebox.mGetStorage.return_value = storage
        manager._dict_groups_percent_avg = {'DATAC1': 80, 'RECOC1': 40, 'SPRC1': 20}

        percent = manager.mCalcOverallRebalPercent(constants)

        self.assertEqual(percent, int(80 * (100 / 175) + 40 * (50 / 175) + 20 * (25 / 175)))
        mock_log_warn.assert_not_called()

    # Auto-generated test for mCalcOverallRebalPercent
    @patch('exabox.ovm.cludiskgroups.ebLogWarn')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mCalcOverallRebalPercent_exception_returns_zero(
        self, mock_get_gcontext, mock_ebCluDbaas, mock_log_warn
    ):
        manager, ebox, _, _ = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        ebox.mGetClusters.side_effect = Exception('boom')

        percent = manager.mCalcOverallRebalPercent(constants)

        self.assertEqual(percent, 0)
        mock_log_warn.assert_called_once()


if __name__ == "__main__":
    unittest.main(warnings='ignore')
    def _mock_cluster_with_sparse(self, ebox, constants, sparse_name=None):
        cluster = MagicMock()
        storage = MagicMock()

        sparse_dg = MagicMock()
        data_dg = MagicMock()
        reco_dg = MagicMock()
        sparse_dg.mGetDgName.return_value = sparse_name or 'SPRC'
        sparse_dg.mGetDgType.return_value = constants._sparse_dg_type_str
        sparse_dg.mGetDiskGroupType.return_value = constants._sparse_dg_type_str

        data_dg.mGetDgType.return_value = constants._data_dg_type_str
        data_dg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_dg.mGetDgName.return_value = 'DATA'
        data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        reco_dg.mGetDgType.return_value = constants._reco_dg_type_str
        reco_dg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        reco_dg.mGetDgName.return_value = 'RECO'

        cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco', 'dg_sparse']
        storage.mGetDiskGroupConfig.side_effect = [data_dg, reco_dg, sparse_dg]
        cluster.mGetCluster.return_value = cluster

        ebox.mGetClusters.return_value = cluster
        ebox.mGetStorage.return_value = storage
        return data_dg, reco_dg, sparse_dg
    # Auto-generated test for mDiskgroupUpdate
    @patch('exabox.ovm.cludiskgroups.ebCluUtils')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDiskgroupUpdate_resize_shrink_success_flow(self, mock_get_gcontext, mock_ebCluDbaas, mock_ebCluUtils):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        # Stub top level options to avoid add-cell shortcut
        args_options = MagicMock()
        args_options.jsonconf = {}
        args_options.steplist = None
        ebox.mGetArgsOptions.return_value = args_options

        # Prepare payload coming from parse input
        new_size_gb = '1024'

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgroupname_key] = 'DATAC'
            req_params[constants._newsizeGB_key] = new_size_gb
            req_params[constants._rebalancepower_key] = 3
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)

        # Current size comes from ASM, ensure shrink path (new < current)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=2 * 1024 * 1024)

        # Stub info gathering helpers
        dbaas_obj.mReadStatusFromDomU.return_value = {}
        manager.mGetLastDomUused = MagicMock(return_value='domu1')
        manager.mGetOutJson = MagicMock(return_value={'foo': 'bar'})

        manager.mValidateAndGetFailgroupDetails = MagicMock(return_value=0)
        manager._extract_cell_vs_griddisks_map = MagicMock(return_value=0)
        manager.mGetFailGroupList = MagicMock(return_value=['fg1'])
        manager.mLogRebalanceTimeEstimate = MagicMock()
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mValidateDgsPostRebalance = MagicMock(return_value=0)
        manager.mResizeGriddisks = MagicMock(return_value=0)

        # simulate celldisk map leading to specific slice values
        cell_vs_griddisks = {
            'cell1': ['gd1', 'gd2'],
            'cell2': ['gd3', 'gd4']
        }

        def fake_extract(dg_name, _, mapping):
            mapping.update(cell_vs_griddisks)
            return 0

        manager._extract_cell_vs_griddisks_map.side_effect = fake_extract

        # Provide reagents for utility to compute slice
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mGetResizeDgonCells = MagicMock(return_value=False)
        manager.mGetGridDiskCountRetryResize = MagicMock(return_value=0)
        manager.mGetCurrentRetrySizeTotalMB = MagicMock(return_value=0)

        # Capture the payload sent to DBaaS
        responses = [{'Status': 'Pass'}]

        def fake_handle(options_arg, injson, info=False, msg=None):
            if msg is not None:
                msg.clear()
            responses.append(injson)
            return 0

        manager.mHandleDbaasapiSynchronousCall = MagicMock(side_effect=fake_handle)

        mock_utils_instance = MagicMock()
        mock_ebCluUtils.return_value = mock_utils_instance

        rc = manager.mDiskgroupUpdate(options, 'ResizeDiskgroup')

        self.assertEqual(rc, 0)
        manager.mClusterParseInput.assert_called_once()
        manager.mUtilGetDiskgroupSize.assert_called_once()
        manager.mValidateAndGetFailgroupDetails.assert_called_once()
        manager.mHandleDbaasapiSynchronousCall.assert_called()
        manager.mEnsureDgsRebalanced.assert_called_once()
        manager.mValidateDgsPostRebalance.assert_called_once()
        manager.mResizeGriddisks.assert_called_once()
        mock_utils_instance.mStepSpecificDetails.assert_called_once()
        mock_utils_instance.mUpdateTaskProgressStatus.assert_called_once()

    # Auto-generated test for mDiskgroupUpdate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDiskgroupUpdate_failgroup_validation_failure_records_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgroupname_key] = 'DATAC1'
            req_params[constants._newsizeGB_key] = '1024'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=2 * 1024 * 1024)
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mGetLastDomUused = MagicMock(return_value='domu1')
        manager.mGetOutJson = MagicMock(return_value={'info': 'dummy'})
        dbaas_obj.mReadStatusFromDomU.return_value = {}

        manager.mValidateAndGetFailgroupDetails = MagicMock(return_value=77)
        manager._extract_cell_vs_griddisks_map = MagicMock()

        rc = manager.mDiskgroupUpdate(options, 'ResizeDiskgroup')

        self.assertEqual(rc, 77)
        manager._extract_cell_vs_griddisks_map.assert_not_called()
        ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_FETCHING_GRIDDISK_COUNT'],
            'mDiskgroupUpdate: Failed to count number of grid disks.'
        )

    # Auto-generated test for mDiskgroupUpdate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDiskgroupUpdate_grid_disk_count_missing_sets_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgroupname_key] = 'DATAC2'
            req_params[constants._newsizeGB_key] = '512'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=1024 * 1024)
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mGetLastDomUused = MagicMock(return_value='domu1')
        manager.mGetOutJson = MagicMock(return_value={'info': 'dummy'})
        dbaas_obj.mReadStatusFromDomU.return_value = {}

        def fake_validate(info, dg_name, consts, out_dict):
            out_dict.update({
                'CELL1': {
                    consts._fgrpprop_celldisks: ['gd_a'],
                    consts._fgrpprop_numdisks: '1'
                },
                'CELL2': {
                    consts._fgrpprop_celldisks: ['gd_b', 'gd_c'],
                    consts._fgrpprop_numdisks: '2'
                }
            })
            return 0

        manager.mValidateAndGetFailgroupDetails = MagicMock(side_effect=fake_validate)

        def fake_extract(dg_name, failgroups, dest):
            dest.update({'CELL1': ['gd_a']})
            return 0

        manager._extract_cell_vs_griddisks_map = MagicMock(side_effect=fake_extract)
        manager.mRecordError = MagicMock(return_value=88)

        rc = manager.mDiskgroupUpdate(options, 'ResizeDiskgroup')

        self.assertEqual(rc, 88)
        manager._extract_cell_vs_griddisks_map.assert_called_once()
        manager.mRecordError.assert_called_once_with(gDiskgroupError['ErrorFetchingDetails'], mock.ANY)
        ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_FETCHING_GRIDDISK_COUNT'],
            'mDiskgroupUpdate: Failed to count number of grid disks.'
        )

    # Auto-generated test for mDiskgroupUpdate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDiskgroupUpdate_parse_failure_bubbles_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)

        manager.mClusterParseInput = MagicMock(return_value=321)
        rc = manager.mDiskgroupUpdate(options, 'ResizeDiskgroup')

        self.assertEqual(rc, 321)
        ebox.mUpdateErrorObject.assert_called_once()
        dbaas_obj.mReadStatusFromDomU.assert_not_called()

    # Auto-generated test for mDiskgroupUpdate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDiskgroupUpdate_resize_equal_size_returns_early(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgroupname_key] = 'DATAC'
            req_params[constants._newsizeGB_key] = '1024'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=1024 * 1024)

        rc = manager.mDiskgroupUpdate(options, 'ResizeDiskgroup')

        self.assertEqual(rc, 0)
        manager.mHandleDbaasapiSynchronousCall.assert_not_called()
        ebox.mUpdateStatusOEDA.assert_not_called()

    # Auto-generated test for mDiskgroupUpdate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDiskgroupUpdate_resize_handles_ora15025_retry_and_vote_reloc(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        args_options = MagicMock()
        args_options.jsonconf = {}
        args_options.steplist = None
        ebox.mGetArgsOptions.return_value = args_options

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgroupname_key] = 'DATAC'
            req_params[constants._newsizeGB_key] = '10'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=40 * 1024)

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mValidateAndGetFailgroupDetails = MagicMock(return_value=0)
        manager._extract_cell_vs_griddisks_map = MagicMock(return_value=0)
        manager.mGetResizeDgonCells = MagicMock(return_value=False)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mValidateDgsPostRebalance = MagicMock(return_value=0)
        manager.mResizeGriddisks = MagicMock(return_value=0)
        manager.mGetFailGroupList = MagicMock(return_value=['fg'])
        manager.mLogRebalanceTimeEstimate = MagicMock()
        manager.mRelocateVotedisk = MagicMock(return_value=0)

        # Build cell map to hit main resize path (decrease size)
        def fake_extract(dg_name, _, mapping):
            mapping.update({'cell1': ['gd1', 'gd2'], 'cell2': ['gd3', 'gd4']})
            return 0

        manager._extract_cell_vs_griddisks_map.side_effect = fake_extract

        call_results = []

        def fake_handle(options_arg, injson, info=False, msg=None):
            call_results.append(injson)
            if msg is not None:
                if len(call_results) == 1:
                    msg['errmsg'] = 'ORA-15025 something'
                else:
                    msg['msg'] = 'relocating voting disks'
            return 0

        manager.mHandleDbaasapiSynchronousCall = MagicMock(side_effect=fake_handle)

        rc = manager.mDiskgroupUpdate(options, 'ResizeDiskgroup')

        self.assertEqual(rc, 0)
        self.assertGreaterEqual(len(call_results), 2)
        manager.mHandleDbaasapiSynchronousCall.assert_called()
        manager.mRelocateVotedisk.assert_called()
        manager.mEnsureDgsRebalanced.assert_called_once()

    # Auto-generated test for mDiskgroupUpdate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDiskgroupUpdate_resize_add_cell_skips_rebalance(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        args_options = MagicMock()
        args_options.jsonconf = {'reshaped_node_subset': {'added_cells': ['cell1']}}
        args_options.steplist = 'RESIZE_DGS'
        ebox.mGetArgsOptions.return_value = args_options
        ebox.mIsOciEXACC.return_value = False

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgroupname_key] = 'DATAC'
            req_params[constants._newsizeGB_key] = '5'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=10 * 1024)
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mValidateAndGetFailgroupDetails = MagicMock(return_value=0)
        manager._extract_cell_vs_griddisks_map = MagicMock(return_value=0)

        def fake_extract(dg_name, _, mapping):
            mapping.update({'cell1': ['gd1', 'gd2'], 'cell2': ['gd3', 'gd4']})
            return 0

        manager._extract_cell_vs_griddisks_map.side_effect = fake_extract

        manager.mGetFailGroupList = MagicMock(return_value=['fg'])
        manager.mLogRebalanceTimeEstimate = MagicMock()
        manager.mResizeGriddisks = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mValidateDgsPostRebalance = MagicMock(return_value=0)

        manager.mHandleDbaasapiSynchronousCall = MagicMock(return_value=0)

        rc = manager.mDiskgroupUpdate(options, 'ResizeDiskgroup')

        self.assertEqual(rc, 0)
        manager.mEnsureDgsRebalanced.assert_not_called()
        manager.mValidateDgsPostRebalance.assert_not_called()
        manager.mResizeGriddisks.assert_not_called()

    # Auto-generated test for mDiskgroupUpdate
    @patch('exabox.ovm.cludiskgroups.ebCluUtils')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mDiskgroupUpdate_resize_expand_triggers_griddisk_phase_first(
        self, mock_get_gcontext, mock_ebCluDbaas, mock_ebCluUtils
    ):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        args_options = MagicMock()
        args_options.jsonconf = {}
        args_options.steplist = None
        ebox.mGetArgsOptions.return_value = args_options
        ebox.mIsOciEXACC.return_value = False

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgroupname_key] = 'DATAC'
            req_params[constants._newsizeGB_key] = '2048'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=1024 * 1024)

        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)

        def fake_validate(info, dg_name, consts, out_dict):
            out_dict.update({
                'FG1': {
                    consts._fgrpprop_numdisks: '2',
                    consts._fgrpprop_celldisks: ['GD_01', 'GD_02']
                },
                'FG2': {
                    consts._fgrpprop_numdisks: '2',
                    consts._fgrpprop_celldisks: ['GD_03', 'GD_04']
                }
            })
            return 0

        manager.mValidateAndGetFailgroupDetails = MagicMock(side_effect=fake_validate)

        def fake_extract(dg_name, failgroups, cell_map):
            cell_map['cell1'] = ['GD_01', 'GD_02']
            cell_map['cell2'] = ['GD_03', 'GD_04']
            return 0

        manager._extract_cell_vs_griddisks_map = MagicMock(side_effect=fake_extract)

        manager.mGetResizeDgonCells = MagicMock(return_value=False)
        manager.mGetGridDiskCountRetryResize = MagicMock(return_value=0)
        manager.mGetCurrentRetrySizeTotalMB = MagicMock(return_value=0)
        manager.mGetFailGroupList = MagicMock(return_value=['fg'])
        manager.mLogRebalanceTimeEstimate = MagicMock()

        manager.mGetLastDomUused = MagicMock(return_value='domu1')
        manager.mGetOutJson = MagicMock(return_value={'path': 'dummy'})
        dbaas_obj.mReadStatusFromDomU.return_value = {}

        call_order = []

        def record(name):
            def _inner(*args, **kwargs):
                call_order.append(name)
                return 0
            return _inner

        manager.mResizeGriddisks = MagicMock(side_effect=record('griddisks'))
        manager.mHandleDbaasapiSynchronousCall = MagicMock(side_effect=record('handle'))
        manager.mEnsureDgsRebalanced = MagicMock(side_effect=record('ensure'))
        manager.mValidateDgsPostRebalance = MagicMock(side_effect=record('validate'))
        manager.mRelocateVotedisk = MagicMock(return_value=0)

        mock_utils_instance = MagicMock()
        mock_ebCluUtils.return_value = mock_utils_instance

        rc = manager.mDiskgroupUpdate(options, 'ResizeDiskgroup')

        self.assertEqual(rc, 0)
        self.assertGreaterEqual(len(call_order), 3)
        self.assertEqual(call_order[:3], ['griddisks', 'handle', 'ensure'])

        first_status_args = ebox.mUpdateStatusOEDA.call_args_list[0].args
        self.assertEqual(first_status_args[1], 'GdResize')

        manager.mResizeGriddisks.assert_called_once()
        manager.mHandleDbaasapiSynchronousCall.assert_called_once()
        manager.mEnsureDgsRebalanced.assert_called_once()
        manager.mValidateDgsPostRebalance.assert_called_once()

        handle_args = manager.mHandleDbaasapiSynchronousCall.call_args[0]
        self.assertTrue(handle_args[2])

        diskgroup_data = manager.mGetDiskGroupOperationData()
        self.assertEqual(diskgroup_data['SizeMB'], 2048 * 1024)

    # Auto-generated test for mClusterDgrpResize
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpResize_delegates_to_update(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        manager.mDiskgroupUpdate = MagicMock(return_value=42)

        rc = manager.mClusterDgrpResize(options)

        self.assertEqual(rc, 42)
        manager.mDiskgroupUpdate.assert_called_once_with(options, 'ResizeDiskgroup')

    # Auto-generated test for mClusterDgrpRebalance
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpRebalance_delegates_to_update(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, dbaas_obj, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        manager.mDiskgroupUpdate = MagicMock(return_value=55)

        rc = manager.mClusterDgrpRebalance(options)

        self.assertEqual(rc, 55)
        manager.mDiskgroupUpdate.assert_called_once_with(options, 'RebalanceDiskgroup')

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_resizable_precheck_only_returns_check_result(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        diskgroup_data = {}
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=[])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            req_params[constants._diskgroupname_key] = 'SPRC_TEMP'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=1024)
        manager.mCheckIfDgsResizable = MagicMock(return_value=9)
        manager.mCreateSparseGriddisks = MagicMock()
        manager.mCreateSparseDg = MagicMock()
        manager.mEnsureDgsRebalanced = MagicMock()
        manager.mUpdateDgrpData = MagicMock()
        manager.mResizeDgAndGriddisks = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aShrinkExistingDgs=False, aResizablePrecheckOnly=True)

        self.assertEqual(rc, 9)
        manager.mCheckIfDgsResizable.assert_called_once()
        manager.mCreateSparseGriddisks.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_duplicate_non_sparse_records_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        diskgroup_data = {}
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=[])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._data_dg_type_str
            req_params[constants._diskgroupname_key] = 'DATAC_NEW'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=2048)
        manager.mCheckIfDgsResizable = MagicMock()
        manager.mRecordError = MagicMock(return_value='dup_error')

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, 'dup_error')
        manager.mRecordError.assert_called_once()
        manager.mCheckIfDgsResizable.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_unsupported_type_errors_without_precheck(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        diskgroup_data = {}
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=[])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._catalog_dg_type_str
            req_params[constants._diskgroupname_key] = 'CATALOG_NEW'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=3072)
        manager.mCheckIfDgsResizable = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aShrinkExistingDgs=False)

        self.assertEqual(rc, 0)
        self.assertTrue(mock_log_error.called)
        manager.mCheckIfDgsResizable.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebLogInfo')
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_unsupported_type_precheck_logs_and_returns(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error, mock_log_info):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        diskgroup_data = {}
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=[])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._delta_dg_type_str
            req_params[constants._diskgroupname_key] = 'DELTA_NEW'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=4096)
        manager.mCheckIfDgsResizable = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aShrinkExistingDgs=False, aResizablePrecheckOnly=True)

        self.assertEqual(rc, 0)
        mock_log_error.assert_called_once()
        self.assertTrue(any('ResizablePrecheckOnly<<<' in str(call.args[0]) for call in mock_log_info.call_args_list))
        manager.mCheckIfDgsResizable.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_initializes_diskgroup_data_when_missing(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        diskgroup_data = {}
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=['rollback_marker'])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[2048, 1024])
        manager.mCheckIfDgsResizable = MagicMock(return_value=7)
        manager.mUpdateDgrpData = MagicMock()
        manager.mResizeDgAndGriddisks = MagicMock()
        manager.mCreateSparseGriddisks = MagicMock()
        manager.mCreateSparseDg = MagicMock()
        manager.mEnsureDgsRebalanced = MagicMock()
        manager.mRollback = MagicMock()

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, 7)
        manager.mGetDiskGroupOperationData.assert_called_once()
        self.assertEqual(diskgroup_data['Status'], 'Pass')
        self.assertEqual(diskgroup_data['ErrorCode'], '0')
        self.assertTrue(diskgroup_data[constants._diskgroupname_key].startswith(constants._sparse_dg_prefix))
        self.assertEqual(diskgroup_data[constants._redundancy_factor], 2)
        manager.mCheckIfDgsResizable.assert_called_once()
        manager.mUpdateDgrpData.assert_not_called()
        manager.mRollback.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_existing_diskgroup_records_error(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        diskgroup_data = {}
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=[])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._data_dg_type_str
            req_params[constants._diskgroupname_key] = 'DATAC'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=True)
        manager.mRecordError = MagicMock(return_value='already-exists')

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, 'already-exists')
        manager.mRecordError.assert_called_once_with(
            gDiskgroupError['DgAlreadyExists'],
            'The diskgroup %s already exists' % constants._data_dg_type_str
        )
        mock_log_error.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_with_external_data_returns_parse_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        external_data = {'seed': True}
        manager.mGetRollbackStack = MagicMock(return_value=[])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            return 77

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aDiskgroupData=external_data)

        self.assertEqual(rc, 77)
        self.assertEqual(external_data[constants._diskgrouptype_key], constants._sparse_dg_type_str)
        self.assertEqual(external_data['Status'], 'Pass')
        manager.mCalculateNewDgSizes.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_calculate_sizes_failure_bubbles_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        diskgroup_data = {}
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=[])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=5)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[1024, 2048])

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, 5)
        manager.mCalculateNewDgSizes.assert_called_once()
        manager.mCheckIfDgsResizable.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_update_dgrp_data_failure_prevents_resize(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        diskgroup_data = {}
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=[])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[2048, 2048])
        manager.mCheckIfDgsResizable = MagicMock(return_value=0)
        manager.mUpdateDgrpData = MagicMock(return_value=-1)
        manager.mResizeDgAndGriddisks = MagicMock()

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, -1)
        manager.mUpdateDgrpData.assert_called_once()
        manager.mResizeDgAndGriddisks.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_sparse_resize_failure_rolls_back(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        self._mock_cluster_with_sparse(ebox, constants)

        diskgroup_data = {}
        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=['mDropGridDisks'])
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            req_params[constants._rebalancepower_key] = '4'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(return_value=2048)
        manager.mCheckIfDgsResizable = MagicMock(return_value=0)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        manager.mResizeDgAndGriddisks = MagicMock(side_effect=[0, 5])
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mRollback = MagicMock(return_value='rollback-result')

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, 5)
        manager.mResizeDgAndGriddisks.assert_called()
        manager.mRollback.assert_called_once_with(['mDropGridDisks'])
        self.assertEqual(diskgroup_data[constants._rebalancepower_key], '4')
        mock_log_error.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_sparse_success_full_path(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}
        rollback_stack = []

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=rollback_stack)
        manager.mGetEbox = MagicMock(return_value=ebox)

        self._setup_sparse_cluster(manager, ebox, constants)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            req_params[constants._rebalancepower_key] = '8'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        self._mock_diskgroup_sizes_sequence(
            manager,
            {
                ('DATAC1', 0): 3072,
                ('RECOC1', 0): 1024
            }
        )

        manager.mCalculateNewDgSizes = MagicMock(side_effect=lambda *args: (diskgroup_data.update({
            constants._data_dg_rawname: {'pct_free': '50'},
            constants._reco_dg_rawname: {'pct_free': '50'}
        }), 0)[1])

        def fake_resizable(options, current_sizes, new_sizes, dg_data, delete_sparse=False):
            dg_data['sparsedg_new_size'] = 2048
            new_sizes[constants._data_dg_rawname] = 2048
            new_sizes[constants._reco_dg_rawname] = 1024
            return 0

        manager.mCheckIfDgsResizable = MagicMock(side_effect=fake_resizable)

        def fake_update(options, dg_data, datadg, cur_size, aDeleteSparse=False):
            dg_data['cell_count'] = 3
            dg_data['griddisk_count'] = 12
            return 0

        manager.mUpdateDgrpData = MagicMock(side_effect=fake_update)

        manager.mResizeDgAndGriddisks = MagicMock(side_effect=[0, 0])
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mRollback = MagicMock(return_value='rollback-result')

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data['Status'], 'Pass')
        self.assertEqual(diskgroup_data['ErrorCode'], '0')
        self.assertEqual(diskgroup_data[constants._diskgrouptype_key], constants._sparse_dg_type_str)
        self.assertEqual(diskgroup_data[constants._rebalancepower_key], '8')
        self.assertEqual(diskgroup_data['cell_count'], 3)
        self.assertEqual(diskgroup_data['griddisk_count'], 12)
        manager.mCheckIfDgsResizable.assert_called_once()
        manager.mUpdateDgrpData.assert_called_once()
        self.assertEqual(rollback_stack, [{manager.mDropGridDisks: (options, diskgroup_data[constants._diskgroupname_key])}, {manager.mDropDiskGroup: (options, diskgroup_data[constants._diskgroupname_key], 'yes')}])
        mock_log_error.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebLogInfo')
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_sparse_update_data_failure_rollbacks(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error, mock_log_info):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}
        rollback_stack = []

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=rollback_stack)
        manager.mGetEbox = MagicMock(return_value=ebox)

        self._setup_sparse_cluster(manager, ebox, constants)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            req_params[constants._rebalancepower_key] = '3'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        self._mock_diskgroup_sizes_sequence(
            manager,
            {
                ('DATAC1', 0): 4096,
                ('RECOC1', 0): 2048
            }
        )
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)

        def populate_new_sizes(options, current_sizes, new_sizes, dg_data, delete_sparse=False):
            new_sizes[constants._data_dg_rawname] = 4096
            new_sizes[constants._reco_dg_rawname] = 2048
            return 0

        manager.mCheckIfDgsResizable = MagicMock(side_effect=populate_new_sizes)
        manager.mUpdateDgrpData = MagicMock(return_value=55)
        manager.mRollback = MagicMock(return_value='rolled')

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, 55)
        manager.mRollback.assert_called_once()
        mock_log_error.assert_any_call(mock.ANY)
        mock_log_info.assert_any_call("*** ebCluManageDiskgroup:mClusterDgrpCreate - Updating DiskgroupData with sparse related info, cell count and griddisk count for rollback")
        self.assertEqual(rollback_stack, [])

    
    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebLogInfo')
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_sparse_skip_resize_but_resizable(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error, mock_log_info):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}
        rollback_stack = []

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=rollback_stack)
        manager.mGetEbox = MagicMock(return_value=ebox)

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            req_params[constants._rebalancepower_key] = '5'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[4096, 2048])

        def fake_resizable(options, current_sizes, new_sizes, dg_data, delete_sparse=False):
            new_sizes[constants._data_dg_rawname] = 5120
            new_sizes[constants._reco_dg_rawname] = 2560
            dg_data[constants._sparse_dg_rawname] = 'SPRC2'
            dg_data['cell_count'] = 10
            return 0

        manager.mCheckIfDgsResizable = MagicMock(side_effect=fake_resizable)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        manager.mResizeDgAndGriddisks = MagicMock()
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mRollback = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aShrinkExistingDgs=False)

        self.assertEqual(rc, 0)
        manager.mCheckIfDgsResizable.assert_called_once()
        manager.mUpdateDgrpData.assert_called_once_with(options, diskgroup_data, 'DATAC', 4096)
        manager.mResizeDgAndGriddisks.assert_not_called()
        manager.mCreateSparseGriddisks.assert_called_once_with(options, diskgroup_data)
        manager.mCreateSparseDg.assert_called_once_with(
            options,
            {
                constants._data_dg_rawname: 5120,
                constants._reco_dg_rawname: 2560
            },
            diskgroup_data
        )
        manager.mEnsureDgsRebalanced.assert_called_once_with(options, 'SPRC2', diskgroup_data)
        manager.mRollback.assert_not_called()
        self.assertEqual(diskgroup_data[constants._rebalancepower_key], '5')
        mock_log_error.assert_not_called()
        mock_log_info.assert_any_call("*** ebCluManageDiskgroup:mClusterDgrpCreate - Updating DiskgroupData with sparse related info, cell count and griddisk count for rollback")

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_sparse_full_path_updates_status(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}
        rollback_stack = []

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=rollback_stack)
        manager.mGetEbox = MagicMock(return_value=ebox)
        ebox.mUpdateStatusOEDA = MagicMock()

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco']

        data_dg = MagicMock()
        data_dg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_dg.mGetDgName.return_value = 'DATAC1'
        data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        reco_dg = MagicMock()
        reco_dg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        reco_dg.mGetDgName.return_value = 'RECOC1'

        storage = MagicMock()
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: {
            'dg_data': data_dg,
            'dg_reco': reco_dg
        }[dgid]

        ebox.mGetClusters.return_value = MagicMock(mGetCluster=MagicMock(return_value=cluster))
        ebox.mGetStorage.return_value = storage

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            req_params[constants._diskgroupname_key] = ''
            req_params[constants._rebalancepower_key] = '5'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)

        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[4096, 2048])

        def fake_resizable(opts, current_sizes, new_sizes, dg_data, delete_sparse=False):
            new_sizes[constants._data_dg_rawname] = 5120
            new_sizes[constants._reco_dg_rawname] = 2560
            dg_data[constants._sparse_dg_rawname] = 'SPRC1'
            return 0

        manager.mCheckIfDgsResizable = MagicMock(side_effect=fake_resizable)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        manager.mResizeDgAndGriddisks = MagicMock(side_effect=[0, 0])
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mRollback = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aShrinkExistingDgs=True)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data[constants._diskgroupname_key], 'SPRC1')
        self.assertEqual(diskgroup_data[constants._rebalancepower_key], '5')
        manager.mUpdateDgrpData.assert_called_once_with(options, diskgroup_data, 'DATAC1', 4096)
        manager.mResizeDgAndGriddisks.assert_has_calls([
            mock.call(options, 'DATAC1', 5120, 4096, rollback_stack, diskgroup_data),
            mock.call(options, 'RECOC1', 2560, 2048, rollback_stack, diskgroup_data)
        ])
        manager.mCreateSparseGriddisks.assert_called_once_with(options, diskgroup_data)
        manager.mCreateSparseDg.assert_called_once_with(
            options,
            {
                constants._data_dg_rawname: 5120,
                constants._reco_dg_rawname: 2560
            },
            diskgroup_data
        )
        manager.mEnsureDgsRebalanced.assert_called_once_with(options, 'SPRC1', diskgroup_data)
        manager.mRollback.assert_not_called()
        ebox.mUpdateStatusOEDA.assert_any_call(True, 'Create_Diskgroup', mock.ANY, 'Creating sparse diskgroup')
        ebox.mUpdateStatusOEDA.assert_any_call(True, 'Complete', mock.ANY, 'Diskgroup Create Completed')

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebLogInfo')
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_sparse_applies_generated_name_when_missing(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error, mock_log_info):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}
        rollback_stack = []

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=rollback_stack)
        manager.mGetEbox = MagicMock(return_value=ebox)
        self._setup_sparse_cluster(manager, ebox, constants, dg_name='SPRC1')

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            req_params[constants._diskgroupname_key] = ''
            req_params[constants._rebalancepower_key] = '7'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[4096, 2048])
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)

        def fake_resizable(options, current_sizes, new_sizes, dg_data, delete_sparse=False):
            new_sizes[constants._data_dg_rawname] = 5120
            new_sizes[constants._reco_dg_rawname] = 2560
            dg_data[constants._sparse_dg_rawname] = 'SPRC1'
            dg_data['cell_count'] = 4
            return 0

        manager.mCheckIfDgsResizable = MagicMock(side_effect=fake_resizable)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        manager.mResizeDgAndGriddisks = MagicMock(side_effect=[0, 0])
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mRollback = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aShrinkExistingDgs=True)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data[constants._diskgroupname_key], 'SPRC1')
        self.assertEqual(diskgroup_data[constants._rebalancepower_key], '7')
        self.assertEqual(diskgroup_data[constants._diskgrouptype_key], constants._sparse_dg_type_str)
        self.assertEqual(diskgroup_data['cell_count'], 4)
        manager.mCheckIfDgsResizable.assert_called_once()
        manager.mUpdateDgrpData.assert_called_once_with(options, diskgroup_data, 'DATAC1', 4096)
        manager.mResizeDgAndGriddisks.assert_has_calls([
            mock.call(options, 'DATAC1', 5120, 4096, rollback_stack, diskgroup_data),
            mock.call(options, 'RECOC1', 2560, 2048, rollback_stack, diskgroup_data)
        ])
        manager.mCreateSparseGriddisks.assert_called_once_with(options, diskgroup_data)
        manager.mCreateSparseDg.assert_called_once_with(
            options,
            {
                constants._data_dg_rawname: 5120,
                constants._reco_dg_rawname: 2560
            },
            diskgroup_data
        )
        manager.mEnsureDgsRebalanced.assert_called_once_with(options, 'SPRC1', diskgroup_data)
        manager.mRollback.assert_not_called()
        mock_log_error.assert_not_called()
        mock_log_info.assert_any_call("*** mClusterDgrpCreate: DG List : dg_data dg_reco dg_sparse")

# Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_sparse_skip_resize_updates_status(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = manager.mGetDiskGroupOperationData()

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco']

        data_dg = MagicMock()
        data_dg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_dg.mGetDgName.return_value = 'DATAC2'
        data_dg.mGetDgRedundancy.return_value = 'HIGH'

        reco_dg = MagicMock()
        reco_dg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        reco_dg.mGetDgName.return_value = 'RECOC2'

        storage = MagicMock()
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: {
            'dg_data': data_dg,
            'dg_reco': reco_dg
        }[dgid]

        ebox.mGetClusters.return_value = MagicMock(mGetCluster=MagicMock(return_value=cluster))
        ebox.mGetStorage.return_value = storage
        ebox.mUpdateStatusOEDA = MagicMock()

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = constants._sparse_dg_type_str
            req_params[constants._diskgroupname_key] = ''
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)

        def fake_calc(opts, data, sizes, use_default):
            data['datadg_new_size'] = 20480
            data['recodg_new_size'] = 10240
            data['sparsedg_new_size'] = 5120
            return 0

        manager.mCalculateNewDgSizes = MagicMock(side_effect=fake_calc)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=lambda opts, name, consts: {
            'DATAC2': 24576,
            'RECOC2': 12288
        }[name])

        def fake_resizable(opts, current_sizes, new_sizes, dg_data, delete_sparse=False):
            new_sizes[constants._data_dg_rawname] = 20480
            new_sizes[constants._reco_dg_rawname] = 10240
            dg_data[constants._sparse_dg_rawname] = 'SPRC2'
            dg_data['sparse_size'] = 5120
            return 0

        manager.mCheckIfDgsResizable = MagicMock(side_effect=fake_resizable)

        def fake_update(opts, data, dg_name, cur_size, delete_sparse=False):
            data['griddisk_count'] = 6
            data['cell_count'] = 3
            data['sparse_slice_size'] = 512
            return 0

        manager.mUpdateDgrpData = MagicMock(side_effect=fake_update)
        manager.mResizeDgAndGriddisks = MagicMock()
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mRollback = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aShrinkExistingDgs=False)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data[constants._diskgroupname_key], 'SPRC2')
        self.assertEqual(manager.mResizeDgAndGriddisks.call_count, 0)
        manager.mCreateSparseGriddisks.assert_called_once_with(options, diskgroup_data)
        manager.mCreateSparseDg.assert_called_once()
        manager.mEnsureDgsRebalanced.assert_called_once_with(options, 'SPRC2', diskgroup_data)
        manager.mRollback.assert_not_called()
        ebox.mUpdateStatusOEDA.assert_any_call(True, 'Complete', mock.ANY, 'Diskgroup Create Completed')

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_sparse_duplicate_detects_existing(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=['marker'])
        manager.mGetEbox = MagicMock(return_value=ebox)

        data_dg = MagicMock()
        data_dg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_dg.mGetDgName.return_value = 'DATAC1'
        data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        reco_dg = MagicMock()
        reco_dg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        reco_dg.mGetDgName.return_value = 'RECOC1'

        sparse_dg = MagicMock()
        sparse_dg.mGetDiskGroupType.return_value = constants._sparse_dg_type_str
        sparse_dg.mGetDgName.return_value = 'SPRC1'

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco', 'dg_sparse']

        storage = MagicMock()
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: {
            'dg_data': data_dg,
            'dg_reco': reco_dg,
            'dg_sparse': sparse_dg
        }[dgid]

        ebox.mGetClusters.return_value = MagicMock(mGetCluster=MagicMock(return_value=cluster))
        ebox.mGetStorage.return_value = storage

        manager.mClusterParseInput = MagicMock(side_effect=lambda opts, req_params, op_data=None: req_params.update({
            constants._diskgrouptype_key: constants._sparse_dg_type_str,
            constants._diskgroupname_key: ''
        }) or 0)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mRecordError = MagicMock(return_value='duplicate-error')

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, 'duplicate-error')
        self.assertEqual(diskgroup_data[constants._diskgroupname_key], 'SPRC1')
        manager.mRecordError.assert_called_once_with(
            gDiskgroupError['DgAlreadyExists'],
            'The diskgroup %s already exists' % constants._sparse_dg_type_str
        )

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_second_resize_failure_returns_error(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}
        rollback_stack = []

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=rollback_stack)
        manager.mGetEbox = MagicMock(return_value=ebox)

        data_dg = MagicMock()
        data_dg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_dg.mGetDgName.return_value = 'DATAC1'
        data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        reco_dg = MagicMock()
        reco_dg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        reco_dg.mGetDgName.return_value = 'RECOC1'

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco']

        storage = MagicMock()
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: {
            'dg_data': data_dg,
            'dg_reco': reco_dg
        }[dgid]

        ebox.mGetClusters.return_value = MagicMock(mGetCluster=MagicMock(return_value=cluster))
        ebox.mGetStorage.return_value = storage

        manager.mClusterParseInput = MagicMock(side_effect=lambda opts, req_params, op_data=None: req_params.update({
            constants._diskgrouptype_key: constants._sparse_dg_type_str,
            constants._diskgroupname_key: ''
        }) or 0)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[4096, 2048])

        def fake_resizable(opts, current_sizes, new_sizes, dg_data, delete_sparse=False):
            new_sizes[constants._data_dg_rawname] = 5120
            new_sizes[constants._reco_dg_rawname] = 2560
            dg_data[constants._sparse_dg_rawname] = 'SPRC1'
            return 0

        manager.mCheckIfDgsResizable = MagicMock(side_effect=fake_resizable)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        manager.mResizeDgAndGriddisks = MagicMock(side_effect=[0, 27])
        manager.mRollback = MagicMock()

        rc = manager.mClusterDgrpCreate(options)

        self.assertEqual(rc, 27)
        manager.mResizeDgAndGriddisks.assert_has_calls([
            mock.call(options, 'DATAC1', 5120, 4096, rollback_stack, diskgroup_data),
            mock.call(options, 'RECOC1', 2560, 2048, rollback_stack, diskgroup_data)
        ])
        manager.mUpdateDgrpData.assert_called_once_with(options, diskgroup_data, 'DATAC1', 4096)
        manager.mRollback.assert_not_called()
        manager.mCreateSparseGriddisks.assert_not_called()
        manager.mEnsureDgsRebalanced.assert_not_called()

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_skip_resize_successful_completion(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}
        rollback_stack = []

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=rollback_stack)
        manager.mGetEbox = MagicMock(return_value=ebox)

        data_dg = MagicMock()
        data_dg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_dg.mGetDgName.return_value = 'DATAC9'
        data_dg.mGetDgRedundancy.return_value = 'HIGH'

        reco_dg = MagicMock()
        reco_dg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        reco_dg.mGetDgName.return_value = 'RECOC9'

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco']

        storage = MagicMock()
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: {
            'dg_data': data_dg,
            'dg_reco': reco_dg
        }[dgid]

        ebox.mGetClusters.return_value = MagicMock(mGetCluster=MagicMock(return_value=cluster))
        ebox.mGetStorage.return_value = storage
        ebox.mUpdateStatusOEDA = MagicMock()

        manager.mClusterParseInput = MagicMock(side_effect=lambda opts, req_params, op_data=None: req_params.update({
            constants._diskgrouptype_key: constants._sparse_dg_type_str,
            constants._diskgroupname_key: ''
        }) or 0)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[6144, 3072])

        def fake_resizable(opts, current_sizes, new_sizes, dg_data, delete_sparse=False):
            new_sizes[constants._data_dg_rawname] = 8192
            new_sizes[constants._reco_dg_rawname] = 4096
            dg_data[constants._sparse_dg_rawname] = 'SPRC9'
            dg_data['cell_count'] = 6
            return 0

        manager.mCheckIfDgsResizable = MagicMock(side_effect=fake_resizable)
        manager.mUpdateDgrpData = MagicMock(return_value=0)
        manager.mResizeDgAndGriddisks = MagicMock()
        manager.mCreateSparseGriddisks = MagicMock(return_value=0)
        manager.mCreateSparseDg = MagicMock(return_value=0)
        manager.mEnsureDgsRebalanced = MagicMock(return_value=0)
        manager.mRollback = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aShrinkExistingDgs=False)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data[constants._diskgroupname_key], 'SPRC9')
        manager.mResizeDgAndGriddisks.assert_not_called()
        manager.mCreateSparseGriddisks.assert_called_once_with(options, diskgroup_data)
        manager.mCreateSparseDg.assert_called_once_with(
            options,
            {
                constants._data_dg_rawname: 8192,
                constants._reco_dg_rawname: 4096
            },
            diskgroup_data
        )
        manager.mEnsureDgsRebalanced.assert_called_once_with(options, 'SPRC9', diskgroup_data)
        ebox.mUpdateStatusOEDA.assert_any_call(True, 'Complete', mock.ANY, 'Completed creating sparse diskgroup')
        ebox.mUpdateStatusOEDA.assert_any_call(True, 'Complete', mock.ANY, 'Diskgroup Create Completed')

    # Auto-generated test for mClusterDgrpCreate
    @patch('exabox.ovm.cludiskgroups.ebLogError')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterDgrpCreate_precheck_only_unsupported_type(self, mock_get_gcontext, mock_ebCluDbaas, mock_log_error):
        manager, ebox, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()
        diskgroup_data = {}

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mGetRollbackStack = MagicMock(return_value=['marker'])
        manager.mGetEbox = MagicMock(return_value=ebox)

        data_dg = MagicMock()
        data_dg.mGetDiskGroupType.return_value = constants._data_dg_type_str
        data_dg.mGetDgName.return_value = 'DATAC2'
        data_dg.mGetDgRedundancy.return_value = 'NORMAL'

        reco_dg = MagicMock()
        reco_dg.mGetDiskGroupType.return_value = constants._reco_dg_type_str
        reco_dg.mGetDgName.return_value = 'RECOC2'

        cluster = MagicMock()
        cluster.mGetCluDiskGroups.return_value = ['dg_data', 'dg_reco']

        storage = MagicMock()
        storage.mGetDiskGroupConfig.side_effect = lambda dgid: {
            'dg_data': data_dg,
            'dg_reco': reco_dg
        }[dgid]

        ebox.mGetClusters.return_value = MagicMock(mGetCluster=MagicMock(return_value=cluster))
        ebox.mGetStorage.return_value = storage

        def fake_parse(opts, req_params, op_data=None):
            req_params[constants._diskgrouptype_key] = 'external'
            req_params[constants._diskgroupname_key] = 'EXT1'
            return 0

        manager.mClusterParseInput = MagicMock(side_effect=fake_parse)
        manager.mCheckDgExist = MagicMock(return_value=False)
        manager.mCalculateNewDgSizes = MagicMock(return_value=0)
        manager.mUtilGetDiskgroupSize = MagicMock(side_effect=[2048, 1024])
        manager.mCheckIfDgsResizable = MagicMock()

        rc = manager.mClusterDgrpCreate(options, aResizablePrecheckOnly=True)

        self.assertEqual(rc, 0)
        self.assertEqual(diskgroup_data[constants._diskgroupname_key], 'EXT1')
        mock_log_error.assert_called_with("*** Diskgroup type external currently unsupported for Precheck")
        manager.mCheckIfDgsResizable.assert_not_called()

    # Auto-generated test for mResizeDgAndGriddisks
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mResizeDgAndGriddisks_shrink_success_runs_both_steps(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        diskgroup_data = {'dg': 'DATAC1'}
        rollback_stack = []

        manager.mResizeDg = MagicMock(return_value=0)
        manager.mResizeGriddisks = MagicMock(return_value=0)
        manager.mRollback = MagicMock()

        rc = manager.mResizeDgAndGriddisks(options, 'DATAC1', 4096, 8192, rollback_stack, diskgroup_data)

        self.assertEqual(rc, 0)
        manager.mResizeDg.assert_called_once_with(options, 'DATAC1', 4096, diskgroup_data, False)
        manager.mResizeGriddisks.assert_called_once_with(options, 'DATAC1', 4096, diskgroup_data)
        self.assertEqual(len(rollback_stack), 2)
        first_entry = rollback_stack[0]
        second_entry = rollback_stack[1]
        self.assertIn(manager.mResizeDg, first_entry)
        self.assertEqual(first_entry[manager.mResizeDg], (options, 'DATAC1', 8192, diskgroup_data, False))
        self.assertIn(manager.mResizeGriddisks, second_entry)
        self.assertEqual(second_entry[manager.mResizeGriddisks], (options, 'DATAC1', 8192, diskgroup_data))
        manager.mRollback.assert_not_called()

    # Auto-generated test for mResizeDgAndGriddisks
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mResizeDgAndGriddisks_growth_failure_triggers_rollback(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        diskgroup_data = {'dg': 'DATAC2'}
        rollback_stack = []

        manager.mGetDiskGroupOperationData = MagicMock(return_value=diskgroup_data)
        manager.mResizeGriddisks = MagicMock(side_effect=[7])
        manager.mResizeDg = MagicMock()
        manager.mRollback = MagicMock(return_value=0)

        rc = manager.mResizeDgAndGriddisks(options, 'DATAC2', 12288, 8192, rollback_stack)

        self.assertEqual(rc, 7)
        manager.mGetDiskGroupOperationData.assert_called_once()
        manager.mResizeGriddisks.assert_called_once_with(options, 'DATAC2', 12288, diskgroup_data)
        manager.mResizeDg.assert_not_called()
        self.assertEqual(len(rollback_stack), 1)
        self.assertIn(manager.mResizeGriddisks, rollback_stack[0])
        self.assertEqual(rollback_stack[0][manager.mResizeGriddisks], (options, 'DATAC2', 8192, diskgroup_data))
        manager.mRollback.assert_called_once_with(rollback_stack)

    # Auto-generated test for mResizeDgAndGriddisks
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mResizeDgAndGriddisks_equal_sizes_skip_operations(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        diskgroup_data = {'dg': 'DATAC3'}
        rollback_stack = []

        manager.mResizeDg = MagicMock()
        manager.mResizeGriddisks = MagicMock()
        manager.mRollback = MagicMock()

        rc = manager.mResizeDgAndGriddisks(options, 'DATAC3', 16384, 16384, rollback_stack, diskgroup_data)

        self.assertEqual(rc, 0)
        manager.mResizeDg.assert_not_called()
        manager.mResizeGriddisks.assert_not_called()
        manager.mRollback.assert_not_called()
        self.assertEqual(rollback_stack, [])

# Auto-generated test for mClusterParseInput
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    def test_mClusterParseInput_sanitize_diskgroup_name_from_string(self, mock_get_gcontext, mock_ebCluDbaas):
        manager, _, _, options = self._create_manager_with_stubs(mock_get_gcontext, mock_ebCluDbaas)
        constants = manager.mGetConstantsObj()

        payload = {
            'Command': 'dg_create',
            'diskgroup_type': 'sparse',
            'diskgroup': 'SPRC1'
        }
        options.jsonconf = {'diskgroupgrouplist': payload}

        req_params = {}

        rc = manager.mClusterParseInput(options, req_params)

        self.assertEqual(rc, 0)
        self.assertEqual(req_params[constants._diskgroupname_key], 'SPRC1')

    # Auto-generated test for mUpdateRebalanceStatus
    @patch('exabox.ovm.cludiskgroups.time.sleep')
    @patch('exabox.ovm.cludiskgroups.time.time')
    @patch('exabox.ovm.cludiskgroups.exaBoxNode')
    @patch('exabox.ovm.cludiskgroups.get_gcontext')
    @patch('exabox.ovm.cludiskgroups.ebCluDbaas')
    def test_mUpdateRebalanceStatus_reads_multiple_groups(self, mock_ebCluDbaas, mock_get_gcontext,
                                                          mock_exaBoxNode, mock_time, mock_sleep):
        manager, _, dbaas_obj, options = self._create_manager_with_stubs(
            mock_get_gcontext, mock_ebCluDbaas, extra_traces=True
        )

        constants = manager.mGetConstantsObj()
        manager.mSetDomUs(['domu1'])
        manager.mClusterDgrpInfo2 = MagicMock(return_value=0)
        manager.mCheckDgPropertyInDbaasOutJson = MagicMock(return_value=0)
        manager.mSetLastDomUused('domu1')
        manager.mSetOutJson('/tmp/out.json')

        dbaas_obj.mReadStatusFromDomU.return_value = {
            'DG_DATA': {
                constants._propkey_rebstat: {
                    constants._rebstatprop_status: 'INCOMPLETE'
                }
            }
        }

        state_stream = MagicMock()
        state_stream.readlines.return_value = [
            '1 RUN 5 10 20 10\n',
            '2 RUN 1 15 10 20\n'
        ]
        state_node = MagicMock()
        state_node.mExecuteCmd.return_value = (None, state_stream, None)

        name_stream_1 = MagicMock()
        name_stream_1.readlines.return_value = [' 1 DATAC1\n']
        name_node_1 = MagicMock()
        name_node_1.mExecuteCmd.return_value = (None, name_stream_1, None)

        name_stream_2 = MagicMock()
        name_stream_2.readlines.return_value = [' 2 RECOC1\n']
        name_node_2 = MagicMock()
        name_node_2.mExecuteCmd.return_value = (None, name_stream_2, None)

        ctx_state = MagicMock()
        ctx_state.__enter__.return_value = state_node
        ctx_state.__exit__.return_value = False

        ctx_name_1 = MagicMock()
        ctx_name_1.__enter__.return_value = name_node_1
        ctx_name_1.__exit__.return_value = False

        ctx_name_2 = MagicMock()
        ctx_name_2.__enter__.return_value = name_node_2
        ctx_name_2.__exit__.return_value = False

        connect_side_effect = [ctx_state, ctx_name_1, ctx_name_2]

        with patch('exabox.ovm.cludiskgroups.connect_to_host', side_effect=connect_side_effect) as mock_connect:
            with patch('exabox.ovm.cludiskgroups.ebCluUtils') as mock_utils:
                utils_instance = MagicMock()
                utils_instance.mIsNumber.return_value = True
                mock_utils.return_value = utils_instance
                mock_time.side_effect = itertools.repeat(1700)
                manager.mCalcOverallRebalPercent = MagicMock(return_value=42)

                returned = manager.mUpdateRebalanceStatus('domu1', 'cmd_run {0}', 'cmd_name {0}', 1000, 300, constants)

        self.assertEqual(returned, 1600)
        self.assertEqual(mock_connect.call_count, 3)
        self.assertEqual(dbaas_obj._mUpdateRequestData.call_count, 1)
        manager.mCalcOverallRebalPercent.assert_called_once_with(constants)
