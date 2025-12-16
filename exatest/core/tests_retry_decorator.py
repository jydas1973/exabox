#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/core/tests_retry_decorator.py /main/1 2023/12/14 05:24:37 jfsaldan Exp $
#
# tests_retry_decorator.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_retry_decorator.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    12/05/23 - Creation
#

import unittest
from unittest.mock import Mock, patch
from unittest.mock import MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogTrace
from exabox.core.Context import get_gcontext
from exabox.core.Error import retryOnException

class ebTestClusterEncryption(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

    def test_retry_exception_raised_1_max_3(self):
        """
        """

        @retryOnException(max_times=3, sleep_interval = 0.5)
        def test_method(aMagicBehaviorIterator):
            """
            Test method with magic object
            """
            ebLogInfo("Running Magic Object")
            return aMagicBehaviorIterator.dummy_method()

        # Test failing
        _magic_iterator = MagicMock()
        _magic_iterator.dummy_method.side_effect = [ValueError, 0]
        self.assertEqual(0, test_method(_magic_iterator))
        self.assertEqual(2, _magic_iterator.dummy_method.call_count)

    def test_retry_exception_raised_3_max_3(self):
        """
        """

        @retryOnException(max_times=3, sleep_interval = 0.5)
        def test_method(aMagicBehaviorIterator):
            """
            Test method with magic object
            """
            ebLogInfo("Running Magic Object")
            return aMagicBehaviorIterator.dummy_method()

        _magic_iterator = MagicMock()
        _magic_iterator.dummy_method.side_effect = [
                ValueError("Error"), ValueError("Error"), ValueError("Error"),
                0, 0 , 0]

        with self.assertRaises(Exception):
            test_method(_magic_iterator)
        self.assertEqual(3, _magic_iterator.dummy_method.call_count)

    def test_retry_exception_raised_2_max_3(self):
        """
        """

        @retryOnException(max_times=3, sleep_interval = 0.5)
        def test_method(aMagicBehaviorIterator):
            """
            Test method with magic object
            """
            ebLogInfo("Running Magic Object")
            return aMagicBehaviorIterator.dummy_method()

        _magic_iterator = MagicMock()
        _magic_iterator.dummy_method.side_effect = [
                ValueError("Error"), ValueError("Error"), 0]

        self.assertEqual(0, test_method(_magic_iterator))
        self.assertEqual(3, _magic_iterator.dummy_method.call_count)

if __name__ == '__main__':
    unittest.main()

