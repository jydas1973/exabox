#!/bin/python
#
# $Header: tests_base_handler.py 07-apr-2026.07:24:38 aypaul   Exp $
#
# tests_base_handler.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_base_handler.py - Unit tests for BaseHandler module
#
#    DESCRIPTION
#      Exercise BaseHandler request validation, parameter parsing, and response flow.
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/07/26 - Add BaseServer handler tests
#    aypaul      04/07/26 - Creation
#
import copy
import io
import json
import unittest

from exabox.BaseServer.BaseHandler import BaseHandler


class DummyConfig(object):

    def __init__(self, prefix, endpoints=None):
        self._prefix = prefix
        self._endpoints = endpoints or {}

    def mGetPrefix(self):
        return self._prefix

    def mGetClientEndpoints(self):
        return copy.deepcopy(self._endpoints)

    def mGetStacktrace(self):
        self.stacktrace_called = True


class DummyLog(object):

    def __init__(self):
        self.messages = []

    def mInfo(self, message):
        self.messages.append(('info', message))

    def mCall(self, message):
        self.messages.append(('call', message))


class DummyServer(object):

    def __init__(self, config, log, shared=None):
        self._config = config
        self._log = log
        self._shared = shared or {}

    def mGetLog(self):
        return self._log

    def mGetConfig(self):
        return self._config

    def mGetSharedData(self):
        return self._shared


class DummyHeaders(dict):

    def get(self, key, default=None):
        return super().get(key, default)


class ebTestBaseHandler(unittest.TestCase):

    def mBuildHandler(self, config=None, callbacks=None, server=None):
        _handler = BaseHandler.__new__(BaseHandler)
        if config is not None:
            _handler._BaseHandler__config = config
        if callbacks is not None:
            _handler._BaseHandler__callbacks = callbacks
        if server is not None:
            _handler._BaseHandler__server = server
            _handler._BaseHandler__log = server.mGetLog()
        return _handler

    def test_001_valid_mandatory_params_success(self):

        _endpoints = {
            'status': {
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

        _config = DummyConfig('BaseServer', endpoints=_endpoints)
        _handler = self.mBuildHandler(config=_config, callbacks={'status': object})
        _handler.command = 'GET'

        _response = {'status': 200, 'error': '', 'text': {}}
        _is_valid = _handler.mValidMandatoryParams(
            'status',
            {'mandatory': 'value', 'regex_val': 'ok', 'state': 'ready'},
            None,
            _response
        )

        self.assertTrue(_is_valid)
        self.assertEqual(_response['status'], 200)
        self.assertEqual(_response['error'], '')

    def test_002_valid_mandatory_params_missing_value_sets_error(self):

        _endpoints = {
            'status': {
                'GET': {
                    'method': 'GET',
                    'params': {'mandatory': 'mandatory'}
                }
            }
        }

        _config = DummyConfig('BaseServer', endpoints=_endpoints)
        _handler = self.mBuildHandler(config=_config, callbacks={'status': object})
        _handler.command = 'GET'

        _response = {}
        _is_valid = _handler.mValidMandatoryParams('status', {}, None, _response)

        self.assertFalse(_is_valid)
        self.assertEqual(_response['status'], 500)
        self.assertIn('missing mandatory param', _response['error'])

    def test_003_get_body_parses_json_payload(self):

        _handler = self.mBuildHandler()
        _payload = json.dumps({'key': 'value'}).encode('utf-8')

        _handler.command = 'POST'
        _handler.headers = DummyHeaders({'content-length': str(len(_payload))})
        _handler.rfile = io.BytesIO(_payload)

        _body = _handler.mGetBody()
        self.assertEqual(_body, {'key': 'value'})

    def test_004_get_body_returns_none_for_invalid_json(self):

        _handler = self.mBuildHandler()
        _payload = b'not-json'

        _handler.command = 'PUT'
        _handler.headers = DummyHeaders({'content-length': str(len(_payload))})
        _handler.rfile = io.BytesIO(_payload)

        _body = _handler.mGetBody()
        self.assertIsNone(_body)

    def test_005_params_url_extracts_endpoint_and_query(self):

        _config = DummyConfig('BaseServer', endpoints={'status': {}})
        _log = DummyLog()
        _server = DummyServer(_config, _log, shared={'shared': True})
        _handler = self.mBuildHandler(config=_config, callbacks={'status': object}, server=_server)
        _handler.path = '/BaseServer/status?mandatory=ok&extra=x'

        _params = _handler.mParamsUrl()

        self.assertEqual(_params['endpointName'], 'status')
        self.assertIs(_params['endpoint'], object)
        self.assertEqual(_params['args']['mandatory'], 'ok')
        self.assertEqual(_params['args']['extra'], 'x')

    def test_006_params_url_returns_none_for_outside_prefix(self):

        _handler = self.mBuildHandler(config=DummyConfig('BaseServer'))
        _handler.path = '/Other/status'

        _params = _handler.mParamsUrl()
        self.assertIsNone(_params)

    def test_007_default_handler_success_path(self):

        _config = DummyConfig('BaseServer')
        _log = DummyLog()
        _server = DummyServer(_config, _log, shared={'shared': True})
        _handler = self.mBuildHandler(config=_config, server=_server)
        _handler.command = 'GET'
        _handler.path = '/BaseServer/status'

        _handler.wfile = io.BytesIO()
        _handler.send_response = lambda status: None
        _handler.send_header = lambda *args, **kwargs: None
        _handler.end_headers = lambda: None

        def mFakeDoHead(self_ref, response):
            _status = response.pop('status', 200)
            response['http_status'] = _status
            response['ctype'] = response.get('ctype', 'application/json')

        _handler.do_HEAD = mFakeDoHead.__get__(_handler, BaseHandler)

        class DummyEndpoint(object):
            def __init__(self, args, body, response, shared):
                self._response = response

            def mGet(self):
                self._response['text'] = {'result': 'ok'}

        _handler.mAuthenticate = lambda: True
        _handler.mGetBody = lambda: None
        _handler.mParamsUrl = lambda: {
            'endpoint': DummyEndpoint,
            'endpointName': 'status',
            'args': {'mandatory': 'ok'}
        }
        _handler.mValidMandatoryParams = lambda *args, **kwargs: True

        _handler.mDefaultHandler('mGet')

        _payload = json.loads(_handler.wfile.getvalue().decode('utf-8'))
        self.assertEqual(_payload['text'], {'result': 'ok'})
        self.assertEqual(_payload['http_status'], 200)
        self.assertEqual(_payload['ctype'], 'application/json')

    def test_008_default_handler_aborts_when_authentication_fails(self):

        _handler = self.mBuildHandler()
        _handler.wfile = io.BytesIO()
        _handler.mAuthenticate = lambda: False

        _handler.mDefaultHandler('mGet')
        self.assertEqual(_handler.wfile.getvalue(), b'')


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
