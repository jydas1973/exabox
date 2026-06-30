#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/utils/clu_utils.py aararora_bug-38723384/2 2026/02/17 09:01:14 aararora Exp $
#
# clu_utils.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
#
#    NAME
#    clu_utils.py - Utility class for helper methods of clucontrol
#                   related classes
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    06/18/26 - Bug#39540098 Carry over cert for R1 to ADBD DomUs
#    rajsag      05/29/26 - Bug 39283211 - support X11 no-XRMEM cell types
#    prsshukl    05/21/26 - Bug 39416987 - EXACC: SSL INSPECTION: PHASE1:
#                           EXACLOUD ISN'T COPYING CUSTOMER ROOT CA AS UNABLE
#                           TO LOGIN TO THE CPS WALLET
#    aararora    03/20/26 - 39106054: Add Falcon agent install helper
#    aararora    01/27/26 - Bug 38723384: Add retry/force logic for crs restart
#    prsshukl    03/04/25 - Bug 38828221: Copy customer Root CA for SSL Inspection enabled infra
#    remamid     12/09/25 - perform kernel shmmax checks for memreshape bug
#                           38626206
#    nelango     08/17/25 - Bug 38257756: Add method to retrieve list of dbs not up
#    aararora    07/04/25 - Bug 38152132 - Append xrmem celltype to es.properties
#    rajsag      05/30/25 - Enh 37542341 - support additional response fields in exacloud status response for add compute steps
#    aararora    06/04/25 - Bug 37999466: Handle down interfaces for DR Network
#    rajsag      05/22/25 - Enh 37526315 - support additional response fields
#                           in exacloud status response for create service
#                           steps
#    aararora    03/13/25 - Bug 37672091: Set global properties in
#                           es.properties oeda file
#    aararora    02/05/25 - ER 37541321: Update percentage progress of
#                           rebalance operation
#    aararora    01/10/25 - Bug 37419029: Set DISABLEVALIDATEDGSPACEFOR37371565
#                           to true
#    aararora    12/18/24 - ER 37402747: Add NTP and DNS entries in xml
#    aararora    10/11/24 - Bug 37154572: Set oeda property to ignore cell
#                           image version difference during add cell.
#    aararora    08/13/24 - ER 36904128: Secure erase API
#    aararora    12/04/23 - Utility class for helper methods of clucontrol
#                           related classes
#    aararora    12/04/23 - Creation
#
import base64
import glob
import json
import os
import shlex
import time
import shutil
from six.moves import urllib

from base64 import b64decode
from exabox.core.DBStore import ebGetDefaultDB
from exabox.utils.common import mCompareModel
from exabox.utils.node import connect_to_host, node_exec_cmd_check, node_cmd_abs_path_check, node_exec_cmd
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError, gReshapeError, gPartialError, gProvError, gNodeElasticError
from exabox.ovm.utils.cellcli_utils import (ebCellCliUtils,
                                            X11_EF_NOXRMEM_MACHINE_TYPE,
                                            X11_HC_NOXRMEM_MACHINE_TYPE)

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.ExaRegion import is_r1_region, get_r1_certificate_path

DEFAULT_CRS_RETRY_ATTEMPTS = 3
DEFAULT_CRS_RETRY_DELAY = 10

FALCON_REMOTE_DIR = "/tmp"
FALCON_SERVICE_NAME = "falcon-sensor.service"
FALCONCTL_PATH = "/opt/CrowdStrike/falconctl"
FALCON_PROXY_PORT = "80"
FALCON_METADATA_URL = "http://169.254.169.254/opc/v2/instance/regionInfo/regionIdentifier"
FALCON_METADATA_HEADER = "Authorization: Bearer Oracle"
FALCON_DOWNLOAD_TIMEOUT = 300
FALCON_RPM_PATTERN = "falcon-sensor*.el{major}.x86_64.rpm"
FALCON_PACKAGE_NAME = "falcon-sensor"
FALCON_LOG_PREFIX = "[FalconAgent]"
FALCON_DEFAULT_CID = "9069F7873C164912A480334E0EE7BC9B-EB"

def mRunCrsCommandsWithRetry(aNode,
                             aCommands,
                             aLabel=None,
                             aTimeout=None,
                             aAttempts=DEFAULT_CRS_RETRY_ATTEMPTS,
                             aDelay=DEFAULT_CRS_RETRY_DELAY,
                             aRaiseOnFailure=True):
    """Execute CRS/SRVCTL command(s) with retry and optional validation."""
    if aAttempts < 1:
        _msg = f"Ensure Attempts are >= 1 to execute the commands. Current number of attempts: {aAttempts}."
        ebLogError(_msg)
        raise ExacloudRuntimeError(_msg)
    if not isinstance(aCommands, (list, tuple)):
        _commands = [aCommands]
    else:
        _commands = list(aCommands)
    _label = aLabel if aLabel else "; ".join(_commands)
    _last_error = None
    for _attempt in range(1, aAttempts + 1):
        # First attempt will be with the command at 0th index
        # Rest of the attempts will be done with the rest of the commands
        # at 1st index onwards
        _command = _commands[min(_attempt - 1, len(_commands) - 1)]
        ebLogInfo(f"Attempt {_attempt}/{aAttempts}: Executing {_label} -> {_command}")
        _stdin, _stdout, _stderr = aNode.mExecuteCmd(_command, aTimeout)
        _exit_status = aNode.mGetCmdExitStatus()
        if _exit_status is None:
            _exit_status = -1
        _out = _stdout.read() if _stdout else ""
        _err = _stderr.read() if _stderr else ""
        if _exit_status == 0:
            ebLogInfo(f"Command {_label} succeeded")
            return True
        _last_error = f"exit status {_exit_status}, stdout: {_out}, stderr: {_err}"
        if _attempt < aAttempts:
            ebLogWarn(f"Command {_label} failed (attempt {_attempt}): {_last_error}. Retrying in {aDelay} seconds")
            # Delay of 10 seconds
            time.sleep(aDelay)
    _message = f"Command {_label} failed after {aAttempts} attempts. Last error: {_last_error}"
    ebLogError(_message)
    if aRaiseOnFailure:
        raise ExacloudRuntimeError(_message)
    return False


class ebCluUtils(object):

    def __init__(self, aExaBoxCluCtrl=None):
        self.__cluctrl = aExaBoxCluCtrl

    def mUpdateRequestObjectData(self, aResult):
        """
        Utility method to update request object for the current request
        with the obtained result in 'data' field of the requests table as json.
        """
        # Return reqobj to ECRA
        _reqobj = self.__cluctrl.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(aResult))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        else:
            #Console output
            ebLogInfo(json.dumps(aResult, sort_keys=True, indent=4))

    def mIsBase64(self, aEncodedStr):
        try:
            return base64.b64encode(base64.b64decode(aEncodedStr)).decode('utf-8') == aEncodedStr
        except Exception:
            return False

    def mSetPropertyValueOeda(self, aProperty, aValue, aPreviousValue,
                              aAddIfNotPresent=True, aPropertiesPath=None):
        """
        Set the property aProperty to aValue in es.properties for
        an oeda request id.
        """
        ebLogInfo(f'Setting {aProperty} to {aValue} in oeda es.properties.')
        if not aPropertiesPath:
            _oeda_properties_path = os.path.join(self.__cluctrl.mGetOedaPath(),'properties','es.properties')
        else:
            _oeda_properties_path = aPropertiesPath
        if not os.path.exists(_oeda_properties_path):
            ebLogWarn(f"OEDA property path {_oeda_properties_path} doesn't exist. Not setting {aProperty} to {aValue}.")
            return
        _err_msg = "{0} property could not be set to {1} in {2} due to an error. Output is {3}. Error is {4}."
        _cmd_prop_exists = f"/bin/grep -q {aProperty} {_oeda_properties_path}"
        _rc, _i, _o, _e = self.__cluctrl.mExecuteLocal(_cmd_prop_exists)
        if _rc != 0:
            ebLogWarn(f'{aProperty} property does not exist in {_oeda_properties_path}')
            if not aAddIfNotPresent:
                return
            try:
                _sed_cmd = f"/bin/sed -i '$a {aProperty}={aValue}' {_oeda_properties_path}"
                self.__cluctrl.mExecuteLocal(_sed_cmd)
            except Exception as ex:
                ebLogError(_err_msg.format(aProperty, aValue, _oeda_properties_path, _o, _e))
                return
        else:
            if aPreviousValue:
                # If we want to check the previous value and then update it - i.e. previous property
                # value is known along with the new property value
                _cmd_change_prop = f"/bin/sed 's/^{aProperty}={aPreviousValue}/{aProperty}={aValue}/' -i {_oeda_properties_path}"
            else:
                # Below command is to update the es properties without checking for previous value
                # - we don't care what is the previous value and we should update it anyhow
                _cmd_change_prop = f"/bin/sed 's/\<{aProperty}\>.*$/{aProperty}={aValue}/g' -i {_oeda_properties_path}"
            _rc, _i, _o, _e = self.__cluctrl.mExecuteLocal(_cmd_change_prop)
            if _rc != 0:
                ebLogError(_err_msg.format(aProperty, aValue, _oeda_properties_path, _o, _e))
                return
        _cmd_verify_prop = f"/bin/grep -q '{aProperty}={aValue}' {_oeda_properties_path}"
        _rc, _i, _o, _e = self.__cluctrl.mExecuteLocal(_cmd_verify_prop)
        if _rc != 0:
            ebLogError(_err_msg.format(aProperty, aValue, _oeda_properties_path, _o, _e))
        else:
            ebLogInfo(f'{aProperty} property is set to {aValue} in {_oeda_properties_path}.')

    def mExtractNtpDnsPayload(self, aPayload):
        """
        Extract ntp and dns information from the payload and return them as list
        """
        _payload = aPayload
        _dns_servers = []
        _ntp_servers = []
        if 'ntp' in _payload:
            for _server in _payload['ntp']:
                if 'ipaddr' in _server:
                    _ntp_servers.append(_server['ipaddr'])
        if 'dns' in _payload:
            for _server in _payload['dns']:
                if 'ipaddr' in _server:
                    _dns_servers.append(_server['ipaddr'])
        return (_dns_servers, _ntp_servers)

    def mIsNumber(self, aString):
        """
        Checks if the passed string is a number
        """
        try:
            float(aString)
            return True
        except ValueError:
            return False

    def mAppendPropertyValueOeda(self, aProperty, aValue, aDelimiter=",", aPropertiesPath=None):
        """
        Append aValue to the existing property aProperty in es.properties.
        """
        ebLogInfo(f'Appending {aValue} to {aProperty} in oeda es.properties.')
        if not aPropertiesPath:
            _oeda_properties_path = os.path.join(self.__cluctrl.mGetOedaPath(),'properties','es.properties')
        else:
            _oeda_properties_path = aPropertiesPath
        if not os.path.exists(_oeda_properties_path):
            ebLogWarn(f"OEDA property path {_oeda_properties_path} doesn't exist. Not appending {aValue} to {aProperty}.")
            return

        _cmd_prop_exists = f"/bin/grep -q {aProperty} {_oeda_properties_path}"
        _rc, _i, _o, _e = self.__cluctrl.mExecuteLocal(_cmd_prop_exists)
        if _rc != 0:
            # Property does not exist, so set it
            try:
                _sed_cmd = f"/bin/sed -i '$a {aProperty}={aValue}' {_oeda_properties_path}"
                self.__cluctrl.mExecuteLocal(_sed_cmd)
            except Exception as ex:
                _err_msg = f"{aProperty} property could not be set to {aValue} in {_oeda_properties_path} due to an error : {ex}."
                ebLogError(_err_msg)
                return
        else:
            # Get the existing values for the given property
            _value = self.__cluctrl.mGetOedaProperty(aProperty)
            # Check if the value being appended is already present in the full property values string
            if aValue.strip(aDelimiter) in _value:
                ebLogInfo(f'{aValue} is already present in {aProperty} in {_oeda_properties_path}. No need to append.')
                return
            # Append the new value using sed
            # The command is designed to append a new value to a multi-line property in es.properties file
            # Below regex checks from property matched till there is no backslash for the property.
            # Once we find a sequence matching this pattern, the below script in {{ .. }} loops and checks for lines not ending with
            # backslash and not having only whitespaces and if the value is not already appended. If such a pattern is found - 
            # it is appended with the given value along with delimiter
            _sed_cmd = f"/bin/sed -i '/^{aProperty}=/,/[^\\\\]$/ {{ /^\s*$/b; /[^\\\\]$/!b; /{aDelimiter}{aValue.strip(aDelimiter)}$/b; s/$/{aDelimiter}{aValue.strip(aDelimiter)}/; }}' {_oeda_properties_path}"
            try:
                self.__cluctrl.mExecuteLocal(_sed_cmd)
            except Exception as ex:
                _err_msg = f"{aProperty} property could not be updated in {_oeda_properties_path} due to an error : {ex}."
                ebLogError(_err_msg)
                return

        ebLogInfo(f'{aValue} is successfully appended to {aProperty} in {_oeda_properties_path}.')

    def mGetAddedCellPayloads(self):
        if not hasattr(self.__cluctrl, 'mGetArgsOptions'):
            return []

        try:
            _options = self.__cluctrl.mGetArgsOptions()
        except Exception as ex:
            ebLogWarn(f"*** Unable to retrieve args options for X11 no-XRMEM detection: {ex}")
            return []

        _jsonconf = getattr(_options, 'jsonconf', None)
        if not isinstance(_jsonconf, dict):
            return []

        _reshape_config = _jsonconf.get('reshaped_node_subset', {})
        if not isinstance(_reshape_config, dict):
            return []

        _added_cells = _reshape_config.get('added_cells', [])
        if isinstance(_added_cells, list):
            return _added_cells
        if isinstance(_added_cells, tuple):
            return list(_added_cells)
        return []

    def mGetCurrentCellNames(self):
        if not hasattr(self.__cluctrl, 'mReturnCellNodes'):
            return []

        try:
            _cell_nodes = self.__cluctrl.mReturnCellNodes()
        except Exception as ex:
            ebLogWarn(f"*** Unable to retrieve current cells for X11 no-XRMEM detection: {ex}")
            return []

        if isinstance(_cell_nodes, dict):
            return list(_cell_nodes.keys())
        if isinstance(_cell_nodes, (list, tuple, set)):
            return list(_cell_nodes)
        return []

    def mGetX11NoXrmemMachineTypes(self):
        _cellcli_utils = ebCellCliUtils(self.__cluctrl)
        _machine_types = set()
        _added_cells = self.mGetAddedCellPayloads()
        for _cell in _added_cells:
            if not isinstance(_cell, dict):
                continue

            _cell_name = _cell.get('cell_hostname') or _cell.get('hostname')
            if not _cell_name:
                continue

            _rack_info = _cell.get('rack_info', {})
            if not isinstance(_rack_info, dict):
                _rack_info = {}

            _machine_type = _cellcli_utils.mGetX11NoXrmemMachineType(
                _cell_name,
                aRackItemDescription=_rack_info.get('description'),
                aCellType=_cell.get('model') or _cell.get('type'))
            if _machine_type:
                _machine_types.add(_machine_type)

        if _added_cells:
            return _machine_types

        for _cell_name in self.mGetCurrentCellNames():
            _machine_type = _cellcli_utils.mGetX11NoXrmemMachineType(_cell_name)
            if _machine_type:
                _machine_types.add(_machine_type)

        return _machine_types

    def mUpdateGlobalEsProperties(self):
        # Update global es.properties under exacloud/oeda/properties folder
        _global_es_properties_path = os.path.join(self.__cluctrl.mGetBasePath(),
                                                  "oeda/properties/es.properties")
        # For a unified method, please update the below dictionary to update any global es properties
        _dict_global_es_properties = {"DISABLEVALIDATEDGSPACEFOR37371565": {"previous": "false",
                                                                            "new": "true",
                                                                            "action": "replace"}}
        _append_celltypes_x11_xrmem = self.__cluctrl.mCheckConfigOption('append_celltypes_x11_xrmem')
        _x11_noxrmem_machine_types = self.mGetX11NoXrmemMachineTypes()
        _celltype_values = []
        _hc_celltype_values = []
        if _append_celltypes_x11_xrmem and _append_celltypes_x11_xrmem == 'True':
            _celltype_values.append("X11MHCXRMEM:X11_XRMEM_ROCE_CELL_XC")
            _hc_celltype_values.append("X11MHCXRMEM:X11_XRMEM_ROCE_CELL_XC")
        if X11_HC_NOXRMEM_MACHINE_TYPE in _x11_noxrmem_machine_types:
            _celltype_values.append("X11MHCNOXRMEM:X11_NOXRMEM_ROCE_CELL_XC")
            _hc_celltype_values.append("X11MHCNOXRMEM:X11_NOXRMEM_ROCE_CELL_XC")
        if X11_EF_NOXRMEM_MACHINE_TYPE in _x11_noxrmem_machine_types:
            _celltype_values.append("X11MEFNOXRMEM:X11_NOXRMEM_ROCE_CELL_EF")
        if _celltype_values:
            _dict_global_es_properties["CELLTYPES"] = {
                "action": "append",
                "value": ",".join(_celltype_values),
                "delimiter": ","
            }
        if _hc_celltype_values:
            _dict_global_es_properties["HC_CELL_TYPES"] = {
                "action": "append",
                "value": ",".join(_hc_celltype_values),
                "delimiter": ","
            }
        for _property, _values in _dict_global_es_properties.items():
            if _values["action"] == "replace":
                self.mSetPropertyValueOeda(_property, _values["new"], _values["previous"],
                                           aPropertiesPath=_global_es_properties_path)
            elif _values["action"] == "append":
                self.mAppendPropertyValueOeda(_property, _values["value"], _values.get("delimiter", ","),
                                              aPropertiesPath=_global_es_properties_path)
    
    def mStepSpecificDetails(self,aTaskType, aStatus, aProgressMessage, aStepName='', aResource=''):
        """
        This method prepares the data aStepSpecificDetails to be populated in mUpdateTaskProgressStatus  
        The task progress status is updated in 'time_check_rebalance_seconds' time. Current
        """
        _data = {}
        _response = {}

        if aTaskType == 'createServiceDetails' or aTaskType == 'deleteServiceDetails' or aTaskType == 'elasticAddDetails' or aTaskType == 'elasticDeleteDetails':
            _data = {
                "stepName": aStepName,
                "status": aStatus,
                "progressMessage": aProgressMessage
            }
        else:
            _data = {
                "resource": aResource,
                "status": aStatus,
                "progressMessage": aProgressMessage
            }

        _response = {aTaskType: _data}
        return _response

    def mUpdateTaskProgressStatus(self, aNodeCompleted, aPercentComplete, aCmdName, aStatus, aStepSpecificDetails={}, aData=None):
        """
        This method prepares a task progress status structure and updates it in the "data" column
        of exacloud mysql DB from where ecra can query the same.

        """

        _stepProgressDetails = {}

        _stepProgressDetails["stepProgressDetails"] = {"message": aCmdName,
                                                        "completedNodes": aNodeCompleted,
                                                        "stepSpecificDetails": aStepSpecificDetails,
                                                        "percent_complete": aPercentComplete,
                                                        "status": aStatus}
        if aData is not None:
            _stepProgressDetails.update(aData)
        self.mUpdateRequestObjectData(_stepProgressDetails)

    def mIsAllowedFlowDownInterfaces(self, aNode, aMissingLink, aSingleDom0, aExadataModel, aCause=None, aAction=None, aDRNet=False):
        """
        This method handles error scenario for down physical interfaces.
        If the command under execution is allowed to not raise exception - do not raise exception.
        """
        _node = aNode
        _missing_link = aMissingLink
        _exadata_model = aExadataModel
        # Do not raise exception for down physical interfaces during network validation call
        # This ensures that the report gets generated and reaches to OCI UI
        flowsAllowedWithIntfDown = ['deleteservice', 'vmgi_delete', 'validate_network_bonding','checkcluster']
        if self.__cluctrl.mGetCmd() in flowsAllowedWithIntfDown or \
                (
                    self.__cluctrl.mGetArgsOptions().healthcheck == 'custom' and \
                    self.__cluctrl.mGetArgsOptions().jsonconf["profile_type"] in ["custnet_validate", "custnet_revalidate"]
                ):

            ebLogWarn('mCheckDom0NetworkType Failed - Network Configuration Error in DOM0 {}'.format(_node.mGetHostname()))
            ebLogWarn('Continuing since the flow is identified to be one of {} or network validation'.format(flowsAllowedWithIntfDown))
            # We need to provide healthcheck with the error information to be shown to the customer
            # Below condition will be matched when there is a hardware fault detected via _missing_link list
            # and when called with the DOM0 hostname from mGetNetworkSetupInformation method.
            # The information for X8 and below hardware is shared with healthcheck command in same format as it is done currently
            # for X9 and above exadata hardware.
            if _missing_link and aSingleDom0 and mCompareModel(_exadata_model, 'X9') < 0:
                _operational_state = {'UP': [], 'DOWN': _missing_link, 'MISSING': [], 'UP_AFTER_BOUNCE': []}
                _interface_details = {"OPERATIONAL_STATE": _operational_state, "INTERFACE_TYPES": {'COPPER': [], 'FIBER': [], 'UNKNOWN': _missing_link}}
                if aCause:
                    _cause = aCause
                else:
                    _cause = f"Faulty interface found: {_missing_link}."
                if aAction:
                    _action = aAction
                else:
                    _action = f"Bring the faulty interface {_missing_link} up for the expected configuration."
                _error_dict = {"CAUSE": _cause, "ACTION": _action, "INTERFACE_DETAILS": _interface_details}
                self.__cluctrl.mSetNetDetectError(aSingleDom0, _error_dict)
            elif aDRNet and aSingleDom0 and mCompareModel(_exadata_model, 'X9') >= 0:
                # For DR net, we don't have a separate error framework for healthcheck for X9 and above
                # For client and backup network, cluinetworkdetect.py has the implementation for error framework
                # for X9 and above exadata model.
                _error_dict = self.__cluctrl.mGetNetDetectError()
                _operational_state = {'UP': [], 'DOWN': _missing_link, 'MISSING': [], 'UP_AFTER_BOUNCE': []}
                _interface_details = {"OPERATIONAL_STATE": _operational_state, "INTERFACE_TYPES": {'COPPER': [], 'FIBER': [], 'UNKNOWN': _missing_link}}
                if aCause:
                    _cause = aCause
                else:
                    _cause = f"Faulty interface found: {_missing_link}."
                if aAction:
                    _action = aAction
                else:
                    _action = f"Bring the faulty interface {_missing_link} up for the expected configuration."
                _error_dict_DOM0 = {}
                if _error_dict and aSingleDom0 in _error_dict:
                    # This condition would be reached when the error dictionary is filled with DOM0 key
                    # incase of hardware issues in client/backup network. Below will append error details
                    # for DR Network to existing dictionary for client/backup networks.
                    _error_dict_DOM0 = _error_dict[aSingleDom0]
                    _error_dict_DOM0["CAUSE"] = _error_dict_DOM0["CAUSE"] + _cause
                    _error_dict_DOM0["ACTION"] = _error_dict_DOM0["ACTION"] + _action
                    _error_dict_DOM0["INTERFACE_DETAILS"]["OPERATIONAL_STATE"]["DOWN"] = _error_dict_DOM0["INTERFACE_DETAILS"]["OPERATIONAL_STATE"]["DOWN"] +\
                                                                                         _operational_state["DOWN"]
                    _error_dict_DOM0["INTERFACE_DETAILS"]["INTERFACE_TYPES"]["UNKNOWN"] = _error_dict_DOM0["INTERFACE_DETAILS"]["INTERFACE_TYPES"]["UNKNOWN"] +\
                                                                                          _interface_details["INTERFACE_TYPES"]["UNKNOWN"]
                if not _error_dict_DOM0:
                    _error_dict_DOM0 = {"CAUSE": _cause, "ACTION": _action, "INTERFACE_DETAILS": _interface_details}
                self.__cluctrl.mSetNetDetectError(aSingleDom0, _error_dict_DOM0)
            return True
        else:
            return False

    def getNotUpDbsList(self, aDomU):
        _not_up_DBlist = []
        _db = ebGetDefaultDB()
        _dbs_up = _db.mGetDBListByNode(aDomU)
        if _dbs_up != '':
            _dbActiveList = self.__cluctrl.mGetActiveDbInstances(aDomU)
            _dbList = _dbs_up.split(" ")
            ebLogInfo('*** DBs list as per the configuration %s' % (_dbList))
            ebLogInfo('*** DBs active now are %s' % (_dbActiveList))
            if not set(_dbList).issubset(set(_dbActiveList)):
                _not_up_DBlist = list(set(_dbList) - set(_dbActiveList))
                ebLogInfo('*** DBs not up now are %s' % (_not_up_DBlist))
        return _not_up_DBlist

    # Validate shmmax/shmall runtime values on the DomU.
    # to be called for mem reshape as part of post checks.
    def mValidateSharedMemSettings(self, aDomU):
        ebLogInfo(f"*** Validating shared memory settings on {aDomU} ***")

        _config_shmmax_ratio = self.__cluctrl.mCheckSubConfigOption('reshape_memory', 'shmmax_ratio')
        if _config_shmmax_ratio is None:
            _config_shmmax_ratio = '0.8'

        try:
            _shmmax_ratio = float(_config_shmmax_ratio)
        except (TypeError, ValueError):
            _msg = (
                f"Invalid reshape_memory.shmmax_ratio value '{_config_shmmax_ratio}'. "
                "Must be numeric"
            )
            ebLogError(f"*** {_msg} ***")
            raise ExacloudRuntimeError(0x0119, 0xA, _msg)

        if _shmmax_ratio <= 0:
            _msg = "reshape_memory.shmmax_ratio must be greater than zero"
            ebLogError(f"*** {_msg} ***")
            raise ExacloudRuntimeError(0x0119, 0xA, _msg)

        with connect_to_host(aDomU, get_gcontext()) as _node:
            _i, _o, _e = _node.mExecuteCmd('/usr/sbin/sysctl -n kernel.shmmax')
            if _node.mGetCmdExitStatus() != 0:
                _err = _e.read().strip()
                _msg = f"Failed to read kernel.shmmax runtime value on node: {aDomU}. {_err}"
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0441, 0xA, _msg)

            try:
                _runtime_shmmax = int(_o.readline().strip())
            except Exception as e:
                _msg = f"Exception: {e}, Invalid kernel.shmmax runtime value on node: {aDomU}"
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0441, 0xA, _msg)

            _i, _o, _e = _node.mExecuteCmd("/bin/grep MemTotal /proc/meminfo")
            if _node.mGetCmdExitStatus() != 0:
                _err = _e.read().strip()
                _msg = f"Failed to read total memory on node: {aDomU}. {_err}"
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0441, 0xA, _msg)

            try:
                _meminfo_line = _o.readline().strip()
                _mem_total_kb = int(_meminfo_line.split()[1])
                _total_memory_bytes = _mem_total_kb * 1024
            except Exception as e:
                _msg = f"Exception: {e}, Invalid MemTotal entry in /proc/meminfo on node: {aDomU}."
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0441, 0xA, _msg)

            _min_shmmax = int(_shmmax_ratio * _total_memory_bytes)
            if _runtime_shmmax < _min_shmmax:
                _msg = (
                    f"kernel.shmmax ({_runtime_shmmax}) is below "
                    f"{_shmmax_ratio * 100}% of total memory "
                    f"({_total_memory_bytes}) on node: {aDomU}"
                )
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0808, 0xA, _msg)

            _i, _o, _e = _node.mExecuteCmd('getconf PAGE_SIZE')
            if _node.mGetCmdExitStatus() != 0:
                _err = _e.read().strip()
                _msg = f"Failed to read PAGE_SIZE on node: {aDomU}. {_err}"
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0441, 0xA, _msg)

            try:
                _page_size = int(_o.readline().strip())
            except Exception as e:
                _msg = f"Exception {e}, Invalid PAGE_SIZE value on node: {aDomU}"
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0441, 0xA, _msg)

            _expected_shmall = int(_runtime_shmmax / _page_size)

            _i, _o, _e = _node.mExecuteCmd('/usr/sbin/sysctl -n kernel.shmall')
            if _node.mGetCmdExitStatus() != 0:
                _err = _e.read().strip()
                _msg = f"Failed to read kernel.shmall runtime value on node: {aDomU}. {_err}"
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0441, 0xA, _msg)

            try:
                _runtime_shmall = int(_o.readline().strip())
            except Exception as e:
                _msg = f"Exception {e}, Invalid kernel.shmall runtime value on node: {aDomU}"
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0808, 0xA, _msg)

            if _runtime_shmall != _expected_shmall:
                _msg = (
                    f"kernel.shmall runtime value ({_runtime_shmall}) does not match expected value ({_expected_shmall}) "
                    f"based on kernel.shmmax on node: {aDomU}"
                )
                ebLogError(f"*** {_msg} ***")
                raise ExacloudRuntimeError(0x0808, 0xA, _msg)

            ebLogInfo(
                f"*** Shared memory settings validated for {aDomU}: "
                f"shmmax={_runtime_shmmax}, shmall={_runtime_shmall}, page_size={_page_size} ***"
            )

    # Copying Domu certificates and key during Create Service flow and Add compute flow
    # if copy fails, then fail CS and Add compute flow respectively.
    def mSetupCustomerRootCACertificates(self):
        try:
            _cert_source_destination_mapping = {}
            _customer_root_ca_cert_path = "/etc/pki/ca-trust/source/anchors/customer-root-ca.crt"
            if self.__cluctrl.mIsSslInspectionEnabled():
                if os.path.exists(_customer_root_ca_cert_path) is False:
                    ebLogError(f"*** Fatal Error *** : customer-root-ca.crt does not exist in cps")
                    raise ExacloudRuntimeError(0x0820, 0xA, 'customer-root-ca.crt addition failed!')
                
                _cert_source_destination_mapping = {
                    f'{_customer_root_ca_cert_path}' : f'{_customer_root_ca_cert_path}',
                }

            if _cert_source_destination_mapping:
                for _, _domU in self.__cluctrl.mReturnDom0DomUPair():
                    with connect_to_host(_domU, get_gcontext(), username='root') as _nodeU:
                        for source_file , dest_file in _cert_source_destination_mapping.items():
                            dest_directory_path = os.path.dirname(dest_file)
                            if _nodeU.mFileExists(dest_directory_path) is False:
                                ebLogTrace(f"Directory path : {dest_directory_path} does not exist , creating the path")
                                _nodeU.mExecuteCmd(f'mkdir -p {dest_directory_path}')
                            # Copy customer-root-ca.crt from cps to DomU
                            ebLogInfo(f"*** Copying customer-root-ca.crt to {dest_file} on {_domU}")
                            _nodeU.mCopyFile(source_file, dest_file)
                            if not _nodeU.mFileExists(dest_file):
                                ebLogError(f"*** Fatal Error *** : Error while copying the customer-root-ca.crt to domU {_domU}")
                                raise ExacloudRuntimeError(0x0820, 0xA, 'customer-root-ca.crt addition failed!')

                            node_exec_cmd_check(_nodeU, "update-ca-trust")
                            ebLogInfo(f"*** Completed CA trust refresh on {_domU}")
                        
        except Exception as e:
            ebLogError(f'Error while copying customer-root-ca.crt to domU: {e}')
            raise ExacloudRuntimeError(0x0820, 0xA, e)

    def mInstallFalconAgentOnDomus(self, aDomus, aOperationLabel=None):
        """Install and configure CrowdStrike Falcon agent on the provided DomUs."""
        if not self.__cluctrl.mCheckConfigOption('falcon_agent_install', 'True'):
            ebLogInfo(f"{FALCON_LOG_PREFIX} Installation disabled via exabox.conf; skipping.")
            return
        _cid = self.__cluctrl.mCheckConfigOption('falcon_sensor_cid')
        if not _cid:
            ebLogWarn(f"{FALCON_LOG_PREFIX} falcon_sensor_cid missing in exabox.conf; using default CID.")
            _cid = FALCON_DEFAULT_CID

        _operation = aOperationLabel or "DomU operation"
        _images_dir = os.path.join(get_gcontext().mGetBasePath(), "images")
        _rpm_urls_cfg = self.__cluctrl.mCheckConfigOption('falcon_sensor_rpm_urls')
        _rpm_urls = dict(_rpm_urls_cfg) if _rpm_urls_cfg else None

        for _domu in aDomus:
            self.mInstallFalconSensor(
                _domu,
                _images_dir,
                _rpm_urls,
                _cid,
                _operation
            )

        ebLogInfo(f"{FALCON_LOG_PREFIX} Falcon agent processing complete for hosts: {aDomus}")

    def mInstallFalconSensor(self, aDomU, aImagesDir, aRpmUrls, aCid, aOperationLabel):
        """Perform Falcon RPM staging, installation, and configuration on a single DomU."""
        ebLogInfo(f"{FALCON_LOG_PREFIX} [{aOperationLabel}] Installing Falcon agent on {aDomU}")
        try:
            with connect_to_host(aDomU, get_gcontext()) as _node:
                _ol_major = self.mDetectOracleLinuxMajor(_node, aDomU)
                ebLogInfo(f"{FALCON_LOG_PREFIX} Detected Oracle Linux version OL{_ol_major} on {aDomU}")

                _local_rpm = self.mFindLocalRpm(aImagesDir, _ol_major)
                _source_rpm = _local_rpm
                if _local_rpm:
                    ebLogInfo(f"{FALCON_LOG_PREFIX} Using local Falcon RPM '{_local_rpm}' for {aDomU}")
                else:
                    _rpm_url = None
                    if aRpmUrls:
                        _rpm_url = aRpmUrls.get(f"ol{_ol_major}")
                        if not _rpm_url:
                            ebLogWarn(f"{FALCON_LOG_PREFIX} RPM URL for OL{_ol_major} not provided; expecting RPM in images directory.")
                    if not _rpm_url:
                        raise ExacloudRuntimeError(
                            f"{FALCON_LOG_PREFIX} Falcon RPM for OL{_ol_major} not found locally. "
                            "Place the appropriate RPM in exacloud/images or configure falcon_sensor_rpm_urls."
                        )
                    _source_rpm = self.mDownloadFalconRpm(aImagesDir, _rpm_url)
                    ebLogInfo(f"{FALCON_LOG_PREFIX} Downloaded Falcon RPM '{_source_rpm}' for {aDomU}")

                _rpm_name = os.path.basename(_source_rpm)
                _remote_rpm_path = os.path.join(FALCON_REMOTE_DIR, _rpm_name)
                self.mStageLocalRpm(_node, aDomU, _source_rpm, _remote_rpm_path)

                if not self.mIsFalconInstalled(_node, aDomU):
                    self.mInstallRpmOnNode(_node, aDomU, _remote_rpm_path)
                else:
                    ebLogInfo(f"{FALCON_LOG_PREFIX} falcon-sensor already installed on {aDomU}; applying configuration.")

                self.mConfigureFalconSensor(_node, aDomU, aCid)
                self.mValidateFalconService(_node, aDomU)
                self.mRemoveRemoteFile(_node, aDomU, _remote_rpm_path)
        except ExacloudRuntimeError:
            raise
        except Exception as _exc:
            raise ExacloudRuntimeError(f"{FALCON_LOG_PREFIX} Falcon agent setup failed on {aDomU}: {_exc}") from _exc
        ebLogInfo(f"{FALCON_LOG_PREFIX} Falcon agent setup completed on {aDomU}")

    def mDetectOracleLinuxMajor(self, aNode, aDomU):
        """Detect oracle major linux version on domu"""
        _cmd = (
            "if [ -r /etc/os-release ]; then "
            ". /etc/os-release >/dev/null 2>&1; "
            "printf '%s' \"${VERSION_ID%%.*}\"; "
            "elif [ -r /etc/oracle-release ]; then "
            "/bin/grep -Eo '[0-9]+' /etc/oracle-release | head -n1; "
            "fi"
        )
        _result = node_exec_cmd(aNode, _cmd, check_error=False)
        _major = (_result.stdout or "").strip()
        if _result.exit_code != 0 or not _major:
            _msg = f"Unable to determine Oracle Linux major version on {aDomU}."
            ebLogError(f"{FALCON_LOG_PREFIX} {_msg}")
            raise ExacloudRuntimeError(_msg)
        return _major

    def mFindLocalRpm(self, aImagesDir, aOlMajor):
        """Return the Falcon RPM path from the images directory if it already exists."""
        if not aImagesDir or not os.path.isdir(aImagesDir):
            return None
        _pattern = os.path.join(aImagesDir, FALCON_RPM_PATTERN.format(major=aOlMajor))
        _matches = list(glob.glob(_pattern))
        if _matches:
            return _matches[0]
        return None

    def mStageLocalRpm(self, aNode, aDomU, aLocalPath, aRemotePath):
        """Copy the Falcon RPM to the DomU tmp directory and ensure it is non-empty."""
        if not os.path.exists(aLocalPath):
            raise ExacloudRuntimeError(f"{FALCON_LOG_PREFIX} Local Falcon RPM '{aLocalPath}' not found.")
        _rm_cmd = node_cmd_abs_path_check(aNode, "rm") or "/bin/rm"
        node_exec_cmd(aNode, f"{_rm_cmd} -f {shlex.quote(aRemotePath)}", check_error=False)
        _remote_dir = os.path.dirname(aRemotePath) or FALCON_REMOTE_DIR
        aNode.mCopyFile(aLocalPath, _remote_dir)
        if not aNode.mFileExists(aRemotePath):
            raise ExacloudRuntimeError(f"{FALCON_LOG_PREFIX} Failed to copy Falcon RPM to {aDomU}:{aRemotePath}")

    def mDownloadFalconRpm(self, aImagesDir, aUrl):
        """Download the Falcon RPM to the shared images directory using curl."""
        _filename = os.path.basename(urllib.parse.urlparse(aUrl).path)

        _target_dir = aImagesDir or os.path.join(get_gcontext().mGetBasePath(), "images")
        _target_path = os.path.join(_target_dir, _filename)
        if os.path.exists(_target_path) and os.path.getsize(_target_path) > 0:
            ebLogInfo(f"{FALCON_LOG_PREFIX} Reusing previously downloaded Falcon RPM '{_target_path}'.")
            return _target_path

        _curl_path = shutil.which("curl") or "/usr/bin/curl"
        _cmd = (
            f"{_curl_path} --fail --location --show-error "
            f"--connect-timeout 30 --max-time {FALCON_DOWNLOAD_TIMEOUT} "
            f"-o {shlex.quote(_target_path)} {shlex.quote(aUrl)}"
        )
        _rc, _, _stdout, _stderr = self.__cluctrl.mExecuteLocal(_cmd, aLogOutError=True)
        if _rc != 0 or not os.path.exists(_target_path) or os.path.getsize(_target_path) == 0:
            raise ExacloudRuntimeError(
                f"{FALCON_LOG_PREFIX} Failed to download Falcon RPM from {aUrl}. "
                f"Exit code: {_rc}, stderr: {_stderr}"
            )
        ebLogInfo(f"{FALCON_LOG_PREFIX} Downloaded Falcon RPM to '{_target_path}'.")
        return _target_path

    def mIsFalconInstalled(self, aNode, aDomU):
        """Check whether the falcon-sensor package is already present on the DomU."""
        _result = node_exec_cmd(
            aNode,
            f"rpm -q {FALCON_PACKAGE_NAME}",
            check_error=False
        )
        return _result.exit_code == 0

    def mInstallRpmOnNode(self, aNode, aDomU, aRemotePath):
        """Install the Falcon RPM on the DomU using rpm -ivh."""
        _rpm_cmd = node_cmd_abs_path_check(aNode, "rpm") or "rpm"
        node_exec_cmd(
            aNode,
            f"{_rpm_cmd} -ivh {shlex.quote(aRemotePath)}",
            check_error=True,
            log_error=True,
            log_stdout_on_error=True
        )

    def mConfigureFalconSensor(self, aNode, aDomU, aCid):
        """Apply CID and proxy settings for Falcon and restart the service to pick them up."""
        if not aNode.mFileExists(FALCONCTL_PATH):
            raise ExacloudRuntimeError(f"{FALCON_LOG_PREFIX} Falcon control utility '{FALCONCTL_PATH}' not found on {aDomU}.")
        _pre_status = node_exec_cmd(
            aNode,
            f"{FALCONCTL_PATH} -g --apd --aph --app",
            check_error=False
        )
        ebLogInfo(f"{FALCON_LOG_PREFIX} Current Falcon proxy settings on {aDomU}: {_pre_status.stdout}")

        node_exec_cmd(
            aNode,
            f"{FALCONCTL_PATH} -s -f --cid={shlex.quote(aCid)}",
            check_error=True,
            log_error=True
        )
        _region = self.mDetectRegionIdentifier(aNode, aDomU)
        if _region:
            _proxy_host = f"prod.csproxy.{_region}.oci.oraclecloud.com"
            node_exec_cmd(
                aNode,
                f"{FALCONCTL_PATH} -s --apd=false --aph={shlex.quote(_proxy_host)} --app={FALCON_PROXY_PORT}",
                check_error=True,
                log_error=True
            )
        else:
            # below can be the case for pdit envs
            ebLogWarn(f"{FALCON_LOG_PREFIX} Region identifier unavailable on {aDomU}; skipping proxy configuration.")
        self.mRestartFalconService(aNode, aDomU)
        _post_status = node_exec_cmd(
            aNode,
            f"{FALCONCTL_PATH} -g --apd --aph --app",
            check_error=False
        )
        ebLogInfo(f"{FALCON_LOG_PREFIX} Updated Falcon proxy settings on {aDomU}: {_post_status.stdout}")

    def mDetectRegionIdentifier(self, aNode, aDomU):
        """Query the OCI metadata service for the region identifier."""
        _curl_cmd = node_cmd_abs_path_check(aNode, "curl")
        if not _curl_cmd:
            return None
        _metadata_cmd = (
            f"{_curl_cmd} --fail --silent --show-error --location "
            "--connect-timeout 5 --max-time 10 "
            f"-H {shlex.quote(FALCON_METADATA_HEADER)} "
            f"{shlex.quote(FALCON_METADATA_URL)}"
        )
        _result = node_exec_cmd(aNode, _metadata_cmd, check_error=False)
        if _result.exit_code == 0 and _result.stdout:
            return _result.stdout.strip().strip('"')
        return None

    def mRestartFalconService(self, aNode, aDomU):
        """Restart the Falcon systemd service on the DomU."""
        _systemctl = node_cmd_abs_path_check(aNode, "systemctl") or "systemctl"
        node_exec_cmd(
            aNode,
            f"{_systemctl} restart {FALCON_SERVICE_NAME}",
            check_error=True,
            log_error=True
        )

    def mValidateFalconService(self, aNode, aDomU):
        """Validate that the Falcon service is active and emit status diagnostics."""
        _systemctl = node_cmd_abs_path_check(aNode, "systemctl") or "systemctl"
        _status_result = node_exec_cmd(
            aNode,
            f"{_systemctl} status {FALCON_SERVICE_NAME} --no-pager",
            check_error=False
        )
        if _status_result.stdout:
            ebLogInfo(f"{FALCON_LOG_PREFIX} {FALCON_SERVICE_NAME} status on {aDomU}:\n{_status_result.stdout}")
        if _status_result.stderr:
            ebLogInfo(f"{FALCON_LOG_PREFIX} {FALCON_SERVICE_NAME} status stderr on {aDomU}:\n{_status_result.stderr}")
        _active_status = node_exec_cmd(
            aNode,
            f"{_systemctl} is-active {FALCON_SERVICE_NAME}",
            check_error=False
        )
        _active_output = (_active_status.stdout or "").strip()
        if _active_status.exit_code != 0 or _active_output != "active":
            raise ExacloudRuntimeError(
                f"{FALCON_LOG_PREFIX} Service {FALCON_SERVICE_NAME} is not active on {aDomU}. Output: {_active_output}"
            )
        _grep_cmd = node_cmd_abs_path_check(aNode, "grep") or "grep"
        _grep_result = node_exec_cmd(
            aNode,
            f"{_grep_cmd} CrowdStrike /var/log/messages | {_grep_cmd} Connected",
            check_error=False
        )
        if _grep_result.exit_code != 0:
            ebLogWarn(f"{FALCON_LOG_PREFIX} Unable to confirm CrowdStrike connectivity log entry on {aDomU}.")

    def mRemoveRemoteFile(self, aNode, aDomU, aRemotePath):
        """Remove the provided remote path on the DOMU"""
        _rm_cmd = node_cmd_abs_path_check(aNode, "rm") or "/bin/rm"
        node_exec_cmd(aNode, f"{_rm_cmd} -f {shlex.quote(aRemotePath)}", check_error=False)

    def mExtractFilenameFromUrl(self, aUrl):
        """Extract file name from the provided url"""
        _parsed = urllib.parse.urlparse(aUrl)
        return os.path.basename(_parsed.path)

    def mCarryoverCertR1(self):
        if self.__cluctrl.isATP():
            if is_r1_region():
                for _, _domU in self.__cluctrl.mReturnDom0DomUPair():
                    with connect_to_host(_domU, get_gcontext()) as _node:
                        node_exec_cmd_check(_node, "/bin/mkdir -p /opt/exacloud")
                        _node.mCopyFile(get_r1_certificate_path(), "/opt/exacloud/combined_r1.crt")
    
# end of file
