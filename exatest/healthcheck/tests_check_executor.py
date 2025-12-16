#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/healthcheck/tests_check_executor.py /main/1 2025/08/13 17:30:11 bhpati Exp $
#
# tests_check_executor.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_check_executor.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    bhpati      07/31/25 - Bug 38102552 - OCI: ECRA WORKFLOW FOR
#                           CLUCTRL.CHECKCLUSTER SHOULD RETURN ERROR IF Node IS
#                           NOT REACHABLE
#    bhpati      07/31/25 - Creation
#
import copy
import json
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogError
from unittest.mock import MagicMock, patch
from exabox.healthcheck.hclogger import get_logger, init_logging
from exabox.healthcheck.check_executor import Finalize
import warnings

class TestFinalize(unittest.TestCase):

    def setUp(self):
        self.result_dict = {
        '1419976_results': ['exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com'],
        '1419976_log1': ['Check ImageVersion, could not complete execution, exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com'],
        '1419976_recommend': ['value5']
        }
        self.finalize = Finalize(self.result_dict)

    def test_finalize_results(self):
        pid = '1419976'
        result = self.finalize.finalize_results(pid)
        self.assertEqual(result, ['value5'])

    def test_extract_list(self):
        result_dict = {'1419976_log1': ['Check ImageVersion, could not complete execution, exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com']}
        result = self.finalize.extract_list(result_dict)
        self.assertEqual(result, ['Check ImageVersion, could not complete execution, exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com'])

    def test_getfilteredict(self):
        pid = '1419976'
        filter_str = '_results'
        result = self.finalize.getfilteredict(pid, filter_str)
        self.assertEqual(result, {'1419976_results': ['exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com']})

    @patch('exabox.healthcheck.hclogger.get_logger')
    @patch('exabox.log.LogMgr.ebLogError')
    def test_update_results(self, mock_ebLogError, mock_get_logger):
        result_dict = {
        '1419976_log1': [
            'Check ImageVersion, could not complete execution, exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com'
        ]}
        self.finalize.update_results(result_dict)

if __name__ == '__main__':
    unittest.main()

