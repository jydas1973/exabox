#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/exaoci/tests_ExaOCIFactory.py /main/5 2025/08/08 06:25:24 kkviswan Exp $
#
# tests_ExaOCIFactory.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_ExaOCIFactory.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    kkviswan    08/06/25 - 38281813 - ECS_MAIN TESTS_EXAOCIFACTORY_PY.DIF IS
#                           FAILING IN ECS_MAIN_LINUX.X64_250805.0145
#    ririgoye    07/30/25 - Bug 38259103 - COVERAGE: INCREASE UNIT TEST
#                           COVERAGE IN EXAOCIFACTORY.PY FILE
#    aypaul      08/10/23 - Update unit test cases for 35685390.
#    ndesanto    07/04/22 - Test OCI connections types
#    ndesanto    07/04/22 - Creation
#

import unittest
import warnings

warnings.filterwarnings("ignore")

from oci.key_management import KmsCryptoClient
from oci.object_storage import ObjectStorageClient
from oci.secrets import SecretsClient
from oci.vault import VaultsClient
from unittest.mock import MagicMock, Mock, patch

from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Context import get_gcontext
from exabox.exaoci.connectors.ResourceConnector import ResourceConnector
from exabox.exaoci.connectors.UserConnector import UserConnector
from exabox.exaoci.connectors.ConfigFileConnector import ConfigFileConnector
from exabox.exaoci.connectors.ExaboxConfConnector import ExaboxConfConnector
from exabox.exaoci.connectors.DefaultConnector import DefaultConnector
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.exaoci.connectors.R1Connector import R1Connector
from exabox.exaoci.connectors.RegionConnector import RegionConnector
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogTrace


class ebTestClusterEncryption(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)

#
# Done - Test the creation of the different connectors (5 types)
# Test the creation of the 4 types of objects supported
#

    @patch("exabox.exaoci.ExaOCIFactory.is_r1_region")
    def test_create_R1Connector(self, aIsR1):
        """
        Function to test the creation of an R1Connector from the factory by
        manually satisfaying the required checks.
        """

        aIsR1.return_value = True
        _factory = ExaOCIFactory()
        self.assertIsInstance(_factory.get_oci_connector(), R1Connector)

    def test_get_auth_principal_token(self):

        _current_connector = R1Connector()
        _current_connector.retries = 1
        with self.assertRaises(ExacloudRuntimeError):
            _current_connector.get_auth_principal_token()

        _current_connector = DefaultConnector()
        _current_connector.retries = 1
        with self.assertRaises(ExacloudRuntimeError):
            _current_connector.get_auth_principal_token()

        _current_connector = ExaboxConfConnector("mock_cert_path", "mock_service_domain")
        _current_connector.retries = 1
        with self.assertRaises(ExacloudRuntimeError):
            _current_connector.get_auth_principal_token()

        _current_connector = ExaboxConfConnector("mock_oci_region", "mock_oci_domin")
        _current_connector.retries = 1
        with self.assertRaises(ExacloudRuntimeError):
            _current_connector.get_auth_principal_token()

    @patch("exabox.exaoci.ExaOCIFactory.ExaboxConfConnector", spec=ExaboxConfConnector)
    @patch("exabox.exaoci.ExaOCIFactory.get_gcontext")
    @patch("exabox.exaoci.ExaOCIFactory.is_r1_region")
    def test_create_ExaboxConfConnector(self, aIsR1, aGContext, aExaboxConfConnector):
        """
        Function to test the creation of an ExaboxConfConnector from the factory by
        manually satisfaying the required checks.
        """

        def _gcontext(*args, **kwargs):
            if args[0] == "oci_certificate_path":
                return "/tmp/some_cert_path"
            elif args[0] == "oci_service_domain":
                return "/tmp/some_domain_name"
            return None

        aIsR1.return_value = False
        aGContext.return_value.mCheckConfigOption.side_effect = _gcontext
        _factory = ExaOCIFactory()
        self.assertIsInstance(_factory.get_oci_connector(), ExaboxConfConnector)

    @patch("exabox.exaoci.ExaOCIFactory.RegionConnector", spec=RegionConnector)
    @patch("exabox.exaoci.ExaOCIFactory.load_oci_region_config")
    @patch("exabox.exaoci.ExaOCIFactory.get_gcontext")
    @patch("exabox.exaoci.ExaOCIFactory.is_r1_region")
    def test_create_RegionConnector(self, aIsR1, aGContext, aRegionConfig, aRegionConnector):
        """
        Function to test the creation of an RegionConnector from the factory by
        manually satisfaying the required checks.
        """

        aIsR1.return_value = False
        aGContext.return_value.mCheckConfigOption.return_value = None
        aRegionConfig.return_value = {
            "realmDomainComponent": "oracleiaas.com",
            "realmKey": "R1_ENVIRONMENT",
            "regionIdentifier": "r1",
            "regionKey": "SEA"
        }
        _factory = ExaOCIFactory()
        self.assertIsInstance(_factory.get_oci_connector(), RegionConnector)

    @patch("exabox.exaoci.ExaOCIFactory.ConfigFileConnector", spec=ConfigFileConnector)
    @patch("exabox.exaoci.ExaOCIFactory.load_oci_region_config")
    @patch("exabox.exaoci.ExaOCIFactory.get_gcontext")
    @patch("exabox.exaoci.ExaOCIFactory.is_r1_region")
    def test_create_ConfigFileConnector(self, aIsR1, aGContext, aRegionConfig, aConfigFileConnector):
        """
        Function to test the creation of an ConfigFileConnector from the factory by
        manually satisfaying the required checks.
        """

        def _gcontext(*args, **kwargs):
            if args[0] == "exakms_oci_config_file":
                return "/tmp/some_oci_config_file_path"
            return None

        aIsR1.return_value = False
        aGContext.return_value.mCheckConfigOption.side_effect = _gcontext
        aRegionConfig.side_effect = Exception("Mock Error")
        _factory = ExaOCIFactory()
        self.assertIsInstance(_factory.get_oci_connector(), ConfigFileConnector)

    @patch("exabox.exaoci.ExaOCIFactory.DefaultConnector", spec=DefaultConnector)
    @patch("exabox.exaoci.ExaOCIFactory.load_oci_region_config")
    @patch("exabox.exaoci.ExaOCIFactory.get_gcontext")
    @patch("exabox.exaoci.ExaOCIFactory.is_r1_region")
    def test_create_DefaultConnector(self, aIsR1, aGContext, aRegionConfig, aDefaultConnector):
        """
        Function to test the creation of an DefaultConnector from the factory by
        manually satisfaying the required checks.
        """

        aIsR1.return_value = False
        aGContext.return_value.mCheckConfigOption.return_value = None
        aRegionConfig.side_effect = Exception("Mock Error")
        _factory = ExaOCIFactory()
        self.assertIsInstance(_factory.get_oci_connector(), DefaultConnector)

    @patch("exabox.exaoci.ExaOCIFactory.ResourceConnector", spec=ResourceConnector)
    @patch("exabox.exaoci.connectors.ResourceConnector.load_config_bundle")
    @patch("exabox.exaoci.ExaOCIFactory.get_gcontext")
    def test_create_ResourceConnector(self, aGContext, aResourceConfig, aResourceConnector):
        """
        Function to test the creation of an ResourceConnector from the factory by
        manually satisfaying the required checks.
        """

        aGContext.return_value.mCheckConfigOption.return_value = None
        aResourceConfig.return_value = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.region1.sea.anzwkljr3vfwx6qa3wjbpedoswnwe4an7s5pcj7lc54u7wul3iyylk66b2cq",
            "realmName": None,
            "monitoringConfig":{
                "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaa2ppvqrm3urmzh7c65yllj3ikoqjt7ifptet3yqb4kzsgdkm73dga",
                "compartmentId":"ocid1.compartment.oc1..aaaaaaaa4p4ovqj665f2umgwylroo62flenbc7tl62s4mwdlylsvagsttlxq",
                "namespace":"exacc_anzwkljr3vfwx6qa3wjbpedoswnwe4an7s5pcj7lc54u7wul3iyylk66b2cq",
                "region":"us-phoenix-1"
            }
        }
        _factory = ExaOCIFactory(ResourceConnector())
        self.assertIsInstance(_factory.get_oci_connector(), ResourceConnector)

    @patch("exabox.exaoci.ExaOCIFactory.UserConnector", spec=UserConnector)
    @patch("exabox.exaoci.connectors.UserConnector.load_config_bundle")
    @patch("exabox.exaoci.ExaOCIFactory.get_gcontext")
    def test_create_UserConnector(self, aGContext, aUserConfig, aUserConnector):
        """
        Function to test the creation of an UserConnector from the factory by
        manually satisfaying the required checks.
        """

        aGContext.return_value.mCheckConfigOption.return_value = None
        aUserConfig.return_value = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.region1.sea.anzwkljr3vfwx6qa3wjbpedoswnwe4an7s5pcj7lc54u7wul3iyylk66b2cq",
            "realmName": None,
            "monitoringConfig":{
                "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaa2ppvqrm3urmzh7c65yllj3ikoqjt7ifptet3yqb4kzsgdkm73dga",
                "compartmentId":"ocid1.compartment.oc1..aaaaaaaa4p4ovqj665f2umgwylroo62flenbc7tl62s4mwdlylsvagsttlxq",
                "namespace":"exacc_anzwkljr3vfwx6qa3wjbpedoswnwe4an7s5pcj7lc54u7wul3iyylk66b2cq",
                "region":"us-phoenix-1"
            }
        }
        _factory = ExaOCIFactory(UserConnector())
        self.assertIsInstance(_factory.get_oci_connector(), UserConnector)

class ebTestExaOCIFactory(unittest.TestCase):
    def setUp(self):
        # Set up test fixtures before each test method
        self.mock_connector = Mock()
        self.mock_connector.get_auth_principal_token.return_value = Mock()
        self.mock_connector.get_region.return_value = "us-phoenix-1"
        self.mock_connector.get_domain.return_value = "oraclecloud.com"
        self.mock_connector.get_certificate_path.return_value = "/tmp/somecert"
        # Create factory instance with mock connector
        self.factory = ExaOCIFactory(self.mock_connector)
    
    @patch('exabox.exaoci.ExaOCIFactory.ObjectStorageClient')
    def test_get_object_storage_client_with_default_connector(self, mock_oss_client):
        """Test ObjectStorage client creation with default connector"""
        mock_client_instance = Mock()
        mock_oss_client.return_value = mock_client_instance
        
        # Test with signer available
        self.mock_connector.get_auth_principal_token.return_value = Mock()
        
        result = self.factory.get_object_storage_client()
        
        # Verify client was created with correct parameters
        mock_oss_client.assert_called_once_with(
            config={}, 
            signer=self.mock_connector.get_auth_principal_token.return_value,
            timeout=60,
            retry_strategy=unittest.mock.ANY
        )
        self.assertEqual(result, mock_client_instance)

    @patch('exabox.exaoci.ExaOCIFactory.ObjectStorageClient')
    def test_get_object_storage_client_with_config_file_connector(self, mock_osi_client):
        """Test ObjectStorage client creation with ConfigFileConnector"""
        from exabox.exaoci.connectors.ConfigFileConnector import ConfigFileConnector
        
        mock_config_connector = Mock(spec=ConfigFileConnector)
        mock_config_connector.get_oci_config.return_value = {
            "region": "us-phoenix-1",
            "tenancy": "test-tenancy"
        }
        
        mock_client_instance = Mock()
        mock_osi_client.return_value = mock_client_instance
        
        result = self.factory.get_object_storage_client(mock_config_connector)
        
        mock_osi_client.assert_called_once_with(
            config=mock_config_connector.get_oci_config.return_value,
            timeout=60,
            retry_strategy=unittest.mock.ANY
        )

    @patch('exabox.exaoci.ExaOCIFactory.ObjectStorageClient')
    def test_get_object_storage_client_with_r1_connector(self, mock_osi_client):
        """Test ObjectStorage client creation with R1Connector"""
        from exabox.exaoci.connectors.R1Connector import R1Connector
        
        mock_r1_connector = Mock(spec=R1Connector)
        mock_r1_connector.get_auth_principal_token.return_value = Mock()
        mock_r1_connector.get_certificate_path.return_value = "/path/to/r1/cert"
        
        mock_client_instance = Mock()
        mock_client_instance.base_client = Mock()
        mock_client_instance.base_client.session = Mock()
        mock_osi_client.return_value = mock_client_instance
        
        result = self.factory.get_object_storage_client(mock_r1_connector)
        
        # Verify certificate path was set
        self.assertEqual(
            mock_client_instance.base_client.session.verify,
            "/path/to/r1/cert"
        )
        # Verify R1 endpoint was set
        self.assertEqual(
            mock_client_instance.base_client.endpoint,
            "https://objectstorage.r1.oracleiaas.com"
        )

    @patch('exabox.exaoci.ExaOCIFactory.ObjectStorageClient')
    def test_get_object_storage_client_no_signer_raises_error(self, mock_osi_client):
        """Test ObjectStorage client creation fails when no signer available"""
        from exabox.core.Error import ExacloudRuntimeError
        
        # Mock no signer available
        self.mock_connector.get_auth_principal_token.return_value = None
        
        with self.assertRaises(ExacloudRuntimeError):
            self.factory.get_object_storage_client()

    @patch('exabox.exaoci.ExaOCIFactory.VirtualNetworkClient')
    def test_get_virtual_network_client_success(self, mock_vn_client):
        """Test VirtualNetwork client creation"""
        mock_client_instance = Mock()
        mock_client_instance.base_client = Mock()
        mock_client_instance.base_client.session = Mock()
        mock_vn_client.return_value = mock_client_instance
        
        self.mock_connector.get_auth_principal_token.return_value = Mock()
        
        result = self.factory.get_virtual_network_client()
        
        mock_vn_client.assert_called_once_with(
            config={},
            signer=self.mock_connector.get_auth_principal_token.return_value,
            timeout=60,
            retry_strategy=unittest.mock.ANY
        )
        self.assertEqual(result, mock_client_instance)

    @patch('exabox.exaoci.ExaOCIFactory.ComputeClient')
    def test_get_compute_client_success(self, mock_compute_client):
        """Test Compute client creation"""
        mock_client_instance = Mock()
        mock_client_instance.base_client = Mock()
        mock_client_instance.base_client.session = Mock()
        mock_compute_client.return_value = mock_client_instance
        
        self.mock_connector.get_auth_principal_token.return_value = Mock()
        
        result = self.factory.get_compute_client()
        
        mock_compute_client.assert_called_once_with(
            config={},
            signer=self.mock_connector.get_auth_principal_token.return_value,
            timeout=60,
            retry_strategy=unittest.mock.ANY
        )
        self.assertEqual(result, mock_client_instance)

    @patch('exabox.exaoci.ExaOCIFactory.KmsCryptoClient')
    def test_get_crypto_client_success(self, mock_crypto_client):
        """Test KmsCrypto client creation"""
        mock_client_instance = Mock()
        mock_client_instance.base_client = Mock()
        mock_client_instance.base_client.session = Mock()
        mock_crypto_client.return_value = mock_client_instance
        
        self.mock_connector.get_auth_principal_token.return_value = Mock()
        crypto_endpoint = "https://test-crypto-endpoint.com"
        
        result = self.factory.get_crypto_client(crypto_endpoint)
        
        mock_crypto_client.assert_called_once_with(
            config={},
            signer=self.mock_connector.get_auth_principal_token.return_value,
            service_endpoint=crypto_endpoint,
            timeout=60,
            retry_strategy=unittest.mock.ANY
        )
        self.assertEqual(result, mock_client_instance)

    @patch('exabox.exaoci.ExaOCIFactory.VaultsClient')
    def test_get_vault_client_with_region_connector(self, mock_vault_client):
        """Test Vault client creation with RegionConnector"""
        from exabox.exaoci.connectors.RegionConnector import RegionConnector
        
        mock_region_connector = Mock(spec=RegionConnector)
        mock_region_connector.get_auth_principal_token.return_value = Mock()
        mock_region_connector.get_region.return_value = "us-phoenix-1"
        mock_region_connector.get_domain.return_value = "oraclecloud.com"
        
        mock_client_instance = Mock()
        mock_client_instance.base_client = Mock()
        mock_vault_client.return_value = mock_client_instance
        
        result = self.factory.get_vault_client(mock_region_connector)
        
        # Verify endpoint was set correctly
        expected_endpoint = "https://vaults.us-phoenix-1.oraclecloud.com"
        self.assertEqual(mock_client_instance.base_client.endpoint, expected_endpoint)

    @patch('exabox.exaoci.ExaOCIFactory.SecretsClient')
    def test_get_secrets_client_with_exabox_conf_connector(self, mock_secrets_client):
        """Test Secrets client creation with ExaboxConfConnector"""
        from exabox.exaoci.connectors.ExaboxConfConnector import ExaboxConfConnector
        
        mock_exabox_connector = Mock(spec=ExaboxConfConnector)
        mock_exabox_connector.get_auth_principal_token.return_value = Mock()
        mock_exabox_connector.get_region.return_value = "eu-frankfurt-1"
        mock_exabox_connector.get_domain.return_value = "oraclecloud.com"
        mock_exabox_connector.get_certificate_path.return_value = "/path/to/cert"
        
        mock_client_instance = Mock()
        mock_client_instance.base_client = Mock()
        mock_client_instance.base_client.session = Mock()
        mock_secrets_client.return_value = mock_client_instance
        
        result = self.factory.get_secrets_client(mock_exabox_connector)
        
        # Verify certificate path was set
        self.assertEqual(
            mock_client_instance.base_client.session.verify,
            "/path/to/cert"
        )
        # Verify endpoint was set correctly
        expected_endpoint = "https://secrets.vaults.eu-frankfurt-1.oci.oraclecloud.com"
        self.assertEqual(mock_client_instance.base_client.endpoint, expected_endpoint)

    @patch('exabox.exaoci.ExaOCIFactory.IdentityClient')
    def test_get_identity_client_success(self, mock_identity_client):
        """Test Identity client creation"""
        mock_client_instance = Mock()
        mock_client_instance.base_client = Mock()
        mock_client_instance.base_client.session = Mock()
        mock_identity_client.return_value = mock_client_instance
        
        self.mock_connector.get_auth_principal_token.return_value = Mock()
        
        result = self.factory.get_identity_client()
        
        mock_identity_client.assert_called_once_with(
            config={},
            signer=self.mock_connector.get_auth_principal_token.return_value,
            timeout=60,
            retry_strategy=unittest.mock.ANY
        )
        self.assertEqual(result, mock_client_instance)

    def test_get_oci_connector(self):
        """Test getting the OCI connector"""
        result = self.factory.get_oci_connector()
        self.assertEqual(result, self.mock_connector)

    def test_set_oci_connector(self):
        """Test setting a new OCI connector"""
        new_connector = Mock()
        self.factory.set_oci_connector(new_connector)
        self.assertEqual(self.factory.get_oci_connector(), new_connector)

    @patch('exabox.exaoci.ExaOCIFactory.ObjectStorageClient')
    def test_get_object_storage_client_with_resource_connector_r1(self, mock_osi_client):
        """Test ObjectStorage client creation with ResourceConnector for R1"""
        from exabox.exaoci.connectors.ResourceConnector import ResourceConnector
        
        mock_resource_connector = Mock(spec=ResourceConnector)
        mock_resource_connector.get_auth_principal_token.return_value = Mock()
        mock_resource_connector.get_oci_config.return_value = {
            "tenancy": "test-tenancy",
            "casper_endpoint": "https://test-casper.com",
            "ca_bundle_path": "/path/to/ca",
            "realm": "r1"
        }
        
        mock_client_instance = Mock()
        mock_osi_client.return_value = mock_client_instance
        
        result = self.factory.get_object_storage_client(mock_resource_connector)
        
        # Verify R1 specific call
        mock_osi_client.assert_called_once_with(
            config={"tenancy": "test-tenancy"},
            signer=mock_resource_connector.get_auth_principal_token.return_value,
            timeout=60,
            service_endpoint="https://test-casper.com",
            ca_bundle_path="/path/to/ca",
            retry_strategy=unittest.mock.ANY
        )

    @patch('exabox.exaoci.ExaOCIFactory.ObjectStorageClient')
    def test_get_object_storage_client_with_resource_connector_non_r1(self, mock_osi_client):
        """Test ObjectStorage client creation with ResourceConnector for non-R1"""
        from exabox.exaoci.connectors.ResourceConnector import ResourceConnector
        
        mock_resource_connector = Mock(spec=ResourceConnector)
        mock_resource_connector.get_auth_principal_token.return_value = Mock()
        mock_resource_connector.get_oci_config.return_value = {
            "tenancy": "test-tenancy",
            "casper_endpoint": "https://test-casper.com",
            "ca_bundle_path": "/path/to/ca",
            "realm": "oc1"
        }
        
        mock_client_instance = Mock()
        mock_osi_client.return_value = mock_client_instance
        
        result = self.factory.get_object_storage_client(mock_resource_connector)
        
        # Verify non-R1 specific call (no ca_bundle_path)
        mock_osi_client.assert_called_once_with(
            config={"tenancy": "test-tenancy"},
            signer=mock_resource_connector.get_auth_principal_token.return_value,
            timeout=60,
            service_endpoint="https://test-casper.com",
            retry_strategy=unittest.mock.ANY
        )

    @patch('exabox.exaoci.ExaOCIFactory.ObjectStorageClient')
    def test_get_object_storage_client_with_user_connector(self, mock_osi_client):
        """Test ObjectStorage client creation with UserConnector"""
        from exabox.exaoci.connectors.UserConnector import UserConnector
        
        mock_user_connector = Mock(spec=UserConnector)
        mock_user_connector.get_auth_principal_token.return_value = Mock()
        mock_user_connector.get_oci_config.return_value = {
            "region": "us-ashburn-1",
            "tenancy": "test-tenancy"
        }
        
        mock_client_instance = Mock()
        mock_osi_client.return_value = mock_client_instance
        
        result = self.factory.get_object_storage_client(mock_user_connector)
        
        mock_osi_client.assert_called_once_with(
            config=mock_user_connector.get_oci_config.return_value,
            signer=mock_user_connector.get_auth_principal_token.return_value,
            timeout=60,
            retry_strategy=unittest.mock.ANY
        )

    def test_factory_str_representation(self):
        """Test string representation of factory"""
        self.mock_connector.get_connector_type.return_value = "TestConnector"
        result = str(self.factory)
        self.assertEqual(result, "<ExaOCIFactory type='TestConnector()'>")


class TestExaOCIFactoryEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.mock_connector = Mock()
        self.factory = ExaOCIFactory(self.mock_connector)

    @patch('exabox.exaoci.ExaOCIFactory.ObjectStorageClient')
    def test_client_creation_exception_handling(self, mock_osi_client):
        """Test exception handling during client creation"""
        from exabox.core.Error import ExacloudRuntimeError
        
        # Simulate exception during client creation
        mock_osi_client.side_effect = Exception("Connection failed")
        self.mock_connector.get_auth_principal_token.return_value = None
        
        with self.assertRaises(ExacloudRuntimeError):
            self.factory.get_object_storage_client()

    @patch('exabox.exaoci.ExaOCIFactory.VirtualNetworkClient')
    def test_virtual_network_client_no_signer(self, mock_vn_client):
        """Test VirtualNetwork client creation fails when no signer available"""
        from exabox.core.Error import ExacloudRuntimeError
        
        self.mock_connector.get_auth_principal_token.return_value = None
        
        with self.assertRaises(ExacloudRuntimeError):
            self.factory.get_virtual_network_client()

    @patch('exabox.exaoci.ExaOCIFactory.ComputeClient')
    def test_compute_client_no_signer(self, mock_compute_client):
        """Test Compute client creation fails when no signer available"""
        from exabox.core.Error import ExacloudRuntimeError
        
        self.mock_connector.get_auth_principal_token.return_value = None
        
        with self.assertRaises(ExacloudRuntimeError):
            self.factory.get_compute_client()

if __name__ == '__main__':
    unittest.main()
