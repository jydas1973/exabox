#
# $Header: ecs/exacloud/exabox/infrapatching/utils/utility.py /main/41 2025/10/22 08:33:53 sdevasek Exp $
#
# utility.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      utility.py - This module contains all the generic methods for each of the handlers.
#
#    DESCRIPTION
#      This module contains all the generic methods for each of the handlers.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jyotdas     02/06/26 - Enh - Allow LATEST targetVersion for DOM0
#                           exasplice patching
#    sdevasek    10/10/25 - ENH 38437135 - IMPLEMENT ADDITION OF SCRIPTNAME
#                           SCRIPTBUNLDENAME AND SCRIPTBUNDLEHASH ATTRIBUTES
#                           TO ECRA REGISTERED PLUGINS METADATA REGISTRATION
#    araghave    06/24/25 - Enhancement Request 38082882 - HANDLING EXACLOUD
#                           ELU CHANGES FOR DOM0 PATCHING
#       jyotdas  06/11/25 - Enh 37912226 - Identify proper targetversion for
#                           elu in exacs infrapatching
#       jyotdas  03/12/25 - Bug 37662723 - Dispatcher error is empty for single
#                           thread patch operation
#       araghave 03/04/25 - Bug 37417431 - EXACS | DOMU | UNWANTED SSH
#                           CONNECTION FROM 169.254.200.1 LOCKING OPC USER
#    antamil     01/31/25 - Enh 37300427 - Enable clusterless cell patching
#                           using management host
#       emekala  12/10/24 - ENH 37374442 - SUPPORT INFRA PATCH MOCK FWK TO
#                           ACCEPT MOCK RESPONSE IN JSON FORMAT VIA REST API
#    diguma      12/06/24 - bug 37365122 - EXACS:24.4.2.1:X11M: ROLLING DOM0
#                           PATCHING FAILS WITH SSH CONNECTIVITY CHECK FAILED
#                           DURING PATCHING EVEN THOUGH EXASSH TO DOMUS WORK
#       emekala  11/27/24 - ENH 37328901 - Add support to initialize infra
#                           patch mock setup when payload has mock request
#                           attribute
#    emekala     11/27/24 - ENH 37328901 - Add support to initialize infra
#                           patch mock setup when payload has mock request
#                           attribute
#                           patch mock setup when payload has mock request
#                           attribute
#    emekala     10/22/24 - ENH 36657637 - COMMANDS EXECUTED IN PRE AND POST
#                           CHECKS SHOULD HAVE TIMEOUT
#    diguma      10/08/24   bug 37130040 - EXACC:BB:EXASCALE:DOM0 PATCHING
#                           FAILS WITH ERROR "EXCEPTION IN RUNNING DOM0 PATCH
#                           TIME DATA '2024-10' DOES NOT MATCH FORMAT
#                           '%Y-%M-%DT%H:%M:%S'"
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    diguma      08/26/24 - bug 36975348: NEED A NEW INDICATOR OF GI STACK
#                           TO BE STARTED IN EXASCALE BASED CLUSTERS
#    diguma      08/21/24 - bug 36871736:REPLACE EXASPLICE WITH ELU(EXADATA
#                           LIVE UPDATE) FOR EXADATA 24.X
#    antamil     08/12/24 - Bug 36798372 - Change the owner of patchmgr files
#                           to opc when management host is used as launchnode
#    antamil     08/01/24 - Bug 36881089 - Configure passwordless ssh using
#                           ssh config file on management host
#    sdevasek    07/22/24 - ENH 36773605 - MAKE PDB_DEGRADED_STATES_MATRIX
#                           CONFIGURABLE INSTEAD OF HAVING AS CONSTANT
#    apotluri    06/21/24 - Enhancement Request 36750543 - PYTHON UPGRADE -
#                           INFRAPATCHING FILES SHOULD HAVE DYNAMICALLY SET
#                           PYTHON PATHS TO AVOID REGRESSIONS
#    araghave    06/17/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    antamil     05/31/24 - Bug 36659206 - Changes to report precheck failure
#                           message to CP
#    sdevasek    05/29/24 - ENH 36659116 - ECRA WR FOR DOMU OS PATCHING STATE
#                           IS NOT CHANGED FROM 202 TO 500 DUE TO ERROR_MESSAGE
#                           STRING OVERFLOW FOR TABLES ECS_REQUESTS_TABLE,
#                           ECS_EXA_APPLIED_PATCHES_TABLE
#    jyotdas     05/22/24 - Bug 36600281 - Patch directory not exist - error
#                           action fail_dontshow_page_oncall at exacloud but
#                           page_oncall at ECRA
#    araghave    03/20/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    emekala     02/14/24 - ENH 36261828 - ADD MOCK SUPPORT WITHIN
#                           INFRAPATCHING LAYER TO RUN INFRAPATCHING OPERATIONS
#                           IN MOCK MODE
#    diguma      01/29/24 - Bug 36237643: EXACS - INFRAPATCHING - ADD SUPPORT 
#                           TO UPGRADE DOMU KVM GUEST WITH ONLY U02 ENCRYPTED
#                           IN OL8
#    antamil     02/02/23 - 36109360 - Codes changes for Cps as launch node 
#    jyotdas     11/29/23 - 35955958 - Ecra status call in pending status
#    avimonda    07/20/23 - Bug 35443002 - Add DOMU_PATCH_BASE
#    jyotdas     06/13/23 - BUG 35488103 - Domu os patch fails with page_oncall
#                           error instead of fail_and_show for dispatcher
#                           errors
#    diguma      02/19/23 - Bug 35103409 - checking if FS is encrypted
#    diguma      12/01/22 - Enh 34840180 - addition of specific alerts for
#                           ExaCC
#    araghave    08/17/22 - Enh 34350140 - EXACLOUD CHANGES TO HANDLE
#                           EXACOMPUTE PRECHECK AND PATCHING OPERATIONS
#    jyotdas     04/04/22 - BUG 34010538 - Apply monthly patch on dom0 fails if
#                           reshape to zero cores is run in parallel
#    jyotdas     02/22/22 - Bug 33798374 - dispatcher error should display only
#                           patching messages for infrapatching operations
#    pkandhas    12/16/21 - Bug 33677531 - Get correct root dir name form 
#                           zip file
#    araghave    08/02/21 - Enh 33182904 - Move all configurable parameters
#                           from constants.py to Infrapatching.conf
#    nmallego    10/27/20 - Enh 31540038 - Change debug level
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import importlib
import datetime
import os
import sys
import zipfile
import json
import subprocess
import traceback
import re
import fcntl
from contextlib import contextmanager

try:
    from collections import OrderedDict
except ImportError:
    from collections.abc import OrderedDict

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.utils.constants import ANSI_ESCAPE, WAIT_LINES_ESCAPE, INFRA_PATCHING_HANDLERS, \
    TASK_HANDLER_MAP, TARGET_HANDLER_MAP, INFRA_PATCHING_KNOWN_ALERTS_EXACOMPUTE,                         \
    INFRA_PATCHING_KNOWN_ALERTS_EXACC, INFRA_PATCHING_KNOWN_ALERTS_EXACS, INFRA_PATCHING_CONF_FILE,       \
    EXACOMPUTE_PATCH_CONF_FILE, EXACS_SRV, EXACC_SRV, KEY_API, TASK_MOCK_HANDLER_MAP, TARGET_MOCK_HANDLER_MAP, \
    SHELL_CMD_TIMEOUT_EXIT_CODE, SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS, PATCH_CELL_CLUSTERLESS, PATCH_DOM0_CLUSTERLESS, \
    PATCH_DOM0
from exabox.log.LogMgr import ebLogInfo, ebLogDebug, ebLogWarn, ebLogError, ebLogTrace
from exabox.infrapatching.core.infrapatcherror import *
from exabox.ovm.cluencryption import getMountPointInfo

#Generic Functions taken out from clupatching.py and written separately
from exabox.ovm.clumisc import ebFortifyIssues

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

def mRegisterInfraPatchingHandlers(dictionary,handlerKeyList, handlerValue):

    if len(handlerKeyList) > 1:
        if handlerKeyList[0] not in dictionary.keys():
            dictionary[handlerKeyList[0]] = {}
        mRegisterInfraPatchingHandlers(dictionary[handlerKeyList[0]], handlerKeyList[1:], handlerValue)
    else:
        dictionary[handlerKeyList[0]] = handlerValue

def mGetInfraPatchingHandler(dictionary,handlerKey):

    _infra_patching_handler = None
    for k, v in dictionary.items():
        if k == handlerKey:
            _infra_patching_handler = v
            return _infra_patching_handler
    return _infra_patching_handler

def mSetFromEnv(default, aEnvVariable=None, aErrorOn=None, aMustConvertTo=None):
    """
       Returns default (str) unless aEnvVariable (str) is provided and an environment variable with the same name exists.
       aErrorOn is an optional list of strings that can be checked to make sure the value does not equal.
       aMustConvertTo is an optional type (str, int, float) that can check to make sure the value
       (which is, and will be returned as string) can safely convert to
     """

    if aEnvVariable and aEnvVariable in os.environ:
        value = os.environ[aEnvVariable]
    else:
        # Just return default, no point in testing error conditions on it.
        return default

    if aErrorOn:
        if any(value == error_value for error_value in aErrorOn):
            err_msg = (
                f"constant taken from environment variable {aEnvVariable} should not be any of [{','.join(aErrorOn)}] but we got {value}")
            raise Exception(err_msg)

    if aMustConvertTo:
            try:
                if aMustConvertTo == int:
                    int(value)
                elif aMustConvertTo == float:
                    float(value)
                # It should always be convertable to string (env variables are all strings), but, just to be safe
                elif aMustConvertTo == str:
                    str(value)
            except ValueError as e:
                ebLogError(str(e))
                err_msg = (
                    f"constant taken from environment variable {aEnvVariable} should be convertable to type [{aMustConvertTo}], we got {value}")
                raise Exception(err_msg)

    return value

def mTruncateErrorMessageDescription(aActualErrorMsg, aSuffixStr="...", aTruncateLength=ERROR_MSG_TRUNCATE_LENGTH):
    """
    :param aActualErrorMsg: Actual error_description string
    :param aSuffixStr: Suffix string need to be added at the end of the string message after truncation
    :param aTruncateLength: Maximum length of the string after truncation including suffix length.
    :return: Truncated string

    Note: Caller should ensure that the aActualErrorMsg string length is greater than aTruncateLength before calling
    this method
    """
    _suffix_length = len(aSuffixStr)
    ebLogInfo(f"error_detail string before truncating is {aActualErrorMsg}")
    _truncated_error_msg = aActualErrorMsg[:aTruncateLength - _suffix_length]
    return _truncated_error_msg + aSuffixStr

def mFormatOut(_o):
    # Example: output was represented as [u'23434\n'], need just the number stuff
    _o = _o.readlines()
    out = str("".join(_o))
    return out

def mGetFirstDirInZip(aZipFile):

    _fortify_obj = ebFortifyIssues()
    if _fortify_obj.mPathManipulationError(aZipFile):
        raise Exception(f"mGetFirstDirInZip: The vulnerable word or character found in file path: {aZipFile}.")

    _zip_file = zipfile.ZipFile(aZipFile, "r")
    for filename in _zip_file.namelist():
        if filename.endswith('/'):
            return str(filename.split('/')[0]) + '/'


def mReadCallback(aData):
    # Escapes special characters to return a well formed output
    _data = ANSI_ESCAPE.sub('', aData.decode('utf-8'))
    _data = WAIT_LINES_ESCAPE.sub('', _data)
    for _line in _data.split('\n'):
        if _line.strip() == '':
            continue
        ebLogInfo(_line, aNoNL=True)


def mErrorCallback(aData):
    # Escapes escape special characters to return a well formed output
    _data = ANSI_ESCAPE.sub('', aData.decode('utf-8'))
    _data = WAIT_LINES_ESCAPE.sub('', _data)
    for _line in _data.split('\n'):
        if _line.strip() == '':
            continue
        ebLogError(_line, aNoNL=True)


def mReadPatcherInfo(aCnsPatcherFile):
    # This would read and return launch node and it's log directory
    try:
        _launch_node = None
        _patchmgr_log_dir = None

        _fortify_obj = ebFortifyIssues()
        if _fortify_obj.mPathManipulationError(aCnsPatcherFile):
            raise Exception(
                f"mReadPatcherInfo: The vulnerable word or character found in file path: {aCnsPatcherFile}.")

        if os.path.isfile (aCnsPatcherFile):
            with open(aCnsPatcherFile, "r") as _f_cur_launch_node:
                _launch_node, _patchmgr_log_dir = \
                _f_cur_launch_node.read().split(':')
    except Exception as e:
        ebLogInfo(f'Failed to read patcher file {aCnsPatcherFile}: {str(e)}')
    return _launch_node, _patchmgr_log_dir

def mManageRPMs(aRPMList, aNode=None, aNodeConnection=None,
                 aAction='install'):
    """
    Function to add or remove a set of RPMs.

    Currently used to remove the krb5-workstation.
    It is installated by ExaCloud for the BDCS and stuff.
    It  hinders the patching. So the idea is to remove it before the
    patching and install it again after patching.

    TODO:  to be removed once we have the
    functionality that allows one to extend patching by means
    of pre and post clustom scripts execution per each patch
    action for these type of tweaks.
    """

    _ret = True
    _cmd_template = ""
    _node = None

    if aAction in 'install':
        _cmd_template = "rpm -Uvh %s;"

    if aAction in 'remove':
        _cmd_template = "rpm -ev %s;"

    if not aNodeConnection:
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode)
    else:
        _node = aNodeConnection

    for rpm in aRPMList:
        _cmd = _cmd_template % rpm
        _in, _out, _err = _node.mExecuteCmd(_cmd)
        _output = _out.readlines()
        if _output:
            ebLogInfo("\n".join(_output))
        else:
            _errors = _err.readlines()
            ebLogTrace("\n".join(_errors))
            _ret = False

    if not aNodeConnection:
        _node.mDisconnect()

    return _ret

def isMockModeEnabled(*initial_data):
    _mock_mode = False
    _mock_config_json_from_payload = {}
    _coptions = get_gcontext().mGetConfigOptions()
    if 'mock_mode_patch' in _coptions:
        if str(_coptions['mock_mode_patch']).upper() == 'TRUE':
            _mock_mode = True
    # Check the patch payload as well as there is a way to enable mock mode via patch payload with mock action
    # to run infra patching in mock.
    for _dictionary in initial_data:
        if "AdditionalOptions" in _dictionary:
            _additional_options = _dictionary["AdditionalOptions"]
            if _additional_options and ("mockMode" in _additional_options[0] or "MockMode" in _additional_options[0]):
                _mock_mode = True
                _mock_config_json_from_payload = _additional_options[0]["mockMode"] if "mockMode" in _additional_options[0] else _additional_options[0]["MockMode"]
                break
    return _mock_mode, _mock_config_json_from_payload 

def getTaskHandlerInstance(aTaskType , aDictionary = None):
    _handler_name = None
    _handler_instance = None
    _handler_class = None
    _mock_mode, _ = isMockModeEnabled(aDictionary)
    if _mock_mode:
        _handler_name = TASK_MOCK_HANDLER_MAP[aTaskType]
    else:
        _handler_name = TASK_HANDLER_MAP[aTaskType]
    if _handler_name:
        _module_name, _class_name = _handler_name.rsplit(".", 1)
        try:
            _handler_class = getattr(importlib.import_module(_module_name), _class_name)
        except ImportError:
            ebLogError("Module does not exist")
    _handler_instance = _handler_class(aDictionary)
    if _handler_instance:
        return _handler_instance
    else:
        return None

def getTargetHandlerInstance(aTargetType, aDictionary = None):
    _handler_name = None
    _handler_instance = None
    _handler_class = None
    _mock_mode, _ = isMockModeEnabled(aDictionary)
    if _mock_mode:
        _handler_name = TARGET_MOCK_HANDLER_MAP[aTargetType]
    else:
        _handler_name = TARGET_HANDLER_MAP[aTargetType]
    if aDictionary and "AdditionalOptions" in aDictionary:
        _additional_options = aDictionary["AdditionalOptions"]
        if ("ClusterLess" in _additional_options[0] and _additional_options[0]["ClusterLess"].upper() == "YES"):
            if aTargetType == PATCH_CELL:
                _handler_type = PATCH_CELL_CLUSTERLESS
            if aTargetType == PATCH_DOM0:
                _handler_type = PATCH_DOM0_CLUSTERLESS
            _handler_name = TARGET_HANDLER_MAP[_handler_type]
    if _handler_name:
        _module_name, _class_name = _handler_name.rsplit(".", 1)
        try:
            _handler_class = getattr(importlib.import_module(_module_name), _class_name)
        except ImportError:
            ebLogError("Module does not exist")
    _handler_instance = _handler_class(aDictionary)
    if _handler_instance:
        return _handler_instance
    else:
        return None

def mGetInfraPatchingKnownAlert(aKey, aSrvType):
    _dict_infrapatching_config = None
    _return_list = None
    _infa_paching_config_file = f"{get_gcontext().mGetBasePath()}/exabox/infrapatching/config/{INFRA_PATCHING_CONF_FILE}"
    if aSrvType == EXACC_SRV:
        _key = INFRA_PATCHING_KNOWN_ALERTS_EXACC
    elif aSrvType == EXACS_SRV:
        _key = INFRA_PATCHING_KNOWN_ALERTS_EXACS
    else:
        _key = INFRA_PATCHING_KNOWN_ALERTS_EXACOMPUTE

    with open(_infa_paching_config_file) as fd:
        _dict_infrapatching_config = json.load(fd, object_pairs_hook=OrderedDict)
    # Validate if infra known alerts are in infrapatching.conf
    if _dict_infrapatching_config:
        if (_key in list(_dict_infrapatching_config.keys()) and
           aKey in list(_dict_infrapatching_config[_key].keys())):
            _return_list = list(_dict_infrapatching_config[_key][aKey])
        else:
            ebLogError(f"{_key}/{aKey} is not present in config file {_infa_paching_config_file}")
    else:
        ebLogError(f"{_infa_paching_config_file} file is not present or empty")
    ebLogInfo(f"Infra known alerts {aKey}: {_return_list}")
    return _return_list

def mGetLaunchNodeConfig(aLaunchNodeType, aOption):
    """
    This function will parse the launchnode config json from 
    infrapatching.config file
    """
    _dict_infrapatching_config = None
    _infa_patching_config_file = None
    _option_value = None
    _infa_patching_config_file = f"{get_gcontext().mGetBasePath()}/exabox/infrapatching/config/{INFRA_PATCHING_CONF_FILE}"
    with open(_infa_patching_config_file) as fd:
        _dict_infrapatching_config = json.load(fd, object_pairs_hook=OrderedDict)
    # Validate if infra known alerts are in infrapatching.conf
    if _dict_infrapatching_config and "launch_node_config" in list(_dict_infrapatching_config.keys()):
        _launch_node_config = _dict_infrapatching_config["launch_node_config"]
        if aLaunchNodeType in _launch_node_config.keys():
            _type_config = _launch_node_config[aLaunchNodeType]
            if aOption in _type_config.keys():
                _option_value = _type_config[aOption] 
    return _option_value
    


def mGetPdbDegradedStatesMatrix():
    """
    This method reads the PDB degradation state matrix from infrapatching.cong file and return this matrix as output
    """
    _dict_infrapatching_config = None
    _return_list = []
    _infa_paching_config_file = f"{get_gcontext().mGetBasePath()}/exabox/infrapatching/config/{INFRA_PATCHING_CONF_FILE}"

    with open(_infa_paching_config_file) as fd:
        _dict_infrapatching_config = json.load(fd, object_pairs_hook=OrderedDict)
    # Validate if infra known alerts are in infrapatching.conf
    if _dict_infrapatching_config and  PDB_DEGRADED_STATES_MATRIX_KEY in _dict_infrapatching_config:
        _return_list = _dict_infrapatching_config[PDB_DEGRADED_STATES_MATRIX_KEY]

        # Remove the first row value as it represents header values
        if _return_list and _return_list[0] == ["pre_patch_openmode", "pre_patch_restricted", "post_patch_openmode",
                                                "post_patch_restricted", "is_pdb_in_degraded"]:
            _return_list = _return_list[1:]     

    else:
        ebLogError(f"Key {PDB_DEGRADED_STATES_MATRIX_KEY} is not present in infrapatching.conf file ")

    return _return_list

def mGetInfraPatchingConfigParam(aKey):
    """
     This method fetches all the configurable parameters
     from the infrapatching/config/infrapatching.conf file
     and returns to the caller.

     Returns :
       Relevant values if present.
       None if empty.
    """

    _infrapatching_config_params = None
    _ret = None
    _infa_paching_config_file = f"{get_gcontext().mGetBasePath()}/exabox/infrapatching/config/{INFRA_PATCHING_CONF_FILE}"
    with open(_infa_paching_config_file) as fd:
        _infrapatching_config_params = json.load(fd, object_pairs_hook=OrderedDict)

    # Fetch required values from infrapatching.conf
    if _infrapatching_config_params[aKey]:
        _ret = _infrapatching_config_params[aKey]
    else:
        ebLogError(f"Configurable parameter : {aKey} not found or is invalid in {_infa_paching_config_file} file.")
	
    return _ret

def mGetExacomputePatchConfigParam(aKey):
    """
     This method fetches all the configurable parameters
     from the infrapatching/config/exacomputepatch.conf file
     and returns to the caller.

     Returns :
       Relevant values if present.
       None if empty.
    """

    _exacompute_config_params = None
    _ret = None
    _exacompute_paching_config_file = f"{get_gcontext().mGetBasePath()}/exabox/infrapatching/config/{EXACOMPUTE_PATCH_CONF_FILE}"
    with open(_exacompute_paching_config_file) as fd:
        _exacompute_config_params = json.load(fd, object_pairs_hook=OrderedDict)

    # Fetch required values from infrapatching.conf
    if _exacompute_config_params[aKey]:
        _ret = _exacompute_config_params[aKey]
    else:
        ebLogError(
            f"Configurable parameter : {aKey} not found or is invalid in {_exacompute_paching_config_file} file.")

    return _ret

def mFilterRequestsForThisRack(aDB, aRackName, aStatus, aCmd=None, aRowsLimit=None):
    """
         This method fetches any operations for a rack from requests table
         based on status (like 'Pending','Done') and operation type
         (like cluctrl.patch, cluctrl.vm_cmd etc)

         Returns :
           The entire request to the caller
           None if empty.
    """
    if not aRackName:
        return None
    if not aStatus:
        return None
    if not aDB:
        return None

    if aCmd:
        _filter = {"status": aStatus, "clustername": aRackName, "cmdtype":aCmd}
    else:
        _filter = {"status": aStatus, "clustername": aRackName}

    ebLogInfo(f"Final _filer for DB Requests: {str(_filter)}")

    if aRowsLimit:
        _requests = aDB.mFilterRequests(_filter, aLimit=aRowsLimit)
    else:
        _requests = aDB.mFilterRequests(_filter)

    return _requests

def mPopulateDispatcherErrorForInfraPatch(aCmdType,aMaterReqUUID,aErrorCode,aErrorMsg,aRequestDataJson=None):
    """
     This method populates dispatcher error for infrapatching only.
     Log output will be in exacloud/log/workers folder (e.g vi agent_2980_140676295862080.log)
     Returns :
       Relevant _json_patch_report if present.
       None if empty.

     aRequestDataJson Format:
    {
	"data": {
		"httpRequestId": "c9641403-b095-46fa-b5c3-7f698880f289",
		"recipients": [{
			"channelType": "topics"
		}],
		"notificationType": {
			"componentId": "Patch_Exadata_Infra_SM",
			"id": "Patch_Exadata_Infra_SMnotification_v1"
		},
		"service": "EXADATA Patch",
		"component": "Patch Exadata Infrastructure",
		"subject": "Patch Exadata Infrastructure Service Update",
		"event_post_time": "2023-06-13:12.37.31 ",
		"log_dir": "log/patch/0fb35836-09e7-11ee-a051-02001710e25b",
		"cluster_name": "slcs27",
		"exadata_rack": "slcs27",
		"target_type": ["dom0"],
		"operation_type": "patch_prereq_check",
		"operation_style": "auto",
		"target_version": "22.1.8.0.0.230211",
		"topic": "",
		"error_code": "0x03010006",
		"error_message": "Master patch request exception detected",
		"error_detail": "mStartPatchRequestExecution error: mCheckIBFabricEntry: No input value specified.",
		"master_request_uuid": "0fb35836-09e7-11ee-a051-02001710e25b"
	}
}
    """
    _json_patch_report = None
    if aCmdType is None:
        return _json_patch_report
    else:
        ebLogInfo(f"Command type to populate dispatcher error for infra patching  is :  {aCmdType}.")
        try:
            if mCheckInfraPatchConfigOptionExists('patching_commands', aCmdType):
                _operation_type = None
                _target_type = None
                _operation_style = None
                _target_version = None
                _data_json = None
                _error_action = None
                if aRequestDataJson:
                    _data_json_obj = json.loads(aRequestDataJson)
                    for key, value in _data_json_obj.items():
                        _data_json = value
                    if _data_json and 'operation_type' in _data_json.keys():
                        _operation_type = _data_json['operation_type']
                    if _data_json and 'target_type' in _data_json.keys():
                        _target_type = _data_json['target_type']
                    if _data_json and 'operation_style' in _data_json.keys():
                        _operation_style = _data_json['operation_style']
                    if _data_json and 'target_version' in _data_json.keys():
                        _target_version = _data_json['target_version']
                    if _data_json and 'error_action' in _data_json.keys():
                        _error_action = _data_json['error_action']
                _json_patch_report = {}
                _data = {}
                _data['service'] = "EXADATA Patch"
                _data['component'] = "Patch Exadata Infrastructure"
                _data['subject'] = "Patch Exadata Infrastructure Service Update"
                _json_patch_report["data"] = _data
                _json_patch_report["data"]["master_request_uuid"] = aMaterReqUUID
                # Populate Dispatcher Error code and Error Message
                _json_patch_report["data"]["error_code"] = aErrorCode
                _json_patch_report["data"]["error_message"] = aErrorMsg
                _json_patch_report["data"]["error_detail"] = aErrorMsg
                if _operation_type:
                    _json_patch_report["data"]["operation_type"] = _operation_type
                if _target_version:
                    _json_patch_report["data"]["to_version"] = _target_version
                if _target_type:
                     _json_patch_report["data"]["target_type"] = _target_type
                if _error_action:
                    _json_patch_report["data"]["error_action"] = _error_action
                ebLogInfo(f"json_patch_report :  {_json_patch_report}.")
        except:
            if aRequestDataJson:
                ebLogError(
                    f"Infrapatching dispatcher error cannot be populated since aRequestDataJson {aRequestDataJson} is not a valid json")
            else:
                ebLogError("Infrapatching dispatcher error cannot be populated since aRequestDataJson is Empty")

    return _json_patch_report

# Python Program to Convert seconds
# into hours, minutes and seconds

def convertSeconds(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%d:%02d:%02d" % (hour, minutes, seconds)

PATCH_BASE = mSetFromEnv(default="/EXAVMIMAGES/", aEnvVariable="EXACLOUD_PATCH_PAYLOAD_BASE",
                         aErrorOn=["/tmp", "/tmp/"])

EXACLOUD_DO_DOM0_ROLLBACK_EVEN_IF_DOMU_MODIFIED_POST_PATCH = mSetFromEnv(default="",
                                                                         aEnvVariable="EXACLOUD_DO_DOM0_ROLLBACK_EVEN_IF_DOMU_MODIFIED_POST_PATCH")

DOMU_PATCH_BASE = mSetFromEnv(default="/u02/", aEnvVariable="EXACLOUD_PATCH_PAYLOAD_BASE",
                              aErrorOn=["/tmp", "/tmp/"])

def mIsFSEncryptedList(aNodeList, aHandler):
    """
     This method checks if one of the nodes on the list
     has the file system encrypted

     return True if one of the nodes has FS encryption
     return False if none of the nodes on the list has FS encryption
    """
    _encrypted = False

    _node = exaBoxNode(get_gcontext())
    for _node_name in aNodeList:
        _node.mConnect(aHost=_node_name)
        _encrypted = mIsFSEncryptedNode(_node, _node_name, aHandler)
        if _node.mIsConnected():
            _node.mDisconnect()
        if _encrypted:
            break
    return _encrypted

def mIsFSEncryptedNode(aNode, aNodeName, aHandler):
    """
     This method checks if the node has file system encrypted

     return True if the nodes has FS encryption
     return False if the node does not have FS encryption
    """
    # Get info about aMountPoint
    _mount_info = getMountPointInfo(aNode, "/u02")

    # Check Filesystem on aMountPoint is indeed encrypted
    if _mount_info.is_luks:
        ebLogInfo("File system /u02 is encrypted")
        # check if keyapi script exists
        _cmd = f'/usr/bin/ls {KEY_API}'
        aNode.mExecuteCmd(_cmd)
        _exit_check = int(aNode.mGetCmdExitStatus())
        if _exit_check != 0:
            _suggestion_msg = f"Unable to access encryption key api script on {aNodeName} - {KEY_API} "
            aHandler.mAddError(aNodeName, DOMU_ENCRYPT_KEY_API_FAILED, _suggestion_msg)
            raise Exception(_suggestion_msg)
        return True
    return False

def isInfrapatchErrorCode(aErrCode):
    # Sample return code for infrapatching is 0x03010004 (length is 10)
    if isinstance(aErrCode, str) and aErrCode.startswith("0x03") and len(aErrCode) == 10:
        return True
    else:
        return False


'''
This function executes commands using python popen subprocess on the local node
and it returns exit status and command output

Example 1:

    If we have to run the command "df -mP /tmp| tail -n1| awk '{print $(NF - 2); }'" on
    localhost it can be achieved by the following code

    _cmd_list = []
    _cmd_list.append(["df", "-mP", "/tmp"])             
    _cmd_list.append(["tail", "-n1"])   
    _cmd_list.append(["awk", '{print $(NF - 2); }'])  
    _ret, _output  = runInfraPatchCommandsLocally(_cmd_list)


Example 2:
    If we have to run the command "cat file" one localhost 
    it can be achieved by the following code

    _cmd_list = []
    _cmd_list.append(['cat', file])
    _ret, _output  = runInfraPatchCommandsLocally(_cmd_list)

'''
def runInfraPatchCommandsLocally(commands):
    _out = None
    _err = None
    _cmd_exec_prev = None
    _cmd_exec_first = None
    _current_command = None
    _rc = None
    try:
        for i in range(len(commands)):
            _current_command = commands[i]
            ebLogTrace(f"Executing command {_current_command}")
            # When are executing the first command there is no input to it
            if i == 0:
                _cmd_exec_first = subprocess.Popen(commands[i], stdout=subprocess.PIPE)
            else:
                _cmd_exec_first = subprocess.Popen(commands[i], stdin=_cmd_exec_prev.stdout, stdout=subprocess.PIPE)
            _cmd_exec_prev = _cmd_exec_first
        if _cmd_exec_prev:
            _out, _err = _cmd_exec_prev.communicate()
            if _err:
                ebLogTrace(f"err= {str(_err.decode('UTF-8').strip())}")
            if _out:
                ebLogTrace(f"out= {str(_out.decode('UTF-8').strip())}")
            _rc = _cmd_exec_prev.returncode
            if _rc != 0:
                ebLogTrace(f"Error in  Running Infrapatch Command {_current_command} Locally")
    except Exception as e:
            ebLogError(f"Exception while Running Infrapatch Command {_current_command} locally. Exception is {str(e)}")
            ebLogError(traceback.format_exc())
    finally:
        if _out:
            return _cmd_exec_prev.returncode, _out.decode("UTF-8").strip()
        else:
            return _rc, None


def mCheckFileExists(file, isCpsLaunchNode=False, _node=None):
    _cmd_list = []
    _file_exists = False
    if isCpsLaunchNode:
        _file_exists = os.path.exists(file)
    else:
        _file_exists = _node.mFileExists(file)
    return _file_exists

def mGetScriptOrder(aPluginsMetadata):
    _script_order = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "ScriptOrder" in _plugin_metadata_attributes:
            _script_order = aPluginsMetadata["ScriptOrder"]
            break
    return _script_order

def mGetScriptAlias(aPluginsMetadata):
    _script_alias = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "ScriptAlias" in _plugin_metadata_attributes:
            _script_alias = aPluginsMetadata["ScriptAlias"]
            break
    return _script_alias

def mGetChangeRequestId(aPluginsMetadata):
    _change_request_id = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "ChangeRequestId" in _plugin_metadata_attributes:
            _change_request_id = aPluginsMetadata["ChangeRequestId"]
            break
    return _change_request_id

def mGetDescription(aPluginsMetadata):
    _description = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "Description" in _plugin_metadata_attributes:
            _description = aPluginsMetadata["Description"]
            break
    return _description

def mGetPluginTargetV2(aPluginsMetadata):
    _plugin_target = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "PluginTarget" in _plugin_metadata_attributes:
            _plugin_target = aPluginsMetadata["PluginTarget"]
            break
    return _plugin_target

def mGetIsEnabled(aPluginsMetadata):
    _is_enabled = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "IsEnabled" in _plugin_metadata_attributes:
            _is_enabled = aPluginsMetadata["IsEnabled"]
            if _is_enabled and _is_enabled.lower() == "yes":
                return True
            else:
                return False

def mGetPluginType(aPluginsMetadata):
    _plugin_type = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "PluginType" in _plugin_metadata_attributes:
            _plugin_type = aPluginsMetadata["PluginType"]
            break
    return _plugin_type

def mGetPhase(aPluginsMetadata):
    _phase = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "Phase" in _plugin_metadata_attributes:
            _phase = aPluginsMetadata["Phase"]
            break
    return _phase

def mGetRebootNode(aPluginsMetadata):
    _reboot_node = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "RebootNode" in _plugin_metadata_attributes:
            _reboot_node_temp = aPluginsMetadata["RebootNode"]
            if _reboot_node_temp and _reboot_node_temp.lower() == "yes":
                _reboot_node = True
            else:
                _reboot_node = False
    return _reboot_node

def mGetFailonError(aPluginsMetadata):
    _fail_onerror = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "FailOnError" in _plugin_metadata_attributes:
            _fail_onerror_temp = aPluginsMetadata["FailOnError"]
            if _fail_onerror_temp and _fail_onerror_temp.lower() == "yes":
                _fail_onerror = True
            else:
                _fail_onerror = False
    return _fail_onerror

def mGetScriptBundleName(aPluginsMetadata):
    _script_bundle_name = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "ScriptAlias" in _plugin_metadata_attributes:
            _script_bundle_name = f'{aPluginsMetadata["ScriptAlias"]}.tar.gz'
            break
    return _script_bundle_name

def mGetScriptName(aPluginsMetadata):
    _script_name = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "ScriptName" in _plugin_metadata_attributes:
            _script_name = aPluginsMetadata["ScriptName"]
            break
    return _script_name

def mGetScriptBundleHash(aPluginsMetadata):
    _script_bundle_hash = None
    for _plugin_metadata_attributes in aPluginsMetadata.keys():
        if "ScriptBundleHash" in _plugin_metadata_attributes:
            _script_bundle_hash = aPluginsMetadata["ScriptBundleHash"]
            break
    return _script_bundle_hash

def checkPluginEnabledFromInfraPatchMetadata(aPluginMetadata):
    _exacloud_plugin_enabled, _dbnu_plugin_enabled = False, False
    try:
        for _plugins_list in aPluginMetadata:
            for _plugin_script_attribute_dict in _plugins_list.keys():
                if "PluginType" in _plugin_script_attribute_dict:

                    _plugin_type = _plugins_list["PluginType"]
                    '''
                     If atleast one occurance of exacloud plugin type is
                     found in the metadata, exacloud plugin is enabled.
                    '''
                    if str(_plugin_type).lower() == "exacloud":
                        _exacloud_plugin_enabled = True

                    if str(_plugin_type).lower() == "dbnu":
                        _dbnu_plugin_enabled = True
    except Exception as e:
        ebLogWarn(f'Unable to process plugin based ecra metadata. Error : {str(e)}')
    finally:
        return _exacloud_plugin_enabled, _dbnu_plugin_enabled

@contextmanager
def flocked(fd):
    """ Locks FD before entering the context, always releasing the lock. """
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)


def mChangeOwnerofDir(aNode, aPath, aUserName, aGroupName):
    _node = None
    try:
        _node = exaBoxNode(get_gcontext())
        _node.mSetUser(aUserName)
        _max_number_of_ssh_retries = mGetInfraPatchingConfigParam('max_number_of_ssh_retries')
        _node.mSetMaxRetries(int(_max_number_of_ssh_retries))
        _node.mConnect(aHost=aNode)
        _node.mExecuteCmdLog("chown -R %s:%s %s" %(aUserName, aGroupName, aPath))
        _exit_code = _node.mGetCmdExitStatus()
        if _exit_code != 0:
            ebLogError(f"Failed to change the owner of {aPath} to opc")
    finally:
        if _node.mIsConnected():
            _node.mDisconnect()

# check if the version is 2[4-9].*
def mIsExaVer24OrHigher(aVersion):
    _regex = r'^2[4-9]\.'
    if re.search(_regex, aVersion):
        return True
    return False

# it converts a string time: 2024-08-07T20:50:46-07:00 to date datatype (timezone 
# had to be removed. It seems that python does not handle well. Since cells should 
# all be synced, comparisons should be consistent
def mConvertTimeEscli(aTime):
    _format = "%Y-%m-%dT%H:%M:%S"
    if not aTime:
        return None

    # format is "%Y-%m-%dT%H:%M:%S", so locate the first ":" and then the second ":"
    _ind1 = aTime.index(':')
    _ind2 = aTime.index(':', (_ind1+1))
    _time = aTime[0:_ind2+3]
    return (datetime.datetime.strptime(_time, _format))


def mValidateTime(aTime1, aTime2):
    _format = "%Y-%m-%dT%H:%M:%S"
    try:
        mConvertTimeEscli(aTime1)
        return (aTime1)
    except Exception as e:
        try:
            ebLogInfo(f"First date passed is invalid {aTime1}, checking second one {aTime2}")
            # try second date
            mConvertTimeEscli(aTime2)
            return (aTime2)
        except Exception as e:
            ebLogInfo(f"Second date is invalid {aTime2}, returning current date")
            _now = datetime.datetime.now()
            _cur_date_format = _now.strftime(_format)
            # pass current date if nothing works
            return _cur_date_format


def mCheckAndFailOnCmdTimeout(aCmd, aNode, aHandler, aTimeOutInSecs=None, aErrorCode=None):
    """
    Common method to check and fail with sepcific error msg if the cmd exit code is due to timeout.
    Call this api immediately after Exacloud mExecute* api invocations that sends aTimeout as an agrument
    and processes the o/p returned by the cmd.
    
    Method arguments:
      aCmd           - Cmd that is executed via mExecute* api
      aNode          - Node obj instance. This is the node where mExecute* api executed
      aHandler       - Handler object instance. This is to get the infra patch task for which mExecute* api executed
                       and for adding the error into mAddError
      aTimeOutInSecs - Custom timeout value used for specific cmd executions
      aErrorCode     - Different error code other than the default cmd timeout error code to be used in the error msg      
    """
    if aNode and int(aNode.mGetCmdExitStatus()) == SHELL_CMD_TIMEOUT_EXIT_CODE:
        if aTimeOutInSecs is None:
            aTimeOutInSecs = SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS
        if aErrorCode is None:
            aErrorCode = SHELL_CMD_EXECUTION_TIMEOUT_ERROR
        _task = aHandler.mGetTask()
        _hostName = aNode.mGetHostname()
        if aNode.mIsConnected():
            aNode.mDisconnect()
        _msg = f"Command: {aCmd} taking more than the expected time: {aTimeOutInSecs} secs to complete on node: {_hostName}. Infra patch operation: {_task} marked as failed for further analysis!"
        aHandler.mAddError(aErrorCode, _msg)
        raise Exception(_msg)

def mGetSshTimeout():
    _value = 0
    _timeout = mGetInfraPatchingConfigParam('ssh_timeout_in_seconds')
    try:
        _value = int(_timeout)
    except Exception as e:
        ebLogInfo("Invalid value for ssh timeout")
        _value = 50

    if _value > 0 and _value < 120:
        return _value
    else:
        return 50

def mCheckInfraPatchConfigOptionExists(option: str, suboption: str) -> bool:
    """
    Checks if a given suboption exists within the specified option in a JSON object.
    :param option: The key to look for (e.g., 'patching_commands') in Dictionary containing the JSON data
    :param suboption: The value to check for in the list associated with the option
    :return: True if suboption exists within option, False otherwise
    """
    _infa_patching_config_file = f"{get_gcontext().mGetBasePath()}/exabox/infrapatching/config/{INFRA_PATCHING_CONF_FILE}"
    try:
        with open(_infa_patching_config_file) as fd:
            _infrapatching_config_params = json.load(fd)
            return suboption in _infrapatching_config_params.get(option, [])
    except KeyError as k:
        ebLogInfo(f"Key {option} not found in infrapatching.conf json")
        return False
    except Exception as e:
        ebLogInfo('Exception for fetching subcommands within patching commands %s ' % str(e))
        return False

    return False

def mCheckDispatcherErrorCode(json_string: str, error_code: str) -> bool:
    """
    Checks if the given error_code exists in the JSON string.
    :param json_string: JSON data as a string from mysql requests table data column
    :param error_code: Error code to check
    :return: True if error_code exists, else False
    """
    try:
        if json_string:
            ebLogInfo(f"json data to check dispatcher error code for patching is : {json_string} ")
            data = json.loads(json_string)
            if data:
                return data.get("data", {}).get("error_code") == error_code
    except json.JSONDecodeError:
        ebLogInfo("JSON Decoder Error for checking dispatcher error code during patching")
        return False
    return False

# This function matches quarterly version strings like "25.2.10.0.0.250314","24.1.10.0.0.250313.1",
# Does not match exasplice versions like 250819
def mQuarterlyVersionPatternMatch(version):
    regex = r"\d+\.\d+\.\d+\.\d+\.\d+\.\d+(?:\.\d+)?"
    pattern = re.compile(regex)
    return bool(pattern.fullmatch(version))


# This function matches SMR version strings like "250617","250819.1"
def mExaspliceVersionPatternMatch(version):
    regex = r'^\d{6}(\.\d+)?$'
    pattern = re.compile(regex)
    return bool(pattern.fullmatch(version))

def mIsLatestTargetVersionAllowed(target_version, target_type, exasplice):
    """
    Check if LATEST targetVersion is allowed as a literal string.
    LATEST is allowed only for DOM0 with exasplice='yes'.

    Args:
        target_version: The target version string
        target_type: The target type (dom0, domu, cell, etc.)
        exasplice: The exasplice value from AdditionalOptions

    Returns:
        True if LATEST is allowed (dom0 + exasplice=yes)
        False otherwise
    """
    return (target_version and target_version.upper() == 'LATEST' and
            target_type and target_type.lower() == PATCH_DOM0 and
            exasplice and exasplice.lower() == 'yes')
