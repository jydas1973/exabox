#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_metrics_collector.py /main/2 2026/04/17 18:05:00 aypaul Exp $
#
# tests_metrics_collector.py
#
# Unit tests for scheduleJobs.metrics_collector
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/16/26 - Bug#38900303 Fix unit tests for codev identified issues
#

import json
import unittest
from unittest.mock import MagicMock, mock_open, patch

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
from exabox.scheduleJobs.metrics_collector import MetricsCollector


def _make_ctx():
    ctx = MagicMock()
    ctx.mGetArgsOptions.return_value = {}
    ctx.mGetConfigOptions.return_value = {}
    return ctx


class ebTestMetricsCollector(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestMetricsCollector, cls).setUpClass(True, False)

    def test_mParseConfig_filters_disabled_metrics(self):
        ctx = _make_ctx()
        payload = {
            "cpu": {
                "uptime": True,
                "idle": False
            },
            "memory": {
                "used": True
            }
        }
        opener = mock_open(read_data=json.dumps(payload))

        with patch("exabox.scheduleJobs.metrics_collector.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.metrics_collector.ebLogInit"), \
             patch("exabox.scheduleJobs.metrics_collector.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.metrics_collector.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = MetricsCollector()

        with patch("builtins.open", opener):
            result = job.mParseConfig()

        self.assertEqual(result, {"cpu": ["uptime"], "memory": ["used"]})

    def test_mExecuteJob_invokes_metrics_pipeline(self):
        ctx = _make_ctx()
        with patch("exabox.scheduleJobs.metrics_collector.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.metrics_collector.ebLogInit"), \
             patch("exabox.scheduleJobs.metrics_collector.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.metrics_collector.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = MetricsCollector()

        with patch.object(job, "mParseConfig", return_value={"cpu": ["uptime"]}) as mock_parse, \
             patch("exabox.scheduleJobs.metrics_collector.ebExacloudSysMetrics") as mock_metrics, \
             patch("exabox.scheduleJobs.metrics_collector.ebLogInfo") as mock_log:
            metric_instance = MagicMock()
            metric_instance.mInsertUpdatedDataIntoDb.return_value = "ok"
            mock_metrics.return_value = metric_instance

            job.mExecuteJob()

        mock_parse.assert_called_once()
        mock_metrics.assert_called_once()
        metric_instance.mInsertUpdatedDataIntoDb.assert_called_once_with({"cpu": ["uptime"]})
        mock_log.assert_any_call("*** Entering the execution of metrics_collector job ***")
        mock_log.assert_any_call("*** Exiting metrics_collector job ***")


if __name__ == '__main__':
    unittest.main()
