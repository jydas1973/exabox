#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_mCheckCellConfig.py /main/1 2024/03/12 21:20:02 jfsaldan Exp $
#
# tests_mCheckCellConfig.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_mCheckCellConfig.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    05/12/26 - Add critical CELL alert precheck tests
#    jfsaldan    03/07/24 - Bug 36350280 - EXACC: CREATE CLUSTER DROPS FLASHLOG
#                           AND FLASHCACHE BEFORE CALLING OEDA CREATE CELLDISKS
#    jfsaldan    03/07/24 - Creation
#

import unittest
from unittest.mock import Mock, patch
from unittest.mock import MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogTrace
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.csstep.cs_createstorage import csCreateStorage


class ebTestCheckCellConfig(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None


    def test_mCheckCellConfig_mvm(self):
        """
        In MVM we don't even need to declare examock commands
        because we expect the method to return False
        in MVM
        """
        _ebox = self.mGetClubox()
        _ebox.mSetSharedEnv(True)

        self.assertEqual(False, _ebox.mCheckCellConfig(_ebox.mGetArgsOptions()))

    def test_mCheckCellConfig_mvm_does_not_run_critical_alert_precheck(self):
        """
        mCheckCellConfig keeps the MVM fast return contract. The critical
        alert precheck is invoked by the create storage step, not by this
        generic cell configuration check.
        """
        _ebox = self.mGetClubox()
        _ebox.mSetSharedEnv(True)

        with patch('exabox.ovm.clumisc.ebCluPreChecks.mCheckCellCriticalHardwareAlerts',
                   side_effect=Exception('unexpected alert precheck')) as _precheck:
            self.assertEqual(False, _ebox.mCheckCellConfig(_ebox.mGetArgsOptions()))
            _precheck.assert_not_called()

    @patch('exabox.ovm.clumisc.mGetAlertHistoryOptions', return_value='')
    @patch('exabox.ovm.clumisc.node_cmd_abs_path_check', return_value='/resolved/cellcli')
    @patch('exabox.ovm.clumisc.node_exec_cmd')
    @patch('exabox.ovm.clumisc.connect_to_host')
    def test_mCheckCellCriticalHardwareAlerts_raises_on_critical_alert_history(
            self, aMockConnectToHost, aMockNodeExecCmd, aMockCellcliPath,
            aMockAlertOptions):
        _ebox = self.mGetClubox()
        _ebox.mReturnCellNodes = Mock(return_value={'cell01.example.com': None})
        _prechecks = ebCluPreChecks(_ebox)

        _node = MagicMock()
        aMockConnectToHost.return_value.__enter__.return_value = _node
        aMockConnectToHost.return_value.__exit__.return_value = False
        aMockNodeExecCmd.return_value = MagicMock(
            exit_code=0,
            stdout='Critical hardware alert\n',
            stderr='')

        with self.assertRaises(ExacloudRuntimeError):
            _prechecks.mCheckCellCriticalHardwareAlerts()

        aMockConnectToHost.assert_called_once()
        self.assertEqual('cell01.example.com', aMockConnectToHost.call_args[0][0])
        aMockConnectToHost.return_value.__enter__.assert_called_once()
        aMockConnectToHost.return_value.__exit__.assert_called_once()
        aMockAlertOptions.assert_called_once_with(_ebox, 'cell01.example.com')
        aMockCellcliPath.assert_called_once_with(_node, 'cellcli')
        aMockNodeExecCmd.assert_called_once_with(
            _node,
            "/resolved/cellcli -e 'list alerthistory where endTime=null AND alertType=stateful "
            "AND alertShortName=Hardware AND severity=critical'",
            timeout=180)
        _node.mExecuteCmd.assert_not_called()
        _node.mExecuteCmdCellcli.assert_not_called()

    @patch('exabox.ovm.clumisc.mGetAlertHistoryOptions', return_value='')
    @patch('exabox.ovm.clumisc.node_cmd_abs_path_check', return_value='/resolved/cellcli')
    @patch('exabox.ovm.clumisc.node_exec_cmd')
    @patch('exabox.ovm.clumisc.connect_to_host')
    def test_mCheckCellCriticalHardwareAlerts_does_not_raise_when_query_fails(
            self, aMockConnectToHost, aMockNodeExecCmd, aMockCellcliPath,
            aMockAlertOptions):
        _ebox = self.mGetClubox()
        _ebox.mReturnCellNodes = Mock(return_value={'cell01.example.com': None})
        _prechecks = ebCluPreChecks(_ebox)

        _node = MagicMock()
        aMockConnectToHost.return_value.__enter__.return_value = _node
        aMockConnectToHost.return_value.__exit__.return_value = False
        aMockNodeExecCmd.return_value = MagicMock(
            exit_code=1,
            stdout='',
            stderr='timed out')

        _prechecks.mCheckCellCriticalHardwareAlerts()

        aMockAlertOptions.assert_called_once_with(_ebox, 'cell01.example.com')
        aMockCellcliPath.assert_called_once_with(_node, 'cellcli')
        aMockNodeExecCmd.assert_called_once_with(
            _node,
            "/resolved/cellcli -e 'list alerthistory where endTime=null AND alertType=stateful "
            "AND alertShortName=Hardware AND severity=critical'",
            timeout=180)
        _node.mExecuteCmd.assert_not_called()
        _node.mExecuteCmdCellcli.assert_not_called()

    @patch('exabox.ovm.clumisc.mGetAlertHistoryOptions',
           return_value='-privilege cloud_role')
    @patch('exabox.ovm.clumisc.node_cmd_abs_path_check', return_value='/resolved/cellcli')
    @patch('exabox.ovm.clumisc.node_exec_cmd')
    @patch('exabox.ovm.clumisc.connect_to_host')
    def test_mCheckCellCriticalHardwareAlerts_uses_alert_history_options(
            self, aMockConnectToHost, aMockNodeExecCmd, aMockCellcliPath,
            aMockAlertOptions):
        _ebox = self.mGetClubox()
        _ebox.mReturnCellNodes = Mock(return_value={'cell01.example.com': None})
        _prechecks = ebCluPreChecks(_ebox)

        _node = MagicMock()
        aMockConnectToHost.return_value.__enter__.return_value = _node
        aMockConnectToHost.return_value.__exit__.return_value = False
        aMockNodeExecCmd.return_value = MagicMock(
            exit_code=0,
            stdout='',
            stderr='')

        _prechecks.mCheckCellCriticalHardwareAlerts()

        aMockAlertOptions.assert_called_once_with(_ebox, 'cell01.example.com')
        aMockCellcliPath.assert_called_once_with(_node, 'cellcli')
        aMockNodeExecCmd.assert_called_once_with(
            _node,
            "/resolved/cellcli -privilege cloud_role -e 'list alerthistory where endTime=null "
            "AND alertType=stateful AND alertShortName=Hardware AND severity=critical'",
            timeout=180)
        _node.mExecuteCmd.assert_not_called()
        _node.mExecuteCmdCellcli.assert_not_called()

    @patch('exabox.ovm.csstep.cs_createstorage.ebCluPreChecks')
    @patch('exabox.ovm.csstep.cs_createstorage.ebCluUtils')
    @patch('exabox.ovm.csstep.cs_createstorage.csUtil')
    def test_create_storage_runs_critical_alert_precheck_before_cell_config(
            self, aMockCsUtil, aMockCluUtils, aMockPreChecks):
        _constants = MagicMock()
        _constants.OSTP_SETUP_CELL = 'setup_cell'
        _constants.OSTP_CREATE_CELL = 'create_cell'
        _constants.OSTP_CREATE_GDISK = 'create_gdisk'

        _csu = MagicMock()
        _csu.mGetConstants.return_value = _constants
        aMockCsUtil.return_value = _csu

        _clu_utils = MagicMock()
        aMockCluUtils.return_value = _clu_utils

        _ebox = MagicMock()
        _ebox.IsZdlraProv.return_value = False
        _ebox.mCheckConfigOption.side_effect = lambda aOption, aValue=None: {
            'delete_cloud_user': False,
            'skip_cell_create': False,
            'force_cell_config': False,
        }.get(aOption, aValue)
        _ebox.mCheckCellConfig.return_value = False

        _call_order = []
        _prechecks = MagicMock()
        aMockPreChecks.return_value = _prechecks
        _prechecks.mCheckCellCriticalHardwareAlerts.side_effect = lambda: _call_order.append('critical_alert_precheck')
        _ebox.mCheckCellConfig.side_effect = lambda *args, **kwargs: _call_order.append('cell_config') or False

        _handler = csCreateStorage()
        _handler.mParallelValidateGriddisks = Mock()
        _handler.doExecute(_ebox, MagicMock(), ['ESTP_CREATE_STORAGE'])

        self.assertEqual(['critical_alert_precheck', 'cell_config'], _call_order)
        aMockPreChecks.assert_called_once_with(_ebox)
        _prechecks.mCheckCellCriticalHardwareAlerts.assert_called_once()
        _ebox.mCheckCellConfig.assert_called_once()
        _csu.mExecuteOEDAStep.assert_any_call(
            _ebox, 'ESTP_CREATE_STORAGE', ['ESTP_CREATE_STORAGE'],
            aOedaStep=_constants.OSTP_CREATE_CELL)


if __name__ == '__main__':
    unittest.main()
