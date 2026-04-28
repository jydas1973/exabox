#!/bin/python
#
# $Header: tests_base_server.py 07-apr-2026.07:24:49 aypaul   Exp $
#
# tests_base_server.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_base_server.py - Unit tests for BaseServer components
#
#    DESCRIPTION
#      Validate BaseServer and BaseServerAdministrator orchestration behaviour.
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/07/26 - Add BaseServer server tests
#    aypaul      04/07/26 - Creation
#
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from exabox.BaseServer.BaseServer import BaseServer, BaseServerAdministrator


class DummyServer(object):
    def __init__(self, config, address, handler):
        self._config = config
        self._address = address
        self._handler = handler
        self.shutdown_called = False
        self.server_close_called = False
        self.log = MagicMock()
        self.log.mInit = MagicMock()
        self.log.mInfo = MagicMock()
        self.log.mClose = MagicMock()
        self.log.mError = MagicMock()

    def mGetLog(self):
        return self.log

    def mGetConfig(self):
        return self._config

    def mGetSharedData(self):
        return {}

    def serve_forever(self):
        raise KeyboardInterrupt()

    def shutdown(self):
        self.shutdown_called = True

    def server_close(self):
        self.server_close_called = True


class FailingServer(DummyServer):
    def serve_forever(self):
        raise RuntimeError("boom")


class ebTestBaseServer(unittest.TestCase):
    def test_001_shared_data_contains_log_and_config(self):
        config = MagicMock()

        with patch(
            "exabox.BaseServer.BaseServer.ExaHTTPSServer.__init__", return_value=None
        ):
            server = BaseServer(config, ("127.0.0.1", 8000), object)

        shared = server.mGetSharedData()
        self.assertIs(shared["config"], config)
        self.assertIs(shared["log"], server.mGetLog())

    def test_002_administrator_disconnects_on_keyboard_interrupt(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "exabox.BaseServer.BaseServer.BaseConfig"
        ) as config_cls:
            config_instance = MagicMock()
            config_instance.mGetConfigValue.side_effect = lambda key: {
                "listen": "127.0.0.1",
                "port": 9000,
            }[key]
            config_instance.mGetPath.return_value = tmp_dir
            config_cls.return_value = config_instance

            admin = BaseServerAdministrator(
                "BaseServer", aServerClass=DummyServer, aHandlerClass=object
            )
            admin.mConnect()

            server = admin.mGetHttpServer()
            self.assertTrue(server.shutdown_called)
            self.assertTrue(server.server_close_called)
            info_messages = [
                call.args[0] for call in server.mGetLog().mInfo.call_args_list
            ]
            self.assertTrue(
                any("Server Started" in message for message in info_messages)
            )
            self.assertTrue(
                any("Server Stopped" in message for message in info_messages)
            )

    def test_003_administrator_logs_error_for_runtime_exception(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "exabox.BaseServer.BaseServer.BaseConfig"
        ) as config_cls:
            config_instance = MagicMock()
            config_instance.mGetConfigValue.side_effect = lambda key: {
                "listen": "127.0.0.1",
                "port": 9001,
            }[key]
            config_instance.mGetPath.return_value = tmp_dir
            config_cls.return_value = config_instance

            admin = BaseServerAdministrator(
                "BaseServer", aServerClass=FailingServer, aHandlerClass=object
            )
            admin.mConnect()

            server = admin.mGetHttpServer()
            server.mGetLog().mError.assert_called()
            self.assertFalse(server.shutdown_called)
            self.assertFalse(server.server_close_called)


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
