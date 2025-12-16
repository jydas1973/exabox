#!/bin/python
#
# $Header: ecs/exacloud/exabox/exaoci/connectors/OCIConnector.py /main/3 2023/08/14 09:52:11 aypaul Exp $
#
# OCIConnector.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      OCIConnector.py - <one-line expansion of the name>
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
#    ndesanto    05/04/22 - Creation
#


from oci.auth.signers import InstancePrincipalsSecurityTokenSigner


class OCIConnector:

    def __init__(self) -> None:
        self.retries = 5
        self.delay = 3
        self.backoff = 2

    def get_connector_type(self) -> str:
        raise NotImplementedError

    def get_auth_principal_token(self) -> InstancePrincipalsSecurityTokenSigner:
        raise NotImplementedError