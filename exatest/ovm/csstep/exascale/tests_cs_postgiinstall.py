#!/bin/python
#
# $Header: tests_cs_postgiinstall.py 03-mar-2026.08:28:56 pbellary Exp $
#
# tests_cs_postgiinstall.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_postgiinstall.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    03/03/26 - Creation
#

import os
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

_THIS_DIR = os.path.dirname(__file__)
_VIEW_ROOT = os.environ.get('ADE_VIEW_ROOT')
if _VIEW_ROOT and _VIEW_ROOT not in sys.path:
    sys.path.insert(0, _VIEW_ROOT)

_parents = list(Path(_THIS_DIR).resolve().parents)
if _parents:
    _fallback_root = str(_parents[min(7, len(_parents) - 1)])
    if _fallback_root not in sys.path:
        sys.path.insert(0, _fallback_root)


def _ensure_module(module_name):
    module = sys.modules.get(module_name)
    if module is None:
        module = types.ModuleType(module_name)
        sys.modules[module_name] = module
        if '.' in module_name:
            parent_name, attr_name = module_name.rsplit('.', 1)
            parent_module = _ensure_module(parent_name)
            setattr(parent_module, attr_name, module)
    return module


_cs_base_module = _ensure_module('exabox.ovm.csstep.cs_base')
_cs_util_module = _ensure_module('exabox.ovm.csstep.cs_util')
_log_module = _ensure_module('exabox.log.LogMgr')

if not hasattr(_cs_base_module, 'CSBase'):
    class _DummyCSBase(object):
        pass
    _cs_base_module.CSBase = _DummyCSBase

if not hasattr(_cs_util_module, 'csUtil'):
    _cs_util_module.csUtil = lambda *args, **kwargs: None

for _log_func in ['ebLogInfo', 'ebLogTrace', 'ebLogError']:
    if not hasattr(_log_module, _log_func):
        setattr(_log_module, _log_func, lambda *args, **kwargs: None)

from ecs.exacloud.exabox.ovm.csstep.exascale.cs_postgiinstall import csPostGIInstall


def _build_ebox():
    ebox = mock.Mock()
    ebox.mUpdateStatus = mock.Mock()
    ebox.mUpdateStatusCS = mock.Mock()
    ebox.mExtraRPMsConfig = mock.Mock()
    ebox.mSetupBDCSTree = mock.Mock()
    ebox.mLogStepElapsedTime = mock.Mock()
    ebox.mRunScript = mock.Mock()
    ebox.mIsExabm = mock.Mock(return_value=False)
    ebox.mHardenOCISecurity = mock.Mock()
    ebox.mSecureSSHCiphers = mock.Mock()
    ebox.mIsFedramp = mock.Mock(return_value=False)
    ebox.mFedrampConfig = mock.Mock()
    ebox.isATP = mock.Mock(return_value=False)
    ebox.mDisableQoSM = mock.Mock()
    ebox.mDisablePasswordExpiration = mock.Mock()
    ebox.mIsDisableDom0CellLockdown = mock.Mock(return_value=False)
    ebox.mSetupLockdown = mock.Mock()
    ebox.mRemoveRspFiles = mock.Mock()
    ebox.mIsOciEXACC = mock.Mock(return_value=False)
    ebox.mRestartDnsmasq = mock.Mock()
    ebox.mAcquireRemoteLock = mock.Mock()
    ebox.mReleaseRemoteLock = mock.Mock()
    ebox.mGetCmd = mock.Mock(return_value='createservice')
    ebox.mReturnDom0DomUPair = mock.Mock(return_value=[])
    ebox.mRemoveDNS = mock.Mock()
    return ebox


class csPostGIInstallTests(unittest.TestCase):

    def setUp(self):
        cs_util_patch = mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postgiinstall.csUtil')
        self.addCleanup(cs_util_patch.stop)
        self._mock_cs_util = cs_util_patch.start()
        self._mock_cs_util.return_value.mRemoveDeprecatedSshAlgorithms = mock.Mock()

    def test_doexecute_runs_core_sequence(self):
        step = csPostGIInstall()
        ebox = _build_ebox()
        options = {'config': 'value'}
        steplist = ['step1']

        step.doExecute(ebox, options, steplist)

        ebox.mUpdateStatus.assert_called_once_with('createservice step ' + step.step)
        ebox.mUpdateStatusCS.assert_any_call(True, step.step, steplist, aComment='Running Extra RPMS and Config')
        ebox.mExtraRPMsConfig.assert_called_once_with(options)
        ebox.mSetupBDCSTree.assert_called_once()
        ebox.mRunScript.assert_any_call(aType='*', aWhen='post.gi_install')
        ebox.mSecureSSHCiphers.assert_called_once()
        ebox.mDisablePasswordExpiration.assert_called_once()
        ebox.mSetupLockdown.assert_called_once()
        ebox.mRemoveRspFiles.assert_called_once()
        ebox.mDisableQoSM.assert_not_called()
        ebox.mRestartDnsmasq.assert_not_called()

    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postgiinstall.ebLogInfo')
    def test_doexecute_handles_optional_branches(self, mock_log_info):
        step = csPostGIInstall()
        ebox = _build_ebox()
        ebox.mIsExabm.return_value = True
        ebox.mIsFedramp.return_value = True
        ebox.isATP.return_value = True
        ebox.mIsOciEXACC.return_value = True
        ebox.mIsDisableDom0CellLockdown.return_value = True

        step.doExecute(ebox, {}, ['step'])

        ebox.mHardenOCISecurity.assert_called_once()
        ebox.mFedrampConfig.assert_called_once()
        ebox.mDisableQoSM.assert_called_once()
        ebox.mDisablePasswordExpiration.assert_called_once()
        ebox.mRestartDnsmasq.assert_called_once()
        ebox.mSetupLockdown.assert_not_called()
        mock_log_info.assert_any_call('*** Skipping Dom0 Lockdown')

    def test_undoexecute_runs_cleanup_and_calls_remove_dns(self):
        step = csPostGIInstall()
        ebox = _build_ebox()
        ebox.mGetCmd.return_value = 'gi_delete'
        ebox.mIsExabm.return_value = True

        step.undoExecute(ebox, {'payload': 'value'}, ['undo_step'])

        ebox.mUpdateStatus.assert_called_once_with('csPostGIInstall step ' + step.step)
        ebox.mRunScript.assert_any_call(aType='*', aWhen='pre.gi_delete')
        ebox.mRunScript.assert_any_call(aType='*', aWhen='post.gi_delete')
        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()
        ebox.mRemoveDNS.assert_called_once()
        ebox.mExtraRPMsConfig.assert_called_with({'payload': 'value'}, aUndo=True)


if __name__ == '__main__':
    unittest.main()
