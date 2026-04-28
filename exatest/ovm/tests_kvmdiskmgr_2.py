#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_kvmdiskmgr_2.py /main/1 2026/01/09 05:01:12 shapatna Exp $
#
# tests_kvmdiskmgr_2.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_kvmdiskmgr_2.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    04/10/26 - Fix encrypted lvresize failure unit test
#                           expectations
#    dekuckre    04/02/26 - Fix Python 3.6 mock call argument assertion in
#                           kvmdiskmgr_2 tests
#    aararora    03/03/26 - Bug 38902170: Correct resource leak issues
#    nelango     02/23/26 - Bug 38996273 : Modify unittests for Bug 38700324 
#    shapatna    01/07/26 - Codex UT enhancement
#    shapatna    01/07/26 - Unit test coverage for kvmdiskmgr.py
#    shapatna    01/07/26 - Creation
#

import contextlib
import os
import sys
import unittest
from unittest import mock

_TEST_DIR = os.path.dirname(__file__)
_VIEW_ROOT = os.path.abspath(os.path.join(_TEST_DIR, '../../../../../'))
if _VIEW_ROOT not in sys.path:
    sys.path.insert(0, _VIEW_ROOT)

from ecs.exacloud.exabox.ovm import kvmdiskmgr
from ecs.exacloud.exabox.ovm.kvmdiskmgr import exaBoxKvmDiskMgr, gPartitionError, gReshapeError


class _DummyStream:

    def __init__(self, lines=None):
        self._lines = list(lines or [])

    def readlines(self):
        return list(self._lines)

    def read(self):
        return "".join(self._lines)

    def close(self):
        return None


class _FakeCluUtils:

    def __init__(self, *args, **kwargs):
        self._steps = []

    def mStepSpecificDetails(self, *args, **kwargs):
        detail = {'args': args, 'kwargs': kwargs}
        self._steps.append(detail)
        return detail

    def mUpdateTaskProgressStatus(self, *args, **kwargs):
        self._steps.append({'progress': (args, kwargs)})


class _FakeNode:

    def __init__(self, responses=None, file_exists=True, default_response=None):
        self.responses = {}
        responses = responses or {}
        for key, value in responses.items():
            self.responses[key] = list(value)
        self._last_status = 0
        self._file_exists = file_exists
        self._default_response = default_response
        self.executed = []
        self.disconnect_called = False

    def mConnect(self, *args, **kwargs):
        return None

    def _get_response(self, cmd):
        if cmd not in self.responses or not self.responses[cmd]:
            if self._default_response is not None:
                status, out_lines, err_lines = self._default_response
                return status, list(out_lines), list(err_lines)
            raise AssertionError('Unexpected command: %s' % cmd)
        return self.responses[cmd].pop(0)

    def mExecuteCmd(self, cmd, **kwargs):
        self.executed.append(cmd)
        status, out_lines, err_lines = self._get_response(cmd)
        self._last_status = status
        return (None, _DummyStream(out_lines), _DummyStream(err_lines))

    def mExecuteCmdLog(self, cmd):
        return self.mExecuteCmd(cmd)

    def mGetCmdExitStatus(self):
        return self._last_status

    def mFileExists(self, _path):
        if isinstance(self._file_exists, dict):
            return self._file_exists.get(_path, True)
        return bool(self._file_exists)

    def mDisconnect(self):
        self.disconnect_called = True

    def mGetHostname(self):
        return 'fake-host'

class TestExaBoxKvmDiskMgr(unittest.TestCase):

    def setUp(self):
        self.fake_ebox = mock.Mock()
        self.fake_edp = mock.Mock()
        self.fake_edp.mGetEbox.return_value = self.fake_ebox
        self.fake_edp.mRecordError.return_value = 0

    def _create_encrypted_node(self, fs_type='xfs', overrides=None):
        overrides = overrides or {}
        keyfile_path = overrides.get('keyfile_path', '/tmp/keyfile')

        responses = {
            'lsblk': (0, [
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/lv line\n'
            ], []),
            'parted_fix': (0, ['fix ok\n'], []),
            'resizepart': (0, ['resize ok\n'], []),
            'pvresize': (0, ['pv ok\n'], []),
            'lvresize': (0, ['lv ok\n'], []),
            'keyapi': (0, [keyfile_path + '\n'], []),
            'crypt': (0, ['crypt ok\n'], []),
            'fsresize': (0, ['fs ok\n'], []),
        }
        for key, value in overrides.items():
            if key in responses:
                responses[key] = value

        keyapi_present = overrides.get('keyapi_present', True)
        keyfile_exists = overrides.get('keyfile_exists', True)
        keyapi_file = (
            "/usr/lib/dracut/modules.d/99exacrypt/"
            "VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh"
        )

        node = mock.Mock()

        def exec_cmd(cmd):
            if cmd.startswith('/usr/bin/lsblk'):
                node._last_key = 'lsblk'
            elif "pretend-input-tty print" in cmd:
                node._last_key = 'parted_fix'
            elif 'resizepart 1 100%' in cmd:
                node._last_key = 'resizepart'
            elif cmd.startswith('/usr/sbin/pvresize'):
                node._last_key = 'pvresize'
            elif 'lvresize' in cmd:
                node._last_key = 'lvresize'
            elif cmd == keyapi_file:
                node._last_key = 'keyapi'
            elif 'cryptsetup' in cmd:
                node._last_key = 'crypt'
            elif fs_type == 'xfs' and 'xfs_growfs' in cmd:
                node._last_key = 'fsresize'
            elif fs_type == 'ext4' and 'resize2fs' in cmd:
                node._last_key = 'fsresize'
            else:
                raise AssertionError('Unexpected command: %s' % cmd)

            status, out_lines, err_lines = responses[node._last_key]
            return (None, _DummyStream(out_lines), _DummyStream(err_lines))

        node.mExecuteCmd.side_effect = exec_cmd

        def status_side_effect():
            return responses[node._last_key][0]

        node.mGetCmdExitStatus.side_effect = status_side_effect

        def file_exists(path):
            if path == keyapi_file:
                return keyapi_present
            if path == keyfile_path:
                return keyfile_exists
            return True

        node.mFileExists.side_effect = file_exists

        return node, keyfile_path

    # Auto-generated test for logDebugInfo
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.ebLogInfo')
    def test_log_debug_info_includes_output_and_errors(self, mock_log):
        manager = exaBoxKvmDiskMgr(object())
        error_stream = mock.Mock()
        error_stream.readlines.return_value = ['error-line']

        manager.logDebugInfo(['out-line'], error_stream)

        expected_calls = [
            mock.call('Command Output : '),
            mock.call('out-line'),
            mock.call('Command Error : '),
            mock.call('error-line')
        ]
        for exp in expected_calls:
            self.assertIn(exp, mock_log.call_args_list)

    # Auto-generated test for mUnmountOedaDbHomes
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_unmount_oeda_db_homes_detaches_and_cleans(self, mock_node_cls, _mock_ctx):
        guest_node = mock.Mock()
        host_node = mock.Mock()
        guest_umounts = []
        sed_called = {'value': False}

        def guest_exec(cmd):
            if cmd == '/usr/bin/cat /etc/fstab':
                return (None, _DummyStream([
                    '/dev/VGExaDbDisk.db19.0.0.0.200414-3.img/LVDBDisk    /u01/app/oracle/product/19.0.0.0/dbhome_1  xfs ...\n'
                ]), _DummyStream([]))
            if cmd.startswith('/usr/bin/umount '):
                guest_umounts.append(cmd)
                return (None, _DummyStream([]), _DummyStream([]))
            if cmd == "/usr/bin/sed -i '/dbhome_1/d' /etc/fstab":
                sed_called['value'] = True
                return (None, _DummyStream([]), _DummyStream([]))
            self.fail('Unexpected guest command: %s' % cmd)

        guest_node.mExecuteCmd.side_effect = guest_exec
        guest_node.mDisconnect = mock.Mock()

        host_calls = {'detach': []}

        def host_exec(cmd):
            if cmd.startswith('/bin/ls '):
                return (None, _DummyStream(['/EXAVMIMAGES/GuestImages/guest/db-1.img\n']), _DummyStream([]))
            if cmd.startswith('/usr/bin/rm -f '):
                return (None, _DummyStream([]), _DummyStream([]))
            self.fail('Unexpected host command: %s' % cmd)

        host_node.mExecuteCmd.side_effect = host_exec

        def record_detach(cmd):
            host_calls['detach'].append(cmd)
            return (None, _DummyStream([]), _DummyStream([]))

        host_node.mExecuteCmdLog.side_effect = record_detach
        host_node.mDisconnect = mock.Mock()

        mock_node_cls.side_effect = [guest_node, host_node]

        ebox = mock.Mock()
        fake_edp = mock.Mock()
        fake_edp.mGetEbox.return_value = ebox

        manager = exaBoxKvmDiskMgr(fake_edp)
        manager.mUnmountOedaDbHomes('dom0', 'guest')

        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()
        self.assertTrue(guest_umounts)
        self.assertTrue(sed_called['value'])
        self.assertTrue(host_calls['detach'])
        host_node.mExecuteCmd.assert_any_call('/usr/bin/rm -f /EXAVMIMAGES/GuestImages/guest/db-1.img')
        guest_node.mDisconnect.assert_called_once()
        host_node.mDisconnect.assert_called_once()

    # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='gpt')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_downsize_encrypted_stops_on_gpt_label(self, mock_node_cls, _mock_ctx, _mock_label):
        node = mock.Mock()
        node.mExecuteCmd.return_value = (None, _DummyStream([
            '/dev/disk0 line\\n',
            '/dev/disk0p1 line\n',
            '/dev/mapper/lv line\n'
        ]), _DummyStream([]))
        mock_node_cls.return_value = node
        record_error_result = object()

        ebox = mock.Mock()
        fake_edp = mock.Mock()
        fake_edp.mGetEbox.return_value = ebox
        fake_edp.mRecordError.return_value = record_error_result

        manager = exaBoxKvmDiskMgr(fake_edp)
        result = manager.mExecuteDomUDownsizeStepsEncrypted('domu', '/dev/mapper/lv', 12)

        self.assertIs(result, record_error_result)
        fake_edp.mRecordError.assert_called_once()
        error_args = fake_edp.mRecordError.call_args[0]
        self.assertEqual(error_args[0], gPartitionError['ErrorRunningRemoteCmd'])
        self.assertIn('GPT', error_args[1])
        ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_PARTED_CMD_FAIL'], mock.ANY)

    # Auto-generated test for mExecuteDom0ResizeSteps
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_execute_dom0_resize_steps_handles_edv_resize(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        node.mExecuteCmd.return_value = (None, _DummyStream([]), _DummyStream([]))
        node.mGetCmdExitStatus.return_value = 0
        mock_node_cls.return_value = node

        xs_utils = mock.Mock()
        ebox = mock.Mock()
        ebox.mGetExascaleUtils.return_value = xs_utils
        ebox.mIsExaScale.return_value = False

        fake_edp = mock.Mock()
        fake_edp.mGetEbox.return_value = ebox

        manager = exaBoxKvmDiskMgr(fake_edp)
        result = manager.mExecuteDom0ResizeSteps('dom0', 'domu', 10, '/dev/exc/EXAVM_123_disk')

        self.assertEqual(result, 0)
        xs_utils.mResizeEDVVolume.assert_called_once_with('EXAVM_123', '10g')
        node.mExecuteCmd.assert_called_once_with('virsh blockresize domu /dev/exc/EXAVM_123_disk --size 10G')

    # Auto-generated test for mExecuteDom0ResizeSteps
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_execute_dom0_resize_steps_records_error_on_failure(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        node.mExecuteCmd.return_value = (None, _DummyStream([]), _DummyStream([]))
        node.mGetCmdExitStatus.return_value = 1
        mock_node_cls.return_value = node

        ebox = mock.Mock()
        ebox.mGetExascaleUtils.return_value = mock.Mock()
        ebox.mIsExaScale.return_value = True

        fake_edp = mock.Mock()
        fake_edp.mGetEbox.return_value = ebox
        fake_edp.mRecordError.return_value = 'failure'

        manager = exaBoxKvmDiskMgr(fake_edp)
        result = manager.mExecuteDom0ResizeSteps('dom0', 'domu', 15, '/dev/vda1')

        self.assertEqual(result, 'failure')
        fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_IMAGE_RESIZE'], mock.ANY)

    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_downsize_steps_disconnects_on_error(self, mock_node_cls, _mock_ctx):
        node = _FakeNode(responses={
            '/usr/bin/lsblk -p -r | /usr/bin/grep -B 2 /u02': [
                (0, ['/dev/sda /u02\n', '/dev/sda1 /u02\n'], [])
            ],
            '/bin/findmnt -rn -o TARGET -S /u02': [
                (0, ['/u02\n'], [])
            ],
            '/usr/sbin/lvresize --resizefs -L9.9G /u02 --yes': [
                (1, ['lvresize failed\n'], ['error\n'])
            ]
        })
        mock_node_cls.return_value = node

        ebox = mock.Mock()
        fake_edp = mock.Mock()
        fake_edp.mGetEbox.return_value = ebox
        fake_edp.mRecordError.return_value = 1

        manager = exaBoxKvmDiskMgr(fake_edp)
        result = manager.mExecuteDomUDownsizeSteps('domu', '/u02', 10)

        self.assertEqual(result, 1)
        self.assertTrue(node.disconnect_called)

    # Auto-generated test for mClusterPartitionResize
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.ebLogError')
    def test_cluster_partition_resize_returns_parse_error(self, mock_log_error):
        ebox = mock.Mock()
        fake_edp = mock.Mock()
        fake_edp.mGetEbox.return_value = ebox
        fake_edp.mGetConstantsObj.return_value = mock.Mock(_partitionname_key='partition')
        fake_edp.mGetPartitionOperationData.return_value = {}
        fake_edp.mClusterParseInput.return_value = 1

        manager = exaBoxKvmDiskMgr(fake_edp)
        result = manager.mClusterPartitionResize(mock.Mock())

        self.assertEqual(result, 1)
        ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['INVALID_INPUT_PARAMETER'], mock.ANY)
        mock_log_error.assert_called_once_with('Returning due to input args related error')

    # Auto-generated test for mClusterPartitionResize
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.connect_to_host')
    def test_cluster_partition_resize_shrink_success(
        self, mock_connect, mock_node_exec, _mock_ctx, mock_mount_info
    ):
        self.fake_ebox.mIsExaScale.return_value = True
        self.fake_ebox.mCheckIfCrsDbsUp.return_value = False
        self.fake_ebox.mGetOracleBaseDirectories.return_value = (None, None, None)
        self.fake_ebox.mGetActiveDbInstances.return_value = []
        self.fake_ebox.mCheckCrsUp.return_value = True
        self.fake_ebox.mCheckDBIsUp.return_value = True
        partition_data = {}
        self.fake_edp.mGetPartitionOperationData.return_value = partition_data
        self.fake_edp.mGetDom0DomUpairs.return_value = [('dom0', 'domu')]
        self.fake_edp.mClusterPartitionTargetDiff.return_value = True
        self.fake_edp.mClusterPartitionInfo2.return_value = (0, {
            'fs': '/dev/mapper/app',
            'used': '30',
            'total': '50',
        })

        constants = type('Const', (), {
            '_partitionname_key': 'partition',
            '_newsizeGB_key': 'newsize',
            '_usedsizeGB_key': 'used',
            '_totalsizeGB_key': 'total',
            '_filesystem_key': 'fs',
        })()
        self.fake_edp.mGetConstantsObj.return_value = constants

        def _parse_input(options, out_params):
            out_params['partition'] = 'u02'
            out_params['newsize'] = '40'
            return 0

        fdisk_cmd = "/sbin/fdisk -l '/dev/mapper/app' | /usr/bin/grep Disk"
        node_domU = _FakeNode({
            fdisk_cmd: [
                (0, ["Disk /dev/mapper/app: 48.3 GB, 48318382080 bytes\n"], []),
                (0, ["Disk /dev/mapper/app: 42.9 GB, 42949672960 bytes\n"], []),
            ],
            '/usr/sbin/e2fsck -f /dev/mapper/app': [
                (0, ['fs clean\n'], []),
            ],
        }, default_response=(0, [''], []))
        node_dom0 = _FakeNode({'/usr/bin/ls -l /dev/exc/u02_disk': [(0, ['-rw 1 root root 123 /dev/exc/u02_disk\n'], [])]})

        def _connect(host, _ctx):
            node = node_domU if host == 'domu' else node_dom0

            @contextlib.contextmanager
            def _mgr():
                try:
                    yield node
                finally:
                    if hasattr(node, 'mDisconnect'):
                        node.mDisconnect()

            return _mgr()

        mock_connect.side_effect = _connect
        self.fake_edp.mClusterParseInput.side_effect = _parse_input
        self.fake_edp.mRecordError.return_value = None
        mock_mount_info.return_value = mock.Mock(is_luks=True)
        mock_node_exec.return_value = mock.Mock(stdout='target /dev/exc/u02_disk')

        self.fake_edp.mExecuteDomUUmountPartition.return_value = 0

        with mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.ebCluUtils', new=_FakeCluUtils):
            manager = exaBoxKvmDiskMgr(self.fake_edp)
            manager.mExecuteDomUDownsizeStepsEncrypted = mock.Mock(return_value=0)
            manager.mExecuteDom0ResizeSteps = mock.Mock(return_value=0)
            result = manager.mClusterPartitionResize({'partition': 'u02'})

        self.assertEqual(result, 0)
        self.fake_edp.mExecuteDomUUmountPartition.assert_called_once_with('domu', 'u02')
        manager.mExecuteDomUDownsizeStepsEncrypted.assert_called_once_with('domu', '/dev/mapper/app', '40')
        manager.mExecuteDom0ResizeSteps.assert_called_once_with('dom0', 'domu', '40', '/dev/exc/u02_disk')
        self.fake_edp.mRecordError.assert_not_called()
        self.assertIn('Status', partition_data)
        self.assertEqual(node_domU.executed[0], fdisk_cmd)

    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_requires_keyapi(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        node.mExecuteCmd.return_value = (None, _DummyStream([
            '/dev/disk0 line\\n',
            '/dev/disk0p1 line\n',
            '/dev/mapper/lv line\n'
        ]), _DummyStream([]))
        node.mFileExists.return_value = False
        mock_node_cls.return_value = node

        ebox = mock.Mock()
        fake_edp = mock.Mock()
        fake_edp.mGetEbox.return_value = ebox
        fake_edp.mRecordError.return_value = 'keyapi-missing'

        manager = exaBoxKvmDiskMgr(fake_edp)
        result = manager.mExecuteDomUUpsizeStepsEncrypted('domu', '/dev/mapper/lv', 25)

        self.assertEqual(result, 'keyapi-missing')
        fake_edp.mRecordError.assert_called_once()
        error_args = fake_edp.mRecordError.call_args[0]
        self.assertEqual(error_args[0], gPartitionError['ErrorRunningRemoteCmd'])
        self.assertIn('keyapi script', error_args[1])
        ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_KEYAPI_FAIL'], mock.ANY)


    # Auto-generated test for mExecuteDomUDownsizeSteps
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_downsize_plain_handles_lvresize_failure(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\\n',
                '/dev/disk0p1 line\n'
            ]), _DummyStream([])),
            #findmnt probe (no bind mounts found)
            (None, _DummyStream([]), _DummyStream([])),
            #lvresize failure
            (None, _DummyStream([]), _DummyStream([]))
        ]

        def get_status():
            cmd = node.mExecuteCmd.call_args_list[-1][0][0]
            if cmd.startswith("/bin/findmnt"):
                return 1   # No bind mounts found
            if "lvresize" in cmd:
                return 1   # Simulate lvresize failure
            return 0       # All other commands succeed

        node.mGetCmdExitStatus.side_effect = get_status
        mock_node_cls.return_value = node

        self.fake_ebox.mCheckConfigOption.return_value = False
        self.fake_edp.mRecordError.return_value = 'lvresize-failure'

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUDownsizeSteps('domu', '/dev/mapper/lv', 50)

        self.assertEqual(result, 'lvresize-failure')
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_LVRESIZE_FAIL'], mock.ANY)
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.assertEqual(
            node.mExecuteCmd.call_args_list[-1][0][0],
            '/usr/sbin/lvresize --resizefs -L47.9G /dev/mapper/lv --yes'
        )


    # Auto-generated test for mExecuteDomUDownsizeSteps
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.os.path.isfile', return_value=True)
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_downsize_plain_metacsum_path_copies_e2fsprogs(
        self, mock_node_cls, _mock_ctx, mock_node_exec_check, _mock_isfile
    ):
        filesystem = '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk'
        lsblk_cmd = f"/usr/bin/lsblk -p -r | /usr/bin/grep -B 2 {filesystem}"
        e2fsck_cmd = f"/usr/sbin/e2fsck -fn {filesystem}"
        pvresize_cmd = '/usr/sbin/pvresize -y --setphysicalvolumesize 49.95G /dev/disk0p1'
        lvresize_fragment = 'lvresize --resizefs -L47.9G'
        partsize = '49.95'
        parted_cmd = (
            f"/bin/echo '1\\n{partsize}GiB\\nYes' | /bin/sudo /usr/sbin/parted -a none /dev/disk0 ---pretend-input-tty resizepart"
        )

        responses = {
            'lsblk': (0, [
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk line\n'
            ], []),
            'e2fsck': (1, ['Journal superblock has an unknown incompatible feature flag set.\n'], []),
            'mkdir': (0, [''], []),
            'lvresize': (0, ['lv ok\n'], []),
            'pvresize': (0, ['pv ok\n'], []),
            'parted': (0, ['parted ok\n'], []),
            'parted_resize': (0, ['resize ok\n'], []),
        }

        exec_check_calls = []

        def exec_cmd_check(node, cmd):
            exec_check_calls.append(cmd)
            return mock.Mock()

        mock_node_exec_check.side_effect = exec_cmd_check

        node = mock.Mock()
        executed = []

        def exec_cmd(cmd):
            executed.append(cmd)
            if cmd == lsblk_cmd:
                node._last_status = responses['lsblk'][0]
                return (None, _DummyStream(responses['lsblk'][1]), _DummyStream(responses['lsblk'][2]))
            if cmd.startswith('/bin/findmnt'):
                node._last_status = 1
                return (None, _DummyStream([]), _DummyStream([]))
            if cmd == e2fsck_cmd:
                node._last_status = responses['e2fsck'][0]
                return (None, _DummyStream(responses['e2fsck'][1]), _DummyStream(responses['e2fsck'][2]))
            if cmd == 'mkdir /opt/exacloud/fstools':
                node._last_status = responses['mkdir'][0]
                return (None, _DummyStream(responses['mkdir'][1]), _DummyStream(responses['mkdir'][2]))
            if cmd.startswith('export LD_LIBRARY_PATH'):
                node._last_status = responses['lvresize'][0]
                return (None, _DummyStream(responses['lvresize'][1]), _DummyStream(responses['lvresize'][2]))
            if 'lvresize --resizefs' in cmd:
                node._last_status = responses['lvresize'][0]
                return (None, _DummyStream(responses['lvresize'][1]), _DummyStream(responses['lvresize'][2]))
            if cmd == pvresize_cmd:
                node._last_status = responses['pvresize'][0]
                return (None, _DummyStream(responses['pvresize'][1]), _DummyStream(responses['pvresize'][2]))
            if cmd == parted_cmd:
                key = 'parted'
            elif cmd.startswith("/bin/echo '1\n") and 'pretend-input-tty resizepart' in cmd:
                key = 'parted_resize'
            else:
                raise AssertionError(f'Unexpected command: {cmd}')
            node._last_status = responses[key][0]
            return (None, _DummyStream(responses[key][1]), _DummyStream(responses[key][2]))
            raise AssertionError(f'Unexpected command: {cmd}')

        node.mExecuteCmd.side_effect = exec_cmd
        node.mCopyFile = mock.Mock()
        node._last_status = 0
        node.mGetCmdExitStatus.side_effect = lambda: node._last_status
        node.mDisconnect = mock.Mock()
        mock_node_cls.return_value = node

        self.fake_ebox.mCheckConfigOption.return_value = False

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUDownsizeSteps('domu', filesystem, 50)

        self.assertEqual(result, 0)
        self.fake_edp.mRecordError.assert_not_called()
        self.fake_ebox.mUpdateErrorObject.assert_not_called()
        self.assertTrue(any(lvresize_fragment in cmd for cmd in executed))
        self.assertTrue(any('--no-fsck' in cmd for cmd in executed if 'lvresize' in cmd))
        node.mCopyFile.assert_called_once_with('images/e2fsprogs.tar.gz', '/opt/exacloud/fstools/')
        self.assertEqual(exec_check_calls, [
            'cd /opt/exacloud/fstools;tar xvf e2fsprogs.tar.gz',
            'cd /opt/exacloud/fstools;/usr/bin/sha256sum -c e2fsprogs_sha256.out --status',
            'cd /opt/exacloud/fstools;rpm2cpio e2fsprogs-1.45.4-3.0.7.el7.x86_64.rpm | cpio -id',
            'cd /opt/exacloud/fstools;rpm2cpio e2fsprogs-libs-1.45.4-3.0.7.el7.x86_64.rpm | cpio -id'
        ])


    # Auto-generated test for mExecuteDomUDownsizeSteps
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_downsize_plain_records_error_when_lsblk_missing(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        class _StreamNone:
            def readlines(self):
                return None

        node.mExecuteCmd.return_value = (None, _StreamNone(), _DummyStream(['error']))
        node.mGetCmdExitStatus.return_value = 0
        mock_node_cls.return_value = node

        self.fake_edp.mRecordError.return_value = 'lsblk-missing'

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        with self.assertRaises(TypeError):
            manager.mExecuteDomUDownsizeSteps('domu', '/dev/mapper/lv', 40)

        self.fake_edp.mRecordError.assert_not_called()
        self.fake_ebox.mUpdateErrorObject.assert_not_called()


    # Auto-generated test for mExecuteDomUUpsizeSteps
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_plain_uses_full_free_when_snapshot_disabled(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\\n',
                '/dev/disk0p1 line\n'
            ]), _DummyStream([])),
            (None, _DummyStream([]), _DummyStream([])),
            (None, _DummyStream([]), _DummyStream([])),
            (None, _DummyStream([]), _DummyStream([]))
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0]
        mock_node_cls.return_value = node

        self.fake_ebox.mCheckConfigOption.return_value = True

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUUpsizeSteps('domu', '/dev/mapper/lv', 30)

        self.assertEqual(result, 0)
        self.fake_ebox.mCheckConfigOption.assert_called_once_with('disable_lvm_snapshot_space', 'True')
        self.assertEqual(
            node.mExecuteCmd.call_args_list[-1][0][0],
            '/usr/sbin/lvresize --resizefs -l +100%FREE /dev/mapper/lv'
        )


    # Auto-generated test for mExecuteDomUUpsizeSteps
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_plain_reserves_snapshot_space_when_enabled(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\\n',
                '/dev/disk0p1 line\n'
            ]), _DummyStream([])),
            (None, _DummyStream([]), _DummyStream([])),
            (None, _DummyStream([]), _DummyStream([])),
            (None, _DummyStream([]), _DummyStream([]))
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0]
        mock_node_cls.return_value = node

        self.fake_ebox.mCheckConfigOption.return_value = False

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUUpsizeSteps('domu', '/dev/mapper/lv', 30)

        self.assertEqual(result, 0)
        lvresize_cmd = node.mExecuteCmd.call_args_list[-1][0][0]
        self.assertIn('--resizefs -L28.0G', lvresize_cmd)
        self.fake_ebox.mUpdateErrorObject.assert_not_called()


    # Auto-generated test for mExecuteDomUUpsizeSteps
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_plain_records_error_when_lsblk_missing(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        node.mExecuteCmd.return_value = (None, _DummyStream([]), _DummyStream(['failure']))
        node.mGetCmdExitStatus.return_value = 0
        mock_node_cls.return_value = node

        self.fake_edp.mRecordError.return_value = 'lsblk-missing'

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        with self.assertRaises(IndexError):
            manager.mExecuteDomUUpsizeSteps('domu', '/dev/mapper/lv', 24)

        self.fake_edp.mRecordError.assert_not_called()
        self.fake_ebox.mUpdateErrorObject.assert_not_called()


    # Auto-generated test for mExecuteDomUUpsizeSteps
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_plain_records_error_when_lvresize_fails(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\\n',
                '/dev/disk0p1 line\n'
            ]), _DummyStream([])),
            (None, _DummyStream(['parted ok\n']), _DummyStream([])),
            (None, _DummyStream(['pv ok\n']), _DummyStream([])),
            (None, _DummyStream(['lv fail\n']), _DummyStream(['detail\n'])),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 1]
        mock_node_cls.return_value = node

        self.fake_ebox.mCheckConfigOption.return_value = True
        self.fake_edp.mRecordError.return_value = 'lvresize-error'

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUUpsizeSteps('domu', '/dev/mapper/lv', 30)

        self.assertEqual(result, 'lvresize-error')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_LVRESIZE_FAIL'], mock.ANY)
        self.assertEqual(
            node.mExecuteCmd.call_args_list[-1][0][0],
            '/usr/sbin/lvresize --resizefs -l +100%FREE /dev/mapper/lv'
        )


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_success_deletes_keyapi(self, mock_node_cls, _mock_ctx,
                                                     mock_node_exec, mock_cmd_path,
                                                     mock_mount_info):
        node, keyfile_path = self._create_encrypted_node(
            fs_type='xfs',
            overrides={
                'crypt': (0, ['crypt ok\n'], []),
                'fsresize': (0, ['fs ok\n'], [])
            }
        )
        mock_node_cls.return_value = node

        mock_cmd_path.side_effect = ['cryptsetup_bin', 'xfs_growfs_bin']
        mock_mount_info.return_value = mock.Mock(fs_type='xfs', mount_point='/mnt')

        self.fake_ebox.mCheckConfigOption.return_value = False

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUUpsizeStepsEncrypted('domu', '/dev/mapper/lv', 42)

        self.assertEqual(result, 0)
        mock_cmd_path.assert_any_call(node, 'cryptsetup', sbin=True)
        mock_cmd_path.assert_any_call(node, 'xfs_growfs', sbin=True)
        mock_node_exec.assert_called_once_with(node, f'/bin/shred -fu {keyfile_path}')
        self.fake_ebox.mUpdateErrorObject.assert_not_called()
        node.mFileExists.assert_called()


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_lvresize_same_size_message_ignored(
        self, mock_node_cls, _mock_ctx, mock_node_exec, mock_cmd_path, mock_mount_info
    ):
        node, keyfile_path = self._create_encrypted_node(
            overrides={'lvresize': (1, ['New size 40G matches existing size\n'], [])}
        )
        mock_node_cls.return_value = node

        mock_cmd_path.side_effect = ['cryptsetup_bin', 'xfs_growfs_bin']
        mock_mount_info.return_value = mock.Mock(fs_type='xfs', mount_point='/mnt')

        self.fake_ebox.mCheckConfigOption.return_value = False

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUUpsizeStepsEncrypted('domu', '/dev/mapper/lv', 40)

        self.assertEqual(result, 0)
        self.fake_edp.mRecordError.assert_not_called()
        self.fake_ebox.mUpdateErrorObject.assert_not_called()
        mock_node_exec.assert_called_once_with(node, f'/bin/shred -fu {keyfile_path}')
        node.mFileExists.assert_called()


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_uses_full_free_when_snapshot_disabled_config(self, mock_node_cls, _mock_ctx,
                                                                          mock_node_exec, mock_cmd_path,
                                                                          mock_mount_info):
        node, keyfile_path = self._create_encrypted_node(
            fs_type='ext4',
            overrides={'fsresize': (0, ['resize2fs ok\n'], [])}
        )
        mock_node_cls.return_value = node

        mock_cmd_path.side_effect = ['cryptsetup_bin', 'resize2fs_bin']
        mock_mount_info.return_value = mock.Mock(fs_type='ext4', mount_point='/mnt')

        self.fake_ebox.mCheckConfigOption.return_value = True

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUUpsizeStepsEncrypted('domu', '/dev/mapper/lv', 32)

        self.assertEqual(result, 0)
        lvresize_cmd = node.mExecuteCmd.call_args_list[4][0][0]
        self.assertIn('-l +100%FREE', lvresize_cmd)
        mock_node_exec.assert_called_once_with(node, f'/bin/shred -fu {keyfile_path}')
        self.fake_ebox.mUpdateErrorObject.assert_not_called()
        node.mFileExists.assert_called()


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_uses_full_free_when_snapshot_disabled(self, mock_node_cls, _mock_ctx,
                                                                   mock_node_exec, mock_cmd_path,
                                                                   mock_mount_info):
        node, keyfile_path = self._create_encrypted_node(
            fs_type='ext4',
            overrides={'fsresize': (0, ['resize2fs ok\n'], [])}
        )
        mock_node_cls.return_value = node

        mock_cmd_path.side_effect = ['cryptsetup_bin', 'resize2fs_bin']
        mock_mount_info.return_value = mock.Mock(fs_type='ext4', mount_point='/mnt')

        self.fake_ebox.mCheckConfigOption.return_value = True

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUUpsizeStepsEncrypted('domu', '/dev/mapper/lv', 32)

        self.assertEqual(result, 0)
        lvresize_cmd = node.mExecuteCmd.call_args_list[4][0][0]
        self.assertIn('-l +100%FREE', lvresize_cmd)
        mock_node_exec.assert_called_once_with(node, f'/bin/shred -fu {keyfile_path}')
        self.fake_ebox.mUpdateErrorObject.assert_not_called()
        node.mFileExists.assert_called()



    # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.ebLogInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='msdos')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_downsize_encrypted_lvresize_same_target_size_ignored(
        self, mock_node_cls, _mock_ctx, _mock_label, mock_cmd_path, mock_node_exec, mock_log_info
    ):
        filesystem = '/dev/mapper/lv'
        new_size = 40
        lsblk_output = [
            '/dev/disk0 line\n',
            '/dev/disk0p1 line\n',
            '/dev/mapper/lv line\n'
        ]
        lsblk_cmd = f"/usr/bin/lsblk -p -r | /usr/bin/grep -B 3 {filesystem}"
        lvsize = float(new_size) - 0.1
        partsize = float(new_size) - 0.05
        lvresize_cmd = f"/usr/sbin/lvresize -L {lvsize}G {filesystem} --force"
        pvresize_cmd = (
            f"/usr/sbin/pvresize -y --setphysicalvolumesize {partsize}G /dev/disk0p1"
        )
        parted_cmd = (
            f"/bin/echo '1\n{partsize}GiB\nYes' | /bin/sudo /usr/sbin/parted -a none "
            "/dev/disk0 ---pretend-input-tty resizepart"
        )
        keyapi_file = (
            "/usr/lib/dracut/modules.d/99exacrypt/"
            "VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh"
        )

        responses = {
            lsblk_cmd: [(0, lsblk_output, [])],
            'e2fsck_bin -fy /dev/mapper/lv': [(0, ['fsck ok\n'], [])],
            'resize2fs_bin -M /dev/mapper/lv': [(0, ['resize min ok\n'], [])],
            'cryptsetup_bin close /dev/mapper/lv -v': [(0, ['crypt close\n'], [])],
            lvresize_cmd: [(1, ['New size matches existing size\n'], ['error detail\n'])],
            keyapi_file: [(0, ['/tmp/keyfile\n'], [])],
            'cryptsetup_bin open /dev/mapper/lv lv --key-file=/tmp/keyfile -v': [(0, ['crypt open\n'], [])],
            'resize2fs_bin /dev/mapper/lv': [(0, ['resize ok\n'], [])],
            pvresize_cmd: [(0, ['pvresize ok\n'], [])],
            parted_cmd: [(0, ['parted ok\n'], [])],
        }

        node = _FakeNode(responses, file_exists=True, default_response=(0, ['ok\n'], []))
        mock_node_cls.return_value = node
        mock_cmd_path.side_effect = lambda _node, cmd, sbin=False: f'{cmd}_bin'

        fake_ebox = mock.Mock()
        fake_ebox.mCheckConfigOption.return_value = True
        fake_edp = mock.Mock()
        fake_edp.mRecordError.return_value = 0
        fake_edp.mGetEbox.return_value = fake_ebox

        manager = exaBoxKvmDiskMgr(fake_edp)
        result = manager.mExecuteDomUDownsizeStepsEncrypted('domu', filesystem, new_size)

        self.assertEqual(result, 0)
        fake_edp.mRecordError.assert_not_called()
        mock_node_exec.assert_called_once_with(node, '/bin/shred -fu /tmp/keyfile')
        mock_log_info.assert_any_call(mock.ANY)
        self.assertTrue(
            any('Ignoring error' in call[0][0] for call in mock_log_info.call_args_list),
            'Expected log about ignoring lvresize error'
        )
        fake_ebox.mUpdateErrorObject.assert_not_called()


    # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.ebLogWarn')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='msdos')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_downsize_encrypted_handles_missing_keyapi_cleanup(
        self, mock_node_cls, _mock_ctx, _mock_label, mock_cmd_path, mock_node_exec, mock_log_warn
    ):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/lv line\n'
            ]), _DummyStream([])),
            (None, _DummyStream(['fsck ok\n']), _DummyStream([])),
            (None, _DummyStream(['resize min ok\n']), _DummyStream([])),
            (None, _DummyStream(['crypt close\n']), _DummyStream([])),
            (None, _DummyStream(['lvresize ok\n']), _DummyStream([])),
            (None, _DummyStream([]), _DummyStream([])),
            (None, _DummyStream(['crypt open\n']), _DummyStream([])),
            (None, _DummyStream(['resize fs\n']), _DummyStream([])),
            (None, _DummyStream(['pvresize ok\n']), _DummyStream([])),
            (None, _DummyStream(['parted ok\n']), _DummyStream([])),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        node.mFileExists.return_value = True
        mock_node_cls.return_value = node
        mock_cmd_path.side_effect = lambda _node, cmd, sbin=False: f'{cmd}_bin'

        fake_ebox = mock.Mock()
        fake_ebox.mCheckConfigOption.return_value = False
        fake_edp = mock.Mock()
        fake_edp.mGetEbox.return_value = fake_ebox

        manager = exaBoxKvmDiskMgr(fake_edp)
        result = manager.mExecuteDomUDownsizeStepsEncrypted('domu', '/dev/mapper/lv', 42)

        self.assertEqual(result, 0)
        fake_edp.mRecordError.assert_not_called()
        mock_node_exec.assert_not_called()
        mock_log_warn.assert_any_call('No keyapi to delete')
        fake_ebox.mUpdateErrorObject.assert_not_called()


    # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='msdos')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_downsize_encrypted_keyapi_command_failure(self, mock_node_cls, _mock_ctx,
                                                       _mock_label, mock_cmd_path,
                                                       mock_node_exec):
        mock_cmd_path.side_effect = lambda _node, cmd, sbin=False: f'{cmd}_bin'

        filesystem = '/dev/mapper/lv'
        new_size = 40
        lsblk_cmd = f"/usr/bin/lsblk -p -r | /usr/bin/grep -B 3 {filesystem}"
        keyapi_file = (
            "/usr/lib/dracut/modules.d/99exacrypt/"
            "VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh"
        )

        responses = {
            lsblk_cmd: [(0, [
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/lv line\n'
            ], [])],
            'e2fsck_bin -fy /dev/mapper/lv': [(0, ['fsck ok\n'], [])],
            'resize2fs_bin -M /dev/mapper/lv': [(0, ['resize min ok\n'], [])],
            'cryptsetup_bin close /dev/mapper/lv -v': [(0, ['crypt close ok\n'], [])],
            '/usr/sbin/lvresize -L 39.9G /dev/mapper/lv --force': [(0, ['lv ok\n'], [])],
            keyapi_file: [(1, [], ['keyapi err\n'])],
        }

        node = _FakeNode(responses, file_exists=True, default_response=(0, ['ok\n'], []))
        mock_node_cls.return_value = node
        mock_cmd_path.side_effect = lambda _node, cmd, sbin=False: f'{cmd}_bin'

        self.fake_ebox.mCheckConfigOption.return_value = True
        self.fake_edp.mRecordError.return_value = 'keyapi-failure'

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUDownsizeStepsEncrypted('domu', filesystem, new_size)

        self.assertEqual(result, 'keyapi-failure')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_KEYAPI_FAIL'], mock.ANY)
        mock_node_exec.assert_not_called()


    # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='msdos')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_downsize_encrypted_cryptsetup_close_failure(self, mock_node_cls, _mock_ctx,
                                                         _mock_label, mock_cmd_path,
                                                         mock_node_exec):
        mock_cmd_path.side_effect = lambda _node, cmd, sbin=False: f'{cmd}_bin'

        filesystem = '/dev/mapper/lv'
        new_size = 44
        lsblk_cmd = f"/usr/bin/lsblk -p -r | /usr/bin/grep -B 3 {filesystem}"
        keyapi_file = (
            "/usr/lib/dracut/modules.d/99exacrypt/"
            "VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh"
        )

        responses = {
            lsblk_cmd: [(0, [
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/lv line\n'
            ], [])],
            'e2fsck_bin -fy /dev/mapper/lv': [(0, ['fsck ok\n'], [])],
            'resize2fs_bin -M /dev/mapper/lv': [(0, ['resize min ok\n'], [])],
            'cryptsetup_bin close /dev/mapper/lv -v': [(1, [], ['crypt close err\n'])],
            keyapi_file: [(0, ['/tmp/keyfile\n'], [])],
            'cryptsetup_bin open /dev/mapper/lv lv --key-file=/tmp/keyfile -v': [(0, ['crypt open\n'], [])],
        }

        node = _FakeNode(responses, file_exists=True, default_response=(0, ['ok\n'], []))
        mock_node_cls.return_value = node
        mock_cmd_path.side_effect = lambda _node, cmd, sbin=False: f'{cmd}_bin'

        self.fake_ebox.mCheckConfigOption.return_value = True
        self.fake_edp.mRecordError.return_value = 'cryptsetup-failure'

        manager = exaBoxKvmDiskMgr(self.fake_edp)
        result = manager.mExecuteDomUDownsizeStepsEncrypted('domu', filesystem, new_size)

        self.assertEqual(result, 'cryptsetup-failure')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_LUKSRESIZE_FAIL'], mock.ANY)
        mock_node_exec.assert_not_called()


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_parted_fix_failure_records_error(
        self, mock_node_cls, _mock_ctx, mock_mount_info
    ):
        node, _ = self._create_encrypted_node(
            overrides={'parted_fix': (1, ['fix error\n'], ['err detail\n'])}
        )
        mock_node_cls.return_value = node

        mock_mount_info.return_value = mock.Mock(fs_type='ext4', mount_point='/mnt')

        self.fake_edp.mRecordError.return_value = 'parted-fix-failure'

        result = exaBoxKvmDiskMgr(self.fake_edp).mExecuteDomUUpsizeStepsEncrypted(
            'domu', '/dev/mapper/lv', 20
        )

        self.assertEqual(result, 'parted-fix-failure')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_PARTED_CMD_FAIL'], mock.ANY)


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_pvresize_failure_records_error(self, mock_node_cls, _mock_ctx):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/lv line\n'
            ]), _DummyStream([])),
            (None, _DummyStream(['fix ok\n']), _DummyStream([])),
            (None, _DummyStream(['resize ok\n']), _DummyStream([])),
            (None, _DummyStream(['pv error\n']), _DummyStream(['detail\n']))
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 1]
        mock_node_cls.return_value = node

        self.fake_edp.mRecordError.return_value = 'pvresize-failure'

        result = exaBoxKvmDiskMgr(self.fake_edp).mExecuteDomUUpsizeStepsEncrypted(
            'domu', '/dev/mapper/lv', 24
        )

        self.assertEqual(result, 'pvresize-failure')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_PVRESIZE_FAIL'], mock.ANY)


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_lvresize_failure_records_error(
        self, mock_node_cls, _mock_ctx, mock_node_exec, mock_mount_info
    ):
        node, keyfile_path = self._create_encrypted_node(
            fs_type='ext4',
            overrides={'lvresize': (1, ['bad out\n'], ['bad err\n'])}
        )
        mock_node_cls.return_value = node

        mock_mount_info.return_value = mock.Mock(fs_type='ext4', mount_point='/mnt')
        self.fake_edp.mRecordError.return_value = 'lvresize-failure'

        result = exaBoxKvmDiskMgr(self.fake_edp).mExecuteDomUUpsizeStepsEncrypted(
            'domu', '/dev/mapper/lv', 26
        )

        self.assertEqual(result, 'lvresize-failure')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_LVRESIZE_FAIL'], mock.ANY)
        mock_node_exec.assert_not_called()


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.ebLogWarn')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_keyapi_command_failure(
        self, mock_node_cls, _mock_ctx, mock_node_exec, mock_log_warn
    ):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/lv line\n'
            ]), _DummyStream([])),
            (None, _DummyStream(['fix ok\n']), _DummyStream([])),
            (None, _DummyStream(['resize ok\n']), _DummyStream([])),
            (None, _DummyStream(['pv ok\n']), _DummyStream([])),
            (None, _DummyStream(['lv ok\n']), _DummyStream([])),
            (None, _DummyStream([]), _DummyStream(['keyapi err\n']))
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0, 1]
        mock_node_cls.return_value = node

        self.fake_edp.mRecordError.return_value = 'keyapi-failure'

        result = exaBoxKvmDiskMgr(self.fake_edp).mExecuteDomUUpsizeStepsEncrypted(
            'domu', '/dev/mapper/lv', 28
        )

        self.assertEqual(result, 'keyapi-failure')
        mock_node_exec.assert_not_called()
        mock_log_warn.assert_called_once_with('No keyapi to delete')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_KEYAPI_FAIL'], mock.ANY)


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_cryptsetup_failure_records_error(
        self, mock_node_cls, _mock_ctx, mock_node_exec, mock_cmd_path, mock_mount_info
    ):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/lv line\n'
            ]), _DummyStream([])),
            (None, _DummyStream(['fix ok\n']), _DummyStream([])),
            (None, _DummyStream(['resize ok\n']), _DummyStream([])),
            (None, _DummyStream(['pv ok\n']), _DummyStream([])),
            (None, _DummyStream(['lv ok\n']), _DummyStream([])),
            (None, _DummyStream(['/tmp/keyfile\n']), _DummyStream([])),
            (None, _DummyStream(['crypt err\n']), _DummyStream([]))
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0, 0, 1]
        node.mFileExists.return_value = True
        mock_node_cls.return_value = node
        mock_cmd_path.side_effect = ['cryptsetup_bin']
        mock_mount_info.return_value = mock.Mock()

        self.fake_edp.mRecordError.return_value = 'cryptsetup-failure'

        result = exaBoxKvmDiskMgr(self.fake_edp).mExecuteDomUUpsizeStepsEncrypted(
            'domu', '/dev/mapper/lv', 30
        )

        self.assertEqual(result, 'cryptsetup-failure')
        mock_node_exec.assert_called_once_with(node, '/bin/shred -fu /tmp/keyfile')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_LUKSRESIZE_FAIL'], mock.ANY)


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_xfs_resize_failure_records_error(
        self, mock_node_cls, _mock_ctx, mock_node_exec, mock_cmd_path, mock_mount_info
    ):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/lv line\n'
            ]), _DummyStream([])),
            (None, _DummyStream(['fix ok\n']), _DummyStream([])),
            (None, _DummyStream(['resize ok\n']), _DummyStream([])),
            (None, _DummyStream(['pv ok\n']), _DummyStream([])),
            (None, _DummyStream(['lv ok\n']), _DummyStream([])),
            (None, _DummyStream(['/tmp/keyfile\n']), _DummyStream([])),
            (None, _DummyStream(['crypt ok\n']), _DummyStream([])),
            (None, _DummyStream(['xfs err\n']), _DummyStream([]))
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0, 0, 0, 1]
        node.mFileExists.return_value = True
        mock_node_cls.return_value = node
        mock_cmd_path.side_effect = ['cryptsetup_bin', 'xfs_growfs_bin']
        mock_mount_info.return_value = mock.Mock(fs_type='xfs', mount_point='/mnt')

        self.fake_edp.mRecordError.return_value = 'fsresize-failure'

        result = exaBoxKvmDiskMgr(self.fake_edp).mExecuteDomUUpsizeStepsEncrypted(
            'domu', '/dev/mapper/lv', 34
        )

        self.assertEqual(result, 'fsresize-failure')
        mock_cmd_path.assert_any_call(node, 'xfs_growfs', sbin=True)
        mock_node_exec.assert_called_once_with(node, '/bin/shred -fu /tmp/keyfile')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_FSRESIZE_FAIL'], mock.ANY)


    # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.get_gcontext', return_value='ctx')
    @mock.patch('ecs.exacloud.exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_upsize_encrypted_ext4_resize_failure_records_error(
        self, mock_node_cls, _mock_ctx, mock_node_exec, mock_cmd_path, mock_mount_info
    ):
        node = mock.Mock()
        node.mExecuteCmd.side_effect = [
            (None, _DummyStream([
                '/dev/disk0 line\n',
                '/dev/disk0p1 line\n',
                '/dev/mapper/lv line\n'
            ]), _DummyStream([])),
            (None, _DummyStream(['fix ok\n']), _DummyStream([])),
            (None, _DummyStream(['resize ok\n']), _DummyStream([])),
            (None, _DummyStream(['pv ok\n']), _DummyStream([])),
            (None, _DummyStream(['lv ok\n']), _DummyStream([])),
            (None, _DummyStream(['/tmp/keyfile\n']), _DummyStream([])),
            (None, _DummyStream(['crypt ok\n']), _DummyStream([])),
            (None, _DummyStream(['resize2fs err\n']), _DummyStream([]))
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0, 0, 0, 1]
        node.mFileExists.return_value = True
        mock_node_cls.return_value = node
        mock_cmd_path.side_effect = ['cryptsetup_bin', 'resize2fs_bin']
        mock_mount_info.return_value = mock.Mock(fs_type='ext4', mount_point='/mnt')

        self.fake_edp.mRecordError.return_value = 'ext4-failure'

        result = exaBoxKvmDiskMgr(self.fake_edp).mExecuteDomUUpsizeStepsEncrypted(
            'domu', '/dev/mapper/lv', 36
        )

        self.assertEqual(result, 'ext4-failure')
        mock_cmd_path.assert_any_call(node, 'resize2fs', sbin=True)
        mock_node_exec.assert_called_once_with(node, '/bin/shred -fu /tmp/keyfile')
        self.fake_edp.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'], mock.ANY)
        self.fake_ebox.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_FSRESIZE_FAIL'], mock.ANY)


if __name__ == '__main__':
    unittest.main()
