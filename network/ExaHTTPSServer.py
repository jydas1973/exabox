"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    ExaHTTPSServer - Functionality for HTTPS and TLS Certificate support

FUNCTION:
    Provide basic/core API for managing HTTPS and TLS certificate validation

NOTE:
    None

History:
    aararora    11/14/2025 - Bug 38638555: Incomplete http requests causing agent to hang and not accept further requests
    aararora    07/10/2025 - Bug 38029254: Support tls 1.3 by default and reject tls 1.0 and 1.1 connections
    aararora    04/10/2024 - Bug 36494783: Make protocol version as configurable.
    aararora    02/22/2024 - Bug 36316151: Make https code generic for ExaCC and ExaCS
    aypaul      11/29/2023 - Enh#35730776 Integration of OCI certificate service with exacloud agent.
    aararora    10/19/2023 - Bug 35647494: Add https support for ExaCC
    ndesanto    08/31/2022 - Retrieve tls.conf path from exabox.conf
    ndesanto    11/05/2019 - Create file. ENH 30480538: HTTPS and Certificate Rotation


"""

from six.moves import BaseHTTPServer
from http.server import (BaseHTTPRequestHandler, HTTPServer,
                         SimpleHTTPRequestHandler)
import ssl

from exabox.config.ebCertificateConfig import ebCertificateConfig
from exabox.core.Error import ExacloudRuntimeError
from exabox.network.HTTPSHelper import (is_https_enabled, get_tls_config_path, is_mtls_enabled_exacc,
                                        use_oci_certificates, get_oci_certificates, is_exacs,
                                        get_ca_cert_path_exacc, get_socket_timeout)
from exabox.log.LogMgr import ebLogError

class ExaHTTPSServer(BaseHTTPServer.HTTPServer):
    
    def __init__(self, *args):
        super().__init__(*args, SimpleHTTPRequestHandler)
        if is_https_enabled():
            _rootca_certificate = None
            _client_certificate = None
            _client_privatekey = None
            # Refer https://docs.python.org/3/library/ssl.html#ssl.PROTOCOL_TLS and https://docs.python.org/3/library/ssl.html#id9
            # For now, to support TLS 1.3 - we can pass ssl version as ssl.PROTOCOL_TLS.
            # TODO : It looks like there is no dedicated constant defined for TLS 1.3, and moving forward instead of using
            # ssl.wrap_socket, we will need to write the below code with defining ssl context and wrapping the socket using
            # the context. Check: https://docs.python.org/3/library/ssl.html#socket-creation
            # TODO : Once python 3.11 becomes default - we will have to change the tls implementation below
            # default protocol - this supports both tls 1.2 and 1.3
            _protocol = "PROTOCOL_TLS"
            if use_oci_certificates():
                _rootca_certificate, _client_certificate, _client_privatekey, _protocol = get_oci_certificates()
            else:
                app_cfg = ebCertificateConfig('exacloud', \
                    get_tls_config_path())
                _rootca_certificate = app_cfg['client_certificate_file']
                _client_certificate = app_cfg['local_certificate_file']
                _client_privatekey = app_cfg['local_certificate_key_file']
                _protocol = app_cfg['protocol']

            context = ssl.SSLContext(getattr(ssl, _protocol))
            # Reject TLS 1.0 and TLS 1.1 connections
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1

            # If exacc_mtls flag is set to True or if this is exacs environment (not exacc)
            # We will enable MTLS config for https otherwise TLS config will be enabled
            if is_mtls_enabled_exacc() or is_exacs():
                if not is_exacs():
                    _rootca_certificate = get_ca_cert_path_exacc(app_cfg=app_cfg)
                ssl_cert_config = ssl.CERT_REQUIRED
                if use_oci_certificates():
                    ssl_cert_config = ssl.CERT_NONE
                context.load_verify_locations(_rootca_certificate)
                context.load_cert_chain(_client_certificate, _client_privatekey)
                context.verify_mode = ssl_cert_config
                self.socket = context.wrap_socket(self.socket, server_side=True)
            else:
                context.load_cert_chain(_client_certificate, _client_privatekey)
                self.socket = context.wrap_socket(self.socket, server_side=True)


class ExaHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def __init__(self, *args):
        # Socket timeout - default set to 15 seconds
        # timeout is a class variable available in StreamRequestHandler
        # which can be overridden as an instance variable to set socket timeout.
        # Internally this will set self.connection.settimeout(self.timeout)
        # in the setup() method of StreamRequestHandler
        self.timeout = get_socket_timeout()
        super().__init__(*args)
        if is_https_enabled():
            if hasattr(self, "socket"):
                _rootca_certificate = None
                _client_certificate = None
                _client_privatekey = None
                # default protocol
                _protocol = "PROTOCOL_TLS"
                if use_oci_certificates():
                    _rootca_certificate, _client_certificate, _client_privatekey, _protocol = get_oci_certificates()
                else:
                    app_cfg = ebCertificateConfig('exacloud', \
                        get_tls_config_path())
                    _rootca_certificate = app_cfg['client_certificate_file']
                    _client_certificate = app_cfg['local_certificate_file']
                    _client_privatekey = app_cfg['local_certificate_key_file']
                    _protocol = app_cfg['protocol']

                context = ssl.SSLContext(getattr(ssl, _protocol))
                # Reject TLS 1.0 and TLS 1.1 connections
                context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
                # If exacc_mtls flag is set to True or if this is exacs environment (not exacc)
                # We will enable MTLS config for https otherwise TLS config will be enabled
                if is_mtls_enabled_exacc() or is_exacs():
                    if not is_exacs():
                        _rootca_certificate = get_ca_cert_path_exacc(app_cfg=app_cfg)
                    ssl_cert_config = ssl.CERT_REQUIRED
                    if use_oci_certificates():
                        ssl_cert_config = ssl.CERT_NONE
                    context.load_verify_locations(_rootca_certificate)
                    context.load_cert_chain(_client_certificate, _client_privatekey)
                    context.verify_mode = ssl_cert_config
                    self.socket = context.wrap_socket(self.socket, server_side=True)
                else:
                    context.load_cert_chain(_client_certificate, _client_privatekey)
                    self.socket = context.wrap_socket(self.socket, server_side=True)
