#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/utils/tests_utility_latest_version.py /main/1 2026/02/06 jyotdas Exp $
#
# tests_utility_latest_version.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_utility_latest_version.py - Unit tests for LATEST version validation
#
#    DESCRIPTION
#      Unit tests for mIsLatestTargetVersionAllowed utility function
#
#    NOTES
#      Tests the LATEST targetVersion handling for DOM0 exasplice patching
#
#    MODIFIED   (MM/DD/YY)
#    jyotdas     02/06/26 - Creation
#
import unittest
from exabox.infrapatching.utils.utility import mIsLatestTargetVersionAllowed

class TestLatestVersionValidation(unittest.TestCase):

    def test_mIsLatestTargetVersionAllowed_valid_case(self):
        """Test LATEST allowed with dom0 + exasplice=yes"""
        result = mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'yes')
        self.assertTrue(result)

    def test_mIsLatestTargetVersionAllowed_case_insensitive_latest(self):
        """Test case insensitivity for LATEST"""
        self.assertTrue(mIsLatestTargetVersionAllowed('latest', 'dom0', 'yes'))
        self.assertTrue(mIsLatestTargetVersionAllowed('Latest', 'dom0', 'yes'))
        self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'yes'))

    def test_mIsLatestTargetVersionAllowed_case_insensitive_dom0(self):
        """Test case insensitivity for dom0"""
        self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'DOM0', 'yes'))
        self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'Dom0', 'yes'))

    def test_mIsLatestTargetVersionAllowed_case_insensitive_exasplice(self):
        """Test case insensitivity for exasplice"""
        self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'YES'))
        self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'Yes'))

    def test_mIsLatestTargetVersionAllowed_returns_false_for_exasplice_no(self):
        """Test returns False with dom0 + exasplice=no"""
        result = mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'no')
        self.assertFalse(result)

    def test_mIsLatestTargetVersionAllowed_returns_false_for_exasplice_none(self):
        """Test returns False with dom0 + exasplice=None"""
        result = mIsLatestTargetVersionAllowed('LATEST', 'dom0', None)
        self.assertFalse(result)

    def test_mIsLatestTargetVersionAllowed_returns_false_for_domu(self):
        """Test returns False with domu target type"""
        result = mIsLatestTargetVersionAllowed('LATEST', 'domu', 'yes')
        self.assertFalse(result)

    def test_mIsLatestTargetVersionAllowed_returns_false_for_cell(self):
        """Test returns False with cell target type"""
        result = mIsLatestTargetVersionAllowed('LATEST', 'cell', 'yes')
        self.assertFalse(result)

    def test_mIsLatestTargetVersionAllowed_returns_false_for_switch(self):
        """Test returns False with switch target type"""
        result = mIsLatestTargetVersionAllowed('LATEST', 'switch', 'yes')
        self.assertFalse(result)

    def test_mIsLatestTargetVersionAllowed_returns_false_for_non_latest_version(self):
        """Test returns False for non-LATEST version string"""
        result = mIsLatestTargetVersionAllowed('25.1.0.0.0.250101', 'dom0', 'yes')
        self.assertFalse(result)

    def test_mIsLatestTargetVersionAllowed_returns_false_for_none_version(self):
        """Test returns False when version is None"""
        result = mIsLatestTargetVersionAllowed(None, 'dom0', 'yes')
        self.assertFalse(result)

    def test_mIsLatestTargetVersionAllowed_returns_false_for_none_target_type(self):
        """Test returns False when target_type is None"""
        result = mIsLatestTargetVersionAllowed('LATEST', None, 'yes')
        self.assertFalse(result)

    def test_mIsLatestTargetVersionAllowed_returns_false_for_empty_strings(self):
        """Test returns False for empty string parameters"""
        self.assertFalse(mIsLatestTargetVersionAllowed('', 'dom0', 'yes'))
        self.assertFalse(mIsLatestTargetVersionAllowed('LATEST', '', 'yes'))
        self.assertFalse(mIsLatestTargetVersionAllowed('LATEST', 'dom0', ''))

if __name__ == '__main__':
    unittest.main()
