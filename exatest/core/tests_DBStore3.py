#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/core/tests_DBStore3.py /main/1 2026/03/27 15:42:00 kanmanic Exp $
#
# tests_DBStore3.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_DBStore3.py - Unit tests for DBStore3 utilities
#
#    DESCRIPTION
#      Tests DBStore3 helpers used by AQ status tracking, including request
#      queue-name updates.
#
#    NOTES
#      Uses a constructed ebExacloudDB instance with mocked execution helpers.
#
#    MODIFIED   (MM/DD/YY)
#    kanmanic    06/15/26 - 39560339 - Test failed AQ response retry selector
#    kanmanic    03/17/26 - 37764703 AQ Status Tracker Support
#

import unittest
from unittest.mock import MagicMock

from exabox.core.DBStore3 import ebExacloudDB


class DBStore3AqNameTest(unittest.TestCase):
    """Unit tests for ebExacloudDB AQ status helper methods."""

    def setUp(self):
        self.db_obj = ebExacloudDB.__new__(ebExacloudDB)
        self.db_obj.mExecuteLog = MagicMock()

    def test_mUpdateAqName_updates_when_uuid_present(self):
        """Verify mUpdateAqName issues an update when UUID is provided."""
        ebExacloudDB.mUpdateAqName(self.db_obj, "uuid-123", "QUEUE_A")

        self.db_obj.mExecuteLog.assert_called_once()
        sql_arg, data_arg = self.db_obj.mExecuteLog.call_args[0]
        expected_sql = """UPDATE requests
                  SET aq_name=%(1)s
                  WHERE uuid=%(2)s"""
        self.assertEqual(sql_arg, expected_sql)
        self.assertEqual(data_arg, ["QUEUE_A", "uuid-123"])

    def test_mUpdateAqName_skips_when_uuid_missing(self):
        """Verify mUpdateAqName avoids executing when UUID is missing."""
        ebExacloudDB.mUpdateAqName(self.db_obj, None, "QUEUE_B")

        self.db_obj.mExecuteLog.assert_not_called()

    def test_mGetFailedAQResponses_selects_bounded_error_rows(self):
        """Verify failed response retry selection uses the expected filter."""
        self.db_obj.mFetchAll = MagicMock(return_value=[("uuid-1",)])

        result = ebExacloudDB.mGetFailedAQResponses(self.db_obj, 7)

        self.assertEqual(result, [("uuid-1",)])
        self.db_obj.mFetchAll.assert_called_once()
        sql_arg, data_arg = self.db_obj.mFetchAll.call_args[0]
        self.assertIn("response_sent=%(1)s", sql_arg)
        self.assertIn("aq_name IS NOT NULL", sql_arg)
        self.assertIn("aq_name!=''", sql_arg)
        self.assertIn("aq_name!='Undef'", sql_arg)
        self.assertIn("LIMIT 7", sql_arg)
        self.assertEqual(data_arg, ['Error'])

    def test_mGetFailedAQResponses_uses_default_for_invalid_limit(self):
        """Verify invalid retry limits fall back to the default batch size."""
        self.db_obj.mFetchAll = MagicMock(return_value=[])

        ebExacloudDB.mGetFailedAQResponses(self.db_obj, "invalid")

        sql_arg, data_arg = self.db_obj.mFetchAll.call_args[0]
        self.assertIn("LIMIT 50", sql_arg)
        self.assertEqual(data_arg, ['Error'])

    def test_mGetFailedAQResponses_skips_non_positive_limit(self):
        """Verify non-positive retry limits avoid a DB fetch."""
        self.db_obj.mFetchAll = MagicMock()

        result = ebExacloudDB.mGetFailedAQResponses(self.db_obj, 0)

        self.assertEqual(result, [])
        self.db_obj.mFetchAll.assert_not_called()


if __name__ == '__main__':
    unittest.main()
