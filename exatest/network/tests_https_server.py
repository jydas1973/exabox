#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/network/tests_https_server.py /main/1 2025/07/14 06:32:01 aararora Exp $
#
# tests_https_server.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_https_server.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    07/10/25 - Unit test for https server
#    aararora    07/10/25 - Creation
#
import os
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from exabox.network.ExaHTTPSServer import ExaHTTPSServer
from exabox.network.ExaHTTPSServer import ExaHTTPRequestHandler
from exabox.managment.src.ManagmentServer import ManagmentServer

class TestExaHTTPSServer(unittest.TestCase):

    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.HTTPServer.__init__')
    def mock_super_init(self, *args, **kwargs):
        self.socket = MagicMock()

    @patch('exabox.network.ExaHTTPSServer.ssl.SSLContext')
    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.HTTPServer.__init__', new=mock_super_init)
    @patch('exabox.network.ExaHTTPSServer.ebCertificateConfig', return_value={'client_certificate_file': 'client_certificate_file',
                                                                              'local_certificate_file': 'local_certificate_file',
                                                                              'local_certificate_key_file': 'local_certificate_key_file',
                                                                              'protocol': 'PROTOCOL_TLS'})
    
    def test_init_calls_super(self, mock_eb_certificate_config, mock_get_tls_config_path, mock_ssl_context):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        ExaHTTPSServer(server_address, None)
        instance = ExaHTTPSServer.__new__(ExaHTTPSServer)
        instance.__init__(server_address, None)
        self.assertIsNotNone(instance.socket)

    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.is_https_enabled', return_value=False)
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.HTTPServer.__init__')
    def test_init_https_disabled(self, mock_super_init, mock_is_https_enabled, mock_get_tls_config_path):
        server_address = ('localhost', 8080)
        ExaHTTPSServer(server_address, None)
        # No SSL configuration should be done
        self.assertTrue(mock_is_https_enabled.called)

    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.is_https_enabled', return_value=True)
    @patch('exabox.network.ExaHTTPSServer.use_oci_certificates', return_value=False)
    @patch('exabox.network.ExaHTTPSServer.ebCertificateConfig', return_value={'client_certificate_file': 'client_certificate_file',
                                                                              'local_certificate_file': 'local_certificate_file',
                                                                              'local_certificate_key_file': 'local_certificate_key_file',
                                                                              'protocol': 'PROTOCOL_TLS'})
    @patch('exabox.network.ExaHTTPSServer.ssl.SSLContext')
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.HTTPServer.__init__', new=mock_super_init)
    def test_init_https_enabled_non_oci(self, mock_ssl_context, mock_eb_certificate_config, mock_use_oci_certificates, mock_is_https_enabled,
                                        mock_get_tls_config_path):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        ExaHTTPSServer(server_address, None)
        self.assertTrue(mock_eb_certificate_config.called)
        self.assertTrue(mock_ssl_context.called)

    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.is_https_enabled', return_value=True)
    @patch('exabox.network.ExaHTTPSServer.use_oci_certificates', return_value=True)
    @patch('exabox.network.ExaHTTPSServer.get_oci_certificates', return_value=('_rootca_certificate', '_client_certificate', '_client_privatekey', 'PROTOCOL_TLS'))
    @patch('exabox.network.ExaHTTPSServer.ssl.SSLContext')
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.HTTPServer.__init__', new=mock_super_init)
    def test_init_https_enabled_oci(self, mock_ssl_context, mock_get_oci_certificates, mock_use_oci_certificates, mock_is_https_enabled,
                                    mock_get_tls_config_path):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        ExaHTTPSServer(server_address, None)
        self.assertTrue(mock_get_oci_certificates.called)
        self.assertTrue(mock_ssl_context.called)

    @patch('exabox.network.ExaHTTPSServer.is_exacs', return_value=False)
    @patch('exabox.network.ExaHTTPSServer.is_mtls_enabled_exacc', return_value=False)
    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.is_https_enabled', return_value=True)
    @patch('exabox.network.ExaHTTPSServer.use_oci_certificates', return_value=True)
    @patch('exabox.network.ExaHTTPSServer.get_oci_certificates', return_value=('_rootca_certificate', '_client_certificate', '_client_privatekey', 'PROTOCOL_TLS'))
    @patch('exabox.network.ExaHTTPSServer.ssl.SSLContext')
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.HTTPServer.__init__', new=mock_super_init)
    def test_init_https_enabled_oci_exacc(self, mock_ssl_context, mock_get_oci_certificates, mock_use_oci_certificates, mock_is_https_enabled,
                                          mock_get_tls_config_path, mock_mtls_enabled_exacc, mock_exacs):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        ExaHTTPSServer(server_address, None)
        self.assertTrue(mock_get_oci_certificates.called)
        self.assertTrue(mock_ssl_context.called)

class TestExaHTTPRequestHandler(unittest.TestCase):

    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.BaseHTTPRequestHandler.__init__')
    def mock_super_init_handler(self, *args, **kwargs):
        self.socket = MagicMock()

    @patch('exabox.network.ExaHTTPSServer.ssl.SSLContext')
    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.BaseHTTPRequestHandler.__init__', new=mock_super_init_handler)
    @patch('exabox.network.ExaHTTPSServer.ebCertificateConfig', return_value={'client_certificate_file': 'client_certificate_file',
                                                                              'local_certificate_file': 'local_certificate_file',
                                                                              'local_certificate_key_file': 'local_certificate_key_file',
                                                                              'protocol': 'PROTOCOL_TLS'})
    
    def test_init_calls_super(self, mock_eb_certificate_config, mock_get_tls_config_path, mock_ssl_context):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        ExaHTTPRequestHandler(server_address, None)
        instance = ExaHTTPRequestHandler.__new__(ExaHTTPRequestHandler)
        instance.__init__(server_address, None)
        self.assertIsNotNone(instance.socket)

    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.is_https_enabled', return_value=False)
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.BaseHTTPRequestHandler.__init__')
    def test_init_https_disabled(self, mock_super_init, mock_is_https_enabled, mock_get_tls_config_path):
        server_address = ('localhost', 8080)
        ExaHTTPRequestHandler(server_address, None)
        # No SSL configuration should be done
        self.assertTrue(mock_is_https_enabled.called)

    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.is_https_enabled', return_value=True)
    @patch('exabox.network.ExaHTTPSServer.use_oci_certificates', return_value=False)
    @patch('exabox.network.ExaHTTPSServer.ebCertificateConfig', return_value={'client_certificate_file': 'client_certificate_file',
                                                                              'local_certificate_file': 'local_certificate_file',
                                                                              'local_certificate_key_file': 'local_certificate_key_file',
                                                                              'protocol': 'PROTOCOL_TLS'})
    @patch('exabox.network.ExaHTTPSServer.ssl.SSLContext')
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.BaseHTTPRequestHandler.__init__', new=mock_super_init_handler)
    def test_init_https_enabled_non_oci(self, mock_ssl_context, mock_eb_certificate_config, mock_use_oci_certificates, mock_is_https_enabled,
                                        mock_get_tls_config_path):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        ExaHTTPRequestHandler(server_address, None)
        self.assertTrue(mock_eb_certificate_config.called)
        self.assertTrue(mock_ssl_context.called)

    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.is_https_enabled', return_value=True)
    @patch('exabox.network.ExaHTTPSServer.use_oci_certificates', return_value=True)
    @patch('exabox.network.ExaHTTPSServer.get_oci_certificates', return_value=('_rootca_certificate', '_client_certificate', '_client_privatekey', 'PROTOCOL_TLS'))
    @patch('exabox.network.ExaHTTPSServer.ssl.SSLContext')
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.BaseHTTPRequestHandler.__init__', new=mock_super_init_handler)
    def test_init_https_enabled_oci(self, mock_ssl_context, mock_get_oci_certificates, mock_use_oci_certificates, mock_is_https_enabled,
                                    mock_get_tls_config_path):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        ExaHTTPRequestHandler(server_address, None)
        self.assertTrue(mock_get_oci_certificates.called)
        self.assertTrue(mock_ssl_context.called)

    @patch('exabox.network.ExaHTTPSServer.is_exacs', return_value=False)
    @patch('exabox.network.ExaHTTPSServer.is_mtls_enabled_exacc', return_value=False)
    @patch('exabox.network.ExaHTTPSServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.network.ExaHTTPSServer.is_https_enabled', return_value=True)
    @patch('exabox.network.ExaHTTPSServer.use_oci_certificates', return_value=False)
    @patch('exabox.network.ExaHTTPSServer.ebCertificateConfig', return_value={'client_certificate_file': 'client_certificate_file',
                                                                              'local_certificate_file': 'local_certificate_file',
                                                                              'local_certificate_key_file': 'local_certificate_key_file',
                                                                              'protocol': 'PROTOCOL_TLS'})
    @patch('exabox.network.ExaHTTPSServer.ssl.SSLContext')
    @patch('exabox.network.ExaHTTPSServer.BaseHTTPServer.BaseHTTPRequestHandler.__init__', new=mock_super_init_handler)
    def test_init_https_enabled_non_oci(self, mock_ssl_context, mock_eb_certificate_config, mock_use_oci_certificates, mock_is_https_enabled,
                                        mock_get_tls_config_path, mock_mtls_enabled_exacc, mock_exacs):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        ExaHTTPRequestHandler(server_address, None)
        self.assertTrue(mock_eb_certificate_config.called)
        self.assertTrue(mock_ssl_context.called)

class TestManagmentServerCreateSocket(unittest.TestCase):

    @patch('exabox.managment.src.ManagmentServer.ssl.SSLContext')
    @patch('exabox.managment.src.ManagmentServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.managment.src.ManagmentServer.ebCertificateConfig', return_value={'client_certificate_file': 'client_certificate_file',
                                                                              'local_certificate_file_remoteec': 'local_certificate_file_remoteec',
                                                                              'local_certificate_key_file_remoteec': 'local_certificate_key_file_remoteec',
                                                                              'protocol': 'PROTOCOL_TLS'})
    
    def test_init_calls_super(self, mock_eb_certificate_config, mock_get_tls_config_path, mock_ssl_context):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        instance = ManagmentServer.__new__(ManagmentServer)
        instance.socket = MagicMock()
        instance.mCreateSocket()
        self.assertIsNotNone(instance.socket)

    @patch('exabox.managment.src.ManagmentServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.managment.src.ManagmentServer.is_https_enabled', return_value=False)
    def test_init_https_disabled(self, mock_is_https_enabled, mock_get_tls_config_path):
        server_address = ('localhost', 8080)
        instance = ManagmentServer.__new__(ManagmentServer)
        instance.socket = MagicMock()
        instance.mCreateSocket()
        # No SSL configuration should be done
        self.assertTrue(mock_is_https_enabled.called)

    @patch('exabox.managment.src.ManagmentServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.managment.src.ManagmentServer.is_https_enabled', return_value=True)
    @patch('exabox.managment.src.ManagmentServer.use_oci_certificates', return_value=False)
    @patch('exabox.managment.src.ManagmentServer.ebCertificateConfig', return_value={'client_certificate_file': 'client_certificate_file',
                                                                              'local_certificate_file_remoteec': 'local_certificate_file_remoteec',
                                                                              'local_certificate_key_file_remoteec': 'local_certificate_key_file_remoteec',
                                                                              'protocol': 'PROTOCOL_TLS'})
    @patch('exabox.managment.src.ManagmentServer.ssl.SSLContext')
    def test_init_https_enabled_non_oci(self, mock_ssl_context, mock_eb_certificate_config, mock_use_oci_certificates, mock_is_https_enabled,
                                        mock_get_tls_config_path):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        instance = ManagmentServer.__new__(ManagmentServer)
        instance.socket = MagicMock()
        instance.mCreateSocket()
        self.assertTrue(mock_eb_certificate_config.called)
        self.assertTrue(mock_ssl_context.called)

    @patch('exabox.managment.src.ManagmentServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.managment.src.ManagmentServer.is_https_enabled', return_value=True)
    @patch('exabox.managment.src.ManagmentServer.use_oci_certificates', return_value=True)
    @patch('exabox.managment.src.ManagmentServer.get_oci_certificates', return_value=('_rootca_certificate', '_client_certificate', '_client_privatekey', 'PROTOCOL_TLS'))
    @patch('exabox.managment.src.ManagmentServer.ssl.SSLContext')
    def test_init_https_enabled_oci(self, mock_ssl_context, mock_get_oci_certificates, mock_use_oci_certificates, mock_is_https_enabled,
                                    mock_get_tls_config_path):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        instance = ManagmentServer.__new__(ManagmentServer)
        instance.socket = MagicMock()
        instance.mCreateSocket()
        self.assertTrue(mock_get_oci_certificates.called)
        self.assertTrue(mock_ssl_context.called)

    @patch('exabox.managment.src.ManagmentServer.is_exacs', return_value=False)
    @patch('exabox.managment.src.ManagmentServer.is_mtls_enabled_exacc', return_value=False)
    @patch('exabox.managment.src.ManagmentServer.get_tls_config_path', return_value=f"{os.path.dirname(os.path.abspath(__file__))}/tls.conf")
    @patch('exabox.managment.src.ManagmentServer.is_https_enabled', return_value=True)
    @patch('exabox.managment.src.ManagmentServer.use_oci_certificates', return_value=False)
    @patch('exabox.managment.src.ManagmentServer.ebCertificateConfig', return_value={'client_certificate_file': 'client_certificate_file',
                                                                              'local_certificate_file_remoteec': 'local_certificate_file_remoteec',
                                                                              'local_certificate_key_file_remoteec': 'local_certificate_key_file_remoteec',
                                                                              'protocol': 'PROTOCOL_TLS'})
    @patch('exabox.managment.src.ManagmentServer.ssl.SSLContext')
    def test_init_https_enabled_non_oci(self, mock_ssl_context, mock_eb_certificate_config, mock_use_oci_certificates, mock_is_https_enabled,
                                        mock_get_tls_config_path, mock_mtls_enabled_exacc, mock_exacs):
        server_address = ('localhost', 8080)
        mock_ssl_context.wrap_socket = MagicMock()
        instance = ManagmentServer.__new__(ManagmentServer)
        instance.socket = MagicMock()
        instance.mCreateSocket()
        self.assertTrue(mock_eb_certificate_config.called)
        self.assertTrue(mock_ssl_context.called)

if __name__ == '__main__':
    unittest.main()