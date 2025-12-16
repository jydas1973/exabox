#!/bin/python
#
# $Header: ecs/exacloud/exabox/managment/src/utils/CpsExaccError.py /main/4 2024/11/29 23:55:11 hgaldame Exp $
#
# CpsExaccError.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      CpsExaccError.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    11/08/24 - enh 37236624 - oci/exacc: remote manager endpoint
#                           for execute cps software oel 7 to oel 8 migration
#    hgaldame    05/16/24 - 36612813 - oci/exacc gen2 | cpssw fleet upgrade |
#                           enhance cps sw upgrade prechecks for run only on
#                           primary cps
#    hgaldame    05/03/24 - ercpssw
#    hgaldame    06/16/23 - 35509904 - oci/exacc: fix error codes on remote
#                           manager for match with ecra error catalog
#    hgaldame    09/30/22 - 34627398 - exacc:bb:22.3.1:cps-sw upgrade: provide
#                           proper error code for precheck failure instead of
#                           returning generic error
#    hgaldame    09/30/22 - Creation
#
from enum import Enum

# CONSTANTS OF ERROR CODE MESSAGE

NO_INFO_PROVIDED = "No information provided"

class CpsMessageRangeEnum(Enum):
    G_SUCCESS_PATCH_GENERIC = "0000"
    G_ERROR_RANGE_CPS_SW_UPGRADE = "0702"


class CpsGenericMesgEnum(Enum):
    GENERIC_UPGRADE_SUCCESS_EXIT_CODE = "0x00000000"

# This file has to be in sync whith $ADE_VIEW_ROOT/ecs/ecra/app/src/main/webapp/WEB-INF/ecra_error_catalog.json
class CpsCpsSwUpgradeErrorEnum(Enum):
    CPS_SW_UPGRADE_OPERATION_FAILED = "0x07020005"
    CPS_SW_UPGRADE_NO_ERROR_CODE = "0x07020006"
    CPS_SW_UPGRADE_NO_ECRA_TOKEN = "0x07020007"
    CPS_SW_UPGRADE_NO_INSTALL_DIR = "0x07020008"
    CHECK_CPS_CHECK_OPERATION_FAILED = "0x07020009"
    CURRENT_CPS_VERSION_MISMATCH = "0x0702000A"
    CPS_SANITY_SOFTWARE_SERVICES_FAIL = "0x0702000B"
    INSUFFICIENT_SPACE_ON_CPS_NODE = "0x0702000C"
    MISSING_IMAGE_MANAGER_ARTIFACT =  "0x0702000D"
    MISSING_CPSSW_ENTRY = "0x0702000E"
    CPS_SWITCHOVER_FAIL = "0x0702000F"
    CPS_CHECK_NON_PRIMARY_NODE = "0x07020010"
    # 0x07020011 0x07020012 already taken on ecra_error_catalog.json
    CPS_CHECK_SINGLE_CPS = "0x07020013"
    CPS_OELMIGR_OPERATION_FAILED = "0x07020014"
    CPS_OELMIGR_POST_SANITY_FAILED = "0x07020015"


# CATALOGUE OF MESSAGES

CPS_MESSAGE_BY_RANGE = {
    CpsMessageRangeEnum.G_SUCCESS_PATCH_GENERIC.value : "Operation executed successfully.",
    CpsMessageRangeEnum.G_ERROR_RANGE_CPS_SW_UPGRADE.value : "CPS SW Upgrade operation failed."
}

CPS_GENERIC_MESSAGE = {
    CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value : "no further action required.",
}

CPS_SW_UPGRADE_DETAIL = {
    CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_OPERATION_FAILED.value : "Check Remote manager logs on cps",
    CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_ERROR_CODE.value : "no error code reported, returning generic error.",
    CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_ECRA_TOKEN.value : "Invalid or not found ocpsSetup.json file on remote manager configuration.",
    CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_INSTALL_DIR.value : "Invalid or not found install directory on remote manager configuration.",
    CpsCpsSwUpgradeErrorEnum.CHECK_CPS_CHECK_OPERATION_FAILED.value :"Pre or post cps sw check operation failed.",
    CpsCpsSwUpgradeErrorEnum.CURRENT_CPS_VERSION_MISMATCH.value: "Current version of Cps deployer installed does not match with the payload",
    CpsCpsSwUpgradeErrorEnum.CPS_SANITY_SOFTWARE_SERVICES_FAIL.value: "Sanity of software services on cps host failed.",
    CpsCpsSwUpgradeErrorEnum.INSUFFICIENT_SPACE_ON_CPS_NODE.value: "Insufficient space on CPS launch node and unable to perform upgrade.",
    CpsCpsSwUpgradeErrorEnum.MISSING_IMAGE_MANAGER_ARTIFACT.value: "CPS deployer bits defined on image manager configuration not found in /u01/downloads area to perform upgrade.",
    CpsCpsSwUpgradeErrorEnum.MISSING_CPSSW_ENTRY.value: "cpssw entry not found on activeVersion.json on image manager configuration",
    CpsCpsSwUpgradeErrorEnum.CPS_SWITCHOVER_FAIL.value: "CPS switchover operation fail .",
    CpsCpsSwUpgradeErrorEnum.CPS_CHECK_NON_PRIMARY_NODE.value: "CPS SW/OS operation attempted on non-primary node. Verify WSS VCN health",
    CpsCpsSwUpgradeErrorEnum.CPS_CHECK_SINGLE_CPS.value: "CPS SW/OS operation attempted on single cps. Operation not supported",
    CpsCpsSwUpgradeErrorEnum.CPS_OELMIGR_OPERATION_FAILED.value: "CPS SW/OS migration operation fails. ",
    CpsCpsSwUpgradeErrorEnum.CPS_OELMIGR_POST_SANITY_FAILED.value: "CPS SW/OS migration sanity check fails. "

}


def mGetErrorMessageByRange(aCodeRange):
    """
    Get error Message by code error Message
    Args:
        aCodeRange(CpsMessageRangeEnum): Code error message. Default:  CpsMessageRangeEnum.G_ERROR_RANGE_CPS_SW_UPGRADE

    Returns:
       (str): Error Message
    """
    _default_message = CPS_MESSAGE_BY_RANGE.get(CpsMessageRangeEnum.G_ERROR_RANGE_CPS_SW_UPGRADE.value)
    return CPS_MESSAGE_BY_RANGE.get(aCodeRange, _default_message)

def mGetDetailCatalogueByRange(aCodeRange):
    """
    Get catalogue of details error by code error range
    Args:
        aCodeRange(CpsMessageRangeEnum): Code error message. Default:  CPS_SW_UPGRADE_DETAIL

    Returns:
        (dict) : Catalogue of details, each catalogue is defined in form "error_code" : "error message",
        e.g.
        {
        "0x07010000" : "Check Remote manager logs on cps"
        }

    """
    _catalogue_dict = {
        CpsMessageRangeEnum.G_SUCCESS_PATCH_GENERIC.value: CPS_GENERIC_MESSAGE,
        CpsMessageRangeEnum.G_ERROR_RANGE_CPS_SW_UPGRADE.value: CPS_SW_UPGRADE_DETAIL
    }
    return _catalogue_dict.get(aCodeRange, CPS_SW_UPGRADE_DETAIL)

def mCpsFormatBuildError(aErrorCode):
    """
    Creates and format an error message by Error Code
    Args:
        aErrorCode (str):  String of a Hexadecimal number. .e.g ( 0x07010000)
        Hexadecimal value has to be defined on any Enum defined on constants section.

    Returns:
        (dict):
            "error_code": String of a hexadecimal value for error code,
            "error_message": String with error message. Error message is defined by a error code range.
                             Error code range is defined by position 2 to 6 from error code,
                             eg. error code : 0x07010000, error range: 0701 , message =  CPS SW Upgrade operation failed.
                             default: No information provided"
            "error_detail" : String with detail of error message
                             default: No information provided"

    """
    _default_error_code = CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_ERROR_CODE.value
    default_message= mBuildDefaultFailureMessage()
    if aErrorCode is None or len(str(aErrorCode)) < 6:
        return default_message
    _error_range = str(aErrorCode[2:6])
    _error_message = mGetErrorMessageByRange(_error_range)
    _detail_catalogue = mGetDetailCatalogueByRange(_error_range)
    return mBuildMessage(aErrorCode, _error_message, _detail_catalogue.get(
        aErrorCode, CPS_SW_UPGRADE_DETAIL.get(_default_error_code)))

def mBuildMessage(aErrorCode, aMessage=None, aDetailMessage=None):
    """
    Wraps a error message into a dict a dict for error message

    Args:
        aErrorCode (str): String of a hexadecimal value for error code,
        aMessage (str): String with error message.
                        default: No information provided"
        aDetailMessage (str): String with detail of error message
                        default: No information provided"

    Returns:
        (dict):
            "error_code": String of a hexadecimal value for error code,
            "error_message": String with error message.
            "error_detail" : String with detail of error message
                             default: No information provided"
    """
    message_dict ={
        "error_code": aErrorCode,
        "error_message": aMessage or "No information provided",
        "error_detail" : aDetailMessage or "No information provided"
    }
    return message_dict

def mBuildDefaultSuccessMessage():
    """
    Build a default success message dict
    Returns:
        (dict):
        "error_code":  "0x00000000",
        "error_message": "Operation executed successfully.".
        "error_detail" : "no further action required."
    """
    return mBuildMessage(CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value,
                         CPS_MESSAGE_BY_RANGE.get(CpsMessageRangeEnum.G_SUCCESS_PATCH_GENERIC.value),
                         CPS_GENERIC_MESSAGE.get(CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value)
                         )

def mBuildDefaultFailureMessage():
    """
    Build a default failure message dict
    Returns:
        (dict):
        "error_code":  "0x07010000",
        "error_message": "CPS SW Upgrade operation failed.".
        "error_detail" : "no error code reported, returning generic error."
    """
    return mBuildMessage(CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_OPERATION_FAILED.value,
                         CPS_MESSAGE_BY_RANGE.get(CpsMessageRangeEnum.G_ERROR_RANGE_CPS_SW_UPGRADE.value),
                         CPS_SW_UPGRADE_DETAIL.get(CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_ERROR_CODE.value)
                         )

def mGetErrorByPrecheckAction(aArgument):
    """
    Get Error Code by cps sw check action
    Args:
        aArgument: list of arguments of execute cps sw check.
    Returns:
        (str): error code

    """
    _arg_list = aArgument.split() if aArgument else []
    _error_code = CpsCpsSwUpgradeErrorEnum.CHECK_CPS_CHECK_OPERATION_FAILED.value
    if _arg_list:
        if "checkcpsversion" in _arg_list:
            _error_code = CpsCpsSwUpgradeErrorEnum.CURRENT_CPS_VERSION_MISMATCH.value
        elif "checkfsavailable" in _arg_list:
            _error_code = CpsCpsSwUpgradeErrorEnum.INSUFFICIENT_SPACE_ON_CPS_NODE.value
        elif "checkcpsartifact" in _arg_list:
            _error_code = CpsCpsSwUpgradeErrorEnum.MISSING_IMAGE_MANAGER_ARTIFACT.value
    return _error_code


