#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/vmboci.py /main/22 2025/05/12 14:45:29 abflores Exp $
#
# vmboci.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      vmboci.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      https://confluence.oraclecorp.com/confluence/display/EDCS/VMbackup+to+OSS+ECRA-Exacloud+communication
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    04/25/25 - Bug 37877334 - EXACLOUD VMBACKUP TO OSS PREVENT
#                           EXACSDBOPS-10887 | TERMINATION FAILS IF VMBACKUP TO
#                           OSS COMPARTMENT DOES NOT EXIST
#    abflores    04/24/25 - Bug 37668982 - CLUSTER TERMINATION IS FAILING IN 
#                           PREVMSETUP | VMBACKUP UNCOMMITED OBJECTS STILL 
#                           EXIST IN CLUSTER BUCKET 
#    jfsaldan    03/18/25 - Backport 37722595 of jfsaldan_bug-37655497 from
#                           main
#    ririgoye    09/04/24 - Backport 37024651 of ririgoye_bug-36746713 from
#                           main
#    apfwkr      08/29/24 - CI# 36991297 of jfsaldan_bug-36883357 from main
#                           (apfwkr_ci_backport_36883357_24.4.1.0.0ecsr).
#    jfsaldan    08/19/24 - Backport 36964820 of jfsaldan_bug-36932309 from
#                           main
#    jfsaldan    07/26/24 - Backport 36887606 of jfsaldan_bug-36860756 from
#                           main
#    ririgoye    08/27/24 - Enh 36746713 - EXACS VMBACKUP : EXACLOUD SHOULD
#                           HAVE A FEATURE FLAG TO USE MULTIPLE/ONE
#                           COMPARTMENTS FOR VM BACKUPS
#    jfsaldan    08/07/24 - Enh 36883357 - EXACLOUD VMBACKUP TO OSS: WE NEED TO
#                           HAVE A FLAG TO ENABLE/SUSPEND VMBACKUP BUCKET
#                           VERSIONING
#    jfsaldan    08/07/24 - Bug 36927823 - EXACS VMBACKUP TO OSS 23.4.1.2.6 ;
#                           EXACLOUD DOESN'T COPY THE SERVICE ENDPOINT NOR
#                           CERTIFICATE PROPERLY INTO THE BACKUP JSON FILE FOR
#                           VMBACKUP TOOL TO READ IN NON-R1 REGIONS
#    jfsaldan    07/22/24 - Bug 36860756 - VMBACKUP TO OBJECTSTORE ON EXADB-D -
#                           FAILURE | LOCAL VARIABLE '_MSG' REFERENCED BEFORE
#                           ASSIGNMENT
#    jfsaldan    06/21/24 - Bug 36726315 - EXACLOUD VMBACKUP: EXACLOUD SHOULD
#                           SET THE KMS OCIDS IN THE PAYLOAD PASSED TO THE
#                           VMBACKUP TOOL ON THE DOM0S, INSTEAD OF SETTING THEM
#                           IN EXABOX.CONF
#    aypaul      03/05/24 - ENH#36082195 Delete objects in bucket if present
#                           before deletion.
#    jfsaldan    01/23/24 - Bug 36197480 - EXACS - EXACLOUD FAILS TO SET
#                           VMBACKUP.CONF VALUES TO ENABLED VMBACKUP TO OSS
#    aypaul      12/19/23 - Enh#35866197 Support reload option using osslist.
#    jfsaldan    10/20/23 - Bug 35857923 - ECS:23.4.1.2:EXACLOUD SHOULD NOT
#                           EXPECT THE DEST_DIR VALUE ON VMBACKUP RESTORE_OSS
#                           CALL
#    jfsaldan    09/27/23 - Enh 35791811 - VMBACKUP TO OSS:EXACLOUD: REDUCE
#                           TIME WHILE TAKING GOLD IMAGE DURING PROVISIONING
#    jfsaldan    09/14/23 - Bug 35811483 - EXACLOUD SHOULD NOT RELY ON THE
#                           VAULT OCID FROM EXABOX.CONF TO CHECK IF VMBACKUP
#                           BUCKETS NEED TO BE DELETED DURING DELETE SERVICE
#    jfsaldan    09/08/23 - Bug 35790909 - PREVMSETUP TASK FAILED IN
#                           DELETESERVICE: IN DELETE VMBACKUPS FROM DOM0 STEP
#    jfsaldan    08/16/23 - Enh 35692408 - EXACLOUD - VMBOSS - CREATE A FLAG IN
#                           EXABOX.CONF THAT TOGGLES BETWEEN INSTANCE
#                           PRINCIPALS AND USERS PRINCIPALS FOR VMBACKUP TO OSS
#                           MODULE
#    jfsaldan    06/13/23 - Enh 35207551 - EXACLOUD - ADD SUPPORT TO TERMINATE
#                           CLUSTER LEVEL VMBACKUP OCI RESOURCES WHEN LAST
#                           CUSTOMER CLUSTER IS TERMINATED
#    jfsaldan    04/25/23 - Enh 35207526 - EXACLOUD TO CREATE TENANT LEVEL
#                           USERS TO BE USED TO ACCESS CUSTOMER TENANCY LEVEL
#                           BUCKETS FOR VMBACKUP TO OSS
#                           ENH 35207515 - EXACLOUD
#                           TO CREATE TENANT LEVEL BUCKETS TO STORE VM BACKUPS
#    jfsaldan    04/25/23 - Creation
#

import base64
import configparser
import functools
import json
import oci
import os
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from exabox.exaoci.connectors.ConfigFileConnector import ConfigFileConnector
from exabox.exaoci.connectors.ExaboxConfConnector import ExaboxConfConnector
from exabox.exaoci.connectors.DefaultConnector import DefaultConnector
from exabox.exaoci.connectors.R1Connector import R1Connector
from exabox.exakms.ExaKmsEntryRSA import ExaKmsEntryRSA
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogTrace, ebLogWarn
from exabox.utils.ExaRegion import (get_r1_certificate_path,
    get_instance_root_compartment, get_instance_compartment)
from exabox.utils.node import connect_to_host, node_exec_cmd_check
from tempfile import NamedTemporaryFile
from typing import Optional, NamedTuple, Tuple


def retry(aRetriesLimit, aSleep):
    """
    Meant to be used as decorator or wrapper.
    This allows to retry a func in case it raises exception, at most aRetriesLimit times.
    It will sleep aSleep seconds between each try

    :param aRetriesLimit: the retry num; retry sleep sec
    :return: decorator
    """

    def aDecorator(func):
        """aDecorator"""

        # Keep func info
        @functools.wraps(func)
        def aWrapper(*args, **kwargs):
            """wrapper"""

            for attempt in range(aRetriesLimit):
                try:
                    return func(*args, **kwargs)

                except Exception as err:   # pylint: disable=broad-except
                    ebLogTrace(f"Try {attempt} of {aRetriesLimit} failed for: '{func}'")
                    ebLogTrace(f"Error: \n{err}")
                    time.sleep(aSleep)
            ebLogError(f"Retry failed for '{func}'")
            raise Exception(f'Exceed max retry num: {aRetriesLimit} failed')

        return aWrapper

    return aDecorator

class CustomerVMBDetails(NamedTuple):
    """
    Useful information to hold about a customer vmbackup info
    """
    dom0: str
    domU: str
    tenancy_ocid: str
    compartment_name: str
    bucket_name: str
    bucket_metadata_name: str

class ebVMBackupOCI(object):

    def __init__(self, aOptions):
        """
        We initialize OCI SDK Clients in here, and declare some variables that
        we'll be used by class methods
        The creation of this object should not fail EVEN if we're in a non-OCI
        setup, because ECRA will always send the vmbackup to OSS information
        during Delete Service to 'ensure' we delete any possible cluster bucket
        In such cases where there is no bucket, we should just do nothing

        :param aOptions: an aOptions context object
        """

        self._options = aOptions

        # Parse payload to get Customers data
        self._customer_nodes_details = self.mParseCustomerValues()

        # Check from config if users principals flag is set to True. Else
        # we'll use Instance Principals
        self._force_users_principals = self.mIsForceUsersPrincipalsSet()

        ebLogTrace(f"VM Backup OCI force_users_principals: '{self._force_users_principals}'")

        # Create Users Principals based ExaOCI Factory to sign requests
        if self._force_users_principals is True:

            # Parse the payload to build config file for ECRA Super User
            self._ecra_su_config = self.mParseEcraSUConfig()

            # Create OCI Factory using the ECRA Super User Credentials, we want
            # to avoid writing the config file to the filesystem so we pass it
            # as a dictionary
            _oci_connector = ConfigFileConnector(
                    aConfigFile = "",
                    aConfigDict=self._ecra_su_config)
            self._oci_factory = ExaOCIFactory(_oci_connector)

        # Create Instance Principals based ExaOCI Factory to sign requests
        else:
            self._oci_factory = ExaOCIFactory()

        # Create Identity Client
        # We rely on this identity client to get some OCIDs, so this client
        # needs to be created first
        self._identity_client = self._oci_factory.get_identity_client()

        # Try to get the OCI Resources names and get the OCIDs that we'll need
        self._ADMIN_TENANCY_OCID = self.mGetTenancyOcid()

        # If the compartment doesn't exist, this will be empty
        self._COMPARTMENT_VMBOSS_NAME = "vmboss_compartment"
        self._COMPARTMENT_VMBOSS_OCID, self._PARENT_COMPARTMENT_VMBOSS_OCID = \
                self.mGetVMBackupCompartmentId()

        if self._force_users_principals is True:
            self._GROUP_VMBOSS_NAME = "vmboss_group"
            self._GROUP_VMBOSS_OCID = self.mGetVMBossGroupOcid()
            self._VAULT_VMBOSS_OCID = self.mGetVMBossVaultOcid()
            self._vault_client = self._oci_factory.get_vault_client()

        self._KEY_VMBOSS_OCID = self.mGetVMBossMasterKeyOcid()

        # The clients below may rely on an OCID that we read from Identity, so
        # make sure those are created aftter the previous OCIDs are declared
        self._secrets_client = self._oci_factory.get_secrets_client()

        self._object_storage_client =  self._oci_factory.get_object_storage_client()

        self._NAMESPACE_TENANCY_OCID = self.mGetVMBossOSSNamespace()
        self._TAG_NAMESPACE = "vmboss_namespace"
        self._TAG_NAMESPACE_DEFINITION = "user_ocid"

        self._CACHE_FILE = "/opt/oracle/vmbackup/ociconf/vmbackup_bucketinformation.json"

        self.CERTIFICATE_R1_REMOTE_PATH = \
                "/opt/oracle/vmbackup/ociconf/combined_r1.crt"
        self.CERTIFICATE_CUSTOM = \
                '/opt/oracle/vmbackup/ociconf/certificate.crt'
        self.CONFIG_CRYPTO_EP = "kms_dp_endpoint"
        self.CONFIG_MASTER_KEY_OCID = "kms_key_id"


    @staticmethod
    def mIsVMBOSSEnabled(aOptions)->bool:
        """
        :returns:
            True: We detect in the payload sent by ECRA that vmbackup with OSS
                is enabled and we're in EXABM mode (OCI)
            False: We detect in the payload sent by ECRA that vmbackup with OSS
                is disabled or we're in NON-EXABM mode (PDIT or instance)
        """

        _is_exabm = (get_gcontext().mGetConfigOptions().get(
            "exabm", "").lower() == "true")
        ebLogTrace(f"VMBoss: Is-ExaBM: '{_is_exabm}'")

        _enabled = False
        if _is_exabm and aOptions.jsonconf:
            if aOptions.jsonconf.get("vmboss", {}).get("vmboss_map", []) != []:
                ebLogTrace(f"Exacloud detected non-empty vmboss map in payload")
                _enabled = True

        return _enabled

    @staticmethod
    def mIsForceUsersPrincipalsSet()-> bool:
        """
        :returns:
            True: We detect from exabox.conf that users principals should be used
            False: We detect from exabox.conf that users principals is disabled, so
                we fallback to instance principals
        """

        _force_users_principals = False
        if (get_gcontext().mGetConfigOptions().get(
            "vmbackup", {}).get("force_users_principals", "").lower() == "true"):
            _force_users_principals = True
        return _force_users_principals

    #
    # Class methods
    #
    def mGetNodeDetails(self)-> Tuple[CustomerVMBDetails]:
        return self._customer_nodes_details

    def mParseCustomerValues(self)-> Tuple[CustomerVMBDetails]:
        """
        This method will try to parse the payload and return a tuple of
        CustomerVMBDetails

        :returns: A tuple of CustomerVMBDetails, with the info
            parsed from the payload
        """

        _list_customer_details = []
        _vmboss_json = self._options.jsonconf.get("vmboss", {})

        _vmboss_nodes_map = _vmboss_json.get("vmboss_map", [])

        _tag_dom0 = "dom0"
        _tag_domU = "domu"
        _tag_customer_tenancy_ocid = "customer_tenancy_ocid"
        _tag_compartment_name = "vmboss_compartment"
        _tag_bucket_name = "vmboss_bucket"
        _tag_metadata_bucket = "vmboss_metadata_bucket"

        for _node_info in _vmboss_nodes_map:

            _customer_info = CustomerVMBDetails(
                _node_info.get(_tag_dom0),
                _node_info.get(_tag_domU),
                _node_info.get(_tag_customer_tenancy_ocid),
                _node_info.get(_tag_compartment_name),
                _node_info.get(_tag_bucket_name),
                _node_info.get(_tag_metadata_bucket))

            # We will make the below checks longer but will offer
            # a better logging experience
            _missing_mandatory = False
            if _customer_info.dom0 is None:
                ebLogWarn(f"Missing '{_tag_dom0}' in '{_node_info}'")
                _missing_mandatory = True

            elif _customer_info.domU is None:
                ebLogWarn(f"Missing '{_tag_domU}' in '{_node_info}'")
                _missing_mandatory = True

            elif _customer_info.tenancy_ocid is None:
                ebLogWarn(f"Missing '{_tag_customer_tenancy_ocid}' in '{_node_info}'")
                _missing_mandatory = True

            elif _customer_info.compartment_name is None:
                ebLogWarn(f"Missing '{_tag_compartment_name}' in '{_node_info}'")
                _missing_mandatory = True

            elif _customer_info.bucket_name is None:
                ebLogWarn(f"Missing '{_tag_bucket_name}' in '{_node_info}'")
                _missing_mandatory = True

            elif _customer_info.bucket_metadata_name is None:
                ebLogWarn(f"Missing '{_tag_metadata_bucket}' in '{_node_info}'")
                _missing_mandatory = True

            if _missing_mandatory:
                _err = ("Can't have empty fields, review the payload: "
                    f"'{_node_info}'")
                ebLogError(_err)
                raise ExacloudRuntimeError(0x095, 0xA, _err)

            else:
                ebLogTrace(f"Node details for: '{_customer_info}' parsed")

            _list_customer_details.append(_customer_info)

        ebLogTrace(f"Exacloud parsed the vmbackup customer details: '{_list_customer_details}'")
        return tuple(_list_customer_details)

    def mReturnDom0DomUPair(self):
        """
        This method will parse the ECRA payload and will return a list of
        Dom0 and DomU pairs
        """
        _dom0_domU_pair = []
        for _customer_details in self._customer_nodes_details:
            _dom0_domU_pair.append(
                    (_customer_details.dom0, _customer_details.domU))

        return _dom0_domU_pair

    def mParseEcraSUConfig(self)-> dict:
        """
        This method will parse the ECRA SU portion of the payload, and will
        return an appropiate config file to be used to create the OCI
        SDK Clients

        :raises KeyError: If any field needed is missing

        :returns: a dictionary representing the User Config File
        """

        _vmboss_json = self._options.jsonconf.get("vmboss", {})

        # Parse the payload to build config file for ECRA Super User
        _config_file_dict = {
            "tenancy":      _vmboss_json.get("su_config_file", {}).get("tenancy", None),
            "user":         _vmboss_json.get("su_config_file", {}).get("user", None),
            "fingerprint":  _vmboss_json.get("su_config_file", {}).get("fingerprint", None),
            "key_file":     _vmboss_json.get("su_config_file", {}).get("key_file", None),
            "region":       _vmboss_json.get("su_config_file", {}).get("region", None)
        }

        # Fail if any ECRA Super User field is missing
        if None in _config_file_dict.values():
            _err = ("Payload has 'None' value used to build an OCI "
                ", please provide a valid configuration in the payload. "
                f"Received: '{_config_file_dict.items()}'")
            raise KeyError(_err)

        return _config_file_dict

    @retry(aRetriesLimit=5, aSleep=5)
    def mGetTenancyOcid(self)->str:
        """
        Get the root compartment OCID.
        Since in prod we identified that the instances might or might not
        be under the root compartment, we will have a flag in
        exabox.conf where we can place the root compartment ocid
        If missing, well try to check if Exacloud is running on an
        OCI instance to get this OCID (through Instance Principals). If we
        detect to be in a non-instance we raise an error with a
        proper message

        :returns: a string representing the OCID of the root compartment
        """

        # Check if exabox.conf has the ocid
        _root_compartment_ocid = \
                get_gcontext().mGetConfigOptions().get(
                        "vmbackup", {}).get("root_compartment_ocid", "")

        if _root_compartment_ocid:
            ebLogInfo("Detected root compartment from exabox.conf: "
                f"{_root_compartment_ocid}")
            return _root_compartment_ocid

        # If not get it from IMDSv2
        try:
            _root_compartment_ocid = get_instance_root_compartment()
            ebLogInfo("Detected root compartment from Exacloud IMDSv2: "
                f"{_root_compartment_ocid}")

        except Exception as e:
            _err = ("Exacloud could not call the IMDS endpoint to get the "
                "Instance Tenancy OCID, Please verify the Instance is healthy"
                f"and you can curl the IMDS endpoint, e.g. try: "
                "'curl http://169.254.169.254/opc/v1/instance/', error: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        return _root_compartment_ocid

    @retry(aRetriesLimit=5, aSleep=5)
    def mGetVMBossGroupOcid(self) -> str:
        """
        Gets the "vmboss_group" user group ocid
        We expect to have permissions to do this, otherwise we won't be able
        to add a user to a group anyway

        :returns str: a String representing the vmboss group ocid

        :raises ExacloudRuntimeError: If we're unabel to get this Group OCID
        """

        # Trigger call and fail on error
        try:
           _response = self._identity_client.list_groups(
                   compartment_id=self._ADMIN_TENANCY_OCID,
                   name=self._GROUP_VMBOSS_NAME)
            # (Pdb) _response.data
            # [{
            #   "compartment_id": "ocid1.t......",
            #   "defined_tags": {},
            #   "description": "group for vmbackup test",
            #   "freeform_tags": {},
            #   "id": "ocid1.group.region1..aaa....",
            #   "inactive_status": null,
            #   "lifecycle_state": "ACTIVE",
            #   "name": "vmbackup_group",
            #   "time_created": "2023-02-15T21:03:09.587000+00:00"
            # }]
        except Exception as e:
            _err = (f"Exacloud can't get the '{self._GROUP_VMBOSS_NAME}' "
                    "Group OCID with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is "
                f"running. Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        # There is no sensitive data in here so we can log it
        ebLogTrace(f"List Groups response: '{_response.data}'")

        if len(_response.data) == 0:
            _err = ("Exacloud didn't find any group with name: "
                f"'{self._GROUP_VMBOSS_NAME}'. This indicates a problem in IAM"
                f"Please review the IAM setup for the host where Exacloud is "
                "running. ")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err)

        # Parse OCID from response
        _vmboss_group_ocid = _response.data[0].id
        if _vmboss_group_ocid is None:
            _err = ("OCI API Call didn't return any Group OCID, review the "
                f"previous request-id. This is a weird OCI issue, not "
                "expected ")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err)

        ebLogInfo(f"Exacloud read the ocid: '{_vmboss_group_ocid}' for the group: "
            f"'{self._GROUP_VMBOSS_NAME}'")
        return _vmboss_group_ocid


    def mGetVMBossVaultOcid(self) -> str:
        """
        Get's the OCID of the Vault used for vmbackup purposes
        We assume this is exabox.conf for now

        :returns str: a String representing the vmboss vault ocid

        :raies ExacloudRuntimeError: If we're unabel to get this OCID
        """

        _vmboss_vault_ocid = \
                get_gcontext().mGetConfigOptions().get(
                        "vmbackup", {}).get("vmboss_vault_ocid", "")

        if _vmboss_vault_ocid == "":
            _err = ("Exacloud needs the VMbackup Vault OCID to be present in "
                "exabox.conf. Please add this value and retry the operation")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err)

        ebLogInfo(f"Detected OCID: '{_vmboss_vault_ocid}' "
            f"for the Vault VMBoss OCID")

        return _vmboss_vault_ocid

    def mGetVMBossMasterKeyOcid(self)->str:
        """
        This method will get the OCID of the master key
        For now we assume this is in exabox.conf

        :returns str: a String representing the vmboss vault key ocid

        :raies ExacloudRuntimeError: If we're unabel to get this OCID
        """

        _vmboss_key_ocid = \
                get_gcontext().mGetConfigOptions().get(
                        "vmbackup", {}).get("vmboss_key_ocid", "")

        # If there's no key specified for vmbackup, we fallback to the
        # key used for ssh operations
        if _vmboss_key_ocid == "":
            _vmboss_key_ocid = \
                get_gcontext().mGetConfigOptions().get("kms_key_id")

            if _vmboss_key_ocid == "":
                _err = ("Exacloud needs 'vmboss_key_ocid' or "
                    "'kms_key_id' OCID to be present in "
                    "exabox.conf. Please add this value and retry the operation")
                ebLogError(_err)
                raise ExacloudRuntimeError(0x095, 0xA, _err)

        ebLogInfo(f"Detected OCID: '{_vmboss_key_ocid}' "
            f"for the Master Key VMBoss OCID")

        return _vmboss_key_ocid

    @retry(aRetriesLimit=5, aSleep=5)
    def mGetVMBossOSSNamespace(self)->str:
        """
        This method will get the Object Storage Namespace name

        :returns str: a String representing the OSS Namespace

        :raies ExacloudRuntimeError: If we're unabel to get this value
        """

        ebLogInfo("Exacloud is about to try to get the OSS Namespace")
        # Trigger call
        try:
            _response = self._object_storage_client.get_namespace()
            # >>> resp = _object_storage.get_namespace()
            # >>> resp
            # <oci.response.Response object at 0x7f1ac353a908>
            # >>> resp.data
            # 'dbaasexadatacustomersea1'

        except Exception as e:
            _err = (f"Exacloud failed to get the OSS namespace  "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")
        ebLogInfo(f"Detected OSS Namespace: '{_response.data}'")
        return _response.data


    @retry(aRetriesLimit=5, aSleep=5)
    def mGetVMBackupCompartmentId(self)-> Optional[tuple]:
        """
        This method will get the OCID of the VMBackup parent Compartment

        :returns tuple[str]: a tuple of strings representing the OCID of the
            compartment and its parent compartment.
            if we can't get the ocid we return (None, None)

            # (Pdb) aa = self._identity_client.list_compartments(
            #           compartment_id=self._ADMIN_TENANCY_OCID,
            #           name="vmbackup_compartment")
            # (Pdb) aa
            # <oci.response.Response object at 0x7f6e7c414a20>
            # (Pdb) aa.data
            # [{
            #   "compartment_id": "ocid1.tena....",
            #   "defined_tags": {},
            #   "description": "Compartment to s...",
            #   "freeform_tags": {},
            #   "id": "ocid1.compartment.region1.....",
            #   "inactive_status": null,
            #   "is_accessible": null,
            #   "lifecycle_state": "ACTIVE",
            #   "name": "vmbackup_compartment",
            #   "time_created": "2023-02-15T21:30:23.627000+00:00"
            # }]
            # (Pdb)

        """

        _vmboss_compartment_ocid = None

        # Search the compartment under the root/Tenancy compartment
        _root_compartment_ocid = self._ADMIN_TENANCY_OCID
        ebLogInfo("Detected root compartment from Exacloud IMDSv2: "
            f"{_root_compartment_ocid}, searching in here")
        try:
            _response = None
            _response = self._identity_client.list_compartments(
                   compartment_id=self._ADMIN_TENANCY_OCID,
                   name=self._COMPARTMENT_VMBOSS_NAME)

        except Exception as e:
            _err = (f"Exacloud can't get the info of the compartment: "
                f"'{self._COMPARTMENT_VMBOSS_NAME}'"
                f"Please review the IAM setup for the host where Exacloud "
                f"is running, or make sure the bucket exists "
                f"Erorr: '{e}'")
            ebLogWarn(_err)

        # Log Request Id
        if _response:
            ebLogTrace(f"Request ID is: '{_response.request_id}'")

            # We validate the response has the compartment
            if len(_response.data) > 0:
                _compartment_id = _response.data[0].id
                ebLogInfo(f"Exacloud found the OCID: '{_compartment_id}' "
                    "for the compartment name: "
                    f"'{self._COMPARTMENT_VMBOSS_NAME}'")
                return (_compartment_id, _root_compartment_ocid)

        # If not present, search under the ECRA compartment
        ebLogWarn("Exacloud didn't find any compartment with name: "
            f"'{self._COMPARTMENT_VMBOSS_NAME}' under "
            f"'{_root_compartment_ocid}'. ")

        _ec_instance_compartment_ocid = get_instance_compartment()
        ebLogInfo("Detected instance compartment from Exacloud IMDSv2: "
            f"{_ec_instance_compartment_ocid}, searching in here")

        # Trigger call and fail on error
        try:
           _response = self._identity_client.list_compartments(
                   compartment_id=_ec_instance_compartment_ocid,
                   name=self._COMPARTMENT_VMBOSS_NAME)

        except Exception as e:
            _err = (f"Exacloud can't get the info of the compartment: "
                f"'{self._COMPARTMENT_VMBOSS_NAME}'"
                f"Please review the IAM setup for the host where Exacloud "
                f"is running, or make sure the bucket exists "
                f"Erorr: '{e}'")
            ebLogWarn(_err)

        # Log Request Id
        if _response:
            ebLogTrace(f"Request ID is: '{_response.request_id}'")

            # We validate the response has the compartment
            if len(_response.data) == 0:
                _err = ("Exacloud didn't find any compartment with name: "
                    f"'{self._COMPARTMENT_VMBOSS_NAME}'. We'll assume for "
                    "now that it doesn't exists ")
                ebLogWarn(_err)
                return (None, None)

            _compartment_id = _response.data[0].id
            ebLogInfo(f"Exacloud found the OCID: '{_compartment_id}' for the compartment "
                f"name: '{self._COMPARTMENT_VMBOSS_NAME}'")
            return (_compartment_id, _ec_instance_compartment_ocid)

        return (None, None)

    #
    # OCI Resource Manipulation methods
    #
    @retry(aRetriesLimit=5, aSleep=5)
    def mCreateCustomerUser(self, aUserName) -> oci.identity.models.user.User:
        """
        This method will try to create the VMBackup User

        :raies ExacloudRuntimeError: If we're unabel to complete this operation

        :returns: a User Details Model
        """

        # Create User details
        _user_details = oci.identity.models.CreateUserDetails(
                compartment_id = self._ADMIN_TENANCY_OCID,
                name = aUserName,
                description="Exacloud generated vmbackup user.")

        # Trigger call and fail on error
        try:
            _response = self._identity_client.create_user(_user_details)
        except Exception as e:
            _err = ("Exacloud failed to create a VMBackup User with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        # At this point if the request was a success, response.data will be a dictionary
        # with the details of the User we just created
        # There is no sensitive data in here so we can log it
        ebLogTrace(f"Create users response: '{_response.data}'")

        # On success we store the Users details
        return _response.data


    @retry(aRetriesLimit=5, aSleep=5)
    def mAddUserToGroup(self, aUserDetails) -> None:
        """
        This method will try to add the User for VMBackups to the vmboss_group

        :raises: ExacloudRuntimeError on error
        """

        # Create add user to group details
        _add_user_to_group_details = oci.identity.models.AddUserToGroupDetails(
            user_id = aUserDetails.id,
            group_id = self._GROUP_VMBOSS_OCID)

        # Trigger call to add user to group
        try:
            _response = self._identity_client.add_user_to_group(
                    _add_user_to_group_details)
        except Exception as e:
            _err = (f"Exacloud failed to add user: '{aUserDetails.name}' to "
                f"the '{self._GROUP_VMBOSS_NAME}' with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        ebLogInfo(f"Exacloud successfully added the User: '{aUserDetails.name}' "
            f"to the group '{self._GROUP_VMBOSS_NAME}' with OCID: {self._GROUP_VMBOSS_OCID}")

    @retry(aRetriesLimit=5, aSleep=5)
    def mCheckIdentityHasUser( self,
            aUserName)->Optional[oci.identity.models.user.User]:
        """

        :returns Optional[User Details]:
            If a User with Name aUserName exists, we return it's details
            If we detect no User, we return None

        :raises ExacloudRuntimeError: If our OCI Client is unable to perform the
            request against the OCI service, as that indicates an underlying issue in
            IAM or network that needs to addressed ASAP
        """

        try:
            # At the moment of writing this there is no API to get a User by name
            # but only by OCID. So we need to use 'list' to get the User's details,
            # since 'list' supports searching by name
            _response = self._identity_client.list_users(
                compartment_id = self._ADMIN_TENANCY_OCID,
                name = aUserName)
            # List users response:
            # '{
            #   "capabilities": {
            #     "can_use_api_keys": true,
            #     "can_use_auth_tokens": true,
            #     "can_use_console_password": true,
            #     "can_use_customer_secret_keys": true,
            #     "can_use_o_auth2_client_credentials": true,
            #     "can_use_smtp_credentials": true
            #   },
            #   "compartment_id": "ocid1.ten....",
            #   "defined_tags": {},
            #   "description": "Exacloud generated vmbackup user.",
            #   "email": null,
            #   "email_verified": false,
            #   "external_identifier": null,
            #   "freeform_tags": {},
            #   "id": "ocid1.user.region1..aaaa...",
            #   "identity_provider_id": null,
            #   "inactive_status": null,
            #   "is_mfa_activated": false,
            #   "last_successful_login_time": null,
            #   "lifecycle_state": "ACTIVE",
            #   "name": "vmbackup_ocid1.tenancy.o...",
            #   "previous_successful_login_time": null,
            #   "time_created": "2023-04-26T21:40:26.154000+00:00"
            # }'

        except Exception as e:
            _err = ("Exacloud failed to list the VMBackup Users with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # At this point if the request was a success, response.data will always be a list
        # (even if empty)
        # There is no sensitive data in here so we can log it
        ebLogTrace(f"List users response: '{_response.data}'")

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        # We validate the response has the user intended
        if len(_response.data) == 0:
            _msg = ("Exacloud didn't find any user with name: "
                f"'{aUserName}'. We'll assume for now the User doesn't "
                "exists ")
            ebLogInfo(_msg)
            return None

        # We need to make sure that the response list contains the user name
        # with the exact name given. Then we store all the User details in an object
        # attribute
        _request_user_name = _response.data[0].name
        if _request_user_name == aUserName:
            ebLogInfo(f"User name: '{_request_user_name}' is present")
            return _response.data[0]
        else:
            raise ExacloudRuntimeError(0x095, 0xA, "Some weird behavior happened")

    @retry(aRetriesLimit=5, aSleep=5)
    def mCheckIdentityHasUserKey(self, aUserDetails)-> list:
        """
        We use the identity client to check if the User has a valid Key uploaded
        in Identity Service.

        :returns:
            If it does we'll return a list of dictionaries, each of them having
                the details of each key. We should know, the User Private
                Key is NEVER pushed to identity, so the response we'll get in here will
                not contain any sensitive data. An example below
            If there is no Key in Identity, we return an empty list

        """

        ebLogInfo("Exacloud is about to list the keyapi's for: "
            f"'{aUserDetails.name}'")

        # Trigger call and fail on error
        try:
            _response = self._identity_client.list_api_keys(
                    aUserDetails.id)
            # (Pdb) aa = self._identity_client.list_api_keys(
            #           "ocid1.us.......")
            # (Pdb) aa.data
            # [{
            #   "fingerprint": "a6:94:26:97:c5:4c:fc:ff:c...",
            #   "inactive_status": null,
            #   "key_id": "ocid1.tenanc......",
            #   "key_value": "-----BEGIN PUB......",
            #   "lifecycle_state": "ACTIVE",
            #   "time_created": "2023-02-16T23:12:29.812000+00:00",
            #   "user_id": "ocid1.user.region1..aaaaaa...."
            # }]

        except Exception as e:
            _err = ("Exacloud failed to list the VMBackup User Keyapi's "
                "with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        # At this point if the request was a success
        # There is no sensitive data in here so we can log it
        ebLogTrace(f"List users Keyapi response: '{_response.data}'")

        return _response.data

    def mCreateCustomerUserCredentials(self)-> Tuple[str]:
        """
        We will create the VMBackup User Credentials in here.
        If we need to use a different cipher/setting we can change this method alone

        :returns: a tuple of string with the generated data
        """

        ebLogInfo("Exacloud is about to create a private/public RSA Key")
        # Create private key, this returns a string
        _private_key_str = ExaKmsEntryRSA.mGeneratePrivateKey()

        # Create an RSA Key object from private key string
        _private_key_rsa = serialization.load_pem_private_key(
                _private_key_str.encode("utf-8"), None, default_backend())

        # Calculate public key from the RSA Key object
        _public_key_str = _private_key_rsa.public_key().public_bytes(
             encoding=serialization.Encoding.PEM,
             format=serialization.PublicFormat.SubjectPublicKeyInfo
         ).decode("utf-8")
        ebLogInfo("Exacloud created the private/public RSA Key")

        return (_private_key_str, _public_key_str)

    @retry(aRetriesLimit=5, aSleep=5)
    def mUploadCustomerUserCredentialsToIdentity(self,
            aPublicKeyStr, aUserDetails):
        """
        This method will try to upload aPublicKeyStr as a Key API from the user
        and returns the API Key details that we get from Identity

        :returns: The details of the public key we just pushed to Identity

        :raises: ExacloudRuntimeError if an error happens when trying to push
            the public key

        """

        # Create KeyAPI details for the request
        _create_api_key_details = oci.identity.models.CreateApiKeyDetails(
                key = aPublicKeyStr)

        # Upload public key to Identity Service
        ebLogInfo("Exacloud is about to upload the public key to Identity")
        try:
            _response = self._identity_client.upload_api_key(
                    user_id = aUserDetails.id,
                    create_api_key_details = _create_api_key_details)
            # NOTE! This example doesn't have any private info
            # (Pdb) upload_api_key_response.data
            # {
            #   "fingerprint": "b8:b0:b6:08:.....",
            #   "inactive_status": null,
            #   "key_id": "ocid1.ten....",
            #   "key_value": "-----BEGI...",
            #   "lifecycle_state": "ACTIVE",
            #   "time_created": "2023-04-27T00:31:15.672000+00:00",
            #   "user_id": "ocid1.user.re...."
            # }

        except Exception as e:
            _err = ("Exacloud failed to upload Key API with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Also make sure the limit for KeyAPIs hasn't been reached. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        ebLogInfo(f"Succesfully pushed KeyAPI with fingerprint: "
            f"'{_response.data.fingerprint}'")

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        # At this point if the request was a success, response.data will be a dictionary
        # with the details of the User keyapi that we just created
        return _response.data


    @retry(aRetriesLimit=5, aSleep=5)
    def mGetUserKeyFromSiV(self, aUserName)->Optional[dict]:
        """
        We check in SiV if our we have a Secret that holds the User Key

        Returns: a dictionary with the contents of the secret (JSON).
            - Empty if no secret is in SiV
        """

        _secret_name = f"vmboss_secret_{aUserName}"

        ebLogInfo(f"Checking for a Customer Credentials in Vault with secret name: "
                f"'{_secret_name}'")
        # Trigger call, if error it means either the secret doesn't exists OR we don't
        # have permissions to see it. We'll assume we have permissions and the secret
        # is missing so that we try to create it later on
        try:
           _response = self._secrets_client.get_secret_bundle_by_name(
                   secret_name = _secret_name,
                   vault_id = self._VAULT_VMBOSS_OCID)
            # (Pdb) resp = self._secrets_client.get_secret_bundle_by_name(
            #           secret_name="test_1", vault_id="oci....")
            # (Pdb) resp.data
            # {
            #   "metadata": null,
            #   "secret_bundle_content": {
            #     "content": "d2VsY29tZTE=",
            #     "content_type": "BASE64"
            #   },
            #   "secret_id": "ocid1.vaultsecret.region1.sea.am...",
            #   "stages": [
            #     "CURRENT",
            #     "LATEST"
            #   ],
            #   "time_created": "2023-05-02T18:34:42.739000+00:00",
            #   "time_of_deletion": null,
            #   "time_of_expiry": null,
            #   "version_name": null,
            #   "version_number": 1
            # }
            # (Pdb)
        except Exception as e:
             ebLogInfo(f"Exacloud didn't detect any secret in vault: "
                     f"'{self._VAULT_VMBOSS_OCID} for: '{_secret_name}'. We'll assume "
                     f"the Credentials are not present and that we have the proper "
                     f"IAM setup")
             return {}

        # There is sensitive data in here so we don't log the whole response
        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        # Parse the response, decode the contents and return them in a dictionary
        _contents = _response.data.secret_bundle_content.content
        try:
            _contents_json_base64decoded = base64.b64decode(_contents.encode("utf-8"))
            _contents_map = json.loads(_contents_json_base64decoded)

        except Exception as e:
            ebLogWarn(f"Exacloud failed to parse the contents of the Secret in Vault. "
                "We'll try to create a new one from scratch. Error is: '{e}'")
            return {}

        return _contents_map

    @retry(aRetriesLimit=5, aSleep=5)
    def mCheckUserBelongsToGroup(self, aUserDetails)-> bool:
        """
        This method will help us check if the user is already part of the vmbackup
        group

        :returns:
            True: User belongs to the vmboss_group
            False: User DOESN'T belong to the vmboss_group
        """

        # Trigger call and fail on error
        try:
           _response = self._identity_client.list_user_group_memberships(
                   compartment_id = self._ADMIN_TENANCY_OCID,
                   user_id = aUserDetails.id)

            # (Pdb) _response = self._identity_client.list_user_group_memberships(
            #       compartment_id="ocid1.tena....",
            #       user_id="ocid1.user.region1.....")
            # (Pdb) _response
            # <oci.response.Response object at 0x7f7a3c02aeb8>
            # (Pdb) _response.data
            # [{
            #   "compartment_id": "ocid1.tenancy.oc.....",
            #   "group_id": "ocid1.group.region1..aaaaa....",
            #   "id": "ocid1.groupmembership.region1..aaaa...",
            #   "inactive_status": null,
            #   "lifecycle_state": "ACTIVE",
            #   "time_created": "2023-04-28T23:24:12.870000+00:00",
            #   "user_id": "ocid1.user.region1..aaaaaaaajyzk..."
            # }]
            # (Pdb)

        except Exception as e:
            _err = (f"Exacloud can't get the VMBackup user '{aUserDetails.name}' "
                    "group membership list with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        # There is no sensitive data in here so we can log it
        ebLogTrace(f"List Group membership response: '{_response.data}'")

        # If the response list is empty, the User doesn't belong in the vmbackup group
        if len(_response.data) == 0:
            ebLogInfo("Exacloud found that the user with name "
                f"'{aUserDetails.name}' is not part of the group: "
                f"'{self._GROUP_VMBOSS_NAME}' with ocid: '{self._GROUP_VMBOSS_OCID}'")
            return False

        # If the response list is non empty then iterate over the response list
        # and check each group OCID
        for _group_details in _response.data:

            if _group_details.group_id == self._GROUP_VMBOSS_OCID:
                ebLogInfo("Exacloud found that the user with name "
                    f"'{aUserDetails.name}' is already part of the group: "
                    f"'{self._GROUP_VMBOSS_NAME}' with ocid: '{self._GROUP_VMBOSS_OCID}'")
                return True

        # If we're here, then the User doesn't belong to the Group
        ebLogWarn(f"Exacloud detected that the user: '{aUserDetails.name}' "
            f"doesn't belong to the Group: '{self._GROUP_VMBOSS_NAME}'")
        return False


    @retry(aRetriesLimit=5, aSleep=5)
    def mUploadCustomerUserCredentialsToSiV(self, aPrivateKeyStr,
            aPublicKeyDetails, aUserDetails)-> None:
        """
        This method will try to push a set of User Credentials to SiV

        :returns: None
        :raises ExacloudRuntimeError: If an error happens when trying to push
            the secret to the Vault

        """

        _contents = {}
        _contents["private_key"] = aPrivateKeyStr
        _contents["public_key_details"] = {
            "key_value": aPublicKeyDetails.key_value,
            "fingerprint": aPublicKeyDetails.fingerprint,
            "time_created": str(aPublicKeyDetails.time_created),
            "lifecycle_state": aPublicKeyDetails.lifecycle_state,
            "user_id": aPublicKeyDetails.user_id
        }

        # This is the json in base64
        _contents_encoded = base64.b64encode( json.dumps(_contents).encode("utf-8"))

        # TODO change this
        _secret_name = f"vmboss_secret_{aUserDetails.name}"

        # Create Secret details
        _create_secret_details = oci.vault.models.CreateSecretDetails(
                compartment_id="ocid1.compartment.region1..aaaaaaaa2ngh2hpgjfokan3pevaooukhykrcpua43e3rfdobjabx56n6xu7q",
                secret_content=oci.vault.models.Base64SecretContentDetails(
                    content_type="BASE64",
                    name="vmboss_test",
                    content=_contents_encoded.decode("utf-8")),
                secret_name = _secret_name,
                vault_id = self._VAULT_VMBOSS_OCID,
                key_id = self._KEY_VMBOSS_OCID)

        # Trigger call and fail on error
        ebLogInfo(f"Exacloud is about to push a secret with name: '{_secret_name}'")
        # TODO, if secret is already present, we must create a new version!
        # otherwise the operation fails
        try:
           _response = self._vault_client.create_secret(
                   create_secret_details = _create_secret_details)

            # Upload the secret to the Vault
            # (Pdb) resp = self._vault_client.create_secret(....
            # (Pdb) resp.data
            # {
            #   "compartment_id": "ocid1.compartment.region1..a.....",
            #   "current_version_number": 1,
            #   "defined_tags": {},
            #   "description": null,
            #   "freeform_tags": {},
            #   "id": "ocid1.vaultsecret.region1.sea.amaaaaaa4mtgwp....",
            #   "key_id": "ocid1.key.region1.sea.avprd5maaag4s.abzwklj...",
            #   "lifecycle_details": null,
            #   "lifecycle_state": "CREATING",
            #   "metadata": null,
            #   "secret_name": "test_created_sdk",
            #   "secret_rules": null,
            #   "time_created": "2023-05-02T19:52:25.957000+00:00",
            #   "time_of_current_version_expiry": null,
            #   "time_of_deletion": null,
            #   "vault_id": "ocid1.vault.region1.sea.avprd5maaag4s.abzwk..."
            # }
            # (Pdb)
        except Exception as e:
            _err = (f"Exacloud can't upload the secret name to the Vault "
                    "the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running, "
                "as well as the error. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")


    @retry(aRetriesLimit=5, aSleep=5)
    def mDeleteUserKeyFromIdentity(self, aListPublicKeyDetails, aUserDetails)-> None:
        """
        Delete the Key(s) from Identity that has the fingerprint from
        the keys of aListPublicKeyDetails

        :param aListPublicKeyDetails: a list of all the public keys to delete
        :param aUserDetails: Details of the User from which to delete the keys

        :returns: None
        :raises ExacloudRuntimeError: If an error happens when trying to delete
            the public key from Identity
        """

        _list_fingerprints = list(map(
            lambda _key_details: _key_details.fingerprint,
            aListPublicKeyDetails))

        ebLogWarn(f"Exacloud will try to delete the Public Keys from Identity with "
            f"the fingerprints: '{_list_fingerprints}'")

        for _fingerprint in _list_fingerprints:
            ebLogInfo(f"Exacloud is about to Delete the publi key with "
                f"finerprint: '{_fingerprint}'")

            # Trigger call and fail on error
            # TODO: According to Oracle docs on success this returns 204,
            # We need to make sure that after a 204 we then check again an receive
            # a 404, to confirm the KeyAPI was indeed deleted
            try:
               _response = self._identity_client.delete_api_key(
                       user_id = aUserDetails.id,
                       fingerprint = _fingerprint)

                # (Pdb) _response = self._identity_client.delete_api_key(
                #           user_id = self._customer_user_details.id,
                #           fingerprint="24:5a....
                # (Pdb) _response.data
                # (Pdb) _response.status
                # 204
                # (Pdb) _response = self._identity_client.delete_api_key(
                #               user_id = self._customer_user_details.id,
                #               fingerprint="24:5a...")
                # *** oci.exceptions.ServiceError: {'opc-request-id':
                #               '24EA467E1ACD484C85, 'code': 'KeyNotFound',
                #               'message': "Key '....' not found", 'status': 404}
                # (Pdb)

            except Exception as e:
                _err = (f"Exacloud can't delete the KeyAPI with fingerprint: "
                        f" '{_fingerprint}' to the Vault with the ECRA Super User. "
                    f"Please review the IAM setup for the host where Exacloud is running, "
                    "as well as the error. "
                    f"Erorr: '{e}'")
                ebLogError(_err)
                raise ExacloudRuntimeError(0x095, 0xA, _err) from e

            # Log Request Id
            ebLogTrace(f"Request ID is: '{_response.request_id}'")

        ebLogInfo("Exacloud successfully deleted the Public Keys from identity that "
            f"had the fingerprints: '{_list_fingerprints}'")


    def mCompareFingerPrints(self, aPrivateKeyDetails, aListPublicKeyDetails)->bool:
        """

        Compares the fingerprint from aPrivateKeyDetails with the ones from the list
        in aListPublicKeyDetails

        :returns bool:
            True: If we find a fingerprint match between SiV and Identity
            False: If we don't find a fingerprint match
        """

        # Get fingerprint from SiV
        _siv_finerprint = aPrivateKeyDetails.get(
                "public_key_details", {}).get("fingerprint", "")

        # Get fingerprints from Identity
        _list_fingerprints = list(map(
            lambda _key_details: _key_details.fingerprint,
            aListPublicKeyDetails))

        _fingerprint_match = False

        # Compare fingerprints
        for _fingerprint in _list_fingerprints:
            if _fingerprint == _siv_finerprint:
                ebLogInfo(f"Exacloud dectected a fingerprint match: '{_fingerprint}'")
                _fingerprint_match = True
                break
            else:
                ebLogWarn(f"Fingerprint doesn't match: '{_fingerprint}'")

        if not _fingerprint_match:
            ebLogWarn(f"Exacloud dectected that no Fingerprint from SiV matches "
                "any fingerprint from Identity.")
            return False

        return True

    def mCheckBucketExists(self, aBucketName:str)-> bool:
        """
        This method will check if a bucket already exists (or we have permissions to
        it). We use HEAD Bucket since is the OCI recommended way

        :returns bools:
            True: If bucket exists
            False: If bucket doesn't exists
        """

        # Trigger call and fail on error
        try:
           _response = self._object_storage_client.head_bucket(
                   namespace_name = self._NAMESPACE_TENANCY_OCID,
                   bucket_name = aBucketName)
            # (Pdb) _response.data
            #
        except Exception as e:
            _msg = (f"Exacloud detected that no bucket exists with name: "
                f"'{aBucketName}'")
            ebLogWarn(_msg)
            ebLogTrace(f"Erorr: '{e}'")
            return False

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        ebLogInfo(f"Exacloud detected that a bucket with name: "
                f"'{aBucketName}' exists")
        return True


    @retry(aRetriesLimit=5, aSleep=5)
    def mCreateBucket(self,
            aUserDetails,
            aCompartmentDetails,
            aBucketName)-> None:
        """
        This method will try to create the VMBackup bucket

        :returns: None
        :raises ExacloudRuntimeError: If an error happens when trying to
            create the bucket
        """

        # Check if we need to tag the bucket during it creation
        _defined_tags = None
        if aUserDetails is not None:
            _defined_tags = {
                self._TAG_NAMESPACE: {
                    self._TAG_NAMESPACE_DEFINITION: aUserDetails.id}}

        # Create bucket details
        _versioning = "Enabled"
        if (get_gcontext().mGetConfigOptions().get(
            "vmbackup", {}).get("force_disable_versioning", "").lower() == "true"):
            _versioning= "Disabled"
        _create_bucket_details = oci.object_storage.models.CreateBucketDetails(
            name = aBucketName,
            compartment_id = aCompartmentDetails.id,
            versioning = _versioning,
            metadata={
                'Comment': 'Created by Exacloud'},
            defined_tags = _defined_tags)

        # Nothing is sensitive here, we can log it
        ebLogInfo(f"Exacloud is about to create a bucket with details:\n"
            f"{_create_bucket_details}'")

        # Trigger call and fail on error
        try:
           _response = self._object_storage_client.create_bucket(
                   namespace_name = self._NAMESPACE_TENANCY_OCID,
                   create_bucket_details = _create_bucket_details)

        except Exception as e:
            _err = (f"Exacloud couldn't create the Bucket with name: "
                f"'{aBucketName}' with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        ebLogInfo(f"Exacloud created with success a bucket with name: "
                f"'{aBucketName}'")

    @retry(aRetriesLimit=5, aSleep=5)
    def mCheckCompartmentExists(self, aCompartmentName:str, aParentCompartmentOcid: str = None)-> bool:
        """
        This method is used to check if we already have created a compartment
        for this customer, under the root 'vmboss_compartment'

        :returns bool:
            True: If the Compartment exists
            False: If it doesn't exists
        """

        if self._COMPARTMENT_VMBOSS_OCID is None:
            _err = (f"OCID of Compartment: '{self._COMPARTMENT_VMBOSS_OCID}' "
                f"is unknown. Please make sure the compartment exists "
                f"and Exacloud has permissions to use it ")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err)

        # Trigger call and fail on error
        _parent_compartment = self._COMPARTMENT_VMBOSS_OCID

        if aParentCompartmentOcid:
            _parent_compartment = aParentCompartmentOcid

        try:
           _response = self._identity_client.list_compartments(
                   compartment_id = _parent_compartment,
                   name = aCompartmentName)
            # (Pdb) aa = self._identity_client.list_compartments(
            #               compartment_id=self._ADMIN_TENANCY_OCID,
            #               name = "vmbackup_compartment")
            # (Pdb) aa.data
            # [{
            #   "compartment_id": "ocid1.t.....",
            #   "defined_tags": {},
            #   "description": "Compartment to...",
            #   "freeform_tags": {},
            #   "id": "ocid1.compartment.region1..aaaaaaa...",
            #   "inactive_status": null,
            #   "is_accessible": null,
            #   "lifecycle_state": "ACTIVE",
            #   "name": "vmbackup_compartment",
            #   "time_created": "2023-02-15T21:30:23.627000+00:00"
            # }]
            # (Pdb)
            #
        except Exception as e:
            _err = (f"Exacloud couldn't check if a Compartment wih name "
                f"'{aCompartmentName}' exists with "
                    "the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        if len(_response.data) == 0:
            _msg = ("Exacloud didn't find any Compartment with name: "
                f"'{aCompartmentName}'. We'll assume the Compartment "
                f"doesn't exists")
            ebLogWarn(_msg)
            return None

        ebLogInfo("Exacloud found the Compartment Id: "
            f"'{_response.data[0].compartment_id}'")

        return _response.data[0]


    @retry(aRetriesLimit=5, aSleep=5)
    def mCreateCustomerCompartment(self, aCompartmentName:str, aParentCompartmentOcid: str = None):
        """
        This method will try to Create the Customer Compartment

        :param aCompartmentName: Compartment name
        :returns: The details of the compartment created
        """

        if self._COMPARTMENT_VMBOSS_OCID is None:
            _err = (f"OCID of Compartment: '{self._COMPARTMENT_VMBOSS_OCID}' "
                f"is unknown. Please make sure the compartment exists "
                f"and Exacloud has permissions to use it ")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err)

        ebLogInfo(f"Exacloud is about to attempt the creation of the Compartment "
            f"with name: '{aCompartmentName}'")

        _parent_compartment = self._COMPARTMENT_VMBOSS_OCID

        if aParentCompartmentOcid:
            _parent_compartment = aParentCompartmentOcid

        # Compartment Details
        _create_compartment_details=oci.identity.models.CreateCompartmentDetails(
            compartment_id = _parent_compartment,
            name = aCompartmentName,
            description="Compartment Create by Exacloud for VMBackup")


        # Trigger call and fail on error
        try:
           _response = self._identity_client.create_compartment(
               create_compartment_details = _create_compartment_details)

            # (Pdb) _response = self._identity_client.create_compartment(
            #                   create_compartment_details = _...
            # (Pdb) _response.data
            # {
            #   "compartment_id": "ocid1.compartment.region1..aa...
            #   "defined_tags": {},
            #   "description": "Compartment Create by Exacloud for VMBackup",
            #   "freeform_tags": {},
            #   "id": "ocid1.compartment.region1..aaaaaaaawyj6o7bs...
            #   "inactive_status": null,
            #   "is_accessible": true,
            #   "lifecycle_state": "ACTIVE",
            #   "name": "vmboss_ocid1.tenancy.oc1..____user_test_for...
            #   "time_created": "2023-05-05T20:57:55.161000+00:00"
            # }
            # (Pdb)

        except Exception as e:
            _err = (f"Exacloud couldn't create the Compartment wih name "
                f"'{aCompartmentName}' with "
                    "the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        ebLogInfo("Exacloud created the Compartment with name: "
            f"'{aCompartmentName}'")

        # Wait for the Compartment Lyfecyle to be ACTIVE
        self.mWaitCompartmentLifecycle(_response.data)

        return _response.data

    def mWaitCompartmentLifecycle(self, aCompartmentDetails)-> int:
        """
        This method will wait for the Compartment from aCompartmentDetails
        to have the ACTIVE lifecycle state.

        raises ExacloudRuntimeError: if the compartment doesn't change to
            ACTIVE after the default retry attempts ~= _retries * _wait_time
        """

        _retries = 10
        _wait_time = 5 #seconds
        _EXPECTED_STATE = "ACTIVE"

        while _retries>0:

            ebLogInfo(f"Attempting to check the current LifeCycle state "
                "of the Compartment")

            _response = self._identity_client.get_compartment(
                    compartment_id = aCompartmentDetails.compartment_id)

            # (Pdb) aaa = self._identity_client.get_compartment(
            #       "ocid1.compartment.region1..aaa....
            # (Pdb) aaa.data
            # {
            #   "compartment_id": "ocid1.compartment.r....
            #   "defined_tags": {},
            #   "description": "Compartment Create by Exacloud for VMBackup",
            #   "freeform_tags": {},
            #   "id": "ocid1.compartment.region1..aaaaaaa....
            #   "inactive_status": null,
            #   "is_accessible": true,
            #   "lifecycle_state": "ACTIVE",
            #   "name": "vmboss_comp_ocid1.tenancy.oc1..aaaa....
            #   "time_created": "2023-05-22T20:31:30.886000+00:00"
            # }
            # (Pdb)


            ebLogTrace(f"Response is: '{_response.data}'")
            time.sleep(_wait_time)
            if _response.data.lifecycle_state == _EXPECTED_STATE:
                ebLogInfo(f"Lifecycle of: '{aCompartmentDetails.name}' is now '{_EXPECTED_STATE}'")
                return 0
            else:
                _retries -= 1
                ebLogInfo(f"Waited '{_wait_time}' seconds before checking lifecycle state of: "
                    f"'{aCompartmentDetails.name}' again")

        _err = (f"The lifecycle of the compartment: '{aCompartmentDetails.name}' "
            f"has NOT changed to '{_EXPECTED_STATE}'. Please review the setup or retry the operation")
        ebLogError(_err)
        raise ExacloudRuntimeError(0x095, 0xA, _err)


    def mSetupVMBackupCustomerUser(self)-> None:
        """
        Main driver method to make sure we have the VMBackup Setup for the VMBackup
        User and it's credentials
        This includes:
            - Making sure the VMBackup User Exists
            - Making sure the VMBackup User belongs to the VMBackup Group
            - Making sure the VMBackup Credentials Exists in
                - Identity
                - SiV

        Mechanism to handle the User's Key:
            - Check if we have (if any) in SiV a Key with it's fingerprint matching
              the one we have (if any) from SiV
            - In case we have a Key missing from one of the two places (SiV, Identity), we
              try to recover:
              1 - If we have a Key in SiV (Private Key) we try to push it to Identity (we
                    only ever push the Public Key to Identity)
              2 - If we only have the Key in Identity (Public Key) we'll delete it and try
                    to create a new one to:
                a) Push to Identity (Public)
                b) Push to SiV (Private)
            - We should not let a stale Public Key in Identity if we don't have it's
              Private pair, since we have an Identity Service Limit of having 3 Keys
              per user at most at a given time

        :raises ExacloudRuntimeError: If any fatal error occurs during this setup

        :returns: None

        """

        _set_unique_user_name = set()
        for _customer_details in self._customer_nodes_details:

            # Since the node details have all the details about all VMs,
            # we do a quick check to make sure we only ever check a user once
            if _customer_details.user_name in _set_unique_user_name:
                ebLogTrace(f"Already checked user: '{_customer_details.user_name}', skipping")
                continue

            _set_unique_user_name.add(_customer_details.user_name)

            # Check if we already have a User created for this Customer Tenancy
            # Else create it
            _user_details = self.mCheckIdentityHasUser(_customer_details.user_name)
            if not _user_details:
                _user_details = self.mCreateCustomerUser(_customer_details.user_name)

            # Make sure the User belongs to the vmbackup group
            # Else add it
            if not self.mCheckUserBelongsToGroup(_user_details):

                # Add the User to the VMBackup Group
                self.mAddUserToGroup(_user_details)

            _siv_user_key_details = self.mGetUserKeyFromSiV(_user_details.name)
            _identity_user_key_details_list = self.mCheckIdentityHasUserKey(_user_details)

            if not _identity_user_key_details_list and not _siv_user_key_details :

                _private_key_str, _public_key_str = self.mCreateCustomerUserCredentials()
                _public_key_details = self.mUploadCustomerUserCredentialsToIdentity(
                        _public_key_str, _user_details)
                self.mUploadCustomerUserCredentialsToSiV(
                        _private_key_str, _public_key_details, _user_details)

            elif not _identity_user_key_details_list and _siv_user_key_details:

                self.mUploadCustomerUserCredentialsToIdentity(
                        _siv_user_key_details.get("public_key_details", {}).get('key_value'),
                        _user_details)

            elif _identity_user_key_details_list and not _siv_user_key_details:

                self.mDeleteUserKeyFromIdentity(_identity_user_key_details_list, _user_details)

                _private_key_str, _public_key_str = self.mCreateCustomerUserCredentials()
                _public_key_details = self.mUploadCustomerUserCredentialsToIdentity(
                                        _public_key_str, _user_details)
                self.mUploadCustomerUserCredentialsToSiV(
                        _private_key_str, _public_key_details, _user_details)

            elif _identity_user_key_details_list and _siv_user_key_details:

                ebLogInfo("Exacloud detected an already present valid User Key in SiV and "
                    f"in Identity. We'll compare the fingerprint")

                if not self.mCompareFingerPrints(_siv_user_key_details,
                        _identity_user_key_details_list):
                    # _private_key_str, _public_key_str = self.mCreateCustomerUserCredentials()
                    # _public_key_details = self.mUploadCustomerUserCredentialsToIdentity(
                    #         _public_key_str, _user_details)
                    # self.mUploadCustomerUserCredentialsToSiV(
                    #         _private_key_str, _public_key_details, _user_details)
                    raise ExacloudRuntimeError(0x095, 0xA, "FIXME, we need to recreate the key in here")

                ebLogInfo("VMBackup validation success for the vmbackup user: "
                    f"'{_customer_details.user_name}'")

        ebLogInfo(f"Exacloud completed the validation for users: '{_set_unique_user_name}'")

    def mSetupVMBackupClusterBucket(self)-> None:
        """
        Main driver method to make sure we have the VMBackup Setup for the User's bucket
        This includes:
            - Making sure the Compartment exists
            - Making sure the Bucket exists

        :raises ExacloudRuntimeError: If any fatal error occurs during this setup

        :returns: None

        """

        _set_unique_bucket_name = set()
        for _customer_details in self._customer_nodes_details:

            # Since the node details have all the details about all VMs,
            # we do a quick check to make sure we only ever check a bucket once
            # For now is ok if we check every compartment for every unique bucket
            if _customer_details.bucket_name in _set_unique_bucket_name:
                ebLogTrace(f"Already checked bucket: '{_customer_details.bucket_name}', skipping")
                continue

            _set_unique_bucket_name.add(_customer_details.bucket_name)

            # Check for "unique_customer_vmboss_compartment" value in exabox.conf
            # If set to True, use default compartment to create all VM backup 
            # buckets, otherwise, create a compartment for each VM
            _is_unique_compartment_set = \
                get_gcontext().mGetConfigOptions().get(
                        "vmbackup", {}).get("unique_customer_compartment", False)

            _parent_compartment = self._PARENT_COMPARTMENT_VMBOSS_OCID
            _compartment_name = self._COMPARTMENT_VMBOSS_NAME

            if str(_is_unique_compartment_set).lower() == 'true':
                ebLogInfo("Creating VM backup bucket in unique compartment.")
                _parent_compartment = self._COMPARTMENT_VMBOSS_OCID
                _compartment_name = _customer_details.compartment_name

            # TODO jfsaldan Needs review
            _compartment_deatails = self.mCheckCompartmentExists(
                                    _compartment_name,
                                    aParentCompartmentOcid=_parent_compartment)

            ebLogInfo(f"Using parent compartment: {_parent_compartment}")

            # Retrieve compartment details
            ebLogInfo(f"Will create bucket in compartment with name {_compartment_name}")
            if not _compartment_deatails:
                _compartment_deatails = self.mCreateCustomerCompartment(
                                        _compartment_name,
                                        aParentCompartmentOcid=_parent_compartment)

            # Create bucket to store backups, if not present
            ebLogInfo(f"Creating VM backup bucket in compartment: {_compartment_name}")
            if self._force_users_principals is True:
                if not self.mCheckBucketExists(_customer_details.bucket_name):
                    _user_details = self.mCheckIdentityHasUser(_customer_details.user_name)
                    self.mCreateBucket(
                        aUserDetails = _user_details,
                        aCompartmentDetails = _compartment_deatails,
                        aBucketName = _customer_details.bucket_name)

            # Create bucket without tagging
            else:
                if not self.mCheckBucketExists(_customer_details.bucket_name):
                    self.mCreateBucket(
                        aUserDetails = None,
                        aCompartmentDetails = _compartment_deatails,
                        aBucketName = _customer_details.bucket_name)

            # Create bucket to store metadata files, if not present
            if not self.mCheckBucketExists(_customer_details.bucket_metadata_name):
                self.mCreateBucket(
                    aUserDetails = None,
                    aCompartmentDetails = _compartment_deatails,
                    aBucketName = _customer_details.bucket_metadata_name)

            ebLogInfo("VMBackup validation success for the vmbackup bucket: "
                    f"'{_customer_details.bucket_name}'")

        ebLogInfo(f"Exacloud completed the validation for buckets: '{_set_unique_bucket_name}'")

    def mSetupVMBackupDom0Cache(self) -> dict:
        """
        This method will be in charge of updating the cache file in all the
        Dom0s from the payload, to create the mapping between DomU Customer
        FQDN and OSS info

        The file will be in: 'self._CACHE_FILE' on each Dom0
        Each Dom0 will have the data about it's own VMs, not about other Dom0s

        The file format for this file is json:

        R1Connector:
        {
            "nodes": [
                {
                    "vm_customer_name": "<vm_fqdn>",
                    "kms_endpoint": "<valt crypto endpoint>",
                    "kms_master_key_ocid": "<ocid.kms.....>",
                    "bucket_name": "vmboss_bucket_<customer_tenancny_id><cluster>",
                    "bucket_metadata_name": "vmboss_metadata_bucket_<customer_tenancny_id>,
                    "bucket_namespace": "<bucket_namespace>"
                },
                {
                    "vm_customer_name": "<vm_fqdn>",
                    "kms_endpoint": "<valt crypto endpoint>",
                    "kms_master_key_ocid": "<ocid.kms.....>",
                    "bucket_name": "vmboss_bucket_<customer_tenancny_id><cluster>",
                    "bucket_metadata_name": "vmboss_metadata_bucket_<customer_tenancny_id>,
                    "bucket_namespace": "<bucket_namespace>"
                }
            ]
        }

        ExaBoxConnector
        {
            "nodes": [
                {
                    "vm_customer_name": "<vm_fqdn>",
                    "kms_endpoint": "<valt crypto endpoint>",
                    "kms_master_key_ocid": "<ocid.kms.....>",
                    "bucket_name": "vmboss_bucket_<customer_tenancny_id><cluster>",
                    "bucket_metadata_name": "vmboss_metadata_bucket_<customer_tenancny_id>,
                    "bucket_namespace": "<bucket_namespace>",
                    "oci_certificate_path": "",
                    "oci_service_domain": ""
                },
                {
                    "vm_customer_name": "<vm_fqdn>",
                    "kms_endpoint": "<valt crypto endpoint>",
                    "kms_master_key_ocid": "<ocid.kms.....>",
                    "bucket_name": "vmboss_bucket_<customer_tenancny_id><cluster>",
                    "bucket_metadata_name": "vmboss_metadata_bucket_<customer_tenancny_id>,
                    "bucket_namespace": "<bucket_namespace>",
                    "oci_certificate_path": "",
                    "oci_service_domain": ""
                }
            ]
        }

        ConfigFileConnector
        {
            "nodes": [
                {
                    "vm_customer_name": "<vm_fqdn>",
                    "kms_endpoint": "<valt crypto endpoint>",
                    "kms_master_key_ocid": "<ocid.kms.....>",
                    "bucket_name": "vmboss_bucket_<customer_tenancny_id><cluster>",
                    "bucket_metadata_name": "vmboss_metadata_bucket_<customer_tenancny_id>,
                    "bucket_namespace": "<bucket_namespace>",
                    "oci_config_file": "<path to ociconf file>",
                    "oci_certificate_path": "",
                    "oci_service_domain": ""
                },
                {
                    "vm_customer_name": "<vm_fqdn>",
                    "kms_endpoint": "<valt crypto endpoint>",
                    "kms_master_key_ocid": "<ocid.kms.....>",
                    "bucket_name": "vmboss_bucket_<customer_tenancny_id><cluster>",
                    "bucket_metadata_name": "vmboss_metadata_bucket_<customer_tenancny_id>,
                    "bucket_namespace": "<bucket_namespace>",
                    "oci_config_file": "<path to ociconf file>",
                    "oci_certificate_path": "",
                    "oci_service_domain": ""
                }
            ]
        }

        RegionConnector
        {
            "nodes": [
                {
                    "vm_customer_name": "<vm_fqdn>",
                    "kms_endpoint": "<valt crypto endpoint>",
                    "kms_master_key_ocid": "<ocid.kms.....>",
                    "bucket_name": "vmboss_bucket_<customer_tenancny_id><cluster>",
                    "bucket_metadata_name": "vmboss_metadata_bucket_<customer_tenancny_id>,
                    "bucket_namespace": "<bucket_namespace>",
                    "oci_region": "",
                    "oci_domain": ""
                },
                {
                    "vm_customer_name": "<vm_fqdn>",
                    "kms_endpoint": "<valt crypto endpoint>",
                    "kms_master_key_ocid": "<ocid.kms.....>",
                    "bucket_name": "vmboss_bucket_<customer_tenancny_id><cluster>",
                    "bucket_metadata_name": "vmboss_metadata_bucket_<customer_tenancny_id>,
                    "bucket_namespace": "<bucket_namespace>",
                    "oci_region": "",
                    "oci_domain": ""
                }
            ]
        }


        :returns: a dictionary with the json contents of all the Dom0s
        """


        # Get crypto endpoint
        _oss_crypto_endpoint = get_gcontext().mGetConfigOptions().get(self.CONFIG_CRYPTO_EP)
        if _oss_crypto_endpoint:
            ebLogInfo(f"Exacloud found crypto endpoint: '{_oss_crypto_endpoint}'")
        else:
            _msg = (f"Exacloud didn't find the crypto endpoint in exabox.conf "
                f"in the field: '{self.CONFIG_CRYPTO_EP}'. This field is needed if "
                "oss vm backup is enabled, please add the proper value of "
                f"the field '{self.CONFIG_CRYPTO_EP}' and retry the step")
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)

        # Get master key ocid
        _oss_master_key_ocid = get_gcontext().mGetConfigOptions().get(self.CONFIG_MASTER_KEY_OCID)
        if _oss_master_key_ocid:
            ebLogInfo(f"Exacloud found crypto endpoint: '{_oss_master_key_ocid}'")
        else:
            _msg = (f"Exacloud didn't find the master key ocid in exabox.conf "
                f"in the field: '{self.CONFIG_MASTER_KEY_OCID}'. This field is needed if "
                "oss vm backup is enabled, please add the proper value of "
                f"the field '{self.CONFIG_MASTER_KEY_OCID}' and retry the step")
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)

        _mapping = {}

        for _customer_details in self._customer_nodes_details:

            with connect_to_host(_customer_details.dom0, get_gcontext()) as _node:

                # Make sure the directory exists
                _cmd_str = f"/bin/mkdir -p {os.path.dirname(self._CACHE_FILE)}"
                ebLogTrace(f"Running: '{_cmd_str}' in: '{_customer_details.dom0}'")
                _out_mkdir = node_exec_cmd_check(_node, _cmd_str)
                ebLogTrace(f"Output: '{_out_mkdir}' in: '{_customer_details.dom0}'")

                # Check if file is present
                if _node.mFileExists(self._CACHE_FILE):

                    _cmd_str = f"/bin/cat {self._CACHE_FILE}"
                    ebLogTrace(f"Running: '{_cmd_str}' in: '{_customer_details.dom0}'")
                    _out_cache_file = node_exec_cmd_check(_node, _cmd_str)
                    _remote_cache_content = _out_cache_file.stdout.strip()
                    _remote_cache_content = json.loads(_remote_cache_content)

                # If not present, initialize an empty dictionary as content. we'll copy
                # the file later
                else:
                    _remote_cache_content = {"nodes": []}


                # Search the customer domu name in the remote cache file contents
                _found = False
                for _idx, _cache_node_info in enumerate(_remote_cache_content.get("nodes", [])):

                    # If present, compare the values
                    if _cache_node_info.get("vm_customer_name", "") == _customer_details.domU:
                        ebLogInfo(f"Exacloud detected the remote file from: '{_customer_details.dom0}' "
                            f"to have already the DomU: '{_customer_details.domU}' details: "
                            f"'{_cache_node_info}'")

                        # Make sure the cache has correct values
                        if (_cache_node_info.get("bucket_name") != _customer_details.bucket_name or
                                _cache_node_info.get("bucket_namespace") != self._NAMESPACE_TENANCY_OCID):
                            ebLogWarn(f"Exacloud detectd the remote cache to have: "
                                f"'{_cache_node_info}', which doesn't match the payload "
                                f"values: Bucket: '{_customer_details.bucket_name}', "
                                f"Bucket Namespace: '{self._NAMESPACE_TENANCY_OCID}'"
                                "We will override this")
                            _remote_cache_content.get("nodes").pop(_idx)

                        else:
                            ebLogInfo("Exacloud detected the remote cache to have the "
                                f"same values as the payload. We will do nothing here")
                            _found = True
                        break

                if _found is False:
                    ebLogInfo(f"Exacloud detected the domU: '{_customer_details.domU}' to be missing "
                        f"or incorrect in: {_customer_details.dom0} cache file, we'll add it.")

                    # Based on the region type, build the node specific info to use
                    # to populate the cache file
                    _oci_factory = ExaOCIFactory()
                    _connector = _oci_factory.get_oci_connector()

                    # Use Users Principals
                    if self._force_users_principals is True:

                        _node_details = {
                            "vm_customer_name": _customer_details.domU,
                            "kms_endpoint": _oss_crypto_endpoint,
                            "kms_master_key_ocid": _oss_master_key_ocid,
                            "bucket_name": _customer_details.bucket_name,
                            "bucket_metadata_name": _customer_details.bucket_metadata_name,
                            "config_file": f"/opt/oracle/vmbackup/ociconf/oci_config_{_customer_details.domU}",
                            "bucket_namespace": self._NAMESPACE_TENANCY_OCID
                            }

                    # For R1, we copy the certificate from the local dir
                    # to self.CERTIFICATE_R1_REMOTE_PATH and set its parameter in vmbackup.conf
                    elif isinstance(_connector, R1Connector):

                        _node_details = {
                            "vm_customer_name": _customer_details.domU,
                            "kms_endpoint": _oss_crypto_endpoint,
                            "kms_master_key_ocid": _oss_master_key_ocid,
                            "bucket_name": _customer_details.bucket_name,
                            "bucket_metadata_name": _customer_details.bucket_metadata_name,
                            "bucket_namespace": self._NAMESPACE_TENANCY_OCID
                            }

                    elif isinstance(_connector, ExaboxConfConnector):

                        _service_domain = get_gcontext(
                            ).mGetConfigOptions().get("oci_service_domain")
                        _node_details = {
                            "vm_customer_name": _customer_details.domU,
                            "kms_endpoint": _oss_crypto_endpoint,
                            "kms_master_key_ocid": _oss_master_key_ocid,
                            "bucket_name": _customer_details.bucket_name,
                            "bucket_metadata_name": _customer_details.bucket_metadata_name,
                            "bucket_namespace": self._NAMESPACE_TENANCY_OCID,
                            "oci_certificate_path": self.CERTIFICATE_CUSTOM,
                            "oci_service_domain": _service_domain
                            }

                    else:

                        _node_details = {
                            "vm_customer_name": _customer_details.domU,
                            "kms_endpoint": _oss_crypto_endpoint,
                            "kms_master_key_ocid": _oss_master_key_ocid,
                            "bucket_name": _customer_details.bucket_name,
                            "bucket_metadata_name": _customer_details.bucket_metadata_name,
                            "bucket_namespace": self._NAMESPACE_TENANCY_OCID
                            }


                    # Finished building detials of node
                    ebLogInfo(f"Exacloud to add below contents to dom0: '{_customer_details.dom0}': "
                            f"'{_node_details}'")
                    _remote_cache_content.get("nodes").append(_node_details)

                    # Override the remote file with the new mapping
                    # We use the 'PASS' comment to avoid logging this in exacloud
                    # logs/traces
                    _content_to_write = json.dumps(_remote_cache_content, indent=4)
                    _cmd_str = f"/bin/echo \'{_content_to_write}\' > {self._CACHE_FILE} #NOLOG pass"
                    _out_writing_content = node_exec_cmd_check(_node, _cmd_str)

        return _mapping


    def mUploadCustomerUserCredentialsToDom0(self)-> None:
        """
        This method will try to populate the VMBackup User's Credentials
        in the Dom0s

        :returns: None
        """

        for _customer_details in self._customer_nodes_details:

            # Read Remote CACHE File and get key_file location
            # We expect the key_file to be empty, the vmbackup tool
            # will make sure of deleting it
            with connect_to_host(_customer_details.dom0, get_gcontext()) as _node:

                # Check if file is present
                if _node.mFileExists(self._CACHE_FILE):

                    _cmd_str = f"/bin/cat {self._CACHE_FILE}"
                    ebLogTrace(f"Running: '{_cmd_str}' in: '{_customer_details.dom0}'")
                    _out_cache_file = node_exec_cmd_check(_node, _cmd_str)
                    ebLogTrace(f"Output: '{_out_cache_file}' in: '{_customer_details.dom0}'")
                    _remote_cache_content = _out_cache_file.stdout.strip()
                    _remote_cache_content = json.loads(_remote_cache_content)

                # If not present, we raise an exception
                else:
                    _err = (f"Exacloud detected that the file '{self._CACHE_FILE}' "
                        f"is not present in: '{_customer_details.dom0}'. This is not expected at this point. "
                        "please retry this step and populate the file: '{self._CACHE_FILE}'")
                    ebLogError(_err)
                    raise ExacloudRuntimeError(0x095, 0xA, _err)

                _found = False
                for _cache_node_info in _remote_cache_content.get("nodes", []):

                    # If present, compare the values
                    if _cache_node_info.get("vm_customer_name", "") == _customer_details.domU:
                        ebLogInfo(f"Exacloud detected the remote file from: '{_customer_details.dom0}' "
                            f"to have the details: "
                            f"'{_cache_node_info}'")
                        _found = True

                        _remote_config_file_path = _cache_node_info.get("config_file", None)

                        # If not there, raise exception
                        if not _remote_config_file_path:
                            _err = (f"Exacloud detected that the file '{self._CACHE_FILE}' "
                                f"to be missing a valid config_file path for: '{_customer_details.domU}'"
                                f"please retry this step and populate the file: '{self._CACHE_FILE}'")
                            ebLogError(_err)
                            raise ExacloudRuntimeError(0x095, 0xA, _err)

                        # If present, we populate it
                        _remote_key_file = os.path.join(
                                os.path.dirname(_remote_config_file_path),
                                f"key_file_{_customer_details.domU}")

                        _siv_user_key_details = self.mGetUserKeyFromSiV(_customer_details.user_name)
                        _remote_config = configparser.ConfigParser()
                        _remote_config["DEFAULT"] = {
                                "user": _siv_user_key_details.get("public_key_details").get("user_id"),
                                "fingerprint": _siv_user_key_details.get("public_key_details").get("fingerprint"),
                                "tenancy": self._ecra_su_config.get("tenancy"),
                                "region" : self._ecra_su_config.get("region"),
                                "key_file": _remote_key_file
                            }

                        # Create local tmp file with config parser info
                        # and copy it to the dom0
                        with NamedTemporaryFile(
                                mode='w', delete=True) as _tmp_file:
                            _remote_config.write(_tmp_file)
                            _tmp_file.flush()
                            _node.mCopyFile(_tmp_file.name,
                                    _remote_config_file_path)

                        ebLogInfo(f"Exacloud updated the config file: '{_remote_config_file_path}'")

                        # Create local tmp file with Private Key
                        # and copy it to the dom0
                        with NamedTemporaryFile(
                                mode='w', delete=True) as _tmp_file:
                            _tmp_file.write(_siv_user_key_details.get("private_key"))
                            _tmp_file.flush()
                            _node.mCopyFile(_tmp_file.name,
                                    _remote_key_file)

                        ebLogInfo(f"Exacloud updated the key file: '{_remote_key_file}'")


    def mUploadCertificatesToDom0(self):
        """
        This method will try copy the Certificate needed to each Dom0 from the
        payload.
        If not Cert is needed, it will do nothing

        :raises ExacloudRuntimeError: If an error happens in the middle
        :returns: None
        """

        _oci_factory = ExaOCIFactory()
        _connector = _oci_factory.get_oci_connector()

        # For R1, we copy the certificate from the local dir
        # to self.CERTIFICATE_R1_REMOTE_PATH and set its parameter in vmbackup.conf
        if isinstance(_connector, R1Connector):
            ebLogInfo("Exacloud detected the environment to be R1, copying certificate "
                f"from local file: '{get_r1_certificate_path()}' to each Dom0 on: "
                f"'{self.CERTIFICATE_R1_REMOTE_PATH}'")

            # Copy the certificate to all Dom0s
            for _customer_details in self._customer_nodes_details:
                with connect_to_host(_customer_details.dom0, get_gcontext()) as _node:

                    #Make sure parent dir exists
                    node_exec_cmd_check(_node,
                            f"/bin/mkdir -p {os.path.dirname(self.CERTIFICATE_R1_REMOTE_PATH)}")
                    _node.mCopyFile(get_r1_certificate_path(),
                            self.CERTIFICATE_R1_REMOTE_PATH)

        elif isinstance(_connector, ExaboxConfConnector):

            ebLogInfo("Nothing to do for custom certificates!")

            # Below logic is commented for now.
            # We will test this below logic later, which is to be used in non-commercial regions
            _certificate_path = get_gcontext().mGetConfigOptions().get("oci_certificate_path")
            _service_domain = get_gcontext().mGetConfigOptions().get("oci_service_domain")
            if _certificate_path and _service_domain:
                ebLogInfo("Exacloud detected the environment to be non-commercial "
                    f"region, copying certificate from local file: "
                    f"'{_certificate_path}' to each Dom0 on: '{self.CERTIFICATE_CUSTOM}'")

                # Copy the certificate to all Dom0s
                for _customer_details in self._customer_nodes_details:
                    with connect_to_host(_customer_details.dom0, get_gcontext()) as _node:
                        node_exec_cmd_check(_node,
                                f"/bin/mkdir -p {os.path.dirname(self.CERTIFICATE_CUSTOM)}")
                        _node.mCopyFile(_certificate_path, self.CERTIFICATE_CUSTOM)

        elif isinstance(_connector, DefaultConnector):
            ebLogInfo("Exacloud detected the environment to be a commercial "
                "region, no need to copy any certificate nor to patch the service "
                "endpoint in the vmbackup.conf file")

        # Raise error is we can't detect the region
        else:
            _msg = ("Exacloud was not able to detect the current region, this is not "
                f"expected to happen. Connector type: {type(_connector)}")
            ebLogError(_msg)


    @retry(aRetriesLimit=5, aSleep=5)
    def mDeleteVMBackupBucket(self, aBucketName)-> None:
        """
        This method will try to delete the bucket aBucketName from the namespace of the
        object storage client

        :param aBucketName: a string representing the bucket name to delete
        """

        # Nothing is sensitive here, we can log it
        ebLogInfo(f"Exacloud is about to delete a bucket with name: '{aBucketName}'")

        # Trigger call and fail on error
        try:
           _response = self._object_storage_client.delete_bucket(
                   namespace_name = self._NAMESPACE_TENANCY_OCID,
                   bucket_name = aBucketName)

        except oci.exceptions.ServiceError as _oci_excep:
            if _oci_excep.status == 409 and _oci_excep.code == 'BucketNotEmpty':
                _err = (f"Exacloud couldn't delete the Bucket with name: "
                                f"'{aBucketName}' with the ECRA Super User since there are existing objects. "
                                f"status: {_oci_excep.status}, code: {_oci_excep.code}")
                ebLogWarn(_err)
                self.mForceDeleteAllObjectsInBucket(aBucketName)
            else:
                _err = (f"Exacloud couldn't delete the Bucket with name: "
                        f"'{aBucketName}' with the ECRA Super User. "
                        f"Please review the IAM setup for the host where Exacloud is running. "
                        f"status: {_oci_excep.status}, code: {_oci_excep.code}")
                ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from _oci_excep

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}', response headers: {_response.headers}")
        ebLogInfo(f"Delete with success a bucket with name: '{aBucketName}'")


    def mForceDeleteAllObjectsInBucket(self, aBucketName):
        """
        This method will delete all available backups on the input bucket.
        """
        ebLogTrace(f"Exacloud is about to delete all objects on the bucket with name: {aBucketName}")

        # Trigger call to fetch list of all objects available on the bucket.
        try:
           list_objects_response = self._object_storage_client.list_objects(
                   namespace_name = self._NAMESPACE_TENANCY_OCID,
                   bucket_name = aBucketName)
        except Exception as _oci_excep:
            ebLogError(f"Failed to fetch list of available objects in bucket {aBucketName}, Reason: {_oci_excep}")

        else:
            for _oci_obj in list_objects_response.data.objects:
                _current_object_name = _oci_obj.name
                ebLogTrace(f"Deleting {_current_object_name} from bucket {aBucketName}")
                try:
                    delete_object_response = self._object_storage_client.delete_object(
                        namespace_name = self._NAMESPACE_TENANCY_OCID,
                        bucket_name = aBucketName,
                        object_name = _current_object_name)
                    ebLogTrace(f"Successfully deleted {_current_object_name} from bucket {aBucketName}")
                except Exception as _oci_excep:
                    ebLogError(f"Failed to delete object {_current_object_name} "
                        f"from bucket {aBucketName}, Reason: {_oci_excep}")

        # Trigger call to fetch list of all object versions available on the
        # bucket.
        try:
           list_objects_response = self._object_storage_client.list_object_versions(
                   namespace_name = self._NAMESPACE_TENANCY_OCID,
                   bucket_name = aBucketName)
        except Exception as _oci_excep:
            ebLogError("Failed to fetch list of available object versions in bucket "
                f"{aBucketName}, Reason: {_oci_excep}")

        else:
            for _oci_obj in list_objects_response.data.items:
                _current_object_name = _oci_obj.name
                _current_object_version = _oci_obj.version_id
                ebLogTrace(f"Deleting {_current_object_name} with version id "
                    f"{_current_object_version} from bucket {aBucketName}")
                try:
                    delete_object_response = self._object_storage_client.delete_object(
                        namespace_name = self._NAMESPACE_TENANCY_OCID,
                        bucket_name = aBucketName,
                        object_name = _current_object_name,
                        version_id = _current_object_version)
                    ebLogTrace(f"Successfully deleted {_current_object_name} from bucket {aBucketName}")
                except Exception as _oci_excep:
                    ebLogError(f"Failed to delete object {_current_object_name} "
                        f"from bucket {aBucketName}, Reason: {_oci_excep}")

        # Trigger call to fetch list of all uncomitted objects available on the
        # bucket.
        try:
           list_multipart_uploads_response = self._object_storage_client.list_multipart_uploads(
                   namespace_name = self._NAMESPACE_TENANCY_OCID,
                   bucket_name = aBucketName)
        except Exception as _oci_excep:
            ebLogError("Failed to fetch list of multipart object in bucket "
                f"{aBucketName}, Reason: {_oci_excep}")

        else:
            if len(list_multipart_uploads_response.data) == 0:
                ebLogInfo(f"Not multipart uploads found for {aBucketName}")

            for _multi_part_obj in list_multipart_uploads_response.data:
                _current_multipart_object= _multi_part_obj.object
                _current_object_uploadId = _multi_part_obj.upload_id
                ebLogTrace(f"Aborting {_current_multipart_object} with upload id "
                    f"{_current_object_uploadId} from bucket {aBucketName}")
                try:
                    abort_multipart_upload_response = self._object_storage_client.abort_multipart_upload(
                        namespace_name = self._NAMESPACE_TENANCY_OCID,
                        bucket_name = aBucketName,
                        object_name = _current_multipart_object,
                        upload_id = _current_object_uploadId)
                    ebLogTrace(f"Successfully aborted {_current_multipart_object} from bucket {aBucketName}")
                except Exception as _oci_excep:
                    ebLogError(f"Failed to abort multipart upload {_current_multipart_object} "
                        f"from bucket {aBucketName}, Reason: {_oci_excep}")

        ebLogInfo("Exacloud deleted all objects on the bucket with name: "
            f"{aBucketName}")

    def mDeleteVMBackupClusterBucket(self):
        """
        Orchestrates the deletion of the buckets during Delete Service.
        For now, buckets are created at a customer cluster level.
        """

        _set_unique_bucket_name = set()
        for _customer_details in self._customer_nodes_details:

            # Since the node details have all the details about all VMs,
            # we do a quick check to make sure we only ever check a bucket once
            # For now is ok if we check every compartment for every unique bucket
            if _customer_details.bucket_name in _set_unique_bucket_name:
                ebLogTrace(f"Already checked bucket: '{_customer_details.bucket_name}', skipping")
                continue

            _set_unique_bucket_name.add(_customer_details.bucket_name)

            if not self.mCheckBucketExists(_customer_details.bucket_name):
                ebLogInfo("Exacloud detected no bucket with name: "
                    f"'{_customer_details.bucket_name}'")
            else:
                ebLogInfo("Exacloud detected a bucket with name: "
                    f"'{_customer_details.bucket_name}'. Deleting it...")
                self.mDeleteVMBackupBucket(_customer_details.bucket_name)

            ebLogInfo("VMBackup bucket deletion finished ok for the bucket: "
                    f"'{_customer_details.bucket_name}'")

