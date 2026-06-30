#!/bin/python
#
# $Header: tests_basehandler.py $
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
# tests_basehandler.py
#
import copy
import errno
import io
import json
import unittest

from unittest.mock import MagicMock, patch

from exabox.BaseServer.BaseHandler import BaseHandler
from exabox.agent.HTTPAuthentication import ebHTTPAuthResult


class RecordingEndpoint(object):

    def __init__(self, args, body, response, shared):
        self.args = args
        self.body = body
        self.response = response
        self.shared = shared

    def mGet(self):
        self.response['text'] = {'callback': 'mGet', 'shared': self.shared}

    def mPost(self):
        self.response['text'] = {'callback': 'mPost'}

    def mPut(self):
        self.response['text'] = {'callback': 'mPut'}

    def mDelete(self):
        self.response['text'] = {'callback': 'mDelete'}

    def mPatch(self):
        self.response['text'] = {'callback': 'mPatch'}


class TestBaseHandler(unittest.TestCase):

    def _make_handler(self):
        handler = BaseHandler.__new__(BaseHandler)
        server = MagicMock()
        log = MagicMock()
        config = MagicMock()
        auth = MagicMock()

        config.mGetPrefix.return_value = 'api'
        config.mGetEndpointClasses.return_value = {'items': RecordingEndpoint}
        config.mGetConfigValue.return_value = 'auth-config'
        config.mGetClientEndpoints.return_value = {}
        server.mGetLog.return_value = log
        server.mGetConfig.return_value = config
        server.mGetSharedData.return_value = {'shared': True}

        setattr(handler, '_BaseHandler__server', server)
        setattr(handler, '_BaseHandler__log', log)
        setattr(handler, '_BaseHandler__config', config)
        setattr(handler, '_BaseHandler__callbacks', {'items': RecordingEndpoint})
        setattr(handler, '_BaseHandler__httpAuth', auth)

        handler.client_address = ('127.0.0.1', 1234)
        handler.command = 'GET'
        handler.path = '/api/items'
        handler.headers = MagicMock()
        handler.rfile = io.BytesIO()
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        return handler, server, log, config, auth

    def _set_client_endpoints(self, handler, endpoint_name, endpoint_config):
        config = getattr(handler, '_BaseHandler__config')
        config.mGetClientEndpoints.return_value = {
            endpoint_name: copy.deepcopy(endpoint_config)
        }

    # Auto-generated test for __init__
    @patch('exabox.BaseServer.BaseHandler.ExaHTTPRequestHandler.__init__', return_value=None)
    @patch('exabox.BaseServer.BaseHandler.ebHTTPAuthentication')
    def test_init_sets_private_members_and_calls_super(self, mock_auth_ctor, mock_super_init):
        server = MagicMock()
        log = MagicMock()
        config = MagicMock()
        callbacks = {'items': RecordingEndpoint}

        server.mGetLog.return_value = log
        server.mGetConfig.return_value = config
        config.mGetEndpointClasses.return_value = callbacks
        config.mGetConfigValue.return_value = 'auth-config'

        auth_instance = MagicMock()
        mock_auth_ctor.return_value = auth_instance

        handler = BaseHandler('request', ('127.0.0.1', 1234), server)

        self.assertIs(getattr(handler, '_BaseHandler__server'), server)
        self.assertIs(getattr(handler, '_BaseHandler__log'), log)
        self.assertIs(getattr(handler, '_BaseHandler__config'), config)
        self.assertEqual(getattr(handler, '_BaseHandler__callbacks'), callbacks)
        self.assertIs(getattr(handler, '_BaseHandler__httpAuth'), auth_instance)
        mock_super_init.assert_called_once()

    # Auto-generated test for __init__
    @patch('exabox.BaseServer.BaseHandler.ebHTTPAuthentication')
    @patch('exabox.BaseServer.BaseHandler.ExaHTTPRequestHandler.__init__', side_effect=IOError(errno.EPIPE, 'broken pipe'))
    def test_init_ignores_broken_pipe(self, mock_super_init, mock_auth_ctor):
        server = MagicMock()
        config = MagicMock()
        server.mGetLog.return_value = MagicMock()
        server.mGetConfig.return_value = config
        config.mGetEndpointClasses.return_value = {}
        config.mGetConfigValue.return_value = 'auth-config'
        mock_auth_ctor.return_value = MagicMock()

        BaseHandler('request', ('127.0.0.1', 1234), server)

        config.mGetStacktrace.assert_not_called()
        mock_super_init.assert_called_once()

    # Auto-generated test for __init__
    @patch('exabox.BaseServer.BaseHandler.ebHTTPAuthentication')
    @patch('exabox.BaseServer.BaseHandler.ExaHTTPRequestHandler.__init__', side_effect=IOError(errno.EACCES, 'io error'))
    def test_init_collects_stacktrace_for_non_epipe_ioerror(self, mock_super_init, mock_auth_ctor):
        server = MagicMock()
        config = MagicMock()
        server.mGetLog.return_value = MagicMock()
        server.mGetConfig.return_value = config
        config.mGetEndpointClasses.return_value = {}
        config.mGetConfigValue.return_value = 'auth-config'
        mock_auth_ctor.return_value = MagicMock()

        BaseHandler('request', ('127.0.0.1', 1234), server)

        config.mGetStacktrace.assert_called_once()
        mock_super_init.assert_called_once()

    # Auto-generated test for __init__
    @patch('exabox.BaseServer.BaseHandler.ebHTTPAuthentication')
    @patch('exabox.BaseServer.BaseHandler.ExaHTTPRequestHandler.__init__', side_effect=RuntimeError('boom'))
    def test_init_collects_stacktrace_for_generic_exception(self, mock_super_init, mock_auth_ctor):
        server = MagicMock()
        config = MagicMock()
        server.mGetLog.return_value = MagicMock()
        server.mGetConfig.return_value = config
        config.mGetEndpointClasses.return_value = {}
        config.mGetConfigValue.return_value = 'auth-config'
        mock_auth_ctor.return_value = MagicMock()

        BaseHandler('request', ('127.0.0.1', 1234), server)

        config.mGetStacktrace.assert_called_once()
        mock_super_init.assert_called_once()

    # Auto-generated test for log_message
    def test_log_message_formats_remote_address(self):
        handler, _, log, _, _ = self._make_handler()

        handler.log_message('status=%s', 'ok')

        log.mCall.assert_called_once_with('127.0.0.1 - [status=ok]')

    # Auto-generated test for mValidMandatoryParams
    def test_mValidMandatoryParams_returns_501_when_params_flag_is_false(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'GET'
        self._set_client_endpoints(
            handler,
            'items',
            {'get': {'method': 'GET', 'params': False}}
        )
        response = {}

        result = handler.mValidMandatoryParams('items', None, None, response)

        self.assertFalse(result)
        self.assertEqual(response['status'], 501)
        self.assertIn('does not support GET', response['text'])

    # Auto-generated test for mValidMandatoryParams
    def test_mValidMandatoryParams_rejects_missing_body_for_post(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'POST'
        self._set_client_endpoints(
            handler,
            'items',
            {'post': {'method': 'POST', 'params': {'name': 'mandatory'}}}
        )
        response = {}

        result = handler.mValidMandatoryParams('items', None, None, response)

        self.assertFalse(result)
        self.assertEqual(response['status'], 500)
        self.assertEqual(response['error'], 'Error, no body found')

    # Auto-generated test for mValidMandatoryParams
    def test_mValidMandatoryParams_prunes_body_and_accepts_supported_rules(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'POST'
        self._set_client_endpoints(
            handler,
            'items',
            {
                'alias': {'alias': '/legacy'},
                'post': {
                    'method': 'POST',
                    'params': {
                        'name': 'mandatory',
                        'encoded': 'base64_file',
                        'mode': 'A|B',
                        'token': 'regex:^tok-[0-9]+$',
                        'optional': 'optional',
                        'hidden': 'hidden'
                    }
                }
            }
        )
        response = {}
        body = {
            'name': 'primary',
            'encoded': 'ZGF0YQ==',
            'mode': 'A',
            'token': 'tok-123',
            'optional': '',
            'unknown': 'drop-me'
        }

        result = handler.mValidMandatoryParams('items', None, body, response)

        self.assertTrue(result)
        self.assertEqual(
            body,
            {
                'name': 'primary',
                'encoded': 'ZGF0YQ==',
                'mode': 'A',
                'token': 'tok-123'
            }
        )

    # Auto-generated test for mValidMandatoryParams
    def test_mValidMandatoryParams_rejects_missing_args_when_none(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'GET'
        self._set_client_endpoints(
            handler,
            'items',
            {'get': {'method': 'GET', 'params': {'name': 'mandatory'}}}
        )
        response = {}

        result = handler.mValidMandatoryParams('items', None, None, response)

        self.assertFalse(result)
        self.assertIn('since not params', response['error'])

    # Auto-generated test for mValidMandatoryParams
    def test_mValidMandatoryParams_rejects_missing_required_key(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'GET'
        self._set_client_endpoints(
            handler,
            'items',
            {'get': {'method': 'GET', 'params': {'name': 'mandatory'}}}
        )
        response = {}

        result = handler.mValidMandatoryParams('items', {'other': 'value'}, None, response)

        self.assertFalse(result)
        self.assertIn("missing mandatory param 'name'", response['error'])

    # Auto-generated test for mValidMandatoryParams
    def test_mValidMandatoryParams_rejects_regex_mismatch(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'GET'
        self._set_client_endpoints(
            handler,
            'items',
            {'get': {'method': 'GET', 'params': {'token': 'regex:^tok-[0-9]+$'}}}
        )
        response = {}

        result = handler.mValidMandatoryParams('items', {'token': 'bad'}, None, response)

        self.assertFalse(result)
        self.assertIn("not match regex", response['error'])

    # Auto-generated test for mValidMandatoryParams
    def test_mValidMandatoryParams_rejects_value_outside_allowed_set(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'GET'
        self._set_client_endpoints(
            handler,
            'items',
            {'get': {'method': 'GET', 'params': {'mode': 'A|B'}}}
        )
        response = {}

        result = handler.mValidMandatoryParams('items', {'mode': 'C'}, None, response)

        self.assertFalse(result)
        self.assertIn("only accepts", response['error'])

    # Auto-generated test for mValidMandatoryParams
    def test_mValidMandatoryParams_prunes_query_args_for_get(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'GET'
        self._set_client_endpoints(
            handler,
            'items',
            {'get': {'method': 'GET', 'params': {'name': 'mandatory', 'hidden': 'hidden'}}}
        )
        response = {}
        url_args = {'name': 'value', 'blank': '   ', 'hidden': '   '}

        result = handler.mValidMandatoryParams('items', url_args, None, response)

        self.assertTrue(result)
        self.assertEqual(url_args, {'name': 'value'})

    # Auto-generated test for mGetBody
    def test_mGetBody_returns_none_for_get(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'GET'

        self.assertIsNone(handler.mGetBody())

    # Auto-generated test for mGetBody
    def test_mGetBody_parses_json_payload_for_non_get(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'POST'
        handler.headers.get.return_value = '14'
        handler.rfile = io.BytesIO(b'{"name": "x"}')

        body = handler.mGetBody()

        self.assertEqual(body, {'name': 'x'})

    # Auto-generated test for mGetBody
    def test_mGetBody_returns_none_for_invalid_json(self):
        handler, _, _, _, _ = self._make_handler()
        handler.command = 'POST'
        handler.headers.get.return_value = '8'
        handler.rfile = io.BytesIO(b'not-json')

        self.assertIsNone(handler.mGetBody())

    # Auto-generated test for do_AUTHHEAD
    def test_do_AUTHHEAD_sends_authentication_headers(self):
        handler, _, _, config, _ = self._make_handler()
        config.mGetPrefix.return_value = 'service-prefix'

        handler.do_AUTHHEAD()

        handler.send_response.assert_called_once_with(401)
        handler.send_header.assert_any_call('WWW-Authenticate', 'Basic realm="service-prefix"')
        handler.send_header.assert_any_call('Content-type', 'text/html')
        handler.end_headers.assert_called_once_with()

    # Auto-generated test for do_HEAD
    def test_do_HEAD_uses_explicit_status_and_content_type(self):
        handler, _, _, _, _ = self._make_handler()
        response = {'status': 202, 'ctype': 'text/plain'}

        handler.do_HEAD(response)

        self.assertEqual(response['http_status'], 202)
        self.assertNotIn('status', response)
        handler.send_response.assert_called_once_with(202)
        handler.send_header.assert_called_once_with('Content-type', 'text/plain')
        handler.end_headers.assert_called_once_with()

    # Auto-generated test for do_HEAD
    def test_do_HEAD_defaults_status_and_content_type(self):
        handler, _, _, _, _ = self._make_handler()
        response = {}

        handler.do_HEAD(response)

        self.assertEqual(response, {'http_status': 200, 'ctype': 'application/json'})
        handler.send_response.assert_called_once_with(200)
        handler.send_header.assert_called_once_with('Content-type', 'application/json')
        handler.end_headers.assert_called_once_with()

    # Auto-generated test for do_GET
    # Auto-generated test for do_POST
    # Auto-generated test for do_PUT
    # Auto-generated test for do_DELETE
    # Auto-generated test for do_PATCH
    def test_http_verb_methods_delegate_to_default_handler(self):
        handler, _, _, _, _ = self._make_handler()
        handler.mDefaultHandler = MagicMock()

        handler.do_GET()
        handler.mDefaultHandler.assert_called_once_with('mGet')

        handler.mDefaultHandler.reset_mock()
        handler.do_POST()
        handler.mDefaultHandler.assert_called_once_with('mPost')

        handler.mDefaultHandler.reset_mock()
        handler.do_PUT()
        handler.mDefaultHandler.assert_called_once_with('mPut')

        handler.mDefaultHandler.reset_mock()
        handler.do_DELETE()
        handler.mDefaultHandler.assert_called_once_with('mDelete')

        handler.mDefaultHandler.reset_mock()
        handler.do_PATCH()
        handler.mDefaultHandler.assert_called_once_with('mPatch')

    # Auto-generated test for mParamsUrl
    def test_mParamsUrl_returns_none_for_invalid_prefix(self):
        handler, _, _, _, _ = self._make_handler()
        handler.path = '/wrong/items'

        self.assertIsNone(handler.mParamsUrl())

    # Auto-generated test for mParamsUrl
    def test_mParamsUrl_detects_shutdown_and_sets_server_flag(self):
        handler, server, _, _, _ = self._make_handler()
        handler.path = '/api/shutdown'

        result = handler.mParamsUrl()

        self.assertEqual(result, 'shutdown')
        self.assertTrue(server._BaseServer__shutdown_request)

    # Auto-generated test for mParamsUrl
    def test_mParamsUrl_resolves_registered_endpoint_without_query(self):
        handler, _, log, _, _ = self._make_handler()
        handler.path = '/api/items'

        result = handler.mParamsUrl()

        self.assertEqual(result['endpoint'], RecordingEndpoint)
        self.assertEqual(result['endpointName'], 'items')
        self.assertIsNone(result['args'])
        log.mInfo.assert_called_once()

    # Auto-generated test for mParamsUrl
    def test_mParamsUrl_parses_query_string_for_unknown_endpoint(self):
        handler, _, _, _, _ = self._make_handler()
        handler.path = '/api/custom?name=value&mode=A'

        result = handler.mParamsUrl()

        self.assertIsNone(result['endpoint'])
        self.assertEqual(result['endpointName'], 'custom')
        self.assertEqual(result['args'], {'name': 'value', 'mode': 'A'})

    # Auto-generated test for mParamsUrl
    def test_mParamsUrl_uses_unmatched_path_as_endpoint_name_without_query(self):
        handler, _, _, _, _ = self._make_handler()
        handler.path = '/api/custom'

        result = handler.mParamsUrl()

        self.assertIsNone(result['endpoint'])
        self.assertEqual(result['endpointName'], 'custom')
        self.assertIsNone(result['args'])

    # Auto-generated test for mParamsUrl
    def test_mParamsUrl_parses_query_string_for_known_endpoint(self):
        handler, _, _, _, _ = self._make_handler()
        handler.path = '/api/items?name=value'

        result = handler.mParamsUrl()

        self.assertEqual(result['endpoint'], RecordingEndpoint)
        self.assertEqual(result['endpointName'], 'items')
        self.assertEqual(result['args'], {'name': 'value'})

    # Auto-generated test for mAuthenticate
    def test_mAuthenticate_rejects_missing_authorization_header(self):
        handler, _, _, _, _ = self._make_handler()
        handler.headers.get.side_effect = [None, '']
        handler.do_AUTHHEAD = MagicMock()

        result = handler.mAuthenticate()

        self.assertFalse(result)
        handler.do_AUTHHEAD.assert_called_once_with()
        self.assertEqual(
            handler.wfile.getvalue(),
            b'Authentication failed not authorized to access this service. No Authorization header provided.'
        )

    # Auto-generated test for mAuthenticate
    def test_mAuthenticate_accepts_valid_authorization_header(self):
        handler, _, _, _, auth = self._make_handler()
        handler.headers.get.return_value = 'Basic good'
        auth.mEvaluateAuth.return_value = ebHTTPAuthResult.AUTH_OK

        result = handler.mAuthenticate()

        self.assertTrue(result)
        auth.mEvaluateAuth.assert_called_once_with('Basic good')

    # Auto-generated test for mAuthenticate
    def test_mAuthenticate_rejects_invalid_authorization_header(self):
        handler, _, _, _, auth = self._make_handler()
        handler.headers.get.return_value = 'Basic bad'
        auth.mEvaluateAuth.return_value = 'AUTH_FAIL'
        handler.do_AUTHHEAD = MagicMock()

        result = handler.mAuthenticate()

        self.assertFalse(result)
        handler.do_AUTHHEAD.assert_called_once_with()
        self.assertEqual(
            handler.wfile.getvalue(),
            b'Basic badAuthentication failed not authorized to access this service'
        )

    # Auto-generated test for mDefaultHandler
    def test_mDefaultHandler_returns_early_when_authentication_fails(self):
        handler, _, _, _, _ = self._make_handler()
        handler.mAuthenticate = MagicMock(return_value=False)
        handler.do_HEAD = MagicMock()

        handler.mDefaultHandler('mGet')

        handler.do_HEAD.assert_not_called()
        self.assertEqual(handler.wfile.getvalue(), b'')

    # Auto-generated test for mDefaultHandler
    def test_mDefaultHandler_handles_shutdown_response(self):
        handler, _, _, config, _ = self._make_handler()
        handler.mAuthenticate = MagicMock(return_value=True)
        handler.mGetBody = MagicMock(return_value=None)
        handler.mParamsUrl = MagicMock(return_value='shutdown')
        handler.do_HEAD = MagicMock()
        config.mGetPrefix.return_value = 'api'

        handler.mDefaultHandler('mGet')

        handler.do_HEAD.assert_called_once()
        response = handler.do_HEAD.call_args[0][0]
        self.assertEqual(response['text'], 'Shutdown api')
        self.assertEqual(json.loads(handler.wfile.getvalue().decode('utf8')), response)

    # Auto-generated test for mDefaultHandler
    def test_mDefaultHandler_rejects_invalid_prefix(self):
        handler, _, _, _, _ = self._make_handler()
        handler.mAuthenticate = MagicMock(return_value=True)
        handler.mGetBody = MagicMock(return_value=None)
        handler.mParamsUrl = MagicMock(return_value=None)
        handler.do_HEAD = MagicMock()

        handler.mDefaultHandler('mGet')

        response = handler.do_HEAD.call_args[0][0]
        self.assertEqual(response['status'], 500)
        self.assertEqual(response['error'], 'Invalid initial signature')

    # Auto-generated test for mDefaultHandler
    def test_mDefaultHandler_returns_welcome_message_for_root_path(self):
        handler, _, _, config, _ = self._make_handler()
        handler.path = '/api'
        handler.mAuthenticate = MagicMock(return_value=True)
        handler.mGetBody = MagicMock(return_value=None)
        handler.mParamsUrl = MagicMock(return_value={'endpoint': RecordingEndpoint, 'endpointName': '', 'args': None})
        handler.do_HEAD = MagicMock()
        config.mGetPrefix.return_value = 'api'

        handler.mDefaultHandler('mGet')

        response = handler.do_HEAD.call_args[0][0]
        self.assertEqual(response['text'], 'Welcome to the api')

    # Auto-generated test for mDefaultHandler
    def test_mDefaultHandler_handles_unknown_endpoint(self):
        handler, _, _, _, _ = self._make_handler()
        handler.path = '/api/unknown'
        handler.mAuthenticate = MagicMock(return_value=True)
        handler.mGetBody = MagicMock(return_value=None)
        handler.mParamsUrl = MagicMock(return_value={'endpoint': None, 'endpointName': 'unknown', 'args': None})
        handler.do_HEAD = MagicMock()

        handler.mDefaultHandler('mGet')

        response = handler.do_HEAD.call_args[0][0]
        self.assertEqual(response['status'], 404)
        self.assertEqual(response['error'], 'Endpoint not found')

    # Auto-generated test for mDefaultHandler
    def test_mDefaultHandler_skips_callback_when_params_are_invalid(self):
        handler, server, _, _, _ = self._make_handler()
        endpoint_class = MagicMock()
        handler.path = '/api/items'
        handler.mAuthenticate = MagicMock(return_value=True)
        handler.mGetBody = MagicMock(return_value={'name': 'value'})
        handler.mParamsUrl = MagicMock(return_value={'endpoint': endpoint_class, 'endpointName': 'items', 'args': {'name': 'value'}})
        handler.mValidMandatoryParams = MagicMock(return_value=False)
        handler.do_HEAD = MagicMock()
        server.mGetSharedData.return_value = {'shared': True}

        handler.mDefaultHandler('mPost')

        endpoint_class.assert_not_called()
        response = handler.do_HEAD.call_args[0][0]
        self.assertEqual(response['status'], 200)

    # Auto-generated test for mDefaultHandler
    def test_mDefaultHandler_invokes_endpoint_callback_when_params_are_valid(self):
        handler, server, _, _, _ = self._make_handler()
        handler.path = '/api/items'
        handler.command = 'GET'
        handler.mAuthenticate = MagicMock(return_value=True)
        handler.mGetBody = MagicMock(return_value=None)
        handler.mParamsUrl = MagicMock(return_value={'endpoint': RecordingEndpoint, 'endpointName': 'items', 'args': {'name': 'value'}})
        handler.mValidMandatoryParams = MagicMock(return_value=True)
        handler.do_HEAD = MagicMock()
        server.mGetSharedData.return_value = {'token': 'shared'}

        handler.mDefaultHandler('mGet')

        response = handler.do_HEAD.call_args[0][0]
        self.assertEqual(response['text'], {'callback': 'mGet', 'shared': {'token': 'shared'}})
        self.assertEqual(json.loads(handler.wfile.getvalue().decode('utf8')), response)


if __name__ == '__main__':
    unittest.main()
