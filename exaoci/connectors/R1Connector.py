#!/bin/python
#
# $Header: ecs/exacloud/exabox/exaoci/connectors/R1Connector.py /main/3 2023/08/14 09:52:11 aypaul Exp $
#
# R1Connection.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      R1Connection.py - <one-line expansion of the name>
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
#    ndesanto    06/27/22 - Exacloud OCI connection factory.
#    ndesanto    04/13/22 - Creation
#


import os
import sys

from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
from time import sleep
from oci.retry import DEFAULT_RETRY_STRATEGY
from exabox.core.Error import ExacloudRuntimeError
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError


class R1Connector(OCIConnector):

    def __init__(self) -> None:
        OCIConnector.__init__(self)
        _exacloudPath = os.path.abspath(sys.argv[0])
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]
        self.__r1Cert = f'{_exacloudPath}/exabox/kms/combined_r1.crt'

    def get_connector_type(self) -> str:
        return "R1Connector"

    def get_auth_principal_token(self) -> InstancePrincipalsSecurityTokenSigner:
        _exception_msg = None
        for _ in range(self.retries):
            try:
                return InstancePrincipalsSecurityTokenSigner(
                                federation_endpoint='https://auth.r1.oracleiaas.com/v1/x509',
                                federation_client_cert_bundle_verify=self.__r1Cert,
                                federation_client_retry_strategy=DEFAULT_RETRY_STRATEGY)

            except Exception as e:
                _exception_msg = e
                ebLogTrace(f'Instance Principal signer creation failed: {e}. Retrying...')
                sleep(self.delay)
                self.delay *= self.backoff
                continue
        else:
            _err_msg = ('OCI Error during Instance Principals creation. '
                        f'{_exception_msg}. Please retry operation')
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg

    def get_certificate_path(self) -> str:
        return self.__r1Cert
