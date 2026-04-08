#!/bin/python
#
# $Header: tests_UserConnector.py 12-mar-2026.08:51:50 prsshukl Exp $
#
# tests_UserConnector.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_UserConnector.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    03/12/26 - Creation
#
import copy
import os
import runpy
import sys
import unittest
from contextlib import ExitStack
from unittest import TestCase
from unittest.mock import MagicMock, patch

from exabox.core.Error import ExacloudRuntimeError
from oci._vendor.requests.exceptions import HTTPError as OCIHTTPError

from exabox.exaoci.connectors.UserConnector import UserConnector


class ebTestUserConnector(TestCase):

    def setUp(self):
        self.base_bundle = {
            "monitoringConfig": {
                "monitoringTenancyOcid": "ocid.tenancy",
                "monitoringUserOcid": "ocid.user",
                "region": "us-phoenix-1"
            },
            "realmName": "region1",
            "corporateProxy": "http://proxy.example.com:80",
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.region1.sea.instance"
        }
        self.config_options = {
            "user_principals_fingerprint": "/tmp/fingerprint",
            "user_principals_key_file": "/tmp/keys"
        }
        self.read_contents = {
            "/tmp/fingerprint": "fingerprint-data",
            "/tmp/keys": "key-data"
        }
        self.module_paths = [
            "exabox.exaoci.connectors.UserConnector",
            "ecs.exacloud.exabox.exaoci.connectors.UserConnector"
        ]

    def _enter_module_patches(self, stack, attribute, **patch_kwargs):
        mocks = []
        for module_path in self.module_paths:
            try:
                mocks.append(stack.enter_context(patch(f"{module_path}.{attribute}", **patch_kwargs)))
            except ModuleNotFoundError:
                continue
        return mocks

    def _build_stub_connector(self, *, config_bundle=None, config_file=None,
                              realm="r1", basepath="/tmp/base", retries=2):
        connector = UserConnector.__new__(UserConnector)
        connector._UserConnector__config_bundle = config_bundle or {}
        connector._UserConnector__config_file = config_file or {}
        connector._UserConnector__realm = realm
        connector._UserConnector__basepath = basepath
        connector._UserConnector__retries = retries
        return connector

    def _make_connector(self, bundle=None, patch_set_cloud_env=True, config_options=None, read_contents=None):
        final_bundle = copy.deepcopy(bundle) if bundle is not None else copy.deepcopy(self.base_bundle)
        option_map = dict(self.config_options)
        if config_options:
            option_map.update(config_options)
        content_map = dict(self.read_contents)
        if read_contents:
            content_map.update(read_contents)

        def fake_get_value(option, _config_path):
            return option_map[option]

        def fake_read(path):
            return content_map[path]

        set_env_mock = None
        with ExitStack() as stack:
            self._enter_module_patches(stack, "load_config_bundle", return_value=final_bundle)
            self._enter_module_patches(stack, "read_file_into_string", side_effect=fake_read)
            self._enter_module_patches(stack, "get_value_from_exabox_config", side_effect=fake_get_value)
            if patch_set_cloud_env:
                set_env_mock = stack.enter_context(
                    patch.object(UserConnector, "set_cloud_env", autospec=True))
            connector = UserConnector()
        return connector, set_env_mock

    # Auto-generated test for __init__
    def test_init_invokes_set_cloud_env_and_builds_config(self):
        connector, set_cloud_env_mock = self._make_connector()
        expected_config = {
            "tenancy": self.base_bundle["monitoringConfig"]["monitoringTenancyOcid"],
            "user": self.base_bundle["monitoringConfig"]["monitoringUserOcid"],
            "fingerprint": self.read_contents[self.config_options["user_principals_fingerprint"]],
            "key_file": self.read_contents[self.config_options["user_principals_key_file"]],
            "region": self.base_bundle["monitoringConfig"]["region"]
        }
        self.assertEqual(expected_config, connector.get_oci_config())
        self.assertIsNotNone(set_cloud_env_mock)
        set_cloud_env_mock.assert_called_once_with(connector)

    # Auto-generated test for mGetConfigOption
    def test_m_get_config_option_delegates_to_config(self):
        connector, _ = self._make_connector()
        expected_value = "/tmp/custom-value"
        with ExitStack() as stack:
            get_value_mocks = self._enter_module_patches(
                stack, "get_value_from_exabox_config", return_value=expected_value)
            result = connector.mGetConfigOption("custom_option")
        self.assertEqual(expected_value, result)
        called_mock = next((mock for mock in get_value_mocks if mock.called), None)
        self.assertIsNotNone(called_mock)
        self.assertEqual(
            ("custom_option",
             os.path.join(connector._UserConnector__basepath, "config/exabox.conf")),
            called_mock.call_args[0])

    # Auto-generated test for mObtainRealm
    def test_m_obtain_realm_handles_explicit_and_inferred_values(self):
        connector = self._build_stub_connector(config_bundle={"realmName": "region1"})
        self.assertEqual("r1", connector.mObtainRealm())

        connector = self._build_stub_connector(config_bundle={"realmName": "oc4"})
        self.assertEqual("oc4", connector.mObtainRealm())

        connector = self._build_stub_connector(
            config_bundle={"exaccInfrastructureOcid": "ocid1.exadatainfrastructure.region1.sea.instance"})
        self.assertEqual("r1", connector.mObtainRealm())

        connector = self._build_stub_connector(
            config_bundle={"exaccInfrastructureOcid": "ocid1.exadatainfrastructure.us-ashburn-1.instance"})
        self.assertEqual("us-ashburn-1", connector.mObtainRealm())

    # Auto-generated test for mObtainRealm
    def test_m_obtain_realm_returns_region1_when_not_sea(self):
        connector = self._build_stub_connector(
            config_bundle={"exaccInfrastructureOcid": "ocid1.exadatainfrastructure.region1.dublin.instance"})
        self.assertEqual("region1", connector.mObtainRealm())

    # Auto-generated test for get_connector_type
    def test_get_connector_type_returns_expected_value(self):
        connector = self._build_stub_connector()
        self.assertEqual("UserConnector", connector.get_connector_type())

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_returns_signer_on_success(self):
        connector = self._build_stub_connector(config_file={
            "tenancy": "ocid.tenancy",
            "user": "ocid.user",
            "fingerprint": "fingerprint-data",
            "key_file": "key-data",
            "region": "us-phoenix-1"
        })
        signer_instance = MagicMock()
        with ExitStack() as stack:
            signer_mocks = self._enter_module_patches(
                stack, "Signer", return_value=signer_instance)
            self._enter_module_patches(
                stack, "get_value_from_exabox_config", return_value="/tmp/keys")
            token = connector.get_auth_principal_token()
        self.assertIs(token, signer_instance)
        called_signer = next((mock for mock in signer_mocks if mock.called), None)
        self.assertIsNotNone(called_signer)
        called_signer.assert_called_once_with(
            tenancy="ocid.tenancy",
            user="ocid.user",
            fingerprint="fingerprint-data",
            private_key_file_location="/tmp/keys")

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_propagates_oci_http_error(self):
        connector = self._build_stub_connector(config_file={
            "tenancy": "ocid.tenancy",
            "user": "ocid.user",
            "fingerprint": "fingerprint-data",
            "key_file": "key-data",
            "region": "us-phoenix-1"
        })
        with ExitStack() as stack:
            self._enter_module_patches(
                stack, "Signer", side_effect=OCIHTTPError("bad request"))
            self._enter_module_patches(
                stack, "get_value_from_exabox_config", return_value="/tmp/keys")
            with self.assertRaises(OCIHTTPError):
                connector.get_auth_principal_token()

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_retries_and_raises_runtime_error(self):
        connector = self._build_stub_connector(
            config_file={
                "tenancy": "ocid.tenancy",
                "user": "ocid.user",
                "fingerprint": "fingerprint-data",
                "key_file": "key-data",
                "region": "us-phoenix-1"
            },
            retries=2)
        with ExitStack() as stack:
            self._enter_module_patches(
                stack, "Signer", side_effect=Exception("failure"))
            self._enter_module_patches(
                stack, "get_value_from_exabox_config", return_value="/tmp/keys")
            sleep_mocks = self._enter_module_patches(stack, "sleep")
            trace_mocks = self._enter_module_patches(stack, "ebLogTrace")
            error_mocks = self._enter_module_patches(stack, "ebLogError")
            with self.assertRaises(ExacloudRuntimeError) as context:
                connector.get_auth_principal_token()
        self.assertIn("failure", str(context.exception))
        total_sleep_calls = sum(mock.call_count for mock in sleep_mocks)
        self.assertEqual(connector._UserConnector__retries, total_sleep_calls)
        for mock in sleep_mocks:
            if mock.called:
                mock.assert_called_with(1)
        self.assertTrue(any(mock.called for mock in trace_mocks))
        self.assertTrue(any(mock.called for mock in error_mocks))
        self.assertIsInstance(context.exception.__cause__, Exception)

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_succeeds_after_transient_failure(self):
        connector = self._build_stub_connector(
            config_file={
                "tenancy": "ocid.tenancy",
                "user": "ocid.user",
                "fingerprint": "fingerprint-data",
                "key_file": "key-data",
                "region": "us-phoenix-1"
            },
            retries=3)
        signer_instance = MagicMock()
        side_effects = [Exception("flaky signer"), signer_instance]

        def signer_side_effect(*_args, **_kwargs):
            result = side_effects.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with ExitStack() as stack:
            signer_mocks = self._enter_module_patches(
                stack, "Signer", side_effect=signer_side_effect)
            self._enter_module_patches(
                stack, "get_value_from_exabox_config", return_value="/tmp/keys")
            sleep_mocks = self._enter_module_patches(stack, "sleep")
            trace_mocks = self._enter_module_patches(stack, "ebLogTrace")
            token = connector.get_auth_principal_token()
        self.assertIs(token, signer_instance)
        # First attempt fails, second succeeds.
        total_sleep_calls = sum(mock.call_count for mock in sleep_mocks)
        self.assertEqual(1, total_sleep_calls)
        for mock in sleep_mocks:
            if mock.called:
                mock.assert_called_once_with(1)
        self.assertTrue(any(mock.called for mock in trace_mocks))
        called_signer = next((mock for mock in signer_mocks if mock.called), None)
        self.assertIsNotNone(called_signer)
        self.assertEqual(2, called_signer.call_count)

    # Auto-generated test for set_cloud_env
    def test_set_cloud_env_sets_proxy_and_ca_bundle(self):
        connector = self._build_stub_connector(
            config_bundle={"corporateProxy": "http://proxy.example.com:80"}, realm="r1")
        expected_ca = os.path.join(connector._UserConnector__basepath, "exabox/kms/combined_r1.crt")
        with patch.dict(os.environ, {}, clear=True):
            connector.set_cloud_env()
            self.assertEqual("http://proxy.example.com:80", os.environ["HTTPS_PROXY"])
            self.assertEqual(expected_ca, os.environ["REQUESTS_CA_BUNDLE"])

    # Auto-generated test for set_cloud_env
    def test_set_cloud_env_skips_proxy_and_ca_when_not_required(self):
        connector = self._build_stub_connector(
            config_bundle={"corporateProxy": "null"}, realm="oc4")
        with patch.dict(os.environ, {}, clear=True):
            connector.set_cloud_env()
            self.assertNotIn("HTTPS_PROXY", os.environ)
            self.assertNotIn("REQUESTS_CA_BUNDLE", os.environ)

    # Auto-generated test for set_cloud_env
    def test_set_cloud_env_sets_ca_without_proxy_values(self):
        for proxy_value in (None, ""):
            with self.subTest(proxy_value=proxy_value):
                connector = self._build_stub_connector(
                    config_bundle={"corporateProxy": proxy_value}, realm="r1")
                expected_ca = os.path.join(
                    connector._UserConnector__basepath, "exabox/kms/combined_r1.crt")
                with patch.dict(os.environ, {}, clear=True):
                    connector.set_cloud_env()
                    self.assertNotIn("HTTPS_PROXY", os.environ)
                    self.assertEqual(expected_ca, os.environ["REQUESTS_CA_BUNDLE"])

    # Auto-generated test for set_cloud_env
    def test_set_cloud_env_sets_ca_when_proxy_is_literal_null(self):
        connector = self._build_stub_connector(
            config_bundle={"corporateProxy": "null"}, realm="r1")
        expected_ca = os.path.join(connector._UserConnector__basepath, "exabox/kms/combined_r1.crt")
        with patch.dict(os.environ, {}, clear=True):
            connector.set_cloud_env()
            self.assertNotIn("HTTPS_PROXY", os.environ)
            self.assertEqual(expected_ca, os.environ["REQUESTS_CA_BUNDLE"])

    # Auto-generated test for set_cloud_env
    def test_set_cloud_env_sets_proxy_without_ca_for_non_r1_realm(self):
        connector = self._build_stub_connector(
            config_bundle={"corporateProxy": "http://proxy.example.com:80"},
            realm="oc4")
        with patch.dict(os.environ, {}, clear=True):
            connector.set_cloud_env()
            self.assertEqual("http://proxy.example.com:80", os.environ["HTTPS_PROXY"])
            self.assertNotIn("REQUESTS_CA_BUNDLE", os.environ)

    # Auto-generated test for module execution
    def test_module_can_execute_via_run_path(self):
        module = sys.modules[UserConnector.__module__]
        module_path = module.__file__
        with patch.dict(os.environ, {}, clear=True):
            globals_after = runpy.run_path(module_path, run_name="__main__")
        self.assertIn("UserConnector", globals_after)
        self.assertEqual("UserConnector", globals_after["UserConnector"].__name__)

    # Auto-generated test for get_oci_config
    def test_get_oci_config_returns_active_configuration(self):
        connector, _ = self._make_connector()
        expected_config = {
            "tenancy": self.base_bundle["monitoringConfig"]["monitoringTenancyOcid"],
            "user": self.base_bundle["monitoringConfig"]["monitoringUserOcid"],
            "fingerprint": self.read_contents[self.config_options["user_principals_fingerprint"]],
            "key_file": self.read_contents[self.config_options["user_principals_key_file"]],
            "region": self.base_bundle["monitoringConfig"]["region"]
        }
        self.assertEqual(expected_config, connector.get_oci_config())

    # Auto-generated test for mObtainRealm
    def test_init_normalizes_region1_realm_value(self):
        connector, _ = self._make_connector()
        self.assertEqual("r1", connector._UserConnector__realm)

    # Auto-generated test for mObtainRealm
    def test_init_preserves_non_region1_realm_value(self):
        custom_bundle = copy.deepcopy(self.base_bundle)
        custom_bundle["realmName"] = "oc4"
        connector, _ = self._make_connector(bundle=custom_bundle)
        self.assertEqual("oc4", connector._UserConnector__realm)

    # Auto-generated test for mObtainRealm
    def test_init_infers_region1_realm_from_infrastructure_ocid(self):
        custom_bundle = copy.deepcopy(self.base_bundle)
        custom_bundle.pop("realmName", None)
        custom_bundle["exaccInfrastructureOcid"] = "ocid1.exadatainfrastructure.region1.sea.instance"
        connector, _ = self._make_connector(bundle=custom_bundle)
        self.assertEqual("r1", connector._UserConnector__realm)

    # Auto-generated test for mObtainRealm
    def test_init_infers_generic_realm_from_infrastructure_ocid(self):
        custom_bundle = copy.deepcopy(self.base_bundle)
        custom_bundle.pop("realmName", None)
        custom_bundle["exaccInfrastructureOcid"] = "ocid1.exadatainfrastructure.us-ashburn-1.instance"
        connector, _ = self._make_connector(bundle=custom_bundle)
        self.assertEqual("us-ashburn-1", connector._UserConnector__realm)


def suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(ebTestUserConnector)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([suite()])


if __name__ == '__main__':
    unittest.main()
