#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/utils/common.py /main/13 2025/11/24 08:39:15 aypaul Exp $
#
# common.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      common.py - Common utilities with no particular business logic.
#
#    DESCRIPTION
#      This module contains a small set of functions/utilities with no
#      particular business logic. It is intended that this module should
#      remain independent from ExaCloud.
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      11/10/25 - ER#37732654 Update vault credentials for ecra
#                           connection.
#    aypaul      08/08/25 - Enh#37732728 Add common methods for generating ECRA
#                           database connection.
#    aypaul      05/21/25 - Bug#37948804 Implement a generic decorator to wrap
#                           a function using try-catch block.
#    jfsaldan    10/29/24 - Bug 37180445 - OCIEXACC: ELASTIC: SYNCUP_CELLS STEP
#                           MIGHT FAIL WHEN DECODING EXACLI PASSWORD IF THE
#                           PASSWORD HAPPENS TO BE A VALID BASE64 STRING
#    ririgoye    09/01/23 - Bug 35769896 - PROTECT YIELD KEYWORDS WITH
#                           TRY-EXCEPT BLOCKS
#    ndesanto    01/24/23 - Added functions to perform system model compare
#    aararora    08/18/22 - Get available size of a local directory
#    aypaul      08/17/22 - Bug#34500653 Mask sensitive information from
#                           payload.
#    scoral      07/11/22 - Added build_dict_from_table.
#    jfsaldan    06/07/22 - Add function to verify base64 on string
#    scoral      05/17/22 - Added version_compare.
#    scoral      07/05/21 - Creation
#

import os
import json
import base64
import binascii
import shutil
import traceback
import sys
from typing import Callable, List, TypeVar, Iterable, Mapping, Sequence
from itertools import tee, dropwhile
from xmlrpc.client import Boolean
from contextlib import contextmanager
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogTrace
from exabox.core.Context import get_gcontext

ECRADBDETAILSREGISTRY = "ecradbdetails"

A = TypeVar('A')

@contextmanager
def connect_to_ecradb():
    #Initialise a thick connection handle for executing queries against the ECRA database.
    #Returns a contextmanager with the connected ecra database. The connection handle will be automatically closed.
    try:
        _ecradb_details = get_ecradb_details()
        import oracledb
        oracledb.init_oracle_client()
        oraconn = oracledb.connect(user =         _ecradb_details.get('user'), \
                                   password =     _ecradb_details.get('password'),\
                                   host =         _ecradb_details.get('host'), \
                                   port =         _ecradb_details.get('port'), \
                                   service_name = _ecradb_details.get('service_name'))
        yield oraconn
    except StopIteration as e:
        ebLogError(f"Error during node connection yielding: {e}")
    except ImportError as ie:
        ebLogWarn(f"Failed to import python library: {ie}")
    finally:
        if 'connection' in locals() and oraconn:
            oraconn.close()

def get_ecradb_details():
    ECRADBDETAILSFILE = get_gcontext().mCheckConfigOption("ecrad_db_secrets").get("db_conn_details")
    ECRADBAPPUSERCRED = get_gcontext().mCheckConfigOption("ecrad_db_secrets").get("db_conn_creds")
    
    if not get_gcontext().mCheckRegEntry(ECRADBDETAILSREGISTRY):
        get_gcontext().mSetRegEntry(ECRADBDETAILSREGISTRY, None)
    _ecradb_details = get_gcontext().mGetRegEntry(ECRADBDETAILSREGISTRY)
    if _ecradb_details is not None:
        return _ecradb_details
    _ecradb_details = {}

    _vault_id = get_gcontext().mCheckConfigOption("ecra_vault_id")
    _retries = 5
    _attempts = 1
    if _vault_id is not None:
        from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
        _ecra_secrets = [ECRADBDETAILSFILE, ECRADBAPPUSERCRED]
        for _secret in _ecra_secrets:
            while _attempts <= _retries:
                try:
                    _factory = ExaOCIFactory()
                    _secrets_client = _factory.get_secrets_client()
                    ebLogInfo(f"Checking for ECRA database details in OCI vault: {_vault_id}, fetching secret: {_secret}")

                    _response = _secrets_client.get_secret_bundle_by_name(
                                secret_name = _secret,
                                vault_id = _vault_id)
                    ebLogTrace(f"Request ID is: '{_response.request_id}'")
                    _contents = _response.data.secret_bundle_content.content
                    _contents_json_base64decoded = base64.b64decode(_contents.encode("utf-8"))
                    if type(_contents_json_base64decoded) is bytes:
                        _contents_json_base64decoded = _contents_json_base64decoded.decode("utf-8")
                    if _secret == ECRADBDETAILSFILE:
                        _ecradb_details = json.loads(_contents_json_base64decoded)
                    else:
                        _ecradb_details["password"] = _contents_json_base64decoded
                    break
                except Exception as ex:
                    ebLogError(f"Failed to fetch ECRA database details from OCI vault: {_vault_id}. Exception: {ex}")
                    _attempts += 1
    else:
        ebLogInfo("Checking for ECRA database details in deployment.config")
        _deployment_config_file = os.path.abspath(os.path.join(get_gcontext().mGetBasePath(), "../../../../deployment/state/deployment.config"))
        _deployment_config = {}
        if os.path.exists(_deployment_config_file):
            with open(_deployment_config_file) as fd:
                _deployment_config = json.load(fd)
        else:
            ebLogWarn(f"Deployment config does not exist at path: {_deployment_config_file}")
            return {}

        _ecradb_details_keys = {"user": "ecrauser","password": "ecrapasswd","host": "db_host","port": "sdb_port","service_name": "sdb_service"}
        ecradb_info_dict = _deployment_config["runtime"]["db"]
        for _key in _ecradb_details_keys.keys():
            _deployment_key = _ecradb_details_keys[_key]
            if _deployment_key in ecradb_info_dict.keys():
                _ecradb_details[_key] = ecradb_info_dict[_deployment_key]
    
    get_gcontext().mSetRegEntry(ECRADBDETAILSREGISTRY, _ecradb_details)
    return get_gcontext().mGetRegEntry(ECRADBDETAILSREGISTRY)

def mask_keys_json(_input_json: dict, _key_to_mask: str) -> None:

    if type(_input_json) is dict:
        _current_keys = list(_input_json.keys())
        for _current_key in _current_keys:
            _current_value = _input_json[_current_key]
            if _key_to_mask.lower() == _current_key.lower():
                _input_json[_current_key] = "**********"
            elif type(_current_value) is dict or type(_current_value) is list:
                mask_keys_json(_current_value, _key_to_mask)
    elif type(_input_json) is list:
        for _list_item in _input_json:
            if type(_list_item) is str:
                continue
            elif type(_list_item) is dict or type(_list_item) is list:
                mask_keys_json(_list_item, _key_to_mask)


def tails(seq: Iterable[A]) -> Iterable[Iterable[A]]:
    """
    Generates a sequence of all possible non-empty tails of an iterable.

    Examples:

    tails([1, 2, 3]) = [[1, 2, 3], [2, 3], [3]]

    tails([1, 2, 3, ...]) =
    [[1, 2, 3, ...], [2, 3, 4, ...], [3, 4, 5, ...], ...]

    tails([]) = []

    :param seq: Iterable to obtain all non-empty tails.
    :returns: Generator of Iterables of all non-empty tails of an iterable.
    """
    try:
        seq_it, seq_next = tee(iter(seq))
        next(seq_next)
        yield seq_it
        yield from tails(seq_next)
    except StopIteration:
        return


def version_compare(ver1: str, ver2: str) -> int:
    """
    Compares two version strings.
    
    Examples:

    version_compare('2.1.2', '2.1.2.1') == -1

    version_compare('3.14.0.0', '3.14') == 0

    version_compare('5.15.20', '5.15.2') == 1

    :param ver1: First version string to compare.
    :param ver2: Second version string to compare.
    :returns: A positive integer if the first version is greater than the
              second version, a negative integer if the first version is
              less than the second version and 0 if they're equal.
    """
    parse_version: Callable[[str], List[int]] = lambda ver: \
        list(reversed(list(dropwhile(lambda x: x == 0,
            reversed(list(map(int, ver.split('.'))))
        ))))

    ver1_p: List[int] = parse_version(ver1)
    ver2_p: List[int] = parse_version(ver2)

    if ver1_p < ver2_p:
        return -1
    if ver1_p > ver2_p:
        return 1
    return 0


def check_string_base64(string: str) -> bool:
    """
    Checks if string is base64 encoded

    Examples:

    check_string_base64("aG9sYQo=") == True
    check_string_base64("hello") == False
    check_string_base64("aG9sYQo\=") == False

    :param string: String to review if it's base64 encoded
    :returns bool: True if string is base64 encoded. False otherwise
    """

    is_base64 = False

    try:
        # Important to use validate=True
        base64.b64decode(string.encode(), validate=True).decode("utf-8")
        is_base64 = True

    except Exception:
        is_base64 = False

    return is_base64


def build_dict_from_table(
    lines: Sequence[str],
    columns: List[str],
    sep: str = ' '
) -> Mapping[str, Mapping[str, str]]:
    """
    Builds a dictionary with a list of lines.

    Example:

    lines = (
        'DATAC1_CD_00_sea201507exdcl04   Yes     ONLINE',
        'DATAC1_CD_01_sea201507exdcl04   No      OFFLINE',
        'DATAC1_CD_02_sea201507exdcl04   Yes     SYNC'
    )
    colums = ('ASMDeactivationOutcome', 'ASMModeStatus')

    build_dict_from_table(lines, columns) = {
        'DATAC1_CD_00_sea201507exdcl04': {
            'ASMDeactivationOutcome': 'Yes',
            'ASMModeStatus': 'ONLINE'
        },
        'DATAC1_CD_01_sea201507exdcl04': {
            'ASMDeactivationOutcome': 'No',
            'ASMModeStatus': 'OFFLINE'
        },
        'DATAC1_CD_02_sea201507exdcl04': {
            'ASMDeactivationOutcome': 'Yes',
            'ASMModeStatus': 'SYNC'
        },
    }

    Note that the first column is not included because that will be the keys
    of the returned dictionary.
    For the same reason if one value from the first column is repeated in more
    than one row, the dictionary will contain only the entry of the last
    incidence in the sequence.

    :param lines: contents of the table.
    :param columns: names of the columns of the table except for the first one.
    :param sep: separator character.
    :returns: dictionary representation of the table.
    """
    result: Mapping[str, Mapping[str, str]] = {}
    num_cols: int = len(columns)
    for line in lines:
        key, *values = line.strip().split(sep)
        if len(values) != num_cols:
            raise ValueError(
                f'Row "{line}" has {len(values)} columns but {num_cols} were '
                'expected.'
            )

        result[key.strip()] = {
            col_name: value.strip()
            for col_name, value
            in zip(columns, values)
        }

    return result

def mGetFolderFreeSize(aFolder):
    """Get the free size for a local directory

    Args:
        aFolder (str): Path to a local directory

    Returns:
        str: Available free size of the given folder in KB. Returns None if Folder does not exist.
    """
    if not os.path.exists(aFolder):
        return None
    _av_size = None
    total, used, free = shutil.disk_usage(aFolder)
    # Available size in KBs
    _av_size = str(free//1024)
    return _av_size

def mGetModelNumber(aModel: str) -> int:
    """
    Helper function for mCompareModel.

    Removes leading and trailing characters then convert to int.
    """
    _list = [ _char for _char in aModel if _char.isdigit() is True]
    return int("".join(_list))

def mIsStrModel(aModel: str) -> bool:
    """
    Helper function for mCompareModel.

    If aModel complies with the expected format for a system model (X#) the
    function returns True, otherwise False.
    """
    _strModel = False
    try:
        mGetModelNumber(aModel)
        _strModel = True
    except:
        pass

    return _strModel

def mCompareModel(x: str, y: str) -> int:
    """
    This method uses the compare function standard of return -1, 0 & 1.

    x <  y = -1 = y >  x
    x == y =  0 = y == x
    x >  y =  1 = y <  x

    This method validates the arguments it recives and raises and exception
    if the values are not what is expected (X#).
    """
    if not mIsStrModel(x):
        raise ValueError("Argument x is not a valid model string")
    if not mIsStrModel(y):
        raise ValueError("Argument y is not a valid model string")

    _x = mGetModelNumber(x)
    _y = mGetModelNumber(y)

    if _x < _y:
        return -1
    elif _y < _x:
        return 1
    else:
        return 0

def read_json_into_string(aPath):
    json_path = aPath
    _data = None
    if os.path.exists(json_path):
        with open(json_path, "r") as file:
            _data = json.load(file)
    return _data

def read_file_into_string(aPath):
    file_path = aPath
    _data = None
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            _data = file.read()
    return _data

def exception_handler_decorator(func):
    def inner_function(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            etype, value, tb = sys.exc_info()
            if etype:
                str_exception  = traceback.format_tb(tb)
                str_currstack = traceback.format_stack()
                ebLogError(f'Exception class:{etype}, value: {value}')
                ebLogError(f'Exception :{str_exception}, Current stack: {str_currstack}')
            ebLogError(f"Traceback: {traceback.format_exc()}")
    return inner_function