#!/bin/python
#
# $Header: ecs/exacloud/exabox/exaoci/connectors/DefaultConnector.py /main/3 2023/08/14 09:52:11 aypaul Exp $
#
# DefaultConnection.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      DefaultConnection.py - <one-line expansion of the name>
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


from time import sleep

from exabox.core.Error import ExacloudRuntimeError
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError
from oci.retry import DEFAULT_RETRY_STRATEGY
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
from oci._vendor.requests.exceptions import HTTPError as OCIHTTPError


class DefaultConnector(OCIConnector):

    def __init__(self) -> None:
        OCIConnector.__init__(self)

    def get_connector_type(self) -> str:
        return "DefaultConnector"

    def get_auth_principal_token(self) -> InstancePrincipalsSecurityTokenSigner:
        _exception_msg = None
        for _ in range(self.retries):
            try:
                # This search OCI default locations for region information (e.g. ~/.oci/)
                return InstancePrincipalsSecurityTokenSigner(federation_client_retry_strategy=DEFAULT_RETRY_STRATEGY)
            except OCIHTTPError as ociError:
                # If we get an OCI HTTP Error, it's possible that we are
                # in dev environment. re-raise and let each class act accordingly
                raise ociError
            except Exception as e:
                _exception_msg = e
                ebLogTrace(f'Instance Principal signer creation failed: {e} Retrying...')
                sleep(self.delay)
                self.delay *= self.backoff
                continue
        else:
            _err_msg = ('OCI Error during Instance Principals creation. '
                        f'{_exception_msg}. Please retry operation')
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg
