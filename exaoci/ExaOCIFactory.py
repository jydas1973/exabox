#!/bin/python
#
# $Header: ecs/exacloud/exabox/exaoci/ExaOCIFactory.py /main/10 2025/08/05 07:01:28 kkviswan Exp $
#
# ExaOCIConnectionFactory.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      ExaOCIConnectionFactory.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    kkviswan    07/23/25 - 38225214 - DELEGATION MANAGEMENT BACKEND
#                           INTEGRATION ISSUES ON EXADB-XS ENVIRONMENT
#    ririgoye    10/04/24 - Bug 37085291 - Move compute and virtual network
#                           clients to ExaOCIFactory
#    jfsaldan    08/17/23 - Enh 35692408 - EXACLOUD - VMBOSS - CREATE A FLAG IN
#                           EXABOX.CONF THAT TOGGLES BETWEEN INSTANCE
#                           PRINCIPALS AND USERS PRINCIPALS FOR VMBACKUP TO OSS
#                           MODULE
#    jfsaldan    02/23/23 - Enh 34965441 - EXACLOUD TO SUPPORT NEW TASK FOR
#                           GOLD IMAGE BACKUP
#    ndesanto    06/27/22 - Exacloud OCI connection factory.
#    ndesanto    04/13/22 - Creation
#


import sys
from oci.core import VirtualNetworkClient, ComputeClient
from oci.key_management import KmsCryptoClient
from oci.object_storage import ObjectStorageClient
from oci.secrets import SecretsClient
from oci.vault import VaultsClient
from oci.identity import IdentityClient
from oci.retry import DEFAULT_RETRY_STRATEGY
from oci._vendor.requests.exceptions import HTTPError as OCIHTTPError

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.exaoci.connectors.ConfigFileConnector import ConfigFileConnector
from exabox.exaoci.connectors.ExaboxConfConnector import ExaboxConfConnector
from exabox.exaoci.connectors.DefaultConnector import DefaultConnector
from exabox.exaoci.connectors.ResourceConnector import ResourceConnector
from exabox.exaoci.connectors.UserConnector import UserConnector
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.exaoci.connectors.R1Connector import R1Connector
from exabox.exaoci.connectors.RegionConnector import RegionConnector
from exabox.utils.ExaRegion import is_r1_region, get_r1_certificate_path
from exabox.utils.oci_region import load_oci_region_config, get_value
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError


class ExaOCIFactory:
    """Class used to Exacloud's OCI related objects and clients

    Non instanciable class.
    
    This class is a container of class methods (similar to static)
    that help with obtaining OCI related objects using the Exacloud
    configurations, such as R1, exabox.conf, regions, OCI SDK default,
    from configuration file.

    Methods
    -------
    _get_connector(self) -> OCIConnector
        Returns an OCIConnector that is an implementation of Exaclouds
        rules to connects to OCI, this object is required to obtain OCI
        clients.
    
    get_oci_connector(self) -> OCIConnector
        Retrieve the Factory connector.
    
    set_oci_connector(self, aConnector: OCIConnector) -> OCIConnector
        Set the connector for the Factory.
    
    get_object_storage_client(self, aConnector: OCIConnector=None) -> ObjectStorageClient
        Returns an OCI ObjectStorageClient from the provided OCIConnector.

    get_crypto_client(self, aCrytpoEndpoint: str, aConnector: OCIConnector=None) -> KmsCryptoClient
        Returns an OCI KmsCryptoClient from the provided OCIConnector.

    get_secrets_client(self, aConnector: OCIConnector=None) -> SecretsClient
        Returns an OCI SecretsClient from the provided OCIConnector.

    get_vault_client(self, aConnector: OCIConnector=None) -> VaultsClient
        Returns an OCI VaultsClient from the provided OCIConnector.

    get_identity_client(self, aConnector: OCIConnector=None) -> IdentityClient
        Returns an OCI IdentityClient from the provided OCIConnector.
    """
    def __init__(self, aConnector: OCIConnector=None) -> None:
        if aConnector:
            self.__oci_connector = aConnector
        else:
            self.__oci_connector = self._get_connector()

    def __str__(self) -> str:
        return f"<ExaOCIFactory type='{self.__oci_connector.get_connector_type()}()'>"

    def get_oci_connector(self) -> OCIConnector:
        return self.__oci_connector

    def set_oci_connector(self, aConnector: OCIConnector):
        self.__oci_connector = aConnector

    def _get_connector(self) -> OCIConnector:
        """ Returns an OCIConnector that has the logic to connect to OCI

        There 5 types of OCICoonectors:
            1) R1Connector
            2) ExaboxConfConnector
            3) ConfigFileConnector
            4) RegionConnector
            5) DefaultConnector
            6) ResourceConnector
            7) UserConnector
        """
        _err_str = "Failed to instantiate an OCI connector."
        # if SEA (Seattle) region then we're in R1
        # R1 is checked first since this code is a special flow
        if is_r1_region():
            return R1Connector()

        # if certificate path and service domain are present in the exabox.conf then
        # use them to create the InstancePrincipalsSecurityTokenSigner
        # This option was added for testing and to override regions, so is checekd second.
        _certificatePath = get_gcontext().mCheckConfigOption("oci_certificate_path")
        _serviceDomain = get_gcontext().mCheckConfigOption("oci_service_domain")
        if _certificatePath and _serviceDomain:
            return ExaboxConfConnector(_certificatePath, _serviceDomain)

        # if an Exabox configuration file is present use it.
        # This is only used for unit testing.
        _cfg_file = get_gcontext().mCheckConfigOption('exakms_oci_config_file')
        if _cfg_file:
            return ConfigFileConnector(_cfg_file)

        # if Region configuration is present use it
        # This option is the main mode, since ECRA will pass this information to Exacloud when starting it
        try:
            _ociRegionConfig = load_oci_region_config()
            _oci_region = get_value(_ociRegionConfig, "regionIdentifier")
            _oci_domain = get_value(_ociRegionConfig, "realmDomainComponent")
            if len(_ociRegionConfig):
                return RegionConnector(_oci_region, _oci_domain)
        except Exception as e:
            _err_str = f"Failed to load OCI region configuration with Exception:\n\n{e}"
            ebLogTrace(_err_str)

        # Default configuration OCI connector
        # This connector uses the default OCI SDK logic to look for region 
        # configuration, we're not meant to reach this point in most cases
        # but is kept for compatibility
        try:
            ebLogTrace("Trying to create an OCI Default connector.")
            return DefaultConnector()
        except OCIHTTPError as e:
            _err_str = f"Failed to create OCI Default Connector with Exception:\n\n{e}"
            ebLogTrace(_err_str)

        # We should not reach this point but if we do we break execution
        raise ExacloudRuntimeError(0x0780, 0x09001, _err_str)

    def get_object_storage_client(self, aConnector: OCIConnector=None) -> ObjectStorageClient:
        """Returns an OCI Object Storage client from the OCIConnector
        """
        if not aConnector:
            aConnector = self.get_oci_connector()

        _object_storage = None
        # In case of a ConfigFileConnector the OCI client is create using the
        # configurations on a file
        if isinstance(aConnector, ConfigFileConnector):
            _config = aConnector.get_oci_config()
            try:
                _object_storage = ObjectStorageClient(
                                    config=_config, timeout=60,
                                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            except Exception as e:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                        f'Otherwise, please retry operation: {e}')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg) from e

            # If the ConfigFile belongs to R1, we need to also override the
            # client's certificate and service endpoint
            if _config.get("region") == "us-seattle-1":
                _object_storage.base_client.session.verify = \
                        get_r1_certificate_path()
                _object_storage.base_client.endpoint = \
                        "https://objectstorage.r1.oracleiaas.com"

        elif isinstance(aConnector, UserConnector):
            _signer = aConnector.get_auth_principal_token()
            _config = aConnector.get_oci_config()
            try:
                _object_storage = ObjectStorageClient(
                                    config=_config, signer=_signer, timeout=60,
                                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            except Exception as e:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                        f'Otherwise, please retry operation: {e}')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg) from e
        elif isinstance(aConnector, ResourceConnector):
            _signer = aConnector.get_auth_principal_token()
            _config = aConnector.get_oci_config()
            try:
                _tenancy = _config.get("tenancy")
                _casper = _config.get("casper_endpoint")
                _ca_path = _config.get("ca_bundle_path")
                _realm = _config.get("realm")
                if _realm == "r1":
                    _object_storage = ObjectStorageClient(config={"tenancy": _tenancy},
                                        signer=_signer, timeout=60, service_endpoint=_casper,
                                        ca_bundle_path=_ca_path, retry_strategy=DEFAULT_RETRY_STRATEGY)
                else:
                    _object_storage = ObjectStorageClient(config={"tenancy": _tenancy}, 
                                        signer=_signer, timeout=60, service_endpoint=_casper, 
                                        retry_strategy=DEFAULT_RETRY_STRATEGY)

            except Exception as e:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                        f'Otherwise, please retry operation: {e}')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg) from e
        else:
            #  For all other connectors an Instance/Resource principal token is needed
            # to create OCI clients
            _signer = aConnector.get_auth_principal_token()

            if _signer:
                _object_storage = ObjectStorageClient(
                    config={}, signer=_signer, timeout=60,
                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            else:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                            'Otherwise, please retry operation.')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

        # For R1 and exabox.conf set the certificate path for the Object Storage client
        if isinstance(aConnector, R1Connector) or \
            isinstance(aConnector, ExaboxConfConnector):
            _object_storage.base_client.session.verify = aConnector.get_certificate_path()

        #  Set the Object Storage client endpoint url, for R1 this url is static
        # for exabox.conf and region the url is constructed from the region and domain
        if isinstance(aConnector, R1Connector):
            _object_storage.base_client.endpoint = "https://objectstorage.r1.oracleiaas.com"
        elif isinstance(aConnector, ExaboxConfConnector) or \
            isinstance(aConnector, RegionConnector):
            _oci_region = aConnector.get_region()
            _oci_domain = aConnector.get_domain()
            _object_storage.base_client.endpoint = f'https://objectstorage.{_oci_region}.{_oci_domain}'

        return _object_storage

    def get_virtual_network_client(self, aConnector=None):
        if not aConnector:
            aConnector = self.get_oci_connector()

        _virtual_network_client = None

        #  In case of a ConfigFileConnector the OCI client is create using the 
        # configurations on a file
        if isinstance(aConnector, ConfigFileConnector):
            _config = aConnector.get_oci_config()
            try:
                _virtual_network_client = VirtualNetworkClient(
                                    config=_config, timeout=60,
                                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            except Exception as e:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                        f'Otherwise, please retry operation: {e}')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

            if _config.get("region") == "us-seattle-1":
                _virtual_network_client.base_client.session.verify = aConnector.get_certificate_path()
                _virtual_network_client.base_client.endpoint = "https://iaas.r1.oracleiaas.com"
        else:
            _signer = aConnector.get_auth_principal_token()

            if _signer:
                _virtual_network_client = VirtualNetworkClient(
                    config={}, 
                    signer=_signer, 
                    timeout=60,
                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            else:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                            'Otherwise, please retry operation.')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)
        
        # For R1 and OCICertificateAndServiceDomainConnector set the certificate path for the Object Storage client
        if isinstance(aConnector, R1Connector) or \
            isinstance(aConnector, ExaboxConfConnector) or \
            isinstance(aConnector, ConfigFileConnector):
            _virtual_network_client.base_client.session.verify = aConnector.get_certificate_path()

        #  Set the Object Storage client endpoint url, for R1 this url is static
        # for OCICertificateAndServiceDomainConnector region the url is constructed from the region and domain
        if isinstance(aConnector, R1Connector) or \
           isinstance(aConnector, ConfigFileConnector):
            _virtual_network_client.base_client.endpoint = 'https://iaas.r1.oracleiaas.com'
        elif isinstance(aConnector, ExaboxConfConnector) or \
            isinstance(aConnector, RegionConnector):
            _oci_region = aConnector.get_region()
            _oci_domain = aConnector.get_domain()
            _virtual_network_client.base_client.endpoint = f'https://iaas.{_oci_region}.{_oci_domain}'

        return _virtual_network_client
    
    def get_compute_client(self, aConnector=None):
        if not aConnector:
            aConnector = self.get_oci_connector()

        _compute_client = None

        #  In case of a ConfigFileConnector the OCI client is create using the 
        # configurations on a file
        if isinstance(aConnector, ConfigFileConnector):
            _config = aConnector.get_oci_config()
            try:
                _compute_client = ComputeClient(
                                    config=_config, 
                                    timeout=60,
                                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            except Exception as e:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                        f'Otherwise, please retry operation: {e}')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

            if _config.get("region") == "us-seattle-1":
                _compute_client.base_client.session.verify = aConnector.get_certificate_path()
                _compute_client.base_client.endpoint = "https://iaas.r1.oracleiaas.com"
        else:
            _signer = aConnector.get_auth_principal_token()

            if _signer:
                _compute_client = ComputeClient(
                    config={}, 
                    signer=_signer, 
                    timeout=60,
                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            else:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                            'Otherwise, please retry operation.')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)
        
        # For R1 and OCICertificateAndServiceDomainConnector set the certificate path for the Object Storage client
        if isinstance(aConnector, R1Connector) or \
            isinstance(aConnector, ExaboxConfConnector) or \
            isinstance(aConnector, ConfigFileConnector):
            _compute_client.base_client.session.verify = aConnector.get_certificate_path()

        #  Set the Object Storage client endpoint url, for R1 this url is static
        # for OCICertificateAndServiceDomainConnector region the url is constructed from the region and domain
        if isinstance(aConnector, R1Connector) or \
           isinstance(aConnector, ConfigFileConnector):
            _compute_client.base_client.endpoint = 'https://iaas.r1.oracleiaas.com'
        elif isinstance(aConnector, ExaboxConfConnector) or \
            isinstance(aConnector, RegionConnector):
            _oci_region = aConnector.get_region()
            _oci_domain = aConnector.get_domain()
            _compute_client.base_client.endpoint = f'https://iaas.{_oci_region}.{_oci_domain}'

        return _compute_client

    def get_crypto_client(self, aCrytpoEndpoint: str, aConnector: OCIConnector=None) -> KmsCryptoClient:
        """Returns an OCI Crypto client from an OCIConnector
        """
        if not aConnector:
            aConnector = self.get_oci_connector()

        _kms_crypto_client = None
        # In case of a ConfigFileConnector the client is created using a file
        if isinstance(aConnector, ConfigFileConnector):
            _config = aConnector.get_oci_config()
            _kms_crypto_client = KmsCryptoClient(config=_config,
                                     service_endpoint=aCrytpoEndpoint, timeout=60,
                                     retry_strategy=DEFAULT_RETRY_STRATEGY)

        else:
            #  For all other connectors an Intace Principal token is needed
            # to create OCI clients
            _signer = aConnector.get_auth_principal_token()

            if _signer:
                _kms_crypto_client = KmsCryptoClient(config={}, signer=_signer,
                                        service_endpoint=aCrytpoEndpoint, timeout=60,
                                        retry_strategy=DEFAULT_RETRY_STRATEGY)
            else:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                            'Otherwise, please retry operation.')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

        # For R1 and exabox.conf set the certificate path for the Crypto client
        if isinstance(aConnector, R1Connector) or \
            isinstance(aConnector, ExaboxConfConnector):
            _kms_crypto_client.base_client.session.verify = aConnector.get_certificate_path()

        return _kms_crypto_client

    def get_vault_client(self, aConnector: OCIConnector=None) -> VaultsClient:
        """Returns an OCI Vault client from an OCIConnector
        """
        _vault_client = None
        if not aConnector:
            aConnector = self.get_oci_connector()

        #  In case of a ConfigFileConnector the OCI client is created using the 
        # configurations from a configuration file
        if isinstance(aConnector, ConfigFileConnector):
            _config = aConnector.get_oci_config()
            try:
                _vault_client = VaultsClient(config=_config, timeout=60, 
                        retry_strategy=DEFAULT_RETRY_STRATEGY)
                        # service_endpoint = "https://vaults.r1.oci.oracleiaas.com")
            except Exception as e:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                        f'Otherwise, please retry operation: {e}')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg) from e

            # If the ConfigFile belongs to R1, we need to also override the
            # client's certificate and service endpoint
            if _config.get("region") == "us-seattle-1":
                _vault_client.base_client.session.verify = \
                        get_r1_certificate_path()
                _vault_client.base_client.endpoint = \
                        "https://vaults.r1.oci.oracleiaas.com"

        else:
            #  For all other connectors an Intace Principal token is needed
            # to create OCI clients
            _signer = aConnector.get_auth_principal_token()

            if _signer:
                _vault_client = VaultsClient(
                    config={}, signer=_signer, timeout=60, 
                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            else:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                            'Otherwise, please retry operation.')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

        # For R1 and exabox.conf set the certificate path for the Object Storage client
        if isinstance(aConnector, R1Connector) or \
            isinstance(aConnector, ExaboxConfConnector):
            _vault_client.base_client.session.verify = aConnector.get_certificate_path()

        #  Set the vault client endpoint url, for R1 this url is static
        # for exabox.conf and region the url is constructed from the region and domain
        if isinstance(aConnector, R1Connector):
            _vault_client.base_client.endpoint = "https://vaults.r1.oci.oracleiaas.com"
        elif isinstance(aConnector, ExaboxConfConnector) or \
            isinstance(aConnector, RegionConnector):
            _oci_region = aConnector.get_region()
            _oci_domain = aConnector.get_domain()
            _vault_client.base_client.endpoint = f'https://vaults.{_oci_region}.{_oci_domain}'

        return _vault_client

    def get_secrets_client(self, aConnector: OCIConnector=None) -> SecretsClient:
        """Returns an OCI Secrects client from an OCIConnector
        """
        _secrets_client = None
        if not aConnector:
            aConnector = self.get_oci_connector()

        #  In case of a ConfigFileConnector the OCI client is created using the 
        # configurations from a configuration file
        if isinstance(aConnector, ConfigFileConnector):
            _config = aConnector.get_oci_config()
            try:
                _secrets_client = SecretsClient(config=_config, timeout=60, 
                        retry_strategy=DEFAULT_RETRY_STRATEGY)
            except Exception as e:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                        f'Otherwise, please retry operation: {e}')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg) from e

            # If the ConfigFile belongs to R1, we need to also override the
            # client's certificate and service endpoint
            if _config.get("region") == "us-seattle-1":
                _secrets_client.base_client.session.verify = \
                        get_r1_certificate_path()
                _secrets_client.base_client.endpoint = \
                        "https://secrets.vaults.r1.oci.oracleiaas.com"

        else:
            #  For all other connectors an Intace Principal token is needed
            # to create OCI clients
            _signer = aConnector.get_auth_principal_token()

            if _signer:
                _secrets_client = SecretsClient(
                    config={}, signer=_signer, timeout=60, 
                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            else:
                _err_msg = ('Could not create a signer and config file not found. '
                            'If in dev environment, please use a config file. '
                            'Otherwise, please retry operation.')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

        # For R1 and exabox.conf set the certificate path for the Object Storage client
        if isinstance(aConnector, R1Connector) or \
            isinstance(aConnector, ExaboxConfConnector):
            _secrets_client.base_client.session.verify = aConnector.get_certificate_path()

        #  Set the secrets client endpoint url, for R1 this url is static
        # for exabox.conf and region the url is constructed from the region and domain
        if isinstance(aConnector, R1Connector):
            _secrets_client.base_client.endpoint = "https://secrets.vaults.r1.oci.oracleiaas.com"
        elif isinstance(aConnector, ExaboxConfConnector) or \
            isinstance(aConnector, RegionConnector):
            _oci_region = aConnector.get_region()
            _oci_domain = aConnector.get_domain()
            _secrets_client.base_client.endpoint = f'https://secrets.vaults.{_oci_region}.oci.{_oci_domain}'

        return _secrets_client

    def get_identity_client(self, aConnector: OCIConnector=None) -> IdentityClient:
        """Returns an OCI Identity client from an OCIConnector
        """
        _identity_client = None
        if not aConnector:
            aConnector = self.get_oci_connector()

        # In case of a ConfigFileConnector the OCI client is created using the
        # credentials from a configuration file
        if isinstance(aConnector, ConfigFileConnector):
            _config = aConnector.get_oci_config()
            try:
                _identity_client = IdentityClient(config=_config, timeout=60,
                        retry_strategy=DEFAULT_RETRY_STRATEGY)
            except Exception as e:
                _err_msg = ('Could not create a signer and config file not found. '
                            'Identity Client creation failure'
                            'If in dev environment, please use a config file. '
                        f'Otherwise, please retry operation: {e}')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg) from e

            # If the ConfigFile belongs to R1, we need to also override the
            # client's certificate and service endpoint
            if _config.get("region") == "us-seattle-1":
                _identity_client.base_client.session.verify = \
                        get_r1_certificate_path()
                _identity_client.base_client.endpoint = \
                        "https://identity.r1.oci.oracleiaas.com"

        else:
            #  For all other connectors an Intace Principal token is needed
            # to create OCI clients
            _signer = aConnector.get_auth_principal_token()

            if _signer:
                _identity_client = IdentityClient(
                    config={}, signer=_signer, timeout=60,
                    retry_strategy=DEFAULT_RETRY_STRATEGY)
            else:
                _err_msg = ('Could not create a signer and config file not found. '
                            'Identity Client creation failure'
                            'If in dev environment, please use a config file. '
                            'Otherwise, please retry operation.')
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

        # For R1 and exabox.conf set the certificate path for the Object Storage client
        if isinstance(aConnector, R1Connector) or \
            isinstance(aConnector, ExaboxConfConnector):
            _identity_client.base_client.session.verify = aConnector.get_certificate_path()

        #  Set the identity client endpoint url, for R1 this url is static
        # for exabox.conf and region the url is constructed from the region and domain
        if isinstance(aConnector, R1Connector):
            _identity_client.base_client.endpoint = "https://identity.r1.oci.oracleiaas.com"
        elif isinstance(aConnector, ExaboxConfConnector) or \
            isinstance(aConnector, RegionConnector):
            _oci_region = aConnector.get_region()
            _oci_domain = aConnector.get_domain()
            _identity_client.base_client.endpoint = f'https://identity.{_oci_region}.{_oci_domain}'

        return _identity_client
