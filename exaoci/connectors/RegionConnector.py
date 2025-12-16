#!/bin/python
#
# $Header: ecs/exacloud/exabox/exaoci/connectors/RegionConnector.py /main/4 2025/11/21 03:51:00 bhpati Exp $
#
# RegionConnection.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      RegionConnection.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    bhpati      11/18/25 - Bug 38477046 - AIM4ECS:0X03010055 - Displaying the
#                           exception message
#    aypaul      08/11/23 - Bug#35685390 Use OCI default retry strategy for OCI
#                           connections.
#    ndesanto    06/27/22 - Exacloud OCI connection factory.
#    ndesanto    04/13/22 - Creation
#

from time import sleep
from oci.retry import DEFAULT_RETRY_STRATEGY
from exabox.core.Error import ExacloudRuntimeError
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError

from oci.auth.signers import InstancePrincipalsSecurityTokenSigner


class RegionConnector(OCIConnector):

    def __init__(self, aOCIRegion: str, aOCIDomain: str) -> None:
        OCIConnector.__init__(self)
        self.__oci_region = aOCIRegion
        self.__oci_domain = aOCIDomain
        
    def get_connector_type(self) -> str:
        return "RegionConnector"

    def get_auth_principal_token(self) -> InstancePrincipalsSecurityTokenSigner:
        _exception_msg = None
        _federationEndpoint = f"https://auth.{self.__oci_region}.{self.__oci_domain}/v1/x509"
        for _ in range(self.retries):
            try:
                return InstancePrincipalsSecurityTokenSigner(
                        federation_endpoint=_federationEndpoint,
                        federation_client_retry_strategy=DEFAULT_RETRY_STRATEGY)
            except Exception as e:
                _exception_msg = e
                ebLogTrace(f"Instance Principal signer creation failed: {_exception_msg} Retrying...")
                sleep(self.delay)
                self.delay *= self.backoff
                continue
        else:
            _err_msg = ("OCI Error during Instance Principals creation. "
                        f"{_exception_msg}. Please retry operation")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg

    def get_region(self) -> str:
        return self.__oci_region

    def get_domain(self) -> str:
        return self.__oci_domain
