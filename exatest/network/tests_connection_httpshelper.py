#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/network/tests_connection_httpshelper.py /main/1 2026/04/03 00:00:00 codex Exp $
#
# tests_connection_httpshelper.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
import json
import os
import tempfile
import unittest
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from exabox.network.Connection import (
    exaBoxConnection,
    ebConnInitialized,
    ebConnConnected,
    ebConnDisconnected,
)
from exabox.network.Local import exaBoxLocal
from exabox.network.Network import (
    exaBoxLoopBackDev,
    exaBoxEtherDev,
    exaBoxIBDev,
    ebNetDevLoopBack,
    ebNetDevEther,
    ebNetDevIB,
)
from exabox.network import HTTPSHelper


class _DummyContext:
    def mCheckConfigOption(self, *_args, **_kwargs):
        return None

    def mCheckRegEntry(self, *_args, **_kwargs):
        return False

    def mGetRegEntry(self, *_args, **_kwargs):
        return None


class _StubSSHConn:
    def __init__(self, should_connect=True):
        self.should_connect = should_connect
        self.is_connectable_calls = []
        self.mConnect_calls = []
        self.mConnectAuthInteractive_calls = []

    def mSetPassword(self, *_):
        pass

    def mSetExaKmsEntry(self, *_):
        pass

    def mSetUser(self, *_):
        pass

    def mSetSudo(self, *_):
        pass

    def mSetMaxRetries(self, *_):
        pass

    def mIsConnectable(self, timeout, aKeyOnly):
        self.is_connectable_calls.append((timeout, aKeyOnly))
        return self.should_connect

    def mConnect(self, timeout, aKeyOnly):
        self.mConnect_calls.append((timeout, aKeyOnly))

    def mConnectAuthInteractive(self, timeout):
        self.mConnectAuthInteractive_calls.append(timeout)


class TestConnection(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('exabox.network.Connection.get_gcontext', return_value=_DummyContext())
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_is_connectable_returns_true_when_already_connected(self):
        conn = exaBoxConnection('my-host')
        conn._exaBoxConnection__state = ebConnConnected
        with mock.patch('exabox.network.Connection.sshconn') as mock_ssh:
            result = conn.mIsConnectable('my-host')
        self.assertTrue(result)
        mock_ssh.assert_not_called()

    def test_is_connectable_resets_disconnected_state_before_probe(self):
        stub = _StubSSHConn(should_connect=True)
        with mock.patch('exabox.network.Connection.sshconn', return_value=stub):
            conn = exaBoxConnection('my-host')
            conn._exaBoxConnection__state = ebConnDisconnected
            conn.mIsConnectable('my-host')
        self.assertEqual(stub.is_connectable_calls, [(None, None)])
        self.assertEqual(conn._exaBoxConnection__state, ebConnDisconnected)

    def test_is_connectable_updates_state_on_failure(self):
        stub = _StubSSHConn(should_connect=False)
        with mock.patch('exabox.network.Connection.sshconn', return_value=stub):
            conn = exaBoxConnection('my-host')
            conn.mIsConnectable('my-host')
        self.assertEqual(conn._exaBoxConnection__state, ebConnInitialized)

    def test_mconnect_forwards_key_only_flag(self):
        stub = _StubSSHConn()
        with mock.patch('exabox.network.Connection.sshconn', return_value=stub):
            conn = exaBoxConnection('my-host')
            conn.mConnect(aKeyOnly=True)
        self.assertEqual(stub.mConnect_calls, [(None, True)])
        self.assertEqual(conn._exaBoxConnection__state, ebConnConnected)

    def test_mconnectauthinteractive_raises_when_already_connected(self):
        stub = _StubSSHConn()
        with mock.patch('exabox.network.Connection.sshconn', return_value=stub):
            conn = exaBoxConnection('my-host')
            conn._exaBoxConnection__state = ebConnConnected
            with self.assertRaises(Exception):
                conn.mConnectAuthInteractive('my-host')
        stub.mConnectAuthInteractive_calls.clear()

    def test_mconnectauthinteractive_resets_disconnected_state(self):
        stub = _StubSSHConn()
        with mock.patch('exabox.network.Connection.sshconn', return_value=stub):
            conn = exaBoxConnection('my-host')
            conn._exaBoxConnection__state = ebConnDisconnected
            conn.mConnectAuthInteractive('my-host')
        self.assertEqual(stub.mConnectAuthInteractive_calls, [None])
        self.assertEqual(conn._exaBoxConnection__state, ebConnConnected)

    def test_mconnecttimed_resets_disconnected_state(self):
        stub = _StubSSHConn()
        with mock.patch('exabox.network.Connection.sshconn', return_value=stub):
            conn = exaBoxConnection('my-host')
            conn._exaBoxConnection__state = ebConnDisconnected
            conn.mConnectTimed('my-host')
        self.assertEqual(stub.mConnect_calls, [(None, None)])
        self.assertEqual(conn._exaBoxConnection__state, ebConnConnected)


class TestHttpsHelper(unittest.TestCase):
    def _write_key(self, key_bytes):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as handle:
            handle.write(key_bytes)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def test_use_oci_certificates_accepts_boolean_true(self):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            with mock.patch('json.load', return_value={'use_ocicerts_https': True}):
                self.assertTrue(HTTPSHelper.use_oci_certificates())
        mock_open.assert_called()

    def test_is_https_enabled_accepts_boolean_true(self):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            with mock.patch('json.load', return_value={'https_enabled': True}):
                self.assertTrue(HTTPSHelper.is_https_enabled())
        mock_open.assert_called()

    def test_is_secret_required_handles_missing_key(self):
        config = {}
        self.assertFalse(HTTPSHelper.is_secret_required(config))

    def test_is_secret_required_returns_false_for_plain_key(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        key_path = self._write_key(key_bytes)
        config = {'client_certificate_key_file': key_path}
        with mock.patch('exabox.network.HTTPSHelper._get_secret', return_value=None):
            self.assertFalse(HTTPSHelper.is_secret_required(config))

    def test_is_secret_required_returns_true_when_secret_missing(self):
        password = b'secret'
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(password),
        )
        key_path = self._write_key(key_bytes)
        config = {'client_certificate_key_file': key_path}
        with mock.patch('exabox.network.HTTPSHelper._get_secret', return_value=None):
            self.assertTrue(HTTPSHelper.is_secret_required(config))

    def test_is_secret_required_returns_true_for_encrypted_key(self):
        password = b'secret'
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(password),
        )
        key_path = self._write_key(key_bytes)
        config = {'client_certificate_key_file': key_path}
        with mock.patch('exabox.network.HTTPSHelper._get_secret', return_value=password):
            self.assertTrue(HTTPSHelper.is_secret_required(config))


class TestLocalAndNetworkHelpers(unittest.TestCase):
    def test_local_init_allows_none_host(self):
        local = exaBoxLocal()
        self.assertIsNone(local._exaBoxLocal__host)

    def test_network_device_types(self):
        loop = exaBoxLoopBackDev()
        ether = exaBoxEtherDev()
        ib = exaBoxIBDev()
        self.assertEqual(loop._exaBoxNetDev__type, ebNetDevLoopBack)
        self.assertEqual(ether._exaBoxNetDev__type, ebNetDevEther)
        self.assertEqual(ib._exaBoxNetDev__type, ebNetDevIB)


if __name__ == '__main__':
    unittest.main()
