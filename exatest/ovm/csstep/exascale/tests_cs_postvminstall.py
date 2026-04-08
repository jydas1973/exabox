#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_cs_postvminstall.py /main/1 2026/01/09 13:46:38 pbellary Exp $
#
# tests_cs_postvminstall.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_postvminstall.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    01/06/26 - Codex UT enhancement
#    pbellary    01/06/26 - Creation

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


# Ensure external dependencies exist so cs_postvminstall import succeeds during tests
_ctx_module = _ensure_module('exabox.core.Context')
_cs_base_module = _ensure_module('exabox.ovm.csstep.cs_base')
_cs_util_module = _ensure_module('exabox.ovm.csstep.cs_util')
_utils_node_module = _ensure_module('exabox.utils.node')
_cluexaccib_module = _ensure_module('exabox.ovm.cluexaccib')
_error_module = _ensure_module('exabox.core.Error')
_log_module = _ensure_module('exabox.log.LogMgr')
_net_validation_module = _ensure_module('exabox.ovm.clunetworkvalidations')
_encryption_module = _ensure_module('exabox.ovm.cluencryption')
_userutils_module = _ensure_module('exabox.ovm.userutils')

if not hasattr(_ctx_module, 'get_gcontext'):
    _ctx_module.get_gcontext = lambda: mock.Mock()

if not hasattr(_cs_base_module, 'CSBase'):
    class _DummyCSBase(object):
        pass
    _cs_base_module.CSBase = _DummyCSBase

if not hasattr(_cs_util_module, 'csUtil'):
    _cs_util_module.csUtil = lambda *args, **kwargs: None

if not hasattr(_utils_node_module, 'connect_to_host'):
    _utils_node_module.connect_to_host = lambda *args, **kwargs: mock.MagicMock()

if not hasattr(_cluexaccib_module, 'ExaCCIB_DomU'):
    class _DummyExaCCIBDomU(object):
        def __init__(self, *args, **kwargs):
            self.args = args

        def mSecureDomUIB(self):
            return None
    _cluexaccib_module.ExaCCIB_DomU = _DummyExaCCIBDomU

if not hasattr(_error_module, 'ebError'):
    class _DummyError(Exception):
        pass
    _error_module.ebError = _DummyError
    _error_module.ExacloudRuntimeError = _DummyError

for _log_func in ['ebLogError', 'ebLogInfo', 'ebLogWarn', 'ebLogCritical', 'ebLogTrace']:
    if not hasattr(_log_module, _log_func):
        setattr(_log_module, _log_func, lambda *args, **kwargs: None)

if not hasattr(_net_validation_module, 'ebNetworkValidations'):
    _net_validation_module.ebNetworkValidations = lambda *args, **kwargs: mock.MagicMock()

_encryption_defaults = {
    'isEncryptionRequested': False,
    'batchEncryptionSetupDomU': None,
    'exacc_fsencryption_requested': False,
    'mSetLuksChannelOnDom0Exacc': None,
    'validateMinImgEncryptionSupport': True,
    'setupU01EncryptedDiskParallel': None,
}


def _return_value_factory(value):
    def _return_value(*args, **kwargs):
        return value
    return _return_value


for _name, _default in _encryption_defaults.items():
    if not hasattr(_encryption_module, _name):
        setattr(_encryption_module, _name, _return_value_factory(_default))

if not hasattr(_userutils_module, 'ebUserUtils'):
    _userutils_module.ebUserUtils = types.SimpleNamespace(
        mPushSecscanKey=lambda *args, **kwargs: None,
        mAddSecscanSshd=lambda *args, **kwargs: None,
    )

from ecs.exacloud.exabox.ovm.csstep.exascale import cs_postvminstall as cs_postvminstall_module
from ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall import csPostVMInstall


def _make_remote_lock_mock():
    remote_lock = mock.MagicMock()
    remote_lock.set_lock_type = mock.Mock()
    remote_lock.return_value = remote_lock
    remote_lock.__enter__.return_value = None
    remote_lock.__exit__.return_value = None
    return remote_lock


def _build_base_ebox():
    ebox = mock.Mock()
    ebox.remote_lock = _make_remote_lock_mock()
    ebox.mUpdateStatus = mock.Mock()
    ebox.mSetupEbtablesOnDom0 = mock.Mock()
    ebox.mUpdateStatusCS = mock.Mock()
    ebox.mLogStepElapsedTime = mock.Mock()
    ebox.mAddEcraNatOnDomU = mock.Mock()
    ebox.mPostVMCreatePatching = mock.Mock()
    ebox.mDom0PostVMCreateNetConfig = mock.Mock()
    ebox.mPatchSSHDConfig = mock.Mock()
    ebox.mSaveClusterConfiguration = mock.Mock()
    ebox.mChangeMinFreeKb = mock.Mock()
    ebox.mRemoveExaCCMacrosVerify = mock.Mock()
    ebox.mSecureDOMUPwd = mock.Mock()
    ebox.mSecureDOMUSsh = mock.Mock()
    ebox.mATPSecureListeners = mock.Mock()
    ebox.mUpdateDBGIBPL = mock.Mock()
    ebox.mCopyFileToClusterConfiguration = mock.Mock()
    ebox.mRunScript = mock.Mock()
    ebox.mCheckCaviumInstanceDomUs = mock.Mock()
    ebox.mCreateNatIptablesRulesFile = mock.Mock()
    ebox.mGetOciExaCCServicesSetup = mock.Mock()
    ebox.mReturnDom0DomUPair.return_value = []
    ebox.mGetConfigPath.return_value = '/tmp/config'
    ebox.mResetClusterSSHKeys = mock.Mock()
    ebox.mCheckClientBackupIPSet = mock.Mock()
    ebox.mIsExabm = mock.Mock(return_value=False)
    ebox.isATP = mock.Mock(return_value=False)
    ebox.mIsOciEXACC = mock.Mock(return_value=False)
    ebox.mIsKVM = mock.Mock(return_value=False)
    ebox.mCheckConfigOption = mock.Mock(return_value=False)
    ebox.mGetCmd = mock.Mock(return_value='createservice')
    ebox.mVMImagesShredding = mock.Mock()
    ebox.isBM.return_value = False
    return ebox


class csPostVMInstallTests(unittest.TestCase):

    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    def test_doexecute_disables_ebtables_before_operations(self, mock_get_ctx):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()

        cs_step.doExecute(ebox, {}, [])

        ebox.mSetupEbtablesOnDom0.assert_called_once_with(aMode=False)

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.ebUserUtils.mAddSecscanSshd')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.ebUserUtils.mPushSecscanKey')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.ExaCCIB_DomU')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.exacc_fsencryption_requested', return_value=False)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=False)
    def test_doexecute_triggers_secscan_and_secures_ib_for_exacc(self, mock_is_enc, mock_exacc_enc,
            mock_get_ctx, mock_exacc_dom, mock_push_key, mock_add_sshd):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domua'), ('dom0b', 'domub')]
        ebox.mIsExabm.return_value = False
        ebox.isATP.return_value = True
        ebox.mIsOciEXACC.return_value = True
        ebox.mIsKVM.return_value = False
        ebox.mCheckConfigOption.return_value = False

        mock_dom_instance = mock.Mock()
        mock_exacc_dom.return_value = mock_dom_instance

        cs_step.doExecute(ebox, {}, [])

        mock_push_key.assert_called_once_with(ebox)
        mock_add_sshd.assert_called_once_with(ebox)
        mock_exacc_dom.assert_called_once_with(['domua', 'domub'])
        mock_dom_instance.mSecureDomUIB.assert_called_once()

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.ebLogWarn')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.exacc_fsencryption_requested', return_value=False)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=False)
    def test_doexecute_logs_warning_for_exacc_kvm(self, mock_is_enc, mock_exacc_enc, mock_get_ctx, mock_warn):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mIsExabm.return_value = False
        ebox.isATP.return_value = False
        ebox.mIsOciEXACC.return_value = True
        ebox.mIsKVM.return_value = True
        ebox.mCheckConfigOption.return_value = False

        cs_step.doExecute(ebox, {}, [])

        mock_warn.assert_called_once()

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.connect_to_host')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.exacc_fsencryption_requested', return_value=False)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=False)
    def test_doexecute_reconfigures_shared_rack_rules(self, mock_is_enc, mock_exacc_enc,
            mock_get_ctx, mock_connect):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        mock_node = mock.Mock()
        mock_node.mGetCmdExitStatus.return_value = 0
        mock_node.mExecuteCmd.side_effect = [('', '', ''), ('', '', '')]

        mock_connect_ctx = mock.MagicMock()
        mock_connect_ctx.__enter__.return_value = mock_node
        mock_connect_ctx.__exit__.return_value = None
        mock_connect.return_value = mock_connect_ctx

        ebox = _build_base_ebox()
        ebox.mReturnDom0DomUPair.return_value = [('dom0x', 'domux')]
        ebox.mIsExabm.return_value = True
        ebox.isATP.return_value = True
        ebox.mIsOciEXACC.return_value = False
        ebox.mIsKVM.return_value = False
        ebox.mCheckConfigOption.return_value = True
        ebox.mGetOciExaCCServicesSetup.return_value = {
            'forwardproxy': {'ip': '10.1.1.1', 'port': '8080'},
            'fileserver': {'ip': '10.2.2.2', 'port': '8443'},
        }

        cs_step.doExecute(ebox, {}, [])

        ebox.mCheckCaviumInstanceDomUs.assert_called_once()
        mock_connect.assert_called_once_with('dom0x', mock_ctx)
        mock_node.mCopyFile.assert_called_once_with(
            '/opt/oci/exacc/exacloud/scripts/network/vmrules_reconfig.py',
            '/tmp/vmrules_reconfig.py')
        chmod_call = mock.call('/bin/chmod +x /tmp/vmrules_reconfig.py')
        run_call = mock.call('/bin/python /tmp/vmrules_reconfig.py -n domux -fip 10.1.1.1 -pip 10.2.2.2 -fp 8080 -pp 8443')
        self.assertEqual(mock_node.mExecuteCmd.mock_calls, [chmod_call, run_call])

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.batchEncryptionSetupDomU')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=True)
    def test_doexecute_runs_non_kvm_encryption(self, mock_is_enc, mock_get_ctx, mock_batch):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mIsOciEXACC.return_value = False
        ebox.mIsKVM.return_value = False
        ebox.mReturnDom0DomUPair.return_value = [('dom0', 'domu')]

        cs_step.doExecute(ebox, {'payload': 'value'}, ['step'])

        mock_batch.assert_called_once_with(ebox, [('dom0', 'domu')], '/u01')
        ebox.mUpdateStatusCS.assert_any_call(True, cs_step.step, ['step'], aComment='Filesystem Encryption on /u01')
        ebox.mLogStepElapsedTime.assert_any_call(mock.ANY, 'Filesystem Encryption on /u01')

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.batchEncryptionSetupDomU')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=True)
    def test_doexecute_skips_non_kvm_encryption_for_exacc(self, mock_is_enc, mock_get_ctx, mock_batch):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mIsOciEXACC.return_value = True
        ebox.mIsKVM.return_value = False

        cs_step.doExecute(ebox, {}, ['step'])

        mock_batch.assert_not_called()
        batch_calls = [call for call in ebox.mUpdateStatusCS.mock_calls if 'Filesystem Encryption on /u01' in str(call)]
        self.assertEqual(batch_calls, [])

    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.setupU01EncryptedDiskParallel')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.mSetLuksChannelOnDom0Exacc')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.validateMinImgEncryptionSupport')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.exacc_fsencryption_requested', return_value=False)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=True)
    def test_doexecute_requires_kvm_encryption_flag(self, mock_is_enc, mock_exacc_enc, mock_get_ctx,
            mock_validate, mock_set_channel, mock_setup):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mIsKVM.return_value = True
        ebox.mIsOciEXACC.return_value = False
        ebox.mReturnDom0DomUPair.return_value = [('dom0', 'domu')]

        cs_step.doExecute(ebox, {}, ['step'])

        mock_validate.assert_not_called()
        mock_set_channel.assert_not_called()
        mock_setup.assert_not_called()
        encryption_calls = [call for call in ebox.mUpdateStatusCS.mock_calls
                            if 'KVM Filesystem Encryption on /u01' in str(call)]
        self.assertEqual(encryption_calls, [])

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    def test_doexecute_adds_ecra_nat_for_bm(self, mock_get_ctx):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.isBM.return_value = True
        ebox.mIsOciEXACC.return_value = False

        cs_step.doExecute(ebox, {}, ['step'])

        ebox.mAddEcraNatOnDomU.assert_called_once()
        ebox.mUpdateStatusCS.assert_any_call(True, cs_step.step, ['step'], aComment='Add ECRA NAT-Ip')

    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    def test_doexecute_adds_ecra_nat_for_exacc_environment(self, mock_get_ctx):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.isBM.return_value = False
        ebox.mIsOciEXACC.return_value = True

        cs_step.doExecute(ebox, {}, ['step'])

        ebox.mAddEcraNatOnDomU.assert_called_once()
        ebox.mUpdateStatusCS.assert_any_call(True, cs_step.step, ['step'], aComment='Add ECRA NAT-Ip')

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    def test_doexecute_secure_listeners_for_atp(self, mock_get_ctx):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.isATP.return_value = True
        ebox.mIsOciEXACC.return_value = False

        cs_step.doExecute(ebox, {}, ['step'])

        ebox.mATPSecureListeners.assert_called_once()
        ebox.mUpdateStatusCS.assert_any_call(True, cs_step.step, ['step'], aComment='ATP: Secure Listeners')

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.ebNetworkValidations')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    def test_doexecute_checks_network_for_exabm(self, mock_get_ctx, mock_net_valid):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        mock_net_mgr = mock.Mock()
        mock_net_valid.return_value = mock_net_mgr

        ebox = _build_base_ebox()
        ebox.mIsExabm.return_value = True
        ebox.isATP.return_value = False
        ebox.mReturnDom0DomUPair.return_value = [('dom0', 'domu')]

        cs_step.doExecute(ebox, {}, [])

        mock_net_valid.assert_called_once_with(ebox, [('dom0', 'domu')])
        mock_net_mgr.mCheckClientBackupIPSet.assert_called_once()

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.setupU01EncryptedDiskParallel')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.mSetLuksChannelOnDom0Exacc')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.validateMinImgEncryptionSupport', return_value=False)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.ebLogCritical')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.exacc_fsencryption_requested', return_value=False)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=True)
    def test_doexecute_raises_when_min_image_invalid(self, mock_is_enc, mock_exacc_enc,
            mock_get_ctx, mock_log_critical, mock_validate, mock_set_channel, mock_setup):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {'fs_encryption_exascale': 'TRUE'}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mIsKVM.return_value = True
        ebox.mIsOciEXACC.return_value = False

        with self.assertRaises(cs_postvminstall_module.ExacloudRuntimeError):
            cs_step.doExecute(ebox, {}, [])

        mock_validate.assert_called_once_with(ebox, [])
        mock_set_channel.assert_not_called()
        mock_setup.assert_not_called()
        mock_log_critical.assert_called_once()

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.setupU01EncryptedDiskParallel')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.mSetLuksChannelOnDom0Exacc')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.validateMinImgEncryptionSupport', return_value=True)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.exacc_fsencryption_requested', return_value=True)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=False)
    def test_doexecute_sets_up_kvm_encryption(self, mock_is_enc, mock_exacc_enc, mock_get_ctx,
            mock_validate, mock_set_channel, mock_setup):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {'fs_encryption_exascale': 'TRUE'}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mIsKVM.return_value = True
        ebox.mIsOciEXACC.return_value = True
        ebox.mReturnDom0DomUPair.return_value = [('dom0', 'domu')]

        cs_step.doExecute(ebox, {}, [])

        mock_validate.assert_called_once_with(ebox, [('dom0', 'domu')])
        mock_set_channel.assert_called_once_with(ebox, 'dom0', 'domu')
        mock_setup.assert_called_once_with(ebox, {}, [('dom0', 'domu')])

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.setupU01EncryptedDiskParallel')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.mSetLuksChannelOnDom0Exacc')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.validateMinImgEncryptionSupport', return_value=True)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.exacc_fsencryption_requested', return_value=False)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=True)
    def test_doexecute_kvm_encryption_non_exacc(self, mock_is_enc, mock_exacc_enc, mock_get_ctx,
            mock_validate, mock_set_channel, mock_setup):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {'fs_encryption_exascale': 'TRUE'}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mIsKVM.return_value = True
        ebox.mIsOciEXACC.return_value = False
        ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domua')]

        cs_step.doExecute(ebox, {}, [])

        mock_validate.assert_called_once_with(ebox, [('dom0a', 'domua')])
        mock_set_channel.assert_not_called()
        mock_setup.assert_called_once_with(ebox, {}, [('dom0a', 'domua')])

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.ebLogError')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.connect_to_host')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.exacc_fsencryption_requested', return_value=False)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=False)
    def test_doexecute_reconfig_shared_rack_failure_raises(self, mock_is_enc, mock_exacc_enc,
            mock_get_ctx, mock_connect, mock_log_error):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [('', '', ''), ('', '', 'err'), ('', '', 'rollback')]
        mock_node.mGetCmdExitStatus.side_effect = [1, 0]

        mock_connect_ctx = mock.MagicMock()
        mock_connect_ctx.__enter__.return_value = mock_node
        mock_connect_ctx.__exit__.return_value = None
        mock_connect.return_value = mock_connect_ctx

        ebox = _build_base_ebox()
        ebox.mReturnDom0DomUPair.return_value = [('dom0', 'domu')]
        ebox.mIsExabm.return_value = True
        ebox.isATP.return_value = True
        ebox.mIsOciEXACC.return_value = False
        ebox.mIsKVM.return_value = False
        ebox.mCheckConfigOption.return_value = True
        ebox.mGetOciExaCCServicesSetup.return_value = {
            'forwardproxy': {'ip': '10.1.1.1', 'port': '8080'},
            'fileserver': {'ip': '10.2.2.2', 'port': '8443'},
        }

        with self.assertRaises(cs_postvminstall_module.ExacloudRuntimeError):
            cs_step.doExecute(ebox, {}, [])

        self.assertEqual(mock_node.mExecuteCmd.call_count, 3)
        mock_log_error.assert_called()

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.ebLogError')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.connect_to_host')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.exacc_fsencryption_requested', return_value=False)
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.isEncryptionRequested', return_value=False)
    def test_doexecute_reconfig_shared_rack_rollback_failure_logs(self, mock_is_enc, mock_exacc_enc,
            mock_get_ctx, mock_connect, mock_log_error):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        mock_node = mock.Mock()
        mock_node.mExecuteCmd.side_effect = [('', '', ''), ('', '', 'err'), ('', '', 'rollback_error')]
        mock_node.mGetCmdExitStatus.side_effect = [1, 1]

        mock_connect_ctx = mock.MagicMock()
        mock_connect_ctx.__enter__.return_value = mock_node
        mock_connect_ctx.__exit__.return_value = None
        mock_connect.return_value = mock_connect_ctx

        ebox = _build_base_ebox()
        ebox.mReturnDom0DomUPair.return_value = [('dom0', 'domu')]
        ebox.mIsExabm.return_value = True
        ebox.isATP.return_value = True
        ebox.mIsOciEXACC.return_value = False
        ebox.mIsKVM.return_value = False
        ebox.mCheckConfigOption.return_value = True
        ebox.mGetOciExaCCServicesSetup.return_value = {
            'forwardproxy': {'ip': '10.1.1.1', 'port': '8080'},
            'fileserver': {'ip': '10.2.2.2', 'port': '8443'},
        }

        with self.assertRaises(cs_postvminstall_module.ExacloudRuntimeError):
            cs_step.doExecute(ebox, {}, [])

        self.assertEqual(mock_node.mExecuteCmd.call_count, 3)
        self.assertEqual(mock_log_error.call_count, 2)
        self.assertTrue(any('Could not rollback changes' in args[0] for args, _ in mock_log_error.call_args_list))

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    def test_doexecute_runs_core_post_steps(self, mock_get_ctx):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()

        cs_step.doExecute(ebox, {}, ['post'])

        ebox.mResetClusterSSHKeys.assert_called_once()
        ebox.mAddEcraNatOnDomU.assert_not_called()
        ebox.mSaveClusterConfiguration.assert_called_once()
        ebox.mChangeMinFreeKb.assert_called_once()
        ebox.mRemoveExaCCMacrosVerify.assert_called_once_with('DomU')
        ebox.mSecureDOMUPwd.assert_called_once()
        ebox.mSecureDOMUSsh.assert_called_once()

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    def test_doexecute_updates_dom0_network_with_lock(self, mock_get_ctx):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()

        cs_step.doExecute(ebox, {}, ['step'])

        ebox.remote_lock.set_lock_type.assert_called_once_with('dom0')
        ebox.remote_lock.__enter__.assert_called_once()
        ebox.remote_lock.__exit__.assert_called_once()
        ebox.mDom0PostVMCreateNetConfig.assert_called_once_with(aMode=False)
        ebox.mUpdateStatusCS.assert_any_call(True, cs_step.step, ['step'], aComment='Update Dom0 Network Config')

    # Auto-generated test for undoExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.csUtil')
    def test_undoexecute_runs_prevm_cleanup(self, mock_csutil):
        cs_step = csPostVMInstall()
        mock_csu = mock.Mock()
        mock_csutil.return_value = mock_csu

        ebox = _build_base_ebox()
        ebox.mGetCmd.return_value = 'createservice'

        cs_step.undoExecute(ebox, {'opt': 'value'}, ['step'])

        ebox.mRunScript.assert_called_once_with(aType='*', aWhen='pre.vm_delete')
        ebox.mVMImagesShredding.assert_called_once_with({'opt': 'value'})
        mock_csu.mPreVMDeleteCreatePatching.assert_called_once_with(ebox, {'opt': 'value'})
        mock_csu.mUndoCopyFileToClusterConfiguration.assert_called_once_with(ebox, 'gi_install_cluster.xml')

    # Auto-generated test for undoExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.csUtil')
    def test_undoexecute_skips_cleanup_for_delete_commands(self, mock_csutil):
        cs_step = csPostVMInstall()
        mock_csu = mock.Mock()
        mock_csutil.return_value = mock_csu

        ebox = _build_base_ebox()
        ebox.mGetCmd.return_value = 'vm_delete'

        cs_step.undoExecute(ebox, {}, [])

        mock_csu.mPreVMDeleteCreatePatching.assert_not_called()
        mock_csu.mUndoCopyFileToClusterConfiguration.assert_called_once_with(ebox, 'gi_install_cluster.xml')

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.connect_to_host')
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    def test_doexecute_skips_shared_rack_reconfig_when_disabled(self, mock_get_ctx, mock_connect):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mCheckConfigOption.return_value = False

        cs_step.doExecute(ebox, {}, [])

        mock_connect.assert_not_called()
        ebox.mCreateNatIptablesRulesFile.assert_called_once()

    # Auto-generated test for doExecute
    @mock.patch('ecs.exacloud.exabox.ovm.csstep.exascale.cs_postvminstall.get_gcontext')
    def test_doexecute_updates_bpl_and_cluster_config(self, mock_get_ctx):
        cs_step = csPostVMInstall()
        mock_ctx = mock.Mock()
        mock_ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = mock_ctx

        ebox = _build_base_ebox()
        ebox.mGetConfigPath.return_value = '/custom/config/path'

        cs_step.doExecute(ebox, {}, ['post'])

        ebox.mUpdateStatusCS.assert_any_call(True, cs_step.step, ['post'], aComment='Update GI and DB BPL')
        ebox.mUpdateDBGIBPL.assert_called_once()
        ebox.mCopyFileToClusterConfiguration.assert_called_once_with('/custom/config/path', 'gi_install_cluster.xml')
        ebox.mRunScript.assert_any_call(aType='*', aWhen='pre.gi_install')


if __name__ == '__main__':
    unittest.main()
