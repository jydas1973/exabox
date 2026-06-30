#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/agent/tests_httpsignatureverification.py /main/1 2025/11/18 03:55:10 shapatna Exp $
#
# tests_httpsignatureverification.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_httpsignatureverification.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/02/26 - Add unit tests for security bug 39471474
#    jbrigido    05/07/26 - Add HTTPSignatureVerification delete cell tests
#    shapatna    11/13/25 - Enh 38574081: Add unit tests to improve the
#                           coverage using Cline
#    shapatna    11/13/25 - Creation
#
import unittest
import json
import warnings
from io import BytesIO
import builtins

from unittest import mock
from unittest.mock import patch, MagicMock, call

from cryptography.exceptions import InvalidSignature

# Match reference import style and base test class
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.agent.HTTPSignatureVerification import (
    HTTPSignatureVerify,
    insertRestrictedEndpointsInformation,
    APIACCESS_CONTROL_ENDPOINTS,
    HTTP_HEADER_EXA_AUTH,
    HTTP_HEADER_EXA_OPC_PRINCIPAL,
    MALFORMED_URL,
)


class _FakeHttpReq(object):
    def __init__(self, headers, request_line, body=None):
        self._headers = headers
        self._request_line = request_line
        self._body = body

    def getHeaders(self):
        return self._headers

    def getRequestLine(self):
        return self._request_line

    def getBody(self):
        return self._body


def _build_exa_opc_principal(ptype="service", svc="database"):
    # Build realistic exa-opc-principal JSON structure
    return json.dumps({
        "claims": [
            {"key": "ptype", "value": ptype},
            {"key": "svc", "value": svc},
        ]
    })


def _build_exa_auth_header(
    keyid="test_key.pem",
    algorithm="rsa-sha256",
    headers_list="(request-target) date exa-opc-principal",
    signature_b64="AAAA"
):
    # Compose exa-authorization header value similar to:
    # keyId="...",algorithm="rsa-sha256",headers="(request-target) date exa-opc-principal",signature="YmFzZTY0"
    parts = [
        f'keyId="{keyid}"',
        f'algorithm="{algorithm}"',
        f'headers="{headers_list}"',
        f'signature="{signature_b64}"',
    ]
    return ",".join(parts)

def _build_exa_auth_header_missing_algorithm(
    keyid="test_key.pem",
    algorithm="rsa-sha256",
    headers_list="(request-target) date exa-opc-principal",
    signature_b64="AAAA"
):
    # Build then remove the algorithm segment entirely
    h = _build_exa_auth_header(
        keyid=keyid,
        algorithm=algorithm,
        headers_list=headers_list,
        signature_b64=signature_b64,
    )
    h = h.replace(f'algorithm="{algorithm}",', "")
    return h


def _mock_open_bytes():
    # Return a context manager yielding bytes stream (public key bytes not actually used as load_pem_public_key is mocked)
    m = MagicMock()
    m.__enter__.return_value = BytesIO(b"-----BEGIN PUBLIC KEY-----\nMIIB...==\n-----END PUBLIC KEY-----\n")
    m.__exit__.return_value = False
    return m


REQUEST_LINE_TARGET_CASES = [
    ("GET / HTTP/1.1", "GET", "/"),
    ("POST /CLUCtrl/sim_install HTTP/1.1", "POST", "/CLUCtrl/sim_install"),
    ("PUT /api/v1/resource HTTP/1.1", "PUT", "/api/v1/resource"),
    ("DELETE /users/123 HTTP/1.0", "DELETE", "/users/123"),
    ("POST /HTTP HTTP/1.1", "POST", "/HTTP"),
    ("POST /HTTP/foo HTTP/1.1", "POST", "/HTTP/foo"),
    ("POST /fooHTTP HTTP/1.1", "POST", "/fooHTTP"),
    ("POST /fooHTTPbar HTTP/1.1", "POST", "/fooHTTPbar"),
    ("POST /foo/HTTP/bar HTTP/1.1", "POST", "/foo/HTTP/bar"),
    ("POST /CLUCtrl/HTTP/sim_install HTTP/1.1", "POST", "/CLUCtrl/HTTP/sim_install"),
    ("POST /CLUCtrl/simHTTPinstall HTTP/1.1", "POST", "/CLUCtrl/simHTTPinstall"),
    (
        "POST /fooHTTPbar/CLUCtrl/sim_install HTTP/1.1",
        "POST",
        "/fooHTTPbar/CLUCtrl/sim_install",
    ),
    ("GET /api?param=HTTP HTTP/1.1", "GET", "/api?param=HTTP"),
    ("GET /api?cmd=fooHTTPbar HTTP/1.1", "GET", "/api?cmd=fooHTTPbar"),
    ("GET /api?url=http://example.com HTTP/1.1", "GET", "/api?url=http://example.com"),
    (
        "GET /api?redirect=https://foo.com/HTTP/bar HTTP/1.1",
        "GET",
        "/api?redirect=https://foo.com/HTTP/bar",
    ),
    (
        "POST /CLUCtrl/sim_install?cmd=HTTP HTTP/1.1",
        "POST",
        "/CLUCtrl/sim_install?cmd=HTTP",
    ),
    (
        "POST /fooHTTPbar?target=CLUCtrl/sim_install HTTP/1.1",
        "POST",
        "/fooHTTPbar?target=CLUCtrl/sim_install",
    ),
    (
        "POST /fooHTTPbar/CLUCtrl?cmd=installHTTPnow HTTP/1.1",
        "POST",
        "/fooHTTPbar/CLUCtrl?cmd=installHTTPnow",
    ),
    ("GET /%48%54%54%50 HTTP/1.1", "GET", "/%48%54%54%50"),
    ("GET /foo%48%54%54%50bar HTTP/1.1", "GET", "/foo%48%54%54%50bar"),
    (
        "GET /CLUCtrl/%48%54%54%50/sim_install HTTP/1.1",
        "GET",
        "/CLUCtrl/%48%54%54%50/sim_install",
    ),
    ("GET http://example.com/ HTTP/1.1", "GET", "http://example.com/"),
    (
        "GET http://example.com/fooHTTPbar HTTP/1.1",
        "GET",
        "http://example.com/fooHTTPbar",
    ),
    (
        "GET https://example.com/CLUCtrl/sim_install HTTP/1.1",
        "GET",
        "https://example.com/CLUCtrl/sim_install",
    ),
    (
        "GET /CLUCtrl/../CLUCtrl/sim_install HTTP/1.1",
        "GET",
        "/CLUCtrl/../CLUCtrl/sim_install",
    ),
    ("GET /CLUCtrl/./sim_install HTTP/1.1", "GET", "/CLUCtrl/./sim_install"),
    ("GET /CLUCtrl//sim_install HTTP/1.1", "GET", "/CLUCtrl//sim_install"),
    (
        "GET /CLUCtrl/%2e%2e/sim_install HTTP/1.1",
        "GET",
        "/CLUCtrl/%2e%2e/sim_install",
    ),
]


MALFORMED_REQUEST_LINES = [
    "",
    "POST",
    "POST /CLUCtrl/deleteservice",
    "POST /CLUCtrl/deleteservice FTP/1.0",
    "POST /CLUCtrl/delete service HTTP/1.1",
    "GET",
    "GET /foo",
    "GET /foo HTTP",
    "GET  /foo HTTP/1.1",
    "GET /foo  HTTP/1.1",
    "GET   /foo   HTTP/1.1",
    "GET\t/foo HTTP/1.1",
    "GET /foo\tHTTP/1.1",
]


class ebTestHTTPSignatureVerification(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        # Keep parity with reference tests
        super(ebTestHTTPSignatureVerification, self).setUpClass(aGenerateDatabase=True, aUseOeda=False)
        warnings.filterwarnings("ignore")

    def setUp(self):
        # Patch at point-of-use within module under test
        self.p_ctx = patch("exabox.agent.HTTPSignatureVerification.get_gcontext")
        self.p_kms = patch("exabox.agent.HTTPSignatureVerification.ExaKmsKVDB")
        self.p_db = patch("exabox.agent.HTTPSignatureVerification.ebGetDefaultDB")
        self.p_load_key = patch("exabox.agent.HTTPSignatureVerification.load_pem_public_key")
        self.p_open = patch.object(builtins, "open", side_effect=lambda *a, **k: _mock_open_bytes())

        self.m_ctx = self.p_ctx.start()
        self.m_kms = self.p_kms.start()
        self.m_db = self.p_db.start()
        self.m_load_key = self.p_load_key.start()
        self.m_open = self.p_open.start()

        # Default context: ociexacc=True (ExaCC) and a session key path
        m_gctx = MagicMock()
        m_gctx.mCheckConfigOption.side_effect = lambda key, default=None: {
            "ociexacc": True,
            "wsclient_sessionkeypath": "/tmp/wsclient",
        }.get(key, default)
        self.m_ctx.return_value = m_gctx

        # Default DB: is prod (dev/qa registry entry absent)
        m_dbinst = MagicMock()
        m_dbinst.mCheckRegEntry.return_value = False
        self.m_db.return_value = m_dbinst

        # Default KMS: endpoints include 'deleteservice' as restricted
        m_kmsinst = MagicMock()
        m_kms_entry = MagicMock()
        m_kms_entry.mCreateValueFromEncData.return_value = json.dumps(["deleteservice"])
        m_kmsinst.mSearchEntry.return_value = m_kms_entry
        self.m_kms.return_value = m_kmsinst

        # Default crypto key: public key with verify() that succeeds (no exception)
        m_pubkey = MagicMock()
        m_pubkey.verify.return_value = None
        self.m_load_key.return_value = m_pubkey

        # Common header values
        self.date_val = "Wed, 01 Jan 2025 00:00:00 GMT"
        self.request_line_restricted = "POST /CLUCtrl/deleteservice HTTP/1.1"
        self.request_line_unrestricted = "POST /CLUCtrl/info HTTP/1.1"
        self.request_line_elastic_cell_update = "POST /CLUCtrl/elastic_cell_update HTTP/1.1"
        self.request_line_exascale_cell_update = "POST /CLUCtrl/exascale_cell_update HTTP/1.1"

    def tearDown(self):
        self.p_open.stop()
        self.p_load_key.stop()
        self.p_db.stop()
        self.p_kms.stop()
        self.p_ctx.stop()

    def _make_req(self, headers=None, restricted=True, request_line=None, body=None):
        if headers is None:
            headers = {}
        if request_line is None:
            request_line = self.request_line_restricted if restricted else self.request_line_unrestricted
        return _FakeHttpReq(headers, request_line, body)

    def _make_verifier_for_request_line(self, request_line, headers=None):
        if headers is None:
            headers = {}
        req = _FakeHttpReq(headers, request_line)
        return HTTPSignatureVerify(req)

    def _set_signature_headers(self, verifier, header_names):
        verifier._HTTPSignatureVerify__current_signature_headers = header_names

    def _set_restricted_endpoints(self, verifier, endpoints):
        verifier._HTTPSignatureVerify__endpoints = endpoints

    def test_mGenerateExaCCHTTPSignature_builds_expected_plaintext(self):
        exa_principal = _build_exa_opc_principal(ptype="service", svc="database_preprod")
        headers = {
            "date": self.date_val,
            "opc-request-id": "req-123",
            HTTP_HEADER_EXA_OPC_PRINCIPAL: exa_principal,
        }
        request_line = "POST /CLUCtrl/deleteservice?database=db1&force=true HTTP/1.1"
        verifier = self._make_verifier_for_request_line(request_line, headers)
        self._set_signature_headers(
            verifier,
            ["(request-target)", "date", "opc-request-id", HTTP_HEADER_EXA_OPC_PRINCIPAL],
        )

        plaintext_signature = verifier.mGenerateExaCCHTTPSignature()

        self.assertEqual(
            plaintext_signature,
            "POST /CLUCtrl/deleteservice?database=db1&force=true "
            + self.date_val
            + " req-123 "
            + exa_principal,
        )

    def test_mGenerateExaCCHTTPSignature_ignores_pseudo_headers(self):
        headers = {
            "date": self.date_val,
            "x-exacc-operation": "scale-storage",
        }
        verifier = self._make_verifier_for_request_line(
            "PUT /CLUCtrl/storage_resize HTTP/1.1",
            headers,
        )
        self._set_signature_headers(
            verifier,
            ["(request-target)", "(created)", "date", "x-exacc-operation"],
        )

        plaintext_signature = verifier.mGenerateExaCCHTTPSignature()

        self.assertEqual(
            plaintext_signature,
            "PUT /CLUCtrl/storage_resize " + self.date_val + " scale-storage",
        )

    def test_mGenerateExaCCHTTPSignature_preserves_valid_request_targets(self):
        for request_line, method, expected_target in REQUEST_LINE_TARGET_CASES:
            verifier = self._make_verifier_for_request_line(
                request_line,
                {"date": self.date_val},
            )
            self._set_signature_headers(verifier, ["(request-target)", "date"])

            with self.subTest(request_line=request_line):
                self.assertEqual(
                    verifier.mGenerateExaCCHTTPSignature(),
                    f"{method} {expected_target} {self.date_val}",
                )

    def test_mGenerateExaCCHTTPSignature_returns_none_for_malformed_request_lines(self):
        for request_line in MALFORMED_REQUEST_LINES:
            verifier = self._make_verifier_for_request_line(
                request_line,
                {"date": self.date_val},
            )
            self._set_signature_headers(verifier, ["(request-target)", "date"])

            with self.subTest(request_line=request_line):
                self.assertEqual(verifier.mGenerateExaCCHTTPSignature(), MALFORMED_URL)

    def test_mCheckIfApiAccessRestricted_matches_configured_endpoint_substrings(self):
        restricted_targets = [
            "POST /CLUCtrl/deleteservice HTTP/1.1",
            "POST /CLUCtrl/deleteservice?database=db1 HTTP/1.1",
            "PATCH /CLUCtrl/vmgi_delete/vm1 HTTP/1.1",
        ]

        for request_line in restricted_targets:
            verifier = self._make_verifier_for_request_line(request_line)
            self._set_restricted_endpoints(verifier, ["deleteservice", "vmgi_delete"])

            with self.subTest(request_line=request_line):
                self.assertTrue(verifier.mCheckIfApiAccessRestricted())

    def test_mCheckIfApiAccessRestricted_returns_false_for_unrestricted_endpoint(self):
        verifier = self._make_verifier_for_request_line(
            "GET /CLUCtrl/listdatabases HTTP/1.1",
        )
        self._set_restricted_endpoints(verifier, ["deleteservice", "vmgi_delete"])

        self.assertFalse(verifier.mCheckIfApiAccessRestricted())

    def test_mCheckIfApiAccessRestricted_preserves_valid_request_targets(self):
        for request_line, method, expected_target in REQUEST_LINE_TARGET_CASES:
            verifier = self._make_verifier_for_request_line(request_line)
            self._set_restricted_endpoints(verifier, [expected_target])

            with self.subTest(request_line=request_line):
                self.assertTrue(
                    verifier.mCheckIfApiAccessRestricted(),
                    f"{method} target {expected_target} should be access restricted",
                )

    def test_mCheckIfApiAccessRestricted_returns_false_for_exacs_deployment(self):
        self.m_ctx.return_value.mCheckConfigOption.side_effect = lambda key, default=None: {
            "ociexacc": False,
            "wsclient_sessionkeypath": "/tmp/wsclient",
        }.get(key, default)
        verifier = self._make_verifier_for_request_line(
            "POST /CLUCtrl/deleteservice HTTP/1.1",
        )
        self._set_restricted_endpoints(verifier, ["deleteservice"])

        self.assertFalse(verifier.mCheckIfApiAccessRestricted())

    def test_mCheckIfApiAccessRestricted_returns_false_for_malformed_request_lines(self):
        for request_line in MALFORMED_REQUEST_LINES:
            verifier = self._make_verifier_for_request_line(request_line)
            self._set_restricted_endpoints(verifier, ["deleteservice"])

            with self.subTest(request_line=request_line):
                self.assertEqual(verifier.mCheckIfApiAccessRestricted(), MALFORMED_URL)

    def test_exacs_ociexacc_false_skips_verification_and_returns_true(self):
        # Simulate ExaCS deployment (ociexacc=False)
        self.m_ctx.return_value.mCheckConfigOption.side_effect = lambda key, default=None: {
            "ociexacc": False,
            "wsclient_sessionkeypath": "/tmp/wsclient",
        }.get(key, default)

        req = self._make_req(headers={}, restricted=True)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertTrue(rc, "Expected True when ociexacc=False (verification disabled)")

    def test_unrestricted_endpoint_returns_true_without_headers(self):
        # Endpoint not in restricted list -> verification skipped
        req = self._make_req(headers={}, restricted=False)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertTrue(rc, "Expected True for non-restricted endpoint even without headers")

    def test_elastic_cell_update_delete_cell_payload_requires_signature(self):
        self.m_kms.return_value.mSearchEntry.return_value.mCreateValueFromEncData.return_value = json.dumps(
            ["elastic_cell_update"])
        body = json.dumps({
            "jsonconf": {
                "reshaped_node_subset": {
                    "removed_cells": [{"cell_node_hostname": "cell1.example.com"}],
                    "added_cells": []
                }
            }
        }).encode("utf-8")

        req = self._make_req(
            headers={},
            request_line=self.request_line_elastic_cell_update,
            body=body)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()

        self.assertFalse(rc, "Expected delete-cell payload to require exa-authorization")

    def test_elastic_cell_update_add_cell_payload_skips_signature(self):
        self.m_kms.return_value.mSearchEntry.return_value.mCreateValueFromEncData.return_value = json.dumps(
            ["elastic_cell_update"])
        body = json.dumps({
            "jsonconf": {
                "reshaped_node_subset": {
                    "removed_cells": [],
                    "added_cells": [{"cell_hostname": "cell2"}]
                }
            }
        }).encode("utf-8")

        req = self._make_req(
            headers={},
            request_line=self.request_line_elastic_cell_update,
            body=body)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()

        self.assertTrue(rc, "Expected add-cell payload to skip delete-cell signature enforcement")

    def test_exascale_cell_update_delete_cell_payload_requires_signature(self):
        self.m_kms.return_value.mSearchEntry.return_value.mCreateValueFromEncData.return_value = json.dumps(
            ["exascale_cell_update"])
        body = json.dumps({
            "jsonconf": {
                "reshaped_node_subset": {
                    "removed_cells": [{"cell_node_hostname": "cell1.example.com"}],
                    "added_cells": []
                }
            }
        }).encode("utf-8")

        req = self._make_req(
            headers={},
            request_line=self.request_line_exascale_cell_update,
            body=body)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()

        self.assertFalse(rc, "Expected exascale delete-cell payload to require exa-authorization")

    def test_exascale_cell_update_add_cell_payload_skips_signature(self):
        self.m_kms.return_value.mSearchEntry.return_value.mCreateValueFromEncData.return_value = json.dumps(
            ["exascale_cell_update"])
        body = json.dumps({
            "jsonconf": {
                "reshaped_node_subset": {
                    "removed_cells": [],
                    "added_cells": [{"cell_hostname": "cell2"}]
                }
            }
        }).encode("utf-8")

        req = self._make_req(
            headers={},
            request_line=self.request_line_exascale_cell_update,
            body=body)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()

        self.assertTrue(rc, "Expected exascale add-cell payload to skip delete-cell signature enforcement")

    def test_missing_exa_authorization_header_devqa_returns_true(self):
        # Force Dev/QA environment so missing header is allowed
        self.m_db.return_value.mCheckRegEntry.return_value = True  # mark as Dev/QA (not prod)

        # Restricted endpoint, but exa-authorization header absent
        headers = {
            "date": self.date_val,
            HTTP_HEADER_EXA_OPC_PRINCIPAL: _build_exa_opc_principal()
        }
        req = self._make_req(headers=headers, restricted=True)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertTrue(rc, "Expected True on Dev/QA when exa-authorization header is missing")

    def test_missing_exa_authorization_header_prod_returns_false(self):
        # Production environment (default), restricted endpoint, header absent
        headers = {"date": self.date_val}
        req = self._make_req(headers=headers, restricted=True)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertFalse(rc, "Expected False on Prod when exa-authorization header is missing")

    def test_validate_headers_missing_mandatory_subheader_returns_false(self):
        # exa-authorization missing algorithm should fail validation
        exa_auth = _build_exa_auth_header_missing_algorithm()
        headers = {
            "date": self.date_val,
            HTTP_HEADER_EXA_OPC_PRINCIPAL: _build_exa_opc_principal(),
            HTTP_HEADER_EXA_AUTH: exa_auth,
        }
        req = self._make_req(headers=headers, restricted=True)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertFalse(rc, "Expected False when a mandatory subheader (algorithm) is missing")

    def test_validate_headers_unsupported_algorithm_returns_false(self):
        exa_auth = _build_exa_auth_header(algorithm="rsa-sha512")
        headers = {
            "date": self.date_val,
            HTTP_HEADER_EXA_OPC_PRINCIPAL: _build_exa_opc_principal(),
            HTTP_HEADER_EXA_AUTH: exa_auth,
        }
        req = self._make_req(headers=headers, restricted=True)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertFalse(rc, "Expected False for unsupported algorithm in exa-authorization")

    def test_missing_required_header_listed_in_headers_returns_false(self):
        # headers list requires 'date', but we omit it from request headers
        exa_auth = _build_exa_auth_header(headers_list="(request-target) date exa-opc-principal")
        headers = {
            HTTP_HEADER_EXA_OPC_PRINCIPAL: _build_exa_opc_principal(),
            HTTP_HEADER_EXA_AUTH: exa_auth,
        }
        req = self._make_req(headers=headers, restricted=True)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertFalse(rc, "Expected False when a header listed in exa-authorization headers is absent")

    def test_signature_verification_invalid_returns_false(self):
        # Make crypto verify raise InvalidSignature
        self.m_load_key.return_value.verify.side_effect = InvalidSignature()

        exa_auth = _build_exa_auth_header()
        headers = {
            "date": self.date_val,
            HTTP_HEADER_EXA_OPC_PRINCIPAL: _build_exa_opc_principal(),
            HTTP_HEADER_EXA_AUTH: exa_auth,
        }
        req = self._make_req(headers=headers, restricted=True)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertFalse(rc, "Expected False when signature verification fails with InvalidSignature")

    def test_exa_opc_principal_invalid_claim_value_returns_false(self):
        # Crypto verify succeeds
        self.m_load_key.return_value.verify.side_effect = None

        # svc value not in allowed list per current implementation (['database', 'database_preprod'])
        invalid_principal = _build_exa_opc_principal(ptype="service", svc="analytics")
        exa_auth = _build_exa_auth_header()
        headers = {
            "date": self.date_val,
            HTTP_HEADER_EXA_OPC_PRINCIPAL: invalid_principal,
            HTTP_HEADER_EXA_AUTH: exa_auth,
        }
        req = self._make_req(headers=headers, restricted=True)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertFalse(rc, "Expected False when exa-opc-principal claims do not match allowed values")

    def test_happy_path_returns_true(self):
        # Crypto verify succeeds and exa-opc-principal claims are allowed
        self.m_load_key.return_value.verify.side_effect = None

        exa_auth = _build_exa_auth_header(
            keyid="test_key.pem",
            algorithm="rsa-sha256",
            headers_list="(request-target) date exa-opc-principal",
            signature_b64="AAAA",
        )
        headers = {
            "date": self.date_val,
            HTTP_HEADER_EXA_OPC_PRINCIPAL: _build_exa_opc_principal(ptype="service", svc="database"),
            HTTP_HEADER_EXA_AUTH: exa_auth,
        }
        req = self._make_req(headers=headers, restricted=True)
        verifier = HTTPSignatureVerify(req)
        rc = verifier.mVerifySignature()
        self.assertTrue(rc, "Expected True for valid signature and valid exa-opc-principal claims")

        # Verify that KMS was consulted for endpoints and public key was loaded using keyId/ctx path
        self.m_kms.assert_called()
        self.m_ctx.return_value.mCheckConfigOption.assert_any_call("wsclient_sessionkeypath")
        self.m_load_key.assert_called()

    def test_insertRestrictedEndpointsInformation_success_and_failure(self):
        # Success path
        m_kmsinst = self.m_kms.return_value
        m_kmsinst.mInsertExaKmsEntry.return_value = True

        rc_true = insertRestrictedEndpointsInformation()
        self.assertTrue(rc_true, "Expected True when KMS insert succeeds")
        # Ensure an entry was built with the correct key and a JSON list value
        self.assertIn(call(APIACCESS_CONTROL_ENDPOINTS, mock.ANY), m_kmsinst.mBuildExaKmsEntry.mock_calls)
        # Failure path
        m_kmsinst.mInsertExaKmsEntry.return_value = False
        rc_false = insertRestrictedEndpointsInformation()
        self.assertFalse(rc_false, "Expected False when KMS insert fails")


if __name__ == '__main__':
    unittest.main()
