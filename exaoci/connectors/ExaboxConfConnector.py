#!/bin/python
#
# $Header: ecs/exacloud/exabox/exaoci/connectors/ExaboxConfConnector.py /main/3 2023/08/14 09:52:11 aypaul Exp $
#
# ExaboxConfConnection.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ExaboxConfConnection.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      08/11/23 - Bug#35685390 Use OCI default retry strategy for OCI
#                           connections.
#    ndesanto    06/27/22 - Exacloud OCI connection factory
#    ndesanto    04/13/22 - Creation
#

from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
from time import sleep
from oci.retry import DEFAULT_RETRY_STRATEGY
from exabox.core.Error import ExacloudRuntimeError
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError
from exabox.utils.ExaRegion import get_canonical_region_name


class ExaboxConfConnector(OCIConnector):

    def __init__(self, aCertPath: str, aServiceDomain: str) -> None:
        OCIConnector.__init__(self)
        self.__certificatePath = aCertPath
        self.__serviceDomain = aServiceDomain
        self.__regionName = get_canonical_region_name()

    def get_connector_type(self) -> str:
        return "ExaboxConfConnector"

    def get_auth_principal_token(self) -> InstancePrincipalsSecurityTokenSigner:
        _exception_msg = None
        _federationEndpoint = f"https://auth.{self.__regionName}.{self.__serviceDomain}/v1/x509"
        for _ in range(self.retries):
            try:
                return InstancePrincipalsSecurityTokenSigner(
                        federation_endpoint=_federationEndpoint,
                        federation_client_cert_bundle_verify=self.__certificatePath,
                        federation_client_retry_strategy=DEFAULT_RETRY_STRATEGY)
            except Exception as e:
                _exception_msg = e
                ebLogTrace(f"Instance Principal signer creation failed: {e} Retrying...")
                sleep(self.delay)
                self.delay *= self.backoff
                continue
        else:
            _err_msg = ("OCI Error during Instance Principals creation. "
                        f"{_exception_msg}. Please retry operation")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg

    def get_certificate_path(self) -> str:
        return self.__certificatePath

    def get_domain(self) -> str:
        return self.__serviceDomain

    def get_region(self) -> str:
        return self.__regionName
