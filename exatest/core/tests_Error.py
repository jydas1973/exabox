#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/core/tests_Error.py /main/1 2024/08/16 19:44:01 gparada Exp $
#
# tests_Error.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_Error.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Unit Tests for exabox.core.Error
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    gparada     08/15/24 - Bug 36931417 Tests for retryOnException
#    gparada     08/15/24 - Creation
#

# Python libs
import unittest
import time
from unittest.mock import patch

# Exacloud libs
from exabox.core.Error import ExacloudRuntimeError, retryOnException
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn

class ebTestError(ebTestClucontrol):
    def test_retryOnException_successful_run(self):
        @retryOnException(max_times=3, sleep_interval=1)
        def successful_function():
            return "Success!"

        result = successful_function()
        self.assertEqual(result, "Success!")

    def test_retry_on_exception(self):
        attempt_count = 0

        @retryOnException(max_times=3, sleep_interval=1)
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise RuntimeError("Failed!")
            return "Success!"

        result = failing_function()
        self.assertEqual(result, "Success!")
        self.assertEqual(attempt_count, 3)

    def test_retryOnException_max_retries_exceeded(self):
        @retryOnException(max_times=2, sleep_interval=1)
        def always_failing_function():
            raise RuntimeError("Failed!")

        with self.assertRaises(ExacloudRuntimeError):
            always_failing_function()

    def test_retryOnException_sleep_interval(self):
        start_time = time.time()

        @retryOnException(max_times=2, sleep_interval=2)
        def slow_failing_function():
            raise RuntimeError("Failed!")

        with self.assertRaises(ExacloudRuntimeError):
            slow_failing_function()

        end_time = time.time()
        self.assertGreater(end_time - start_time, 2)

    @patch('exabox.log.LogMgr.ebLogWarn')
    @patch('exabox.log.LogMgr.ebLogError')
    def test_retryOnException_logging(self, mock_ebLogWarn, mock_ebLogError):

        with patch('exabox.core.Error.ebLogWarn', mock_ebLogWarn), \
            patch('exabox.core.Error.ebLogError', mock_ebLogError):
            @retryOnException(max_times=2, sleep_interval=1)
            def failing_function():
                raise RuntimeError("Failed!")

            with self.assertRaises(ExacloudRuntimeError):
                failing_function()

        self.assertEqual(mock_ebLogWarn.call_count, 2)
        self.assertEqual(mock_ebLogError.call_count, 1)

if __name__ == "__main__":
    unittest.main()
