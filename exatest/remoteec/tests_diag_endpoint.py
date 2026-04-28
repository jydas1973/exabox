#!/bin/python
#
# $Header: tests_diag_endpoint.py 23-apr-2026.17:12:16 shapatna Exp $
#
# tests_diag_endpoint.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_diag_endpoint.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    04/23/26 - Bug: 39248066 - Fix for restricting file read
#                           outside diagPath directory
#    shapatna    04/23/26 - Creation
#

import base64
import os
import shutil
import tempfile
import unittest

from unittest import mock

from exabox.managment.src.DiagEndpoint import DiagEndpoint


class _FakeConfig(object):

    def __init__(self, aConfigPath, aExacloudPath):
        self._configPath = aConfigPath
        self._exacloudPath = aExacloudPath

    def mGetPath(self):
        return self._configPath

    def mGetExacloudPath(self):
        return self._exacloudPath

    def mGetConfigValue(self, aKey):
        if aKey == "editor_whitelist":
            return []
        if aKey == "exacloud_log_qry_blacklist":
            return []
        if aKey == "ecra_token":
            return None
        return None

    def mGetExacloudConfigValue(self, aKey):
        return False


class _FakeAsync(object):

    def __init__(self):
        self._processes = []

    def mStartAppend(self, aProcess):
        self._processes.append(aProcess)

    def mGetProcessList(self):
        return list(self._processes)


class _FakeLog(object):

    def __init__(self):
        self.info = []
        self.warn = []

    def mInfo(self, aMessage):
        self.info.append(aMessage)

    def mWarn(self, aMessage):
        self.warn.append(aMessage)


class TestDiagEndpoint(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="diag_endpoint_")
        self._exacloudRoot = os.path.join(self._tmpdir, "exacloud")
        self._configPath = os.path.join(self._exacloudRoot, "exabox", "managment", "src")
        self._diagRoot = os.path.join(self._exacloudRoot, "exabox", "oeda", "requests")

        os.makedirs(self._configPath)
        os.makedirs(self._diagRoot)
        os.makedirs(os.path.join(self._exacloudRoot, "bin"))

    def tearDown(self):
        shutil.rmtree(self._tmpdir)

    def _createEndpoint(self, aBody=None, aUrlArgs=None):
        _response = {}
        _shared = {
            "async": _FakeAsync(),
            "config": _FakeConfig(self._configPath, self._exacloudRoot),
            "log": _FakeLog(),
        }
        _endpoint = DiagEndpoint(aUrlArgs, aBody or {}, _response, _shared)
        return _endpoint, _response

    # Auto-generated test for mListDiags
    def test_mListDiags_filters_to_incident_zip_files(self):
        os.makedirs(os.path.join(self._diagRoot, "nested"))
        with open(os.path.join(self._diagRoot, "Incident_alpha.zip"), "wb") as _fd:
            _fd.write(b"alpha")
        with open(os.path.join(self._diagRoot, "ignore.txt"), "wb") as _fd:
            _fd.write(b"ignore")
        with open(os.path.join(self._diagRoot, "nested", "Incident_beta.zip"), "wb") as _fd:
            _fd.write(b"beta")
        with open(os.path.join(self._diagRoot, "nested", "Incident_gamma.tar"), "wb") as _fd:
            _fd.write(b"gamma")

        _endpoint, _ = self._createEndpoint()

        self.assertEqual(
            sorted(_endpoint.mListDiags()),
            ["Incident_alpha.zip", "nested/Incident_beta.zip"],
        )

    # Auto-generated test for mListDiags
    def test_mListDiags_returns_empty_list_when_no_incident_zip_exists(self):
        with open(os.path.join(self._diagRoot, "diag.txt"), "wb") as _fd:
            _fd.write(b"ignore")

        _endpoint, _ = self._createEndpoint()

        self.assertEqual(_endpoint.mListDiags(), [])

    # Auto-generated test for mDownloadDiag
    def test_mDownloadDiag_returns_base64_content_for_file_within_diag_root(self):
        os.makedirs(os.path.join(self._diagRoot, "nested"))
        _diagFile = os.path.join(self._diagRoot, "nested", "Incident_alpha.zip")
        _payload = b"diag-bytes"
        with open(_diagFile, "wb") as _fd:
            _fd.write(_payload)

        _endpoint, _response = self._createEndpoint()
        _endpoint.mDownloadDiag("nested/Incident_alpha.zip")

        self.assertEqual(_response["status"], 200)
        self.assertEqual(_response["ctype"], "application/octet-stream")
        self.assertEqual(_response["text"], base64.b64encode(_payload).decode("utf-8"))

    # Auto-generated test for mDownloadDiag
    def test_mDownloadDiag_sets_error_when_requested_file_is_missing_inside_diag_root(self):
        _endpoint, _response = self._createEndpoint()

        _endpoint.mDownloadDiag("missing/Incident_missing.zip")

        self.assertEqual(_response["status"], 500)
        self.assertIn("File not found in File System or cannot access File System", _response["text"])
        self.assertEqual(_response["text"], _response["error"])
        self.assertIn(os.path.join(self._diagRoot, "missing", "Incident_missing.zip"), _response["text"])

    # Auto-generated test for mDownloadDiag
    def test_mDownloadDiag_rejects_path_escape_even_when_target_file_exists(self):
        _outsideDir = os.path.join(self._tmpdir, "outside")
        os.makedirs(_outsideDir)
        _outsideFile = os.path.join(_outsideDir, "Incident_escape.zip")
        with open(_outsideFile, "wb") as _fd:
            _fd.write(b"escape")

        _endpoint, _response = self._createEndpoint()
        _endpoint.mDownloadDiag("../../../../outside/Incident_escape.zip")

        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["text"], _response["error"])
        self.assertIn(_outsideFile, _response["text"])

    # Auto-generated test for mDownloadDiag
    def test_mDownloadDiag_rejects_symlink_that_resolves_outside_diag_root(self):
        _outsideDir = os.path.join(self._tmpdir, "outside")
        os.makedirs(_outsideDir)
        _outsideFile = os.path.join(_outsideDir, "Incident_link_escape.zip")
        with open(_outsideFile, "wb") as _fd:
            _fd.write(b"escape")

        os.symlink(_outsideFile, os.path.join(self._diagRoot, "Incident_link_escape.zip"))

        _endpoint, _response = self._createEndpoint()
        _endpoint.mDownloadDiag("Incident_link_escape.zip")

        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["text"], _response["error"])
        self.assertIn(_outsideFile, _response["text"])

    # Auto-generated test for mPost
    def test_mPost_returns_500_when_zip_path_is_outside_diag_root(self):
        _body = {
            "zip": "../../exabox/managment/config/endpoints.conf",
            "local": "/tmp/ignored",
        }
        _endpoint, _response = self._createEndpoint(_body)

        _endpoint.mPost()

        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["text"], _response["error"])
        self.assertIn("File not found in File System or cannot access File System", _response["text"])

    # Auto-generated test for mCreateDiag
    def test_mCreateDiag_builds_command_without_optional_payload(self):
        _endpoint, _response = self._createEndpoint({"remote_xml_path": "/tmp/diag.xml"})

        with mock.patch.object(_endpoint, "mCreateBashProcess", return_value={"id": "123"}) as _create:
            _endpoint.mCreateDiag()

        _create.assert_called_once_with(
            [[
                os.path.join(self._exacloudRoot, "bin/exacloud"),
                "-clu",
                "create_diag",
                "-cf",
                "/tmp/diag.xml",
            ]],
            aName="diag create",
        )
        self.assertEqual(_response["text"], {"id": "123"})

    # Auto-generated test for mCreateDiag
    def test_mCreateDiag_builds_command_with_optional_payload(self):
        _body = {
            "remote_xml_path": "/tmp/diag.xml",
            "remote_payload_path": "/tmp/payload.json",
        }
        _endpoint, _response = self._createEndpoint(_body)

        with mock.patch.object(_endpoint, "mCreateBashProcess", return_value={"id": "456"}) as _create:
            _endpoint.mCreateDiag()

        _create.assert_called_once_with(
            [[
                os.path.join(self._exacloudRoot, "bin/exacloud"),
                "-clu",
                "create_diag",
                "-cf",
                "/tmp/diag.xml",
                "-jc",
                "/tmp/payload.json",
            ]],
            aName="diag create",
        )
        self.assertEqual(_response["text"], {"id": "456"})

    # Auto-generated test for mGet
    def test_mGet_stores_listed_diagnostics_in_response(self):
        _endpoint, _response = self._createEndpoint()

        with mock.patch.object(_endpoint, "mListDiags", return_value=["Incident_alpha.zip"]) as _list:
            _endpoint.mGet()

        _list.assert_called_once_with()
        self.assertEqual(_response["text"], ["Incident_alpha.zip"])

    # Auto-generated test for mPost
    def test_mPost_delegates_to_mDownloadDiag_using_zip_from_body(self):
        _endpoint, _ = self._createEndpoint({"zip": "Incident_alpha.zip"})

        with mock.patch.object(_endpoint, "mDownloadDiag") as _download:
            _endpoint.mPost()

        _download.assert_called_once_with("Incident_alpha.zip")

    # Auto-generated test for mPut
    def test_mPut_delegates_to_mCreateDiag(self):
        _endpoint, _ = self._createEndpoint({"remote_xml_path": "/tmp/diag.xml"})

        with mock.patch.object(_endpoint, "mCreateDiag") as _create:
            _endpoint.mPut()

        _create.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
