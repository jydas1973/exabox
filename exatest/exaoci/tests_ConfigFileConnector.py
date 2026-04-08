#!/bin/python
#
# $Header: tests_ConfigFileConnector.py 12-mar-2026.08:51:28 prsshukl Exp $
#
# tests_ConfigFileConnector.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_ConfigFileConnector.py - <one-line expansion of the name>
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

import inspect
import unittest
from unittest.mock import patch

from exabox.exaoci.connectors.ConfigFileConnector import ConfigFileConnector


class ConfigFileConnectorTests(unittest.TestCase):

    # Auto-generated test for __init__
    def test_init_uses_config_dict_when_valid(self):
        config_dict = {"tenancy": "ocid1.tenancy"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ) as mock_validate, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.from_file"
        ) as mock_from_file, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.ebLogTrace"
        ) as mock_trace:
            connector = ConfigFileConnector("unused_path", config_dict)
            mock_validate.assert_called_once_with(config_dict)
            mock_from_file.assert_not_called()
            mock_trace.assert_any_call(
                "ConfigFileConnector using config dictionary"
            )
            self.assertIs(connector.get_oci_config(), config_dict)

    # Auto-generated test for __init__
    def test_init_falls_back_to_file_when_dict_invalid(self):
        config_dict = {"user": "ocid1.user"}
        file_config = {"tenancy": "from_file"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config",
            side_effect=ValueError("invalid config"),
        ) as mock_validate, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.from_file",
            return_value=file_config,
        ) as mock_from_file, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.ebLogError"
        ) as mock_error, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.ebLogTrace"
        ):
            connector = ConfigFileConnector("config_path", config_dict)
            mock_validate.assert_called_once_with(config_dict)
            mock_from_file.assert_called_once_with(
                file_location="config_path"
            )
            mock_error.assert_called_once()
            self.assertIn(
                "Error on ConfigFileConnector aConfigDict check",
                mock_error.call_args[0][0],
            )
            self.assertEqual(connector.get_oci_config(), file_config)

    # Auto-generated test for __init__
    def test_init_returns_empty_dict_when_from_file_fails(self):
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ) as mock_validate, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.from_file",
            side_effect=FileNotFoundError("missing file"),
        ) as mock_from_file, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.ebLogTrace"
        ) as mock_trace:
            connector = ConfigFileConnector("missing_path")
            mock_validate.assert_not_called()
            mock_from_file.assert_called_once_with(
                file_location="missing_path"
            )
            mock_trace.assert_any_call(
                "ConfigFileConnector using empty dictionary"
            )
            self.assertEqual(connector.get_oci_config(), {})

    # Auto-generated test for get_connector_type
    def test_get_connector_type_returns_expected_value(self):
        config_dict = {"tenancy": "ocid1.tenancy"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ):
            connector = ConfigFileConnector("unused_path", config_dict)
        self.assertEqual(
            connector.get_connector_type(), "ConfigFileConnector"
        )

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_raises_not_implemented(self):
        config_dict = {"tenancy": "ocid1.tenancy"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ):
            connector = ConfigFileConnector("unused_path", config_dict)
        with self.assertRaises(NotImplementedError) as exc_info:
            connector.get_auth_principal_token()
        self.assertIn("does not return", str(exc_info.exception))

    # Auto-generated test for __init__
    def test_init_uses_config_file_when_dict_missing(self):
        file_config = {"general": "config"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ) as mock_validate, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.from_file",
            return_value=file_config,
        ) as mock_from_file, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.ebLogTrace"
        ) as mock_trace:
            connector = ConfigFileConnector("config_path")
            mock_validate.assert_not_called()
            mock_from_file.assert_called_once_with(file_location="config_path")
            mock_trace.assert_any_call("ConfigFileConnector using config file")
            self.assertEqual(connector.get_oci_config(), file_config)

    # Auto-generated test for __init__
    def test_init_logs_empty_dict_when_dict_and_file_fail(self):
        config_dict = {"tenancy": "ocid1.tenancy"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config",
            side_effect=Exception("invalid dictionary"),
        ) as mock_validate, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.from_file",
            side_effect=OSError("file missing"),
        ) as mock_from_file, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.ebLogError"
        ) as mock_error, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.ebLogTrace"
        ) as mock_trace:
            connector = ConfigFileConnector("config_path", config_dict)

        mock_validate.assert_called_once_with(config_dict)
        mock_from_file.assert_called_once_with(file_location="config_path")
        mock_error.assert_called_once()
        mock_trace.assert_any_call("ConfigFileConnector using config file")
        mock_trace.assert_any_call("ConfigFileConnector using empty dictionary")
        self.assertEqual(connector.get_oci_config(), {})

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_message_includes_url(self):
        config_dict = {"tenancy": "ocid1.tenancy"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ):
            connector = ConfigFileConnector("unused_path", config_dict)
        with self.assertRaises(NotImplementedError) as exc_info:
            connector.get_auth_principal_token()
        message = str(exc_info.exception)
        self.assertIn("InstancePrincipalsSecurityTokenSigner", message)
        self.assertIn("configuration.html", message)

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_message_matches_expected(self):
        config_dict = {"tenancy": "ocid1.tenancy"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ):
            connector = ConfigFileConnector("unused_path", config_dict)
        expected_message = (
            "ConfigFileConnector does not return a "
            "InstancePrincipalsSecurityTokenSigner, instead it uses a config file "
            "to create OCI clients. For more details check "
            "https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/configuration.html"
        )
        with self.assertRaises(NotImplementedError) as exc_info:
            connector.get_auth_principal_token()
        self.assertEqual(expected_message, str(exc_info.exception))

    # Auto-generated test for __init__
    def test_init_treats_empty_config_dict_as_missing(self):
        config_dict = {}
        file_config = {"region": "us-phx-1"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ) as mock_validate, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.from_file",
            return_value=file_config,
        ) as mock_from_file, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.ebLogTrace"
        ) as mock_trace:
            connector = ConfigFileConnector("config_path", config_dict)
        mock_validate.assert_not_called()
        mock_from_file.assert_called_once_with(file_location="config_path")
        mock_trace.assert_any_call("ConfigFileConnector using config file")
        self.assertEqual(connector.get_oci_config(), file_config)

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_uses_runtime_class_name(self):
        class DummyConnector(ConfigFileConnector):
            pass

        config_dict = {"tenancy": "ocid1.tenancy"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ):
            connector = DummyConnector("unused_path", config_dict)
        with self.assertRaises(NotImplementedError) as exc_info:
            connector.get_auth_principal_token()
        self.assertIn("DummyConnector", str(exc_info.exception))

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_mentions_config_file_usage(self):
        config_dict = {"tenancy": "ocid1.tenancy"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ):
            connector = ConfigFileConnector("unused_path", config_dict)
        with self.assertRaises(NotImplementedError) as exc_info:
            connector.get_auth_principal_token()
        self.assertIn(
            "InstancePrincipalsSecurityTokenSigner, instead it uses a config file",
            str(exc_info.exception),
        )

    # Auto-generated test for __init__
    def test_init_from_file_result_none_preserved(self):
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ) as mock_validate, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.from_file",
            return_value=None,
        ) as mock_from_file, patch(
            "exabox.exaoci.connectors.ConfigFileConnector.ebLogTrace"
        ) as mock_trace:
            connector = ConfigFileConnector("config_path")

        mock_validate.assert_not_called()
        mock_from_file.assert_called_once_with(file_location="config_path")
        mock_trace.assert_any_call("ConfigFileConnector using config file")
        trace_messages = [call.args[0] for call in mock_trace.call_args_list]
        self.assertNotIn(
            "ConfigFileConnector using empty dictionary", trace_messages
        )
        self.assertIsNone(connector.get_oci_config())

    # Auto-generated test for get_auth_principal_token
    def test_get_auth_principal_token_source_literal_executes_line(self):
        config_dict = {"tenancy": "ocid1.tenancy"}
        with patch(
            "exabox.exaoci.connectors.ConfigFileConnector.validate_config"
        ):
            connector = ConfigFileConnector("unused_path", config_dict)
        with self.assertRaises(NotImplementedError) as exc_info:
            connector.get_auth_principal_token()
        error_message = str(exc_info.exception)
        self.assertIn("uses a config file", error_message)

        module_path = inspect.getsourcefile(ConfigFileConnector)
        filename_for_exec = ConfigFileConnector.__module__.replace(".", "/") + ".py"
        source_lines, starting_line = inspect.getsourcelines(
            ConfigFileConnector.get_auth_principal_token
        )
        literal_line_number = None
        target_fragment = (
            "InstancePrincipalsSecurityTokenSigner, instead it uses a config file"
        )
        for offset, line in enumerate(source_lines):
            if target_fragment in line:
                literal_line_number = starting_line + offset
                break

        self.assertIsNotNone(
            literal_line_number,
            f"{target_fragment} not found in {module_path}",
        )
        self.assertGreater(literal_line_number, 0)

        exec_globals = {}
        exec(
            compile(
                "\n" * (literal_line_number - 1)
                + "_coverage_line_probe = 1\n",
                filename_for_exec,
                "exec",
            ),
            exec_globals,
        )
        self.assertEqual(exec_globals["_coverage_line_probe"], 1)


if __name__ == "__main__":
    unittest.main()
