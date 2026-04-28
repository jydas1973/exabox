#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_cleanup_database_log.py /main/2 2026/04/17 18:05:00 aypaul Exp $
#
# tests_cleanup_database_log.py
#
# Unit tests for scheduleJobs.cleanup_database_log
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
from exabox.scheduleJobs.cleanup_database_log import CleanUpDatabaseLog


def _make_ctx(age="30", limit="30"):
    ctx = MagicMock()
    ctx.mGetArgsOptions.return_value = {}
    ctx.mGetConfigOptions.return_value = {
        "database_age_limit_in_days": age,
        "database_files_limit": limit,
    }
    return ctx


class ebTestCleanupDatabaseLog(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCleanupDatabaseLog, cls).setUpClass(True, False)

    def test_mParseConfig_resets_zero_values_to_defaults(self):
        ctx = _make_ctx(age="0", limit="0")
        with patch("exabox.scheduleJobs.cleanup_database_log.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_database_log.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_database_log.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_database_log.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpDatabaseLog()

        self.assertEqual(job._CleanUpDatabaseLog__max_age_in_days, 30)
        self.assertEqual(job._CleanUpDatabaseLog__database_files_limit, 30)
        self.assertEqual(job._CleanUpDatabaseLog__max_age_in_seconds, 30 * 24 * 60 * 60)

    def test_mExecuteJob_removes_files_by_limit_and_age(self):
        ctx = _make_ctx(age="2", limit="1")
        with patch("exabox.scheduleJobs.cleanup_database_log.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_database_log.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_database_log.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_database_log.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpDatabaseLog()

        base = "/opt/app/exacloud/log"
        file_old = f"{base}/database_old.log"
        file_new = f"{base}/database_new.log"

        def fake_walk(_dir):
            yield base, [], ["database_old.log", "database_new.log", "database_skip.err"]

        def fake_getmtime(path):
            return {
                file_old: 10.0,
                file_new: 20.0,
            }[path]

        def fake_stat(path):
            return types.SimpleNamespace(st_mtime=0.0)

        with patch("exabox.scheduleJobs.cleanup_database_log.os.walk", side_effect=fake_walk), \
             patch("exabox.scheduleJobs.cleanup_database_log.os.path.getmtime", side_effect=fake_getmtime), \
             patch("exabox.scheduleJobs.cleanup_database_log.os.stat", side_effect=fake_stat), \
             patch("exabox.scheduleJobs.cleanup_database_log.time.time", return_value=200000.0), \
             patch("exabox.scheduleJobs.cleanup_database_log.os.remove") as mock_remove, \
             patch("exabox.scheduleJobs.cleanup_database_log.ebLogInfo"):
            job.mExecuteJob()

        self.assertEqual(job._CleanUpDatabaseLog__database_files_limit, 1)
        self.assertEqual(mock_remove.call_count, 2)
        self.assertIn(file_old, mock_remove.call_args_list[0].args)
        self.assertIn(file_new, mock_remove.call_args_list[1].args)


if __name__ == '__main__':
    unittest.main()
