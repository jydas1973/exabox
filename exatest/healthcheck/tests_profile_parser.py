#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/healthcheck/tests_profile_parser.py /main/2 2026/01/06 05:52:21 shapatna Exp $
#
# tests_profile_parser.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_profile_parser.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    12/11/25 - Add unit tests for profile_parser.py
#    shapatna    12/11/25 - Creation
#
import unittest
from unittest.mock import Mock, patch

# Reference base class used by exatest-style tests
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

# Import target under test
from exabox.healthcheck.profile_parser import ProfileParser


# Fake HcConstants to isolate tests from real constants module
class _FakeHcConstants:
    PROFILE_NAME = "profile_name"
    CHECK_LIST = "check_list"
    RESULT_LEVEL = "result_level"
    CHECK_PARAM = "check_param"
    PROFILE_TARGET = "target"
    PROFILE_TAGS = "tags"
    PROFILE_ALERT_LEVEL = "alert_level"
    PROFILE_CUSTOM_CHK = "custom_check"
    HCCONF = "hcconf"
    PROFILE_INCLUDE = "include"
    PROFILE_EXCLUDE = "exclude"
    CUSTOMCHECK = "CUSTOMCHECK"
    ALL = "ALL"


def _make_mock_check_parser():
    """
    Build a mock object emulating the CheckParser interface used by ProfileParser:
    - mGetTargetList
    - mGetTagList
    - mGetAlertLevelList
    - mGetTagCheckList
    - mGetCheckId
    """
    m = Mock(name="MockCheckParser")

    # Targets, tags, and alert levels available to the system
    m.mGetTargetList.return_value = ["TGT1", "TGT2", "ALL"]
    m.mGetTagList.return_value = ["TAG1", "TAG2", "ALL"]
    # Ordered alert levels (lowest to highest)
    m.mGetAlertLevelList.return_value = ["L1", "L2", "L3"]

    # Master checklist mapping for tags/targets/alert levels/custom groups
    # Include required 'ALL' bucket used for validation of numeric ids
    master = {
        "ALL": ["100", "200", "300", "400"],
        "TGT1": ["100", "200"],
        "TGT2": ["200", "300"],
        "TAG1": ["200", "300"],
        "TAG2": ["100", "300"],
        "L1": ["100", "200"],
        "L2": ["200", "300"],
        "L3": ["300", "400"],
        "CUSTOMCHECK": ["900"]
    }
    m.mGetTagCheckList.return_value = master

    # Name-to-id mapping for string identifiers
    # Used when profile CHECK_PARAM or include/exclude carry names
    name_map = {
        "CHK_FOO": "100",
        "CHK_BAR": "200",
        "CHK_BAZ": "300",
        "CHK_QUX": "400",
        "CHK_CUST": "900",
    }
    m.mGetCheckId.side_effect = lambda name: name_map.get(name)

    return m


class ebTestCluincident(ebTestClucontrol):
    """
    Tests for ProfileParser using ebTestClucontrol base to match exatest structure.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Patch constants and logging in target module
        cls._p_hc = patch("exabox.healthcheck.profile_parser.HcConstants", _FakeHcConstants)
        cls._p_dbg = patch("exabox.healthcheck.profile_parser.ebLogDebug")
        cls._p_err = patch("exabox.healthcheck.profile_parser.ebLogError")
        cls.HcConstants = cls._p_hc.start()
        cls.mock_dbg = cls._p_dbg.start()
        cls.mock_err = cls._p_err.start()

    @classmethod
    def tearDownClass(cls):
        cls._p_err.stop()
        cls._p_dbg.stop()
        cls._p_hc.stop()
        super().tearDownClass()

    def setUp(self):
        # Reset patched loggers before each test to avoid cross-test contamination
        self.mock_err.reset_mock()
        self.mock_dbg.reset_mock()

    # Auto-generated test for validateProfile: success path
    def test_validateProfile_success(self):
        oCheckParser = _make_mock_check_parser()
        json_profile = {
            _FakeHcConstants.PROFILE_NAME: "hc_profile_ok",
            _FakeHcConstants.CHECK_LIST: {
                _FakeHcConstants.PROFILE_TARGET: ["TGT1"],
                _FakeHcConstants.PROFILE_TAGS: ["TAG1"],
                _FakeHcConstants.PROFILE_ALERT_LEVEL: "L2",
            },
            _FakeHcConstants.RESULT_LEVEL: "INFO",
        }
        p = ProfileParser(oCheckParser, json_profile)
        self.assertTrue(p.validateProfile(json_profile))
        self.mock_err.assert_not_called()

    # Auto-generated test for validateProfile: missing required keys -> False
    def test_validateProfile_missing_required_keys(self):
        oCheckParser = _make_mock_check_parser()
        # Missing CHECK_LIST and RESULT_LEVEL
        json_profile = {
            _FakeHcConstants.PROFILE_NAME: "missing_keys",
        }
        p = ProfileParser(oCheckParser, json_profile)
        self.assertFalse(p.validateProfile(json_profile))
        self.assertTrue(self.mock_err.called)

    # Auto-generated test for validateProfile: invalid target/tag/alert_level -> False
    def test_validateProfile_invalid_values(self):
        o = _make_mock_check_parser()
        bad = {
            _FakeHcConstants.PROFILE_NAME: "bad_values",
            _FakeHcConstants.CHECK_LIST: {
                _FakeHcConstants.PROFILE_TARGET: ["NOT_A_TARGET"],
                _FakeHcConstants.PROFILE_TAGS: ["NOT_A_TAG"],
                _FakeHcConstants.PROFILE_ALERT_LEVEL: "L999",
            },
            _FakeHcConstants.RESULT_LEVEL: "WARN",
        }
        p = ProfileParser(o, bad)
        self.assertFalse(p.validateProfile(bad))
        self.assertTrue(self.mock_err.called)

    # Auto-generated test for parseProfile: numeric and string check_param handling
    def test_parseProfile_check_params_numeric_and_string(self):
        o = _make_mock_check_parser()
        json_profile = {
            _FakeHcConstants.PROFILE_NAME: "with_params",
            _FakeHcConstants.CHECK_LIST: {
                _FakeHcConstants.PROFILE_TARGET: ["TGT1"],
                _FakeHcConstants.PROFILE_TAGS: ["TAG1"],
                _FakeHcConstants.PROFILE_ALERT_LEVEL: "L1",
            },
            _FakeHcConstants.RESULT_LEVEL: "INFO",
            _FakeHcConstants.CHECK_PARAM: {
                "100": {"threshold": 5},      # numeric id in ALL -> accepted
                "CHK_BAR": {"mode": "fast"},  # named -> resolves to 200
                "999": {"ignore": True},      # numeric not in ALL -> error path
                "UNKNOWN_NAME": {"x": 1},     # name not resolvable -> error path
            },
            _FakeHcConstants.HCCONF: {"key": "val"},
        }
        p = ProfileParser(o, json_profile)
        # Force happy path init to call validate+parse
        self.assertTrue(p.mInitProfileParser())
        chk = p.mGetCheckParam()
        self.assertIn("100", chk)
        self.assertIn("200", chk)  # from CHK_BAR
        # Ensure erroneous params did not populate
        self.assertNotIn("999", chk)
        self.assertNotIn("UNKNOWN_NAME", chk)
        # HCCONF retained
        self.assertEqual({"key": "val"}, p.mGetHcConf())
        # Get-param-by-id
        self.assertEqual({"threshold": 5}, p.mGetCheckParamForId("100"))
        self.assertEqual({}, p.mGetCheckParamForId("does_not_exist"))

    # Auto-generated test for buildChecklist: intersection, include, exclude, custom
    def test_buildChecklist_intersect_include_exclude_custom(self):
        o = _make_mock_check_parser()
        # Construct a profile that intersects TGT1 (100,200) with TAG1 (200,300) and alert L1 (100,200)
        # Intersection should give at least {"200"}; then include "CHK_BAZ"(300) and exclude "200"
        json_profile = {
            _FakeHcConstants.PROFILE_NAME: "complex",
            _FakeHcConstants.CHECK_LIST: {
                _FakeHcConstants.PROFILE_TARGET: ["TGT1"],
                _FakeHcConstants.PROFILE_TAGS: ["TAG1"],
                _FakeHcConstants.PROFILE_ALERT_LEVEL: "L1",
                _FakeHcConstants.PROFILE_INCLUDE: ["CHK_BAZ"],  # -> 300
                _FakeHcConstants.PROFILE_EXCLUDE: ["200"],
            },
            _FakeHcConstants.RESULT_LEVEL: "INFO",
            _FakeHcConstants.PROFILE_CUSTOM_CHK: True,
        }
        p = ProfileParser(o, json_profile)
        self.assertTrue(p.mInitProfileParser())
        cl = p.buildChecklist()
        # "200" excluded, include "300" and CUSTOMCHECK adds "900"
        self.assertIn("300", cl)
        self.assertIn("900", cl)
        self.assertNotIn("200", cl)

    # Auto-generated test for mInitProfileParser: failure path when validation fails
    def test_mInitProfileParser_failure(self):
        o = _make_mock_check_parser()
        # Missing RESULT_LEVEL to trigger failure
        bad = {
            _FakeHcConstants.PROFILE_NAME: "fail_init",
            _FakeHcConstants.CHECK_LIST: {
                _FakeHcConstants.PROFILE_TARGET: ["TGT1"],
                _FakeHcConstants.PROFILE_TAGS: ["TAG1"],
                _FakeHcConstants.PROFILE_ALERT_LEVEL: "L1",
            },
        }
        p = ProfileParser(o, bad)
        self.assertFalse(p.mInitProfileParser())

    # Auto-generated test for getters and mDumpProfile logging
    def test_getters_and_dump(self):
        o = _make_mock_check_parser()
        json_profile = {
            _FakeHcConstants.PROFILE_NAME: "getter_profile",
            _FakeHcConstants.CHECK_LIST: {
                _FakeHcConstants.PROFILE_TARGET: ["TGT2"],
                _FakeHcConstants.PROFILE_TAGS: ["TAG2"],
                _FakeHcConstants.PROFILE_ALERT_LEVEL: "ALL",
            },
            _FakeHcConstants.RESULT_LEVEL: "DEBUG",
        }
        p = ProfileParser(o, json_profile)
        self.assertTrue(p.mInitProfileParser())

        # Getter validations
        self.assertEqual(json_profile, p.mGetJsonProfile())
        self.assertEqual("getter_profile", p.mGetProfileName())
        self.assertEqual(["TGT2"], p.mGetProfileTargetList())
        self.assertEqual(["TAG2"], p.mGetProfileTagList())
        self.assertEqual("DEBUG", p.mGetResultLevel())
        self.assertEqual(None, p.mGetCustomCheckList())  # not set
        self.assertEqual({}, p.mGetCheckParam())
        self.assertEqual({}, p.mGetHcConf())

        # Dump should log profile via ebLogDebug
        p.mDumpProfile()
        self.assertTrue(self.mock_dbg.called)


# Coverage plan (auto-generated summary)
# Public methods covered by tests:
# - mInitProfileParser: positive and negative paths
# - mGetJsonProfile
# - mGetProfileTargetList
# - mGetProfileTagList
# - mGetResultLevel
# - mGetCustomCheckList
# - mGetProfileName
# - mGetCheckParam
# - mGetCheckParamForId (valid id and missing id)
# - mGetHcConf
# - mDumpProfile
# - validateProfile: success, missing keys, invalid values branches
# - parseProfile: numeric, named, invalid id/name, HCCONF assignment
# - buildChecklist: intersect, include, exclude, custom branches
#
# No properties detected in target file. No DBaaS/grid-disk mandatory methods in this module.
# All public methods enumerated are touched by tests at least once.

if __name__ == '__main__':
    unittest.main()