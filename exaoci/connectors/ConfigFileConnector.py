#!/bin/python
#
# $Header: ecs/exacloud/exabox/exaoci/connectors/ConfigFileConnector.py /main/3 2023/06/12 15:57:13 jfsaldan Exp $
#
# ConfigFileConnector.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ConfigFileConnector.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    04/26/23 - Enh 35207526 - Adding support in
#                           ConfigFileConnector to receive a config dict in the
#                           constructor
#    ndesanto    06/27/22 - Exacloud OCI connection factory.
#    ndesanto    04/13/22 - Creation
#


from time import sleep

from oci.config import from_file, validate_config

from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError

from oci.auth.signers import InstancePrincipalsSecurityTokenSigner


class ConfigFileConnector(OCIConnector):

    def __init__(self, aConfigFile, aConfigDict=None) -> None:
        """
        :param aConfigFile: a string representing the path of a Config File
        :param aConfigDict[Optional]: a dictionary representing the
            Configuration File. If present, we will try to use it before
            trying with aConfigFile
        """
        _config = None

        if aConfigDict:
            try:
                validate_config(aConfigDict)
            except Exception as e:
                ebLogError("Error on ConfigFileConnector aConfigDict check. "
                    f"We'll try to use aConfigFile. Error: '{e}'")
            else:
                ebLogTrace("ConfigFileConnector using config dictionary")
                _config = aConfigDict

        # Try with aConfigFile if aConfigDict didn't work or wasn't given
        if _config is None:
            try:
                ebLogTrace("ConfigFileConnector using config file")
                _config = from_file(file_location=aConfigFile)
            except:
                # in case the from_file function fails return and empty
                # dictionary
                _config = {}
        self.__config_file = _config

    def get_connector_type(self) -> str:
        return "ConfigFileConnector"

    def get_auth_principal_token(self) -> InstancePrincipalsSecurityTokenSigner:
        raise NotImplementedError(f"{self.__class__.__name__} does not return a "\
            "InstancePrincipalsSecurityTokenSigner, instead it uses a config file "
            "to create OCI clients. For more details check "
            "https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/configuration.html")

    def get_oci_config(self) -> dict:
        return self.__config_file
