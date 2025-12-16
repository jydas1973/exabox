#!/bin/python
#
# $Header: ecs/exacloud/exabox/exaoci/connectors/UserConnector.py /main/1 2023/02/22 08:35:07 pbellary Exp $
#
# UserConnector.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      UserConnector.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    12/08/22 - Creation
#
from time import sleep
import json
import os

from exabox.core.Error import ExacloudRuntimeError
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogTrace, ebLogError
from exabox.utils.oci_region import load_config_bundle
from exabox.utils.common import read_json_into_string, read_file_into_string
from exabox.config.Config import get_value_from_exabox_config

from oci.signer import Signer
from oci.config import from_file
from oci._vendor.requests.exceptions import HTTPError as OCIHTTPError

class UserConnector(OCIConnector):

    def __init__(self) -> None:
        self.__retries = 5
        self.__basepath: str = os.path.abspath(os.path.dirname(__file__) + "/../../..")
        self.__config_bundle = load_config_bundle()
        self.__realm = self.mObtainRealm()
        _tenancy = self.__config_bundle.get('monitoringConfig').get('monitoringTenancyOcid')
        _user = self.__config_bundle.get('monitoringConfig').get('monitoringUserOcid')
        _region = self.__config_bundle.get('monitoringConfig').get('region')
        _fingerprint = read_file_into_string(self.mGetConfigOption("user_principals_fingerprint"))
        _key_file = read_file_into_string(self.mGetConfigOption("user_principals_key_file"))

        # generate config info from signer with region and tenancy_id
        _config = {
            "tenancy": _tenancy,
            "user": _user,
            "fingerprint": _fingerprint,
            "key_file": _key_file,
            "region": _region
        }
        self.set_cloud_env()
        self.__config_file = _config

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

    def get_connector_type(self) -> str:
        return "UserConnector"

    def mGetConfigOption(self, aOption):
        return get_value_from_exabox_config(aOption, os.path.join(self.__basepath, "config/exabox.conf"))

    def get_auth_principal_token(self) -> Signer:
        _tenancy = self.__config_file.get("tenancy")
        _user = self.__config_file.get("user")
        _fingerprint = self.__config_file.get("fingerprint")

        _exception_msg = None
        for _ in range(self.__retries):
            try:
                # get signer from user principals
                return Signer(
                    tenancy=_tenancy,
                    user=_user,
                    fingerprint=_fingerprint,
                    private_key_file_location=self.mGetConfigOption("user_principals_key_file"))
            except OCIHTTPError as ociError:
                # If we get an OCI HTTP Error, it's possible that we are
                # in dev environment. re-raise and let each class act accordingly
                raise ociError
            except Exception as e:
                _exception_msg = e
                ebLogTrace(f'User Principal signer creation failed: {e} Retrying...')
                sleep(1)
                continue
        else:
            _err_msg = ('OCI Error during User Principals creation. '
                        f'{_exception_msg}. Please retry operation')
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from _exception_msg

    def get_oci_config(self) -> dict:
        return self.__config_file

    def set_cloud_env(self):
        _proxy = self.__config_bundle.get('corporateProxy')

        # set proxy if needed
        if _proxy is not None or _proxy != "" or _proxy != "null":
            os.environ["HTTPS_PROXY"] = "{}".format(_proxy)

        _ca_path = os.path.join(self.__basepath, "exabox/kms/combined_r1.crt")
        if self.__realm == "r1":
            os.environ["REQUESTS_CA_BUNDLE"] = _ca_path