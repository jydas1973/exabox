#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_cleanup_incident_tar_zipfiles.py /main/2 2026/04/17 18:05:00 aypaul Exp $
#
# tests_cleanup_incident_tar_zipfiles.py
#
# Unit tests for scheduleJobs.cleanup_incident_tar_zipfiles
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/16/26 - Bug#38900303 Fix unit tests for codev identified issues
#

import unittest
from types import SimpleNamespace
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
from exabox.scheduleJobs.cleanup_incident_tar_zipfiles import CleanUpIncidentTarAndZipFiles


def _ctx_with_limits(incident="2", tfactl="2", cpuresize="2"):
    ctx = MagicMock()
    ctx.mGetArgsOptions.return_value = {}
    ctx.mGetConfigOptions.return_value = {
        "incident_zip_files_limit": incident,
        "tfactl_zip_files_limit": tfactl,
        "cpuresize_diag_files_limit": cpuresize,
    }
    return ctx


class ebTestCleanupIncidentTarZipFiles(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCleanupIncidentTarZipFiles, cls).setUpClass(True, False)

    def test_mExecuteJob_removes_excess_archives(self):
        ctx = _ctx_with_limits(incident="1", tfactl="1", cpuresize="1")
        with patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpIncidentTarAndZipFiles()

        log_dir = "/opt/app/exacloud/log"
        cpulog_a = f"{log_dir}/cpu_logs/node1/a.tar"
        cpulog_b = f"{log_dir}/cpu_logs/node2/b.tar.gz"
        tfactl_a = f"{log_dir}/tfactl_logs/tfactl_demo_a.zip"
        tfactl_b = f"{log_dir}/tfactl_logs/tfactl_demo_b.zip"
        tar_a = f"{log_dir}/inc/tar_a.tar"
        tar_b = f"{log_dir}/inc/tar_b.tar"
        zip_a = f"{log_dir}/inc/zip_a.zip"
        zip_b = f"{log_dir}/inc/zip_b.zip"

        glob_side_effect = [
            [cpulog_a, cpulog_b],
            [tfactl_a, tfactl_b],
            [cpulog_a, tar_a, tar_b],
            [cpulog_b, zip_a, zip_b],
        ]

        def fake_getmtime(path):
            mapping = {
                cpulog_a: 1,
                cpulog_b: 2,
                tfactl_a: 3,
                tfactl_b: 4,
                tar_a: 5,
                tar_b: 6,
                zip_a: 7,
                zip_b: 8,
            }
            return mapping[path]

        with patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.CPULOG_DIR", "cpu_logs"), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.TFACTL_PREFIX", "tfactl_demo_"), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.glob.glob", side_effect=glob_side_effect), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.os.path.getmtime", side_effect=fake_getmtime), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.os.remove") as mock_remove, \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.ebLogInfo"), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.ebLogTrace"):
            job.mExecuteJob()

        removed_files = {call.args[0] for call in mock_remove.call_args_list}
        self.assertEqual(len(removed_files), 4)
        self.assertIn(cpulog_a, removed_files)
        self.assertIn(tfactl_a, removed_files)
        self.assertIn(tar_a, removed_files)
        self.assertIn(zip_a, removed_files)

    def test_mExecuteJob_no_matching_files_logs_message(self):
        ctx = _ctx_with_limits()
        with patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = CleanUpIncidentTarAndZipFiles()

        with patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.glob.glob", return_value=[]), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.os.path.getmtime"), \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.os.remove") as mock_remove, \
             patch("exabox.scheduleJobs.cleanup_incident_tar_zipfiles.ebLogInfo") as mock_info:
            job.mExecuteJob()

        mock_remove.assert_not_called()
        mock_info.assert_any_call("No matching incident files to delete.")


if __name__ == '__main__':
    unittest.main()
