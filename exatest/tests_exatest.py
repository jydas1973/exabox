#!/bin/python
#
# $Header: $
#
# tests_exatest.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_exatest.py - Unit tests for exatest coverage helpers
#
#    DESCRIPTION
#      Verifies coverage HTML resolution used by exatest ADE coverage reporting.
#
#    MODIFIED   (MM/DD/YY)
#    joysjose    05/22/26 - Bug 39354509 - Add exatest coverage lookup tests
#

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

from exabox.exatest import exatest


class TestExatestCoverageHtmlLookup(unittest.TestCase):

    def setUp(self):
        self._orig_cwd = os.getcwd()
        self._tmpdir = tempfile.mkdtemp(prefix="exatest_cov_")
        self._exacloud_root = os.path.join(self._tmpdir, "exacloud")
        self._result_dir = os.path.join(self._tmpdir, "results")
        self._coverage_dir = os.path.join(self._result_dir, "coverage_html")
        os.makedirs(self._exacloud_root)
        os.makedirs(self._coverage_dir)

        self._manager = exatest.ebExatestManager()
        self._manager.mSetExacloudPath(self._exacloud_root)
        self._manager.mSetResultDir(self._result_dir)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmpdir)

    def _make_source_path(self, aRelativePath):
        _path = os.path.join(self._exacloud_root, aRelativePath)
        _dirname = os.path.dirname(_path)
        if _dirname and not os.path.exists(_dirname):
            os.makedirs(_dirname)
        return _path

    def _write_status(self, aRelativeFilename, aHtmlFilename):
        _status_path = os.path.join(self._coverage_dir, "status.json")
        with open(_status_path, "w") as _file:
            json.dump(
                {
                    "files": {
                        "entry": {
                            "index": {
                                "relative_filename": aRelativeFilename,
                                "html_filename": aHtmlFilename
                            }
                        }
                    }
                },
                _file
            )

    def _write_html(self, aFilename, aClassName="run", aLineNo=10):
        _html_path = os.path.join(self._coverage_dir, aFilename)
        with open(_html_path, "w") as _file:
            _file.write(
                '<p id="t{0}" class="{1}">{0} sample&nbsp;</p>\n'.format(
                    aLineNo, aClassName
                )
            )
        return _html_path

    def test_mGetCoverageHtmlReportPath_uses_status_json_mapping(self):
        _source = self._make_source_path("exabox/ovm/sample_same.py")
        _mapped_html = self._write_html("mapped.html")
        self._write_html("aaa_sample_same_py.html")
        self._write_status("exabox/ovm/sample_same.py", "mapped.html")

        self.assertEqual(
            _mapped_html,
            self._manager.mGetCoverageHtmlReportPath(_source)
        )

    def test_mGetCoverageHtmlReportPath_falls_back_to_glob(self):
        _source = self._make_source_path("exabox/ovm/sample_fallback.py")
        _fallback_html = self._write_html("zzz_sample_fallback_py.html")

        self.assertEqual(
            _fallback_html,
            self._manager.mGetCoverageHtmlReportPath(_source)
        )

    def test_mCalculateAdeCoverage_uses_status_json_lookup(self):
        _source = self._make_source_path("exabox/ovm/sample_same.py")
        self._write_html("aaa_sample_same_py.html", aClassName="mis")
        self._write_html("mapped.html", aClassName="run")
        self._write_status("exabox/ovm/sample_same.py", "mapped.html")

        _log = Mock()

        with patch.object(self._manager, "mGetLog", return_value=_log), \
             patch.object(self._manager, "mExecuteLocal", return_value=(0, "\n1c10\n", "")):
            self._manager.mCalculateAdeCoverage([_source])

        _info_messages = [str(_call.args[0]) for _call in _log.info.call_args_list]
        self.assertTrue(
            any("ADE Coverage total: 1/1 = 100.00%" in _msg for _msg in _info_messages)
        )


if __name__ == "__main__":
    unittest.main()
