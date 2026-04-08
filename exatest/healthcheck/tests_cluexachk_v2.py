#!/usr/bin/env python
#
# tests_cluexachk_v2.py
#
# Additional unit tests to extend coverage for cluexachk.py.

import os
import gc
import fcntl
import tempfile
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from contextlib import ExitStack
from unittest.mock import MagicMock, patch, call

from exabox.healthcheck.cluexachk import FileLockMgr, LockMode
from exabox.healthcheck.cluexachk import ebCluExachk as cluexachk


class DummyHealthCheck(object):
    """Lightweight healthcheck wrapper used by the v2 tests."""

    def __init__(self, ebox, cluster_hosts, recommend, json_map):
        self._ebox = ebox
        self._cluster_hosts = cluster_hosts
        self._recommend = recommend
        self._json_map = json_map
        self._log_handler = MagicMock()
        self._default_log_handler = MagicMock()

    def mGetEbox(self):
        return self._ebox

    def mGetClusterPath(self):
        return '/cluster'

    def mGetRecommend(self):
        return self._recommend

    def mGetJsonMap(self):
        return self._json_map

    def mGetLogHandler(self):
        return self._log_handler

    def mGetDefaultLogHandler(self):
        return self._default_log_handler

    def mGetClusterHostD(self):
        return self._cluster_hosts


class TestCluexachkV2(unittest.TestCase):
    """Focused coverage for cluexachk heavy branches."""

    # Auto-generated test for file_lock
    def test_file_lock_raises_when_mode_invalid(self):
        """Ensures FileLockMgr.file_lock rejects non-LockMode inputs."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        try:
            mgr = FileLockMgr(tmp_path)
            with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_log_error:
                result = mgr.file_lock('invalid')
        finally:
            os.unlink(tmp_path)

        self.assertFalse(result)
        mock_log_error.assert_called_once()

    # Auto-generated test for file_lock
    def test_file_lock_acquires_shared_lock_successfully(self):
        """Validates shared mode opens file read-only and acquires lock."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        mgr = FileLockMgr(tmp_path)

        with ExitStack() as stack:
            mock_open = stack.enter_context(patch('exabox.healthcheck.cluexachk.open', wraps=open))
            mock_flock = stack.enter_context(patch('exabox.healthcheck.cluexachk.fcntl.flock'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            result = mgr.file_lock(LockMode.SHARED)

        try:
            self.assertTrue(result)
            mock_open.assert_called_with(tmp_path, 'r')
            mock_flock.assert_called_once()
            self.assertEqual(mock_flock.call_args[0][1], fcntl.LOCK_SH)
        finally:
            if mgr.fd:
                try:
                    mgr.fd.close()
                except Exception:
                    pass
            os.unlink(tmp_path)

    # Auto-generated test for file_lock
    def test_file_lock_acquires_exclusive_lock_successfully(self):
        """Validates exclusive mode opens file writable and acquires lock."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        mgr = FileLockMgr(tmp_path)

        with ExitStack() as stack:
            mock_open = stack.enter_context(patch('exabox.healthcheck.cluexachk.open', wraps=open))
            mock_flock = stack.enter_context(patch('exabox.healthcheck.cluexachk.fcntl.flock'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            result = mgr.file_lock(LockMode.EXCLUSIVE)

        try:
            self.assertTrue(result)
            mock_open.assert_called_with(tmp_path, 'w')
            mock_flock.assert_called_once()
            self.assertEqual(mock_flock.call_args[0][1], fcntl.LOCK_EX)
        finally:
            if mgr.fd:
                try:
                    mgr.fd.close()
                except Exception:
                    pass
            os.unlink(tmp_path)

    # Auto-generated test for file_lock
    def test_file_lock_logs_error_when_open_fails(self):
        """Exercises exception path when underlying open raises."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        mgr = FileLockMgr(tmp_path)

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.open', side_effect=OSError('broken')))
            mock_log_error = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = mgr.file_lock(LockMode.SHARED)

        try:
            self.assertFalse(result)
            mock_log_error.assert_called_once()
        finally:
            os.unlink(tmp_path)

    # Auto-generated test for __del__
    def test_file_lock_destructor_releases_lock(self):
        """Ensures FileLockMgr.__del__ unlocks and closes descriptor when present."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        mgr = FileLockMgr(tmp_path)

        fake_fd = MagicMock()
        fake_fd.fileno.return_value = 321
        type(fake_fd).closed = False

        mgr.fd = fake_fd

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.fcntl.flock'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            mgr.__del__()

        fake_fd.fileno.assert_called_once()
        fake_fd.close.assert_called_once()

        os.unlink(tmp_path)

        # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_install_success_branch(self):
        ebox = MagicMock()
        ebox.mExecuteCmdLog2.return_value = ('success', [])
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        @contextmanager
        def fake_lock(*_args, **_kwargs):
            yield True

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.mkdir'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_lock))
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertTrue(result)
        ebox.mExecuteCmdLog2.assert_called_once_with('/ctrl/ahf_setup -silent -local -ahf_loc /ctrl/install -data_dir /ctrl/install -tmp_loc /tmp/cache')

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_fresh_install_skips_retry(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-1'

        err_stream = MagicMock()
        err_stream.readlines.return_value = ['failure']

        node.mExecuteCmd.return_value = (None, err_stream, None)
        node.mGetCmdExitStatus.return_value = True

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, True)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=True))
            mock_uninstall = stack.enter_context(patch.object(test_obj, 'mAhfUninstall'))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'dom0',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        node.mExecuteCmd.assert_called_once()
        mock_uninstall.assert_not_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_retry_succeeds_after_uninstall(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-1'

        first_err = MagicMock()
        first_err.readlines.return_value = ['fail']
        second_err = MagicMock()
        second_err.readlines.return_value = ['retry success']

        node.mExecuteCmd.side_effect = [
            (None, first_err, None),
            (None, second_err, None)
        ]
        node.mGetCmdExitStatus.side_effect = [True, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=True))
            mock_uninstall = stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'dom0',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 2)
        mock_uninstall.assert_called_once_with(node, '/remote/install')

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_domU_tfactl_failure_returns_false(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        ebox.isATP.return_value = True
        ebox.IsZdlraProv.return_value = False
        ebox.mCheckSubConfigOption.return_value = '/remote/data'
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        node.mFileExists.side_effect = [True, True]

        err_stream = MagicMock()
        err_stream.readlines.return_value = ['failure']

        node.mExecuteCmd.side_effect = [
            (None, err_stream, None),
            (None, err_stream, None),
            (None, err_stream, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, True, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mRetriveAhfInstallDataPath', return_value='/path'))
            stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteDataDir'))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mGetHigherAHFPath', return_value='/remote/bin'))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'domU',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        self.assertEqual(node.mExecuteCmd.call_count, 2)

# Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_skips_install_when_upgrade_not_required(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=False))
            mock_isfile = stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertTrue(result)
        mock_isfile.assert_not_called()

    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_returns_false_when_binary_missing(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            mock_log_error = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=False))
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertFalse(result)
        mock_log_error.assert_called()

    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_returns_false_when_lock_not_acquired(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        @contextmanager
        def fake_lock(*_args, **_kwargs):
            yield False

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_lock))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertFalse(result)

    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_handles_install_failure(self):
        ebox = MagicMock()
        ebox.mExecuteCmdLog2.return_value = (['log'], 'failure')
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        @contextmanager
        def fake_lock(*_args, **_kwargs):
            yield True

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_lock))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.mkdir'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            mock_health = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertFalse(result)
        mock_health.assert_called()

    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_raises_on_exception(self):
        ebox = MagicMock()
        ebox.mExecuteCmdLog2.side_effect = RuntimeError('boom')
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        @contextmanager
        def fake_lock(*_args, **_kwargs):
            yield True

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_lock))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.mkdir'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            mock_log_error = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            with self.assertRaises(Exception):
                test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        mock_log_error.assert_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_domU_atp_executes_tfactl_commands(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

            def mCheckSubConfigOption(self, section, key):
                mapping = {
                    ('ahf_paths', 'remote_ahf_data_path_domu'): '/remote/data',
                    ('ahf_paths', 'remote_ahf_data_path_zdlra_domu'): '/zdlra'
                }
                return mapping[(section, key)]

            def IsZdlraProv(self):
                return False

            def isATP(self):
                return True

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-node'
        node.mFileExists.side_effect = [True, True]

        install_log = MagicMock()
        install_log.readlines.return_value = ['success']
        tfactl_out = MagicMock()
        tfactl_out.readlines.return_value = ['tfactl ok']

        node.mExecuteCmd.side_effect = [
            (None, install_log, None),
            (None, tfactl_out, None),
            (None, tfactl_out, None),
        ]
        node.mGetCmdExitStatus.side_effect = [False, False, False]

        def fake_copy(a_node, local_path, remote_path):
            test_obj.ahf_copy_path = os.path.join(remote_path, 'ahf_setup')
            return True

        with patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)) as mock_version, \
             patch.object(test_obj, 'mRemoveOldExachk') as mock_remove, \
             patch.object(test_obj, 'mCopyAhfImage', side_effect=fake_copy) as mock_copy, \
             patch.object(test_obj, 'mAhfUninstall', return_value=True) as mock_uninstall, \
             patch.object(test_obj, 'mDeleteDataDir') as mock_delete_data, \
             patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]) as mock_chown, \
             patch.object(test_obj, 'mGetHigherAHFPath', return_value='/override/bin'), \
             patch.object(test_obj, 'mRetriveAhfInstallDataPath', return_value='/other/path'), \
             patch.object(test_obj, 'mGetTFACTLStatus', return_value=True) as mock_tfactl_status, \
             patch.object(test_obj, 'mDeleteAhfImage') as mock_delete_image:
            result = test_obj.mSetupAhfonRemote(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)
        install_cmd = node.mExecuteCmd.call_args_list[0][0][0]
        self.assertIn('/override/bin/ahf_setup', install_cmd)
        self.assertIn('-env_type exacs', install_cmd)
        tfactl_redact_cmd = node.mExecuteCmd.call_args_list[1][0][0]
        tfactl_autopurge_cmd = node.mExecuteCmd.call_args_list[2][0][0]
        self.assertEqual(tfactl_redact_cmd, '(/remote/install/oracle.ahf/bin/tfactl set redact=SANITIZE )')
        self.assertEqual(tfactl_autopurge_cmd, '(/remote/install/oracle.ahf/bin/tfactl set manageLogsAutoPurge=ON )')

        mock_version.assert_called_once()
        mock_remove.assert_called_once_with(node)
        mock_copy.assert_called_once_with(node, '/local/ahf_setup', '/remote/bin')
        mock_uninstall.assert_called_once_with(node, '/remote/install')
        mock_delete_data.assert_called_once_with(node)
        mock_tfactl_status.assert_called_once_with('/remote/install', node)
        mock_delete_image.assert_called_once_with(node)
        self.assertEqual(
            mock_chown.call_args_list,
            [call(node, '/remote/data', 'root', 'root'), call(node, '/remote/data', 'oracle', 'oinstall')]
        )

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_domU_root_chown_failure_returns_false(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        ebox.IsZdlraProv.return_value = False
        ebox.isATP.return_value = False
        ebox.mCheckSubConfigOption.side_effect = lambda section, key: {
            ('ahf_paths', 'remote_ahf_data_path_domu'): '/remote/data'
        }[(section, key)]
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        node.mFileExists.side_effect = [True, True]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mRetriveAhfInstallDataPath', return_value='/other/path'))
            stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteDataDir'))
            mock_chown = stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[False]))
            stack.enter_context(patch.object(test_obj, 'mGetHigherAHFPath', return_value='/remote/bin'))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))

            result = test_obj.mSetupAhfonRemote(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        mock_chown.assert_called_once_with(node, '/remote/data', 'root', 'root')
        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_returns_false_when_copy_fails(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-1'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=False))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'dom0',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_retry_failure(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-1'

        first_err = MagicMock()
        first_err.readlines.side_effect = [['err1'], ['err1']]
        second_err = MagicMock()
        second_err.readlines.side_effect = [['err2'], ['err2']]

        node.mExecuteCmd.side_effect = [
            (None, first_err, None),
            (None, second_err, None)
        ]
        node.mGetCmdExitStatus.side_effect = [True, True]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=True))
            mock_uninstall = stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'dom0',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        self.assertEqual(node.mExecuteCmd.call_count, 2)
        mock_uninstall.assert_called_once_with(node, '/remote/install')

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_returns_when_host_list_empty(self):
        json_map = {}
        recommend = []

        ebox = MagicMock()
        ebox.mCheckConfigOption.return_value = False
        ebox.mReturnAllClusterHosts.return_value = ([], [], [], [])
        ebox.mReturnDom0DomUNATPair.return_value = []
        ebox.mIsExabm.return_value = False
        ebox.mIsOciEXACC.return_value = False
        ebox.mIsKVM.return_value = False
        ebox.SharedEnv.return_value = False
        ebox.mGetUUID.return_value = 'uuid'
        ebox.mGetClusterPath.return_value = '/cluster'
        ebox.mGetOedaPath.return_value = '/oeda'

        hc = DummyHealthCheck(ebox, {}, recommend, json_map)
        options = SimpleNamespace(jsonconf={})
        test_obj = cluexachk(hc, options)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.makedirs'))
            log_info = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            log_health = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            log_remove = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'))
            log_set = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', side_effect=['dest', None]))
            stack.enter_context(patch.dict('exabox.healthcheck.cluexachk.os.environ', {
                'PYTHONPATH': 'orig',
                'RAT_ECRA': '1',
                'RAT_ROOT_COLLECTIONS_IN_SERIAL': '1',
                'RAT_NOCLEAN_DIR': '1'
            }, clear=False))

            test_obj.mRemoteRunExachk(options)

        log_info.assert_any_call('WARNING: host list is empty for Exachk execution')
        log_health.assert_any_call('WRN', 'No hosts provided for Exachk execution')
        log_remove.assert_called_once_with('dest')
        self.assertEqual(log_set.call_args_list[0], call(hc.mGetLogHandler(), True))
        self.assertEqual(log_set.call_args_list[-1], call(hc.mGetDefaultLogHandler()))
        self.assertEqual(json_map['Exachk']['hostCheck'], {})
        self.assertEqual(recommend, [])

    def test_mRemoteRunExachk_releases_remote_lock_on_command_error(self):
        json_map = {}
        recommend = []

        node = MagicMock()
        node.mGetNodeType.return_value = 'dom0'
        node.mGetPingable.return_value = True
        node.mGetHostname.return_value = 'dom0-1'

        cluster_hosts = {'dom0-1': node}

        ebox = MagicMock()
        ebox.mCheckConfigOption.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-1'], ['domu-1'], [], [])
        ebox.mReturnDom0DomUNATPair.return_value = []
        ebox.mIsExabm.return_value = False
        ebox.mIsOciEXACC.return_value = False
        ebox.isATP.return_value = False
        ebox.mIsKVM.return_value = False
        ebox.SharedEnv.return_value = True
        ebox.mGetUUID.return_value = 'uuid'
        ebox.mGetClusterPath.return_value = '/cluster'
        ebox.mGetClusterName.return_value = 'cluster-name'
        ebox.mGetCmd.return_value = 'other'
        ebox.mGetOedaPath.return_value = '/oeda'
        ebox.mExecuteCmdLog2.return_value = (['output'], 'stderr-info')

        hc = DummyHealthCheck(ebox, cluster_hosts, recommend, json_map)
        options = SimpleNamespace(jsonconf={'dom0_verify': 'True'})
        test_obj = cluexachk(hc, options)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.datetime') as mock_datetime, \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch.dict(
                 'exabox.healthcheck.cluexachk.os.environ',
                 {
                     'PYTHONPATH': 'orig',
                     'RAT_ECRA': '1',
                     'RAT_ROOT_COLLECTIONS_IN_SERIAL': '1',
                     'RAT_NOCLEAN_DIR': '1'
                 },
                 clear=False
             ):
            mock_now = mock_datetime.now.return_value
            mock_now.strftime.return_value = '010203'
            test_obj.mRemoteRunExachk(options)

        ebox.mReleaseRemoteLock.assert_called_once()
        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Fail')
        self.assertIn('mExecuteCmd Failed', json_map['Exachk']['hostCheck'][host_key]['logs'][0])
        self.assertIn('mExecuteCmd Failed', recommend[-1])


    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_success_with_zip_dir_copies_and_renames(self):
        json_map = {}
        recommend = []

        node = MagicMock()
        node.mGetNodeType.return_value = 'dom0'
        node.mGetPingable.return_value = True
        node.mGetHostname.return_value = 'dom0-1'

        cluster_hosts = {'dom0-1': node}

        ebox = MagicMock()
        ebox.mCheckConfigOption.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-1'], ['domu-1'], [], [])
        ebox.mReturnDom0DomUNATPair.return_value = []
        ebox.mIsExabm.return_value = False
        ebox.mIsOciEXACC.return_value = False
        ebox.isATP.return_value = False
        ebox.mIsKVM.return_value = False
        ebox.SharedEnv.return_value = False
        ebox.mGetUUID.return_value = 'uuid'
        ebox.mGetClusterPath.return_value = '/cluster'
        ebox.mGetClusterName.return_value = 'CLUSTER'
        ebox.mGetOedaPath.return_value = '/oeda'
        ebox.mExecuteCmdLog2.return_value = ('stdout', '')
        ebox.mGetCmd.return_value = 'other'

        hc = DummyHealthCheck(ebox, cluster_hosts, recommend, json_map)
        hc.mGetHcConfig = lambda: {
            'diag_root': '/diag',
            'exachk_zip_dir': '/zipdest'
        }

        options = SimpleNamespace(jsonconf={
            'dom0_verify': 'True',
            'identitydir': '/identity/key',
            'other': '-profile custom'
        })

        test_obj = cluexachk(hc, options)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        ipmi_node = MagicMock()
        ipmi_node.mConnectTimed.return_value = None
        ipmi_node.mGetCmdExitStatus.return_value = False
        ipmi_out = MagicMock()
        ipmi_out.readlines.return_value = ['CLUSTER\n']
        ipmi_err = MagicMock()
        ipmi_err.readlines.return_value = []
        ipmi_node.mExecuteCmd.return_value = (None, ipmi_out, ipmi_err)

        extracted_files = []

        def fake_extract(file_name, dest):
            extracted_files.append((file_name, dest))

        def fake_stat(_):
            raise OSError()

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda payload: payload))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'))
            mock_remove_log_dest = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=fake_stat))
            mock_makedirs = stack.enter_context(patch('exabox.healthcheck.cluexachk.os.makedirs'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.glob.glob', return_value=['/tmp/exachk_010203.zip']))
            mock_zipfile = stack.enter_context(patch('exabox.healthcheck.cluexachk.zipfile.ZipFile'))
            mock_move = stack.enter_context(patch('exabox.healthcheck.cluexachk.shutil.move'))
            mock_make_archive = stack.enter_context(patch('exabox.healthcheck.cluexachk.shutil.make_archive'))
            mock_rmtree = stack.enter_context(patch('exabox.healthcheck.cluexachk.shutil.rmtree'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=ipmi_node))
            mock_datetime = stack.enter_context(patch('exabox.healthcheck.cluexachk.datetime'))
            stack.enter_context(patch.dict('exabox.healthcheck.cluexachk.os.environ', {
                'PYTHONPATH': 'orig',
                'RAT_ECRA': '1',
                'RAT_ROOT_COLLECTIONS_IN_SERIAL': '1',
                'RAT_NOCLEAN_DIR': '1'
            }, clear=False))

            mock_now = MagicMock()
            mock_now.strftime.return_value = '010203010101'
            mock_datetime.now.return_value = mock_now

            zip_mock = MagicMock()
            zip_mock.namelist.return_value = ['output/report.json', 'extra.txt']
            zip_mock.extract.side_effect = fake_extract
            mock_zipfile.return_value = zip_mock

            test_obj.mRemoteRunExachk(options)

        host_entry = json_map['Exachk']['hostCheck']['dom0-1']
        self.assertEqual(host_entry['TestResult'], 'Pass')
        self.assertNotIn('logs', host_entry)
        self.assertIn(('output/report.json', '/diag/diagnostic/results/exachk/'), extracted_files)
        zip_mock.close.assert_called_once()
        mock_move.assert_called_once()
        mock_make_archive.assert_called_once()
        mock_rmtree.assert_called_once()
        mock_remove_log_dest.assert_called_once_with('tmp_dest')
        self.assertGreaterEqual(mock_makedirs.call_count, 2)


    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_success_without_zip_dir_sets_permissions(self):
        json_map = {}
        recommend = []

        node = MagicMock()
        node.mGetNodeType.return_value = 'dom0'
        node.mGetPingable.return_value = True
        node.mGetHostname.return_value = 'dom0-1'

        cluster_hosts = {'dom0-1': node}

        ebox = MagicMock()
        ebox.mCheckConfigOption.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-1'], ['domu-1'], [], [])
        ebox.mReturnDom0DomUNATPair.return_value = []
        ebox.mIsExabm.return_value = False
        ebox.mIsOciEXACC.return_value = False
        ebox.isATP.return_value = False
        ebox.mIsKVM.return_value = False
        ebox.SharedEnv.return_value = False
        ebox.mGetUUID.return_value = 'uuid'
        ebox.mGetClusterPath.return_value = '/cluster'
        ebox.mGetOedaPath.return_value = '/oeda'
        ebox.mExecuteCmdLog2.return_value = ('stdout', '')
        ebox.mGetCmd.return_value = 'other'
        ebox.mGetClusterName.return_value = 'CLUSTER'

        hc = DummyHealthCheck(ebox, cluster_hosts, recommend, json_map)
        hc.mGetHcConfig = lambda: {
            'diag_root': '/diag'
        }

        options = SimpleNamespace(jsonconf={'dom0_verify': 'True'})

        test_obj = cluexachk(hc, options)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        def fake_stat(_):
            raise OSError()

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda payload: payload))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=fake_stat))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.makedirs'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.glob.glob', return_value=['/tmp/exachk_010203.zip']))
            mock_zipfile = stack.enter_context(patch('exabox.healthcheck.cluexachk.zipfile.ZipFile'))
            mock_move = stack.enter_context(patch('exabox.healthcheck.cluexachk.shutil.move'))
            mock_make_archive = stack.enter_context(patch('exabox.healthcheck.cluexachk.shutil.make_archive'))
            mock_rmtree = stack.enter_context(patch('exabox.healthcheck.cluexachk.shutil.rmtree'))
            mock_walk = stack.enter_context(patch('exabox.healthcheck.cluexachk.os.walk', return_value=[('ROOT', ['subdir'], ['file1.txt'])]))
            mock_chmod = stack.enter_context(patch('exabox.healthcheck.cluexachk.os.chmod'))
            mock_datetime = stack.enter_context(patch('exabox.healthcheck.cluexachk.datetime'))
            stack.enter_context(patch.dict('exabox.healthcheck.cluexachk.os.environ', {
                'PYTHONPATH': 'orig',
                'RAT_ECRA': '1',
                'RAT_ROOT_COLLECTIONS_IN_SERIAL': '1',
                'RAT_NOCLEAN_DIR': '1'
            }, clear=False))

            mock_now = MagicMock()
            mock_now.strftime.return_value = '010203010101'
            mock_datetime.now.return_value = mock_now

            zip_mock = MagicMock()
            zip_mock.namelist.return_value = ['output/report.json']
            mock_zipfile.return_value = zip_mock

            test_obj.mRemoteRunExachk(options)

        host_entry = json_map['Exachk']['hostCheck']['dom0-1']
        self.assertEqual(host_entry['TestResult'], 'Pass')
        self.assertNotIn('logs', host_entry)
        zip_mock.close.assert_called_once()
        mock_move.assert_not_called()
        mock_make_archive.assert_not_called()
        mock_rmtree.assert_not_called()
        mock_walk.assert_called_once()
        mock_chmod.assert_any_call('ROOT/subdir', 0o755)
        mock_chmod.assert_any_call('ROOT/file1.txt', 0o644)

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_success_path_returns_true(self):
        ebox = MagicMock()
        ebox.isATP.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'exascale-host'
        err_stream = MagicMock()
        err_stream.readlines.return_value = ['install ok']
        node.mExecuteCmd.return_value = (None, err_stream, None)
        node.mGetCmdExitStatus.return_value = False

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))

            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        node.mExecuteCmd.assert_called_once()

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_tfactl_failure_sets_ret_false(self):
        ebox = MagicMock()
        ebox.isATP.return_value = True
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'exascale-host'

        err_stream = MagicMock()
        err_stream.readlines.return_value = ['output']

        node.mExecuteCmd.side_effect = [
            (None, err_stream, None),
            (None, err_stream, None),
            (None, err_stream, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, False, True]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))

            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_chown_to_oracle_failure_returns_false(self):
        ebox = MagicMock()
        ebox.isATP.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'exascale-host'

        err_stream = MagicMock()
        err_stream.readlines.return_value = ['install ok']

        node.mExecuteCmd.return_value = (None, err_stream, None)
        node.mGetCmdExitStatus.return_value = False

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, False]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))

            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        node.mExecuteCmd.assert_called_once()

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_raises_exception_rethrows(self):
        ebox = MagicMock()
        ebox.isATP.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'exascale-host'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', side_effect=RuntimeError('copy failed')))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))

            with self.assertRaises(Exception):
                test_obj.mSetupAhfonExascale(
                    node,
                    'domU',
                    '/local/ahf_setup',
                    '/remote/bin',
                    '/remote/install',
                    '/remote/data'
                )

        node.mExecuteCmd.assert_not_called()


if __name__ == '__main__':
    unittest.main()


    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_success_logs_and_returns_true(self):
        ebox = MagicMock()
        ebox.mExecuteCmdLog2.return_value = ('success', [])
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.mkdir'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=SimpleNamespace(mGetBasePath=lambda: '/base')))

            @contextmanager
            def fake_lock(*_args, **_kwargs):
                yield True

            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_lock))
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertTrue(result)
        ebox.mExecuteCmdLog2.assert_called_once_with(
            '/ctrl/ahf_setup -silent -local -ahf_loc /ctrl/install -data_dir /ctrl/install -tmp_loc /tmp/cache'
        )

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_retry_success_after_uninstall(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-1'

        first_err = MagicMock()
        first_err.readlines.return_value = ['initial fail']
        second_err = MagicMock()
        second_err.readlines.return_value = ['retry success']

        node.mExecuteCmd.side_effect = [
            (None, first_err, None),
            (None, second_err, None)
        ]
        node.mGetCmdExitStatus.side_effect = [True, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=True))
            mock_uninstall = stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'dom0',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 2)
        mock_uninstall.assert_called_once_with(node, '/remote/install')

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_fresh_install_skips_uninstall_retry(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-1'

        err_stream = MagicMock()
        err_stream.readlines.return_value = ['failure']

        node.mExecuteCmd.return_value = (None, err_stream, None)
        node.mGetCmdExitStatus.return_value = True

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, True)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=True))
            mock_uninstall = stack.enter_context(patch.object(test_obj, 'mAhfUninstall'))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'dom0',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        mock_uninstall.assert_not_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_domU_tfactl_failure_sets_false(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

            def isATP(self):
                return True

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        node.mFileExists.side_effect = [True, True]

        err_stream = MagicMock()
        err_stream.readlines.return_value = ['ok']

        node.mExecuteCmd.side_effect = [
            (None, err_stream, None),
            (None, err_stream, None),
            (None, err_stream, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, True, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mRetriveAhfInstallDataPath', return_value='/other/path'))
            stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteDataDir'))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mGetHigherAHFPath', return_value='/remote/bin'))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'domU',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_success_with_atp_settings(self):
        class DummyEbox(object):
            def isATP(self):
                return True

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'

        err_stream = MagicMock()
        err_stream.readlines.return_value = ['ok']

        node.mExecuteCmd.side_effect = [
            (None, err_stream, None),
            (None, err_stream, None),
            (None, err_stream, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, False, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)


    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_domU_chown_success_branch(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        ebox.IsZdlraProv.return_value = False
        ebox.isATP.return_value = False
        ebox.mCheckSubConfigOption.side_effect = ['/remote/data', '/remote/data']

        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-host'
        node.mFileExists.side_effect = [True, True]

        install_log = MagicMock()
        install_log.readlines.return_value = ['install ok']

        node.mExecuteCmd.return_value = (None, install_log, None)
        node.mGetCmdExitStatus.return_value = False

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteDataDir'))
            stack.enter_context(patch.object(test_obj, 'mRetriveAhfInstallDataPath', return_value='/different'))
            stack.enter_context(patch.object(test_obj, 'mGetHigherAHFPath', return_value='/remote/bin'))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            mock_chown = stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))

            result = test_obj.mSetupAhfonRemote(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 1)
        self.assertEqual(
            mock_chown.call_args_list,
            [call(node, '/remote/data', 'root', 'root'), call(node, '/remote/data', 'oracle', 'oinstall')]
        )

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_retry_success_logs(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-host'
        node.mFileExists.side_effect = [True, True]

        first_err = MagicMock()
        first_err.readlines.return_value = ['first failure']
        second_err = MagicMock()
        second_err.readlines.return_value = ['retry success']

        node.mExecuteCmd.side_effect = [
            (None, first_err, None),
            (None, second_err, None)
        ]
        node.mGetCmdExitStatus.side_effect = [True, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            mock_uninstall = stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            log_info = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            log_health = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))

            result = test_obj.mSetupAhfonRemote(
                node,
                'dom0',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 2)
        mock_uninstall.assert_called_once_with(node, '/remote/install')
        log_info.assert_any_call('*** installing AHF Image on dom0-host , device type dom0 in progress...')
        log_health.assert_any_call('NFO', '*** AHF : Retry Installation Success. Installtion command output for host : %s' % (node.mGetHostname()))

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_domU_autopurge_success(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

            def IsZdlraProv(self):
                return False

            def isATP(self):
                return True

            def mCheckSubConfigOption(self, *_args):
                return '/remote/data'

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-host'
        node.mFileExists.side_effect = [True, True]

        install_log = MagicMock()
        install_log.readlines.return_value = ['install ok']
        sanitize_log = MagicMock()
        sanitize_log.readlines.return_value = ['sanitize ok']

        node.mExecuteCmd.side_effect = [
            (None, install_log, None),
            (None, sanitize_log, None),
            (None, sanitize_log, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, False, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteDataDir'))
            stack.enter_context(patch.object(test_obj, 'mRetriveAhfInstallDataPath', return_value='/other'))
            stack.enter_context(patch.object(test_obj, 'mGetHigherAHFPath', return_value='/remote/bin'))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))

            result = test_obj.mSetupAhfonRemote(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)
        node.mExecuteCmd.assert_any_call('(/remote/install/oracle.ahf/bin/tfactl set redact=SANITIZE )')
        node.mExecuteCmd.assert_any_call('(/remote/install/oracle.ahf/bin/tfactl set manageLogsAutoPurge=ON )')

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_domU_skips_install_when_data_path_matches(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

            def IsZdlraProv(self):
                return False

            def isATP(self):
                return False

            def mCheckSubConfigOption(self, *_args):
                return '/remote/data'

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-host'
        node.mFileExists.side_effect = [True, True]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(False, False)))
            mock_remove = stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            mock_copy = stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            mock_uninstall = stack.enter_context(patch.object(test_obj, 'mAhfUninstall'))
            mock_delete = stack.enter_context(patch.object(test_obj, 'mDeleteDataDir'))
            mock_chown = stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip'))
            stack.enter_context(patch.object(test_obj, 'mRetriveAhfInstallDataPath', return_value='/remote/data/u02'))
            stack.enter_context(patch.object(test_obj, 'mGetHigherAHFPath'))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus'))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))

            result = test_obj.mSetupAhfonRemote(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        mock_remove.assert_called_once_with(node)
        mock_copy.assert_called_once_with(node, '/local/ahf_setup', '/remote/bin')
        mock_uninstall.assert_not_called()
        mock_delete.assert_not_called()
        mock_chown.assert_not_called()
        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_success_logs_branch(self):
        ebox = MagicMock()
        ebox.mExecuteCmdLog2.return_value = ('success log', [])
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base'

        @contextmanager
        def fake_lock(*_args, **_kwargs):
            yield True

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.mkdir'))
            log_info = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            log_health = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_lock))

            result = test_obj.mSetupAhfonCtrlPlane('/local/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertTrue(result)
        log_info.assert_any_call('*** installing AHF Image on path /ctrl/install of control plane in progress...')
        log_health.assert_any_call('NFO', '*** AHF : Install success on control plane : %s: ' % (str('success log')))

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_exascale_branch_calls_exascale_setup(self):
        ebox = MagicMock()
        ebox.mGetEbox.return_value = ebox
        ebox.mIsExaScale.return_value = True
        ebox.mReturnAllClusterHosts.return_value = ([], ['domu-host'], [], [])
        ebox.mCheckSubConfigOption.side_effect = lambda section, key: {
            ('ahf_paths', 'remote_ahf_bin_path'): '/remote/bin',
            ('ahf_paths', 'remote_ahf_data_path_domu'): '/remote/data'
        }[(section, key)]
        ebox.mCheckConfigOption.return_value = False

        hc = DummyHealthCheck(ebox, {'domu-host': MagicMock()}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        class DummyProcessStructure(object):
            def __init__(self, target, args):
                self._target = target
                self._args = args

            def mSetMaxExecutionTime(self, *_args):
                pass

            def mSetJoinTimeout(self, *_args):
                pass

            def mSetLogTimeoutFx(self, *_args):
                pass

            def run(self):
                self._target(*self._args)

        class DummyProcessManager(object):
            def __init__(self):
                self._procs = []

            def mStartAppend(self, proc):
                self._procs.append(proc)

            def mJoinProcess(self):
                for proc in self._procs:
                    proc.run()

        dummy_node = MagicMock()

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base/'

        @contextmanager
        def fake_connect(*_args, **_kwargs):
            yield dummy_node

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value=None))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=DummyProcessManager()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', side_effect=lambda f, a: DummyProcessStructure(f, a)))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=dummy_node))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.connect_to_host', side_effect=fake_connect))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            mock_exascale = stack.enter_context(patch.object(test_obj, 'mSetupAhfonExascale', return_value=True))
            mock_remote = stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', return_value=False))

        result = test_obj.mInstallAhf('domU', SimpleNamespace(jsonconf={}))

        self.assertTrue(result['domu-host'])
        mock_exascale.assert_called_once()
        mock_remote.assert_not_called()

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_dom0_success_records_result_and_releases_lock(self):
        ebox = MagicMock()
        ebox.mGetEbox.return_value = ebox
        ebox.mIsExaScale.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], ['domu-host'], [], [])
        ebox.mCheckSubConfigOption.side_effect = lambda section, key: {
            ('ahf_paths', 'remote_ahf_bin_path'): '/remote/bin',
            ('ahf_paths', 'remote_ahf_data_path_dom0'): '/remote/data'
        }[(section, key)]
        ebox.mCheckConfigOption.return_value = False

        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        dummy_node = MagicMock()

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base/'

        class DummyProcessStructure(object):
            def __init__(self, target, args):
                self._target = target
                self._args = args

            def mSetMaxExecutionTime(self, *_args):
                return None

            def mSetJoinTimeout(self, *_args):
                return None

            def mSetLogTimeoutFx(self, *_args):
                return None

            def run(self):
                self._target(*self._args)

        class DummyProcessManager(object):
            def __init__(self):
                self._procs = []

            def mStartAppend(self, proc):
                self._procs.append(proc)

            def mJoinProcess(self):
                for proc in self._procs:
                    proc.run()

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', side_effect=['tmp_dest', None]))
            remove_dest = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=DummyProcessManager()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', side_effect=lambda f, a: DummyProcessStructure(f, a)))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=dummy_node))
            setup_remote = stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', return_value=True))

            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={}))

        self.assertEqual(result, {'dom0-host': True})
        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()
        setup_remote.assert_called_once()
        dummy_node.mSetUser.assert_called_once_with('root')
        dummy_node.mConnectTimed.assert_called_once_with(aHost='dom0-host', aTimeout='10')
        remove_dest.assert_called_once_with('tmp_dest')

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_records_failed_host_when_setup_returns_false(self):
        ebox = MagicMock()
        ebox.mGetEbox.return_value = ebox
        ebox.mIsExaScale.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])

        def sub_config(section, key):
            mapping = {
                ('ahf_paths', 'remote_ahf_bin_path'): '/remote/bin',
                ('ahf_paths', 'remote_ahf_data_path_dom0'): '/remote/data',
            }
            return mapping[(section, key)]

        ebox.mCheckSubConfigOption.side_effect = sub_config
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mAcquireRemoteLock = MagicMock()
        ebox.mReleaseRemoteLock = MagicMock()

        hc = DummyHealthCheck(ebox, {'dom0-host': MagicMock()}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        class DummyProcessStructure(object):
            def __init__(self, target, args):
                self._target = target
                self._args = args

            def mSetMaxExecutionTime(self, *_args):
                pass

            def mSetJoinTimeout(self, *_args):
                pass

            def mSetLogTimeoutFx(self, *_args):
                pass

            def run(self):
                self._target(*self._args)

        class DummyProcessManager(object):
            def __init__(self):
                self._procs = []

            def mStartAppend(self, proc):
                self._procs.append(proc)

            def mJoinProcess(self):
                for proc in self._procs:
                    proc.run()

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base/'

        class DummyNode(object):
            def mSetUser(self, user):
                self.user = user

            def mConnectTimed(self, aHost, aTimeout):
                self._last_connect = (aHost, aTimeout)

            def mGetHostname(self):
                return 'dom0-host'

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'))
            remove_dest = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=DummyProcessManager()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', side_effect=lambda f, a: DummyProcessStructure(f, a)))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=DummyNode()))
            setup_remote = stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', return_value=False))

            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {'dom0-host': False})
        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()
        setup_remote.assert_called_once()
        remove_dest.assert_called_once_with('tmp_dest')

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_skips_host_when_connection_fails(self):
        ebox = MagicMock()
        ebox.mGetEbox.return_value = ebox
        ebox.mIsExaScale.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])

        def sub_config(section, key):
            mapping = {
                ('ahf_paths', 'remote_ahf_bin_path'): '/remote/bin',
                ('ahf_paths', 'remote_ahf_data_path_dom0'): '/remote/data',
            }
            return mapping[(section, key)]

        ebox.mCheckSubConfigOption.side_effect = sub_config
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mAcquireRemoteLock = MagicMock()
        ebox.mReleaseRemoteLock = MagicMock()

        hc = DummyHealthCheck(ebox, {'dom0-host': MagicMock()}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        class DummyProcessStructure(object):
            def __init__(self, target, args):
                self._target = target
                self._args = args

            def mSetMaxExecutionTime(self, *_args):
                pass

            def mSetJoinTimeout(self, *_args):
                pass

            def mSetLogTimeoutFx(self, *_args):
                pass

            def run(self):
                self._target(*self._args)

        class DummyProcessManager(object):
            def __init__(self):
                self._procs = []

            def mStartAppend(self, proc):
                self._procs.append(proc)

            def mJoinProcess(self):
                for proc in self._procs:
                    proc.run()

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base/'

        class FailingNode(object):
            def mSetUser(self, user):
                self.user = user

            def mConnectTimed(self, aHost, aTimeout):
                raise RuntimeError('connect failed')

            def mGetHostname(self):
                return 'dom0-host'

        with ExitStack() as stack:
            mock_info = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=DummyProcessManager()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', side_effect=lambda f, a: DummyProcessStructure(f, a)))

            def node_factory(*_args, **_kwargs):
                return FailingNode()

            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', side_effect=node_factory))
            setup_remote = stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote'))

            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {})
        mock_info.assert_any_call('WARNING: CheckInfo failed to connect to: dom0-host ')
        setup_remote.assert_not_called()
        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_sanitize_commands_success(self):
        ebox = MagicMock()
        ebox.isATP.return_value = True
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-host'
        node.mFileExists.side_effect = [True, True]

        install_log = MagicMock()
        install_log.readlines.return_value = ['install ok']
        tfactl_log = MagicMock()
        tfactl_log.readlines.return_value = ['tfactl ok']

        node.mExecuteCmd.side_effect = [
            (None, install_log, None),
            (None, tfactl_log, None),
            (None, tfactl_log, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, False, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))

            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        node.mExecuteCmd.assert_any_call('(/remote/install/oracle.ahf/bin/tfactl set redact=SANITIZE )')
        node.mExecuteCmd.assert_any_call('(/remote/install/oracle.ahf/bin/tfactl set manageLogsAutoPurge=ON )')
    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_handles_tfactl_failure(self):
        class DummyEbox(object):
            def isATP(self):
                return True

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'

        err_stream = MagicMock()
        err_stream.readlines.return_value = ['ok']

        node.mExecuteCmd.side_effect = [
            (None, err_stream, None),
            (None, err_stream, None),
            (None, err_stream, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, True, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)

    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_install_success_branch(self):
        ebox = MagicMock()
        ebox.mExecuteCmdLog2.return_value = ('install ok', [])
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        @contextmanager
        def fake_lock(*_args, **_kwargs):
            yield True

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.mkdir'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_lock))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            mock_health = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertTrue(result)
        ebox.mExecuteCmdLog2.assert_called_once_with('/ctrl/ahf_setup -silent -local -ahf_loc /ctrl/install -data_dir /ctrl/install -tmp_loc /tmp/cache')
        self.assertTrue(mock_health.called)

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_success_without_retry(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-1'
        node.mFileExists.side_effect = [True, True]

        install_err = MagicMock()
        install_err.readlines.return_value = ['success']
        node.mExecuteCmd.return_value = (None, install_err, None)
        node.mGetCmdExitStatus.return_value = False

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=True))
            mock_uninstall = stack.enter_context(patch.object(test_obj, 'mAhfUninstall'))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            mock_health = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'dom0',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        node.mExecuteCmd.assert_called_once()
        mock_uninstall.assert_not_called()
        self.assertTrue(mock_health.called)


    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_second_tfactl_failure(self):
        class DummyEbox(object):
            def isATP(self):
                return True

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'

        install_err = MagicMock()
        install_err.readlines.return_value = ['install ok']
        tfactl_ok = MagicMock()
        tfactl_ok.readlines.return_value = ['tfactl ok']
        tfactl_fail = MagicMock()
        tfactl_fail.readlines.return_value = ['tfactl fail']

        node.mExecuteCmd.side_effect = [
            (None, install_err, None),
            (None, tfactl_ok, None),
            (None, tfactl_fail, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, False, True]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_exception_rethrows_and_restores_ownership(self):
        class DummyEbox(object):
            def isATP(self):
                return False

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, Exception('chown failure')]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            with self.assertRaises(Exception):
                test_obj.mSetupAhfonExascale(
                    node,
                    'domU',
                    '/ctrl/ahf_setup',
                    '/remote/bin',
                    '/remote/install',
                    '/remote/data'
                )

        # First call succeeded, second raised and should trigger final exception
        self.assertEqual(test_obj.mChgFolderOwnShip.call_count, 2)

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_returns_false_when_initial_chown_fails(self):
        ebox = MagicMock()
        ebox.isATP.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'exascale-host'

        with ExitStack() as stack:
            mock_chown = stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=False))
            mock_copy = stack.enter_context(patch.object(test_obj, 'mCopyAhfImage'))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            mock_log_error = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))

            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        mock_chown.assert_called_once_with(node, '/remote/data', 'root', 'root')
        mock_copy.assert_not_called()
        mock_log_error.assert_called()


    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_install_success_path(self):
        ebox = MagicMock()
        ebox.mExecuteCmdLog2.return_value = ('success', [])
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        @contextmanager
        def fake_lock(*_args, **_kwargs):
            yield True

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.mkdir'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_lock))
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertTrue(result)
        ebox.mExecuteCmdLog2.assert_called_once_with('/ctrl/ahf_setup -silent -local -ahf_loc /ctrl/install -data_dir /ctrl/install -tmp_loc /tmp/cache')

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_returns_false_when_copy_fails(self):
        ebox = MagicMock()
        ebox.isATP.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'exascale-host'

        with ExitStack() as stack:
            mock_chown = stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=True))
            mock_copy = stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=False))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            mock_log_error = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))

            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/local/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        mock_chown.assert_called_once_with(node, '/remote/data', 'root', 'root')
        mock_copy.assert_called_once_with(node, '/local/ahf_setup', '/remote/bin')
        mock_log_error.assert_called()


    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_install_success_branch(self):
        ebox = MagicMock()
        ebox.mExecuteCmdLog2.return_value = ('success', [])
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        @contextmanager
        def fake_lock(*_args, **_kwargs):
            yield True

        class DummyContext(object):
            def mGetBasePath(self):
                return '/base'

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.mkdir'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=DummyContext()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_lock))
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/ahf_setup', '/ctrl/install', '/tmp/cache')

        self.assertTrue(result)
        ebox.mExecuteCmdLog2.assert_called_once_with('/ctrl/ahf_setup -silent -local -ahf_loc /ctrl/install -data_dir /ctrl/install -tmp_loc /tmp/cache')

    # Auto-generated test for mCopyAhfImage
    def test_mCopyAhfImage_returns_false_when_disk_space_low(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        low_space = MagicMock()
        low_space.readlines.return_value = ['low']
        node.mExecuteCmd.return_value = (None, low_space, None)

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            mock_log_error = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mCopyAhfImage(node, '/local/ahf_setup', '/remote/bin')

        self.assertFalse(result)
        node.mExecuteCmd.assert_called_once_with("df -PBM / | tail -1| awk '0+$4 <= 150  {print}'")
        node.mCopyFile.assert_not_called()
        self.assertTrue(any('Not enough space' in args[0] for args, _ in mock_log_error.call_args_list))

    # Auto-generated test for mCopyAhfImage
    def test_mCopyAhfImage_logs_error_when_local_image_missing(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        disk_ok = MagicMock()
        disk_ok.readlines.return_value = []
        node.mExecuteCmd.return_value = (None, disk_ok, None)

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=False))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            mock_log_error = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mCopyAhfImage(node, '/missing/ahf_setup', '/remote/bin')

        self.assertFalse(result)
        mock_log_error.assert_any_call('*** Local Ahf Image : /missing/ahf_setup not found !')
        node.mFileExists.assert_not_called()
        node.mCopyFile.assert_not_called()

    # Auto-generated test for mCopyAhfImage
    def test_mCopyAhfImage_returns_false_when_chmod_fails(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        disk_ok = MagicMock()
        disk_ok.readlines.return_value = []
        chmod_log = MagicMock()
        chmod_log.readlines.return_value = ['permission denied']
        node.mExecuteCmd.side_effect = [
            (None, disk_ok, None),
            (None, chmod_log, None)
        ]
        node.mFileExists.side_effect = [False]
        node.mGetCmdExitStatus.return_value = True

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            mock_log_error = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mCopyAhfImage(node, '/local/ahf_setup', '/remote/bin')

        self.assertFalse(result)
        node.mMakeDir.assert_called_once_with('/remote/bin')
        node.mCopyFile.assert_called_once_with('/local/ahf_setup', '/remote/bin/ahf_setup')
        mock_log_error.assert_any_call('*** could not change ahf_setup permissions for host - domu-1')

    # Auto-generated test for mCopyAhfImage
    def test_mCopyAhfImage_handles_copy_exception(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        disk_ok = MagicMock()
        disk_ok.readlines.return_value = []
        node.mExecuteCmd.return_value = (None, disk_ok, None)
        node.mFileExists.side_effect = [True, False]
        node.mCopyFile.side_effect = RuntimeError('copy failed')

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            mock_log_error = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mCopyAhfImage(node, '/local/ahf_setup', '/remote/bin')

        self.assertFalse(result)
        mock_log_error.assert_any_call('*** AHF image copy failed for host: domu-1 with error copy failed')
        node.mGetCmdExitStatus.assert_not_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_domU_root_chown_failure_returns_false(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

            def IsZdlraProv(self):
                return False

            def isATP(self):
                return False

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-2'
        node.mFileExists.side_effect = [True, True]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(True, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mRetriveAhfInstallDataPath', return_value='/tmp/ahf'))
            stack.enter_context(patch.object(test_obj, 'mAhfUninstall', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteDataDir'))
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', return_value=False))
            stack.enter_context(patch.object(test_obj, 'mGetHigherAHFPath', return_value='/remote/bin'))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'domU',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_upgrade_skip_returns_true(self):
        ebox = MagicMock()
        ebox.mIsOciEXACC.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mFileExists.side_effect = [True, True]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mAhfRemoteVersionCheck', return_value=(False, False)))
            stack.enter_context(patch.object(test_obj, 'mRemoveOldExachk'))
            mock_copy = stack.enter_context(patch.object(test_obj, 'mCopyAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonRemote(
                node,
                'dom0',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        mock_copy.assert_not_called()
        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_full_success_with_tfactl_settings(self):
        class DummyEbox(object):
            def isATP(self):
                return True

        ebox = DummyEbox()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-success'

        install_err = MagicMock()
        install_err.readlines.return_value = ['install ok']
        tfactl_first = MagicMock()
        tfactl_first.readlines.return_value = ['tfactl sanitize ok']
        tfactl_second = MagicMock()
        tfactl_second.readlines.return_value = ['tfactl purge ok']

        node.mExecuteCmd.side_effect = [
            (None, install_err, None),
            (None, tfactl_first, None),
            (None, tfactl_second, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, False, False]

        with ExitStack() as stack:
            stack.enter_context(patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]))
            stack.enter_context(patch.object(test_obj, 'mCopyAhfImage', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mGetTFACTLStatus', return_value=True))
            stack.enter_context(patch.object(test_obj, 'mDeleteAhfImage'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogInfo'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogHealth'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/ctrl/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_skips_when_not_exacc(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.connect_to_host'))
            test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        ebox.mGetOciExacc.assert_called_once()

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_warns_when_host_missing(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        ebox.mCheckConfigOption.return_value = None
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with ExitStack() as stack:
            mock_warn = stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.connect_to_host'))
            test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        mock_warn.assert_called()

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_success_calls_setup_with_defaults(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        ebox.mCheckConfigOption.side_effect = ['remote-host']
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        fake_node = MagicMock()

        @contextmanager
        def fake_connect(*_args, **_kwargs):
            yield fake_node

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', return_value=True))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.connect_to_host', new=fake_connect))
            test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        test_obj.mSetupAhfonRemote.assert_called_once()

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_honors_options_and_propagates_exception(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        ebox.mCheckConfigOption.side_effect = ['remote-host']
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/custom/install'}))

        fake_node = MagicMock()

        @contextmanager
        def fake_connect(*_args, **_kwargs):
            yield fake_node

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.get_gcontext'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.connect_to_host', new=fake_connect))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.os.path.join', return_value='/joined'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', side_effect=RuntimeError('boom')))
            with self.assertRaises(RuntimeError):
                test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={'ahf_install_path': '/custom/install'}))

        test_obj.mSetupAhfonRemote.assert_called_once()

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_early_return_for_invalid_paths(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.return_value = 'relative/path'
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        hc = DummyHealthCheck(ebox, {'host': MagicMock()}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': 'relative'}))

        self.assertIsNone(result)

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_connect_failure_skips_host_and_returns_empty(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])
        ebox.mIsExaScale.return_value = False
        hc = DummyHealthCheck(ebox, {'dom0-host': MagicMock()}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        def fake_node_factory(*_args, **_kwargs):
            raise RuntimeError('connect fail')

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', side_effect=fake_node_factory))
            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {})

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_success_path_records_per_host_results(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], ['domu-host'], [], [])
        ebox.mIsExaScale.return_value = False
        ebox.mAcquireRemoteLock.return_value = None
        ebox.mReleaseRemoteLock.return_value = None
        hc = DummyHealthCheck(ebox, {
            'dom0-host': MagicMock(),
            'domu-host': MagicMock(),
        }, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        fake_node = MagicMock()
        fake_node.mGetHostname.return_value = 'dom0-host'

        def fake_node_factory(*_args, **_kwargs):
            return fake_node

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            proc_mgr = MagicMock()
            proc_mgr.mJoinProcess = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=proc_mgr))
            proc_struct = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', return_value=proc_struct))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', side_effect=fake_node_factory))
            stack.enter_context(patch.object(fake_node, 'mConnectTimed'))
            stack.enter_context(patch.object(fake_node, 'mSetUser'))
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', return_value=True))
            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {'dom0-host': True})

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_selected_host_filters_execution(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host1', 'dom0-host2'], [], [], [])
        ebox.mIsExaScale.return_value = False
        hc = DummyHealthCheck(ebox, {
            'dom0-host1': MagicMock(),
            'dom0-host2': MagicMock(),
        }, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        fake_node = MagicMock()
        fake_node.mGetHostname.return_value = 'dom0-host1'

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            proc_mgr = MagicMock()
            proc_mgr.mJoinProcess = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=proc_mgr))
            proc_struct = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', return_value=proc_struct))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=fake_node))
            stack.enter_context(patch.object(fake_node, 'mConnectTimed'))
            stack.enter_context(patch.object(fake_node, 'mSetUser'))
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', return_value=True))
            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}), _selected_host='dom0-host1')

        self.assertEqual(result, {'dom0-host1': True})

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_domU_skips_lock_and_uses_exascale(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = ([], ['domu-host'], [], [])
        ebox.mIsExaScale.return_value = True
        hc = DummyHealthCheck(ebox, {
            'domu-host': MagicMock(),
        }, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        fake_node = MagicMock()
        fake_node.mGetHostname.return_value = 'domu-host'

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            proc_mgr = MagicMock()
            proc_mgr.mJoinProcess = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=proc_mgr))
            proc_struct = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', return_value=proc_struct))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=fake_node))
            stack.enter_context(patch.object(fake_node, 'mConnectTimed'))
            stack.enter_context(patch.object(fake_node, 'mSetUser'))
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonExascale', return_value=True))
            result = test_obj.mInstallAhf('domU', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {'domu-host': True})

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_handles_setup_failure_and_records_false(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])
        ebox.mIsExaScale.return_value = False
        ebox.mAcquireRemoteLock.return_value = None
        ebox.mReleaseRemoteLock.return_value = None
        hc = DummyHealthCheck(ebox, {
            'dom0-host': MagicMock(),
        }, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        fake_node = MagicMock()
        fake_node.mGetHostname.return_value = 'dom0-host'

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            proc_mgr = MagicMock()
            proc_mgr.mJoinProcess = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=proc_mgr))
            proc_struct = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', return_value=proc_struct))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=fake_node))
            stack.enter_context(patch.object(fake_node, 'mConnectTimed'))
            stack.enter_context(patch.object(fake_node, 'mSetUser'))
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', return_value=False))
            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {'dom0-host': False})

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_logs_and_returns_on_unknown_device(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            result = test_obj.mInstallAhf('unknown', SimpleNamespace(jsonconf={}))

        self.assertIsNone(result)
        mock_error.assert_called()

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_handles_exception_from_setup(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])
        ebox.mIsExaScale.return_value = False
        ebox.mAcquireRemoteLock.return_value = None
        ebox.mReleaseRemoteLock.return_value = None
        hc = DummyHealthCheck(ebox, {
            'dom0-host': MagicMock(),
        }, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        fake_node = MagicMock()
        fake_node.mGetHostname.return_value = 'dom0-host'

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            proc_mgr = MagicMock()
            proc_mgr.mJoinProcess = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=proc_mgr))
            proc_struct = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', return_value=proc_struct))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=fake_node))
            stack.enter_context(patch.object(fake_node, 'mConnectTimed'))
            stack.enter_context(patch.object(fake_node, 'mSetUser'))
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', side_effect=RuntimeError('boom')))
            with self.assertRaises(RuntimeError):
                test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_skips_when_not_exacc(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with patch('exabox.healthcheck.cluexachk.connect_to_host') as mock_connect:
            result = test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        self.assertIsNone(result)
        mock_connect.assert_not_called()

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_warns_when_host_missing(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        ebox.mCheckConfigOption.return_value = None
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with patch('exabox.healthcheck.cluexachk.ebLogWarn') as mock_warn, \
             patch.object(test_obj, 'mSetupAhfonRemote') as mock_setup, \
             patch('exabox.healthcheck.cluexachk.connect_to_host') as mock_connect:
            result = test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        self.assertIsNone(result)
        mock_warn.assert_called()
        mock_setup.assert_not_called()
        mock_connect.assert_not_called()

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_invokes_remote_setup(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        ebox.mCheckConfigOption.return_value = 'remote-host'
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        dummy_context = MagicMock()
        dummy_context.mGetBasePath.return_value = '/base'
        node_obj = MagicMock()

        captured = {}

        @contextmanager
        def fake_connect(host, ctx):
            captured['host'] = host
            captured['ctx'] = ctx
            yield node_obj

        with patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=dummy_context), \
             patch('exabox.healthcheck.cluexachk.connect_to_host', side_effect=fake_connect), \
             patch.object(test_obj, 'mSetupAhfonRemote', return_value=True) as mock_setup:
            result = test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        self.assertIsNone(result)
        self.assertEqual(captured['host'], 'remote-host')
        self.assertIs(captured['ctx'], dummy_context)
        mock_setup.assert_called_once_with(
            node_obj,
            'standby_cps',
            os.path.join('/base', 'ahf_setup'),
            '/base',
            os.path.join('/base', 'ahf_install'),
            os.path.join('/base', 'ahf_install')
        )

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_raises_when_connect_fails(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        ebox.mCheckConfigOption.return_value = 'remote-host'
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        dummy_context = MagicMock()
        dummy_context.mGetBasePath.return_value = '/base'

        @contextmanager
        def fake_connect(*_args, **_kwargs):
            raise RuntimeError('connect failed')
            yield

        with patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=dummy_context), \
             patch('exabox.healthcheck.cluexachk.connect_to_host', side_effect=fake_connect), \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_log:
            with self.assertRaises(Exception) as ctx:
                test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        self.assertIn('connect failed', str(ctx.exception))
        mock_log.assert_called()

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_releases_lock_on_process_structure_error(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])
        ebox.mIsExaScale.return_value = False
        ebox.mAcquireRemoteLock = MagicMock()
        ebox.mReleaseRemoteLock = MagicMock()
        hc = DummyHealthCheck(ebox, {
            'dom0-host': MagicMock(),
        }, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=MagicMock()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', side_effect=RuntimeError('boom')))
            with self.assertRaises(RuntimeError):
                test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()

    # Auto-generated test for mDeleteAhfImage
    def test_mDeleteAhfImage_skips_when_copy_path_missing(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))
        test_obj.ahf_copy_path = '/remote/ahf_setup'

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        node.mFileExists.return_value = False

        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info, \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            test_obj.mDeleteAhfImage(node)

        node.mExecuteCmd.assert_not_called()
        mock_error.assert_not_called()
        mock_info.assert_called_once()

    # Auto-generated test for mDeleteAhfImage
    def test_mDeleteAhfImage_executes_rm_on_success(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))
        test_obj.ahf_copy_path = '/remote/ahf_setup'

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        node.mFileExists.return_value = True
        node.mExecuteCmd.return_value = (None, MagicMock(), None)
        node.mGetCmdExitStatus.return_value = False

        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info, \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            test_obj.mDeleteAhfImage(node)

        node.mExecuteCmd.assert_called_once_with('rm /remote/ahf_setup')
        mock_error.assert_not_called()
        self.assertGreaterEqual(mock_info.call_count, 2)

    # Auto-generated test for mDeleteAhfImage
    def test_mDeleteAhfImage_logs_error_on_rm_failure(self):
        ebox = MagicMock()
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))
        test_obj.ahf_copy_path = '/remote/ahf_setup'

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        node.mFileExists.return_value = True
        err_stream = MagicMock()
        node.mExecuteCmd.return_value = (None, err_stream, None)
        node.mGetCmdExitStatus.return_value = True

        with patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            test_obj.mDeleteAhfImage(node)

        node.mExecuteCmd.assert_called_once_with('rm /remote/ahf_setup')
        mock_error.assert_called()

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_lock_acquisition_failure_returns_empty(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])
        ebox.mIsExaScale.return_value = False
        ebox.mAcquireRemoteLock.return_value = False
        ebox.mReleaseRemoteLock = MagicMock()
        hc = DummyHealthCheck(ebox, {'dom0-host': MagicMock()}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        fake_node = MagicMock()
        fake_node.mGetHostname.return_value = 'dom0-host'

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            proc_mgr = MagicMock()
            proc_mgr.mJoinProcess = MagicMock()
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=proc_mgr))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', return_value=MagicMock()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=fake_node))

            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {})
        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()
        fake_node.mConnectTimed.assert_not_called()

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_process_manager_dispatch_failure_marks_host_false(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])
        ebox.mIsExaScale.return_value = False
        ebox.mAcquireRemoteLock = MagicMock()
        ebox.mReleaseRemoteLock = MagicMock()
        hc = DummyHealthCheck(ebox, {'dom0-host': MagicMock()}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        fake_node = MagicMock()
        fake_node.mGetHostname.return_value = 'dom0-host'

        class DummyProcessStructure(object):
            def __init__(self, func, args):
                self._func = func
                self._args = args

            def mSetMaxExecutionTime(self, *_args, **_kwargs):
                return self

            def mSetJoinTimeout(self, *_args, **_kwargs):
                return self

            def mSetLogTimeoutFx(self, *_args, **_kwargs):
                return self

        process_manager = MagicMock()
        process_manager.mJoinProcess = MagicMock()

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=process_manager))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', side_effect=lambda func, args: DummyProcessStructure(func, args)))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=fake_node))
            stack.enter_context(patch.object(fake_node, 'mSetUser'))
            stack.enter_context(patch.object(fake_node, 'mConnectTimed'))
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', return_value=False))

            def fake_start_append(process):
                process._func(*process._args)
                raise RuntimeError('dispatch failed')

            process_manager.mStartAppend.side_effect = fake_start_append

            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {'dom0-host': False})
        process_manager.mStartAppend.assert_called_once()
        fake_node.mSetUser.assert_called_once_with('root')
        fake_node.mConnectTimed.assert_called_once_with(aHost='dom0-host', aTimeout='10')
        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()
    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_lock_acquisition_failure_returns_empty(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])
        ebox.mIsExaScale.return_value = False
        ebox.mAcquireRemoteLock.return_value = False
        hc = DummyHealthCheck(ebox, {'dom0-host': MagicMock()}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure'))

            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {})
        ebox.mAcquireRemoteLock.assert_called_once()

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_process_manager_dispatch_failure_marks_host_false(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])
        ebox.mIsExaScale.return_value = False
        hc = DummyHealthCheck(ebox, {'dom0-host': MagicMock()}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        fake_node = MagicMock()
        fake_node.mGetHostname.return_value = 'dom0-host'

        class DummyProcessStructure(object):
            def __init__(self, func, args):
                self._func = func
                self._args = args

            def mSetMaxExecutionTime(self, *_args, **_kwargs):
                return self

            def mSetJoinTimeout(self, *_args, **_kwargs):
                return self

            def mSetLogTimeoutFx(self, *_args, **_kwargs):
                return self

        process_manager = MagicMock()

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=process_manager))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', side_effect=lambda func, args: DummyProcessStructure(func, args)))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=fake_node))
            stack.enter_context(patch.object(fake_node, 'mSetUser'))
            stack.enter_context(patch.object(fake_node, 'mConnectTimed'))
            stack.enter_context(patch.object(test_obj, 'mSetupAhfonRemote', return_value=False))

            def fake_start_append(process):
                process._func(*process._args)
                raise RuntimeError('dispatch failed')

            process_manager.mStartAppend.side_effect = fake_start_append

            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        self.assertEqual(result, {'dom0-host': False})
        fake_node.mSetUser.assert_called_once_with('root')
        fake_node.mConnectTimed.assert_called_once_with(aHost='dom0-host', aTimeout='10')

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_skips_when_not_exacc(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = False
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with patch('exabox.healthcheck.cluexachk.connect_to_host') as mock_connect:
            result = test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        self.assertIsNone(result)
        mock_connect.assert_not_called()

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_warns_when_host_missing(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        ebox.mCheckConfigOption.return_value = None
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        with patch('exabox.healthcheck.cluexachk.ebLogWarn') as mock_warn, \
             patch.object(test_obj, 'mSetupAhfonRemote') as mock_setup, \
             patch('exabox.healthcheck.cluexachk.connect_to_host') as mock_connect:
            result = test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        self.assertIsNone(result)
        mock_warn.assert_called()
        mock_setup.assert_not_called()
        mock_connect.assert_not_called()

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_invokes_remote_setup(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        ebox.mCheckConfigOption.return_value = 'remote-host'
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        dummy_context = MagicMock()
        dummy_context.mGetBasePath.return_value = '/base'
        node_obj = MagicMock()

        captured = {}

        @contextmanager
        def fake_connect(host, ctx):
            captured['host'] = host
            captured['ctx'] = ctx
            yield node_obj

        with patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=dummy_context), \
             patch('exabox.healthcheck.cluexachk.connect_to_host', side_effect=fake_connect), \
             patch.object(test_obj, 'mSetupAhfonRemote', return_value=True) as mock_setup:
            result = test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        self.assertIsNone(result)
        self.assertEqual(captured['host'], 'remote-host')
        self.assertIs(captured['ctx'], dummy_context)
        mock_setup.assert_called_once_with(
            node_obj,
            'standby_cps',
            os.path.join('/base', 'ahf_setup'),
            '/base',
            os.path.join('/base', 'ahf_install'),
            os.path.join('/base', 'ahf_install')
        )

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_raises_when_connect_fails(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        ebox.mCheckConfigOption.return_value = 'remote-host'
        hc = DummyHealthCheck(ebox, {}, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={}))

        dummy_context = MagicMock()
        dummy_context.mGetBasePath.return_value = '/base'

        @contextmanager
        def fake_connect(*_args, **_kwargs):
            raise RuntimeError('connect failed')
            yield  # pragma: no cover

        with patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=dummy_context), \
             patch('exabox.healthcheck.cluexachk.connect_to_host', side_effect=fake_connect), \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_log:
            with self.assertRaises(Exception) as ctx:
                test_obj.mInstallAhfOnRemoteCps(SimpleNamespace(jsonconf={}))

        self.assertIn('connect failed', str(ctx.exception))
        mock_log.assert_called()

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_releases_lock_on_process_structure_error(self):
        ebox = MagicMock()
        ebox.mCheckSubConfigOption.side_effect = ['/remote/bin', '/remote/data']
        ebox.mCheckConfigOption.return_value = None
        ebox.IsZdlraProv.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-host'], [], [], [])
        ebox.mIsExaScale.return_value = False
        ebox.mAcquireRemoteLock = MagicMock()
        ebox.mReleaseRemoteLock = MagicMock()
        hc = DummyHealthCheck(ebox, {
            'dom0-host': MagicMock(),
        }, [], {})
        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        with ExitStack() as stack:
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogDebug'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogError'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ebLogWarn'))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessManager', return_value=MagicMock()))
            stack.enter_context(patch('exabox.healthcheck.cluexachk.ProcessStructure', side_effect=RuntimeError('boom')))
            with self.assertRaises(RuntimeError):
                test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()
