#!/bin/python
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#

import base64
import unittest

import bcrypt

from exabox.agent.AuthenticationStorage import ebHttpCredentialType
from exabox.agent.HTTPAuthentication import ebHTTPAuthentication, ebHTTPAuthResult
from exabox.agent.HTTPResponses import HttpCb
from unittest.mock import Mock, patch


class _FakeAuthStorage(object):

    def __init__(self, aCredential, aCredentialType=ebHttpCredentialType.HASH):
        self.__credential = aCredential
        self.__credentialType = aCredentialType

    def mGetCredential(self):
        return self.__credential

    def mGetCredentialType(self):
        return self.__credentialType


class _FakeRequest(object):

    def __init__(self, aHeaders=None):
        self.__headers = aHeaders or {}

    def getHeaders(self):
        return self.__headers


class ebTestHTTPAuthentication(unittest.TestCase):

    def _mMakeAuthHeader(self, aUser=b'admin', aPassword=b'secret'):
        _token = base64.b64encode(aUser + b':' + aPassword).decode('utf8')
        return 'Basic {}'.format(_token)

    def test_000_hash_bytes_accepts_valid_bcrypt_hash(self):
        _stored_hash = bcrypt.hashpw(b'secret', bcrypt.gensalt())
        _auth = ebHTTPAuthentication(_FakeAuthStorage({b'admin': _stored_hash}))

        self.assertEqual(
            _auth.mEvaluateAuth(self._mMakeAuthHeader()),
            ebHTTPAuthResult.AUTH_OK
        )

    def test_001_malformed_hash_returns_auth_failure_response(self):
        _response = {}

        with patch("exabox.agent.HTTPResponses.ebGetHTTPAuthStorage",
                   return_value=_FakeAuthStorage({b'admin': b'$2b$12$short'})):
            _callback = HttpCb({"GET": Mock()}, aAuthenticated=True)

        _allowed = _callback.mProcessAuth(
            _FakeRequest({"Authorization": self._mMakeAuthHeader()}),
            _response
        )

        self.assertFalse(_allowed)
        self.assertEqual(
            _response["output"],
            "Authentication failed. Not authorized to access this service."
        )
        self.assertEqual(_response["success"], "False")


if __name__ == '__main__':
    unittest.main(warnings='ignore')
