#!/bin/python
#
# $Header: ecs/exacloud/exabox/utils/ExaRegion.py /main/11 2025/04/23 04:55:22 aypaul Exp $
#
# ExaRegion.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      ExaRegion.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/21/25 - Bug#37492328 Cache details fetched from the IMDS
#                           endpoint.
#    jfsaldan    12/11/24 - Bug 37352485 - EXACS:24.4.2.1:VMBACKUP TO OSS ON
#                           PREPROD : ON DEMAND BACKUP FAILED - THE ROOT
#                           COMPARTMENT SEEMS TO NOT BE CALCULATED PROPERLY
#    ririgoye    10/24/23 - Bug 35919782 - Add retries for Instance Principals
#                           creation
#    jfsaldan    09/14/23 - Bug 35811483 - EXACLOUD SHOULD NOT RELY ON THE
#                           VAULT OCID FROM EXABOX.CONF TO CHECK IF VMBACKUP
#                           BUCKETS NEED TO BE DELETED DURING DELETE SERVICBug
#                           35811483 - EXACLOUD SHOULD NOT RELY ON THE VAULT
#                           OCID FROM EXABOX.CONF TO CHECK IF VMBACKUP BUCKETS
#                           NEED TO BE DELETED DURING DELETE SERVICE
#    hcheon      08/30/23 - 35197827 Use OCI instance metadata v2
#    jfsaldan    04/26/23 - Enh 35207526 - Add support in ExaOCI to use Users
#                           Principals in non-commercial regions
#    ndesanto    04/13/22 - Retrieve region directly from cavium.
#    ndesanto    04/13/22 - Creation
#

import six
import json
import os
import urllib
import urllib.request
import urllib.error
import copy

URLError = urllib.error.URLError
HTTPError = urllib.error.HTTPError

from time import sleep
from exabox.log.LogMgr import ebLogInit, ebLogInfo, ebLogError, ebLogVerbose, ebLogWarn, ebLogTrace
from exabox.core.Context import get_gcontext

MAX_URL_REQ_RETRIES = 3
RETRY_WAIT_TIME = 30
CAVIUM_URL = "http://169.254.169.254/opc/v2/instance"
R1_REGION = "sea"
REGION_CACHE_NAME = "exaregion_information"
REGION_INFO_KEYS = {"region_info": "regionInfo", "region": "region", "canonical_region_name": "canonicalRegionName", 
                    "instance_compartment": "compartmentId", "instance_root_compartment": "tenantId"}

def fetch_and_cache_region_details(aUrl: str=None, aType: str=None):

    _information_type = aType
    if aType is None:
        return None

    if not get_gcontext().mCheckRegEntry(REGION_CACHE_NAME):
        get_gcontext().mSetRegEntry(REGION_CACHE_NAME, {})
    _current_region_information = get_gcontext().mGetRegEntry(REGION_CACHE_NAME)
    if _current_region_information.get(_information_type, None) is not None:
        ebLogTrace(f"Returning {_information_type} from region cache information: {_current_region_information.get(_information_type)}")
        return _current_region_information.get(_information_type)

    _imdsv2_url = aUrl
    if not _imdsv2_url:
        _imdsv2_url = f"{CAVIUM_URL}/{REGION_INFO_KEYS.get(_information_type)}"
    _resp_data = _handle_url_req(_imdsv2_url)

    if _information_type == "region_info" and _resp_data:
        _data = json.loads(_resp_data)
        # Special case for R1, change "region1" to "R1_ENVIRONMENT"
        if "realmKey" in _data:
            if _data["realmKey"] == "region1":
                _data["realmKey"] = "R1_ENVIRONMENT"
        _current_region_information[_information_type] = copy.deepcopy(_data)
    elif _resp_data:
        _current_region_information[_information_type] = copy.deepcopy(_resp_data)
    else:
        return None
        
    get_gcontext().mSetRegEntry(REGION_CACHE_NAME, _current_region_information)
    return _current_region_information[_information_type]

def get_region_info(aUrl: str=None) -> dict:
    return fetch_and_cache_region_details(aUrl, "region_info")

def get_region(aUrl: str=None) -> str:
    return fetch_and_cache_region_details(aUrl, "region")

def is_r1_region() -> bool:
    _out = False
    _region_info = get_region(None)
    if _region_info and R1_REGION in _region_info:
        _out = True
    return _out

def get_r1_certificate_path() -> str:
    _ca_path = os.path.abspath("exabox/kms/combined_r1.crt")
    return _ca_path

def get_canonical_region_name(aUrl: str=None) -> str:
    return fetch_and_cache_region_details(aUrl, "canonical_region_name")

def get_instance_compartment(aUrl: str=None) -> str:
    return fetch_and_cache_region_details(aUrl, "instance_compartment")

def get_instance_root_compartment(aUrl: str=None) -> str:
    return fetch_and_cache_region_details(aUrl, "instance_root_compartment")

def _handle_url_req(aUrl: str=None) -> str:
    _url = aUrl
    _header = {'Authorization': 'Bearer Oracle'}
    _request = urllib.request.Request(_url, None, _header)
    for retry in range(MAX_URL_REQ_RETRIES):
        try:
            return six.ensure_str(urllib.request.urlopen(_request).read())
        except HTTPError as e:
            ebLogError(f"The server couldn\'t fulfill the request due to the following error: {e}")
            ebLogError(f"Error code: {e.code}")
        except URLError as e:
            ebLogError(f"Got URLError during request: {e}\n Reason for URLError: {e.reason}")
        except Exception as e:
            ebLogError(f"Failure during URL request handling: {e}")

        if retry < MAX_URL_REQ_RETRIES - 1:
            sleep(RETRY_WAIT_TIME) 

    ebLogError(f"Could not fulfill the request to {_url} after {MAX_URL_REQ_RETRIES} retries.")
    return None 
