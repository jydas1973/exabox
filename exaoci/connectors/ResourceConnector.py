#!/bin/python
#
# $Header: ecs/exacloud/exabox/exaoci/connectors/ResourceConnector.py /main/6 2025/08/01 04:35:11 asrigiri Exp $
#
# ResourceConnector.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      ResourceConnector.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    asrigiri    07/15/25 - Bug 38156507 - OCI: CREATEEXACCCONSOLEHIS FAILED AS PROXY IS SET TO NULL.
#    pbellary    05/03/25 - Bug 36909657 - EXACC GEN2: CREATE CONSOLE FAILS DUE TO WRONG REFERENCE OF PROXY FROM JSON FILE 
#    pbellary    22/12/23 - Bug 36124951 - CREATE CONSOLE HISTORY WF FAILED WHILE TRYING TO CONNECT PROXY ON NO PROXY INFRA
#    pbellary    28/11/23 - Bug 36025488 - EXACC:SERIAL CONSOLE: CONSOLE HISTORY CREATION IS FAILING 
#    pbellary    12/08/22 - Creation
#
from time import sleep
import json
import os
import glob

from exabox.core.Error import ExacloudRuntimeError
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError
from exabox.utils.oci_region import load_config_bundle
from exabox.utils.common import read_json_into_string, read_file_into_string
from exabox.config.Config import get_value_from_exabox_config

from oci.auth.signers import get_resource_principals_signer
from oci import regions
from oci._vendor.requests.exceptions import HTTPError as OCIHTTPError

class ResourceConnector(OCIConnector):

    def __init__(self) -> None:
        self.__retries = 5
        self.__basepath: str = os.path.abspath(os.path.dirname(__file__) + "/../../..")
        self.__config_bundle = load_config_bundle()
        self.__realm = self.mObtainRealm()
        self.__region = self.mObtainRegion()
        self.__dns_suffix = self.mObtainDnsSuffix()

        # constants
        # it is always database the RP provider
        self.__endpoint_service = "database"
        # it is always auth the RP auth
        self.__auth_service = "auth"
        self.__object_service = "object_storage"
        self.__dbaas_endpoint = self.mSetEndpoint(self.__endpoint_service)
        self.__auth_endpoint = self.mSetEndpoint(self.__auth_service)
        self.__casper_endpoint = self.mSetEndpoint(self.__object_service)

    def mObtainRealm(self):
        _realm = None

        if self.__config_bundle.get("realmName"):
            _realm = self.__config_bundle.get("realmName")
            if _realm == "region1":
                return "r1"
        else:
            _exaOcid = self.__config_bundle.get("exaccInfrastructureOcid")
            _ocidComponents = _exaOcid.split(".")
            if len(_ocidComponents) > 3 and _ocidComponents[2] == "region1" and _ocidComponents[3] == "sea":
                return "r1"
            return _ocidComponents[2].strip()

    def mObtainRegion(self):
        if self.__realm == "r1":
            return "r1"
        _exaOcid = self.__config_bundle.get("exaccInfrastructureOcid")
        _ocidComponents = _exaOcid.split(".")
        if len(_ocidComponents) > 3:
            return regions.get_region_from_short_name(_ocidComponents[3].strip())
        else:
            _err_msg = f"Error in fetching region from exaccInfrastructureOcid:{_exaOcid}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg)

    def mObtainDnsSuffix(self):
        if self.__config_bundle.get("dnsSuffix"):
            return self.__config_bundle.get("dnsSuffix")
        else:
            if self.__realm == "r1":
                return "r1.oracleiaas.com"
            elif self.__realm == "oc4":
                return "{region}.oraclegovcloud.uk".format(region=self.__region)

        return "{region}.oci.oraclecloud.com".format(region=self.__region)

    def mSetEndpoint(self, service):
        _region = self.__region
        _endpoint_service = service

        if _region == "r1":
            if _endpoint_service == "object_storage":
                _url = "objectstorage"
            else:
                _url = _endpoint_service

            _endpoint = regions.endpoint_for(
                _endpoint_service,
                service_endpoint_template="https://{}.{}".format(_url, f"{_region}.oracleiaas.com"),
                region=_region,
                endpoint=None,
                endpoint_service_name=service)
        else:
            _endpoint = regions.endpoint_for(
                _endpoint_service,
                service_endpoint_template=None,
                region=_region,
                endpoint=None,
                endpoint_service_name=service)

        if service.lower() == "database":
            _databaseUrl = self.__config_bundle.get("databaseUrl")
            if _databaseUrl:
                if "preprod" in _databaseUrl:
                    if _databaseUrl.find("https://") != 0:
                        _endpoint = "https://" + _databaseUrl
                    else:
                        _endpoint = _databaseUrl
        return _endpoint

    def mGetConfigOption(self, aOption):
        return get_value_from_exabox_config(aOption, os.path.join(self.__basepath, "config/exabox.conf"))

    def mGetRPKey(self):
        return read_file_into_string(self.mGetConfigOption("resource_principals_key"))

    def mGetRPAuthEnv(self):
        _oxpa_json = read_json_into_string(self.mObtainOxpaFile())
        _ocps_setup_json = read_json_into_string(self.mObtainOcpsSetupFile())
        
        # Retrieve the 'proxy' value from the config
        _proxy_attr = _ocps_setup_json.get("proxy")

        # Strip the value only if it's a valid string; otherwise, set _proxy to None
        if isinstance(_proxy_attr, str):
           _proxy = _proxy_attr.strip()
        else:
           _proxy = None

        _tenancy = _oxpa_json.get('OciExaCapacityParam').get('tenantOcid')
        _resource_id = _oxpa_json.get('OciExaCapacityParam').get('exaOcid')

        # set proxy if needed
        if _proxy is not None and _proxy.lower() != "null" and _proxy.lower() != "none":
            os.environ["HTTPS_PROXY"] = "{}".format(_proxy)

        _key = self.mGetRPKey()
        _ca_path = os.path.join(self.__basepath, "exabox/kms/combined_r1.crt")

        os.environ["OCI_RESOURCE_PRINCIPAL_VERSION"] = self.mGetConfigOption("resource_principals_version")
        os.environ["OCI_RESOURCE_PRINCIPAL_RPT_ENDPOINT"] = self.__dbaas_endpoint
        os.environ["OCI_RESOURCE_PRINCIPAL_RPST_ENDPOINT"] = self.__auth_endpoint
        os.environ["OCI_RESOURCE_PRINCIPAL_RESOURCE_ID"] = _resource_id
        os.environ["OCI_RESOURCE_PRINCIPAL_TENANCY_ID"] = _tenancy
        os.environ["OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM"] = _key
        os.environ["OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM_PASSPHRASE"] = ""
        os.environ["OCI_RESOURCE_PRINCIPAL_REGION"] = self.__region
        if self.__realm == "r1":
            os.environ["REQUESTS_CA_BUNDLE"] = _ca_path

        _config = {
            "tenancy": _tenancy,
            "casper_endpoint": self.__casper_endpoint,
            "ca_bundle_path": _ca_path,
            "realm": self.__realm
        }
        self.__config_file = _config

        ebLogInfo("Getting signer V2.1.1")
        return get_resource_principals_signer()

    def mObtainOxpaFile(self):
        for _oxpa_file in glob.glob("/opt/oci/config_bundle/*-clu01/*-clu01.oxpaInput.json"):
            return _oxpa_file

        _err_msg = "oxpaInput.json file not found. Exiting"
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(aErrorMsg=_err_msg)

    def mObtainOcpsSetupFile(self):
        for _oxpa_file in glob.glob("/opt/oci/config_bundle/*-clu01.ocpsSetup.json"):
            return _oxpa_file

        _err_msg = "ocpsSetup.json file not found. Exiting"
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(aErrorMsg=_err_msg)

    def get_connector_type(self) -> str:
        return "ResourceConnector"

    def get_oci_config(self) -> dict:
        return self.__config_file

    def get_auth_principal_token(self) -> get_resource_principals_signer:
        _exception_msg = None
        for _ in range(self.__retries):
            try:
                return self.mGetRPAuthEnv()
            except OCIHTTPError as ociError:
                # If we get an OCI HTTP Error, it's possible that we are
                # in dev environment. re-raise and let each class act accordingly
                raise ociError
            except Exception as e:
                _exception_msg = e
                ebLogTrace(f'Resource Principal signer creation failed: {e} Retrying...')
                sleep(1)
                continue
        else:
            _err_msg = ('OCI Error during Resource Principals creation. '
                        f'{_exception_msg}. Please retry operation')
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg
