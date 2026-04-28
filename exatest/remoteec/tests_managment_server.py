#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_managment_server.py /main/1 04/16/26 00:48:35 shapatna Exp $
#
# tests_managment_server.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_managment_server.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    04/16/26 - Bug 39111671 Enhance UT Coverage for exabox/managment directory
#    shapatna    04/16/26 - Creation

import ssl
import runpy
import unittest

from unittest.mock import Mock, patch

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.BaseServer.BaseServer import BaseServer, BaseServerAdministrator
from exabox.managment.src.ManagmentServer import ManagmentServer, ManagmentServerAdm


class ebTestManagmentServer(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)

    def _mMakeServer(self):
        _shared = {}
        _log = Mock()
        _server = ManagmentServer.__new__(ManagmentServer)
        _server.socket = "plain-socket"
        _server.mGetSharedData = Mock(return_value=_shared)
        _server.mGetLog = Mock(return_value=_log)
        return _server, _shared, _log

    def _mMakeContext(self):
        _context = Mock()
        _context.options = 0
        _context.wrap_socket.return_value = "wrapped-socket"
        return _context

    # Auto-generated test for __init__
    def test_000_init_calls_bootstrap_methods(self):
        with patch.object(BaseServer, "__init__", return_value=None) as _base_init, \
             patch.object(ManagmentServer, "mCreateSocket") as _create_socket, \
             patch.object(ManagmentServer, "mCreateExacloudUtil") as _create_util, \
             patch.object(ManagmentServer, "mCreateDatabaseObject") as _create_db, \
             patch.object(ManagmentServer, "mStartAsyncProcess") as _start_async:
            _server = ManagmentServer("cfg", "addr", "handler")

        _base_init.assert_called_once_with(_server, "cfg", "addr", "handler")
        _create_socket.assert_called_once_with()
        _create_util.assert_called_once_with()
        _create_db.assert_called_once_with()
        _start_async.assert_called_once_with()
        self.assertFalse(_server._ManagmentServer__stopAsync)

    # Auto-generated test for mCreateSocket
    def test_001_mcreatesocket_skips_ssl_when_https_is_disabled(self):
        _server, _, _ = self._mMakeServer()
        with patch("exabox.managment.src.ManagmentServer.is_https_enabled", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.ssl.SSLContext") as _ssl_context:
            _server.mCreateSocket()

        _ssl_context.assert_not_called()
        self.assertEqual(_server.socket, "plain-socket")

    # Auto-generated test for mCreateSocket
    def test_002_mcreatesocket_returns_when_cert_and_key_are_missing(self):
        _server, _, _ = self._mMakeServer()
        with patch("exabox.managment.src.ManagmentServer.is_https_enabled", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.use_oci_certificates", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.ebCertificateConfig", return_value={
                 "client_certificate_file": "/tmp/rootca.pem",
                 "local_certificate_file_remoteec": None,
                 "local_certificate_key_file_remoteec": None,
                 "protocol": "PROTOCOL_TLS"
             }), \
             patch("exabox.managment.src.ManagmentServer.get_tls_config_path", return_value="/tmp/tls.cfg"), \
             patch("exabox.managment.src.ManagmentServer.ssl.SSLContext") as _ssl_context:
            _server.mCreateSocket()

        _ssl_context.assert_not_called()
        self.assertEqual(_server.socket, "plain-socket")

    # Auto-generated test for mCreateSocket
    def test_003_mcreatesocket_wraps_socket_for_plain_tls(self):
        _server, _, _ = self._mMakeServer()
        _context = self._mMakeContext()
        with patch("exabox.managment.src.ManagmentServer.is_https_enabled", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.use_oci_certificates", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.ebCertificateConfig", return_value={
                 "client_certificate_file": "/tmp/rootca.pem",
                 "local_certificate_file_remoteec": "/tmp/server.pem",
                 "local_certificate_key_file_remoteec": "/tmp/server.key",
                 "protocol": "PROTOCOL_TLS"
             }), \
             patch("exabox.managment.src.ManagmentServer.get_tls_config_path", return_value="/tmp/tls.cfg"), \
             patch("exabox.managment.src.ManagmentServer.is_mtls_enabled_exacc", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.is_exacs", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.ssl.SSLContext", return_value=_context):
            _server.mCreateSocket()

        _context.load_cert_chain.assert_called_once_with("/tmp/server.pem", "/tmp/server.key")
        _context.load_verify_locations.assert_not_called()
        _context.wrap_socket.assert_called_once_with("plain-socket", server_side=True)
        self.assertEqual(_server.socket, "wrapped-socket")

    # Auto-generated test for mCreateSocket
    def test_004_mcreatesocket_uses_exacc_ca_for_mtls(self):
        _server, _, _ = self._mMakeServer()
        _context = self._mMakeContext()
        _config = {
            "client_certificate_file": "/tmp/rootca.pem",
            "local_certificate_file_remoteec": "/tmp/server.pem",
            "local_certificate_key_file_remoteec": "/tmp/server.key",
            "protocol": "PROTOCOL_TLS"
        }
        with patch("exabox.managment.src.ManagmentServer.is_https_enabled", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.use_oci_certificates", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.ebCertificateConfig", return_value=_config), \
             patch("exabox.managment.src.ManagmentServer.get_tls_config_path", return_value="/tmp/tls.cfg"), \
             patch("exabox.managment.src.ManagmentServer.is_mtls_enabled_exacc", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.is_exacs", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.get_ca_cert_path_exacc", return_value="/tmp/exacc-ca.pem") as _get_ca, \
             patch("exabox.managment.src.ManagmentServer.ssl.SSLContext", return_value=_context):
            _server.mCreateSocket()

        _get_ca.assert_called_once_with(app_cfg=_config)
        _context.load_verify_locations.assert_called_once_with("/tmp/exacc-ca.pem")
        _context.load_cert_chain.assert_called_once_with("/tmp/server.pem", "/tmp/server.key")
        self.assertEqual(_context.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(_server.socket, "wrapped-socket")

    # Auto-generated test for mCreateSocket
    def test_005_mcreatesocket_uses_oci_certificates_for_exacs(self):
        _server, _, _ = self._mMakeServer()
        _context = self._mMakeContext()
        with patch("exabox.managment.src.ManagmentServer.is_https_enabled", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.use_oci_certificates", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.get_oci_certificates", return_value=(
                 "/tmp/oci-rootca.pem", "/tmp/oci-server.pem", "/tmp/oci-server.key", "PROTOCOL_TLS"
             )), \
             patch("exabox.managment.src.ManagmentServer.is_mtls_enabled_exacc", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.is_exacs", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.get_ca_cert_path_exacc") as _get_ca, \
             patch("exabox.managment.src.ManagmentServer.ssl.SSLContext", return_value=_context):
            _server.mCreateSocket()

        _get_ca.assert_not_called()
        _context.load_verify_locations.assert_called_once_with("/tmp/oci-rootca.pem")
        _context.load_cert_chain.assert_called_once_with("/tmp/oci-server.pem", "/tmp/oci-server.key")
        self.assertEqual(_context.verify_mode, ssl.CERT_NONE)
        self.assertEqual(_server.socket, "wrapped-socket")

    # Auto-generated test for mCreateExacloudUtil
    def test_006_mcreateexacloudutil_stores_utility_and_logs(self):
        _server, _shared, _log = self._mMakeServer()
        with patch("exabox.managment.src.ManagmentServer.ebExacloudUtil", return_value="util-object") as _util_cls:
            _server.mCreateExacloudUtil()

        _util_cls.assert_called_once_with(aGenerateDatabase=False, aUseOeda=False,
                                          aExatestAgent=False, aDeploy=True)
        self.assertEqual(_shared["util"], "util-object")
        _log.mInfo.assert_called_once_with("Exacloud Util Created")

    # Auto-generated test for mCreateDatabaseObject
    def test_007_mcreatedatabaseobject_prepares_environment_and_stores_db(self):
        _server, _shared, _log = self._mMakeServer()
        _util = Mock()
        _shared["util"] = _util
        with patch("exabox.managment.src.ManagmentServer.ebGetDefaultDB", return_value="db-object") as _get_db:
            _server.mCreateDatabaseObject()

        _util.mPrepareEnviroment.assert_called_once_with()
        _get_db.assert_called_once_with()
        self.assertEqual(_shared["db"], "db-object")
        _log.mInfo.assert_called_once_with("Database Exacloud Created")

    # Auto-generated test for mStartAsyncProcess
    def test_008_mstartasyncprocess_stores_manager_and_logs(self):
        _server, _shared, _log = self._mMakeServer()
        with patch("exabox.managment.src.ManagmentServer.ProcessManager", return_value="pm-object") as _pm_cls:
            _server.mStartAsyncProcess()

        _pm_cls.assert_called_once_with()
        self.assertEqual(_shared["async"], "pm-object")
        _log.mInfo.assert_called_once_with("Process Manager Created")

    # Auto-generated test for mCreateSocket
    def test_014_mcreatesocket_uses_oci_certificates_for_plain_tls(self):
        _server, _, _ = self._mMakeServer()
        _context = self._mMakeContext()
        with patch("exabox.managment.src.ManagmentServer.is_https_enabled", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.use_oci_certificates", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.get_oci_certificates", return_value=(
                 "/tmp/oci-rootca.pem", "/tmp/oci-server.pem", "/tmp/oci-server.key", "PROTOCOL_TLS"
             )), \
             patch("exabox.managment.src.ManagmentServer.is_mtls_enabled_exacc", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.is_exacs", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.get_ca_cert_path_exacc") as _get_ca, \
             patch("exabox.managment.src.ManagmentServer.ssl.SSLContext", return_value=_context):
            _server.mCreateSocket()

        _get_ca.assert_not_called()
        _context.load_verify_locations.assert_not_called()
        _context.load_cert_chain.assert_called_once_with("/tmp/oci-server.pem", "/tmp/oci-server.key")
        _context.wrap_socket.assert_called_once_with("plain-socket", server_side=True)
        self.assertEqual(_server.socket, "wrapped-socket")

    # Auto-generated test for mCreateSocket
    def test_015_mcreatesocket_uses_exacc_ca_with_oci_certificates_for_mtls(self):
        _server, _, _ = self._mMakeServer()
        _context = self._mMakeContext()
        with patch("exabox.managment.src.ManagmentServer.is_https_enabled", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.use_oci_certificates", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.get_oci_certificates", return_value=(
                 "/tmp/oci-rootca.pem", "/tmp/oci-server.pem", "/tmp/oci-server.key", "PROTOCOL_TLS"
             )), \
             patch("exabox.managment.src.ManagmentServer.is_mtls_enabled_exacc", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.is_exacs", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.get_ca_cert_path_exacc",
                   return_value="/tmp/exacc-ca.pem") as _get_ca, \
             patch("exabox.managment.src.ManagmentServer.ssl.SSLContext", return_value=_context):
            _server.mCreateSocket()

        _get_ca.assert_called_once_with(app_cfg=None)
        _context.load_verify_locations.assert_called_once_with("/tmp/exacc-ca.pem")
        _context.load_cert_chain.assert_called_once_with("/tmp/oci-server.pem", "/tmp/oci-server.key")
        self.assertEqual(_context.verify_mode, ssl.CERT_NONE)
        self.assertEqual(_server.socket, "wrapped-socket")

    # Auto-generated test for mCreateSocket
    def test_016_mcreatesocket_uses_configured_ca_for_exacs_without_oci_certs(self):
        _server, _, _ = self._mMakeServer()
        _context = self._mMakeContext()
        _config = {
            "client_certificate_file": "/tmp/rootca.pem",
            "local_certificate_file_remoteec": "/tmp/server.pem",
            "local_certificate_key_file_remoteec": "/tmp/server.key",
            "protocol": "PROTOCOL_TLS"
        }

        with patch("exabox.managment.src.ManagmentServer.is_https_enabled", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.use_oci_certificates", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.ebCertificateConfig", return_value=_config), \
             patch("exabox.managment.src.ManagmentServer.get_tls_config_path", return_value="/tmp/tls.cfg"), \
             patch("exabox.managment.src.ManagmentServer.is_mtls_enabled_exacc", return_value=False), \
             patch("exabox.managment.src.ManagmentServer.is_exacs", return_value=True), \
             patch("exabox.managment.src.ManagmentServer.get_ca_cert_path_exacc") as _get_ca, \
             patch("exabox.managment.src.ManagmentServer.ssl.SSLContext", return_value=_context):
            _server.mCreateSocket()

        _get_ca.assert_not_called()
        _context.load_verify_locations.assert_called_once_with("/tmp/rootca.pem")
        _context.load_cert_chain.assert_called_once_with("/tmp/server.pem", "/tmp/server.key")
        self.assertEqual(_context.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(_server.socket, "wrapped-socket")


class ebTestManagmentServerAdm(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)

    # Auto-generated test for __init__
    def test_009_init_registers_server_class(self):
        with patch.object(BaseServerAdministrator, "__init__", return_value=None) as _base_init:
            ManagmentServerAdm()

        _base_init.assert_called_once_with(unittest.mock.ANY, "managment", ManagmentServer)

    # Auto-generated test for mParseParams
    def test_010_mparseparams_skips_daemonization_when_flag_is_absent(self):
        _admin = ManagmentServerAdm.__new__(ManagmentServerAdm)
        _parser = Mock()
        _parser.parse_args.return_value = Mock(daemon=False)

        with patch("exabox.managment.src.ManagmentServer.argparse.ArgumentParser", return_value=_parser), \
             patch.object(_admin, "mDaemonize") as _daemonize, \
             patch.object(_admin, "mRedirectDescriptors") as _redirect:
            _admin.mParseParams()

        _parser.add_argument.assert_called_once_with('--daemon', '-da', action="store_true",
                                                     help='Start process as daemon')
        _daemonize.assert_not_called()
        _redirect.assert_not_called()

    # Auto-generated test for mParseParams
    def test_011_mparseparams_daemonizes_when_flag_is_present(self):
        _admin = ManagmentServerAdm.__new__(ManagmentServerAdm)
        _parser = Mock()
        _parser.parse_args.return_value = Mock(daemon=True)

        with patch("exabox.managment.src.ManagmentServer.argparse.ArgumentParser", return_value=_parser), \
             patch.object(_admin, "mDaemonize") as _daemonize, \
             patch.object(_admin, "mRedirectDescriptors") as _redirect:
            _admin.mParseParams()

        _daemonize.assert_called_once_with()
        _redirect.assert_called_once_with()

    # Auto-generated test for mDisconnect
    def test_012_mdisconnect_kills_async_workers_before_super_disconnect(self):
        _admin = ManagmentServerAdm.__new__(ManagmentServerAdm)
        _async = Mock()
        _httpd = Mock()
        _httpd.mGetSharedData.return_value = {"async": _async}

        with patch.object(_admin, "mGetHttpServer", return_value=_httpd), \
             patch.object(BaseServerAdministrator, "mDisconnect") as _base_disconnect:
            _admin.mDisconnect()

        _async.mKillAll.assert_called_once_with()
        _base_disconnect.assert_called_once_with()

    # Auto-generated test for __main__
    def test_013_module_main_executes_admin_lifecycle(self):
        _httpd = Mock()
        _async = Mock()
        _httpd.mGetSharedData.return_value = {"async": _async}
        _parser = Mock()
        _parser.parse_args.return_value = Mock(daemon=False)

        with patch.object(BaseServerAdministrator, "__init__", return_value=None) as _base_init, \
             patch.object(BaseServerAdministrator, "mGetHttpServer", return_value=_httpd), \
             patch.object(BaseServerAdministrator, "mConnect") as _connect, \
             patch.object(BaseServerAdministrator, "mDisconnect") as _base_disconnect, \
             patch.object(BaseServerAdministrator, "mDaemonize") as _daemonize, \
             patch.object(BaseServerAdministrator, "mRedirectDescriptors") as _redirect, \
             patch("argparse.ArgumentParser", return_value=_parser):
            runpy.run_module("exabox.managment.src.ManagmentServer", run_name="__main__")

        self.assertEqual(_base_init.call_args[0][1], "managment")
        self.assertEqual(_base_init.call_args[0][2].__name__, "ManagmentServer")
        _connect.assert_called_once_with()
        _async.mKillAll.assert_called_once_with()
        _base_disconnect.assert_called_once_with()
        _daemonize.assert_not_called()
        _redirect.assert_not_called()


if __name__ == '__main__':
    unittest.main(warnings='ignore')
