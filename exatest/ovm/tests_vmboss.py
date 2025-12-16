#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_vmboss.py /main/2 2025/11/18 03:55:10 shapatna Exp $
#
# tests_vmboss.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_vmboss.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    11/12/25 - Enh 38574081: Add unit tests to improve the
#                           coverage using Cline
#    jfsaldan    11/08/23 - Bug 35903298 - EXACS - 2341 | ZRHPREPROD EXACLOUD
#                           AGENT AUTO SHUTDOWN
#    jfsaldan    11/08/23 - Creation
#

import unittest
from unittest.mock import Mock, patch
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogTrace
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext
from unittest import mock
from unittest.mock import MagicMock
import io
import types
from exabox.ovm.vmboss import ebCluVmbackupObjectStore

class ebTestVMBoss(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None


    @patch("exabox.ovm.clucontrol.ebCluVmbackupObjectStore")
    def test_force_old_endpoint_disabled(self, aMagicVMBoss):

        _ebox = self.mGetClubox()
        _vmbackup_opts = dict(get_gcontext().mGetConfigOptions().get(
                "vmbackup", {}))
        _vmbackup_opts["force_ecra_oss_api"] = "False"
        self.mGetContext().mSetConfigOption("vmbackup", _vmbackup_opts)
        _rc = _ebox.mHandlerVMBackupOSS()
        self.assertEqual(1, _rc)

    @patch("exabox.ovm.clucontrol.ebCluVmbackupObjectStore")
    def test_force_old_endpoint_enabled(self, aMagicVMBoss):

        _ebox = self.mGetClubox()
        _vmbackup_opts = dict(get_gcontext().mGetConfigOptions().get(
                "vmbackup", {}))
        _vmbackup_opts["force_ecra_oss_api"] = "True"
        self.mGetContext().mSetConfigOption("vmbackup", _vmbackup_opts)
        _rc = _ebox.mHandlerVMBackupOSS()
        self.assertEqual(0, _rc)

class ebTestVMBossObjectStore(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

    def setUp(self):
        # Patch get_gcontext to control config and base path
        self.p_getctx = patch('exabox.ovm.vmboss.get_gcontext')
        self.mock_getctx = self.p_getctx.start()
        self.mock_ctx = Mock()
        self.mock_ctx.mGetBasePath.return_value = '/tmp/WorkDir'
        # Default config options used by the class under test
        self.config = {
            'ociexacc': 'False',
            'exabm': 'False',
            'max_oss_vmbackups': None,
            'vmbackup2oss_skip_image': 'True',
        }
        self.mock_ctx.mGetConfigOptions.return_value = self.config
        self.mock_getctx.return_value = self.mock_ctx

        # Patch ebKmsVmbObjectStore used inside vmboss.py
        self.p_kms = patch('exabox.ovm.vmboss.ebKmsVmbObjectStore')
        self.mock_kms_cls = self.p_kms.start()
        self.mock_kms = Mock()
        self.mock_kms_cls.return_value = self.mock_kms

        # Patch exaBoxNode used inside vmboss.py
        self.p_node = patch('exabox.ovm.vmboss.exaBoxNode')
        self.mock_node_cls = self.p_node.start()
        self.mock_node = Mock()
        self.mock_node_cls.return_value = self.mock_node

        # Patch ebExit to raise SystemExit instead of exiting the test process
        self.p_exit = patch('exabox.ovm.vmboss.ebExit', side_effect=lambda code: (_ for _ in ()).throw(SystemExit(code)))
        self.mock_exit = self.p_exit.start()

        # Filesystem helpers used by mPrecheckValidVM and mRestore
        self.p_os_stat = patch('exabox.ovm.vmboss.os.stat', side_effect=OSError('missing'))
        self.p_os_mkdir = patch('exabox.ovm.vmboss.os.mkdir')
        self.p_os_exists = patch('exabox.ovm.vmboss.os.path.exists', return_value=True)
        self.p_os_makedirs = patch('exabox.ovm.vmboss.os.makedirs')
        self.p_os_stat.start()
        self.mock_os_mkdir = self.p_os_mkdir.start()
        self.p_os_exists.start()
        self.p_os_makedirs.start()

        # Patch subprocess module used in exabox.ovm.vmboss
        self.p_subproc = patch('exabox.ovm.vmboss.subprocess')
        self.mock_subproc = self.p_subproc.start()

        # Build a minimal ebox mock with required methods
        self.ebox = self._make_ebox()

    def tearDown(self):
        for p in [
            self.p_getctx,
            self.p_kms,
            self.p_node,
            self.p_exit,
            self.p_os_stat,
            self.p_os_mkdir,
            self.p_os_exists,
            self.p_os_makedirs,
            self.p_subproc,
        ]:
            p.stop()

    def _make_ebox(self):
        ebox = Mock()
        # Match signature: key, default=None
        ebox.mCheckConfigOption.side_effect = lambda key, default=None: self.config.get(key, default)

        # Domain pairs
        ebox.mReturnDom0DomUPair.return_value = [('dom0a.ecra', 'vm1.ecra')]
        ebox.mReturnDom0DomUNATPair.side_effect = lambda *_args, **_kw: [('dom0a.ecra', 'vm1.ecra')]

        # Machines and Networks to compute domain name
        mock_machines = Mock()
        mock_machine_cfg = Mock()
        mock_machine_cfg.mGetMacNetworks.return_value = ['net1']
        mock_machines.mGetMachineConfig.return_value = mock_machine_cfg

        mock_networks = Mock()
        mock_net_cfg = Mock()
        mock_net_cfg.mGetNetNatDomainName.return_value = 'ecra'
        mock_networks.mGetNetworkConfig.return_value = mock_net_cfg

        ebox.mGetMachines.return_value = mock_machines
        ebox.mGetNetworks.return_value = mock_networks
        return ebox

    def _io_lines(self, lines):
        return io.StringIO(''.join(lines))

    def test_mGetDomainName_returns_dot_domain(self):
        obj = ebCluVmbackupObjectStore(self.ebox, {})
        self.assertEqual('.ecra', obj.mGetDomainName())

    def test_mPrecheckValidVM_returns_expected_dom0_domU(self):
        obj = ebCluVmbackupObjectStore(self.ebox, {})
        options = types.SimpleNamespace(jsonconf={'vmname': 'vm1'})
        dom0, domU = obj.mPrecheckValidVM(options, 'backup')
        self.assertEqual('dom0a.ecra', dom0)
        self.assertEqual('vm1.ecra', domU)
        # Stage dir should be attempted to be created when missing
        self.assertTrue(self.mock_os_mkdir.called)

    def test_mList_returns_sorted_versions_for_cluster(self):
        obj = ebCluVmbackupObjectStore(self.ebox, {})
        options = types.SimpleNamespace(jsonconf={'vmname': 'vm1'})

        # mListObjects returns all objects, including details
        self.mock_kms.mListObjects.return_value = (False, [
            {'name': 'vm1.ecra.2'},
            {'name': 'vm1.ecra.2.details'},
            {'name': 'vm1.ecra.1'},
            {'name': 'vm2.ecra.1'},
        ])
        # Only versions that have a .details companion should be included
        def _get_object_side(name):
            return (False, {}) if name in ('vm1.ecra.1.details', 'vm1.ecra.2.details') else (True, None)
        self.mock_kms.mGetObject.side_effect = _get_object_side

        out = obj.mList(options)
        self.assertEqual(['vm1.ecra.1', 'vm1.ecra.2'], out)

    def test_mBackup_skips_when_sequence_already_in_objectstore(self):
        obj = ebCluVmbackupObjectStore(self.ebox, {})
        options = types.SimpleNamespace(jsonconf={'vmname': 'vm1'})

        # Node indicates backup path exists and contains multiple seq dirs
        self.mock_node.mFileExists.side_effect = lambda path: True
        # First ls -d to list sequence directories
        self.mock_node.mExecuteCmd.return_value = (0, self._io_lines([
            '/EXAVMIMAGES/Backup/Local/dom0a.ecra/4/\n',
            '/EXAVMIMAGES/Backup/Local/dom0a.ecra/5/\n'
        ]), None)
        # Latest seq is 5; mark .details present in OSS so backup returns early
        self.mock_kms.mGetObject.return_value = (False, {'name': 'vm1.ecra.5.details'})

        obj.mBackup(options)

        # Should not attempt to upload when already present
        self.mock_kms.mPutKms.assert_not_called()

    def test_mBackup_happy_path_uploads_and_prunes_old(self):
        obj = ebCluVmbackupObjectStore(self.ebox, {})
        options = types.SimpleNamespace(jsonconf={'vmname': 'vm1'})

        # Node indicates backup path exists and contains sequence directories
        self.mock_node.mFileExists.side_effect = lambda path: path.endswith('.backup_summary.json') or 'Backup/Local/dom0a.ecra' in path
        # List sequence directories
        self.mock_node.mExecuteCmd.side_effect = [
            # '/bin/ls -d {backup}/*/'
            (0, self._io_lines([
                '/EXAVMIMAGES/Backup/Local/dom0a.ecra/4/\n',
                '/EXAVMIMAGES/Backup/Local/dom0a.ecra/5/\n'
            ]), None),
            # '/bin/ls {last_seq_dir}'
            (0, self._io_lines(['20250101_010101/\n']), None),
            # '/bin/ls {vmpath} | grep ...' -> list disk files to include in tar
            (0, self._io_lines([
                '/EXAVMIMAGES/Backup/Local/dom0a.ecra/5/20250101_010101/GuestImages/vm1.ecra/disk1\n',
                '/EXAVMIMAGES/Backup/Local/dom0a.ecra/5/20250101_010101/GuestImages/vm1.ecra/disk2\n'
            ]), None),
            # tar execution
            (0, self._io_lines(['']), None),
            # '/usr/bin/md5sum ' on remote file
            (0, self._io_lines(['abc123  /EXAVMIMAGES/Backup/Local/dom0a.ecra/5/20250101_010101/GuestImages/vm1.ecra.tgz\n']), None),
            # remove remote tar
            (0, self._io_lines(['']), None),
        ]
        # Latest seq (5) not present in OSS
        self.mock_kms.mGetObject.side_effect = [
            (True, None),  # _oss_obj + '.details' (not present -> proceed)
            (False, {}),   # lastN '.details' exists -> prune
        ]
        # Local md5
        self.mock_subproc.check_output.return_value = b'abc123  /tmp/WorkDir/vmbstage//vm1.ecra.tgz'
        # No errors during put
        self.mock_kms.mPutKms.return_value = None

        obj.mBackup(options)

        # Uploaded with expected object name and hash
        self.mock_kms.mPutKms.assert_called()
        put_args = self.mock_kms.mPutKms.call_args[0]
        self.assertTrue(put_args[0].startswith('vm1.ecra.5'))
        self.assertEqual('abc123', put_args[2])

        # Prune lastN (seq 2) when .details exists
        self.mock_kms.mDeleteObject.assert_any_call('vm1.ecra.2')
        self.mock_kms.mDeleteObject.assert_any_call('vm1.ecra.2.details')

    def test_mRestore_happy_path_downloads_and_extracts(self):
        obj = ebCluVmbackupObjectStore(self.ebox, {})
        options = types.SimpleNamespace(jsonconf={'vmname': 'vm1'})

        with patch.object(ebCluVmbackupObjectStore, 'mList', return_value=['vm1.ecra.4', 'vm1.ecra.5']):
            # KMS returns local hash
            self.mock_kms.mGetKms.return_value = 'abc123'
            # Remote md5 equals local hash
            self.mock_node.mExecuteCmd.return_value = (0, self._io_lines(['abc123  /EXAVMIMAGES/GuestImages/vm1.ecra.tgz\n']), None)

            obj.mRestore(options)

            self.mock_kms.mGetKms.assert_called_once()
            # Ensure untar command executed on the node
            self.assertTrue(self.mock_node.mExecuteCmd.call_count >= 2)

    def test_mRestore_no_backups_exits_cleanly(self):
        obj = ebCluVmbackupObjectStore(self.ebox, {})
        options = types.SimpleNamespace(jsonconf={'vmname': 'vm1'})

        with patch.object(ebCluVmbackupObjectStore, 'mList', return_value=[]):
            with self.assertRaises(SystemExit) as cm:
                obj.mRestore(options)
            self.assertEqual(0, cm.exception.code)

    def test_mExecute_dispatches_operations(self):
        obj = ebCluVmbackupObjectStore(self.ebox, {})

        obj.mBackup = Mock()
        obj.mRestore = Mock()
        obj.mDelete = Mock()

        # backup
        obj.mExecute(types.SimpleNamespace(jsonconf={'operation': 'backup'}))
        obj.mBackup.assert_called_once()

        # restore
        obj.mExecute(types.SimpleNamespace(jsonconf={'operation': 'restore'}))
        obj.mRestore.assert_called_once()

        # delete
        obj.mExecute(types.SimpleNamespace(jsonconf={'operation': 'delete'}), aCmd='go')
        obj.mDelete.assert_called_once()

    def test_mDelete_selective_by_vm(self):
        obj = ebCluVmbackupObjectStore(self.ebox, {})
        options = types.SimpleNamespace(jsonconf={'vmname': 'vm1'})

        with patch.object(ebCluVmbackupObjectStore, 'mList', return_value=['vm1.ecra.4', 'vm2.ecra.1']):
            with patch.object(ebCluVmbackupObjectStore, 'mPrecheckValidVM', return_value=('dom0a.ecra', 'vm1.ecra')):
                obj.mDelete(options, aCmd='delete')

        # Only vm1 variants should be deleted
        self.mock_kms.mDeleteObject.assert_any_call('vm1.ecra.4')
        self.mock_kms.mDeleteObject.assert_any_call('vm1.ecra.4.details')

if __name__ == '__main__':
    unittest.main()
