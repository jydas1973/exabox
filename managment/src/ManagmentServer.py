"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    managmentServer - Basic functionality

FUNCTION:
    Create HTTPServer called managment

NOTE:
    None    

History:
    aararora    07/10/25 - Bug 38029254: Support tls 1.3 by default and reject tls 1.0 and 1.1 connections
    abysebas    12/11/24 - BUG 35647508 - OCI-EXACC: REMOTEEC TO PROVIDE MECHANISM TO ROTATE THE REMOTEEC SERVER CERTIFICATES
    ndesanto    07/24/20 - EXACC bug installation issue fix
    jesandov    03/26/19 - File Creation
"""


import argparse
import time
import sys
import os
import ssl

from multiprocessing import Manager

from exabox.config.ebCertificateConfig import ebCertificateConfig
from exabox.exatest.common.ebExacloudUtil import ebExacloudUtil
from exabox.BaseServer.BaseServer import BaseServerAdministrator, BaseServer
from exabox.BaseServer.AsyncProcessing import ProcessManager
from exabox.core.DBStore import ebGetDefaultDB
from exabox.network.HTTPSHelper import is_https_enabled, get_tls_config_path, is_mtls_enabled_exacc, use_oci_certificates, get_oci_certificates, is_exacs, get_ca_cert_path_exacc

class ManagmentServer(BaseServer):

    def __init__(self, aConfig, *args):

        #Init the server
        BaseServer.__init__(self, aConfig, *args)

        #Init socket using new remoteec cert and keys
        self.mCreateSocket()

        #Init the Shared Memory
        self.__stopAsync = False
        self.mCreateExacloudUtil()
        self.mCreateDatabaseObject()
        self.mStartAsyncProcess()

    def mCreateSocket(self):
        if is_https_enabled():
            _rootca_certificate = None
            _client_certificate = None
            _client_privatekey = None
            # Refer https://github.com/benoitc/gunicorn/issues/1933 and https://docs.python.org/3/library/ssl.html#id9
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
                app_cfg = ebCertificateConfig('remoteec', \
                    get_tls_config_path())
                _rootca_certificate = app_cfg['client_certificate_file']
                _client_certificate = app_cfg['local_certificate_file_remoteec']
                _client_privatekey = app_cfg['local_certificate_key_file_remoteec']
                _protocol = app_cfg['protocol']

            if not _client_certificate and not _client_privatekey:
                return

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

    def mCreateExacloudUtil(self):
        self.mGetSharedData()['util'] = ebExacloudUtil(aGenerateDatabase=False, aUseOeda=False, \
                                                       aExatestAgent=False, aDeploy=True)
        self.mGetLog().mInfo("Exacloud Util Created")

    def mCreateDatabaseObject(self):
        _util = self.mGetSharedData()['util']
        _util.mPrepareEnviroment()
        self.mGetSharedData()['db'] = ebGetDefaultDB()
        self.mGetLog().mInfo("Database Exacloud Created")

    def mStartAsyncProcess(self):
        _pmanager = ProcessManager()
        self.mGetSharedData()['async'] = _pmanager
        self.mGetLog().mInfo("Process Manager Created")



class ManagmentServerAdm(BaseServerAdministrator):

    def __init__(self):
        BaseServerAdministrator.__init__(self, "managment", ManagmentServer)

    def mParseParams(self):

        parser = argparse.ArgumentParser(description='Server Commandline Arguments')
        parser.add_argument('--daemon', '-da', action="store_true", help='Start process as daemon')
        args = parser.parse_args()

        if args.daemon:
            self.mDaemonize()
            self.mRedirectDescriptors()

    def mDisconnect(self):
        self.mGetHttpServer().mGetSharedData()['async'].mKillAll()
        super(ManagmentServerAdm, self).mDisconnect()


if __name__ == "__main__":

    _server = ManagmentServerAdm()
    _server.mParseParams()
    _server.mConnect()
    _server.mDisconnect()

