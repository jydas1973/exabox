#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/utils/clu_utils.py /main/12 2025/08/21 12:30:30 nelango Exp $
#
# clu_utils.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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
import json
import os

from exabox.core.DBStore import ebGetDefaultDB
from exabox.utils.common import mCompareModel

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace

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

    def mUpdateGlobalEsProperties(self):
        # Update global es.properties under exacloud/oeda/properties folder
        _global_es_properties_path = os.path.join(self.__cluctrl.mGetBasePath(),
                                                  "oeda/properties/es.properties")
        # For a unified method, please update the below dictionary to update any global es properties
        _dict_global_es_properties = {"DISABLEVALIDATEDGSPACEFOR37371565": {"previous": "false",
                                                                            "new": "true",
                                                                            "action": "replace"}}
        _append_celltypes_x11_xrmem = self.__cluctrl.mCheckConfigOption('append_celltypes_x11_xrmem')
        if _append_celltypes_x11_xrmem and _append_celltypes_x11_xrmem == 'True':
            _dict_global_es_properties["CELLTYPES"] = {
                "action": "append",
                "value": "X11MHCXRMEM:X11_XRMEM_ROCE_CELL_XC",
                "delimiter": ","
            }
            _dict_global_es_properties["HC_CELL_TYPES"] = {
                "action": "append",
                "value": "X11MHCXRMEM:X11_XRMEM_ROCE_CELL_XC",
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
