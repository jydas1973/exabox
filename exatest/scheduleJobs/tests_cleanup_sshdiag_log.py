#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_cleanup_sshdiag_log.py /main/2 2026/04/17 18:05:00 aypaul Exp $
#
# tests_cleanup_sshdiag_log.py
#
# Unit tests for scheduleJobs.cleanup_sshdiag_log
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/16/26 - Bug#38900303 Fix unit tests for codev identified issues
#

import types
import unittest
from unittest.mock import MagicMock, patch

import six

if not hasattr(six, "ensure_binary"):
    def _ensure_binary(value, encoding='utf-8', errors='strict'):
        if isinstance(value, bytes):
            return value
        return str(value).encode(encoding, errors)

    def _ensure_text(value, encoding='utf-8', errors='strict'):
        if isinstance(value, bytes):
            return value.decode(encoding, errors)
        return str(value)

    six.ensure_binary = _ensure_binary
    six.ensure_text = _ensure_text
    six.ensure_str = _ensure_text

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.scheduleJobs.cleanup_sshdiag_log import CleanUpSshDiagLog


def _ctx(age="30", limit="30"):
    ctx = MagicMock()
    ctx.mGetArgsOptions.return_value = {}
    ctx.mGetConfigOptions.return_value = {
        "sshdiag_age_limit_in_days": age,
        "sshdiag_files_limit": limit,
    }
    return ctx


class ebTestCleanupSshDiagLog(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCleanupSshDiagLog, cls).setUpClass(True, False)

    def test_mParseConfig_resets_zero_values(self):
        ctx = _ctx(age="0", limit="0")
        with patch("exabox.scheduleJobs.cleanup_sshdiag_log.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpSshDiagLog()

        self.assertEqual(job._CleanUpSshDiagLog__max_age_in_days, 30)
        self.assertEqual(job._CleanUpSshDiagLog__sshdiag_files_limit, 30)
        self.assertEqual(job._CleanUpSshDiagLog__max_age_in_seconds, 30 * 24 * 60 * 60)

    def test_mExecuteJob_removes_old_files(self):
        ctx = _ctx(age="1", limit="1")
        with patch("exabox.scheduleJobs.cleanup_sshdiag_log.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpSshDiagLog()

        base = "/opt/app/exacloud/log"
        file_old = f"{base}/ssh_diag_20240101.log"
        file_new = f"{base}/ssh_diag_20240102.log"

        walk_result = [
            (base, [], ["ssh_diag_20240101.log", "ssh_diag_20240102.log"]),
        ]

        def fake_stat(path):
            return types.SimpleNamespace(st_mtime=0.0)

        def fake_os_walk(_dir):
            for item in walk_result:
                yield item

        def fake_getmtime(path):
            return {
                file_old: 1.0,
                file_new: 2.0,
            }[path]

        with patch("exabox.scheduleJobs.cleanup_sshdiag_log.os.walk", side_effect=fake_os_walk), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.os.path.getmtime", side_effect=fake_getmtime), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.os.stat", side_effect=fake_stat), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.time.time", return_value=200000.0), \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.os.remove") as mock_remove, \
             patch("exabox.scheduleJobs.cleanup_sshdiag_log.ebLogInfo"):
            job.mExecuteJob()

        self.assertEqual(job._CleanUpSshDiagLog__sshdiag_files_limit, 1)
        self.assertEqual(mock_remove.call_count, 2)
        self.assertIn(file_old, mock_remove.call_args_list[0].args)
        self.assertIn(file_new, mock_remove.call_args_list[1].args)


if __name__ == '__main__':
    unittest.main()
