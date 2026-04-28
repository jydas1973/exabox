#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_cleanup_clusters.py /main/1 2024/02/19 06:45:03 aararora Exp $
#
# tests_cleanup_clusters.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cleanup_clusters.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/16/26 - Bug#38900303 Fix unit tests for codev identified issues
#    aararora    01/03/24 - Bug 35863722: Cleanup of cluster xml files under
#                           PodRepo directory
#    aararora    01/03/24 - Creation
#
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
from exabox.scheduleJobs.cleanup_clusters import CleanUpClustersFolder


def _build_cluster_ctx(cleanup_hours):
    ctx = MagicMock()
    ctx.mGetArgsOptions.return_value = {}
    ctx.mGetConfigOptions.return_value = {
        "clusters_podrepo_cleanup_duration_hours": cleanup_hours
    }
    return ctx


class ebTestCleanupClusters(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCleanupClusters, cls).setUpClass(True, False)

    @patch("exabox.scheduleJobs.cleanup_clusters.os.remove")
    @patch("exabox.scheduleJobs.cleanup_clusters.os.path.getmtime")
    @patch("exabox.scheduleJobs.cleanup_clusters.time.time", return_value=7200.0)
    @patch("exabox.scheduleJobs.cleanup_clusters.glob.glob")
    @patch("exabox.scheduleJobs.cleanup_clusters.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_clusters.exaBoxCoreInit")
    @patch("exabox.scheduleJobs.cleanup_clusters.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_clusters.os.getcwd", return_value="/opt/app/exacloud/bin")
    def test_mExecuteJob_removes_stale_xml_files(
        self,
        mock_getcwd,
        mock_get_ctx,
        mock_core_init,
        mock_log_init,
        mock_glob,
        mock_time,
        mock_getmtime,
        mock_remove,
    ):
        mock_get_ctx.return_value = _build_cluster_ctx("1")
        mock_glob.return_value = [
            "/opt/app/exacloud/clusters/PodRepo/old.xml",
            "/opt/app/exacloud/clusters/PodRepo/new.xml",
        ]
        mock_getmtime.side_effect = [0.0, 7100.0]

        job = CleanUpClustersFolder()
        job.mExecuteJob()

        mock_remove.assert_called_once_with("/opt/app/exacloud/clusters/PodRepo/old.xml")
        self.assertEqual(
            job._CleanUpClustersFolder__clusters_podrepo_cleanup_duration_hours, 1
        )

    @patch("exabox.scheduleJobs.cleanup_clusters.os.remove")
    @patch("exabox.scheduleJobs.cleanup_clusters.os.path.getmtime", return_value=7199.0)
    @patch("exabox.scheduleJobs.cleanup_clusters.time.time", return_value=7200.0)
    @patch("exabox.scheduleJobs.cleanup_clusters.glob.glob", return_value=["/opt/app/exacloud/clusters/PodRepo/recent.xml"])
    @patch("exabox.scheduleJobs.cleanup_clusters.ebLogInit")
    @patch("exabox.scheduleJobs.cleanup_clusters.exaBoxCoreInit")
    @patch("exabox.scheduleJobs.cleanup_clusters.get_gcontext")
    @patch("exabox.scheduleJobs.cleanup_clusters.os.getcwd", return_value="/opt/app/exacloud/work/bin")
    def test_mExecuteJob_skips_recent_files_and_honours_default_window(
        self,
        mock_getcwd,
        mock_get_ctx,
        mock_core_init,
        mock_log_init,
        mock_glob,
        mock_time,
        mock_getmtime,
        mock_remove,
    ):
        mock_get_ctx.return_value = _build_cluster_ctx("0")

        job = CleanUpClustersFolder()
        job.mExecuteJob()

        mock_remove.assert_not_called()
        self.assertEqual(
            job._CleanUpClustersFolder__clusters_podrepo_cleanup_duration_hours, 336
        )


if __name__ == '__main__':
    unittest.main()
