#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/agent/tests_httpsignatureverification.py /main/1 2025/11/18 03:55:10 shapatna Exp $
#
# tests_httpsignatureverification.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
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
)


class _FakeHttpReq(object):
    def __init__(self, headers, request_line):
        self._headers = headers
        self._request_line = request_line

    def getHeaders(self):
        return self._headers

    def getRequestLine(self):
        return self._request_line


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

    def tearDown(self):
        self.p_open.stop()
        self.p_load_key.stop()
        self.p_db.stop()
        self.p_kms.stop()
        self.p_ctx.stop()

    def _make_req(self, headers=None, restricted=True):
        if headers is None:
            headers = {}
        rl = self.request_line_restricted if restricted else self.request_line_unrestricted
        return _FakeHttpReq(headers, rl)

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