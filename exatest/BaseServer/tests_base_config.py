#!/bin/python
#
# $Header: tests_base_config.py 07-apr-2026.07:24:26 aypaul   Exp $
#
# tests_base_config.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_base_config.py - Unit tests for BaseConfig module
#
#    DESCRIPTION
#      Validate BaseConfig configuration discovery and authentication wiring.
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/07/26 - Add BaseServer tests
#    aypaul      04/07/26 - Creation
#
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from exabox.BaseServer.BaseConfig import BaseConfig


class ebTestBaseConfig(unittest.TestCase):

    def mBuildLayout(self):

        _tmp_dir = tempfile.TemporaryDirectory()
        _root_dir = Path(_tmp_dir.name)
        _server_dir = _root_dir / 'ecs' / 'exacloud' / 'exabox' / 'BaseServer'
        _server_config_dir = _server_dir / 'config'
        _exacloud_config_dir = _root_dir / 'ecs' / 'exacloud' / 'config'

        _server_config_dir.mkdir(parents=True)
        _exacloud_config_dir.mkdir(parents=True)

        (_server_config_dir / 'basic.conf').write_text(
            json.dumps({'auth': {'user': 'svc'}, 'listen': '127.0.0.1', 'port': 5555}),
            encoding='utf-8'
        )
        (_server_config_dir / 'endpoints.conf').write_text(
            json.dumps(
                {
                    'status': {
                        'help': 'show status',
                        'class': 'DummyEndpoint',
                        'package': 'exatest_dummy_module',
                        'GET': {
                            'method': 'GET',
                            'params': {
                                'mandatory': 'mandatory',
                                'regex_val': 'regex:^ok$',
                                'state': 'ready|busy',
                                'optional': 'optional'
                            }
                        }
                    }
                }
            ),
            encoding='utf-8'
        )
        (_exacloud_config_dir / 'exabox.conf').write_text(
            json.dumps({'wallet': 'dummy'}),
            encoding='utf-8'
        )

        return _tmp_dir, _server_dir

    def test_001_refresh_config_loads_files_and_authentication(self):

        _tmp_dir, _server_dir = self.mBuildLayout()
        _dummy_module = types.ModuleType('exatest_dummy_module')

        class DummyEndpoint(object):
            def __init__(self, *args, **kwargs):
                pass

        _dummy_module.DummyEndpoint = DummyEndpoint
        sys.modules['exatest_dummy_module'] = _dummy_module

        _original_argv = sys.argv[:]
        sys.argv = [str(_server_dir / 'launcher.py')]

        try:
            with patch(
                'exabox.BaseServer.BaseConfig.ebBasicAuthStorage', return_value='basic'
            ) as _basic_auth, patch(
                'exabox.BaseServer.BaseConfig.ebGetHTTPAuthStorage', return_value='resolved'
            ) as _auth_storage:
                _config = BaseConfig('BaseServer')

            self.assertTrue(_config.mGetPath().endswith('BaseServer/'))
            self.assertTrue(_config.mGetExacloudPath().endswith('exacloud'))
            self.assertEqual(_config.mGetConfigValue('listen'), '127.0.0.1')
            self.assertEqual(_config.mGetConfigValue('port'), 5555)

            _client_endpoints = _config.mGetClientEndpoints()
            self.assertIn('status', _client_endpoints)
            self.assertNotIn('class', _client_endpoints['status'])
            self.assertEqual(_client_endpoints['status']['GET']['method'], 'GET')

            _endpoint_classes = _config.mGetEndpointClasses()
            self.assertIs(_endpoint_classes['status'], DummyEndpoint)

            _basic_auth.assert_called_once_with({'user': 'svc'})
            _auth_storage.assert_called_once_with('remoteec_', 'basic', ANY)
        finally:
            sys.argv = _original_argv
            sys.modules.pop('exatest_dummy_module', None)
            _tmp_dir.cleanup()

    def test_002_refresh_config_missing_prefix_raises(self):

        _original_argv = sys.argv[:]
        sys.argv = ['/tmp/run_base_server.py']

        try:
            with self.assertRaisesRegex(Exception, 'Prefix: MissingPrefix is absent'):
                BaseConfig('MissingPrefix')
        finally:
            sys.argv = _original_argv

    def test_003_refresh_config_missing_exabox_folder_raises(self):

        _original_argv = sys.argv[:]
        sys.argv = ['/tmp/BaseServer/main.py']

        try:
            with self.assertRaisesRegex(Exception, 'exabox folder not present'):
                BaseConfig('BaseServer')
        finally:
            sys.argv = _original_argv


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
