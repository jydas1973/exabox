#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/utils/tests_common.py /main/2 2024/08/12 15:59:21 naps Exp $
#
# tests_common.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_common.py - Unit tests for exabox common utilities
#
#    DESCRIPTION
#      Tests model parsing helpers, model comparison behavior, and ECRA DB
#      detail loading from configuration.
#
#    NOTES
#      Uses mocked file reads where configuration input is required.
#
#    MODIFIED   (MM/DD/YY)
#    kanmanic    06/15/26 - 39560339 - Fix ECRA DB connection close guards
#    kanmanic    03/17/26 - 37764703 AQ Status Tracker Support
#    naps        08/12/24 - Bug 36908342 - X11 support.
#    ndesanto    01/24/23 - Tests for funcions in exabox/utils/common.py file
#    ndesanto    01/24/23 - Creation
#

import json
import unittest
from unittest.mock import patch, mock_open, MagicMock

from exabox.utils.common import (
    mGetModelNumber,
    mIsStrModel,
    mCompareModel,
    get_ecradb_details,
    connect_to_ecradb,
)


class UtilsNodeTest(unittest.TestCase):
    """exabox.utils.node unit tests"""

    def test_mGetModelNumber_not_a_number(self):
        self.assertRaises(ValueError, mGetModelNumber, "not a number")

    def test_mGetModelNumber_empty(self):
        self.assertRaises(ValueError, mGetModelNumber, "")

    def test_mGetModelNumber_None(self):
        self.assertRaises(TypeError, mGetModelNumber, None)

    def test_mGetModelNumber_X8(self):
        self.assertEqual(8, mGetModelNumber("X8"))

    def test_mGetModelNumber_X10(self):
        self.assertEqual(10, mGetModelNumber("X10"))

    def test_mGetModelNumber_X11(self):
        self.assertEqual(11, mGetModelNumber("X11"))

    def test_mGetModelNumber_X100(self):
        self.assertEqual(100, mGetModelNumber("X100"))

    def test_mIsStrModel_None(self):
        self.assertFalse(mIsStrModel(None))

    def test_mIsStrModel_empty(self):
        self.assertFalse(mIsStrModel(""))

    def test_mIsStrModel_Not_a_model_number(self):
        self.assertFalse(mIsStrModel("Not a model number"))

    def test_mIsStrModel_X8(self):
        self.assertTrue(mIsStrModel("X8"))

    def test_mIsStrModel_X10(self):
        self.assertTrue(mIsStrModel("X10"))

    def test_mIsStrModel_X11(self):
        self.assertTrue(mIsStrModel("X11"))

    def test_mIsStrModel_X100(self):
        self.assertTrue(mIsStrModel("X100"))

    def test_mCompareModel_not_a_number_first_arg(self):
        self.assertRaises(ValueError, mCompareModel, "not a number", "X10")

    def test_mCompareModel_not_a_number_second_arg(self):
        self.assertRaises(ValueError, mCompareModel, "X10", "not a number")

    def test_mCompareModel_not_a_number_first_arg_X11(self):
        self.assertRaises(ValueError, mCompareModel, "not a number", "X11")

    def test_mCompareModel_not_a_number_second_arg_X11(self):
        self.assertRaises(ValueError, mCompareModel, "X11", "not a number")

    def test_mCompareModel_False_X8_more_than_X10(self):
        self.assertFalse(mCompareModel("X8", "X10") > -1)

    def test_mCompareModel_False_X10_less_than_X8(self):
        self.assertFalse(mCompareModel("X10", "X8") < 1)

    def test_mCompareModel_False_X10_more_than_X11(self):
        self.assertFalse(mCompareModel("X10", "X11") > -1)

    def test_mCompareModel_False_X11_less_than_X10(self):
        self.assertFalse(mCompareModel("X11", "X10") < 1)

    def test_mCompareModel_False_X8_equals_X10(self):
        self.assertFalse(mCompareModel("X8", "X10") == 0)

    def test_mCompareModel_False_X10_not_equals_X10(self):
        self.assertFalse(mCompareModel("X10", "X10") != 0)

    def test_mCompareModel_True_X10_more_than_X8(self):
        self.assertTrue(mCompareModel("X10", "X8") > 0)

    def test_mCompareModel_True_X8_equals_X8(self):
        self.assertTrue(mCompareModel("X8", "X8") == 0)

    def test_mCompareModel_True_X10_equals_X10(self):
        self.assertTrue(mCompareModel("X10", "X10") == 0)

    def test_mCompareModel_True_X8_less_than_X10(self):
        self.assertTrue(mCompareModel("X8", "X10") < 0)

    def test_mCompareModel_True_X8_less_than_or_equal_X10(self):
        self.assertTrue(mCompareModel("X8", "X10") <= 0)

    def test_mCompareModel_True_X10_less_than_or_equal_X10(self):
        self.assertTrue(mCompareModel("X10", "X10") <= 0)

    def test_mCompareModel_True_X10_more_than_or_equal_X8(self):
        self.assertTrue(mCompareModel("X10", "X8") >= 0)

    def test_mCompareModel_True_X10_more_than_or_equal_X10(self):
        self.assertTrue(mCompareModel("X10", "X10") >= 0)


    def test_mCompareModel_False_X10_equals_X11(self):
        self.assertFalse(mCompareModel("X10", "X11") == 0)

    def test_mCompareModel_False_X11_not_equals_X11(self):
        self.assertFalse(mCompareModel("X11", "X11") != 0)

    def test_mCompareModel_True_X11_more_than_X10(self):
        self.assertTrue(mCompareModel("X11", "X10") > 0)

    def test_mCompareModel_True_X11_equals_X11(self):
        self.assertTrue(mCompareModel("X11", "X11") == 0)

    def test_mCompareModel_True_X10_less_than_X11(self):
        self.assertTrue(mCompareModel("X10", "X11") < 0)

    def test_mCompareModel_True_X10_less_than_or_equal_X11(self):
        self.assertTrue(mCompareModel("X10", "X11") <= 0)

    def test_mCompareModel_True_X11_less_than_or_equal_X11(self):
        self.assertTrue(mCompareModel("X11", "X11") <= 0)

    def test_mCompareModel_True_X11_more_than_or_equal_X10(self):
        self.assertTrue(mCompareModel("X11", "X10") >= 0)

    def test_mCompareModel_True_X11_more_than_or_equal_X11(self):
        self.assertTrue(mCompareModel("X11", "X11") >= 0)


class GetEcraDbDetailsTest(unittest.TestCase):
    """Unit tests for get_ecradb_details configuration handling."""

    def test_connect_to_ecradb_closes_successful_connection(self):
        """Ensure connect_to_ecradb closes the yielded DB connection."""
        fake_connection = MagicMock()
        fake_oracledb = MagicMock()
        fake_oracledb.connect.return_value = fake_connection
        details = {
            "user": "user",
            "password": "pwd",
            "host": "host",
            "port": "1521",
            "service_name": "svc",
        }

        with patch('exabox.utils.common.get_ecradb_details', return_value=details), \
             patch.dict('sys.modules', {'oracledb': fake_oracledb}):
            with connect_to_ecradb() as connection:
                self.assertIs(connection, fake_connection)

        fake_oracledb.init_oracle_client.assert_called_once()
        fake_oracledb.connect.assert_called_once_with(user="user",
                                                      password="pwd",
                                                      host="host",
                                                      port="1521",
                                                      service_name="svc")
        fake_connection.close.assert_called_once()

    class _FakeContext(object):
        def __init__(self):
            self._registry = {}

        def mCheckConfigOption(self, key, default=None):
            if key == "ecrad_db_secrets":
                return {"db_conn_details": "details_secret", "db_conn_creds": "creds_secret"}
            if key == "ecra_vault_id":
                return ""
            return {}

        def mCheckRegEntry(self, key):
            return key in self._registry

        def mSetRegEntry(self, key, value):
            self._registry[key] = value

        def mGetRegEntry(self, key):
            return self._registry.get(key)

        def mGetBasePath(self):
            return "/tmp"

    def test_get_ecradb_details_skips_empty_vault(self):
        """Ensure empty vault id falls back to deployment config without OCI calls."""
        fake_context = self._FakeContext()
        deployment_config = {
            "runtime": {
                "db": {
                    "ecrauser": "ecra_user",
                    "ecrapasswd": "ecra_pass",
                    "db_host": "db.host.local",
                    "sdb_port": "1521",
                    "sdb_service": "svc.ecra.internal"
                }
            }
        }
        expected = {
            "user": "ecra_user",
            "password": "ecra_pass",
            "host": "db.host.local",
            "port": "1521",
            "service_name": "svc.ecra.internal"
        }

        with patch('exabox.utils.common.get_gcontext', return_value=fake_context), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(deployment_config))):
            details = get_ecradb_details()

        self.assertEqual(details, expected)
        self.assertEqual(fake_context.mGetRegEntry("ecradbdetails"), expected)


if __name__ == '__main__':
    unittest.main()
