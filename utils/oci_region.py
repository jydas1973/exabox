"""
$Header:

 Copyright (c) 2014, 2023, Oracle and/or its affiliates.

NAME:
    oci_region.py - Base Class for cryptography testing

FUNCTION:
    This class handles the OCI region file, creation and update.

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    ndesanto    04/29/22 - Store region info in DB cache.
    ndesanto    04/13/22 - Retrieve region directly from cavium.
    ndesanto    01/13/22 - OCI regions file related functions.
    ndesanto    01/12/21 - Creation of the file
"""

import base64
import json
import os
from typing import Any

from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInit, ebLogInfo, ebLogError, ebLogVerbose, ebLogWarn
from exabox.agent.ExaLock import ExaLock
from exabox.config.Config import get_value_from_exabox_config
from exabox.utils.ExaRegion import get_region_info
from exabox.utils.common import read_json_into_string
from exabox.core.DBStore import ebGetDefaultDB


__basepath: str = os.path.abspath(os.path.dirname(__file__) + "/../..")
REGION_LOCK = f"{__basepath}/region.lock"


def _get_region_from_db_cache() -> dict:
    _out = None
    _db = ebGetDefaultDB()
    _db.mCreateDataCacheTable()
    _dataStr= _db.mGetDataFromDataCacheByName("region")
    if _dataStr:
        _out = json.loads(_dataStr)

    return _out


def parse_region_info(aBase64Msg: str) -> dict:
    _region_info = {}
    if aBase64Msg:
        _region_str = base64.b64decode(aBase64Msg).decode('utf-8')
        _region_info = json.loads(_region_str)
    
    return _region_info


def _set_region_to_db_cache(aRegionInfo: dict) -> None:
    _data = json.dumps(aRegionInfo)
    _db = ebGetDefaultDB()
    _db.mCreateDataCacheTable()
    _dataStr = _db.mGetDataFromDataCacheByName("region")
    if _dataStr:
        _db.mUpdateDataCache("region", _data)
    else:
        _db.mInsertDataCache("region", _data)


def load_oci_region_config() -> dict:
    #Check if value is cached
    _region = _get_region_from_db_cache()

    if not _region:
        # Retrieve from server
        _region = get_region_info()
        if _region:
            # Save to cache
            with ExaLock(REGION_LOCK):
                _set_region_to_db_cache(_region)

    return _region


def get_oci_config(aRealmKey: str, aRealmDomainComponent: str, \
    aRegionKey: str, aRegionIdentifier: str) -> dict:

    _config: dict = {
        "realmKey": aRealmKey, 
        "realmDomainComponent": aRealmDomainComponent, 
        "regionKey": aRegionKey, 
        "regionIdentifier": aRegionIdentifier
    }
    return _config


def get_value(aDict: dict, aKey: str, aDefault: str="") -> Any:
    return aDict[aKey] if aKey in aDict else aDefault


def update_oci_config(aConfig: dict) -> None:
    """
    Creates/overrides a regions config entry on the DB cache
    """
    try:
        with ExaLock(REGION_LOCK):
            _set_region_to_db_cache(aConfig)
    except Exception as e:
        _msg = "Cannot create regions DB cache entry."
        ebLogError(_msg)
        raise ExacloudRuntimeError(aErrorMsg=_msg) from e

def load_config_bundle():
    """
    Load json file /opt/oci/config_bundle/exacc.json
    """
    _exacc_config_path:str = get_value_from_exabox_config("exacc_config_file", \
        os.path.join(__basepath, "config/exabox.conf"))
    _config_bundle = read_json_into_string(_exacc_config_path)
    return _config_bundle